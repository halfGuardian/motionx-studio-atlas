#!/usr/bin/env python3
"""Durable, checksummed research snapshots. No canonical-data write or approval."""
import argparse,gzip,hashlib,json,re
from pathlib import Path
from discovery import digest,read,write

def hash_bytes(data):return hashlib.sha256(data).hexdigest()

def archive(source,review,destination,run_id):
    if not re.fullmatch(r'[0-9]+',run_id):raise ValueError('numeric Actions run ID required')
    destination=Path(destination)
    if destination.exists():raise ValueError('immutable archive destination already exists')
    destination.mkdir(parents=True);files=[]
    for label,folder in [('snapshots',Path(source)),('review',Path(review))]:
        for path in sorted(folder.rglob('*')):
            if not path.is_file() or path.is_symlink() or path.suffix not in ('.json','.jsonl','.csv','.html','.sqlite'):continue
            relative=Path(label)/path.relative_to(folder)
            raw=path.read_bytes();packed=gzip.compress(raw,mtime=0)
            if len(packed)>40_000_000:raise ValueError('archive object too large; shard the research source before archiving')
            target=destination/relative.with_suffix(relative.suffix+'.gz');target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(packed)
            files.append({'path':str(target.relative_to(destination)),'sha256':hash_bytes(packed),'uncompressed_sha256':hash_bytes(raw),'bytes':len(raw),'compressed_bytes':len(packed)})
    if not files:raise ValueError('no snapshot/report files to archive')
    manifest={'version':1,'actions_run_id':run_id,'files':files,'snapshot_hash':digest(files),'publication_approved':False,'restore_note':'Verify every object and projection hash. Missing/incomplete source history cannot create closure or deletion signals.'}
    write(destination/'manifest.json',manifest);return manifest

def restore(source,destination):
    source=Path(source);destination=Path(destination);m=read(source/'manifest.json')
    if m.get('version')!=1 or digest(m['files'])!=m.get('snapshot_hash'):raise ValueError('archive manifest integrity mismatch')
    if destination.exists():raise ValueError('fresh restore directory required')
    staged=[]
    for f in m['files']:
        path=Path(f['path'])
        if path.is_absolute() or '..' in path.parts or path.parts[0] not in ('snapshots','review') or path.suffix!='.gz':raise ValueError('unsafe archive path')
        object_path=source/path
        if object_path.is_symlink():raise ValueError('archive symlink rejected')
        data=object_path.read_bytes()
        if hash_bytes(data)!=f['sha256']:raise ValueError('archive object integrity mismatch')
        if not 0<=f['bytes']<=300_000_000:raise ValueError('archive decompression limit')
        import io
        with gzip.GzipFile(fileobj=io.BytesIO(data)) as stream:raw=stream.read(f['bytes']+1)
        if len(raw)!=f['bytes'] or hash_bytes(raw)!=f['uncompressed_sha256']:raise ValueError('archive decompressed integrity mismatch')
        staged.append((path.with_suffix(''),raw))
    destination.mkdir(parents=True)
    for path,raw in staged:
        target=destination/path;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw)
    return m

def main():
    p=argparse.ArgumentParser(description=__doc__);sub=p.add_subparsers(dest='command',required=True)
    a=sub.add_parser('archive');a.add_argument('--snapshots',type=Path,required=True);a.add_argument('--review',type=Path,required=True);a.add_argument('--output',type=Path,required=True);a.add_argument('--run-id',required=True)
    a=sub.add_parser('restore');a.add_argument('archive',type=Path);a.add_argument('--output',type=Path,required=True)
    args=p.parse_args()
    result=archive(args.snapshots,args.review,args.output,args.run_id) if args.command=='archive' else restore(args.archive,args.output)
    print(json.dumps({'snapshot_hash':result['snapshot_hash'],'files':len(result['files']),'publication_approved':False}))
if __name__=='__main__':main()
