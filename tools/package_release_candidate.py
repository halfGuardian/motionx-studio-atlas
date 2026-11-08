#!/usr/bin/env python3
"""Package a read-only review bundle or complete static draft atlas, not deploy."""
import argparse,shutil
from pathlib import Path
from discovery import ROOT

def package(output,review_only=False,source=ROOT):
    output=Path(output).resolve();source=Path(source).resolve()
    if output.exists() or output.is_relative_to(source):raise ValueError('Fresh artifact directory outside the checkout required')
    paths=[source/'data/release-candidate',source/'data/global-programme/continuation/reports',source/'data/nz-census/final-review/reports']
    if not review_only:
        paths=[source/'index.html',source/'atlas.css',source/'studios.json',*sorted(source.glob('*.js')),source/'data/public',source/'data/release-candidate',source/'data/global-programme',source/'data/nz-census',source/'data/annecy/reports',source/'data/boutique/reports',source/'data/bulk/reports',source/'data/bulk/LICENSES',source/'data/bulk/NOTICE.html']
    for path in paths:
        if not path.exists() or path.is_symlink() or path.is_dir() and any(p.is_symlink() for p in path.rglob('*')):raise ValueError('Missing/unsafe public artifact path: '+path.name)
    for path in paths:
        target=output/path.relative_to(source);target.parent.mkdir(parents=True,exist_ok=True)
        if path.is_dir():shutil.copytree(path,target)
        else:shutil.copyfile(path,target)
    if review_only:
        (output/'index.html').write_text('<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>MotionX release decisions</title><h1>MotionX release decision bundle</h1><p><a href="data/release-candidate/reports/dashboard.html">182 integrated company records, two withheld records and exact fields</a> · <a href="data/release-candidate/DECISIONS.md">Short maintainer decisions</a></p><p>This review-only bundle contains evidence and exact fields. Atlas profile links require the matching checkout or the separate complete static-atlas artifact. Serve either folder over local HTTP. Neither artifact is a deployment or human approval.</p>',encoding='utf-8')
    return output

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',required=True,type=Path);p.add_argument('--review-only',action='store_true');a=p.parse_args();print(package(a.output,a.review_only))
