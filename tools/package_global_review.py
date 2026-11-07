#!/usr/bin/env python3
"""Package the checked global report with working relative assets, never publish."""
import argparse,shutil
from pathlib import Path
from discovery import ROOT

def package(output,source=ROOT):
    output=Path(output).resolve();source=Path(source).resolve()
    if output.exists() or output.is_relative_to(source):raise ValueError('Artifact output must be fresh and outside the checkout')
    included=[source/'data/global-programme',source/'data/nz-census/final-review/reports',source/'global-review.js',source/'nz-final-review.js']
    for path in included:
        if not path.exists():raise ValueError('Missing review artifact input: '+path.name)
        if path.is_symlink() or (path.is_dir() and any(p.is_symlink() for p in path.rglob('*'))):raise ValueError('Symlink/private-path projection forbidden')
    for path in included:
        dest=output/path.relative_to(source);dest.parent.mkdir(parents=True,exist_ok=True)
        if path.is_dir():shutil.copytree(path,dest)
        else:shutil.copyfile(path,dest)
    (output/'index.html').write_text('<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>MotionX global research artifact</title><h1>MotionX global research artifact</h1><p><a href="data/global-programme/continuation/reports/dashboard.html">Company proposals, scope impact and continuation queue</a> · <a href="data/global-programme/reports/dashboard.html">Starting global review dashboard</a></p><p>This is an offline research bundle, not the published Atlas. Serve this folder over localhost HTTP. Public-directory profiles require the matching repository checkout. Working notes cannot authorise publication.</p><p><a href="https://github.com/halfGuardian/motionx-studio-atlas/pull/18" rel="noopener noreferrer">Draft PR #18 and human review</a></p></html>\n',encoding='utf-8')
    return output

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);args=p.parse_args();print(package(args.output))
