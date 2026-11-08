#!/usr/bin/env python3
"""Reconcile individually researched companies; never publish research proposals.

The public scope sidecar is reversible. Original records and evidence are frozen.
No fetch, approval, import, relocation or capability verification is performed.
"""
import argparse, copy, csv, gzip, html, json, re, tempfile
from collections import Counter
from pathlib import Path
from discovery import ROOT, read, write, digest
from bulk_catalog import compact, sha
from global_programme import GlobalIndex, iso
from annecy_match import key
from launch_readiness import records
from unified_catalog import validate_research
from nz_quality_gate import csv_safe
from validate import url_valid
from boutique import record_host, shared

HOME=ROOT/'data/global-programme/continuation'
ROLES={'potential_client','service_provider','both','adjacent_uncertain','out_of_scope'}
LABELS={'potential_client':'Potential MotionX client','service_provider':'Relevant service provider','both':'Both client and provider','adjacent_uncertain':'Adjacent / uncertain relevance','out_of_scope':'Out of scope'}
GROUPS={'games':['Game Development'], 'production':['Film / Television Production','Film / Video Production'], 'visual':['Animation','VFX','Cinematics','Virtual Production','Previsualization','Previs','Game Art'], 'technical':['Motion Capture','Performance Capture','Facial Capture','Body Capture','Volumetric Capture','Retargeting','Motion Editing','Production Technology','Digital / Interactive Production']}
STATES={'primary_self_report','access_unavailable','insufficient_current_content','directory_only','corroborated_identity_official_unavailable'}
FIELDS={'candidate_id','record_id','name','country','official_name','aliases','official_website','reviewed_on','operation_evidence','commercial_role','city','company_claims','reason','evidence','rights','automatic_collection','human_approved','facility_verified','independent_review','identity_hold'}

def validate_backlog(backlog,checkpoint):
    path=ROOT/'data/global-programme/reports/global-report.json.gz'
    if sha(path)!=checkpoint['starting_source_report_sha256'] or backlog.get('starting_report_sha256')!=sha(path):raise ValueError('Starting research history changed')
    source=json.loads(gzip.decompress(path.read_bytes()));pending={'potential_new_company','research_required','identity_conflict','possible_alias','additional_branch_review','company_geography_pending'};groups={}
    for r in source['observations']:
        if r['disposition'] in pending:groups.setdefault((key(r['name']),r['country']),[]).append(r)
    if backlog['review_keys']!=len(groups) or len(backlog['candidates'])!=len(groups) or backlog['pending_observations']!=sum(map(len,groups.values())):raise ValueError('Incomplete continuation backlog')
    seen=set()
    for c in backlog['candidates']:
        k=(key(c['name']),c['country_hint']);origin=groups.get(k,[])
        if not origin or k in seen or c['candidate_id']!='research-'+digest(k)[:24] or c['human_approved'] is not False or c['independent_review'] is not None:raise ValueError('Backlog key/approval mismatch')
        seen.add(k)
        expected={'observation_ids':{r['observation_id'] for r in origin},'source_urls':{r['source_url'] for r in origin if r.get('source_url')},'original_outcomes':{r['disposition'] for r in origin},'website_hints':{r['website'] for r in origin if r.get('website')},'city_hints':{r['city'] for r in origin if r.get('city')}}
        if any(set(c[field])!=values or len(c[field])!=len(values) for field,values in expected.items()):raise ValueError('Lost source observations or research hints')

def scope_policy(rows, home=HOME):
    value=read(home/'inputs/scope-reviews.json'); overrides={}; byid={r['id']:r for r in rows}
    if value.get('version')!=1:raise ValueError('Invalid scope review version')
    iso(value['reviewed_on'])
    expected={'record_id','name','evidence','reason','role','excluded','basis','confidence','human_approved','facility_verified','automatic_collection','reviewed_on'}
    for r in value['records']:
        if set(r)!=expected or r['record_id'] not in byid or r['record_id'] in overrides or r['name']!=byid[r['record_id']]['name']:raise ValueError('Scope identity conflict')
        if r['human_approved'] is not False or r['facility_verified'] is not False or r['automatic_collection'] is not False or r['role'] not in ROLES or type(r['excluded']) is not bool or r['excluded']!=(r['role']=='out_of_scope') or r['basis']!='individual_service_review' or not r['reason'] or not r['evidence'] or any(not url_valid(u) for u in r['evidence']):raise ValueError('Invalid reversible exclusion evidence')
        iso(r['reviewed_on']);overrides[r['record_id']]=copy.deepcopy(r)
    return {'version':1,'labels':LABELS,'groups':GROUPS,'overrides':overrides,'reviewed_on':value['reviewed_on'],'baseline_records':len(rows),'human_approved':False,'purchasing_intent':'unknown','description':'Owner-defined sector eligibility, not verified purchasing intent, facility services or company operation. Only individually reviewed audio-only companies are excluded; records remain available in audit mode.'}

