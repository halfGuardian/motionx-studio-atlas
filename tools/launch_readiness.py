#!/usr/bin/env python3
"""Build an advisory research queue and licensing audit. Never approve or publish."""
import argparse, hashlib, html, json, re, tempfile
from collections import Counter
from pathlib import Path
from compact_index import review_flags
from discovery import ROOT, read, write, digest
from validate import url_valid, ID

STATUSES = ('Reuse documented', 'Reuse requires review', 'Permission not established', 'Restricted')

def file_sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def records(public, database):
    public=Path(public);m=read(public/'manifest.json')
    if file_sha(database)!=m['baseline']['sha256']: raise ValueError('baseline integrity mismatch')
    rows=[{**r,'evidence_class':'A' if r['evidence_state']=='confirmed' else 'C','record_kind':'retained_location'} for r in read(database)]
    for key,meta in sorted(m['shards'].items()):
        path=public/key
        if not re.fullmatch(r'shards/[a-f0-9]{12}-\d{3,}\.json',key) or path.is_symlink() or not path.resolve().is_relative_to(public.resolve()) or file_sha(path)!=meta['sha256']: raise ValueError('shard integrity mismatch')
        chunk=read(path)
        if len(chunk)!=meta['records']: raise ValueError('shard count mismatch')
        rows.extend(chunk)
    if len({r['id'] for r in rows})!=len(rows) or len(rows)!=m['counts']['records']: raise ValueError('catalogue identity/count mismatch')
    return m,rows

def dataset(name,url,version,retrieval,licence,status,attribution,commercial,notices,question,promotion,count=None):
    if status not in STATUSES or not url_valid(url): raise ValueError('invalid audit source/status')
    return dict(source=name,url=url,dataset_version=version,retrieval_or_recorded_review=retrieval,applicable_licence=licence,redistribution_status=status,attribution_requirements=attribution,commercial_use_restrictions=commercial,required_notices=notices,unresolved_questions=question,broader_promotion_or_reuse=promotion,records=count)

