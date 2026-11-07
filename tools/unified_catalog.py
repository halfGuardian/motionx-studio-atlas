#!/usr/bin/env python3
"""Build one research atlas: retained locations + all place observations + companies.

Inclusion is not verification. Company-only records get no invented coordinates.
Existing reviewed records remain byte-for-byte in studios.json. Source prose,
personal contacts and unresolved status-overlay payloads are not republished.
"""
import argparse,csv,hashlib,json,math,re,tempfile
from collections import Counter,defaultdict
from datetime import date
from pathlib import Path
from urllib.parse import urlsplit
from bulk_catalog import compact,sha
from bulk_ingest import ingest,country,domains,SHARED_HOSTS
from discovery import ROOT,read,write,digest
from validate import ID,url_valid,validate,normalized
from compact_index import add_transport

KINDS={'source_location','company_reference'}
FIELDS={'id','company_id','name','city','country','lat','lng','website','website_kind','categories','capabilities','capability_evidence','evidence_state','evidence_class','evidence','verified_on','source_observed_on','coordinate_precision','coordinate_source','location_type','relationships','status','identity_status','record_kind','source_provenance','license','attribution','research_reasons','potential_duplicates','source_status','source_category','source_type','provider_confidence','source_release','organisation_matching_reasons','research_review'}

def validate_research(rows):
    errors=[];seen=set()
    for row in rows:
        rid=row.get('id','invalid')
        def error(msg):errors.append(str(rid)+': '+msg)
        if set(row)-FIELDS:error('unsupported/private fields')
        for field in ('id','company_id'):
            if not isinstance(row.get(field),str) or not ID.fullmatch(row[field]):error('invalid '+field)
        if rid in seen:error('duplicate source identity')
        seen.add(rid)
        if not isinstance(row.get('name'),str) or not row['name'].strip():error('missing source name')
        if row.get('record_kind') not in KINDS or row.get('evidence_class') not in ('B','C'):error('invalid research kind/class')
        if row.get('evidence_state')!='unknown' or row.get('verified_on') or row.get('capabilities') or row.get('capability_evidence') or row.get('relationships'):error('research cannot grant verified services/ownership')
        if not isinstance(row.get('city'),str) or not isinstance(row.get('country'),str):error('invalid geography text')
        point=row.get('lat') is not None or row.get('lng') is not None
        if point and (any(type(row.get(k)) not in (float,int) or not math.isfinite(row[k]) for k in ('lat','lng')) or abs(row['lat'])>90 or abs(row['lng'])>180):error('invalid original point')
        if row.get('record_kind')=='company_reference' and point:error('company references cannot acquire fabricated map points')
        if row.get('evidence_class')=='B' and (not point or not row.get('city') or not row.get('country') or row.get('license')=='UNSPECIFIED'):error('incomplete source-listed location')
        if row.get('coordinate_precision') not in ('approximate','unverified'):error('research point is not a verified facility geocode')
        for k in ('website','evidence','coordinate_source'):
            if row.get(k) and not url_valid(row[k]):error('unsafe '+k)
        if not isinstance(row.get('categories'),list) or any(not isinstance(c,str) or not c.strip() for c in row['categories']):error('invalid source sectors')
        if not row.get('license') or not row.get('attribution'):error('source terms/attribution required')
        review=row.get('research_review')
        if review is not None:
            expected={'version','relevance','publication_state','source_rights','operation_status','reviewed_on','human_approved','facility_verified'}
            if (not isinstance(review,dict) or set(review)!=expected or review.get('version')!=1
                or row.get('record_kind')!='company_reference' or row.get('evidence_class')!='C'
                or review.get('relevance') not in ('motionx_core','adjacent_production','game_development','supporting_services')
                or review.get('publication_state')!='provisional_research_lead'
                or review.get('source_rights') not in ('agency_factual_projection_permission','minimal_facts_terms_unspecified')
                or review.get('operation_status') not in ('programme_listing_only','source_self_report_unverified','regional_listing_only')
                or review.get('reviewed_on')!=row.get('source_observed_on')
                or review.get('human_approved') is not False or review.get('facility_verified') is not False):error('invalid company research review; approval/facility inference forbidden')
        duplicates=row.get('potential_duplicates',[])
        if not isinstance(duplicates,list):error('invalid duplicate review metadata')
        else:
            for match in duplicates:
                if (not isinstance(match,dict) or set(match)!={'ids','reasons'}
                    or not isinstance(match.get('ids'),list) or not match['ids']
                    or any(not isinstance(i,str) or not ID.fullmatch(i) for i in match['ids'])
                    or not isinstance(match.get('reasons'),list) or not match['reasons']
                    or any(not isinstance(reason,str) or not reason.strip() for reason in match['reasons'])):
                    error('invalid duplicate review metadata')
        try:
            if date.fromisoformat(row['source_observed_on']).isoformat()!=row['source_observed_on'] or row['source_observed_on']>date.today().isoformat():raise ValueError()
        except (ValueError,KeyError,TypeError):error('invalid observation date')
        if not isinstance(row.get('source_provenance'),list) or not row['source_provenance']:error('source provenance missing');continue
        for p in row['source_provenance']:
            if set(p)-{'source_id','source_record_id','url','license','license_url','observed_on','observation_hash'}:error('unsupported provenance fields')
            if not url_valid(p.get('url')) or not url_valid(p.get('license_url')) or not re.fullmatch(r'[a-f0-9]{64}',p.get('observation_hash','')) or p.get('observed_on')!=row['source_observed_on']:error('invalid source provenance')
    return errors

