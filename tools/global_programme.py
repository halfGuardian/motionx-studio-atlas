#!/usr/bin/env python3
"""Offline global reconciliation, source coverage and incremental review.

No network collection, canonical writes, automatic mergers, closures or approvals.
All records are factual research projections; source restrictions remain scoped.
"""
import argparse, copy, csv, gzip, hashlib, html, io, json, re, tempfile
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path
from urllib.parse import urlsplit
from discovery import ROOT, read, write, digest
from launch_readiness import records
from bulk_catalog import sha
from boutique import region, record_host, host, shared, source_inputs as boutique_inputs
from annecy_match import IdentityIndex, key, place
from nz_research import source_inputs as nz_inputs
from nz_quality_gate import csv_safe
from validate import url_valid
from triage import classify as classify_discovery

HOME=ROOT/'data/global-programme'
OUTCOMES={'represented_source_identity','existing_company','company_geography_pending','possible_alias','identity_conflict','potential_new_company','additional_branch_review','historical_review','out_of_scope','research_required','duplicate_observation'}
MAX_RECORDS=100000
MAX_BYTES=50_000_000
MAX_STATE_BYTES=500_000_000
FIELDS={'source_record_id','name','website','city','country','aliases','service_claims','source_url','observed_on','source_updated_on','relationship_claims','location_claim','status_claim'}
FRESHNESS={'company_identity_days':365,'geographic_evidence_days':365,'company_service_claim_days':180,'facility_capability_days':180,'source_policy_days':90}


def iso(value):
    if not isinstance(value,str) or date.fromisoformat(value).isoformat()!=value or value>date.today().isoformat():raise ValueError('Invalid actual observation date')
    return value


def bounded(path,limit=MAX_BYTES):
    path=Path(path)
    if path.stat().st_size>limit:raise ValueError('Input exceeds parsing limit')
    return read(path)


def validate_assessments(value):
    if value.get('version')!=1 or not isinstance(value.get('sources'),list):raise ValueError('Invalid source-assessment schema')
    iso(value['reviewed_on']);seen=set()
    for row in value['sources']:
        if row['id'] in seen or row.get('automatic_collection') is not False or row.get('fully_enumerated') is not False or row.get('human_approved') is not False or row.get('records_admitted')!=0:raise ValueError('Assessment cannot grant collection, completeness or approval')
        seen.add(row['id']);iso(row['observed_on'])
        for field in ('url','robots_url','terms_url'):
            if (field!='terms_url' or row.get(field)) and not url_valid(row.get(field,'')):raise ValueError('Unsafe source-assessment URL')
        if type(row.get('accessible_pages')) is not int or row['accessible_pages']<0:raise ValueError('Invalid page enumeration count')
    return value['sources']


def normalise(row):
    if not isinstance(row,dict) or set(row)-FIELDS:raise ValueError('Unsupported/private observation fields')
    result={'website':'','city':'','country':'','aliases':[],'service_claims':[],'relationship_claims':[],'location_claim':'','status_claim':'',**copy.deepcopy(row)}
    for k in ('source_record_id','name','website','city','country','source_url','observed_on','location_claim','status_claim'):
        if not isinstance(result.get(k),str) or len(result[k])>2000 or any(ord(c)<32 for c in result[k]):raise ValueError('Invalid bounded observation text: '+k)
    if not result['source_record_id'] or not result['name'].strip() or len(result['name'])>300:raise ValueError('Stable source ID and name required')
    for k in ('aliases','service_claims','relationship_claims'):
        if not isinstance(result[k],list) or len(result[k])>100 or any(not isinstance(v,str) or len(v)>500 for v in result[k]):raise ValueError('Invalid claim/alias list')
    if result['website'] and '://' not in result['website']:result['website']='https://'+result['website']
    for k in ('website','source_url'):
        if (k=='source_url' or result[k]) and not url_valid(result[k]):raise ValueError('Unsafe evidence URL')
    iso(result['observed_on'])
    if result.get('source_updated_on'):iso(result['source_updated_on'])
    result['country']=place(result['country'])
    return result


