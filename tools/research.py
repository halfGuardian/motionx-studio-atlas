#!/usr/bin/env python3
"""Prepare unverified research dossiers and safe review artifacts; never publish data."""
import argparse
from collections import Counter,defaultdict
import copy
from datetime import date
import html
import json
from pathlib import Path
from urllib.parse import urlsplit

from discovery import ROOT,digest,read,safe_output,write
from import_csv import plan_import
from triage import triage
from validate import CSV_FIELDS,DuplicateIndex,normalized,url_valid,validate


def dossier(queue,source_report,database,config,records=(),as_of=None):
    today=date.fromisoformat(as_of or date.today().isoformat())
    routed=triage(queue,source_report,database,config)
    sources={s['id']:s for s in config['sources']}
    proposals=[]
    by_id={r['id']:r for r in database}
    changes=[]
    for record in records:
        errors,warnings=validate([record])
        changes.append({'id':record.get('id'),'action':'update' if record.get('id') in by_id else 'add',
                        'before':by_id.get(record.get('id')),'after':record,'validation_errors':errors,'warnings':warnings,
                        'review_state':'source_researched_pending_human_PR_review'})
    for routed_candidate in routed['candidates']:
        c=routed_candidate['observation'];source=sources.get(c['source_id'],{})
        age=(today-date.fromisoformat(c['last_seen'])).days
        risks=[];questions=['Is this an active physical production facility rather than an office or remote team?',
                           'Does the evidence support each claimed capability at this specific site?',
                           'Are municipality and coordinates supported independently of the marketed city label?']
        if age<0 or age>30:risks.append('Observation is future dated or older than 30 days; revisit the source.')
        if c.get('missing_since'):risks.append('Missing from a source; do not infer closure.')
        if routed_candidate['matching_scope']=='organisation':risks.append('Organisation-only match does not resolve branch or facility identity.')
        if routed_candidate.get('duplicate_observation_ids'):risks.append('Repeated evidence pointer; review identity before creating a record.')
        if not c.get('city') or not c.get('country'):risks.append('City/country not present in observation; research required.')
        matching=[by_id[i] for i in routed_candidate['matched_location_ids']]
        claims=[{'claim':term,'status':'unverified_source_term','source':c['url'],'requires_site_verification':True} for term in c.get('claim_terms',[])]
        backlog_name=c['label'].partition(' — ')[0] if c.get('source_kind')=='manual_backlog' else ''
        proposals.append({'candidate_id':c['id'],'candidate_hash':digest(c),'organisation_name':source.get('organisation_name') or c.get('hint_company_id') or backlog_name or 'Identity unresolved',
                          'candidate_location_name':c['label'],'city':c.get('city',''),'country':c.get('country',''),
                          'place_status':'unverified_source_reference' if c.get('city') else 'unknown',
                          'parent_relationships':{'status':'unverified_hint','values':source.get('parent_hints',[])},
                          'official_website':source.get('url',''),'evidence_urls':list(dict.fromkeys([c['url'],*c.get('sources',[])])),
                          'potential_sector':{'status':'unverified_hint','values':source.get('sector_hints',[])},
                          'facility_claims':claims,'existing_matches':[{'id':r['id'],'company_id':r['company_id'],'name':r['name'],'city':r['city'],'country':r['country']} for r in matching],
                          'matching_reasons':routed_candidate['reasons'],'triage':routed_candidate['classification'],
                          'triage_confidence':routed_candidate['triage_confidence'],'discovery_confidence':c['confidence'],
                          'review_priority':'high' if routed_candidate['classification']=='potentially_new' and 0<=age<=30 else 'medium' if routed_candidate['classification']=='requires_research' else 'low',
                          'evidence_freshness':'current_observation' if 0<=age<=30 else 'revisit_required',
                          'identity_risks':risks,'evidence_age_days':age,'observed_on':c['last_seen'],
                          'alerts':[{'signal':s,'status':'requires_investigation','source':c['url']} for s in c.get('signals',[])],
                          'unresolved_questions':questions,'review_status':'unverified','publication_approved':False})
    return {'version':1,'as_of':today.isoformat(),'publication_mode':'human_review_and_manual_merge_of_exact_GitHub_PR',
            'queue_hash':digest(queue),'database_hash':digest(database),'source_report_hash':digest(source_report),
            'sources':source_report.get('sources',[]),'candidate_counts':routed['counts'],'dossiers':proposals,'record_changes':changes,
            'source_access':[{'id':s['id'],'enabled':s['enabled'],'review':s.get('access_review',{}),
                              'disabled_reason':s.get('disabled_reason','')} for s in config['sources']],
            'approved_claims':0,'published_records':0,'warning':'Source terms, schema checks and link clicks are not human approval or independent business verification.'}


