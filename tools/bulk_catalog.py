#!/usr/bin/env python3
"""Stage a hash-bound, sharded Class-B catalogue for human PR review.

The licensed snapshots are reclassified, never trusted as approved input. This
does not alter studios.json, approve claims, merge a PR or deploy. A reviewer
must authorise the exact source policy, decisions and generated catalogue.
"""
import argparse,gzip,hashlib,json,math,re,tempfile
from collections import Counter,defaultdict
from pathlib import Path
from datetime import date
from bulk_ingest import ingest,source_policy
from discovery import ROOT,read,write,digest
from validate import validate,url_valid,ID

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def validate_b(rows):
    errors,warnings=validate(rows)
    for r in rows:
        ref=r.get('id','invalid')
        def error(s):errors.append(ref+': '+s)
        if r.get('evidence_class')!='B' or r.get('evidence_state')!='unknown' or r.get('verified_on') or r.get('capabilities') or r.get('capability_evidence'):
            error('source-listed data cannot claim verified operation/capabilities/review')
        if r.get('relationships'):error('directory ownership claims need separate evidence review')
        if r.get('coordinate_precision')=='exact':error('directory points are not verified facility geocodes')
        if r.get('identity_status') not in ('source_provisional','matched_existing'):error('identity resolution status required')
        if r.get('website_kind') not in ('official','source_listing'):error('website kind required')
        if not r.get('license') or not r.get('attribution'):error('source licence and attribution required')
        if set(r)-{'id','company_id','name','city','country','website','lat','lng','address','categories','capabilities','capability_evidence','evidence_state','evidence_class','evidence','verified_on','source_observed_on','coordinate_precision','coordinate_source','location_type','relationships','status','website_kind','source_provenance','license','attribution','identity_status'}:
            error('unsupported/private source-listed fields')
        provenance=r.get('source_provenance')
        if not isinstance(provenance,list) or not provenance:error('record-level provenance required');continue
        for p in provenance:
            if not isinstance(p,dict) or not url_valid(p.get('url')) or not url_valid(p.get('license_url')) or not p.get('source_id') or not p.get('source_record_id') or not re.fullmatch('[a-f0-9]{64}',p.get('observation_hash','')):
                error('invalid record-level provenance');continue
            try:
                if date.fromisoformat(p['observed_on']).isoformat()!=p['observed_on'] or p['observed_on']>date.today().isoformat():raise ValueError()
            except (KeyError,TypeError,ValueError):error('actual, non-future observation date required')
            if p.get('observed_on')!=r.get('source_observed_on') or p.get('license')!=r.get('license'):error('provenance date/licence mismatch')
    return errors,warnings

def compact(path,value):
    text=json.dumps(value,ensure_ascii=False,separators=(',',':'),allow_nan=False)+'\n';path.write_text(text,encoding='utf-8')
    # Sidecars for mirrors/previews. Pages negotiates its own compression; never
    # pretend GitHub Pages will serve these with Content-Encoding automatically.
    with gzip.GzipFile(filename='',fileobj=path.with_suffix(path.suffix+'.gz').open('wb'),mode='wb',mtime=0) as f:f.write(text.encode())

