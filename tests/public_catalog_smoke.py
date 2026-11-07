from public_scope import visible_counts
"""Actual proposed public catalogue over HTTP, separate from baseline fixtures."""
import csv,io,json,os,shutil,threading,time
from collections import defaultdict
from functools import partial
from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
from pathlib import Path
from playwright.sync_api import sync_playwright,expect

ROOT=Path(__file__).resolve().parents[1]
class Quiet(SimpleHTTPRequestHandler):
    def log_message(self,*_):pass

def main():
    manifest=json.loads((ROOT/'data/public/manifest.json').read_text());counts=visible_counts(ROOT,manifest['counts']);inclusive=manifest.get('mode')=='unified_research';noun='records' if inclusive else 'locations';total=counts['records'] if inclusive else counts['public_locations'];index=json.loads((ROOT/'data/public/index.json').read_text())
    server=ThreadingHTTPServer(('127.0.0.1',0),partial(Quiet,directory=str(ROOT.parent)));threading.Thread(target=server.serve_forever,daemon=True).start();url=f'http://127.0.0.1:{server.server_port}/{ROOT.name}/';checks=0;report={}
    def passed(s):
        nonlocal checks;checks+=1;print('PASS '+s,flush=True)
    try:
        with sync_playwright() as p:
            browser=p.chromium.launch(executable_path=os.environ.get('CHROMIUM') or shutil.which('chromium'),headless=True,args=['--no-sandbox'])
            page=browser.new_page(viewport={'width':1440,'height':950},accept_downloads=True);requests=[];errors=[];page.on('request',lambda r:requests.append(r.url));page.on('pageerror',lambda e:errors.append(str(e)))
            start=time.monotonic();page.goto(url,wait_until='domcontentloaded');expect(page.locator('#count')).to_have_text(f"{total} {noun}",timeout=45000);report['initial_ready_seconds']=round(time.monotonic()-start,3)
            assert page.evaluate('document.documentElement.dataset.catalog')=='sharded';assert not [r for r in requests if '/shards/' in r]
            assert page.evaluate('studios.length')==manifest['counts']['records'];expect(page.locator('#companies')).to_contain_text('Records can overlap' if inclusive else 'provisional source identities')
            expect(page.locator('.leaflet-control-attribution')).to_contain_text('OpenStreetMap contributors');page.wait_for_function('!!document.querySelector(".leaflet-tile-loaded")',timeout=30000)
            report['initial_app_timings']=page.evaluate('({...MotionXPerformance})')
            report['complete_query']=page.evaluate('''()=>{const start=performance.now(),all=D.queryDirectory(directory,{sort:'relevance',scopeMode:'all'});if(all.length!==studios.length||new Set(all.map(r=>r.id)).size!==studios.length)throw Error('Incomplete search coverage');return {records:all.length,milliseconds:performance.now()-start};}''')
            expected=page.evaluate('D.queryDirectory(directory,{query:"Framestore",sort:"relevance"}).length');search_start=time.monotonic();page.locator('#search').fill('Framestore');expect(page.locator('#count')).to_have_text(str(expected)+' '+noun);report['search_end_to_end_ms']=round((time.monotonic()-search_start)*1000,2);report['search_compute_ms']=page.evaluate('MotionXPerformance.search_ms');page.locator('#resetFilters').click()
            report['map_navigation']=page.evaluate('''()=>{const start=performance.now();map.setView([51.5,-.12],10,{animate:false});return {elapsed_ms:performance.now()-start,marker_render_ms:MotionXPerformance.marker_render_ms,markers:layer.getLayers().length};}''')
            passed(f"actual {total}-record HTTP catalogue, live tiles, source classes, no initial detail downloads")
            page.locator('#advancedFilters > summary').click()
            page.locator('#evidenceClass').select_option('A');expect(page.locator('#count')).to_have_text(f"{counts['class_a']} {noun}")
            page.locator('#evidenceClass').select_option('B');expect(page.locator('#count')).to_have_text(f"{counts['class_b']} {noun}")
            page.locator('#confirmedOnly').check();expect(page.locator('#count')).to_have_text('0 '+noun);page.locator('#resetFilters').click()
            passed('Class A/B totals and zero inferred confirmed capabilities in source-listed data')
            chosen=next(r for r in index if not inclusive or (r[11]=='B' and r[12]=='source_location' and r[10]=='source_provisional'));id,name=chosen[0],chosen[2]
            page.goto(url+'#/location/'+id,wait_until='domcontentloaded');expect(page.locator('#profileTitle')).to_have_text(name)
            expect(page.locator('#detailContent')).to_contain_text('Class B — Source-listed, not independently corroborated');expect(page.locator('#detailContent')).to_contain_text('No facility capability is confirmed');expect(page.locator('#detailContent')).to_contain_text('Directory provenance & reuse')
            report['uncached_profile_detail_ms']=page.evaluate('MotionXPerformance.profile_open_ms')
            org=chosen[1];page.locator('#detailContent a[href="#/organisation/'+org+'"]').first.click();expect(page.locator('#profileTitle')).to_be_visible();page.go_back();expect(page.locator('#profileTitle')).to_have_text(name);page.go_forward();expect(page.locator('#detailContent')).to_contain_text('Records under this identity' if inclusive else 'provisional source grouping')
            passed('real source-listed direct profile URL, evidence, organisation route and browser history')
            page.locator('#close').click();page.locator('#advancedFilters').evaluate('(d)=>d.open=true');page.locator('#evidenceClass').select_option('B');page.locator('#country').select_option(chosen[4]);page.locator('#search').fill(name);expect(page.locator('[data-id="'+id+'"]').first).to_be_visible()
            with page.expect_download() as info:page.locator('#exportCsv').click()
            content=Path(info.value.path()).read_text(encoding='utf-8-sig');rows=list(csv.DictReader(io.StringIO(content)));assert id in {r['id'] for r in rows};assert all(r['evidence_class']=='B' and r['source_provenance'] and r['license'] for r in rows);assert rows[0]['export_licences']
            passed('actual filtered CSV, source provenance and complete redistribution licence copies')
            groups=defaultdict(list)
            for r in index:
                if isinstance(r[5],(int,float)) and isinstance(r[6],(int,float)):groups[r[5],r[6]].append(r)
            shared=next((values for values in groups.values() if 1<len(values)<=20),None)
            if shared:
                page.locator('#resetFilters').click();page.evaluate('(r)=>map.setView([r[5],r[6]],16,{animate:false})',shared[0]);page.evaluate('(id)=>layer.getLayers().find(m=>m.motionxLocations.includes(id)).openPopup()',shared[0][0])
                button=page.locator('.leaflet-popup-content li button').filter(has_text=shared[0][2]+' — '+shared[0][3]);button.press('Enter');expect(page.locator('#profileTitle')).to_have_text(shared[0][2]);passed('actual coincident source points retain selectable keyboard-accessible facilities')
            if inclusive:
                company=next(r for r in index if r[12]=='company_reference');page.locator('#close').click();page.locator('#recordKind').select_option('company_reference');expect(page.locator('#count')).to_have_text(str(counts['company_references'])+' records');page.wait_for_function('layer.getLayers().length===0');(expect(page.locator('#fitResults')).to_be_enabled() if manifest.get('global_visibility') else expect(page.locator('#fitResults')).to_be_disabled());before=page.evaluate('JSON.stringify(map.getCenter())');page.locator('#search').fill(company[2]);page.locator('[data-id="'+company[0]+'"]').click();expect(page.locator('#profileTitle')).to_have_text(company[2]);expect(page.locator('#detailContent')).to_contain_text('No source coordinates; no map pin is invented');expect(page.locator('#detailContent')).to_contain_text('Class C');assert page.evaluate('JSON.stringify(map.getCenter())')==before;passed('all company references remain in the same directory with no invented map points')
            else:
                page.goto(url+'#/location/'+manifest['baseline']['research_only_ids'][0],wait_until='domcontentloaded');expect(page.locator('#profileTitle')).to_have_text('Profile evidence unavailable');expect(page.locator('#detailContent')).to_contain_text('research queue')
            if inclusive:
                baseline=json.loads((ROOT/'studios.json').read_text());legacy=next(r for r in baseline if r['evidence_state']=='unknown');page.goto(url+'#/location/'+legacy['id'],wait_until='domcontentloaded');expect(page.locator('#profileTitle')).to_have_text(legacy['name']);expect(page.locator('#detailContent')).to_contain_text('Class C')
            page.goto(url+'#/location/not-a-real-id',wait_until='domcontentloaded');expect(page.locator('#profileTitle')).to_have_text('This profile could not be found.');passed('retained legacy profile stays accessible with C evidence; invalid profiles fail clearly' if inclusive else 'research-only identity and invalid profile fail clearly')
            page.goto(url+'#/location/'+id,wait_until='domcontentloaded');expect(page.locator('#profileTitle')).to_have_text(name);page.set_viewport_size({'width':390,'height':844});assert page.evaluate('document.documentElement.scrollWidth<=innerWidth');page.locator('#close').click();page.locator('#listTab').click();expect(page.locator('aside')).to_be_visible();page.locator('#mapTab').click();expect(page.locator('#map')).to_be_visible();assert not errors,errors;passed('real-data 390px mobile profile and map/list navigation')
            report['unthrottled_app_timings']=page.evaluate('MotionXPerformance');page.close()
            page=browser.new_page(viewport={'width':390,'height':844});session=page.context.new_cdp_session(page);session.send('Network.enable');session.send('Network.emulateNetworkConditions',{'offline':False,'latency':150,'downloadThroughput':96000,'uploadThroughput':32000});session.send('Emulation.setCPUThrottlingRate',{'rate':4})
            start=time.monotonic();page.goto(url,wait_until='domcontentloaded');expect(page.locator('#dataStatus')).to_contain_text('Full results are available after integrity checks',timeout=15000);assert page.locator('#search').is_disabled();assert page.locator('#count').inner_text()!=f'{total} {noun}';expect(page.locator('#count')).to_have_text(f"{total} {noun}",timeout=90000);report['throttled_initial_ready_seconds']=round(time.monotonic()-start,3);report['throttled_app_timings']=page.evaluate('MotionXPerformance');assert page.evaluate('document.documentElement.scrollWidth<=innerWidth');passed('real catalogue at 96,000 bytes/sec, 150ms latency, 4x CPU slowdown, 390px viewport; progress never claims partial results are complete')
            transport=manifest['index'].get('compact',manifest['index'])
            report.update(kind='real_proposed_catalogue_not_deployed_production',records=total,class_a=counts['class_a'],class_b=counts['class_b'],baseline_bytes=(ROOT/'studios.json').stat().st_size,index_bytes=transport['bytes'],index_gzip_bytes=(ROOT/'data/public'/(transport['path']+'.gz')).stat().st_size,checks=checks,conditions='Local HTTP subdirectory / installed headless Chromium. The app explicitly fetches lossless columnar gzip index/compressed baseline and checks compressed/decompressed hashes. Pages deployment performance is not measured. CPU/network emulation is not a physical low-memory mobile device.')
            Path('/tmp/motionx-v11-real-performance.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report),flush=True);browser.close()
    finally:server.shutdown();server.server_close()
    print(f'{checks} actual-catalogue browser checks passed',flush=True)
if __name__=='__main__':main()
