#!/usr/bin/env python3
"""Stream licensed snapshots/CSV/JSON into an append-only SQLite research ledger.

A source observation never approves publication. A/B proposals are staged separately
on a PR branch. C is research-only. No existing canonical record is overwritten.
"""
import argparse,csv,hashlib,html,json,math,re,sqlite3,struct
from collections import Counter,defaultdict
from datetime import date
from pathlib import Path
from urllib.parse import urlsplit
from discovery import ROOT,digest,read,write
from validate import normalized,url_valid,DuplicateIndex,validate
from bulk_snapshot import safe_website

COUNTRIES=read(ROOT/'data/bulk/country-codes.json')['codes']
ALIASES={'usa':'United States','unitedstatesofamerica':'United States','uk':'United Kingdom','czechrepublic':'Czechia','republicofkorea':'South Korea','russianfederation':'Russia','vietnam':'Vietnam','cotedivoire':'Côte d’Ivoire','türkiye':'Türkiye','turkey':'Türkiye'}
COUNTRY_NAMES={normalized(v):v for v in COUNTRIES.values()}
def country(value):
    if not isinstance(value,str):return ''
    return COUNTRIES.get(value.upper()) or ALIASES.get(normalized(value)) or COUNTRY_NAMES.get(normalized(value),'')
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
        if s.get('id') in result or not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*',s.get('id','')):raise ValueError('invalid/duplicate source identity')
        if s.get('adapter') not in ('wikidata_sparql','overpass','overture_geoparquet','licensed_batch'):raise ValueError('unreviewed source adapter')
        result[s['id']]=s
    return result

def domains(rows):
    by_name=defaultdict(set);by_domain=defaultdict(set)
    for r in rows:
        for name in [r['name'],r.get('company_name',''),r['company_id'],r['name'].partition(' — ')[0]]:
            if name:by_name[normalized(name)].add(r['company_id'])
        try:
            h=(urlsplit(r['website']).hostname or '').removeprefix('www.')
            if r.get('website_kind')!='source_listing' and h and h not in SHARED_HOSTS:by_domain[h].add(r['company_id'])
        except ValueError:pass
    return by_name,by_domain

SHARED_HOSTS={'facebook.com','instagram.com','linkedin.com','youtube.com','youtu.be','tiktok.com','linktr.ee','sites.google.com','overturemaps-us-west-2.s3.amazonaws.com'}

def near(a,b,km=80):
    if any(type(r.get(k)) not in (int,float) for r in (a,b) for k in ('lat','lng')):return False
    lat1,lat2=math.radians(a['lat']),math.radians(b['lat']);dl=math.radians(a['lng']-b['lng']);dp=lat1-lat2
    distance=6371*2*math.asin(min(1,math.sqrt(math.sin(dp/2)**2+math.cos(lat1)*math.cos(lat2)*math.sin(dl/2)**2)))
    return distance<=km

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

def wkb_point(value):
    try:
        b=bytes.fromhex(value);endian='<' if b[0]==1 else '>' if b[0]==0 else None
        if not endian:return None
        kind=struct.unpack(endian+'I',b[1:5])[0]
        if kind & 0xffff != 1:return None
        offset=9 if kind & 0x20000000 else 5
        lng,lat=struct.unpack(endian+'dd',b[offset:offset+16])
        return (lat,lng) if math.isfinite(lat) and math.isfinite(lng) and abs(lat)<=90 and abs(lng)<=180 else None
    except (ValueError,TypeError,IndexError,struct.error):return None

