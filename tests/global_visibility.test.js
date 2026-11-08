'use strict';
const test=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),D=require('../data.js'),G=require('../geography.js'),C=require('../catalog.js');globalThis.crypto ||= require('node:crypto').webcrypto;
const read=p=>JSON.parse(fs.readFileSync(p)),index=read('data/public/index.json'),rows=index.map(r=>({id:r[0],company_id:r[1],name:r[2],city:r[3],country:r[4],lat:r[5],lng:r[6],categories:r[7],evidence_class:r[11],record_kind:r[12]})),v=read('data/public/visibility.json');
test('complete actual company audit and display coordinates leave original records immutable',()=>{
 G.validate(v,rows,D);assert.equal(Object.keys(v.company_audit).length,1677);const before=JSON.stringify(rows),points=G.viewPoints(rows,v),id='boutique-5926fcc99b16ed8ea595dcf5459f';assert.equal(rows.find(r=>r.id===id).lat,null);const display=points.find(r=>r.id===id);assert.equal(display.display_kind,'company_reference_location');assert.equal(display.lat,-41.28664);assert.equal(display.evidence_class,'C');assert.equal(JSON.stringify(rows),before);
});
test('reference metadata cannot move original points, inherit geography or assert a verified facility',()=>{
 for(const change of [p=>p.facility_verified=true,p=>p.human_approved=true,p=>p.precision='exact',p=>p.country='Australia',p=>p.coordinate_source='javascript:bad',p=>p.lat=100]){const bad=structuredClone(v);change(Object.values(bad.references)[0]);assert.throws(()=>G.validate(bad,rows,D));}
 const incomplete=structuredClone(v);delete incomplete.company_audit[Object.keys(incomplete.company_audit)[0]];assert.throws(()=>G.validate(incomplete,rows,D),/Incomplete/);
});
test('CSV reference location is separate, licensed and never replaces original coordinates',async()=>{
 const catalog=await C.load(D,async url=>new Response(fs.readFileSync(url.split('?')[0]))),id='boutique-5926fcc99b16ed8ea595dcf5459f',raw=await catalog.details(id),bundle=await catalog.exportBundle(catalog.rows.filter(r=>r.id===id));assert.equal(raw.lat,null);assert.equal(bundle.rows[0].lat,null);assert.equal(bundle.rows[0].company_reference_location.precision,'city');assert.match(bundle.licenseTexts,/Creative Commons Attribution/);assert.match(bundle.notices,/not studio entrances/);assert.match(D.exportCSV(bundle.rows,bundle),/company_reference_location/);
});
