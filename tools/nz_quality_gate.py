#!/usr/bin/env python3
"""Final NZ proposal review: classify evidence, stage conflicts, never approve."""
import argparse,copy,csv,html,json,re,tempfile
from collections import Counter
from datetime import date
from pathlib import Path
from urllib.parse import urlsplit
from discovery import ROOT,read,write,digest
from bulk_catalog import compact,sha
from compact_index import add_transport
from catalogue_history import records
from validate import url_valid
from unified_catalog import validate_research

HOME=ROOT/'data/nz-census/final-review';NZ=ROOT/'data/nz-census';PREFIX='nzcensus-'
GROUPS={'motionx_core':'MotionX core','adjacent_production':'Adjacent production','game_development':'Game development','supporting_services':'Supporting services','out_of_scope':'Out of scope'}
READINESS={'eligible_source_authorised_identity':'Eligible scoped agency identity reference','eligible_minimal_factual_reference':'Eligible minimal factual reference; wider rights unresolved','staged_identity_review':'Staged: identity requires review','staged_scope_review':'Staged: scope requires review'}
DECISIONS={'accept_provisional':'Accept provisional company reference','existing_alias':'Existing company / alias','needs_evidence':'Needs further evidence','identity_conflict':'Identity conflict','out_of_scope':'Out of scope','historical_review':'Historical or inactive — further confirmation required','rights_review':'Source permission requires review'}
COMPANY_FIELDS=set('record_id company_id operating_name aliases original_record_hash original_source_license source_observations source_periods original_service_labels evidence potential_duplicates original_match_candidates relevance classification_basis company_service_claims claim_state current_operation operation_note country_association rights_status requires_maintainer_rights_scope_review permitted_scope publication_readiness public_sector_override human_review_questions reviewed_on human_decision human_reviewer human_reviewed_on human_approved original_sectors'.split())
IDENTITY_FIELDS=set('source_name most_likely_identity aliases resolution operation_status evidence existing_match_candidates proposed_match_candidates country_or_brand_conflicts recommendation human_review_needed reviewed_on human_decision human_approved'.split())
FACILITY_FIELDS=set('proposal_id name operator_source_claim operator_legal_identity municipality country source_address_claim address_verified_by_human function_source_claim current_operation evidence coordinate_precision lat lng coordinate_rationale unverified_aspects independent_facility_review human_decision human_approved'.split())



