#!/usr/bin/env python3
"""Stream licensed snapshots/CSV/JSON into an append-only SQLite research ledger.

A source observation never approves publication. A/B proposals are staged separately
on a PR branch. C is research-only. No existing canonical record is overwritten.
"""
import argparse,csv,hashlib,html,json,math,re,sqlite3
from collections import Counter,defaultdict
from datetime import date
from pathlib import Path
from urllib.parse import urlsplit
from discovery import ROOT,digest,read,write
from validate import normalized,url_valid,DuplicateIndex,validate

COUNTRIES=read(ROOT/'data/bulk/country-codes.json')['codes']
ALIASES={'usa':'United States','unitedstatesofamerica':'United States','uk':'United Kingdom','czechrepublic':'Czechia','republicofkorea':'South Korea','russianfederation':'Russia','vietnam':'Vietnam','cotedivoire':'Côte d’Ivoire','türkiye':'Türkiye','turkey':'Türkiye'}
def country(value):
    if not isinstance(value,str):return ''
    return COUNTRIES.get(value.upper(),ALIASES.get(normalized(value),next((name for name in COUNTRIES.values() if normalized(name)==normalized(value)),'')))
def point(value):
    if not isinstance(value,str):return None
    m=re.fullmatch(r'Point\((-?[\d.]+) (-?[\d.]+)\)',value)
    if not m:return None
    lng,lat=map(float,m.groups());return (lat,lng) if math.isfinite(lat) and math.isfinite(lng) and abs(lat)<=90 and abs(lng)<=180 else None

def source_policy(config):
    result={}
    for s in config['sources']:
        if not s.get('enabled'):continue
        if not s.get('license') or not url_valid(s.get('license_url')) or not s.get('review') or not s.get('policy_urls'):raise ValueError('source licence/access review required')
        result[s['id']]=s
    return result

def domains(rows):
    by_name=defaultdict(set);by_domain=defaultdict(set)
    for r in rows:
        for name in [r['name'],r.get('company_name',''),r['company_id'],r['name'].partition(' — ')[0]]:
            if name:by_name[normalized(name)].add(r['company_id'])
        try:by_domain[(urlsplit(r['website']).hostname or '').removeprefix('www.')].add(r['company_id'])
        except ValueError:pass
    return by_name,by_domain

def normalize_wikidata(raw,observed,policy):
    qid=raw['source_record_id'];types={u.rsplit('/',1)[-1] for u in raw.get('types',[])}
    coords=[p for p in (point(v) for v in raw.get('coordinates',[])) if p]
    headquarters=raw.get('headquarters',[]);places=raw.get('places',[])
    countries=list(dict.fromkeys(country(v['name']) for v in raw.get('countries',[]) if country(v['name'])))
    source='https://www.wikidata.org/wiki/'+qid
    physical=raw.get('physical_facility',False) or 'Q21550789' in types
    reasons=[]
    if types & {'Q5','Q215627','Q4167410','Q4167836'}:reasons.append('human, disambiguation or category entity; not a studio facility')
    if raw.get('ended'):reasons.append('source has dissolution/end evidence; current physical operation requires research')
    if not physical:reasons.append('organisation listing; headquarters/company identity is not proof of a physical production facility')
    if len(coords)!=1:reasons.append('missing or conflicting direct facility coordinates; never substitute headquarters/city coordinates')
    if len(countries)!=1:reasons.append('current country missing or ambiguous')
    if not raw.get('name') or raw['name']==qid:reasons.append('human-readable operating/facility name unavailable')
    city=places[0]['name'] if len(places)==1 and places[0]['name'] else 'Municipality not supplied'
    # Parent ownership is a research claim, not the operating name or a branch capability.
    return {'candidate_id':'wd-'+qid.lower(),'source_record_id':qid,'source_id':policy['id'],'organisation_key':'wd-'+qid.lower(),
        'name':raw.get('name',qid),'city':city,'country':countries[0] if len(countries)==1 else '',
        'lat':coords[0][0] if len(coords)==1 else None,'lng':coords[0][1] if len(coords)==1 else None,
        'website':next((u for u in raw.get('websites',[]) if url_valid(u)),source),
        'website_kind':'official' if any(url_valid(u) for u in raw.get('websites',[])) else 'source_listing',
        'sectors':raw.get('sectors',[]),'facility_type':'production_studio' if physical else 'uncertain',
        'place_basis':'direct Wikidata facility coordinates; municipality is only the listed administrative place, not a verified street address',
        'parent_claims':raw.get('parents',[]),'source_observed_on':observed,'evidence_urls':[source],
        'license':policy['license'],'license_url':policy['license_url'],'attribution':policy['attribution'],
        'class':'C' if reasons else 'B','reasons':reasons or ['Wikidata physical-studio entity with direct coordinates and a country; source-listed only, not operationally corroborated'],
        'capabilities':[],'capability_evidence':{},'is_location_reference':physical and bool(coords)}

