"""Real HTTP map/directory acceptance for the 182 admitted companies."""
import csv
import io
import json
import os
import shutil
import threading
import time
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from playwright.sync_api import sync_playwright, expect

ROOT = Path(os.environ.get('MOTIONX_MAP_GATE_ROOT', Path(__file__).resolve().parents[1]))


class Quiet(SimpleHTTPRequestHandler):
    def log_message(self, *_): pass


def main():
    report = json.loads((ROOT / 'data/release-candidate/map-gate/reports/acceptance.json').read_text())
    server = ThreadingHTTPServer(('127.0.0.1', 0), partial(Quiet, directory=str(ROOT.parent)))
    threading.Thread(target=server.serve_forever, daemon=True).start()
    url = f'http://127.0.0.1:{server.server_port}/{ROOT.name}/'
    checks = 0; metrics = {}

    def passed(label):
        nonlocal checks
        checks += 1; print('PASS ' + label, flush=True)

    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(executable_path=os.environ.get('CHROMIUM') or shutil.which('chromium'), headless=True, args=['--no-sandbox'])
            page = browser.new_page(viewport={'width': 1440, 'height': 1000}, accept_downloads=True)
            errors = []; page.on('pageerror', lambda e: errors.append(str(e)))
            start = time.monotonic(); page.goto(url, wait_until='domcontentloaded')
            expect(page.locator('#count')).to_have_text('42474 records', timeout=45000)
            metrics['initial_http_ready_seconds'] = round(time.monotonic() - start, 3)
            assert page.request.get(url + 'atlas.css').status == 200
            assert page.evaluate('getComputedStyle(document.documentElement).backgroundColor') == 'rgb(11, 16, 25)'
            expect(page.locator('.leaflet-control-attribution')).to_contain_text('OpenStreetMap')
            actual = page.evaluate('()=>({all:studios.length,new:studios.filter(r=>r.id.startsWith("globalcompany-")).length,points:MotionXGeography.viewPoints(studios.filter(r=>r.id.startsWith("globalcompany-")),catalog.visibility).length,none:studios.filter(r=>r.id.startsWith("globalcompany-")&&!catalog.visibility.references[r.id]).length})')
            assert actual == {'all': 42478, 'new': 182, 'points': 102, 'none': 80}, actual
            passed('actual styled HTTP atlas loads all 182 companies, 102 separate references and 80 unpinned companies; OSM attribution retained')

            page.locator('#advancedFilters').evaluate('(d)=>d.open=true')
            cases = [('Able & Baker', 'Spain', 'Animation'), ('Mighty Eyes', 'New Zealand', 'Game Development'),
                     ('Interference Pattern', 'United Kingdom', 'VFX'), ('SIGNOS STUDIO', 'Colombia', 'Motion Capture')]
            for name, country, sector in cases:
                page.locator('#resetFilters').click(); page.locator('#country').select_option(country)
                page.locator('#category').select_option(sector); page.locator('#search').fill(name)
                expect(page.locator('#count')).to_have_text('1 record')
                page.wait_for_function('(name)=>matches.length===1&&matches[0].name===name',arg=name)
                page.locator('#fitResults').click(); expect(page.locator('.company-city-reference')).to_have_count(1)
                page.locator('.company-city-reference').focus(); page.locator('.company-city-reference').press('Space')
                expect(page.locator('.leaflet-popup-content')).to_contain_text(name)
                page.locator('.leaflet-popup-content [data-record-id]').first.press('Enter')
                expect(page.locator('#profileTitle')).to_have_text(name)
                expect(page.locator('#detailContent')).to_contain_text('not a verified studio entrance')
                page.locator('#close').click(); page.locator('#confirmedOnly').check()
                expect(page.locator('#count')).to_have_text('0 records')
            passed('new animation, game, VFX and mocap company searches combine with country/sector; keyboard markers open profiles and confirmed-only adds no invented capabilities')

            page.locator('#resetFilters').click(); page.locator('#country').select_option('Luxembourg')
            page.locator('#category').select_option('Animation'); page.locator('#search').fill('a_BAHN')
            expect(page.locator('#count')).to_have_text('1 record'); expect(page.locator('#browseNoReference')).to_have_text('Browse 1 unpinned company')
            page.locator('#mapLegendToggle').click()
            page.locator('#browseNoReference').click(); expect(page.locator('#geographicView')).to_have_value('no_display')
            expect(page.locator('#country')).to_have_value('Luxembourg'); expect(page.locator('#category')).to_have_value('Animation')
            expect(page.locator('#count')).to_have_text('1 record'); page.locator('#list a.profile-link').press('Enter')
            expect(page.locator('#profileTitle')).to_have_text('a_BAHN')
            expect(page.locator('#detailContent')).to_contain_text('No city is recorded'); page.locator('#close').click()
            for r in report['records']:
                if r['city'] and r['state'] == 'unpinned':
                    page.locator('#resetFilters').click(); page.locator('#search').fill(r['name'])
                    expect(page.locator('#count')).to_have_text('1 record')
                    page.wait_for_function('(name)=>matches.length===1&&matches[0].name===name',arg=r['name'])
                    assert page.evaluate('companyReferenceLayer.getLayers().length') == 0
                    page.locator('#list a.profile-link').click()
                    expect(page.locator('#detailContent')).to_contain_text(r['reason']); page.locator('#close').click()
            passed('integrated unpinned view preserves country/category/search and explains all four city holds plus companies with no city')

            page.locator('#resetFilters').click(); page.locator('#country').select_option('United Kingdom')
            page.locator('#city').fill('London'); page.locator('#category').select_option('Animation')
            page.locator('#geographicView').select_option('company_city')
            page.wait_for_function('matches.every(r=>r.record_kind==="company_reference"&&catalog.visibility.references[r.id])&&matches.some(r=>r.name==="Picturesmith")&&matches.some(r=>r.name==="The Illuminated Film Company")')
            page.evaluate('map.setView([51.50853,-0.12574],16,{animate:false})')
            expect(page.locator('.company-city-reference')).to_have_count(1)
            ids = page.evaluate('companyReferences.filter(r=>r.lat===51.50853&&r.lng===-0.12574).map(r=>r.id)')
            assert len(ids) >= 4
            for rid in ids:
                page.locator('.company-city-reference').focus(); page.locator('.company-city-reference').press('Space')
                page.evaluate('map.panBy([0,20],{animate:false})')
                page.locator('.leaflet-popup-content [data-record-id="' + rid + '"]').press('Enter')
                page.wait_for_function('(id)=>selected===id',arg=rid); page.locator('#close').click()
            page.locator('#resetFilters').click(); page.locator('#geographicView').select_option('company_city'); expect(page.locator('#count')).to_have_text('109 records'); page.locator('#fitResults').click()
            page.wait_for_function('companyReferenceLayer.getLayers().length>0')
            assert page.evaluate('companyReferenceLayer.getLayers().flatMap(m=>m.motionxLocations).length') == 110
            passed('all coincident London company references remain individually keyboard-selectable through map movement; global clustering preserves all 110 old/new display points')

            page.locator('#resetFilters').click(); page.locator('#search').fill('Able & Baker')
            expect(page.locator('#count')).to_have_text('1 record')
            with page.expect_download() as info: page.locator('#exportCsv').click()
            rows = list(csv.DictReader(io.StringIO(Path(info.value.path()).read_text(encoding='utf-8-sig'))))
            assert len(rows) == 1 and not rows[0]['lat'] and not rows[0]['lng'] and not rows[0]['capabilities']
            p = json.loads(rows[0]['company_reference_location']); assert p['coordinate_license'] == 'CC-BY-4.0' and p['city'] == 'Madrid'
            assert rows[0]['license'] == 'UNSPECIFIED' and not p['human_approved'] and not p['facility_verified']
            assert page.evaluate('catalog.visibility.references["boutique-5926fcc99b16ed8ea595dcf5459f"].lat') == -41.28664
            frame = page.evaluate('catalog.rows.find(r=>r.id==="overture-39fd34a0-9be1-4ac0-a46e-ebd53a1599ff")')
            assert (frame['lat'], frame['lng']) == (34.02437092, -118.47703191)
            passed('filtered CSV retains null originals, provisional company rights and separate licensed city evidence; Floating Rock and Frame Machine unchanged')

            page.set_viewport_size({'width': 390, 'height': 844}); page.locator('#listTab').click(); page.locator('#resetFilters').click(); page.locator('#mapTab').click()
            page.locator('#browseNoReference').press('Enter'); expect(page.locator('#geographicView')).to_have_value('no_display')
            expect(page.locator('#search')).to_be_focused(); expect(page.locator('#list')).to_be_visible()
            assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
            page.locator('#search').fill('a_BAHN'); expect(page.locator('#count')).to_have_text('1 record')
            page.locator('#list a.profile-link').press('Enter'); expect(page.locator('#profileTitle')).to_have_text('a_BAHN'); page.locator('#close').click()
            page.goto(url + 'data/release-candidate/map-gate/reports/dashboard.html')
            expect(page.locator('[data-map-review]')).to_have_count(182); page.locator('#mapReviewState').select_option('unpinned')
            expect(page.locator('#mapReviewCount')).to_contain_text('80 of 182'); page.locator('#mapReviewSearch').fill('Corona')
            expect(page.locator('#mapReviewCount')).to_contain_text('1 of 182'); expect(page.locator('article:visible')).to_contain_text('Ozone Story Tech')
            assert page.evaluate('document.documentElement.scrollWidth<=innerWidth'); assert not errors, errors
            browser.close(); passed('390px styled map-to-unpinned keyboard navigation, profiles and complete geographic decision dashboard remain accessible')
    finally:
        server.shutdown(); server.server_close()
    metrics.update(checks=checks, admitted=182, approximate_company_references=102, unpinned=80,
                   actual_records=42478, conditions='Actual HTTP subdirectory and packaged CSS/assets; installed Chromium at 1440x1000 and 390x844. No network/CPU throttle; separate full real/synthetic suites measure constrained performance. No deployed Pages or physical-device claim.')
    Path('/tmp/motionx-map-gate-http.json').write_text(json.dumps(metrics, indent=2) + '\n')
    print(str(checks) + ' final map acceptance HTTP checks passed', flush=True)


if __name__ == '__main__': main()
