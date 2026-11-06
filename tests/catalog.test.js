'use strict';
const {test}=require('node:test'),assert=require('node:assert/strict');
globalThis.crypto ||= require('node:crypto').webcrypto;
const D=require('../data.js'),C=require('../catalog.js');
const original=require('../studios.json').find(r=>r.evidence_state==='confirmed');
function fixture(){
  const a={...original,id:'original',company_id:'original-org'};
  const held={...a,id:'legacy',evidence_state:'unknown',capabilities:[],capability_evidence:{},verified_on:''};
  const row={...a,id:'source-one',company_id:'source-org',name:'Example Source Studio',categories:['Animation'],capabilities:[],capability_evidence:{},relationships:[],evidence_class:'B',evidence_state:'unknown',verified_on:'',coordinate_precision:'approximate',location_type:'uncertain',source_observed_on:'2026-11-06',identity_status:'source_provisional',website_kind:'official',license:'CC0-1.0',attribution:'Test provider',source_provenance:[{source_id:'test',source_record_id:'1',url:'https://example.test/1',license_url:'https://example.test/licence',observed_on:'2026-11-06',observation_hash:'a'.repeat(64)}]};
  const key='shards/123456789abc-000.json',index=[[row.id,row.company_id,row.name,row.city,row.country,row.lat,row.lng,row.categories,key,row.source_observed_on,row.identity_status]];
  return {a,held,row,key,index};
}
async function server(f=fixture()){
  const files=new Map([['./studios.json',JSON.stringify([f.a,f.held])],['./data/public/index.json',JSON.stringify(f.index)],['./data/public/'+f.key,JSON.stringify([f.row])]]);
  const manifest={version:1,baseline:{path:'./studios.json',sha256:await C.sha(files.get('./studios.json')),eligible_ids:[f.a.id],research_only_ids:[f.held.id]},index:{path:'index.json',sha256:await C.sha(files.get('./data/public/index.json')),records:1},shards:{[f.key]:{sha256:await C.sha(files.get('./data/public/'+f.key)),records:1}},counts:{public_locations:2,class_a:1,class_b:1}};
  files.set('./data/public/manifest.json',JSON.stringify(manifest));const calls=[];
  const fetcher=async path=>{calls.push(path);return new Response(files.get(path)||'missing',{status:files.has(path)?200:404});};
  return {files,calls,manifest,fetcher,f};
}
test('index loads every A/B location; provenance shards are lazy and shared',async()=>{
  const s=await server(),catalog=await C.load(D,s.fetcher);
  assert.equal(catalog.rows.length,2);assert.equal(catalog.researchOnly.has('legacy'),true);
  assert.equal(s.calls.length,3);assert.equal(catalog.rows[1].evidence_class,'B');assert.equal(catalog.rows[1].website,undefined);
  const [one,two]=await Promise.all([catalog.details('source-one'),catalog.details('source-one')]);
  assert.equal(one,two);assert.equal(s.calls.filter(p=>p.includes('/shards/')).length,1);
  assert.deepEqual(await catalog.exportRows(catalog.rows),[{...s.f.a,evidence_class:'A'},s.f.row]);
});
test('A/B filter and confirmed capabilities never inherit directory sector claims',async()=>{
  const s=await server(),catalog=await C.load(D,s.fetcher),index=D.createDirectoryIndex(catalog.rows);
  assert.equal(D.queryDirectory(index,{evidenceClass:'B'}).length,1);
  assert.equal(D.queryDirectory(index,{evidenceClass:'B',confirmedOnly:true}).length,0);
  assert.equal(D.queryDirectory(index,{evidenceClass:'B',capabilities:['Animation']}).length,0);
  assert.equal(D.queryDirectory(index,{evidenceClass:'B',sector:'Animation'}).length,1);
});
test('baseline or index tampering fails closed; no partial data fallback',async()=>{
  for(const path of ['./studios.json','./data/public/index.json']){
    const s=await server();s.files.set(path,s.files.get(path)+' ');
    await assert.rejects(C.load(D,s.fetcher),/integrity/);
  }
});
test('corrupt/missing shard fails export without returning partial rows and can retry',async()=>{
  const s=await server(),catalog=await C.load(D,s.fetcher),key='./data/public/'+s.f.key,raw=s.files.get(key);
  s.files.delete(key);await assert.rejects(catalog.exportRows(catalog.rows),/HTTP 404/);
  s.files.set(key,raw+' ');await assert.rejects(catalog.details('source-one'),/integrity/);
  s.files.set(key,raw);assert.equal((await catalog.details('source-one')).id,'source-one');
});
test('indexed path traversal, duplicate IDs and coordinate mismatches rejected',async()=>{
  for(const mutate of [f=>{f.index[0][8]='../studios.json';},f=>{f.index[0][0]='original';},f=>{f.index[0][5]=1000;}]){
    const f=fixture();mutate(f);const s=await server(f);await assert.rejects(C.load(D,s.fetcher),/indexed/);
  }
  const f=fixture();f.row.lat+=1;const s=await server(f),catalog=await C.load(D,s.fetcher);
  await assert.rejects(catalog.details('source-one'),/identity mismatch/);
});
test('source-listed rows cannot acquire verified claims or unsafe provenance',()=>{
  for(const mutate of [r=>r.verified_on='2026-11-06',r=>r.evidence_state='confirmed',r=>r.coordinate_precision='exact',r=>r.source_provenance[0].url='javascript:alert(1)',r=>r.capabilities=['Motion Capture']]){
    const {row}=fixture();mutate(row);assert.throws(()=>C.checkB(D,row));
  }
});
test('legacy C profile stays in research and unknown identity fails clearly',async()=>{
  const s=await server(),catalog=await C.load(D,s.fetcher);
  await assert.rejects(catalog.details('legacy'),/research queue/);await assert.rejects(catalog.details('missing'),/unavailable/);
});
test('CSV carries class, source attribution and full provenance',async()=>{
  const s=await server(),catalog=await C.load(D,s.fetcher),rows=await catalog.exportRows(catalog.rows),csv=D.exportCSV(rows);
  assert.match(csv,/source_provenance/);assert.match(csv,/CC0-1.0/);assert.match(csv,/Test provider/);
});
