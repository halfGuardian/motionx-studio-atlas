"""HTTP smoke of the real maintenance artifact; no company data publication."""
import json
import os
import shutil
import threading
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from playwright.sync_api import sync_playwright, expect

ROOT = Path(os.environ['MOTIONX_MAINTENANCE_ROOT'])


class Quiet(SimpleHTTPRequestHandler):
    def log_message(self, *_): pass


def main():
    report = json.loads((ROOT / 'report.json').read_text()); total = len(report['proposals'])
    server = ThreadingHTTPServer(('127.0.0.1', 0), partial(Quiet, directory=str(ROOT)))
    threading.Thread(target=server.serve_forever, daemon=True).start(); url = f'http://127.0.0.1:{server.server_port}/'
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(executable_path=os.environ.get('CHROMIUM') or shutil.which('chromium'), headless=True, args=['--no-sandbox'])
            page = browser.new_page(viewport={'width': 1440, 'height': 950}); errors = []; page.on('pageerror', lambda e: errors.append(str(e)))
            page.goto(url + 'review.html'); expect(page.locator('[data-proposal]')).to_have_count(total)
            expect(page.locator('h1')).to_have_text('Unapproved global maintenance review')
            expect(page.locator('#reviewCount')).to_contain_text(str(total) + ' of ' + str(total))
            page.locator('#sourceCoverage').evaluate('(d)=>d.open=true')
            expect(page.locator('#sourceCoverage')).to_contain_text('Tommy Lahitte')
            expect(page.locator('#sourceCoverage')).to_contain_text('CC-BY-4.0')
            expect(page.locator('#sourceCoverage')).to_contain_text('ea-studios')
            assert page.locator('button').count() == 0
            print('PASS actual permitted-source review loads every proposal with source attribution and no approval control', flush=True)

            target = report['proposals'][0]; search = page.locator('#maintenanceSearch'); search.focus(); search.fill(target['proposal_id'])
            expect(page.locator('#reviewCount')).to_contain_text('1 of ' + str(total)); card = page.locator('[data-proposal]:visible')
            card.locator('summary').press('Enter'); expect(card.locator('pre')).to_be_visible()
            expect(card.locator('pre')).to_contain_text('"canonical_update": null')
            expect(card.locator('pre')).to_contain_text('"human_approved": false')
            search.fill('no-such-synthetic-query'); expect(page.locator('#reviewCount')).to_contain_text('0 of ' + str(total))
            print('PASS keyboard search and exact before/after evidence expose uncertain claims and useful empty results', flush=True)

            page.set_viewport_size({'width': 390, 'height': 844}); search.fill(target['proposal_id'])
            assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
            page.get_by_role('link', name='Complete audit').click(); downloaded = json.loads(page.locator('body').inner_text())
            assert downloaded == report and downloaded['summary']['canonical_updates'] == 0
            assert all(p['canonical_update'] is None and not p['human_approved'] for p in downloaded['proposals'])
            assert not errors, errors; browser.close()
            print('PASS 390px report and exact JSON download preserve all proposal/source dates and zero publication', flush=True)
    finally:
        server.shutdown(); server.server_close()
    Path('/tmp/motionx-maintenance-http.json').write_text(json.dumps({'checks': 3, 'actual_proposals': total, 'catalogue_records_unchanged': report['summary']['catalogue_records'], 'conditions': 'Actual generated historical-source artifact over local HTTP; installed Chromium at 1440x950 and 390x844; no deployed Pages or live monthly workflow claim.'}, indent=2) + '\n')
    print('3 maintenance HTTP checks passed', flush=True)


if __name__ == '__main__': main()