def inputs(home=HOME):
    parent=read(home/'inputs/parent-checkpoint.json')
    for name,expected in parent['parent_files'].items():
        path=Path(name)
        if path.is_absolute() or '..' in path.parts or path.parts[:3]!=('data','nz-census','reports') or sha(ROOT/path)!=expected:raise ValueError('Frozen prior NZ review changed: '+name)
    if sha(NZ/'release.json')!=parent['original_release_sha256']:raise ValueError('Original source checkpoint changed')
    if sha(ROOT/'data/annecy/reports/human-precision-review.json')!=parent['annecy_worksheet_sha256']:raise ValueError('Historical Annecy worksheet changed')
    companies=read(home/'inputs/companies.json')['companies'];identities=read(home/'inputs/identities.json')['identities'];facilities=read(home/'inputs/facilities.json')['facilities']
    original=read(NZ/'reports/proposals.json')['company_references'];byid={r['id']:r for r in original}
    if len(companies)!=59 or {c['record_id'] for c in companies}!=set(byid):raise ValueError('Every one of the 59 original proposals must be audited exactly once')
    if len({c['record_id'] for c in companies})!=59:raise ValueError('Duplicate company review')
    for rows,allowed in ((companies,COMPANY_FIELDS),(identities,IDENTITY_FIELDS),(facilities,FACILITY_FIELDS)):
        if any(set(row)-allowed for row in rows):raise ValueError('Unsupported/private fields cannot enter public research artifacts')
    for c in companies:
        origin=byid[c['record_id']]
        if c['company_id']!=origin['company_id'] or c['operating_name']!=origin['name'] or c['original_source_license']!=origin['license'] or c['requires_maintainer_rights_scope_review']!=(origin['license']=='UNSPECIFIED'):raise ValueError('Original identity/rights scope cannot be silently rewritten')
        if c['publication_readiness']=='eligible_source_authorised_identity' and origin['license']!='NZ-On-Air-Permission':raise ValueError('Unknown rights do not become source-authorised through a review label')
        if c['original_record_hash']!=digest(byid[c['record_id']]) or c['original_sectors']!=byid[c['record_id']]['categories']:raise ValueError('Company review is stale or refers to another proposal')
        if c['relevance'] not in GROUPS or c['publication_readiness'] not in READINESS:raise ValueError('Unknown relevance/readiness')
        if c['relevance']=='out_of_scope' and not c['publication_readiness'].startswith('staged_'):raise ValueError('Out-of-scope proposal cannot enter the directory')
        if c['current_operation'] not in ('programme_listing_only','source_self_report_unverified','regional_listing_only'):raise ValueError('No independent operation verification may be invented')
        if c['original_source_license']=='NZ-On-Air-Permission' and c['relevance'] in ('motionx_core','adjacent_production','supporting_services'):
            if not any(e['kind'] in ('official_company','official_agency') and e['url']!=byid[c['record_id']]['evidence'] for e in c['evidence']):raise ValueError('Programme receipt alone cannot establish production specialisation')
        if c['public_sector_override'] and (c['operating_name']!='Insight Creative' or c['public_sector_override']!=['Game Production Support']):raise ValueError('Unreviewed classification override')
    original_keys={o['name'] for o in read(NZ/'reports/reconciliation.json')['observations'] if o['disposition'] in ('identity_hold','unresolved')}
    if {i['source_name'] for i in identities}!=(original_keys|{'Niantic Aotearoa NZ'}) or len(identities)!=28:raise ValueError('Unresolved identity/closure continuity failure')
    if len(facilities)!=4 or {f['proposal_id'] for f in facilities}!={f['proposal_id'] for f in read(NZ/'reports/proposals.json')['facility_evidence_proposals']}:raise ValueError('Facility proposal continuity failure')
    for f in facilities:
        if f['lat'] is not None or f['lng'] is not None or f['coordinate_precision']!='unverified' or f['independent_facility_review']!='not_completed':raise ValueError('Facility review cannot create a pin or verification')
    for row in companies+identities+facilities:
        if row['human_approved'] is not False or row['human_decision'] is not None or row.get('human_reviewer') is not None or row.get('human_reviewed_on') is not None:raise ValueError('Automated preparation cannot fill human decisions/approval')
        if not row.get('evidence'):raise ValueError('Review needs evidence links')
        for e in row['evidence']:
            if set(e)-{'url','observed_on','source_published_on','kind','rights','source_date_basis'}:raise ValueError('Unsupported/private evidence fields')
            if e.get('rights')=='NZ-On-Air-Permission' and urlsplit(e['url']).hostname!='www.nzonair.govt.nz':raise ValueError('Agency grant cannot cover other domains')
            if e.get('kind')=='official_agency' and urlsplit(e['url']).hostname!='www.nzonair.govt.nz':raise ValueError('Unreviewed agency identity')
            if not url_valid(e['url']) or 'filmotagosouthland.com' in e['url'] or 'waikatoscreen.nz' in e['url']:raise ValueError('Unsafe/restricted new evidence')
            if date.fromisoformat(e['observed_on']).isoformat()!=e['observed_on'] or e['observed_on']>date.today().isoformat():raise ValueError('Invalid review date')
            if e.get('source_published_on') is not None and date.fromisoformat(e['source_published_on']).isoformat()!=e['source_published_on']:raise ValueError('Invalid actual source publication date')
    return parent,companies,identities,facilities