def load_snapshot(path,policy,metadata=None):
    """An explicit reviewed dataset grant is needed even for offline new inputs.

    CSV accepts only the public factual fields above; list columns are JSON.
    The tool has no URL fetch option. Existing historical projections are replayed
    separately, without retroactively granting bulk reuse or enabling a crawler.
    """
    if policy.get('mode')!='reviewed_dataset_replay' or policy.get('reuse_decision')!='scoped_dataset_permission' or policy.get('human_approved') is not False:raise ValueError('Source permission/replay policy not admitted')
    if not url_valid(policy.get('license_url','')) or not policy.get('attribution') or not policy.get('license'):raise ValueError('Scoped licence and attribution required')
    iso(policy['reviewed_on'])
    if policy.get('permission_expires_on') and policy['permission_expires_on']<date.today().isoformat():raise ValueError('Permission review expired')
    path=Path(path)
    if path.stat().st_size>MAX_BYTES:raise ValueError('Input exceeds parsing limit')
    if path.suffix=='.csv':
        if not metadata:raise ValueError('CSV requires explicit snapshot metadata')
        source=[]
        with path.open(encoding='utf-8-sig',newline='') as f:
            reader=csv.DictReader(f)
            if not reader.fieldnames or len(set(reader.fieldnames))!=len(reader.fieldnames) or set(reader.fieldnames)-FIELDS:raise ValueError('Unsupported/private CSV columns')
            for row in reader:
                if len(source)>=MAX_RECORDS:raise ValueError('Record parsing limit')
                for k in ('aliases','service_claims','relationship_claims'):
                    if row.get(k):row[k]=json.loads(row[k])
                    else:row.pop(k,None)
                source.append(row)
        data={**metadata,'records':source}
    else:data=bounded(path)
    if set(data)-{'version','source_id','snapshot_id','observed_on','status','complete','expected_records','source_url','license','records','failure','enumeration_scope'}:raise ValueError('Unsupported snapshot fields')
    if data.get('version')!=1 or not isinstance(data.get('source_id'),str) or not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*',data['source_id']) or len(data['source_id'])>100:raise ValueError('Invalid snapshot schema/source identity')
    if data.get('source_id')!=policy['source_id'] or data.get('license')!=policy['license'] or not data.get('snapshot_id') or len(str(data['snapshot_id']))>150:raise ValueError('Source/snapshot licence conflict')
    iso(data['observed_on'])
    if not url_valid(data.get('source_url','')) or data.get('status') not in ('success','partial','failed') or type(data.get('complete')) is not bool:raise ValueError('Invalid access/completeness receipt')
    if not isinstance(data.get('records'),list) or len(data['records'])>MAX_RECORDS:raise ValueError('Record parsing limit')
    if not isinstance(data.get('enumeration_scope'),str) or not data['enumeration_scope']:raise ValueError('Explicit enumeration scope required')
    rows=[normalise(r) for r in data['records']]
    if any(r['observed_on']>data['observed_on'] for r in rows):raise ValueError('Observation newer than snapshot receipt')
    ids=[r['source_record_id'] for r in rows]
    if len(ids)!=len(set(ids)):raise ValueError('Duplicate/conflicting source IDs')
    if data['complete'] and (data['status']!='success' or type(data.get('expected_records')) is not int or data['expected_records']!=len(rows)):raise ValueError('Unsubstantiated complete enumeration')
    if data['status']=='failed' and (rows or not data.get('failure')):raise ValueError('Failed fetch must retain a failure, never a replacement empty roster')
    return {**data,'records':rows,'input_sha256':sha(path),'policy_hash':digest(policy),'automatic_publication':False}


def registered_snapshots(home=HOME,root=ROOT):
    """Admit reviewed local CSV/JSON snapshots to the same global review path.

    Registry entries are repository data paths, never URLs or shell commands.
    Each change is reviewable in a PR. A failed/partial snapshot cannot replace
    published records or remove any retained research/history.
    """
    registry=bounded(home/'inputs/snapshot-registry.json')
    if registry.get('version')!=1 or not isinstance(registry.get('sources'),list) or len(registry['sources'])>1000:raise ValueError('Invalid bounded snapshot registry')
    out=[];ledgers=[];seen=set()
    def local(name):
        path=Path(name)
        if path.is_absolute() or '..' in path.parts or not path.parts or path.parts[0]!='data':raise ValueError('Only repository data paths may be registered')
        target=root/path
        if target.is_symlink() or not target.resolve().is_relative_to((root/'data').resolve()):raise ValueError('Registry path escapes public research data')
        return target
    for entry in registry['sources']:
        if set(entry)-{'source_id','policy','snapshot','metadata','state'} or entry.get('source_id') in seen:raise ValueError('Duplicate/unsupported registered source')
        seen.add(entry['source_id']);policy_path=local(entry['policy']);snapshot_path=local(entry['snapshot']);metadata_path=local(entry['metadata']) if entry.get('metadata') else None
        policy=bounded(policy_path)
        if policy['source_id']!=entry['source_id']:raise ValueError('Registered source-policy identity conflict')
        snapshot=load_snapshot(snapshot_path,policy,bounded(metadata_path) if metadata_path else None)
        state_path=local(entry['state']);state=check_state(bounded(state_path,MAX_STATE_BYTES))
        if digest(state['sources'].get(entry['source_id']))!=digest(snapshot):raise ValueError('Registered snapshot/state head mismatch; run incremental first')
        events=[e for e in state['history'] if e['source_id']==entry['source_id']]
        if any(e['snapshot']['policy_hash']!=snapshot['policy_hash'] or e['snapshot']['license']!=policy['license'] for e in events):raise ValueError('Historical source-policy scope changed; preserve prior reports and review the policy revision')
        ledgers.append({'source_id':entry['source_id'],'origin':'registered_dataset_snapshot','records':len(snapshot['records']),'expected_records':snapshot.get('expected_records'),'complete_declared_snapshot':snapshot['complete'],'snapshot_id':snapshot['snapshot_id'],'observed_on':snapshot['observed_on'],'source_url':snapshot['source_url'],'input_hash':snapshot['input_sha256'],'policy_hash':snapshot['policy_hash'],'policy_path':entry['policy'],'policy_reviewed_on':policy['reviewed_on'],'snapshot_path':entry['snapshot'],'metadata_sha256':sha(metadata_path) if metadata_path else None,'scope':snapshot['enumeration_scope'],'access_status':snapshot['status'],'failure':snapshot.get('failure'),'rights':policy['license'],'license_url':policy['license_url'],'attribution':policy['attribution'],'current_operation_independently_verified':False})
        ledgers[-1].update(state_path=entry['state'],state_sha256=sha(state_path),historical_snapshots=len(events),review_signals=[s for event in events for s in event['signals']],current_snapshot_records=len(snapshot['records']))
        start=len(out)
        for event in events:
            version=event['snapshot']
            if len(version['records'])>MAX_RECORDS:raise ValueError('Historical snapshot exceeds parsing limit')
            for raw in version['records']:
                row=normalise(raw)
                out.append({**row,'source_id':entry['source_id'],'origin':'registered_dataset_snapshot','origin_hash':digest([version['snapshot_id'],row]),'historical_rights':policy['license'],'source_snapshot_id':version['snapshot_id'],'attribution':policy['attribution'],'license_url':policy['license_url'],'source_enumeration_complete':version['complete'],'source_change_signals':[s for s in event['signals'] if s.get('source_record_id')==row['source_record_id']]})
        ledgers[-1]['records']=len(out)-start
    return out,ledgers


