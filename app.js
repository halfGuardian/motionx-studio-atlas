/* MotionX public atlas: static GitHub Pages, no embedded studio records. */
'use strict';
const $ = id => document.getElementById(id);
const esc = value => String(value ?? '').replace(/[&<>"']/g, c =>
  ({'&':'&amp;', '<':'&lt;', '>':'&gt;', '"':'&quot;', "'":'&#39;'}[c]));
let studios = [], selected = null, page = 0, loaded = false;
const pageSize = 50;
const countLabel = (count, label) => `${count} ${label}${count === 1 ? '' : 's'}`;
const map = globalThis.L ? L.map('map', {worldCopyJump: true, preferCanvas: true}).setView([28, -25], 2) : null;
const layer = map ? L.layerGroup().addTo(map) : null;
if (map) {
  const osm = L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noopener noreferrer">OpenStreetMap contributors</a>',
    maxZoom: 19
  }).addTo(map);
  const tileStatus = document.createElement('div');
  tileStatus.style.cssText = 'position:absolute;z-index:800;bottom:64px;left:12px;background:#111824eb;padding:9px;border-radius:8px;font:12px system-ui;max-width:280px;display:none;pointer-events:none';
  $('map').appendChild(tileStatus);
  osm.on('tileerror', () => {
    tileStatus.style.display = 'block';
    tileStatus.textContent = 'Map tiles could not load. The studio list is still available.';
  });
  osm.on('tileload', () => { tileStatus.style.display = 'none'; });
} else {
  $('map').textContent = 'Map library could not load. Use the studio list or reload to retry.';
}
function filtered() {
  return MotionXData.filterRecords(studios, $('search').value, $('category').value, $('country').value);
}
function renderList(rows = filtered()) {
  page = Math.min(page, Math.max(0, Math.ceil(rows.length / pageSize) - 1));
  $('count').textContent = countLabel(rows.length, 'location');
  $('companies').textContent = `${countLabel(new Set(rows.map(s => s.company_id)).size, 'organization')} · ${studios.length} total locations / ${countLabel(new Set(studios.map(s => s.company_id)).size, 'organization')}`;
  $('list').innerHTML = rows.slice(page * pageSize, (page + 1) * pageSize).map(s => `
    <article class="entry ${selected === s.id ? 'selected' : ''}">
      <h3><button class="profile-link" data-id="${esc(s.id)}">${esc(s.name)}</button></h3>
      <div class="muted">${esc(s.city)}, ${esc(s.country)}</div>
      ${s.categories.map(t => `<span class="tag">${esc(t)}</span>`).join('')}
      <div class="muted">Evidence: ${esc(s.evidence_state)} · Coordinates: ${esc(s.coordinate_precision)}</div>
    </article>`).join('') || '<p class="muted">No matching studios.</p>';
  $('pageInfo').textContent = rows.length ? `${page * pageSize + 1}–${Math.min((page + 1) * pageSize, rows.length)} of ${rows.length}` : '0 results';
  $('previousPage').disabled = page === 0;
  $('nextPage').disabled = (page + 1) * pageSize >= rows.length;
}
function render() {
  if (!loaded) return;
  const rows = filtered();
  renderList(rows);
  if (!layer) return;
  layer.clearLayers();
  for (const s of rows) {
    L.circleMarker([s.lat, s.lng], {radius: 8, color: '#ffd1d2', weight: 2,
      fillColor: '#e74f60', fillOpacity: .88}).addTo(layer).on('click', () => show(s));
  }
}
function show(s) {
  selected = s.id;
  $('detail').style.display = 'block';
  const precision = s.coordinate_precision === 'exact' ? 'Exact (see cited research evidence)' :
    `${s.coordinate_precision} — approximate reference pin; not a verified street address`;
  $('detailContent').innerHTML = `<div class="sub">STUDIO PROFILE</div><h2>${esc(s.name)}</h2>
    <p class="muted">${esc(s.city)}, ${esc(s.country)}</p>
    <div class="stats"><span class="stat">Evidence confidence: ${esc(s.evidence_state)}</span></div>
    <p class="muted">${esc(s.status)}</p>
    <p><b>Capabilities and confidence</b></p><ul>${s.capabilities.map(c => {
      const e = s.capability_evidence[c];
      return `<li>${esc(c)} — ${esc(e.state)}${e.evidence ? ` · <a href="${esc(e.evidence)}" target="_blank" rel="noopener noreferrer">Source</a>` : ''}${e.verified_on ? ` · reviewed ${esc(e.verified_on)}` : ' · not yet reviewed'}</li>`;
    }).join('')}</ul>
    <p><b>Coordinate precision</b><br>${esc(precision)}</p>
    <p><b>Location reference</b><br>${esc(s.address || 'Street address not verified')}</p>
    <p><b>Website</b><br><a href="${esc(s.website)}" target="_blank" rel="noopener noreferrer">${esc(s.website)}</a></p>
    ${s.email ? `<p><b>Public email</b><br><a href="mailto:${esc(s.email)}">${esc(s.email)}</a></p>` : ''}
    ${s.phone ? `<p><b>Public phone</b><br>${esc(s.phone)}</p>` : ''}
    <p><b>Research source</b><br>${s.evidence ? `<a href="${esc(s.evidence)}" target="_blank" rel="noopener noreferrer">Official/public source</a>` : 'No source recorded'}<br>
    <span class="muted">${s.legacy_research ? 'Legacy recorded review date (not independently verified)' : 'Recorded review date'}: ${esc(s.verified_on || 'Not reviewed')}. Source presence does not prove capability, registration or current operation.</span></p>`;
  renderList();
}
function updateTabs() {
  const list = document.body.classList.contains('show-list');
  $('mapTab').classList.toggle('active', !list);
  $('listTab').classList.toggle('active', list);
}
$('mapTab').onclick = () => {
  document.body.classList.remove('show-list'); updateTabs(); setTimeout(() => map?.invalidateSize(), 60);
};
$('listTab').onclick = () => { document.body.classList.add('show-list'); updateTabs(); };
$('list').onclick = event => {
  const button = event.target.closest('[data-id]');
  if (!button) return;
  const s = studios.find(row => row.id === button.dataset.id);
  if (!s) return;
  document.body.classList.remove('show-list'); updateTabs();
  setTimeout(() => { map?.invalidateSize(); map?.flyTo([s.lat, s.lng], Math.max(map.getZoom(), 7)); }, 60);
  show(s);
};
$('close').onclick = () => { $('detail').style.display = 'none'; selected = null; renderList(); };
let searchTimer;
for (const id of ['search', 'category', 'country']) {
  $(id).addEventListener('input', () => {
    clearTimeout(searchTimer);
    searchTimer = setTimeout(() => {
      page = 0; selected = null; $('detail').style.display = 'none'; render();
    }, id === 'search' ? 120 : 0);
  });
}
$('previousPage').onclick = () => { page--; renderList(); };
$('nextPage').onclick = () => { page++; renderList(); };
$('fitResults').onclick = () => {
  const rows = filtered();
  if (rows.length && map) map.fitBounds(L.latLngBounds(rows.map(s => [s.lat, s.lng])).pad(.25), {maxZoom: 10});
};
$('exportCsv').onclick = () => {
  const columns = ['id', 'company_id', 'name', 'city', 'country', 'lat', 'lng', 'address', 'website', 'email', 'phone',
    'categories', 'capabilities', 'capability_evidence', 'evidence_state', 'coordinate_precision', 'evidence', 'verified_on'];
  const quote = value => {
    let text = Array.isArray(value) ? value.join('|') : typeof value === 'object' && value ? JSON.stringify(value) : String(value ?? '');
    if (typeof value !== 'number' && /^[\s]*[=+@-]/.test(text)) text = "'" + text; // Spreadsheet formula protection.
    return '"' + text.replace(/"/g, '""') + '"';
  };
  const csv = [columns.join(','), ...filtered().map(s => columns.map(k => quote(s[k])).join(','))].join('\r\n');
  const a = document.createElement('a');
  a.href = URL.createObjectURL(new Blob(['\uFEFF' + csv], {type: 'text/csv;charset=utf-8'}));
  a.download = 'motionx_studios_filtered_v0.6.csv';
  document.body.appendChild(a); a.click();
  setTimeout(() => { URL.revokeObjectURL(a.href); a.remove(); }, 1000);
};
window.addEventListener('resize', () => setTimeout(() => map?.invalidateSize(), 80));
function setControls(enabled) {
  for (const id of ['search', 'category', 'country', 'exportCsv', 'fitResults', 'previousPage', 'nextPage']) $(id).disabled = !enabled;
  if (!map) $('fitResults').disabled = true;
}
async function initialize() {
  loaded = false; setControls(false);
  $('dataStatus').hidden = false; $('dataStatus').firstChild.textContent = 'Loading studio database… ';
  $('retryLoad').hidden = true;
  $('count').textContent = 'Loading locations…'; $('companies').textContent = '';
  try {
    studios = await MotionXData.loadDatabase();
    for (const [id, values, label] of [
      ['country', [...new Set(studios.map(s => s.country))].sort(), 'All countries'],
      ['category', [...new Set([...MotionXData.sectors, ...studios.flatMap(s => [...s.categories, ...s.capabilities])])].sort(), 'All specializations']
    ]) {
      $(id).replaceChildren(new Option(label, ''), ...values.map(value => new Option(value, value)));
    }
    loaded = true; page = 0; setControls(true); render();
    $('dataStatus').hidden = true;
  } catch (error) {
    studios = []; layer?.clearLayers();
    $('count').textContent = 'Studio data unavailable'; $('companies').textContent = '';
    $('list').textContent = 'No records loaded. Retry when the database is available.';
    $('dataStatus').firstChild.textContent = `Unable to load studios.json. ${error.name === 'AbortError' ? 'Request timed out.' : error.message} Serve this site over HTTP and check your connection. `;
    $('retryLoad').hidden = false;
    console.error('MotionX database load failed:', error);
  }
}
$('retryLoad').onclick = initialize;
initialize();
