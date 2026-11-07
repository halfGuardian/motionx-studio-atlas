'use strict';
const test=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
const root=path.resolve(__dirname,'..'),home=path.join(root,'data/boutique'),read=p=>JSON.parse(fs.readFileSync(p,'utf8'));
const source=read(path.join(home,'inputs/nzfc-facilities.json'));
const triage=read(path.join(home,'reports/triage.json'));
const report=fs.readFileSync(path.join(home,'reports/nzfc-coverage.html'),'utf8');
const escapeHtml=s=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
// Frozen primary-source listing observed 2026-11-07; this independent snapshot
// catches accidental omission of a listed vendor in future source/data revisions.
const expectedNames=[
  "37Degrees Studio",
  "808 Ltd",
  "Albedo",
  "Animation Research Ltd",
  "Bespoke Post",
  "Blockhead",
  "Cause and FX",
  "Cirkus",
  "Deep Animation",
  "Department of Post",
  "Envy Studios",
  "Fathom",
  "Final Boss VFX",
  "Floating Rock",
  "Flux Animation",
  "Franklin Rd Music & Sound",
  "Images & Sound",
  "Jon Online",
  "Masters of Reality",
  "Mechanic Animation",
  "Method",
  "Mukpuddy Animation Ltd",
  "Native Audio",
  "Natural History New Zealand",
  "OHUfx",
  "Park Road Post Production",
  "Perceptual Engineering",
  "Pinnacle Post",
  "Pixie Post",
  "POW Studios",
  "PRPVFX",
  "Sauce FX Studios",
  "Studio Local",
  "Teaspoon Films",
  "The Inside Track",
  "The Rebel Fleet",
  "The Soundroom",
  "Toybox",
  "Undercover Media",
  "Vinewood Animation",
  "Wētā FX",
  "Yukfoo"
];
test('NZFC source snapshot retains every one of the 42 reviewed vendors',()=>{
  const actual=source.records.map(r=>r.name);
  assert.deepEqual(actual,expectedNames);
  assert.equal(new Set(source.records.map(r=>r.source_record_id)).size,42);
  assert.equal(source.complete,true);
});
test('every NZFC listing is reconciled, including excluded and identity-held names',()=>{
  const audit=triage.audit.filter(a=>a.source_id==='nzfc-facilities'),byId=new Map(audit.map(a=>[a.source_record_id,a]));
  assert.equal(audit.length,42);
  assert.equal(byId.size,42);
  const counts=Object.create(null);
  for(const row of source.records){
    const decision=byId.get(row.source_record_id);
    assert.ok(decision,'Unreconciled source record '+row.name);
    assert.equal(decision.name,row.name);
    assert.ok(decision.matching_reason);
    counts[decision.decision]=(counts[decision.decision]||0)+1;
    assert.ok(report.includes(escapeHtml(row.name)),'Missing from public source audit: '+row.name);
  }
  assert.equal(counts.new_company_reference,27);
  assert.equal(counts.repeat_source_reference,3);
  assert.equal(counts.already_represented,2);
  assert.equal(counts.identity_review,1);
  assert.equal(counts.irrelevant_or_insufficient_specialisation,9);
  assert.equal((report.match(/<tr data-outcome=/g)||[]).length,42);
  assert.match(report,/42 \/ 42/);
  assert.match(report,/<b>0<\/b><small>New verified facility pins<\/small>/);
});
test('full NZFC PP/A/VFX/S/DIT labels survive independently of reduced boutique tags',()=>{
  const snapshot=read(path.join(root,'data/coverage/nzfc-2026-11-07.json'));
  assert.equal(snapshot.observed_on,'2026-11-07');
  assert.deepEqual(snapshot.records.map(r=>r.name),expectedNames);
  const byName=new Map(snapshot.records.map(r=>[r.name,r.nzfc_service_codes]));
  assert.deepEqual(byName.get('Blockhead'),['PP','A']);
  assert.deepEqual(byName.get('POW Studios'),['PP','S','A','VFX']);
  assert.deepEqual(byName.get('Images & Sound'),['PP','S','VFX','DIT']);
  for(const row of snapshot.records){
    assert.ok(row.nzfc_service_codes.length>0);
    const reportLine=report.split('\\n').find(line=>line.includes('<th scope="row">'+escapeHtml(row.name)+'</th>'));
    assert.ok(reportLine&&reportLine.includes('<td>'+row.nzfc_service_codes.join(' · ')+'</td>'),'Missing complete directory categories for '+row.name);
  }
});
test('represented NZFC names are real Atlas records; no company-only map pins invented',()=>{
  const index=read(path.join(root,'data/public/index.json'));
  const lookup=new Map(index.map(row=>[row[0],row]));
  const retained=new Map(read(path.join(root,'studios.json')).map(row=>[row.id,row]));
  const audit=triage.audit.filter(a=>a.source_id==='nzfc-facilities');
  for(const row of audit){
    if(row.decision==='identity_review'||row.decision==='irrelevant_or_insufficient_specialisation'){
      assert.equal(row.record_id,null,'Held/excluded reference must not silently publish '+row.name);
      continue;
    }
    assert.ok(row.record_id,'Missing represented identity for '+row.name);
    const item=lookup.get(row.record_id);
    assert.ok(item||retained.has(row.record_id),'Missing catalogue or retained baseline record for '+row.name);
    if(['new_company_reference','repeat_source_reference'].includes(row.decision)){
      assert.equal(item[5],null,'Unverified company cannot receive an invented map latitude');
      assert.equal(item[6],null,'Unverified company cannot receive an invented map longitude');
      assert.equal(item[12],'company_reference','Must remain a company, not a facility');
    }
  }
});
test('NZFC Weta resolves to Wellington in the coverage report; Blockhead remains held',()=>{
  const weta=triage.audit.find(a=>a.source_id==='nzfc-facilities'&&a.name==='Wētā FX');
  assert.ok(weta.matched_record_ids.includes('weta-fx-wellington'));
  assert.ok(report.includes('../../../index.html#/location/weta-fx-wellington'));
  const blockhead=triage.audit.find(a=>a.source_id==='nzfc-facilities'&&a.name==='Blockhead');
  assert.equal(blockhead.decision,'identity_review');
  assert.match(blockhead.matching_reason,/Assembly/);
});
test('Atlas reveals unmapped records explicitly and links the complete NZFC crosscheck',()=>{
  const html=fs.readFileSync(path.join(root,'index.html'),'utf8'),app=fs.readFileSync(path.join(root,'app.js'),'utf8');
  assert.match(html,/nzfc-coverage.html/);
  assert.match(html,/id="unmappedCount"/);
  assert.match(html,/id="browseUnmapped"/);
  assert.match(app,/matches.length-points.length/);
  assert.match(app,/browseUnmapped/);
  assert.match(app,/motionx_atlas_filtered_v1.3.csv/);
});
