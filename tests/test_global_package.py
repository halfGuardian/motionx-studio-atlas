import sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from package_global_review import package

class ReviewPackageTests(unittest.TestCase):
    def test_relative_review_assets_are_retained_and_unsafe_outputs_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)/'checkout';out=Path(tmp)/'bundle'
            for rel in ('data/global-programme/reports/dashboard.html','data/nz-census/final-review/reports/dashboard.html','global-review.js','nz-final-review.js'):
                p=root/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_text('fixture '+rel)
            package(out,root);self.assertEqual((out/'global-review.js').read_bytes(),(root/'global-review.js').read_bytes());self.assertTrue((out/'data/global-programme/reports/dashboard.html').is_file());self.assertIn('matching repository checkout',(out/'index.html').read_text())
            with self.assertRaises(ValueError):package(out,root)
            with self.assertRaises(ValueError):package(root/'unsafe',root)
            (root/'data/global-programme/private-link').symlink_to('/etc/passwd')
            with self.assertRaises(ValueError):package(Path(tmp)/'unsafe-bundle',root)
