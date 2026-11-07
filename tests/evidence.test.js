'use strict';
const {test}=require('node:test'),assert=require('node:assert/strict'),D=require('../data.js');
const base=require('../studios.json').find(r=>D.confirmedCapture(r));
function row(id,cls,extra={}){return {...base,id,company_id:id+'-org',name:'Research '+id,record_kind:'source_location',evidence_state:'unknown',evidence_class:cls,capabilities:[],capability_evidence:{},categories:['Animation'],relationships:[],...extra};}
test('A/B/C use the specified colours and different non-colour symbols',()=>{
  assert.deepEqual(Object.values(D.evidenceStyles).map(s=>s.colour),['#238B67','#347FBA','#B58A2A']);
  assert.equal(new Set(Object.values(D.evidenceStyles).map(s=>s.shape)).size,3);
  assert.equal(D.evidenceClass({...base,evidence_state:'unknown'}),'C');
  assert.equal(D.evidenceClass({evidence_class:'C',evidence_state:'confirmed'}),'C');
});
test('mixed clusters and identical coordinates expose every evidence class without moving a point',()=>{
  const rows=[row('one','A'),row('two','B'),row('three','C')],before=JSON.stringify(rows),groups=D.coordinateGroups(rows),clusters=D.clusterCoordinateGroups(groups,4);
  assert.equal(groups.length,1);assert.equal(clusters[0].rows.length,3);
  const info=D.markerEvidence(clusters[0].rows);assert.deepEqual(info.counts,{A:1,B:1,C:1});assert.equal(info.mixed,true);
  assert.match(info.label,/A 1 source-reviewed, B 1 directory-listed, C 1 research leads/);assert.equal(JSON.stringify(rows),before);
});
test('combined totals keep companies searchable without assigning a geographic point',()=>{
  const rows=[row('a','A'),row('b','B'),row('c','C',{record_kind:'company_reference',lat:null,lng:null,identity_status:'source_provisional'})];
  const summary=D.catalogueSummary(rows);assert.deepEqual(summary,{records:3,geolocated:2,A:1,B:1,C:1,provisionalIdentities:1,confirmedCapture:0});
  assert.equal(D.queryDirectory(D.createDirectoryIndex(rows),{}).length,3);
  for(const c of ['A','B','C'])assert.equal(D.queryDirectory(D.createDirectoryIndex(rows),{evidenceClass:c}).length,1);
});
test('confirmed capture depends on location-specific evidence, never company or sector claims',()=>{
  const approved={...base,id:'reviewed',evidence_class:'A'},source=row('unreviewed','B',{categories:['Motion Capture']}),company=row('company','C',{lat:null,lng:null});
  const index=D.createDirectoryIndex([source,company,approved]);
  assert.deepEqual(D.queryDirectory(index,{confirmedCaptureOnly:true}).map(r=>r.id),['reviewed']);
  assert.equal(D.evidenceClass(source),'B');assert.equal(D.confirmedCapture(company),false);
});
test('exact name relevance precedes class, while equal relevance prefers reviewed evidence',()=>{
  const rows=[row('c','C',{name:'Exact Studio'}),row('a','A',{name:'Exact Studio'}),row('b','B',{name:'Other Exact Studio'})];
  assert.deepEqual(D.queryDirectory(D.createDirectoryIndex(rows),{query:'Exact Studio',sort:'relevance'}).map(r=>r.id),['a','c','b']);
});
test('organisation search respects operating identities without inventing parent relationships',()=>{
  const index=D.createDirectoryIndex([row('a','A',{company_id:'operator-one',company_name:'Original Operating Brand'}),row('b','B',{company_id:'different-brand'})]);
  assert.equal(D.queryDirectory(index,{organisation:'Operating Brand'}).length,1);
  assert.equal(D.queryDirectory(index,{organisation:'operator-one'}).length,1);assert.equal(index.groups.size,0);
});
test('research flags, stale dates and sparse-country priorities are advisory only',()=>{
  const candidate=row('lead','C',{review_flags:1|8|16,source_observed_on:'2020-01-01'}),index=D.createDirectoryIndex([candidate]);
  assert.equal(D.queryDirectory(index,{researchFocus:'duplicates'}).length,1);assert.equal(D.queryDirectory(index,{researchFocus:'permission'}).length,1);
  assert.equal(D.queryDirectory(index,{researchFocus:'stale'}).length,1);assert.equal(D.queryDirectory(index,{researchFocus:'gaps'}).length,1);
  assert.ok(D.researchContext(candidate,index).priority>0);assert.equal(candidate.evidence_class,'C');assert.equal(candidate.evidence_state,'unknown');
  assert.equal(D.queryDirectory(index,{confirmedOnly:true}).length,0);
});
test('mixed-evidence CSV preserves references, formulas, classes and null coordinates',()=>{
  const csv=D.exportCSV([row('a','A'),row('b','B'),row('c','C',{name:'=HYPERLINK("bad")',lat:null,lng:null,record_kind:'company_reference'})]);
  assert.match(csv,/'=HYPERLINK/);assert.match(csv,/company_reference/);for(const c of ['A','B','C'])assert.ok(csv.includes('"'+c+'"'));
});
test('large-map cluster anchors always use an unchanged member location',()=>{
  const rows=Array.from({length:300},(_,i)=>row('point-'+i,i%3===0?'A':i%3===1?'B':'C',{lat:10+(i%20)/100,lng:20+Math.floor(i/20)/100})),before=JSON.stringify(rows);
  const clusters=D.clusterCoordinateGroups(D.coordinateGroups(rows),4);
  assert.equal(clusters.flatMap(c=>c.rows).length,rows.length);
  for(const cluster of clusters){assert.ok(cluster.rows.includes(cluster.anchor));assert.deepEqual([cluster.anchor.lat,cluster.anchor.lng],[rows.find(r=>r.id===cluster.anchor.id).lat,rows.find(r=>r.id===cluster.anchor.id).lng]);}
  assert.equal(JSON.stringify(rows),before);
});
