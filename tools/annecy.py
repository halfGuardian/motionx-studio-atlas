#!/usr/bin/env python3
"""Reconcile every Annecy exhibitor; append only source-supported Class C references.

Preparation never approves publication, creates facilities or changes existing data.
Research inputs are inert, hash-bound checkpoints, not instructions or approvals.
"""
import argparse,copy,csv,hashlib,html,json,re,tempfile
from collections import Counter
from datetime import date
from pathlib import Path
from boutique import host,shared,region,relevance
from annecy_match import IdentityIndex,key,place
from bulk_catalog import compact,sha
from compact_index import add_transport
from discovery import ROOT,read,write,digest
from launch_readiness import records
from unified_catalog import validate_research
from validate import url_valid

HOME=ROOT/'data/annecy'
EVENT='https://www.annecyfestival.com/en/the-mifa/exhibitors/exhibition-area/2024-exhibitors'
DISPOSITIONS={'previously_existing','newly_added','duplicate','rejected','inactive','unresolved'}
CLAIMS={'Animation','CG','VFX','Character animation','Game cinematics','Unreal Engine','Rigging','Pipeline tools','Previs','Game production','Game art','Realtime','Digital humans','Virtual production','Motion editing'}

def inputs(home=HOME):
    rows=read(home/'inputs/exhibitors.json')['records'];research=read(home/'inputs/research.json');policy=read(home/'source-policy.json')
    if len(rows)!=1074 or len({r['exhibitor_id'] for r in rows})!=1074:raise ValueError('complete 1074-row input required')
    expected={r['exhibitor_id'] for r in rows if r['research_group'] in ('priority','production_review')};studies=research['records']
    if len(studies)!=len(expected) or {r['exhibitor_id'] for r in studies}!=expected:raise ValueError('research checkpoint must cover all 253 + 313 target rows')
    if policy['automatic_collection'] or policy['redistribution_permission']!='not_established':raise ValueError('unreviewed source-policy change')
    for r in studies:
        if r['human_approved'] is not False or r['independent_operation_verification']!='unknown':raise ValueError('research cannot fabricate approval or verification')
        if set(r['company_service_claims'])-CLAIMS:raise ValueError('unsupported service claim')
        if not r['search_attempts'] or not all(re.fullmatch('[a-f0-9]{64}',a['response_sha256']) for a in r['search_attempts']):raise ValueError('research attempt audit missing')
        for s in r['sources']:
            if not url_valid(s['url']) or date.fromisoformat(s['observed_on']).isoformat()!=s['observed_on']:raise ValueError('unsafe source or date')
        if r['decision']=='source_supported_company':
            if not r['company_service_claims'] or not url_valid(r['official_website']) or r['current_operation']!='company_self_report_observed' or not any(s['kind']=='official_company' and s['access']=='readable_page' for s in r['sources']):raise ValueError('historical/index-only evidence cannot qualify a new reference')
    return rows,{r['exhibitor_id']:r for r in studies},policy

def sectors(claims):
    output=[]
    if any(k in claims for k in ('Animation','CG','Character animation','Rigging')):output.append('Animation')
    if 'VFX' in claims:output.append('VFX')
    if 'Game production' in claims:output.append('Game Development')
    if 'Game cinematics' in claims:output.append('Cinematics')
    if 'Previs' in claims:output.append('Previs')
    if 'Virtual production' in claims:output.append('Virtual Production')
    return output or ['Animation']

