#!/usr/bin/env python3
"""Reproduce the proposed public catalogue from its licensed research archive.

Validation is not human publication approval. No source fetch or database write.
"""
import contextlib,gzip,io,json,tempfile
from pathlib import Path
from bulk_archive import restore
from bulk_catalog import build,sha,validate_b
from bulk_ingest import ingest
from discovery import ROOT,read,digest

def check(root=ROOT):
    root=Path(root);release=read(root/'data/bulk/release.json')
    archive=Path(release['snapshot_archive'])
    if archive.is_absolute() or '..' in archive.parts or archive.parts[:3]!=('data','bulk','runs'):raise ValueError('unapproved release archive path')
    if sha(root/'studios.json')!=release['retained_baseline_sha256']:raise ValueError('retained baseline changed')
    if digest(read(root/'data/bulk/sources.json'))!=release['source_policy_hash']:raise ValueError('source policy changed; regenerate proposal, do not reuse stale claims')
    with tempfile.TemporaryDirectory() as tmp:
        tmp=Path(tmp);restore(root/archive,tmp/'restored');snapshots=tmp/'restored/snapshots'
        report=ingest(snapshots,tmp/'review',read(root/'data/bulk/sources.json'),read(root/'studios.json'))
        if not report['acquisition_complete']:raise ValueError('complete acquisition provenance required for this release')
        if release.get('mode')=='unified_research':
            from unified_catalog import build as build_unified
            companies=Path(release['company_references'])
            if companies.is_absolute() or '..' in companies.parts or sha(root/companies)!=release['company_reference_sha256']:raise ValueError('company reference projection changed')
            expected,_=build_unified(snapshots,root/companies,tmp/'public',root/'studios.json',root/'data/bulk/sources.json',observed=release['company_observed_on_utc'],company_source=release['company_source_url'])
        else:expected=build(read(tmp/'review/proposed-b.json'),root/'studios.json',tmp/'public',release['source_policy_hash'],report['run_id'])
        if expected['counts']!=release['expected_counts']:raise ValueError('release counts differ from reproduced catalogue')
        extension=root/'data/boutique/release.json'
        if extension.exists():
            from boutique import extend
            config=read(extension)
            if config['baseline_records']!=expected['counts']['records']:raise ValueError('boutique baseline mismatch')
            for name,expected_hash in config['input_hashes'].items():
                path=Path(name)
                if path.is_absolute() or '..' in path.parts or (path.parts[0] not in ('inputs','benchmarks') and str(path) not in ('regions.json','vocabulary.json')) or sha(root/'data/boutique'/path)!=expected_hash:raise ValueError('boutique input checkpoint changed')
            proposal=extend(tmp/'public',root/'studios.json',root/'data/boutique')
            expected=read(tmp/'public/manifest.json')
            if expected['counts']!=config['expected_counts']:raise ValueError('boutique release counts differ')
            if digest(read(root/'data/boutique/sources.json'))!=config['source_registry_hash']:raise ValueError('boutique source policy changed')
        annecy=root/'data/annecy/release.json'
        if annecy.exists():
            from annecy import verify_checkpoint,extend as extend_annecy
            config=verify_checkpoint(root/'data/annecy')
            if expected['counts']!=config['before_counts']:raise ValueError('Annecy baseline mismatch')
            proposal=extend_annecy(tmp/'public',root/'studios.json',root/'data/annecy')
            expected=read(tmp/'public/manifest.json')
            if expected['counts']!=config['after_counts']:raise ValueError('Annecy release counts differ')
        nz=root/'data/nz-census/release.json'
        if nz.exists():
            from nz_research import checkpoint,extend as extend_nz
            config=checkpoint(root/'data/nz-census')
            if expected['counts']!=config['before_counts']:raise ValueError('NZ census baseline mismatch')
            extend_nz(tmp/'public',root/'studios.json',root/'data/nz-census')
            expected=read(tmp/'public/manifest.json')
            if expected['counts']!=config['after_counts']:raise ValueError('NZ census release counts differ')
        gate=root/'data/nz-census/final-review/release.json'
        if gate.exists():
            from nz_quality_gate import checkpoint as gate_checkpoint,apply as apply_gate
            config=gate_checkpoint(root/'data/nz-census/final-review')
            if expected['counts']!=config['before_counts']:raise ValueError('NZ quality gate baseline mismatch')
            apply_gate(tmp/'public',root/'studios.json',root/'data/nz-census/final-review')
            expected=read(tmp/'public/manifest.json')
            if expected['counts']!=config['after_counts']:raise ValueError('NZ final gate release counts differ')
        visibility=root/'data/global-programme/inputs/location-reviews.json'
        if visibility.exists():
            from global_visibility import install
            install(tmp/'public',root/'studios.json',root/'data/global-programme')
            expected=read(tmp/'public/manifest.json')
        if (root/'data/global-programme/continuation/inputs/scope-reviews.json').exists():
            from global_continuation import install as install_scope
            install_scope(tmp/'public',root/'studios.json',root/'data/global-programme/continuation')
            expected=read(tmp/'public/manifest.json')
        if (root/'data/release-candidate/inputs/admissions.json').exists():
            from release_candidate import apply_draft
            apply_draft(tmp/'public',root/'studios.json',root/'data/release-candidate')
            expected=read(tmp/'public/manifest.json')
        generated={str(p.relative_to(tmp/'public')) for p in (tmp/'public').rglob('*.json')}
        actual={str(p.relative_to(root/'data/public')) for p in (root/'data/public').rglob('*.json')}
        if generated!=actual:raise ValueError('catalogue file set differs from reclassified snapshots')
        for name in sorted(generated):
            if read(tmp/'public'/name)!=read(root/'data/public'/name):raise ValueError('public catalogue differs from exact source proposal: '+name)
            compressed=root/'data/public'/(name+'.gz')
            if compressed.exists() and gzip.decompress(compressed.read_bytes())!=(root/'data/public'/name).read_bytes():raise ValueError('invalid gzip sidecar')
        return {'validation_errors':0,'counts':expected['counts'],'baseline_preserved':release['retained_baseline_sha256'],'raw_source_records':report['raw_source_records'],'research_candidates':report['candidate_classes'].get('C',0),'warnings':expected['warnings'],'approval':'Human review and authorised merge still required; tests are not approval.'}

if __name__=='__main__':
    with contextlib.redirect_stdout(io.StringIO()):result=check()
    print(json.dumps(result,indent=2))
