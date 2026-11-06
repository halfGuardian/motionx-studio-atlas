"""Read-only triage regressions, including real observed link projection and continuity."""
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from discovery import archive_history, digest, extract, read, scan
from triage import classify, markdown, triage


class TriageTests(unittest.TestCase):
    def setUp(self):
        self.database=read(ROOT/'studios.json')
        self.config=read(ROOT/'data/discovery/sources.json')
        self.sources={s['id']:s for s in self.config['sources']}
        self.backlog=read(ROOT/'data/discovery/backlog.json')
        self.observed=read(ROOT/'tests/fixtures/discovery/observed-links-42149794259.json')['observations']
        self.queue=copy.deepcopy(self.backlog)
        for link in self.observed:
            # Test replay of real observed IDs/URLs/labels, not a reconstructed original artifact.
            item={**link,'city':'','country':'','confidence':'unknown','content_hash':digest(link),
                  'first_seen':'2026-11-06','last_seen':'2026-11-06','source_kind':'official',
                  'review_status':'pending','missing_since':None,'signals':[]}
            self.queue['candidates'][link['id']]=item
        self.report={'observed_on':'2026-11-06','sources':[{'id':sid,'status':'ok','candidate_count':sum(l['source_id']==sid for l in self.observed)} for sid in self.sources]}
        self.rejected=[r for r in read(ROOT/'data/research/v0.8-global-expansion/review-queue.json') if r['decision']=='reject']

    def run_triage(self):return triage(self.queue,self.report,self.database,self.config,self.rejected,observed_on='2026-11-06')

    def test_real_link_projection_classification_totals_and_no_writes(self):
        before=copy.deepcopy((self.queue,self.database,self.report))
        report=self.run_triage()
        self.assertEqual(report['candidate_count'],133)
        self.assertEqual(report['counts'],{'already_represented':46,'potentially_new':14,'irrelevant':24,'requires_research':49})
        self.assertEqual(report['published_records'],0)
        self.assertEqual(report['approval_changes'],0)
        self.assertEqual((self.queue,self.database,self.report),before)
        self.assertEqual(len([r for r in report['candidates'] if r['matching_scope']=='organisation' and r['classification']=='already_represented']),8)

    def test_matching_retains_evidence_dates_and_original_confidence(self):
        result=self.run_triage()
        for row in result['candidates']:
            original=self.queue['candidates'][row['id']]
            self.assertEqual(row['observation'],original)
            self.assertEqual(row['candidate_hash'],digest(original))
            self.assertTrue(row['reasons'])
            self.assertEqual(row['observation']['confidence'],'unknown')
        self.assertEqual(result['database_hash'],digest(self.database))

    def test_source_nav_filter_and_real_ea_observation(self):
        result=self.run_triage()
        for row in result['candidates']:
            if row['observation']['source_id']=='ea-studios':
                self.assertEqual(row['classification'],'irrelevant')
                self.assertEqual(row['observation']['url'],'https://www.ea.com/careers/locations')
                self.assertFalse(row['source_enabled'])
        source=self.sources['cinesite-group']
        html='''<a href="https://cinesite.com/about-us/">About</a>
        <a href="https://image-engine.com/">FIND OUT MORE</a>
        <a href="https://future-operator.example.org/">Find out more</a>
        <a href="https://image-engine.com/">Privacy</a>'''
        rows=extract(source,html)
        self.assertEqual([r['url'] for r in rows],['https://image-engine.com/','https://future-operator.example.org/'])
        self.assertEqual(extract(source,html+html),rows)

    def test_cinesite_homepages_are_organisation_matches_not_new_facilities(self):
        rows=[r for r in self.run_triage()['candidates'] if r['observation']['source_id']=='cinesite-group']
        self.assertEqual(sum(r['classification']=='irrelevant' for r in rows),20)
        self.assertEqual(sum(r['matching_scope']=='organisation' for r in rows),7)
        self.assertFalse(any(r['classification']=='potentially_new' for r in rows))

    def test_dneg_all_19_match_existing_location_specific_urls(self):
        rows=[r for r in self.run_triage()['candidates'] if r['observation']['source_id']=='dneg-studios']
        self.assertEqual(len(rows),19)
        self.assertTrue(all(r['classification']=='already_represented' and r['matching_scope']=='location' for r in rows))

    def test_old_toronto_operator_is_detected_without_inheriting_capabilities(self):
        row=next(r for r in self.run_triage()['candidates'] if r['observation']['url'].endswith('/locations/toronto'))
        self.assertEqual(row['matched_location_ids'],['ubisoft-toronto'])
        self.assertEqual(row['matching_scope'],'organisation')
        self.assertNotIn('capabilities',row['observation'])

    def test_market_hq_and_historical_closure_links_need_research(self):
        rows=self.run_triage()['candidates']
        for slug in ['stockholm','san-francisco','sydney','paris-area','taiwan','ubisoft-mobile-hq','ubisoft-worldwide-hq']:
            row=next(r for r in rows if not r['id'].startswith('backlog') and r['observation']['url'].endswith('/'+slug))
            self.assertEqual(row['classification'],'requires_research',slug)

    def test_same_city_different_company_does_not_match(self):
        candidate={'url':'https://www.dneg.com/location/guildford','label':'Guildford'}
        outcome=classify(candidate,self.sources['dneg-studios'],self.database,[])
        self.assertEqual(outcome['classification'],'potentially_new')
        self.assertFalse(outcome['matched_location_ids'])

    def test_duplicate_observations_are_linked_not_removed(self):
        original=next(v for v in self.queue['candidates'].values() if v['source_id']=='dneg-studios')
        other={**original,'id':'different-source-id','source_id':'other-source'}
        self.queue['candidates'][other['id']]=other
        result=self.run_triage()
        row=next(r for r in result['candidates'] if r['id']==other['id'])
        self.assertIn(original['id'],row['duplicate_observation_ids'])
        self.assertEqual(result['candidate_count'],134)
        self.assertEqual(row['classification'],'requires_research')

    def test_failed_sources_and_backlog_are_never_deleted_or_approved(self):
        self.report['sources']=[{'id':s,'status':'fetch_or_parse_error'} for s in self.sources]
        result=self.run_triage()
        self.assertEqual(result['candidate_count'],133)
        backlog=[r for r in result['candidates'] if r['id'].startswith('backlog')]
        self.assertEqual(len(backlog),41)
        self.assertTrue(all(r['classification']=='requires_research' for r in backlog))
        self.assertEqual(len(result['candidates']),len(self.queue['candidates']))

    def test_report_includes_original_bytes_and_cli_does_not_modify_inputs(self):
        with tempfile.TemporaryDirectory() as folder:
            p=Path(folder)
            for name,value in [('queue',self.queue),('report',self.report)]:
                (p/(name+'.json')).write_text(json.dumps(value,indent=1)+'\n')
            original=(p/'queue.json').read_bytes()
            result=subprocess.run([sys.executable,str(ROOT/'tools/triage.py'),'--queue',str(p/'queue.json'),'--report',str(p/'report.json'),'--output',str(p/'out')],capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stderr)
            self.assertEqual((p/'out/queue.json').read_bytes(),original)
            self.assertEqual((p/'queue.json').read_bytes(),original)
            self.assertTrue((p/'out/summary.md').is_file())
            self.assertIn('requires_research',result.stdout)

    def test_invalid_queue_and_html_labels_are_handled_safely(self):
        first=next(iter(self.queue['candidates']))
        self.queue['candidates'][first]['url']='javascript:alert(1)'
        with self.assertRaises(ValueError):self.run_triage()
        self.queue['candidates'][first]['url']='https://example.org/'
        self.queue['candidates'][first]['label']='<script>unsafe</script>|\nheading'
        summary=markdown(self.run_triage())
        self.assertNotIn('<script>',summary)
        self.assertIn('&lt;script&gt;',summary)