STUDIO_SECTORS={'film':'Film Production','cinema':'Film Production','video':'Video Production','television':'Television Production','animation':'Animation','motion_capture':'Motion Capture','performance_capture':'Performance Capture','virtual_production':'Virtual Production'}
OFFICE_SECTORS={'film_production':'Film Production','production_company':'Film Production','video_games':'Game Development','game_development':'Game Development','animation':'Animation','visual_effects':'VFX'}
def normalize_osm(raw,observed,policy):
    t=raw['tags'];name=t.get('name:en') or t.get('name','');reasons=[]
    sector=STUDIO_SECTORS.get(t.get('studio')) or OFFICE_SECTORS.get(t.get('office'))
    physical=t.get('man_made')=='studio' and t.get('studio') in STUDIO_SECTORS
    if not sector:reasons.append('studio type unspecified or outside screen/game production (for example music/radio)')
    if not physical:reasons.append('business/office tag does not independently establish a physical production facility')
    if not name:reasons.append('facility name missing')
    if any(t.get(k) and t[k] not in ('no','false') for k in ('disused','abandoned','disused:man_made','disused:office','end_date')):reasons.append('inactive/ended signal requires human research; no closure applied to existing records')
    lat,lng=raw.get('lat'),raw.get('lng')
    if any(type(v) not in (int,float) or not math.isfinite(v) for v in (lat,lng)) or isinstance(lat,(int,float)) and abs(lat)>90 or isinstance(lng,(int,float)) and abs(lng)>180:reasons.append('coordinates absent or invalid')
    place=country(t.get('addr:country',''))
    if not place:reasons.append('country not supplied; no unsupported bulk reverse-geocoding')
    city=t.get('addr:city') or 'Municipality not supplied'
    url='https://www.openstreetmap.org/'+raw['source_record_id'];website=t.get('website') or t.get('contact:website')
    organisation_key='osm-brand-'+(t.get('brand:wikidata') or digest([t.get('brand') or t.get('operator') or name,(urlsplit(website).hostname if url_valid(website) else '')])[:20]).lower()
    return {'candidate_id':'osm-'+raw['source_record_id'].replace('/','-'),'source_record_id':raw['source_record_id'],'source_id':policy['id'],'organisation_key':organisation_key,
        'name':name,'city':city,'country':place,'lat':lat,'lng':lng,'website':website if url_valid(website) else url,
        'website_kind':'official' if url_valid(website) else 'source_listing','sectors':[sector] if sector else [],'facility_type':'production_studio' if physical else 'production_office',
        'place_basis':'OSM node or way/relation centre; not independently geocoded. City/country only where supplied in source tags.',
        'parent_claims':[],'source_observed_on':observed,'evidence_urls':[url],'license':policy['license'],'license_url':policy['license_url'],'attribution':policy['attribution'],
        'class':'C' if reasons else 'B','reasons':reasons or ['Named, explicitly screen-production-tagged physical studio with coordinates and country; source-listed only'],
        'capabilities':[],'capability_evidence':{},'is_location_reference':physical and lat is not None and lng is not None,
        'identity_hints':{'wikidata':t.get('wikidata',''),'operator_wikidata':t.get('operator:wikidata',''),'brand_wikidata':t.get('brand:wikidata','')}}

