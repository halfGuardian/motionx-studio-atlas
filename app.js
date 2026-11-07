/* Static GitHub Pages. Reviewed baseline + optional hash-bound bulk catalogue. */
'use strict';
const $=id=>document.getElementById(id), D=MotionXData;
const esc=value=>String(value??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const external=(url,label)=>D.httpsURL(url)?`<a href="${esc(url)}" target="_blank" rel="noopener noreferrer">${esc(label)}</a>`:'Source not recorded';
const profileLink=(kind,id,label,extra='')=>`<a href="${D.profileHash(kind,id)}" ${extra}>${esc(label)}</a>`;
const countLabel=(n,label)=>`${n} ${label}${n===1?'':'s'}`;
const badge=(row,compact=false)=>{const c=typeof row==='string'?row:D.evidenceClass(row),style=D.evidenceStyles[c];return `<span class="evidence-badge evidence-${c}" data-evidence="${c}"><span class="evidence-symbol" aria-hidden="true">${style.symbol}</span> ${compact?'Class '+c:'Class '+c+' · '+style.label}</span>`;};
const pageSize=50;
const hasPoint=s=>Number.isFinite(s.lat)&&Number.isFinite(s.lng),unified=()=>catalog?.manifest.mode==='unified_research';
let studios=[],directory=null,matches=[],selected=null,page=0,loaded=false,viewMode='locations',opener=null,openerHash=null;
let markerGroups=[],spatial=null,searchTimer;
let catalog=null,routeVersion=0,captureQuick=false,comparison=[];
const timings=globalThis.MotionXPerformance={};
const map=globalThis.L?L.map('map',{worldCopyJump:true,preferCanvas:true,zoomAnimation:false,fadeAnimation:false,markerZoomAnimation:false}).setView([28,-25],2):null;
const layer=map?L.layerGroup().addTo(map):null;
if(map){
  const osm=L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png',{
    attribution:'&copy; <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noopener noreferrer">OpenStreetMap contributors</a>',maxZoom:19}).addTo(map);
  const status=document.createElement('div');status.className='tile-status';status.hidden=true;
  status.textContent='Map tiles could not load. Every studio remains accessible in the directory.';$('map').appendChild(status);
  osm.on('tileerror',()=>{status.hidden=false;});osm.on('tileload',()=>{status.hidden=true;});
}else{const message=document.createElement('p');message.className='map-error';message.textContent='Map library could not load. Use the studio directory, or reload to retry.';$('map').appendChild(message);if(innerWidth<=750){document.body.classList.add('show-list');updateTabs();}}
function controls(){return {query:$('search').value,country:$('country').value,city:$('city').value,sector:$('category').value,
  locationType:$('locationType').value,evidenceClass:$('evidenceClass').value,recordKind:$('recordKind').value,confirmedOnly:$('confirmedOnly').checked,capabilityMode:$('capabilityMode').value,organisation:$('organisation').value,sort:$('sortResults').value,researchFocus:$('researchFocus').value,confirmedCaptureOnly:captureQuick,
  capabilities:[...document.querySelectorAll('#capabilityOptions input:checked')].map(input=>input.value)};}
function filtered(){return matches;}
function locationCard(s){
  const org=directory.organisations.get(s.company_id);
  return `<article class="entry evidence-entry-${D.evidenceClass(s)} ${selected===s.id?'selected':''}">
    ${badge(s,true)}
    ${profileLink('organisation',org.id,org.name,'class="org-link"')}
    <h3>${profileLink('location',s.id,s.name,`class="profile-link" data-id="${esc(s.id)}"`)}</h3>
    <div class="muted">${esc(s.city||'City not supplied')}, ${esc(s.country||'Country not supplied')}</div>
    ${unified()?'<div class="eyebrow">'+(s.record_kind==='company_reference'?'COMPANY REFERENCE · NO VERIFIED BRANCH':s.record_kind==='source_location'?'SOURCE LOCATION OBSERVATION':'RETAINED ATLAS LOCATION')+'</div>':''}
    ${s.categories.map(t=>`<span class="tag">${esc(t)}</span>`).join('')}
    <div class="confidence">${hasPoint(s)?esc(s.coordinate_precision)+' coordinates':'No source coordinates'} · ${D.observationAge(s)===null?'Date not recorded':(s.source_observed_on?'Observed ':'Recorded ')+D.observationAge(s)+' days ago'}</div><button class="compare-record" data-compare="${esc(s.id)}" aria-pressed="${comparison.includes(s.id)}">${comparison.includes(s.id)?'Selected for comparison':'Compare record'}</button></article>`;
}
function organisationCard(org,rows){return `<article class="entry"><div class="eyebrow">${unified()&&org.rows.every(r=>r.record_kind!=='retained_location')?'SOURCE IDENTITY — UNREVIEWED':'OPERATING ORGANISATION'}</div>
  <h3>${profileLink('organisation',org.id,org.name,'class="profile-link"')}</h3>
  <p class="muted">${countLabel(rows.length,unified()?'matching record':'matching location')} · ${org.rows.length} total</p>
  <div class="muted">${esc([...new Set(rows.map(r=>r.country))].sort().join(' · '))}</div><div class="evidence-breakdown">${Object.entries(D.evidenceCounts(rows)).filter(([,n])=>n).map(([c,n])=>badge(c,true)+' <span>'+n+'</span>').join(' ')}</div></article>`;}