class ContinuityTests(unittest.TestCase):
    def test_narrowed_filters_do_not_flag_historical_nav_as_missing_in_later_runs(self):
        source={'id':'test','enabled':True,'kind':'official','adapter':'links','url':'https://example.org/studios',
                'link_pattern':r'^https://example.org/','reuse_note':'Fixture only'}
        body='<a href="/about">About</a><a href="/studio/a">Studio</a>'
        initial,_=scan({'version':1,'sources':[source]},read(ROOT/'data/discovery/backlog.json'),[],fetcher=lambda _:body)
        narrow={**source,'link_pattern':r'^https://example.org/studio/'}
        second,report=scan({'version':1,'sources':[narrow]},initial,[],fetcher=lambda _:body)
        self.assertTrue(any(e['type']=='extraction_rules_changed' for e in report['events']))
        third,report=scan({'version':1,'sources':[narrow]},second,[],fetcher=lambda _:body)
        self.assertFalse(any(e['type']=='missing_from_source' for e in report['events']))
        self.assertEqual(len(third['candidates']),len(initial['candidates']))
        self.assertTrue(all(c['missing_since'] is None for c in third['candidates'].values()))

    def test_raw_history_survives_successive_archive_cycles(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);previous=root/'previous';previous.mkdir()
            old=b'{"events": ["original"]}\n'
            (previous/'report.json').write_bytes(old)
            (previous/'queue.json').write_text('{"version":1}\n')
            run=root/'run'
            archive_history(previous,run)
            old_path=run/'history'/(hashlib.sha256(old).hexdigest()+'.json')
            self.assertEqual(old_path.read_bytes(),old)
            (run/'report.json').write_text('{"events": []}\n')
            (run/'queue.json').write_text('{"version":1,"new":true}\n')
            next_run=root/'next'
            archive_history(run,next_run)
            self.assertEqual((next_run/'history'/old_path.name).read_bytes(),old)
            self.assertEqual(len(list((next_run/'history').glob('*.json'))),4)

    def test_network_failures_retain_queue_and_prior_success_metadata(self):
        config=read(ROOT/'data/discovery/sources.json')
        queue=read(ROOT/'data/discovery/backlog.json')
        def fail(_):raise OSError('network unavailable')
        state,report=scan(config,queue,[],fetcher=fail)
        self.assertEqual(state['candidates'],queue['candidates'])
        self.assertEqual(len(report['sources']),5)  # EA disabled, never fetched
        self.assertTrue(all(s['status']=='fetch_or_parse_error' for s in report['sources']))


if __name__=='__main__':unittest.main()
