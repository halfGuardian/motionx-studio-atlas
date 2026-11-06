"""Discovery is not verification: deterministic fixture/network/approval regressions."""
import copy
from datetime import date
import json
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from urllib import error, request

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from discovery import (CHECKS, Fetcher, NoUnsafeRedirect, digest, extract, load_config,
                       prepare, public_url, read, review_template, scan, seed_backlog)

TODAY = date.today().isoformat()
SOURCE = {'id':'test-studios','enabled':True,'kind':'official','adapter':'links',
          'url':'https://example.org/locations','link_pattern':r'^https://example.org/studio/',
          'company_id':'test-company','reuse_note':'Fixture only; not a real studio.'}
CONFIG = {'version':1,'sources':[SOURCE]}
EMPTY = {'version':1,'candidates':{},'sources':{}}
HTML = '<a href="/studio/alpha?utm_source=test">Alpha studio</a><a href="/studio/alpha">Alpha studio</a><script><a href="/studio/hidden">ignored</a></script><a href="mailto:person@example.org">Email</a>'


def observed(html=HTML, previous=None, today=TODAY):
    return scan(CONFIG, previous or EMPTY, [], fetcher=lambda _:html, today=today)


class ExtractionTests(unittest.TestCase):
    def test_enabled_sources_are_bounded_and_explicit(self):
        config=load_config(read(ROOT/'data/discovery/sources.json'))
        self.assertEqual(len(config['sources']),25)
        self.assertTrue(all(s['kind']=='official' for s in config['sources']))
        for changes in ({'id':'BAD'}, {'adapter':'execute-js'}, {'reuse_note':''}, {'url':'http://example.org'}, {'link_pattern':''}):
            with self.assertRaises(ValueError):load_config({'version':1,'sources':[{**SOURCE,**changes}]})
        with self.assertRaises(ValueError):load_config({'version':1,'sources':[SOURCE,SOURCE]})

    def test_links_strip_tracking_deduplicate_skip_scripts_and_contacts(self):
        items=extract(SOURCE,HTML)
        self.assertEqual(items,[{'url':'https://example.org/studio/alpha','label':'Alpha studio','city':'','country':''}])
        state,report=observed()
        candidate=next(iter(state['candidates'].values()))
        self.assertEqual(candidate['confidence'],'unknown')
        self.assertEqual(report['published_records'],0)
        self.assertNotIn('capabilities',candidate)

    def test_directory_candidates_are_also_unverified(self):
        state,_=scan({'version':1,'sources':[{**SOURCE,'kind':'directory'}]},EMPTY,[],fetcher=lambda _:HTML)
        self.assertTrue(all(c['confidence']=='unknown' for c in state['candidates'].values()))

    def test_jsonld_retains_place_but_not_phone_email_address_or_person(self):
        source={**SOURCE,'adapter':'jsonld'}
        html='<script type="application/ld+json">'+json.dumps({'@graph':[
            {'@type':'ProfessionalService','name':'Studio Example','url':'https://example.org/studio/a','telephone':'+1234567890','email':'person@example.org','address':{'streetAddress':'not copied','addressLocality':'City','addressCountry':{'name':'Country'}}},
            {'@type':'Person','name':'Private Person','address':{'addressLocality':'City'}}]})+'</script>'
        items=extract(source,html)
        self.assertEqual(items,[{'url':'https://example.org/studio/a','label':'Studio Example','city':'City','country':'Country'}])

    def test_rss_atom_change_signals_are_not_status_changes(self):
        source={**SOURCE,'adapter':'feed'}
        for feed in ['<rss><channel><item><title>Studio closes, acquired and relocating</title><link>https://example.org/news/change</link></item></channel></rss>',
                     '<feed xmlns="http://www.w3.org/2005/Atom"><entry><title>Studio closes, acquired and relocating</title><link href="https://example.org/news/change"/></entry></feed>']:
            state,report=scan({'version':1,'sources':[source]},EMPTY,[],fetcher=lambda _:feed)
            item=next(iter(state['candidates'].values()))
            self.assertEqual(len(item['signals']),3)
            self.assertEqual(item['review_status'],'pending')
            self.assertEqual(report['published_records'],0)
        with self.assertRaises(ValueError):extract(source,'<!DOCTYPE x [<!ENTITY evil "x">]><rss/>')

    def test_repeat_scan_is_idempotent_and_changed_link_resets_review(self):
        first,_=observed()
        repeated,report=observed(previous=first)
        self.assertEqual(first,repeated)
        self.assertFalse(report['events'])
        changed,report=observed(HTML.replace('Alpha studio','Alpha closes'),first)
        self.assertEqual(len(changed['candidates']),1)
        self.assertTrue(any(e['type']=='evidence_changed' for e in report['events']))
        self.assertEqual(next(iter(changed['candidates'].values()))['confidence'],'unknown')

    def test_absence_is_review_signal_not_deletion_and_reappearance_is_tracked(self):
        first,_=observed()
        missing,report=observed('<a href="/studio/beta">Beta studio</a>',first)
        old_id=next(iter(first['candidates']))
        self.assertEqual(missing['candidates'][old_id]['missing_since'],TODAY)
        self.assertTrue(any(e['type']=='missing_from_source' for e in report['events']))
        again,report=observed(previous=missing)
        self.assertIsNone(again['candidates'][old_id]['missing_since'])
        self.assertTrue(any(e['type']=='reappeared' for e in report['events']))

    def test_empty_failed_and_disabled_sources_never_withdraw_candidates(self):
        first,_=observed()
        empty,report=observed('<html>redesigned</html>',first)
        self.assertEqual(empty['candidates'],first['candidates'])
        self.assertEqual(report['sources'][0]['status'],'extraction_empty')
        def fail(_):raise OSError('secret response must not be logged')
        failed,report=scan(CONFIG,first,[],fetcher=fail)
        self.assertEqual(failed['candidates'],first['candidates'])
        self.assertNotIn('secret',json.dumps(report))
        disabled,report=scan({'version':1,'sources':[{**SOURCE,'enabled':False}]},first,[],fetcher=fail)
        self.assertFalse(report['sources'])
        self.assertEqual(disabled,first)

    def test_deferred_v08_backlog_is_preserved_without_publishing(self):
        seed=read(ROOT/'data/discovery/backlog.json')
        historical=read(ROOT/'data/research/v0.8-global-expansion/review-queue.json')
        self.assertEqual(seed,seed_backlog(historical))
        self.assertEqual(len(seed['candidates']),41)
        self.assertTrue(all(c['confidence']=='unknown' and c['reason'] for c in seed['candidates'].values()))

    def test_existing_matches_do_not_auto_accept_or_deduplicate(self):
        database=[{'id':'existing','website':'https://example.org/studio/alpha','evidence':'','city':'City','country':'Country','company_id':'test-company'}]
        state,_=scan(CONFIG,EMPTY,database,fetcher=lambda _:HTML)
        candidate=next(iter(state['candidates'].values()))
        self.assertEqual(candidate['existing_matches'],['existing'])
        self.assertEqual(candidate['review_status'],'pending')


