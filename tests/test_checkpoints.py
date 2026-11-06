"""Continuity cannot be recovered by silently resetting state or trusting changed bytes."""
import copy,hashlib,json,subprocess,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
from checkpoints import validate_manifest,recover,check_queue,archive_manifest
from restore_discovery import restore
from discovery import scan,read
from test_discovery import CONFIG,EMPTY,observed

class CheckpointTests(unittest.TestCase):
    def fixture(self,root):
        q,_=observed();p=root/'queue.json';p.write_text(json.dumps(q))
        return {'version':1,'queue_path':'queue.json','files':[{'path':'queue.json','kind':'queue','sha256':hashlib.sha256(p.read_bytes()).hexdigest()}]}
    def test_recovery_preserves_all_candidates_but_explicitly_reports_incomplete_history(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);manifest=self.fixture(root);q,r,_=recover(manifest,root,lost_run_id=10)
            self.assertEqual(q,read(root/'queue.json'));self.assertFalse(r['history_complete']);self.assertTrue(r['suppress_absence_signals']);self.assertEqual(r['approved_claims'],0)
    def test_tampered_bytes_missing_file_traversal_and_symlink_fail_closed(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);m=self.fixture(root)
            for change in ({'sha256':'0'*64},{'path':'../elsewhere'},{'path':'missing.json'}):
                bad=copy.deepcopy(m);bad['files'][0].update(change)
                with self.assertRaises((ValueError,OSError)):validate_manifest(bad,root)
            p=root/'queue.json';original=p.read_bytes();p.write_bytes(original+b' ')
            with self.assertRaises(ValueError):validate_manifest(m,root)
            p.unlink();(root/'target.json').write_bytes(original);p.symlink_to(root/'target.json')
            with self.assertRaises(ValueError):validate_manifest(m,root)
    def test_suppressed_absence_after_recovery_is_not_a_closure_signal(self):
        q,_=observed();state,r=scan(CONFIG,q,[],fetcher=lambda _:'<a href="/studio/new">New</a>',detect_absence=False)
        self.assertTrue(set(q['candidates']).issubset(state['candidates']))
        self.assertFalse(any(event['type']=='missing_from_source' for event in r['events']))
    def test_malformed_observation_dates_and_identity_are_rejected(self):
        q,_=observed();c=next(iter(q['candidates'].values()))
        for change in ({'last_seen':'2026-99-99'},{'first_seen':'2999-01-01'},{'url':'http://localhost'},{'id':'changed'}):
            bad=copy.deepcopy(q);next(iter(bad['candidates'].values())).update(change)
            with self.assertRaises((ValueError,KeyError)):check_queue(bad)
    def test_missing_newest_artifact_uses_an_older_valid_artifact_without_hiding_gap(self):
        q,report=observed()
        def run(args,**kwargs):
            if args[1:3]==['run','list']:return subprocess.CompletedProcess(args,0,json.dumps([{'databaseId':2},{'databaseId':1}]))
            if args[3]=='2':return subprocess.CompletedProcess(args,1,'','expired')
            path=Path(args[-1]);path.mkdir();(path/'queue.json').write_text(json.dumps(q));(path/'report.json').write_text(json.dumps(report))
            return subprocess.CompletedProcess(args,0,'','')
        with tempfile.TemporaryDirectory() as folder:
            out=Path(folder)/'restore';restore(out,runner=run)
            self.assertEqual(read(out/'queue.json'),q);r=read(out/'recovery.json')
            self.assertEqual(r['run_id'],1);self.assertFalse(r['history_complete']);self.assertTrue(r['suppress_absence_signals'])
    def test_invalid_run_metadata_and_network_failures_do_not_reset_queue(self):
        with tempfile.TemporaryDirectory() as folder:
            out=Path(folder)/'restore'
            def invalid(args,**kwargs):return subprocess.CompletedProcess(args,0,'[{"databaseId":"$(bad)"}]')
            with self.assertRaises(ValueError):restore(out,runner=invalid)
            self.assertFalse(out.exists())
            def fail(*args,**kwargs):raise subprocess.CalledProcessError(1,args[0])
            with self.assertRaises(subprocess.CalledProcessError):restore(out,runner=fail)
            self.assertFalse(out.exists())
    def test_committed_manifest_matches_reviewed_v093_checkpoint(self):
        files=validate_manifest(read(ROOT/'data/discovery/checkpoints.json'))
        q=files['data/research/v0.9.3-global/queue.json'][2]
        self.assertEqual(len(q['candidates']),172)
        self.assertEqual(sum(c['source_kind']=='manual_backlog' for c in q['candidates'].values()),41)