def classify(row,policy):
    if row['id'] in policy['overrides']:return policy['overrides'][row['id']]
    cats=set(row['categories']);groups=policy['groups']
    client=bool(cats.intersection(groups['games']+groups['production']));technical=bool(cats.intersection(groups['technical']))
    role='both' if cats.intersection(groups['visual']) or client and technical else 'potential_client' if client else 'service_provider' if technical else 'adjacent_uncertain'
    return {'role':role,'excluded':False,'basis':'recorded_sector_eligibility','confidence':'source_sector_only','reason':'Recorded sectors support owner-defined audience eligibility only; operation, service availability and purchasing intent are not established.','evidence':[],'human_approved':False,'facility_verified':False}

def validate_reviews(value,backlog,rows):
    if value.get('version')!=1 or not isinstance(value.get('reviews'),list):raise ValueError('Invalid research input')
    iso(value['reviewed_on']);keys={r['candidate_id']:r for r in backlog['candidates']};ids={r['id']:r for r in rows};seen=set()
    for r in value['reviews']:
        rid=r.get('candidate_id') or r.get('record_id')
        if set(r)-FIELDS or (FIELDS-{'record_id','identity_hold'})-set(r) or not rid or rid in seen or type(r.get('identity_hold',False)) is not bool:raise ValueError('Unsupported/private, missing or duplicate review fields')
        seen.add(rid)
        if r.get('record_id') and (r['record_id'] not in ids or r['name']!=ids[r['record_id']]['name'] or r['country']!=ids[r['record_id']]['country']):raise ValueError('Geographic review changed source identity')
        if r.get('candidate_id') in keys and (r['name']!=keys[r['candidate_id']]['name'] or r['country']!=keys[r['candidate_id']]['country_hint']):raise ValueError('Backlog identity mismatch')
        if r.get('candidate_id') and r['candidate_id'] not in keys and not r['candidate_id'].startswith('supplemental-'):raise ValueError('Unknown backlog key')
        iso(r['reviewed_on'])
        if r['operation_evidence'] not in STATES or r['commercial_role'] not in ROLES or r['human_approved'] is not False or r['facility_verified'] is not False or r['automatic_collection'] is not False or r['independent_review'] is not None or r['rights']!='minimal_factual_reference_only':raise ValueError('Research cannot infer operation, licence or human approval')
        if not r['reason'] or not r['evidence'] or any(set(e)!={'url','basis'} or not url_valid(e['url']) for e in r['evidence']) or r['official_website'] and not url_valid(r['official_website']):raise ValueError('Unsafe/missing source evidence')
        if any(not isinstance(r[k],list) or len(r[k])>50 or any(not isinstance(t,str) or not t.strip() for t in r[k]) for k in ('aliases','company_claims')):raise ValueError('Invalid company claims')
    return value['reviews']

