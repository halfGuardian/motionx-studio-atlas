"""Bulk research must preserve provenance and never manufacture verification."""
import copy,csv,json,sqlite3,struct,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import Mock,patch

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
import bulk_collect as collect
import bulk_ingest as bulk
import bulk_batch as batch
import bulk_archive as archive
import bulk_catalog as catalog
import bulk_snapshot as snapshot
from discovery import read,write,digest

def policy():
    p=copy.deepcopy(next(s for s in read(ROOT/'data/bulk/sources.json')['sources'] if s['id']=='overture'))
    p['eligible_categories']={'film_studio':'Film Production'};return p

def place(key='one',name='Test Production',city='Test City',**values):
    return {'source_record_id':key,'name':name,'category':'film_studio','geometry_wkb':(b'\x01'+struct.pack('<Idd',1,10.,20.)).hex(),
        'websites':['https://example.test/'+key], 'addresses':[{'country':'NZ','locality':city}],
        'sources':[{'dataset':'Meta','record_id':key,'property':''}], 'confidence':.99,'operating_status':'open',
        'filename':'https://overturemaps-us-west-2.s3.amazonaws.com/release/'+policy()['release']+'/theme=places/type=place/a.parquet',**values}

class BulkTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
        self.config={'sources':[policy()]}
    def snapshot(self,records,key='places-00000',observed='2026-11-06'):
        folder=self.root/'input'/'overture';write(folder/(key+'.json'),records)
        write(folder/(key+'.meta.json'),{'source':'overture','license':'per-provider','observed_on':observed,'projection_hash':digest(records)})
    def run_ingest(self,suffix='1',base=None):
        with patch('builtins.print'):
            return bulk.ingest(self.root/'input',self.root/('out'+suffix),self.config,base or [],self.root/'ledger.sqlite')
    def test_source_listed_never_verified_or_capture(self):
        self.snapshot([place()]);r=self.run_ingest();self.assertEqual(r['candidate_classes'],{'B':1});self.assertEqual(r['published_records'],0)
        row=read(self.root/'out1/proposed-b.json')[0]
        self.assertEqual(row['evidence_class'],'B');self.assertEqual(row['capabilities'],[]);self.assertEqual(row['verified_on'],'')
        self.assertEqual(row['source_provenance'][0]['observed_on'],'2026-11-06')
    def test_geometry_is_original_not_bbox(self):
        r=bulk.normalize_overture(place(lat=-55,lng=-120),'2026-11-06',policy())
        self.assertEqual((r['lat'],r['lng']),(20,10))
        r=bulk.normalize_overture(place(geometry_wkb=None,lat=20,lng=10),'2026-11-06',policy())
        self.assertEqual(r['class'],'C');self.assertIsNone(r['lat'])
    def test_ineligible_category_and_unknown_licence_deferred(self):
        for values in ({'category':'photo_shop'},{'sources':[{'dataset':'Unreviewed provider'}]},{'operating_status':'permanently_closed'},{'confidence':.5},{'confidence':True},{'confidence':float('nan')},{'addresses':[]}):
            self.assertEqual(bulk.normalize_overture(place(**values),'2026-11-06',policy())['class'],'C')
    def test_existing_and_within_batch_duplicate_are_not_overwritten(self):
        self.snapshot([place('one'),place('two')]);base=[{'id':'existing','company_id':'known','name':'Test Production','city':'Test City','country':'New Zealand','website':'https://example.test'}];before=copy.deepcopy(base)
        r=self.run_ingest(base=base);self.assertEqual(r['candidate_classes'],{'C':2});self.assertEqual(base,before)
        self.assertEqual(read(self.root/'out1/proposed-b.json'),[])
    def test_same_name_different_business_is_not_merged_into_retained_organisation(self):
        self.snapshot([place(city='Other City')]);base=[{'id':'existing','company_id':'different-company','name':'Test Production','city':'Far City','country':'United Kingdom','website':'https://different.example.test','lat':55.,'lng':0.}]
        result=self.run_ingest(base=base);row=read(self.root/'out1/proposed-b.json')[0]
        self.assertEqual(result['candidate_classes'],{'B':1});self.assertNotEqual(row['company_id'],'different-company');self.assertEqual(row['identity_status'],'source_provisional')
    def test_supplied_http_domain_is_identity_hint_without_invented_https_link(self):
        self.snapshot([place(name='Source brand variation',websites=['http://example.test/'])]);base=[{'id':'existing','company_id':'known','name':'Operating Brand','city':'Test City','country':'New Zealand','website':'https://example.test/','lat':20.,'lng':10.}]
        result=self.run_ingest(base=base);self.assertEqual(result['candidate_classes'],{'C':1})
        c=json.loads((self.root/'out1/candidates.jsonl').read_text());self.assertEqual(c['website_kind'],'source_listing');self.assertEqual(c['existing_organisation_matches'],['known'])
    def test_two_facilities_same_city_remain_in_audit(self):
        self.snapshot([place('one'),place('two')]);r=self.run_ingest()
        self.assertEqual(r['unique_candidate_identities'],2);self.assertEqual(r['candidate_classes'],{'B':1,'C':1})
        self.assertEqual(len((self.root/'out1/candidates.jsonl').read_text().splitlines()),2)
    def test_repeat_import_and_incremental_history(self):
        self.snapshot([place()]);first=self.run_ingest();second=self.run_ingest('2')
        self.assertEqual(first['run_id'],second['run_id']);self.assertEqual(second['previously_seen_observation_versions'],1)
        self.assertEqual(read(self.root/'out1/proposed-b.json'),read(self.root/'out2/proposed-b.json'))
        self.snapshot([place(name='Changed source name')]);third=self.run_ingest('3')
        self.assertNotEqual(first['run_id'],third['run_id'])
        with sqlite3.connect(self.root/'ledger.sqlite') as db:
            self.assertEqual(db.execute('select count(*) from observations').fetchone()[0],2)
            self.assertEqual(db.execute('select count(*) from runs').fetchone()[0],2)
    def test_dates_are_per_record_not_last_page_and_cache_not_freshened(self):
        self.snapshot([place('one')],observed='2026-10-21');self.snapshot([place('two','Other Company','Other City',websites=[])],'places-00001')
        self.run_ingest();rows=read(self.root/'out1/proposed-b.json')
        self.assertEqual([r['source_observed_on'] for r in rows],['2026-10-21','2026-11-06'])
    def test_corruption_stops_processing(self):
        self.snapshot([place()]);write(self.root/'input/overture/places-00000.json',[])
        with self.assertRaisesRegex(ValueError,'hash'):self.run_ingest()
        self.assertFalse((self.root/'out1').exists())
    def test_conflicting_source_versions_are_audited_not_silently_coalesced(self):
        self.snapshot([place()]);self.snapshot([place(name='Conflicting facility name')],'places-00001')
        result=self.run_ingest();self.assertEqual(result['candidate_classes'],{'C':1});self.assertEqual(result['conflicting_source_identities'],1);self.assertEqual(result['duplicate_source_observations_coalesced'],0)
        c=json.loads((self.root/'out1/candidates.jsonl').read_text());self.assertEqual(len(c['conflicting_source_versions']),2)
    def test_disabled_source_not_processed_and_policy_required(self):
        self.snapshot([place()]);self.config['sources'][0]['enabled']=False
        self.assertEqual(self.run_ingest()['raw_source_records'],0)
        self.config['sources'][0]['enabled']=True;self.config['sources'][0].pop('review')
        with self.assertRaisesRegex(ValueError,'review'):self.run_ingest('2')
    def test_csv_formula_is_escaped_and_html_not_injected(self):
        self.snapshot([place(name='=2+5<img src=x>')]);self.run_ingest()
        with (self.root/'out1/candidates.csv').open() as f:row=list(csv.DictReader(f))[0]
        self.assertTrue(row['name'].startswith("'="))
        self.assertNotIn('<img src=x>',(self.root/'out1/coverage.html').read_text())
    def test_country_aliases_and_invalid_coords(self):
        self.assertEqual(bulk.country('NZ'),'New Zealand');self.assertEqual(bulk.country('UK'),'United Kingdom')
        self.assertEqual(bulk.country('not a country'),'');self.assertIsNone(bulk.point('Point(181 12)'))
        self.assertIsNone(bulk.wkb_point('garbage'))
    def test_company_and_headquarters_are_not_physical_facilities(self):
        p={'id':'wikidata','license':'CC0-1.0','license_url':'https://www.wikidata.org/wiki/Wikidata:Licensing','attribution':'Wikidata'}
        r=bulk.normalize_wikidata({'source_record_id':'Q123','name':'Company','countries':[{'name':'Canada'}],'headquarters':[{'name':'Toronto','coordinate':'Point(1 2)'}]},'2026-11-06',p)
        self.assertEqual(r['class'],'C');self.assertIsNone(r['lat'])
    def test_no_official_source_claim_from_fallback_listing(self):
        r=bulk.normalize_overture(place(websites=[]),'2026-11-06',policy())
        self.assertEqual(r['website_kind'],'source_listing');self.assertEqual(r['website'],r['evidence_urls'][0])
    def test_overture_confidence_metadata_inherits_paired_provider_licence(self):
        raw=place();raw['sources'].append({'dataset':'Overture','property':'/properties/confidence'})
        r=bulk.normalize_overture(raw,'2026-11-06',policy());self.assertEqual(r['class'],'B');self.assertEqual(r['license'],'CDLA-Permissive-2.0')
        raw['sources'].append({'dataset':'Overture-signals','property':'/properties/operating_status'})
        self.assertEqual(bulk.normalize_overture(raw,'2026-11-06',policy())['class'],'C')

