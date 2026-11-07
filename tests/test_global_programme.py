import copy,csv,gzip,json,sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from global_programme import load_snapshot,advance,empty_state,check_state,GlobalIndex,reconcile,HOME,OUTCOMES
from discovery import digest

class GlobalProgrammeTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.path=Path(self.tmp.name)/'snapshot.json'
        self.policy={'source_id':'test','mode':'reviewed_dataset_replay','reuse_decision':'scoped_dataset_permission','license':'CC0-1.0','license_url':'https://example.org/licence','attribution':'Synthetic test source only','reviewed_on':'2026-11-07','human_approved':False}
        self.row={'source_record_id':'a','name':'Test Boutique','website':'https://boutique.example.org/','country':'New Zealand','city':'Wellington','source_url':'https://source.example.org/a','observed_on':'2026-11-07','service_claims':['Animation','motion capture company claim']}
        self.value={'version':1,'source_id':'test','snapshot_id':'one','observed_on':'2026-11-07','status':'success','complete':True,'expected_records':1,'source_url':'https://source.example.org/','license':'CC0-1.0','records':[self.row],'enumeration_scope':'all supplied animation company rows'}

    def load(self,value=None,policy=None):
        self.path.write_text(json.dumps(value or self.value));return load_snapshot(self.path,policy or self.policy)

    def test_permission_gated_csv_json_and_private_fields(self):
        self.assertEqual(len(self.load()['records']),1)
        for patch in ({'reuse_decision':'permission_pending'},{'mode':'unrestricted_crawl'},{'permission_expires_on':'2026-01-01'}):
            with self.subTest(patch=patch),self.assertRaises(ValueError):self.load(policy=self.policy|patch)
        value=copy.deepcopy(self.value);value['records'][0]['email']='person@example.org'
        with self.assertRaises(ValueError):self.load(value)
        csv_path=self.path.with_suffix('.csv')
        with csv_path.open('w',newline='') as f:
            row=self.row|{'service_claims':json.dumps(self.row['service_claims'])};writer=csv.DictWriter(f,fieldnames=list(row));writer.writeheader();writer.writerow(row)
        self.assertEqual(load_snapshot(csv_path,self.policy,{k:v for k,v in self.value.items() if k!='records'})['records'][0],self.load()['records'][0])

    def test_failed_fetch_and_incomplete_history_never_infer_closure(self):
        state,_=advance(empty_state(),self.load());before=copy.deepcopy(state)
        failed=self.value|{'snapshot_id':'failed','status':'failed','complete':False,'expected_records':None,'records':[],'failure':'robots unavailable; collection stopped'}
        state,signals=advance(state,self.load(failed));self.assertEqual(before['sources']['test']['records'][0]['name'],'Test Boutique');self.assertEqual(state['history'][0]['snapshot']['records'],before['sources']['test']['records']);self.assertTrue(all(not s.get('closure_inference') for s in signals))
        partial=self.value|{'snapshot_id':'partial','status':'partial','complete':False,'expected_records':None,'records':[]}
        state,signals=advance(state,self.load(partial));self.assertIn('history_incomplete_no_absence_inference',[s['kind'] for s in signals]);self.assertNotIn('source_absence_investigation',[s['kind'] for s in signals]);self.assertEqual(state['canonical_updates'],[])

    def test_repeat_import_changes_and_complete_absence_are_review_signals_only(self):
        snapshot=self.load();state,signals=advance(empty_state(),snapshot);same,signals=advance(state,snapshot);self.assertEqual(state,same);self.assertEqual(signals,[])
        changed=copy.deepcopy(self.value);changed['snapshot_id']='two';changed['records'][0]['name']='Renamed Boutique';changed['records'][0]['city']='Auckland';new,signals=advance(state,self.load(changed));self.assertEqual(signals[0]['kind'],'possible_identity_geography_service_change');self.assertIn('city',signals[0]['changed_fields']);self.assertEqual(new['history'][0]['snapshot']['records'][0]['name'],'Test Boutique')
        empty=self.value|{'snapshot_id':'three','records':[],'expected_records':0};end,signals=advance(new,self.load(empty));self.assertEqual(signals[0]['kind'],'source_absence_investigation');self.assertFalse(signals[0]['closure_inference']);self.assertFalse(end['human_approved'])
        with self.assertRaises(ValueError):advance(state,self.load(changed|{'snapshot_id':'one'}))

    def test_corrupted_missing_snapshot_history_is_detected(self):
        state,_=advance(empty_state(),self.load())
        for mutate in ('history','head','embedded'):
            broken=copy.deepcopy(state)
            if mutate=='history':broken['history']=[]
            elif mutate=='head':broken['sources']['test']['records']=[]
            else:broken['history'][0]['snapshot']['records']=[]
            with self.subTest(mutate=mutate),self.assertRaises(ValueError):check_state(broken)

    def test_partial_counts_duplicate_ids_unsafe_urls_and_stale_claims(self):
        for patch in ({'expected_records':2},{'records':[self.row,self.row]},{'records':[self.row|{'website':'javascript:alert(1)'}]}):
            with self.subTest(patch=patch),self.assertRaises(ValueError):self.load(self.value|patch)
        stale=copy.deepcopy(self.value);stale['records'][0]['source_updated_on']='2020-01-01';_,signals=advance(empty_state(),self.load(stale));self.assertIn('stale_source_assertion',[s['kind'] for s in signals])

    def test_identity_does_not_merge_foreign_branches_shared_domains_or_capabilities(self):
        row={'id':'existing','company_id':'org','name':'Test Boutique','country':'Canada','city':'Toronto','website':'https://boutique.example.org/','record_kind':'company_reference','source_provenance':[]}
        index=GlobalIndex([row]);observation=self.row|{'source_id':'test','origin':'test','origin_hash':digest(self.row)}
        match,state=index.resolve(observation);self.assertEqual(state,'company_geography_pending');self.assertEqual(match['record_ids'],['existing'])
        out=reconcile([row],[observation,observation|{'origin_hash':'b'*64}],'2026-11-07');self.assertEqual(out[1]['disposition'],'duplicate_observation');self.assertIsNone(out[0]['geographic_evidence']['coordinate_proposal']);self.assertEqual(out[0]['service_evidence']['facility_confirmed_capabilities'],[]);self.assertIsNone(out[0]['canonical_update'])
        # Same domain and country with distinct operating identities remains conflict.
        _,state=GlobalIndex([row|{'name':'Another Brand','country':'New Zealand'}]).resolve(observation);self.assertEqual(state,'identity_conflict')

    def test_actual_global_denominators_and_all_pending_approvals(self):
        with gzip.open(HOME/'reports/global-report.json.gz','rt') as f:report=json.load(f)
        self.assertEqual(len(report['countries']),178);self.assertEqual(report['summary']['catalogue_records'],42296);self.assertEqual(sum(report['summary']['outcomes'].values()),len(report['observations']));self.assertEqual(len({o['observation_id'] for o in report['observations']}),len(report['observations']));self.assertTrue(all(o['disposition'] in OUTCOMES and not o['human_approved'] and o['canonical_update'] is None for o in report['observations']));self.assertEqual(report['summary']['company_geography']['company_only_records'],1677)
        self.assertTrue(all(not s['automatic_collection'] and not s['fully_enumerated'] for s in report['source_assessments']));self.assertIsNone(report['summary']['human_recall']);self.assertFalse(report['summary']['global_complete'])

    def test_source_key_collision_cannot_silently_rebrand_an_existing_company(self):
        row={'id':'old','company_id':'old-org','name':'Original Studio','website':'https://old.example.org/','country':'Canada','source_provenance':[{'source_id':'test','source_record_id':'a'}]}
        match,outcome=GlobalIndex([row]).resolve(self.row|{'source_id':'test'});self.assertEqual(outcome,'identity_conflict');self.assertEqual(match['record_ids'],['old'])

    def test_heldout_sample_retains_unmatched_denominator_and_no_ai_ground_truth(self):
        report=json.loads((HOME/'reports/heldout-review.json').read_text());self.assertEqual(report['denominator'],14);self.assertEqual(report['model_match_candidates']+report['model_unmatched'],14);self.assertIsNone(report['human_precision']);self.assertIsNone(report['human_recall']);self.assertEqual(report['independent_labels'],0);self.assertFalse(report['blind_independent_business_benchmark']);self.assertTrue(all(s['independent_company_label'] is None and not s['human_approved'] for s in report['samples']))

    def test_historical_discovery_navigation_and_topics_do_not_become_new_companies(self):
        report=json.load(gzip.open(HOME/'reports/global-report.json.gz','rt'));history=[o for o in report['observations'] if o['origin']=='retained_discovery_checkpoint'];self.assertEqual(len(history),430);self.assertTrue(all(o['disposition']!='potential_new_company' for o in history));self.assertTrue(any(o['disposition']=='out_of_scope' for o in history));self.assertTrue(all(o['original_candidate_sha256'] and not o['closure_inference'] for o in history));self.assertEqual(report['summary']['historical_files_retained'],209)

if __name__=='__main__':unittest.main()