def empty_state():
    return {'version':1,'sources':{},'history':[],'human_approved':False,'canonical_updates':[]}


def check_state(state):
    if set(state)!=set(empty_state()) or state['human_approved'] is not False or state['canonical_updates']!=[] or not isinstance(state['history'],list) or not isinstance(state['sources'],dict):raise ValueError('Unsafe maintenance state')
    previous=None
    for event in state['history']:
        if event.get('previous_hash')!=previous or event.get('event_hash')!=digest({k:v for k,v in event.items() if k!='event_hash'}):raise ValueError('Corrupted or missing snapshot history')
        if digest(event.get('snapshot'))!=event.get('snapshot_hash'):raise ValueError('Historical snapshot integrity failure')
        previous=event['event_hash']
    # Every mutable head is bound by the final event for that source.
    heads={e['source_id']:e['snapshot_hash'] for e in state['history']}
    if set(heads)!=set(state['sources']):raise ValueError('History/source head discontinuity')
    for sid,source in state['sources'].items():
        if heads[sid]!=digest(source):raise ValueError('Snapshot head integrity failure')
    return state


def advance(state,snapshot,freshness=None):
    """Append-only review signals. Missing/failed/partial history cannot close studios."""
    check_state(state);state=copy.deepcopy(state);sid=snapshot['source_id'];old=state['sources'].get(sid);signals=[]
    if old and old.get('snapshot_id')==snapshot['snapshot_id']:
        if digest(old)!=digest(snapshot):raise ValueError('Snapshot ID reused with changed content')
        return state,[]
    if old and snapshot['observed_on']<old['observed_on']:raise ValueError('Out-of-order snapshot; preserve as historical evidence separately')
    # Keep the last known facts across a failure or partial snapshot. Absence
    # comparisons still require the immediate head to be a complete success.
    oldrows={}
    for event in state['history']:
        if event['source_id']==sid:oldrows.update({r['source_record_id']:r for r in event['snapshot']['records']})
    previous_head_rows={r['source_record_id']:r for r in (old or {}).get('records',[])};newrows={r['source_record_id']:r for r in snapshot['records']}
    if snapshot['status']=='failed':signals.append({'kind':'source_failure','reason':snapshot['failure'],'closure_inference':False})
    else:
        for rid,r in sorted(newrows.items()):
            if rid not in oldrows:signals.append({'kind':'newly_observed','source_record_id':rid,'after':r,'not_necessarily_new_business':True})
            elif digest(oldrows[rid])!=digest(r):
                changed=[k for k in FIELDS if oldrows[rid].get(k)!=r.get(k)]
                fact_changes=set(changed)-{'observed_on','source_updated_on'}
                signals.append({'kind':'possible_identity_geography_service_change' if fact_changes else 'evidence_refreshed','source_record_id':rid,'changed_fields':sorted(changed),'before':oldrows[rid],'after':r,'human_review_required':True})
        coherent=bool(old and old['complete'] and snapshot['complete'] and old['status']==snapshot['status']=='success' and old['enumeration_scope']==snapshot['enumeration_scope'] and old['policy_hash']==snapshot['policy_hash'])
        if coherent:
            for rid in sorted(set(previous_head_rows)-set(newrows)):signals.append({'kind':'source_absence_investigation','source_record_id':rid,'before':previous_head_rows[rid],'closure_inference':False,'reason':'Absent from comparable complete snapshots; not evidence of closure.'})
        elif old:signals.append({'kind':'history_incomplete_no_absence_inference','closure_inference':False})
    for r in snapshot['records']:
        age=(date.fromisoformat(snapshot['observed_on'])-date.fromisoformat(r.get('source_updated_on') or r['observed_on'])).days
        if age>(freshness or FRESHNESS)['company_identity_days']:signals.append({'kind':'stale_source_assertion','source_record_id':r['source_record_id'],'age_days':age,'human_review_required':True})
    state['sources'][sid]=snapshot
    event={'source_id':sid,'snapshot_id':snapshot['snapshot_id'],'snapshot_hash':digest(snapshot),'previous_hash':state['history'][-1]['event_hash'] if state['history'] else None,'snapshot':snapshot,'signals':signals}
    event['event_hash']=digest(event);state['history'].append(event);check_state(state)
    return state,signals


class GlobalIndex(IdentityIndex):
    def __init__(self,rows):
        super().__init__(rows);self.provenance=defaultdict(set)
        for r in rows:
            for p in r.get('source_provenance',[]):self.provenance[p.get('source_id'),p.get('source_record_id')].add(r['id'])

    def resolve(self,o):
        ids=self.provenance.get((o['source_id'],o['source_record_id']),set())
        if ids:
            result=self.result(ids,'source_identity','high','Existing source-specific identity key. This binds a retained observation, not a verified current business or branch.')
            if len(result['company_ids'])>1 or not any(key(o['name'])==key(self.rows[i]['name']) for i in ids):
                result.update(confidence='low',reason='Source identity key has multiple operating identities or changed operating-name evidence. Preserve all values; investigate rebrand, ownership or ID collision.')
                return result,'identity_conflict'
            return result,'represented_source_identity'
        result=self.match(o['name'],o.get('country',''),o.get('website',''),o.get('aliases',[]));ids=result['record_ids'];countries={place(self.rows[i]['country']) for i in ids}
        if len(result['company_ids'])>1 and result['match_status'] in ('name_and_domain','name_and_country'):return result,'identity_conflict'
        if ids and o.get('country') and place(o['country']) not in countries:return result,'company_geography_pending'
        if result['match_status'] in ('name_and_domain','name_and_country'):return result,'existing_company'
        if result['match_status']=='possible_alias':return result,'possible_alias'
        if ids:return result,'identity_conflict'
        return result,'potential_new_company'