def build_audit(m,rows,bulk,discovery,receipt):
    new=[r for r in rows if r['record_kind']!='retained_location'];licences=Counter(r.get('license') for r in new)
    game_count=sum(any(p.get('source_id')=='game-studios-db' for p in r.get('source_provenance',[])) for r in new)
    observed=sorted({r['source_observed_on'] for r in new if r.get('source_observed_on')});retrieval=', '.join(observed) or 'Not recorded'
    overture=next(s for s in bulk['sources'] if s['id']=='overture')
    datasets=[
      dataset('Retained MotionX source evidence','https://github.com/halfGuardian/motionx-studio-atlas',m['baseline']['sha256'],'Per-record dates; legacy unknowns are not verified','Factual research with heterogeneous source terms','Reuse requires review','Keep each evidence URL/date and original operating identity.','No blanket permission for third-party authored content established.','Coordinate credits and evidence citations.','13 legacy evidence unknowns; source-wide redistribution clearance is not asserted.','Pending a scoped launch review.',len(rows)-len(new)),
      dataset('Overture Places — CDLA projected metadata','https://docs.overturemaps.org/attribution/',overture['release'],retrieval,'CDLA-Permissive-2.0','Reuse documented','Overture and original providers, per-record IDs/dates and transformation notes.','No noncommercial restriction in the documented licence.','Full CDLA text.','Current business operation and facility capabilities remain uncorroborated.','Documented for the projected licensed fields, subject to notices; not source-wide clearance.',licences.get('CDLA-Permissive-2.0',0)),
      dataset('Overture Places — Foursquare projected metadata','https://docs.overturemaps.org/attribution/',overture['release'],retrieval,'Apache-2.0','Reuse documented','Foursquare copyright, attribution and transformation notice.','No noncommercial restriction in the documented licence.','Full Apache licence and Foursquare NOTICE.','Retain notices in downstream exports; source score is not verification.','Documented for the projected licensed fields with full notices.',licences.get('Apache-2.0',0)),
      dataset('Overture-signals status overlays (payload withheld)','https://docs.overturemaps.org/attribution/',overture['release'],retrieval,'Per-field grant not established','Permission not established','Keep source identity and original observation/page hashes.','Not established.','Do not redistribute unresolved overlay payloads.','Original payload is withheld; affected reference identities remain in Class C.','No; permission for overlay values remains unresolved.'),
      dataset('Game Studios & Publishers Database — factual references',receipt['source_url'],receipt['source_commit'],receipt['observed_on_utc'],'UNSPECIFIED','Permission not established','EddieWing/source link; factual identifiers only, no authored descriptions or social/contact profiles.','No explicit dataset redistribution or commercial-use grant established.','Visible unspecified-terms warning and source receipt.','Download/local-use instructions are not an explicit redistribution licence. Source changed '+receipt['source_changed_at_utc']+'.','No; all '+format(game_count,',')+' references require further permission review.',game_count),
      dataset('GeoNames approximate city references','https://www.geonames.org/',m['baseline']['sha256'],'Per-record coordinate/evidence dates','CC-BY-4.0','Reuse documented','Credit GeoNames, link CC BY 4.0 and identify use as approximate city references.','Commercial reuse permitted subject to attribution.','Retain coordinate-source URLs and attribution.','City reference points are not verified facility geocodes.','Documented for attributed city reference coordinates.'),
      dataset('Iver Heath city reference — ONS / Planning Data','https://www.planning.data.gov.uk/entity/2504906',m['baseline']['sha256'],'Per-record coordinate/evidence dates','OGL-3.0','Reuse documented','Crown copyright / Office for National Statistics via Planning Data; link OGL v3.0.','Subject to OGL terms.','Existing coordinate attribution and source link.','Not a verified facility address.','Documented for the attributed reference point.'),
      dataset('ISO country display names — Unicode CLDR','https://cldr.unicode.org/','Committed country-codes.json',bulk.get('reviewed_on','Not recorded'),'Unicode-3.0','Reuse documented','Keep Unicode copyright and permission notice.','Subject to Unicode licence.','Full Unicode-3.0 licence in LICENSES.','A country name is not independent geocoding.','Documented with notice.'),
      dataset('Interactive OpenStreetMap tiles','https://operations.osmfoundation.org/policies/tiles/','Existing interactive tile service','Not a newly acquired place dataset','OSM attribution / tile usage policy','Reuse documented','© OpenStreetMap contributors with copyright link.','Service usage limits apply; no bulk tile download or prefetch.','Visible map attribution.','Tile-service policy does not license separate business-directory collection.','Interactive use only, subject to tile policy.'),
    ]
    for sid in sorted({p['source_id'] for r in new for p in r.get('source_provenance',[]) if r['id'].startswith(('boutique-','annecy-','nzcensus-'))}):
        cohort=[r for r in new if any(p['source_id']==sid for p in r.get('source_provenance',[]))];first=cohort[0];p=next(p for p in first['source_provenance'] if p['source_id']==sid)
        datasets.append(dataset(('NZ census research: ' if sid in ('nzonair-gdsr','nzonair-gdsr-context','nz-company-primary-review') else 'Boutique discovery: ')+sid,p['url'],first.get('source_release',''),p['observed_on'],p['license'],'Reuse documented' if p['license'] in ('CC-BY-4.0','NZ-On-Air-Permission') else 'Permission not established',first['attribution'],'Subject to the source-specific grant; no blanket source-wide clearance.','Retain original source links, dates, attribution and applicable full licence.','Company references do not establish current facilities or independently verified services.','Accurate attributed agency projection; retain copyright and controlling terms. No third-party media or independent verification.' if p['license']=='NZ-On-Air-Permission' else 'CC BY factual projection with notices.' if p['license']=='CC-BY-4.0' else 'Further permission review before automated bulk reuse.',len(cohort)))
    global_refs=[r for r in new if r['id'].startswith('globalcompany-')]
    if global_refs:
        datasets.append(dataset('Global release candidate — minimal factual company references','https://github.com/halfGuardian/motionx-studio-atlas',m['release_candidate']['parent_commit'],', '.join(sorted({r['source_observed_on'] for r in global_refs})),'UNSPECIFIED','Reuse requires review','Retain every per-record source URL/date, original source sector labels and scoped attribution.','No source-wide redistribution or commercial reuse grant inferred; limited factual fields only.','Keep unverified Class C/company-only status, source-specific uncertainty and attribution. No copied descriptions, media or contacts.','Maintainer must review the exact minimal factual scope and draft PR; unknown source-wide terms are neither a blanket grant nor an automatic ban on company identifiers.','Only the exact limited factual release candidate is proposed; expanded reuse needs a separate source-specific decision.',len(global_refs)))
    for registry_name,registry in (('bulk registry',bulk),('discovery registry',discovery)):
        for source in registry['sources']:
            url=source.get('url') or source.get('endpoint')
            if not url_valid(url): continue
            restricted=source['id'] in ('ea','electronic-arts','ea-studios','cinesite','cinesite-group')
            status='Restricted' if restricted else 'Reuse requires review' if source.get('enabled') else 'Permission not established'
            review=source.get('access_review',{})
            datasets.append(dataset(registry_name+': '+source['id'],url,digest(source),review.get('reviewed_on') or bulk.get('reviewed_on','Not recorded'),source.get('license') or 'No source-wide redistribution grant recorded',status,source.get('attribution') or 'Retain factual source links and per-record evidence.','See recorded source-specific terms; no blanket commercial permission.',source.get('reuse_note') or source.get('review') or source.get('reason','No grant recorded.'),source.get('disabled_reason') or source.get('reason') or 'Collection access does not establish redistribution permission.','No automatic source-wide clearance; inspect the scoped dataset entries above.'))
    return {'version':1,'basis':'Existing recorded source-policy and provenance audits; no new permission or human approval is granted by report generation.','baseline_sha256':m['baseline']['sha256'],'public_access':'The repository and GitHub Pages remain public; internal research intent does not restrict access.','datasets':datasets,'launch_checklist':['Resolve game-company dataset redistribution/commercial-use permission before broader reuse or promotion.','Keep A/B/C labels, company-only records without pins, duplicate warnings and per-source notices.','Review 13 legacy unknown-evidence locations individually; no automatic removals.','Resolve identity conflicts and corroborate actual physical facilities before upgrading a record.','Preserve all raw/reference IDs, original coordinates and evidence history during any correction.','Verify current provider notices and all inherited coordinate attribution.','Review canonical changes in a human-authorised PR; do not fabricate approval hashes.','Inspect required-review rules and bypass rights; current enforcement is unconfirmed.','Re-test deployed Pages after any authorised merge; this draft does not deploy.']}

