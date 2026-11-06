"""Exact release preservation, safe import replay and v1 discovery reliability."""
import copy,csv,json,sys,unittest,subprocess,tempfile
from datetime import date
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
from discovery import digest,merge_checkpoint,read,scan
from research import stage,dossier,review_html
from validate import validate,read_records
from import_csv import plan_import
from triage import classify
from review_rules import audit
from snapshots import before_v10
from test_discovery import observed,CONFIG
P=ROOT/'data/research/v1.0-launch'

class LaunchTests(unittest.TestCase):
    def test_all_existing_ids_preserved_only_three_hashed_updates(self):
        base=before_v10();rows=read(ROOT/'studios.json');m=read(P/'evidence.json')
        self.assertEqual(digest(base),m['baseline_hash']);self.assertEqual(len(base),182)
        self.assertEqual([r['id'] for r in rows[:182]],[r['id'] for r in base])
        self.assertEqual([r['id'] for r,b in zip(rows,base) if r!=b],list(m['before_updates']))
        self.assertEqual([(r['lat'],r['lng']) for r in rows[:182]],[(r['lat'],r['lng']) for r in base])
        self.assertEqual((len(rows),len({r['company_id'] for r in rows}),len({r['country'] for r in rows})),(243,119,38))
        errors,warnings=validate(rows);self.assertFalse(errors);self.assertEqual(len(warnings),265)
        self.assertEqual(sum(r['evidence_state']=='unknown' for r in rows),13)
    def test_exact_evidence_and_csv_replay_need_no_approval_fabrication(self):
        base=before_v10();records=read(P/'records.json');manifest=read(P/'evidence.json')
        self.assertEqual(records,read_records(P/'batch.csv'))
        allowed=[r['id'] for r in manifest['records'] if r.get('distinct_reason')]
        class ReviewedDate(date):
            @classmethod
            def today(cls):return cls(2026,11,6)
        with patch('research.date',ReviewedDate):result,report=stage(base,records,manifest,allowed)
        self.assertEqual(result,read(ROOT/'studios.json'));self.assertEqual(len(report['additions']),61)
        self.assertEqual(report['approved_claims'],0);self.assertFalse(report['main_written'])
        again,repeat=plan_import(result,records,allowed)
        self.assertEqual(again,result);self.assertEqual(len(repeat['unchanged_records']),64)
        self.assertFalse(repeat['new_records'] or repeat['rejected_records'])
        bad=copy.deepcopy(manifest);bad['records'][0]['record_hash']='stale'
        with patch('research.date',ReviewedDate),self.assertRaises(ValueError):stage(base,records,bad,allowed)
    def test_facility_scopes_brands_and_public_data(self):
        rows=read(P/'records.json');new=rows[:61];byid={r['id']:r for r in rows}
        self.assertEqual(sum('Motion Capture' in r['capabilities'] for r in new),7)
        for r in rows:
            self.assertFalse(r.get('phone') or r.get('email'))
            self.assertEqual(r['coordinate_precision'],'city')
            self.assertTrue(all(e['verified_on']=='2026-11-06' and e['state']=='confirmed' for e in r['capability_evidence'].values()))
        production=byid['platige-warsaw-production'];capture=byid['platige-warsaw-mocap']
        self.assertEqual(production['company_id'],capture['company_id']);self.assertNotEqual(production['evidence'],capture['evidence'])
        self.assertEqual((production['lat'],production['lng']),(capture['lat'],capture['lng']))
        self.assertNotIn('Motion Capture',production['capabilities'])
        self.assertNotIn('Game Development',byid['virtuos-montreal']['capabilities'])
        self.assertEqual(byid['virtuos-paris']['city'],'Cergy');self.assertEqual(byid['lemon-sky-shah-alam']['city'],'Shah Alam')
    def test_optional_operating_name_must_be_consistent(self):
        r=copy.deepcopy(read(P/'records.json')[0]);other=copy.deepcopy(r);other['id']='another-location';other['city']='Elsewhere';other['company_name']='Wrong brand'
        self.assertTrue(any('conflicting' in e for e in validate([r,other])[0]))
    def test_checkpoint_identity_conflicts_never_replace_history_or_reviews(self):
        q,_=observed();bad=copy.deepcopy(q)
        for field,value in [('url','https://example.org/other'),('source_id','other-source'),('unit_key','other-stage')]:
            bad=copy.deepcopy(q);next(iter(bad['candidates'].values()))[field]=value
            with self.assertRaisesRegex(ValueError,'identity conflict'):merge_checkpoint(q,bad)
        before=copy.deepcopy(q);out,_=merge_checkpoint(q,q);self.assertEqual(out,before);self.assertEqual(q,before)
    def test_matching_does_not_expand_shared_contact_url_to_all_branches(self):
        q,_=observed();c=copy.deepcopy(CONFIG);source=c['sources'][0];source['company_id']='test'
        # The same source URL is an index, not a facility identity.
        sample=copy.deepcopy(read(P/'records.json')[0]);sample.update(company_id='test',city='Paris',country='France',website=source['url'],evidence=source['url'])
        second={**sample,'id':'other','city':'London','country':'United Kingdom'}
        out,_=scan(c,{'version':1,'sources':{},'candidates':{}},[sample,second],fetcher=lambda _:'<a href="'+source['url']+'">Studio</a>')
        for value in out['candidates'].values():self.assertEqual(value['existing_matches'],[])
    def test_same_city_named_facilities_need_identity_review(self):
        rows=read(P/'records.json');same=[r for r in rows if r['company_id']=='platige']
        c={'url':'https://platige.com/studio/','label':'Warsaw','city':'Warsaw','country':'Poland','observation_kind':'location_reference'}
        result=classify(c,{'company_id':'platige'},same,[])
        self.assertEqual(result['classification'],'requires_research');self.assertEqual(len(result['matched_location_ids']),2)
    def test_rules_audit_reports_unavailable_and_empty_rules_honestly(self):
        def fail(args,**kwargs):return subprocess.CompletedProcess(args,1,'','403')
        result=audit('halfGuardian/motionx-studio-atlas',fail)
        self.assertTrue(all(e['status']=='unavailable' for e in result['endpoints'].values()))
        def empty(args,**kwargs):return subprocess.CompletedProcess(args,0,'[]' if args[-1].endswith('/main') else '{}')
        result=audit('halfGuardian/motionx-studio-atlas',empty)
        self.assertEqual(result['endpoints']['effective_rules']['rules'],[])
        self.assertIn('Not asserted',result['enforcement_claim'])
        with self.assertRaises(ValueError):audit('owner/repo;command',fail)

    def test_release_queue_retains_every_checkpoint_observation_without_business_approval(self):
        old=read(ROOT/'data/research/v0.9.3-global/queue.json');new=read(P/'queue.json')
        self.assertEqual(len(new['candidates']),200)
        for cid,c in old['candidates'].items():self.assertEqual(new['candidates'][cid],c)
        deferred=read(P/'review-queue.json');self.assertEqual(len(deferred),28)
        self.assertTrue(all(not r['publication_approved'] for r in deferred))
        config=read(ROOT/'data/discovery/sources.json')
        self.assertEqual(len(config['sources']),25);self.assertEqual(sum(s['enabled'] for s in config['sources']),8)
        self.assertFalse(next(s for s in config['sources'] if s['id']=='ea-studios')['enabled'])
    def test_report_priorities_and_stale_evidence_do_not_approve_claims(self):
        queue=read(P/'queue.json');report=dossier(queue,{'sources':[]},before_v10(),read(ROOT/'data/discovery/sources.json'),as_of='2027-01-01')
        self.assertTrue(all(r['evidence_freshness']=='revisit_required' and not r['publication_approved'] for r in report['dossiers']))
        self.assertEqual(report['approved_claims'],0);self.assertEqual(report['published_records'],0)
        html=review_html(report);self.assertIn('priority',html);self.assertIn('before manual merge',html)
    def test_compatible_blank_unit_key_does_not_break_historical_checkpoints(self):
        q,_=observed();other=copy.deepcopy(q)
        for c in other['candidates'].values():c.setdefault('unit_key','')
        merged,_=merge_checkpoint(q,other);self.assertEqual(merged,q)
    def test_public_record_urls_exclude_credentials_local_addresses_and_tokens(self):
        from validate import url_valid
        for url in ['https://user:pass@example.org/','https://localhost/','https://127.0.0.1/','https://10.0.0.1/','https://service.internal/','https://example.org/?token=secret','https://example.org/\x00']:
            self.assertFalse(url_valid(url),url)
        self.assertTrue(url_valid('https://example.org/public-source'))