def proposal(e,r):
    name=r['operating_name'];site=r['official_website'];identity=digest([key(name),site if shared(host(site)) else host(site)])
    rid='annecy-'+identity[:28];observed=r['sources'][0]['observed_on'];ev=r['sources'][0]['url'];current_country=place(r['current_company_country'])
    return {'id':rid,'company_id':'annecy-org-'+identity[:24],'name':name,'city':'','country':current_country,'lat':None,'lng':None,'website':site,'website_kind':'official','categories':sectors(r['company_service_claims']),'capabilities':[],'capability_evidence':{},'evidence_state':'unknown','evidence_class':'C','verified_on':'','source_observed_on':observed,'evidence':ev,'coordinate_precision':'unverified','coordinate_source':ev,'location_type':'uncertain','relationships':[],'record_kind':'company_reference','identity_status':'source_provisional','status':'Source-supported Class C company reference. Services are company self-claims, not independently verified facility capabilities. No physical branch or map coordinate is established.','license':'UNSPECIFIED','attribution':'Annecy / MIFA 2024 historical exhibitor identity supplied by the user; current company self-description assessed separately at the linked official source. Minimal factual reference, no source prose, logo or contact details. No source-wide reuse grant established.','research_reasons':['Independent current operation and physical facilities require human review.','Event participation is historical evidence only; event nationality is not a branch location.','Geography is a company-level association where supported, never a geocoded facility.','Source reuse permission is not established; no automated collector enabled.'],'potential_duplicates':[],'source_status':'company self-report observed; independent verification unknown','source_type':'Annecy company research reference','source_category':','.join(r['company_service_claims']),'source_release':digest(r),'source_provenance':[{'source_id':'annecy-2024-company-review','source_record_id':e['exhibitor_id'],'url':s['url'],'license':'UNSPECIFIED','license_url':s['url'],'observed_on':observed,'observation_hash':digest({'exhibitor':e['source_row_hash'],'research':r,'source':s})} for s in r['sources']]}

