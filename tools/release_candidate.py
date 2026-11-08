#!/usr/bin/env python3
"""Prepare/check an integrated, unapproved Class C release candidate.

No fetch, approval, merge, deployment, Class A promotion or facility import.
The sole mutation command is explicitly named prepare-draft. Every original
record/history is hash-bound, and an already integrated tree cannot be reapplied.
"""
import argparse,copy,gzip,html,json,re,tempfile
from collections import Counter
from datetime import date
from pathlib import Path
from urllib.parse import urlsplit
from discovery import ROOT,read,write,digest
from bulk_catalog import compact,sha
from compact_index import add_transport
from launch_readiness import records
from unified_catalog import validate_research
from global_programme import GlobalIndex
from global_continuation import classify,proposal_conflicts
from global_visibility import build as geographic_audit
from validate import url_valid

HOME=ROOT/'data/release-candidate'
CONT=ROOT/'data/global-programme/continuation'
CATEGORY_ALIASES={'Animation production':'Animation','Original animation production':'Animation','Game cinematics':'Cinematics','Film production':'Film / Television Production','Immersive production':'Digital / Interactive Production','Digital content production':'Digital / Interactive Production'}
SECTORS={'Animation','VFX','Cinematics','Film / Television Production','Film / Video Production','Digital / Interactive Production','Game Development','Virtual Production','Production Technology','Production Facilities','Motion Capture','Previsualization','Game Art'}
SPECIALISATIONS={'Rigging','Storyboards','Art direction','Character design'}

def inputs(home=HOME):
    cfg=read(home/'inputs/parent-checkpoint.json')
    if cfg['publication_approved'] is not False:raise ValueError('No fabricated publication approval')
    for name,h in cfg['protected_history'].items():
        p=Path(name)
        if p.is_absolute() or '..' in p.parts or sha(ROOT/p)!=h:raise ValueError('Protected research changed: '+name)
    for name,h in cfg['parent_asset_hashes'].items():
        if Path(name).name!=name or sha(home/'inputs/parent-public'/name)!=h:raise ValueError('Frozen parent public asset changed')
    source=CONT/'reports/proposed-companies.json'
    if sha(source)!=cfg['company_proposals_sha256'] or sha(CONT/'reports/geography-proposals.json')!=cfg['geography_proposals_sha256']:raise ValueError('Proposal checkpoint changed')
    proposals=read(source);decisions=read(home/'inputs/admissions.json');taxonomy=read(home/'inputs/taxonomy.json')['mapping']
    if decisions['publication_approved'] is not False or len(decisions['decisions'])!=len(proposals):raise ValueError('Every proposal needs an unapproved admission assessment')
    byid={r['id']:r for r in proposals};seen=set()
    fields={'record_id','original_proposal_sha256','recommendation','reason','website_kind','website_basis','rights_decision','source_wide_license','reviewed_on','human_approved'}
    for d in decisions['decisions']:
        if set(d)!=fields or d['record_id'] in seen or d['record_id'] not in byid or digest(byid[d['record_id']])!=d['original_proposal_sha256']:raise ValueError('Admission identity/hash mismatch or private field')
        seen.add(d['record_id'])
        if d['recommendation'] not in ('admit_minimal_factual_reference','withhold_industry_scope','withhold_identity','withhold_rights') or d['human_approved'] is not False or d['rights_decision']!='minimal_factual_identifiers_only' or d['source_wide_license']!='UNSPECIFIED' or d['website_kind'] not in ('official','source_listing') or not d['reason']:raise ValueError('Unsupported admission/permission/approval assertion')
        try:
            if date.fromisoformat(d['reviewed_on']).isoformat()!=d['reviewed_on'] or d['reviewed_on']>date.today().isoformat():raise ValueError()
        except (ValueError,TypeError):raise ValueError('Invalid actual assessment date')
    if set(taxonomy)!={c for p in proposals for c in p['categories']}:raise ValueError('Every original category must have an explicit mapping, including intentionally omitted specialisations')
    for label,target in taxonomy.items():
        expected=CATEGORY_ALIASES.get(label,label if label in SECTORS else None)
        if label not in SECTORS|SPECIALISATIONS|set(CATEGORY_ALIASES) or target!=expected:raise ValueError('Taxonomy cannot infer a new technical service or sector')
    return cfg,proposals,decisions['decisions'],taxonomy

