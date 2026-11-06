'use strict';
const {test} = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const {loadDatabase, validateDatabase, filterRecords} = require('../data.js');
const rows = JSON.parse(fs.readFileSync(require('node:path').join(__dirname, '../studios.json')));
test('canonical database loads and retains all identities', () => {
  assert.equal(validateDatabase(rows).length, 129);
  assert.equal(new Set(rows.map(r => r.company_id)).size, 66);
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
  const added = rows.slice(31);
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
