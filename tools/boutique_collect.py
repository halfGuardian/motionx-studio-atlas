#!/usr/bin/env python3
"""Download one reviewed, author-offered animation dataset. No recursive crawl.

Writes only to a fresh research folder, never data/public or studios.json.
Network/robots failures are reports, never closure or removal signals.
"""
import argparse, hashlib, json, re
from datetime import date
from pathlib import Path
from urllib import error, robotparser
from discovery import Fetcher, ROOT, USER_AGENT, read, write

REPOSITORY='https://github.com/tlahitte/animation-studios-directory'

def styles(value):
    if isinstance(value,str):return [s.strip() for s in value.split(',') if s.strip()]
    if isinstance(value,list) and all(isinstance(s,str) for s in value):return value
    raise ValueError('invalid animation-style assertions')

def project(value,commit,observed):
    if not re.fullmatch('[a-f0-9]{40}',commit):raise ValueError('immutable commit required')
    rows=value['studios']
    if not isinstance(rows,list) or len(rows)>100000 or value['count']!=len(rows):raise ValueError('incomplete/oversized dataset')
    date.fromisoformat(value['generated']);date.fromisoformat(observed)
    url=f'{REPOSITORY}/blob/{commit}/site/data/studios.json'
    return {'source_id':'animstudios-github','source_version':commit,'license':'CC-BY-4.0','observed_on':observed,'complete':True,'records':[{'source_record_id':'row-'+str(n),'name':r['name'],'website':r['website'],'city':r.get('city',''),'country':r.get('country',''),'source_kind':r['type'],'size_claim':r.get('size','Unknown'),'animation_types':styles(r.get('animation_types','')),'source_url':url,'source_updated_on':value['generated'],'observed_on':observed} for n,r in enumerate(rows,1)]}

def collect(commit,output,registry=None,fetcher=None):
    if not re.fullmatch('[a-f0-9]{40}',commit):raise ValueError('immutable commit required')
    output=Path(output)
    if output.exists() or output.resolve().is_relative_to((ROOT/'data/public').resolve()):raise ValueError('fresh research output required')
    policy=next(s for s in (registry or read(ROOT/'data/boutique/sources.json'))['sources'] if s['id']=='animstudios-github')
    if not policy['automatic_collection'] or policy['license']!='CC-BY-4.0':raise ValueError('source policy does not permit collection')
    reviewed=re.search(r'/blob/([a-f0-9]{40})/site/data/studios\.json$',policy.get('source_url',''))
    if not reviewed or reviewed[1]!=commit:raise ValueError('unreviewed source revision; review licence/access and policy before collection')
    fetcher=fetcher or Fetcher();observed=date.today().isoformat();url=f'https://raw.githubusercontent.com/tlahitte/animation-studios-directory/{commit}/site/data/studios.json';host='raw.githubusercontent.com'
    report={'source_id':policy['id'],'commit':commit,'observed_on':observed,'complete':False,'published_records':0,'closure_signals':[],'history_policy':'Fresh immutable snapshots only; failures never delete prior observations.'}
    try:
        robot=robotparser.RobotFileParser('https://'+host+'/robots.txt')
        try:
            body,_,enc=fetcher.response(robot.url,host);robot.parse(body.decode(enc).splitlines())
            report['robots_sha256']=hashlib.sha256(body).hexdigest()
        except error.HTTPError as exc:
            if exc.code!=404:raise
            robot.parse([]);report['robots_status']=404
        if not robot.can_fetch(USER_AGENT,url):raise ValueError('robots disallows this download; no fallback')
        delay=max(1,robot.crawl_delay(USER_AGENT) or 0);rate=robot.request_rate(USER_AGENT)
        if rate:delay=max(delay,rate.seconds/rate.requests)
        if delay>60:raise ValueError('robots rate requires manual/slower review')
        body,kind,enc=fetcher.response(url,host,delay)
        if len(body)>2000000 or kind not in ('application/json','text/plain'):raise ValueError('dataset type/size limit')
        projected=project(json.loads(body.decode(enc)),commit,observed)
        write(output/'animstudios.json',projected)
        report.update(complete=True,raw_records=len(projected['records']),raw_sha256=hashlib.sha256(body).hexdigest(),projection_sha256=hashlib.sha256((output/'animstudios.json').read_bytes()).hexdigest(),source_url=projected['records'][0]['source_url'])
    except (OSError,ValueError,TypeError,KeyError) as exc:report['error']={'type':type(exc).__name__,'reason':str(exc)[:250]}
    write(output/'collection.json',report);return report

def query_plan(vocabulary):
    return [{'language':language,'query':term+' '+region,'status':'planned_not_executed','provider_requirement':'Permitted indexed search; never scrape search engines.'} for language,terms in vocabulary['languages'].items() for term in terms for region in vocabulary['regions']]

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('command',choices=('collect','queries'));p.add_argument('--commit');p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    if a.command=='queries':write(a.output,query_plan(read(ROOT/'data/boutique/vocabulary.json')))
    else:
        result=collect(a.commit or '',a.output);print(json.dumps(result,indent=2))
        if not result['complete']:raise SystemExit(1)
if __name__=='__main__':main()