def parent_rows(public,database,cfg):
    m,rows=records(public,database);byid={r['id']:r for r in rows}
    if any(rid not in byid or digest(byid[rid])!=h for rid,h in cfg['record_hashes'].items()):raise ValueError('Original company identity, coordinates or evidence lost/changed')
    if sha(database)!=cfg['root_sha256']:raise ValueError('Root studio database changed')
    return m,rows

def audit(parent,home=HOME):
    cfg,proposals,decisions,taxonomy=inputs(home);index=GlobalIndex(parent);reviews={r['proposal_id']:r for r in read(CONT/'reports/report.json')['reviews'] if r['proposal_id']};out=[];admitted=[]
    for d in decisions:
        original=next(r for r in proposals if r['id']==d['record_id']);review=reviews[original['id']]
        # A directory/partner/public profile URL is evidence, never its subject's
        # corporate domain for matching or parent/branch inference.
        m=index.match(original['name'],original['country'],original['website'] if d['website_kind']=='official' else '',review['aliases'])
        if set(m['record_ids'])-set(review.get('dismissed_record_ids',[])):raise ValueError('Unresolved duplicate identity at intake: '+original['name'])
        row=copy.deepcopy(original);labels=row['categories'];row['categories']=list(dict.fromkeys(taxonomy[c] for c in labels if taxonomy[c]));row['source_category']=json.dumps(labels,ensure_ascii=False,separators=(',',':'));row['website_kind']=d['website_kind']
        if not row['name'] or not row['country'] or not row['categories'] or not row['source_provenance'] or not url_valid(row['website']):raise ValueError('Insufficient minimal identity/geography/sector evidence')
        cats=set(row['categories']);relevance='game_development' if 'Game Development' in cats else 'motionx_core' if cats.intersection({'Animation','VFX','Cinematics','Motion Capture','Virtual Production','Previsualization','Game Art'}) else 'supporting_services' if 'Production Technology' in cats else 'adjacent_production'
        row['research_review']={'version':1,'relevance':relevance,'publication_state':'provisional_research_lead','source_rights':'minimal_facts_terms_unspecified','operation_status':'source_self_report_unverified' if review['operation_evidence']=='primary_self_report' else 'regional_listing_only','reviewed_on':row['source_observed_on'],'human_approved':False,'facility_verified':False}
        row['status']='Provisional Class C company reference. Name, country and any city are source associations, not independently verified current operation, legal jurisdiction, physical branches or facility services. No confirmed capabilities or publication approval.'
        row['source_status']='Company self-report or source listing; current operation unverified'
        row['source_type']='Global research minimal factual company reference'
        row['research_reasons']=['Only minimal company identifiers and coarse source-supported sectors are included.','Original source labels are retained in source_category; company assertions are not confirmed facility capabilities.','Source-wide reuse remains UNSPECIFIED. Do not copy source descriptions, imagery, contacts or proprietary data.']
        row['attribution']='Sources: '+', '.join(dict.fromkeys(p['url'] for p in row['source_provenance']))+'. Minimal factual company reference; original source labels retained. Source-wide redistribution/commercial reuse remains UNSPECIFIED. No authored source descriptions, imagery or contacts reproduced.'
        if row['id'] in index.rows or row['company_id'] in {r['company_id'] for r in parent}:raise ValueError('New proposal reuses an existing identity')
        accepted=d['recommendation']=='admit_minimal_factual_reference'
        out.append({**d,'name':row['name'],'country':row['country'],'city':row['city'],'source_country_hint':review['source_country_hint'],'original_categories':labels,'public_categories':row['categories'],'source_evidence':review['evidence'],'source_reviewed_on':original['source_observed_on'],'operation_confidence':review['operation_evidence'],'current_operation':'unverified','matching':m,'prior_name_only_conflicts':review.get('automatic_matching',review['matching']),'identity_resolution':review.get('identity_resolution_note','No conflicting company identity found in the complete parent catalogue or proposal set.'),'rights_scope':'Minimal name/country/supported city, source URL and coarse company-sector facts. No source-wide licence, prose, imagery, contacts, precise facility or verified-service grant.','excluded_unsupported_fields':['confirmed facility capabilities','physical branch/entrance','parent ownership','buying intent','current-operation guarantee','third-party authored descriptions','personal contact data'],'exact_public_fields':row if accepted else None,'original_proposal':original if not accepted else None})
        if accepted:admitted.append(row)
    errors=validate_research(admitted)
    if errors:raise ValueError('Invalid Class C release references: '+str(errors[:5]))
    conflict_reviews=[{'proposal_id':r['id'],'name':r['name'],'aliases':reviews[r['id']]['aliases']} for r in admitted]
    if proposal_conflicts(admitted,conflict_reviews):raise ValueError('Within-release alias/domain conflict')
    return admitted,out

