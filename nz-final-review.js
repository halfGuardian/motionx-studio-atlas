/* Maintainer working notes only. This page cannot approve or publish records. */
(function(root){
  'use strict';
  const decisions=new Set(['accept_provisional','existing_alias','needs_evidence','identity_conflict','out_of_scope','historical_review','rights_review']);
  function matches(text,kind,relevance,readiness,filters={}){
    return text.toLocaleLowerCase().includes((filters.query||'').trim().toLocaleLowerCase())&&(!filters.kind||kind===filters.kind)&&(!filters.relevance||relevance===filters.relevance)&&(!filters.readiness||readiness===filters.readiness);
  }
  function workingDraft(datasetHash,items){
    if(!/^[a-f0-9]{64}$/.test(datasetHash))throw new Error('Invalid review checkpoint.');
    const seen=new Set(),rows=items.map(item=>{
      if(!/^[a-z0-9-]+$/.test(item.item_id)||seen.has(item.item_id)||!/^[a-f0-9]{64}$/.test(item.content_hash)||item.decision&&!decisions.has(item.decision))throw new Error('Invalid working review item.');
      seen.add(item.item_id);
      return {item_id:item.item_id,content_hash:item.content_hash,human_decision:item.decision||null,human_notes:String(item.notes||'').slice(0,4000),human_reviewer:null,human_approved:false};
    });
    return {version:1,kind:'unauthenticated_working_draft',dataset_hash:datasetHash,human_approved:false,publication_authorised:false,instructions:'Working choices are not authenticated human review or approval. No importer accepts this draft. Review the exact PR in GitHub before authorising a merge.',items:rows};
  }
  const api={matches,workingDraft};if(typeof module!=='undefined')module.exports=api;
  if(typeof document==='undefined')return;
  const cards=[...document.querySelectorAll('#reviewCards article')],query=document.getElementById('reviewQuery'),kind=document.getElementById('reviewKind'),relevance=document.getElementById('reviewRelevance'),readiness=document.getElementById('reviewReadiness');if(!query)return;
  function filter(){let count=0;for(const card of cards){card.hidden=!matches(card.textContent,card.dataset.kind,card.dataset.relevance,card.dataset.readiness,{query:query.value,kind:kind.value,relevance:relevance.value,readiness:readiness.value});if(!card.hidden)count++;}document.getElementById('reviewCount').textContent=count+' of '+cards.length+' review items';}
  for(const control of [query,kind,relevance,readiness])control.addEventListener(control===query?'input':'change',filter);filter();
  document.getElementById('exportReview').addEventListener('click',()=>{
    const draft=workingDraft(document.getElementById('reviewCards').dataset.datasetHash,cards.map(card=>({item_id:card.dataset.item,content_hash:card.dataset.hash,decision:card.querySelector('[data-decision]').value,notes:card.querySelector('[data-notes]').value})));
    const url=URL.createObjectURL(new Blob([JSON.stringify(draft,null,2)+'\n'],{type:'application/json'})),a=document.createElement('a');a.href=url;a.download='motionx-nz-working-review.json';document.body.appendChild(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),1000);document.getElementById('reviewExportStatus').textContent='Working draft downloaded. No approval granted, no records published, and no notes sent to a server.';
  });
})(globalThis);