PROVIDER_LICENSES={**{normalized(n):'CDLA-Permissive-2.0' for n in ('Meta','Microsoft','PinMeTo','Krick','RenderSEO','DAC','BrightQuery','Birdeye','Uberall','OpenTravel')},'foursquare':'Apache-2.0','alltheplaces':'CC0-1.0'}
def normalize_overture(raw,observed,policy):
    rid=raw['source_record_id'];category=raw.get('category','');reasons=[]
    sector=policy.get('eligible_categories',{}).get(category)
    if not sector:reasons.append('category not yet reviewed as an eligible production business/facility; research only')
    if raw.get('operating_status') in ('permanently_closed','temporarily_closed'):reasons.append('directory has a closure signal; requires research, never closes an existing published location')
    threshold=policy.get('minimum_provider_confidence',.9)
    if not .9<=threshold<=1:raise ValueError('relaxing the reviewed 0.9 existence-quality floor requires a code/policy review')
    if type(raw.get('confidence')) not in (float,int) or not math.isfinite(raw['confidence']) or not threshold<=raw['confidence']<=1:reasons.append('provider existence confidence below '+str(threshold)+' or unavailable; not an independent verification score')
    name=raw.get('name') if isinstance(raw.get('name'),str) else '';coords=wkb_point(raw.get('geometry_wkb'))
    if not coords:reasons.append('exact source Point geometry missing; bbox/city coordinates not substituted')
    addresses=raw.get('addresses') or []
    countries=list(dict.fromkeys(country(a.get('country')) for a in addresses if country(a.get('country'))))
    if len(countries)!=1:reasons.append('country absent or conflicting in the source')
    cities=list(dict.fromkeys(a['locality'].strip() for a in addresses if isinstance(a.get('locality'),str) and a['locality'].strip()))
    if len(cities)!=1:reasons.append('source municipality absent or conflicting; no invented city or bulk reverse-geocoding')
    city=cities[0] if len(cities)==1 else 'Municipality not supplied'
    if not isinstance(name,str) or not name.strip():reasons.append('operating/facility name missing')
    providers=raw.get('sources') or []
    if raw.get('withheld_overlays'):reasons.append('source-provider status-overlay redistribution mapping unresolved; payload withheld and candidate remains research-only')
    # Official October 2026 licence table lists each original provider together
    # with Overture under that provider's licence. Confidence-only Overture
    # transformation metadata is not a separate content provider. Unknown status
    # overlays remain unresolved; do not invent a licence for Overture-signals.
    content_providers=[s for s in providers if not (s.get('dataset')=='Overture' and s.get('property')=='/properties/confidence')]
    licences=sorted({PROVIDER_LICENSES.get(normalized(s.get('dataset') or ''),'unresolved') for s in content_providers})
    if not licences or 'unresolved' in licences:reasons.append('source-provider redistribution licence unresolved')
    website=next((u for u in raw.get('websites') or [] if url_valid(u) and safe_website(u)),None)
    website_hosts=sorted({(urlsplit(u).hostname or '').removeprefix('www.') for u in raw.get('websites') or [] if safe_website(u)})
    source=raw['filename']
    prefix='https://overturemaps-us-west-2.s3.amazonaws.com/release/'+policy['release']+'/theme=places/type=place/'
    if not source.startswith(prefix) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._-]*\.parquet',source[len(prefix):]):raise ValueError('unapproved source object path')
    organisation='overture-org-'+digest([normalized(name),(urlsplit(website).hostname or '').removeprefix('www.')])[:24] if website else 'overture-org-'+digest(rid)[:24]
    return {'candidate_id':'overture-'+re.sub('[^a-z0-9]+','-',rid.lower()).strip('-'),'source_record_id':rid,'source_id':'overture','organisation_key':organisation,
        'name':name,'city':city,'country':countries[0] if len(countries)==1 else '', 'lat':coords[0] if coords else None,'lng':coords[1] if coords else None,
        'website':website or source,'website_kind':'official' if website else 'source_listing','sectors':[sector] if sector else [],'facility_type':'uncertain',
        'place_basis':'Original Overture Point geometry, not a verified facility geocode. Municipality/country copied only from provider locality/country fields.',
        'parent_claims':[],'source_observed_on':observed,'evidence_urls':[source],'source_release':policy['release'],'source_category':category,'source_providers':providers,
        'provider_confidence':raw.get('confidence'),'source_operating_status':raw.get('operating_status'),'identity_website_hosts':website_hosts,'license':' AND '.join(licences),
        'license_url':policy['license_url'],'attribution':'Overture Maps Foundation; '+', '.join(sorted({s.get('dataset','') for s in providers}))+'. Foursquare data transformed to Overture schema; MotionX filters/normalizes fields. See data/bulk/LICENSES.',
        'class':'C' if reasons else 'B','reasons':reasons or ['Permissively licensed production-place directory listing; operating status, site type and capabilities remain uncorroborated'],
        'capabilities':[],'capability_evidence':{},'is_location_reference':bool(coords)}

