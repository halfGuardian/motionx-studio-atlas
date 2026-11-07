const test=require('node:test'),assert=require('node:assert/strict'),B=require('../boutique.js'),fs=require('node:fs'),path=require('node:path');
test('boutique filters combine independent signals with AND and preserve evidence classes',()=>{
  const rows=[{id:'one',evidence_class:'C'},{id:'two',evidence_class:'A'}],profiles={one:{score:50,signals:{cinematics:20,realtime:20,character:10},region:'Asia',size_claim:'Small',research_status:'source_listed_research'},two:{score:10,signals:{animation:10},region:'Europe',size_claim:'Unknown',research_status:'taxonomy_lead'}};
  assert.deepEqual(B.filter(rows,profiles,{cinematics:true,realtime:true,performance:true,region:'Asia',minimum:40}),[rows[0]]);assert.deepEqual(B.filter(rows,profiles,{size:'Unknown'}),[rows[1]]);assert.equal(B.filter(rows,profiles,{status:'primary_claims_reviewed'}).length,0);assert.equal(rows[0].evidence_class,'C');
  profiles.one.research_terms=['Unreal Engine','Mocap cleanup'];assert.deepEqual(B.filter(rows,profiles,{query:'Unreal'}),[rows[0]]);assert.deepEqual(B.filter(rows,profiles,{query:'Facial Capture'}),[]);
});
test('actual research-visible data contains both seed businesses with real provenance, without reading benchmarks',()=>{
  const folder=path.join(__dirname,'../data/public'),m=JSON.parse(fs.readFileSync(path.join(folder,'manifest.json'))),index=JSON.parse(fs.readFileSync(path.join(folder,'index.json'))),meta=JSON.parse(fs.readFileSync(path.join(folder,'boutique.json')));
  const frame=index.find(r=>r[0]==='overture-39fd34a0-9be1-4ac0-a46e-ebd53a1599ff'),floating=index.find(r=>r[2]==='Floating Rock Studio');assert.ok(frame&&floating);assert.equal(frame[2],'Frame Machine');
  for(const entry of [frame,floating]){assert.ok(meta.profiles[entry[0]]);const detail=JSON.parse(fs.readFileSync(path.join(folder,entry[8]))).find(r=>r.id===entry[0]);assert.ok(detail.source_provenance.length);assert.equal(detail.evidence_class,'C');}
  assert.equal(floating[5],null);assert.ok(meta.profiles[frame[0]].sources.some(s=>s.url.includes('framemachine.tv')));assert.ok(meta.profiles[floating[0]].sources.some(s=>s.url.includes('nzfilm.co.nz')));assert.equal(m.counts.records,41735+m.counts.company_references-1116);
});
