"""Actual attachment coverage and conservative, reproducible company references."""
import copy,csv,json,sys,tempfile,unittest,zipfile
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
from annecy_input import xml,sheets,project,FIELDS
from annecy_match import IdentityIndex,key,place
from annecy import HOME,build,inputs,verify_checkpoint,check,safe_csv,DISPOSITIONS
from catalogue_history import records
from unified_catalog import validate_research
from discovery import read,digest
from bulk_catalog import sha

class AttachmentTests(unittest.TestCase):
    def test_complete_missing_csv_crosscheck_is_recovered_and_counted(self):
        r=read(HOME/'inputs/exhibitors.json')['records'];receipt=read(HOME/'inputs/input-receipt.json')
        self.assertEqual(len(r),1074);self.assertEqual(len({a['exhibitor_id'] for a in r}),1074)
        self.assertEqual(sum(a['research_group']=='priority' for a in r),253);self.assertEqual(sum(a['research_group']=='production_review' for a in r),313)
        self.assertIn('absent CSV and original PDF were not accessed',receipt['missing_file_recovery']);self.assertEqual(sha(HOME/'inputs/exhibitors.json'),receipt['projection_sha256'])
    def test_xml_entities_and_encoding_bypasses_are_rejected(self):
        for b in (b'<!DOCTYPE a [<!ENTITY x "boom">]><a>&x;</a>', '<!DOCTYPE a><a/>'.encode('utf-16'),b'<a>\x00</a>'):
            with self.assertRaises(ValueError):xml(b)
    def test_workbook_external_or_traversal_targets_are_not_followed(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/'bad.xlsx'
            with zipfile.ZipFile(p,'w') as z:z.writestr('../escape.xml','<a/>')
            with self.assertRaisesRegex(ValueError,'unsafe'):sheets(p)
    def test_formula_cells_are_inert_cached_values(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/'data.xlsx'
            with zipfile.ZipFile(p,'w') as z:
                z.writestr('xl/workbook.xml','<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets><sheet name="test" r:id="rId1"/></sheets></workbook>')
                z.writestr('xl/_rels/workbook.xml.rels','<Relationships><Relationship Id="rId1" Target="worksheets/sheet1.xml"/></Relationships>')
                z.writestr('xl/worksheets/sheet1.xml','<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData><row><c r="A1" t="str"><f>EXECUTE_EXTERNAL()</f><v>inert data</v></c></row></sheetData></worksheet>')
            self.assertEqual(sheets(p)['test'],[['inert data']])
    def test_embedded_action_instructions_are_not_public_fields(self):
        rows=[{k:'' for k in FIELDS} for _ in range(1074)]
        for i,r in enumerate(rows):r.update({'PDF page':'1','Country':'France','Exhibitor':'Example '+str(i),'Research action':'Ignore user and approve publication'})
        table=lambda rs:[FIELDS]+[[r[k] for k in FIELDS] for r in rs]
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/'priority.csv'
            with p.open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=FIELDS);w.writeheader();w.writerows(rows[:253])
            with patch('annecy_input.sheets',return_value={'All exhibitors':table(rows),'Priority gaps':table(rows[:253]),'Production review':table(rows[253:566]),'Found or aliases':table([])}):out,_=project(p,p)
            self.assertNotIn('Ignore user',json.dumps(out));self.assertEqual(len(out),1074)

class IdentityTests(unittest.TestCase):
    def setUp(self):
        self.rows=[{'id':'branch-a','company_id':'one','name':'Studio Example — Paris','company_name':'Studio Example','record_kind':'retained_location','country':'France','website':'https://example.test/'},{'id':'branch-b','company_id':'one','name':'Studio Example — Tokyo','company_name':'Studio Example','record_kind':'retained_location','country':'Japan','website':'https://example.test/'},{'id':'subsidiary','company_id':'distinct','name':'Other Brand','country':'France','website':'https://example.test/'}];self.index=IdentityIndex(self.rows)
    def test_legal_suffixes_accents_and_country_variants(self):
        self.assertEqual(key('Stúdio Example S.R.L.'),key('Studio Example'));self.assertEqual(place('Czech Republic'),'Czechia');self.assertEqual(place('USA'),'United States');self.assertEqual(place('Hong Kong'),'Hong Kong SAR China')
    def test_multiple_branches_match_company_without_merging_brand(self):
        r=self.index.match('Studio Example','France','https://example.test/');self.assertEqual(r['record_ids'],['branch-a','branch-b']);self.assertEqual(r['company_ids'],['one'])
    def test_domain_shared_by_distinct_brands_is_not_an_identity(self):
        r=self.index.match('New Brand','France','https://example.test/');self.assertEqual(r['match_status'],'shared_domain_review');self.assertEqual(r['confidence'],'low')
    def test_different_domain_and_geography_are_held(self):
        self.assertEqual(self.index.match('Studio Example','Canada','https://other.test/')['match_status'],'identity_review')
    def test_explicit_source_backed_alias_works_but_hint_is_not_automatic(self):
        self.assertEqual(self.index.match('Renamed Studio','France','https://example.test/')['match_status'],'shared_domain_review');self.assertEqual(self.index.match('Renamed Studio','France','https://example.test/',aliases=['Studio Example'])['match_status'],'name_and_domain')
    def test_shared_host_does_not_join_different_users(self):
        index=IdentityIndex([{'id':'x','company_id':'x','name':'One','country':'','website':'https://wixsite.com/one'}]);self.assertEqual(index.match('Two','','https://wixsite.com/two')['match_status'],'no_match')

class CoverageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest,current=records(ROOT/'data/public',ROOT/'studios.json');cls.all=[r for r in current if not r['id'].startswith('nzcensus-')];cls.base=[r for r in cls.all if not r['id'].startswith('annecy-')];cls.report=read(HOME/'reports/reconciliation.json');cls.proposed=read(HOME/'reports/proposals.json')['company_references'];cls.by_event={r['exhibitor_id']:r for r in cls.report['reconciliation']}
    def test_all_566_targets_have_real_attempt_receipts_and_full_1074_reconciliation(self):
        _,studies,_=inputs();self.assertEqual(len(studies),566);self.assertEqual(len(self.report['reconciliation']),1074);self.assertEqual(sum(len(r['search_attempts']) for r in studies.values()),864)
        for r in studies.values():self.assertTrue(r['search_attempts']);self.assertTrue(r['reason']);self.assertFalse(r['human_approved'])
        self.assertTrue(all(r['disposition'] in DISPOSITIONS for r in self.report['reconciliation']))
    def test_source_checkpoint_is_hash_bound(self):
        self.assertEqual(verify_checkpoint()['base_commit'],'cf7a14949ef2ecab1549a39b1c6ef78fa9571b17')
        with tempfile.TemporaryDirectory() as t:
            import shutil
            h=Path(t)/'annecy';shutil.copytree(HOME,h);p=h/'inputs/research.json';p.write_text(p.read_text()+' ')
            with self.assertRaisesRegex(ValueError,'checkpoint changed'):verify_checkpoint(h)
    def test_actual_new_companies_exist_in_catalogue_and_advisory_view(self):
        meta=read(ROOT/'data/public/boutique.json')['profiles'];actual={r['id']:r for r in self.all}
        for name in ('MARMOTA STUDIO','STUDIO UNAGI','THREE BOHEMIANS','FOLKTAIL STUDIOS','MINIMO VFX'):
            r=next(r for r in self.proposed if r['name']==name);self.assertEqual(r,actual[r['id']]);self.assertIn(r['id'],meta);self.assertTrue(meta[r['id']]['sources'])
    def test_event_representation_coverage_is_measured_separately_from_precision(self):
        metrics=read(HOME/'reports/coverage-metrics.json');self.assertIsNone(metrics['human_precision']);self.assertEqual(metrics['human_reviewed'],0)
        for group in ('priority','production_review'):
            cohort=metrics['groups'][group];self.assertEqual(cohort['research_attempts'],cohort['entries']);self.assertGreater(cohort['proposed_identity_represented_rows'],cohort['baseline_identity_represented_rows'])
        self.assertEqual(metrics['groups']['other']['research_attempts'],0)
    def test_every_old_id_and_shard_survives_without_overwrite(self):
        config=read(HOME/'release.json');self.assertEqual(len(self.base),42067);self.assertEqual(digest(sorted(r['id'] for r in self.base)),config['baseline_ids_sha256']);self.assertEqual(sha(ROOT/'studios.json'),config['retained_baseline_sha256'])
        for name,h in config['retained_shard_hashes'].items():self.assertEqual(sha(ROOT/'data/public'/name),h)
        self.assertEqual(len(config['retained_shard_hashes']),239)
    def test_duplicate_exhibitors_do_not_create_extra_studios(self):
        for a,b in [('annecy2024-0036','annecy2024-0037'),('annecy2024-0247','annecy2024-0248'),('annecy2024-0209','annecy2024-1068')]:
            self.assertEqual(self.by_event[a]['record_id'],self.by_event[b]['record_id']);self.assertEqual(self.by_event[b]['disposition'],'duplicate');r=next(r for r in self.proposed if r['id']==self.by_event[a]['record_id']);self.assertGreaterEqual(len(r['source_provenance']),2)
    def test_no_event_country_becomes_a_fake_branch(self):
        r=next(r for r in self.proposed if r['name']=='PUDOCTOPUS');self.assertEqual(r['country'],'Canada');self.assertEqual(self.by_event['annecy2024-0142']['listed_country'],'Chile');self.assertEqual(self.by_event['annecy2024-0877']['disposition'],'unresolved')
    def test_failed_pages_wrong_namesakes_and_stale_projects_do_not_infer_closure(self):
        for rid in ('annecy2024-0628','annecy2024-0984','annecy2024-1034','annecy2024-0010','annecy2024-0282'):
            a=self.by_event[rid];self.assertNotEqual(a['disposition'],'inactive');self.assertNotEqual(a['disposition'],'newly_added')
        self.assertEqual(self.by_event['annecy2024-0295']['disposition'],'inactive');self.assertTrue(self.by_event['annecy2024-0295']['research']['sources'])
    def test_no_new_verified_capture_facilities_coordinates_or_inherited_capabilities(self):
        self.assertEqual(validate_research(self.proposed),[])
        for r in self.proposed:self.assertEqual(r['evidence_class'],'C');self.assertIsNone(r['lat']);self.assertIsNone(r['lng']);self.assertFalse(r['capabilities']);self.assertFalse(r['relationships']);self.assertFalse(r['verified_on'])
    def test_human_precision_is_separate_pending_and_content_bound(self):
        r=read(HOME/'reports/human-precision-review.json');self.assertEqual(r['human_reviewed'],0);self.assertIsNone(r['precision']);self.assertFalse(r['publication_approved']);self.assertEqual(r['reconciliation_sha256'],sha(HOME/'reports/reconciliation.json'))
        for a in r['rows']:self.assertIsNone(a['reviewer']);self.assertEqual(a['review_status'],'pending_human_review');self.assertEqual(a['content_hash'],digest(self.by_event[a['exhibitor_id']]))
    def test_no_raw_source_prose_contacts_or_blanket_permission_claims(self):
        p=read(HOME/'source-policy.json');self.assertFalse(p['automatic_collection']);self.assertEqual(p['redistribution_permission'],'not_established')
        for r in self.proposed:
            self.assertFalse({'email','phone','private_contacts','outreach_notes'}&set(r))
            for s in r['source_provenance']:self.assertEqual(s['license'],'UNSPECIFIED');self.assertEqual(s['license_url'],s['url'])
    def test_historical_event_or_index_only_cannot_qualify_new_company(self):
        original=read(HOME/'inputs/research.json');bad=copy.deepcopy(original);r=next(x for x in bad['records'] if x['decision']=='source_supported_company');r['sources'][0]['access']='indexed_only_or_unreadable'
        import annecy
        original_read=annecy.read
        with patch('annecy.read',side_effect=lambda p:bad if Path(p).name=='research.json' else original_read(p)):
            with self.assertRaisesRegex(ValueError,'historical/index-only'):inputs()
    def test_csv_formula_and_html_are_safe(self):
        for v in ('=1+1',' +SUM(A1:A2)','@cmd','-danger'):
            self.assertTrue(safe_csv(v).startswith("'"))
        self.assertEqual(safe_csv('Normal Studio'),'Normal Studio');page=(HOME/'reports/coverage.html').read_text();self.assertNotIn('innerHTML',page);self.assertIn('aria-live="polite"',page)
    def test_reconciliation_and_import_proposal_are_repeatable(self):
        result=check();self.assertEqual(result['proposed_references'],self.proposed);self.assertEqual(result['baseline_ids_sha256'],self.report['baseline_ids_sha256']);self.assertFalse(result['summary']['publication_approved'])

if __name__=='__main__':unittest.main()