def normalize_batch(raw,observed,policy):
    """Only reviewed directory mappings can produce B. Input claims cannot produce A."""
    sid=policy['id'];key=raw['source_record_id'];reasons=[]
    name=raw.get('name','');city=raw.get('city') or 'Municipality not supplied';place=country(raw.get('country',''))
    lat,lng=raw.get('lat'),raw.get('lng')
    coords=all(type(v) in (int,float) and math.isfinite(v) for v in (lat,lng)) and abs(lat)<=90 and abs(lng)<=180
    sectors=[s for s in raw.get('sectors',[]) if s in policy.get('eligible_sectors',[])]
    if not policy.get('physical_place_directory'):reasons.append('company listing does not establish a physical production place')
    if not sectors:reasons.append('sector mapping requires source review')
    if not coords:reasons.append('valid original source coordinates unavailable')
    if not place:reasons.append('country missing or unsupported')
    if not name.strip():reasons.append('operating/facility name missing')
    website=raw.get('website');url=raw.get('source_url')
    if not url_valid(url):reasons.append('record-level source URL missing or invalid')
    host=(urlsplit(website).hostname or '').removeprefix('www.') if url_valid(website) else ''
    return {'candidate_id':sid+'-'+digest(key)[:28],'source_record_id':key,'source_id':sid,
        'organisation_key':sid+'-org-'+digest([normalized(name),host] if host else key)[:24],
        'name':name,'city':city,'country':place,'lat':lat if coords else None,'lng':lng if coords else None,
        'website':website if url_valid(website) else url,'website_kind':'official' if url_valid(website) else 'source_listing',
        'sectors':sectors,'facility_type':'uncertain','place_basis':'Directory point and locality as supplied; facility accuracy and current operation not independently corroborated.',
        'parent_claims':raw.get('parent_claims',[]),'source_observed_on':observed,'evidence_urls':[url] if url_valid(url) else [],
        'license':policy['license'],'license_url':policy['license_url'],'attribution':policy['attribution'],
        'class':'C' if reasons else 'B','reasons':reasons or ['Permitted production-place directory listing; not independent verification'],
        'capabilities':[],'capability_evidence':{},'is_location_reference':bool(coords)}

SCHEMA='''PRAGMA journal_mode=WAL;
CREATE TABLE IF NOT EXISTS observations(source TEXT, source_key TEXT, content_hash TEXT, first_seen TEXT, last_seen TEXT, payload TEXT, PRIMARY KEY(source,source_key,content_hash));
CREATE TABLE IF NOT EXISTS runs(run_id TEXT PRIMARY KEY, observed_on TEXT, input_hash TEXT, baseline_hash TEXT, policy_hash TEXT);
CREATE TABLE IF NOT EXISTS decisions(run_id TEXT, candidate_id TEXT, evidence_class TEXT, decision TEXT, payload TEXT, PRIMARY KEY(run_id,candidate_id));
CREATE INDEX IF NOT EXISTS decision_class ON decisions(run_id,evidence_class);
'''