def observations(rows,home=HOME):
    """Replay retained source facts plus entire existing bounded research snapshots.

    Replaying old inputs is not new collection or retroactive permission approval.
    Every duplicate observation is retained with its original input hash.
    """
    out=[];ledgers=[]
    for r in rows:
        for p in r.get('source_provenance',[]):
            out.append({'source_id':p['source_id'],'source_record_id':p['source_record_id'],'name':r['name'],'website':r['website'] if r.get('website_kind')!='source_listing' else '', 'country':r['country'],'city':r['city'],'source_url':p['url'],'observed_on':p['observed_on'],'service_claims':r['categories'],'aliases':[],'relationship_claims':[],'origin':'retained_provenance','origin_hash':digest([r['id'],p]),'historical_rights':p['license']})
    policies,boutique,inputs=boutique_inputs()
    for a in inputs:ledgers.append({'source_id':a['source_id'],'origin':'existing_boutique_snapshot','records':a['raw_records'],'complete_declared_snapshot':a['complete'],'input_hash':a['sha256'],'scope':'Complete supplied snapshot only; not present operation or whole-country coverage.'})
    for o in boutique:
        out.append({k:o.get(k,'') for k in ('source_id','source_record_id','name','website','country','city','source_url','observed_on','source_updated_on')}|{'service_claims':o['animation_types'],'aliases':[],'relationship_claims':[],'origin':'existing_boutique_snapshot','origin_hash':o['observation_hash'],'historical_rights':o['license']})
    exhibits=read(ROOT/'data/annecy/inputs/exhibitors.json')
    for e in exhibits['records']:
        out.append({'source_id':'annecy-2024-event','source_record_id':e['exhibitor_id'],'name':e['name'],'website':'','country':place(e['listed_country']),'city':'','source_url':'https://www.annecyfestival.com/','observed_on':'2026-11-07','service_claims':[e['listed_activity']],'aliases':[],'relationship_claims':[],'origin':'user_supplied_historical_event','origin_hash':e['source_row_hash'],'historical_rights':'UNSPECIFIED','activity':e['listed_activity']})
    ledgers.append({'source_id':'annecy-2024-event','origin':'user_supplied_historical_event','records':len(exhibits['records']),'complete_declared_snapshot':True,'input_hash':sha(ROOT/'data/annecy/inputs/exhibitors.json'),'scope':'1,074 supplied exhibitor rows, including non-studios; historical 2024 participation, no blanket database reuse grant.'})
    registry,policies,nz,assessments=nz_inputs()
    for o in nz:
        out.append({'source_id':o['source_id'],'source_record_id':o['observation_id'],'name':o['name'],'website':o.get('site_url') or '', 'country':'New Zealand','city':'','source_url':o['source_url'],'observed_on':o['observed_on'],'service_claims':o['service_labels'],'aliases':[],'relationship_claims':[],'origin':'retained_nz_research','origin_hash':digest(o),'historical_rights':policies[o['source_id']]['license'],'location_claim':o.get('location_claim','')})
    for sid,p in policies.items():ledgers.append({'source_id':sid,'origin':'retained_nz_research','records':sum(o['source_id']==sid for o in nz),'complete_declared_snapshot':p['access_audit']['declared_complete'],'input_hash':digest(p),'scope':p['scope'],'rights':p['permission']})
    # Retain each checkpoint's observations; shared candidate IDs are accounted
    # as repeat evidence, never removed or promoted to approved business records.
    queues=[ROOT/'data/discovery/backlog.json',*sorted((ROOT/'data/research').glob('**/queue.json'))]
    discovery_policies={s['id']:s for s in read(ROOT/'data/discovery/sources.json')['sources']}
    for path in queues:
        queue=read(path);candidates=queue.get('candidates',{})
        if not isinstance(candidates,dict):raise ValueError('Invalid historical discovery queue')
        for candidate_id,candidate in sorted(candidates.items()):
            if candidate.get('id')!=candidate_id or not url_valid(candidate.get('url','')):raise ValueError('Historical candidate identity/evidence conflict')
            observed=candidate.get('last_seen') or candidate.get('first_seen');iso(observed)
            out.append({'source_id':candidate['source_id'],'source_record_id':candidate_id,'name':candidate['label'],'website':'','city':candidate.get('city',''),'country':place(candidate.get('country','')),'source_url':candidate['url'],'observed_on':observed,'service_claims':[],'aliases':[],'relationship_claims':[],'origin':'retained_discovery_checkpoint','origin_hash':digest([str(path.relative_to(ROOT)),candidate]),'historical_rights':'UNSPECIFIED','original_queue_path':str(path.relative_to(ROOT)),'original_review_status':candidate.get('review_status','unknown'),'original_candidate_sha256':digest(candidate),'first_seen':candidate.get('first_seen'),'missing_since_source_assertion':candidate.get('missing_since'),'closure_inference':False})
            out[-1]['historical_candidate_triage']=classify_discovery(candidate,discovery_policies.get(candidate['source_id']),rows,[])
        for sid,n in sorted(Counter(c['source_id'] for c in candidates.values()).items()):
            ledgers.append({'source_id':sid,'origin':'retained_discovery_checkpoint','records':n,'complete_declared_snapshot':False,'input_hash':sha(path),'scope':'Retained observations in '+str(path.relative_to(ROOT))+'; not complete discovery history or a source roster. All original candidate values are preserved.'})
    additional,scopes=registered_snapshots(home);out.extend(additional);ledgers.extend(scopes)
    return out,ledgers


