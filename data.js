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
      const host=url.hostname.replace(/\.$/,'').toLowerCase();
      if(!host.includes('.') || host==='localhost' || /\.(localhost|local|internal)$/.test(host) || /^[\d.]+$/.test(host) || host.includes(':')) return false;
      if(/[\u0000-\u001f\u007f]/.test(value) || /[?&](access_token|api[_-]?key|auth|password|token)=/i.test(value)) return false;
      return typeof value === 'string' && !value.includes('\\') && url.port!=='0' && url.protocol === 'https:' && !!url.hostname &&
        !url.username && !url.password && !/\s/.test(value);
    } catch { return false; }
  }
  function validDate(value) {
    return typeof value === 'string' && /^\d{4}-\d{2}-\d{2}$/.test(value) &&
      !Number.isNaN(Date.parse(value)) && new Date(value).toISOString().slice(0, 10) === value;
  }
  function validateDatabase(rows) {
    if (!Array.isArray(rows)) throw new Error('Database must be an array of locations.');
    const ids = new Set(), companyNames = new Map();
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
      if (row.company_name !== undefined) {
        if (typeof row.company_name!=='string' || !row.company_name.trim() || companyNames.has(row.company_id) && companyNames.get(row.company_id)!==row.company_name) fail('invalid/conflicting company name');
        companyNames.set(row.company_id,row.company_name);
      }
      if (row.location_type !== undefined && !['production_studio', 'capture_facility', 'creative_hub', 'mixed_campus', 'production_office', 'uncertain'].includes(row.location_type)) fail('invalid location type');
      if (row.coordinate_source !== undefined && !httpsURL(row.coordinate_source)) fail('invalid coordinate source');
      if (row.relationships !== undefined) {
        if (!Array.isArray(row.relationships)) fail('relationships must be an array');
        const seenRelations = new Set();
        for (const relation of row.relationships) {
          if (!relation || typeof relation.id !== 'string' || !/^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(relation.id) ||
              relation.id === row.company_id || seenRelations.has(relation.id) ||
              !['subsidiary_of', 'group_member', 'partner_of'].includes(relation.type) ||
              typeof relation.name !== 'string' || !relation.name.trim() ||
              !httpsURL(relation.evidence) || !validDate(relation.verified_on)) fail('invalid organisation relationship');
          seenRelations.add(relation.id);
        }
      }
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
  function filterRecords(rows, query = '', category = '', country = '', confirmedOnly = false) {
    const q = query.trim().toLocaleLowerCase();
    return rows.filter(row => (!confirmedOnly || (category ? row.capability_evidence[category]?.state === 'confirmed' : Object.values(row.capability_evidence).some(e => e.state === 'confirmed'))) && (!category || row.categories.includes(category) || row.capabilities.includes(category)) &&
      (!country || row.country === country) && (!q ||
        [row.name, row.city, row.country, ...(row.relationships || []).map(r => r.name), ...row.categories, ...row.capabilities].join(' ').toLocaleLowerCase().includes(q)));
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
  function visibleCoordinateGroups(groups, bounds) {
    if (bounds.east - bounds.west >= 360) return groups.filter(g => g[0].lat >= bounds.south && g[0].lat <= bounds.north);
    const wrap = lng => ((lng + 180) % 360 + 360) % 360 - 180;
    const west = wrap(bounds.west), east = wrap(bounds.east);
    return groups.filter(group => {
      const {lat, lng} = group[0], longitude = wrap(lng);
      return lat >= bounds.south && lat <= bounds.north &&
        (west <= east ? longitude >= west && longitude <= east : longitude >= west || longitude <= east);
    });
  }
  const fold = value => String(value || '').normalize('NFKD').replace(/[\u0300-\u036f]/g, '').toLocaleLowerCase();
  const idPattern = /^[a-z0-9]+(?:-[a-z0-9]+)*$/;
  function organisationName(id, rows) {
    const supplied = rows.find(r => r.company_name)?.company_name;
    if (supplied) return supplied;
    const names = [...new Set(rows.map(r => r.name.split(' — ')[0]))].sort((a,b) => a.length-b.length);
    if (names.every(n => n === names[0] || n.startsWith(names[0] + ' '))) return names[0];
    return id.split('-').map(word => word[0].toUpperCase()+word.slice(1)).join(' ');
  }
  function createDirectoryIndex(rows) {
    const byId = new Map(), organisations = new Map(), groups = new Map();
    for (const row of rows) {
      byId.set(row.id, row);
      if (!organisations.has(row.company_id)) organisations.set(row.company_id, {id:row.company_id, rows:[]});
      organisations.get(row.company_id).rows.push(row);
      for (const relation of row.relationships || []) {
        if (!['subsidiary_of','group_member'].includes(relation.type)) continue;
        if (!groups.has(relation.id)) groups.set(relation.id, {id:relation.id, name:relation.name, members:new Set(), evidence:[]});
        const group = groups.get(relation.id); group.members.add(row.company_id);
        group.evidence.push({location_id:row.id, company_id:row.company_id, ...relation});
      }
    }
    for (const org of organisations.values()) org.name=organisationName(org.id, org.rows);
    const entries = rows.map(row => ({row, categories:new Set(row.categories), capabilities:new Set(row.capabilities),
      text:fold([row.name,row.company_id,organisations.get(row.company_id).name,row.city,row.country,
        ...(row.relationships || []).map(r=>r.name),...row.categories,...row.capabilities].join(' ')), city:fold(row.city)}));
    return {rows, entries, byId, organisations, groups};
  }
  function queryDirectory(index, filters = {}) {
    const words=fold(filters.query).trim().split(/\s+/).filter(Boolean), city=fold(filters.city).trim();
    const caps=[...new Set(filters.capabilities || [])], mode=filters.capabilityMode==='any'?'some':'every';
    return index.entries.filter(entry => {
      const r=entry.row;
      if(filters.evidenceClass && r.evidence_class!==filters.evidenceClass)return false;
      if (filters.country && r.country!==filters.country || city && !entry.city.includes(city) ||
          filters.locationType && (r.location_type || 'uncertain')!==filters.locationType ||
          filters.company && r.company_id!==filters.company ||
          filters.sector && !entry.categories.has(filters.sector) && !entry.capabilities.has(filters.sector)) return false;
      const match = cap => entry.capabilities.has(cap) && (!filters.confirmedOnly || r.capability_evidence[cap]?.state==='confirmed');
      if (caps.length && !caps[mode](match)) return false;
      if (filters.confirmedOnly && !caps.length && !(filters.sector ?
          r.capability_evidence[filters.sector]?.state==='confirmed' : Object.values(r.capability_evidence).some(e=>e.state==='confirmed'))) return false;
      return words.every(word=>entry.text.includes(word));
    }).map(entry=>entry.row);
  }
  function relatedOrganisations(index, id) {
    const related = new Set();
    for (const group of index.groups.values()) if (group.id===id || group.members.has(id)) {
      for (const member of group.members) if (member!==id) related.add(member);
      if (group.id!==id && index.organisations.has(group.id)) related.add(group.id);
    }
    return [...related].map(key=>index.organisations.get(key));
  }
  function profileHash(kind, id) {
    if (!['location','organisation'].includes(kind) || !idPattern.test(id)) throw new Error('Invalid profile identity');
    return `#/${kind}/${id}`;
  }
  function parseProfileHash(hash) {
    if (!hash || hash==='#' || hash==='#/' || hash==='#search') return {kind:'directory',id:''};
    if (typeof hash!=='string' || hash.length>300) return {kind:'invalid',id:''};
    try {
      const decoded=decodeURIComponent(hash), match=/^#\/(location|organisation)\/([a-z0-9]+(?:-[a-z0-9]+)*)$/.exec(decoded);
      return match?{kind:match[1],id:match[2]}:{kind:'invalid',id:''};
    } catch { return {kind:'invalid',id:''}; }
  }
  const csvColumns=['id','company_id','company_name','name','city','country','lat','lng','address','website','categories','capabilities',
    'capability_evidence','evidence_state','coordinate_precision','evidence','verified_on','location_type','coordinate_source','relationships',
    'evidence_class','source_observed_on','website_kind','identity_status','source_provenance','license','attribution'];
  function csvCell(value) {
    let text=Array.isArray(value)?(value.some(v=>typeof v==='object')?JSON.stringify(value):value.join('|')):
      value && typeof value==='object'?JSON.stringify(value):String(value??'');
    if (typeof value!=='number' && /^[\s\u200B\u200C\u200D]*[=+@-]/u.test(text)) text="'"+text;
    return '"'+text.replace(/"/g,'""')+'"';
  }
  function exportCSV(rows) { return [csvColumns.join(','),...rows.map(r=>csvColumns.map(c=>csvCell(r[c])).join(','))].join('\r\n'); }
  function createSpatialIndex(groups, cellSize=5) {
    if (!(cellSize>0 && cellSize<=180 && Number.isFinite(cellSize))) throw new Error('Invalid spatial cell size');
    const maxX=Math.ceil(360/cellSize)-1,maxY=Math.ceil(180/cellSize)-1;
    const buckets=new Map(), wrap=lng=>((lng+180)%360+360)%360-180;
    for (const group of groups) {
      const key=`${Math.floor((wrap(group[0].lng)+180)/cellSize)},${Math.min(maxY,Math.floor((group[0].lat+90)/cellSize))}`;
      if (!buckets.has(key)) buckets.set(key,[]);buckets.get(key).push(group);
    }
    return {query(bounds) {
      const south=Math.max(-90,bounds.south), north=Math.min(90,bounds.north);
      const y0=Math.max(0,Math.floor((south+90)/cellSize)), y1=Math.min(maxY,Math.floor((north+90)/cellSize));
      const west=wrap(bounds.west),east=wrap(bounds.east);
      const ranges=bounds.east-bounds.west>=360?[[-180,180]]:west<=east?[[west,east]]:[[west,180],[-180,east]];
      const found=new Set();
      for (const [w,e] of ranges) for(let x=Math.floor((w+180)/cellSize);x<=Math.min(maxX,Math.floor((e+180)/cellSize));x++)
        for(let y=y0;y<=y1;y++) for(const group of buckets.get(`${x},${y}`)||[]) found.add(group);
      return visibleCoordinateGroups([...found],bounds);
    }};
  }
  function clusterCoordinateGroups(groups, zoom, cellSize=72) {
    if (groups.length<=2000) return groups.map(group=>({groups:[group],rows:group}));
    const cells=new Map(), scale=256*2**zoom;
    for (const group of groups) {
      const r=group[0], lat=Math.max(-85.0511,Math.min(85.0511,r.lat))*Math.PI/180;
      const x=((((r.lng+180)%360+360)%360)/360)*scale;
      const y=(1-Math.log(Math.tan(lat)+1/Math.cos(lat))/Math.PI)/2*scale;
      const key=`${Math.floor(x/cellSize)},${Math.floor(y/cellSize)}`;
      if(!cells.has(key))cells.set(key,{groups:[],rows:[]});
      cells.get(key).groups.push(group);cells.get(key).rows.push(...group);
    }
    return [...cells.values()];
  }
  const api = {validateDatabase, loadDatabase, validDate, filterRecords, coordinateGroups, visibleCoordinateGroups, sectors, httpsURL, fold, createDirectoryIndex, queryDirectory, relatedOrganisations, profileHash, parseProfileHash, csvCell, exportCSV, createSpatialIndex, clusterCoordinateGroups};
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  else root.MotionXData = api;
})(globalThis);
