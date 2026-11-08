'use strict';
const test=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),D=require('../data.js'),C=require('../commercial.js'),Catalog=require('../catalog.js');globalThis.crypto ||= require('node:crypto').webcrypto;
const policy=JSON.parse(fs.readFileSync('data/public/commercial.json'));
test('game developer eligibility adds neither capture nor provider claims',()=>{
 const r={id:'game',categories:['Game Development'],capabilities:[]},before=JSON.stringify(r),a=C.classify(r,policy);assert.equal(a.role,'potential_client');assert.equal(a.excluded,false);assert.equal(C.matches(a,'provider'),false);assert.equal(C.matches(a,'client'),true);assert.equal(JSON.stringify(r),before);
});
test('reviewed audio-only exclusions are reversible and mixed visual/audio retained',()=>{
 const a=C.classify({id:'nzcensus-1238fc887e8013b884ea4e5ef08a'},policy);assert.equal(C.matches(a,''),false);assert.equal(C.matches(a,'','all'),true);assert.equal(C.matches(a,'out_of_scope','excluded'),true);assert.equal(C.classify({id:'nzcensus-6555982e90d64a7764473f0d6967'},policy).excluded,false);assert.equal(C.classify({id:'fixture',categories:['VFX','Audio Post-production']},policy).role,'potential_client');
});
test('complete actual index, role filters and exports retain all original records',async()=>{
 const c=await Catalog.load(D,async url=>new Response(fs.readFileSync(url.split('?')[0]))),before=JSON.stringify(c.rows),i=D.createDirectoryIndex(c.rows,c.commercial);assert.equal(c.rows.length,42296);assert.equal(D.queryDirectory(i).length,42292);assert.equal(D.queryDirectory(i,{scopeMode:'all'}).length,42296);assert.equal(D.queryDirectory(i,{scopeMode:'excluded'}).length,4);
 const games=D.queryDirectory(i,{sector:'Game Development',commercialRole:'client'});assert.ok(games.length>=1116);assert.ok(games.some(r=>!r.capabilities.length));const audio=D.queryDirectory(i,{scopeMode:'excluded'});const b=await c.exportBundle(audio);assert.equal(b.rows.length,4);assert.ok(b.rows.every(r=>r.commercial_role==='out_of_scope'&&r.directory_scope==='excluded_audio_only'));assert.equal(JSON.stringify(c.rows),before);assert.match(D.exportCSV(b.rows,b),/commercial_evidence/);assert.doesNotMatch(D.exportCSV(b.rows,b).split('\r\n')[0],/advisory_service_alignment/);
});
test('scope sidecar cannot invent approval, move records or hide unknown names',()=>{
 const ids=Object.values(policy.overrides).map(r=>({id:r.record_id,name:r.name}));const p=structuredClone(policy);p.baseline_records=ids.length;C.validate(p,ids,D);
 for(const fn of [r=>r.human_approved=true,r=>r.role='verified_buyer',r=>r.evidence=['javascript:bad'],r=>r.name='Wrong identity',r=>r.excluded=!r.excluded]){const bad=structuredClone(p);fn(Object.values(bad.overrides)[0]);assert.throws(()=>C.validate(bad,ids,D));}
 assert.equal(C.classify({id:'sound-games',categories:['Game Development']},p).excluded,false);
});

test('generic production stays plausible, with explicit sector confidence and original source categories',()=>{
 const rows=[['Film / Video Production'],['Film / Television Production'],['Game Publishing']];
 for(const categories of rows){const row={id:'generic',categories},before=structuredClone(row),a=C.classify(row,policy);assert.equal(a.role,'plausible_unconfirmed');assert.equal(a.confidence,'plausible_sector_only');assert.equal(C.matches(a,'client'),false);assert.equal(C.matches(a,'plausible_unconfirmed'),true);assert.deepEqual(row,before);}
 for(const categories of [['Animation'],['VFX'],['Game Development']]){const a=C.classify({id:'explicit',categories},policy);assert.equal(C.matches(a,'client'),true);assert.equal(a.confidence,'explicit_sector_eligibility');assert.equal(a.facility_verified,false);}
 assert.equal(C.classify({id:'sound-film',categories:['Film / Video Production']},policy).excluded,false);
});

test('visual production eligibility does not imply an external service offer',()=>{
 const visual=C.classify({id:'fixture',categories:['Animation','VFX','Audio Post-production']},policy);
 assert.equal(visual.role,'potential_client');assert.equal(C.matches(visual,'provider'),false);assert.equal(visual.excluded,false);
 assert.equal(C.classify({id:'fixture',categories:['Animation','Motion Editing']},policy).role,'both');
});