def build(base,home=HOME):
    exhibits,studies,policy=inputs(home);matcher=IdentityIndex(base);new=[];audit=[];groups={};domains={};profiles={};before=Counter()
    for e in exhibits:
        r=studies.get(e['exhibitor_id']);prior=matcher.match(e['name'],e['listed_country']);before[prior['match_status']]+=1
        current=matcher.match(r['operating_name'],r['current_company_country'] or e['listed_country'],r['official_website'],r['supported_aliases']) if r and r['decision']=='source_supported_company' else prior
        row={**e,'baseline_match':prior,'current_match':current,'research':r,'disposition':'unresolved','record_id':None,'reason':current['reason'],'confidence':current['confidence'],'human_review_status':'pending','independent_operation_verification':'unknown'}
        if current['match_status'] in ('name_and_domain','name_and_country'):
            row.update(disposition='previously_existing',record_id=current['record_ids'][0],reason=current['reason']+' Identity representation does not establish current operation or services.')
        if r and r['decision'] in ('inactive','not_a_production_studio'):
            row.update(disposition='inactive' if r['decision']=='inactive' else 'rejected',reason=r['reason'],confidence='medium')
        elif r and r['decision']=='source_supported_company':
            if current['match_status'] in ('identity_review','shared_domain_review','possible_alias'):
                row.update(disposition='unresolved',reason=current['reason']+' Hold proposed addition until alias, brand or domain conflict is resolved.',confidence='low')
            elif row['disposition']=='previously_existing':pass
            else:
                ident=(key(r['operating_name']),r['official_website'] if shared(host(r['official_website'])) else host(r['official_website']));h=host(r['official_website'])
                if ident in groups:
                    record=groups[ident];row.update(disposition='duplicate',record_id=record['id'],reason='Same source-supported operating identity and official domain as another exhibitor. Both event rows retained; no extra branch inferred.',confidence='high')
                    # Preserve every independent event observation on the single new reference.
                    record['source_provenance']+=proposal(e,r)['source_provenance']
                elif h in domains and not shared(h):
                    row.update(reason='Same new official domain under a different legal/brand name; hold identity rather than merge distinct subsidiaries or invent a new branch.',confidence='low')
                else:
                    record=proposal(e,r);groups[ident]=record;domains[h]=record;new.append(record);row.update(disposition='newly_added',record_id=record['id'],reason=r['reason'],confidence='medium')
                if row['record_id']:
                    rid=row['record_id'];claims=r['company_service_claims'];signals,_=relevance(record['name'],claims)
                    if signals:profiles[rid]={'record_id':rid,'name':record['name'],'country':record['country'],'region':region(record['country']),'signals':signals,'research_terms':claims,'sources':[{'url':s['url'],'basis':'official_company','observed_on':s['observed_on']} for s in r['sources']],'size_claim':'Unknown','size_reviewed_on':'','independence':'unknown','external_support_need':'unknown','purchasing_intent':'unknown','research_status':'primary_claims_reviewed','source_supported_location':False,'score':sum(signals.values()),'score_meaning':'Advisory company-service alignment; not facility verification, purchasing intent or human approval.'}
        elif r and row['disposition']=='unresolved':row.update(reason=r['reason'],confidence='low')
        audit.append(row)
    errors=validate_research(new)
    if errors:raise ValueError(str(errors[:5]))
    counts=Counter(a['disposition'] for a in audit);claims=Counter(c for r in studies.values() if r['decision']=='source_supported_company' for c in r['company_service_claims'])
    summary={'exhibitor_entries':len(exhibits),'priority_research_entries':sum(e['research_group']=='priority' for e in exhibits),'production_research_entries':sum(e['research_group']=='production_review' for e in exhibits),'target_entries_with_research_attempts':len(studies),'indexed_search_queries':sum(len(r['search_attempts']) for r in studies.values()),'page_requests':sum(bool(r['page_attempt']) for r in studies.values()),'readable_company_assessments_before_identity_matching':sum(r['decision']=='source_supported_company' for r in studies.values()),'baseline_identity_matches':dict(before),'dispositions':dict(sorted(counts.items())),'new_class_c_company_references':len(new),'new_physical_locations':0,'new_confirmed_capability_claims':0,'new_verified_capture_facilities':0,'existing_records_examined':len(base),'existing_ids_preserved':True,'all_source_rows_reconciled':len(audit)==1074,'target_attempt_coverage':1.0,'independently_verified_current_operations_added':0,'human_reviewed_precision_sample':None,'publication_approved':False,'company_service_signals_not_facility_verification':dict(sorted(claims.items())),'remaining_gaps':['All new references require human identity, relevance and current-operation review; none is a verified physical facility.','508 non-target exhibitors receive full-catalogue identity reconciliation, not individual current-company research.','Unresolved aliases, parent/brand distinctions, stale projects, wrong namesakes and inaccessible primary pages remain queued.','A readable self-description is company evidence, not independent current-operation verification.','Original PDF and missing CSV not accessed. Workbook supplied the complete crosscheck.','No blanket PDF/directory redistribution permission; source policy and source-specific links remain explicit.','No completed human precision sample; no measured human precision or approval claimed.']}
    summary['outcomes_by_research_group']={group:dict(sorted(Counter(a['disposition'] for a in audit if a['research_group']==group).items())) for group in ('priority','production_review','other')}
    summary['previous_identity_hints']={'same_country_matches':143,'possible_aliases':24,'no_strong_match':907,'meaning':'Historical user-supplied audit, not current-operation verification.'}
    return {'version':1,'summary':summary,'reconciliation':audit,'proposed_references':new,'new_profiles':profiles,'source_policy':policy,'baseline_ids_sha256':digest(sorted(r['id'] for r in base))}

