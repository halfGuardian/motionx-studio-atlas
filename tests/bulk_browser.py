"""HTTP browser and performance checks for the optional sharded catalogue.

Synthetic records live in a TemporaryDirectory only. Real source acquisition
counts must come from coverage.json, never this performance fixture.
"""
import copy,json,os,shutil,sys,tempfile,threading,time
from functools import partial
from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
from pathlib import Path
from playwright.sync_api import sync_playwright,expect

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
from bulk_catalog import build
from discovery import read

class Quiet(SimpleHTTPRequestHandler):
    def log_message(self,*_):pass

def fixture(i):
    # Two facilities share each original point; no artificial coordinate offsets.
    j=i//2
    url='https://synthetic-'+str(i)+'.example.test/fixture-only'
    return {'id':'synthetic-b-'+str(i),'company_id':'synthetic-org-'+str(i//4),'name':'Synthetic Production '+str(i),'city':'Fixture City '+str(i%20),'country':['New Zealand','Brazil','Japan','Kenya','Canada'][i%5],
        'lat':(j%200)*.8-80,'lng':(j//200)*2.8-175,'website':url,'address':'Synthetic benchmark point; never public data','categories':['Animation'],
        'capabilities':[],'capability_evidence':{},'evidence_state':'unknown','evidence_class':'B','evidence':url,'verified_on':'','source_observed_on':'2026-11-06',
        'coordinate_precision':'approximate','coordinate_source':url,'location_type':'uncertain','relationships':[],'status':'Synthetic benchmark only; never imported','website_kind':'official',
        'source_provenance':[{'source_id':'test-fixture','source_record_id':str(i),'url':url,'license':'CC0-1.0','license_url':'https://example.test/licence','observed_on':'2026-11-06','observation_hash':'a'*64}],
        'license':'CC0-1.0','attribution':'Synthetic test fixture, not acquired studio data','identity_status':'source_provisional'}

def main():
    checks=0
    def passed(s):
        nonlocal checks;checks+=1;print('PASS '+s,flush=True)
    with tempfile.TemporaryDirectory() as tmp:
        root=Path(tmp);site=root/'atlas';site.mkdir()
        for name in ('index.html','app.js','atlas.css','data.js','catalog.js','studios.json'):shutil.copyfile(ROOT/name,site/name)
        (site/'index.html').write_text((site/'index.html').read_text().replace('<html lang="en">','<html lang="en" data-catalog="sharded">'))
        rows=[fixture(i) for i in range(50000)]
        (site/'data').mkdir();manifest=build(rows,site/'studios.json',site/'data/public','a'*64,'synthetic-benchmark')
        server=ThreadingHTTPServer(('127.0.0.1',0),partial(Quiet,directory=str(root)));threading.Thread(target=server.serve_forever,daemon=True).start()
        url=f'http://127.0.0.1:{server.server_port}/atlas/'
        try:
            with sync_playwright() as p:
                browser=p.chromium.launch(executable_path=os.environ.get('CHROMIUM') or shutil.which('chromium'),headless=True,args=['--no-sandbox'])
                page=browser.new_page(viewport={'width':1440,'height':950},accept_downloads=True);errors=[];requests=[]
                page.on('pageerror',lambda e:errors.append(str(e)));page.on('request',lambda req:requests.append(req.url))
                start=time.monotonic();page.goto(url,wait_until='domcontentloaded');expect(page.locator('#count')).to_have_text('50230 locations',timeout=45000);ready=time.monotonic()-start
                assert not [r for r in requests if '/shards/' in r]
                assert page.locator('.entry').count()==50
                passed('50,000 synthetic B + 230 retained A searchable; no provenance shards fetched initially')
                assert page.evaluate('!!map')
                page.evaluate('() => {const r=directory.byId.get("synthetic-b-49999");map.setView([r.lat,r.lng],10,{animate:false});}')
                pan_ms=page.evaluate('MotionXPerformance.marker_render_ms')
                assert page.evaluate('layer.getLayers().length')<2000
                page.evaluate('() => layer.getLayers().find(m=>m.motionxLocations.includes("synthetic-b-49999")).openPopup()')
                expect(page.locator('.leaflet-popup-content li button')).to_have_count(2)
                page.locator('.leaflet-popup-content li button').filter(has_text='Synthetic Production 49999').press('Enter');expect(page.locator('#profileTitle')).to_have_text('Synthetic Production 49999');page.locator('#close').click()
                passed('viewport rendering and keyboard selection of two source-listed facilities at unchanged identical coordinates')
                requests.clear()
                expect(page.locator('#companies')).to_contain_text('provisional source identities')
                page.locator('#evidenceClass').select_option('B');expect(page.locator('#count')).to_have_text('50000 locations')
                page.locator('#confirmedOnly').check();expect(page.locator('#count')).to_have_text('0 locations');page.locator('#confirmedOnly').uncheck()
                page.locator('#country').select_option('Brazil');expect(page.locator('#count')).to_have_text('10000 locations')
                page.locator('#search').fill('Synthetic Production 49996');expect(page.locator('#count')).to_have_text('1 location')
                search_ms=page.evaluate('MotionXPerformance.search_ms');page.locator('[data-id="synthetic-b-49996"]').click();expect(page.locator('#profileTitle')).to_have_text('Synthetic Production 49996')
                expect(page.locator('#detailContent')).to_contain_text('Class B — Source-listed, not independently corroborated')
                expect(page.locator('#detailContent')).to_contain_text('No facility capability is confirmed')
                assert len([r for r in requests if '/shards/' in r])<=1
                profile_ms=page.evaluate('MotionXPerformance.profile_open_ms');passed('A/B and confirmed-only filters, lazy source evidence and safe Class B profile')
                page.locator('#close').click()
                with page.expect_download() as download:page.locator('#exportCsv').click()
                csv=Path(download.value.path()).read_text(encoding='utf-8-sig');assert 'synthetic-b-49996' in csv and 'source_provenance' in csv and 'CC0-1.0' in csv
                passed('filtered CSV obtains full licence/provenance, not compact stubs')
                page.locator('#resetFilters').click();page.locator('#search').fill('Synthetic Production 49999');expect(page.locator('#count')).to_have_text('1 location')
                page.locator('[data-id="synthetic-b-49999"]').click();expect(page.locator('#profileTitle')).to_have_text('Synthetic Production 49999')
                page.go_back();expect(page.locator('#detail')).to_be_hidden();page.go_forward();expect(page.locator('#profileTitle')).to_have_text('Synthetic Production 49999')
                page.goto(url+'#/location/synthetic-b-49999',wait_until='domcontentloaded');expect(page.locator('#profileTitle')).to_have_text('Synthetic Production 49999')
                passed('direct source-listed profile URL, browser back/forward and cached shard navigation')
                page.set_viewport_size({'width':390,'height':844});page.locator('#close').click();page.locator('#listTab').click();page.locator('#evidenceClass').select_option('B');page.locator('#search').fill('Synthetic Production 49999');expect(page.locator('#count')).to_have_text('1 location');page.locator('[data-id="synthetic-b-49999"]').click();expect(page.locator('#profileTitle')).to_have_text('Synthetic Production 49999');assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
                passed('390px mobile shard profile, filters and horizontal containment')
                assert not errors,errors
                report={'kind':'synthetic_only_not_acquisition','synthetic_locations':50000,'baseline_retained':243,'baseline_class_a_visible':230,'legacy_research_only':13,'conditions':'Local HTTP subdirectory, installed headless Chromium, 1440x950 and 390x844, no CPU/network throttling; not a physical low-memory phone.',
                    'compact_index_bytes':manifest['index']['bytes'],'compact_index_gzip_bytes':(site/'data/public/index.json.gz').stat().st_size,'full_detail_bytes':sum(x['bytes'] for x in manifest['shards'].values()),'initial_ready_seconds':round(ready,3),'search_ms':search_ms,'profile_ms':profile_ms,'viewport_render_ms':pan_ms,'app_timings':page.evaluate('MotionXPerformance'),'checks':checks}
                Path('/tmp/motionx-v11-bulk-performance.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report),flush=True)
                browser.close()
        finally:server.shutdown();server.server_close()
    print(f'{checks} bulk HTTP browser checks passed',flush=True)
if __name__=='__main__':main()