def atlas_prefix(output):
    try:return '../'*len(Path(output).resolve().relative_to(ROOT.resolve()).parts)
    except ValueError:return '../../../'

def generate(public,database,output,bulk=None,discovery=None,receipt=None,return_prefix=None,historical=False):
    output=Path(output)
    prefix=atlas_prefix(output) if return_prefix is None else return_prefix
    if not re.fullmatch(r'(?:\.\./){0,8}',prefix):raise ValueError('Invalid relative Atlas return link')
    if output.exists(): raise ValueError('fresh report output directory required')
    if historical:
        from catalogue_history import records as parent_records,public_file
        m,rows=parent_records(public,database);manifest_path=public_file(public,'manifest.json')
    else:m,rows=records(public,database);manifest_path=Path(public)/'manifest.json'
    audit=build_audit(m,rows,bulk or read(ROOT/'data/bulk/sources.json'),discovery or read(ROOT/'data/discovery/sources.json'),receipt or read(ROOT/'data/bulk/unified-input/source-receipt.json'))
    audit['catalogue_sha256']=file_sha(manifest_path)
    queue=[]
    for r in rows:
        if r['evidence_class']=='A': continue
        queue.append([r['id'],r['evidence_class'],review_flags(r),digest(r),r['country'],r.get('source_observed_on') or r.get('verified_on',''),r.get('evidence',''),[other for p in r.get('potential_duplicates',[]) for other in p['ids'] if other!=r['id']]])
    queue.sort(key=lambda row:(-bool(row[2]&1),-bool(row[2]&8),row[4],row[0]))
    output.mkdir(parents=True)
    write(output/'licensing.json',audit)
    write(output/'review-queue.json',{'version':1,'catalogue_sha256':audit['catalogue_sha256'],'baseline_sha256':audit['baseline_sha256'],'approval_granted':False,'columns':['record_id','evidence_class','advisory_risk_flags','record_hash','country','recorded_date','evidence_url','possible_matches'],'flags':{'1':'possible duplicate','2':'historical/status assertion','4':'geography/physical branch unresolved','8':'source permission review','16':'no confirmed facility capabilities'},'records':len(queue),'entries':queue,'next_step':'Research individual claims, then prepare an exact-content proposal using the existing research.py stage-pr workflow. Scores and this queue never approve publication.'})
    # A review template is hash-bound to exact source data, not an approval file.
    esc=html.escape
    def link(url,label): return '<a href="'+esc(url,quote=True)+'" target="_blank" rel="noopener noreferrer">'+esc(label)+'</a>' if url_valid(url) else esc(label)
    cards=''.join('<article><h2>'+link(d['url'],d['source'])+'</h2><p class="status">'+esc(d['redistribution_status'])+'</p><dl>'+''.join('<dt>'+esc(k.replace('_',' '))+'</dt><dd>'+esc(str(v))+'</dd>' for k,v in d.items() if k not in ('source','url','redistribution_status'))+'</dl></article>' for d in audit['datasets'])
    page='<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>MotionX — Licensing & launch readiness</title><style>body{font:16px/1.6 system-ui;color:#edf3fa;background:#0c1420;max-width:1050px;margin:auto;padding:24px}a{color:#acd9ff}a:focus-visible{outline:3px solid #ffd875}article{background:#152133;border:1px solid #43546a;border-radius:10px;padding:20px;margin:20px 0}h2{font-size:20px}.status{border-left:4px solid #B58A2A;padding-left:12px;font-weight:bold}dl{display:grid;grid-template-columns:minmax(120px,1fr) 3fr;gap:10px;font-size:14px}dd{margin:0;overflow-wrap:anywhere}dt{color:#bccbde}li{margin:10px 0}@media(max-width:600px){body{padding:12px}dl{display:block}dt{font-weight:bold;margin-top:12px}}</style><h1>Licensing & future-launch readiness</h1><p><a href="../../../index.html">Return to the unified atlas</a> · <a href="licensing.json">Machine-readable audit</a></p><p>'+esc(audit['public_access'])+'</p><p>'+esc(audit['basis'])+'</p><p><strong>All '+format(sum(r.get('license')=='UNSPECIFIED' for r in rows),',')+' references with UNSPECIFIED terms are retained with audit access; normal directory scope may exclude reviewed out-of-scope records. Source-specific cohorts are distinguished below. No authored descriptions or photographs are added.</strong></p><h2>Future-launch checklist</h2><ul>'+''.join('<li>'+esc(s)+'</li>' for s in audit['launch_checklist'])+'</ul>'+cards+'</html>'
    page=page.replace('href="../../../index.html"','href="'+prefix+'index.html"')
    (output/'licensing.html').write_text(page,encoding='utf-8')
    return {'datasets':len(audit['datasets']),'review_queue':len(queue),'approval_granted':False}

