"""Research outcomes, append-only importing, explicit correction and publication gates."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from discovery import digest,prepare,read
from import_csv import plan_import
from validate import read_records,validate
from snapshots import before_v092,before_v093
FOLDER=ROOT/'data/research/v0.9.2-batch-1'


class VerifiedBatchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows=before_v093()
        cls.baseline=before_v092()
        cls.manifest=read(FOLDER/'evidence.json')
        cls.batch=read_records(FOLDER/'batch.csv')
        cls.decisions=read(FOLDER/'decisions.json')
        cls.queue=read(FOLDER/'queue.json')

    def test_all_candidates_have_explicit_sourced_outcomes(self):
        self.assertEqual(len(self.decisions),17)
        self.assertEqual({d['candidate_id'] for d in self.decisions},set(self.queue['candidates']))
        self.assertEqual(sum(d['decision']=='exclude' for d in self.decisions),4)
        self.assertEqual(sum(d['decision']=='defer' for d in self.decisions),2)
        self.assertTrue(all(d['sources'] and d['reason'] for d in self.decisions))
        self.assertFalse(any(r['company_id'] in ('red-storm','ubisoft-japan','ubisoft-brazil','ubisoft-northern-europe') for r in self.batch))

    def test_all_prior_records_except_explicit_correction_are_unchanged(self):
        self.assertEqual(digest(self.baseline),self.manifest['baseline_hash'])
        self.assertEqual(len(self.rows),141)
        self.assertEqual(len({r['company_id'] for r in self.rows}),77)
        self.assertEqual(len({r['country'] for r in self.rows}),30)
        changed=[a['id'] for a,b in zip(self.baseline,self.rows[:129]) if a!=b]
        self.assertEqual(changed,['audiomotion'])
        self.assertEqual(self.rows[129:],self.batch)

    def test_every_proposed_record_has_location_and_capability_evidence(self):
        records=read(FOLDER/'records.json')
        for record,evidence in zip(records,self.manifest['records']):
            self.assertEqual(record['id'],evidence['id'])
            self.assertIn(record['evidence'],evidence['location_sources'])
            self.assertEqual(record['capability_evidence'],evidence['capability_evidence'])
            self.assertEqual(record['relationships'],evidence['relationships'])
            self.assertEqual(record['verified_on'],'2026-11-06')
            self.assertTrue(all(v['state']=='confirmed' and v['evidence'] for v in record['capability_evidence'].values()))
            self.assertFalse(record['email'] or record['phone'])
        self.assertFalse(validate(records)[0])

    def test_legitimate_duplicates_require_visible_review_and_repeat_import_is_safe(self):
        _,blocked=plan_import(self.baseline,self.batch)
        self.assertEqual({d['id'] for d in blocked['potential_duplicates']},{'ubisoft-barcelona-mobile-main','studiot3d-london-stage-2'})
        allowed=['ubisoft-barcelona-mobile-main','studiot3d-london-stage-2']
        combined,preview=plan_import(self.baseline,self.batch,allowed)
        self.assertEqual(len(preview['new_records']),12)
        self.assertTrue(all(d['allowed_as_distinct'] for d in preview['potential_duplicates']))
        repeated,report=plan_import(combined,self.batch)
        self.assertEqual(combined,repeated)
        self.assertFalse(report['new_records'])
        self.assertEqual(len(report['unchanged_records']),12)

    def test_audiomotion_correction_reuses_identity_and_preserves_before_record(self):
        update=read(FOLDER/'updates.json')[0]
        self.assertEqual(update['previous_record_hash'],digest(update['before']))
        current=next(r for r in self.rows if r['id']=='audiomotion')
        self.assertEqual(current,update['after'])
        self.assertEqual(current['company_id'],update['before']['company_id'])
        self.assertEqual(current['city'],'Didcot')
        self.assertEqual(current['legacy_research'],update['before']['legacy_research'])
        self.assertEqual(sum(r['id']=='audiomotion' for r in self.rows),1)

    def test_site_specific_capture_does_not_spread_to_game_studios_or_other_stages(self):
        one=next(r for r in self.batch if r['id']=='studiot3d-london-stage-1')
        two=next(r for r in self.batch if r['id']=='studiot3d-london-stage-2')
        self.assertEqual((one['lat'],one['lng']),(two['lat'],two['lng']))
        self.assertEqual(two['capabilities'],['Motion Capture','Volumetric Capture'])
        self.assertIn('Virtual Production',one['capabilities'])
        games=[r for r in self.batch if r['company_id']!='studiot3d']
        self.assertEqual(len(games),10)
        self.assertTrue(all(r['capabilities']==['Game Development'] for r in games))

    def test_coordinates_and_market_municipalities_are_explicit(self):
        refs=read(FOLDER/'city-references.json')['references']
        for row in self.batch:
            self.assertNotEqual(row['coordinate_precision'],'exact')
            reference=next(r for r in refs.values() if r['source']==row['coordinate_source'])
            self.assertEqual((row['lat'],row['lng']),(reference['lat'],reference['lng']))
        by_id={r['id']:r for r in self.batch}
        self.assertEqual(by_id['ivory-tower-villeurbanne']['city'],'Villeurbanne')
        self.assertEqual(by_id['ubisoft-milan-assago']['city'],'Assago')
        self.assertEqual(by_id['ubisoft-montpellier-main']['city'],'Castelnau-le-Lez')
        self.assertEqual(by_id['ubisoft-montpellier-main']['coordinate_precision'],'region')
        self.assertIn('urban-area',by_id['ubisoft-montpellier-main']['status'])

    def test_pending_human_review_gate_cannot_prepare_or_publish(self):
        reviews=read(FOLDER/'reviews.json')
        self.assertTrue(all(r['decision']=='pending' and not r['reviewed_by'] and not any(r['checks'].values()) for r in reviews))
        with self.assertRaisesRegex(ValueError,'explicit named approval'):
            prepare(self.baseline,self.queue,read(FOLDER/'records.json'),reviews)
        with tempfile.TemporaryDirectory() as folder:
            baseline=Path(folder)/'baseline.json';baseline.write_text(json.dumps(self.baseline))
            result=subprocess.run([sys.executable,str(ROOT/'tools/discovery.py'),'prepare','--database',str(baseline),
                '--queue',str(FOLDER/'queue.json'),'--records',str(FOLDER/'records.json'),'--reviews',str(FOLDER/'reviews.json'),'--output',str(Path(folder)/'proposal')],capture_output=True,text=True)
            self.assertNotEqual(result.returncode,0)
            self.assertFalse((Path(folder)/'proposal/studios.json').exists())

    def test_live_refresh_preserves_queue_history_and_never_fetches_ea(self):
        refresh=read(FOLDER/'discovery-refresh.json')
        self.assertEqual(len(refresh['sources']),5)
        self.assertTrue(all(s['id']!='ea-studios' and s['status']=='ok' for s in refresh['sources']))
        self.assertEqual(next(s['candidate_count'] for s in refresh['sources'] if s['id']=='cinesite-group'),7)
        self.assertEqual(refresh['retained'],133)
        self.assertEqual(refresh['history_snapshots'],2)
        self.assertEqual(len(self.queue['candidates']),17)


if __name__=='__main__':unittest.main()