def branch_reviews(value,backlog,index):
    """Office/department evidence and dated changes cannot create studios."""
    if value.get('version')!=1 or not isinstance(value.get('reviews'),list):raise ValueError('Invalid branch research')
    iso(value['reviewed_on']);keys={r['candidate_id']:r for r in backlog['candidates']};seen=set();out=[]
    expected={'candidate_id','source_name','source_country_hint','operating_name','city','country','scope','production_status','commercial_role','reason','reviewed_on','evidence','human_approved','facility_verified','canonical_updates','rights','automatic_collection'}
    statuses={'career_page_conflicts_with_reported_change','production_not_established','company_role_self_report','production_closure_announced','production_ramp_down_announced'}
    scopes={'mixed_support_and_historical_development','regional_office','film_tv_production_office','office_production_type_unresolved'}
    for r in value['reviews']:
        c=keys.get(r.get('candidate_id'))
        if set(r)!=expected or not c or r['candidate_id'] in seen or r['source_name']!=c['name'] or r['source_country_hint']!=c['country_hint']:raise ValueError('Branch source identity/history conflict')
        seen.add(r['candidate_id']);iso(r['reviewed_on'])
        if r['human_approved'] is not False or r['facility_verified'] is not False or r['canonical_updates']!=[] or r['automatic_collection'] is not False or r['rights']!='minimal_factual_reference_only' or r['commercial_role'] not in ROLES or r['scope'] not in scopes or r['production_status'] not in statuses:raise ValueError('Branch research cannot publish a studio, closure or verified capability')
        if not r['country'] or not r['city'] or not r['reason'] or not r['evidence']:raise ValueError('Incomplete branch evidence')
        for e in r['evidence']:
            if set(e)!={'url','basis','published_on'} or not url_valid(e['url']) or e['basis'] not in ('official_location_page','official_production_change_announcement','independent_report'):raise ValueError('Unsafe branch source')
            if e['published_on']:
                iso(e['published_on'])
                if e['published_on']>r['reviewed_on']:raise ValueError('Evidence cannot be published after its recorded review')
        if r['production_status'] in ('production_closure_announced','production_ramp_down_announced') and not any(e['basis']=='official_production_change_announcement' and e['published_on'] for e in r['evidence']):raise ValueError('A disappearing link is not closure evidence')
        if r['production_status']=='career_page_conflicts_with_reported_change' and len({e['url'] for e in r['evidence'] if e['basis']=='independent_report' and e['published_on']})<2:raise ValueError('Conflicting operation assertions require corroboration')
        matching=index.match(r['operating_name'],r['country'])
        out.append({**r,'matching':matching,'disposition':'branch_or_department_research','proposal_id':None,'publication_state':'not_published','canonical_approved':False,'facility_proposal_prepared':False})
    return out

def proposed_record(review):
    # Bind identities to the frozen research key, not a website or brand spelling.
    seed=digest(review['candidate_id'])[:28];evidence=next(e['url'] for e in review['evidence'] if e['basis']!='access_failed_or_insufficient')
    return {'id':'globalcompany-'+seed,'company_id':'globalorg-'+seed,'name':review['official_name'],'city':review['city'],'country':review['country'],'lat':None,'lng':None,'website':review['official_website'] or evidence,'website_kind':'official' if review['official_website'] else 'source_listing','categories':review['company_claims'],'capabilities':[],'capability_evidence':{},'evidence_state':'unknown','evidence_class':'C','verified_on':'','source_observed_on':review['reviewed_on'],'evidence':evidence,'coordinate_precision':'unverified','coordinate_source':evidence,'location_type':'uncertain','relationships':[],'record_kind':'company_reference','identity_status':'source_provisional','status':'Research proposal only. Company self-report is not independent current-operation or physical-facility verification. No capture stage or buying intent established. Human publication review required.','license':'UNSPECIFIED','attribution':'MotionX minimal factual company reference; source-wide commercial reuse unresolved. No authored source prose, contacts or media reproduced.','research_reasons':[review['reason'],'Company service assertions do not establish capabilities at every branch.'],'potential_duplicates':[],'source_status':'company claim; independent current operation unverified','source_type':'Individual global company research','source_provenance':[{'source_id':'global-company-primary-review','source_record_id':review['candidate_id'],'url':e['url'],'license':'UNSPECIFIED','license_url':e['url'],'observed_on':review['reviewed_on'],'observation_hash':digest(review)} for e in review['evidence'] if e['basis']!='access_failed_or_insufficient']}

def proposal_conflicts(proposals,reviews):
    """Check proposals against one another as well as the frozen catalogue.

    Shared parent domains may represent distinct brands, so hold for identity
    research instead of merging, deleting or choosing one record by input order.
    """
    groups={};byid={r['proposal_id']:r for r in reviews if r.get('proposal_id')}
    for row in proposals:
        r=byid[row['id']]
        for name in {row['name'],r['name'],*r['aliases']}:
            groups.setdefault(('name_country',key(name),row['country']),set()).add(row['id'])
        domain=record_host(row)
        if domain and not shared(domain):groups.setdefault(('official_domain',domain),set()).add(row['id'])
    return [{'proposal_ids':sorted(ids),'reason':k[0],'identity_key':list(k[1:]),'human_approved':False,'resolution':'Research alias, parent/brand and country identity. No automatic merge or publication.'} for k,ids in sorted(groups.items()) if len(ids)>1]