def reconcile(rows,obs,as_of):
    index=GlobalIndex(rows);seen={};output=[]
    for n,o in enumerate(obs):
        uid='global-obs-'+digest([o['source_id'],o['source_record_id'],o['origin'],o['origin_hash']])[:24]
        match,status=index.resolve(o);dedup=(o['source_id'],o['source_record_id']);previous=seen.get(dedup)
        if previous:
            changed=any(s['kind']=='possible_identity_geography_service_change' for s in o.get('source_change_signals',[]))
            status='research_required' if changed else 'duplicate_observation';reason='Stable source identity has changed name, geography, relationship or service assertions; before/after evidence retained for human review.' if changed else 'Repeated source identity retained for provenance; no additional business/facility created.'
        else:
            seen[dedup]=uid;reason=match['reason']
            if o.get('historical_candidate_triage'):
                triage=o['historical_candidate_triage'];kind=triage['classification']
                status={'irrelevant':'out_of_scope','requires_research':'research_required','already_represented':'existing_company','potentially_new':'additional_branch_review'}[kind]
                reason='Historical discovery matching only: '+' '.join(triage['reasons'])
                ids=triage['matched_location_ids']
                if ids:match=index.result(ids,'source_specific_discovery_triage','medium',reason)
            if o.get('activity'):
                activity=o['activity'].casefold()
                if not any(t in activity for t in ('animation studio','development studio','video game studio','production company','service provider','agency','not specified')):
                    status='out_of_scope';reason='Historical event activity supplies no production-studio evidence. Excluded from this projection; no existing record is removed.'
                elif status=='potential_new_company' and not any(t in activity for t in ('animation studio','development studio','video game studio')):
                    status='research_required';reason='General production, agency or unspecified exhibitor needs specialist-production qualification before a studio proposal.'
        country=place(o.get('country',''));geography='company_country_association' if country else 'unknown'
        output.append({**o,'observation_id':uid,'disposition':status,'research_region':region(country),'matching':match,'matching_reason':reason,'duplicate_of':previous,'identity_claim_state':'source_listed_unverified','geographic_evidence':{'scope':geography,'city_claim':o.get('city',''),'facility_verified':False,'coordinate_proposal':None,'inherit_parent_geography':False},'service_evidence':{'company_source_claims':o.get('service_claims',[]),'facility_confirmed_capabilities':[],'claim_state':'source_assertion_not_facility_verification'},'evidence_age_days':(date.fromisoformat(as_of)-date.fromisoformat(o['observed_on'])).days,'relationship_claims':o.get('relationship_claims',[]),'human_approved':False,'canonical_update':None})
        output[-1]['observation_age_days']=output[-1].pop('evidence_age_days')
        updated=o.get('source_updated_on');output[-1]['source_assertion_age_days']=(date.fromisoformat(as_of)-date.fromisoformat(updated)).days if updated else None
        output[-1]['freshness_state']='historical_event_current_operation_unknown' if o['origin']=='user_supplied_historical_event' else 'source_snapshot_stale_review' if updated and output[-1]['source_assertion_age_days']>FRESHNESS['company_service_claim_days'] else 'source_assertion_date_not_established' if not updated else 'dated_source_assertion_not_current_operation_verification'
    return output


def upstream_registry():
    sources=[]
    for path in ('data/discovery/sources.json','data/boutique/sources.json','data/nz-census/sources.json','data/bulk/sources.json'):
        value=read(ROOT/path)
        for source in value['sources']:
            sources.append({'registry':path,'registry_sha256':sha(ROOT/path),'source_id':source['id'],'historical_policy':source,'global_collection_enabled':False,'global_mode':'retained_snapshot_review_only','rights_inherited_across_sources':False})
    return sources


def heldout(rows,obs,home=HOME):
    frozen=read(home/'inputs/heldout-sample.json');reviews=read(home/'inputs/heldout-page-reviews.json');byid={r['sample_id']:r for r in reviews['samples']};index=GlobalIndex(rows);result=[]
    observation_urls={o['source_url'] for o in obs};observation_hosts={host(u) for u in observation_urls}
    if len(byid)!=len(frozen['samples']):raise ValueError('Held-out review continuity failed')
    for r in frozen['samples']:
        if any(r[k] is not None for k in ('independent_company_label','independent_country_label','independent_facility_label','independent_capability_labels','human_reviewer')) or r['human_approved'] is not False:raise ValueError('This pending sample cannot fabricate independent labels or approvals')
        review=byid[r['sample_id']]
        if review['source_url']!=r['source_url'] or review['human_approved'] is not False:raise ValueError('Held-out source/review conflict')
        o={'source_id':'heldout-official-pages','source_record_id':r['sample_id'],'name':r['name'],'website':r['source_url'],'country':r['query_country']};match,status=index.resolve(o)
        result.append({**r,'agent_page_review':review,'model_match':match,'model_outcome':status,'exact_source_overlap_with_replay':r['source_url'] in observation_urls,'source_domain_overlap_with_replay':host(r['source_url']) in observation_hosts,'classification':'unlabelled_evaluation_only','human_approved':False})
    matched=sum(bool(r['model_match']['record_ids']) for r in result)
    return {'frozen_sample_sha256':sha(home/'inputs/heldout-sample.json'),'selection':frozen['selection'],'source_separation':frozen['source_separation'],'denominator':len(result),'model_match_candidates':matched,'model_unmatched':len(result)-matched,'model_candidate_match_fraction_not_precision_or_recall':matched/len(result),'exact_replay_source_overlap':sum(r['exact_source_overlap_with_replay'] for r in result),'domain_replay_source_overlap':sum(r['source_domain_overlap_with_replay'] for r in result),'independent_labels':0,'human_precision':None,'human_recall':None,'blind_independent_business_benchmark':False,'canonical_updates':[],'samples':result}


