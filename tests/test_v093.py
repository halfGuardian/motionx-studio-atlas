"""Release audit: old records, explicit correction, evidence scope and import repeatability."""
import copy,json
from pathlib import Path
import sys,unittest
from unittest.mock import patch
from datetime import date
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from discovery import read,digest
from validate import read_records,validate
from import_csv import plan_import
from research import stage,dossier,review_html
from snapshots import before_v093,before_v10
P=ROOT/'data/research/v0.9.3-global'

class BatchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base=before_v093();cls.current=before_v10();cls.records=read(P/'records.json');cls.batch=read_records(P/'batch.csv');cls.manifest=read(P/'evidence.json')

    def test_totals_preserve_baseline_and_exact_explicit_update(self):
        self.assertEqual(digest(self.base),self.manifest['baseline_hash'])
        self.assertEqual(len(self.current),182)
        self.assertEqual(len({r['company_id'] for r in self.current}),88)
        self.assertEqual(len({r['country'] for r in self.current}),32)
        self.assertEqual(self.current[141:],self.batch)
        changed=[a['id'] for a,b in zip(self.base,self.current) if a!=b]
        self.assertEqual(changed,['centroid-uxbridge'])
        old=next(r for r in self.base if r['id']==changed[0]);new=next(r for r in self.current if r['id']==changed[0])
        self.assertEqual((old['lat'],old['lng']),(new['lat'],new['lng']))
        self.assertEqual(new,read(P/'updates.json')[0]['after'])
        self.assertEqual(old,read(P/'updates.json')[0]['before'])

    def test_manifest_binds_every_location_capability_and_coordinate(self):
        m={r['id']:r for r in self.manifest['records']}
        self.assertEqual(set(m),{r['id'] for r in self.records})
        for r in self.records:
            evidence=m[r['id']]
            self.assertEqual(evidence['record_hash'],digest(r))
            self.assertIn(r['evidence'],evidence['location_sources'])
            self.assertEqual(r['capability_evidence'],evidence['capability_evidence'])
            self.assertFalse(r['email'] or r['phone'])
            self.assertEqual(r['coordinate_precision'],'city')
            self.assertEqual(r['verified_on'],self.manifest['reviewed_on'])
            if 'coordinate_reference' in evidence:
                ref=evidence['coordinate_reference'];self.assertEqual((r['lat'],r['lng'],r['coordinate_source']),(ref['lat'],ref['lng'],ref['source']))
        self.assertEqual(validate(self.current)[0],[])
        self.assertEqual(len(validate(self.current)[1]),201)

    def test_safe_import_flags_distinct_stage_and_repeat_changes_nothing(self):
        _,report=plan_import(self.base,self.batch)
        self.assertEqual([d['id'] for d in report['potential_duplicates']],['annapurna-anr-vp-hyderabad'])
        combined,report=plan_import(self.base,self.batch,['annapurna-anr-vp-hyderabad'])
        self.assertEqual(len(report['new_records']),41)
        again,repeat=plan_import(combined,self.batch)
        self.assertEqual(again,combined);self.assertEqual(len(repeat['unchanged_records']),41)
        self.assertFalse(repeat['new_records'] or repeat['rejected_records'])

    def test_replay_staging_matches_branch_without_claiming_human_approval(self):
        class ReviewedDate(date):
            @classmethod
            def today(cls):return cls(2026,11,6)
        with patch('research.date',ReviewedDate):
            result,audit=stage(self.base,self.records,self.manifest,['annapurna-anr-vp-hyderabad'])
        self.assertEqual(result,self.current)
        self.assertEqual(audit['approved_claims'],0);self.assertFalse(audit['main_written'])
        self.assertEqual(len(audit['record_changes']),42)

    def test_capture_claims_are_site_specific_and_same_site_facilities_remain_separate(self):
        captured=[r for r in self.batch if 'Motion Capture' in r['capabilities']]
        self.assertEqual({r['id'] for r in captured},{'larian-kuala-lumpur','annapurna-am-mocap-hyderabad'})
        self.assertEqual(sum(r['company_id']=='larian' for r in self.batch),7)
        lab=next(r for r in self.batch if r['id']=='annapurna-am-mocap-hyderabad')
        vp=next(r for r in self.batch if r['id']=='annapurna-anr-vp-hyderabad')
        self.assertNotEqual(lab['evidence'],vp['evidence'])
        self.assertEqual((lab['lat'],lab['lng']),(vp['lat'],vp['lng']))
        self.assertNotIn('Motion Capture',vp['capabilities']);self.assertNotIn('Virtual Production',lab['capabilities'])
        self.assertEqual(next(r for r in self.batch if r['id']=='massive-stockholm')['company_id'],'massive-entertainment')
        self.assertEqual(next(r for r in self.batch if r['id']=='flying-bark-burbank')['city'],'Burbank')
        self.assertEqual(next(r for r in self.batch if r['id']=='folks-burbank')['city'],'Burbank')

if __name__=='__main__':unittest.main()
