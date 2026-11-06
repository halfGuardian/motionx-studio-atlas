#!/usr/bin/env python3
"""Read complete relevant category slices from Overture's documented public Places release.

Optional acquisition dependency: duckdb==1.4.3. The ingestion/ledger tools remain
standard-library only. Column projection excludes phones, emails, people and street
addresses. The Places theme has no OSM data; do not use other Overture themes here.
"""
import argparse,hashlib,json,re,time,socket,ipaddress
from datetime import date
from pathlib import Path
from urllib import request,parse
import xml.etree.ElementTree as ET
from discovery import read,write,digest
from bulk_snapshot import safe_website
from bulk_collect import SameOrigin

BUCKET='https://overturemaps-us-west-2.s3.amazonaws.com'
RELEASE='2026-10-21.0'
CANDIDATE_PATTERN=r'(film|movie|video|television).*(produc|studio)|animat|visual_effect|game_develop|game_studio|motion_capture|performance_capture|virtual_production|post_produc|sound_stage|cinematic'

def metadata(url):
    parts=parse.urlsplit(url)
    if parts.scheme!='https' or parts.hostname!='overturemaps-us-west-2.s3.amazonaws.com' or parts.username or parts.password or parts.port not in (None,443):raise ValueError('unapproved dataset origin')
    answers=socket.getaddrinfo(parts.hostname,443,type=socket.SOCK_STREAM)
    if not answers or any(not ipaddress.ip_address(a[4][0]).is_global for a in answers):raise ValueError('nonpublic dataset DNS')
    req=request.Request(url,headers={'User-Agent':'MotionXBulkResearch/1.1 (https://github.com/halfGuardian/motionx-studio-atlas)','Accept':'application/xml,application/json'})
    with request.build_opener(SameOrigin(parts.hostname)).open(req,timeout=60) as r:
        body=r.read(8_000_001)
        if len(body)>8_000_000:raise ValueError('listing metadata exceeds limit')
        return body

