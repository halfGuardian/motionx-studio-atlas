"""Final geographic acceptance of the actual 182-company release, not a fixture."""
import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import map_gate as gate
from discovery import read, digest
from bulk_catalog import sha
from launch_readiness import records


class MapGateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest, cls.rows = records(ROOT / 'data/public', ROOT / 'studios.json')
        cls.report = gate.check()
        cls.value = read(ROOT / 'data/public/visibility.json')
        cls.new = [r for r in cls.rows if r['id'].startswith('globalcompany-')]

    def test_every_recorded_city_and_all_unlocated_companies_have_an_outcome(self):
        s = self.report['summary']
        self.assertEqual((s['admitted_companies'], s['recorded_city_associations_audited']), (182, 106))
        self.assertEqual((s['city_associations_with_display_reference'], s['city_associations_still_unpinned']), (102, 4))
        self.assertEqual((s['companies_without_recorded_city'], s['admitted_companies_unpinned']), (76, 80))
        self.assertEqual(len({r['record_id'] for r in self.report['records']}), 182)
        holds = {r['name'] for r in self.report['records'] if r['city'] and r['state'] == 'unpinned'}
        self.assertEqual(holds, {'DELTAROCKET', 'EX NIHILO PRODUCTIONS', 'Ozone Story Tech', 'MENZILMEKAN ANIMATION'})
        self.assertTrue(all(r['reason'] and r['reason_code'] for r in self.report['records']))

    def test_all_original_rows_and_eight_prior_display_points_are_preserved(self):
        cfg = read(gate.HOME / 'inputs/checkpoint.json')
        self.assertEqual(len(self.rows), 42478)
        self.assertEqual(digest({r['id']: digest(r) for r in sorted(self.rows, key=lambda r: r['id'])}), cfg['full_record_hashes_sha256'])
        before = read(gate.HOME / 'inputs/pr19-2936438/data/public/visibility.json')
        for rid, p in before['references'].items(): self.assertEqual(self.value['references'][rid], p)
        self.assertEqual(self.value['additional_references'], before['additional_references'])
        self.assertEqual(self.report['summary']['total_company_display_points'], 110)
        self.assertTrue(all(r['lat'] is None and r['lng'] is None and not r['capabilities'] and r['evidence_class'] == 'C' for r in self.new))

    def test_coordinate_provenance_and_homonyms_are_explicit(self):
        points = read(gate.HOME / 'inputs/city-coordinates.json')['points']
        self.assertEqual(len(points), 69)
        self.assertEqual(points['US/Long Beach']['source_record']['admin1code'], 'CA')
        self.assertEqual(points['ES/Garachico']['source_record']['geonameid'], 2517350)
        self.assertEqual(points['BR/Palmas']['source_record']['geonameid'], 3474574)
        self.assertEqual(points['KR/Gwacheon']['source_record']['geonameid'], 1841909)
        for r in self.report['records']:
            if not r['coordinate']: continue
            p = r['coordinate']
            self.assertEqual(p['coordinate_license'], 'CC-BY-4.0')
            self.assertFalse(p['human_approved']); self.assertFalse(p['facility_verified'])
            self.assertEqual(p['city'], r['city']); self.assertEqual(p['country'], r['country'])
            self.assertTrue(p['company_evidence_sources']); self.assertIn('current operation is unverified', p['explanation'])

    def test_agency_footers_approval_private_fields_and_future_dates_are_rejected(self):
        original_read = gate.read
        for mutate in (lambda d: d['records'][0].update(human_approved=True),
                       lambda d: d['records'][0]['evidence'][0].update(basis='agency_footer'),
                       lambda d: d['records'][0].update(reviewed_on_utc='2099-01-01'),
                       lambda d: d['records'][0].update(private_contact='not allowed')):
            bad = copy.deepcopy(original_read(gate.HOME / 'inputs/city-reviews.json')); mutate(bad)
            with patch('map_gate.read', side_effect=lambda p: bad if Path(p).name == 'city-reviews.json' else original_read(p)):
                with self.assertRaises(ValueError): gate.inputs(self.rows)

    def test_historical_taiwan_city_evidence_is_company_specific(self):
        byname = {r['name']: r for r in self.report['records']}
        for name in ('STUDIO ILYA ANIMATION, INTL.', 'ZERO ONE FILM CO. LTD'):
            r = byname[name]
            self.assertEqual(r['confidence'], 'historical_source_association')
            self.assertTrue(any('taiwancinema.bamid.gov.tw' in e['url'] for e in r['evidence']))
            self.assertTrue(any(e.get('source_year') in (2021, 2022) for e in r['evidence']))
            self.assertIn('shared pavilion footer is rejected', r['reason'])
        self.assertTrue(any('dottodot.tv' in e['url'] for e in byname['DOTTODOT LTD.']['evidence']))

    def test_repeat_draft_preparation_is_a_noop(self):
        files = [ROOT / 'data/public/manifest.json', ROOT / 'data/public/visibility.json', ROOT / 'studios.json']
        before = [sha(p) for p in files]
        self.assertEqual(gate.prepare()['summary'], self.report['summary'])
        self.assertEqual([sha(p) for p in files], before)

    def test_source_and_shard_arrival_orders_reproduce_identical_sidecar_bytes(self):
        from bulk_catalog import compact
        before = read(gate.HOME / 'inputs/pr19-2936438/data/public/visibility.json')
        reordered = dict(reversed(list(before.items())))
        reordered['company_audit'] = dict(reversed(list(before['company_audit'].items())))
        left, _ = gate.extend_visibility(before, self.rows)
        right, _ = gate.extend_visibility(reordered, list(reversed(self.rows)))
        with tempfile.TemporaryDirectory() as folder:
            a, b = Path(folder) / 'a.json', Path(folder) / 'b.json'
            compact(a, left); compact(b, right)
            self.assertEqual(a.read_bytes(), b.read_bytes())
            self.assertEqual(a.with_suffix('.json.gz').read_bytes(), b.with_suffix('.json.gz').read_bytes())

    def test_preserved_reference_cannot_be_moved(self):
        before = read(gate.HOME / 'inputs/pr19-2936438/data/public/visibility.json')
        before['references']['boutique-5926fcc99b16ed8ea595dcf5459f']['lat'] += .01
        with self.assertRaisesRegex(ValueError, 'Previously reviewed'): gate.extend_visibility(before, self.rows)

    def test_review_html_and_research_csv_escape_untrusted_text(self):
        report = copy.deepcopy(self.report)
        report['records'][0]['reason'] = '<script>alert(1)</script>'
        report['records'][0]['name'] = '=HYPERLINK("bad")'
        with tempfile.TemporaryDirectory() as folder:
            gate.save(report, folder)
            page = (Path(folder) / 'dashboard.html').read_text()
            self.assertIn('&lt;script&gt;', page); self.assertNotIn('<script>alert(1)', page)
            self.assertIn("'=HYPERLINK", (Path(folder) / 'companies.csv').read_text())


if __name__ == '__main__': unittest.main()