def build(rows,home=HOME):
    checkpoint=read(home/'inputs/checkpoint.json');backlog=read(home/'inputs/backlog.json')
    validate_backlog(backlog,checkpoint)
    if len(rows)!=checkpoint['baseline_records'] or digest({r['id']:digest(r) for r in rows})!=checkpoint['record_hashes_sha256']:raise ValueError('Frozen canonical baseline changed')
    policy=scope_policy(rows,home);research=validate_reviews(read(home/'inputs/company-reviews.json'),backlog,rows);index=GlobalIndex(rows);results=[];proposals=[];bykey={}; geography=[]
    for review in research:
        match=index.match(review['official_name'],review['country'],review['official_website'],[review['name'],*review['aliases']])
        ids=match['record_ids'];supported=bool(review['company_claims']) and review['operation_evidence'] in ('primary_self_report','directory_only','corroborated_identity_official_unavailable') and review['commercial_role'] not in ('out_of_scope','adjacent_uncertain') and any(e['basis']!='access_failed_or_insufficient' for e in review['evidence'])
        coherent=match['match_status'] in ('name_and_domain','name_and_country') and len(match['company_ids'])==1
        status='research_out_of_scope' if review['commercial_role']=='out_of_scope' else 'identity_review' if review.get('identity_hold') else 'existing_identity_reconciled' if coherent else 'identity_review' if ids else 'company_proposal_prepared' if supported else 'research_unresolved'
        lineage=next((c for c in backlog['candidates'] if c['candidate_id']==review.get('candidate_id')),None)
        result={**review,'matching':match,'disposition':status,'proposal_id':None,'publication_state':'not_published','canonical_approved':False,'eligible_factual_reference':supported and not review.get('identity_hold',False),'facility_proposal_prepared':False,'backlog_evidence':{'source_urls':lineage['source_urls'],'observation_ids':lineage['observation_ids'],'original_outcomes':lineage['original_outcomes']} if lineage else None}
        if status=='company_proposal_prepared':
            record=proposed_record(review)
            if record['id'] in {r['id'] for r in proposals}:raise ValueError('Duplicate proposed operating identity')
            proposals.append(record);result['proposal_id']=record['id']
        if review.get('record_id'):
            before=index.rows[review['record_id']]
            if review['city'] and review['operation_evidence']=='primary_self_report':
                point=None
                gazetteer=ROOT/'data/research/v1.0-launch/city-references.json';ref=read(gazetteer)['references'].get(review['city'])
                if ref is None:
                    # Reuse a cited city gazetteer point, never another studio's
                    # street coordinates or a parent's geographic association.
                    existing=[r for r in read(ROOT/'studios.json') if r['city']==review['city'] and r['country']==review['country'] and r['coordinate_precision']=='city' and r.get('coordinate_source','').startswith('https://www.geonames.org/')]
                    if existing and len({(r['lat'],r['lng'],r['coordinate_source']) for r in existing})==1:
                        gazetteer=ROOT/'studios.json';r=existing[0];ref={'lat':r['lat'],'lng':r['lng'],'source':r['coordinate_source']}
                if ref and before['city']==review['city'] and before['record_kind']=='company_reference' and before['lat'] is None and ref['source'].startswith('https://www.geonames.org/'):
                    point={'lat':ref['lat'],'lng':ref['lng'],'precision':'city','coordinate_source':ref['source'],'coordinate_license':'CC-BY-4.0','license_url':'https://www.geonames.org/about.html','attribution':'GeoNames, Creative Commons Attribution 4.0. Approximate city reference; not a facility address.','gazetteer_input_sha256':sha(gazetteer)}
                geography.append({'record_id':before['id'],'name':before['name'],'before':{'city':before['city'],'country':before['country'],'lat':before['lat'],'lng':before['lng']},'proposed_company_city':review['city'],'country':review['country'],'kind':'company_city_correction_review' if before['city']!=review['city'] else 'company_city_reference_review','evidence':review['evidence'],'reviewed_on':review['reviewed_on'],'original_coordinates_changed':False,'facility_verified':False,'human_approved':False,'coordinate':point,'next_step':'Review company city, identity and licensed gazetteer before authorising a separate approximate display point. Never overwrite original coordinates.'})
        results.append(result)
        if review.get('candidate_id'):bykey[review['candidate_id']]=result
    conflicts=proposal_conflicts(proposals,results);held={rid for c in conflicts for rid in c['proposal_ids']};withheld=[r for r in proposals if r['id'] in held];proposals=[r for r in proposals if r['id'] not in held]
    for r in results:
        pid=r['proposal_id']
        if pid in held:
            r.update(disposition='identity_review',withheld_proposal_id=pid,proposal_id=None,proposal_identity_conflicts=[c for c in conflicts if pid in c['proposal_ids']])
            r['reason']+=' Within-batch name/alias or official-domain overlap requires operating-identity research; the complete withheld payload is retained in proposal-conflicts.json. No company is automatically merged or published.'
    branches=branch_reviews(read(home/'inputs/branch-reviews.json'),backlog,index)
    for r in branches:
        if r['candidate_id'] in bykey:raise ValueError('One research key cannot have conflicting company and branch reviews')
        bykey[r['candidate_id']]=r
    errors=validate_research(proposals)
    if errors:raise ValueError('; '.join(errors))
    queue=[{**c,'continuation_disposition':bykey[c['candidate_id']]['disposition'] if c['candidate_id'] in bykey else 'not_yet_individually_investigated','review':bykey.get(c['candidate_id'])} for c in backlog['candidates']]
    impact=[];roles=Counter()
    for row in rows:
        assessment=classify(row,policy);roles[assessment['role']]+=1
        if row['id'] in policy['overrides']:impact.append({'record_id':row['id'],'name':row['name'],'record_kind':row['record_kind'],'original_lat':row['lat'],'original_lng':row['lng'],'before_search_visible':True,'after_search_visible':not assessment['excluded'],'before_default_csv':True,'after_default_csv':not assessment['excluded'],'map_markers_changed':0 if row['lat'] is None else int(assessment['excluded']),'audit_mode_visible':True,'raw_record_sha256':digest(row),**assessment})
    excluded=sum(r['excluded'] for r in impact)
    summary={'starting_commit':checkpoint['starting_commit'],'reviewed_on_utc':read(home/'inputs/company-reviews.json')['reviewed_on'],'canonical_records_before':len(rows),'canonical_records_after':len(rows),'canonical_additions':0,'proposed_new_class_c_company_references':len(proposals),'individual_company_reviews':len(results),'backlog_keys_reviewed':sum(c['candidate_id'] in bykey for c in queue),'backlog_keys_remaining':sum(c['candidate_id'] not in bykey for c in queue),'backlog_observations_preserved':backlog['pending_observations'],'backlog_keys_preserved':len(queue),'research_dispositions':dict(sorted(Counter(r['disposition'] for r in results).items())),'countries_individually_investigated':len({r['country'] for r in results if r['country']}),'commercial_role_counts':dict(sorted(roles.items())),'audio_only_exclusions':excluded,'normal_results_before':len(rows),'normal_results_after':len(rows)-excluded,'audit_results_after':len(rows),'map_markers_changed':sum(r['map_markers_changed'] for r in impact),'original_records_changed':0,'geographic_review_proposals':len(geography),'new_verified_facilities':0,'new_verified_capabilities':0,'human_approved':False,'independent_precision':None,'independent_recall':None,'validation_errors':0,'warnings':['Canonical records remain frozen; company proposals have not been imported or published.','Company self-report and historical exhibitor/directory corroboration do not independently prove current operation.','725 normalized queue keys are not 725 verified distinct businesses.','No new automated collection permissions or source completeness claims.','The 14-candidate held-out evaluation still lacks independent human labels.','Role classifications derive mostly from recorded source sectors; they do not establish purchasing intent or current service availability.']}
    summary['branch_or_department_reviews']=len(branches);summary['dated_branch_change_alerts']=sum(r['production_status'] in ('career_page_conflicts_with_reported_change','production_closure_announced','production_ramp_down_announced') for r in branches);summary['branch_reviewed_on_utc']=read(home/'inputs/branch-reviews.json')['reviewed_on']
    summary['company_reviews_country_unresolved']=sum(not r['country'] for r in results);summary['cross_proposal_identity_conflicts']=len(conflicts)
    summary['all_reviewed_country_count']=len({r['country'] for r in results+branches if r['country']})
    policy['summary']={k:summary[k] for k in ('normal_results_after','audio_only_exclusions','map_markers_changed','original_records_changed')}
    countries=[]
    for country in sorted({c['country_hint'] for c in queue}|{r['country'] for r in results+branches}):
        cohort=[r for r in results if r['country']==country];countries.append({'country':country or 'Country unresolved','pending_keys_at_checkpoint':sum(c['country_hint']==country for c in queue),'individual_reviews':len(cohort),'branch_or_department_reviews':sum(r['country']==country for r in branches),'company_proposals':sum(r['disposition']=='company_proposal_prepared' for r in cohort),'identity_matches':sum(r['disposition']=='existing_identity_reconciled' for r in cohort),'unresolved_reviews':sum(r['disposition'] in ('research_unresolved','identity_review') for r in cohort),'coverage_complete':False})
    sources=[{'url':e['url'],'company':r['official_name'],'country':r['country'],'reviewed_on':r['reviewed_on'],'basis':e['basis'],'operation_evidence':r['operation_evidence'],'rights':r['rights'],'automatic_collection_enabled':False,'enumeration_scope':'Individual company evidence only; source directory not fully enumerated.','source_wide_reuse_granted':False,'human_approved':False} for r in results for e in r['evidence']]
    suspects=[{'record_id':r['id'],'name':r['name'],'country':r['country'],'website':r.get('website',''),'review_state':'individually_reviewed' if r['id'] in policy['overrides'] else 'name_signal_only_not_audio_exclusion','excluded':classify(r,policy)['excluded']} for r in rows if re.search(r'audio|sound|recording|music|mastering|mixing|\badr\b|foley',r['name'],re.I)]
    visible=[r for r in rows if not classify(r,policy)['excluded']]
    filter_impact={'records':{'before':len(rows),'after':len(visible)},'company_references':{'before':sum(r['record_kind']=='company_reference' for r in rows),'after':sum(r['record_kind']=='company_reference' for r in visible)},'game_development_sector':{'before':sum('Game Development' in r['categories'] for r in rows),'after':sum('Game Development' in r['categories'] for r in visible)},'audio_post_sector':{'before':sum('Audio Post-production' in r['categories'] for r in rows),'after':sum('Audio Post-production' in r['categories'] for r in visible)},'New Zealand_country_filter':{'before':sum(r['country']=='New Zealand' for r in rows),'after':sum(r['country']=='New Zealand' for r in visible)},'original_coordinate_records':{'before':sum(r['lat'] is not None for r in rows),'after':sum(r['lat'] is not None for r in visible)},'default_csv_rule':'Export exactly the current filtered visible results; four audio-only references remain exportable in explicit audit mode. No raw source record is overwritten.'}
    sources.extend({'url':e['url'],'company':r['operating_name'],'country':r['country'],'reviewed_on':r['reviewed_on'],'basis':e['basis'],'published_on':e['published_on'],'operation_evidence':r['production_status'],'rights':r['rights'],'automatic_collection_enabled':False,'enumeration_scope':'Individual office/department and dated event only; not proof of current production.','source_wide_reuse_granted':False,'human_approved':False} for r in branches for e in r['evidence'])
    return policy,{'version':1,'summary':summary,'reviews':results,'branches':branches,'proposals':proposals,'withheld_company_proposals':withheld,'proposal_identity_conflicts':conflicts,'geography_proposals':geography,'scope_impact':impact,'filter_impact':filter_impact,'backlog':queue,'country_progress':countries,'source_evidence_ledger':sources,'audio_scope_research_queue':suspects}

