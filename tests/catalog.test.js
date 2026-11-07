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
test('boutique metadata loads lazily, verifies integrity, and retries without losing atlas rows',async()=>{
  const s=await server(),p={record_id:'original',name:'Example',country:'Canada',region:'North America',score:10,signals:{animation:10},research_terms:['Animation'],size_claim:'Unknown',size_reviewed_on:'',independence:'unknown',external_support_need:'unknown',purchasing_intent:'unknown',research_status:'taxonomy_lead',sources:[{url:'https://example.test',basis:'existing_record_taxonomy',observed_on:'2026-11-07'}]};
  const text=JSON.stringify({version:1,profiles:{original:p},summary:{}});s.manifest.boutique={path:'boutique.json',sha256:await C.sha(text)};s.files.set('./data/public/manifest.json',JSON.stringify(s.manifest));const catalog=await C.load(D,s.fetcher);
  assert.equal(s.calls.some(p=>p.includes('boutique')),false);await assert.rejects(catalog.boutique(),/404/);assert.equal(catalog.rows.length,2);
  s.files.set('./data/public/boutique.json',text+' ');await assert.rejects(catalog.boutique(),/integrity/);s.files.set('./data/public/boutique.json',text);assert.equal((await catalog.boutique()).profiles.original.score,10);assert.equal(catalog.rows[0].evidence_class,'A');
});
test('boutique payload cannot assert purchasing intent, inject capability scores or unsafe URLs',async()=>{
  for(const mutate of [p=>p.purchasing_intent='likely',p=>p.external_support_need='high',p=>p.signals={capture_stage:10},p=>p.sources[0].url='javascript:alert(1)',p=>p.research_terms=[{}]]){
    const s=await server(),p={record_id:'original',name:'Example',country:'Canada',region:'North America',score:10,signals:{animation:10},research_terms:['Animation'],size_claim:'Unknown',size_reviewed_on:'',independence:'unknown',external_support_need:'unknown',purchasing_intent:'unknown',research_status:'taxonomy_lead',sources:[{url:'https://example.test',basis:'existing_record_taxonomy',observed_on:'2026-11-07'}]};mutate(p);const text=JSON.stringify({version:1,profiles:{original:p}});s.manifest.boutique={path:'boutique.json',sha256:await C.sha(text)};s.files.set('./data/public/boutique.json',text);s.files.set('./data/public/manifest.json',JSON.stringify(s.manifest));const catalog=await C.load(D,s.fetcher);await assert.rejects(catalog.boutique(),/Invalid/);assert.equal(catalog.rows.length,2);
  }
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
test('CSV supplies full licence copies and fails closed when required notices are unavailable',async()=>{
  const s=await server(),text='Test CC0 licence text\nThis is a fixture, not an acquired dataset.';
  s.files.set('./data/bulk/LICENSES/CC0-1.0.txt',text);s.manifest.licence_files={'CC0-1.0.txt':{sha256:await C.sha(text)}};
  s.files.set('./data/public/manifest.json',JSON.stringify(s.manifest));const catalog=await C.load(D,s.fetcher),bundle=await catalog.exportBundle(catalog.rows);
  assert.match(D.exportCSV(bundle.rows,bundle),/Test CC0 licence text/);
  s.files.delete('./data/bulk/LICENSES/CC0-1.0.txt');await assert.rejects(catalog.exportBundle(catalog.rows),/notices unavailable/);
});
test('inclusive research validation accepts a company without a pin but never verified services',()=>{
  const {row}=fixture();Object.assign(row,{record_kind:'company_reference',evidence_class:'C',city:'',lat:null,lng:null,coordinate_precision:'unverified',license:'UNSPECIFIED'});
  C.checkResearch(D,row);assert.throws(()=>C.checkResearch(D,{...row,lat:51,lng:0}),/coordinates/);
  assert.throws(()=>C.checkResearch(D,{...row,verified_on:'2026-11-06'}),/verification/);
  const rows=[row,{...row,id:'source-location',record_kind:'source_location',lat:51,lng:0}],index=D.createDirectoryIndex(rows);
  assert.equal(D.queryDirectory(index,{recordKind:'company_reference'}).length,1);
  assert.equal(D.queryDirectory(index,{confirmedOnly:true}).length,0);
});
test('compressed unified catalogue keeps legacy and company references; corrupted gzip fails without fallback',async()=>{
  const s=await server(),{gzipSync}=require('node:zlib'),{createHash}=require('node:crypto');
  s.f.row.record_kind='source_location';const company={...s.f.row,id:'company-only',company_id:'company-only-org',name:'Company Without Pin',city:'',lat:null,lng:null,evidence_class:'C',record_kind:'company_reference',coordinate_precision:'unverified'};
  const data=[s.f.row,company],packedIndex=[s.f.index[0].concat(['B','source_location']),[company.id,company.company_id,company.name,company.city,company.country,null,null,company.categories,s.f.key,company.source_observed_on,company.identity_status,'C','company_reference']];
  s.manifest.mode='unified_research';s.manifest.baseline.active_ids=[s.f.a.id,s.f.held.id];s.manifest.baseline.research_only_ids=[];s.manifest.counts={records:4,class_a:1,class_b:1,class_c:2};
  for(const [path,value,meta] of [['./data/public/index.json',packedIndex,s.manifest.index],['./data/public/'+s.f.key,data,s.manifest.shards[s.f.key]]]){
    const text=JSON.stringify(value),packed=gzipSync(text);meta.sha256=await C.sha(text);meta.gzip_sha256=createHash('sha256').update(packed).digest('hex');meta.records=value.length;s.files.set(path,text);s.files.set(path+'.gz',packed);
  }
  s.files.set('./data/public/manifest.json',JSON.stringify(s.manifest));const catalog=await C.load(D,s.fetcher);
  assert.equal(catalog.rows.length,4);assert.equal(catalog.rows.find(r=>r.id==='legacy').evidence_class,'C');assert.equal((await catalog.details('company-only')).lat,null);
  assert.ok(s.calls.includes('./data/public/index.json.gz'));assert.ok(!s.calls.includes('./data/public/index.json'));
  const bytes=Buffer.from(s.files.get('./data/public/index.json.gz'));bytes[bytes.length-2]^=1;s.files.set('./data/public/index.json.gz',bytes);
  await assert.rejects(C.load(D,s.fetcher),/integrity/);
});
test('real compact transport preserves every identity, category and original coordinate',()=>{
  const fs=require('node:fs'),path=require('node:path'),folder=path.join(__dirname,'../data/public');
  const original=JSON.parse(fs.readFileSync(path.join(folder,'index.json'),'utf8')),packed=JSON.parse(fs.readFileSync(path.join(folder,'index.compact.json'),'utf8'));
  const rows=C.decodeIndex(packed,original.length).map(r=>r.slice(0,13)).sort((a,b)=>a[0]<b[0]?-1:1);
  assert.deepEqual(rows,original);assert.equal(rows.filter(r=>r[12]==='company_reference').length,JSON.parse(fs.readFileSync(path.join(folder,'manifest.json'),'utf8')).counts.company_references);assert.equal(rows.filter(r=>r[0].startsWith('gamedb-')).length,1116);
});
test('malformed column lengths, dictionary references and identity encodings fail closed',()=>{
  const fs=require('node:fs'),packed=JSON.parse(fs.readFileSync(require('node:path').join(__dirname,'../data/public/index.compact.json'),'utf8'));
  for(const mutate of [v=>v.columns[0].pop(),v=>v.columns[3][0]=-1,v=>v.columns[0][0]='~uINVALID',v=>v.columns[13][0]=32]){
    const changed=structuredClone(packed);mutate(changed);assert.throws(()=>C.decodeIndex(changed,packed.rows));
  }
});
test('compact index reports progress, uses versioned cache keys and never falls back after corruption',async()=>{
  const s=await server(),entry=s.f.index[0].concat(['B','source_location',17]),tables={},columns=entry.map(v=>[v]);
  for(const k of [3,4,7,8,9,10,11,12]){tables[k]=[entry[k]];columns[k]=[0];}
  const text=JSON.stringify({encoding:'motionx-columnar-v1',rows:1,tables,columns}),gzip=require('node:zlib').gzipSync(text),hash=await C.sha(text),ghash=require('node:crypto').createHash('sha256').update(gzip).digest('hex');
  s.manifest.mode='unified_research';s.manifest.baseline.active_ids=['original','legacy'];s.manifest.baseline.research_only_ids=[];s.manifest.counts={records:3,class_a:1,class_b:1,class_c:1};
  s.manifest.index.compact={path:'index.compact.json',encoding:'motionx-columnar-v1',sha256:hash,gzip_sha256:ghash,records:1,content_addressed:true};
  const key='./data/public/index.compact.json.gz?sha256='+hash;s.files.set(key,gzip);s.files.set('./data/public/manifest.json',JSON.stringify(s.manifest));
  const progress=[],cache=[];let release,complete=false;const gate=new Promise(resolve=>release=resolve);
  const fetcher=async(path,options)=>{cache.push([path,options.cache]);if(path===key)await gate;return s.fetcher(path,options);};
  const loading=C.load(D,fetcher,undefined,{onProgress:info=>progress.push(info)}).then(v=>{complete=true;return v;});
  await new Promise(resolve=>setImmediate(resolve));assert.equal(complete,false);release();const catalog=await loading;
  assert.equal(catalog.rows.length,3);assert.ok(progress.some(p=>p.received>0));assert.ok(cache.some(([p,c])=>p===key&&c==='force-cache'));assert.ok(!s.calls.includes('./data/public/index.json'));
  const broken=Buffer.from(gzip);broken[12]^=1;s.files.set(key,broken);await assert.rejects(C.load(D,s.fetcher),/integrity/);assert.ok(!s.calls.includes('./data/public/index.json'));
});
