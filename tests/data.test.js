'use strict';
const {test} = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const {loadDatabase, validateDatabase, filterRecords} = require('../data.js');
const canonical = JSON.parse(fs.readFileSync(require('node:path').join(__dirname, '../studios.json')));
const originals=JSON.parse(fs.readFileSync(require('node:path').join(__dirname,'../data/research/v1.0-launch/evidence.json'))).before_updates;
const rows=canonical.slice(0,182).map(r=>originals[r.id]||r);
test('canonical database loads and retains all identities', () => {
  assert.equal(validateDatabase(canonical).length, 243);
  assert.equal(new Set(canonical.map(r => r.company_id)).size, 119);
});
test('relative URL is GitHub Pages compatible and disables stale cache', async () => {
  const result = await loadDatabase(async (path, options) => {
    assert.equal(path, './studios.json');
    assert.equal(options.cache, 'no-store');
    assert.ok(options.signal instanceof AbortSignal);
    return {ok: true, json: async () => rows};
  });
  assert.equal(result, rows);
});
test('HTTP failure rejects without fallback', async () => {
  await assert.rejects(loadDatabase(async () => ({ok: false, status: 404})), /HTTP 404/);
});
test('invalid JSON rejects without fallback', async () => {
  await assert.rejects(loadDatabase(async () => ({ok: true, json: async () => {throw new SyntaxError('bad JSON');}})), /bad JSON/);
});
test('network failure rejects without fallback', async () => {
  await assert.rejects(loadDatabase(async () => {throw new Error('offline');}), /offline/);
});
test('malformed database rejects the entire response', () => {
  for (const bad of [{}, null, [null], [...rows, rows[0]], [{...rows[0], lat: NaN}],
      [{...rows[0], evidence: 'javascript:alert(1)'}], [{...rows[0], capabilities: ['missing evidence']}],
      [{...rows[0], verified_on: '2026-02-30'}], [{...rows[0], website: ''}]]) {
    assert.throws(() => validateDatabase(bad));
  }
});
test('valid empty database is allowed', async () => {
  assert.deepEqual(await loadDatabase(async () => ({ok: true, json: async () => []})), []);
});
test('search and combined country / specialization filters use external records', () => {
  assert.equal(filterRecords(rows, 'beyond').length, 2);
  assert.equal(filterRecords(rows.slice(0, 31), '', '', 'Canada').length, 7);
  assert.equal(filterRecords(rows, 'facial', 'Motion Capture', 'Canada').length, 5);
  assert.equal(filterRecords(rows, 'does not exist').length, 0);
});
test('VFX-only locations do not require mocap', () => {
  const vfx = {...rows[0], categories: ['VFX'], capabilities: [], capability_evidence: {}};
  assert.equal(validateDatabase([vfx]).length, 1);
  assert.equal(filterRecords([vfx], '', 'VFX').length, 1);
  assert.equal(filterRecords([vfx], '', 'Motion Capture').length, 0);
});
test('confirmed and likely capabilities require a dated source', () => {
  const row = structuredClone(rows[0]);
  const cap = row.capabilities[0];
  row.capability_evidence[cap].state = 'likely';
  assert.throws(() => validateDatabase([row]));
  row.capability_evidence[cap].verified_on = '2024-01-01';
  assert.equal(validateDatabase([row]).length, 1);
});
test('HTML contains no embedded studio snapshot', () => {
  const html = fs.readFileSync(require('node:path').join(__dirname, '../index.html'), 'utf8');
  assert.ok(!html.includes('beyond-vancouver'));
  assert.match(html, /src="data.js"/);
  assert.match(html, /src="app.js"/);
});

test('researched VFX studios remain separate locations under stable organisations', () => {
  const ilm = filterRecords(rows, 'Industrial Light & Magic');
  assert.equal(ilm.length, 5);
  assert.equal(new Set(ilm.map(r => r.company_id)).size, 1);
  assert.equal(filterRecords(rows, 'Framestore').length, 7);
  assert.equal(filterRecords(rows.slice(0, 31), '', 'VFX', 'India').length, 2);
  assert.equal(filterRecords(rows, 'Framestore', 'Previsualization', 'United Kingdom').length, 1);
});
test('batch 1 does not infer mocap from VFX', () => {
  const added = rows.slice(0, 31).filter(r => ['weta-fx', 'ilm', 'framestore'].includes(r.company_id));
  assert.equal(added.length, 13);
  assert.equal(filterRecords(added, '', 'Motion Capture').length, 0);
  assert.ok(added.every(r => r.evidence_state === 'confirmed' && r.coordinate_precision === 'city'));
});

