"""Actual baseline preservation and incremental failure-safe research staging."""
import copy
import csv
import json
import shutil
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT / 'tools'))
import maintenance as m
from discovery import digest, read, write
from global_programme import advance, empty_state, check_state, load_snapshot
from global_continuation import GROUPS

TODAY = date.today().isoformat()
POLICY = {'groups': GROUPS, 'overrides': {}}


def row(**changes):
    return {'source_record_id': 'test-1', 'name': 'Synthetic Test Animation', 'website': 'https://synthetic.example.org/',
        'city': 'Auckland', 'country': 'New Zealand', 'aliases': [], 'service_claims': ['Animation'], 'relationship_claims': [],
        'source_url': 'https://permitted.example.org/test', 'observed_on': TODAY, 'location_claim': '', 'status_claim': '', **changes}


def snapshot(rows, sid='test-permitted', version='one', **changes):
    return {'version': 1, 'source_id': sid, 'snapshot_id': version, 'observed_on': TODAY, 'status': 'success',
        'complete': True, 'expected_records': len(rows), 'source_url': 'https://permitted.example.org/test',
        'license': 'CC0-1.0', 'records': rows, 'enumeration_scope': 'Synthetic explicit test roster only',
        'policy_hash': 'a' * 64, 'input_sha256': digest(rows), 'automatic_publication': False, **changes}


def dossier(state, existing=()):
    return m.proposals(state, existing, POLICY, TODAY, m.config())


