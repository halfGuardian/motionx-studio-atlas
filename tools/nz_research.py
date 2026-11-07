#!/usr/bin/env python3
"""Evidence-led continuation of NZ Wave 1. Prepare references, never approve them.

All source rows retain outcomes. Programme presence, failed fetches, domains and
agent decisions do not establish a current physical studio or human approval.
"""
import argparse,copy,csv,hashlib,html,json,re,tempfile
from collections import Counter,defaultdict
from pathlib import Path
from datetime import date
from discovery import ROOT,read,write,digest
from launch_readiness import records
from boutique import host,record_host,shared,relevance,region
from annecy_match import IdentityIndex,key
from nz_census import load_observations,ALIASES,fold
from bulk_catalog import compact,sha
from compact_index import add_transport
from unified_catalog import validate_research
from validate import url_valid

HOME=ROOT/'data/nz-census';PREFIX='nzcensus-';GRANT='NZ-On-Air-Permission'
DECISIONS={'represented','represented_alias','represented_company_geography_pending','new_reference','duplicate_observation','identity_hold','unresolved','out_of_scope','reported_nz_closure'}


def source_inputs(home=HOME):
    registry=read(home/'sources.json');policies={s['id']:s for s in registry['sources']}
    if registry['automatic_collection'] is not False:raise ValueError('No collector enablement is authorised')
    _,old=load_observations();gov=read(home/'inputs/gdsr.json');observations=[dict(r,source_period='',origin='historical_wave1') for r in old]
    if Counter(r['source_period'] for r in gov['records'])!={'2026':43,'2025':40,'2024':33}:raise ValueError('Incomplete published programme sections')
    if gov['license']!=GRANT or policies['nzonair-gdsr']['permission']!='accurate_attributed_reproduction_permitted':raise ValueError('Source permission checkpoint mismatch')
    for r in gov['records']:
        observations.append({'observation_id':'nzonair-gdsr:'+r['id'],'source_id':'nzonair-gdsr','name':r['name'],'service_labels':r['labels'],'source_url':r['source_url'],'detail_url':'','site_url':'','location_claim':r['location_claim'],'observed_on':gov['observed_on'],'source_scope':gov['completeness'],'source_period':r['source_period'],'origin':'permitted_programme_projection'})
    observations += read(home/'inputs/regional-leads.json')['records']
    assessments={}
    for r in read(home/'inputs/assessments.json')['records']:
        k=fold(r['source_name'])
        if k in assessments:raise ValueError('Conflicting assessment keys')
        if r['human_approved'] is not False or r['claim_scope']!='company_only' or r['claims_state'] not in ('source_supported_unverified','unknown'):raise ValueError('Research cannot grant verification/approval')
        for u in r['evidence_urls']+r['identity_evidence_urls']:
            if not url_valid(u) or 'filmotagosouthland.com' in u:raise ValueError('Unsafe or restricted new acquisition evidence')
        if r['official_url'] and not url_valid(r['official_url']):raise ValueError('Unsafe official URL')
        if date.fromisoformat(r['observed_on']).isoformat()!=r['observed_on']:raise ValueError('Invalid actual review date')
        assessments[k]=r
    historical_ids={o['observation_id'] for o in old}
    ids=[o['observation_id'] for o in observations]
    if len(ids)!=len(set(ids)) or len(old)!=98:raise ValueError('Source continuity/identity failure')
    for o in observations:
        if not url_valid(o['source_url']) or not o['service_labels'] or o['source_id'] not in policies:raise ValueError('Invalid source observation')
        permission=policies[o['source_id']]['permission']
        if permission in ('commercial_reuse_restricted','written_consent_required','permission_pending') and o['observation_id'] not in historical_ids:raise ValueError('Restricted source cannot create new roster observations')
    for sid,policy in policies.items():
        if not url_valid(policy['url']) or not url_valid(policy['license_url']):raise ValueError('Unsafe source policy URL')
        if policy['access_audit']['enumerated_rows']!=sum(o['source_id']==sid for o in observations):raise ValueError('Source enumeration audit count mismatch')
    return registry,policies,observations,assessments


