const test = require('node:test'), assert = require('node:assert/strict'), fs = require('node:fs');
const review = require('../annecy-review.js'), D = require('../data.js');
test('Annecy dashboard combines query, outcome and group without changing data', () => {
  assert.ok(review.matches('Marmota Studio Chile', 'newly_added', 'priority', 'MARMOTA', 'newly_added', 'priority'));
  assert.equal(review.matches('Marmota Studio Chile', 'newly_added', 'priority', 'Marmota', 'unresolved', ''), false);
  assert.equal(review.matches('Example', 'duplicate', 'other', '', '', 'priority'), false);
});
test('real Annecy references have shareable existing routes, no pins and no verified capabilities', () => {
  const proposed = JSON.parse(fs.readFileSync('data/annecy/reports/proposals.json')).company_references;
  const index = JSON.parse(fs.readFileSync('data/public/index.json')), metadata = JSON.parse(fs.readFileSync('data/public/boutique.json'));
  const m = proposed.find(r => r.name === 'MARMOTA STUDIO'); assert.ok(m);
  assert.ok(index.some(r => r[0] === m.id)); assert.ok(metadata.profiles[m.id].research_terms.includes('Rigging'));
  for (const row of proposed) {
    assert.equal(row.lat, null); assert.deepEqual(row.capabilities, []); assert.equal(row.evidence_class, 'C');
    assert.deepEqual(D.parseProfileHash(D.profileHash('location', row.id)), {kind:'location', id:row.id});
  }
});
