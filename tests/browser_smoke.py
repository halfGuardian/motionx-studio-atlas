"""HTTP browser checks. Optional QA dependency: pip install playwright.

Uses installed Chromium (CHROMIUM env override) or Playwright's browser.
Real Leaflet CDN and OpenStreetMap tile requests are not stubbed. This is the
retained 243-record compatibility fixture; public_catalog_smoke.py separately
tests the actual full sharded public catalogue and its Class C exclusion.
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

    def do_GET(self):
        from urllib.parse import urlsplit
        if urlsplit(self.path).path in (f'/{ROOT.name}/',f'/{ROOT.name}/index.html'):
            # Compatibility fixture exposes advanced controls; production tests
            # separately exercise the real collapsed/filter keyboard workflow.
            body=(ROOT/'index.html').read_text().replace(' data-catalog="sharded"','').replace('id="advancedFilters"','id="advancedFilters" open').encode()
            self.send_response(200);self.send_header('Content-Type','text/html; charset=utf-8');self.send_header('Content-Length',str(len(body)));self.end_headers();self.wfile.write(body)
        else:super().do_GET()


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
            assert page.evaluate('layer.getLayers().length') <= len({(r['lat'], r['lng']) for r in database})
            assert page.evaluate('layer.getLayers().flatMap(m=>m.motionxLocations).sort()') == sorted(r['id'] for r in database)
            passed('real Leaflet map, live OpenStreetMap tiles and attribution')
            shared=page.evaluate("() => {const group=D.coordinateGroups(studios).find(g=>g.length>1);map.setView([group[0].lat,group[0].lng],16,{animate:false});layer.getLayers().find(m=>m.motionxLocations.includes(group[0].id)).openPopup();return group.map(r=>r.id);}")
            assert len(shared)>=2
            for record_id in shared:
                page.evaluate("id => { layer.getLayers().find(m => m.motionxLocations.includes(id)).openPopup(); }",record_id)
                button = page.locator('.leaflet-popup-content li button[data-record-id="'+record_id+'"]')
                button.focus()
                button.press('Enter')
                expect(page.locator('#detailContent h2')).to_have_text(next(r['name'] for r in database if r['id']==record_id))
                page.locator('#close').click()
            passed('coincident marker popup lists all studios and keyboard selection opens each profile')
            page.locator('#country').select_option('Canada')
            page.locator('#search').fill('Beyond Capture')
            expect(page.locator('#count')).to_have_text('2 locations')
            expect(page.locator('#companies')).to_contain_text('1 organization')
            page.locator('[data-id="beyond-vancouver"]').click()
            expect(page.locator('#detailContent')).to_contain_text('confirmed')
            expect(page.locator('#detailContent')).to_contain_text('approximate reference pin')
            expect(page.locator('#detailContent')).to_contain_text('Source presence does not prove')
            page.locator('#close').click()
            passed('search, company grouping and profile evidence / coordinate precision')
            with page.expect_download() as download_info:
                page.locator('#exportCsv').click()
            download = download_info.value
            assert download.suggested_filename == 'motionx_atlas_filtered_v1.2.csv'
            content = Path(download.path()).read_text(encoding='utf-8-sig')
            assert content.count('\n') == 2 and 'beyond-vancouver' in content and 'beyond-montreal' in content
            passed('filtered CSV download with location and company identities')
            page.locator('#search').fill('')
            page.locator('#country').select_option('Canada')
            page.locator('#category').select_option('Performance Capture')
            expected_performance=sum(r['country']=='Canada' and 'Performance Capture' in r['capabilities'] for r in database)
            expect(page.locator('#count')).to_have_text(f'{expected_performance} locations')
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

            page.locator('#search').fill('StudioT3D')
            expect(page.locator('#count')).to_have_text('2 locations')
            page.locator('#category').select_option('Volumetric Capture')
            expect(page.locator('#count')).to_have_text('1 location')
            page.locator('[data-id="studiot3d-london-stage-2"]').click()
            expect(page.locator('#detailContent')).to_contain_text('Guildhall Production Studio')
            expect(page.locator('#detailContent')).not_to_contain_text('Virtual Production — confirmed')
            page.locator('#close').click()
            page.locator('#category').select_option('')
            page.locator('#search').fill('Audiomotion')
            expect(page.locator('#count')).to_have_text('1 location')
            page.locator('[data-id="audiomotion"]').click()
            expect(page.locator('#detailContent')).to_contain_text('Didcot')
            expect(page.locator('#detailContent')).to_contain_text('Recorded review date: 2026-11-06')
            expect(page.locator('#detailContent')).not_to_contain_text('Legacy recorded review date')
            page.locator('#close').click()
            page.locator('#search').fill('')
            expect(page.locator('#count')).to_have_text(f'{total_locations} locations')
            passed('new co-located capture stages, precise capability filters and explicitly reviewed legacy correction')

            page.locator('#search').fill('Larian')
            page.locator('#category').select_option('Motion Capture')
            page.locator('#confirmedOnly').check()
            expect(page.locator('#count')).to_have_text('1 location')
            page.locator('[data-id="larian-kuala-lumpur"]').click()
            expect(page.locator('#detailContent')).to_contain_text('Motion Capture — confirmed')
            expect(page.locator('#detailContent')).not_to_contain_text('Facial Capture — confirmed')
            page.locator('#close').click()
            page.locator('#category').select_option('')
            page.locator('#search').fill('Annapurna')
            expect(page.locator('#count')).to_have_text('2 locations')
            page.evaluate('() => { layer.getLayers().find(m => m.getPopup()).openPopup(); }')
            expect(page.locator('.leaflet-popup-content button')).to_have_count(2)
            page.locator('.leaflet-popup-content button').last.press('Enter')
            expect(page.locator('#detailContent h2')).to_contain_text('ANR Virtual Production Stage')
            expect(page.locator('#detailContent')).not_to_contain_text('Facial Capture — confirmed')
            page.locator('#close').click()
            page.locator('#search').fill('Koawa')
            expect(page.locator('#count')).to_have_text('0 locations')
            page.locator('#confirmedOnly').uncheck()
            expect(page.locator('#count')).to_have_text('1 location')
            page.locator('#search').fill('')
            expect(page.locator('#count')).to_have_text(f'{total_locations} locations')
            passed('confirmed capability filtering, site-specific capture and keyboard selection between Annapurna stages')

            page.goto(url+'#/location/dneg-london',wait_until='domcontentloaded')
            page.evaluate('window.releaseDatabase()')
            expect(page.locator('#profileTitle')).to_have_text('DNEG — London')
            assert page.evaluate('document.activeElement.id')=='profileTitle'
            page.locator('#detailContent a[href="#/organisation/dneg"]').first.click()
            expect(page.locator('#profileTitle')).to_have_text('DNEG')
            expect(page.locator('#organisationBranches a')).to_have_count(19)
            page.go_back()
            expect(page.locator('#profileTitle')).to_have_text('DNEG — London')
            page.go_forward()
            expect(page.locator('#profileTitle')).to_have_text('DNEG')
            page.locator('#close').press('Enter')
            expect(page.locator('#detail')).to_be_hidden()
            page.goto(url+'#/organisation/cinesite-group',wait_until='domcontentloaded')
            page.evaluate('window.releaseDatabase()')
            expect(page.locator('#detailContent')).to_contain_text('separate operating brands')
            expect(page.locator('#detailContent')).to_contain_text('Imaginarium')
            page.keyboard.press('Escape')
            page.locator('#search').fill('Plastic Wax')
            page.locator('#capabilityOptions').evaluate("e=>e.closest('details').open=true")
            page.locator('#capabilityOptions input[value="Motion Capture"]').check()
            page.locator('#capabilityOptions input[value="Facial Capture"]').check()
            page.locator('#confirmedOnly').check()
            page.locator('#city').fill('Rhodes')
            page.locator('#locationType').select_option('mixed_campus')
            expect(page.locator('#count')).to_have_text('1 location')
            page.locator('#capabilityOptions input[value="Volumetric Capture"]').check()
            expect(page.locator('#count')).to_have_text('0 locations')
            expect(page.locator('#list')).to_contain_text('No studios match')
            page.locator('#capabilityMode').select_option('any')
            expect(page.locator('#count')).to_have_text('1 location')
            page.locator('#resetFilters').click()
            expect(page.locator('#count')).to_have_text(f'{total_locations} locations')
            assert not page.locator('#capabilityOptions input:checked').count()
            page.locator('a[href="#search"]').focus()
            page.locator('a[href="#search"]').press('Enter')
            expect(page.locator('#detail')).to_be_hidden()
            passed('direct profile links, organisation/parent identities, back/forward, focus, AND/OR capabilities, city/type/confirmed-only, empty state and reset')

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

            page=browser.new_page(viewport={'width':390,'height':844},accept_downloads=True)
            fixture=[{**database[0],'id':f'coincident-{i}','company_id':'fixture','name':f'Facility {i}', 'lat':51.5,'lng':-.12} for i in range(65)]
            fixture[64]['name']='=HYPERLINK("https://example.test","<img src=x onerror=window.injected=true>")'
            page.route('**/studios.json',lambda route:route.fulfill(content_type='application/json',body=json.dumps(fixture)))
            page.goto(url,wait_until='domcontentloaded');expect(page.locator('#count')).to_have_text('65 locations')
            page.evaluate('()=>layer.getLayers()[0].openPopup()')
            expect(page.locator('.leaflet-popup-content li button')).to_have_count(30)
            page.locator('.leaflet-popup-content button').filter(has_text='Next').press('Enter')
            page.locator('.leaflet-popup-content button').filter(has_text='Next').press('Enter')
            expect(page.locator('.leaflet-popup-content li button')).to_have_count(5)
            last_id=page.locator('.leaflet-popup-content li button').last.get_attribute('data-record-id')
            page.locator('.leaflet-popup-content li button').last.press('Enter')
            expect(page.locator('#profileTitle')).to_have_text(next(r['name'] for r in fixture if r['id']==last_id))
            page.keyboard.press('Escape');page.locator('#listTab').click();page.locator('[data-id="coincident-64"]').click()
            expect(page.locator('#profileTitle')).to_contain_text('<img src=x')
            assert not page.locator('#detailContent img').count()
            assert not page.evaluate('!!window.injected')
            assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
            assert page.locator('#detailContent a[target="_blank"]:not([rel="noopener noreferrer"])').count()==0
            page.keyboard.press('Escape')
            page.locator('#listTab').click()
            with page.expect_download() as info:page.locator('#exportCsv').click()
            text=Path(info.value.path()).read_text(encoding='utf-8-sig')
            assert "'=HYPERLINK" in text
            page.goto(url+'#/location/%3Cscript%3E',wait_until='domcontentloaded')
            expect(page.locator('#profileTitle')).to_have_text('This profile could not be found.')
            assert not page.evaluate('!!window.injected')
            page.close();passed('65 coincident studios remain selectable through popup pagination on mobile; hostile text, URL routes, external links and formula CSV are safe')

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

            page = browser.new_page(viewport={'width':1440,'height':950},accept_downloads=True)
            original = json.loads((ROOT / 'studios.json').read_text())[0]
            records = [{**original, 'id': f'load-test-{i}', 'company_id': f'company-{i//2}',
                        'name': f'VFX test fixture {i}', 'country':['Canada','United States','Japan','Brazil','Kenya'][i%5],
                        'city':f'City {i%20}', 'categories':['VFX','Animation'] if i%2==0 else ['VFX'],
                        'capabilities':['VFX','Animation'] if i%2==0 else ['VFX'],
                        'capability_evidence':{cap:{'state':'confirmed','evidence':'https://example.test/fixture','verified_on':'2026-11-06'} for cap in (['VFX','Animation'] if i%2==0 else ['VFX'])},
                        'location_type':'production_studio' if i%2==0 else 'capture_facility',
                        'lat': (i % 250) * .64 - 80, 'lng': (i // 250) * 1.75 - 175}
                       for i in range(50000)]
            body=json.dumps(records)
            page.route('**/studios.json', lambda route: route.fulfill(content_type='application/json', body=body))
            start=time.monotonic();page.goto(url,wait_until='domcontentloaded')
            expect(page.locator('#count')).to_have_text('50000 locations',timeout=30000)
            initial=time.monotonic()-start
            assert page.locator('.entry').count()==50
            assert page.evaluate('layer.getLayers().length')<2000
            page.evaluate('() => { map.setView([0,0],4,{animate:false}); }')
            assert page.evaluate("""() => {
                const b=map.getBounds().pad(.2), visible=MotionXData.visibleCoordinateGroups(markerGroups,{west:b.getWest(),east:b.getEast(),south:b.getSouth(),north:b.getNorth()});
                const expected=visible.flat().map(r=>r.id).sort();
                const actual=layer.getLayers().flatMap(m=>m.motionxLocations).sort();
                return JSON.stringify(actual)===JSON.stringify(expected);
            }""")
            page.evaluate('() => { map.setView([35,179],4,{animate:false}); }')
            assert page.evaluate("""() => {
                const b=map.getBounds().pad(.2), visible=MotionXData.visibleCoordinateGroups(markerGroups,{west:b.getWest(),east:b.getEast(),south:b.getSouth(),north:b.getNorth()});
                return JSON.stringify(layer.getLayers().flatMap(m=>m.motionxLocations).sort())===JSON.stringify(visible.flat().map(r=>r.id).sort());
            }""")
            page.locator('#nextPage').click();expect(page.locator('#pageInfo')).to_have_text('51–100 of 50000')
            page.locator('#country').select_option('Canada')
            page.locator('#locationType').select_option('production_studio')
            page.locator('#confirmedOnly').check()
            page.locator('#capabilityPicker summary').click()
            page.locator('#capabilityOptions input[value="VFX"]').check()
            page.locator('#capabilityOptions input[value="Animation"]').check()
            expect(page.locator('#count')).to_have_text('5000 locations')
            multifilter_ms=page.evaluate('MotionXPerformance.search_ms')
            page.locator('#search').fill('VFX test fixture 49990')
            expect(page.locator('#count')).to_have_text('1 location')
            search_ms=page.evaluate('MotionXPerformance.search_ms')
            page.locator('[data-id="load-test-49990"]').click()
            expect(page.locator('#detailContent h2')).to_have_text('VFX test fixture 49990')
            profile_ms=page.evaluate('MotionXPerformance.profile_open_ms')
            page.locator('#close').click()
            page.set_viewport_size({'width':390,'height':844});page.locator('#listTab').click()
            page.locator('[data-id="load-test-49990"]').click()
            assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
            page.locator('#close').click();page.locator('#mapTab').click()
            elapsed=time.monotonic()-start
            assert initial<20 and elapsed<30, (initial,elapsed)
            assert max(search_ms,multifilter_ms)<1500 and profile_ms<1500
            metrics={'synthetic_locations':len(records),'fixture_json_bytes':len(body.encode()),'initial_http_ready_seconds':round(initial,3),
                'search_ms':round(search_ms,3),'multi_filter_ms':round(multifilter_ms,3),'profile_open_ms':round(profile_ms,3),
                'complete_smoke_seconds':round(elapsed,3),'list_page_size':50,'client_timings':page.evaluate('MotionXPerformance')}
            Path('/tmp/motionx-v10-performance.json').write_text(json.dumps(metrics,indent=2))
            passed(f'50000 synthetic locations, indexed filters, grouped viewport rendering, profiles and mobile ({elapsed:.1f}s)')
            page.close()
            # Distinct identities at exactly the same coordinate stay directly selectable.
            page=browser.new_page(viewport={'width':1440,'height':950})
            records[5001].update(lat=records[5000]['lat'],lng=records[5000]['lng'])
            page.route('**/studios.json',lambda route:route.fulfill(content_type='application/json',body=json.dumps(records)))
            page.goto(url,wait_until='domcontentloaded');expect(page.locator('#count')).to_have_text('50000 locations',timeout=30000)
            page.evaluate('() => { map.setView([studios[5000].lat,studios[5000].lng],17,{animate:false}); }')
            page.evaluate('() => { layer.getLayers().find(m=>m.motionxLocations.includes("load-test-5000")).openPopup(); }')
            expect(page.locator('.leaflet-popup-content button')).to_have_count(2)
            page.locator('.leaflet-popup-content button').last.press('Enter')
            expect(page.locator('#detailContent h2')).to_have_text('VFX test fixture 5001')
            passed('50000-location shared-coordinate chooser preserves keyboard selection and original coordinates')
            page.close()
            browser.close()
    finally:
        server.shutdown()
    print(f'{checks} browser checks passed')


if __name__ == '__main__':
    main()
