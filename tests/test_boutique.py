"""Full-atlas reconciliation and honest boutique research, not benchmark injection."""
import copy, json, sys, tempfile, unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
from boutique import HOME, Matcher, relevance, build_research, evaluate, source_inputs, save_reports, region
from boutique_collect import collect, project, query_plan
from launch_readiness import records
from discovery import read, digest
from bulk_catalog import sha
from unified_catalog import validate_research

class MatchingTests(unittest.TestCase):
    def setUp(self):
        self.rows=[{'id':'one','name':'Example Animation','website':'https://example.test','country':'Canada'}, {'id':'two','name':'Example Animation','website':'https://example.test','country':'Japan'}, {'id':'brand','name':'Distinct Brand','website':'https://example.test','country':'Canada'}]
        self.matcher=Matcher(self.rows)
    def test_exact_identity_preserves_multiple_branches(self):
        ids,reason,confidence,conflict=self.matcher.match(self.rows[0]);self.assertEqual(ids,['one','two']);self.assertFalse(conflict);self.assertEqual(confidence,'high')
    def test_domain_alone_never_merges_a_distinct_operating_brand(self):
        ids,reason,confidence,conflict=self.matcher.match({'name':'Unrelated Brand','website':'https://example.test','country':'Canada'});self.assertTrue(conflict);self.assertEqual(confidence,'low')
    def test_identical_names_at_different_domains_need_review(self):
        self.assertTrue(self.matcher.match({'name':'Example Animation','website':'https://different.test','country':'Canada'})[3])
    def test_shared_host_is_not_an_organisation_identity(self):
        m=Matcher([{'id':'one','name':'One','website':'https://wixsite.com/one','country':''}]);self.assertEqual(m.match({'name':'Two','website':'https://wixsite.com/two','country':''})[0],[])
    def test_source_listing_url_is_not_confused_with_company_website(self):
        m=Matcher([{'id':'one','name':'Example Animation','website':'https://directory.test/row','website_kind':'source_listing','country':'Canada'}]);self.assertEqual(m.match({'name':'Example Animation','website':'https://example.test/','country':'Canada'})[0],['one'])
    def test_accents_and_punctuation_are_normalized_without_losing_brand_words(self):
        m=Matcher([{'id':'x','name':'Stiúidio Fia','website':'https://fia.test','country':''}]);self.assertEqual(m.match({'name':'Stiuidio Fia','website':'https://fia.test','country':''})[0],['x']);self.assertFalse(m.match({'name':'Fia','website':'https://other.test','country':''})[0])
    def test_taxonomy_and_negative_terms_do_not_invent_character_or_capture_services(self):
        self.assertEqual(relevance('Wedding Video',['Animation'])[0],{});s,_=relevance('Creative House',['3D']);self.assertIn('cg',s);self.assertNotIn('character',s);self.assertNotIn('pipeline',s)
        s,_=relevance('Production House',['animación de personajes','Unreal Engine']);self.assertIn('character',s);self.assertIn('realtime',s)
        self.assertIn('animation',relevance('Production House',['Stop Motion'])[0])
    def test_global_regions_do_not_default_unknown_or_african_countries_to_europe(self):
        self.assertEqual(region('Algeria'),'Africa');self.assertEqual(region('Cambodia'),'Asia');self.assertEqual(region('Unknown'),'Unknown');self.assertEqual(region('New Zealand'),'Oceania')

class FullDiscoveryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest,current=records(ROOT/'data/public',ROOT/'studios.json');cls.all=[r for r in current if not r['id'].startswith('annecy-')];cls.base=[r for r in cls.all if not r['id'].startswith('boutique-')];cls.result=build_research(cls.base)
    def test_entire_41735_record_baseline_and_all_source_rows_are_examined(self):
        self.assertEqual(len(self.base),41735);self.assertEqual(self.result['summary']['existing_catalogue_records_examined'],41735)
        self.assertEqual(self.result['summary']['raw_source_rows'],sum(a['raw_records'] for a in self.result['input_audit']));self.assertEqual(len(self.result['audit']),570)
        self.assertEqual(next(a['raw_records'] for a in self.result['input_audit'] if a['source_id']=='animstudios-github'),424)
    def test_existing_frame_machine_is_visible_at_original_identity_with_actual_primary_evidence(self):
        frame=next(r for r in self.all if r['id']=='overture-39fd34a0-9be1-4ac0-a46e-ebd53a1599ff')
        self.assertEqual(frame['name'],'Frame Machine');p=self.result['profiles'][frame['id']];self.assertIn('realtime',p['signals']);self.assertEqual(p['research_status'],'primary_claims_reviewed');self.assertTrue(any('framemachine.tv/about-frame_machine/' in s['url'] for s in p['sources']))
        self.assertFalse(any(r['name']=='Frame Machine' for r in self.result['proposed_references']))
    def test_floating_rock_is_discovered_from_full_nzfc_collection_without_reading_benchmark(self):
        row=next(r for r in self.all if r.get('website')=='https://floating-rock.com/');self.assertIsNone(row['lat']);self.assertEqual(row['evidence_class'],'C');self.assertIn(row['id'],self.result['profiles'])
        actual=[a for a in self.result['audit'] if a['record_id']==row['id']];self.assertTrue(any(a['source_id']=='nzfc-facilities' for a in actual));self.assertEqual(row['capabilities'],[])
        # Benchmark names by themselves are insufficient: both must exist in real public data.
        self.assertNotIn('benchmarks',build_research.__code__.co_names)
        with patch('boutique.evaluate',side_effect=AssertionError('acquisition cannot call benchmark')):self.assertEqual(len(build_research(self.base)['proposed_references']),len(self.result['proposed_references']))
    def test_every_existing_id_and_source_shard_is_preserved(self):
        release=read(HOME/'release.json');self.assertEqual(sha(ROOT/'studios.json'),release['retained_baseline_sha256'])
        for name,expected in release['retained_shard_hashes'].items():self.assertEqual(sha(ROOT/'data/public'/name),expected)
        self.assertEqual({r['id'] for r in self.base}|{r['id'] for r in self.result['proposed_references']},{r['id'] for r in self.all})
    def test_new_references_cannot_grant_verified_capabilities_locations_or_ownership(self):
        rows=self.result['proposed_references'];self.assertEqual(validate_research(rows),[])
        for r in rows:self.assertEqual(r['evidence_class'],'C');self.assertIsNone(r['lat']);self.assertEqual(r['capabilities'],[]);self.assertEqual(r['relationships'],[])
        for p in self.result['profiles'].values():self.assertEqual(p['external_support_need'],'unknown');self.assertEqual(p['purchasing_intent'],'unknown');self.assertLessEqual(p['score'],100)
    def test_a_reviewed_source_identity_conflict_is_held_even_without_an_existing_match(self):
        observation=next(a for a in self.result['audit'] if a['source_id']=='nzfc-facilities' and a['name']=='Blockhead');self.assertEqual(observation['decision'],'identity_review');self.assertIsNone(observation['record_id']);self.assertIn('Assembly',observation['matching_reason']);self.assertFalse(any(r['name']=='Blockhead' for r in self.result['proposed_references']))
    def test_unresolved_reuse_links_belong_to_each_records_own_evidence(self):
        rows=[r for r in self.result['proposed_references'] if r['license']=='UNSPECIFIED'];self.assertEqual(len(rows),97)
        for r in rows:
            for p in r['source_provenance']:self.assertEqual(p['license_url'],p['url'])
    def test_taxonomy_only_leads_are_not_reported_as_primary_source_reviews(self):
        weak=[p for p in self.result['profiles'].values() if p['research_status']=='taxonomy_lead'];self.assertGreater(len(weak),1000);self.assertLess(self.result['summary']['source_supported_reference_profiles'],1000)
    def test_repeat_preparation_is_idempotent_without_duplicate_business_ids(self):
        again=build_research(self.base);self.assertEqual(self.result,again);ids=[r['id'] for r in again['proposed_references']];self.assertEqual(len(ids),len(set(ids)));self.assertEqual(self.result['summary']['publication_approved'],False)
    def test_benchmark_splits_are_separate_hash_bound_and_not_claimed_blind(self):
        dev=read(HOME/'benchmarks/development.json');held=read(HOME/'benchmarks/held-out.json');self.assertGreaterEqual(len(dev['records']),100);self.assertGreater(len(held['records']),0);self.assertFalse({r['domain'] for r in dev['records']}&{r['domain'] for r in held['records']})
        result=evaluate(self.result,self.all);self.assertEqual(result,read(HOME/'reports/benchmark-results.json'));self.assertIn('Not a blind',result['method']);self.assertFalse(result['approval_granted'])
        missing=evaluate({**self.result,'profiles':{}},[]);self.assertEqual(missing['splits']['development']['recall'],0)
    def test_source_observations_and_graph_are_audited_without_fabricated_relationships(self):
        for a in self.result['audit']:self.assertTrue(a['source_url'].startswith('https://'));self.assertEqual(len(a['observation_hash']),64);self.assertTrue(a['matching_reason'])
        self.assertTrue(self.result['graph']);self.assertTrue(all(e['type'] in ('source_co_listing','event_participation','official_company_reference') for e in self.result['graph']));self.assertTrue(all(e['to'].startswith('page:') for e in self.result['graph'] if e['type']=='official_company_reference'))
    def test_no_private_contact_or_authored_project_fields_are_projected(self):
        _,observations,_=source_inputs()
        for r in observations:self.assertFalse({'email','phone','contact','notable_projects','budget','sales_lead'}&set(r))
    def test_input_checkpoint_tampering_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            import shutil
            shutil.copytree(HOME,Path(tmp)/'home');h=Path(tmp)/'home';d=read(h/'inputs/primary-indexed.json');d['records'][0]['email']='private@example.test';(h/'inputs/primary-indexed.json').write_text(json.dumps(d))
            with self.assertRaisesRegex(ValueError,'private'):source_inputs(h)

