/* Hash-bound compact search index and lazy provenance shards. No backend. */
(function(root){
  'use strict';
  const identifier=/^[a-z0-9]+(?:-[a-z0-9]+)*$/;
  const shardPath=/^shards\/[a-f0-9]{12}-\d{3,}\.json$/;
  async function sha(text){
    if(!root.crypto?.subtle)throw new Error('Secure data integrity checks unavailable. Serve over HTTPS or localhost.');
    return [...new Uint8Array(await root.crypto.subtle.digest('SHA-256',new TextEncoder().encode(text)))].map(v=>v.toString(16).padStart(2,'0')).join('');
  }
  async function json(fetcher,path,hash,limit=8000000){
    const controller=new AbortController(),timer=setTimeout(()=>controller.abort(),30000);
    try{
      const response=await fetcher(path,{cache:'no-store',signal:controller.signal});
      if(!response.ok)throw new Error(`Catalogue request failed (HTTP ${response.status}): ${path}`);
      if(Number(response.headers?.get('content-length'))>limit)throw new Error('Catalogue response exceeds size limit.');
      const text=await response.text();
      if(new TextEncoder().encode(text).length>limit)throw new Error('Catalogue response exceeds size limit.');
      if(hash && await sha(text)!==hash)throw new Error(`Catalogue integrity mismatch: ${path}`);
      return {value:JSON.parse(text),text};
    }finally{clearTimeout(timer);}
  }
  function checkB(D,row){
    D.validateDatabase([row]);
    if(row.evidence_class!=='B'||row.evidence_state!=='unknown'||row.verified_on||row.capabilities.length||Object.keys(row.capability_evidence).length||row.relationships?.length||row.coordinate_precision==='exact'||!row.license||!row.attribution||!D.validDate(row.source_observed_on)||!['official','source_listing'].includes(row.website_kind)||!['source_provisional','matched_existing'].includes(row.identity_status)||!Array.isArray(row.source_provenance)||!row.source_provenance.length)throw new Error('Invalid source-listed evidence.');
    for(const p of row.source_provenance)if(!D.httpsURL(p.url)||!D.httpsURL(p.license_url)||p.observed_on!==row.source_observed_on||!p.source_record_id||!/^[a-f0-9]{64}$/.test(p.observation_hash))throw new Error('Invalid source provenance.');
  }
  async function load(D,fetcher=root.fetch.bind(root),path='./data/public/manifest.json'){
    if(path!=='./data/public/manifest.json')throw new Error('Unapproved catalogue manifest path.');
    const [{value:m},{value:base,text:baseText}]=await Promise.all([json(fetcher,path,null,2000000),json(fetcher,'./studios.json',null,60000000)]);
    D.validateDatabase(base);
    if(m.version!==1||m.baseline?.path!=='./studios.json'||m.index?.path!=='index.json'||!m.shards||!Array.isArray(m.baseline.eligible_ids)||!Array.isArray(m.baseline.research_only_ids)||await sha(baseText)!==m.baseline.sha256)throw new Error('Invalid catalogue/baseline integrity.');
    const baseMap=new Map(base.map(r=>[r.id,r])),ids=new Set(),rows=[];
    for(const id of m.baseline.eligible_ids){const r=baseMap.get(id);if(!r||r.evidence_state!=='confirmed'||!r.evidence||!r.verified_on||ids.has(id))throw new Error('Invalid Class A baseline identity.');ids.add(id);rows.push({...r,evidence_class:'A'});}
    const held=new Set(m.baseline.research_only_ids);
    if(held.size!==m.baseline.research_only_ids.length||[...held].some(id=>!baseMap.has(id)||ids.has(id))||held.size+ids.size!==base.length)throw new Error('Incomplete baseline preservation audit.');
    const index=(await json(fetcher,'./data/public/index.json',m.index.sha256,20000000)).value;
    if(!Array.isArray(index)||index.length!==m.index.records)throw new Error('Invalid compact index.');
    const metadata=new Map();
    for(const entry of index){
      if(!Array.isArray(entry)||entry.length!==11)throw new Error('Invalid compact location.');
      const [id,company_id,name,city,country,lat,lng,categories,shard,observed,identity_status]=entry;
      if(!identifier.test(id)||!identifier.test(company_id)||baseMap.has(id)||ids.has(id)||![name,city,country].every(t=>typeof t==='string'&&t.trim()&&t.length<=2000)||!Number.isFinite(lat)||Math.abs(lat)>90||!Number.isFinite(lng)||Math.abs(lng)>180||!Array.isArray(categories)||!categories.length||categories.some(c=>typeof c!=='string'||!c.trim())||!shardPath.test(shard)||!m.shards[shard]||!D.validDate(observed)||!['source_provisional','matched_existing'].includes(identity_status))throw new Error('Invalid indexed source-listed location.');
      const row={id,company_id,name,city,country,lat,lng,categories,capabilities:[],capability_evidence:{},relationships:[],evidence_class:'B',evidence_state:'unknown',coordinate_precision:'approximate',location_type:'uncertain',source_observed_on:observed,identity_status,detail_shard:shard};
      rows.push(row);ids.add(id);metadata.set(id,row);
    }
    if(rows.length!==m.counts.public_locations||m.counts.class_a!==m.baseline.eligible_ids.length||m.counts.class_b!==index.length)throw new Error('Catalogue counts mismatch.');
    const pending=new Map(),full=new Map(rows.filter(r=>r.evidence_class==='A').map(r=>[r.id,r]));
    async function details(id){
      if(full.has(id))return full.get(id);
      const stub=metadata.get(id);if(!stub)throw new Error(held.has(id)?'This legacy identity is retained in the research queue pending location-evidence review.':'Profile identity unavailable.');
      const key=stub.detail_shard,meta=m.shards[key];
      if(!pending.has(key))pending.set(key,(async()=>{
        const values=(await json(fetcher,'./data/public/'+key,meta.sha256)).value;
        if(!Array.isArray(values)||values.length!==meta.records)throw new Error('Shard record count mismatch.');
        const staged=new Map();
        for(const row of values){
          checkB(D,row);const expected=metadata.get(row.id);
          if(!expected||expected.detail_shard!==key||staged.has(row.id)||['company_id','name','city','country','lat','lng','source_observed_on','identity_status'].some(f=>row[f]!==expected[f])||JSON.stringify(row.categories)!==JSON.stringify(expected.categories))throw new Error('Shard/index identity mismatch.');
          staged.set(row.id,row);
        }
        for(const [rid,row] of staged)full.set(rid,row);
      })().catch(error=>{pending.delete(key);throw error;}));
      await pending.get(key);if(!full.has(id))throw new Error('Profile missing from detail shard.');return full.get(id);
    }
    async function exportRows(filtered){
      const results=new Array(filtered.length);let cursor=0;
      await Promise.all(Array.from({length:Math.min(3,filtered.length)},async()=>{while(cursor<filtered.length){const i=cursor++;results[i]=await details(filtered[i].id);}}));return results;
    }
    return {rows,manifest:m,details,exportRows,researchOnly:held};
  }
  const api={load,sha,checkB};if(typeof module!=='undefined'&&module.exports)module.exports=api;else root.MotionXCatalog=api;
})(globalThis);