class NZIdentityIndex(IdentityIndex):
    """Index provenance once; provenance is a review lead, never a merge key."""
    def __init__(self, rows):
        super().__init__(rows)
        self.provenance = defaultdict(set)
        for row in rows:
            for p in row.get('source_provenance', []):
                self.provenance[(p.get('source_id'), p.get('source_record_id'))].add(row['id'])


def enumeration_eligible(access, permission):
    """A complete snapshot needs coherent, stable, authorised enumeration.

    Conflicting overlapping page fragments cannot be combined by line offset.
    A zero-result widget does not prove a directory empty. This only evaluates
    the declared roster, not independent operation or whole-region recall.
    """
    return (permission == 'accurate_attributed_reproduction_permitted'
            and access.get('declared_complete') is True
            and access.get('stable_snapshot') is True
            and access.get('unavailable_pages', 0) == 0
            and access.get('overlap_conflicts', 0) == 0
            and access.get('enumerated_rows', 0) > 0
            and access.get('expected_rows') == access.get('enumerated_rows'))


def identity(index,o,a=None):
    aliases=[o['name']]+list((a or {}).get('aliases',[]))+list(ALIASES.get(fold(o['name']),()))
    name=(a or {}).get('operating_name') or o['name'];website=(a or {}).get('official_url') or o.get('site_url','')
    first=index.match(name,'New Zealand',website,aliases)
    # A source-backed operating-name variant can retain an old identity even
    # after an official-domain change. This does not overwrite the old record.
    plain=index.match(name,'New Zealand','',aliases)
    if a and a['decision']=='existing' and plain['match_status']=='name_and_country':first=plain
    candidates=first['record_ids'];nz=[rid for rid in candidates if index.rows[rid]['country']=='New Zealand'];foreign=[rid for rid in candidates if index.rows[rid]['country'] and index.rows[rid]['country']!='New Zealand'];unknown=[rid for rid in candidates if not index.rows[rid]['country']]
    source_key=o['observation_id'].split(':',1)[-1]
    provenance=set().union(*(index.provenance.get((o['source_id'], k), set()) for k in (o['observation_id'], source_key, source_key.removeprefix('nzfc-'))))
    return {**first,'provenance_candidate_ids':sorted(provenance),'nz_ids':nz,'foreign_ids':foreign,'unknown_country_ids':unknown,'aliases_considered':aliases,'official_domain':host(website)}


def make_reference(o,a,policy,entity_key):
    rid=PREFIX+digest(entity_key)[:28];company=PREFIX+'org-'+digest(entity_key)[:24]
    name=a['operating_name'] if a else o['name'];gov=o['source_id']=='nzonair-gdsr';evidence=o['source_url'] if gov else a['evidence_urls'][0]
    site=(a or {}).get('official_url') or evidence
    labels=o['service_labels'] if gov else (a or {})['company_service_claims'];license=policy['license'] if gov else 'UNSPECIFIED'
    return {'id':rid,'company_id':company,'name':name,'city':'','country':'New Zealand','lat':None,'lng':None,'website':site,'website_kind':'official' if (a or {}).get('official_url') else 'source_listing','categories':['Game Development'] if gov else a['sectors'],'capabilities':[],'capability_evidence':{},'evidence_state':'unknown','evidence_class':'C','verified_on':'','source_observed_on':o['observed_on'],'evidence':evidence,'coordinate_precision':'unverified','coordinate_source':evidence,'location_type':'uncertain','relationships':[],'record_kind':'company_reference','identity_status':'source_provisional','status':'Source-supported Class C company reference associated with New Zealand. Current physical facilities, technical services, ownership and current operation have not been independently verified. No facility pin or capture-stage claim is created.','license':license,'attribution':'Copyright © NZ On Air. Accurate factual company-name/programme-year projection, source acknowledged; no endorsement. Permission applies to this scoped agency projection, not third-party websites or detailed service claims.' if gov else 'MotionX company research: minimal factual reference to the linked company/official source, reviewed '+o['observed_on']+'. Source-wide reuse terms not established; no authored prose, media or contacts reproduced.','research_reasons':['Company identity representation is separate from verified NZ facility coverage.','Programme eligibility is historical/period-specific evidence, not proof of present operation.' if gov else 'Company self-report/source listing is not independent technical verification.','No source-wide rights are inferred from public availability.','Original source service labels are preserved in the census reconciliation, not promoted to confirmed capabilities.'],'potential_duplicates':[],'source_status':'source-supported; current independent operation verification unknown','source_type':'NZ company research reference','source_category':json.dumps(({o['source_id']:o['service_labels']} if gov else ({'company_page':labels} if policy['permission']=='commercial_reuse_restricted' else {o['source_id']:o['service_labels'],'company_page':labels})),ensure_ascii=False,sort_keys=True),'source_release':digest([o,a]),'source_provenance':[{'source_id':o['source_id'] if gov else 'nz-company-primary-review','source_record_id':o['observation_id'],'url':evidence,'license':license,'license_url':policy['license_url'] if gov else evidence,'observed_on':o['observed_on'],'observation_hash':digest([o,a])}]}


