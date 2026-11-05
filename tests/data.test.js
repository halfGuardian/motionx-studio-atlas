'use strict';
const {test} = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const {loadDatabase, validateDatabase, filterRecords} = require('../data.js');
const rows = JSON.parse(fs.readFileSync(require('node:path').join(__dirname, '../studios.json')));
test('canonical database loads and retains all identities', () => {
  assert.equal(validateDatabase(rows).length, 31);
  assert.equal(new Set(rows.map(r => r.company_id)).size, 19);
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
  assert.equal(filterRecords(rows, '', '', 'Canada').length, 7);
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
  assert.equal(filterRecords(rows, '', 'VFX', 'India').length, 2);
  assert.equal(filterRecords(rows, 'Framestore', 'Previsualization', 'United Kingdom').length, 1);
});
test('batch 1 does not infer mocap from VFX', () => {
  const added = rows.filter(r => ['weta-fx', 'ilm', 'framestore'].includes(r.company_id));
  assert.equal(added.length, 13);
  assert.equal(filterRecords(added, '', 'Motion Capture').length, 0);
  assert.ok(added.every(r => r.evidence_state === 'confirmed' && r.coordinate_precision === 'city'));
});
