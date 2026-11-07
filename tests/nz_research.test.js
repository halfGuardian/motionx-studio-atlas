'use strict';
const test=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
globalThis.crypto ||= require('node:crypto').webcrypto;
const review=require('../nz-review.js'),D=require('../data.js'),C=require('../catalog.js');
const root=path.join(__dirname,'..'),proposed=JSON.parse(fs.readFileSync(path.join(root,'data/nz-census/reports/proposals.json'))).company_references;
test('NZ dashboard ANDs text, outcome and source without hiding source identity',()=>{
  assert.ok(review.matches('Assembly New Zealand','new_reference',' ASSEMBLY ','new_reference','screen-auckland-digital','screen-auckland-digital'));
  assert.equal(review.matches('Assembly','new_reference','','represented'),false);
  assert.equal(review.matches('Assembly','new_reference','','','screen-auckland-digital','nzonair-gdsr'),false);
  assert.ok(review.matches('Wētā Workshop','new_reference','wētā',''));
});
test('all real NZ references validate, retain shareable routes and have no pins or confirmed capabilities',()=>{
  assert.equal(proposed.length,59);
  const index=JSON.parse(fs.readFileSync(path.join(root,'data/public/index.json')));
  for(const row of proposed){
    C.checkResearch(D,row);assert.equal(row.evidence_class,'C');assert.equal(row.record_kind,'company_reference');assert.equal(row.lat,null);assert.deepEqual(row.capabilities,[]);
    assert.ok(index.some(r=>r[0]===row.id));assert.deepEqual(D.parseProfileHash(D.profileHash('location',row.id)),{kind:'location',id:row.id});
  }
});
async function actualCatalog(corrupt=false){
  return C.load(D,async url=>{
    const local=url.split('?')[0];assert.match(local,/^\.\/(data\/public\/|data\/bulk\/LICENSES\/|studios.json)/);assert.equal(local.includes('..'),false);
    const p=path.join(root,local),body=corrupt&&local.endsWith('NZ-On-Air-Permission.txt')?'changed grant':fs.readFileSync(p);
    return new Response(body,{status:200});
  });
}
test('actual lazy NZ shard and export include exact scoped NZ On Air grant, never CC BY',async()=>{
  const c=await actualCatalog(),row=proposed.find(r=>r.name==='Balancing Monkey Games');
  const detail=await c.details(row.id);assert.deepEqual(detail,row);
  const bundle=await c.exportBundle(c.rows.filter(r=>r.id===row.id));
  assert.equal(bundle.rows.length,1);assert.match(bundle.licenseTexts,/Copyright © NZ On Air/);assert.match(bundle.licenseTexts,/copyright-and-terms-use/);assert.doesNotMatch(bundle.licenseTexts,/Creative Commons Attribution/);
});
test('scoped source grant still fails closed when exported notice hash is corrupted',async()=>{
  const c=await actualCatalog(true),row=proposed.find(r=>r.name==='Balancing Monkey Games');
  await assert.rejects(c.exportBundle(c.rows.filter(r=>r.id===row.id)),/integrity mismatch/);
});

test('malformed collision notes fail validation before profile rendering',()=>{
  const row=structuredClone(proposed.find(r=>r.potential_duplicates.length));delete row.potential_duplicates[0].reasons;
  assert.throws(()=>C.checkResearch(D,row),/duplicate review metadata/);
});
