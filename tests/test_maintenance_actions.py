"""Simulated GitHub responses with real isolated Git branches; no live PR writes."""
import copy
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT / 'tools'))
import maintenance as m
import maintenance_actions as actions
from discovery import read, write
from test_maintenance import row, snapshot


class GitFixture:
    def __init__(self, folder):
        self.root = Path(folder) / 'work'; self.remote = Path(folder) / 'remote.git'; self.root.mkdir()
        self.pr = None; self.other = []; self.calls = []; self.created = 0; self.edited = 0; self.deny_create = False
        subprocess.run(['git', 'init', '--bare', str(self.remote)], check=True, capture_output=True)
        self.git(['init', '-b', 'main']); (self.root / 'README.md').write_text('Isolated synthetic workflow fixture only.\n')
        self.git(['add', '.']); self.commit('initial'); self.git(['remote', 'add', 'origin', str(self.remote)]); self.git(['push', '-u', 'origin', 'main'])

    def git(self, args):
        return subprocess.run(['git', *args], cwd=self.root, capture_output=True, text=True, check=True).stdout

    def commit(self, message): self.git(['-c', 'user.name=Workflow Test', '-c', 'user.email=test@example.test', 'commit', '-m', message])

    def __call__(self, args, **kwargs):
        self.calls.append(args)
        if args[0] == 'git': return subprocess.run(args, cwd=self.root, **kwargs)
        if args[:3] == ['gh', 'pr', 'list']:
            value = ([self.pr] if self.pr else []) if '--head' in args else self.other
            return subprocess.CompletedProcess(args, 0, json.dumps(value), '')
        if args[:3] == ['gh', 'pr', 'create']:
            if self.deny_create: return subprocess.CompletedProcess(args, 1, '', 'GitHub Actions is not permitted to create or approve pull requests; synthetic-token-must-not-leak')
            assert '--draft' in args and args[args.index('--base') + 1] == 'main'
            body = Path(args[args.index('--body-file') + 1]).read_text(); assert 'Merging this PR archives research only' in body
            self.created += 1; self.pr = {'number': 321, 'state': 'OPEN', 'isDraft': True, 'isCrossRepository': False, 'baseRefName': 'main', 'headRefOid': self.git(['rev-parse', 'HEAD']).strip()}
            return subprocess.CompletedProcess(args, 0, 'https://example.test/synthetic-pr/321\n', '')
        if args[:3] == ['gh', 'pr', 'edit']:
            self.edited += 1; self.pr['headRefOid'] = self.git(['rev-parse', 'HEAD']).strip()
            return subprocess.CompletedProcess(args, 0, '', '')
        if args[:3] == ['gh', 'pr', 'view']: return subprocess.CompletedProcess(args, 0, json.dumps(self.pr), '')
        raise AssertionError('Unexpected command ' + repr(args))


class MaintenanceActionsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory(); cls.prepared = Path(cls.tmp.name) / 'prepared'
        m.prepare(m.HOME / 'inputs/discovery-42149794259', cls.prepared)

    @classmethod
    def tearDownClass(cls): cls.tmp.cleanup()

    def stage(self, tmp, name='stage'):
        out = Path(tmp) / name; shutil.copytree(self.prepared, out); return out

    def test_real_git_draft_creation_repeat_noop_and_research_only_diff(self):
        with tempfile.TemporaryDirectory() as tmp:
            fixture = GitFixture(tmp); out = self.stage(tmp)
            result = actions.propose(out, '2026-11', fixture, fixture.root)
            self.assertEqual(result['status'], 'created_draft'); self.assertFalse(result['publication'])
            changed = fixture.git(['diff', '--name-only', 'origin/main...HEAD']).splitlines()
            self.assertTrue(changed); self.assertTrue(all(p.startswith('data/maintenance/batches/2026-11/') for p in changed))
            head = fixture.git(['rev-parse', 'HEAD']); self.assertEqual(actions.propose(out, '2026-11', fixture, fixture.root)['status'], 'unchanged')
            self.assertEqual(head, fixture.git(['rev-parse', 'HEAD'])); self.assertEqual(fixture.created, 1)
            self.assertFalse(any('--force' in x or '--force-with-lease' in x or 'merge' in x or 'review' in x for x in fixture.calls))

    def test_updates_keep_history_and_before_reports_and_reject_older_state(self):
        with tempfile.TemporaryDirectory() as tmp:
            f = GitFixture(tmp); original = self.stage(tmp); actions.propose(original, '2026-11', f, f.root)
            state, _ = m.add_snapshot(read(original / 'state.json'), snapshot([row()], sid='synthetic-permitted-test'))
            state_path = Path(tmp) / 'state.json'; write(state_path, state)
            out = Path(tmp) / 'new'; m.prepare(m.HOME / 'inputs/discovery-42149794259', out, state_path)
            self.assertEqual(actions.propose(out, '2026-11', f, f.root)['status'], 'updated_draft')
            target = f.root / 'data/maintenance/batches/2026-11'; self.assertTrue(list((target / 'revisions').glob('*.json'))); m.verify(target)
            with self.assertRaisesRegex(ValueError, 'Older/missing'): actions.propose(original, '2026-11', f, f.root)
            self.assertEqual(f.edited, 1)

    def test_pr_creation_denial_leaves_recoverable_branch_and_exact_restriction(self):
        with tempfile.TemporaryDirectory() as tmp:
            f = GitFixture(tmp); out = self.stage(tmp); f.deny_create = True
            with self.assertRaisesRegex(ValueError, 'GitHub Actions is not permitted') as err: actions.propose(out, '2026-11', f, f.root)
            self.assertNotIn('synthetic-token-must-not-leak', str(err.exception))
            self.assertTrue(f.git(['ls-remote', '--heads', 'origin', 'refs/heads/automation/atlas-maintenance-2026-11']).strip())
            f.deny_create = False; self.assertEqual(actions.propose(out, '2026-11', f, f.root)['status'], 'created_draft')
            self.assertEqual(f.created, 1)

    def test_one_open_batch_and_closed_period_prevent_repeat_pr_spam(self):
        with tempfile.TemporaryDirectory() as tmp:
            f = GitFixture(tmp); out = self.stage(tmp)
            f.other = [{'number': 12, 'headRefName': 'automation/atlas-maintenance-2026-10'}]
            self.assertEqual(actions.propose(out, '2026-11', f, f.root)['status'], 'previous_batch_awaits_owner_review')
            f.other = []; f.pr = {'state': 'MERGED'}
            self.assertEqual(actions.propose(out, '2026-11', f, f.root)['status'], 'period_already_closed'); self.assertEqual(f.created, 0)

    def test_no_new_content_since_a_merged_batch_does_not_open_next_month_pr(self):
        with tempfile.TemporaryDirectory() as tmp:
            f = GitFixture(tmp); previous = f.root / 'data/maintenance/batches/2026-10'; shutil.copytree(self.prepared, previous)
            f.git(['add', 'data']); f.commit('synthetic previously reviewed research'); f.git(['push', 'origin', 'main'])
            self.assertEqual(actions.propose(self.stage(tmp), '2026-11', f, f.root)['status'], 'no_new_research_content')
            self.assertEqual(f.created, 0)

    def test_non_draft_and_unexpected_public_changes_cannot_be_overwritten(self):
        with tempfile.TemporaryDirectory() as tmp:
            f = GitFixture(tmp); out = self.stage(tmp); actions.propose(out, '2026-11', f, f.root)
            f.pr['isDraft'] = False
            with self.assertRaisesRegex(ValueError, 'human review'): actions.propose(out, '2026-11', f, f.root)
            f.pr['isDraft'] = True; (f.root / 'studios.json').write_text('Synthetic external edit, never real data')
            f.git(['add', 'studios.json']); f.commit('external modification'); f.git(['push', 'origin', 'HEAD:automation/atlas-maintenance-2026-11']); f.pr['headRefOid'] = f.git(['rev-parse', 'HEAD']).strip()
            with self.assertRaisesRegex(ValueError, 'outside its batch'): actions.propose(out, '2026-11', f, f.root)

    def test_stale_pr_head_is_detected_without_force_push(self):
        with tempfile.TemporaryDirectory() as tmp:
            f = GitFixture(tmp); out = self.stage(tmp); actions.propose(out, '2026-11', f, f.root)
            f.pr['headRefOid'] = '0' * 40
            with self.assertRaisesRegex(ValueError, 'head changed'): actions.propose(out, '2026-11', f, f.root)

    def test_untrusted_month_and_truncated_open_inventory_are_blocked(self):
        with self.assertRaises(ValueError): actions.month('2026-11; command')
        with tempfile.TemporaryDirectory() as tmp:
            f = GitFixture(tmp); f.other = [{'number': i, 'headRefName': 'other-' + str(i)} for i in range(100)]
            with self.assertRaisesRegex(ValueError, 'truncated'): actions.propose(self.stage(tmp), '2026-11', f, f.root)

    def restore_runner(self, available=True, corrupt=False, network=False):
        def runner(args, **kwargs):
            if network: return subprocess.CompletedProcess(args, 1, '', 'HTTP 403 Resource not accessible by integration')
            if args[:3] == ['gh', 'run', 'list']: return subprocess.CompletedProcess(args, 0, '[{"databaseId":123}]', '')
            if args[:2] == ['gh', 'api']:
                value = {'artifacts': [{'name': 'atlas-maintenance', 'expires_at': '2027-02-04T00:00:00Z'}]} if '/artifacts?' in args[2] else {'head_branch': 'main', 'path': '.github/workflows/discovery.yml', 'status': 'completed', 'event': 'schedule', 'conclusion': 'failure', 'head_repository': {'full_name': actions.REPOSITORY}}
                return subprocess.CompletedProcess(args, 0, json.dumps(value), '')
            if args[:3] == ['gh', 'run', 'download']:
                if not available: return subprocess.CompletedProcess(args, 1, '', 'expired')
                target = Path(args[-1]); shutil.copytree(self.prepared, target)
                if corrupt: (target / 'state.json').write_text('{}')
                return subprocess.CompletedProcess(args, 0, '', '')
            raise AssertionError(args)
        return runner

    def test_failed_run_valid_partial_artifact_is_recovered_not_skipped(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / 'restore'; actions.restore(out, self.restore_runner())
            r = read(out / 'recovery.json'); self.assertEqual(r['mode'], 'verified_actions_artifact'); self.assertEqual(r['source_run_conclusion'], 'failure')
            self.assertFalse(r['history_complete']); self.assertEqual(read(out / 'maintenance/state.json'), read(self.prepared / 'state.json'))

    def test_expired_or_corrupted_artifacts_use_hash_bound_original_without_complete_claim(self):
        for runner in (self.restore_runner(available=False), self.restore_runner(corrupt=True)):
            with tempfile.TemporaryDirectory() as tmp:
                out = Path(tmp) / 'restore'; actions.restore(out, runner)
                r = read(out / 'recovery.json'); self.assertEqual(r['mode'], 'committed_discovery_bootstrap'); self.assertFalse(r['history_complete'])
                self.assertEqual(r['source_run_id'], 42666896576)
                self.assertEqual(len(read(out / 'maintenance/discovery/queue.json')['candidates']), 200)

    def test_network_or_permission_failure_never_silently_resets_state(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / 'restore'
            with self.assertRaisesRegex(ValueError, 'Resource not accessible'): actions.restore(out, self.restore_runner(network=True))
            self.assertFalse(out.exists())

    def test_candidate_union_survives_artifact_loss_and_archives_old_bytes(self):
        with tempfile.TemporaryDirectory() as tmp:
            left = Path(tmp) / 'left'; shutil.copytree(self.prepared / 'discovery', left)
            right = Path(tmp) / 'right'; shutil.copytree(self.prepared / 'discovery', right / 'discovery')
            q = read(right / 'discovery/queue.json'); rid = next(iter(q['candidates'])); q['candidates'].pop(rid); write(right / 'discovery/queue.json', q)
            result = actions.join_discovery(left, right)
            self.assertEqual(result['retained_candidates'], 133); self.assertIn(rid, read(left / 'queue.json')['candidates'])
            self.assertGreater(len(list((left / 'history').glob('*.json'))), 0)

    def test_restoration_requires_main_repo_completed_discovery_run(self):
        base = {'head_branch': 'main', 'path': '.github/workflows/discovery.yml', 'status': 'completed', 'event': 'schedule', 'head_repository': {'full_name': actions.REPOSITORY}}
        self.assertTrue(actions.eligible(base))
        for patch in ({'head_branch': 'other'}, {'event': 'pull_request'}, {'status': 'in_progress'}, {'head_repository': {'full_name': 'other/fork'}}): self.assertFalse(actions.eligible(base | patch))


if __name__ == '__main__': unittest.main()