def public_records(original,home=HOME):
    """Minimal company assertions only. This does not approve publication."""
    _,companies,_,_=inputs(home);byid={r['id']:r for r in original};result=[]
    for c in companies:
        if c['publication_readiness'].startswith('staged_'):continue
        row=copy.deepcopy(byid[c['record_id']])
        row['research_review']={'version':1,'relevance':c['relevance'],'publication_state':'provisional_research_lead','source_rights':'agency_factual_projection_permission' if row['license']=='NZ-On-Air-Permission' else 'minimal_facts_terms_unspecified','operation_status':c['current_operation'],'reviewed_on':c['reviewed_on'],'human_approved':False,'facility_verified':False}
        if c['public_sector_override']:
            row['categories']=c['public_sector_override']
            row['attribution']+=' Final review adds the coarse agency-reported playtesting support classification, not a verified company or facility service.'
            e=next(e for e in c['evidence'] if e['kind']=='official_agency' and e['url']!=row['evidence'])
            row['source_provenance'].append({'source_id':'nzonair-gdsr-context','source_record_id':row['id'],'url':e['url'],'license':'NZ-On-Air-Permission','license_url':'https://www.nzonair.govt.nz/copyright-and-terms-use/','observed_on':e['observed_on'],'observation_hash':digest(e)})
            row['research_reasons'].append('Agency evidence describes game playtesting support, not independently established game development or facility capabilities.')
        result.append(row)
    errors=validate_research(result)
    if errors:raise ValueError('Invalid public review projection: '+str(errors[:5]))
    return result


def apply(public,database,home=HOME):
    public=Path(public);m,rows=records(public,database)
    if m.get('nz_quality_gate') or len(rows)!=42298:raise ValueError('Fresh 42,298-record pre-gate proposal required; repeated application refused')
    original=[r for r in rows if r['id'].startswith(PREFIX)];base=[r for r in rows if not r['id'].startswith(PREFIX)]
    final=public_records(original,home);final_ids={r['id'] for r in final};staged=sorted(r['id'] for r in original if r['id'] not in final_ids)
    _,companies,_,_=inputs(home);before=copy.deepcopy(m['counts']);key='shards/821e1c1af0a4-000.json'
    compact(public/key,sorted(final,key=lambda r:r['id']));m['shards'][key].update(sha256=sha(public/key),gzip_sha256=sha(public/(key+'.gz')),bytes=(public/key).stat().st_size,gzip_bytes=(public/(key+'.gz')).stat().st_size,records=len(final))
    byid={r['id']:r for r in final};index=[]
    for row in read(public/'index.json'):
        if row[0] in staged:continue
        if row[0] in byid:row[7]=byid[row[0]]['categories']
        index.append(row)
    compact(public/'index.json',index);m['index'].update(sha256=sha(public/'index.json'),gzip_sha256=sha(public/'index.json.gz'),gzip_bytes=(public/'index.json.gz').stat().st_size,bytes=(public/'index.json').stat().st_size,records=len(index))
    for k in ('records','public_records','class_c','company_references'):m['counts'][k]-=len(staged)
    m['counts']['source_identities']=len({r['company_id'] for r in base+final if r['record_kind']!='retained_location'})
    for k in ('company_references_without_coordinates','unreviewed_new_references'):m['warnings'][k]-=len(staged)
    m['warnings']['nz_census_references_requiring_review']=len(final);m['warnings']['nz_gate_staged_proposals']=len(staged);m['warnings']['nz_gate_minimal_facts_wider_rights_review']=sum(c['requires_maintainer_rights_scope_review'] for c in companies if c['record_id'] in final_ids)
    advisory=read(public/'boutique.json')
    for rid in staged:advisory['profiles'].pop(rid,None)
    advisory['nz_quality_gate']={'audited_proposals':59,'eligible_directory_leads':len(final),'staged_proposals':len(staged),'human_approved':False}
    compact(public/'boutique.json',advisory);m['boutique'].update(sha256=sha(public/'boutique.json'),gzip_sha256=sha(public/'boutique.json.gz'),gzip_bytes=(public/'boutique.json.gz').stat().st_size)
    m['licence_files']={p.name:{'sha256':sha(p)} for p in sorted((ROOT/'data/bulk/LICENSES').glob('*.txt'))}
    m['nz_quality_gate']={'version':1,'report_path':'data/nz-census/final-review/reports/dashboard.html','staged_ids':staged,'audited_proposals':59,'human_approved':False}
    add_transport(public,database,m,index,[r for r in base+final if r['record_kind']!='retained_location']);write(public/'manifest.json',m)
    return {'before_counts':before,'after_counts':m['counts'],'staged_ids':staged,'original_ids_sha256':digest(sorted(r['id'] for r in base))}


