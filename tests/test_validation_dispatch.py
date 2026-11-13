"""Execute the actual manual-validation guards, including stale and hostile input."""
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import textwrap
import unittest

ROOT = Path(__file__).resolve().parents[1]


class ValidationDispatchTests(unittest.TestCase):
    def test_both_jobs_reject_wrong_commit_and_accept_only_exact_head(self):
        workflow = (ROOT / '.github/workflows/test.yml').read_text()
        blocks = workflow.split('      - name: Require the exact owner-selected review commit\n')[1:]
        self.assertEqual(len(blocks), 2)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            subprocess.run(['git', 'init', str(root)], check=True, capture_output=True)
            subprocess.run(['git', '-C', str(root), '-c', 'user.name=Test', '-c', 'user.email=test@example.invalid', 'commit', '--allow-empty', '-m', 'fixture'], check=True, capture_output=True)
            sha = subprocess.check_output(['git', '-C', str(root), 'rev-parse', 'HEAD'], text=True).strip()
            bash = shutil.which('bash')
            if os.name == 'nt':
                bash = str(Path(shutil.which('git')).parents[1] / 'bin/bash.exe')
            for block in blocks:
                script = textwrap.dedent(block.split('        run: |\n', 1)[1].split('\n      - ', 1)[0])
                for expected, github_sha in ((sha, sha), ('0' * 40, sha), (sha, '0' * 40), ('short', sha), ('$(touch injected)', sha)):
                    summary = root / 'summary'
                    summary.unlink(missing_ok=True)
                    env = {**os.environ, 'EXPECTED_SHA': expected, 'GITHUB_SHA': github_sha, 'GITHUB_STEP_SUMMARY': summary.as_posix()}
                    result = subprocess.run([bash, '-e', '-c', script], cwd=root, env=env, capture_output=True, text=True)
                    accepted = expected == sha and github_sha == sha
                    self.assertEqual(result.returncode == 0, accepted, result.stderr)
                    self.assertEqual(summary.exists(), accepted)
                    self.assertFalse((root / 'injected').exists())


if __name__ == '__main__':
    unittest.main()
