"""One inclusive research workspace; no dropped companies or fabricated pins."""
import csv,json,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
from discovery import write,read,digest
from unified_catalog import build,validate_research
from test_bulk import place,policy

class UnifiedTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
        self.base=[read(ROOT/'studios.json')[0]];write(self.root/'base.json',self.base)
        self.config={'sources':[policy()]};write(self.root/'config.json',self.config)
        self.records=[place('one'),place('two',name='Needs Research',confidence=.5)]
        p=self.root/'snapshot/overture';write(p/'places-00000.json',self.records);write(p/'places-00000.meta.json',{'source':'overture','license':'per-provider','observed_on':'2026-11-06','projection_hash':digest(self.records)})
        write(p/'category-inventory.json',[{'count':2,'selected_for_research':True}]);write(self.root/'snapshot/overture-collection.json',{'complete':True})
        with (self.root/'companies.csv').open('w',newline='') as f:
            w=csv.DictWriter(f,fieldnames=['Name','Type','Country','Website','Status','Description']);w.writeheader();w.writerow({'Name':'Company Without Address','Type':'Studio','Country':'Canada','Website':'https://company.example.test','Status':'Closed','Description':'Authored source prose must not be copied.'})
    def build(self,suffix='one'):
        with patch('builtins.print'):
            return build(self.root/'snapshot',self.root/'companies.csv',self.root/suffix,self.root/'base.json',self.root/'config.json',observed='2026-11-06')
    def test_all_quality_classes_and_company_reference_share_one_index(self):
        m,rows=self.build();self.assertEqual(m['counts']['records'],4);self.assertEqual(m['counts']['source_location_observations'],2);self.assertEqual(m['counts']['company_references'],1)
        self.assertEqual(len(read(self.root/'one/index.json')),3);self.assertTrue(any(r['evidence_class']=='C' and r['record_kind']=='source_location' for r in rows))
        self.assertEqual(read(self.root/'base.json'),self.base);self.assertEqual(m['baseline']['active_ids'],[r['id'] for r in self.base]);self.assertEqual(m['baseline']['research_only_ids'],[])
    def test_company_never_becomes_a_physical_facility_or_verified_claim(self):
        _,rows=self.build();r=next(r for r in rows if r['record_kind']=='company_reference')
        self.assertIsNone(r['lat']);self.assertIsNone(r['lng']);self.assertEqual(r['city'],'');self.assertEqual(r['evidence_class'],'C');self.assertEqual(r['capabilities'],[])
        self.assertEqual(r['source_status'],'Closed');self.assertEqual(r['evidence_state'],'unknown');self.assertNotIn('Authored source prose',json.dumps(rows));self.assertEqual(r['license'],'UNSPECIFIED')
        self.assertEqual(validate_research(rows),[])
        self.assertTrue(validate_research([{**r,'lat':1.,'lng':2.}]))
        self.assertTrue(validate_research([{**r,'capabilities':['Motion Capture']}]))
    def test_repeat_build_is_idempotent_and_original_points_are_unchanged(self):
        m,rows=self.build();second,_=self.build('two')
        self.assertEqual(m,second);self.assertEqual(read(self.root/'one/index.json'),read(self.root/'two/index.json'))
        point=next(r for r in rows if r['record_kind']=='source_location');self.assertEqual((point['lat'],point['lng']),(20,10))
    def test_incomplete_source_snapshot_cannot_be_misrepresented_as_complete(self):
        write(self.root/'snapshot/overture-collection.json',{'complete':False})
        with self.assertRaisesRegex(ValueError,'complete source'):self.build()

if __name__=='__main__':unittest.main()