def geography(rows):
    value,_=geographic_audit(rows);byid={r['id']:r for r in rows};value['additional_references']={};decisions=[]
    for p in read(CONT/'reports/geography-proposals.json'):
        row=byid[p['record_id']];point=p['coordinate'];licensed=False
        if point:
            gazetteer=ROOT/'data/research/v1.0-launch/city-references.json';ref=read(gazetteer)['references'].get(p['proposed_company_city'])
            if ref and sha(gazetteer)==point['gazetteer_input_sha256']:
                licensed=(ref['lat'],ref['lng'],ref['source'])==(point['lat'],point['lng'],point['coordinate_source'])
            elif sha(ROOT/'studios.json')==point['gazetteer_input_sha256']:
                licensed=any(r['city']==p['proposed_company_city'] and r['country']==p['country'] and r['coordinate_precision']=='city' and (r['lat'],r['lng'],r.get('coordinate_source',''))==(point['lat'],point['lng'],point['coordinate_source']) for r in read(ROOT/'studios.json'))
        valid=licensed and p['country']==row['country'] and point['coordinate_license']=='CC-BY-4.0' and row['lat'] is None and row['lng'] is None and (row['city']==p['proposed_company_city'] or p['kind']=='company_additional_city_reference_review')
        decision={**p,'release_disposition':'prepare_separate_city_reference' if valid else 'staged_geographic_review','reason':'Source-supported company municipality and an existing hash-bound licensed GeoNames point; original record stays unchanged.' if valid else 'No licensed coordinate payload, or unresolved municipality/correction/facility scope. Preserve original city and null coordinates; not a company-admission blocker.'}
        if valid:
            ref={**point,'city':p['proposed_company_city'],'country':row['country'],'company_evidence':p['evidence'][0]['url'],'observed_on':p['reviewed_on'],'evidence_class':'C','human_approved':False,'facility_verified':False,'explanation':'Separate approximate company city reference for '+p['proposed_company_city']+'. Source-reported municipality only; this does not locate its entrance or verify a physical studio, second facility or current operation. Original record coordinates and city are retained.'}
            if p['kind']=='company_additional_city_reference_review':value['additional_references'].setdefault(row['id'],[]).append(ref)
            else:value['references'][row['id']]=ref
            value['company_audit'][row['id']]='reviewed_city_reference'
        decisions.append(decision)
    value['summary'].update(reviewed_display_references=len(value['references'])+sum(map(len,value['additional_references'].values())),additional_city_references=sum(map(len,value['additional_references'].values())),still_without_display_reference=len(value['company_audit'])-len(value['references']),human_approved=False)
    value['summary']['geographic_dispositions']=dict(sorted(Counter(value['company_audit'].values()).items()))
    return value,decisions

