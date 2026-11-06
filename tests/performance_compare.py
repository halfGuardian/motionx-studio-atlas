"""Optional HTTP comparison against an archived v0.9.3 checkout. No synthetic data committed.

python tests/performance_compare.py --baseline /tmp/motionx-v093 --output /tmp/comparison.json
The baseline directory must contain the exact original index.html, app.js and data.js.
"""
import argparse,json,os,shutil,threading,time
from functools import partial
from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
class Quiet(SimpleHTTPRequestHandler):
    def log_message(self,*_):pass

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--baseline',type=Path,required=True);parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
    first=json.loads((ROOT/'studios.json').read_text())[0]
    rows=[{**first,'id':f'benchmark-{i}','company_id':f'company-{i//2}','name':f'Benchmark studio {i}','city':f'City {i%20}','country':['Canada','Japan','Brazil','Kenya','United States'][i%5],
        'categories':['VFX','Animation'] if i%2==0 else ['VFX'],'capabilities':['VFX','Animation'] if i%2==0 else ['VFX'],
        'capability_evidence':{cap:{'state':'confirmed','evidence':'https://example.test/fixture','verified_on':'2026-11-06'} for cap in (['VFX','Animation'] if i%2==0 else ['VFX'])},
        'location_type':'production_studio' if i%2==0 else 'capture_facility','lat':i%250*.64-80,'lng':i//250*1.75-175} for i in range(50000)]
    body=json.dumps(rows);result={'synthetic_locations':50000,'same_fixture_bytes':len(body.encode()),'method':'Same 50,000-record response intercepted over local HTTP; real Leaflet and OSM; one cold page per version. Local headless Chromium, not a device/network lab. DOM/filter timings include rendering; route fulfillment overhead included in initial load.','versions':{}}
    with sync_playwright() as p:
        browser=p.chromium.launch(executable_path=os.environ.get('CHROMIUM') or shutil.which('chromium'),headless=True,args=['--no-sandbox'])
        for version,directory in [('v0.9.3',args.baseline),('v1.0',ROOT)]:
            server=ThreadingHTTPServer(('127.0.0.1',0),partial(Quiet,directory=str(directory)));threading.Thread(target=server.serve_forever,daemon=True).start()
            page=browser.new_page(viewport={'width':1440,'height':950});page.set_default_timeout(60000)
            page.route('**/studios.json',lambda route:route.fulfill(content_type='application/json',body=body))
            measurements={};errors=[];page.on('pageerror',lambda error:errors.append(str(error)))
            # Instrument the same loader path only with timers; source behavior remains unchanged.
            source=(directory/'data.js').read_text().replace('const controller = new AbortController();', 'globalThis.MotionXCompare={data_start:performance.now()};const controller = new AbortController();').replace('return validateDatabase(await response.json());','const parsed=await response.json();const t=performance.now();const result=validateDatabase(parsed);globalThis.MotionXCompare.validate_ms=performance.now()-t;globalThis.MotionXCompare.load_validate_ms=performance.now()-globalThis.MotionXCompare.data_start;return result;')
            page.route('**/data.js',lambda route,request,source=source:route.fulfill(content_type='application/javascript',body=source))
            start=time.monotonic()
            try:
                page.goto(f'http://127.0.0.1:{server.server_port}/',wait_until='domcontentloaded')
                page.wait_for_function('document.querySelector("#count").textContent==="50000 locations"',timeout=60000)
                measurements['initial_http_ready_seconds']=round(time.monotonic()-start,3)
                measurements['data_timings']=page.evaluate('globalThis.MotionXCompare');measurements['directory_dom_entries']=page.locator('.entry').count();measurements['initial_markers']=page.evaluate('layer.getLayers().length')
                measurements['pan_ms']=round(page.evaluate('()=>{const t=performance.now();map.setView([10,140],4,{animate:false});return performance.now()-t;}'),2)
                start=time.monotonic();page.locator('#search').fill('Benchmark studio 49990');page.wait_for_function('document.querySelector("#count").textContent==="1 location"');measurements['search_ui_ms']=round((time.monotonic()-start)*1000,2)
                start=time.monotonic();page.locator('[data-id="benchmark-49990"]').click();page.wait_for_function('document.querySelector("#detailContent h2").textContent==="Benchmark studio 49990"');measurements['profile_ui_ms']=round((time.monotonic()-start)*1000,2)
                page.set_viewport_size({'width':390,'height':844});measurements['mobile_no_horizontal_overflow']=page.evaluate('document.documentElement.scrollWidth<=innerWidth')
                measurements['multi_capability_filter']='supported; measured separately in release browser smoke' if version=='v1.0' else 'not supported in baseline'
                measurements['status']='completed'
            except Exception as e:measurements.update(status='incomplete',elapsed_seconds=round(time.monotonic()-start,3),error=type(e).__name__,page_errors=errors,data_status=page.locator('#dataStatus').inner_text())
            finally:result['versions'][version]=measurements;page.close();server.shutdown();print(version,measurements,flush=True)
        browser.close()
    args.output.write_text(json.dumps(result,indent=2)+'\n')
if __name__=='__main__':main()
