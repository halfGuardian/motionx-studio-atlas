"""Explicit frozen PR #18 cohort for historical report reproduction.

The public loader still reads the actual integrated catalogue. Historical tools
opt into this reader; the release-candidate checker validates all current rows.
No rows are hidden from the public application or the canonical validator.
"""
from pathlib import Path
from discovery import ROOT, read, digest
from bulk_catalog import sha

HOME=ROOT/'data/release-candidate'

def public_file(public,name):
    public=Path(public)
    if read(public/'manifest.json').get('release_candidate'):
        checkpoint=read(HOME/'inputs/parent-checkpoint.json')
        if name in checkpoint['parent_asset_hashes']:
            p=HOME/'inputs/parent-public'/name
            if sha(p)!=checkpoint['parent_asset_hashes'][name]:raise ValueError('Frozen parent asset changed: '+name)
            return p
    return public/name

def records(public,database):
    from launch_readiness import records as current_records
    public=Path(public);m,rows=current_records(public,database)
    if not m.get('release_candidate'):return m,rows
    cfg=read(HOME/'inputs/parent-checkpoint.json');byid={r['id']:r for r in rows}
    if any(rid not in byid or digest(byid[rid])!=h for rid,h in cfg['record_hashes'].items()):raise ValueError('Historical record lost or changed in release candidate')
    parent=read(public_file(public,'manifest.json'))
    if parent['counts']!=cfg['parent_counts'] or sha(database)!=cfg['root_sha256']:raise ValueError('Frozen parent count/root mismatch')
    return parent,[r for r in rows if r['id'] in cfg['record_hashes']]
