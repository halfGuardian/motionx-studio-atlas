#!/usr/bin/env python3
"""Validate immutable discovery checkpoints; recover candidates, never business approval."""
import argparse,hashlib,json
from datetime import date
from pathlib import Path
from discovery import ROOT,read,write,safe_output,merge_checkpoint
from validate import url_valid
MAX_FILE=50_000_000
MAX_TOTAL=250_000_000

def inside(root,path):
    if path.is_symlink() or root.resolve() not in path.resolve().parents:raise ValueError('checkpoint path must be a regular repository file')
    return path

def check_queue(queue):
    if queue.get('version')!=1 or not isinstance(queue.get('candidates'),dict) or not isinstance(queue.get('sources'),dict):raise ValueError('invalid checkpoint schema')
    if len(queue['candidates'])>100000:raise ValueError('checkpoint exceeds candidate limit')
    for cid,c in queue['candidates'].items():
        if not isinstance(c,dict) or c.get('id')!=cid or not url_valid(c.get('url')):raise ValueError('invalid checkpoint candidate identity')
        for field in ('source_id','label','confidence','content_hash'):
            if not isinstance(c.get(field),str):raise ValueError('missing candidate provenance')
        first=date.fromisoformat(c['first_seen']);last=date.fromisoformat(c['last_seen'])
        if last<first:raise ValueError('checkpoint observation dates are reversed')
        if c.get('review_status') not in ('pending','deferred','rejected','approved'):raise ValueError('invalid queue review state')
    return queue

def validate_manifest(manifest,root=ROOT):
    if manifest.get('version')!=1 or not isinstance(manifest.get('files'),list) or not manifest['files']:raise ValueError('nonempty checkpoint manifest required')
    seen=set();files={};total=0
    for entry in manifest['files']:
        relative=entry.get('path','');path=Path(relative)
        if path.is_absolute() or '..' in path.parts or relative in seen:raise ValueError('invalid or repeated checkpoint path')
        seen.add(relative);path=inside(root,root/path)
        size=path.stat().st_size
        if size>MAX_FILE:raise ValueError('checkpoint file exceeds limit')
        total+=size
        if total>MAX_TOTAL:raise ValueError('checkpoint archive exceeds limit; partition without deleting history')
        body=path.read_bytes()
        if hashlib.sha256(body).hexdigest()!=entry.get('sha256'):raise ValueError('checkpoint content hash mismatch')
        value=json.loads(body)
        if entry.get('kind')=='queue':check_queue(value)
        elif entry.get('kind') not in ('history','report'):raise ValueError('unknown checkpoint file kind')
        files[relative]=(entry,body,value)
    if manifest.get('queue_path') not in files or files[manifest['queue_path']][0]['kind']!='queue':raise ValueError('checkpoint queue is not bound by manifest')
    return files

def recover(manifest,root=ROOT,lost_run_id=None):
    files=validate_manifest(manifest,root);queue=files[manifest['queue_path']][2]
    report={'mode':'partial_checkpoint_recovery','checkpoint_candidate_count':len(queue['candidates']),
            'checkpoint_files':len(files),'lost_run_id':lost_run_id,'history_complete':False,
            'suppress_absence_signals':True,'published_records':0,'approved_claims':0,
            'warning':'Artifact history not present in this reviewed checkpoint cannot be reconstructed. Preserve archives; do not infer closure or approval from recovery.'}
    return queue,report,files

def archive_manifest(folder,run_id,root=ROOT):
    folder=inside(root,folder);queue=folder/'queue.json';check_queue(read(queue))
    paths=[queue,folder/'report.json',*([folder/'recovery.json'] if (folder/'recovery.json').is_file() else []),*sorted((folder/'history').glob('*.json'))]
    entries=[]
    for path in paths:
        inside(root,path)
        if not path.is_file():raise ValueError('complete queue/report archive required')
        json.loads(path.read_bytes());kind='queue' if path==queue else 'report' if path.name in ('report.json','recovery.json') else 'history'
        entries.append({'path':path.relative_to(root).as_posix(),'kind':kind,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
    manifest={'version':1,'queue_path':queue.relative_to(root).as_posix(),'source_run_id':run_id,'archived_on':date.today().isoformat(),
              'files':entries,'business_claim_approval':False,'note':'Technical checkpoint for continuity; no human business approval inferred.'}
    validate_manifest(manifest,root);return manifest

def main():
    p=argparse.ArgumentParser(description=__doc__);sub=p.add_subparsers(dest='mode',required=True)
    recovery=sub.add_parser('recover');recovery.add_argument('--manifest',type=Path,default=ROOT/'data/discovery/checkpoints.json');recovery.add_argument('--output',type=Path,required=True);recovery.add_argument('--lost-run-id')
    archive=sub.add_parser('manifest');archive.add_argument('--folder',type=Path,required=True);archive.add_argument('--run-id',type=int,required=True);archive.add_argument('--output',type=Path,required=True)
    a=p.parse_args()
    try:
        if a.mode=='recover':
            safe_output(a.output,[a.manifest]);
            if a.output.exists():raise ValueError('recovery output must be a fresh directory')
            q,r,files=recover(read(a.manifest),lost_run_id=a.lost_run_id);write(a.output/'queue.json',q);write(a.output/'recovery.json',r)
            for entry,body,_ in files.values():
                folder=a.output/'history';folder.mkdir(exist_ok=True);(folder/(hashlib.sha256(body).hexdigest()+'.json')).write_bytes(body)
            print(json.dumps(r));return 0
        manifest=archive_manifest(a.folder,a.run_id)
        if a.folder.resolve() in a.output.resolve().parents:raise ValueError('manifest must be outside the archived files')
        safe_output(a.output,[a.folder]);write(a.output,manifest);return 0
    except (OSError,ValueError,KeyError,TypeError) as exc:print(f'Checkpoint operation blocked: {exc}');return 1
if __name__=='__main__':raise SystemExit(main())