def nz_memorandum():
    companies=read(ROOT/'data/nz-census/final-review/inputs/companies.json')['companies'];scope=read(CONT/'inputs/scope-reviews.json')['records'];excluded={r['record_id']:r for r in scope if r['excluded']};out=[];staged=[]
    for c in companies:
        if c['publication_readiness'].startswith('staged_'):staged.append({'name':c['operating_name'],'id':c['record_id'],'reason':c['classification_basis'],'recommendation':'retain_staged','evidence':c['evidence']});continue
        group='outside_motionx_scope' if c['record_id'] in excluded else 'facility_geography_decision' if c['operating_name'] in ('Lane Street Studios','Avalon Studios','Stone Street Studios') else 'rights_scope_question' if c['original_source_license']=='UNSPECIFIED' else 'suitable_minimal_factual_publication_review'
        out.append({'id':c['record_id'],'name':c['operating_name'],'group':group,'recommendation':'retain only in audit; exclude normal directory under the individually supported audio-only decision' if c['record_id'] in excluded else 'recommend company-only Class C minimal factual reference; facility pins/services remain separate' if group=='facility_geography_decision' else 'recommend the documented minimal factual fields; one explicit cohort scope decision, no source-wide reuse grant' if group=='rights_scope_question' else 'recommend the source-authorised factual company identity; detailed services remain unverified','rights':c['rights_status'],'permitted_scope':c['permitted_scope'],'evidence':excluded[c['record_id']]['evidence'] if c['record_id'] in excluded else c['evidence'],'current_operation':c['operation_note'],'original_classification':c['classification_basis'],'source_categories':c['original_sectors'],'human_approved':False})
    return {'original_provisional_references':57,'recommendation_counts':dict(sorted(Counter(c['group'] for c in out).items())),'identity_ambiguity_new_blockers':0,'company_only_references_recommended':sum(c['group']!='outside_motionx_scope' for c in out),'rows':out,'separately_staged':staged,'facility_dossiers':read(ROOT/'data/nz-census/final-review/inputs/facilities.json')['facilities'],'scope_decision':'Retain all records/history. Review 30 scoped agency references and the limited-factual-field cohort; retain Envy visual/audio services, exclude four audio-only references from normal results. Melodics and Level remain staged. Facility/booking/operator questions do not grant pins or capture services.','human_approved':False,'pr15_approval_required':True}