SCHEMA='''PRAGMA journal_mode=WAL;
CREATE TABLE IF NOT EXISTS observations(source TEXT, source_key TEXT, content_hash TEXT, first_seen TEXT, last_seen TEXT, payload TEXT, PRIMARY KEY(source,source_key,content_hash));
CREATE TABLE IF NOT EXISTS runs(run_id TEXT PRIMARY KEY, observed_on TEXT, input_hash TEXT, baseline_hash TEXT, policy_hash TEXT);
CREATE TABLE IF NOT EXISTS decisions(run_id TEXT, candidate_id TEXT, evidence_class TEXT, decision TEXT, payload TEXT, PRIMARY KEY(run_id,candidate_id));
CREATE INDEX IF NOT EXISTS decision_class ON decisions(run_id,evidence_class);
'''

def inputs(folder,policies):
    for sid,p in policies.items():
        for path in sorted((folder/sid).glob('*.json')):
            if path.name.endswith('.meta.json'):continue
            meta=read(path.with_name(path.stem+'.meta.json'));rows=read(path)
            if meta.get('projection_hash')!=digest(rows) or meta.get('source')!=sid or meta.get('license')!=p['license']:raise ValueError('snapshot provenance/hash/licence mismatch: '+str(path))
            date.fromisoformat(meta['observed_on'])
            for r in rows:
                if sid=='wikidata':r={**r,'physical_facility':meta.get('class')=='Q21550789'}
                yield sid,r,meta