def build(home=HOME):
    history=read(home/'inputs/history-checkpoint.json')
    for name,expected in history['files'].items():
        path=Path(name)
        if path.is_absolute() or '..' in path.parts or sha(ROOT/path)!=expected:raise ValueError('Historical research changed: '+name)
    m,rows=records(ROOT/'data/public',ROOT/'studios.json');obs,ledgers=observations(rows,home);as_of=read(home/'inputs/source-assessments.json')['reviewed_on'];iso(as_of)
    results=reconcile(rows,obs,as_of);search=[]
    for p in sorted((home/'inputs').glob('country-source-search*.json')):search+=read(p)['countries']
    counts=Counter(r['country'] for r in rows if r['country']);searched={r['country']:r for r in search}
    if len(searched)!=len(search) or set(searched)!=set(counts):raise ValueError('Every represented country/territory needs exactly one search receipt')
    assessments=validate_assessments(bounded(home/'inputs/source-assessments.json'));country_rows=[]
    for c,n in sorted(counts.items()):
        hits=searched[c]['hits'];reviews=[s for s in assessments if s['country']==c]
        country_rows.append({'country':c,'region':region(c),'catalogue_references':n,'retained_locations':sum(r['country']==c and r['record_kind']=='retained_location' for r in rows),'company_references':sum(r['country']==c and r['record_kind']=='company_reference' for r in rows),'source_discovery':searched[c],'source_leads':len(hits),'page_assessments':len(reviews),'fully_enumerated_new_sources':0,'local_language_coverage':'not_systematically_assessed','current_industry_completeness':'not_established','human_approved':False})
    bysource={}
    for sid in sorted({o['source_id'] for o in results}|{s['source_id'] for s in ledgers}):
        group=[o for o in results if o['source_id']==sid]
        bysource[sid]={'observations':len(group),'distinct_source_keys':len({r['source_record_id'] for r in group}),'outcomes':dict(sorted(Counter(r['disposition'] for r in group).items())),'scopes':[l for l in ledgers if l['source_id']==sid],'current_worldwide_completeness':False,'new_collection_enabled':False}
    visibility=read(home/'reports/visibility-summary.json');facility=read(ROOT/'data/nz-census/final-review/inputs/facilities.json')['facilities']
    summary={'catalogue_records':len(rows),'catalogue_counts':m['counts'],'countries_and_territories':len(counts),'country_unknown_records':sum(not r['country'] for r in rows),'countries_with_source_search':len(search),'new_source_page_assessments':len(assessments),'new_sources_fully_enumerated':0,'search_source_leads':sum(len(r['hits']) for r in search),'distinct_source_lead_urls':len({hit['url'] for r in search for hit in r['hits']}),'replayed_observations':len(results),'distinct_source_identity_keys':len({(o['source_id'],o['source_record_id']) for o in results}),'registered_snapshot_rows':sum(o['origin']=='registered_dataset_snapshot' for o in results),'historical_files_retained':len(history['files']),'outcomes':dict(sorted(Counter(o['disposition'] for o in results).items())),'new_canonical_companies':0,'new_canonical_locations':0,'new_independently_verified_facilities':0,'facility_dossiers_pending':len(facility),'company_geography':visibility,'human_precision':None,'human_recall':None,'human_review_completed':0,'global_complete':False,'automatic_collection':False,'automatic_publication':False,'as_of':as_of}
    input_paths=[p for p in sorted((home/'inputs').glob('*.json')) if p.name not in ('parent-manifest.json','baseline.json')]+[ROOT/'data/boutique/sources.json',ROOT/'data/annecy/inputs/exhibitors.json',ROOT/'data/nz-census/release.json']
    return {'version':1,'summary':summary,'countries':country_rows,'sources':bysource,'source_assessments':assessments,'upstream_policies':upstream_registry(),'observations':results,'facility_dossiers':facility,'heldout':heldout(rows,obs,home),'freshness_policy':FRESHNESS,'input_hashes':{str(p.relative_to(ROOT)):sha(p) for p in input_paths},'baseline_record_hashes_sha256':digest({r['id']:digest(r) for r in rows}),'human_approved':False,'canonical_updates':[]}


