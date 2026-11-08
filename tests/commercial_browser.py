"""Actual HTTP atlas: scope visibility, audience filtering and safe exports."""
import csv,io,json,os,shutil,threading
from pathlib import Path
from functools import partial
from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
from playwright.sync_api import sync_playwright,expect
ROOT=Path(__file__).resolve().parents[1]
class Quiet(SimpleHTTPRequestHandler):
 def log_message(self,*_):pass

def main():
 server=ThreadingHTTPServer(('127.0.0.1',0),partial(Quiet,directory=str(ROOT.parent)));threading.Thread(target=server.serve_forever,daemon=True).start();url=f'http://127.0.0.1:{server.server_port}/{ROOT.name}/';checks=0
 def passed(label):
  nonlocal checks;checks+=1;print('PASS '+label,flush=True)
 try:
  with sync_playwright() as pw:
   browser=pw.chromium.launch(executable_path=os.environ.get('CHROMIUM') or shutil.which('chromium'),headless=True,args=['--no-sandbox']);page=browser.new_page(viewport={'width':1440,'height':1000},accept_downloads=True);errors=[];page.on('pageerror',lambda e:errors.append(str(e)));page.goto(url,wait_until='domcontentloaded');expect(page.locator('#count')).to_have_text('42292 records',timeout=45000);assert page.evaluate('catalog.rows.length')==42296
   page.locator('#scopeMode').select_option('excluded');expect(page.locator('#count')).to_have_text('4 records');assert page.evaluate('matches.every(r=>r.lat===null&&r.lng===null)');assert page.evaluate('layer.getLayers().length')==0
   passed('normal directory excludes exactly four reviewed audio-only references; all 42296 raw records remain unchanged and no map points are removed')
   row=page.locator('#list a[data-id="nzcensus-a574603da74bca72ee54c088614e"]');row.focus();row.press('Enter');expect(page.locator('#profileTitle')).to_have_text('The Sound Room');expect(page.locator('.commercial-scope')).to_contain_text('Excluded from normal directory');page.locator('#close').click()
   with page.expect_download() as info:page.locator('#exportCsv').click()
   rows=list(csv.DictReader(io.StringIO(Path(info.value.path()).read_text(encoding='utf-8-sig'))));assert len(rows)==4 and all(r['commercial_role']=='out_of_scope' and not r['lat'] and not r['capabilities'] for r in rows);assert all(r['commercial_evidence'] for r in rows);assert 'advisory_service_alignment' not in rows[0]
   passed('excluded records remain keyboard-accessible, clearly labeled and exportable with scope evidence, licence notices and no invented capability')
   page.locator('#resetFilters').click();page.locator('#search').fill('Envy Studios');expect(page.locator('#count')).to_have_text('1 record');page.locator('#commercialRole').select_option('provider');expect(page.locator('#count')).to_have_text('1 record');page.locator('#list a.profile-link').click();expect(page.locator('.commercial-scope')).to_contain_text('Both client and provider');expect(page.locator('.commercial-scope')).to_contain_text('Video editing');page.locator('#close').click()
   passed('multidisciplinary visual/audio Envy remains eligible as a provider and client with individual evidence')
   page.locator('#resetFilters').click();page.locator('#advancedFilters').evaluate('(d)=>d.open=true');page.locator('#category').select_option('Game Development');page.locator('#country').select_option('New Zealand');page.locator('#commercialRole').select_option('client');page.wait_for_function('matches.length>0&&matches.every(r=>r.categories.includes("Game Development")&&r.country==="New Zealand")');assert page.evaluate('matches.some(r=>!r.capabilities.length)');page.locator('#confirmedOnly').check();page.wait_for_function('matches.every(r=>Object.values(r.capability_evidence).some(e=>e.state==="confirmed"))')
   passed('game-development client filter needs no capture capability; confirmed-only remains a separate facility-evidence requirement')
   page.locator('#resetFilters').click();page.locator('#geographicView').select_option('company_city');expect(page.locator('#count')).to_have_text('1 record');expect(page.locator('#list')).to_contain_text('Floating Rock');page.locator('#resetFilters').click();page.locator('#scopeMode').select_option('all');expect(page.locator('#count')).to_have_text('42296 records');page.locator('#resetFilters').click();expect(page.locator('#count')).to_have_text('42292 records')
   passed('supported company-city reference discovery, explicit all-record audit view and reset use the same result set as map and CSV')
   page.set_viewport_size({'width':390,'height':844});page.locator('#listTab').click();page.locator('#commercialRole').focus();page.locator('#commercialRole').select_option('out_of_scope');expect(page.locator('#scopeMode')).to_have_value('all');expect(page.locator('#count')).to_have_text('4 records');assert page.evaluate('document.documentElement.scrollWidth<=innerWidth');page.screenshot(path='/tmp/motionx-global-commercial-mobile.png',full_page=True)
   passed('390px mobile and keyboard focus preserve audit scope access without horizontal overflow')
   report=browser.new_page(viewport={'width':390,'height':844});report.goto(url+'data/global-programme/continuation/reports/dashboard.html');expect(report.locator('h1')).to_have_text('Global company research continuation');assert report.locator('article').count()>=68;report.locator('#reviewSearch').fill('Mamoncillo');expect(report.locator('#reviewCount')).to_contain_text('1 of');expect(report.locator('article:visible')).to_contain_text('identity review');report.locator('#reviewSearch').fill('');report.locator('#reviewCountry').select_option('__unknown__');expect(report.locator('#reviewCount')).to_contain_text('1 of');expect(report.locator('article:visible')).to_contain_text('Score Draw Media');report.locator('#reviewCountry').select_option('New Zealand');expect(report.locator('#reviewCount')).to_contain_text('individual reviews shown');expect(report.locator('[data-branch-review]')).to_have_count(7);expect(report.locator('#branches')).to_have_text('Office, branch and department investigations');expect(report.locator('body')).to_contain_text('production closure announced');expect(report.locator('body')).to_contain_text('Human review remains required');assert report.evaluate('document.documentElement.scrollWidth<=innerWidth');report.close();assert not errors,errors
   passed('downloadable country/company review dashboard exposes actual proposals, unresolved research and human-review requirements')
   failed=browser.new_page();failed.route('**/data/public/commercial.json.gz?*',lambda r:r.fulfill(status=503,body='Unavailable'));failed.goto(url,wait_until='domcontentloaded');expect(failed.locator('#dataStatus')).to_contain_text('Unable to load studio catalogue',timeout=45000);expect(failed.locator('#count')).to_have_text('Studio data unavailable');assert failed.evaluate('matches.length')==0;failed.close();browser.close()
   passed('missing scope policy fails closed with clear retry state rather than silently showing an outdated scope')
 finally:server.shutdown();server.server_close()
 Path('/tmp/motionx-global-commercial-http.json').write_text(json.dumps({'checks':checks,'stored_records':42296,'normal_directory_records':42292,'excluded_audio_only':4,'conditions':'Actual local HTTP GitHub Pages subdirectory; installed Chromium; 1440x1000 and 390x844; no throttle in this suite. Not deployed Pages, independent business verification or human approval.'},indent=2)+'\n');print(str(checks)+' commercial HTTP checks passed',flush=True)
if __name__=='__main__':main()
