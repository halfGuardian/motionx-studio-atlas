from public_scope import visible_counts
"""Annecy actual proposals over a GitHub Pages-style HTTP subdirectory."""
import csv,io,json,os,shutil,threading
from functools import partial
from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
from pathlib import Path
from playwright.sync_api import sync_playwright,expect
ROOT=Path(__file__).resolve().parents[1]
class Quiet(SimpleHTTPRequestHandler):
    def log_message(self,*_):pass

def main():
    manifest=json.loads((ROOT/'data/public/manifest.json').read_text());proposals=json.loads((ROOT/'data/annecy/reports/proposals.json').read_text())['company_references'];marmota=next(r for r in proposals if r['name']=='MARMOTA STUDIO');rid=marmota['id'];checks=0
    server=ThreadingHTTPServer(('127.0.0.1',0),partial(Quiet,directory=str(ROOT.parent)));threading.Thread(target=server.serve_forever,daemon=True).start();url=f'http://127.0.0.1:{server.server_port}/{ROOT.name}/'
    def passed(s):
        nonlocal checks;checks+=1;print('PASS '+s,flush=True)
    try:
        with sync_playwright() as pw:
            browser=pw.chromium.launch(executable_path=os.environ.get('CHROMIUM') or shutil.which('chromium'),headless=True,args=['--no-sandbox']);page=browser.new_page(viewport={'width':1440,'height':1000},accept_downloads=True);errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
            page.goto(url+'data/annecy/reports/coverage.html');expect(page.locator('tbody tr')).to_have_count(1074);expect(page.locator('#count')).to_have_text('1,074 exhibitor rows');page.locator('#group').select_option('priority');expect(page.locator('#count')).to_have_text('253 of 1,074 exhibitor rows');page.locator('#group').select_option('production_review');expect(page.locator('#count')).to_have_text('313 of 1,074 exhibitor rows')
            passed('all 1,074 historical exhibitors and exact 253/313 research groups are readable over HTTP')
            page.locator('#group').select_option('');page.locator('#search').fill('MARMOTA STUDIO');page.locator('#state').select_option('newly_added');expect(page.locator('#count')).to_have_text('1 of 1,074 exhibitor rows');expect(page.locator('tbody tr:visible')).to_contain_text('Rigging');expect(page.locator('tbody tr:visible a[href="https://www.marmotastudio.com/services"]')).to_be_visible();link=page.locator('tbody tr:visible a[href*="#/location/"]');link.focus();link.press('Enter');expect(page.locator('#profileTitle')).to_have_text('MARMOTA STUDIO',timeout=45000);expect(page.locator('#detailContent')).to_contain_text('Class C');expect(page.locator('#detailContent')).to_contain_text('No source coordinates')
            passed('dashboard source links and keyboard profile navigation reach the actual Class C reference without a fabricated map point')
            page.goto(url+'#/location/'+rid);expect(page.locator('#profileTitle')).to_have_text('MARMOTA STUDIO',timeout=45000);page.locator('#close').click();expect(page.locator('#count')).to_have_text(str(visible_counts(ROOT,manifest['counts'])['records'])+' records');page.locator('[data-quick="boutique"]').click();expect(page.locator('#boutiqueFilters')).to_be_visible(timeout=30000);page.locator('#search').fill('MARMOTA STUDIO');expect(page.locator('#list a[data-id="'+rid+'"]').first).to_be_visible();page.locator('#list a[data-id="'+rid+'"]').first.click();expect(page.locator('.boutique-profile')).to_contain_text('Rigging');expect(page.locator('.boutique-profile')).to_contain_text('External support need');page.locator('#close').click()
            passed('shareable direct URL and real boutique search retain service evidence separately from verified capabilities')
            with page.expect_download() as info:page.locator('#exportCsv').click()
            rows=list(csv.DictReader(io.StringIO(Path(info.value.path()).read_text(encoding='utf-8-sig'))));row=next(r for r in rows if r['id']==rid);assert row['evidence_class']=='C' and not row['lat'] and not row['capabilities'];assert 'marmotastudio.com/services' in row['source_provenance'];assert row['license']=='UNSPECIFIED'
            passed('filtered CSV preserves Class C, provenance, unresolved terms and empty coordinates/confirmed capabilities')
            page.goto(url+'data/annecy/reports/coverage.html');page.set_viewport_size({'width':390,'height':844});page.locator('#search').fill('MARMOTA');expect(page.locator('#count')).to_have_text('1 of 1,074 exhibitor rows');page.locator('#search').focus();assert page.evaluate('document.activeElement.id')=='search';assert page.evaluate('document.documentElement.scrollWidth<=innerWidth');page.screenshot(path='/tmp/motionx-v13-annecy-mobile.png',full_page=True)
            passed('390px review dashboard wraps evidence and supports keyboard filtering without horizontal overflow')
            assert not errors,errors;browser.close()
    finally:server.shutdown();server.server_close()
    Path('/tmp/motionx-v13-http.json').write_text(json.dumps({'checks':checks,'catalogue_records':manifest['counts']['records'],'new_class_c_references':len(proposals),'conditions':'Local HTTP subdirectory; installed headless Chromium, 1440x1000 and 390x844; no network/CPU throttle. PR proposal, not deployed Pages or human evidence verification.'},indent=2)+'\n');print(str(checks)+' Annecy HTTP checks passed',flush=True)
if __name__=='__main__':main()