test('coincident coordinates group every studio without mutating records', () => {
  const {coordinateGroups} = require('../data.js');
  const fixtures = [{id:'a',lat:1,lng:2},{id:'b',lat:1,lng:2},{id:'c',lat:1,lng:3}];
  const before = JSON.stringify(fixtures);
  assert.deepEqual(coordinateGroups(fixtures).map(g => g.map(r => r.id)), [['a','b'],['c']]);
  assert.equal(JSON.stringify(fixtures), before);
  assert.equal(coordinateGroups(fixtures.slice(1))[0][0].id, 'b');
});
test('optional metadata is backward compatible and validates sourced relationships', () => {
  const base = structuredClone(rows[0]);
  assert.equal(validateDatabase([base]).length, 1);
  const relationship = {id:'test-parent',name:'Test Parent',type:'group_member',evidence:'https://example.org/source',verified_on:'2026-01-01'};
  const extended = {...base, location_type:'capture_facility', coordinate_source:'https://example.org/city',relationships:[relationship]};
  assert.equal(validateDatabase([extended]).length, 1);
  for (const changes of [{location_type:'corporate-hq'},{coordinate_source:'javascript:alert(1)'},{relationships:{}},
      {relationships:[{...relationship,evidence:''}]},{relationships:[{...relationship,verified_on:'2026-02-30'}]},
      {relationships:[{...relationship,id:base.company_id}]},{relationships:[relationship,relationship]}]) {
    assert.throws(() => validateDatabase([{...extended,...changes}]));
  }
});
test('organisation relationship names are searchable without collapsing studios', () => {
  const hits = filterRecords(rows, 'Cinesite Group');
  assert.equal(hits.length, 15);
  assert.equal(hits.filter(r => r.company_id === 'imaginarium').length, 2);
  const imaginarium = filterRecords(rows, 'Imaginarium', 'Facial Capture');
  assert.equal(imaginarium.length, 2);
  assert.deepEqual(imaginarium.map(r => r.city).sort(), ['Iver Heath','London']);
});
test('new batch has six individually sourced capture facilities', () => {
  const added = rows.slice(31, 129);
  const capture = added.filter(r => r.capabilities.some(c => ['Motion Capture','Facial Capture','Performance Capture'].includes(c)));
  assert.equal(capture.length, 6);
  assert.ok(capture.every(r => r.coordinate_precision === 'city'));
  assert.equal(filterRecords(added, 'DNEG', 'Motion Capture').length, 0);
});
test('10000 location grouping retains all records and exact original coordinates', () => {
  const {coordinateGroups} = require('../data.js');
  const synthetic = Array.from({length:10000}, (_,i) => ({id:`synthetic-${i}`,lat:i%160-80,lng:i%350-175}));
  const before = JSON.stringify(synthetic);
  const groups = coordinateGroups(synthetic);
  assert.equal(groups.reduce((n,g) => n + g.length,0), 10000);
  assert.equal(groups.length,5600);
  assert.ok(groups.some(g => g.length > 1));
  assert.equal(JSON.stringify(synthetic), before);
});

test('viewport grouping retains coincident studios and leaves source coordinates intact', () => {
  const {coordinateGroups,visibleCoordinateGroups} = require('../data.js');
  const fixtures = [{id:'a',lat:0,lng:0},{id:'b',lat:0,lng:0},{id:'c',lat:45,lng:140}];
  const original = JSON.stringify(fixtures), groups = coordinateGroups(fixtures);
  assert.deepEqual(visibleCoordinateGroups(groups,{west:-10,east:10,south:-10,north:10}).map(g=>g.map(r=>r.id)), [['a','b']]);
  assert.equal(JSON.stringify(fixtures),original);
  assert.equal(visibleCoordinateGroups(groups,{west:-180,east:180,south:-90,north:90}).length,2);
});
test('viewport grouping handles the antimeridian and repeated world copies', () => {
  const {coordinateGroups,visibleCoordinateGroups} = require('../data.js');
  const groups=coordinateGroups([{id:'east',lat:0,lng:179},{id:'west',lat:0,lng:-179},{id:'centre',lat:0,lng:0},{id:'north',lat:80,lng:179}]);
  for (const [west,east] of [[170,190],[170,-170],[530,550],[-190,-170]]) {
    assert.deepEqual(visibleCoordinateGroups(groups,{west,east,south:-10,north:10}).map(g=>g[0].id),['east','west']);
  }
  assert.deepEqual(visibleCoordinateGroups(groups,{west:-200,east:200,south:-10,north:10}).map(g=>g[0].id),['east','west','centre']);
});