def review_report(home=HOME):
    parent,companies,identities,facilities=inputs(home)
    included=[c for c in companies if not c['publication_readiness'].startswith('staged_')]
    summary={'pre_v15_reference_records':42239,'prior_raw_proposal_records':42298,'proposed_reference_records':42239+len(included),'retained_locations':243,'retained_operating_organisations':119,'countries_and_territories':178,'audited_companies':len(companies),'relevance':dict(sorted(Counter(c['relevance'] for c in companies).items())),'publication_readiness':dict(sorted(Counter(c['publication_readiness'] for c in companies).items())),'eligible_directory_research_leads':len(included),'staged_proposals':len(companies)-len(included),'identity_key_reviews':27,'separate_closure_alerts':1,'identity_outcomes':dict(sorted(Counter(i['resolution'] for i in identities if i['source_name']!='Niantic Aotearoa NZ').items())),'facility_dossiers':len(facilities),'independent_facility_reviews':0,'maintainer_minimal_rights_scope_decisions':sum(c['requires_maintainer_rights_scope_review'] for c in companies),'human_decisions':0,'human_approved':False,'historical_nz_pending_worksheet':29,'historical_annecy_pending_worksheet':37,'new_map_pins':0,'new_verified_capabilities':0,'recommendation':'READY FOR HUMAN REVIEW','recommendation_basis':'Every proposal has relevance, rights scope, operation uncertainty, matching context and a documented disposition. Conflicts are staged, company assertions are labelled, and no automated decision grants publication approval.','census_complete':False}
    items=[]
    for c in companies:items.append({'item_id':'company-'+c['record_id'],'kind':'company','name':c['operating_name'],'relevance':c['relevance'],'readiness':c['publication_readiness'],'evidence':c['evidence'],'data':c})
    for i in identities:items.append({'item_id':'identity-'+digest(i['source_name'])[:20],'kind':'identity','name':i['source_name'],'relevance':'','readiness':i['resolution'],'evidence':i['evidence'],'data':i})
    for f in facilities:items.append({'item_id':f['proposal_id'],'kind':'facility','name':f['name'],'relevance':'supporting_services','readiness':'independent_facility_review_pending','evidence':f['evidence'],'data':f})
    for item in items:item.update(content_hash=digest(item),human_decision=None,human_notes='',human_reviewer=None,human_approved=False)
    worksheet={'version':1,'dataset_hash':digest(items),'human_approved':False,'human_review_completed':0,'purpose':'Local worksheet drafts are not authenticated GitHub reviews or publication authorisation. No import/apply command consumes these decisions. Review the exact PR in GitHub.','decision_options':DECISIONS,'historical_nz_worksheet_sha256':parent['parent_files']['data/nz-census/reports/human-review.json'],'historical_annecy_worksheet_sha256':parent['annecy_worksheet_sha256'],'items':items}
    return {'summary':summary,'companies':companies,'identities':identities,'facilities':facilities,'worksheet':worksheet}


def csv_safe(value):
    if isinstance(value,(dict,list)):value=json.dumps(value,ensure_ascii=False,sort_keys=True)
    s=str(value or '')
    return "'"+s if re.match(r'^[\s\u200B\u200C\u200D]*[=+@-]',s) else s


