"""Offline validation/import tests; synthetic fixtures never enter production data."""
import copy
import csv
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from validate import REQUIRED, possible_duplicates, read_records, validate
from import_csv import plan_import


def record(**changes):
    row = {'id': 'test-location', 'company_id': 'test-company', 'name': 'Test fixture',
           'city': 'Test city', 'country': 'Test country', 'lat': 0, 'lng': 0,
           'website': 'https://example.org/', 'evidence': '', 'verified_on': '',
           'coordinate_precision': 'city', 'evidence_state': 'unknown',
           'categories': ['VFX'], 'capabilities': [], 'capability_evidence': {}}
    row.update(changes)
    return row


from snapshots import before_v092


class ValidationTests(unittest.TestCase):
    def test_canonical_database_and_relationships(self):
        rows = read_records(ROOT / 'studios.json')
        self.assertEqual(validate(rows)[0], [])
        self.assertEqual(len(rows), 141)
        self.assertEqual(len({r['company_id'] for r in rows}), 77)
        for company in ('beyond', 'centroid'):
            self.assertEqual(sum(r['company_id'] == company for r in rows), 2)
        legacy = [r for r in rows if 'legacy_research' in r]
        self.assertEqual(len(legacy), 18)
        self.assertEqual({r['id'] for r in legacy if r['evidence_state'] != 'unknown'}, {'audiomotion'})

    def test_non_mocap_sector_is_valid(self):
        self.assertFalse(validate([record()])[0])

    def test_required_fields(self):
        for field in REQUIRED:
            with self.subTest(field=field):
                row = record(); del row[field]
                self.assertTrue(validate([row])[0])

    def test_unique_id(self):
        self.assertIn('duplicate id', ' '.join(validate([record(), record()])[0]))

    def test_coordinate_types_ranges_and_finiteness(self):
        for key, values in [('lat', [91, -91, float('nan'), float('inf'), True, '12', 10**1000]),
                            ('lng', [181, -181, None, []])]:
            for value in values:
                with self.subTest(key=key, value=value):
                    self.assertTrue(validate([record(**{key: value})])[0])
        self.assertFalse(validate([record(lat=-90, lng=180)])[0])

    def test_urls(self):
        for url in ['http://example.org', 'javascript:alert(1)', 'https://',
                    'https://user:pass@example.org', 'https://example.org:bad', 'https://bad host', [], 5]:
            with self.subTest(url=url):
                self.assertTrue(validate([record(website=url)])[0])

    def test_dates(self):
        for value in ['2026-02-30', '20261106', '2026-1-01', 2026]:
            self.assertTrue(validate([record(verified_on=value)])[0])
        self.assertFalse(validate([record(verified_on='2024-02-29')])[0])

    def test_evidence_states_and_support(self):
        self.assertTrue(validate([record(evidence_state='verified')])[0])
        for state in ('confirmed', 'likely'):
            self.assertTrue(validate([record(evidence_state=state)])[0])
            self.assertFalse(validate([record(evidence_state=state, evidence='https://example.org/source', verified_on='2024-02-29')])[0])

    def test_per_capability_confidence(self):
        evidence = {'VFX': {'state': 'likely', 'evidence': 'https://example.org/source', 'verified_on': '2024-01-01'}}
        row = record(capabilities=['VFX'], capability_evidence=evidence)
        self.assertFalse(validate([row])[0])
        row['capability_evidence']['VFX']['evidence'] = ''
        self.assertTrue(validate([row])[0])
        self.assertTrue(validate([record(capabilities=['VFX'])])[0])

    def test_malformed_records_do_not_crash(self):
        for data in [None, {}, [None], [[]], [{'id': [], 'website': {}, 'city': {}, 'capabilities': [{}]}]]:
            self.assertTrue(validate(data)[0])

    def test_possible_duplicates_normalize_accents_and_domain(self):
        a = record(name='Tést Studio', website='https://www.example.org/')
        b = record(id='another-location', company_id='another-company', name='Test Studio', website='https://example.org/services')
        pairs = possible_duplicates([a, b])
        self.assertEqual(len(pairs), 1)
        self.assertIn('name/city', pairs[0]['reasons'])
        self.assertIn('website/city', pairs[0]['reasons'])

    def test_legitimate_other_city_is_not_duplicate(self):
        self.assertFalse(possible_duplicates([record(), record(id='another', city='Other city')]))