def review_html(report):
    def esc(value):return html.escape(str(value),quote=True)
    def link(url):return f'<a href="{esc(url)}" rel="noopener noreferrer">{esc(url)}</a>' if url_valid(url) else esc(url)
    groups=defaultdict(list)
    for p in report['dossiers']:groups[(p['organisation_name'],p['country'] or 'Country unresolved')].append(p)
    body=['<h1>MotionX research review</h1>',f'<p>As of {esc(report["as_of"])} · Unverified discoveries and source-researched proposals await human review.</p>',
          '<p><strong>No records or claims have been approved or published by this report.</strong> A human must review and authorise the exact PR content before manual merge.</p>',
          '<h2>Candidate summary</h2><dl>'+''.join(f'<dt>{esc(k)}</dt><dd>{v}</dd>' for k,v in report['candidate_counts'].items())+'</dl>',
          '<h2>Proposed record changes</h2>']
    previous_group=None
    for change in sorted(report['record_changes'],key=lambda c:(c['after'].get('company_id',''),c['after'].get('country',''),c['id'])):
        before=change['before'] or {};after=change['after']
        group=(after.get('company_id',''),after.get('country',''))
        if group!=previous_group:body.append('<h3>'+esc(group[0])+' / '+esc(group[1])+'</h3>');previous_group=group
        fields=[k for k in sorted(set(before)|set(after)) if before.get(k)!=after.get(k)]
        body.append(f'<details><summary>{esc(change["action"])} · {esc(change["id"])} · {esc(after.get("name",""))} — {esc(after.get("country",""))}</summary>')
        body.append('<p>Source-researched; human PR approval pending. Validation errors: '+esc(change['validation_errors'])+'</p>')
        body.append('<p>Warnings: '+esc(change['warnings'])+'</p>')
        evidence=list(dict.fromkeys([after.get('evidence',''),*[e.get('evidence','') for e in after.get('capability_evidence',{}).values()],*[r['evidence'] for r in after.get('relationships',[])]]))
        body.append('<ul>'+''.join('<li>'+link(u)+'</li>' for u in evidence if u)+'</ul>')
        body.append('<table><caption>Before and after — changed fields only</caption><thead><tr><th>Field</th><th>Before</th><th>Proposed</th></tr></thead><tbody>')
        for field in fields:
            body.append('<tr><th>'+esc(field)+'</th><td><pre>'+esc(json.dumps(before.get(field),ensure_ascii=False,indent=2))+'</pre></td><td><pre>'+esc(json.dumps(after.get(field),ensure_ascii=False,indent=2))+'</pre></td></tr>')
        body.append('</tbody></table></details>')
    body.append('<h2>Companies and countries</h2><nav aria-label="Company and country index"><ul>')
    for i,(name,country) in enumerate(sorted(groups)):body.append(f'<li><a href="#group-{i}">{esc(name)} / {esc(country)} ({len(groups[(name,country)])})</a></li>')
    body.append('</ul></nav>')
    for i,((name,country),items) in enumerate(sorted(groups.items())):
        body.append(f'<section id="group-{i}"><h2>{esc(name)} / {esc(country)}</h2>')
        for item in items:
            body.append('<details><summary>'+esc(item['candidate_location_name'])+' · '+esc(item.get('review_priority','medium'))+' priority · '+esc(item['triage'])+' · '+esc(item['review_status'])+'</summary>')
            body.append('<p>'+esc(item['city'] or 'City unresolved')+' · observed '+esc(item['observed_on'])+' · '+str(item['evidence_age_days'])+' days old · routing confidence: '+esc(item['triage_confidence'])+' · evidence confidence: '+esc(item['discovery_confidence'])+'</p>')
            body.append('<h3>Evidence</h3><ul>'+''.join('<li>'+link(u)+'</li>' for u in item['evidence_urls'])+'</ul>')
            for title,key in [('Existing matches','existing_matches'),('Matching reasons','matching_reasons'),('Potential sector (unverified)','potential_sector'),('Facility terms (unverified)','facility_claims'),('Parent/group hints (unverified)','parent_relationships'),('Identity/duplicate risks','identity_risks'),('Closure/relocation/rebrand alerts — investigate','alerts'),('Research questions','unresolved_questions')]:
                body.append('<h3>'+title+'</h3><pre>'+esc(json.dumps(item[key],ensure_ascii=False,indent=2))+'</pre>')
            body.append('</details>')
        body.append('</section>')
    body.append('<h2>Source collection status</h2><pre>'+esc(json.dumps(report['sources'],ensure_ascii=False,indent=2))+'</pre>')
    body.append('<h2>Source access review — no automatic permission grants</h2><table><thead><tr><th>Source</th><th>Collection</th><th>Review / restrictions</th></tr></thead><tbody>')
    for source in report.get('source_access',[]):
        review=source['review'];urls=review.get('policy_urls') or ([review['url']] if review.get('url') else [])
        body.append('<tr><th>'+esc(source['id'])+'</th><td>'+('Enabled; runtime robots mandatory' if source['enabled'] else 'Disabled')+'</td><td>'+esc(review.get('note') or source['disabled_reason'])+'<ul>'+''.join('<li>'+link(u)+'</li>' for u in urls)+'</ul></td></tr>')
    body.append('</tbody></table>')
    return '<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta http-equiv="Content-Security-Policy" content="default-src \'none\'; style-src \'unsafe-inline\'; base-uri \'none\'; form-action \'none\'"><title>MotionX research review</title><style>body{font:16px/1.5 system-ui;background:#101722;color:#eef2f7;max-width:1100px;margin:2rem auto;padding:0 1rem}a{color:#9ed7ff}details{background:#1c2636;border:1px solid #546070;padding:1rem;margin:1rem 0;border-radius:8px}summary{cursor:pointer;font-weight:650}summary:focus-visible,a:focus-visible{outline:3px solid #ffdf6f;outline-offset:4px}pre{white-space:pre-wrap;overflow-wrap:anywhere}table{border-collapse:collapse;width:100%;table-layout:fixed}td,th{border:1px solid #6d7b90;padding:.5rem;vertical-align:top;text-align:left;overflow-wrap:anywhere}dt{font-weight:700}dd{margin-bottom:.5rem}</style><main>'+''.join(body)+'</main></html>'