def save(report,output):
    output=Path(output);output.mkdir(parents=True,exist_ok=True);esc=html.escape
    for filename,value in [('summary.json',report['summary']),('company-audit.json',report['companies']),('identity-review.json',report['identities']),('facility-dossiers.json',report['facilities']),('worksheet.json',report['worksheet'])]:write(output/filename,value)
    fields=['item_id','kind','name','relevance','readiness','content_hash','evidence','recommended_outcome','human_decision','human_notes','human_reviewer']
    with (output/'worksheet.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.writer(f,lineterminator='\n');w.writerow(fields)
        for item in report['worksheet']['items']:
            row={**item,'recommended_outcome':item['data'].get('recommendation') or item['data'].get('classification_basis') or item['data']['function_source_claim']}
            w.writerow([csv_safe(row.get(k,'')) for k in fields])
    def profile_links(ids):
        return ' · '.join('<a href="../../../../index.html#/location/'+esc(rid,quote=True)+'">'+esc(rid)+'</a>' for rid in ids) or 'No supported exact identity established'
    cards=[]
    for item in report['worksheet']['items']:
        data=item['data'];links=''.join('<li><a href="'+esc(e['url'],quote=True)+'" rel="noopener noreferrer">'+esc(e['url'])+'</a><br>Observed '+esc(e['observed_on'])+' · source publication/update date '+esc(e.get('source_published_on') or 'unknown / not established')+' ('+esc(e.get('source_date_basis','unknown'))+')'+' · rights '+esc(e.get('rights','UNSPECIFIED'))+'</li>' for e in item['evidence'])
        body=''
        if item['kind']=='company':
            public=not data['publication_readiness'].startswith('staged_')
            body='<p>'+esc(data['classification_basis'])+'</p><dl><dt>Operating identity / aliases</dt><dd>'+esc(data['operating_name']+' / '+(', '.join(data['aliases']) or 'None established'))+'</dd><dt>Current operation</dt><dd>'+esc(data['current_operation']+' · '+data['operation_note'])+'</dd><dt>Rights scope</dt><dd>'+esc(data['rights_status']+' · '+data['permitted_scope'])+'</dd><dt>Before → proposed directory classification</dt><dd>'+esc(', '.join(data['original_sectors']))+' → '+esc(', '.join(data['public_sector_override'] or data['original_sectors']) if public else 'Staged — not in directory')+' · Class C; no verified facility claim'+'</dd><dt>Company service assertions — unverified</dt><dd>'+esc(', '.join(data['company_service_claims']) or 'No detailed company service claim established by the programme listing')+'</dd><dt>Identity / duplicates</dt><dd>'+profile_links(sorted(set(data['original_match_candidates']+[rid for p in data['potential_duplicates'] for rid in p['ids']])))+'</dd><dt>Country</dt><dd>'+esc(data['country_association'])+'</dd></dl><p>'+('<a href="../../../../index.html#/location/'+esc(data['record_id'],quote=True)+'">Open provisional company profile</a>' if public else 'Staged: excluded from directory search and CSV exports; retained in this evidence review.')+'</p><ul>'+''.join('<li>'+esc(q)+'</li>' for q in data['human_review_questions'])+'</ul>'
        elif item['kind']=='identity':
            body='<p>'+esc(data['recommendation'])+'</p><dl><dt>Likely identity</dt><dd>'+esc(data['most_likely_identity'])+'</dd><dt>Current operation</dt><dd>'+esc(data['operation_status'])+'</dd><dt>Conflicts</dt><dd>'+esc(data['country_or_brand_conflicts'])+'</dd><dt>Existing / proposed matches</dt><dd>'+profile_links(data['existing_match_candidates']+data['proposed_match_candidates'])+'</dd></dl><p>'+esc(data['human_review_needed'])+'</p>'
        else:
            body='<dl><dt>Operator source claim</dt><dd>'+esc(data['operator_source_claim'])+' · legal identity '+esc(data['operator_legal_identity'])+'</dd><dt>Municipality / source address</dt><dd>'+esc(data['municipality']+' / '+(data['source_address_claim'] or 'Exact address unestablished'))+'</dd><dt>Current operation</dt><dd>'+esc(data['current_operation'])+'</dd><dt>Function</dt><dd>'+esc(data['function_source_claim'])+'</dd><dt>Coordinates</dt><dd>'+esc(data['coordinate_rationale'])+' Precision: unverified; no coordinates proposed.</dd></dl><ul>'+''.join('<li>'+esc(q)+'</li>' for q in data['unverified_aspects'])+'</ul>'
        cards.append('<article id="'+esc(item['item_id'],quote=True)+'" data-item="'+esc(item['item_id'],quote=True)+'" data-kind="'+esc(item['kind'],quote=True)+'" data-relevance="'+esc(item['relevance'],quote=True)+'" data-readiness="'+esc(item['readiness'],quote=True)+'" data-hash="'+item['content_hash']+'"><h2>'+esc(item['name'])+'</h2><p>'+esc(item['kind']+' · '+GROUPS.get(item['relevance'],item['relevance'])+' · '+READINESS.get(item['readiness'],item['readiness']).replace('_',' '))+'</p>'+body+'<h3>Evidence and dates</h3><ul>'+links+'</ul><label>Maintainer working decision<select data-decision aria-label="Decision for '+esc(item['name'],quote=True)+'"><option value="">Pending — no human decision</option>'+''.join('<option value="'+key+'">'+esc(label)+'</option>' for key,label in DECISIONS.items())+'</select></label><label>Working notes (no confidential data)<textarea data-notes aria-label="Notes for '+esc(item['name'],quote=True)+'" rows="2" maxlength="4000"></textarea></label></article>')
    options=lambda mapping:''.join('<option value="'+k+'">'+esc(v)+'</option>' for k,v in mapping.items())
    page='''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>MotionX NZ final quality gate — maintainer review</title><style>*{box-sizing:border-box}body{background:#101822;color:#edf1f8;font:16px/1.6 system-ui;max-width:1200px;margin:auto;padding:22px;overflow-wrap:anywhere}a{color:#addcff}article{background:#172333;border:1px solid #43516a;border-radius:10px;padding:20px;margin:22px 0}label{display:block;margin:12px 0}input,select,textarea,button{background:#101822;color:inherit;border:1px solid #8798ad;font:inherit;padding:10px;min-height:44px;max-width:100%}textarea,article select{width:100%}a:focus-visible,input:focus-visible,select:focus-visible,textarea:focus-visible,button:focus-visible{outline:3px solid #ffd77a}dd{margin:0 0 12px}dt{font-weight:bold}pre{white-space:pre-wrap;overflow-wrap:anywhere}article[hidden]{display:none}.filters{display:flex;flex-wrap:wrap;gap:16px}@media(max-width:700px){body{padding:12px}article{padding:14px}.filters{display:block}}</style><h1>NZ final quality gate · maintainer review</h1><p><strong>READY FOR HUMAN REVIEW.</strong> This recommendation does not authorise publication. All decisions below start pending. Company/source assertions are distinct from independently verified facility evidence. No new pins, Class A records or confirmed capabilities are created.</p><p><strong>42,296 proposed directory references: 57 eligible new Class C leads, two staged proposals, all 42,239 original IDs retained. The root database remains 243 locations / 119 operating organisations. No new facility pins or approvals.</strong></p><p>Repository, PR and downloadable research artifacts are public. Staging excludes a record from the directory; it is not a privacy boundary. No confidential material, contacts, authored third-party descriptions or assets belong here.</p><p><a href="../../../../index.html">Atlas</a> · <a href="company-audit.json">59 company audits</a> · <a href="identity-review.json">27 identity keys + NZ closure alert</a> · <a href="facility-dossiers.json">4 facility dossiers</a> · <a href="worksheet.csv">Blank CSV worksheet</a> · <a href="worksheet.json">Content-bound worksheet</a> · <a href="../../reports/coverage.html">Frozen prior source reconciliation</a></p><p>Original 29-entry NZ and 37-row Annecy human worksheets remain unchanged. 91 detailed review cards below contain no completed human decisions. Dates marked unknown were not replaced with crawl dates.</p><details><summary>Relevance, publication readiness and unresolved counts</summary><pre>'''+esc(json.dumps(report['summary'],ensure_ascii=False,indent=2))+'''</pre></details><div class="filters"><label>Search evidence and names<input id="reviewQuery" type="search"></label><label>Item type<select id="reviewKind"><option value="">All</option><option value="company">Companies</option><option value="identity">Identity review</option><option value="facility">Facility dossiers</option></select></label><label>Relevance<select id="reviewRelevance"><option value="">All</option>'''+options(GROUPS)+'''</select></label><label>Publication readiness<select id="reviewReadiness"><option value="">All</option>'''+options(READINESS)+'''</select></label></div><p id="reviewCount" role="status" aria-live="polite"></p><p>Selections and notes stay in this page until explicitly downloaded. A worksheet download is an unauthenticated working draft, not a GitHub approval; no tool imports these decisions or publishes records. Review the exact PR commit in GitHub before an authorised merge.</p><button id="exportReview">Download working decisions</button><p id="reviewExportStatus" role="status" aria-live="polite"></p><div id="reviewCards" data-dataset-hash="'''+report['worksheet']['dataset_hash']+'''">'''+''.join(cards)+'''</div><script src="../../../../nz-final-review.js"></script></html>'''
    (output/'dashboard.html').write_text(page,encoding='utf-8')


def checkpoint(home=HOME):
    cfg=read(home/'release.json')
    if cfg.get('human_approved') is not False:raise ValueError('No fabricated release approval')
    for name,expected in cfg['input_hashes'].items():
        p=Path(name)
        if p.is_absolute() or '..' in p.parts or sha(home/p)!=expected:raise ValueError('Final-review input checkpoint changed: '+name)
    return cfg


def check(home=HOME):
    cfg=checkpoint(home);parent,companies,_,_=inputs(home);m,all_rows=records(ROOT/'data/public',ROOT/'studios.json');original=read(NZ/'reports/proposals.json')['company_references'];final=public_records(original,home);base=[r for r in all_rows if not r['id'].startswith(PREFIX)]
    if len(base)!=42239 or digest(sorted(r['id'] for r in base))!=cfg['original_ids_sha256']:raise ValueError('Pre-v1.5 identity set changed')
    oldcfg=read(NZ/'release.json')
    if sha(ROOT/'studios.json')!=oldcfg['retained_baseline_sha256']:raise ValueError('Original root database changed')
    for name,h in oldcfg['retained_shard_hashes'].items():
        if sha(ROOT/'data/public'/name)!=h:raise ValueError('Original evidence shard changed')
    if {r['id']:r for r in all_rows if r['id'].startswith(PREFIX)}!={r['id']:r for r in final}:raise ValueError('Public projection violates reviewed staging/classification')
    if m['counts']!=cfg['after_counts'] or m.get('nz_quality_gate',{}).get('staged_ids')!=cfg['staged_ids']:raise ValueError('Final gate count/staging mismatch')
    report=review_report(home)
    with tempfile.TemporaryDirectory() as tmp:
        save(report,Path(tmp))
        for p in Path(tmp).iterdir():
            if p.read_bytes()!=(home/'reports'/p.name).read_bytes():raise ValueError('Stale final review report: '+p.name)
    return report


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('command',choices=('prepare','check'));a=p.parse_args()
    if a.command=='prepare':
        result=apply(ROOT/'data/public',ROOT/'studios.json');report=review_report();save(report,HOME/'reports');write(HOME/'release.json',{'version':1,**result,'input_hashes':{str(p.relative_to(HOME)):sha(p) for p in sorted((HOME/'inputs').glob('*.json'))},'human_approved':False})
    else:report=check()
    print(json.dumps(report['summary'],ensure_ascii=False,indent=2))
if __name__=='__main__':main()