def install(public,database,home=HOME):
    public=Path(public);m,rows=records(public,database);policy,_=build(rows,home);compact(public/'commercial.json',policy)
    m['commercial_scope']={'path':'commercial.json','sha256':sha(public/'commercial.json'),'gzip_sha256':sha(public/'commercial.json.gz'),'gzip_bytes':(public/'commercial.json.gz').stat().st_size,'content_addressed':True};write(public/'manifest.json',m)

def save(report,out):
    out=Path(out);write(out/'report.json',report);write(out/'summary.json',report['summary']);write(out/'proposed-companies.json',report['proposals']);write(out/'geography-proposals.json',report['geography_proposals']);write(out/'countries.json',report['country_progress']);write(out/'source-ledger.json',report['source_evidence_ledger']);write(out/'audio-scope-research-queue.json',report['audio_scope_research_queue'])
    write(out/'branch-reviews.json',report['branches']);write(out/'proposal-conflicts.json',{'conflicts':report['proposal_identity_conflicts'],'withheld_company_proposals':report['withheld_company_proposals']})
    fields=['candidate_id','name','country_hint','continuation_disposition','source_urls','observation_ids']
    with (out/'backlog.csv').open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fields,lineterminator='\n');w.writeheader()
        for r in report['backlog']:w.writerow({k:csv_safe(json.dumps(r[k],ensure_ascii=False) if isinstance(r[k],list) else r[k]) for k in fields})
    esc=lambda x:html.escape(str(x)); sections=[]
    for r in sorted(report['reviews'],key=lambda r:(r['country'],r['official_name'].casefold())):
        links=' · '.join('<a href="'+esc(e['url'])+'" rel="noopener noreferrer">'+esc(e['basis'].replace('_',' '))+'</a>' for e in r['evidence'])
        sections.append('<article data-company-review data-country="'+esc(r['country'])+'" data-disposition="'+esc(r['disposition'])+'"><h3>'+esc(r['official_name'])+' · '+esc(r['country'] or 'Country unresolved')+'</h3><p><strong>'+esc(r['disposition'].replace('_',' '))+'</strong> · '+esc(LABELS[r['commercial_role']])+'</p><p>'+esc(r['reason'])+'</p><p>Company claims: '+esc(', '.join(r['company_claims']) or 'Insufficient evidence')+'. City: '+esc(r['city'] or 'Unresolved')+'. Reviewed '+esc(r['reviewed_on'])+' UTC.</p><p>Matches: '+esc(', '.join(r['matching']['record_ids']) or 'No name/domain match in complete catalogue')+' · '+esc(r['matching']['reason'])+'</p><p>'+links+'</p></article>')
    impact=''.join('<li>'+esc(r['name'])+': '+('excluded from normal search/map/CSV; retained in audit mode' if r['excluded'] else 'retained: multidisciplinary visual/audio provider')+'. '+esc(r['reason'])+'</li>' for r in report['scope_impact'])
    country_table='<div class="table-scroll"><table><caption>Backlog progress by country; no national census is complete</caption><tr><th>Country</th><th>Keys at checkpoint</th><th>Reviewed</th><th>Proposals</th><th>Existing matches</th><th>Still uncertain</th></tr>'+''.join('<tr>'+''.join('<td>'+esc(r[k])+'</td>' for k in ('country','pending_keys_at_checkpoint','individual_reviews','company_proposals','identity_matches','unresolved_reviews'))+'</tr>' for r in report['country_progress'])+'</table></div>'
    document='<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>MotionX company research continuation</title><style>body{background:#11151d;color:#e8ecf1;font:17px/1.55 system-ui;max-width:1100px;margin:auto;padding:24px;overflow-wrap:anywhere}a{color:#6cddf5}article{border:1px solid #485466;border-radius:12px;padding:16px;margin:16px 0}pre{white-space:pre-wrap;overflow-wrap:anywhere}.table-scroll{overflow:auto}td,th{text-align:left;padding:6px;border-bottom:1px solid #485466}a:focus{outline:3px solid #fff}</style><h1>Global company research continuation</h1><p>Research proposals only. No canonical additions, verified facilities, purchasing intent, human approval or publication asserted. Current website self-report is not independent verification.</p><nav><a href="#companies">Company/country reviews</a> · <a href="#scope">Scope impact</a> · <a href="proposed-companies.json">Actual Class C payloads</a> · <a href="proposal-conflicts.json">Within-batch identity holds</a> · <a href="geography-proposals.json">Geographic proposals</a> · <a href="backlog.csv">Complete remaining queue</a> · <a href="source-ledger.json">Source rights and access ledger</a> · <a href="audio-scope-research-queue.json">Unreviewed name signals (not exclusions)</a> · <a href="report.json">Machine report</a> · <a href="../../reports/dashboard.html">Starting programme dashboard</a></nav><h2>Measured checkpoint</h2><pre>'+esc(json.dumps(report['summary'],indent=2,ensure_ascii=False))+'</pre>'+country_table+'<h2 id="scope">Reversible scope review</h2><ul>'+impact+'</ul><h2 id="companies">Company reviews grouped by country and operating name</h2>'+''.join(sections)+'<h2>Human review remains required</h2><p>Review each proposal, identity match, source rights and company-city correction before a separate authorised publication change. These tools cannot apply records or invent human labels. The complete queue retains every original observation. Access failures do not establish closures; no source has been fully enumerated by this cohort.</p></html>\n'
    country_options=''.join(('<option>'+esc(c)+'</option>' if c else '<option value="__unknown__">Country unresolved</option>') for c in sorted({r['country'] for r in report['reviews']+report['branches']}))
    disposition_options=''.join('<option value="'+esc(c)+'">'+esc(c.replace('_',' '))+'</option>' for c in sorted({r['disposition'] for r in report['reviews']+report['branches']}))
    controls='<div><label>Find company or evidence question <input id="reviewSearch" type="search"></label> <label>Country <select id="reviewCountry"><option value="">All reviewed countries</option>'+country_options+'</select></label> <label>Disposition <select id="reviewDisposition"><option value="">All review outcomes</option>'+disposition_options+'</select></label> <p id="reviewCount" role="status" aria-live="polite">All '+str(len(report['reviews'])+len(report['branches']))+' individual reviews shown.</p></div>'
    script="""<script>
    (()=>{const $=id=>document.getElementById(id),rows=[...document.querySelectorAll('[data-company-review]')],fold=s=>s.normalize('NFKD').replace(/[\\u0300-\\u036f]/g,'').toLowerCase();function render(){const words=fold($('reviewSearch').value).trim().split(/\\s+/).filter(Boolean);let count=0;for(const row of rows){row.hidden=!!($('reviewCountry').value&&(row.dataset.country||'__unknown__')!==$('reviewCountry').value||$('reviewDisposition').value&&row.dataset.disposition!==$('reviewDisposition').value||!words.every(w=>fold(row.textContent).includes(w)));if(!row.hidden)count++;}$('reviewCount').textContent=count+' of '+rows.length+' individual reviews shown. This is not complete global coverage.';}for(const id of ['reviewSearch','reviewCountry','reviewDisposition'])$(id).addEventListener('input',render);})();
    </script>"""
    branches='<h2 id="branches">Office, branch and department investigations</h2><p>These are not new company or facility payloads. Dated production changes do not automatically close organisations, delete source records or create current capabilities. <a href="branch-reviews.json">Machine-readable branch/change audit</a></p>'+''.join('<article data-company-review data-branch-review data-country="'+esc(r['country'])+'" data-disposition="branch_or_department_research"><h3>'+esc(r['operating_name'])+' · '+esc(r['city']+', '+r['country'])+'</h3><p><strong>'+esc(r['production_status'].replace('_',' '))+'</strong> · '+esc(r['scope'].replace('_',' '))+'</p><p>'+esc(r['reason'])+'</p><p>Reviewed '+esc(r['reviewed_on'])+' UTC. Existing match candidates: '+esc(', '.join(r['matching']['record_ids']) or 'No exact operating-name match')+'. No canonical change or independent facility verification.</p><p>'+' · '.join('<a href="'+esc(e['url'])+'" rel="noopener noreferrer">'+esc(e['basis'].replace('_',' '))+((' · '+esc(e['published_on'])) if e['published_on'] else '')+'</a>' for e in r['evidence'])+'</p></article>' for r in report['branches'])
    document=document.replace('<h2 id="companies">Company reviews grouped by country and operating name</h2>','<h2>Search, map, filters and CSV impact</h2><pre>'+esc(json.dumps(report['filter_impact'],indent=2))+'</pre><h2 id="companies">Company reviews grouped by country and operating name</h2>'+controls).replace('<h2>Human review remains required</h2>',branches+'<h2>Human review remains required</h2>').replace('</nav>',' · <a href="#branches">Branch and production-change alerts</a></nav>').replace('</html>',script+'</html>')
    (out/'dashboard.html').write_text(document,encoding='utf-8')

