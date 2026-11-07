#!/usr/bin/env python3
"""Reproduce v1.1 plus boutique additions into a fresh proposal, never publish."""
import argparse,contextlib,io,json,tempfile
from pathlib import Path
from discovery import ROOT,read,write,digest
from bulk_archive import restore
from bulk_catalog import sha
from unified_catalog import build
from boutique import HOME,extend,save_reports

def prepare(output):
    output=Path(output)
    if output.exists():raise ValueError('fresh proposal output required; never overwrite history')
    release=read(ROOT/'data/bulk/release.json')
    if sha(ROOT/'studios.json')!=release['retained_baseline_sha256']:raise ValueError('retained baseline changed; explicit reconciliation required')
    if digest(read(ROOT/'data/bulk/sources.json'))!=release['source_policy_hash']:raise ValueError('historical bulk policy changed; do not silently reclassify old records')
    if sha(ROOT/release['company_references'])!=release['company_reference_sha256']:raise ValueError('historical game-company projection changed')
    with tempfile.TemporaryDirectory() as tmp:
        restore(ROOT/release['snapshot_archive'],Path(tmp)/'restored')
        m,_=build(Path(tmp)/'restored/snapshots',ROOT/release['company_references'],output/'public',ROOT/'studios.json',ROOT/'data/bulk/sources.json',observed=release['company_observed_on_utc'],company_source=release['company_source_url'])
        if m['counts']!=release['expected_counts']:raise ValueError('baseline release reproduction mismatch')
    before=read(output/'public/manifest.json');result=extend(output/'public',ROOT/'studios.json');save_reports(result,output/'reports')
    inputs={str(p.relative_to(HOME)):sha(p) for folder in ('inputs','benchmarks') for p in sorted((HOME/folder).glob('*.json'))}
    inputs.update({name:sha(HOME/name) for name in ('regions.json','vocabulary.json')})
    write(output/'release.json',{'version':1,'baseline_records':41735,'baseline_main_commit':'6d5ba61bba4e654369a6444b6363aeb342d43173','retained_baseline_sha256':sha(ROOT/'studios.json'),'retained_shard_hashes':{n:v['sha256'] for n,v in before['shards'].items()},'input_hashes':inputs,'source_registry_hash':digest(read(HOME/'sources.json')),'expected_counts':read(output/'public/manifest.json')['counts'],'publication_approved':False,'approval_mode':'Draft PR with explicit human review; no approval bundle or historical approval reused.'})
    return result['summary']

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    with contextlib.redirect_stdout(io.StringIO()):summary=prepare(a.output)
    print(json.dumps(summary,indent=2))
if __name__=='__main__':main()
