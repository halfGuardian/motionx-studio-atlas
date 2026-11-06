"""v0.8 provenance, optional metadata and full-batch import regressions."""
import copy
import csv
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from validate import read_records, validate, CSV_FIELDS
from import_csv import plan_import

FOLDER = ROOT / 'data/research/v0.8-global-expansion'


class ExpansionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows = read_records(ROOT / 'studios.json')
        cls.batch = read_records(FOLDER / 'batch.csv')
        cls.manifest = json.loads((FOLDER / 'evidence.json').read_text())

    def test_original_records_and_coordinates_are_unchanged(self):
        seed = self.rows[:31]
        digest = hashlib.sha256(json.dumps(seed, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
        self.assertEqual(digest, self.manifest['baseline_digest'])
        self.assertEqual(self.rows[31:], self.batch)
        self.assertEqual(len(self.batch), 98)

    def test_organisation_and_geographic_totals(self):
        self.assertEqual(len(self.rows), 129)
        self.assertEqual(len({r['company_id'] for r in self.rows}), 66)
        self.assertEqual(len({r['company_id'] for r in self.batch} - {r['company_id'] for r in self.rows[:31]}), 47)
        self.assertEqual(len({r['country'] for r in self.batch}), 26)

    def test_every_location_has_evidence_and_appropriate_metadata(self):
        by_id = {r['id']: r for r in self.manifest['records']}
        self.assertEqual(set(by_id), {r['id'] for r in self.batch})
        for row in self.batch:
            m = by_id[row['id']]
            self.assertIn(row['evidence'], m['location_sources'])
            self.assertEqual(row['capability_evidence'], m['capability_sources'])
            self.assertEqual(row['relationships'], m['relationships'])
            self.assertEqual(row['coordinate_source'], m['coordinate_reference']['source'])
            self.assertEqual((row['lat'], row['lng']), (m['coordinate_reference']['lat'], m['coordinate_reference']['lng']))
            self.assertEqual(row['coordinate_precision'], 'city')
            self.assertEqual(row['email'], '')
            self.assertEqual(row['phone'], '')
            self.assertEqual(row['verified_on'], self.manifest['reviewed_on'])
            self.assertFalse(m['duplicate_candidates'])

    def test_separate_capture_stages_not_merged(self):
        stages = [r for r in self.batch if r['company_id'] == 'imaginarium']
        self.assertEqual(len(stages), 2)
        self.assertEqual({r['city'] for r in stages}, {'Iver Heath', 'London'})
        self.assertTrue(all(r['location_type'] == 'capture_facility' for r in stages))
        capture = [r for r in self.batch if any(c in r['capabilities'] for c in ['Motion Capture','Facial Capture','Performance Capture'])]
        self.assertEqual(len(capture), 6)
        self.assertTrue(all(r['capability_evidence'][c]['evidence'] for r in capture for c in r['capabilities']))

    def test_import_preview_and_repeat_are_safe(self):
        combined, preview = plan_import(self.rows[:31], self.batch)
        self.assertEqual(combined, self.rows)
        self.assertEqual(len(preview['new_records']), 98)
        self.assertFalse(preview['potential_duplicates'])
        self.assertFalse(preview['database_errors'])
        repeated, report = plan_import(combined, self.batch)
        self.assertEqual(repeated, combined)
        self.assertEqual(len(report['unchanged_records']), 98)
        self.assertFalse(report['new_records'])

    def test_deferred_and_rejected_candidates_are_not_published(self):
        queue = json.loads((FOLDER / 'review-queue.json').read_text())
        self.assertTrue(any(r['candidate'] == 'BioWare Edmonton' and r['decision'] == 'reject' for r in queue))
        self.assertTrue(any(r['candidate'] == 'Montréal' and r['organisation'].startswith('Eyeline') for r in queue))
        self.assertFalse(any(r['company_id'] == 'bioware' for r in self.batch))
        self.assertTrue(all(r['reason'] and r['sources'] for r in queue))


class MetadataTests(unittest.TestCase):
    def setUp(self):
        self.row = copy.deepcopy(read_records(FOLDER / 'batch.csv')[0])
        self.row['relationships'] = [{'id':'test-parent','name':'Test Parent','type':'group_member','evidence':'https://example.org/source','verified_on':'2026-01-01'}]

    def test_old_schema_still_valid(self):
        for key in ('relationships', 'coordinate_source', 'location_type'):
            self.row.pop(key, None)
        self.assertFalse(validate([self.row])[0])

    def test_optional_metadata_validation(self):
        self.assertFalse(validate([self.row])[0])
        for key, value in [('location_type','head-office-as-studio'),('coordinate_source','javascript:alert(1)'),('relationships',{})]:
            with self.subTest(key=key):
                row = copy.deepcopy(self.row); row[key] = value
                self.assertTrue(validate([row])[0])

    def test_sourced_relationships_and_review_dates_required(self):
        for key, value in [('id',self.row['company_id']),('type','owned-probably'),('evidence',''),('verified_on','2026-02-30'),('name','')]:
            with self.subTest(key=key):
                row=copy.deepcopy(self.row); row['relationships'][0][key]=value
                self.assertTrue(validate([row])[0])
        row=copy.deepcopy(self.row); row['relationships']*=2
        self.assertTrue(validate([row])[0])

    def test_csv_metadata_roundtrip_and_import_idempotency(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'batch.csv'; database=Path(folder)/'studios.json'
            database.write_text('[]\n')
            row=copy.deepcopy(self.row)
            for key in ('categories','capabilities'):row[key]='|'.join(row[key])
            for key in ('capability_evidence','relationships'):row[key]=json.dumps(row[key])
            with path.open('w',newline='') as stream:
                writer=csv.DictWriter(stream,fieldnames=CSV_FIELDS);writer.writeheader();writer.writerow(row)
            self.assertEqual(read_records(path),[self.row])
            args=[sys.executable,str(ROOT/'tools/import_csv.py'),str(path),'--database',str(database),'--apply']
            result=subprocess.run(args,capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stdout)
            before=database.read_bytes()
            result=subprocess.run(args,capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stdout)
            self.assertFalse(json.loads(result.stdout)['written'])
            self.assertEqual(database.read_bytes(),before)


if __name__ == '__main__':
    unittest.main()
