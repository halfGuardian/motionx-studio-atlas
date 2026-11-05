#!/usr/bin/env python3
"""MotionX Studio Atlas offline research batch validator. Standard library only."""
import argparse,csv,json,re,sys,urllib.parse
from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path
REQUIRED=('id','company_id','name','city','country','lat','lng','website','evidence','evidence_state','coordinate_precision')
STATES={'confirmed','likely','unknown'}
PRECISIONS={'exact','approximate','city','region','unverified'}
def host(url):
    try:return urllib.parse.urlsplit(url).hostname or ''
    except ValueError:return ''
def validate(rows):
    errors=[]; warnings=[]; seen={}; names=defaultdict(list)
    for i,r in enumerate(rows,1):
        ref=r.get('id') or f'row-{i}'
        for k in REQUIRED:
            if r.get(k) in (None,''): errors.append(f'{ref}: missing {k}')
        if ref in seen: errors.append(f'{ref}: duplicate id (first row {seen[ref]})')
        seen[ref]=i
        try:
            lat=float(r['lat']);lon=float(r['lng'])
            if not (-90<=lat<=90 and -180<=lon<=180):errors.append(f'{ref}: coordinates outside bounds')
        except (KeyError,ValueError,TypeError):errors.append(f'{ref}: invalid coordinates')
        if r.get('evidence_state') not in STATES:errors.append(f'{ref}: evidence_state must be confirmed/likely/unknown')
        if r.get('coordinate_precision') not in PRECISIONS:errors.append(f'{ref}: invalid coordinate_precision')
        for field in ('website','evidence'):
            url=r.get(field,'')
            if url and (not url.startswith('https://') or not host(url)):errors.append(f'{ref}: {field} must be a valid https URL')
        if r.get('evidence_state')=='confirmed' and not r.get('evidence'):errors.append(f'{ref}: confirmed requires evidence URL')
        if r.get('verified_on'):
            try:
                d=date.fromisoformat(r['verified_on'])
                if d>date.today()+timedelta(days=1):warnings.append(f'{ref}: verification date is in future')
            except ValueError:errors.append(f'{ref}: invalid verified_on date')
        if r.get('coordinate_precision') in ('city','region','unverified') and r.get('address') and 'approximate' not in r['address'].lower() and 'unverified' not in r['address'].lower():warnings.append(f'{ref}: address is more precise than coordinate precision; review')
        if r.get('evidence_state')=='confirmed' and not r.get('verified_on'):warnings.append(f'{ref}: no verification date')
        names[(r.get('name','').casefold(),r.get('city','').casefold())].append(ref)
    for key,ids in names.items():
        if len(ids)>1:warnings.append(f'possible duplicate same name/city: {", ".join(ids)}')
    return errors,warnings

def main():
    p=argparse.ArgumentParser();p.add_argument('input',help='JSON array or CSV file');p.add_argument('--output',help='write validated JSON array');p.add_argument('--report',help='write JSON report');a=p.parse_args()
    src=Path(a.input)
    if src.suffix.lower()=='.csv':
        with src.open(encoding='utf-8-sig',newline='') as f:rows=list(csv.DictReader(f))
        for r in rows:
            for k in ('lat','lng'):
                if r.get(k):
                    try:r[k]=float(r[k])
                    except ValueError:pass
            for k in ('categories','capabilities'):
                r[k]=[x.strip() for x in r.get(k,'').split('|') if x.strip()]
    else:rows=json.loads(src.read_text(encoding='utf-8'))
    if not isinstance(rows,list):p.error('input must be an array')
    errors,warnings=validate(rows)
    report={'records':len(rows),'companies':len({r.get('company_id') for r in rows}),'errors':errors,'warnings':warnings,'accepted':not errors}
    print(json.dumps(report,indent=2,ensure_ascii=False))
    if a.report:Path(a.report).write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    if a.output and not errors:Path(a.output).write_text(json.dumps(rows,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    return 1 if errors else 0
if __name__=='__main__':sys.exit(main())
