const test=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),zlib=require('node:zlib');
const G=require('../global-review.js');
test('working notes bind exact content and never become human approval',()=>{
 const rows=[{observation_id:'obs',content_hash:'a'.repeat(64)}];const value=G.bundle('b'.repeat(64),{obs:{decision:'needs_evidence',content_hash:'a'.repeat(64),notes:'Pending independent source check'}},rows);
 assert.equal(value.human_approved,false);assert.equal(value.authenticated_review,false);assert.deepEqual(value.canonical_updates,[]);assert.equal(value.decisions[0].human_approved,false);
 assert.throws(()=>G.bundle('b'.repeat(64),{obs:{decision:'needs_evidence',content_hash:'c'.repeat(64),notes:''}},rows));assert.throws(()=>G.bundle('b'.repeat(64),{obs:{decision:'approved',content_hash:'a'.repeat(64),notes:''}},rows));
});
test('formula-safe CSV and evidence links reject executable or credential URLs',()=>{
 for(const v of ['=1','\u200b+SUM(1)','  @cmd','-2'])assert.ok(G.cell(v).startsWith("'"));assert.ok(G.csv([{name:'"line\nnext',notes:'=cmd'}],['name','notes']).includes("'=cmd"));
 for(const v of ['javascript:alert(1)','https://user:pass@example.org/','http://example.org/','https://example.org:444/'])assert.equal(G.safeURL(v),null);assert.equal(G.safeURL('https://example.org/'),'https://example.org/');
});
test('actual global index filters all observations without treating names as verified facilities',()=>{
 const data=JSON.parse(zlib.gunzipSync(fs.readFileSync('data/global-programme/reports/review-index.json.gz'))),rows=data.rows.map(values=>Object.fromEntries(data.fields.map((k,i)=>[k,values[i]])));
 assert.equal(rows.length,data.summary.replayed_observations);assert.equal(G.filter(rows,{country:'New Zealand',q:'Floating Rock'}).length>0,true);assert.equal(G.filter(rows,{outcome:'potential_new_company'}).every(r=>r.disposition==='potential_new_company'),true);assert.equal(data.summary.new_independently_verified_facilities,0);assert.equal(data.summary.human_precision,null);
});