class NetworkTests(unittest.TestCase):
    def test_robots_denial_stops_before_query_no_fallback(self):
        client=Mock();client.robots.return_value=(False,{'allows':False})
        config={'sources':[{'id':'wikidata','enabled':True,'adapter':'wikidata_sparql','license':'CC0-1.0','endpoint':'https://query.wikidata.org/sparql','query_classes':{'Q21550789':'Film Production'}}]}
        with tempfile.TemporaryDirectory() as tmp,patch('builtins.print'):
            r=collect.collect(config,tmp,client)
        client.get.assert_not_called();self.assertFalse(r['sources'][0]['complete']);self.assertEqual(r['published_records'],0)
    def test_network_failure_never_creates_closure_or_deletes_history(self):
        client=Mock();client.robots.return_value=(True,{'allows':True});client.get.side_effect=OSError('network unavailable')
        config={'sources':[{'id':'openstreetmap','enabled':True,'adapter':'overpass','license':'ODbL-1.0','endpoint':'https://overpass-api.de/api/interpreter'}]}
        with tempfile.TemporaryDirectory() as tmp,patch('builtins.print'):
            path=Path(tmp)/'older.json';write(path,{'history':['retained']});r=collect.collect(config,tmp,client)
            self.assertEqual(read(path),{'history':['retained']})
        self.assertFalse(r['sources'][0]['complete']);self.assertIn('network',r['sources'][0]['errors'][0]['reason']);self.assertNotIn('closed',json.dumps(r))
    def test_private_dns_and_alternate_host_rejected(self):
        c=collect.Client()
        with self.assertRaisesRegex(ValueError,'origin'):c.get('https://other.example/api')
        with patch('bulk_collect.socket.getaddrinfo',return_value=[(None,None,None,None,('127.0.0.1',443))]):
            with self.assertRaisesRegex(ValueError,'DNS'):c.get('https://query.wikidata.org/sparql')
        with self.assertRaisesRegex(ValueError,'redirect'):collect.SameOrigin('query.wikidata.org').redirect_request(None,None,302,'',{},'https://other.example')
    def test_contacts_removed_from_osm_projection(self):
        rows=collect.clean_osm([{'type':'node','id':1,'tags':{'name':'Studio','phone':'private','email':'private','addr:street':'street','man_made':'studio'}}])
        self.assertEqual(set(rows[0]['tags']),{'name','man_made'})