def build(records,baseline,output,policy_hash,run_id):
    baseline=Path(baseline);base=read(baseline);errors,warnings=validate(base)
    b_errors,b_warnings=validate_b(records)
    if errors or b_errors:raise ValueError('invalid catalogue: '+str((errors+b_errors)[:8]))
    base_ids={r['id'] for r in base}
    if any(r['id'] in base_ids for r in records):raise ValueError('bulk proposal cannot overwrite retained baseline IDs')
    output=Path(output)
    if output.exists():raise ValueError('fresh output directory required')
    output.mkdir(parents=True);(output/'shards').mkdir()
    grouped=defaultdict(list)
    for r in sorted(records,key=lambda r:r['id']):grouped[r['country']].append(r)
    index=[];shards={}
    for country,rows in sorted(grouped.items()):
        country_key=digest(country)[:12]
        for offset in range(0,len(rows),1000):
            chunk=rows[offset:offset+1000];name=f'shards/{country_key}-{offset//1000:03d}.json';path=output/name;compact(path,chunk)
            shards[name]={'sha256':sha(path),'records':len(chunk),'country':country,'bytes':path.stat().st_size}
            for r in chunk:index.append([r[k] for k in ('id','company_id','name','city','country','lat','lng','categories')]+[name,r['source_observed_on'],r['identity_status']])
    index.sort(key=lambda r:r[0]);compact(output/'index.json',index)
    # Preserve every legacy ID/evidence byte in the original canonical file.
    # Unreviewed legacy records are explicitly retained for research, never relabelled A.
    eligible=[r for r in base if r['evidence_state']=='confirmed' and r.get('evidence') and r.get('verified_on')]
    held=[r for r in base if r not in eligible]
    write(output/'legacy-research.json',{'reason':'Original IDs/evidence retained in studios.json; insufficient evidence for Class A/B catalogue. No confirmed capability claim is removed.','ids':[r['id'] for r in held]})
    if any(e.get('state')=='confirmed' for r in held for e in r['capability_evidence'].values()):raise ValueError('cannot quarantine a confirmed capability without explicit correction review')
    all_public=eligible+records
    manifest={'version':1,'review_mode':'manual_human_pr_review','publication_approved':False,'baseline':{'path':'./studios.json','sha256':sha(baseline),'retained_records':len(base),'eligible_ids':[r['id'] for r in eligible],'research_only_ids':[r['id'] for r in held]},
        'index':{'path':'index.json','sha256':sha(output/'index.json'),'records':len(records),'bytes':(output/'index.json').stat().st_size},'shards':shards,
        'source_policy_hash':policy_hash,'research_run_id':run_id,'counts':{'class_a':len(eligible),'class_b':len(records),'retained_legacy_research':len(held),'public_locations':len(all_public),'operating_identities':len({r['company_id'] for r in all_public}),'reviewed_operating_organisations':len({r['company_id'] for r in eligible}),'provisional_source_identities':len({r['company_id'] for r in records if r['identity_status']=='source_provisional'}),'countries':len({r['country'] for r in all_public})},
        'index_columns':['id','company_id','name','city','country','lat','lng','categories','detail_shard','source_observed_on','identity_status'],
        'licences':'../bulk/LICENSES/','warnings':{'baseline':len(warnings),'source_listed':len(b_warnings)},'warning_meaning':'Directory coordinates and operation are uncorroborated. Source-listed records carry no confirmed capabilities. Provisional source identities are not independently established operating organisations.'}
    write(output/'manifest.json',manifest)
    write(output/'audit.json',{'baseline_sha256_before':sha(baseline),'baseline_sha256_after':sha(baseline),'retained_location_ids':[r['id'] for r in base], 'proposed_b_ids':[r['id'] for r in records],'research_only_legacy_ids':[r['id'] for r in held],'canonical_validation_errors':0,'source_listed_validation_errors':0,'source_listed_warnings':b_warnings,'approval_required':'Human must review the exact PR diff before merge. Draft status and tests do not enforce approval. No historical approval bundle is reused.'})
    return manifest

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--input',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--database',type=Path,default=ROOT/'studios.json');p.add_argument('--config',type=Path,default=ROOT/'data/bulk/sources.json');a=p.parse_args()
    with tempfile.TemporaryDirectory() as tmp:
        folder=Path(tmp)/'review';report=ingest(a.input,folder,read(a.config),read(a.database))
        manifest=build(read(folder/'proposed-b.json'),a.database,a.output,digest(read(a.config)),report['run_id'])
    print(json.dumps(manifest['counts'],indent=2))
if __name__=='__main__':main()