def save(report,out):
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    # Compact machine reports avoid hundreds of thousands of repeated pretty lines.
    raw=(json.dumps(report,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False)+'\n').encode()
    report_hash=hashlib.sha256(raw).hexdigest();(out/'global-report.json.gz').write_bytes(gzip.compress(raw,mtime=0));(out/'global-report.json').unlink(missing_ok=True)
    for name,value in [('summary.json',report['summary']),('countries.json',report['countries']),('heldout-review.json',report['heldout']),('source-ledger.json',{'sources':report['sources'],'assessments':report['source_assessments'],'upstream_policies':report['upstream_policies']})]:
        (out/name).write_text(json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False)+'\n',encoding='utf-8')
    with (out/'reconciliation.csv').open('w',newline='',encoding='utf-8') as f:
        fields=['observation_id','source_id','source_record_id','name','country','city','disposition','matching_reason','source_url','observed_on','historical_rights','human_approved'];w=csv.writer(f,lineterminator='\n');w.writerow(fields)
        for r in report['observations']:w.writerow([csv_safe(r.get(k,'')) for k in fields])
    worksheet={'version':1,'report_sha256':report_hash,'human_approved':False,'decisions':[],'purpose':'Working review notes are not authenticated approval and cannot update the public database.'};write(out/'working-decisions.json',worksheet)
    review_fields=['observation_id','source_id','name','country','disposition','matching_reason','source_url','observed_on','service_claims','origin','city','research_region','historical_rights','source_updated_on','freshness_state','source_change_signals']
    review_index={'version':1,'report_sha256':worksheet['report_sha256'],'summary':report['summary'],'fields':review_fields+['content_hash'],'rows':[[r.get(k,'') for k in review_fields]+[digest(r)] for r in report['observations']]}
    (out/'review-index.json.gz').write_bytes(gzip.compress((json.dumps(review_index,ensure_ascii=False,separators=(',',':'))+'\n').encode(),mtime=0))
    esc=html.escape
    def table(headers,body):return '<div class="table-scroll"><table><thead><tr>'+''.join('<th scope="col">'+esc(v)+'</th>' for v in headers)+'</tr></thead><tbody>'+body+'</tbody></table></div>'
    countries=''.join('<tr><th scope="row">'+esc(c['country'])+'</th><td>'+esc(c['region'])+'</td><td>'+str(c['catalogue_references'])+'</td><td>'+str(c['source_leads'])+'</td><td>'+str(c['page_assessments'])+'</td><td>English source search only; industry completeness and local-language coverage not established</td></tr>' for c in report['countries'])
    sources=''.join('<tr><th><a rel="noopener noreferrer" href="'+esc(s['url'],quote=True)+'">'+esc(s['id'])+'</a></th><td>'+esc(s['country'])+'</td><td>'+esc(s['status'])+'</td><td>'+esc(s['rights_status'])+'</td><td>'+esc(s['note'])+'</td><td>'+str(s['accessible_pages'])+' / '+str(s['records_admitted'])+' / false</td></tr>' for s in report['source_assessments'])
    replay=''.join('<tr><th scope="row">'+esc(sid)+'</th><td>'+str(s['observations'])+'</td><td>'+str(s['distinct_source_keys'])+'</td><td>'+esc(json.dumps(s['outcomes'],sort_keys=True))+'</td><td>'+esc('; '.join(v['scope']+(' | Access: '+v['access_status']+' | observed '+v['observed_on']+' | expected '+str(v['expected_records'])+(' | '+v['failure'] if v['failure'] else '') if 'access_status' in v else '') for v in s['scopes']) or 'Retained source observations only; no new complete live roster acquired.')+'</td></tr>' for sid,s in report['sources'].items())
    alerts=[]
    for sid,s in report['sources'].items():
        for scope in s['scopes']:
            investigations=[v for v in scope.get('review_signals',[]) if v['kind'] in ('possible_identity_geography_service_change','source_absence_investigation','source_failure','history_incomplete_no_absence_inference')]
            if investigations:alerts.append('<details><summary>'+esc(sid)+' · '+str(len(investigations))+' change/failure investigation signals</summary><pre>'+esc(json.dumps(investigations,ensure_ascii=False,indent=2))+'</pre></details>')
    replay_table='<details><summary>All replayed sources and accountable reconciliation outcomes</summary>'+table(['Source','Observations','Source identity keys','Outcomes','Actual scope; not global completeness'],replay)+'</details><h2>Source change and continuity investigations</h2><p>Failed or missing sources never remove records. Source absence, name, location, ownership and service revisions are investigation signals, not business facts or approvals.</p>'+(''.join(alerts) or '<p>No change/absence claim is introduced by the registered snapshot at this checkpoint. Existing partial/inaccessible source limits remain above.</p>')
    page='''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>MotionX global coverage and review</title><style>body{background:#101822;color:#edf1f8;font:16px/1.6 system-ui;margin:auto;padding:22px;max-width:1600px;overflow-wrap:anywhere}a{color:#b6dfff}button,input,select,textarea{background:#172333;color:inherit;padding:10px;border:1px solid #8798ad;font:inherit;min-height:44px;max-width:100%;box-sizing:border-box}label{display:inline-block;margin:8px}table{border-collapse:collapse;width:100%}td,th{border:1px solid #43516a;padding:10px;text-align:left;vertical-align:top}th{font-weight:600}pre{white-space:pre-wrap;overflow-wrap:anywhere}:focus-visible{outline:3px solid #ffd77a}.table-scroll{overflow:auto}#review article{border:1px solid #43516a;border-radius:10px;padding:15px;margin:12px 0}#review{min-height:100px}.pending{color:#ffd77a}details{margin:16px 0}summary{cursor:pointer;min-height:44px}@media(max-width:650px){body{padding:12px}label{display:block;margin:8px 0}input,select{width:100%}}</style><h1>Global coverage · evidence and review</h1><p class="pending">Programme in progress. Search leads ≠ enumerated directories ≠ distinct companies ≠ verified facilities. No automated publication or human approval.</p><p><a href="../../../index.html">Atlas</a> · <a href="../PROGRAMME.md">Programme and resume commands</a> · <a href="global-report.json.gz">Complete accountable JSON</a> · <a href="reconciliation.csv">Reconciliation CSV</a> · <a href="unpinned-companies.csv">All unpinned companies</a> · <a href="source-ledger.json">Source policy and enumeration ledger</a></p><div id="summary"></div><details><summary>Every represented country or territory</summary>'''+table(['Country/territory','Research region','References','Source leads','Page assessments','Remaining work'],countries)+'''</details><details open><summary>Actual new source access and permission assessments</summary>'''+table(['Source','Query geography','Access result','Reuse status','Scope, boutiques and gaps','Pages / admitted records / complete'],sources)+'''</details><p>Queries are English-language first passes. A source found for a country may cover other countries or be irrelevant. All result URLs/titles and dates remain in the machine report. No source-wide licence is inferred from public access. Existing restricted sources remain disabled.</p><h2>Every admitted/replayed observation</h2><p>Claim states apply separately to identity, geographic association, company services and facility capabilities. Historical snapshots retain their original rights limitations. Selecting an outcome below only drafts notes; it cannot approve or publish records.</p><label>Search<input id="q" type="search"></label><label>Country<select id="country"><option value="">All countries</option></select></label><label>Region<select id="region"><option value="">All regions</option></select></label><label>Source rights<select id="rights"><option value="">All historical rights</option></select></label><label>Source<select id="source"><option value="">All sources</option></select></label><label>Outcome<select id="outcome"><option value="">All outcomes</option></select></label><p id="count" role="status" aria-live="polite">Loading complete report…</p><div id="review"></div><button id="previous">Previous 25</button> <button id="next">Next 25</button><p><button id="exportJson">Export working decisions JSON</button> <button id="exportCsv">Export working decisions CSV</button></p><p id="error" role="alert"></p><script src="../../../global-review.js"></script></html>'''
    page=page.replace('<h2>Every admitted/replayed observation</h2>',replay_table+'<h2>Every admitted/replayed observation</h2>')
    page=page.replace('<h2>Every admitted/replayed observation</h2>','<details><summary>Geographic audit, facility proposals and independent-quality gates</summary><p>'+str(report['summary']['company_geography']['company_only_records'])+' company references audited; 1 separate city-reference marker; 1,676 without a display reference; no original coordinates changed. Four retained facility dossiers remain pending independent review, with no new verified facility or capture claim.</p><p><a href="../../nz-census/final-review/reports/dashboard.html">Retained facility dossiers and before/after identity review</a> · <a href="heldout-review.json">14-candidate frozen evaluation worksheet with overlap disclosure</a>. Human precision/recall remain null; no human labels exist. Source policies and proposals do not grant publication approval.</p></details><h2>Every admitted/replayed observation</h2>')
    (out/'dashboard.html').write_text(page,encoding='utf-8')


