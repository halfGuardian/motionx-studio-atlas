#!/usr/bin/env python3
"""Collect explicitly licensed API metadata in resumable, hashed snapshots; never publish.

Only the registered API hosts are fetched. No recursive links, hidden endpoints,
contact harvesting, API-host failover or denial workarounds. All results are proposals.
"""
import argparse,hashlib,json,re,socket,ipaddress,time
from datetime import date,datetime,timezone
from pathlib import Path
from urllib import request,parse,error,robotparser
from discovery import digest,read,write

AGENT='MotionXBulkResearch/1.1 (https://github.com/halfGuardian/motionx-studio-atlas; public studio directory research)'
MAX_RESPONSE=32_000_000
class SameOrigin(request.HTTPRedirectHandler):
    def __init__(self,host):self.host=host
    def redirect_request(self,req,fp,code,msg,headers,url):
        u=parse.urlsplit(url)
        if u.scheme!='https' or u.hostname!=self.host or u.username or u.password or u.port not in (None,443):raise ValueError('cross-origin/unsafe redirect blocked')
        return super().redirect_request(req,fp,code,msg,headers,url)

class Client:
    def __init__(self):self.last=0
    def get(self,url,accept='application/json',max_bytes=MAX_RESPONSE):
        u=parse.urlsplit(url)
        if u.scheme!='https' or u.hostname not in ('query.wikidata.org','overpass-api.de') or u.username or u.password or u.port not in (None,443):raise ValueError('unregistered API origin')
        answers=socket.getaddrinfo(u.hostname,443,type=socket.SOCK_STREAM)
        if not answers or any(not ipaddress.ip_address(a[4][0]).is_global for a in answers):raise ValueError('nonpublic API DNS')
        time.sleep(max(0,3-(time.monotonic()-self.last)));self.last=time.monotonic()
        opener=request.build_opener(SameOrigin(u.hostname))
        req=request.Request(url,headers={'User-Agent':AGENT,'Accept':accept,'Accept-Encoding':'identity'})
        with opener.open(req,timeout=180) as r:
            body=r.read(max_bytes+1)
            if len(body)>max_bytes:raise ValueError('response limit; partition query or use an approved dump')
            return body,r.headers.get_content_type()
    def robots(self,url):
        p=parse.urlsplit(url);robots=f'https://{p.hostname}/robots.txt';robot=robotparser.RobotFileParser(robots)
        try:
            body,_=self.get(robots,'text/plain',1_000_000);robot.parse(body.decode('utf-8-sig',errors='replace').splitlines())
            return robot.can_fetch(AGENT,url),{'url':robots,'sha256':hashlib.sha256(body).hexdigest(),'allows':robot.can_fetch(AGENT,url)}
        except error.HTTPError as e:
            if e.code==404:return True,{'url':robots,'status':404,'allows':True,'note':'No robots file; explicit API documentation and data licence still required.'}
            raise

def query_wikidata(class_id,after='',limit=1000):
    # Page distinct entities before OPTIONAL joins, so one item never falls between pages.
    # Keyset cursor includes a complete entity URI; fixed Q IDs only.
    if not re.fullmatch(r'Q[1-9][0-9]*',class_id) or after and not re.fullmatch(r'Q[1-9][0-9]*',after):raise ValueError('invalid Wikidata cursor/class')
    cursor=f'FILTER(STR(?item)>"http://www.wikidata.org/entity/{after}")' if after else ''
    return f'''SELECT ?item ?itemLabel ?type ?website ?coord ?hq ?hqLabel ?hqCoord ?place ?placeLabel ?country ?countryLabel ?ended ?parent ?parentLabel WHERE {{
      {{ SELECT DISTINCT ?item WHERE {{ ?item wdt:P31/wdt:P279* wd:{class_id}. {cursor} }} ORDER BY STR(?item) LIMIT {int(limit)} }}
      OPTIONAL {{?item wdt:P31 ?type.}}
      OPTIONAL {{?item wdt:P856 ?website.}}
      OPTIONAL {{?item wdt:P625 ?coord.}}
      OPTIONAL {{?item wdt:P159 ?hq. OPTIONAL {{?hq wdt:P625 ?hqCoord.}}}}
      OPTIONAL {{?item wdt:P131 ?place.}}
      OPTIONAL {{?item wdt:P17 ?country.}}
      OPTIONAL {{?item wdt:P576 ?ended.}}
      OPTIONAL {{?item wdt:P749 ?parent.}}
      SERVICE wikibase:label {{bd:serviceParam wikibase:language "en,mul".}}
    }} ORDER BY STR(?item)'''

def clean_wikidata(bindings,sector):
    grouped={}
    for b in bindings:
        item=b.get('item',{}).get('value','');qid=item.rsplit('/',1)[-1]
        if not re.fullmatch(r'Q[1-9][0-9]*',qid):continue
        row=grouped.setdefault(qid,{'source_record_id':qid,'name':'','sectors':[sector],'types':[],'websites':[],'coordinates':[],'headquarters':[],'places':[],'countries':[],'ended':[],'parents':[]})
        value=lambda k:b.get(k,{}).get('value','')
        row['name']=value('itemLabel') or qid
        for field,key in [('types','type'),('websites','website'),('coordinates','coord'),('ended','ended')]:
            if value(key) and value(key) not in row[field]:row[field].append(value(key))
        for field,key,label,coord in [('headquarters','hq','hqLabel','hqCoord'),('places','place','placeLabel',None),('countries','country','countryLabel',None),('parents','parent','parentLabel',None)]:
            if value(key):
                item={'id':value(key).rsplit('/',1)[-1],'name':value(label)}
                if coord and value(coord):item['coordinate']=value(coord)
                if item not in row[field]:row[field].append(item)
    return list(grouped.values())

