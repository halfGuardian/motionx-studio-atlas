/* Shared pure database checks and HTTP loader; also exercised by Node tests. */
(function (root) {
  'use strict';
  const states = ['confirmed', 'likely', 'unknown'];
  const precisions = ['exact', 'approximate', 'city', 'region', 'unverified'];
  const sectors = ['VFX', 'Animation', 'Game Development', 'Motion Capture',
    'Performance Capture', 'Previsualization', 'Virtual Production', 'Cinematics', 'Research'];
  function httpsURL(value) {
    try {
      const url = new URL(value);
      return typeof value === 'string' && url.protocol === 'https:' && !!url.hostname &&
        !url.username && !url.password && !/\s/.test(value);
    } catch { return false; }
  }
  function validDate(value) {
    return typeof value === 'string' && /^\d{4}-\d{2}-\d{2}$/.test(value) &&
      !Number.isNaN(Date.parse(value)) && new Date(value).toISOString().slice(0, 10) === value;
  }
  function validateDatabase(rows) {
    if (!Array.isArray(rows)) throw new Error('Database must be an array of locations.');
    const ids = new Set();
    for (const row of rows) {
      if (!row || typeof row !== 'object' || Array.isArray(row)) throw new Error('Invalid location record.');
      const fail = message => { throw new Error(`${row.id || 'Location'}: ${message}`); };
      for (const field of ['id', 'company_id', 'name', 'city', 'country']) {
        if (typeof row[field] !== 'string' || !row[field].trim()) fail(`missing ${field}`);
      }
      for (const field of ['id', 'company_id']) {
        if (!/^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(row[field])) fail(`invalid ${field}`);
      }
      if (ids.has(row.id)) fail('duplicate location ID');
      ids.add(row.id);
      if (!Number.isFinite(row.lat) || Math.abs(row.lat) > 90 ||
          !Number.isFinite(row.lng) || Math.abs(row.lng) > 180) fail('invalid coordinates');
      for (const field of ['categories', 'capabilities']) {
        if (!Array.isArray(row[field]) || row[field].some(v => typeof v !== 'string' || !v.trim()) ||
            new Set(row[field]).size !== row[field].length) fail(`invalid ${field}`);
      }
      if (!row.categories.length) fail('missing sector');
      if (!states.includes(row.evidence_state) || !precisions.includes(row.coordinate_precision)) fail('invalid evidence or precision');
      if (!httpsURL(row.website) || (row.evidence && !httpsURL(row.evidence))) fail('invalid public URL');
      for (const field of ['address', 'status', 'email', 'phone', 'evidence', 'verified_on']) {
        if (row[field] !== undefined && typeof row[field] !== 'string') fail(`invalid ${field}`);
      }
      if (row.verified_on && !validDate(row.verified_on)) fail('invalid review date');
      if (row.evidence_state !== 'unknown' && (!row.evidence || !row.verified_on)) fail('missing evidence/review date');
      if (row.coordinate_precision === 'exact' && (!row.address || !row.evidence || !row.verified_on)) fail('missing exact location evidence');
      const evidence = row.capability_evidence;
      if (!evidence || typeof evidence !== 'object' || Array.isArray(evidence) ||
          Object.keys(evidence).length !== row.capabilities.length ||
          row.capabilities.some(c => !Object.hasOwn(evidence, c))) fail('missing capability evidence');
      for (const item of Object.values(evidence)) {
        if (!item || (item.evidence !== undefined && typeof item.evidence !== 'string') ||
            (item.verified_on !== undefined && typeof item.verified_on !== 'string') || !states.includes(item.state) || (item.evidence && !httpsURL(item.evidence)) ||
            (item.verified_on && !validDate(item.verified_on)) ||
            (item.state !== 'unknown' && (!item.evidence || !item.verified_on))) fail('invalid capability evidence');
      }
    }
    return rows;
  }
  async function loadDatabase(fetcher = root.fetch.bind(root), path = './studios.json') {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 20000);
    try {
      const response = await fetcher(path, {cache: 'no-store', signal: controller.signal});
      if (!response.ok) throw new Error(`Database request failed (HTTP ${response.status}).`);
      return validateDatabase(await response.json());
    } finally { clearTimeout(timeout); }
  }
  function filterRecords(rows, query = '', category = '', country = '') {
    const q = query.trim().toLocaleLowerCase();
    return rows.filter(row => (!category || row.categories.includes(category) || row.capabilities.includes(category)) &&
      (!country || row.country === country) && (!q ||
        [row.name, row.city, row.country, ...row.categories, ...row.capabilities].join(' ').toLocaleLowerCase().includes(q)));
  }
  function coordinateGroups(rows) {
    const groups = new Map();
    for (const row of rows) {
      const key = JSON.stringify([row.lat, row.lng]);
      if (!groups.has(key)) groups.set(key, []);
      groups.get(key).push(row);
    }
    return [...groups.values()];
  }
  const api = {validateDatabase, loadDatabase, filterRecords, coordinateGroups, sectors};
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  else root.MotionXData = api;
})(globalThis);