class CollectorTests(unittest.TestCase):
    def test_robots_failure_stops_collection_without_false_closure_or_deletion(self):
        class Fetch:
            def response(self,*_):return b'User-agent: *\nDisallow: /', 'text/plain','utf-8'
        with tempfile.TemporaryDirectory() as tmp:
            r=collect('8178b6b5e6db6c5b6f25206359ec44037f6d11b3',Path(tmp)/'new',fetcher=Fetch());self.assertFalse(r['complete']);self.assertEqual(r['published_records'],0);self.assertEqual(r['closure_signals'],[]);self.assertIn('robots',r['error']['reason'])
    def test_network_error_retains_existing_snapshot(self):
        class Fetch:
            def response(self,*_):raise OSError('network unavailable')
        with tempfile.TemporaryDirectory() as tmp:
            prior=Path(tmp)/'old';prior.write_text('retained');r=collect('8178b6b5e6db6c5b6f25206359ec44037f6d11b3',Path(tmp)/'new',fetcher=Fetch());self.assertEqual(prior.read_text(),'retained');self.assertFalse(r['complete']);self.assertEqual(r['error']['type'],'OSError')
    def test_disabled_source_cannot_be_collected(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(ValueError,'policy'):collect('8178b6b5e6db6c5b6f25206359ec44037f6d11b3',Path(tmp)/'new',{'sources':[{'id':'animstudios-github','automatic_collection':False,'license':'CC-BY-4.0'}]})
    def test_a_new_revision_requires_licence_and_policy_review(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(ValueError,'unreviewed source revision'):collect('b'*40,Path(tmp)/'new')
    def test_projection_strips_contacts_and_raw_prose(self):
        raw={'generated':'2026-04-12','count':1,'studios':[{'name':'Example','website':'example.test','email':'private@example.test','notable_projects':'Authored prose','type':'studio','animation_types':'2D, 3D, VFX'}]};p=project(raw,'a'*40,'2026-11-07');self.assertNotIn('private@',json.dumps(p));self.assertNotIn('Authored prose',json.dumps(p));self.assertEqual(p['records'][0]['animation_types'],['2D','3D','VFX'])
        with self.assertRaises(ValueError):project({**raw,'count':2},'a'*40,'2026-11-07')
    def test_queries_are_plans_not_claimed_executed_or_seed_injected(self):
        plan=query_plan(read(HOME/'vocabulary.json'));self.assertGreater(len(plan),100);self.assertTrue(all(q['status']=='planned_not_executed' for q in plan));self.assertNotIn('Frame Machine',json.dumps(plan));self.assertNotIn('Floating Rock',json.dumps(plan))

if __name__=='__main__':unittest.main()
