#!/usr/bin/env python3
"""Project a permitted CSV/JSON/JSONL dataset into an immutable bulk snapshot.

Requires an enabled, reviewed licensed_batch source in the registry. Unknown
columns (including contacts, approval and verification flags) are rejected.
This tool never modifies studios.json or approves any record.
"""
import argparse,csv,json,re
from datetime import date
from pathlib import Path
from bulk_ingest import source_policy
from discovery import ROOT,read,write,digest
from validate import url_valid

FIELDS={'source_record_id','name','city','country','lat','lng','website','sectors','source_url','source_updated_on','parent_claims'}

def rows(path):
    if path.suffix.lower()=='.csv':
        with path.open(encoding='utf-8-sig',newline='') as f:
            reader=csv.DictReader(f)
            if not reader.fieldnames or len(reader.fieldnames)!=len(set(reader.fieldnames)):raise ValueError('unique headings required')
            for row in reader:yield row
    elif path.suffix.lower() in ('.jsonl','.ndjson'):
        with path.open(encoding='utf-8') as f:
            for line in f:
                if len(line)>100_000:raise ValueError('oversized source record')
                if line.strip():yield json.loads(line)
    else:
        value=read(path)
        if not isinstance(value,list):raise ValueError('JSON array required')
        yield from value

def project(row):
    if not isinstance(row,dict) or set(row)-FIELDS:raise ValueError('unsupported/private columns; supply the documented public projection')
    if not isinstance(row.get('source_record_id'),str) or not row['source_record_id'].strip():raise ValueError('stable source_record_id required')
    if len(row['source_record_id'])>256 or not re.fullmatch(r'[A-Za-z0-9_.:/#-]+',row['source_record_id']):raise ValueError('public business/source identifier required, not contacts or query credentials')
    clean=dict(row)
    for k,v in clean.items():
        if isinstance(v,str) and (len(v)>2000 or any(ord(c)<32 for c in v)):raise ValueError('unsafe/oversized text field')
    for field in ('lat','lng'):
        try:clean[field]=float(row[field])
        except (ValueError,KeyError,TypeError):clean[field]=None
    sectors=clean.get('sectors',[])
    if isinstance(sectors,str):sectors=[v.strip() for v in sectors.split('|') if v.strip()]
    if not isinstance(sectors,list) or any(not isinstance(v,str) for v in sectors):raise ValueError('invalid sectors')
    clean['sectors']=sectors
    if not isinstance(clean.get('name',''),str):raise ValueError('name must be text')
    for field in ('website','source_url'):
        if clean.get(field) and not url_valid(clean[field]):raise ValueError('invalid/unsafe public URL field')
    if clean.get('source_updated_on'):
        try:
            if date.fromisoformat(clean['source_updated_on']).isoformat()!=clean['source_updated_on']:raise ValueError()
        except (TypeError,ValueError):raise ValueError('invalid source update date')
    parents=clean.get('parent_claims',[])
    if isinstance(parents,str):parents=json.loads(parents or '[]')
    if not isinstance(parents,list) or len(parents)>20:raise ValueError('invalid parent claims')
    for p in parents:
        if not isinstance(p,dict) or set(p)-{'name','source_url'} or not isinstance(p.get('name'),str):raise ValueError('parent claims require public name/source only')
        if not url_valid(p.get('source_url')):raise ValueError('unsafe parent-claim URL')
    clean['parent_claims']=parents
    return clean

def prepare(path,output,source,config,observed):
    date.fromisoformat(observed)
    if observed>date.today().isoformat():raise ValueError('observation date cannot be in the future')
    policy=source_policy(config).get(source)
    if not policy or policy['adapter']!='licensed_batch':raise ValueError('enabled, reviewed licensed_batch source required')
    if output.exists():raise ValueError('fresh snapshot directory required')
    folder=output/source;folder.mkdir(parents=True)
    page=[];count=0;rejected=[];version_hashes={};pages=[]
    def flush():
        key=f'batch-{len(pages):05d}';write(folder/(key+'.json'),page)
        meta={'source':source,'license':policy['license'],'observed_on':observed,'projection_hash':digest(page),'row_count':len(page)}
        write(folder/(key+'.meta.json'),meta);pages.append(meta)
    for number,row in enumerate(rows(path),1):
        try:
            clean=project(row);key=clean['source_record_id'];h=digest(clean)
            if key in version_hashes and version_hashes[key]!=h:raise ValueError('conflicting records share a source identity')
            version_hashes[key]=h;page.append(clean);count+=1
            if len(page)==2000:flush();page=[]
        except (ValueError,TypeError) as exc:rejected.append({'row':number,'reason':str(exc)})
    if page:flush()
    import hashlib
    h=hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda:stream.read(1_048_576),b''):h.update(chunk)
    input_hash=h.hexdigest()
    report={'source':source,'observed_on':observed,'raw_source_records':count+len(rejected),'accepted_observations':count,'rejected':rejected,'pages':pages,'input_sha256':input_hash,'complete':True,'publication_approved':False}
    write(output/'batch-report.json',report);return report

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('input',type=Path);p.add_argument('--output',type=Path,required=True);p.add_argument('--source',required=True);p.add_argument('--observed-on',required=True);p.add_argument('--config',type=Path,default=ROOT/'data/bulk/sources.json');a=p.parse_args()
    print(json.dumps(prepare(a.input,a.output,a.source,read(a.config),a.observed_on),indent=2))
if __name__=='__main__':main()