function renderList(){
  const grouped=new Map();for(const row of matches){if(!grouped.has(row.company_id))grouped.set(row.company_id,[]);grouped.get(row.company_id).push(row);}
  const items=viewMode==='locations'?matches:[...grouped.keys()];
  page=Math.min(page,Math.max(0,Math.ceil(items.length/pageSize)-1));
  $('count').textContent=countLabel(matches.length,unified()?'record':'location');
  $('companies').textContent=`${countLabel(grouped.size,'organization')} · ${studios.length} total locations / ${countLabel(directory.organisations.size,'organization')}`;
  if(catalog){const c=catalog.manifest.counts;$('companies').textContent=unified()?`${c.retained_locations} retained · ${c.source_location_observations.toLocaleString()} source observations · ${c.company_references.toLocaleString()} company references. Records can overlap.`:`${grouped.size} matching identities · ${c.class_a} Class A / ${c.class_b} Class B locations · ${c.reviewed_operating_organisations} reviewed operating organisations / ${c.provisional_source_identities} provisional source identities`;}
  $('list').innerHTML=items.slice(page*pageSize,(page+1)*pageSize).map(item=>viewMode==='locations'?locationCard(item):organisationCard(directory.organisations.get(item),grouped.get(item))).join('')||
    '<div class="empty-state"><h3>'+(unified()?'No records match yet.':'No studios match yet.')+'</h3><p class="muted">Try fewer capabilities, a broader city search, or reset the filters.</p><button data-reset>Reset all filters</button></div>';
  $('pageInfo').textContent=items.length?`${page*pageSize+1}–${Math.min((page+1)*pageSize,items.length)} of ${items.length}`:'0 results';
  $('previousPage').disabled=page===0;$('nextPage').disabled=(page+1)*pageSize>=items.length;
}
function render(){
  if(!loaded)return;
  const start=performance.now();matches=D.queryDirectory(directory,controls());timings.search_ms=performance.now()-start;
  const selectedCaps=controls().capabilities.length;$('capabilitySummary').textContent=`Capabilities · ${selectedCaps?selectedCaps+' selected':'any'}`;
  renderList();const points=matches.filter(hasPoint);markerGroups=D.coordinateGroups(points);spatial=D.createSpatialIndex(markerGroups);renderMarkers();$('fitResults').disabled=!map||!markerGroups.length;
  const counts=D.evidenceCounts(points);for(const c of ['A','B','C'])$('legend'+c).textContent=counts[c].toLocaleString();
  syncQuickFilters();
}
function chooser(rows,distinct,marker){
  const panel=document.createElement('div'),heading=document.createElement('p'),list=document.createElement('ul');
  heading.textContent=`${rows.length} ${unified()?'records':'studios'} ${distinct>1?'in this map group':'at this coordinate'}`;
  const breakdown=document.createElement('p');breakdown.className='evidence-breakdown';breakdown.innerHTML=Object.entries(D.evidenceCounts(rows)).filter(([,n])=>n).map(([c,n])=>badge(c,true)+' <strong>'+n+'</strong>').join(' ');panel.append(heading,breakdown,list);
  let offset=0;const size=30;
  const pagination=document.createElement('div');pagination.className='pagination';
  const previous=document.createElement('button'),next=document.createElement('button'),info=document.createElement('span');
  previous.textContent='← Previous';next.textContent='Next →';info.setAttribute('aria-live','polite');
  function draw(){list.replaceChildren();for(const studio of rows.slice(offset,offset+size)){
    const li=document.createElement('li'),button=document.createElement('button');button.type='button';button.dataset.recordId=studio.id;
    button.innerHTML=badge(studio,true)+'<span>'+esc(studio.name+' — '+studio.city)+'</span>';
    button.onclick=()=>{marker.closePopup();navigate('location',studio.id,button);};li.appendChild(button);list.appendChild(li);
  }if(rows.length>size){info.textContent=`${offset+1}–${Math.min(offset+size,rows.length)} of ${rows.length}`;previous.disabled=offset===0;next.disabled=offset+size>=rows.length;}}
  previous.onclick=()=>{offset-=size;draw();list.querySelector('button')?.focus();};next.onclick=()=>{offset+=size;draw();list.querySelector('button')?.focus();};
  if(rows.length>size){pagination.append(previous,info,next);panel.appendChild(pagination);}
  if(distinct>1){const zoom=document.createElement('button');zoom.textContent=unified()?'Zoom to these records':'Zoom to these studios';zoom.onclick=()=>{marker.closePopup();map.fitBounds(L.latLngBounds(rows.map(r=>[r.lat,r.lng])).pad(.2),{maxZoom:17,animate:false});};panel.appendChild(zoom);}
  draw();return panel;
}
function renderMarkers(){
  if(!layer||!spatial)return;const start=performance.now();layer.clearLayers();
  const b=map.getBounds().pad(.2),bounds={west:b.getWest(),east:b.getEast(),south:b.getSouth(),north:b.getNorth()};
  const visible=markerGroups.length>120?spatial.query(bounds):markerGroups;
  const clusters=D.clusterCoordinateGroups(visible,map.getZoom());
  for(const cluster of clusters){const s=cluster.anchor||cluster.rows[0],count=cluster.rows.length,info=D.markerEvidence(cluster.rows),c=D.evidenceClass(s),colour=D.evidenceStyles[c].colour;
    const shape=c==='A'?'<rect x="5" y="5" width="20" height="20" rx="2"/>':c==='B'?'<circle cx="15" cy="15" r="11"/>':'<polygon points="15,2 29,27 1,27"/>';
    const a=100*info.counts.A/count,ab=100*(info.counts.A+info.counts.B)/count;
    const html=count===1?`<svg viewBox="0 0 30 30" aria-hidden="true"><g fill="${colour}" stroke="#fff" stroke-width="1.5">${shape}</g><text x="15" y="${c==='C'?22:20}" text-anchor="middle" fill="#000" font-size="12" font-weight="800">${c}</text></svg>`:
      `<span class="cluster-ring" style="background:conic-gradient(#238B67 0 ${a}%,#347FBA ${a}% ${ab}%,#B58A2A ${ab}% 100%)"><span class="cluster-core">${count.toLocaleString()}<small>${info.classes.join(' · ')}</small></span></span>`;
    const title=(count===1?s.name+'. ':'')+info.label+' — select to explore';
    const marker=L.marker([s.lat,s.lng],{keyboard:true,title,icon:L.divIcon({className:count===1?'evidence-marker':'evidence-cluster',html,iconSize:count===1?[30,30]:[52,52],iconAnchor:count===1?[15,15]:[26,26]})});
    marker.addTo(layer);marker.motionxLocations=cluster.rows.map(r=>r.id);
    const element=marker.getElement();element.setAttribute('role','button');element.setAttribute('aria-label',title);element.dataset.evidence=count===1?c:info.classes.length===1?info.classes[0]:'mixed';for(const cls of ['A','B','C'])element.dataset['classCount'+cls]=info.counts[cls];
    element.addEventListener('keydown',e=>{if(e.key===' '){e.preventDefault();marker.fire('click');}});
    if(count===1){marker.on('click',()=>navigate('location',s.id));continue;}
    const panel=chooser(cluster.rows,cluster.groups.length,marker);marker.bindPopup(panel,{maxWidth:320});
    marker.on('popupopen',()=>panel.querySelector('button')?.focus());
  }
  timings.viewport_groups=visible.length;timings.rendered_markers=clusters.length;timings.marker_render_ms=performance.now()-start;
}
map?.on('moveend',()=>{if(markerGroups.length>120&&!layer.getLayers().some(m=>m.isPopupOpen()))renderMarkers();});
map?.on('popupclose',()=>requestAnimationFrame(()=>{if(markerGroups.length>120&&!layer.getLayers().some(m=>m.isPopupOpen()))renderMarkers();}));
function branchLinks(rows,limit=12){return '<ul class="branch-list">'+rows.slice(0,limit).map(r=>`<li>${profileLink('location',r.id,r.name+` · ${r.city||'City not supplied'}, ${r.country||'Country not supplied'}`)}</li>`).join('')+'</ul>';}
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
  return `<div class="eyebrow">${s.record_kind==='company_reference'?'COMPANY REFERENCE · PHYSICAL BRANCHES UNVERIFIED':s.record_kind==='source_location'?'SOURCE LOCATION OBSERVATION':'STUDIO LOCATION'}</div><h2 id="profileTitle" tabindex="-1">${esc(s.name)}</h2>
    <p class="muted">${esc(s.city||'City not supplied')}, ${esc(s.country||'Country not supplied')}${!hasPoint(s)?' · No source coordinates; no map pin is invented.':''}</p>
    <p>${profileLink('organisation',org.id,org.name)} · ${countLabel(org.rows.length,unified()?'record':'location')} in this ${s.identity_status==='source_provisional'?'provisional source identity':'operating organisation'}</p>
    ${badge(s)}<span class="stat">${s.evidence_class==='B'?'Class B — Source-listed, not independently corroborated':D.evidenceClass(s)==='A'?'Class A — Source-reviewed location':'Class C — Research required'} · Evidence confidence: ${esc(s.evidence_state)}</span><span class="stat">${esc((s.location_type||'uncertain').replaceAll('_',' '))}</span>
    <p class="source-note muted">${esc(s.status)}</p>
    <h3>Source-confirmed capabilities</h3>${capabilities('confirmed')?'<ul>'+capabilities('confirmed')+'</ul>':'<p class="muted">No facility capability is confirmed in the recorded evidence.</p>'}
    ${capabilities('likely')?'<h3>Likely capabilities</h3><ul>'+capabilities('likely')+'</ul>':''}
    ${capabilities('unknown')?'<h3>Unreviewed capabilities</h3><ul>'+capabilities('unknown')+'</ul>':''}
    <h3>Specialisations & location</h3><p>${s.categories.map(c=>`<span class="tag">${esc(c)}</span>`).join('')}</p>
    <dl><dt>Location type</dt><dd>${esc((s.location_type||'uncertain').replaceAll('_',' '))}</dd><dt>Coordinate precision</dt><dd>${esc(precision)}${s.coordinate_source?' · '+external(s.coordinate_source,s.source_provenance?'Original source reference':'City reference source'):''}</dd><dt>Location reference</dt><dd>${esc(s.address||'Street address not verified')}</dd><dt>Website</dt><dd>${external(s.website,s.website_kind==='source_listing'?'Directory source listing':s.source_provenance?'Website listed by source':'Official website')}</dd></dl>
    <h3>Evidence & review</h3><p>${external(s.evidence,s.source_provenance?'Source dataset':'Official/public source')}<br><span class="muted">${s.legacy_research&&s.evidence_state==='unknown'?'Legacy recorded review date (not independently verified)':'Recorded review date'}: ${esc(s.verified_on||'Not reviewed')}. Source presence does not prove capability, registration or current operation.</span></p>
    <h3>Organisation relationships</h3>${relationshipList([s])}
    ${s.source_provenance?'<h3>Directory provenance & reuse</h3><p class="source-note">Current operation, physical facility type and services have not been independently corroborated. The source category is not a verified capability. Observed: '+esc(s.source_observed_on)+'. Identity: '+esc(s.identity_status.replaceAll('_',' '))+(s.identity_status==='matched_existing'?'. This is a candidate match to a retained operating identity; it does not confirm a physical branch or ownership.':'')+'</p><ul>'+s.source_provenance.map(p=>'<li>'+esc(p.source_id+' / '+p.source_record_id)+' · '+external(p.url,'Source object')+' · '+external(p.license_url,p.license==='UNSPECIFIED'?'Source reuse terms not specified':p.license)+' · '+esc(p.observed_on)+'</li>').join('')+'</ul><p class="muted">'+esc(s.attribution)+'</p>':''}
    ${s.research_reasons?.length?'<h3>Research notes</h3><ul>'+s.research_reasons.map(r=>'<li>'+esc(r)+'</li>').join('')+'</ul><p>Source status: '+esc(s.source_status||'Not supplied')+' — source assertion, not a MotionX closure or current-operation decision.</p>':''}
    ${s.potential_duplicates?.length?'<h3>Possible existing matches</h3><ul>'+s.potential_duplicates.flatMap(p=>p.ids.filter(id=>id!==s.id).map(id=>'<li>'+profileLink('location',id,directory.byId.get(id)?.name||id)+' · '+esc(p.reasons.join('; '))+` <button data-compare-pair="${esc(id)}" data-primary="${esc(s.id)}">Compare evidence</button></li>`)).join('')+'</ul><p class="muted">Matches require research. Distinct facilities are not automatically merged.</p>':''}
    <h3>Research next steps</h3><p class="muted">${s.source_observed_on?'Source observation':'Recorded date'}: ${esc(s.source_observed_on||s.verified_on||'Missing')}${D.observationAge(s)===null?'':' · '+D.observationAge(s)+' days ago'}. An observation date is not a new verification.</p>${D.researchContext(s,directory).reasons.length?'<ul>'+D.researchContext(s,directory).reasons.map(r=>'<li>'+esc(r)+'</li>').join('')+'</ul>':'<p>Review existing sources before proposing any correction.</p>'}
    <h3>${unified()?'Related records under this identity':'Other branches & facilities'}</h3>${branches.length?branchLinks(branches):'<p class="muted">No other branch is currently listed under this operating identity.</p>'}
    ${branches.length>12?'<p>'+profileLink('organisation',org.id,'Browse all '+org.rows.length+' locations')+'</p>':''}
    <p>${profileLink('organisation',org.id,'View organisation and related operating brands')}</p>
    <p><a href="${D.profileHash('location',s.id)}">Permanent link to this record</a> · <button data-copy-profile>Copy profile link</button></p><p class="muted">Human research and a reviewed PR are required before changing the source-reviewed database.</p>`;
}
function organisationProfile(id){
  const org=directory.organisations.get(id),group=directory.groups.get(id);
  if(!org&&!group)return null;
  const rows=org?org.rows:[...group.members].flatMap(key=>directory.organisations.get(key).rows);
  const provisional=rows.every(r=>r.source_observed_on&&r.identity_status==='source_provisional');
  const name=org?org.name:group.name;
  const related=org?D.relatedOrganisations(directory,id):[...group.members].map(key=>directory.organisations.get(key));
  return `<div class="eyebrow">${provisional?'PROVISIONAL SOURCE IDENTITY':org?'OPERATING ORGANISATION':'SOURCED PARENT / GROUP'}</div><h2 id="profileTitle" tabindex="-1">${esc(name)}</h2>
    <p class="evidence-breakdown">${Object.entries(D.evidenceCounts(rows)).filter(([,n])=>n).map(([c,n])=>badge(c,true)+' <strong>'+n+'</strong>').join(' ')}</p><p class="muted">${rows.filter(r=>r.record_kind==='company_reference').length} company-only references · ${rows.filter(r=>r.record_kind==='source_location').length} source observations · ${rows.filter(r=>r.record_kind==='retained_location'||!r.record_kind).length} established locations. Grouping does not establish new ownership or physical branches.</p>
    <p class="muted">${countLabel(rows.length,unified()?'record':'location')} · ${countLabel(new Set(rows.map(r=>r.country).filter(Boolean)).size,'country')}</p>
    <p class="source-note">${provisional?'This provisional source grouping uses directory names and links. Operating identity, physical branches and ownership require research. Grouping confirms no facility services.':org?'Established records use this stable operating identity. Attached source observations remain candidate matches requiring research. Capabilities remain specific to each facility.':'These are separate operating brands linked by cited ownership/group relationships. This group is not counted as an additional operating studio.'}</p>
    ${org?'<h3>Parent & group evidence</h3>'+relationshipList(rows):''}
    <h3>${unified()?'Records under this identity':provisional?'Source-listed locations':org?'Branches & facilities':'Locations across operating brands'}</h3><div id="organisationBranches">${branchLinks(rows,50)}</div>
    ${rows.length>50?`<button id="moreBranches" data-org="${esc(id)}" data-offset="50">${unified()?'Show more records':'Show more locations'}</button>`:''}
    <h3>${org?'Related operating brands':'Operating brands'}</h3>${related.length?'<ul class="branch-list">'+related.map(o=>`<li>${profileLink('organisation',o.id,o.name+' · '+countLabel(o.rows.length,'location'))}</li>`).join('')+'</ul>':'<p class="muted">No related operating brand is established in the recorded ownership evidence.</p>'}
    <p class="muted">Grouping is based on cited relationships; related brands do not inherit each other’s services.</p>
    ${!org?relationshipList(rows):''}<p><a href="${D.profileHash('organisation',id)}">Permanent link to this ${org?'organisation':'group'}</a></p>`;
}
function navigate(kind,id,element){if(element){opener=element;openerHash=element.getAttribute('href');}const hash=D.profileHash(kind,id);if(location.hash!==hash)history.pushState(null,'',hash);applyRoute();}
async function compareRecords(ids){
  if(ids.length!==2||ids[0]===ids[1]||ids.some(id=>!directory.byId.has(id)))return;
  const version=++routeVersion;$('detail').hidden=false;$('detailContent').textContent='Loading both source records…';
  try{const rows=await Promise.all(ids.map(id=>catalog?catalog.details(id):directory.byId.get(id)));if(version!==routeVersion)return;
    const fields=['id','company_id','record_kind','city','country','lat','lng','coordinate_precision','categories','capabilities','capability_evidence','relationships','source_observed_on','verified_on','source_status','license'];
    const formatted=v=>Array.isArray(v)&&v.every(s=>typeof s==='string')?v.join(', '):v&&typeof v==='object'?JSON.stringify(v,null,2):v??'Not supplied';
    $('detailContent').innerHTML='<h2 id="profileTitle" tabindex="-1">Compare research records</h2><p>Comparison does not merge identities or approve claims. Original source observations remain separate.</p>'+rows.map(r=>'<article class="comparison-record">'+badge(r)+'<h3>'+profileLink('location',r.id,r.name)+'</h3><dl>'+fields.map(k=>'<dt>'+esc(k.replaceAll('_',' '))+'</dt><dd>'+esc(formatted(r[k]))+'</dd>').join('')+'</dl><p>'+external(r.evidence,'Original evidence')+' · '+external(r.website,'Website recorded by source')+'</p><ul>'+(r.source_provenance||[]).map(p=>'<li>'+esc(p.source_id+' / '+p.source_record_id)+' · '+external(p.url,'Source')+' · '+esc(p.observed_on)+'</li>').join('')+'</ul></article>').join('');$('profileTitle').focus();
  }catch(error){if(version===routeVersion)$('detailContent').textContent='Comparison unavailable: '+error.message;}
}
function closeProfile(restoreFocus=true){if(location.hash)history.pushState(null,'',location.pathname+location.search);applyRoute(restoreFocus);}
async function applyRoute(restoreFocus=true){
  if(!loaded)return;const version=++routeVersion,start=performance.now(),route=D.parseProfileHash(location.hash);
  if(route.kind==='directory'){$('detail').hidden=true;selected=null;renderList();if(restoreFocus&&opener){const target=[...$('list').querySelectorAll('a')].find(a=>a.getAttribute('href')===openerHash);if(target?.getClientRects().length)target.focus();else if($('search').getClientRects().length)$('search').focus();else $('map').focus();}return;}
  let content=null;
  if(route.kind==='location'){
    let s=directory.byId.get(route.id);if(s||catalog?.researchOnly.has(route.id)){
      if(catalog){$('detail').hidden=false;$('detailContent').textContent='Loading profile evidence…';try{s=await catalog.details(route.id);}catch(error){if(version!==routeVersion)return;$('detailContent').innerHTML='<h2 id="profileTitle" tabindex="-1">Profile evidence unavailable</h2><p>'+esc(error.message)+'</p><button data-retry-profile>Retry profile</button>';return;}if(version!==routeVersion)return;}
      selected=s.id;content=locationProfile(s);
      if(map&&hasPoint(s)&&!map.getBounds().contains([s.lat,s.lng]))map.setView([s.lat,s.lng],Math.max(map.getZoom(),6),{animate:false});}
  }else if(route.kind==='organisation'){selected='organisation:'+route.id;content=organisationProfile(route.id);}
  $('detailContent').innerHTML=content||'<div class="eyebrow">PROFILE UNAVAILABLE</div><h2 id="profileTitle" tabindex="-1">This profile could not be found.</h2><p>The link may be incomplete or the identity may not be listed yet.</p><button data-close>Back to directory</button>';
  $('detail').hidden=false;$('profileTitle').focus();renderList();timings.profile_open_ms=performance.now()-start;
}
window.addEventListener('hashchange',applyRoute);
function updateTabs(){const list=document.body.classList.contains('show-list');for(const[id,on]of[['mapTab',!list],['listTab',list]]){$(id).classList.toggle('active',on);$(id).setAttribute('aria-pressed',String(on));}}
$('mapTab').onclick=()=>{document.body.classList.remove('show-list');updateTabs();setTimeout(()=>map?.invalidateSize(),60);};
$('listTab').onclick=()=>{document.body.classList.add('show-list');updateTabs();};
$('close').onclick=()=>closeProfile();document.addEventListener('keydown',e=>{if(e.key==='Escape'&&!$('detail').hidden){e.preventDefault();closeProfile();}});
document.addEventListener('click',e=>{
  const pair=e.target.closest('[data-compare-pair]');if(pair){compareRecords([pair.dataset.primary,pair.dataset.comparePair]);return;}
  const compare=e.target.closest('[data-compare]');if(compare){const id=compare.dataset.compare;comparison=comparison.includes(id)?comparison.filter(v=>v!==id):[...comparison.slice(-1),id];renderList();$('comparisonStatus').textContent=comparison.length+' of 2 records selected for comparison.';if(comparison.length===2)compareRecords(comparison);return;}
  const copy=e.target.closest('[data-copy-profile]');if(copy){const value=new URL(location.href).href;if(navigator.clipboard?.writeText)navigator.clipboard.writeText(value).then(()=>{copy.textContent='Link copied';}).catch(()=>{copy.textContent='Use the permanent link above';});else copy.textContent='Use the permanent link above';return;}
  if(e.target.closest('[data-retry-profile]')){applyRoute();return;}
  if(e.target.closest('.skip-link')){e.preventDefault();closeProfile(false);if(innerWidth<=750){document.body.classList.add('show-list');updateTabs();}$('search').focus();return;}
  const reset=e.target.closest('[data-reset]');if(reset){resetFilters();return;}
  if(e.target.closest('[data-close]')){closeProfile();return;}
  const more=e.target.closest('#moreBranches');if(more){const org=directory.organisations.get(more.dataset.org),group=directory.groups.get(more.dataset.org);
    const rows=org?org.rows:[...group.members].flatMap(id=>directory.organisations.get(id).rows);const offset=Number(more.dataset.offset);
    $('organisationBranches').insertAdjacentHTML('beforeend',branchLinks(rows.slice(offset),50));more.dataset.offset=offset+50;if(offset+50>=rows.length)more.remove();return;}
  const anchor=e.target.closest('a[href^="#/"]');if(!anchor||e.button!==0||e.ctrlKey||e.metaKey||e.shiftKey||e.altKey)return;
  const route=D.parseProfileHash(anchor.getAttribute('href'));e.preventDefault();if(route.kind==='directory')closeProfile();else if(route.kind!=='invalid')navigate(route.kind,route.id,anchor);
});
function syncQuickFilters(){const current=captureQuick?'capture':$('recordKind').value==='company_reference'?'companies':$('evidenceClass').value||'all';$('evidenceClass').dataset.selected=$('evidenceClass').value;for(const button of document.querySelectorAll('[data-quick]'))button.setAttribute('aria-pressed',String(button.dataset.quick===current));}
function resetFilters(){for(const id of ['search','country','city','category','locationType','evidenceClass','recordKind','organisation','researchFocus'])$(id).value='';captureQuick=false;$('sortResults').value='relevance';$('confirmedOnly').checked=false;$('capabilityMode').value='all';document.querySelectorAll('#capabilityOptions input').forEach(i=>{i.checked=false;});page=0;closeProfile(false);render();}
for(const button of document.querySelectorAll('[data-quick]'))button.onclick=()=>{const value=button.dataset.quick;if(value==='all'){resetFilters();return;}captureQuick=value==='capture';$('evidenceClass').value=['A','B','C'].includes(value)?value:'';$('recordKind').value=value==='companies'?'company_reference':'';page=0;closeProfile(false);render();};
$('resetFilters').onclick=resetFilters;
for(const id of ['search','country','city','category','locationType','evidenceClass','recordKind','organisation','researchFocus','sortResults','confirmedOnly','capabilityMode','capabilityOptions'])$(id).addEventListener('input',()=>{
  if(['evidenceClass','recordKind'].includes(id))captureQuick=false;
  clearTimeout(searchTimer);searchTimer=setTimeout(()=>{page=0;closeProfile(false);render();},['search','city'].includes(id)?120:0);
});
for(const mode of ['locations','organisations'])$(mode+'View').onclick=()=>{viewMode=mode;page=0;for(const m of ['locations','organisations'])$(m+'View').setAttribute('aria-pressed',String(m===mode));renderList();};
$('previousPage').onclick=()=>{page--;renderList();};$('nextPage').onclick=()=>{page++;renderList();};
$('fitResults').onclick=()=>{const points=matches.filter(hasPoint);if(points.length&&map)map.fitBounds(L.latLngBounds(points.map(r=>[r.lat,r.lng])).pad(.25),{maxZoom:10,animate:false});};
$('exportCsv').onclick=async()=>{const button=$('exportCsv'),snapshot=matches.slice();button.disabled=true;button.textContent='Loading evidence…';try{const bundle=catalog?await catalog.exportBundle(snapshot):{rows:snapshot};const rows=bundle.rows;const a=document.createElement('a');a.href=URL.createObjectURL(new Blob(['\uFEFF'+D.exportCSV(rows,bundle)],{type:'text/csv;charset=utf-8'}));a.download='motionx_atlas_filtered_v1.1.csv';document.body.appendChild(a);a.click();setTimeout(()=>{URL.revokeObjectURL(a.href);a.remove();},1000);}catch(error){$('dataStatus').hidden=false;$('dataStatus').firstChild.textContent='CSV export failed. No partial file downloaded. '+error.message+' ';$('retryLoad').hidden=false;}finally{button.disabled=false;button.textContent='↓ CSV';}};
window.addEventListener('resize',()=>setTimeout(()=>map?.invalidateSize(),80));
function setControls(enabled){document.querySelectorAll('#filters input,#filters select,#quickFilters button,#exportCsv,#sortResults,#resetFilters,#fitResults,#locationsView,#organisationsView,#previousPage,#nextPage').forEach(el=>{el.disabled=!enabled;});if(!map)$('fitResults').disabled=true;}
async function initialize(){
  const start=performance.now();loaded=false;setControls(false);$('dataStatus').hidden=false;$('dataStatus').firstChild.textContent='Loading studio database… ';$('retryLoad').hidden=true;$('count').textContent='Loading locations…';$('companies').textContent='';$('detail').hidden=true;
  studios=[];matches=[];directory=null;markerGroups=[];spatial=null;layer?.clearLayers();$('list').textContent='Loading the complete catalogue…';$('catalogSummary').replaceChildren();for(const c of ['A','B','C'])$('legend'+c).textContent='—';
  try{
    const progress=info=>{const total=info.total?Math.min(100,Math.floor(info.received/info.total*100)):null;$('dataStatus').firstChild.textContent=`Loading complete global search index${total===null?'':': '+total+'%'} · ${(info.received/1048576).toFixed(1)} MB received. Full results are available after integrity checks. `;};
    if(document.documentElement.dataset.catalog==='sharded'){catalog=await MotionXCatalog.load(D,undefined,undefined,{onProgress:progress});studios=catalog.rows;}else{catalog=null;studios=(await D.loadDatabase()).map(r=>({...r,evidence_class:r.evidence_state==='confirmed'?'A':'C'}));}timings.load_validate_ms=performance.now()-start;const indexing=performance.now();directory=D.createDirectoryIndex(studios);timings.index_ms=performance.now()-indexing;
    const summary=D.catalogueSummary(studios);$('catalogSummary').innerHTML=[['Total records',summary.records],['Geolocated records',summary.geolocated],['Source-reviewed locations',summary.A],['Provisional identities',summary.provisionalIdentities],['Confirmed capture facilities',summary.confirmedCapture]].map(([label,n])=>'<div><dt>'+label+'</dt><dd>'+n.toLocaleString()+'</dd></div>').join('');
    $('country').replaceChildren(new Option('All countries',''),...[...new Set(studios.map(r=>r.country).filter(Boolean))].sort().map(c=>new Option(c,c)));
    $('category').replaceChildren(new Option('All sectors',''),...[...new Set([...D.sectors,...studios.flatMap(r=>r.categories)])].sort().map(c=>new Option(c,c)));
    $('capabilityOptions').replaceChildren();for(const capability of [...new Set(studios.flatMap(r=>r.capabilities))].sort()){
      const label=document.createElement('label');label.className='check-label';const input=document.createElement('input');input.type='checkbox';input.value=capability;label.append(input,document.createTextNode(capability));$('capabilityOptions').appendChild(label);
    }
    loaded=true;page=0;setControls(true);render();$('dataStatus').hidden=true;timings.ready_ms=performance.now()-start;applyRoute();
  }catch(error){studios=[];matches=[];markerGroups=[];directory=null;layer?.clearLayers();$('count').textContent='Studio data unavailable';$('companies').textContent='';$('list').textContent='No records loaded. Retry when the database is available.';
    $('dataStatus').firstChild.textContent=`${document.documentElement.dataset.catalog==='sharded'?'Unable to load studio catalogue.':'Unable to load studios.json.'} ${error.name==='AbortError'?'Request timed out.':error.message} Serve this site over HTTP and check your connection. `;$('retryLoad').hidden=false;console.error('MotionX database load failed:',error);
  }
}
$('retryLoad').onclick=initialize;initialize();
