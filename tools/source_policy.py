#!/usr/bin/env python3
"""Inspect explicitly configured public policy URLs, never studio pages or recursive links."""
import argparse
from datetime import date
import hashlib
import json
from pathlib import Path
import re
from urllib import error, robotparser

from discovery import Fetcher, USER_AGENT, public_url, read, safe_output, write

RESTRICTIONS = re.compile(r'\b(scrap\w*|crawl\w*|robots?|automat\w*|data.mining|text.and.data|artificial.intelligence|generative.ai)\b', re.I)


def audit(config, fetcher=None):
    fetcher = fetcher or Fetcher()
    output=[]
    for source in config['sources']:
        if source.get('access_review',{}).get('decision')=='automated_collection_disabled':
            output.append({'id':source['id'],'decision':'previously_prohibited_not_fetched','source_fetched':False});continue
        host=public_url(source['url'])
        result={'id':source['id'],'source_url':source['url'],'reviewed_on':date.today().isoformat(),
                'robots_url':f'https://{host}/robots.txt','terms':[], 'source_fetched':False,
                'decision':'manual_review_required'}
        robot=robotparser.RobotFileParser(result['robots_url'])
        try:
            body,_,encoding=fetcher.response(result['robots_url'],host)
            robot.parse(body.decode(encoding,errors='replace').splitlines())
            result['robots_sha256']=hashlib.sha256(body).hexdigest()
            result['robots_allows_collector']=robot.can_fetch(USER_AGENT,source['url'])
        except error.HTTPError as exc:
            result['robots_allows_collector']=exc.code==404
            result['robots_status']=exc.code
        except (OSError,ValueError,LookupError) as exc:
            result['robots_allows_collector']=False
            result['robots_error']=type(exc).__name__
        if not result['robots_allows_collector']:
            result['decision']='blocked_or_unavailable_robots'
            output.append(result);continue
        for url in source.get('policy_urls',[]):
            policy={'url':url}
            try:
                if public_url(url)!=host or not robot.can_fetch(USER_AGENT,url):
                    raise ValueError('policy URL not fetchable on this origin')
                delay=max(1,robot.crawl_delay(USER_AGENT) or 0)
                rate=robot.request_rate(USER_AGENT)
                if rate:delay=max(delay,rate.seconds/rate.requests)
                if delay>60:raise ValueError('policy requires slower/manual review')
                body,_,encoding=fetcher.response(url,host,delay)
                text=body.decode(encoding,errors='replace')
                # Keywords are review leads, never an automatic permission/ban decision.
                visible=re.sub('<[^>]+>',' ',text)
                policy.update(status='fetched',sha256=hashlib.sha256(body).hexdigest(),
                              review_keywords=sorted({m.group(0).lower() for m in RESTRICTIONS.finditer(visible)}))
            except (OSError,ValueError,LookupError) as exc:
                policy.update(status='unavailable',error_type=type(exc).__name__)
            result['terms'].append(policy)
        # No code path grants approval just because a keyword wasn't found.
        output.append(result)
    return {'reviewed_on':date.today().isoformat(),'sources':output,'auto_enabled':0,'studio_pages_fetched':0}


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--config',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();safe_output(a.output,[a.config]);result=audit(read(a.config));write(a.output,result)
    for source in result['sources']:print('SOURCE_POLICY '+json.dumps(source))


if __name__=='__main__':main()
