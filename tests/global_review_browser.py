"""Actual global research dashboard, safe decisions and failure recovery over HTTP."""
import csv,io,json,os,shutil,threading
from functools import partial
from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
from pathlib import Path
from playwright.sync_api import sync_playwright,expect
ROOT=Path(__file__).resolve().parents[1]
class Quiet(SimpleHTTPRequestHandler):
    def log_message(self,*args):pass
def main():
    root=Path(os.environ.get('MOTIONX_REVIEW_ROOT',str(ROOT)));server=ThreadingHTTPServer(('127.0.0.1',0),partial(Quiet,directory=str(root)));threading.Thread(target=server.serve_forever,daemon=True).start();url=f'http://127.0.0.1:{server.server_port}/data/global-programme/reports/dashboard.html';checks=0;total=json.loads((root/'data/global-programme/reports/summary.json').read_text())['replayed_observations']
    def passed(message):
        nonlocal checks;checks+=1;print('PASS '+message,flush=True)
    try:
        with sync_playwright() as p:
            browser=p.chromium.launch(executable_path=os.environ.get('CHROMIUM') or shutil.which('chromium'),headless=True,args=['--no-sandbox']);page=browser.new_page(viewport={'width':1440,'height':950},accept_downloads=True);errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
            page.goto(url);expect(page.locator('#count')).to_contain_text(str(total)+' total',timeout=30000);expect(page.locator('#summary')).to_contain_text('178 source-search receipts');assert page.locator('#review article').count()==25
            passed('complete real global review index loads over HTTP, with 178 explicit country/source-search denominators and only 25 rendered cards')
            page.locator('#country').select_option('New Zealand');page.locator('#q').fill('Floating Rock');expect(page.locator('#review')).to_contain_text('Floating Rock');expect(page.locator('#review')).to_contain_text('No independently verified facility capability');page.locator('#review select').first.select_option('needs_evidence');page.locator('#review textarea').first.fill('\u200b=HYPERLINK("https://evil.example/")')
            with page.expect_download() as download:page.locator('#exportJson').click()
            value=json.loads(Path(download.value.path()).read_text());assert value['human_approved'] is False and value['authenticated_review'] is False and value['canonical_updates']==[];assert value['decisions'][0]['content_hash']
            with page.expect_download() as download:page.locator('#exportCsv').click()
            rows=list(csv.DictReader(io.StringIO(Path(download.value.path()).read_text(encoding='utf-8-sig'))));assert rows[0]['notes'].startswith("'");assert rows[0]['human_approved']=='false'
            passed('country/search/source-qualified company review exports content-bound working decisions with formula protection and no approval/publication')
            page.set_viewport_size({'width':390,'height':844});page.locator('#q').focus();page.locator('#q').press('Tab');assert page.evaluate('document.activeElement.id')=='country';assert page.evaluate('document.documentElement.scrollWidth<=innerWidth');assert not errors,errors
            passed('390px review controls, visible keyboard focus and horizontal containment')
            page.route('**/review-index.json.gz',lambda route:route.fulfill(status=503,body='source report unavailable'));page.reload();expect(page.locator('#error')).to_contain_text('unavailable');expect(page.locator('#exportJson')).to_be_disabled();expect(page.locator('#count')).to_have_text('Research report unavailable')
            passed('missing report fails explicitly and cannot substitute an empty approved queue')
            browser.close()
        Path('/tmp/motionx-global-review-http.json').write_text(json.dumps({'checks':checks,'dataset':'actual '+str(total)+' replayed observations; not new published businesses','conditions':'Local HTTP, installed Chromium, desktop and 390px emulation; no deployment or physical-device claim'},indent=2)+'\n')
    finally:server.shutdown();server.server_close()
    print(str(checks)+' global review HTTP checks passed',flush=True)
if __name__=='__main__':main()