def check(home=HOME):
    m,rows=records(ROOT/'data/public',ROOT/'studios.json');policy,report=build(rows,home)
    if report!=read(home/'reports/report.json') or policy!=read(ROOT/'data/public/commercial.json'):raise ValueError('Stale continuation report or scope projection')
    if sha(ROOT/'studios.json')!=read(home/'inputs/checkpoint.json')['root_sha256']:raise ValueError('Retained root database changed')
    with tempfile.TemporaryDirectory() as tmp:
        save(report,tmp)
        for p in Path(tmp).iterdir():
            if not (home/'reports'/p.name).is_file() or p.read_bytes()!=(home/'reports'/p.name).read_bytes():raise ValueError('Stale generated continuation artifact: '+p.name)
    d=m.get('commercial_scope',{})
    if d.get('path')!='commercial.json' or d.get('sha256')!=sha(ROOT/'data/public/commercial.json') or d.get('gzip_sha256')!=sha(ROOT/'data/public/commercial.json.gz') or d.get('gzip_bytes')!=(ROOT/'data/public/commercial.json.gz').stat().st_size:raise ValueError('Commercial scope transport mismatch')
    return report['summary']

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('command',choices=('prepare','check'));a=p.parse_args()
    if a.command=='prepare':
        _,rows=records(ROOT/'data/public',ROOT/'studios.json');_,report=build(rows);install(ROOT/'data/public',ROOT/'studios.json');save(report,HOME/'reports');result=report['summary']
    else:result=check()
    print(json.dumps(result,indent=2,ensure_ascii=False))
