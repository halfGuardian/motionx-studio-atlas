#!/usr/bin/env python3
"""Try recent main-branch discovery artifacts, then an explicitly partial hashed checkpoint."""
import argparse,json,subprocess,tempfile,shutil
from pathlib import Path
from checkpoints import check_queue,recover
from discovery import ROOT,read,write

def restore(output,runner=subprocess.run,manifest=None):
    if output.exists():raise ValueError('restore output must be fresh')
    response=runner(['gh','run','list','--workflow','discovery.yml','--branch','main','--status','success','--limit','20','--json','databaseId'],capture_output=True,text=True,check=True)
    runs=json.loads(response.stdout)
    if not isinstance(runs,list):raise ValueError('invalid Actions run response')
    attempts=[]
    for run in runs[:20]:
        rid=run.get('databaseId')
        if type(rid) is not int or rid<=0:raise ValueError('invalid discovery run ID')
        with tempfile.TemporaryDirectory() as temp:
            attempt=Path(temp)/'download'
            r=runner(['gh','run','download',str(rid),'--name','studio-discovery','--dir',str(attempt)],capture_output=True,text=True)
            if r.returncode==0:
                try:
                    for p in attempt.rglob('*'):
                        if p.is_symlink():raise ValueError('artifact symlinks are not allowed')
                    check_queue(read(attempt/'queue.json'));report=read(attempt/'report.json')
                    if not isinstance(report.get('sources'),list):raise ValueError('invalid source report')
                    shutil.copytree(attempt,output)
                    write(output/'recovery.json',{'mode':'restored_actions_artifact','run_id':rid,'attempted_run_ids':attempts+[rid],
                        'history_complete':not attempts,'suppress_absence_signals':bool(attempts),'warning':'A later artifact was unavailable; later observations may need archive recovery.' if attempts else '', 'published_records':0})
                    return
                except (OSError,ValueError,KeyError,TypeError):pass
            attempts.append(rid)
    q,report,files=recover(manifest or read(ROOT/'data/discovery/checkpoints.json'),lost_run_id=attempts[0] if attempts else None)
    report['attempted_run_ids']=attempts;write(output/'queue.json',q);write(output/'recovery.json',report)
    for entry,body,_ in files.values():
        import hashlib
        target=output/'history';target.mkdir(exist_ok=True);(target/(hashlib.sha256(body).hexdigest()+'.json')).write_bytes(body)

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    try:restore(a.output);print(json.dumps(read(a.output/'recovery.json')));return 0
    except (OSError,ValueError,KeyError,TypeError,subprocess.CalledProcessError) as exc:print('Discovery restore blocked: '+type(exc).__name__);return 1
if __name__=='__main__':raise SystemExit(main())