class NetworkTests(unittest.TestCase):
    def test_source_and_redirect_restrictions(self):
        for url in ['http://example.org','https://localhost/','https://127.0.0.1/','https://10.0.0.1/','https://user:password@example.org/','https://example.org:8443/','https://example.org/?token=abc']:
            with self.assertRaises(ValueError):public_url(url)
        handler=NoUnsafeRedirect('example.org')
        for url in ['https://evil.org/','http://example.org/','https://example.org:8443/']:
            with self.assertRaises(ValueError):handler.redirect_request(request.Request(SOURCE['url']),None,302,'',{},url)

    def test_robots_disallow_does_not_fetch_page(self):
        fetcher=Fetcher()
        with patch.object(fetcher,'response',return_value=(b'User-agent: *\nDisallow: /locations','text/plain','utf-8')) as response:
            with self.assertRaises(ValueError):fetcher(SOURCE)
            self.assertEqual(response.call_count,1)

    def test_robots_unavailability_fails_closed(self):
        fetcher=Fetcher()
        with patch.object(fetcher,'response',side_effect=error.HTTPError('https://example.org/robots.txt',403,'Forbidden',{},None)) as response:
            with self.assertRaises(ValueError):fetcher(SOURCE)
            self.assertEqual(response.call_count,1)

    def test_robots_404_allows_and_rate_is_honoured(self):
        fetcher=Fetcher()
        with patch.object(fetcher,'response',side_effect=[error.HTTPError('https://example.org/robots.txt',404,'Missing',{},None),(b'<html/>','text/html','utf-8')]) as response:
            self.assertEqual(fetcher(SOURCE),'<html/>')
            self.assertEqual(response.call_count,2)
        fetcher=Fetcher()
        with patch.object(fetcher,'response',side_effect=[(b'User-agent: *\nCrawl-delay: 4','text/plain','utf-8'),(b'<html/>','text/html','utf-8')]) as response:
            fetcher(SOURCE)
            self.assertEqual(response.call_args.args[-1],4)

    def test_private_dns_is_blocked_before_request(self):
        with patch('discovery.socket.getaddrinfo',return_value=[(socket.AF_INET,socket.SOCK_STREAM,6,'',('192.168.1.1',443))]):
            with self.assertRaises(ValueError):Fetcher().response(SOURCE['url'],'example.org')