test('confirmed-only filtering uses the specific selected capability evidence', () => {
  const unknown = {...rows[0], id: 'fixture-unknown', categories: ['VFX'], capabilities: ['Motion Capture'],
    capability_evidence: {'Motion Capture': {state:'unknown', evidence:'', verified_on:''}}};
  const known = rows.find(r => r.id === 'larian-kuala-lumpur');
  assert.deepEqual(filterRecords([unknown, known], '', 'Motion Capture', '', true), [known]);
  assert.equal(filterRecords([unknown, known], '', 'Motion Capture', '', false).length, 2);
  assert.equal(filterRecords([known], '', 'Motion Capture', 'Canada', true).length, 0);
  assert.equal(filterRecords([known], '', 'Facial Capture', '', true).length, 0);
});
test('20000 locations retain complete identity and coordinates in viewport rendering', () => {
  const {coordinateGroups, visibleCoordinateGroups} = require('../data.js');
  const fixture = Array.from({length:20000}, (_, i) => ({id:`fixture-${i}`, lat:(i%200)*.8-80, lng:Math.floor(i/200)*3.5-175}));
  fixture[5001] = {...fixture[5001], lat:fixture[5000].lat, lng:fixture[5000].lng};
  const before=JSON.stringify(fixture), start=performance.now(), groups=coordinateGroups(fixture);
  const visible=visibleCoordinateGroups(groups, {west:-20,east:20,south:-20,north:20});
  assert.equal(groups.flat().length,20000);
  assert.equal(groups.find(g => g.length===2).length,2);
  assert.ok(visible.length < 2000 && visible.length > 0);
  assert.equal(JSON.stringify(fixture),before);
  assert.ok(performance.now()-start < 3000);
});

