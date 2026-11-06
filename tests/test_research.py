"""Research preparation cannot grant approval, publish, or erase discovery history."""
import copy
from datetime import date,timedelta
import json
from pathlib import Path
import sys
import unittest
from urllib import error

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from discovery import digest,extract,scan,load_config
from research import dossier,review_html,stage
from source_policy import audit
from pr_reviews import review_state
from test_discovery import SOURCE,CONFIG,EMPTY,observed,TODAY
from test_pipeline import record

class AdaptersTests(unittest.TestCase):
    def source(self):
        return {**SOURCE,'adapter':'location_labels','place_labels':{'London':{'city':'London','country':'United Kingdom','unit_key':'stage-a'},'Paris':{'city':'Paris','country':'France','unit_key':'stage-b'}}}

    def test_labels_ignore_navigation_and_do_not_inherit_next_card_claims(self):
        source=self.source()
        rows=extract(source,'<nav>London</nav><h2>London</h2><p>Office reference</p><h2>Paris</h2><p>Facial capture</p><footer>Motion capture</footer>')
        self.assertEqual(len(rows),2)
        self.assertEqual(rows[0]['claim_terms'],[])
        self.assertEqual(rows[1]['claim_terms'],['Facial Capture'])
        self.assertEqual(rows[0]['observation_kind'],'location_reference')

    def test_explicit_two_facilities_in_same_city_keep_identity(self):
        source=self.source();source['place_labels']['Paris'].update(city='London',country='United Kingdom')
        state,_=scan({'version':1,'sources':[source]},EMPTY,[],fetcher=lambda _:'<h2>London</h2><h2>Paris</h2>')
        self.assertEqual(len(state['candidates']),2)
        again,_=scan({'version':1,'sources':[source]},state,[],fetcher=lambda _:'<h2>London</h2><h2>Paris</h2>')
        self.assertEqual(state,again)
        self.assertTrue(all(c['confidence']=='unknown' for c in state['candidates'].values()))

    def test_page_changes_and_failed_fetch_preserve_candidates(self):
        first,_=observed()
        changed,report=observed('<div>new design</div>',first)
        self.assertEqual(changed['candidates'],first['candidates'])
        self.assertIn('page_changed',[r['type'] for r in report['events']])
        def fail(_):raise OSError('do not log response')
        failed,report=scan(CONFIG,first,[],fetcher=fail)
        self.assertEqual(failed['candidates'],first['candidates'])
        self.assertEqual(report['sources'][0]['status'],'fetch_or_parse_error')

    def test_new_enabled_sources_require_recorded_review(self):
        with self.assertRaises(ValueError):load_config({**CONFIG,'require_access_review':True})
        config=json.loads((ROOT/'data/discovery/sources.json').read_text())
        self.assertEqual(len(load_config(config)['sources']),25)
        self.assertFalse(next(s for s in config['sources'] if s['id']=='ea-studios')['enabled'])

    def test_structured_roster_is_not_discarded_as_contact_navigation(self):
        source=self.source();source['url']='https://example.org/contact'
        queue,report=scan({'version':1,'sources':[source]},EMPTY,[],fetcher=lambda _:'<h2>London</h2>')
        result=dossier(queue,report,[],{'version':1,'sources':[source]})
        self.assertEqual(result['candidate_counts']['potentially_new'],1)
        self.assertFalse(result['dossiers'][0]['publication_approved'])

class PolicyTests(unittest.TestCase):
    def test_policy_keywords_never_grant_permission(self):
        class Fetch:
            def response(self,url,host,delay=1):return (b'User-agent: *\nAllow: /' if url.endswith('robots.txt') else b'Public policy'), 'text/plain','utf-8'
        result=audit({'sources':[{**SOURCE,'policy_urls':['https://example.org/privacy']}]},Fetch())
        self.assertEqual(result['auto_enabled'],0)
        self.assertEqual(result['sources'][0]['decision'],'manual_review_required')
        self.assertFalse(result['sources'][0]['source_fetched'])

    def test_robots_deny_failure_and_known_prohibition_are_fail_closed(self):
        for body in (b'User-agent: *\nDisallow: /',None):
            class Fetch:
                def response(self,url,host,delay=1):
                    if body is None:raise OSError('network unavailable')
                    self.assert_robots=url.endswith('robots.txt')
                    if not self.assert_robots:raise AssertionError('prohibited policy fetched')
                    return body,'text/plain','utf-8'
            result=audit({'sources':[{**SOURCE,'policy_urls':['https://example.org/privacy']}]},Fetch())
            self.assertFalse(result['sources'][0]['robots_allows_collector'])
        class Fail:
            def response(self,*args,**kwargs):raise AssertionError('EA must not be fetched')
        r=audit({'sources':[{**SOURCE,'access_review':{'decision':'automated_collection_disabled'}}]},Fail())
        self.assertEqual(r['sources'][0]['decision'],'previously_prohibited_not_fetched')

