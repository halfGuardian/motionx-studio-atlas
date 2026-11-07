import copy,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
from discovery import read,digest
from launch_readiness import records
from global_continuation import HOME,build,check,classify,validate_reviews,proposed_record,validate_backlog
from unified_catalog import validate_research

class ContinuationTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.manifest,cls.rows=records(ROOT/'data/public',ROOT/'studios.json');cls.policy,cls.report=build(cls.rows);cls.input=read(HOME/'inputs/company-reviews.json');cls.backlog=read(HOME/'inputs/backlog.json')
 def test_frozen_canonical_records_and_all_pending_history_survive(self):
  self.assertEqual(check()['canonical_records_after'],42296);self.assertEqual(len(self.report['backlog']),725);self.assertEqual(self.report['summary']['backlog_observations_preserved'],753);self.assertFalse(any(r['canonical_approved'] for r in self.report['reviews']))
 def test_real_proposals_are_valid_class_c_without_capabilities_or_coordinates(self):
  self.assertGreater(len(self.report['proposals']),0);self.assertEqual(validate_research(self.report['proposals']),[])
  for r in self.report['proposals']:
   self.assertEqual(r['evidence_class'],'C');self.assertIsNone(r['lat']);self.assertIsNone(r['lng']);self.assertFalse(r['capabilities']);self.assertFalse(r['relationships']);self.assertEqual(r['verified_on'],'');self.assertTrue(r['source_provenance'])
 def test_matched_or_uncertain_identities_never_become_duplicate_company_proposals(self):
  for r in self.report['reviews']:
   if r['matching']['record_ids']:self.assertIsNone(r['proposal_id'])
 def test_composite_exhibitor_identity_is_held_even_when_no_canonical_name_matches(self):
  r=next(r for r in self.report['reviews'] if r['name']=='MAKIA CREATIVE / MAMONCILLO');self.assertEqual(r['disposition'],'identity_review');self.assertIsNone(r['proposal_id'])
 def test_backlog_cannot_lose_original_observations_or_claim_human_approval(self):
  checkpoint=read(HOME/'inputs/checkpoint.json')
  for field,value in [('observation_ids',[]),('source_urls',[]),('human_approved',True)]:
   bad=copy.deepcopy(self.backlog);bad['candidates'][0][field]=value
   with self.assertRaises(ValueError):validate_backlog(bad,checkpoint)
 def test_game_development_is_client_eligibility_without_capture_inference(self):
  r={'id':'fixture','categories':['Game Development'],'capabilities':[]};before=copy.deepcopy(r);a=classify(r,self.policy);self.assertEqual(a['role'],'potential_client');self.assertFalse(a['excluded']);self.assertEqual(r,before)
 def test_four_audio_only_exclusions_retain_multidisciplinary_envy(self):
  impact=self.report['scope_impact'];self.assertEqual(sum(r['excluded'] for r in impact),4);self.assertFalse(next(r for r in impact if r['name']=='Envy Studios')['excluded']);self.assertTrue(all(r['audit_mode_visible'] for r in impact));self.assertEqual(self.report['summary']['map_markers_changed'],0)
  effect=self.report['filter_impact'];self.assertEqual(effect['game_development_sector']['before'],effect['game_development_sector']['after']);self.assertEqual(effect['audio_post_sector'],{'before':5,'after':1});self.assertEqual(effect['original_coordinate_records']['before'],effect['original_coordinate_records']['after'])
 def test_a_sound_name_does_not_establish_audio_only_services(self):
  self.assertFalse(classify({'id':'fixture','name':'Sound Games','categories':['Game Development']},self.policy)['excluded'])
 def test_review_cannot_fabricate_approval_verified_facility_or_automatic_permission(self):
  for field,value in [('human_approved',True),('facility_verified',True),('automatic_collection',True),('rights','bulk_scraping_granted'),('independent_review','AI Reviewer')]:
   bad=copy.deepcopy(self.input);bad['reviews'][0][field]=value
   with self.assertRaises(ValueError):validate_reviews(bad,self.backlog,self.rows)
 def test_missing_duplicate_and_unsafe_reviews_are_rejected(self):
  bad=copy.deepcopy(self.input);bad['reviews'].append(bad['reviews'][0])
  with self.assertRaises(ValueError):validate_reviews(bad,self.backlog,self.rows)
  bad=copy.deepcopy(self.input);bad['reviews'][0]['evidence'][0]['url']='javascript:alert(1)'
  with self.assertRaises(ValueError):validate_reviews(bad,self.backlog,self.rows)
 def test_exact_geographic_correction_never_changes_original_city_or_pin(self):
  p=next(p for p in self.report['geography_proposals'] if p['name']=='Tumblehead');self.assertEqual(p['before']['city'],'Copenhagen');self.assertEqual(p['proposed_company_city'],'Viborg');self.assertIsNone(p['coordinate']);self.assertFalse(p['original_coordinates_changed'])
 def test_additional_city_points_have_licensed_provenance_and_remain_proposals(self):
  points=[p for p in self.report['geography_proposals'] if p['coordinate']];self.assertGreater(len(points),0)
  for p in points:self.assertEqual(p['coordinate']['precision'],'city');self.assertEqual(p['coordinate']['coordinate_license'],'CC-BY-4.0');self.assertFalse(p['human_approved']);self.assertIsNone(p['before']['lat'])
 def test_company_ids_survive_website_and_brand_corrections(self):
  r=next(r for r in self.input['reviews'] if r['operation_evidence']=='primary_self_report' and r['candidate_id']);a=proposed_record(r);other=copy.deepcopy(r);other['official_name']='Corrected brand';other['official_website']='https://example.com/';b=proposed_record(other);self.assertEqual((a['id'],a['company_id']),(b['id'],b['company_id']))
 def test_access_failure_is_unresolved_not_closure_and_metrics_remain_unlabeled(self):
  for r in self.report['reviews']:
   if r['operation_evidence']=='access_unavailable':self.assertIsNone(r['proposal_id']);self.assertNotIn('closed',r['disposition'])
  self.assertIsNone(self.report['summary']['independent_precision']);self.assertIsNone(self.report['summary']['independent_recall'])
if __name__=='__main__':unittest.main()