def extend(public,base_path,home=HOME):
    public=Path(public);m,base=records(public,base_path);report=build(base,home);new=report['proposed_references'];retained=set(r['id'] for r in base)
    if any(r['id'] in retained for r in new):raise ValueError('extension already present or ID collision; rebuild from frozen baseline')
    report['before_counts']=copy.deepcopy(m['counts']);report['retained_shard_hashes']={name:d['sha256'] for name,d in m['shards'].items()};report['retained_baseline_sha256']=sha(base_path)
    index=read(public/'index.json');name='shards/'+digest('annecy-v13')[:12]+'-000.json'
    if (public/name).exists():raise ValueError('append target exists')
    compact(public/name,sorted(new,key=lambda r:r['id']));m['shards'][name]={'sha256':sha(public/name),'gzip_sha256':sha(public/(name+'.gz')),'gzip_bytes':(public/(name+'.gz')).stat().st_size,'records':len(new),'country':'Multiple / unresolved','bytes':(public/name).stat().st_size}
    for r in new:index.append([r[k] for k in ('id','company_id','name','city','country','lat','lng','categories')]+[name,r['source_observed_on'],r['identity_status'],r['evidence_class'],r['record_kind']])
    index.sort(key=lambda r:r[0]);compact(public/'index.json',index);m['index'].update(sha256=sha(public/'index.json'),gzip_sha256=sha(public/'index.json.gz'),gzip_bytes=(public/'index.json.gz').stat().st_size,records=len(index),bytes=(public/'index.json').stat().st_size)
    for k in ('records','public_records','class_c','company_references'):m['counts'][k]+=len(new)
    m['counts']['countries']=len({r['country'] for r in base+new if r['country']});m['counts']['source_identities']=len({r['company_id'] for r in base+new if r['record_kind']!='retained_location'})
    for k in ('unspecified_company_source_terms','company_references_without_coordinates','unreviewed_new_references'):m['warnings'][k]+=len(new)
    m['warnings']['annecy_class_c_company_references_requiring_review']=len(new)
    advisory=read(public/'boutique.json');advisory['profiles'].update(report['new_profiles']);advisory['annecy_summary']=report['summary'];compact(public/'boutique.json',advisory)
    m['boutique'].update(sha256=sha(public/'boutique.json'),gzip_sha256=sha(public/'boutique.json.gz'),gzip_bytes=(public/'boutique.json.gz').stat().st_size)
    add_transport(public,base_path,m,index,[r for r in base+new if r['record_kind']!='retained_location']);write(public/'manifest.json',m)
    report['after_counts']=copy.deepcopy(m['counts']);report['summary']['all_identity_keys_after']=len({r['company_id'] for r in base+new});return report

def safe_csv(value):
    value=str(value or '')
    return "'"+value if value.lstrip().startswith(('=','+','-','@','\t','\r')) else value