def observation(c,base_companies):
    resolved=c.get('organisation_matching_reasons',{}).get('resolved_identity')
    city=c.get('city','');city='' if city=='Municipality not supplied' else city
    return {'id':c['candidate_id'],'company_id':resolved or c['organisation_key'],'name':c['name'] or c['source_record_id'],
        'city':city,'country':c.get('country',''),'lat':c['lat'],'lng':c['lng'],'website':c['website'],'website_kind':c['website_kind'],
        'categories':c['sectors'],'capabilities':[],'capability_evidence':{},'evidence_state':'unknown','evidence_class':c['class'],'verified_on':'',
        'source_observed_on':c['source_observed_on'],'evidence':c['evidence_urls'][0],'coordinate_precision':'approximate' if c['lat'] is not None else 'unverified',
        'coordinate_source':c['evidence_urls'][0],'location_type':'uncertain','relationships':[],'record_kind':'source_location',
        'status':'Source location observation. Current operation, physical production-facility type and services have not been independently corroborated. '+c['place_basis'],
        'identity_status':'matched_existing' if resolved in base_companies else 'source_provisional','source_provenance':c['provenance'],
        'license':c['license'],'attribution':c['attribution'],'research_reasons':c['reasons'],'potential_duplicates':c.get('potential_duplicates',[]),
        'source_status':c.get('source_operating_status') or 'not supplied','source_category':c.get('source_category',''),'source_type':'directory place',
        'provider_confidence':c.get('provider_confidence'),'source_release':c.get('source_release',''),'organisation_matching_reasons':c.get('organisation_matching_reasons',{})}

