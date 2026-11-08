/* Display-only geography: source records and facility capabilities are immutable. */
(function(root){
 'use strict';
 function validate(value,rows,D){
  if(value?.version!==1||!value.company_audit||!value.references||!value.golden_reviews)throw new Error('Invalid geographic visibility metadata.');
  const byId=new Map(rows.map(r=>[r.id,r]));
  for(const [id,status] of Object.entries(value.company_audit)){const r=byId.get(id);if(!r||r.record_kind!=='company_reference'||Number.isFinite(r.lat)||Number.isFinite(r.lng)||!['company_identity_no_verified_location','source_supported_city_region','reviewed_city_reference','independently_supported_facility','identity_geography_conflict','historical_operation_review','insufficient_evidence'].includes(status))throw new Error('Geographic audit identity mismatch.');}
  if(Object.keys(value.company_audit).length!==rows.filter(r=>r.record_kind==='company_reference').length)throw new Error('Incomplete unpinned-company audit.');
  for(const [id,p] of Object.entries(value.references)){const r=byId.get(id);if(!r||r.record_kind!=='company_reference'||D.evidenceClass(r)!=='C'||r.lat!==null||r.lng!==null||p.city!==r.city||p.country!==r.country||!Number.isFinite(p.lat)||Math.abs(p.lat)>90||!Number.isFinite(p.lng)||Math.abs(p.lng)>180||!['city','region'].includes(p.precision)||p.evidence_class!=='C'||p.human_approved!==false||p.facility_verified!==false||p.coordinate_license!=='CC-BY-4.0'||![p.company_evidence,p.coordinate_source,p.license_url].every(D.httpsURL)||!D.validDate(p.observed_on)||!p.explanation||!p.attribution)throw new Error('Company reference cannot assert a verified facility or alter an original point.');}
  return value;
 }
 function viewPoints(rows,value){return rows.flatMap(r=>Number.isFinite(r.lat)&&Number.isFinite(r.lng)?[r]:value?.references[r.id]?[{...r,lat:value.references[r.id].lat,lng:value.references[r.id].lng,display_kind:'company_reference_location',display_reference:value.references[r.id]}]:[]);}
 function status(row,value){return value?.references[row.id]?'Approximate company city/region reference; original coordinates remain absent.':row.record_kind==='company_reference'?'Unlocated company reference; no supported display point.':Number.isFinite(row.lat)?'Original source point; facility precision depends on recorded evidence.':'No coordinate evidence.';}
 const api={validate,viewPoints,status};if(typeof module!=='undefined')module.exports=api;else root.MotionXGeography=api;
})(globalThis);