def build(base,home=HOME):
    registry,policies,obs,assessments=source_inputs(home);index=NZIdentityIndex(base);new=[];out=[];entities={};profiles={};facility=[]
    base_ids={r['id'] for r in base}
    for o in obs:
        a=assessments.get(fold(o['name']));m=identity(index,o,a);before=identity(index,o);result={**o,'before_match':before,'matching':m,'assessment':a,'disposition':'unresolved','record_ids':[],'reason':'Current operating identity, relevance or active-operation evidence remains unresolved.','confidence':'low','new_reference':False,'human_reviewed':False,'nz_facility_verified':False}
        nz_orgs={index.rows[i]['company_id'] for i in m['nz_ids']}
        credible=(a and a['decision'] in ('qualified','existing')) or (o['source_id']=='nzonair-gdsr' and o['source_period']=='2026')
        operating=(a or {}).get('operating_name') or o['name'];site=(a or {}).get('official_url','');entity_key=[key(operating),host(site) if site and not shared(host(site)) else 'nz-source-identity'];prior=entities.get(digest(entity_key))
        if a and a['decision'] in ('hold','reported_nz_closure','out_of_scope'):
            status={'hold':'identity_hold','reported_nz_closure':'reported_nz_closure','out_of_scope':'out_of_scope'}[a['decision']];result.update(disposition=status,reason=a['reason'],record_ids=m['nz_ids'],confidence='medium' if a['evidence_urls'] else 'low')
        elif m['nz_ids'] and len(nz_orgs)==1 and m['match_status'] in ('name_and_country','name_and_domain'):
            result.update(disposition='represented_alias' if a and a['aliases'] or any(fold(x)!=fold(o['name']) for x in m['aliases_considered']) else 'represented',record_ids=m['nz_ids'],reason=m['reason']+' Representation does not independently establish current operation or a facility.',confidence=m['confidence'])
        elif m['nz_ids']:
            result.update(disposition='identity_hold',record_ids=m['nz_ids'],reason='Multiple NZ identities or conflicting official names/domains require review; no overwrite or automatic merge.')
        elif m['provenance_candidate_ids'] and not m['nz_ids']:
            result.update(disposition='identity_hold',record_ids=m['provenance_candidate_ids'],reason='Existing source provenance refers to a differently named/geographic identity. Resolve that lineage before creating a new reference; no automatic merge.')
        elif m['unknown_country_ids'] and m['match_status']=='name_and_domain':
            result.update(disposition='represented_company_geography_pending',record_ids=m['unknown_country_ids'],reason='Name and official domain agree with an existing company reference; its NZ facility geography remains unestablished.',confidence='medium')
        elif m['unknown_country_ids'] or m['match_status'] in ('possible_alias','shared_domain_review'):
            result.update(disposition='identity_hold',reason=m['reason']+' Geography/operating-brand identity must be resolved before an addition.')
        elif m['foreign_ids'] and m['match_status']=='name_and_domain':
            result.update(disposition='represented_company_geography_pending',record_ids=m['foreign_ids'],reason='Compatible company name and official domain exist abroad. NZ facility remains unestablished; no foreign address/coordinates are transferred.',confidence='medium')
        elif prior:
            p=make_reference(o,a,policies[o['source_id']],entity_key)['source_provenance'][0]
            if p not in prior['source_provenance']:prior['source_provenance'].append(p)
            labels=json.loads(prior['source_category']);bucket=labels.setdefault(o['source_id'],[])
            if policies[o['source_id']]['permission']!='commercial_reuse_restricted':
                for label in o['service_labels']:
                    if label not in bucket:bucket.append(label)
            prior['source_category']=json.dumps(labels,ensure_ascii=False,sort_keys=True)
            result.update(disposition='duplicate_observation',record_ids=[prior['id']],reason='Same proposed operating identity already represented by another source/year. Every observation and its original labels remain in this audit.',confidence='medium')
        elif credible:
            # Foreign exact names are collision leads. New provisional identity
            # needs NZ evidence and a reviewed explanation; never move the pin.
            if m['foreign_ids'] and not (a and a['decision']=='qualified' and a['official_url']):
                result.update(disposition='identity_hold',reason='Foreign-only name collision; programme country alone cannot resolve brand/branch identity.')
            else:
                name=(a or {}).get('operating_name') or o['name'];site=(a or {}).get('official_url','');entity_key=[key(name),host(site) if site and not shared(host(site)) else 'nz-source-identity'];ek=digest(entity_key)
                if ek in entities:
                    row=entities[ek];result.update(disposition='duplicate_observation',record_ids=[row['id']],reason='Another source/year already resolves to this proposed company reference; every source observation is retained.',confidence='medium')
                    p=make_reference(o,a,policies[o['source_id']],entity_key)['source_provenance'][0]
                    if p not in row['source_provenance']:row['source_provenance'].append(p)
                else:
                    row=make_reference(o,a,policies[o['source_id']],entity_key)
                    if row['id'] in base_ids:raise ValueError('Reference extension collision')
                    if m['foreign_ids']:row['potential_duplicates']=[{'ids':m['foreign_ids'],'reasons':['Foreign-only name collision; do not merge or transfer NZ facility evidence.']}]
                    entities[ek]=row;new.append(row);result.update(disposition='new_reference',record_ids=[row['id']],new_reference=True,reason=(a or {}).get('reason') or 'Current published 2026 agency programme supports a provisional company-name/NZ sector association. No detailed services, active operation or physical branch independently established.',confidence='medium')
                if a:
                    signals,_=relevance(row['name'],a['company_service_claims'])
                    if signals:profiles[row['id']]={'record_id':row['id'],'name':row['name'],'country':'New Zealand','region':'Oceania','signals':signals,'research_terms':a['company_service_claims']+a['aliases'],'sources':[{'url':u,'observed_on':a['observed_on'],'basis':'official_company' if u==a['official_url'] else 'official_regional_source'} for u in a['evidence_urls']],'size_claim':'Unknown','size_reviewed_on':'','independence':'unknown','external_support_need':'unknown','purchasing_intent':'unknown','research_status':'primary_claims_reviewed' if a['official_url'] else 'source_listed_research','source_supported_location':False,'score':sum(signals.values())}
        else:
            result.update(reason='Historical programme/showreel/listing or unconfirmed identity requires current research; absence from newer lists is never a closure signal.')
        out.append(result)
    # Fold programme-year aliases only when evidence explicitly supports them;
    # otherwise source-name ambiguity stays visible rather than hiding rows.
    errors=validate_research(new)
    if errors:raise ValueError(str(errors[:8]))
    for name,city,typ in [('Avalon Studios','Lower Hutt','production_studios'),('Lane Street Studios','Upper Hutt','production_studios'),('Stone Street Studios','Wellington','sound_stages')]:
        matches=[r for r in out if r['name']==name];a=assessments[fold(name)]
        facility.append({'proposal_id':'nz-facility-'+digest(name)[:20],'name':name,'operating_record_ids':sorted({i for r in matches for i in r['record_ids']}),'source_supported_city':city,'country':'New Zealand','location_type_claim':typ,'coordinate_precision':'unverified','lat':None,'lng':None,'evidence_urls':a['evidence_urls']+sorted({r['source_url'] for r in matches}),'reviewed_on':'2026-11-07','status':'source_supported_proposal_pending_independent_human_review','independent_facility_review':'not_completed','publication_approved':False,'notes':'Region marketing label does not replace actual municipality. No new pin, address or Class A promotion.'})
    facility.append({'proposal_id':'nz-facility-'+digest('Te Whare Piringa')[:20],'name':'Te Whare Piringa Film Studio','operating_record_ids':[],'operator_source_claim':'Local Gecko Productions','source_supported_city':'Rotorua','country':'New Zealand','location_type_claim':'production_studios','coordinate_precision':'unverified','lat':None,'lng':None,'evidence_urls':['https://filmbayofplenty.com/why-film-in-the-bay-of-plenty/film-studios-production-hubs/'],'reviewed_on':'2026-11-07','status':'source_supported_proposal_pending_independent_human_review','independent_facility_review':'not_completed','publication_approved':False,'notes':'Multiple rooms in one featured facility do not establish multiple companies. Operator and facility evidence need review; no capture-stage claim or map pin.'})
    source_counts={s['id']:{'name':s['name'],'source_url':s['url'],'completeness':s['scope'],'permission':s['permission'],'observations':sum(o['source_id']==s['id'] for o in obs),'outcomes':dict(sorted(Counter(r['disposition'] for r in out if r['source_id']==s['id']).items())),'limitation':s['detail'],'reviewed_on':registry['reviewed_on'],'enumeration_audit':s['access_audit'],'eligible_complete_reusable_snapshot':enumeration_eligible(s['access_audit'],s['permission'])} for s in registry['sources']}
    represented_ids={i for r in out if r['disposition'] in ('represented','represented_alias','represented_company_geography_pending') for i in r['record_ids'] if i in index.rows}
    unresolved_names={fold(r['name']) for r in out if r['disposition'] in ('identity_hold','unresolved')}
    summary={'baseline_records_examined':len(base),'source_observations':len(obs),'distinct_normalised_source_names':len({fold(o['name']) for o in obs}),'outcomes':dict(sorted(Counter(r['disposition'] for r in out).items())),'existing_companies_reconciled':len({index.rows[i]['company_id'] for i in represented_ids}),'existing_record_ids_reconciled':len(represented_ids),'new_class_c_company_references':len(new),'new_map_points':0,'new_verified_capability_claims':0,'unresolved_source_name_keys':len(unresolved_names),'reported_nz_closure_identities':len({key((r['assessment'] or {}).get('operating_name') or r['name']) for r in out if r['disposition']=='reported_nz_closure'}),'reported_nz_closure_name_keys':len({fold(r['name']) for r in out if r['disposition']=='reported_nz_closure'}),'independently_human_reviewed_facilities':0,'source_supported_facility_proposals':len(facility),'human_precision':None,'publication_approved':False,'census_complete':False,'sources':source_counts,'limitations':['All additions are provisional company references, not verified active physical studios.','Four Auckland pages are partial coverage; Wellington full directory remains unavailable.','Otago/Southland commercial reuse and Waikato written-consent restrictions stop new roster projection.','VFXG 45-business list remains unobtained; no roster reconstruction or email outreach.','116 permitted government rows span three programme years; neither eligibility nor presence proves present operation.','No human precision/facility review or source-wide rights approval is fabricated.']}
    return {'version':2,'summary':summary,'observations':out,'proposed_references':new,'profiles':profiles,'facility_proposals':facility,'baseline_ids_sha256':digest(sorted(r['id'] for r in base))}


