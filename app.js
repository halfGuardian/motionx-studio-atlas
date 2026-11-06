/* MotionX v1.0. Static GitHub Pages; every public record comes from studios.json. */
'use strict';
const $=id=>document.getElementById(id), D=MotionXData;
const esc=value=>String(value??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const external=(url,label)=>D.httpsURL(url)?`<a href="${esc(url)}" target="_blank" rel="noopener noreferrer">${esc(label)}</a>`:'Source not recorded';
const profileLink=(kind,id,label,extra='')=>`<a href="${D.profileHash(kind,id)}" ${extra}>${esc(label)}</a>`;
const countLabel=(n,label)=>`${n} ${label}${n===1?'':'s'}`;
const pageSize=50;
let studios=[],directory=null,matches=[],selected=null,page=0,loaded=false,viewMode='locations',opener=null;
let markerGroups=[],spatial=null,searchTimer;
const timings=globalThis.MotionXPerformance={};
const map=globalThis.L?L.map('map',{worldCopyJump:true,preferCanvas:true}).setView([28,-25],2):null;
const layer=map?L.layerGroup().addTo(map):null;
if(map){
  const osm=L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png',{
    attribution:'&copy; <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noopener noreferrer">OpenStreetMap contributors</a>',maxZoom:19}).addTo(map);
  const status=document.createElement('div');status.className='tile-status';status.hidden=true;
  status.textContent='Map tiles could not load. Every studio remains accessible in the directory.';$('map').appendChild(status);
  osm.on('tileerror',()=>{status.hidden=false;});osm.on('tileload',()=>{status.hidden=true;});
}else $('map').textContent='Map library could not load. Use the studio directory, or reload to retry.';
function controls(){return {query:$('search').value,country:$('country').value,city:$('city').value,sector:$('category').value,
  locationType:$('locationType').value,confirmedOnly:$('confirmedOnly').checked,capabilityMode:$('capabilityMode').value,
  capabilities:[...document.querySelectorAll('#capabilityOptions input:checked')].map(input=>input.value)};}
function filtered(){return matches;}
function locationCard(s){
  const org=directory.organisations.get(s.company_id);
  return `<article class="entry ${selected===s.id?'selected':''}">
    ${profileLink('organisation',org.id,org.name,'class="org-link"')}
    <h3>${profileLink('location',s.id,s.name,`class="profile-link" data-id="${esc(s.id)}"`)}</h3>
    <div class="muted">${esc(s.city)}, ${esc(s.country)}</div>
    ${s.categories.map(t=>`<span class="tag">${esc(t)}</span>`).join('')}
    <div class="confidence ${esc(s.evidence_state)}">Evidence: ${esc(s.evidence_state)} · ${esc(s.coordinate_precision)} coordinates</div></article>`;
}
function organisationCard(org,rows){return `<article class="entry"><div class="eyebrow">OPERATING ORGANISATION</div>
  <h3>${profileLink('organisation',org.id,org.name,'class="profile-link"')}</h3>
  <p class="muted">${countLabel(rows.length,'matching location')} · ${org.rows.length} total</p>
  <div class="muted">${esc([...new Set(rows.map(r=>r.country))].sort().join(' · '))}</div></article>`;}