def companies(path,base,observed,source_url):
    names,hosts=domains(base);output=[]
    with Path(path).open(encoding='utf-8-sig',newline='') as stream:
        for number,raw in enumerate(csv.DictReader(stream),1):
            # Factual reference fields only. Do not copy authored descriptions,
            # social/contact profiles or pretend an unspecified licence is CC0.
            name=raw['Name'].strip();place=country(raw['Country']);website=raw.get('Website','')
            safe=website if url_valid(website) else source_url;h=(urlsplit(website).hostname or '').removeprefix('www.') if url_valid(website) else ''
            nm=names.get(normalized(name),set());hm=hosts.get(h,set()) if h not in SHARED_HOSTS else set();compatible=hm&nm if nm else hm
            resolved=next(iter(compatible)) if len(compatible)==1 else None
            key=digest([normalized(name),place])[:28];cid=resolved or 'gamedb-org-'+digest([normalized(name),h or place])[:24]
            sectors=[]
            if 'Studio' in raw['Type']:sectors.append('Game Development')
            if 'Publisher' in raw['Type']:sectors.append('Game Publishing')
            output.append({'id':'gamedb-'+key,'company_id':cid,'name':name,'city':'','country':place,'lat':None,'lng':None,
                'website':safe,'website_kind':'official' if safe==website else 'source_listing','categories':sectors,'capabilities':[],'capability_evidence':{},
                'evidence_state':'unknown','evidence_class':'C','verified_on':'','source_observed_on':observed,'evidence':source_url,'coordinate_precision':'unverified',
                'coordinate_source':source_url,'location_type':'uncertain','relationships':[],'record_kind':'company_reference','identity_status':'matched_existing' if resolved else 'source_provisional',
                'status':'Company reference, not a verified physical branch or production facility. Source classifications and operating-status labels require current research. No map point is invented.',
                'license':'UNSPECIFIED','attribution':'EddieWing / Game Studios & Publishers Database. Factual company references projected; authored descriptions omitted. Source README offers download/local use; no explicit dataset redistribution licence is stated.',
                'research_reasons':['Company-level listing; cities, physical branches and facility capabilities unverified.','Source provides no explicit dataset redistribution licence; factual reference fields only, no authored descriptions.'],
                'potential_duplicates':[],'source_status':raw.get('Status','not supplied'),'source_type':raw['Type'],'source_category':'company-level games classification','source_release':sha(path),
                'source_provenance':[{'source_id':'game-studios-db','source_record_id':'csv-row-'+str(number),'url':source_url,'license':'UNSPECIFIED','license_url':'https://github.com/EddieWing/gamedev-studios-db#using-it','observed_on':observed,'observation_hash':digest({k:raw.get(k) for k in ('Name','Type','Country','Website','Status')})}]})
    return output

