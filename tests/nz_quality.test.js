'use strict';
const test=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
globalThis.crypto ||= require('node:crypto').webcrypto;
const G=require('../nz-final-review.js'),D=require('../data.js'),C=require('../catalog.js'),root=path.join(__dirname,'..');
const original=JSON.parse(fs.readFileSync(path.join(root,'data/nz-census/reports/proposals.json'))).company_references;
async function load(){return C.load(D,async url=>{const local=url.split('?')[0];assert.match(local,/^\.\/(data\/public\/|data\/bulk\/LICENSES\/|studios.json)/);assert.equal(local.includes('..'),false);return new Response(fs.readFileSync(path.join(root,local)));});}
test('maintainer filters AND item kind, relevance, readiness and text',()=>{
 assert.ok(G.matches('Assembly animation','company','motionx_core','eligible_minimal_factual_reference',{query:' ASSEMBLY ',kind:'company',relevance:'motionx_core'}));
 assert.equal(G.matches('Melodics','company','out_of_scope','staged_scope_review',{readiness:'eligible_source_authorised_identity'}),false);
 assert.equal(G.matches('Avalon','facility','supporting_services','pending',{kind:'company'}),false);
});
test('selecting accept only exports working notes and cannot create approval or a reviewer',()=>{
 const draft=G.workingDraft('a'.repeat(64),[{item_id:'company-one',content_hash:'b'.repeat(64),decision:'accept_provisional',notes:'Working evidence note',human_approved:true,human_reviewer:'fabricated'}]);
 assert.equal(draft.kind,'unauthenticated_working_draft');assert.equal(draft.human_approved,false);assert.equal(draft.publication_authorised,false);assert.equal(draft.items[0].human_approved,false);assert.equal(draft.items[0].human_reviewer,null);
 assert.equal(draft.items[0].human_decision,'accept_provisional');assert.throws(()=>G.workingDraft('bad',[]),/checkpoint/);
 assert.throws(()=>G.workingDraft('a'.repeat(64),[{item_id:'one',content_hash:'b'.repeat(64),decision:'publish_now'}]),/working review/);
});
test('worksheet drafts remain content-bound, unique and size-limited',()=>{
 const i={item_id:'one',content_hash:'b'.repeat(64),notes:'x'.repeat(5000)};assert.equal(G.workingDraft('a'.repeat(64),[i]).items[0].human_notes.length,4000);
 assert.throws(()=>G.workingDraft('a'.repeat(64),[i,i]),/working review/);
 const w=JSON.parse(fs.readFileSync(path.join(root,'data/nz-census/final-review/reports/worksheet.json')));assert.equal(w.items.length,91);assert.ok(w.items.every(i=>i.human_decision===null&&i.human_approved===false));
});
test('actual staged identities are excluded from search, lazy profiles and export bundles',async()=>{
 const c=await load(),staged=original.filter(r=>['Melodics','Level'].includes(r.name));assert.equal(c.rows.length,c.manifest.counts.records);assert.equal(c.staged.size,2);
 for(const r of staged){assert.ok(c.staged.has(r.id));assert.equal(c.rows.some(x=>x.id===r.id),false);await assert.rejects(c.details(r.id),/identity unavailable/i);await assert.rejects(c.exportBundle([{id:r.id}]),/identity unavailable/i);}
});
test('company review metadata validates and cannot elevate an agency lead to verified capabilities',async()=>{
 const c=await load(),r=original.find(r=>r.name==='Balancing Monkey Games'),full=await c.details(r.id);assert.equal(full.research_review.operation_status,'programme_listing_only');assert.equal(full.research_review.relevance,'game_development');assert.deepEqual(full.capabilities,[]);assert.equal(full.evidence_class,'C');
 for(const [field,value] of [['human_approved',true],['facility_verified',true],['publication_state','approved'],['relevance','out_of_scope']]){const bad=structuredClone(full);bad.research_review[field]=value;assert.throws(()=>C.checkResearch(D,bad),/company research review/);}
});
test('playtesting export labels source assertions separately and keeps the scoped agency licence',async()=>{
 const c=await load(),r=original.find(r=>r.name==='Insight Creative'),full=await c.details(r.id);assert.deepEqual(full.categories,['Game Production Support']);assert.equal(full.research_review.relevance,'supporting_services');assert.deepEqual(full.capabilities,[]);
 const bundle=await c.exportBundle(c.rows.filter(row=>row.id===r.id));assert.equal(bundle.rows.length,1);const csv=D.exportCSV(bundle.rows,bundle);assert.match(csv,/research_review/);assert.match(csv,/source_category/);assert.match(csv,/provisional_research_lead/);assert.match(csv,/NZ On Air/);
});
