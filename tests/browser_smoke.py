"""HTTP browser checks. Optional QA dependency: pip install playwright.

Uses installed Chromium (CHROMIUM env override) or Playwright's browser.
Real Leaflet CDN and OpenStreetMap tile requests are not stubbed.
"""
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import shutil
import threading
import time
from playwright.sync_api import sync_playwright, expect

ROOT = Path(__file__).resolve().parents[1]


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *_):
        pass


def main():
    database = json.loads((ROOT / 'studios.json').read_text())
    total_locations = len(database)
    total_companies = len({r['company_id'] for r in database})
    server = ThreadingHTTPServer(('127.0.0.1', 0), partial(QuietHandler, directory=str(ROOT.parent)))
    threading.Thread(target=server.serve_forever, daemon=True).start()
    url = f'http://127.0.0.1:{server.server_port}/{ROOT.name}/'
    checks = 0
    def passed(label):
        nonlocal checks
        checks += 1
        print(f'PASS {label}', flush=True)
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(executable_path=os.environ.get('CHROMIUM') or shutil.which('chromium'),
                                         headless=True, args=['--no-sandbox'])
            page = browser.new_page(viewport={'width': 1440, 'height': 950}, accept_downloads=True)
            errors, tile_responses, data_requests = [], [], []
            page.on('pageerror', lambda error: errors.append(str(error)))
            page.on('response', lambda response: tile_responses.append(response.status) if 'tile.openstreetmap.org' in response.url else None)
            page.on('request', lambda request: data_requests.append(request.url) if request.url.endswith('/studios.json') else None)
            page.add_init_script("""const originalFetch = window.fetch.bind(window);
                window.fetch = (...args) => String(args[0]).endsWith('studios.json')
                  ? new Promise(resolve => {window.releaseDatabase = () => resolve(originalFetch(...args));})
                  : originalFetch(...args);""")
            page.goto(url, wait_until='domcontentloaded')
            expect(page.locator('#dataStatus')).to_contain_text('Loading studio database')
            expect(page.locator('#exportCsv')).to_be_disabled()
            page.wait_for_function('typeof window.releaseDatabase === "function"')
            page.evaluate('window.releaseDatabase()')
            expect(page.locator('#count')).to_have_text(f'{total_locations} locations')
            expect(page.locator('#companies')).to_contain_text(f'{total_companies} organizations')
            assert data_requests == [url + 'studios.json']
            assert page.locator('.entry').count() == min(total_locations, 50)
            passed(f'HTTP subdirectory loading, disabled loading controls, {total_locations} locations / {total_companies} organizations')
            expect(page.locator('.leaflet-control-attribution')).to_contain_text('OpenStreetMap contributors')
            page.wait_for_function('document.querySelector(".leaflet-tile-loaded") !== null', timeout=20000)
            assert 200 in tile_responses
            assert page.evaluate('layer.getLayers().length') == len({(r['lat'], r['lng']) for r in database})
            passed('real Leaflet map, live OpenStreetMap tiles and attribution')
            page.evaluate("layer.getLayers().find(m => m.getPopup()).openPopup()")
            buttons = page.locator('.leaflet-popup-content button')
            labels = buttons.all_text_contents()
            assert len(labels) >= 2
            for label in labels:
                page.evaluate("layer.getLayers().find(m => m.getPopup()).openPopup()")
                button = page.locator('.leaflet-popup-content button').filter(has_text=label)
                button.focus()
                button.press('Enter')
                expect(page.locator('#detailContent h2')).to_have_text(label.split(' — ')[0])
                page.locator('#close').click()
            passed('coincident marker popup lists all studios and keyboard selection opens each profile')
            page.locator('#search').fill('beyond')
            expect(page.locator('#count')).to_have_text('2 locations')
            expect(page.locator('#companies')).to_contain_text('1 organization')
            page.locator('[data-id="beyond-vancouver"]').click()
            expect(page.locator('#detailContent')).to_contain_text('unknown')
            expect(page.locator('#detailContent')).to_contain_text('approximate reference pin')
            expect(page.locator('#detailContent')).to_contain_text('not independently verified')
            page.locator('#close').click()
            passed('search, company grouping and profile evidence / coordinate precision')
            with page.expect_download() as download_info:
                page.locator('#exportCsv').click()
            download = download_info.value
            assert download.suggested_filename == 'motionx_studios_filtered_v0.9.csv'
            content = Path(download.path()).read_text(encoding='utf-8-sig')
            assert content.count('\n') == 2 and 'beyond-vancouver' in content and 'beyond-montreal' in content
            passed('filtered CSV download with location and company identities')
            page.locator('#search').fill('')
            page.locator('#country').select_option('Canada')
            page.locator('#category').select_option('Performance Capture')
            expect(page.locator('#count')).to_have_text('5 locations')
            page.locator('#fitResults').click()
            assert page.evaluate('layer.getLayers().length') == len({(r['lat'], r['lng']) for r in database if r['country'] == 'Canada' and 'Performance Capture' in r['capabilities']})
            page.locator('#country').select_option('')
            page.locator('#category').select_option('')
            expect(page.locator('#count')).to_have_text(f'{total_locations} locations')
            passed('combined country / capability filtering and fit-results action')
            page.locator('#search').fill('Industrial Light & Magic')
            expect(page.locator('#count')).to_have_text('5 locations')
            expect(page.locator('#companies')).to_contain_text('1 organization')
            page.locator('#search').fill('Framestore')
            expect(page.locator('#count')).to_have_text('7 locations')
            page.locator('#search').fill('')
            page.locator('#country').select_option('India')
            page.locator('#category').select_option('VFX')
            india_vfx = [r for r in database if r['country'] == 'India' and 'VFX' in r['categories']]
            expect(page.locator('#count')).to_have_text(f'{len(india_vfx)} locations')
            page.locator('[data-id="ilm-mumbai"]').click()
            expect(page.locator('#detailContent')).to_contain_text('Animation — confirmed')
            expect(page.locator('#detailContent')).to_contain_text('city — approximate reference pin')
            expect(page.locator('#detailContent a').filter(has_text='Official/public source')).to_have_attribute('href', 'https://www.ilm.com/locations/')
            assert 'Motion Capture' not in page.locator('#detailContent').inner_text()
            page.locator('#close').click()
            with page.expect_download() as batch_download:
                page.locator('#exportCsv').click()
            batch_content = Path(batch_download.value.path()).read_text(encoding='utf-8-sig')
            assert 'ilm-mumbai' in batch_content and 'framestore-mumbai' in batch_content
            assert batch_content.count('\n') == len(india_vfx)
            page.locator('#search').fill('Framestore')
            page.locator('#country').select_option('United Kingdom')
            page.locator('#category').select_option('Previsualization')
            expect(page.locator('#count')).to_have_text('1 location')
            passed('batch 1 organisation grouping, VFX/country filters, confirmed profile evidence, new-record CSV export and London previs')
            page.locator('#search').fill('')
            page.locator('#country').select_option('')
            page.locator('#category').select_option('')
            expect(page.locator('#count')).to_have_text(f'{total_locations} locations')
            page.locator('#search').fill('Imaginarium')
            expect(page.locator('#count')).to_have_text('2 locations')
            page.locator('[data-id="imaginarium-pinewood"]').click()
            expect(page.locator('#detailContent')).to_contain_text('capture facility')
            expect(page.locator('#detailContent')).to_contain_text('Cinesite Group')
            expect(page.locator('#detailContent')).to_contain_text('City reference source')
            page.locator('#close').click()
            page.locator('#search').fill('Cinesite Group')
            expect(page.locator('#count')).to_have_text('15 locations')
            page.locator('#search').fill('')
            expect(page.locator('#count')).to_have_text(f'{total_locations} locations')
            passed('optional location type, sourced group relationships, coordinate provenance and relationship search')
            page.screenshot(path='/tmp/motionx-v08-desktop.png')
            page.set_viewport_size({'width': 390, 'height': 844})
            page.locator('#listTab').click()
            expect(page.locator('aside')).to_be_visible()
            page.locator('[data-id="beyond-vancouver"]').click()
            expect(page.locator('#detail')).to_be_visible()
            assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
            page.screenshot(path='/tmp/motionx-v08-mobile.png')
            page.locator('#close').click()
            page.locator('#listTab').click()
            page.locator('#mapTab').click()
            expect(page.locator('#map')).to_be_visible()
            passed('390px mobile list, profile, map navigation and no horizontal overflow')
            assert not errors, errors
            page.close()

            # Every failure is explicit, disables actions and has no embedded fallback.
            for label, status, body in [('404', 404, '{}'), ('invalid JSON', 200, '{broken'),
                                         ('invalid schema', 200, '[{"id":"bad"}]')]:
                page = browser.new_page()
                page.route('**/studios.json', lambda route, request, status=status, body=body: route.fulfill(status=status, content_type='application/json', body=body))
                page.goto(url, wait_until='domcontentloaded')
                expect(page.locator('#count')).to_have_text('Studio data unavailable')
                expect(page.locator('#dataStatus')).to_contain_text('Unable to load studios.json')
                expect(page.locator('#retryLoad')).to_be_visible()
                expect(page.locator('#exportCsv')).to_be_disabled()
                assert page.locator('.entry').count() == 0
                page.unroute('**/studios.json')
                page.locator('#retryLoad').click()
                expect(page.locator('#count')).to_have_text(f'{total_locations} locations')
                page.close()
                passed(f'{label} error state, no fallback, successful retry')
            page = browser.new_page()
            page.route('**/studios.json', lambda route: route.abort())
            page.goto(url, wait_until='domcontentloaded')
            expect(page.locator('#count')).to_have_text('Studio data unavailable')
            page.close()
            passed('network failure state')

            page = browser.new_page()
            original = json.loads((ROOT / 'studios.json').read_text())[0]
            records = [{**original, 'id': f'load-test-{i}', 'company_id': f'company-{i}',
                        'name': f'VFX test fixture {i}', 'categories': ['VFX'], 'capabilities': [],
                        'capability_evidence': {}, 'lat': (i % 100) * 1.6 - 80, 'lng': (i // 100) * 3.5 - 175}
                       for i in range(10000)]
            page.route('**/studios.json', lambda route: route.fulfill(content_type='application/json', body=json.dumps(records)))
            start = time.monotonic()
            page.goto(url, wait_until='domcontentloaded')
            expect(page.locator('#count')).to_have_text('10000 locations', timeout=20000)
            assert page.locator('.entry').count() == 50
            page.evaluate('() => { map.setView([0, 0], 4, {animate:false}); }')
            expected_visible = page.evaluate('''() => {
                const b = map.getBounds().pad(.2);
                return MotionXData.visibleCoordinateGroups(markerGroups,
                    {west:b.getWest(),east:b.getEast(),south:b.getSouth(),north:b.getNorth()}).length;
            }''')
            assert page.evaluate('layer.getLayers().length') == expected_visible
            assert 0 < expected_visible < 2000
            page.evaluate('() => { map.setView([35, 140], 4, {animate:false}); }')
            # Longitude -179 is also in a viewport spanning 170..190 (world wrapping).
            assert page.evaluate('''() => {
                const b=map.getBounds().pad(.2), visible=MotionXData.visibleCoordinateGroups(markerGroups,
                    {west:b.getWest(),east:b.getEast(),south:b.getSouth(),north:b.getNorth()});
                const expected=new Set(visible.map(g=>JSON.stringify([g[0].lat,g[0].lng])));
                return layer.getLayers().length === expected.size && layer.getLayers().every(m=>{
                    const p=m.getLatLng(); return expected.has(JSON.stringify([p.lat,p.lng]));
                });
            }''')
            expect(page.locator('#count')).to_have_text('10000 locations')
            page.locator('#nextPage').click()
            expect(page.locator('#pageInfo')).to_have_text('51–100 of 10000')
            page.locator('#category').select_option('VFX')
            expect(page.locator('#count')).to_have_text('10000 locations')
            page.locator('#search').fill('VFX test fixture 9999')
            expect(page.locator('#count')).to_have_text('1 location')
            elapsed = time.monotonic() - start
            assert elapsed < 20, f'10k smoke path exceeded 20 seconds: {elapsed}'
            Path('/tmp/motionx-v09-performance.json').write_text(json.dumps({'synthetic_locations':len(records),'unique_coordinate_groups':len({(r['lat'], r['lng']) for r in records}),'viewport_markers_at_zoom_4':expected_visible,'list_page_size':50,'load_pan_paginate_filter_seconds':round(elapsed,3)}))
            passed(f'10000 synthetic locations, viewport rendering/panning, 50-row pagination, filtering ({elapsed:.1f}s)')
            # A coincident chooser must retain every filtered studio and keyboard focus
            # even when Leaflet auto-pans its popup in viewport mode.
            page.unroute('**/studios.json')
            records[5001].update(lat=records[5000]['lat'],lng=records[5000]['lng'])
            page.route('**/studios.json', lambda route: route.fulfill(content_type='application/json', body=json.dumps(records)))
            page.goto(url, wait_until='domcontentloaded')
            expect(page.locator('#count')).to_have_text('10000 locations')
            page.evaluate('() => { map.setView([studios[5000].lat, studios[5000].lng], 5, {animate:false}); }')
            page.evaluate('layer.getLayers().find(m => m.getPopup()).openPopup()')
            expect(page.locator('.leaflet-popup-content button')).to_have_count(2)
            page.wait_for_timeout(400)
            page.locator('.leaflet-popup-content button').last.press('Enter')
            expect(page.locator('#detailContent h2')).to_have_text('VFX test fixture 5001')
            passed('viewport-mode coincident chooser preserves keyboard selection and profile navigation')
            page.close()
            browser.close()
    finally:
        server.shutdown()
    print(f'{checks} browser checks passed')


if __name__ == '__main__':
    main()
