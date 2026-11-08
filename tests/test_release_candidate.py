"""The integrated directory, independent of the standalone proposal reports."""
import copy,json,sys,tempfile,shutil,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
from discovery import read,digest,write
from launch_readiness import records
import release_candidate as rc

class ReleaseCandidateTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.manifest,cls.rows=records(ROOT/'data/public',ROOT/'studios.json');cls.report=rc.check();cls.cfg=read(rc.HOME/'inputs/parent-checkpoint.json');cls.new=cls.report['integrated_records'];cls.byid={r['id']:r for r in cls.rows}
 def test_integrated_subset_and_exact_original_records_are_preserved(self):
  self.assertEqual(len(self.new),182);self.assertEqual(len(self.rows),42478)
  for rid,h in self.cfg['record_hashes'].items():self.assertEqual(digest(self.byid[rid]),h)
  self.assertEqual(self.manifest['counts']['company_references'],1859);self.assertEqual(self.manifest['counts']['countries'],179)
  self.assertEqual({r['name'] for r in self.report['admissions'] if r['exact_public_fields'] is None},{'SIUNG FILM PRODUCTIONS SDN.BHD','VENTURA INTERACTIVE'})
 def test_taxonomy_preserves_source_labels_without_inventing_capabilities(self):
  byname={r['name']:r for r in self.new};self.assertIn('Animation',byname['a_BAHN']['categories']);self.assertIn('Animation production',json.loads(byname['a_BAHN']['source_category']));self.assertIn('Cinematics',byname['Mirayi']['categories']);self.assertNotIn('Rigging',byname['Mirayi']['capabilities']);self.assertIn('Game Development',byname['2Up Games']['categories'])
  for r in self.new:self.assertIsNone(r['lat']);self.assertIsNone(r['lng']);self.assertEqual(r['evidence_class'],'C');self.assertEqual(r['verified_on'],'');self.assertFalse(r['capabilities']);self.assertFalse(r['capability_evidence']);self.assertFalse(r['relationships']);self.assertFalse(r['research_review']['human_approved'])
 def test_source_listing_urls_are_not_misrepresented_as_corporate_sites(self):
  for r in self.new:
   if 'linkedin.com/' in r['website']:self.assertEqual(r['website_kind'],'source_listing')
   self.assertEqual(r['license'],'UNSPECIFIED');self.assertTrue(r['source_provenance']);self.assertIn('No authored source descriptions',r['attribution'])
 def test_admission_cannot_be_reapplied_or_fabricate_permission_or_approval(self):
  with self.assertRaisesRegex(ValueError,'fresh exact'):rc.apply_draft(ROOT/'data/public',ROOT/'studios.json')
  with tempfile.TemporaryDirectory() as tmp:
   home=Path(tmp);shutil.copytree(rc.HOME/'inputs',home/'inputs');bad=read(home/'inputs/admissions.json');bad['decisions'][0]['human_approved']=True;write(home/'inputs/admissions.json',bad)
   with self.assertRaisesRegex(ValueError,'approval'):rc.inputs(home)
 def test_any_original_field_change_is_rejected_before_draft_preparation(self):
  altered=copy.deepcopy(self.rows);altered[0]['city']='Invented correction'
  with patch('release_candidate.records',return_value=(self.manifest,altered)):
   with self.assertRaisesRegex(ValueError,'lost/changed'):rc.parent_rows(ROOT/'data/public',ROOT/'studios.json',self.cfg)
 def test_city_references_are_separate_and_all_seventeen_decisions_are_retained(self):
  v=read(ROOT/'data/public/visibility.json');old=read(rc.HOME/'inputs/parent-public/visibility.json');fid='boutique-5926fcc99b16ed8ea595dcf5459f';self.assertEqual(v['references'][fid],old['references'][fid]);self.assertEqual(len(self.report['geographic_decisions']),17);self.assertEqual(sum(g['release_disposition']=='prepare_separate_city_reference' for g in self.report['geographic_decisions']),7)
  mid='boutique-bd922ba2cd1dcd66361049c27ed0';self.assertEqual(self.byid[mid]['city'],'Adelaide');self.assertIsNone(self.byid[mid]['lat']);self.assertEqual(v['additional_references'][mid][0]['city'],'Brisbane');self.assertEqual(v['additional_references'][mid][0]['coordinate_license'],'CC-BY-4.0')
  frame=self.byid['overture-39fd34a0-9be1-4ac0-a46e-ebd53a1599ff'];self.assertEqual((frame['city'],frame['lat'],frame['lng']),('Santa Monica',34.02437092,-118.47703191))
 def test_nz_prerequisites_are_exception_focused_and_staged_cases_stay_staged(self):
  memo=self.report['nz_decision_memorandum'];self.assertEqual(len(memo['rows']),57);self.assertEqual(memo['company_only_references_recommended'],53);self.assertEqual({r['name'] for r in memo['separately_staged']},{'Melodics','Level'});self.assertEqual(sum(r['group']=='outside_motionx_scope' for r in memo['rows']),4);self.assertFalse(memo['human_approved'])
if __name__=='__main__':unittest.main()
