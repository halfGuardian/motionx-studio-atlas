"""Full-catalogue NZ reconciliation, access boundaries and immutable history."""
import copy,csv,io,json,sys,tempfile,unittest,shutil
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
import nz_research as nz
from discovery import read,write,digest
from catalogue_history import records
from bulk_catalog import sha
from validate import url_valid
from unified_catalog import validate_research

class CensusResearchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest,cls.all=records(ROOT/'data/public',ROOT/'studios.json')
        cls.base=[r for r in cls.all if not r['id'].startswith(nz.PREFIX)]
        cls.report=nz.check();cls.rows=cls.report['observations'];cls.new=cls.report['proposed_references']
    def named(self,name):return [r for r in self.rows if r['name']==name]

    def test_every_retained_and_added_source_row_has_traceable_outcome(self):
        self.assertEqual(len(self.rows),217);self.assertEqual(len({r['observation_id'] for r in self.rows}),217)
        self.assertEqual(sum(self.report['summary']['outcomes'].values()),217)
        _,old=nz.load_observations();current={r['observation_id']:r for r in self.rows}
        for row in old:
            for k,v in row.items():self.assertEqual(current[row['observation_id']][k],v)
        for row in self.rows:
            self.assertIn(row['disposition'],nz.DECISIONS);self.assertTrue(row['reason']);self.assertTrue(url_valid(row['source_url']));self.assertFalse(row['nz_facility_verified'])
        receipts=read(nz.HOME/'inputs/research-receipts.json')
        self.assertEqual(len(receipts['records']),42)

    def test_baseline_root_coordinates_evidence_ids_and_all_240_shards_unchanged(self):
        cfg=nz.checkpoint();self.assertEqual(len(self.base),42239)
        self.assertEqual(digest(sorted(r['id'] for r in self.base)),cfg['baseline_ids_sha256'])
        self.assertEqual(len(cfg['retained_shard_hashes']),240)
        for name,h in cfg['retained_shard_hashes'].items():self.assertEqual(sha(ROOT/'data/public'/name),h)
        self.assertEqual(sha(ROOT/'studios.json'),'ae9930e0ec522812c6bc189efc4b5beac48e781e6e60f8164172755e1259b4f4')
        self.assertEqual(self.manifest['counts']['retained_locations'],243)
        self.assertEqual(self.manifest['counts']['retained_operating_organisations'],119)

    def test_all_59_additions_are_company_only_not_capture_or_facility_verification(self):
        self.assertEqual(len(self.new),59);self.assertEqual(validate_research(self.new),[])
        for r in self.new:
            self.assertEqual(r['evidence_class'],'C');self.assertEqual(r['record_kind'],'company_reference')
            self.assertIsNone(r['lat']);self.assertIsNone(r['lng']);self.assertEqual(r['city'],'')
            self.assertEqual(r['capabilities'],[]);self.assertEqual(r['capability_evidence'],{})
            self.assertEqual(r['evidence_state'],'unknown');self.assertEqual(r['verified_on'],'');self.assertEqual(r['relationships'],[])
        self.assertEqual(self.report['summary']['new_map_points'],0);self.assertEqual(self.report['summary']['new_verified_capability_claims'],0)

    def test_documented_aliases_reconcile_without_duplicate_references(self):
        for name in ['A44','Fox & Co']:
            row=self.named(name)[0];self.assertIn(row['disposition'],('represented','represented_alias'));self.assertTrue(row['record_ids'])
        for row in self.new:self.assertNotIn(row['name'],['A44','Fox & Co'])
        fox=self.named('Fox & Co')[0];self.assertIn('overture-6c6b',fox['record_ids'][0]);self.assertTrue(fox['assessment']['identity_evidence_urls'])

    def test_foreign_assembly_and_stone_street_pins_never_become_nz_branches(self):
        byid={r['id']:r for r in self.base}
        for name in ['Assembly','Stone Street Studios']:
            row=self.named(name)[0];self.assertEqual(row['disposition'],'new_reference')
            self.assertTrue(row['matching']['foreign_ids']);self.assertNotIn(row['record_ids'][0],byid)
            for rid in row['matching']['foreign_ids']:self.assertNotEqual(byid[rid]['country'],'New Zealand')
        block=self.named('Blockhead');self.assertTrue(block);self.assertTrue(all(r['disposition']=='identity_hold' for r in block))
        self.assertFalse(any(r['name']=='Blockhead' for r in self.new))

    def test_ambiguous_operating_brands_and_wrong_country_stay_held(self):
        for name in ['Cause and FX','Cirkus','Beyond Fun','Rascal Kids']:
            self.assertTrue(any(r['disposition']=='identity_hold' for r in self.named(name)))
        metia=next(r for r in self.new if r['name']=='Metia Interactive');self.assertIn('metia.co.nz',metia['website']);self.assertNotIn('metia.com/',metia['website'])

    def test_multiple_programme_years_deduplicate_and_retain_all_periods(self):
        gov=[r for r in self.rows if r['source_id']=='nzonair-gdsr']
        from collections import Counter
        self.assertEqual(Counter(r['source_period'] for r in gov),{'2026':43,'2025':40,'2024':33})
        names=[r for r in gov if r['name']=='Balancing Monkey Games'];self.assertGreater(len(names),1)
        self.assertEqual(len({i for r in names for i in r['record_ids']}),1)
        target=next(r for r in self.new if r['id']==names[0]['record_ids'][0]);self.assertEqual(len(target['source_provenance']),len(names))
        historical=self.named('2Up Games');self.assertTrue(all(r['disposition']=='unresolved' for r in historical))
        self.assertFalse(any(r['name']=='2Up Games' for r in self.new))

    def test_closure_is_one_review_alert_not_a_global_deletion(self):
        closure=[r for r in self.rows if r['disposition']=='reported_nz_closure']
        self.assertEqual(len(closure),4);self.assertEqual(self.report['summary']['reported_nz_closure_identities'],1)
        self.assertFalse(any('Niantic' in r['name'] for r in self.new));self.assertEqual(len(self.base),42239)

    def test_original_service_codes_and_own_site_claims_remain_separate(self):
        old=self.named('POW Studios');row=next(r for r in old if r['source_id']=='nzfc-facilities');self.assertEqual(row['service_labels'],['PP','S','A','VFX'])
        graph=next(r for r in self.new if r['name']=='Graphic Monk Ltd');self.assertNotIn('DynaKinetix',json.dumps(graph));self.assertNotIn('motion capture',graph['source_category'].lower())
        self.assertTrue(any('motion' in x.lower() for r in self.named('Graphic Monk Ltd') for x in r['service_labels']))
        self.assertEqual(graph['capabilities'],[])

    def test_facility_proposals_keep_actual_municipalities_and_require_review(self):
        facilities={r['name']:r for r in self.report['facility_proposals']}
        self.assertEqual(facilities['Avalon Studios']['source_supported_city'],'Lower Hutt')
        self.assertEqual(facilities['Lane Street Studios']['source_supported_city'],'Upper Hutt')
        self.assertEqual(facilities['Te Whare Piringa Film Studio']['source_supported_city'],'Rotorua')
        for r in facilities.values():self.assertIsNone(r['lat']);self.assertFalse(r['publication_approved']);self.assertEqual(r['independent_facility_review'],'not_completed')

    def test_permissions_are_scoped_and_restricted_sources_never_project_new_rosters(self):
        registry,policies,obs,a=nz.source_inputs()
        self.assertFalse(registry['automatic_collection'])
        for sid in ['waikato-screen','vfxg-nz']:self.assertFalse(any(o['source_id']==sid for o in obs))
        for o in obs:
            if o['source_id']=='film-otago-southland-selected':self.assertEqual(o['origin'],'historical_wave1')
        eligible=[s for s in self.report['summary']['sources'].values() if s['eligible_complete_reusable_snapshot']];self.assertEqual(len(eligible),1);self.assertIn('NZ On Air',eligible[0]['name'])
        grant=(ROOT/'data/bulk/LICENSES/NZ-On-Air-Permission.txt').read_text();self.assertIn('https://www.nzonair.govt.nz/copyright-and-terms-use/',grant)
        self.assertNotIn('CC-BY-4.0',policies['nzonair-gdsr']['license'])

    def test_new_restricted_rows_cannot_masquerade_as_historical_or_approved(self):
        with tempfile.TemporaryDirectory() as t:
            home=Path(t)/'nz';shutil.copytree(nz.HOME/'inputs',home/'inputs');shutil.copyfile(nz.HOME/'sources.json',home/'sources.json')
            leads=read(home/'inputs/regional-leads.json');leads['records'][0].update(source_id='waikato-screen',origin='historical_wave1')
            write(home/'inputs/regional-leads.json',leads)
            with self.assertRaisesRegex(ValueError,'Restricted source'):nz.source_inputs(home)
            shutil.copyfile(nz.HOME/'inputs/regional-leads.json',home/'inputs/regional-leads.json')
            assessments=read(home/'inputs/assessments.json');assessments['records'][0]['human_approved']=True;write(home/'inputs/assessments.json',assessments)
            with self.assertRaisesRegex(ValueError,'cannot grant verification'):nz.source_inputs(home)
            registry=read(home/'sources.json');registry['automatic_collection']=True;write(home/'sources.json',registry)
            with self.assertRaisesRegex(ValueError,'No collector'):nz.source_inputs(home)

    def test_mixed_dynamic_snapshots_and_missing_pages_cannot_claim_full_enumeration(self):
        good=dict(declared_complete=True,stable_snapshot=True,unavailable_pages=0,overlap_conflicts=0,enumerated_rows=116,expected_rows=116)
        self.assertTrue(nz.enumeration_eligible(good,'accurate_attributed_reproduction_permitted'))
        for diff in [dict(stable_snapshot=False),dict(unavailable_pages=1),dict(overlap_conflicts=1),dict(enumerated_rows=0),dict(expected_rows=None),dict(declared_complete=False)]:
            self.assertFalse(nz.enumeration_eligible({**good,**diff},'accurate_attributed_reproduction_permitted'))
        self.assertFalse(nz.enumeration_eligible(good,'commercial_reuse_restricted'))

    def test_provenance_leads_are_indexed_but_do_not_establish_geography(self):
        row=copy.deepcopy(self.base[-1]);row.update(id='lead',name='Other Brand',country='Australia',source_provenance=[{'source_id':'example','source_record_id':'1'}])
        i=nz.NZIdentityIndex([row]);match=nz.identity(i,dict(name='Unresolved Company',site_url='',source_id='example',observation_id='example:1'))
        self.assertEqual(match['provenance_candidate_ids'],['lead']);self.assertEqual(match['nz_ids'],[])

    def test_reapply_is_refused_and_stale_checkpoint_cannot_grant_approval(self):
        with self.assertRaisesRegex(ValueError,'repeated application refused'):nz.extend(ROOT/'data/public',ROOT/'studios.json')
        with tempfile.TemporaryDirectory() as t:
            home=Path(t);write(home/'release.json',{'historical_nzfc_sha256':sha(ROOT/'data/coverage/nzfc-2026-11-07.json'),'input_hashes':{'changed.json':'f'*64}});write(home/'changed.json',{})
            with self.assertRaisesRegex(ValueError,'checkpoint changed'):nz.checkpoint(home)
        h=read(nz.HOME/'reports/human-review.json');self.assertEqual(h['reviewed'],0);self.assertIsNone(h['precision']);self.assertFalse(h['publication_approved'])
        self.assertTrue(all(r['reviewer'] is None and r['decision'] is None for r in h['rows']))
        self.assertFalse(self.report['summary']['census_complete'])

    def test_duplicate_metadata_is_usable_by_profiles_and_comparison(self):
        collision=next(r for r in self.new if r['potential_duplicates'])
        for r in self.new:
            for match in r['potential_duplicates']:
                self.assertTrue(match['ids']);self.assertTrue(match['reasons']);self.assertTrue(all(isinstance(x,str) for x in match['reasons']))
        bad=copy.deepcopy(collision);bad['potential_duplicates'][0].pop('reasons')
        self.assertTrue(any('duplicate review metadata' in e for e in validate_research([bad])))
        bad['potential_duplicates']='invalid'
        self.assertTrue(any('duplicate review metadata' in e for e in validate_research([bad])))

    def test_report_output_is_deterministic_escaped_and_formula_safe(self):
        report=copy.deepcopy(self.report);report['observations'][0]['name']='<script>alert(1)</script>';report['observations'][0]['reason']='=HYPERLINK("bad")'
        with tempfile.TemporaryDirectory() as t:
            output=Path(t);nz.save(report,output);first={p.name:p.read_bytes() for p in output.iterdir()};nz.save(report,output)
            self.assertEqual(first,{p.name:p.read_bytes() for p in output.iterdir()});page=(output/'coverage.html').read_text();self.assertNotIn('<script>alert',page);self.assertIn('&lt;script&gt;',page)
            rows=list(csv.DictReader(io.StringIO((output/'reconciliation.csv').read_text())));self.assertTrue(rows[0]['reason'].startswith("'="));self.assertEqual(rows[0]['observed_on'],'2026-11-07')
        self.assertTrue(all(nz.safe_csv(v).startswith("'") for v in ['=1',' +1','-1','@x']))

if __name__=='__main__':unittest.main()