def inputs(folder,policies):
    for sid,p in policies.items():
        for path in sorted((folder/sid).glob('*.json')):
            if path.name.endswith('.meta.json') or not path.with_name(path.stem+'.meta.json').exists():continue
            meta=read(path.with_name(path.stem+'.meta.json'));rows=read(path)
            if meta.get('projection_hash')!=digest(rows) or meta.get('source')!=sid or meta.get('license')!=p['license']:raise ValueError('snapshot provenance/hash/licence mismatch: '+str(path))
            date.fromisoformat(meta['observed_on'])
            for r in rows:
                if sid=='wikidata':r={**r,'physical_facility':meta.get('class')=='Q21550789'}
                yield sid,r,meta

def ingest(folder,output,config,base,ledger=None,existing=()):
    output=Path(output)
    if output.exists():raise ValueError('fresh output directory required; reuse --ledger for incremental history')
    policies=source_policy(config);db=sqlite3.connect(ledger or ':memory:');db.executescript(SCHEMA)
    grouped={};dates={};conflicts=defaultdict(list);raw_count=0;source_counts=Counter();repeat=0;observed=date.today().isoformat();hashes=[];unique_versions=set()
    with db:
        for sid,r,meta in inputs(Path(folder),policies):
            raw_count+=1;source_counts[sid]+=1;key=r['source_record_id'];h=digest(r);observed=meta['observed_on'];hashes.append(digest([sid,key,h,observed]))
            unique_versions.add((sid,key,h))
            cursor=db.execute('INSERT OR IGNORE INTO observations VALUES(?,?,?,?,?,?)',(sid,key,h,observed,observed,json.dumps(r,ensure_ascii=False)))
            if not cursor.rowcount:repeat+=1
            db.execute('UPDATE observations SET first_seen=min(first_seen,?),last_seen=max(last_seen,?) WHERE source=? AND source_key=? AND content_hash=?',(observed,observed,sid,key,h))
            dates[sid,key]=min(dates.get((sid,key),observed),observed)
            if (sid,key) not in grouped:grouped[sid,key]=r
            elif sid=='wikidata':
                g=grouped[sid,key]
                for field in ('types','coordinates','headquarters','places','countries','websites','parents','sectors','ended'):
                    for value in r.get(field,[]):
                        if value not in g[field]:g[field].append(value)
                g['physical_facility']=g.get('physical_facility',False) or r.get('physical_facility',False)
            elif grouped[sid,key]!=r:
                conflicts[sid,key].append({'observation_hash':h,'observed_on':observed})
        processor_hash=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
        run=digest([sorted(hashes),digest(base),digest(config),digest(list(existing)),processor_hash])
        db.execute('INSERT OR IGNORE INTO runs VALUES(?,?,?,?,?)',(run,observed,digest(sorted(hashes)),digest(base),digest(config)))
        matching_base=base+list(existing);existing_by_id={r['id']:r for r in matching_base};names,hosts=domains(matching_base);index=DuplicateIndex(matching_base);decisions=[];proposed=[];dupes=[]
        retained_companies={r['company_id'] for r in base}
        for (sid,key),raw in sorted(grouped.items()):
            seen_on=dates[sid,key]
            adapter=policies[sid]['adapter']
            normalizer={'wikidata_sparql':normalize_wikidata,'overpass':normalize_osm,'overture_geoparquet':normalize_overture,'licensed_batch':normalize_batch}[adapter]
            c=normalizer(raw,seen_on,policies[sid]);c['observation_hash']=digest(raw)
            if conflicts[sid,key]:
                if c['class']=='B':c['reasons']=[]
                c['class']='C';c['reasons'].append('conflicting versions share one source identity; no version selected for publication');c['conflicting_source_versions']=[{'observation_hash':digest(raw),'observed_on':seen_on}]+conflicts[sid,key]
            identity_host=(urlsplit(c['website']).hostname or '').removeprefix('www.') if c['website_kind']=='official' else ''
            name_matches=names.get(normalized(c['name']),set());host_matches=set(hosts.get(identity_host,set()))
            for h in c.get('identity_website_hosts',[]):
                if h not in SHARED_HOSTS:host_matches.update(hosts.get(h,set()))
            company_matches=name_matches | host_matches
            compatible=host_matches & name_matches if name_matches else host_matches
            resolved=next(iter(compatible)) if len(compatible)==1 else None
            if name_matches and host_matches and not compatible:
                if c['class']=='B':c['reasons']=[]
                c['class']='C';c['reasons'].append('conflicting organisation name/domain signals; no operating identity merged')
            c['existing_organisation_matches']=sorted(company_matches)
            c['organisation_matching_reasons']={'name_matches':sorted(name_matches),'directory_website_domain_matches':sorted(host_matches),'resolved_identity':resolved,'confidence':'source-domain association only; not independent ownership verification' if resolved else 'unresolved; name-only matches never merge operating identities'}
            previous=existing_by_id.get(c['candidate_id'])
            if previous:
                before={k:previous.get(k) for k in ('name','city','country','lat','lng','categories','source_observed_on')}
                after={k:c.get(k) for k in ('name','city','country','lat','lng','source_observed_on')};after['categories']=c['sectors']
                c['existing_record_change_proposal']={'id':previous['id'],'before_hash':digest(previous),'before':before,'observed_source_values':after,'changed_fields':[k for k in before if before[k]!=after[k]],'research_only':True,'approval_required':True}
            # Company matching is advisory; never merges distinct branches or inherits services.
            tentative={'id':c['candidate_id'],'company_id':resolved or c['organisation_key'],'name':c['name'],'city':c['city'],'country':c['country'],'website':c['website']}
            match_row={**tentative,'website':c['website'] if c['website_kind']=='official' else ''}
            matches=index.matches(match_row) if c['city']!='Municipality not supplied' else []
            # A city reference and a real municipality label may describe the same
            # branch. Defer nearby same-organisation matches without merging pins.
            if not matches and company_matches:
                matches=[{'ids':[r['id'],c['candidate_id']],'reasons':['same organisation near an existing reference; metropolitan/municipality identity requires review']} for r in matching_base if r['company_id'] in company_matches and country(r['country'])==c['country'] and near(r,c)]
            if matches:
                if c['class']=='B':c['reasons']=[]
                c['class']='C';c['reasons'].append('possible existing location: source/city/name match is insufficient to overwrite or auto-merge a reviewed facility');c['potential_duplicates']=matches;dupes.append(c['candidate_id'])
            c['provenance']=[{'source_id':sid,'source_record_id':key,'url':u,'license':c['license'],'license_url':c['license_url'],'observed_on':seen_on,'observation_hash':c['observation_hash']} for u in c['evidence_urls']]
            c['publication_approved']=False;c['decision']='propose_source_listed' if c['class']=='B' else 'research_required'
            if c['class']=='B':
                r={**tentative,'lat':c['lat'],'lng':c['lng'],'address':c['place_basis'],'categories':c['sectors'],'capabilities':[],'capability_evidence':{},'evidence_state':'unknown','evidence_class':'B','evidence':c['evidence_urls'][0],'verified_on':'','source_observed_on':seen_on,'coordinate_precision':'approximate','coordinate_source':c['evidence_urls'][0],'location_type':c['facility_type'],'relationships':[], 'status':'Source-listed directory record; current operation, physical precision and site capabilities have not been independently corroborated. '+c['place_basis'],'website_kind':c['website_kind'],'source_provenance':c['provenance'],'license':c['license'],'attribution':c['attribution'],'identity_status':'matched_existing' if resolved in retained_companies else 'source_provisional'}
                proposed.append(r)
                # Later observations are reviewed as possible duplicates, never silently
                # merged into this proposal. Same-owner, same-city facilities survive in C.
                index.add(match_row)
            db.execute('INSERT OR IGNORE INTO decisions VALUES(?,?,?,?,?)',(run,c['candidate_id'],c['class'],c['decision'],json.dumps(c,ensure_ascii=False)));decisions.append(c)
    counts=Counter(c['class'] for c in decisions)
    batch_path=Path(folder)/'batch-report.json'
    batch_report=read(batch_path) if batch_path.exists() else {}
    rejected=batch_report.get('rejected',[])
    if batch_report and (batch_report.get('accepted_observations')!=raw_count or batch_report.get('raw_source_records')!=raw_count+len(rejected)):raise ValueError('batch report/snapshot record-count mismatch')
    inventory=Path(folder)/'overture/category-inventory.json'
    expected=sum(r['count'] for r in read(inventory) if r.get('selected_for_research')) if inventory.exists() else None
    acquisition=Path(folder)/'overture-collection.json'
    complete=read(acquisition).get('complete',False) if acquisition.exists() else None
    report={'version':1,'run_id':run,'processor_hash':processor_hash,'observed_on':observed,'raw_source_records':raw_count+len(rejected),'retained_source_observations':raw_count,'source_records':dict(source_counts),'unique_candidate_identities':len(decisions),'unique_location_references':sum(c['is_location_reference'] for c in decisions),'organisation_leads_without_physical_facility_evidence':sum(not c['is_location_reference'] for c in decisions),'duplicate_source_observations_coalesced':raw_count-len(unique_versions),'conflicting_source_identities':sum(bool(v) for v in conflicts.values()),'previously_seen_observation_versions':repeat,'potential_existing_duplicates':len(dupes),'candidate_classes':dict(counts),'proposed_public_additions':len(proposed),'baseline_locations_preserved':len(base),'baseline_hash':digest(base),'existing_source_listed_preserved':len(existing),'expected_selected_source_records':expected,'acquisition_complete':(complete is True and (expected is None or expected==source_counts.get('overture',0))) or batch_report.get('complete',False) is True,'rejected_malformed_records':len(rejected),'rejected_record_audit':rejected,'deferred_candidates':counts.get('C',0),'proposed_countries':len({r['country'] for r in proposed}),'proposed_operating_identities':len({r['company_id'] for r in proposed}),'country_classes':{place:dict(Counter(c['class'] for c in decisions if c['country']==place)) for place in sorted({c['country'] for c in decisions})},'published_records':0,'approval':'human review of exact proposed files required; no source or classifier grants approval','sources':[{k:p.get(k) for k in ('id','license','license_url','attribution','endpoint','policy_urls','review')} for p in policies.values()],'reasons':dict(Counter(reason for c in decisions if c['class']=='C' for reason in c['reasons']))}
    output.mkdir(parents=True)
    write(output/'coverage.json',report);write(output/'proposed-b.json',proposed)
    with (output/'candidates.jsonl').open('w') as f:
        for c in decisions:f.write(json.dumps(c,ensure_ascii=False)+'\n')
    with (output/'candidates.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=['candidate_id','name','city','country','class','decision','source_id','source_record_id','evidence_urls','reasons','license']);w.writeheader()
        def safe(value):
            text=json.dumps(value,ensure_ascii=False) if isinstance(value,list) else str(value)
            return "'"+text if re.match(r'^[\s\u200b\u200c\u200d]*[=+@-]',text) else text
        for c in decisions:w.writerow({k:safe(c[k]) for k in w.fieldnames})
    from bulk_report import dashboard
    dashboard(output/'coverage.html',report,decisions)
    if ledger:db.execute('PRAGMA wal_checkpoint(TRUNCATE)')
    db.close();print('BULK_COVERAGE '+json.dumps(report),flush=True);return report

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--input',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--ledger',type=Path);p.add_argument('--config',type=Path,default=ROOT/'data/bulk/sources.json');p.add_argument('--database',type=Path,default=ROOT/'studios.json');a=p.parse_args()
    ingest(a.input,a.output,read(a.config),read(a.database),a.ledger)
if __name__=='__main__':main()
