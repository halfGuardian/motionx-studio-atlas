from public_scope import visible_counts
"""Current NZ audit and unpinned company references under an HTTP subdirectory."""
import csv,io,json,os,shutil,threading
from functools import partial
from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
from pathlib import Path
from playwright.sync_api import sync_playwright,expect
ROOT=Path(__file__).resolve().parents[1]
class Quiet(SimpleHTTPRequestHandler):
    def log_message(self,*_):pass

def main():
    manifest=json.loads((ROOT/'data/public/manifest.json').read_text());audit=json.loads((ROOT/'data/nz-census/reports/reconciliation.json').read_text());proposed=json.loads((ROOT/'data/nz-census/reports/proposals.json').read_text())['company_references'];assembly=next(r for r in proposed if r['name']=='Assembly');gov=next(r for r in proposed if r['name']=='Balancing Monkey Games');a44=next(r for r in audit['observations'] if r['name']=='A44');checks=0
    server=ThreadingHTTPServer(('127.0.0.1',0),partial(Quiet,directory=str(ROOT.parent)));threading.Thread(target=server.serve_forever,daemon=True).start();url=f'http://127.0.0.1:{server.server_port}/{ROOT.name}/'
    def passed(s):
        nonlocal checks;checks+=1;print('PASS '+s,flush=True)
    try:
        with sync_playwright() as pw:
            browser=pw.chromium.launch(executable_path=os.environ.get('CHROMIUM') or shutil.which('chromium'),headless=True,args=['--no-sandbox']);page=browser.new_page(viewport={'width':1440,'height':1000},accept_downloads=True);errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
            page.goto(url+'data/nz-census/reports/coverage.html');expect(page.locator('#observations tr')).to_have_count(217);expect(page.locator('#count')).to_have_text('217 of 217 observations');expect(page.locator('body')).to_contain_text('This census is incomplete')
            page.locator('#source').select_option('nzonair-gdsr');expect(page.locator('#count')).to_have_text('116 of 217 observations');page.locator('#state').select_option('unresolved');expect(page.locator('#count')).to_have_text('19 of 217 observations');page.locator('#q').fill('2Up Games');expect(page.locator('#count')).to_have_text('2 of 217 observations')
            passed('all 217 source rows, 116 programme observations and historical unresolved companies remain filterable')
            page.locator('#source').select_option('');page.locator('#state').select_option('new_reference');page.locator('#q').fill('Assembly');expect(page.locator('#count')).to_have_text('1 of 217 observations')
            link=page.locator('#observations tr:visible a[href*="#/location/"]');link.focus();link.press('Enter');expect(page.locator('#profileTitle')).to_have_text('Assembly',timeout=45000);expect(page.locator('#detailContent')).to_contain_text('New Zealand');expect(page.locator('#detailContent')).to_contain_text('Class C');expect(page.locator('#detailContent')).to_contain_text('No source coordinates');expect(page.locator('#detailContent a[href="https://www.assemblyltd.com/info"]').first).to_be_visible()
            passed('keyboard dashboard link opens the real NZ Assembly Class C reference without changing the foreign pin')
            page.goto(url+'#/location/'+a44['record_ids'][0]);expect(page.locator('#profileTitle')).to_contain_text('A44',timeout=45000);assert not a44['record_ids'][0].startswith('nzcensus-');page.locator('#close').click();expect(page.locator('#count')).to_have_text(str(visible_counts(ROOT,manifest['counts'])['records'])+' records');expect(page.locator('a[href="data/nz-census/reports/coverage.html"]')).to_be_visible();expect(page.locator('.leaflet-control-attribution')).to_contain_text('OpenStreetMap')
            passed('existing A44 identity, full directory count, current audit link and OSM attribution are preserved')
            page.locator('#browseUnmapped').click();expect(page.locator('#count')).to_have_text(str(visible_counts(ROOT,manifest['counts'])['company_references'])+' records');page.locator('#search').fill('Balancing Monkey Games');expect(page.locator('#count')).to_have_text('1 record');page.locator('#list a[data-id="'+gov['id']+'"]').click();expect(page.locator('#profileTitle')).to_have_text(gov['name']);expect(page.locator('#detailContent')).to_contain_text('Class C');expect(page.locator('#detailContent')).to_contain_text('NZ-On-Air-Permission');page.locator('#close').click()
            with page.expect_download(timeout=30000) as info:page.locator('#exportCsv').click()
            rows=list(csv.DictReader(io.StringIO(Path(info.value.path()).read_text(encoding='utf-8-sig'))));assert len(rows)==1;row=rows[0];assert row['id']==gov['id'] and row['evidence_class']=='C' and not row['lat'] and not row['capabilities'];assert row['license']=='NZ-On-Air-Permission';assert 'Copyright © NZ On Air' in row['export_licences'];assert 'copyright-and-terms-use' in row['export_licences'];assert 'Creative Commons Attribution' not in row['export_licences'];assert row['source_provenance']
            passed('unpinned company search and filtered CSV retain scoped government grant, source years and zero confirmed services')
            page.goto(url+'data/nz-census/reports/coverage.html');page.set_viewport_size({'width':390,'height':844});page.locator('#source').select_option('film-otago-southland-selected');expect(page.locator('#count')).to_have_text('2 of 217 observations');page.locator('#q').fill('Graphic Monk');expect(page.locator('#count')).to_have_text('1 of 217 observations');page.locator('#q').focus();assert page.evaluate('document.activeElement.id')=='q';assert page.evaluate('document.documentElement.scrollWidth<=innerWidth');page.screenshot(path='/tmp/motionx-v15-nz-mobile.png',full_page=True)
            passed('mobile dashboard keeps historic restricted-source labels, source warnings and keyboard filtering visible without overflow')
            assert not errors,errors;browser.close()
    finally:server.shutdown();server.server_close()
    Path('/tmp/motionx-v15-http.json').write_text(json.dumps({'checks':checks,'catalogue_records':manifest['counts']['records'],'source_observations':len(audit['observations']),'new_class_c_references':len(proposed),'conditions':'Local HTTP subdirectory; installed headless Chromium, desktop 1440x1000 and mobile 390x844. No CPU/network throttle. Not deployed Pages, a physical low-memory device, independent company verification or human approval.'},indent=2)+'\n');print(str(checks)+' NZ HTTP checks passed',flush=True)
if __name__=='__main__':main()
