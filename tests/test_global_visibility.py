import copy,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
from global_visibility import check,build,DISPOSITIONS
from catalogue_history import records
from discovery import read,digest
class GlobalVisibilityTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.manifest,cls.rows=records(ROOT/'data/public',ROOT/'studios.json');cls.value,cls.audit=build(cls.rows)
 def test_every_1677_company_reference_has_an_accountable_geographic_disposition(self):
  self.assertEqual(len(self.audit),1677);self.assertEqual(len({r['record_id'] for r in self.audit}),1677);self.assertTrue(all(r['disposition'] in DISPOSITIONS and r['reason'] for r in self.audit));self.assertFalse(any(r['facility_verified'] or r['human_approved'] for r in self.audit))
 def test_complete_parent_records_and_historical_files_are_unchanged(self):self.assertEqual(check()['summary']['original_record_coordinates_changed'],0)
 def test_floating_rock_city_reference_does_not_populate_original_company_coordinates(self):
  r=next(r for r in self.rows if r['id']=='boutique-5926fcc99b16ed8ea595dcf5459f');self.assertIsNone(r['lat']);p=self.value['references'][r['id']];self.assertEqual(p['precision'],'city');self.assertEqual(p['city'],'Wellington');self.assertEqual(p['evidence_class'],'C');self.assertFalse(p['facility_verified'])
 def test_frame_machine_is_a_source_observation_not_a_new_company_or_verified_facility(self):
  r=next(r for r in self.rows if r['name']=='Frame Machine');self.assertEqual(r['record_kind'],'source_location');self.assertEqual(r['evidence_class'],'C');self.assertNotIn(r['id'],self.value['references']);self.assertEqual((r['lat'],r['lng']),(34.02437092,-118.47703191))
if __name__=='__main__':unittest.main()
