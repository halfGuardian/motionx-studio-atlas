'use strict';
const test=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),D=require('../data.js'),Catalog=require('../catalog.js'),G=require('../geography.js');globalThis.crypto ||= require('node:crypto').webcrypto;
const read=p=>JSON.parse(fs.readFileSync(p));
const load=()=>Catalog.load(D,async url=>new Response(fs.readFileSync(url.split('?')[0])));
test('integrated new company sectors and source labels survive lazy details and exports',async()=>{
 const c=await load(),i=D.createDirectoryIndex(c.rows,c.commercial,c.visibility),expected=read('data/release-candidate/reports/integrated-records.json');
 assert.equal(c.rows.length,42478);assert.equal(D.queryDirectory(i).length,42474);assert.equal(expected.length,182);
 for(const row of expected){const actual=await c.details(row.id);assert.deepEqual(actual,row);assert.equal(actual.capabilities.length,0);assert.equal(actual.research_review.human_approved,false);assert.equal(actual.lat,null);}
 for(const name of ['Able & Baker','a_BAHN','Animadre Studio'])assert.equal(D.queryDirectory(i,{query:name,sector:'Animation'}).length,1);
 const games=D.queryDirectory(i,{query:'2Up Games',sector:'Game Development',commercialRole:'client'});assert.equal(games.length,1);assert.equal(games[0].capabilities.length,0);assert.equal(D.queryDirectory(i,{query:'2Up Games',confirmedOnly:true}).length,0);
 const bundle=await c.exportBundle(c.rows.filter(r=>r.id.startsWith('globalcompany-')));assert.equal(bundle.rows.length,182);assert.ok(bundle.rows.every(r=>r.source_category&&r.license==='UNSPECIFIED'));assert.match(bundle.notices,/no explicit dataset redistribution licence/);
});
test('additional same-country city references remain one company with original null coordinates',async()=>{
 const c=await load(),i=D.createDirectoryIndex(c.rows,c.commercial,c.visibility),id='boutique-bd922ba2cd1dcd66361049c27ed0',row=c.rows.find(r=>r.id===id),before=JSON.stringify(row);
 assert.equal(D.queryDirectory(i,{query:'ModelFarm',city:'Brisbane'}).length,1);const points=G.viewPoints([row],c.visibility);assert.deepEqual(points.map(p=>p.city),['Adelaide','Brisbane']);assert.ok(points.every(p=>p.id===id&&p.evidence_class==='C'));assert.equal(JSON.stringify(row),before);
 const b=await c.exportBundle([row]);assert.equal(b.rows[0].lat,null);assert.equal(b.rows[0].company_reference_location.city,'Adelaide');assert.equal(b.rows[0].additional_company_reference_locations[0].city,'Brisbane');assert.match(b.licenseTexts,/Creative Commons Attribution/);
 const bad=structuredClone(c.visibility);bad.additional_references[id][0].country='New Zealand';assert.throws(()=>G.validate(bad,c.rows,D));bad.additional_references[id][0].country='Australia';bad.additional_references[id][0].human_approved=true;assert.throws(()=>G.validate(bad,c.rows,D));
});
