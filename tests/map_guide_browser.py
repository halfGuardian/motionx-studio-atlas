"""Real HTTP map guide: compact by default and operable without covering the map."""
import json
import os
import shutil
import threading
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from playwright.sync_api import sync_playwright, expect

ROOT = Path(__file__).resolve().parents[1]


class Quiet(SimpleHTTPRequestHandler):
    def log_message(self, *_): pass


def main():
    server = ThreadingHTTPServer(('127.0.0.1', 0), partial(Quiet, directory=str(ROOT.parent)))
    threading.Thread(target=server.serve_forever, daemon=True).start(); url = f'http://127.0.0.1:{server.server_port}/{ROOT.name}/'
    measurements = []
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(executable_path=os.environ.get('CHROMIUM') or shutil.which('chromium'), headless=True, args=['--no-sandbox'])
            page = browser.new_page(viewport={'width': 1440, 'height': 950}); errors = []; page.on('pageerror', lambda e: errors.append(str(e)))
            for width, height in ((1440, 950), (768, 1024), (390, 844), (320, 568), (844, 390)):
                page.set_viewport_size({'width': width, 'height': height}); page.goto(url, wait_until='domcontentloaded')
                expect(page.locator('#count')).to_have_text('42474 records', timeout=45000)
                guide = page.locator('#evidenceLegend'); toggle = page.locator('#mapLegendToggle')
                expect(toggle).to_be_visible(); expect(page.locator('#mapLegendBody')).to_be_hidden()
                assert not guide.evaluate('(d)=>d.open')
                box = guide.bounding_box(); area = page.locator('#map').bounding_box()
                assert 44 <= box['height'] <= 52 and box['width'] <= 165, box
                assert box['x'] >= area['x'] and box['x'] + box['width'] <= area['x'] + area['width'] + 1
                assert box['y'] < area['y'] + 25
                assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
                measurements.append({'viewport': [width, height], 'collapsed_box': box})
                if width in (1440, 390): page.screenshot(path=f'/tmp/motionx-map-guide-{width}.png')
            print('PASS desktop, tablet, mobile and landscape start with a small top-right Map guide; no horizontal overflow', flush=True)

            page.set_viewport_size({'width': 1440, 'height': 950}); page.goto(url, wait_until='domcontentloaded')
            expect(page.locator('#count')).to_have_text('42474 records', timeout=45000)
            toggle = page.locator('#mapLegendToggle'); toggle.focus(); toggle.press('Enter')
            expect(page.locator('#mapLegendBody')).to_be_visible(); expect(page.locator('#legendA')).to_have_text('230')
            expect(page.locator('#legendB')).to_have_text('4,626'); expect(page.locator('#referenceCount')).to_have_text('110')
            centre = page.evaluate('map.getCenter()'); page.locator('#showCompanyReferences').uncheck()
            expect(page.locator('#referenceCount')).to_have_text('0'); page.locator('#showCompanyReferences').check()
            expect(page.locator('#referenceCount')).to_have_text('110')
            assert page.evaluate('map.getCenter()') == centre
            page.locator('#showCompanyReferences').press('Escape'); expect(page.locator('#mapLegendBody')).to_be_hidden(); expect(toggle).to_be_focused()
            toggle.press('Space'); expect(page.locator('#mapLegendBody')).to_be_visible(); toggle.press('Enter'); expect(page.locator('#mapLegendBody')).to_be_hidden()
            print('PASS native Enter/Space disclosure, Escape/focus recovery and unchanged evidence/reference controls without map movement', flush=True)

            touch_context = browser.new_context(viewport={'width': 390, 'height': 844}, is_mobile=True, has_touch=True)
            touch = touch_context.new_page(); touch.goto(url, wait_until='domcontentloaded')
            expect(touch.locator('#count')).to_have_text('42474 records', timeout=45000)
            touch.locator('#mapLegendToggle').tap(); expect(touch.locator('#browseNoReference')).to_be_visible()
            touch.screenshot(path='/tmp/motionx-map-guide-mobile-open.png')
            touch.locator('#browseNoReference').tap(); expect(touch.locator('#geographicView')).to_have_value('no_display')
            expect(touch.locator('#list')).to_be_visible(); expect(touch.locator('#search')).to_be_focused()
            touch.locator('#search').fill('a_BAHN'); expect(touch.locator('#count')).to_have_text('1 record')
            touch.locator('#list a.profile-link').press('Enter'); expect(touch.locator('#profileTitle')).to_have_text('a_BAHN')
            touch_context.close()
            print('PASS touch disclosure keeps unpinned-company directory and keyboard profiles accessible on mobile', flush=True)

            context = browser.new_context(viewport={'width': 1440, 'height': 950}); fallback = context.new_page()
            fallback.route('**/leaflet.js', lambda route: route.abort('failed')); fallback.goto(url, wait_until='domcontentloaded')
            expect(fallback.locator('#count')).to_have_text('42474 records', timeout=45000)
            expect(fallback.locator('.map-error')).to_contain_text('Map library could not load')
            fallback.locator('#mapLegendToggle').press('Enter'); expect(fallback.locator('#mapLegendBody')).to_be_visible()
            context.close(); assert not errors, errors; browser.close()
            print('PASS disclosure and directory remain usable if Leaflet fails to load', flush=True)
    finally:
        server.shutdown(); server.server_close()
    Path('/tmp/motionx-map-guide-http.json').write_text(json.dumps({'checks': 4, 'measurements': measurements, 'conditions': 'Actual local HTTP catalogue, installed Chromium, live Leaflet/OSM except explicit failure fixture; not a deployed-site claim.'}, indent=2) + '\n')
    print('4 map-guide HTTP checks passed', flush=True)


if __name__ == '__main__': main()