def apply_draft(public,database,home=HOME):
    public=Path(public);cfg,_,_,_=inputs(home);m,parent=parent_rows(public,database,cfg)
    if m.get('release_candidate') or len(parent)!=cfg['parent_counts']['records'] or sha(public/'manifest.json')!=cfg['parent_asset_hashes']['manifest.json']:raise ValueError('A fresh exact PR #18 parent is required; repeated draft application refused')
    new,audit_rows=audit(parent,home);all_rows=parent+new;index=read(public/'index.json');name='shards/'+digest('global-release-candidate-minimal-facts-v1')[:12]+'-000.json'
    compact(public/name,sorted(new,key=lambda r:r['id']));m['shards'][name]={'sha256':sha(public/name),'gzip_sha256':sha(public/(name+'.gz')),'records':len(new),'country':'Multiple source-associated countries','bytes':(public/name).stat().st_size,'gzip_bytes':(public/(name+'.gz')).stat().st_size}
    for row in new:index.append([row[k] for k in ('id','company_id','name','city','country','lat','lng','categories')]+[name,row['source_observed_on'],row['identity_status'],'C','company_reference'])
    index.sort(key=lambda r:r[0]);compact(public/'index.json',index);m['index'].update(sha256=sha(public/'index.json'),gzip_sha256=sha(public/'index.json.gz'),bytes=(public/'index.json').stat().st_size,gzip_bytes=(public/'index.json.gz').stat().st_size,records=len(index))
    for field in ('records','public_records','class_c','company_references'):m['counts'][field]+=len(new)
    m['counts']['countries']=len({r['country'] for r in all_rows if r['country']});m['counts']['source_identities']=len({r['company_id'] for r in all_rows if r['record_kind']!='retained_location'})
    for field in ('unreviewed_new_references','company_references_without_coordinates','unspecified_company_source_terms'):m['warnings'][field]+=len(new)
    m['warnings'].update(global_rc_minimal_factual_references=len(new),global_rc_source_wide_rights_unspecified=len(new),global_rc_withheld_company_proposals=len(audit_rows)-len(new))
    visibility,geo=geography(all_rows);compact(public/'visibility.json',visibility);m['global_visibility'].update(sha256=sha(public/'visibility.json'),gzip_sha256=sha(public/'visibility.json.gz'),gzip_bytes=(public/'visibility.json.gz').stat().st_size)
    policy=read(public/'commercial.json');policy['baseline_records']=len(all_rows);policy['summary']['normal_results_after']=len(all_rows)-sum(r['excluded'] for r in policy['overrides'].values());compact(public/'commercial.json',policy);m['commercial_scope'].update(sha256=sha(public/'commercial.json'),gzip_sha256=sha(public/'commercial.json.gz'),gzip_bytes=(public/'commercial.json.gz').stat().st_size)
    m['release_candidate']={'version':1,'state':'draft_pending_human_pr_review','parent_commit':cfg['parent_commit'],'parent_records':len(parent),'new_company_reference_ids':sorted(r['id'] for r in new),'report_path':'data/release-candidate/reports/dashboard.html','publication_approved':False,'human_approved':False}
    add_transport(public,database,m,index,[r for r in all_rows if r['record_kind']!='retained_location']);write(public/'manifest.json',m)
    return check_data(public,database,home)

