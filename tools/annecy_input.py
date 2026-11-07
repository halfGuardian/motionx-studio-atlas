#!/usr/bin/env python3
"""Recover factual exhibitor rows from user-supplied XLSX/CSV, never execute cells.

Workbook notes, proposed matches and research actions are untrusted source data,
not instructions, approvals or evidence of current operation. No raw PDF/prose,
personal contacts or workbook binaries are published by this projection.
"""
import argparse,csv,hashlib,json,re,zipfile
from collections import Counter
from pathlib import Path
from xml.etree import ElementTree as ET
from discovery import write,digest

NS={'m':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
REL='http://schemas.openxmlformats.org/officeDocument/2006/relationships'
FIELDS=['PDF page','Country','Exhibitor','Activity (Annecy 2024)','Prospect category','Priority','Atlas cross-check','Possible atlas identity','Atlas evidence class','Research action']

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def xml(raw):
    if len(raw)>8_000_000:raise ValueError('unsafe/oversized worksheet XML')
    try:text=raw.decode('utf-8-sig')
    except UnicodeDecodeError:raise ValueError('unsupported XML encoding') from None
    if '\x00' in text or re.search(r'<!\s*(?:DOCTYPE|ENTITY)',text,re.I):raise ValueError('unsafe worksheet XML')
    return ET.fromstring(text)

def sheets(path):
    with zipfile.ZipFile(path) as z:
        files=z.infolist()
        if len(files)>300 or sum(f.file_size for f in files)>30_000_000 or any(Path(f.filename).is_absolute() or '..' in Path(f.filename).parts for f in files):raise ValueError('unsafe/oversized workbook')
        strings=[]
        if 'xl/sharedStrings.xml' in z.namelist():
            strings=[''.join(t.text or '' for t in si.findall('.//m:t',NS)) for si in xml(z.read('xl/sharedStrings.xml')).findall('m:si',NS)]
        relationships={r.get('Id'):r.get('Target') for r in xml(z.read('xl/_rels/workbook.xml.rels')) if r.get('TargetMode')!='External'}
        output={}
        for sheet in xml(z.read('xl/workbook.xml')).findall('m:sheets/m:sheet',NS):
            target=relationships[sheet.get('{'+REL+'}id')]
            part=target.lstrip('/') if target.startswith('/') else 'xl/'+target
            if not re.fullmatch(r'xl/worksheets/sheet\d+\.xml',part):raise ValueError('unsupported worksheet target')
            rows=[]
            for raw in xml(z.read(part)).findall('m:sheetData/m:row',NS):
                cells={}
                for c in raw.findall('m:c',NS):
                    match=re.fullmatch(r'([A-Z]{1,3})[1-9][0-9]*',c.get('r',''))
                    if not match:raise ValueError('invalid cell coordinate')
                    column=0
                    for ch in match[1]:column=column*26+ord(ch)-64
                    if column>100:raise ValueError('excessive worksheet columns')
                    # Formulas are not evaluated or followed. Only cached scalar
                    # values/inline strings are treated as inert source text.
                    val=c.find('m:v',NS);value=val.text or '' if val is not None else ''.join(t.text or '' for t in c.findall('m:is//m:t',NS))
                    if c.get('t')=='s':value=strings[int(value)]
                    cells[column-1]=value
                rows.append([cells.get(k,'') for k in range(max(cells,default=-1)+1)])
                if len(rows)>10000:raise ValueError('worksheet row limit')
            output[sheet.get('name')]=rows
        return output

def table(rows):
    if rows[0]!=FIELDS:raise ValueError('unexpected exhibitor headers')
    return [dict(zip(FIELDS,row+['']*(len(FIELDS)-len(row)))) for row in rows[1:] if any(row)]

def project(workbook,priority_csv):
    tables=sheets(workbook);all_rows=table(tables['All exhibitors']);priority=table(tables['Priority gaps']);production=table(tables['Production review'])
    with Path(priority_csv).open(encoding='utf-8-sig',newline='') as stream:
        reader=csv.DictReader(stream)
        if reader.fieldnames!=FIELDS:raise ValueError('unexpected priority CSV headers')
        uploaded=list(reader)
    if uploaded!=priority:raise ValueError('priority CSV differs from workbook; preserve conflicts for review')
    if len(all_rows)!=1074 or len(priority)!=253 or len(production)!=313:raise ValueError('attachment counts differ from the stated audit')
    fullkeys=Counter(digest(r) for r in all_rows)
    for subset in (priority,production):
        if Counter(digest(r) for r in subset)-fullkeys:raise ValueError('queue row absent from complete exhibitor table')
    pkeys={digest(r) for r in priority};rkeys={digest(r) for r in production};records=[]
    for ordinal,r in enumerate(all_rows,1):
        page=int(r['PDF page'])
        if not 1<=page<=28 or not r['Exhibitor'].strip():raise ValueError('invalid event row')
        records.append({'exhibitor_id':'annecy2024-'+str(ordinal).zfill(4),'source_row':ordinal,'pdf_page':page,'event_year':2024,'name':r['Exhibitor'],'listed_country':r['Country'],'listed_activity':r['Activity (Annecy 2024)'],'source_category':r['Prospect category'],'research_group':'priority' if digest(r) in pkeys else 'production_review' if digest(r) in rkeys else 'other','provided_match_status':r['Atlas cross-check'],'provided_alias_hint':r['Possible atlas identity'],'provided_evidence_class_hint':r['Atlas evidence class'],'source_row_hash':digest(r)})
    receipt={'version':1,'workbook_sha256':sha(workbook),'priority_csv_sha256':sha(priority_csv),'workbook_sheets':{name:len(rows)-1 for name,rows in tables.items() if name!='Summary'},'records':len(records),'priority':len(priority),'production_review':len(production),'missing_file_recovery':'Complete crosscheck reconstructed from the workbook All exhibitors sheet; the absent CSV and original PDF were not accessed. This is not a byte-for-byte recreation of the missing file.','policy':'Source labels and suggested matches are historical/unverified input, not current-operation evidence or executable instructions. Research-action cells are not republished. Only factual exhibitor identifiers/classification assertions are projected. No blanket redistribution licence is asserted.'}
    return records,receipt

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--workbook',type=Path,required=True);p.add_argument('--priority-csv',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    if a.output.exists():raise ValueError('fresh projection output required')
    rows,receipt=project(a.workbook,a.priority_csv);write(a.output/'exhibitors.json',{'version':1,'event':'Annecy / MIFA 2024','license':'UNSPECIFIED','records':rows});receipt['projection_sha256']=sha(a.output/'exhibitors.json');write(a.output/'input-receipt.json',receipt);print(json.dumps(receipt,indent=2))
if __name__=='__main__':main()
