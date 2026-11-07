/* Hash-bound compact search index and lazy provenance shards. No backend. */
(function(root){
  'use strict';
  const identifier=/^[a-z0-9]+(?:-[a-z0-9]+)*$/;
  const shardPath=/^shards\/[a-f0-9]{12}-\d{3,}\.json$/;
  async function sha(text){
    return shaBytes(new TextEncoder().encode(text));
  }
  async function shaBytes(bytes){
    if(!root.crypto?.subtle)throw new Error('Secure data integrity checks unavailable. Serve over HTTPS or localhost.');
    return [...new Uint8Array(await root.crypto.subtle.digest('SHA-256',bytes))].map(v=>v.toString(16).padStart(2,'0')).join('');
  }
  async function json(fetcher,path,hash,limit=8000000,packedHash=null,progress=null,cache='no-store'){
    const controller=new AbortController(),timer=setTimeout(()=>controller.abort(),packedHash?120000:60000);
    try{
      const response=await fetcher(path,{cache,signal:controller.signal});
      if(!response.ok)throw new Error(`Catalogue request failed (HTTP ${response.status}): ${path}`);
      if(Number(response.headers?.get('content-length'))>limit)throw new Error('Catalogue response exceeds size limit.');
      let text,bytes;
      if(response.body?.getReader){
        const reader=response.body.getReader(),chunks=[];let length=0;
        try{while(true){const {value,done}=await reader.read();if(done)break;length+=value.length;if(length>limit)throw new Error('Catalogue response exceeds size limit.');chunks.push(value);progress?.(length,Number(response.headers?.get('content-length'))||0);}}
        catch(error){await reader.cancel().catch(()=>{});throw error;}
        bytes=new Uint8Array(length);let offset=0;for(const c of chunks){bytes.set(c,offset);offset+=c.length;}
      }else bytes=new Uint8Array(await response.arrayBuffer());
      if(bytes.length>limit)throw new Error('Catalogue response exceeds size limit.');
      if(packedHash){
        const packed=bytes;
        if(packed.length>limit)throw new Error('Compressed catalogue response exceeds size limit.');
        if(packed[0]===31&&packed[1]===139){
          if(await shaBytes(packed)!==packedHash)throw new Error('Compressed catalogue integrity mismatch.');
          const stream=new Blob([packed]).stream().pipeThrough(new DecompressionStream('gzip')),reader=stream.getReader(),chunks=[];let length=0;
          while(true){const {value,done}=await reader.read();if(done)break;length+=value.length;if(length>limit){await reader.cancel();throw new Error('Catalogue decompression exceeds size limit.');}chunks.push(value);}
          const bytes=new Uint8Array(length);let offset=0;for(const c of chunks){bytes.set(c,offset);offset+=c.length;}text=new TextDecoder('utf-8',{fatal:true}).decode(bytes);
        }else if(response.headers?.get('content-encoding'))text=new TextDecoder('utf-8',{fatal:true}).decode(packed);
        else throw new Error('Invalid compressed catalogue representation.');
      }else text=new TextDecoder('utf-8',{fatal:true}).decode(bytes);
      if(new TextEncoder().encode(text).length>limit)throw new Error('Catalogue response exceeds size limit.');
      if(hash && await sha(text)!==hash)throw new Error(`Catalogue integrity mismatch: ${path}`);
      return {value:JSON.parse(text),text};
    }finally{clearTimeout(timer);}
  }
  function asset(fetcher,path,meta,limit=8000000,progress=null){
    const suffix=meta.content_addressed?'?sha256='+meta.sha256:'',cache=meta.content_addressed?'force-cache':'no-store';
    if(meta.gzip_sha256&&typeof root.DecompressionStream==='function'){
      if(!/^[a-f0-9]{64}$/.test(meta.gzip_sha256))throw new Error('Invalid compressed asset hash.');
      return json(fetcher,path+'.gz'+suffix,meta.sha256,limit,meta.gzip_sha256,progress,cache);
    }
    return json(fetcher,path+suffix,meta.sha256,limit,null,progress,cache);
  }
  function fullIdentity(value){
    if(typeof value!=='string')throw new Error('Invalid packed identity.');
    if(!value.startsWith('~'))return value;
    const code=value.slice(0,2),data=value.slice(2);
    if(!/^[A-Za-z0-9+/]+$/.test(data)||data.length>24)throw new Error('Invalid packed identity.');
    let raw;try{raw=[...atob(data+'='.repeat((4-data.length%4)%4))].map(c=>c.charCodeAt(0).toString(16).padStart(2,'0')).join('');}catch{throw new Error('Invalid packed identity.');}
    if(code==='~u'&&raw.length===32)return 'overture-'+[raw.slice(0,8),raw.slice(8,12),raw.slice(12,16),raw.slice(16,20),raw.slice(20)].join('-');
    const prefix={'~o':'overture-org-','~g':'gamedb-org-','~c':'gamedb-'}[code];
    if(!prefix||raw.length!==(code==='~c'?28:24))throw new Error('Invalid packed identity.');
    return prefix+raw;
  }
  function decodeIndex(value,expected){
    const tableColumns=[3,4,7,8,9,10,11,12];
    if(value?.encoding!=='motionx-columnar-v1'||!Number.isSafeInteger(expected)||expected<0||expected>250000||value.rows!==expected||!Array.isArray(value.columns)||value.columns.length!==14||value.columns.some(c=>!Array.isArray(c)||c.length!==expected)||!value.tables||Object.keys(value.tables).length!==tableColumns.length||tableColumns.some(k=>!Array.isArray(value.tables[k])||value.tables[k].length>expected))throw new Error('Invalid columnar index.');
    const rows=[];
    for(let i=0;i<expected;i++){
      const row=value.columns.map((column,k)=>{
        const v=column[i];if(!tableColumns.includes(k))return v;
        if(!Number.isSafeInteger(v)||v<0||v>=value.tables[k].length)throw new Error('Invalid compact dictionary reference.');
        return value.tables[k][v];
      });
      row[0]=fullIdentity(row[0]);row[1]=fullIdentity(row[1]);
      if(!Number.isInteger(row[13])||row[13]<0||row[13]>31)throw new Error('Invalid advisory research flags.');rows.push(row);
    }
    return rows;
  }
  async function licence(fetcher,name,hash){
    if(!/^(CDLA-Permissive-2\.0|Apache-2\.0|CC0-1\.0|CC-BY-4\.0|Foursquare-NOTICE)\.txt$/.test(name)||!/^[a-f0-9]{64}$/.test(hash||''))throw new Error('Unreviewed redistribution licence.');
    const controller=new AbortController(),timer=setTimeout(()=>controller.abort(),30000);
    try{const response=await fetcher('./data/bulk/LICENSES/'+name,{signal:controller.signal});
      if(!response.ok)throw new Error('Redistribution notices unavailable.');
      const text=await response.text();if(text.length>100000||await sha(text)!==hash)throw new Error('Redistribution notice integrity mismatch.');return text;
    }finally{clearTimeout(timer);}
  }
  function checkB(D,row){
    D.validateDatabase([row]);
    if(row.evidence_class!=='B'||row.evidence_state!=='unknown'||row.verified_on||row.capabilities.length||Object.keys(row.capability_evidence).length||row.relationships?.length||row.coordinate_precision==='exact'||!row.license||!row.attribution||!D.validDate(row.source_observed_on)||!['official','source_listing'].includes(row.website_kind)||!['source_provisional','matched_existing'].includes(row.identity_status)||!Array.isArray(row.source_provenance)||!row.source_provenance.length)throw new Error('Invalid source-listed evidence.');
    for(const p of row.source_provenance)if(!D.httpsURL(p.url)||!D.httpsURL(p.license_url)||p.observed_on!==row.source_observed_on||!p.source_record_id||!/^[a-f0-9]{64}$/.test(p.observation_hash))throw new Error('Invalid source provenance.');
  }
  function checkResearch(D,row){
    if(!row||!identifier.test(row.id)||!identifier.test(row.company_id)||!['B','C'].includes(row.evidence_class)||!['source_location','company_reference'].includes(row.record_kind)||typeof row.name!=='string'||!row.name.trim()||typeof row.city!=='string'||typeof row.country!=='string')throw new Error('Invalid research identity.');
    const hasPoint=row.lat!==null||row.lng!==null;
    if(hasPoint&&(!Number.isFinite(row.lat)||Math.abs(row.lat)>90||!Number.isFinite(row.lng)||Math.abs(row.lng)>180)||row.record_kind==='company_reference'&&hasPoint)throw new Error('Invalid research coordinates.');
    if(row.evidence_state!=='unknown'||row.verified_on||!Array.isArray(row.capabilities)||row.capabilities.length||!row.capability_evidence||Object.keys(row.capability_evidence).length||row.relationships?.length||row.coordinate_precision==='exact'||!Array.isArray(row.categories)||row.categories.some(c=>typeof c!=='string'||!c.trim())||!D.httpsURL(row.website)||!D.httpsURL(row.evidence)||!D.validDate(row.source_observed_on)||!row.license||!row.attribution||!Array.isArray(row.source_provenance)||!row.source_provenance.length)throw new Error('Research records cannot claim verification.');
    if(row.evidence_class==='B'&&(!hasPoint||!row.city||!row.country||row.license==='UNSPECIFIED'))throw new Error('Incomplete Class B source location.');
    for(const p of row.source_provenance)if(!D.httpsURL(p.url)||!D.httpsURL(p.license_url)||!p.source_record_id||p.observed_on!==row.source_observed_on||!/^[a-f0-9]{64}$/.test(p.observation_hash))throw new Error('Invalid research provenance.');
  }
  async function load(D,fetcher=root.fetch.bind(root),path='./data/public/manifest.json',options={}){
    if(path!=='./data/public/manifest.json')throw new Error('Unapproved catalogue manifest path.');
    const {value:m}=await json(fetcher,path,null,2000000);
    const transport=m.index?.compact,compressedBase=m.baseline?.compressed;
    if(transport&&(transport.path!=='index.compact.json'||transport.encoding!=='motionx-columnar-v1'||transport.records!==m.index.records||!/^[a-f0-9]{64}$/.test(transport.sha256)))throw new Error('Invalid compact transport.');
    if(compressedBase&&(compressedBase.path!=='baseline.json'||compressedBase.sha256!==m.baseline.sha256||!/^[a-f0-9]{64}$/.test(compressedBase.sha256)))throw new Error('Invalid compressed baseline.');
    const notify=(received,total)=>options.onProgress?.({phase:'index',received,total:total||(transport||m.index).gzip_bytes||0,records:m.counts?.records});
    const [{value:base,text:baseText},indexResponse]=await Promise.all([
      compressedBase?asset(fetcher,'./data/public/baseline.json',compressedBase,60000000):json(fetcher,'./studios.json',null,60000000),
      asset(fetcher,'./data/public/'+(transport?.path||'index.json'),transport||m.index,20000000,notify)
    ]);
    D.validateDatabase(base);
    if(m.version!==1||m.baseline?.path!=='./studios.json'||m.index?.path!=='index.json'||!m.shards||!Array.isArray(m.baseline.eligible_ids)||!Array.isArray(m.baseline.research_only_ids)||await sha(baseText)!==m.baseline.sha256||!/^[a-f0-9]{64}$/.test(m.index.sha256)||Object.entries(m.shards).some(([key,v])=>!shardPath.test(key)||!/^[a-f0-9]{64}$/.test(v.sha256)||!Number.isInteger(v.records)||v.records<1||v.records>1000))throw new Error('Invalid catalogue/baseline integrity.');
    const unified=m.mode==='unified_research',baseMap=new Map(base.map(r=>[r.id,r])),ids=new Set(),rows=[];
    if(new Set(m.baseline.eligible_ids).size!==m.baseline.eligible_ids.length||m.baseline.eligible_ids.some(id=>baseMap.get(id)?.evidence_state!=='confirmed'))throw new Error('Invalid Class A baseline identity.');
    for(const id of unified?m.baseline.active_ids:m.baseline.eligible_ids){const r=baseMap.get(id);if(!r||(!unified&&(r.evidence_state!=='confirmed'||!r.evidence||!r.verified_on))||ids.has(id))throw new Error('Invalid Class A baseline identity.');ids.add(id);rows.push({...r,evidence_class:r.evidence_state==='confirmed'?'A':'C',...(unified?{record_kind:'retained_location'}:{})});}
    const held=new Set(m.baseline.research_only_ids);
    if(held.size!==m.baseline.research_only_ids.length||[...held].some(id=>!baseMap.has(id)||ids.has(id))||held.size+ids.size!==base.length)throw new Error('Incomplete baseline preservation audit.');
    const index=transport?decodeIndex(indexResponse.value,m.index.records):indexResponse.value;
    if(!Array.isArray(index)||index.length!==m.index.records)throw new Error('Invalid compact index.');
    const metadata=new Map();
    for(const entry of index){
      if(!Array.isArray(entry)||entry.length!==(transport?14:unified?13:11))throw new Error('Invalid compact location.');
      const [id,company_id,name,city,country,lat,lng,categories,shard,observed,identity_status,evidenceClass,recordKind]=entry;
      const validPoint=Number.isFinite(lat)&&Math.abs(lat)<=90&&Number.isFinite(lng)&&Math.abs(lng)<=180;
      if(!identifier.test(id)||!identifier.test(company_id)||baseMap.has(id)||ids.has(id)||typeof name!=='string'||!name.trim()||name.length>2000||![city,country].every(t=>typeof t==='string'&&t.length<=2000&&(unified||t.trim()))||(!validPoint&&!(unified&&lat===null&&lng===null))||!Array.isArray(categories)||(!unified||evidenceClass==='B')&&!categories.length||categories.some(c=>typeof c!=='string'||!c.trim())||!shardPath.test(shard)||!m.shards[shard]||!D.validDate(observed)||!['source_provisional','matched_existing'].includes(identity_status)||(unified&&(!['B','C'].includes(evidenceClass)||!['source_location','company_reference'].includes(recordKind)||recordKind==='company_reference'&&validPoint)))throw new Error('Invalid indexed source-listed location.');
      const row={id,company_id,name,city,country,lat,lng,categories,capabilities:[],capability_evidence:{},relationships:[],evidence_class:unified?evidenceClass:'B',evidence_state:'unknown',coordinate_precision:validPoint?'approximate':'unverified',location_type:'uncertain',source_observed_on:observed,identity_status,detail_shard:shard,record_kind:unified?recordKind:'source_location',review_flags:transport?entry[13]:0};
      rows.push(row);ids.add(id);metadata.set(id,row);
    }
    if(rows.length!==(unified?m.counts.records:m.counts.public_locations)||m.counts.class_a!==m.baseline.eligible_ids.length||(!unified&&m.counts.class_b!==index.length)||(unified&&['A','B','C'].some(cls=>rows.filter(r=>r.evidence_class===cls).length!==m.counts['class_'+cls.toLowerCase()])))throw new Error('Catalogue counts mismatch.');
    const pending=new Map(),full=new Map(rows.filter(r=>baseMap.has(r.id)).map(r=>[r.id,r]));
    let boutiquePending;
    async function boutique(){
      const meta=m.boutique;if(!meta)return {version:1,profiles:{},summary:{}};
      if(meta.path!=='boutique.json'||!/^[a-f0-9]{64}$/.test(meta.sha256))throw new Error('Invalid boutique metadata path.');
      if(!boutiquePending)boutiquePending=(async()=>{
        const value=(await asset(fetcher,'./data/public/boutique.json',meta,10000000)).value;
        if(value?.version!==1||!value.profiles||Array.isArray(value.profiles)||Object.keys(value.profiles).length>rows.length)throw new Error('Invalid boutique research metadata.');
        const weights={animation:10,cg:10,character:20,cinematics:20,realtime:20,pipeline:10,vfx:5,previs:5};
        for(const [id,p] of Object.entries(value.profiles)){
          if(!Array.isArray(p.research_terms)||p.research_terms.length>100||p.research_terms.some(t=>typeof t!=='string'||t.length>300))throw new Error('Invalid company research terms.');
          if(!ids.has(id)||p.record_id!==id||!['name','country','region','size_claim','size_reviewed_on'].every(k=>typeof p[k]==='string')||!Number.isInteger(p.score)||p.score<0||p.score>100||!p.signals||Array.isArray(p.signals)||Object.entries(p.signals).some(([k,v])=>!Object.hasOwn(weights,k)||v!==weights[k])||Object.values(p.signals).reduce((a,b)=>a+b,0)!==p.score||p.external_support_need!=='unknown'||p.purchasing_intent!=='unknown'||p.independence!=='unknown'||!['taxonomy_lead','source_listed_research','primary_claims_reviewed'].includes(p.research_status)||!Array.isArray(p.sources)||p.sources.length>100||p.sources.some(s=>!s||typeof s.basis!=='string'||typeof s.url!=='string'||s.url&&!D.httpsURL(s.url)||s.observed_on&&!D.validDate(s.observed_on)||s.source_updated_on&&!D.validDate(s.source_updated_on)))throw new Error('Invalid advisory fit or evidence links.');
        }
        return value;
      })().catch(error=>{boutiquePending=null;throw error;});
      return boutiquePending;
    }
    async function details(id){
      if(full.has(id))return full.get(id);
      const stub=metadata.get(id);if(!stub)throw new Error(held.has(id)?'This legacy identity is retained in the research queue pending location-evidence review.':'Profile identity unavailable.');
      const key=stub.detail_shard,meta=m.shards[key];
      if(!pending.has(key))pending.set(key,(async()=>{
        const values=(await asset(fetcher,'./data/public/'+key,meta)).value;
        if(!Array.isArray(values)||values.length!==meta.records)throw new Error('Shard record count mismatch.');
        const staged=new Map();
        for(const row of values){
          if(unified)checkResearch(D,row);else checkB(D,row);const expected=metadata.get(row.id);
          if(!expected||expected.detail_shard!==key||staged.has(row.id)||['company_id','name','city','country','lat','lng','source_observed_on','identity_status',...(unified?['record_kind','evidence_class']:[])].some(f=>row[f]!==expected[f])||JSON.stringify(row.categories)!==JSON.stringify(expected.categories))throw new Error('Shard/index identity mismatch.');
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
    async function exportBundle(filtered){
      const values=await exportRows(filtered),codes=[...new Set(values.filter(r=>r.license&&r.license!=='UNSPECIFIED').flatMap(r=>r.license.split(' AND ')))];
      const texts=await Promise.all(codes.map(async code=>code+'\n'+await licence(fetcher,code+'.txt',m.licence_files?.[code+'.txt']?.sha256)));
      let notices=codes.includes('Apache-2.0')?await licence(fetcher,'Foursquare-NOTICE.txt',m.licence_files?.['Foursquare-NOTICE.txt']?.sha256):'';
      if(values.some(r=>r.license==='UNSPECIFIED'))notices+='\nSome source references have no explicit dataset redistribution licence. Retain each source-specific attribution and permission warning; factual references do not grant source-wide reuse rights. Authored descriptions and contacts omitted.';
      return {rows:values,licenseTexts:texts.join('\n\n'),notices};
    }
    return {rows,manifest:m,details,exportRows,exportBundle,boutique,researchOnly:held};
  }
  const api={load,sha,checkB,checkResearch,decodeIndex};if(typeof module!=='undefined'&&module.exports)module.exports=api;else root.MotionXCatalog=api;
})(globalThis);