def ingest(folder,output,config,base,ledger=None):
    output=Path(output)
    if output.exists():raise ValueError('fresh output directory required; reuse --ledger for incremental history')
    policies=source_policy(config);db=sqlite3.connect(ledger or ':memory:');db.executescript(SCHEMA)
    grouped={};raw_count=0;source_counts=Counter();repeat=0;observed=date.today().isoformat();hashes=[]
    with db:
        for sid,r,meta in inputs(Path(folder),policies):
            raw_count+=1;source_counts[sid]+=1;key=r['source_record_id'];h=digest(r);hashes.append(h);observed=meta['observed_on']
            cursor=db.execute('INSERT OR IGNORE INTO observations VALUES(?,?,?,?,?,?)',(sid,key,h,observed,observed,json.dumps(r,ensure_ascii=False)))
            if not cursor.rowcount:repeat+=1
            db.execute('UPDATE observations SET last_seen=? WHERE source=? AND source_key=? AND content_hash=?',(observed,sid,key,h))
            if (sid,key) not in grouped:grouped[sid,key]=r
            elif sid=='wikidata':
                g=grouped[sid,key]
                for field in ('types','coordinates','headquarters','places','countries','websites','parents','sectors','ended'):
                    for value in r.get(field,[]):
                        if value not in g[field]:g[field].append(value)
                g['physical_facility']=g.get('physical_facility',False) or r.get('physical_facility',False)
        run=digest([sorted(hashes),digest(base),digest(config)])
        db.execute('INSERT OR IGNORE INTO runs VALUES(?,?,?,?,?)',(run,observed,digest(sorted(hashes)),digest(base),digest(config)))
        names,hosts=domains(base);index=DuplicateIndex(base);decisions=[];proposed=[];dupes=[]
        for (sid,key),raw in sorted(grouped.items()):
            c=(normalize_wikidata if sid=='wikidata' else normalize_osm)(raw,observed,policies[sid]);c['observation_hash']=digest(raw)
            company_matches=names.get(normalized(c['name']),set()) or hosts.get((urlsplit(c['website']).hostname or '').removeprefix('www.'),set())
            c['existing_organisation_matches']=sorted(company_matches)
            # Company matching is advisory; never merges distinct branches or inherits services.
            tentative={'id':c['candidate_id'],'company_id':next(iter(company_matches)) if len(company_matches)==1 else c['organisation_key'],'name':c['name'],'city':c['city'],'country':c['country'],'website':c['website']}
            matches=index.matches(tentative) if c['city']!='Municipality not supplied' else []
            if matches:
                c['class']='C';c['reasons'].append('possible existing location: source/city/name match is insufficient to overwrite or auto-merge a reviewed facility');c['potential_duplicates']=matches;dupes.append(c['candidate_id'])
            c['provenance']=[{'source_id':sid,'source_record_id':key,'url':u,'license':c['license'],'license_url':c['license_url'],'observed_on':observed,'observation_hash':c['observation_hash']} for u in c['evidence_urls']]
            c['publication_approved']=False;c['decision']='propose_source_listed' if c['class']=='B' else 'research_required'
            if c['class']=='B':
                r={**tentative,'lat':c['lat'],'lng':c['lng'],'address':c['place_basis'],'categories':c['sectors'],'capabilities':[],'capability_evidence':{},'evidence_state':'unknown','evidence_class':'B','evidence':c['evidence_urls'][0],'verified_on':'','source_observed_on':observed,'coordinate_precision':'approximate','coordinate_source':c['evidence_urls'][0],'location_type':c['facility_type'],'relationships':[], 'status':'Source-listed directory record; current operation, physical precision and site capabilities have not been independently corroborated. '+c['place_basis'],'website_kind':c['website_kind'],'source_provenance':c['provenance'],'license':c['license'],'attribution':c['attribution']}
                proposed.append(r)
            db.execute('INSERT OR IGNORE INTO decisions VALUES(?,?,?,?,?)',(run,c['candidate_id'],c['class'],c['decision'],json.dumps(c,ensure_ascii=False)));decisions.append(c)
    counts=Counter(c['class'] for c in decisions)
    report={'version':1,'run_id':run,'observed_on':observed,'raw_source_records':raw_count,'source_records':dict(source_counts),'unique_candidate_identities':len(decisions),'unique_location_references':sum(c['is_location_reference'] for c in decisions),'organisation_leads_without_physical_facility_evidence':sum(not c['is_location_reference'] for c in decisions),'duplicate_source_observations_coalesced':raw_count-len(decisions),'previously_seen_observation_versions':repeat,'potential_existing_duplicates':len(dupes),'candidate_classes':dict(counts),'proposed_public_additions':len(proposed),'baseline_locations_preserved':len(base),'baseline_hash':digest(base),'published_records':0,'approval':'human review of exact proposed files required; no source or classifier grants approval','sources':[{k:p.get(k) for k in ('id','license','license_url','attribution','endpoint','policy_urls','review')} for p in policies.values()],'reasons':dict(Counter(reason for c in decisions if c['class']=='C' for reason in c['reasons']))}
    output.mkdir(parents=True)
    write(output/'coverage.json',report);write(output/'proposed-b.json',proposed)
    with (output/'candidates.jsonl').open('w') as f:
        for c in decisions:f.write(json.dumps(c,ensure_ascii=False)+'\n')
    with (output/'candidates.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=['candidate_id','name','city','country','class','decision','source_id','source_record_id','evidence_urls','reasons','license']);w.writeheader()
        for c in decisions:w.writerow({k:json.dumps(c[k],ensure_ascii=False) if isinstance(c[k],list) else c[k] for k in w.fieldnames})
    rows=''.join('<tr><td>'+html.escape(c['name'])+'</td><td>'+html.escape(c['country'])+'</td><td>'+c['class']+'</td><td>'+html.escape('; '.join(c['reasons']))+'</td></tr>' for c in decisions)
    (output/'coverage.html').write_text('<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>MotionX bulk research</title><style>body{font:16px system-ui;background:#111824;color:#eef;padding:2rem}table{border-collapse:collapse}td,th{border:1px solid #789;padding:.5rem}pre{white-space:pre-wrap}</style><h1>Bulk acquisition review — no publication approved</h1><p>A: current site evidence. B: source-listed, not independently corroborated. C: research-only. Company leads are not physical studio counts.</p><pre>'+html.escape(json.dumps(report,indent=2))+'</pre><table><tr><th>Name</th><th>Country</th><th>Class</th><th>Reasons</th></tr>'+rows+'</table></html>')
    if ledger:db.execute('PRAGMA wal_checkpoint(TRUNCATE)')
    db.close();print('BULK_COVERAGE '+json.dumps(report),flush=True);return report

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--input',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--ledger',type=Path);p.add_argument('--config',type=Path,default=ROOT/'data/bulk/sources.json');p.add_argument('--database',type=Path,default=ROOT/'studios.json');a=p.parse_args()
    ingest(a.input,a.output,read(a.config),read(a.database),a.ledger)
if __name__=='__main__':main()