def check(home=HOME):
    report=build(home)
    with tempfile.TemporaryDirectory() as tmp:
        save(report,Path(tmp))
        for p in Path(tmp).iterdir():
            if p.read_bytes()!=(home/'reports'/p.name).read_bytes():raise ValueError('Stale global report: '+p.name)
    return report


def maintenance_check(home=HOME):
    checkpoint=read(home/'maintenance/checkpoint.json')
    for name,expected in checkpoint['files'].items():
        relative=Path(name)
        if relative.is_absolute() or '..' in relative.parts or sha(home/'maintenance'/relative)!=expected:raise ValueError('Maintenance checkpoint changed: '+name)
    state=check_state(read(home/'maintenance/state.json'));snapshot=load_snapshot(home/'maintenance/snapshot.json',read(home/'maintenance/policy.json'));repeat,signals=advance(state,snapshot,read(home/'maintenance/freshness-policy.json'))
    if repeat!=state or signals or len(state['history'])!=1 or len(state['sources'][snapshot['source_id']]['records'])!=424:raise ValueError('Actual licensed snapshot replay/idempotency failure')
    return {'actual_source_rows':424,'history_events':1,'repeat_signals':0,'canonical_updates':0,'human_approved':False}


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('command',choices=('prepare','check','incremental','maintenance-check'));p.add_argument('--snapshot',type=Path);p.add_argument('--policy',type=Path);p.add_argument('--metadata',type=Path);p.add_argument('--state',type=Path);p.add_argument('--freshness',type=Path);p.add_argument('--output',type=Path,default=HOME/'reports');a=p.parse_args()
    if a.command=='maintenance-check':print(json.dumps(maintenance_check(),indent=2));return
    if a.command=='incremental':
        if not all((a.snapshot,a.policy,a.state)):p.error('incremental requires --snapshot, --policy and --state')
        if a.state.resolve().is_relative_to((ROOT/'data/public').resolve()) or a.state.resolve()==(ROOT/'studios.json').resolve():raise ValueError('Maintenance state must not overwrite published data')
        freshness=bounded(a.freshness) if a.freshness else FRESHNESS
        if set(freshness)!=set(FRESHNESS) or any(type(v) is not int or not 1<=v<=3650 for v in freshness.values()):raise ValueError('Invalid freshness policy')
        try:
            value=load_snapshot(a.snapshot,bounded(a.policy),bounded(a.metadata) if a.metadata else None);state,signals=advance(bounded(a.state,MAX_STATE_BYTES) if a.state.exists() else empty_state(),value,freshness)
        except (ValueError,OSError,KeyError,TypeError) as error:
            write(a.output/'failure.json',{'status':'blocked_no_state_or_canonical_update','reason':str(error),'human_approved':False,'canonical_updates':[]});raise
        write(a.state,state);write(a.output/'incremental-signals.json',{'signals':signals,'human_approved':False,'canonical_updates':[]});print(json.dumps({'history_events':len(state['history']),'signals':len(signals),'canonical_updates':0}));return
    report=check() if a.command=='check' else build()
    if a.command=='prepare':save(report,a.output)
    print(json.dumps(report['summary'],ensure_ascii=False,indent=2))
if __name__=='__main__':main()