def extend(public,database,home=HOME):
    public=Path(public);m,base=records(public,database)
    if len(base)!=42239 or any(r['id'].startswith(PREFIX) for r in base):raise ValueError('Fresh reproduced 42,239-record baseline required; repeated application refused')
    report=build(base,home);new=report['proposed_references'];report['before_counts']=copy.deepcopy(m['counts']);report['retained_shard_hashes']={n:d['sha256'] for n,d in m['shards'].items()};report['retained_baseline_sha256']=sha(database)
    index=read(public/'index.json');name='shards/'+digest('nz-census-v15')[:12]+'-000.json'
    if (public/name).exists():raise ValueError('Append target already exists')
    compact(public/name,sorted(new,key=lambda r:r['id']));m['shards'][name]={'sha256':sha(public/name),'gzip_sha256':sha(public/(name+'.gz')),'gzip_bytes':(public/(name+'.gz')).stat().st_size,'records':len(new),'country':'New Zealand','bytes':(public/name).stat().st_size}
    for r in new:index.append([r[k] for k in ('id','company_id','name','city','country','lat','lng','categories')]+[name,r['source_observed_on'],r['identity_status'],r['evidence_class'],r['record_kind']])
    index.sort(key=lambda r:r[0]);compact(public/'index.json',index);m['index'].update(sha256=sha(public/'index.json'),gzip_sha256=sha(public/'index.json.gz'),gzip_bytes=(public/'index.json.gz').stat().st_size,records=len(index),bytes=(public/'index.json').stat().st_size)
    for k in ('records','public_records','class_c','company_references'):m['counts'][k]+=len(new)
    m['counts']['source_identities']=len({r['company_id'] for r in base+new if r['record_kind']!='retained_location'})
    for k in ('company_references_without_coordinates','unreviewed_new_references'):m['warnings'][k]+=len(new)
    m['warnings']['unspecified_company_source_terms']+=sum(r['license']=='UNSPECIFIED' for r in new);m['warnings']['nz_census_references_requiring_review']=len(new);m['warnings']['nz_census_foreign_name_collisions']=sum(bool(r['potential_duplicates']) for r in new);m['warnings']['possible_duplicate_candidates']+=m['warnings']['nz_census_foreign_name_collisions']
    advisory=read(public/'boutique.json');advisory['profiles'].update(report['profiles']);advisory['nz_census_summary']={k:v for k,v in report['summary'].items() if k!='sources'};compact(public/'boutique.json',advisory);m['boutique'].update(sha256=sha(public/'boutique.json'),gzip_sha256=sha(public/'boutique.json.gz'),gzip_bytes=(public/'boutique.json.gz').stat().st_size)
    m['licence_files']={p.name:{'sha256':sha(p)} for p in sorted((ROOT/'data/bulk/LICENSES').glob('*.txt'))};add_transport(public,database,m,index,[r for r in base+new if r['record_kind']!='retained_location']);write(public/'manifest.json',m)
    report['after_counts']=copy.deepcopy(m['counts']);return report