def stage(existing,records,manifest,allow_distinct=()):
    """Stage source-researched records on a PR branch. No human approval is granted."""
    if manifest.get('publication_mode')!='github_PR_human_review' or manifest.get('baseline_hash')!=digest(existing):
        raise ValueError('PR mode and matching current database hash required; stale proposals must be researched/rebased')
    if not isinstance(records,list) or not records:raise ValueError('nonempty source-researched records required')
    errors,_=validate(records)
    if errors:raise ValueError('invalid proposed records: '+'; '.join(errors))
    allowed=set(CSV_FIELDS)|{'legacy_research'}
    evidence={m['id']:m for m in manifest.get('records',[])}
    by_id={r['id']:r for r in existing}
    additions=[];updates=[]
    for row in records:
        if set(row)-allowed or row.get('email') or row.get('phone'):raise ValueError('private/unknown/contact fields excluded')
        research=evidence.get(row['id'],{})
        if row.get('evidence_state') not in ('confirmed','likely') or any(v['state']=='unknown' for v in row['capability_evidence'].values()):
            raise ValueError('unverified discoveries/unknown capability claims cannot become proposed public records')
        if research.get('record_hash')!=digest(row):raise ValueError('research manifest must bind the exact proposed record')
        reviewed=date.fromisoformat(research.get('reviewed_on',''))
        if not 0 <= (date.today()-reviewed).days <= 30:raise ValueError('source research is stale or future dated')
        if row.get('verified_on')!=reviewed.isoformat() or any(c['verified_on']!=reviewed.isoformat() for c in row['capability_evidence'].values()):
            raise ValueError('location and capability reviews must match the manifest review date')
        if row['id'] in allow_distinct and not research.get('distinct_reason'):
            raise ValueError('distinct-facility approval requires a source-backed rationale')
        if not research.get('location_sources') or row.get('evidence') not in research['location_sources'] or research.get('capability_evidence')!=row['capability_evidence']:
            raise ValueError('per-record source research manifest required; discovery alone cannot stage a canonical record')
        if row['id'] in by_id and row!=by_id[row['id']]:
            if research.get('previous_record_hash')!=digest(by_id[row['id']]):raise ValueError('explicit update requires matching previous record hash')
            if row['company_id']!=by_id[row['id']]['company_id'] and not research.get('identity_change_reason'):
                raise ValueError('organisation identity changes require an explicit sourced rationale')
            updates.append(row)
        else:additions.append(row)
    revised=[next((u for u in updates if u['id']==r['id']),r) for r in existing]
    for update in updates:
        if DuplicateIndex(r for r in revised if r['id']!=update['id']).matches(update) and update['id'] not in allow_distinct:
            raise ValueError('updated record requires distinct-facility duplicate review')
    combined,preview=plan_import(revised,additions,allow_distinct)
    if preview['database_errors'] or preview['rejected_records'] or any(not d['allowed_as_distinct'] for d in preview['potential_duplicates']):
        raise ValueError('import validation or duplicate review blocks staging')
    _,repeat=plan_import(combined,additions,allow_distinct)
    return combined,{'publication_mode':'github_PR_human_review','baseline_hash':digest(existing),'proposed_hash':digest(combined),
                     'additions':preview['new_records'],'updates':[r['id'] for r in updates],'preview':preview,'repeat':repeat,
                     'human_approval':'pending exact-content PR review and manual merge','approved_claims':0,'main_written':False,
                     'record_changes':[{'id':r['id'],'before':by_id.get(r['id']),'after':r} for r in records]}


