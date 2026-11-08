'use strict';
const test=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs');
const D=require('../data.js'),C=require('../catalog.js'),G=require('../geography.js');
globalThis.crypto ||= require('node:crypto').webcrypto;
const read=p=>JSON.parse(fs.readFileSync(p));
const load=()=>C.load(D,async url=>new Response(fs.readFileSync(url.split('?')[0])));

test('every admitted company is in exactly one of the map-reference and integrated unpinned views',async()=>{
 const c=await load(),i=D.createDirectoryIndex(c.rows,c.commercial,c.visibility),newIds=new Set(read('data/release-candidate/reports/integrated-records.json').map(r=>r.id));
 const mapped=D.queryDirectory(i,{geographicView:'company_city'}).filter(r=>newIds.has(r.id));
 const unpinned=D.queryDirectory(i,{geographicView:'no_display'}).filter(r=>newIds.has(r.id));
 assert.equal(mapped.length,102);assert.equal(unpinned.length,80);assert.equal(new Set([...mapped,...unpinned].map(r=>r.id)).size,182);
 assert.ok(mapped.every(r=>r.lat===null&&r.lng===null));assert.ok(unpinned.every(r=>!c.visibility.references[r.id]));
 assert.equal(D.queryDirectory(i,{geographicView:'unpinned'}).filter(r=>newIds.has(r.id)).length,182);
});

test('new animation, game, VFX and mocap company sector searches combine with country without confirming facilities',async()=>{
 const c=await load(),i=D.createDirectoryIndex(c.rows,c.commercial,c.visibility);
 for(const [query,country,sector]of [['Able & Baker','Spain','Animation'],['Mighty Eyes','New Zealand','Game Development'],['Interference Pattern','United Kingdom','VFX'],['SIGNOS STUDIO','Colombia','Motion Capture']]){
  const rows=D.queryDirectory(i,{query,country,sector});assert.equal(rows.length,1,query);assert.equal(G.viewPoints(rows,c.visibility).length,1,query);
  assert.equal(D.queryDirectory(i,{query,country,sector,confirmedOnly:true}).length,0,query);
 }
 const unpinned=D.queryDirectory(i,{query:'a_BAHN',country:'Luxembourg',sector:'Animation',geographicView:'no_display'});assert.equal(unpinned.length,1);assert.equal(G.viewPoints(unpinned,c.visibility).length,0);
 const exportBundle=await c.exportBundle(c.rows.filter(r=>r.id.startsWith('globalcompany-')));
 assert.equal(exportBundle.rows.filter(r=>r.company_reference_location).length,102);assert.ok(exportBundle.rows.every(r=>r.lat===null&&r.lng===null&&!r.capabilities.length&&r.license==='UNSPECIFIED'));
 assert.match(exportBundle.licenseTexts,/Creative Commons Attribution/);
});

test('coincident and clustered city references preserve access to every company and reject invalid geographic state',async()=>{
 const c=await load(),rows=c.rows.filter(r=>r.id.startsWith('globalcompany-')),before=JSON.stringify(rows),points=G.viewPoints(rows,c.visibility),groups=D.coordinateGroups(points);
 assert.equal(points.length,102);assert.ok(groups.some(g=>g.length>=4));
 const clusters=D.clusterCoordinateGroups(groups,2);assert.deepEqual(clusters.flatMap(g=>g.rows.map(r=>r.id)).sort(),points.map(r=>r.id).sort());assert.equal(JSON.stringify(rows),before);
 const bad=structuredClone(c.visibility);bad.intake_map_gate[rows[0].id].state='verified_facility';assert.throws(()=>G.validate(bad,c.rows,D));
 bad.intake_map_gate=c.visibility.intake_map_gate;bad.additional_references=1;assert.throws(()=>G.validate(bad,c.rows,D));
});