class BatchTests(unittest.TestCase):
    def test_csv_json_bulk_and_approval_columns_rejected(self):
        policy={'id':'test-directory','enabled':True,'adapter':'licensed_batch','license':'CC0-1.0','license_url':'https://example.test/licence','review':'permitted bulk directory','policy_urls':['https://example.test/terms'],'attribution':'Test directory','physical_place_directory':True,'eligible_sectors':['Animation']}
        row={'source_record_id':'one','name':'Example Studio','city':'City','country':'NZ','lat':1,'lng':2,'website':'https://example.test','sectors':['Animation'],'source_url':'https://example.test/place/1'}
        with tempfile.TemporaryDirectory() as tmp,patch('builtins.print'):
            root=Path(tmp);write(root/'batch.json',[row,{**row,'source_record_id':'two','verified':True}]);r=batch.prepare(root/'batch.json',root/'input',policy['id'],{'sources':[policy]},'2026-11-06')
            self.assertEqual(r['accepted_observations'],1);self.assertEqual(len(r['rejected']),1)
            result=bulk.ingest(root/'input',root/'out',{'sources':[policy]},[])
            self.assertEqual(result['candidate_classes'],{'B':1})
            self.assertEqual(result['raw_source_records'],2);self.assertEqual(result['retained_source_observations'],1);self.assertEqual(result['rejected_malformed_records'],1);self.assertTrue(result['acquisition_complete'])
            with (root/'batch.csv').open('w',newline='') as f:
                w=csv.DictWriter(f,fieldnames=list(row));w.writeheader();w.writerow({**row,'sectors':'Animation'})
            r=batch.prepare(root/'batch.csv',root/'csv',policy['id'],{'sources':[policy]},'2026-11-06')
            self.assertEqual(r['accepted_observations'],1)
    def test_conflicting_source_identity_rejected_not_overwritten(self):
        with self.assertRaisesRegex(ValueError,'private'):batch.project({'source_record_id':'one','email':'no'})
        with self.assertRaisesRegex(ValueError,'stable'):batch.project({'name':'studio'})
        r=batch.project({'source_record_id':'one','name':'Test','lat':'not a number','lng':'2','sectors':'Animation|VFX'})
        self.assertIsNone(r['lat']);self.assertEqual(r['sectors'],['Animation','VFX'])

