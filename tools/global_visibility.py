#!/usr/bin/env python3
"""Audit every company-only record; add a separate sourced display reference.

No original record, coordinate, evidence class, capability or approval is changed.
"""
import argparse,csv,json,math,tempfile
from collections import Counter
from datetime import date
from pathlib import Path
from discovery import ROOT,read,write,digest
from launch_readiness import records
from bulk_catalog import compact,sha
from validate import url_valid
from nz_quality_gate import csv_safe
HOME=ROOT/'data/global-programme'
DISPOSITIONS={'company_identity_no_verified_location','source_supported_city_region','reviewed_city_reference','independently_supported_facility','identity_geography_conflict','historical_operation_review','insufficient_evidence'}

def build(rows,home=HOME):
    original={r['id']:r for r in rows};reviews=read(home/'inputs/location-reviews.json');byid={};references={}
    # The first saved review input predates an explicit version field.
    if reviews.get('version',1)!=1 or date.fromisoformat(reviews['reviewed_on']).isoformat()!=reviews['reviewed_on'] or reviews['reviewed_on']>date.today().isoformat():raise ValueError('Invalid actual geographic review date')
    for review in reviews['records']:
        if review['record_id'] in byid:raise ValueError('Duplicate geographic review identity')
        row=original.get(review['record_id'])
        if not row or review['human_approved'] is not False or review['facility_capabilities_verified'] is not False or row['name']!=review['name'] or row['record_kind']!=review['record_kind'] or row['country']!=review['country'] or row['city']!=review['city']:raise ValueError('Identity, geography or verification conflict in location review')
        if not url_valid(review['company_evidence']) or not url_valid(review['service_evidence']):raise ValueError('Unsafe company evidence')
        if review['reference']:
            ref=review['reference']
            if row['record_kind']!='company_reference' or row['evidence_class']!='C' or row['lat'] is not None or row['lng'] is not None or ref['precision'] not in ('city','region') or ref['city']!=row['city'] or ref['country']!=row['country']:raise ValueError('Reference cannot move a source point or become a verified facility')
            if any(type(ref[k]) not in (float,int) or not math.isfinite(ref[k]) for k in ('lat','lng')) or abs(ref['lat'])>90 or abs(ref['lng'])>180 or ref['coordinate_license']!='CC-BY-4.0' or not url_valid(ref['coordinate_source']) or not url_valid(ref['license_url']):raise ValueError('Invalid licensed reference coordinate')
            references[row['id']]={**ref,'company_evidence':review['company_evidence'],'observed_on':reviews['reviewed_on'],'evidence_class':'C','facility_verified':False,'human_approved':False}
        byid[row['id']]=review
    audit=[]
    for row in rows:
        if row['record_kind']!='company_reference':continue
        if row['lat'] is not None or row['lng'] is not None:raise ValueError('Company-only baseline unexpectedly has coordinates')
        status='insufficient_evidence';reason='Company identity or geographic source evidence remains insufficient.'
        if row.get('source_provenance') and row.get('country'):status='company_identity_no_verified_location';reason='Source-associated company identity/country; no verified physical branch or coordinate.'
        if row.get('city') and row.get('evidence'):status='source_supported_city_region';reason='Recorded city/region association and evidence retained; no automatic geocode or independent facility verification.'
        if row.get('source_status') in ('Closed','Acquired','permanently_closed','temporarily_closed'):status='historical_operation_review';reason='Recorded historical/status assertion requires review; acquisition is not closure and a failed source cannot delete a company.'
        if row.get('potential_duplicates'):status='identity_geography_conflict';reason='Name/domain/identity candidates require review before assigning a physical location. No foreign address is inherited.'
        if row['id'] in references:status='reviewed_city_reference';reason=references[row['id']]['explanation']
        audit.append({'record_id':row['id'],'company_id':row['company_id'],'name':row['name'],'country':row['country'],'city':row['city'],'disposition':status,'reason':reason,'original_record_sha256':digest(row),'evidence':row.get('evidence',''),'source_observed_on':row.get('source_observed_on',''),'license':row.get('license','UNSPECIFIED'),'human_approved':False,'facility_verified':False})
    counts=dict(sorted(Counter(r['disposition'] for r in audit).items()))
    if any(s not in DISPOSITIONS for s in counts):raise ValueError('Unknown geographic disposition')
    public={'version':1,'company_audit':{r['record_id']:r['disposition'] for r in audit},'references':references,'golden_reviews':byid,'summary':{'company_only_records':len(audit),'original_unpinned_records':len(audit),'reviewed_display_references':len(references),'still_without_display_reference':len(audit)-len(references),'geographic_dispositions':counts,'independently_reviewed_new_facilities':0,'new_verified_capabilities':0,'original_record_coordinates_changed':0,'human_approved':False}}
    return public,audit

def install(public,database,home=HOME):
    public=Path(public);m,rows=records(public,database);value,audit=build(rows,home)
    compact(public/'visibility.json',value);m['global_visibility']={'path':'visibility.json','sha256':sha(public/'visibility.json'),'gzip_sha256':sha(public/'visibility.json.gz'),'gzip_bytes':(public/'visibility.json.gz').stat().st_size,'content_addressed':True};write(public/'manifest.json',m)
    return value,audit

def save(value,audit,out):
    out=Path(out);write(out/'unpinned-companies.json',audit);write(out/'visibility-summary.json',value['summary'])
    with (out/'unpinned-companies.csv').open('w',newline='',encoding='utf-8') as f:
        fields=['record_id','name','country','city','disposition','reason','evidence','source_observed_on','license'];w=csv.DictWriter(f,fieldnames=fields,lineterminator='\n');w.writeheader()
        for row in audit:w.writerow({k:csv_safe(row[k]) for k in fields})

def check(home=HOME):
    baseline=read(home/'inputs/baseline.json');m,rows=records(ROOT/'data/public',ROOT/'studios.json')
    if digest(sorted(r['id'] for r in rows))!=baseline['baseline_ids_sha256'] or digest({r['id']:digest(r) for r in rows})!=baseline['baseline_record_hashes_sha256']:raise ValueError('Original catalogue record changed')
    for name,h in baseline['original_public_files'].items():
        if name!='manifest.json' and sha(ROOT/'data/public'/name)!=h:raise ValueError('Historical public file changed: '+name)
    original_manifest=read(home/'inputs/parent-manifest.json')
    if {k:v for k,v in m.items() if k not in ('global_visibility','commercial_scope')}!=original_manifest:raise ValueError('Parent manifest metadata changed beyond the display/scope sidecars')
    if sha(ROOT/'studios.json')!=baseline['root_sha256'] or m['counts']!=baseline['counts']:raise ValueError('Original root/counts changed')
    value,audit=build(rows,home)
    descriptor=m.get('global_visibility',{})
    if descriptor.get('path')!='visibility.json' or descriptor.get('sha256')!=sha(ROOT/'data/public/visibility.json') or descriptor.get('gzip_sha256')!=sha(ROOT/'data/public/visibility.json.gz') or descriptor.get('gzip_bytes')!=(ROOT/'data/public/visibility.json.gz').stat().st_size:raise ValueError('Display projection transport integrity mismatch')
    if value!=read(ROOT/'data/public/visibility.json') or read(home/'reports/unpinned-companies.json')!=audit:raise ValueError('Stale visibility projection/audit')
    return value

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('command',choices=('prepare','check'));a=p.parse_args()
    if a.command=='prepare':value,audit=install(ROOT/'data/public',ROOT/'studios.json');save(value,audit,HOME/'reports')
    else:value=check()
    print(json.dumps(value['summary'],indent=2))
if __name__=='__main__':main()