class ResearchBatchTests(unittest.TestCase):
    def setUp(self):
        self.folder = ROOT / 'data/research/v0.7-batch-1'
        self.batch = read_records(self.folder / 'batch.csv')
        self.database = before_v092()[:31]
        self.evidence = json.loads((self.folder / 'evidence.json').read_text())

    def test_batch_exactly_matches_imported_records(self):
        self.assertEqual(len(self.batch), 13)
        by_id = {r['id']: r for r in self.database}
        for row in self.batch:
            self.assertEqual(by_id[row['id']], row)
        counts = {company: sum(r['company_id'] == company for r in self.batch)
                  for company in ('weta-fx', 'ilm', 'framestore')}
        self.assertEqual(counts, {'weta-fx': 1, 'ilm': 5, 'framestore': 7})

    def test_research_evidence_and_city_references(self):
        reviews = {r['id']: r for r in self.evidence['records']}
        self.assertEqual(set(reviews), {r['id'] for r in self.batch})
        for row in self.batch:
            review = reviews[row['id']]
            self.assertFalse(review['existing_id_match'])
            self.assertFalse(review['existing_company_id_match'])
            self.assertFalse(review['duplicate_candidates_against_baseline'])
            self.assertIn(row['evidence'], review['location_sources'])
            self.assertEqual(row['capability_evidence'], review['capability_sources'])
            self.assertEqual(row['verified_on'], self.evidence['verified_on'])
            geo = review['coordinate_reference']
            self.assertEqual((row['lat'], row['lng']), (geo['lat'], geo['lng']))
            self.assertEqual(row['coordinate_precision'], 'city')
            self.assertTrue(geo['source'].startswith('https://www.geonames.org/'))
            self.assertIn('VFX', row['categories'])
            self.assertNotIn('Motion Capture', row['capabilities'])
            self.assertNotIn('Performance Capture', row['capabilities'])
            self.assertNotIn('Game Development', row['categories'])
            for claim in row['capability_evidence'].values():
                self.assertEqual(claim['state'], 'confirmed')
                self.assertEqual(claim['verified_on'], row['verified_on'])

    def test_batch_replay_is_idempotent(self):
        combined, report = plan_import(self.database, self.batch)
        self.assertEqual(combined, self.database)
        self.assertEqual(len(report['unchanged_records']), 13)
        self.assertFalse(report['new_records'])
        self.assertFalse(report['rejected_records'])
        self.assertFalse(report['potential_duplicates'])

    def test_batch_can_be_replayed_against_preserved_seed(self):
        baseline = [r for r in self.database if 'legacy_research' in r]
        combined, report = plan_import(baseline, self.batch)
        self.assertEqual(combined, self.database)
        self.assertEqual(len(report['new_records']), 13)
        self.assertFalse(report['database_errors'])
        self.assertFalse(report['potential_duplicates'])