def safe_csv(v):
    if isinstance(v,(list,dict)):v=json.dumps(v,ensure_ascii=False,sort_keys=True)
    s=str(v or '');return "'"+s if s.lstrip().startswith(('=','+','-','@','\t','\r')) else s


def save(report,output):
    output=Path(output);output.mkdir(parents=True,exist_ok=True)
    audit={k:v for k,v in report.items() if k not in ('proposed_references','profiles')};write(output/'reconciliation.json',dict(sorted(audit.items())));write(output/'summary.json',report['summary']);write(output/'proposals.json',{'human_approved':False,'canonical_updates':[],'company_references':report['proposed_references'],'facility_evidence_proposals':report['facility_proposals']})
    fields=['observation_id','source_id','name','source_period','service_labels','disposition','record_ids','confidence','reason','source_url','observed_on']
    with (output/'reconciliation.csv').open('w',encoding='utf-8',newline='') as f:
        w=csv.writer(f,lineterminator='\n');w.writerow(fields)
        for r in report['observations']:w.writerow([safe_csv(r.get(k,'')) for k in fields])
    sample=sorted(report['observations'],key=lambda r:digest(r['observation_id']));selected=[]
    for status in sorted(DECISIONS):selected += [r for r in sample if r['disposition']==status][:4]
    write(output/'human-review.json',{'reviewed':0,'precision':None,'publication_approved':False,'content_sha256':sha(output/'reconciliation.json'),'method':'Deterministic stratified pending worksheet. Agent source assessments and automated tests are not human approval. Historical Annecy worksheet remains separate and pending.','rows':[{'observation_id':r['observation_id'],'name':r['name'],'content_hash':digest(r),'decision':None,'reviewer':None,'status':'pending_human_review'} for r in selected]})
    esc=html.escape
    source_rows=''.join('<tr><th scope="row"><a href="'+esc(s['source_url'],quote=True)+'">'+esc(s['name'])+'</a></th><td>'+esc(s['completeness'])+'</td><td>'+str(s['observations'])+'</td><td>'+esc(s['permission'])+'</td><td>'+esc(s['limitation'])+'</td></tr>' for s in report['summary']['sources'].values())
    rows=[]
    for r in sorted(report['observations'],key=lambda r:(r['source_id'],r['name'],r['source_period'])):
        a=r['assessment'] or {};links=' · '.join('<a href="'+esc(u,quote=True)+'" rel="noopener noreferrer">Evidence</a>' for u in [r['source_url']]+a.get('evidence_urls',[]));profiles=' · '.join('<a href="../../../index.html#/location/'+esc(i,quote=True)+'">'+esc(i)+'</a>' for i in r['record_ids'])
        rows.append('<tr data-status="'+esc(r['disposition'],quote=True)+'" data-source="'+esc(r['source_id'],quote=True)+'"><td>'+esc(r['name'])+'<br>'+esc(r['source_id']+' '+r['source_period'])+'</td><td>'+esc(', '.join(r['service_labels']))+'</td><td>'+esc(r['disposition'])+'<br>'+esc(r['confidence'])+'</td><td>'+esc(r['reason'])+'<br>'+profiles+'</td><td>'+links+'<br>Observed '+esc(r['observed_on'])+'</td></tr>')
    totals=report['summary']
    overview='<p><strong>'+str(totals['source_observations'])+' observations · '+str(totals['distinct_normalised_source_names'])+' source-name keys · '+str(totals['existing_companies_reconciled'])+' existing company identities reconciled · '+str(totals['new_class_c_company_references'])+' proposed Class C references · '+str(totals['unresolved_source_name_keys'])+' unresolved source identities</strong></p><p>Reviewed 7 November 2026. '+str(totals['reported_nz_closure_identities'])+' reported NZ office closure identity requires investigation; no record is deleted. '+str(totals['source_supported_facility_proposals'])+' source-supported facility proposals; 0 independent human facility reviews; approval pending. Countries on company references are source associations, not geocoded facilities.</p>'
    facilities='<h2>Separate facility evidence proposals</h2><ul>'+''.join('<li>'+esc(f['name'])+' · '+esc(f['source_supported_city'])+' · '+esc(f['status'].replace('_',' '))+' · '+ ' · '.join('<a href="'+esc(u,quote=True)+'">Evidence</a>' for u in f['evidence_urls'])+'</li>' for f in report['facility_proposals'])+'</ul>'
    page='''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>MotionX — NZ coverage and evidence review</title><style>body{background:#101822;color:#edf1f8;font:16px/1.6 system-ui;max-width:1450px;margin:auto;padding:22px;overflow-wrap:anywhere}a{color:#addcff}table{border-collapse:collapse;width:100%}td,th{border:1px solid #43516a;padding:10px;text-align:left;vertical-align:top;overflow-wrap:anywhere}input,select{background:#172333;color:inherit;padding:12px;min-height:44px;border:1px solid #8798ad;font:inherit;max-width:100%}label{display:inline-block;margin:8px;max-width:calc(100% - 16px)}input,select{box-sizing:border-box}a:focus-visible,input:focus-visible,select:focus-visible{outline:3px solid #ffd77a}pre{white-space:pre-wrap;overflow-wrap:anywhere}tr[hidden]{display:none}@media(max-width:700px){body{padding:12px}table,tbody,tr,td{display:block}thead{display:none}th{display:block}}</style><h1>New Zealand coverage · evidence and identity resolution</h1><p>This census is incomplete. Company references, source geographic claims and independently verified facilities are separate measures. Every addition is Class C, without a new map pin or confirmed capability. A current source or programme listing is not independent operation verification.</p><p><a href="../../../index.html">Atlas</a> · <a href="reconciliation.json">Full JSON audit</a> · <a href="reconciliation.csv">CSV</a> · <a href="proposals.json">References and facility proposals</a> · <a href="human-review.json">Pending human review</a></p>''' + overview + '''<details><summary>Counts, source scope and limitations</summary><pre>'''+esc(json.dumps(report['summary'],ensure_ascii=False,indent=2))+'''</pre></details><h2>Every source assessed</h2><table><thead><tr><th>Source</th><th>Completeness</th><th>Observed rows</th><th>Rights</th><th>Limits and next work</th></tr></thead><tbody>'''+source_rows+'''</tbody></table>''' + facilities + '''<h2>Every retained observation</h2><p>Original service labels are preserved as source assertions. Foreign/global record links do not establish NZ facilities. Profile links require this matching checkout served over HTTP.</p><label>Name, source or reason <input id="q" type="search"></label><label>Source <select id="source"><option value="">All sources</option>'''+''.join('<option value="'+esc(k)+'">'+esc(v['name'])+'</option>' for k,v in report['summary']['sources'].items())+'''</select></label><label>Outcome <select id="state"><option value="">All outcomes</option>'''+''.join('<option>'+s+'</option>' for s in sorted(DECISIONS))+'''</select></label><p id="count" role="status" aria-live="polite"></p><table><thead><tr><th>Company / source period</th><th>Original labels</th><th>Outcome / confidence</th><th>Identity and next work</th><th>Evidence / review date</th></tr></thead><tbody id="observations">'''+''.join(rows)+'''</tbody></table><script src="../../../nz-review.js"></script></html>'''
    (output/'coverage.html').write_text(page,encoding='utf-8')