class ApprovalTests(unittest.TestCase):
    def setUp(self):
        self.database=read(ROOT/'studios.json')
        self.queue,_=observed()
        self.cid=next(iter(self.queue['candidates']))
        self.record=copy.deepcopy(self.database[31])
        self.record.update(id='fixture-location',company_id='fixture-company',name='Fixture Studio',city='Fixture City',country='Fixture Country',website='https://example.org/studio/alpha',evidence='https://example.org/studio/alpha',verified_on=TODAY,email='',phone='')
        self.records=[self.record]
        self.review=review_template(self.database,self.queue,self.records,[self.cid])[0]
        self.review.update(decision='approved',reviewed_by='public-reviewer',reviewed_on=TODAY,reason='Fixture: all relevant claims manually reviewed.',checks={c:True for c in CHECKS})

    def run_prepare(self):
        return prepare(self.database,self.queue,self.records,[self.review])

    def test_pending_template_cannot_publish(self):
        template=review_template(self.database,self.queue,self.records,[self.cid])
        self.assertEqual(template[0]['decision'],'pending')
        self.assertFalse(any(template[0]['checks'].values()))
        with self.assertRaises(ValueError):prepare(self.database,self.queue,self.records,template)

    def test_reviewed_addition_uses_importer_and_repeat_is_idempotent(self):
        before=copy.deepcopy(self.database)
        combined,report,additions=self.run_prepare()
        self.assertEqual(combined[:-1],before)
        self.assertEqual(self.database,before)
        self.assertEqual(additions,self.records)
        self.assertEqual(report['import_preview']['new_records'],['fixture-location'])
        self.assertEqual(report['import_repeat']['unchanged_records'],['fixture-location'])
        self.assertFalse(report['import_repeat']['new_records'])

    def test_any_changed_candidate_record_or_database_invalidates_approval(self):
        for target,key,value in [(self.queue['candidates'][self.cid],'label','changed'),(self.record,'city','changed'),(self.database[0],'status','changed')]:
            original=target[key];target[key]=value
            with self.assertRaises(ValueError):self.run_prepare()
            target[key]=original

    def test_absent_candidate_or_missing_evidence_check_blocks(self):
        self.queue['candidates'][self.cid]['missing_since']=TODAY
        with self.assertRaises(ValueError):self.run_prepare()
        self.queue['candidates'][self.cid]['missing_since']=None
        for key in CHECKS:
            self.review['checks'][key]=False
            with self.assertRaises(ValueError):self.run_prepare()
            self.review['checks'][key]=True

    def test_expired_future_or_predating_reviews_are_blocked(self):
        for day in ['2000-01-01','2999-01-01']:
            self.review['reviewed_on']=day
            with self.assertRaises(ValueError):self.run_prepare()

    def test_existing_id_cannot_be_overwritten_as_addition(self):
        self.record['id']=self.database[0]['id']
        self.review.update(record_id=self.record['id'],record_hash=digest(self.record))
        with self.assertRaises(ValueError):self.run_prepare()

    def test_explicit_update_preserves_identity_and_checks_old_hash(self):
        self.records[0]=copy.deepcopy(self.database[31]);self.record=self.records[0]
        self.record.update(status='Fixture reviewed update',verified_on=TODAY)
        self.review.update(record_id=self.record['id'],action='update',record_hash=digest(self.record),previous_record_hash=digest(self.database[31]))
        combined,report,additions=self.run_prepare()
        self.assertEqual(len(combined),len(self.database))
        self.assertEqual(combined[31]['status'],'Fixture reviewed update')
        self.assertEqual(report['approved_updates'],[self.record['id']])
        self.assertFalse(additions)
        self.review['previous_record_hash']='stale'
        with self.assertRaises(ValueError):self.run_prepare()

    def test_duplicate_facility_requires_explicit_rationale(self):
        self.record.update(company_id=self.database[31]['company_id'],city=self.database[31]['city'],country=self.database[31]['country'])
        self.review['record_hash']=digest(self.record)
        with self.assertRaises(ValueError):self.run_prepare()
        self.review.update(allow_distinct_location=True,distinct_reason='Fixture independently supported separate stage')
        self.assertEqual(len(self.run_prepare()[0]),len(self.database)+1)

    def test_contacts_and_unknown_location_evidence_are_not_publishable(self):
        for key,value in [('phone','123'),('email','person@example.org'),('evidence_state','unknown')]:
            before=self.record[key];self.record[key]=value;self.review['record_hash']=digest(self.record)
            with self.assertRaises(ValueError):self.run_prepare()
            self.record[key]=before
        self.record['private_crm_note']='excluded fixture field'
        self.review['record_hash']=digest(self.record)
        with self.assertRaises(ValueError):self.run_prepare()

    def test_cli_produces_review_bundle_then_proposal_without_changing_canonical(self):
        original=(ROOT/'studios.json').read_bytes()
        with tempfile.TemporaryDirectory() as folder:
            folder=Path(folder)
            for name,data in [('queue',self.queue),('records',self.records),('reviews',[self.review])]:
                (folder/(name+'.json')).write_text(json.dumps(data))
            result=subprocess.run([sys.executable,str(ROOT/'tools/discovery.py'),'review-template',
                '--queue',str(folder/'queue.json'),'--records',str(folder/'records.json'),
                '--candidate',self.cid,'--output',str(folder/'pending-bundle')],capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stderr)
            self.assertEqual(read(folder/'pending-bundle/reviews.json')[0]['decision'],'pending')
            args=[sys.executable,str(ROOT/'tools/discovery.py'),'prepare','--queue',str(folder/'queue.json'),'--records',str(folder/'records.json'),'--reviews',str(folder/'reviews.json')]
            output=folder/'proposal'
            result=subprocess.run([*args,'--output',str(output)],capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stderr)
            self.assertTrue((output/'batch.csv').is_file())
            self.assertEqual(len(read(output/'studios.json')),len(self.database)+1)
            result=subprocess.run([*args,'--output',str(ROOT)],capture_output=True,text=True)
            self.assertNotEqual(result.returncode,0)
        self.assertEqual((ROOT/'studios.json').read_bytes(),original)


if __name__=='__main__': unittest.main()