class ImportTests(unittest.TestCase):
    def test_new_record_and_repeat_import(self):
        combined, report = plan_import([], [record(), record()])
        self.assertEqual(len(combined), 1)
        self.assertEqual(report['new_records'], ['test-location'])
        self.assertEqual(report['unchanged_records'], ['test-location'])
        repeated, report = plan_import(combined, [record()])
        self.assertEqual(repeated, combined)
        self.assertFalse(report['new_records'])

    def test_id_conflict_never_overwrites(self):
        combined, report = plan_import([record()], [record(name='Changed')], ['test-location'])
        self.assertEqual(combined, [record()])
        self.assertEqual(len(report['rejected_records']), 1)

    def test_duplicates_held_and_explicit_distinct_location(self):
        candidate = record(id='another-location')
        combined, report = plan_import([record()], [candidate])
        self.assertEqual(len(combined), 1)
        self.assertEqual(len(report['potential_duplicates']), 1)
        combined, report = plan_import([record()], [candidate], ['another-location'])
        self.assertEqual(len(combined), 2)
        self.assertTrue(report['potential_duplicates'][0]['allowed_as_distinct'])

    def test_within_batch_duplicate_is_held(self):
        combined, report = plan_import([], [record(), record(id='another')])
        self.assertEqual(len(combined), 1)
        self.assertEqual(len(report['potential_duplicates']), 1)

    def test_bad_input_and_invalid_existing_database(self):
        combined, report = plan_import([], [record(lat=100)])
        self.assertEqual(combined, [])
        self.assertTrue(report['rejected_records'])
        combined, report = plan_import([record(lat=100)], [record()])
        self.assertTrue(report['database_errors'])
        self.assertFalse(report['new_records'])

    def test_multiple_locations_preserve_company_id(self):
        combined, report = plan_import([record()], [record(id='branch-two', city='Another city')])
        self.assertEqual(len(combined), 2)
        self.assertEqual(len({r['company_id'] for r in combined}), 1)
        self.assertFalse(report['potential_duplicates'])

    def run_import(self, csv_path, database, *args):
        result = subprocess.run([sys.executable, str(ROOT / 'tools/import_csv.py'), str(csv_path),
                                 '--database', str(database), *args], capture_output=True, text=True)
        return result.returncode, json.loads(result.stdout)

    def write_csv(self, path, rows):
        fields = list(record())
        with path.open('w', newline='', encoding='utf-8-sig') as f:
            writer = csv.DictWriter(f, fieldnames=fields); writer.writeheader()
            for row in rows:
                output = copy.deepcopy(row)
                for key in ('categories', 'capabilities'):
                    output[key] = '|'.join(output[key])
                output['capability_evidence'] = json.dumps(output['capability_evidence'])
                writer.writerow(output)

    def test_cli_dry_run_apply_and_repeat(self):
        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / 'studios.json'; database.write_text('[]\n')
            batch = Path(directory) / 'batch.csv'; self.write_csv(batch, [record()])
            code, report = self.run_import(batch, database, '--dry-run')
            self.assertEqual(code, 0); self.assertFalse(report['written'])
            self.assertEqual(database.read_text(), '[]\n')
            code, report = self.run_import(batch, database, '--apply')
            self.assertEqual(code, 0); self.assertTrue(report['written'])
            before = database.read_bytes()
            code, report = self.run_import(batch, database, '--apply')
            self.assertEqual(code, 0); self.assertFalse(report['written'])
            self.assertEqual(database.read_bytes(), before)

    def test_cli_batch_is_atomic_on_rejection(self):
        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / 'studios.json'; database.write_text('[]\n')
            batch = Path(directory) / 'batch.csv'
            self.write_csv(batch, [record(), record(id='invalid', lat=100)])
            code, report = self.run_import(batch, database, '--apply')
            self.assertEqual(code, 1); self.assertFalse(report['written'])
            self.assertEqual(database.read_text(), '[]\n')

    def test_cli_duplicate_does_not_write(self):
        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / 'studios.json'; database.write_text(json.dumps([record()]))
            batch = Path(directory) / 'batch.csv'; self.write_csv(batch, [record(id='another')])
            code, report = self.run_import(batch, database, '--apply')
            self.assertEqual(code, 1); self.assertFalse(report['written'])
            self.assertEqual(len(json.loads(database.read_text())), 1)

    def test_cli_structural_errors_produce_report_file(self):
        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / 'studios.json'; database.write_text('[]\n')
            batch = Path(directory) / 'batch.csv'; batch.write_text('id,id\na,b\n')
            report_path = Path(directory) / 'report.json'
            code, report = self.run_import(batch, database, '--report', str(report_path))
            self.assertEqual(code, 1)
            self.assertEqual(json.loads(report_path.read_text()), report)
            self.assertTrue(report['database_errors'])
            self.assertEqual(database.read_text(), '[]\n')

    def test_csv_rejects_unsupported_columns(self):
        with tempfile.TemporaryDirectory() as directory:
            batch = Path(directory) / 'batch.csv'
            self.write_csv(batch, [])
            batch.write_text(batch.read_text().rstrip() + ',unsupported_column\n')
            with self.assertRaises(ValueError): read_records(batch)

    def test_bad_csv_and_bad_evidence_json(self):
        with tempfile.TemporaryDirectory() as directory:
            batch = Path(directory) / 'batch.csv'
            batch.write_text('id,id\na,b\n')
            with self.assertRaises(ValueError): read_records(batch)
            self.write_csv(batch, [record()])
            batch.write_text(batch.read_text().replace(',{}', ',{oops'))
            self.assertTrue(validate(read_records(batch))[0])


if __name__ == '__main__':
    unittest.main()
