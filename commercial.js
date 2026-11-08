/* Owner-defined audience eligibility. Never changes facility capabilities. */
(function(root){
 'use strict';
 const roles=['potential_client','service_provider','both','plausible_unconfirmed','adjacent_uncertain','out_of_scope'];
 function validate(p,rows,D){
  const ids=new Set(rows.map(r=>r.id)),byId=new Map(rows.map(r=>[r.id,r]));
  if(p?.version!==2||p.baseline_records!==rows.length||p.human_approved!==false||p.purchasing_intent!=='unknown'||!D.validDate(p.reviewed_on)||!p.overrides||Array.isArray(p.overrides)||Object.keys(p.overrides).length>rows.length||!p.groups||!p.labels||roles.some(r=>typeof p.labels[r]!=='string')||['games','production','publishing','visual','technical'].some(g=>!Array.isArray(p.groups[g])||p.groups[g].length>100||p.groups[g].some(s=>typeof s!=='string'||!s.trim())))throw new Error('Invalid commercial scope policy.');
  for(const [id,r] of Object.entries(p.overrides))if(!ids.has(id)||r.record_id!==id||r.name!==byId.get(id).name||!roles.includes(r.role)||typeof r.excluded!=='boolean'||r.excluded!==(r.role==='out_of_scope')||r.basis!=='individual_service_review'||r.human_approved!==false||r.facility_verified!==false||r.automatic_collection!==false||!D.validDate(r.reviewed_on)||!r.reason||!Array.isArray(r.evidence)||!r.evidence.length||r.evidence.some(u=>!D.httpsURL(u)))throw new Error('Invalid reversible scope exclusion.');
  return p;
 }
 function classify(row,p){
  if(!p)return {role:'adjacent_uncertain',excluded:false,basis:'scope_policy_unavailable',confidence:'unresolved',reason:'Owner scope policy is not configured for this catalogue.',evidence:[]};
  if(p.overrides[row.id])return p.overrides[row.id];
  const has=g=>p.groups[g].some(c=>row.categories.includes(c)),client=has('games')||has('visual'),plausible=has('production')||has('publishing'),technical=has('technical');
  const role=client&&technical?'both':client?'potential_client':technical?'service_provider':plausible?'plausible_unconfirmed':'adjacent_uncertain';
  return {role,excluded:false,basis:role==='plausible_unconfirmed'?'broad_production_listing':'explicit_sector_eligibility',confidence:role==='plausible_unconfirmed'?'plausible_sector_only':role==='adjacent_uncertain'?'insufficient_relevance_evidence':'explicit_sector_eligibility',reason:'Recorded sectors support owner-defined audience eligibility only; operation, service availability and purchasing intent are not established.',evidence:[],human_approved:false,facility_verified:false};
 }
 function matches(assessment,role,scope='public'){
  if(scope==='excluded'&&!assessment.excluded||scope!=='all'&&scope!=='excluded'&&assessment.excluded)return false;
  return !role||(role==='client'?['potential_client','both'].includes(assessment.role):role==='provider'?['service_provider','both'].includes(assessment.role):assessment.role===role);
 }
 function exportFields(row,p){const a=classify(row,p);return {...row,commercial_role:a.role,directory_scope:a.excluded?'excluded_audio_only':'eligible_or_uncertain',commercial_basis:a.basis,commercial_confidence:a.confidence,commercial_reason:a.reason,commercial_evidence:a.evidence};}
 const api={validate,classify,matches,exportFields,roles};if(typeof module!=='undefined'&&module.exports)module.exports=api;else root.MotionXCommercial=api;
})(typeof globalThis!=='undefined'?globalThis:this);