def checkpoint(home=HOME):
    config=read(home/'release.json')
    if sha(ROOT/'data/coverage/nzfc-2026-11-07.json')!=config['historical_nzfc_sha256']:raise ValueError('Historical NZFC snapshot changed')
    for name,expected in config['input_hashes'].items():
        p=Path(name)
        if p.is_absolute() or '..' in p.parts or sha(home/p)!=expected:raise ValueError('NZ research checkpoint changed: '+name)
    return config


def check(home=HOME,output=None):
    config=checkpoint(home);m,all_rows=records(ROOT/'data/public',ROOT/'studios.json');base=[r for r in all_rows if not r['id'].startswith(PREFIX)];report=build(base,home)
    if len(base)!=42239 or report['baseline_ids_sha256']!=config['baseline_ids_sha256']:raise ValueError('Original 42,239 identities changed')
    if sha(ROOT/'studios.json')!=config['retained_baseline_sha256'] or m['counts']!=config['after_counts']:raise ValueError('Retained baseline or release totals changed')
    for n,h in config['retained_shard_hashes'].items():
        if sha(ROOT/'data/public'/n)!=h:raise ValueError('Retained evidence shard overwritten')
    if {r['id']:r for r in all_rows if r['id'].startswith(PREFIX)}!={r['id']:r for r in report['proposed_references']}:raise ValueError('Reference proposal differs from catalogue')
    report.update(before_counts=config['before_counts'],after_counts=m['counts'],retained_shard_hashes=config['retained_shard_hashes'],retained_baseline_sha256=config['retained_baseline_sha256'])
    with tempfile.TemporaryDirectory() as t:
        save(report,Path(t))
        for p in Path(t).iterdir():
            if p.read_bytes()!=(Path(output or home/'reports')/p.name).read_bytes():raise ValueError('Stale NZ report: '+p.name)
    return report


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('command',choices=('prepare','check'));p.add_argument('--output',type=Path,default=HOME/'reports');a=p.parse_args()
    if a.command=='prepare':
        report=extend(ROOT/'data/public',ROOT/'studios.json');save(report,a.output);paths=[HOME/'sources.json',*sorted((HOME/'inputs').glob('*.json'))];write(HOME/'release.json',{'version':1,'base_pr_commit':'2197b340723ab3c40cdb03c1d67ec29ea304f17d','input_hashes':{str(p.relative_to(HOME)):sha(p) for p in paths},**{k:report[k] for k in ('before_counts','after_counts','baseline_ids_sha256','retained_shard_hashes','retained_baseline_sha256')},'historical_nzfc_sha256':sha(ROOT/'data/coverage/nzfc-2026-11-07.json'),'publication_approved':False})
    else:report=check(output=a.output)
    print(json.dumps(report['summary'],ensure_ascii=False,indent=2))
if __name__=='__main__':main()