def template(record_id,public,database,queue_path,output):
    if not ID.fullmatch(record_id): raise ValueError('invalid record identity')
    output=Path(output)
    if output.exists(): raise ValueError('fresh template path required')
    m,rows=records(public,database);queue=read(queue_path)
    if queue['baseline_sha256']!=file_sha(database) or queue['catalogue_sha256']!=file_sha(Path(public)/'manifest.json') or queue.get('approval_granted') is not False: raise ValueError('stale or invalid review checkpoint')
    row=next((r for r in rows if r['id']==record_id),None);entry=next((r for r in queue['entries'] if r[0]==record_id),None)
    if not row or not entry or entry[3]!=digest(row): raise ValueError('source record not bound to pending checkpoint')
    write(output,{'status':'unverified_research_template','approval_granted':False,'baseline_sha256':m['baseline']['sha256'],'source_record_hash':digest(row),'original_reference':row,'required_human_research':['Confirm current physical production facility and operating identity; company-only references do not establish branches.','Retain the record ID and all source observations; resolve possible duplicates explicitly.','Cite current location and each facility capability independently, with actual review dates.','Review source permissions, coordinates and any ownership relationship.','Prepare before/after evidence using research.py stage-pr. An explicit reviewed reconciliation must preserve the original reference when a canonical record is later promoted.'],'canonical_record':None})

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('command',choices=('generate','template','check'));p.add_argument('--public',type=Path,default=ROOT/'data/public');p.add_argument('--database',type=Path,default=ROOT/'studios.json');p.add_argument('--output',type=Path,required=True);p.add_argument('--record-id');p.add_argument('--queue',type=Path,default=ROOT/'data/bulk/reports/review-queue.json');a=p.parse_args()
    if a.command=='generate': print(json.dumps(generate(a.public,a.database,a.output)))
    elif a.command=='template': template(a.record_id or '',a.public,a.database,a.queue,a.output)
    else:
        with tempfile.TemporaryDirectory() as folder:
            fresh=Path(folder)/'reports';result=generate(a.public,a.database,fresh,return_prefix=atlas_prefix(a.output),historical=a.output.resolve()==(ROOT/'data/global-programme/reports/readiness').resolve())
            for path in fresh.iterdir():
                if not (a.output/path.name).is_file() or path.read_bytes()!=(a.output/path.name).read_bytes():raise ValueError('stale readiness report: '+path.name)
        print(json.dumps({**result,'report_integrity':'passed'}))
if __name__=='__main__': main()