const Directory = require('../data.js');
test('operating organisation pages retain separate branches and subsidiaries', () => {
  const index=Directory.createDirectoryIndex(rows);
  assert.equal(index.organisations.get('dneg').rows.length,19);
  assert.equal(index.organisations.get('dneg').name,'DNEG');
  assert.ok(index.groups.get('cinesite-group').members.has('imaginarium'));
  assert.ok(!index.organisations.has('cinesite-group'));
  assert.equal(index.organisations.get('studiot3d').rows.length,2);
  assert.ok(Directory.relatedOrganisations(index,'imaginarium').some(o=>o.id==='cinesite'));
  assert.ok(!Directory.relatedOrganisations(index,'annapurna-studios').some(o=>o.id==='animatrik'));
});
test('multi-capability AND and OR are explicit and never inherit parent services', () => {
  const index=Directory.createDirectoryIndex(rows);
  const both=Directory.queryDirectory(index,{capabilities:['Motion Capture','Facial Capture'],confirmedOnly:true});
  assert.ok(both.length>0 && both.every(r=>r.capability_evidence['Motion Capture'].state==='confirmed' && r.capability_evidence['Facial Capture'].state==='confirmed'));
  const any=Directory.queryDirectory(index,{capabilities:['Motion Capture','Facial Capture'],capabilityMode:'any',confirmedOnly:true});
  assert.ok(any.length>=both.length);
  assert.ok(!both.some(r=>r.id==='larian-kuala-lumpur'));
  assert.equal(Directory.queryDirectory(index,{company:'dneg',capabilities:['Motion Capture']}).length,0);
});
test('country, city, sector, type and multiword search combine with AND', () => {
  const index=Directory.createDirectoryIndex(rows);
  const hits=Directory.queryDirectory(index,{query:'Larian Studios',country:'Malaysia',city:'kuala',sector:'Game Development',locationType:'production_studio',capabilities:['Motion Capture'],confirmedOnly:true});
  assert.deepEqual(hits.map(r=>r.id),['larian-kuala-lumpur']);
  assert.equal(Directory.queryDirectory(index,{...{query:'Larian'},country:'Canada',city:'Paris'}).length,0);
  assert.ok(Directory.queryDirectory(index,{query:'montreal'}).some(r=>r.city==='Montréal'));
});
test('GitHub Pages profile hashes round-trip IDs and reject hostile or broken routes', () => {
  for(const kind of ['location','organisation']) assert.deepEqual(Directory.parseProfileHash(Directory.profileHash(kind,'a-stable-identity')),{kind,id:'a-stable-identity'});
  for(const hash of ['#/location/../main','#/location/%2F%2Fevil.test','#/location/%E0%A4%A','#/organisation/<script>','#/location/a?redirect=https://evil.test','#/unknown/a','#'.repeat(400)]) assert.equal(Directory.parseProfileHash(hash).kind,'invalid');
  assert.equal(Directory.parseProfileHash('').kind,'directory');
  assert.throws(()=>Directory.profileHash('location','https://evil.test'));
});
test('CSV guards formulas, preserves numeric coordinates and quotes multiline text', () => {
  for(const text of ['=IMPORTXML("evil")',' +cmd','\t@SUM(1)','\r\n-unsafe','\u200B=1']) assert.ok(Directory.csvCell(text).startsWith('"\''));
  assert.equal(Directory.csvCell(-73.5),'"-73.5"');
  assert.equal(Directory.csvCell('a,"b"\nc'),'"a,""b""\nc"');
  assert.ok(Directory.exportCSV([rows[0]]).includes(rows[0].id));
  assert.ok(!Directory.exportCSV([rows[0]]).split('\r\n')[0].includes('phone'));
});
test('spatial buckets match exact viewport results including antimeridian and poles', () => {
  const fixture=Array.from({length:50000},(_,i)=>({id:`fixture-${i}`,lat:(i%250)*.64-80,lng:Math.floor(i/250)*1.75-175}));
  fixture.push({id:'north',lat:90,lng:180},{id:'south',lat:-90,lng:-180});
  const groups=Directory.coordinateGroups(fixture), index=Directory.createSpatialIndex(groups);
  for(const bounds of [{west:-20,east:20,south:-20,north:20},{west:170,east:195,south:-90,north:90},{west:-190,east:-170,south:-90,north:90},{west:-360,east:360,south:-90,north:90}]) {
    const actual=index.query(bounds).flat().map(r=>r.id).sort(), expected=Directory.visibleCoordinateGroups(groups,bounds).flat().map(r=>r.id).sort();
    assert.deepEqual(actual,expected);
  }
});
test('50000-record map groups retain every identity and never move coordinates', () => {
  const fixture=Array.from({length:50000},(_,i)=>({id:`fixture-${i}`,lat:(i%250)*.64-80,lng:Math.floor(i/250)*1.75-175}));
  fixture[1]={...fixture[1],lat:fixture[0].lat,lng:fixture[0].lng};
  const before=JSON.stringify(fixture), groups=Directory.coordinateGroups(fixture), clusters=Directory.clusterCoordinateGroups(groups,2);
  assert.ok(clusters.length<1000);
  assert.equal(new Set(clusters.flatMap(c=>c.rows.map(r=>r.id))).size,50000);
  assert.equal(JSON.stringify(fixture),before);
});
test('parent operators with their own branches can navigate separately owned brands',()=>{
  const D=require('../data.js'),index=D.createDirectoryIndex(canonical);
  assert.equal(index.organisations.get('virtuos').rows.length,10);
  assert.ok(D.relatedOrganisations(index,'virtuos').some(o=>o.id==='glass-egg'));
  assert.ok(D.relatedOrganisations(index,'glass-egg').some(o=>o.id==='virtuos'));
  assert.equal(index.organisations.get('glass-egg').rows.length,2);
  assert.ok(!D.queryDirectory(index,{company:'virtuos',capabilities:['Motion Capture']}).length);
});
test('operating names are validated consistently and skip-to-search is a directory route',()=>{
  const D=require('../data.js'),r={...rows[18],company_name:'Test'};
  assert.throws(()=>D.validateDatabase([r,{...r,id:'other',company_name:'Other'}]));
  assert.equal(D.parseProfileHash('#search').kind,'directory');
  assert.throws(()=>D.createSpatialIndex([],0));
});
test('public links exclude IP literals, credentials, controls and token queries',()=>{
 const {httpsURL}=require('../data.js');
 for(const url of ['https://user:pass@example.org/','https://localhost/','https://127.1/','https://10.0.0.1/','https://[::1]/','https://service.internal/','https://example.org/?token=secret','https://example.org/\x00']) assert.equal(httpsURL(url),false,url);
 assert.equal(httpsURL('https://example.org/public-source'),true);
});
