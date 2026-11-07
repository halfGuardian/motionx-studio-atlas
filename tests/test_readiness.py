"""Advisory queue integrity, unresolved permissions and a lossless index codec."""
import copy,gzip,json,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
from compact_index import pack,unpack,short_id,full_id
from launch_readiness import generate,template,file_sha,records
from discovery import read,write

class CodecTests(unittest.TestCase):
    def test_ids_and_ieee_coordinates_round_trip_without_offsets(self):
        ids=['overture-12345678-9abc-def0-1234-56789abcdef0','overture-org-'+'f'*24,'gamedb-'+'b'*28,'gamedb-org-'+'c'*24,'existing-identity']
        for rid in ids:self.assertEqual(full_id(short_id(rid)),rid)
        row=[ids[0],ids[1],'Preserved Name','City','Country',12.345678901234567,-173.88776655443322,['Animation'],'shards/123456789abc-000.json','2026-11-06','source_provisional','C','source_location']
        self.assertEqual(unpack(pack([row],{row[0]:17})),[row+[17]])
    def test_empty_index_is_valid_but_malformed_encoding_is_not(self):
        self.assertEqual(unpack(pack([])),[])
        with self.assertRaises(ValueError):unpack({'encoding':'not-the-codec'})
        with self.assertRaises(ValueError):full_id('~xabc')

class ReadinessTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name);self.public=self.root/'public';self.public.mkdir()
        self.base=[read(ROOT/'studios.json')[0]];self.database=self.root/'studios.json';write(self.database,self.base)
        self.company={**self.base[0],'id':'company-reference','company_id':'company-provisional','name':'Company reference','city':'','lat':None,'lng':None,'evidence_class':'C','record_kind':'company_reference','evidence_state':'unknown','capabilities':[],'capability_evidence':{},'verified_on':'','source_observed_on':'2026-11-06','license':'UNSPECIFIED'}
        (self.public/'shards').mkdir();self.shard=self.public/'shards/123456789abc-000.json';write(self.shard,[self.company])
        write(self.public/'manifest.json',{'baseline':{'sha256':file_sha(self.database)},'counts':{'records':2},'shards':{'shards/123456789abc-000.json':{'sha256':file_sha(self.shard),'records':1}}})
    def test_permissions_are_never_granted_by_report_generation(self):
        result=generate(self.public,self.database,self.root/'reports');self.assertFalse(result['approval_granted']);self.assertEqual(result['review_queue'],1)
        audit=read(self.root/'reports/licensing.json');game=next(d for d in audit['datasets'] if d['source'].startswith('Game Studios'))
        self.assertEqual(game['redistribution_status'],'Permission not established');self.assertEqual(game['applicable_licence'],'UNSPECIFIED')
        self.assertIn('public',audit['public_access']);self.assertEqual(read(self.database),self.base)
        self.assertEqual(read(self.shard)[0]['evidence_class'],'C')
    def test_template_is_pending_and_bound_to_exact_record_and_baseline(self):
        generate(self.public,self.database,self.root/'reports');out=self.root/'proposal.json';template(self.company['id'],self.public,self.database,self.root/'reports/review-queue.json',out)
        proposal=read(out);self.assertIsNone(proposal['canonical_record']);self.assertFalse(proposal['approval_granted']);self.assertEqual(proposal['original_reference']['name'],self.company['name'])
        self.assertEqual(proposal['original_reference']['id'],self.company['id'])
    def test_stale_checkpoint_cannot_prepare_a_template(self):
        generate(self.public,self.database,self.root/'reports');queue=read(self.root/'reports/review-queue.json');queue['catalogue_sha256']='a'*64;write(self.root/'queue.json',queue)
        with self.assertRaisesRegex(ValueError,'stale'):template(self.company['id'],self.public,self.database,self.root/'queue.json',self.root/'out.json')
    def test_changed_source_record_or_fabricated_approval_is_rejected(self):
        generate(self.public,self.database,self.root/'reports');queue=read(self.root/'reports/review-queue.json');queue['entries'][0][3]='f'*64;write(self.root/'queue.json',queue)
        with self.assertRaisesRegex(ValueError,'bound'):template(self.company['id'],self.public,self.database,self.root/'queue.json',self.root/'out.json')
        queue['approval_granted']=True;write(self.root/'queue.json',queue)
        with self.assertRaisesRegex(ValueError,'checkpoint'):template(self.company['id'],self.public,self.database,self.root/'queue.json',self.root/'out.json')
    def test_missing_or_corrupt_source_shard_fails_without_partial_report(self):
        self.shard.write_text('[]')
        with self.assertRaisesRegex(ValueError,'integrity'):generate(self.public,self.database,self.root/'reports')
        self.assertFalse((self.root/'reports').exists())
    def test_policy_text_is_html_escaped_and_unsafe_links_rejected(self):
        bulk=read(ROOT/'data/bulk/sources.json');bulk['sources'].append({'id':'<script>alert(1)</script>','url':'https://example.test','enabled':False,'reason':'<img src=x onerror=alert(1)>'})
        generate(self.public,self.database,self.root/'reports',bulk=bulk);page=(self.root/'reports/licensing.html').read_text()
        self.assertNotIn('<script>',page);self.assertNotIn('<img',page);self.assertIn('&lt;script&gt;',page)

if __name__=='__main__':unittest.main()
