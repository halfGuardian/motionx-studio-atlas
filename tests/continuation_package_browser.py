"""Review the actual standalone artifact, not a mock research dashboard."""
import json,os,shutil,threading
from pathlib import Path
from functools import partial
from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
from playwright.sync_api import sync_playwright,expect
class Quiet(SimpleHTTPRequestHandler):
 def log_message(self,*_):pass

def main():
 root=Path(os.environ['MOTIONX_REVIEW_ROOT']);report=json.loads((root/'data/global-programme/continuation/reports/report.json').read_text());total=len(report['reviews'])+len(report['branches']);checks=0
 server=ThreadingHTTPServer(('127.0.0.1',0),partial(Quiet,directory=str(root)));threading.Thread(target=server.serve_forever,daemon=True).start();base=f'http://127.0.0.1:{server.server_port}/'
 def passed(label):
  nonlocal checks;checks+=1;print('PASS '+label,flush=True)
 try:
  with sync_playwright() as pw:
   browser=pw.chromium.launch(executable_path=os.environ.get('CHROMIUM') or shutil.which('chromium'),headless=True,args=['--no-sandbox']);page=browser.new_page(viewport={'width':390,'height':844});errors=[];page.on('pageerror',lambda e:errors.append(str(e)));page.goto(base+'data/global-programme/continuation/reports/dashboard.html');expect(page.locator('[data-company-review]')).to_have_count(total);page.locator('#reviewCountry').select_option('Japan');expect(page.locator('#reviewCount')).to_contain_text('1 of');expect(page.locator('article:visible')).to_contain_text('Ubisoft Japan');page.locator('#reviewCountry').select_option('__unknown__');expect(page.locator('article:visible')).to_contain_text('Score Draw Media');page.locator('#reviewCountry').select_option('');page.locator('#reviewDisposition').select_option('company_proposal_prepared');expect(page.locator('#reviewCount')).to_contain_text(str(len(report['proposals']))+' of');assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
   passed('standalone 390px company/branch/unknown-country filters expose real pending proposals without claiming complete global coverage')
   page.locator('a[href="geography-proposals.json"]').click();values=json.loads(page.locator('body').inner_text());assert len(values)==5 and sum(bool(r['coordinate']) for r in values)==4;assert all(not r['human_approved'] and not r['facility_verified'] and not r['original_coordinates_changed'] for r in values)
   passed('artifact relative JSON links preserve all original coordinates and distinguish four licensed city proposals from a geographic correction question')
   response=page.goto(base+'data/global-programme/reports/readiness/licensing.html');assert response.status==200;page.get_by_role('link',name='Return to the unified atlas').click();expect(page).to_have_url(base+'index.html');expect(page.locator('h1')).to_contain_text('MotionX global research artifact');assert not errors,errors;browser.close()
   passed('nested licensing report returns to the actual artifact landing page; no repository-root dependency or broken data/index.html link')
 finally:server.shutdown();server.server_close()
 Path('/tmp/motionx-global-continuation-package-http.json').write_text(json.dumps({'checks':checks,'company_reviews':len(report['reviews']),'branch_reviews':len(report['branches']),'proposed_companies':len(report['proposals']),'conditions':'Actual standalone review directory over local HTTP, Chromium, 390x844; no network/CPU throttle, deployment or human verification.'},indent=2)+'\n');print(str(checks)+' standalone continuation HTTP checks passed',flush=True)
if __name__=='__main__':main()