def main():
    p=argparse.ArgumentParser(description=__doc__);sub=p.add_subparsers(dest='mode',required=True)
    report=sub.add_parser('report')
    for key in ('queue','report','config'):report.add_argument('--'+key,type=Path,required=True)
    report.add_argument('--records',type=Path)
    proposal=sub.add_parser('stage-pr')
    for key in ('records','manifest'):proposal.add_argument('--'+key,type=Path,required=True)
    proposal.add_argument('--allow-distinct-location',action='append',default=[])
    for cmd in (report,proposal):
        cmd.add_argument('--database',type=Path,default=ROOT/'studios.json');cmd.add_argument('--output',type=Path,required=True)
    a=p.parse_args()
    try:
        safe_output(a.output,[v for k,v in vars(a).items() if isinstance(v,Path) and k!='output'])
        if a.output.exists():raise ValueError('output must be a fresh directory')
        database=read(a.database)
        if a.mode=='report':
            result=dossier(read(a.queue),read(a.report),database,read(a.config),read(a.records) if a.records else [])
            write(a.output/'proposals.json',result);(a.output/'review.html').write_text(review_html(result),encoding='utf-8')
            (a.output/'summary.md').write_text('# Research review\n\n'+json.dumps(result['candidate_counts'])+'\n\nOpen review.html locally. No approval or publication has occurred.\n',encoding='utf-8')
        else:
            combined,result=stage(database,read(a.records),read(a.manifest),a.allow_distinct_location)
            write(a.output/'studios.json',combined);write(a.output/'proposal-audit.json',result)
            review=dossier({'version':1,'sources':{},'candidates':{}},{'sources':[]},database,
                           {'version':1,'sources':[]},read(a.records))
            write(a.output/'proposal-review.json',review)
            (a.output/'review.html').write_text(review_html(review),encoding='utf-8')
        print(json.dumps({'mode':a.mode,'published_records':0,'approved_claims':0}))
        return 0
    except (OSError,ValueError,TypeError,KeyError) as exc:
        print(f'Research preparation blocked: {exc}');return 1


if __name__=='__main__':raise SystemExit(main())