class ProposalTests(unittest.TestCase):
    def proposal(self):
        r=record(evidence_state='confirmed',evidence='https://example.org/location',verified_on=TODAY)
        m={'publication_mode':'github_PR_human_review','baseline_hash':digest([]),'records':[{'id':r['id'],'record_hash':digest(r),'reviewed_on':TODAY,'location_sources':[r['evidence']],'capability_evidence':r['capability_evidence']}]}
        return r,m

    def test_pr_staging_is_append_only_repeatable_and_does_not_approve(self):
        r,m=self.proposal();rows,audit=stage([],[r],m)
        self.assertEqual(rows,[r]);self.assertFalse(audit['main_written'])
        self.assertEqual(audit['approved_claims'],0)
        self.assertEqual(audit['repeat']['unchanged_records'],[r['id']])
        self.assertIn('pending',audit['human_approval'])

    def test_stale_baseline_changed_record_and_unverified_claims_block_staging(self):
        row,manifest=self.proposal()
        for patch in ({'baseline_hash':'stale'},{'publication_mode':'auto_publish'}):
            with self.assertRaises(ValueError):stage([],[row],{**manifest,**patch})
        for patch in ({'city':'changed'},{'evidence_state':'unknown'},{'phone':'private contact'}):
            with self.assertRaises(ValueError):stage([],[{**row,**patch}],manifest)
        for day in ((date.today()-timedelta(days=31)).isoformat(),(date.today()+timedelta(days=1)).isoformat()):
            m=copy.deepcopy(manifest);m['records'][0]['reviewed_on']=day
            with self.assertRaises(ValueError):stage([],[row],m)

    def test_duplicate_and_update_require_explicit_research(self):
        row,m=self.proposal();base={**row,'id':'previous'};m['baseline_hash']=digest([base])
        with self.assertRaises(ValueError):stage([base],[row],m)
        with self.assertRaises(ValueError):stage([base],[row],m,[row['id']])
        m['records'][0]['distinct_reason']='Separate source-backed physical stages; fixture.'
        rows,_=stage([base],[row],m,[row['id']]);self.assertEqual(len(rows),2)
        m['baseline_hash']=digest([row]);update={**row,'name':'Changed'};m['records'][0]['record_hash']=digest(update)
        with self.assertRaises(ValueError):stage([row],[update],m)
        m['records'][0]['previous_record_hash']=digest(row)
        rows,audit=stage([row],[update],m);self.assertEqual(rows,[update]);self.assertEqual(audit['updates'],[row['id']])

    def test_dashboard_escapes_evidence_and_claims_never_become_approved(self):
        queue,report=observed();candidate=next(iter(queue['candidates'].values()))
        candidate.update(label='<script>alert(1)</script>',claim_terms=['Motion Capture'],signals=['possible_closure'])
        result=dossier(queue,report,[],CONFIG)
        output=review_html(result)
        self.assertIn('&lt;script&gt;',output);self.assertNotIn('<script>',output)
        self.assertIn("default-src 'none'",output)
        self.assertIn('unverified_source_term',output)
        self.assertEqual(result['dossiers'][0]['alerts'][0]['status'],'requires_investigation')
        self.assertEqual(result['approved_claims'],0)
        self.assertNotIn('onclick',output)

class NativeReviewTests(unittest.TestCase):
    def review(self,**patch):
        return {'id':1,'user':{'login':'maintainer','type':'User'},'state':'APPROVED','commit_id':'head','author_association':'OWNER','submitted_at':'2026-11-06T01:00:00Z',**patch}

    def test_exact_head_account_review_records_no_publication_authorisation(self):
        result=review_state([self.review()],'head','author')
        self.assertEqual(result['status'],'review_recorded')
        self.assertFalse(result['publication_authorised_by_this_tool']);self.assertFalse(result['merged'])
        self.assertIn('does not prove human',result['human_identity_claim'])

    def test_bots_author_outsiders_and_stale_reviews_are_ignored(self):
        for patch in ({'commit_id':'old'},{'user':{'login':'agent[bot]','type':'Bot'}},{'user':{'login':'author','type':'User'}},{'author_association':'NONE'}):
            self.assertEqual(review_state([self.review(**patch)],'head','author')['status'],'pending_review')
        # Reviewer display names or invented strings have no approval authority.
        self.assertEqual(review_state([{'reviewed_by':'AI reviewer','decision':'approved'}],'head','author')['status'],'pending_review')

    def test_latest_dismissal_or_changes_requested_supersedes_approval(self):
        for state in ('DISMISSED','CHANGES_REQUESTED'):
            reviews=[self.review(),self.review(id=2,state=state,submitted_at='2026-11-06T02:00:00Z')]
            self.assertEqual(review_state(reviews,'head','author')['status'],'pending_review')
