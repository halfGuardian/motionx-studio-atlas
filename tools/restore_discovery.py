#!/usr/bin/env python3
"""Try recent main-branch discovery artifacts, then an explicitly partial hashed checkpoint."""
import argparse,json,subprocess,tempfile,shutil,hashlib,os
from pathlib import Path
from checkpoints import check_queue,recover,MAX_FILE,MAX_TOTAL
from discovery import ROOT,read,write

def restore(output,runner=subprocess.run,manifest=None,include_failed=False):
    if output.exists():raise ValueError('restore output must be fresh')
    args=['gh','run','list','--workflow','discovery.yml','--branch','main']
    if not include_failed:args+=['--status','success']
    response=runner(args+['--limit','20','--json','databaseId'],capture_output=True,text=True,check=True)
    runs=json.loads(response.stdout)
    if not isinstance(runs,list):raise ValueError('invalid Actions run response')
    attempts=[]
    for run in runs[:20]:
        rid=run.get('databaseId')
        if type(rid) is not int or rid<=0:raise ValueError('invalid discovery run ID')
        if include_failed:
            repository=os.environ.get('GITHUB_REPOSITORY','halfGuardian/motionx-studio-atlas')
            metadata=runner(['gh','api',f'repos/{repository}/actions/runs/{rid}'],capture_output=True,text=True,check=True)
            m=json.loads(metadata.stdout)
            if m.get('head_branch')!='main' or m.get('path')!='.github/workflows/discovery.yml' or m.get('status')!='completed' or m.get('head_repository',{}).get('full_name')!=repository:continue
        with tempfile.TemporaryDirectory() as temp:
            attempt=Path(temp)/'download'
            r=runner(['gh','run','download',str(rid),'--name','studio-discovery','--dir',str(attempt)],capture_output=True,text=True)
            if r.returncode==0:
                try:
                    total=0;count=0
                    for p in attempt.rglob('*'):
                        count+=1
                        if count>10000 or p.is_symlink():raise ValueError('artifact path limit or symlink')
                        if not p.is_file():continue
                        relative=p.relative_to(attempt)
                        if relative.as_posix() not in ('queue.json','report.json','recovery.json') and not (len(relative.parts)==2 and relative.parts[0]=='history' and p.suffix=='.json'):
                            raise ValueError('unexpected discovery artifact file')
                        size=p.stat().st_size;total+=size
                        if size>MAX_FILE or total>MAX_TOTAL:raise ValueError('discovery artifact exceeds size limit')
                    check_queue(read(attempt/'queue.json'));report=read(attempt/'report.json')
                    if not isinstance(report.get('sources'),list):raise ValueError('invalid source report')
                    prior=read(attempt/'recovery.json') if (attempt/'recovery.json').exists() else {}
                    partial=bool(attempts) or prior.get('continuity_version')!=2 or prior.get('history_complete') is not True or prior.get('suppress_absence_signals') is not False
                    shutil.copytree(attempt,output)
                    if (attempt/'recovery.json').exists():
                        body=(attempt/'recovery.json').read_bytes();history=output/'history';history.mkdir(exist_ok=True);(history/(hashlib.sha256(body).hexdigest()+'.json')).write_bytes(body)
                    write(output/'recovery.json',{'mode':'restored_actions_artifact','continuity_version':2,'run_id':rid,'attempted_run_ids':attempts+[rid],
                        'history_complete':not partial,'suppress_absence_signals':partial,'warning':'An artifact gap or inherited partial history remains; no complete recovery or absence inference is claimed.' if partial else '', 'published_records':0})
                    return
                except (OSError,ValueError,KeyError,TypeError):pass
            attempts.append(rid)
    q,report,files=recover(manifest or read(ROOT/'data/discovery/checkpoints.json'),lost_run_id=attempts[0] if attempts else None)
    report['attempted_run_ids']=attempts;write(output/'queue.json',q);write(output/'recovery.json',report)
    for entry,body,_ in files.values():
        target=output/'history';target.mkdir(exist_ok=True);(target/(hashlib.sha256(body).hexdigest()+'.json')).write_bytes(body)

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);p.add_argument('--include-failed',action='store_true');a=p.parse_args()
    try:restore(a.output,include_failed=a.include_failed);print(json.dumps(read(a.output/'recovery.json')));return 0
    except (OSError,ValueError,KeyError,TypeError,subprocess.CalledProcessError) as exc:print('Discovery restore blocked: '+type(exc).__name__);return 1
if __name__=='__main__':raise SystemExit(main())