def save(report,output):
    output=Path(output);output.mkdir(parents=True,exist_ok=True);public={k:v for k,v in report.items() if k not in ('proposed_references','new_profiles')}
    write(output/'reconciliation.json',dict(sorted(public.items())));write(output/'proposals.json',{'human_approved':False,'canonical_updates':[],'company_references':report['proposed_references']});write(output/'summary.json',{'summary':report['summary'],'before':report['before_counts'],'after':report['after_counts']})
    coverage={}
    for group in ('priority','production_review','other'):
        cohort=[a for a in report['reconciliation'] if a['research_group']==group]
        before=sum(a['baseline_match']['match_status'] in ('name_and_country','name_and_domain') for a in cohort)
        after=sum(a['disposition'] in ('previously_existing','newly_added','duplicate') for a in cohort)
        coverage[group]={'entries':len(cohort),'baseline_identity_represented_rows':before,'proposed_identity_represented_rows':after,'proposed_row_representation_fraction':round(after/len(cohort),6),'research_attempts':sum(bool(a['research']) for a in cohort)}
    write(output/'coverage-metrics.json',{'meaning':'Exhibitor-row identity representation, including duplicate event entries, not verified operating facilities, blind recall or human precision. The number of genuine eligible companies among unresolved rows remains unknown.','groups':coverage,'human_precision':None,'human_reviewed':0})
    fields=['exhibitor_id','name','listed_country','research_group','disposition','record_id','confidence','reason','sources','observed_on']
    with (output/'reconciliation.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=fields,lineterminator="\n");w.writeheader()
        for a in report['reconciliation']:
            r=a['research'] or {};w.writerow({k:safe_csv(' | '.join(s['url'] for s in r.get('sources',[])) if k=='sources' else ' | '.join(sorted({s['observed_on'] for s in r.get('sources',[])})) if k=='observed_on' else a.get(k,'')) for k in fields})
    selected=sorted(report['reconciliation'],key=lambda a:digest(a['exhibitor_id']))
    sample=[]
    for status in sorted(DISPOSITIONS):sample += [a for a in selected if a['disposition']==status][:8]
    write(output/'human-precision-review.json',{'method':'Deterministic stratified worksheet; agent decisions are not human precision measurements. Check current operation, identity, relevance, geography, claims and permissions.','reconciliation_sha256':sha(output/'reconciliation.json'),'human_reviewed':0,'precision':None,'publication_approved':False,'rows':[{'exhibitor_id':a['exhibitor_id'],'name':a['name'],'proposed_disposition':a['disposition'],'sources':(a['research'] or {}).get('sources',[]),'content_hash':digest(a),'reviewer':None,'decision':None,'reason':None,'review_status':'pending_human_review'} for a in sample]})
    esc=html.escape;body=[]
    for a in sorted(report['reconciliation'],key=lambda r:(r['listed_country'],r['name'],r['exhibitor_id'])):
        r=a['research'] or {};sources=' · '.join('<a rel="noopener noreferrer" href="'+esc(s['url'],quote=True)+'">'+esc(s['kind'])+'</a> ('+esc(s['observed_on'])+')' for s in r.get('sources',[]));rid=a['record_id'];link='<a href="../../../index.html#/location/'+esc(rid,quote=True)+'">Atlas reference</a>' if rid else 'No addition';claims=', '.join(r.get('company_service_claims',[])) or 'Unverified';country=a['listed_country']
        body.append('<tr data-state="'+a['disposition']+'" data-group="'+a['research_group']+'"><td>'+esc(a['exhibitor_id'])+'<br><strong>'+esc(a['name'])+'</strong><br>'+esc(country)+' (2024 association)</td><td>'+esc(a['disposition'])+'<br>'+link+'<br>'+esc(a['confidence'])+' confidence</td><td>'+esc(a['reason'])+'<br>Company service signals: '+esc(claims)+'</td><td>'+sources+'<br>Match IDs: '+esc(', '.join(a['current_match']['record_ids']))+'</td></tr>')
    page='''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>MotionX — Annecy 2024 coverage</title><style>body{background:#0c1420;color:#edf3fa;font:16px/1.55 system-ui;max-width:1450px;margin:auto;padding:24px}a{color:#a9d7ff}input,select{background:#152133;color:#fff;border:1px solid #8798ad;padding:12px;min-height:44px;font:inherit}label{display:inline-block;margin:8px}a:focus-visible,input:focus-visible,select:focus-visible{outline:3px solid #ffda80}table{border-collapse:collapse;width:100%}th,td{border:1px solid #43546a;padding:12px;vertical-align:top;text-align:left;overflow-wrap:anywhere}pre{white-space:pre-wrap}tr[hidden]{display:none}@media(max-width:700px){body{padding:12px}table,tbody,tr,td{display:block}thead{display:none}}</style><h1>Annecy 2024 · Boutique studio coverage</h1><p>Historical exhibitor participation is not current-operation verification. All additions are Class C company references without invented facilities, coordinates or confirmed capture claims. Agent source assessment is not human approval.</p><p><a href="../../../index.html">Open atlas</a> · <a href="reconciliation.json">Full JSON audit</a> · <a href="reconciliation.csv">CSV</a> · <a href="human-precision-review.json">Pending human precision worksheet</a></p><details><summary>Coverage, before/after counts and limitations</summary><pre>'''+esc(json.dumps({'summary':report['summary'],'before':report['before_counts'],'after':report['after_counts']},indent=2,ensure_ascii=False))+'''</pre></details><p>Grouped by listed country and company. Source-supported claims describe the operating company; they are not verified services at every branch. Previously existing means an identity match, not current-operation approval.</p><label>Company or country <input id="search" type="search"></label><label>Outcome <select id="state"><option value="">All outcomes</option>'''+''.join('<option>'+s+'</option>' for s in sorted(DISPOSITIONS))+'''</select></label><label>Research group <select id="group"><option value="">All exhibitors</option><option value="priority">253 high-priority entries</option><option value="production_review">313 production entries</option><option value="other">Other 508 entries</option></select></label><p id="count" role="status" aria-live="polite">1,074 exhibitor rows</p><table><thead><tr><th>Company / historical geography</th><th>Outcome</th><th>Assessment and unresolved questions</th><th>Evidence / matching</th></tr></thead><tbody>'''+''.join(body)+'''</tbody></table><script src="../../../annecy-review.js"></script></html>'''
    (output/'coverage.html').write_text(page,encoding='utf-8')

def verify_checkpoint(home=HOME):
    config=read(home/'release.json')
    for name,expected in config['input_hashes'].items():
        path=Path(name)
        if path.is_absolute() or '..' in path.parts or path.parts[0] not in ('inputs','source-policy.json'):raise ValueError('unsafe checkpoint path')
        if sha(home/path)!=expected:raise ValueError('Annecy input checkpoint changed: '+name)
    return config

def check(home=HOME,output=None):
    config=verify_checkpoint(home);m,all_rows=records(ROOT/'data/public',ROOT/'studios.json');base=[r for r in all_rows if not r['id'].startswith('annecy-')];report=build(base,home)
    report.update(before_counts=config['before_counts'],after_counts=m['counts'],retained_shard_hashes=config['retained_shard_hashes'],retained_baseline_sha256=sha(ROOT/'studios.json'));report['summary']['all_identity_keys_after']=len({r['company_id'] for r in all_rows})
    if digest(sorted(r['id'] for r in base))!=config['baseline_ids_sha256'] or len(base)!=42067:raise ValueError('retained catalogue identity set changed')
    if m['counts']!=config['after_counts'] or sha(ROOT/'studios.json')!=config['retained_baseline_sha256']:raise ValueError('release counts/baseline changed')
    for name,expected in config['retained_shard_hashes'].items():
        if sha(ROOT/'data/public'/name)!=expected:raise ValueError('retained source shard changed')
    actual={r['id']:r for r in all_rows if r['id'].startswith('annecy-')}
    if actual!={r['id']:r for r in report['proposed_references']}:raise ValueError('public reference differs from reviewed proposal')
    with tempfile.TemporaryDirectory() as tmp:
        save(report,Path(tmp))
        for p in Path(tmp).iterdir():
            if p.read_bytes()!=(Path(output or home/'reports')/p.name).read_bytes():raise ValueError('stale Annecy report: '+p.name)
    return report

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('command',choices=('check','prepare'));p.add_argument('--output',type=Path,default=HOME/'reports');a=p.parse_args()
    if a.command=='check':report=check(output=a.output)
    else:
        report=extend(ROOT/'data/public',ROOT/'studios.json');save(report,a.output);paths=list((HOME/'inputs').glob('*.json'))+[HOME/'source-policy.json'];write(HOME/'release.json',{'version':1,'base_commit':'cf7a14949ef2ecab1549a39b1c6ef78fa9571b17','input_hashes':{str(p.relative_to(HOME)):sha(p) for p in paths},**{k:report[k] for k in ('before_counts','after_counts','baseline_ids_sha256','retained_shard_hashes','retained_baseline_sha256')},'publication_approved':False,'human_review_required':True})
    print(json.dumps(report['summary'],indent=2))
if __name__=='__main__':main()