def build(snapshot,company_csv,output,base_path=ROOT/'studios.json',config_path=ROOT/'data/bulk/sources.json',observed=None,company_source=None):
    output=Path(output)
    if output.exists():raise ValueError('fresh proposal directory required')
    base=read(base_path);errors,warnings=validate(base)
    if errors:raise ValueError('invalid retained baseline')
    observed=observed or date.today().isoformat()
    company_source=company_source or 'https://github.com/EddieWing/gamedev-studios-db/blob/main/data/companies.csv'
    with tempfile.TemporaryDirectory() as tmp:
        review=Path(tmp)/'review';report=ingest(snapshot,review,read(config_path),base)
        if not report['acquisition_complete']:raise ValueError('complete source snapshot required for this combined release')
        new=[]
        with (review/'candidates.jsonl').open() as stream:
            for line in stream:new.append(observation(json.loads(line),{r['company_id'] for r in base}))
    game=companies(company_csv,base,observed,company_source);new+=game
    errors=validate_research(new)
    if errors:raise ValueError('invalid research records: '+str(errors[:8]))
    if {r['id'] for r in new}&{r['id'] for r in base}:raise ValueError('source ID collides with retained location')
    output.mkdir(parents=True);(output/'shards').mkdir();groups=defaultdict(list)
    for row in new:groups[row['country']].append(row)
    index=[];shards={}
    for place,rows in sorted(groups.items()):
        rows.sort(key=lambda r:r['id']);key=digest(place)[:12]
        for offset in range(0,len(rows),500):
            chunk=rows[offset:offset+500];name=f'shards/{key}-{offset//500:03d}.json';compact(output/name,chunk)
            shards[name]={'sha256':sha(output/name),'gzip_sha256':sha(output/(name+'.gz')),'gzip_bytes':(output/(name+'.gz')).stat().st_size,'records':len(chunk),'country':place,'bytes':(output/name).stat().st_size}
            for r in chunk:index.append([r[k] for k in ('id','company_id','name','city','country','lat','lng','categories')]+[name,r['source_observed_on'],r['identity_status'],r['evidence_class'],r['record_kind']])
    index.sort(key=lambda r:r[0]);compact(output/'index.json',index)
    active=[{**r,'evidence_class':'A' if r['evidence_state']=='confirmed' else 'C','record_kind':'retained_location'} for r in base]+new
    classes=Counter(r['evidence_class'] for r in active);countries={r['country'] for r in active if r['country']}
    manifest={'version':1,'mode':'unified_research','review_mode':'manual_human_pr_review','publication_approved':False,
        'baseline':{'path':'./studios.json','sha256':sha(base_path),'retained_records':len(base),'active_ids':[r['id'] for r in base],'eligible_ids':[r['id'] for r in base if r['evidence_state']=='confirmed'],'research_only_ids':[]},
        'index':{'path':'index.json','sha256':sha(output/'index.json'),'gzip_sha256':sha(output/'index.json.gz'),'gzip_bytes':(output/'index.json.gz').stat().st_size,'records':len(index),'bytes':(output/'index.json').stat().st_size},'shards':shards,
        'index_columns':['id','company_id','name','city','country','lat','lng','categories','detail_shard','source_observed_on','identity_status','evidence_class','record_kind'],
        'source_policy_hash':digest(read(config_path)),'research_run_id':report['run_id'],'licence_files':{p.name:{'sha256':sha(p)} for p in sorted((ROOT/'data/bulk/LICENSES').glob('*.txt'))},
        'counts':{'records':len(active),'public_records':len(active),'class_a':classes['A'],'class_b':classes['B'],'class_c':classes['C'],'retained_locations':len(base),'source_location_observations':len(new)-len(game),'company_references':len(game),'records_with_coordinates':sum(type(r.get('lat')) in (float,int) and type(r.get('lng')) in (float,int) for r in active),'countries':len(countries),'retained_operating_organisations':len({r['company_id'] for r in base}),'source_identities':len({r['company_id'] for r in new})},
        'warning_meaning':'All source records are accessible in one research directory. Record totals are not verified unique studio/facility counts. Source status/type/sector are claims; company references have no invented coordinates. Existing curated evidence is preserved.'}
    manifest['warnings']={'canonical_baseline':len(warnings),'unreviewed_new_references':len(new),'source_point_precision_unverified':sum(r['record_kind']=='source_location' for r in new),'company_references_without_coordinates':len(game),'unspecified_company_source_terms':len(game),'source_records_missing_city':sum(r['record_kind']=='source_location' and not r['city'] for r in new),'source_records_missing_country':sum(r['record_kind']=='source_location' and not r['country'] for r in new),'possible_duplicate_candidates':report['potential_existing_duplicates']}
    add_transport(output,base_path,manifest,index,new)
    write(output/'manifest.json',manifest)
    write(output/'audit.json',{'retained_baseline_sha256':sha(base_path),'retained_ids':[r['id'] for r in base],'source_observations':report['raw_source_records'],'company_csv_sha256':sha(company_csv),'company_reference_ids':[r['id'] for r in game],'record_classes':dict(classes),'source_research_report':report,'validation_errors':0,'baseline_warnings':warnings,'new_verified_capability_claims':0,'policy':'User-directed inclusive research view; no candidate is silently promoted to verified, no source closure is applied to a reviewed record, no company is given fabricated coordinates.'})
    return manifest,new

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--snapshots',type=Path,required=True);p.add_argument('--companies',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--observed-on');p.add_argument('--company-source');a=p.parse_args()
    manifest,_=build(a.snapshots,a.companies,a.output,observed=a.observed_on,company_source=a.company_source);print(json.dumps(manifest['counts'],indent=2))
if __name__=='__main__':main()
