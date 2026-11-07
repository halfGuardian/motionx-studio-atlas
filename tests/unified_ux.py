"""Read-only HTTP checks of actual evidence UX, review tools and safe failures."""
import csv,io,json,os,shutil,threading,time
from functools import partial
from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
from pathlib import Path
from playwright.sync_api import sync_playwright,expect

ROOT=Path(__file__).resolve().parents[1]
class Quiet(SimpleHTTPRequestHandler):
    def log_message(self,*_):pass

def main():
    manifest=json.loads((ROOT/'data/public/manifest.json').read_text());counts=manifest['counts'];duplicate_count=manifest['warnings']['possible_duplicate_candidates'];total_text=str(counts['records'])+' records'
    server=ThreadingHTTPServer(('127.0.0.1',0),partial(Quiet,directory=str(ROOT.parent)));threading.Thread(target=server.serve_forever,daemon=True).start();url=f'http://127.0.0.1:{server.server_port}/{ROOT.name}/';checks=0;report={}
    def passed(text):
        nonlocal checks;checks+=1;print('PASS '+text,flush=True)
    try:
        with sync_playwright() as p:
            browser=p.chromium.launch(executable_path=os.environ.get('CHROMIUM') or shutil.which('chromium'),headless=True,args=['--no-sandbox'])
            context=browser.new_context(viewport={'width':1440,'height':950},accept_downloads=True);page=context.new_page();errors=[];page.on('pageerror',lambda error:errors.append(str(error)))
            page.goto(url,wait_until='domcontentloaded');expect(page.locator('#count')).to_have_text(total_text,timeout=45000);expect(page.locator('#evidenceLegend')).to_be_visible()
            for cls,colour,shape in [('A','#238B67','rect'),('B','#347FBA','circle'),('C','#B58A2A','polygon')]:
                page.locator('[data-quick="'+cls+'"]').click();expect(page.locator('#count')).to_have_text(str(counts['class_'+cls.lower()])+' records')
                target=page.evaluate('''()=>{const r=D.coordinateGroups(matches.filter(hasPoint)).find(g=>g.length===1)[0];map.setView([r.lat,r.lng],19,{animate:false});const m=layer.getLayers().find(m=>m.motionxLocations.includes(r.id));if(m.motionxLocations.length!==1)throw Error('Expected isolated marker');m.getElement().dataset.testTarget='shape';return {name:r.name,id:r.id};}''')
                marker=page.locator('[data-test-target="shape"]');expect(marker).to_have_attribute('role','button');expect(marker).to_have_attribute('data-evidence',cls)
                assert marker.locator('svg '+shape).get_attribute('fill') is None # fill is inherited from the SVG group
                assert marker.locator('svg g').get_attribute('fill')==colour
                marker.focus();marker.press('Space');expect(page.locator('#profileTitle')).to_have_text(target['name']);expect(page.locator('#detailContent .evidence-badge').first).to_have_attribute('data-evidence',cls);page.locator('#close').click()
            passed('exact A/B/C colours, distinct SVG shapes, class-aware quick filters and Space-key profile selection')
            page.locator('[data-quick="all"]').click();expect(page.locator('#count')).to_have_text(total_text);page.evaluate('map.setView([28,-25],2,{animate:false})')
            mixed=page.evaluate('''()=>{const m=layer.getLayers().find(m=>{const c=D.evidenceCounts(m.motionxLocations.map(id=>directory.byId.get(id)));return c.A&&c.B&&c.C;});if(!m)throw Error('No actual mixed-class world cluster');m.getElement().dataset.testTarget='mixed';return m.getElement().getAttribute('aria-label');}''')
            assert 'directory-listed' in mixed and 'research leads' in mixed
            marker=page.locator('[data-test-target="mixed"]');marker.focus();marker.press('Enter');expect(page.locator('.leaflet-popup-content .evidence-breakdown')).to_contain_text('Class A');expect(page.locator('.leaflet-popup-content .evidence-breakdown')).to_contain_text('Class B');expect(page.locator('.leaflet-popup-content .evidence-breakdown')).to_contain_text('Class C')
            page.locator('.leaflet-popup-content li button').first.press('Enter');expect(page.locator('#profileTitle')).to_be_visible();page.locator('#close').click()
            passed('actual mixed-class clusters expose A/B/C composition and selectable records through Enter')
            page.locator('[data-quick="companies"]').click();expect(page.locator('#count')).to_have_text(str(counts['company_references'])+' records');assert page.evaluate('layer.getLayers().length')==0;assert page.locator('#fitResults').is_enabled()==bool(manifest.get('global_visibility'));expect(page.locator('#catalogSummary')).to_contain_text('40,619');expect(page.locator('#catalogSummary')).to_contain_text('230')
            assert page.evaluate('matches.every(r=>r.record_kind==="company_reference"&&!hasPoint(r))')
            page.locator('[data-quick="capture"]').click();capture=page.evaluate('matches.length');assert capture>0;assert page.evaluate('matches.every(D.confirmedCapture)');report['confirmed_capture_quick_filter']=capture
            passed('original company coordinates remain absent; display references are separate; capture quick filter requires site-specific confirmed claims')
            page.locator('[data-quick="all"]').click();page.locator('#advancedFilters > summary').focus();page.locator('#advancedFilters > summary').press('Enter');assert page.locator('#advancedFilters').evaluate('(d)=>d.open')
            page.locator('#researchFocus').select_option('duplicates');expect(page.locator('#count')).to_have_text(str(duplicate_count)+' records');first=page.locator('#list .profile-link[data-id]').first;first.click();expect(page.locator('#detailContent')).to_contain_text('Possible existing matches');page.locator('[data-compare-pair]').first.click();expect(page.locator('#profileTitle')).to_have_text('Compare research records');expect(page.locator('.comparison-record')).to_have_count(2);expect(page.locator('#detailContent')).to_contain_text('does not merge');page.locator('#close').click()
            passed('keyboard-accessible advanced controls, complete duplicate queue and source-preserving record comparison')
            page.locator('[data-quick="all"]').click();page.locator('#advancedFilters').evaluate('(d)=>d.open=true');page.locator('#country').select_option('New Zealand');expect(page.locator('#count')).not_to_have_text(total_text)
            with page.expect_download() as info:page.locator('#exportCsv').click()
            exported=list(csv.DictReader(io.StringIO(Path(info.value.path()).read_text(encoding='utf-8-sig'))));assert {r['evidence_class'] for r in exported}=={'A','B','C'};assert all(r['country']=='New Zealand' for r in exported);assert exported[0]['export_licences'];assert all(not r['lat'] and not r['lng'] for r in exported if r['record_kind']=='company_reference')
            passed('real mixed A/B/C CSV export retains provenance, licences, company references and original geography')
            page.locator('[data-quick="all"]').click();start=time.monotonic();page.reload(wait_until='domcontentloaded');expect(page.locator('#count')).to_have_text(total_text);report['warm_cache_ready_seconds']=round(time.monotonic()-start,3)
            page.screenshot(path='/tmp/motionx-v11-desktop.png');page.set_viewport_size({'width':390,'height':844});expect(page.locator('#evidenceLegend')).to_be_visible();page.screenshot(path='/tmp/motionx-v11-mobile-map.png');page.locator('#listTab').click();expect(page.locator('aside')).to_be_visible();expect(page.locator('.directory-legend')).to_be_visible();assert page.evaluate('document.documentElement.scrollWidth<=innerWidth');page.locator('[data-quick="C"]').click();page.locator('#list .profile-link[data-id]').first.click();expect(page.locator('#profileTitle')).to_be_visible();page.screenshot(path='/tmp/motionx-v11-mobile-profile.png');page.locator('#close').click();page.screenshot(path='/tmp/motionx-v11-mobile-list.png')
            passed('390px map/list/profile layout, permanent map legend and warm hash-versioned cache navigation')
            audit=context.new_page();audit.goto(url+'data/bulk/reports/licensing.html',wait_until='domcontentloaded');expect(audit.locator('h1')).to_contain_text('Licensing');game=audit.locator('article').filter(has_text='Game Studios & Publishers Database');expect(game).to_contain_text('Permission not established');expect(game).to_contain_text('UNSPECIFIED');expect(audit.locator('body')).to_contain_text('repository and GitHub Pages remain public');assert audit.evaluate('document.documentElement.scrollWidth<=innerWidth');audit.close()
            passed('licensing dashboard retains unresolved company-source permissions and public-access boundary')
            # Independent fresh context: a truncated index cannot reveal partial
            # source results or silently fall back to the old baseline/index.
            failed_context=browser.new_context(viewport={'width':390,'height':844});failed=failed_context.new_page();requests=[];failed.on('request',lambda r:requests.append(r.url));packed=(ROOT/'data/public/index.compact.json.gz').read_bytes()
            failed.route('**/data/public/index.compact.json.gz?*',lambda route:route.fulfill(status=200,content_type='application/octet-stream',body=packed[:len(packed)//2]))
            failed.goto(url,wait_until='domcontentloaded');expect(failed.locator('#count')).to_have_text('Studio data unavailable',timeout=45000);expect(failed.locator('#search')).to_be_disabled();expect(failed.locator('#retryLoad')).to_be_visible();assert failed.locator('#list .entry').count()==0;assert not any('/data/public/index.json' in r for r in requests)
            failed.unroute('**/data/public/index.compact.json.gz?*');failed.locator('#retryLoad').click();expect(failed.locator('#count')).to_have_text(total_text,timeout=45000);failed_context.close()
            passed('truncated compact-index download fails closed without partial results; full retry recovers every record')
            missing_context=browser.new_context(viewport={'width':390,'height':844});missing=missing_context.new_page();map_errors=[];missing.on('pageerror',lambda error:map_errors.append(str(error)));missing.route('**/leaflet.js',lambda route:route.abort('failed'));missing.goto(url,wait_until='domcontentloaded');expect(missing.locator('#count')).to_have_text(total_text,timeout=45000);expect(missing.locator('aside')).to_be_visible();expect(missing.locator('.directory-legend')).to_be_visible();assert 'Map library could not load' in missing.locator('#map').text_content();expect(missing.locator('#fitResults')).to_be_disabled();missing.locator('[data-quick="B"]').click();expect(missing.locator('#count')).to_have_text('4626 records');missing.locator('#list .profile-link[data-id]').first.click();expect(missing.locator('#profileTitle')).to_be_visible();assert not map_errors,map_errors;missing_context.close()
            passed('blocked Leaflet script leaves all records, filters and profiles usable in the mobile directory')
            assert not errors,errors;report.update(checks=checks,kind='actual_catalogue_ux_not_deployed_pages',conditions='Local HTTP subdirectory / installed headless Chromium, 1440x950 and 390x844, no CPU/network throttle; warm reload explicitly identified. Screenshots are proposed UI, not production.');Path('/tmp/motionx-v11-ux-performance.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report),flush=True);browser.close()
    finally:server.shutdown();server.server_close()
    print(f'{checks} unified UX browser checks passed',flush=True)
if __name__=='__main__':main()