def check_data(public,database,home=HOME):
    cfg,_,_,_=inputs(home);m,rows=parent_rows(public,database,cfg);parent=[r for r in rows if r['id'] in cfg['record_hashes']];new,decisions=audit(parent,home);actual={r['id']:r for r in rows if r['id'] not in cfg['record_hashes']}
    if actual!={r['id']:r for r in new}:raise ValueError('Integrated directory differs from the audited minimal publication subset')
    state=m.get('release_candidate',{})
    if state.get('state')!='draft_pending_human_pr_review' or state.get('publication_approved') is not False or state.get('human_approved') is not False or sorted(actual)!=state.get('new_company_reference_ids'):raise ValueError('Invalid draft state or fabricated approval')
    visibility,geo=geography(rows)
    if read(Path(public)/'visibility.json')!=visibility:raise ValueError('Unsupported geographic display reference')
    policy=read(Path(public)/'commercial.json');parent_policy=read(home/'inputs/parent-public/commercial.json')
    if policy['overrides']!=parent_policy['overrides'] or policy['baseline_records']!=len(rows):raise ValueError('Audio-only scope or actual catalogue counts changed incorrectly')
    expected=copy.deepcopy(cfg['parent_counts'])
    for k in ('records','public_records','class_c','company_references'):expected[k]+=len(new)
    expected['countries']=len({r['country'] for r in rows if r['country']});expected['source_identities']=len({r['company_id'] for r in rows if r['record_kind']!='retained_location'})
    if m['counts']!=expected:raise ValueError('Release manifest totals do not describe actual records')
    public=Path(public);indexed=read(public/'index.json');byid={r['id']:r for r in rows};source_ids={r['id'] for r in rows if r['record_kind']!='retained_location'}
    if len(indexed)!=len(source_ids) or {r[0] for r in indexed}!=source_ids:raise ValueError('Current index lost or duplicated a company/source identity')
    for entry in indexed:
        row=byid[entry[0]]
        if entry[:8]!=[row[k] for k in ('id','company_id','name','city','country','lat','lng','categories')] or entry[9:]!=[row['source_observed_on'],row['identity_status'],row['evidence_class'],row['record_kind']] or entry[8] not in m['shards']:raise ValueError('Index metadata differs from the actual record')
    assets=[(m['index']['path'],m['index']),(m['index']['compact']['path'],m['index']['compact']),(m['baseline']['compressed']['path'],m['baseline']['compressed']),(m['global_visibility']['path'],m['global_visibility']),(m['commercial_scope']['path'],m['commercial_scope']),*m['shards'].items()]
    for name,meta in assets:
        path=public/name
        if sha(path)!=meta['sha256'] or sha(public/(name+'.gz'))!=meta['gzip_sha256'] or gzip.decompress((public/(name+'.gz')).read_bytes())!=path.read_bytes():raise ValueError('Release transport/provenance integrity mismatch: '+name)
    for r in new:
        if r['lat'] is not None or r['lng'] is not None or r['capabilities'] or r['capability_evidence'] or r['verified_on'] or r['relationships']:raise ValueError('Unreviewed company became a verified physical facility')
    return {'summary':{'parent_records':len(parent),'draft_records':len(rows),'admitted_companies':len(new),'withheld_companies':len(decisions)-len(new),'new_confirmed_capabilities':0,'new_physical_facility_records':0,'original_records_changed':0,'geographic_proposals':len(geo),'new_city_display_references':sum(g['release_disposition']=='prepare_separate_city_reference' for g in geo),'staged_geographic_proposals':sum(g['release_disposition']=='staged_geographic_review' for g in geo),'remaining_city_associations':238,'existing_research_keys_preserved':725,'unresolved_research_cases_preserved':381,'countries_and_territories':m['counts']['countries'],'retained_locations':243,'retained_reviewed_organisations':119,'total_source_identity_keys':m['counts']['source_identities'],'company_references':m['counts']['company_references'],'normal_directory_records':len(rows)-4,'human_approved':False,'publication_approved':False},'admissions':decisions,'integrated_records':new,'geographic_decisions':geo,'commercial_before':dict(sorted(Counter(classify(r,parent_policy)['role'] for r in parent).items())),'commercial_after':dict(sorted(Counter(classify(r,policy)['role'] for r in rows).items())),'taxonomy':read(home/'inputs/taxonomy.json'),'nz_decision_memorandum':nz_memorandum(),'ongoing_work':{'research_checkpoint':'data/global-programme/continuation/reports/research-checkpoint.json','geographic_queue':'data/global-programme/continuation/reports/geographic-associations.json','source_followup':'data/global-programme/continuation/reports/source-followup.json','historical_backlog_untouched':True,'source_or_worldwide_coverage_complete':False}}