def run(output,release=RELEASE):
    import duckdb
    if not re.fullmatch(r'20\d\d-\d\d-\d\d\.\d+',release):raise ValueError('invalid release identity')
    output=Path(output);folder=output/'overture';folder.mkdir(parents=True,exist_ok=True)
    previous=output/'overture-collection.json'
    if previous.exists():
        cached=read(previous)
        if cached.get('complete') and cached.get('release')==release:
            pages=sorted(folder.glob('places-*.meta.json'));count=0
            for meta_path in pages:
                meta=read(meta_path);values=read(meta_path.with_name(meta_path.name.replace('.meta.json','.json')))
                if meta.get('query_pattern')!=CANDIDATE_PATTERN or meta.get('release')!=release or digest(values)!=meta.get('projection_hash'):raise ValueError('cached snapshot integrity/query conflict')
                count+=len(values)
            if len(pages)!=cached.get('pages') or count!=cached.get('raw_source_records'):raise ValueError('cached snapshot incomplete')
            print('OVERTURE_COLLECTION '+json.dumps({**cached,'cache_reused':True,'freshness_note':'Immutable release snapshot reused; observation dates NOT advanced.'}),flush=True)
            return cached
    report={'id':'overture','adapter':'documented_public_geoparquet','release':release,'observed_on':date.today().isoformat(),'complete':False,'errors':[], 'permission_basis':'Explicit official downloadable Places release under per-provider CDLA-Permissive-2.0 / Apache-2.0 / CC0 licences. No website crawling. OSM/WD API restrictions are not changed or bypassed.','policy_urls':['https://docs.overturemaps.org/getting-data/','https://docs.overturemaps.org/guides/places/','https://docs.overturemaps.org/attribution/'],'published_records':0}
    start=time.monotonic()
    try:
        listing=metadata(BUCKET+'/?'+parse.urlencode({'list-type':2,'prefix':f'release/{release}/theme=places/type=place/'}))
        root=ET.fromstring(listing)
        if root.findtext('{*}IsTruncated')=='true':raise ValueError('object list truncated; require complete pagination before extraction')
        keys=[e.text for e in root.findall('.//{*}Key') if e.text.endswith('.parquet')]
        if not keys:raise ValueError('documented release has no accessible Places parquet objects')
        report['listing_sha256']=hashlib.sha256(listing).hexdigest();report['objects']=keys
        write(output/'overture-collection.json',report)
        print('OVERTURE_PHASE '+json.dumps({'phase':'object_listing','objects':len(keys),'elapsed_seconds':round(time.monotonic()-start,3)}),flush=True)
        con=duckdb.connect();con.execute("SET memory_limit='1500MB'; SET threads=2; SET temp_directory='/tmp/motionx-duckdb';")
        con.execute('INSTALL httpfs; LOAD httpfs;')
        # DuckDB uses SECONDS (not milliseconds). Bound individual network calls.
        con.execute("SET s3_region='us-west-2'; SET http_timeout=120; SET http_retries=2;")
        print('OVERTURE_PHASE '+json.dumps({'phase':'httpfs_ready','elapsed_seconds':round(time.monotonic()-start,3)}),flush=True)
        uris=[BUCKET+'/'+k for k in keys]
        relation='read_parquet('+repr(uris)+',union_by_name=true,filename=true,hive_partitioning=true)'
        description=con.execute('DESCRIBE SELECT * FROM '+relation).fetchall();report['columns']=[r[0] for r in description]
        print('OVERTURE_PHASE '+json.dumps({'phase':'schema','columns':report['columns'],'elapsed_seconds':round(time.monotonic()-start,3)}),flush=True)
        write(folder/'schema.json',description)
        if 'taxonomy' in report['columns']:cat='taxonomy.primary'
        elif 'categories' in report['columns']:cat='categories.primary'
        else:raise ValueError('unrecognised category schema; requires adapter review')
        rows=con.execute('SELECT '+cat+' AS category,count(*) AS count FROM '+relation+' GROUP BY 1 ORDER BY 1').fetchall()
        inventory=[{'category':c,'count':n,'selected_for_research':bool(c and re.search(CANDIDATE_PATTERN,c,re.I))} for c,n in rows]
        write(folder/'category-inventory.json',inventory);report['global_places_scanned']=sum(r['count'] for r in inventory);report['selected_categories']=[r for r in inventory if r['selected_for_research']]
        print('OVERTURE_CATEGORY_INVENTORY '+json.dumps(report['selected_categories']),flush=True)
        write(output/'overture-collection.json',report)
        # All qualifying category rows, all countries. No arbitrary LIMIT.
        select=f'''SELECT id AS source_record_id,names.primary AS name,{cat} AS category,
          bbox.xmin AS lng,bbox.ymin AS lat,bbox.xmax AS xmax,bbox.ymax AS ymax,
          hex(geometry) AS geometry_wkb,websites,addresses,sources,confidence,operating_status,filename
          FROM {relation} WHERE regexp_matches({cat},?)'''
        cursor=con.execute(select,[CANDIDATE_PATTERN]);columns=[r[0] for r in cursor.description]
        count=0;page=0
        while True:
            values=cursor.fetchmany(2000)
            if not values:break
            cleaned=[]
            for values_row in values:
                r=dict(zip(columns,values_row));r['websites']=[u for u in r.get('websites') or [] if safe_website(u)];r['addresses']=[{k:a.get(k) for k in ('locality','region','country')} for a in r.get('addresses') or []]
                r['sources']=[{k:s.get(k) for k in ('property','dataset','record_id','update_time','confidence')} for s in r.get('sources') or []]
                cleaned.append(r)
            key=f'places-{page:05d}';path=folder/(key+'.json');meta=folder/(key+'.meta.json')
            if path.exists() and read(path)!=cleaned:raise ValueError('immutable snapshot conflict; use a new release/run directory')
            write(path,cleaned);write(meta,{'source':'overture','release':release,'observed_on':report['observed_on'],'license':'per-provider','row_count':len(cleaned),'projection_hash':digest(cleaned),'query_pattern':CANDIDATE_PATTERN,'source_objects':keys})
            count+=len(cleaned);page+=1
            print('OVERTURE_PROGRESS '+json.dumps({'source_records':count,'pages':page,'projection_hash':digest(cleaned),'elapsed_seconds':round(time.monotonic()-start,3)}),flush=True)
        report.update(complete=True,raw_source_records=count,pages=page)
        con.close()
    except Exception as e:
        report['errors'].append({'type':type(e).__name__,'reason':str(e)[:1000]})
    report['elapsed_seconds']=round(time.monotonic()-start,3);write(output/'overture-collection.json',report);print('OVERTURE_COLLECTION '+json.dumps(report),flush=True)
    return report

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);p.add_argument('--release',default=RELEASE);a=p.parse_args();run(a.output,a.release)
if __name__=='__main__':main()