function renderList(){
  const grouped=new Map();for(const row of matches){if(!grouped.has(row.company_id))grouped.set(row.company_id,[]);grouped.get(row.company_id).push(row);}
  const items=viewMode==='locations'?matches:[...grouped.keys()];
  page=Math.min(page,Math.max(0,Math.ceil(items.length/pageSize)-1));
  $('count').textContent=countLabel(matches.length,'location');
  $('companies').textContent=`${countLabel(grouped.size,'organization')} · ${studios.length} total locations / ${countLabel(directory.organisations.size,'organization')}`;
  $('list').innerHTML=items.slice(page*pageSize,(page+1)*pageSize).map(item=>viewMode==='locations'?locationCard(item):organisationCard(directory.organisations.get(item),grouped.get(item))).join('')||
    '<div class="empty-state"><h3>No studios match yet.</h3><p class="muted">Try fewer capabilities, a broader city search, or reset the filters.</p><button data-reset>Reset all filters</button></div>';
  $('pageInfo').textContent=items.length?`${page*pageSize+1}–${Math.min((page+1)*pageSize,items.length)} of ${items.length}`:'0 results';
  $('previousPage').disabled=page===0;$('nextPage').disabled=(page+1)*pageSize>=items.length;
}
function render(){
  if(!loaded)return;
  const start=performance.now();matches=D.queryDirectory(directory,controls());timings.search_ms=performance.now()-start;
  const selectedCaps=controls().capabilities.length;$('capabilitySummary').textContent=`Capabilities · ${selectedCaps?selectedCaps+' selected':'any'}`;
  renderList();markerGroups=D.coordinateGroups(matches);spatial=D.createSpatialIndex(markerGroups);renderMarkers();
}
function chooser(rows,distinct,marker){
  const panel=document.createElement('div'),heading=document.createElement('p'),list=document.createElement('ul');
  heading.textContent=`${rows.length} studios ${distinct>1?'in this map group':'at this coordinate'}`;panel.append(heading,list);
  let offset=0;const size=30;
  const pagination=document.createElement('div');pagination.className='pagination';
  const previous=document.createElement('button'),next=document.createElement('button'),info=document.createElement('span');
  previous.textContent='← Previous';next.textContent='Next →';info.setAttribute('aria-live','polite');
  function draw(){list.replaceChildren();for(const studio of rows.slice(offset,offset+size)){
    const li=document.createElement('li'),button=document.createElement('button');button.type='button';
    button.textContent=`${studio.name} — ${studio.city}`;
    button.onclick=()=>{marker.closePopup();navigate('location',studio.id,button);};li.appendChild(button);list.appendChild(li);
  }if(rows.length>size){info.textContent=`${offset+1}–${Math.min(offset+size,rows.length)} of ${rows.length}`;previous.disabled=offset===0;next.disabled=offset+size>=rows.length;}}
  previous.onclick=()=>{offset-=size;draw();list.querySelector('button')?.focus();};next.onclick=()=>{offset+=size;draw();list.querySelector('button')?.focus();};
  if(rows.length>size){pagination.append(previous,info,next);panel.appendChild(pagination);}
  if(distinct>1){const zoom=document.createElement('button');zoom.textContent='Zoom to these studios';zoom.onclick=()=>{marker.closePopup();map.fitBounds(L.latLngBounds(rows.map(r=>[r.lat,r.lng])).pad(.2),{maxZoom:17,animate:false});};panel.appendChild(zoom);}
  draw();return panel;
}
function renderMarkers(){
  if(!layer||!spatial)return;const start=performance.now();layer.clearLayers();
  const b=map.getBounds().pad(.2),bounds={west:b.getWest(),east:b.getEast(),south:b.getSouth(),north:b.getNorth()};
  const visible=markerGroups.length>2000?spatial.query(bounds):markerGroups;
  const clusters=D.clusterCoordinateGroups(visible,map.getZoom());
  for(const cluster of clusters){const s=cluster.rows[0],count=cluster.rows.length;
    const marker=cluster.groups.length>1?L.marker([s.lat,s.lng],{keyboard:true,title:`${count} studios — select to explore`,
      icon:L.divIcon({className:'cluster-icon',html:`<span>${count}</span>`,iconSize:[40,40],iconAnchor:[20,20]})}):
      L.circleMarker([s.lat,s.lng],{radius:8,color:'#ffd1d2',weight:2,fillColor:'#e74f60',fillOpacity:.88});
    marker.addTo(layer);marker.motionxLocations=cluster.rows.map(r=>r.id);
    if(count===1){marker.on('click',()=>navigate('location',s.id));continue;}
    const panel=chooser(cluster.rows,cluster.groups.length,marker);marker.bindPopup(panel,{maxWidth:320});
    marker.on('popupopen',()=>panel.querySelector('button')?.focus());
  }
  timings.viewport_groups=visible.length;timings.rendered_markers=clusters.length;timings.marker_render_ms=performance.now()-start;
}
map?.on('moveend',()=>{if(markerGroups.length>2000&&!layer.getLayers().some(m=>m.isPopupOpen()))renderMarkers();});
map?.on('popupclose',()=>requestAnimationFrame(()=>{if(markerGroups.length>2000&&!layer.getLayers().some(m=>m.isPopupOpen()))renderMarkers();}));
function branchLinks(rows,limit=12){return '<ul class="branch-list">'+rows.slice(0,limit).map(r=>`<li>${profileLink('location',r.id,r.name+` · ${r.city}, ${r.country}`)}</li>`).join('')+'</ul>';}
function relationshipList(rows){
  const entries=new Map();for(const r of rows)for(const rel of r.relationships||[])entries.set(JSON.stringify([rel.id,rel.type,rel.evidence]),rel);
  if(!entries.size)return '<p class="muted">No parent or group relationship is established in this research.</p>';
  return '<ul>'+[...entries.values()].map(r=>`<li>${directory.organisations.has(r.id)||directory.groups.has(r.id)?profileLink('organisation',r.id,r.name):esc(r.name)} — ${esc(r.type.replaceAll('_',' '))} · ${external(r.evidence,'Source')} · ${esc(r.verified_on)}</li>`).join('')+'</ul>';
}
function locationProfile(s){
  const org=directory.organisations.get(s.company_id),branches=org.rows.filter(r=>r.id!==s.id);
  const precision=s.coordinate_precision==='exact'?'Exact (see cited research evidence)':`${s.coordinate_precision} — approximate reference pin; not a verified street address`;
  const capabilities=state=>s.capabilities.filter(c=>s.capability_evidence[c].state===state).map(c=>{
    const e=s.capability_evidence[c];return `<li>${esc(c)} — ${esc(e.state)}${e.evidence?' · '+external(e.evidence,'Source'):''}${e.verified_on?' · reviewed '+esc(e.verified_on):' · not yet reviewed'}</li>`;
  }).join('');
  return `<div class="eyebrow">STUDIO LOCATION</div><h2 id="profileTitle" tabindex="-1">${esc(s.name)}</h2>
    <p class="muted">${esc(s.city)}, ${esc(s.country)}</p>
    <p>${profileLink('organisation',org.id,org.name)} · ${countLabel(org.rows.length,'location')} in this operating organisation</p>
    <span class="stat">Evidence confidence: ${esc(s.evidence_state)}</span><span class="stat">${esc((s.location_type||'uncertain').replaceAll('_',' '))}</span>
    <p class="source-note muted">${esc(s.status)}</p>
    <h3>Source-confirmed capabilities</h3>${capabilities('confirmed')?'<ul>'+capabilities('confirmed')+'</ul>':'<p class="muted">No facility capability is confirmed in the recorded evidence.</p>'}
    ${capabilities('likely')?'<h3>Likely capabilities</h3><ul>'+capabilities('likely')+'</ul>':''}
    ${capabilities('unknown')?'<h3>Unreviewed capabilities</h3><ul>'+capabilities('unknown')+'</ul>':''}
    <h3>Specialisations & location</h3><p>${s.categories.map(c=>`<span class="tag">${esc(c)}</span>`).join('')}</p>
    <dl><dt>Location type</dt><dd>${esc((s.location_type||'uncertain').replaceAll('_',' '))}</dd><dt>Coordinate precision</dt><dd>${esc(precision)}${s.coordinate_source?' · '+external(s.coordinate_source,'City reference source'):''}</dd><dt>Location reference</dt><dd>${esc(s.address||'Street address not verified')}</dd><dt>Website</dt><dd>${external(s.website,'Official website')}</dd></dl>
    <h3>Evidence & review</h3><p>${external(s.evidence,'Official/public source')}<br><span class="muted">${s.legacy_research&&s.evidence_state==='unknown'?'Legacy recorded review date (not independently verified)':'Recorded review date'}: ${esc(s.verified_on||'Not reviewed')}. Source presence does not prove capability, registration or current operation.</span></p>
    <h3>Organisation relationships</h3>${relationshipList([s])}
    <h3>Other branches & facilities</h3>${branches.length?branchLinks(branches):'<p class="muted">No other branch is currently listed under this operating identity.</p>'}
    ${branches.length>12?'<p>'+profileLink('organisation',org.id,'Browse all '+org.rows.length+' locations')+'</p>':''}
    <p>${profileLink('organisation',org.id,'View organisation and related operating brands')}</p>
    <p><a href="${D.profileHash('location',s.id)}">Permanent link to this location</a></p>`;
}
function organisationProfile(id){
  const org=directory.organisations.get(id),group=directory.groups.get(id);
  if(!org&&!group)return null;
  const rows=org?org.rows:[...group.members].flatMap(key=>directory.organisations.get(key).rows);
  const name=org?org.name:group.name;
  const related=org?D.relatedOrganisations(directory,id):[...group.members].map(key=>directory.organisations.get(key));
  return `<div class="eyebrow">${org?'OPERATING ORGANISATION':'SOURCED PARENT / GROUP'}</div><h2 id="profileTitle" tabindex="-1">${esc(name)}</h2>
    <p class="muted">${countLabel(rows.length,'location')} · ${countLabel(new Set(rows.map(r=>r.country)).size,'country')}</p>
    <p class="source-note">${org?'Locations share this stable operating identity. Capabilities remain specific to each facility.':'These are separate operating brands linked by cited ownership/group relationships. This group is not counted as an additional operating studio.'}</p>
    ${org?'<h3>Parent & group evidence</h3>'+relationshipList(rows):''}
    <h3>${org?'Branches & facilities':'Locations across operating brands'}</h3><div id="organisationBranches">${branchLinks(rows,50)}</div>
    ${rows.length>50?`<button id="moreBranches" data-org="${esc(id)}" data-offset="50">Show more locations</button>`:''}
    <h3>${org?'Related operating brands':'Operating brands'}</h3>${related.length?'<ul class="branch-list">'+related.slice(0,100).map(o=>`<li>${profileLink('organisation',o.id,o.name+' · '+countLabel(o.rows.length,'location'))}</li>`).join('')+'</ul>':'<p class="muted">No related operating brand is established in the recorded ownership evidence.</p>'}
    <p class="muted">Grouping is based on cited relationships; related brands do not inherit each other’s services.</p>
    ${!org?relationshipList(rows):''}<p><a href="${D.profileHash('organisation',id)}">Permanent link to this ${org?'organisation':'group'}</a></p>`;
}
function navigate(kind,id,element){if(element)opener=element;const hash=D.profileHash(kind,id);if(location.hash!==hash)history.pushState(null,'',hash);applyRoute();}
function closeProfile(){if(location.hash)history.pushState(null,'',location.pathname+location.search);applyRoute();}
function applyRoute(){
  if(!loaded)return;const start=performance.now(),route=D.parseProfileHash(location.hash);
  if(route.kind==='directory'){$('detail').hidden=true;selected=null;renderList();if(opener?.isConnected)opener.focus();return;}
  let content=null;
  if(route.kind==='location'){
    const s=directory.byId.get(route.id);if(s){selected=s.id;content=locationProfile(s);
      if(map&&!map.getBounds().contains([s.lat,s.lng]))map.setView([s.lat,s.lng],Math.max(map.getZoom(),6),{animate:false});}
  }else if(route.kind==='organisation'){selected='organisation:'+route.id;content=organisationProfile(route.id);}
  $('detailContent').innerHTML=content||'<div class="eyebrow">PROFILE UNAVAILABLE</div><h2 id="profileTitle" tabindex="-1">This profile could not be found.</h2><p>The link may be incomplete or the identity may not be listed yet.</p><button data-close>Back to directory</button>';
  $('detail').hidden=false;$('profileTitle').focus();renderList();timings.profile_open_ms=performance.now()-start;
}
window.addEventListener('hashchange',applyRoute);
function updateTabs(){const list=document.body.classList.contains('show-list');for(const[id,on]of[['mapTab',!list],['listTab',list]]){$(id).classList.toggle('active',on);$(id).setAttribute('aria-pressed',String(on));}}
$('mapTab').onclick=()=>{document.body.classList.remove('show-list');updateTabs();setTimeout(()=>map?.invalidateSize(),60);};
$('listTab').onclick=()=>{document.body.classList.add('show-list');updateTabs();};
$('close').onclick=closeProfile;document.addEventListener('keydown',e=>{if(e.key==='Escape'&&!$('detail').hidden){e.preventDefault();closeProfile();}});
document.addEventListener('click',e=>{
  const reset=e.target.closest('[data-reset]');if(reset){resetFilters();return;}
  if(e.target.closest('[data-close]')){closeProfile();return;}
  const more=e.target.closest('#moreBranches');if(more){const org=directory.organisations.get(more.dataset.org),group=directory.groups.get(more.dataset.org);
    const rows=org?org.rows:[...group.members].flatMap(id=>directory.organisations.get(id).rows);const offset=Number(more.dataset.offset);
    $('organisationBranches').insertAdjacentHTML('beforeend',branchLinks(rows.slice(offset),50));more.dataset.offset=offset+50;if(offset+50>=rows.length)more.remove();return;}
  const anchor=e.target.closest('a[href^="#/"]');if(!anchor||e.button!==0||e.ctrlKey||e.metaKey||e.shiftKey||e.altKey)return;
  const route=D.parseProfileHash(anchor.getAttribute('href'));e.preventDefault();if(route.kind==='directory')closeProfile();else if(route.kind!=='invalid')navigate(route.kind,route.id,anchor);
});
function resetFilters(){for(const id of ['search','country','city','category','locationType'])$(id).value='';$('confirmedOnly').checked=false;$('capabilityMode').value='all';document.querySelectorAll('#capabilityOptions input').forEach(i=>{i.checked=false;});page=0;closeProfile();render();}
$('resetFilters').onclick=resetFilters;
for(const id of ['search','country','city','category','locationType','confirmedOnly','capabilityMode','capabilityOptions'])$(id).addEventListener('input',()=>{
  clearTimeout(searchTimer);searchTimer=setTimeout(()=>{page=0;closeProfile();render();},['search','city'].includes(id)?120:0);
});
for(const mode of ['locations','organisations'])$(mode+'View').onclick=()=>{viewMode=mode;page=0;for(const m of ['locations','organisations'])$(m+'View').setAttribute('aria-pressed',String(m===mode));renderList();};
$('previousPage').onclick=()=>{page--;renderList();};$('nextPage').onclick=()=>{page++;renderList();};
$('fitResults').onclick=()=>{if(matches.length&&map)map.fitBounds(L.latLngBounds(matches.map(r=>[r.lat,r.lng])).pad(.25),{maxZoom:10,animate:false});};
$('exportCsv').onclick=()=>{const a=document.createElement('a');a.href=URL.createObjectURL(new Blob(['\uFEFF'+D.exportCSV(matches)],{type:'text/csv;charset=utf-8'}));a.download='motionx_studios_filtered_v1.0.csv';document.body.appendChild(a);a.click();setTimeout(()=>{URL.revokeObjectURL(a.href);a.remove();},1000);};
window.addEventListener('resize',()=>setTimeout(()=>map?.invalidateSize(),80));
function setControls(enabled){document.querySelectorAll('#filters input,#filters select,#exportCsv,#resetFilters,#fitResults,#locationsView,#organisationsView,#previousPage,#nextPage').forEach(el=>{el.disabled=!enabled;});if(!map)$('fitResults').disabled=true;}
async function initialize(){
  const start=performance.now();loaded=false;setControls(false);$('dataStatus').hidden=false;$('dataStatus').firstChild.textContent='Loading studio database… ';$('retryLoad').hidden=true;$('count').textContent='Loading locations…';$('companies').textContent='';$('detail').hidden=true;
  try{
    studios=await D.loadDatabase();timings.load_validate_ms=performance.now()-start;const indexing=performance.now();directory=D.createDirectoryIndex(studios);timings.index_ms=performance.now()-indexing;
    $('country').replaceChildren(new Option('All countries',''),...[...new Set(studios.map(r=>r.country))].sort().map(c=>new Option(c,c)));
    $('category').replaceChildren(new Option('All sectors',''),...[...new Set([...D.sectors,...studios.flatMap(r=>r.categories)])].sort().map(c=>new Option(c,c)));
    $('capabilityOptions').replaceChildren();for(const capability of [...new Set(studios.flatMap(r=>r.capabilities))].sort()){
      const label=document.createElement('label');label.className='check-label';const input=document.createElement('input');input.type='checkbox';input.value=capability;label.append(input,document.createTextNode(capability));$('capabilityOptions').appendChild(label);
    }
    loaded=true;page=0;setControls(true);render();$('dataStatus').hidden=true;timings.ready_ms=performance.now()-start;applyRoute();
  }catch(error){studios=[];matches=[];markerGroups=[];directory=null;layer?.clearLayers();$('count').textContent='Studio data unavailable';$('companies').textContent='';$('list').textContent='No records loaded. Retry when the database is available.';
    $('dataStatus').firstChild.textContent=`Unable to load studios.json. ${error.name==='AbortError'?'Request timed out.':error.message} Serve this site over HTTP and check your connection. `;$('retryLoad').hidden=false;console.error('MotionX database load failed:',error);
  }
}
$('retryLoad').onclick=initialize;initialize();