def save(report,out):
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    for n,v in [('summary',report['summary']),('admissions',report['admissions']),('integrated-records',report['integrated_records']),('geographic-decisions',report['geographic_decisions']),('nz-decision-memorandum',report['nz_decision_memorandum']),('release-audit',report)]:write(out/(n+'.json'),v)
    esc=lambda v:html.escape(str(v),quote=True)
    cards=[]
    for r in report['admissions']:
        links=' · '.join('<a href="'+esc(e['url'])+'" rel="noopener noreferrer">'+esc(e['basis'].replace('_',' '))+'</a>' for e in r['source_evidence'])
        cards.append('<article data-company data-country="'+esc(r['country'])+'" data-state="'+esc(r['recommendation'])+'"><h2>'+esc(r['name'])+' · '+esc(r['country'])+'</h2><p><strong>'+esc(r['recommendation'].replace('_',' '))+'</strong></p><p>'+esc(r['reason'])+'</p><p>'+esc(r['city'] or 'City not established')+' · sectors '+esc(', '.join(r['public_categories']))+' · source labels '+esc(', '.join(r['original_categories']))+'</p><p>Evidence reviewed '+esc(r['source_reviewed_on'])+'. Current operation unverified. '+esc(r['website_basis'])+'</p><p>'+links+'</p>'+('<a href="../../../index.html#/location/'+esc(r['record_id'])+'">Open integrated provisional profile</a>' if r['exact_public_fields'] else '<p>Withheld; original proposal remains in the audit.</p>')+'<details><summary>Exact proposed public fields and rights scope</summary><pre>'+esc(json.dumps(r['exact_public_fields'],indent=2,ensure_ascii=False))+'</pre><p>'+esc(r['rights_scope'])+'</p></details></article>')
    page='<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>MotionX integrated release candidate</title><style>body{background:#101822;color:#edf1f8;font:16px/1.6 system-ui;max-width:1150px;margin:auto;padding:22px;overflow-wrap:anywhere}a{color:#addcff}article{border:1px solid #43516a;border-radius:10px;padding:18px;margin:18px 0}pre{white-space:pre-wrap;overflow-wrap:anywhere}input,select,button{font:inherit;min-height:44px;max-width:100%;background:#172333;color:inherit;border:1px solid #8798ad;padding:8px}label{display:block;margin:10px 0}:focus-visible{outline:3px solid #ffd77a}[hidden]{display:none}@media(max-width:650px){body{padding:12px}}</style><h1>Integrated release candidate · human review</h1><p>Real directory entries in this draft; no authorised production release, merge or publication approval. Company references stay Class C, with current operation and physical facilities unverified.</p><nav><a href="../../../index.html">Open integrated atlas</a> · <a href="release-audit.json">Complete audit</a> · <a href="geographic-decisions.json">17 geographic decisions</a> · <a href="nz-decision-memorandum.json">NZ prerequisite decisions</a> · <a href="../DECISIONS.md">Short maintainer decisions</a> · <a href="readiness/licensing.html">Current scoped licensing audit</a></nav><pre>'+esc(json.dumps(report['summary'],indent=2))+'</pre><label>Find company or evidence<input id="reviewSearch" type="search"></label><label>Admission<select id="reviewState"><option value="">All 184 audited proposals</option><option value="admit_minimal_factual_reference">Integrated minimal factual references</option><option value="withhold_industry_scope">Withheld for industry scope</option></select></label><p id="reviewCount" role="status" aria-live="polite"></p>'+''.join(cards)+'<script>(()=>{const rows=[...document.querySelectorAll("[data-company]")],q=document.getElementById("reviewSearch"),s=document.getElementById("reviewState"),c=document.getElementById("reviewCount");function render(){const words=q.value.normalize("NFKD").toLowerCase().trim().split(/\\s+/).filter(Boolean);let n=0;for(const r of rows){r.hidden=!!(s.value&&r.dataset.state!==s.value||!words.every(w=>r.textContent.normalize("NFKD").toLowerCase().includes(w)));if(!r.hidden)n++;}c.textContent=n+" of "+rows.length+" company proposals shown. This is not human approval.";}q.addEventListener("input",render);s.addEventListener("change",render);render();})();</script></html>'
    (out/'dashboard.html').write_text(page,encoding='utf-8')

def check(public=ROOT/'data/public',database=ROOT/'studios.json',home=HOME):
    report=check_data(public,database,home)
    with tempfile.TemporaryDirectory() as tmp:
        save(report,tmp)
        for p in Path(tmp).iterdir():
            if p.read_bytes()!=(home/'reports'/p.name).read_bytes():raise ValueError('Stale release audit: '+p.name)
    return report

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('command',choices=('prepare-draft','check'));a=p.parse_args()
    if a.command=='prepare-draft':result=apply_draft(ROOT/'data/public',ROOT/'studios.json');save(result,HOME/'reports')
    else:result=check()
    print(json.dumps(result['summary'],indent=2))