class IncrementalMaintenanceTests(unittest.TestCase):
    def test_monthly_day_interval_disable_and_manual_gate(self):
        c = m.config()
        self.assertTrue(m.due(c, '2026-12-01')); self.assertFalse(m.due(c, '2026-12-02'))
        self.assertTrue(m.due(c, '2026-12-02', True))
        c['monthly']['enabled'] = False; self.assertFalse(m.due(c, '2026-12-01', True))
        c['monthly'].update(enabled=True, interval_months=3)
        self.assertTrue(m.due(c, '2027-04-01')); self.assertFalse(m.due(c, '2027-05-01'))

    def test_source_expiry_disables_only_runtime_copy_and_keeps_ea_cinesite_off(self):
        c = m.config(); before = read(m.local(c['discovery_registry']))
        current = m.effective_registry(c, TODAY); expired = m.effective_registry(c, '2030-01-01')
        self.assertEqual(sum(s['enabled'] for s in current['sources']), 8)
        self.assertFalse(any(s['enabled'] for s in expired['sources']))
        self.assertEqual(before, read(m.local(c['discovery_registry'])))
        self.assertFalse(any(s['enabled'] for s in current['sources'] if s['id'] in ('ea-studios', 'cinesite-group')))

    def test_configuration_cannot_enable_publication_or_invalid_cadence(self):
        for mutate in (lambda c: c.update(automatic_publication=True), lambda c: c['monthly'].update(day_utc=31), lambda c: c['monthly'].update(branch_prefix='main'), lambda c: c['freshness'].update(policy_review_days=True)):
            with tempfile.TemporaryDirectory() as tmp:
                c = m.config(); mutate(c); p = Path(tmp) / 'config.json'; write(p, c)
                with self.assertRaises(ValueError): m.config(p)

    def test_same_snapshot_is_idempotent_and_changed_reused_id_is_rejected(self):
        s = snapshot([row()]); state, _ = m.add_snapshot(empty_state(), s)
        self.assertEqual(m.add_snapshot(state, s), (state, []))
        with self.assertRaises(ValueError): m.add_snapshot(state, s | {'records': [row(name='Conflicting identity')]})

    def test_failures_and_partial_rosters_keep_facts_and_do_not_close_companies(self):
        state, _ = m.add_snapshot(empty_state(), snapshot([row()]))
        for s in (snapshot([], version='failed', complete=False, status='failed', failure='robots denied'), snapshot([], version='partial', complete=False, status='partial')):
            state, changes = m.add_snapshot(state, s)
            self.assertEqual(len(dossier(state)), 1)
            self.assertFalse(any(x.get('closure_inference') for x in changes))
        self.assertEqual(state['canonical_updates'], []); self.assertFalse(state['human_approved'])

    def test_complete_absence_is_only_a_review_signal_and_keeps_old_record(self):
        s, _ = m.add_snapshot(empty_state(), snapshot([row()]))
        s, _ = m.add_snapshot(s, snapshot([], version='two'))
        p = dossier(s)[0]; self.assertIn('source_absence_review', p['kinds'])
        self.assertIsNone(p['canonical_update']); self.assertEqual(p['proposed_minimal_fields']['operation_status'], 'unverified')

    def test_rename_geography_and_services_keep_before_after_values(self):
        s, _ = m.add_snapshot(empty_state(), snapshot([row()]))
        s, _ = m.add_snapshot(s, snapshot([row(name='Renamed Test', city='Wellington', service_claims=['Game Development', 'Motion Capture'])], version='two'))
        p = dossier(s)[0]; changes = p['source_changes'][-1]
        self.assertEqual(changes['before']['city'], 'Auckland'); self.assertEqual(changes['after']['city'], 'Wellington')
        self.assertIn('technical_capability_review', p['kinds']); self.assertEqual(p['proposed_minimal_fields']['capabilities'], [])

    def test_explicit_closure_assertion_is_uncertain_and_never_an_update(self):
        s, _ = m.add_snapshot(empty_state(), snapshot([row(status_claim='Studio closing')]))
        p = dossier(s)[0]; self.assertIn('possible_closure_review', p['kinds']); self.assertIsNone(p['canonical_update'])

    def test_exact_factual_duplicates_group_but_different_cities_and_brands_do_not(self):
        s, _ = m.add_snapshot(empty_state(), snapshot([row()]))
        s, _ = m.add_snapshot(s, snapshot([row()], sid='second-permitted'))
        p = dossier(s); self.assertEqual(len(p), 1); self.assertEqual(len(p[0]['evidence']), 2)
        s, _ = m.add_snapshot(s, snapshot([row(city='Wellington'), row(source_record_id='brand', name='Another Brand')], sid='third-permitted'))
        self.assertEqual(len(dossier(s)), 3)

    def test_distinct_named_units_in_one_city_do_not_collapse_into_one_facility(self):
        s, _ = m.add_snapshot(empty_state(), snapshot([row(location_claim='Stage A'), row(source_record_id='stage-b', location_claim='Stage B')]))
        p = dossier(s); self.assertEqual(len(p), 2)
        self.assertTrue(all('facility_or_city_reference_review' in r['kinds'] and not r['facility_verified'] for r in p))

    def test_game_developers_need_no_capture_and_generic_film_is_not_high_confidence(self):
        for claims, role in ((['Game Development'], 'potential_client'), (['Animation'], 'potential_client'), (['Motion Capture'], 'service_provider'), (['Game Development', 'Motion Capture'], 'both'), (['Film Production'], 'plausible_unconfirmed')):
            s, _ = m.add_snapshot(empty_state(), snapshot([row(service_claims=claims)]))
            p = dossier(s)[0]; self.assertEqual(p['commercial']['role'], role)
            self.assertEqual(p['proposed_minimal_fields']['capabilities'], [])

    def test_audio_signals_and_multidisciplinary_firms_are_not_auto_excluded(self):
        for claims in (['Audio Post Production'], ['Audio Post Production', 'Animation']):
            s, _ = m.add_snapshot(empty_state(), snapshot([row(name='Audio Synthetic Test', service_claims=claims)]))
            p = dossier(s)[0]; self.assertIn('audio_only_scope_review', p['kinds']); self.assertFalse(p['commercial']['excluded'])

    def test_existing_reviewed_audio_exclusion_is_retained_by_exact_identity(self):
        existing = row() | {'id': 'reviewed', 'company_id': 'reviewed', 'record_kind': 'company_reference', 'source_provenance': [], 'categories': []}
        policy = copy.deepcopy(POLICY); policy['overrides']['reviewed'] = {'excluded': True, 'role': 'out_of_scope', 'reason': 'Synthetic individually reviewed test exclusion'}
        s, _ = m.add_snapshot(empty_state(), snapshot([row()]))
        p = m.proposals(s, [existing], policy, TODAY, m.config())[0]
        self.assertTrue(p['commercial']['excluded']); self.assertEqual(p['commercial']['role'], 'out_of_scope')
        self.assertIn('reviewed_audio_exclusion_conflict', p['kinds'])
        self.assertEqual(p['recommendation'], 'compare_source_assertions_only_preserve_existing_facts')

    def test_foreign_location_same_name_and_domain_is_not_a_verified_branch(self):
        existing = {'id': 'old', 'company_id': 'org', 'name': row()['name'], 'city': 'Toronto', 'country': 'Canada', 'website': row()['website'], 'categories': ['Animation'], 'record_kind': 'company_reference', 'source_provenance': []}
        s, _ = m.add_snapshot(empty_state(), snapshot([row()]))
        p = dossier(s, [existing])[0]; self.assertIn('city_association_change_review', p['kinds'])
        self.assertIsNone(p['geographic_proposal']['coordinates']); self.assertFalse(p['facility_verified'])

    def test_source_age_and_observation_age_are_separate(self):
        s, _ = m.add_snapshot(empty_state(), snapshot([row(source_updated_on='2020-01-01')]))
        e = dossier(s)[0]['evidence'][0]; self.assertEqual(e['observation_age_days'], 0); self.assertGreater(e['source_age_days'], 1000)

    def test_csv_permission_private_columns_and_duplicate_ids_fail_closed(self):
        policy = {'source_id': 'test-permitted', 'mode': 'reviewed_dataset_replay', 'reuse_decision': 'scoped_dataset_permission', 'license': 'CC0-1.0', 'license_url': 'https://example.org/license', 'attribution': 'Synthetic test only', 'reviewed_on': TODAY, 'human_approved': False}
        value = snapshot([row()]); value.pop('policy_hash'); value.pop('input_sha256'); value.pop('automatic_publication')
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / 'input.json'; write(p, value)
            with self.assertRaises(ValueError): load_snapshot(p, policy | {'reuse_decision': 'publicly_accessible'})
            write(p, value | {'records': [row(), row()]})
            with self.assertRaises(ValueError): load_snapshot(p, policy)
            csv = Path(tmp) / 'input.csv'; csv.write_text('source_record_id,name,private_contact\n1,Test,secret\n')
            with self.assertRaises(ValueError): load_snapshot(csv, policy, {k: v for k, v in value.items() if k != 'records'})

    def test_corrupt_and_missing_chain_events_do_not_reset_state(self):
        s, _ = m.add_snapshot(empty_state(), snapshot([row()]))
        bad = copy.deepcopy(s); bad['history'][0]['snapshot']['records'] = []
        with self.assertRaises(ValueError): check_state(bad)

    def test_additional_permitted_csv_and_json_registrations_share_incremental_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); (root / 'data').mkdir(); entries = []
            for kind in ('json', 'csv'):
                sid = 'synthetic-' + kind; s = snapshot([row()], sid=sid)
                for field in ('policy_hash', 'input_sha256', 'automatic_publication'): s.pop(field)
                policy = {'source_id': sid, 'mode': 'reviewed_dataset_replay', 'reuse_decision': 'scoped_dataset_permission', 'license': 'CC0-1.0', 'license_url': 'https://example.org/licence', 'attribution': 'Synthetic test dataset only', 'reviewed_on': TODAY, 'human_approved': False}
                write(root / ('data/' + sid + '-policy.json'), policy)
                p = root / ('data/' + sid + '.' + kind); metadata = None
                if kind == 'csv':
                    metadata = {k: v for k, v in s.items() if k != 'records'}; write(root / 'data/csv-metadata.json', metadata)
                    with p.open('w', newline='') as stream:
                        writer = csv.DictWriter(stream, fieldnames=list(row())); writer.writeheader()
                        writer.writerow({k: json.dumps(v) if isinstance(v, list) else v for k, v in row().items()})
                else: write(p, s)
                loaded = load_snapshot(p, policy, metadata); state, _ = m.add_snapshot(empty_state(), loaded); write(root / ('data/' + sid + '-state.json'), state)
                entry = {'source_id': sid, 'policy': 'data/' + sid + '-policy.json', 'snapshot': 'data/' + sid + '.' + kind, 'state': 'data/' + sid + '-state.json'}
                if metadata: entry['metadata'] = 'data/csv-metadata.json'
                entries.append(entry)
            write(root / 'data/registry.json', {'version': 1, 'sources': entries}); c = m.config(); c['snapshot_registry'] = 'data/registry.json'
            with patch('maintenance.local', side_effect=lambda name: root / name): values = list(m.dataset_snapshots(c))
            self.assertEqual(len(values), 2); state = empty_state()
            for _, _, loaded, _ in values: state, _ = m.add_snapshot(state, loaded)
            self.assertEqual(len(dossier(state)), 1); self.assertEqual(len(dossier(state)[0]['evidence']), 2)


class ActualMaintenanceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory(); cls.out = Path(cls.tmp.name) / 'first'
        cls.before = m.publication_fingerprint()
        cls.report = m.prepare(m.HOME / 'inputs/discovery-42149794259', cls.out)

    @classmethod
    def tearDownClass(cls): cls.tmp.cleanup()

    def test_full_actual_catalogue_and_public_assets_preserved(self):
        self.assertEqual(self.report['summary']['catalogue_records'], 42478)
        self.assertEqual(self.before, m.publication_fingerprint())
        self.assertEqual(self.report['summary']['retained_discovery_candidates'], 133)
        self.assertEqual(self.report['summary']['canonical_updates'], 0)
        self.assertEqual(self.report['summary']['reviewed_company_proposals'], 0)
        self.assertFalse(self.report['summary']['global_complete'])

    def test_actual_registry_is_eight_live_seventeen_manual_one_offline(self):
        s = self.report['summary']; self.assertEqual((s['automatic_official_sources_configured'], s['manual_official_sources'], s['offline_dataset_sources']), (8, 17, 1))
        ds = next(s for s in self.report['source_coverage'] if s['source_id'] == 'animstudios-github')
        self.assertEqual(ds['records'], 424); self.assertEqual(ds['license'], 'CC-BY-4.0'); self.assertTrue(ds['complete'])

    def test_repeat_replay_is_idempotent_and_retains_every_historical_event(self):
        out = Path(self.tmp.name) / 'repeat'; r = m.prepare(m.HOME / 'inputs/discovery-42149794259', out, self.out / 'state.json')
        self.assertEqual(r['summary']['new_change_signals'], 0)
        self.assertEqual(read(out / 'state.json'), read(self.out / 'state.json'))
        self.assertEqual(r['content_fingerprint'], self.report['content_fingerprint'])

    def test_archive_corruption_approvals_and_extra_files_are_rejected(self):
        for name in ('state.json', 'report.json'):
            out = Path(self.tmp.name) / name.replace('.', '-'); shutil.copytree(self.out, out)
            p = out / name; p.write_bytes(p.read_bytes() + b' ')
            with self.assertRaises(ValueError): m.verify(out)
        out = Path(self.tmp.name) / 'approval'; shutil.copytree(self.out, out)
        r = read(out / 'report.json'); r['summary']['human_approved'] = True; write(out / 'report.json', r); m.seal(out)
        with self.assertRaises(ValueError): m.verify(out)

    def test_raw_discovery_unknown_files_and_nested_output_are_rejected(self):
        with self.assertRaises(ValueError): m.prepare(self.out / 'discovery', self.out / 'discovery/nested')
        out = Path(self.tmp.name) / 'private'; shutil.copytree(self.out / 'discovery', out); (out / 'private.env').write_text('synthetic fixture only')
        with self.assertRaises(ValueError): m.validate_discovery(out)

    def test_dashboard_escapes_text_and_has_no_approval_control(self):
        r = copy.deepcopy(self.report); r['proposals'] = r['proposals'][:1]; r['proposals'][0]['name'] = '<img src=x onerror=alert(1)>'
        out = Path(self.tmp.name) / 'escaped'; out.mkdir(); m.save_report(r, out)
        page = (out / 'review.html').read_text(); self.assertNotIn('<img src=x', page); self.assertIn('&lt;img', page); self.assertNotIn('onclick=', page)


class ActualScheduledMaintenanceTests(unittest.TestCase):
    def test_real_scheduled_artifact_uses_eight_sources_and_retains_legacy_history_uncertainty(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / 'scheduled'; before = m.publication_fingerprint()
            r = m.prepare(m.HOME / 'inputs/discovery-42666896576', out)
            self.assertEqual(r['summary']['retained_discovery_candidates'], 200)
            current = [s for s in r['source_coverage'] if s['automatic_collection_configured']]
            self.assertEqual(len(current), 8); self.assertTrue(all(s['status'] == 'ok' for s in current))
            self.assertEqual(sum(s['observations'] for s in current), 58)
            self.assertFalse(r['discovery_recovery']['history_complete'])
            self.assertTrue(r['discovery_recovery']['legacy_completeness_flag_not_proof'])
            self.assertEqual(before, m.publication_fingerprint()); m.verify(out)


if __name__ == '__main__': unittest.main()