class CatalogueArchiveTests(unittest.TestCase):
    setUp=BulkTests.setUp
    snapshot=BulkTests.snapshot
    run_ingest=BulkTests.run_ingest
    def test_catalogue_preserves_all_ids_and_shards_original_geometry(self):
        self.snapshot([place()]);self.run_ingest();base=read(ROOT/'studios.json');write(self.root/'baseline.json',base)
        rows=read(self.root/'out1/proposed-b.json');m=catalog.build(rows,self.root/'baseline.json',self.root/'public',digest(self.config),'run')
        self.assertEqual(m['baseline']['retained_records'],243);self.assertEqual(m['counts']['class_a'],230)
        self.assertEqual(m['counts']['retained_legacy_research'],13);self.assertEqual(m['counts']['class_b'],1)
        index=read(self.root/'public/index.json');self.assertEqual(index[0][5:7],[20,10]);self.assertEqual(len(index[0]),11)
        self.assertEqual(read(self.root/'baseline.json'),base);self.assertFalse(m['publication_approved'])
    def test_verified_claims_or_existing_identity_cannot_enter_b_catalogue(self):
        self.snapshot([place()]);self.run_ingest();row=read(self.root/'out1/proposed-b.json')[0]
        self.assertEqual(catalog.validate_b([row])[0],[])
        for changes in ({'verified_on':'2026-11-06'},{'evidence_class':'A'},{'capabilities':['Motion Capture']},{'email':'private@example.test'},{'source_provenance':[]}):
            self.assertTrue(catalog.validate_b([{**row,**changes}])[0])
        write(self.root/'base.json',[row])
        with self.assertRaisesRegex(ValueError,'overwrite'):catalog.build([row],self.root/'base.json',self.root/'public','policy','run')
    def test_archive_round_trip_and_expired_artifact_recovery(self):
        self.snapshot([place()]);self.run_ingest()
        m=archive.archive(self.root/'input',self.root/'out1',self.root/'archive','1234')
        restored=archive.restore(self.root/'archive',self.root/'restored');self.assertEqual(m,restored)
        self.assertEqual(read(self.root/'restored/snapshots/overture/places-00000.json'),[place()])
        with patch('builtins.print'):r=bulk.ingest(self.root/'restored/snapshots',self.root/'rebuilt',self.config,[])
        self.assertEqual(r['candidate_classes'],{'B':1});self.assertEqual(r['published_records'],0)
    def test_corrupt_or_missing_archive_never_yields_partial_state(self):
        self.snapshot([place()]);self.run_ingest();m=archive.archive(self.root/'input',self.root/'out1',self.root/'archive','1234')
        path=self.root/'archive'/m['files'][0]['path'];path.write_bytes(b'broken')
        with self.assertRaisesRegex(ValueError,'integrity'):archive.restore(self.root/'archive',self.root/'restored')
        self.assertFalse((self.root/'restored').exists());path.unlink()
        with self.assertRaises(FileNotFoundError):archive.restore(self.root/'archive',self.root/'restored')
    def test_disappearing_records_or_changed_sources_never_delete_existing_b(self):
        self.snapshot([place()]);self.run_ingest();write(self.root/'base.json',read(ROOT/'studios.json'));records=read(self.root/'out1/proposed-b.json')
        first=self.root/'public1';catalog.build(records,self.root/'base.json',first,'policy','run1')
        second=self.root/'public2';m=catalog.build([],self.root/'base.json',second,'policy','failed-source',first)
        self.assertEqual(m['counts']['class_b'],1);self.assertEqual(catalog.existing_catalog(second),records)
        changed=[{**records[0],'name':'Unreviewed new name'}];third=self.root/'public3';catalog.build(changed,self.root/'base.json',third,'policy','run3',second)
        self.assertEqual(catalog.existing_catalog(third),records);self.assertEqual(len(read(third/'audit.json')['incremental_audit']['updates_deferred']),1)
        fourth=self.root/'public4';catalog.build(records,self.root/'base.json',fourth,'policy','repeat',third)
        self.assertEqual(read(fourth/'index.json'),read(first/'index.json'))
    def test_duplicate_reports_bound_pair_detail_without_discarding_records(self):
        from validate import DuplicateIndex
        index=DuplicateIndex([{'id':'same-'+str(i),'company_id':'same','name':'same','city':'City','country':'Country','website':'https://example.test'} for i in range(1000)])
        matches=index.matches({'id':'other','company_id':'same','name':'same','city':'City','country':'Country','website':'https://example.test'})
        self.assertEqual(len(matches),20);self.assertEqual(matches[0]['additional_group_matches']['website/city'],980)
    def test_public_projection_withholds_unresolved_overlay_but_preserves_identity_hash(self):
        raw=place();raw['sources']+=[{'dataset':'Overture','property':'/properties/confidence'},{'dataset':'Overture-signals','property':'/properties/operating_status'}];self.snapshot([raw])
        report=snapshot.project(self.root/'input',self.root/'safe');self.assertEqual(report['status_overlays_withheld'],1)
        clean=read(self.root/'safe/overture/places-00000.json')[0];self.assertEqual(clean['source_record_id'],raw['source_record_id']);self.assertEqual(clean['original_observation_hash'],digest(raw))
        self.assertIsNone(clean['operating_status']);self.assertNotIn('Overture-signals',[s['dataset'] for s in clean['sources']])
        self.assertEqual(bulk.normalize_overture(clean,'2026-11-06',policy())['class'],'C')
    def test_social_subdomains_are_not_republished_as_official_company_websites(self):
        self.assertFalse(snapshot.safe_website('https://m.facebook.com/profile.php?id=123'))
        self.assertFalse(snapshot.safe_website('https://m.youtube.com/channel/test'))
        self.assertTrue(snapshot.safe_website('https://studio.example.test/'))
    def test_municipality_alias_near_existing_city_reference_is_deferred(self):
        self.snapshot([place(city='Neighbouring Municipality')]);base=[{'id':'existing','company_id':'existing-org','name':'Test Production','city':'Marketed Metro','country':'New Zealand','website':'https://example.test','lat':20.1,'lng':10.1}]
        r=self.run_ingest(base=base);self.assertEqual(r['candidate_classes'],{'C':1});self.assertEqual(r['potential_existing_duplicates'],1)

if __name__=='__main__':unittest.main()
