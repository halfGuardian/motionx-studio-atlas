"""No unreviewed specialisations, lost history, fabricated approvals or staged leaks."""
import copy,json,shutil,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
import nz_quality_gate as gate
from discovery import read,write,digest
from launch_readiness import records
from unified_catalog import validate_research
from bulk_catalog import sha

class FinalGateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report=gate.check();cls.parent,cls.companies,cls.identities,cls.facilities=gate.inputs();cls.manifest,cls.current=records(ROOT/'data/public',ROOT/'studios.json');cls.raw=read(ROOT/'data/nz-census/reports/proposals.json')['company_references'];cls.published=gate.public_records(cls.raw)
    def temp_home(self):
        t=tempfile.TemporaryDirectory();self.addCleanup(t.cleanup);home=Path(t.name)/'gate';shutil.copytree(gate.HOME/'inputs',home/'inputs');return home
    def test_every_59_company_has_classification_evidence_rights_and_explicit_operation_uncertainty(self):
        self.assertEqual(len(self.companies),59);self.assertEqual(len({c['record_id'] for c in self.companies}),59)
        self.assertEqual(sum(self.report['summary']['relevance'].values()),59)
        for c in self.companies:
            self.assertTrue(c['evidence']);self.assertTrue(c['classification_basis']);self.assertTrue(c['operation_note']);self.assertTrue(c['rights_status']);self.assertTrue(c['human_review_questions']);self.assertIn(c['relevance'],gate.GROUPS);self.assertIsNone(c['human_decision']);self.assertFalse(c['human_approved'])
    def test_known_non_studio_and_unresolved_name_are_staged_but_not_erased(self):
        staged={c['operating_name'] for c in self.companies if c['publication_readiness'].startswith('staged_')};self.assertEqual(staged,{'Melodics','Level'})
        ids={c['record_id'] for c in self.companies if c['operating_name'] in staged}
        self.assertEqual(set(self.manifest['nz_quality_gate']['staged_ids']),ids)
        self.assertFalse(ids&{r['id'] for r in self.current});self.assertTrue(ids<={r['id'] for r in self.raw})
        self.assertEqual(self.manifest['counts']['records'],42296)
    def test_agency_and_unspecified_rights_are_distinguished_without_a_blanket_factual_ban(self):
        self.assertEqual(sum(c['publication_readiness']=='eligible_source_authorised_identity' for c in self.companies),30)
        minimal=[c for c in self.companies if c['publication_readiness']=='eligible_minimal_factual_reference'];self.assertEqual(len(minimal),27)
        self.assertTrue(all(c['requires_maintainer_rights_scope_review'] and c['original_source_license']=='UNSPECIFIED' for c in minimal))
        self.assertEqual(sum(r['license']=='UNSPECIFIED' for r in self.published),27)
        home=self.temp_home();data=read(home/'inputs/companies.json');c=next(c for c in data['companies'] if c['operating_name']=='Native Audio');c['evidence'][0]['rights']='NZ-On-Air-Permission';write(home/'inputs/companies.json',data)
        with self.assertRaisesRegex(ValueError,'Agency grant cannot cover'):gate.inputs(home)
    def test_programme_alone_cannot_gain_production_specialisation(self):
        home=self.temp_home();data=read(home/'inputs/companies.json');row=next(c for c in data['companies'] if c['operating_name']=='Balancing Monkey Games');row['relevance']='motionx_core';write(home/'inputs/companies.json',data)
        with self.assertRaisesRegex(ValueError,'Programme receipt alone'):gate.inputs(home)
    def test_playtesting_is_game_production_support_not_inferred_game_development(self):
        row=next(r for r in self.published if r['name']=='Insight Creative');self.assertEqual(row['categories'],['Game Production Support']);self.assertEqual(row['research_review']['relevance'],'supporting_services')
        self.assertTrue(any('our-year-in-review-2024-2025' in p['url'] for p in row['source_provenance']))
        self.assertEqual(row['capabilities'],[])
    def test_company_marketing_cannot_become_a_facility_capability_or_approval(self):
        self.assertEqual(len(self.published),57)
        for row in self.published:
            self.assertEqual(row['evidence_class'],'C');self.assertEqual(row['record_kind'],'company_reference');self.assertIsNone(row['lat']);self.assertIsNone(row['lng']);self.assertFalse(row['capabilities']);self.assertFalse(row['capability_evidence']);self.assertFalse(row['verified_on']);self.assertFalse(row['research_review']['human_approved']);self.assertFalse(row['research_review']['facility_verified'])
        for field,value in [('human_approved',True),('facility_verified',True),('publication_state','approved'),('relevance','out_of_scope')]:
            row=copy.deepcopy(self.published[0]);row['research_review'][field]=value;self.assertTrue(validate_research([row]))
    def test_27_original_keys_plus_office_closure_are_reviewed_without_automatic_merges(self):
        self.assertEqual(len(self.identities),28);self.assertEqual(sum(self.report['summary']['identity_outcomes'].values()),27)
        byname={i['source_name']:i for i in self.identities}
        for name in ['Geo AR','Runaway Play','Staples Productions']:self.assertEqual(byname[name]['resolution'],'supported_proposed_alias');self.assertTrue(byname[name]['proposed_match_candidates'])
        self.assertIn('global',byname['Niantic Aotearoa NZ']['recommendation']);self.assertEqual(byname['Niantic Aotearoa NZ']['evidence'][0]['source_published_on'],'2026-07-07')
        self.assertIn('Canadian',byname['Beyond Fun']['recommendation']);self.assertIn('parent',byname['Blind Squirrel Entertainment']['recommendation'])
    def test_facility_dossiers_keep_municipalities_no_geocodes_and_sale_uncertainty(self):
        places={f['name']:f['municipality'] for f in self.facilities};self.assertEqual(set(places.values()),{'Lower Hutt','Upper Hutt','Wellington','Rotorua'})
        for f in self.facilities:self.assertIsNone(f['lat']);self.assertIsNone(f['lng']);self.assertFalse(f['human_approved']);self.assertEqual(f['independent_facility_review'],'not_completed');self.assertTrue(f['coordinate_rationale'])
        lane=next(f for f in self.facilities if f['name']=='Lane Street Studios');self.assertIn('sale',lane['current_operation']);self.assertTrue(any('not a closure' in x for x in lane['unverified_aspects']))
    def test_human_working_sheet_is_91_pending_items_not_fabricated_review(self):
        worksheet=self.report['worksheet'];self.assertEqual(len(worksheet['items']),91);self.assertFalse(worksheet['human_approved']);self.assertEqual(worksheet['human_review_completed'],0)
        self.assertTrue(all(i['human_decision'] is None and i['human_reviewer'] is None for i in worksheet['items']))
        self.assertEqual(len(read(ROOT/'data/nz-census/reports/human-review.json')['rows']),29)
        self.assertEqual(sha(ROOT/'data/annecy/reports/human-precision-review.json'),self.parent['annecy_worksheet_sha256'])
    def test_pre_v15_ids_shards_root_and_original_service_labels_are_unchanged(self):
        cfg=read(ROOT/'data/nz-census/release.json');base=[r for r in self.current if not r['id'].startswith('nzcensus-')]
        self.assertEqual(len(base),42239);self.assertEqual(digest(sorted(r['id'] for r in base)),cfg['baseline_ids_sha256']);self.assertEqual(sha(ROOT/'studios.json'),cfg['retained_baseline_sha256'])
        for name,h in cfg['retained_shard_hashes'].items():self.assertEqual(sha(ROOT/'data/public'/name),h)
        old={r['id']:r for r in self.raw}
        for r in self.published:self.assertEqual(r['source_category'],old[r['id']]['source_category']);self.assertEqual(r['company_id'],old[r['id']]['company_id'])
    def test_changed_source_record_or_human_approval_cannot_be_silently_applied(self):
        home=self.temp_home();data=read(home/'inputs/companies.json');data['companies'][0]['human_approved']=True;write(home/'inputs/companies.json',data)
        with self.assertRaisesRegex(ValueError,'cannot fill human'):gate.inputs(home)
        data['companies'][0]['human_approved']=False;data['companies'][0]['private_contact']='must not be copied';write(home/'inputs/companies.json',data)
        with self.assertRaisesRegex(ValueError,'Unsupported/private fields'):gate.inputs(home)
        data['companies'][0].pop('private_contact');data['companies'][0]['original_record_hash']='a'*64;write(home/'inputs/companies.json',data)
        with self.assertRaisesRegex(ValueError,'stale'):gate.inputs(home)
    def test_changed_facility_pin_or_scope_cannot_enter_public_projection(self):
        home=self.temp_home();data=read(home/'inputs/facilities.json');data['facilities'][0]['lat']=-41.;write(home/'inputs/facilities.json',data)
        with self.assertRaisesRegex(ValueError,'cannot create a pin'):gate.inputs(home)
        shutil.copyfile(gate.HOME/'inputs/facilities.json',home/'inputs/facilities.json');data=read(home/'inputs/companies.json');next(c for c in data['companies'] if c['operating_name']=='Melodics')['publication_readiness']='eligible_source_authorised_identity';write(home/'inputs/companies.json',data)
        with self.assertRaisesRegex(ValueError,'Out-of-scope'):gate.inputs(home)
    def test_repeat_apply_and_stale_input_hashes_are_rejected(self):
        with self.assertRaisesRegex(ValueError,'repeated application refused'):gate.apply(ROOT/'data/public',ROOT/'studios.json')
        home=self.temp_home();write(home/'release.json',read(gate.HOME/'release.json'));(home/'inputs/companies.json').write_text('{}')
        with self.assertRaisesRegex(ValueError,'checkpoint changed'):gate.checkpoint(home)
    def test_review_html_escaping_and_working_csv_formula_safety(self):
        report=copy.deepcopy(self.report);report['worksheet']['items'][0]['name']='<script>alert(1)</script>'
        with tempfile.TemporaryDirectory() as t:
            gate.save(report,Path(t));text=(Path(t)/'dashboard.html').read_text();self.assertIn('&lt;script&gt;',text);self.assertNotIn('<script>alert',text)
        for s in ['=1','+cmd','-1','@cmd','\u200b=1',' \t+1']:self.assertTrue(gate.csv_safe(s).startswith("'"))
    def test_reports_are_deterministic_and_data_complete(self):
        with tempfile.TemporaryDirectory() as t:
            out=Path(t);gate.save(self.report,out);before={p.name:p.read_bytes() for p in out.iterdir()};gate.save(self.report,out);self.assertEqual(before,{p.name:p.read_bytes() for p in out.iterdir()})
        self.assertEqual(self.report['summary']['recommendation'],'READY FOR HUMAN REVIEW');self.assertFalse(self.report['summary']['human_approved']);self.assertFalse(self.report['summary']['census_complete'])

if __name__=='__main__':unittest.main()
