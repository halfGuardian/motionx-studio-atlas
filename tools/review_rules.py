#!/usr/bin/env python3
"""Read-only GitHub review-rule inventory. Never claims that bypasses are impossible."""
import argparse,json,re,subprocess
from pathlib import Path

def audit(repository,runner=subprocess.run):
    if not re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+',repository):raise ValueError('invalid repository')
    report={'repository':repository,'branch':'main','read_only':True,'enforcement_claim':'Not asserted: inspect required reviews, enforcement state and bypass actors before publication.','endpoints':{}}
    for name,path in [('classic_protection',f'repos/{repository}/branches/main/protection'),('effective_rules',f'repos/{repository}/rules/branches/main')]:
        try:
            r=runner(['gh','api',path],capture_output=True,text=True,timeout=30)
            if r.returncode:report['endpoints'][name]={'status':'unavailable','note':'API did not expose rules (for example permission, plan or no configured protection); human review enforcement is unconfirmed.'};continue
            if len(r.stdout)>1_000_000:raise ValueError('rule response exceeds limit')
            value=json.loads(r.stdout)
            if (name=='effective_rules' and not isinstance(value,list)) or (name=='classic_protection' and not isinstance(value,dict)):raise ValueError('invalid rule response')
            report['endpoints'][name]={'status':'read','rules':value}
        except (OSError,subprocess.TimeoutExpired,ValueError):report['endpoints'][name]={'status':'unavailable','note':'Rules audit failed; review enforcement remains unconfirmed.'}
    return report

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--repository',required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    if a.output.exists():p.error('choose a fresh report path')
    report=audit(a.repository);a.output.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report));return 0
if __name__=='__main__':raise SystemExit(main())
