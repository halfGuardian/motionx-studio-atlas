#!/usr/bin/env python3
"""Prepare a redistributable snapshot, withholding unresolved status overlays.

Full originals stay in the source Actions artifact and immutable dated release.
Their hashes are retained. Withheld data can never turn into an approved claim.
"""
import argparse,copy,shutil
from pathlib import Path
from discovery import read,write,digest
from validate import url_valid
from urllib.parse import urlsplit

SOCIAL_HOSTS={'facebook.com','instagram.com','linkedin.com','youtube.com','youtu.be','tiktok.com','twitter.com','x.com','vk.com'}

def safe_website(value):
    # Preserve a safe supplied HTTP string as research text; do not invent a
    # working HTTPS endpoint or display it as a verified official link.
    valid=url_valid(value) or isinstance(value,str) and value.startswith('http://') and url_valid('https://'+value[7:])
    return bool(valid and (urlsplit(value).hostname or '').removeprefix('www.') not in SOCIAL_HOSTS)

def project(source,destination):
    source=Path(source);destination=Path(destination)
    if destination.exists():raise ValueError('fresh projection directory required')
    destination.mkdir(parents=True);receipts=[];withheld=0
    for path in sorted(source.rglob('*.json')):
        relative=path.relative_to(source)
        if relative.parts[0]!='overture' or path.name.endswith('.meta.json') or not path.with_name(path.stem+'.meta.json').exists():
            if not path.name.endswith('.meta.json'):write(destination/relative,read(path))
            continue
        rows=read(path);meta=read(path.with_name(path.stem+'.meta.json'))
        if digest(rows)!=meta['projection_hash']:raise ValueError('original snapshot integrity mismatch')
        result=[]
        for row in rows:
            item=copy.deepcopy(row)
            item['websites']=[u for u in item.get('websites') or [] if safe_website(u)]
            overlays=[s for s in item.get('sources',[]) if s.get('dataset')=='Overture-signals']
            if overlays:
                if any(s.get('property')!='/properties/operating_status' for s in overlays):raise ValueError('unreviewed overlay property; cannot safely project')
                item['original_observation_hash']=digest(row);item['withheld_overlays']=['Overture-signals operating-status overlay; redistribution mapping unresolved']
                item['sources']=[s for s in item['sources'] if s not in overlays]
                item['operating_status']=None;withheld+=1
            if item!=row:item['original_observation_hash']=digest(row)
            result.append(item)
        write(destination/relative,result)
        write(destination/relative.with_name(path.stem+'.meta.json'),{**meta,'upstream_projection_hash':meta['projection_hash'],'projection_hash':digest(result),'transformation':'Unresolved Overture-signals status payloads withheld; original observation/page hashes preserved. Such candidates remain C.'})
        receipts.append({'path':str(relative),'upstream_projection_hash':meta['projection_hash'],'redistributable_projection_hash':digest(result),'records':len(result)})
    report={'version':1,'pages':receipts,'status_overlays_withheld':withheld,'publication_approved':False,'history_note':'Original source artifact retains full observations, including withheld overlays. This public projection preserves every source ID and the original hashes, but does not redistribute unresolved overlay content. Maintain an offline copy of the full Actions artifact before its expiry if needed for a complete original-payload archive.'}
    write(destination/'redistribution.json',report);return report

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('input',type=Path);p.add_argument('--output',type=Path,required=True);a=p.parse_args();print(project(a.input,a.output)['status_overlays_withheld'])
if __name__=='__main__':main()