SAFE_TAGS={'name','name:en','brand','brand:wikidata','operator','operator:wikidata','wikidata','website','contact:website','addr:city','addr:country','addr:suburb','addr:postcode','man_made','studio','office','company','industrial','disused','abandoned','disused:man_made','disused:office','start_date','end_date','check_date','survey:date'}
def clean_osm(elements):
    return [{'source_record_id':str(e['type'])+'/'+str(e['id']),'tags':{k:v for k,v in e.get('tags',{}).items() if k in SAFE_TAGS},
             'lat':e.get('lat',e.get('center',{}).get('lat')),'lng':e.get('lon',e.get('center',{}).get('lon')),
             'version':e.get('version'),'timestamp':e.get('timestamp')} for e in elements if e.get('type') in ('node','way','relation') and type(e.get('id')) is int]

OVERPASS='''[out:json][timeout:120][maxsize:134217728];(
 nwr[man_made=studio];
 nwr[office~"^(film_production|video_games|game_development|animation|visual_effects|production_company)$"];
 nwr[studio~"^(animation|motion_capture|performance_capture|virtual_production|film|cinema|video|television)$"];
);out center meta;'''

def collect(config,output,client=None,page_size=1000,max_pages=None):
    client=client or Client();output=Path(output);output.mkdir(parents=True,exist_ok=True)
    report=read(output/'collection.json') if (output/'collection.json').exists() else {'version':1,'observed_on':date.today().isoformat(),'sources':[],'publication_approved':False,'published_records':0}
    for source in config['sources']:
        if not source.get('enabled') or source.get('adapter') not in ('wikidata_sparql','overpass'):continue
        status={'id':source['id'],'license':source['license'],'endpoint':source['endpoint'],'pages':[],'complete':False,'errors':[]}
        folder=output/source['id'];folder.mkdir(exist_ok=True)
        try:
            allowed,policy=client.robots(source['endpoint']);status['robots']=policy
            if not allowed:raise ValueError('robots disallows configured API endpoint; no fallback host')
            if source['adapter']=='wikidata_sparql':
                for class_id,sector in source['query_classes'].items():
                    after='';page=0
                    while True:
                        if max_pages and page>=max_pages:status['errors'].append({'class':class_id,'reason':'operator safety budget exhausted; resumable cursor retained; source incomplete'});break
                        key=f'{class_id}-{page:05d}';path=folder/(key+'.json');meta_path=folder/(key+'.meta.json')
                        query=query_wikidata(class_id,after,page_size)
                        if path.exists() and meta_path.exists():
                            meta=read(meta_path);rows=read(path)
                            if meta.get('query_hash')!=digest(query) or meta.get('projection_hash')!=digest(rows):raise ValueError('cache integrity/cursor conflict')
                        else:
                            url=source['endpoint']+'?'+parse.urlencode({'query':query,'format':'json'})
                            raw,_=client.get(url,'application/sparql-results+json');value=json.loads(raw)
                            rows=clean_wikidata(value['results']['bindings'],sector)
                            meta={'query_hash':digest(query),'query':query,'response_sha256':hashlib.sha256(raw).hexdigest(),'projection_hash':digest(rows),'observed_on':date.today().isoformat(),'source':source['id'],'class':class_id,'row_count':len(rows),'after':after,'license':source['license']}
                            write(path,rows);write(meta_path,meta)
                        status['pages'].append({'path':str(path),'count':len(rows),'hash':digest(rows),'class':class_id})
                        if not rows:break
                        cursor=max(r['source_record_id'] for r in rows)
                        if cursor<=after:raise ValueError('nonadvancing page cursor')
                        after=cursor;page+=1
                        if len(rows)<page_size:break
            elif source['adapter']=='overpass':
                path=folder/'studios.json';meta_path=folder/'studios.meta.json'
                if path.exists() and meta_path.exists():
                    rows=read(path);meta=read(meta_path)
                    if meta.get('projection_hash')!=digest(rows):raise ValueError('cache integrity conflict')
                else:
                    raw,_=client.get(source['endpoint']+'?'+parse.urlencode({'data':OVERPASS}));value=json.loads(raw)
                    if value.get('remark'):raise ValueError('Overpass partial/error response: '+value['remark'][:200])
                    rows=clean_osm(value['elements']);write(path,rows)
                    write(meta_path,{'query':OVERPASS,'response_sha256':hashlib.sha256(raw).hexdigest(),'projection_hash':digest(rows),'observed_on':date.today().isoformat(),'source':source['id'],'row_count':len(rows),'license':source['license']})
                status['pages'].append({'path':str(path),'count':len(rows),'hash':digest(rows)})
            else:raise ValueError('unknown adapter')
            status['complete']=not status['errors']
        except (OSError,ValueError,KeyError,TypeError) as e:
            status['errors'].append({'type':type(e).__name__,'reason':str(e)[:240]});status['complete']=False
        report['sources']=[r for r in report['sources'] if r['id']!=source['id']]+[status]
        write(output/'collection.json',report)
        print('BULK_SOURCE '+json.dumps(status),flush=True)
    return report

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--config',type=Path,default=Path('data/bulk/sources.json'));p.add_argument('--output',type=Path,required=True);p.add_argument('--max-pages',type=int);a=p.parse_args()
    collect(read(a.config),a.output,max_pages=a.max_pages)
if __name__=='__main__':main()
