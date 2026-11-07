/* Offline review worksheet. Draft decisions are never publication approval. */
(function(root){'use strict';
  const choices=['needs_evidence','existing_company','possible_alias','additional_branch_review','identity_conflict','historical_review','out_of_scope','rights_review'];
  function safeURL(value){try{const u=new URL(value),h=u.hostname.toLowerCase().replace(/\.$/,'');return u.protocol==='https:'&&!u.username&&!u.password&&!u.port&&h.includes('.')&&!h.endsWith('.local')&&!h.endsWith('.localhost')&&!h.endsWith('.internal')&&!/^[\d.]+$/.test(h)&&!/[\\\u0000-\u0020\u007f]/.test(value)&&!/[?&](?:access_token|api[_-]?key|auth|password|token)=/i.test(value)?u.href:null;}catch{return null;}}
  const cell=v=>{const s=typeof v==='object'?JSON.stringify(v):String(v??'');return /^[\s\u200b\u200c\u200d]*[=+@-]/u.test(s)?"'"+s:s;};
  function csv(rows,fields){return '\uFEFF'+[fields,...rows.map(r=>fields.map(k=>cell(r[k])))].map(r=>r.map(v=>'"'+String(v).replaceAll('"','""')+'"').join(',')).join('\r\n');}
  function filter(rows,options){const q=String(options.q||'').toLocaleLowerCase();return rows.filter(r=>(!options.country||r.country===options.country)&&(!options.region||r.research_region===options.region)&&(!options.rights||r.historical_rights===options.rights)&&(!options.source||r.source_id===options.source)&&(!options.outcome||r.disposition===options.outcome)&&(!q||[r.name,r.country,r.city,r.source_id,r.disposition,r.matching_reason,...r.service_claims].join(' ').toLocaleLowerCase().includes(q)));}
  function bundle(reportHash,decisions,rows){
    if(!/^[a-f0-9]{64}$/.test(reportHash))throw Error('Invalid report checkpoint');const byid=new Map(rows.map(r=>[r.observation_id,r]));const result=[];
    for(const [id,d] of Object.entries(decisions)){
      const row=byid.get(id);if(!row||!choices.includes(d.decision)||typeof d.notes!=='string'||d.notes.length>2000||d.content_hash!==row.content_hash)throw Error('Unknown or stale working decision');
      result.push({observation_id:id,content_hash:row.content_hash,decision:d.decision,notes:d.notes,human_approved:false});
    }
    return {version:1,report_sha256:reportHash,human_approved:false,authenticated_review:false,canonical_updates:[],purpose:'Unauthenticated working notes only. Review the exact PR and source evidence in GitHub; no importer accepts these as approval.',decisions:result};
  }
  const api={choices,safeURL,cell,csv,filter,bundle};if(typeof module==='object'&&module.exports)module.exports=api;root.MotionXGlobalReview=api;
  if(!root.document)return;
  const $=id=>document.getElementById(id),decisions=Object.create(null);let rows=[],page=0,reportHash='';
  function el(tag,text){const n=document.createElement(tag);if(text!==undefined)n.textContent=text;return n;}
  function download(value,type,name){const u=URL.createObjectURL(new Blob([value],{type})),a=el('a');a.href=u;a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(u),1000);}
  function render(){const selected=filter(rows,{q:$('q').value,country:$('country').value,region:$('region').value,rights:$('rights').value,source:$('source').value,outcome:$('outcome').value});page=Math.min(page,Math.max(0,Math.ceil(selected.length/25)-1));$('count').textContent=selected.length+' matching observations · '+rows.length+' total; repeated source observations are not additional businesses';$('review').replaceChildren();
    for(const r of selected.slice(page*25,page*25+25)){
      const card=el('article');card.dataset.observation=r.observation_id;card.append(el('h3',r.name),el('p',[r.country||'Country unknown',r.city,r.source_id,r.disposition].filter(Boolean).join(' · ')),el('p',r.matching_reason),el('p','Company service assertions: '+(r.service_claims.join(', ')||'none')+'. No independently verified facility capability is inferred.'),el('p','Observed '+r.observed_on+' · '+r.origin+' · Source assertion date: '+(r.source_updated_on||'not established')+' · '+r.freshness_state+' · company geography and current operation require separate review.'));
      const u=safeURL(r.source_url);if(u){const a=el('a','Source evidence');a.href=u;a.target='_blank';a.rel='noopener noreferrer';card.append(a);}
      const changes=(Array.isArray(r.source_change_signals)?r.source_change_signals:[]).filter(s=>s.kind==='possible_identity_geography_service_change');if(changes.length){const details=el('details');details.append(el('summary','Before/after source assertions — investigation required'),el('pre',JSON.stringify(changes,null,2)));card.append(details);}
      const label=el('label','Working decision '),select=el('select');select.setAttribute('aria-label','Working decision for '+r.name);const initial=el('option','Pending — no human decision');initial.value='';select.append(initial);for(const c of choices){const o=el('option',c.replaceAll('_',' '));o.value=c;select.append(o);}select.value=decisions[r.observation_id]?.decision||'';
      const notes=el('textarea');notes.maxLength=2000;notes.setAttribute('aria-label','Working notes for '+r.name);notes.placeholder='Public research notes only; no private contacts or confidential information.';notes.value=decisions[r.observation_id]?.notes||'';
      const save=()=>{if(select.value)decisions[r.observation_id]={content_hash:r.content_hash,decision:select.value,notes:notes.value};else delete decisions[r.observation_id];};select.addEventListener('change',save);notes.addEventListener('input',save);label.append(select);card.append(el('br'),label,notes);$('review').append(card);
    }
    $('previous').disabled=page===0;$('next').disabled=(page+1)*25>=selected.length;
  }
  for(const id of ['q','country','region','rights','source','outcome'])$(id).addEventListener(id==='q'?'input':'change',()=>{page=0;render();});$('previous').onclick=()=>{page--;render();};$('next').onclick=()=>{page++;render();};
  $('exportJson').onclick=()=>{try{download(JSON.stringify(bundle(reportHash,decisions,rows),null,2),'application/json','motionx-global-working-decisions.json');}catch(e){$('error').textContent=e.message;}};
  $('exportCsv').onclick=()=>{try{const b=bundle(reportHash,decisions,rows);download(csv(b.decisions.map(r=>({...r,report_sha256:b.report_sha256})),['observation_id','content_hash','decision','notes','human_approved','report_sha256']),'text/csv;charset=utf-8','motionx-global-working-decisions.csv');}catch(e){$('error').textContent=e.message;}};
  fetch('./review-index.json.gz',{cache:'no-store'}).then(r=>{if(!r.ok)throw Error('Review index unavailable; no empty/approved substitute.');if(!globalThis.DecompressionStream)throw Error('This compressed review report requires a browser with gzip stream support. Download the JSON gzip artifact for offline review.');return new Response(r.body.pipeThrough(new DecompressionStream('gzip'))).json();}).then(data=>{
    if(data.version!==1||!Array.isArray(data.rows)||!Array.isArray(data.fields)||data.rows.length>250000)throw Error('Invalid bounded review index');reportHash=data.report_sha256;
    rows=data.rows.map(values=>Object.fromEntries(data.fields.map((k,i)=>[k,values[i]])));if(new Set(rows.map(r=>r.observation_id)).size!==rows.length)throw Error('Duplicate observation identities');
    for(const [id,key] of [['country','country'],['region','research_region'],['rights','historical_rights'],['source','source_id'],['outcome','disposition']])for(const value of [...new Set(rows.map(r=>r[key]))].filter(Boolean).sort()){const o=el('option',value);o.value=value;$(id).append(o);}
    $('summary').append(el('p',data.summary.catalogue_records.toLocaleString()+' preserved catalogue references · '+data.summary.countries_and_territories+' represented countries/territories · '+data.summary.countries_with_source_search+' source-search receipts · '+data.summary.new_sources_fully_enumerated+' newly complete enumerations · 0 new independently reviewed facilities · human precision/recall pending.'));render();
  }).catch(e=>{$('count').textContent='Research report unavailable';$('error').textContent=e.message;for(const id of ['exportJson','exportCsv','previous','next'])$(id).disabled=true;});
})(typeof globalThis==='object'?globalThis:this);
