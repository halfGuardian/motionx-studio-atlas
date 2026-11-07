#!/usr/bin/env python3
"""Bounded, provenance-first boutique discovery. Benchmarks are evaluation inputs only.

No crawler, publication approval, capability verification, closure inference or
CRM inference is performed. A source listing is a research observation.
"""
import argparse, copy, hashlib, html, json, re, tempfile, unicodedata
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path
from urllib.parse import urlsplit
from discovery import ROOT, read, write, digest
from validate import url_valid
from launch_readiness import records
from bulk_ingest import SHARED_HOSTS, country as country_name
from bulk_catalog import compact, sha
from unified_catalog import validate_research
from compact_index import add_transport

HOME=ROOT/'data/boutique'
SHARED=set(SHARED_HOSTS)|{'wixsite.com','wordpress.com','squarespace.com','youtube.com','vimeo.com','facebook.com','linkedin.com','instagram.com','github.com'}
DIMENSIONS={
 'animation':(10,('animation','2d','stop-motion','stop motion','motion graphics','animacion','animacao','animazione','动画','アニメーション','애니메이션')),
 'cg':(10,('3d','cg','computer animation','synthese')),
 'character':(20,('character animation','creature animation','digital human','animation de personnages','animacion de personajes')),
 'cinematics':(20,('cinematic','cinematique','ゲームシネマティクス')),
 'realtime':(20,('unreal','real-time','realtime','temps reel','tempo real')),
 'pipeline':(10,('rigging','retarget','mocap cleanup','motion editing','mocap integration','animation outsourcing','co-development')),
 'vfx':(5,('vfx','visual effects','effets visuels','efeitos visuais','efectos visuales')),
 'previs':(5,('previs','virtual production','production virtuelle','produccion virtual')),
}
NEGATIVE=('wedding','photography','videograph','dance school','yoga','3d printing')

def fold(value):
    return ' '.join(''.join(c for c in unicodedata.normalize('NFKD',str(value)).casefold() if not unicodedata.combining(c)).split())

def name_key(value):
    # Do not strip "studio" or brand words: broad token stripping joins unrelated companies.
    return re.sub(r'[^\w]+','',fold(value))

def host(url):
    return (urlsplit(url).hostname or '').lower().removeprefix('www.') if url_valid(url) else ''

def shared(h): return any(h==v or h.endswith('.'+v) for v in SHARED)

def record_host(row):
    # A source listing/parquet URL is evidence, not the company's website.
    return '' if row.get('website_kind')=='source_listing' else host(row.get('website',''))

def relevance(name,tags):
    text=fold(' '.join(tags)); title=fold(name)
    signals={key:weight for key,(weight,terms) in DIMENSIONS.items() if any(term in text for term in terms)}
    # Negative names are not a veto when specific production evidence exists.
    excluded=any(term in title for term in NEGATIVE) and not any(k in signals for k in ('cg','character','cinematics','realtime','pipeline','vfx','previs'))
    return ({} if excluded else signals),excluded

class Matcher:
    def __init__(self,rows):
        self.names=defaultdict(list);self.hosts=defaultdict(list);self.rows={r['id']:r for r in rows}
        for row in rows:
            self.names[name_key(row['name'])].append(row['id'])
            h=record_host(row)
            if h and not shared(h):self.hosts[h].append(row['id'])

    def match(self,observation):
        n=set(self.names.get(name_key(observation['name']),[]));h=host(observation['website']);d=set(self.hosts.get(h,[])) if not shared(h) else set()
        exact=n&d
        # Domain is a discovery identity signal, never automatic parent/branch identity.
        if exact:return sorted(exact), 'exact name and non-shared website domain', 'high', False
        if d:
            compatible={rid for rid in d if name_key(observation['name']) in name_key(self.rows[rid]['name']) or name_key(self.rows[rid]['name']) in name_key(observation['name'])}
            if compatible:return sorted(compatible),'domain and compatible operating name (alternate identity)','medium',False
            return sorted(d),'same domain but different operating names; brand/ownership collision','low',True
        if n:
            compatible={rid for rid in n if not observation.get('country') or not self.rows[rid].get('country') or observation['country']==self.rows[rid]['country']}
            # An exact name alone must not attach facts to a different-domain business.
            no_conflict={rid for rid in compatible if observation.get('country') and self.rows[rid].get('country')==observation['country'] and (not record_host(self.rows[rid]) or record_host(self.rows[rid])==h)}
            if no_conflict:return sorted(no_conflict),'exact name and compatible geography; website unavailable','medium',False
            return sorted(n),'name collision or different country/domain; identity review required','low',True
        return [],'no exact name or non-shared domain match in full atlas','unresolved',False

def source_inputs(home=HOME):
    registry=read(home/'sources.json');policies={s['id']:s for s in registry['sources']};observations=[];audit=[]
    for path in sorted((home/'inputs').glob('*.json')):
        data=read(path)
        if 'source_id' not in data:continue
        policy=policies.get(data['source_id'])
        if not policy or not policy['include_factual_references']:raise ValueError('unreviewed input source: '+data['source_id'])
        if data['license']!=policy['license']:raise ValueError('input licence differs from reviewed policy')
        if len(data['records'])>100000:raise ValueError('source parsing limit exceeded')
        ids=set()
        for r in data['records']:
            if r['source_record_id'] in ids:raise ValueError('duplicate source observation ID')
            ids.add(r['source_record_id'])
            original=dict(r)
            # The documented dataset stores bare domains, not URLs. Add an HTTPS
            # scheme for navigation without claiming that the target was fetched.
            site=r.get('website','')
            if site and '://' not in site:site='https://'+site
            if site.startswith('http://'):site='https://'+site[7:]
            if not url_valid(site) or not url_valid(r.get('source_url')):raise ValueError('unsafe source/website URL')
            if set(r)-{'source_record_id','name','website','city','country','region','source_kind','size_claim','animation_types','source_url','source_updated_on','observed_on','identity_review_reason'}:raise ValueError('unsupported/private input fields')
            if r.get('identity_review_reason') and (not isinstance(r['identity_review_reason'],str) or len(r['identity_review_reason'])>500):raise ValueError('invalid identity review note')
            if not isinstance(r['animation_types'],list) or not r['name'].strip() or len(r['name'])>300:raise ValueError('invalid factual observation')
            for k in ('observed_on','source_updated_on'):
                if r.get(k) and (date.fromisoformat(r[k]).isoformat()!=r[k] or r[k]>date.today().isoformat()):raise ValueError('invalid observation/source date')
            observations.append({**r,'website':site,'country':country_name(r['country']) if r['country'] else '', 'source_id':data['source_id'],'license':data['license'],'observation_hash':digest(original)})
        audit.append({'source_id':data['source_id'],'input':path.name,'sha256':sha(path),'raw_records':len(ids),'complete':data['complete'],'source_version':data['source_version']})
    return registry,observations,audit

def region(country):
    return REGIONS.get(country,'Unknown')

_countries=read(ROOT/'data/bulk/country-codes.json')['codes']
REGIONS={_countries[code]:label for label,codes in read(HOME/'regions.json')['groups'].items() for code in codes}

def build_research(base,home=HOME):
    registry,observations,inputs=source_inputs(home);matcher=Matcher(base);policies={s['id']:s for s in registry['sources']}
    profiles={};new=[];audit=[];graph=[];groups={};group_hosts=defaultdict(list);existing=set();collisions=[]
    def profile(row,tags,source=None,size='Unknown',basis='source_listed'):
        signals,excluded=relevance(row['name'],tags)
        if not signals or excluded:return
        p=profiles.setdefault(row['id'],{'record_id':row['id'],'name':row['name'],'country':row['country'],'region':region(row['country']),'signals':{},'research_terms':[],'sources':[], 'size_claim':'Unknown','size_reviewed_on':'','independence':'unknown','external_support_need':'unknown','purchasing_intent':'unknown','research_status':'taxonomy_lead','source_supported_location':False})
        for key,value in signals.items():p['signals'][key]=max(p['signals'].get(key,0),value)
        for term in tags:
            if term not in p['research_terms']:p['research_terms'].append(term)
        if source and source not in p['sources']:p['sources'].append(source)
        # Historical advisory key: this is the source snapshot date, not a
        # fabricated human verification date. Actual observation is in sources.
        if size!='Unknown':p['size_claim']=size;p['size_reviewed_on']=source.get('source_updated_on','') if source else '';p['size_caveat']='Directory estimate, not a current independently verified headcount.'
        if basis=='official_company':p['research_status']='primary_claims_reviewed'
        elif basis!='taxonomy_lead' and p['research_status']=='taxonomy_lead':p['research_status']='source_listed_research'
        p['score']=sum(p['signals'].values());p['score_meaning']='Advisory service alignment only; no verification, buying intent or support need is inferred.'
    # Evaluate ALL records, including old Class B/C. Category-only leads remain explicitly weak.
    for row in base:
        tags=row.get('categories',[])+row.get('capabilities',[])
        profile(row,tags,{'url':row.get('evidence',''),'observed_on':row.get('source_observed_on') or row.get('verified_on',''),'basis':'existing_record_taxonomy'},basis='taxonomy_lead')
    for o in observations:
        signals,excluded=relevance(o['name'],o['animation_types']);ids,reason,confidence,conflict=matcher.match(o)
        out={'source_id':o['source_id'],'source_record_id':o['source_record_id'],'observation_hash':o['observation_hash'],'name':o['name'],'website':o['website'],'source_url':o['source_url'],'observed_on':o['observed_on'],'matched_record_ids':ids,'matching_reason':reason,'confidence':confidence,'decision':'','record_id':None}
        if o.get('identity_review_reason'):
            out.update(decision='identity_review',matching_reason=o['identity_review_reason'],confidence='low');collisions.append(out);audit.append(out);continue
        if o['source_kind']=='support_org' or excluded or not signals:
            out['decision']='irrelevant_or_insufficient_specialisation';audit.append(out);continue
        # Do not publish ambiguous name/domain collisions as an invented distinct company.
        if conflict:
            out['decision']='identity_review';collisions.append(out);audit.append(out);continue
        if ids:
            out['decision']='already_represented';out['record_id']=ids[0];existing.update(ids)
            targets=[matcher.rows[rid] for rid in ids]
        else:
            # Company identity key uses domain + normalized name, never an invented branch.
            h=host(o['website']);key=digest([o['website'] if shared(h) else h,name_key(o['name'])]);prior=groups.get(key)
            # Domain aliases can reconcile only a unique compatible name, not arbitrary brands.
            if not prior and not shared(h):
                candidates=[v for v in group_hosts[h] if name_key(v['name']) in name_key(o['name']) or name_key(o['name']) in name_key(v['name'])]
                if len(candidates)>1:
                    out.update(decision='identity_review',matching_reason='multiple new same-domain operating-name candidates',matched_record_ids=[r['id'] for r in candidates]);collisions.append(out);audit.append(out);continue
                if candidates:prior=candidates[0]
            if prior:
                row=prior;out['decision']='repeat_source_reference';out['matching_reason']='same new company reference; original observations retained'
            else:
                pol=policies[o['source_id']];rid='boutique-'+key[:28]
                row={'id':rid,'company_id':'boutique-org-'+key[:24],'name':o['name'],'city':o['city'],'country':o['country'],'lat':None,'lng':None,'website':o['website'],'website_kind':'official','categories':['Animation'] if any(k in signals for k in ('animation','cg','character')) else ['VFX'] if 'vfx' in signals else ['Cinematics'], 'capabilities':[],'capability_evidence':{},'evidence_state':'unknown','evidence_class':'C','verified_on':'','source_observed_on':o['observed_on'],'evidence':o['source_url'],'coordinate_precision':'unverified','coordinate_source':o['source_url'],'location_type':'uncertain','relationships':[],'record_kind':'company_reference','identity_status':'source_provisional','status':'Source-supported company reference. Current physical branches, ownership and site-specific services require review; no map pin is invented.','license':o['license'],'attribution':pol['attribution'],'research_reasons':['Company-level evidence, not an approved physical facility.','No source-wide redistribution grant recorded; minimal factual references only.' if o['license']=='UNSPECIFIED' else 'CC BY 4.0 factual projection; source size/style assertions require corroboration.'],'potential_duplicates':[],'source_status':'not independently established','source_type':'boutique discovery reference','source_category':','.join(o['animation_types']),'source_release':o['observation_hash'],'source_provenance':[{'source_id':o['source_id'],'source_record_id':o['source_record_id'],'url':o['source_url'],'license':o['license'],'license_url':pol['license_url'] if o['license']!='UNSPECIFIED' else o['source_url'],'observed_on':o['observed_on'],'observation_hash':o['observation_hash']}]}
                groups[key]=row;group_hosts[h].append(row);new.append(row);out['decision']='new_company_reference'
            out['record_id']=row['id'];targets=[row]
        for row in targets:
            profile(row,o['animation_types'],{'url':o['source_url'],'observed_on':o['observed_on'],'source_updated_on':o['source_updated_on'],'basis':o['source_kind']},o['size_claim'],o['source_kind'])
            graph.append({'from':row['id'],'to':'page:'+digest(o['source_url'])[:24] if o['source_kind']=='official_company' else 'source:'+o['source_id'],'type':'event_participation' if o['source_kind']=='event_participant' else 'official_company_reference' if o['source_kind']=='official_company' else 'source_co_listing','source_url':o['source_url'],'observed_on':o['observed_on'],'meaning':'Discovery signal only; no collaboration, ownership, customer relationship or current branch is inferred.'})
        audit.append(out)
    # Enrichment cannot add a candidate. It is not used by the acquisition/matching loop.
    all_matcher=Matcher(base+new)
    for e in read(home/'inputs/enrichment.json')['records']:
        ids,_,_,conflict=all_matcher.match(e)
        if conflict:continue
        for rid in ids:
            for url in e['evidence']:profile(all_matcher.rows[rid],e['claims'],{'url':url,'observed_on':read(home/'inputs/enrichment.json')['observed_on'],'basis':'official_company'},basis='official_company')
    errors=validate_research(new)
    if errors:raise ValueError(str(errors[:10]))
    counts=Counter(a['decision'] for a in audit)
    summary={'existing_catalogue_records_examined':len(base),'raw_source_rows':len(observations),'decisions':dict(counts),'existing_relevant_record_ids':len(existing),'new_unique_company_references':len(new),'new_confirmed_operating_locations':0,'new_verified_capture_claims':0,'qualifying_research_records':len(profiles),'advisory_alignment_40_plus':sum(p['score']>=40 for p in profiles.values()),'source_supported_reference_profiles':sum(p['research_status']!='taxonomy_lead' for p in profiles.values()),'taxonomy_only_leads':sum(p['research_status']=='taxonomy_lead' for p in profiles.values()),'unique_provisional_or_operating_identity_keys':len({r['company_id'] for r in base+new if r['id'] in profiles}),'countries_with_new_references':len({r['country'] for r in new if r['country']}),'publication_approved':False,'human_reviewed_precision_sample':None,'limitations':['Reference benchmark is retrospective and has source overlap; held-out entities are not a blind global sample.','Size/independence are not uniformly corroborated. Relevant service evidence does not prove independent SME status.','All additions are Class C company references; zero new facility geocodes or capture-stage claims.','Taxonomy-only candidates are weak leads, not confirmed boutique companies.','Unknown source reuse terms remain visible; automatic collection stays disabled for unresolved sources.']}
    source_yields={sid:dict(Counter(a['decision'] for a in audit if a['source_id']==sid)) for sid in policies}
    summary['regions']=dict(Counter(p['region'] for p in profiles.values()))
    summary['source_supported_regions']=dict(Counter(p['region'] for p in profiles.values() if p['research_status']!='taxonomy_lead'))
    summary['specialisation_signals']={k:sum(k in p['signals'] for p in profiles.values()) for k in DIMENSIONS}
    summary['unknown_size_records']=sum(p['size_claim']=='Unknown' for p in profiles.values())
    summary['new_source_listed_class_b_locations']=0
    summary['unresolved_identity_observations']=len(collisions)
    return {'version':1,'input_audit':inputs,'source_registry_hash':digest(registry),'summary':summary,'source_yields':source_yields,'audit':audit,'profiles':dict(sorted(profiles.items())),'graph':graph,'proposed_references':new}

def evaluate(report,all_rows,home=HOME):
    matcher=Matcher(all_rows);results={}
    freeze=read(home/'benchmarks/freeze.json')
    for name in ('development','held-out'):
        path=home/'benchmarks'/f'{name}.json'
        if sha(path)!=freeze['files'][path.name]:raise ValueError('benchmark freeze hash changed')
        output=[]
        for b in read(path)['records']:
            ids,reason,confidence,conflict=matcher.match({'name':b['name'],'website':'https://'+b['domain']+'/','country':b['country']})
            visible=[rid for rid in ids if rid in report['profiles']]
            status='unrelated_or_misleading' if conflict else 'discovered_correctly' if visible and reason.startswith('exact name') else 'alternate_identity' if visible else 'missing'
            output.append({**b,'status':status,'record_ids':ids,'research_visible_ids':visible,'reason':reason if visible or conflict else 'No qualifying research-visible match; source coverage or specialisation evidence gap.','confidence':confidence})
        counts=Counter(r['status'] for r in output);found=counts['discovered_correctly']+counts['alternate_identity']
        results[name]={'total':len(output),'found':found,'recall':round(found/len(output),4),'statuses':dict(counts),'entries':output}
    return {'method':read(home/'benchmarks/development.json')['method'],'splits':results,'target_recall':1.0,'approval_granted':False}

def extend(public,base_path,home=HOME):
    """Append references to an exactly reproduced v1.1 catalogue. Never rewrite old shards."""
    public=Path(public);m,base=records(public,base_path);report=build_research(base,home);new=report['proposed_references'];old_index=read(public/'index.json');index=list(old_index)
    existing_ids={b['id'] for b in base}
    if any(r['id'] in existing_ids for r in new):raise ValueError('new ID collides with retained catalogue')
    for offset in range(0,len(new),500):
        chunk=sorted(new,key=lambda r:r['id'])[offset:offset+500];name=f'shards/{digest("boutique-v12")[:12]}-{offset//500:03d}.json'
        if (public/name).exists():raise ValueError('extension already applied; rebuild from baseline for idempotent application')
        compact(public/name,chunk);m['shards'][name]={'sha256':sha(public/name),'gzip_sha256':sha(public/(name+'.gz')),'gzip_bytes':(public/(name+'.gz')).stat().st_size,'records':len(chunk),'country':'Multiple / unresolved','bytes':(public/name).stat().st_size}
        for r in chunk:index.append([r[k] for k in ('id','company_id','name','city','country','lat','lng','categories')]+[name,r['source_observed_on'],r['identity_status'],r['evidence_class'],r['record_kind']])
    index.sort(key=lambda r:r[0]);compact(public/'index.json',index)
    m['index'].update(sha256=sha(public/'index.json'),gzip_sha256=sha(public/'index.json.gz'),gzip_bytes=(public/'index.json.gz').stat().st_size,records=len(index),bytes=(public/'index.json').stat().st_size)
    for k in ('records','public_records','class_c','company_references'):m['counts'][k]+=len(new)
    m['counts']['countries']=len({r['country'] for r in base+new if r['country']});m['counts']['source_identities']=len({r['company_id'] for r in base+new if r['record_kind']!='retained_location'})
    m['warnings']['boutique_company_references_requiring_review']=len(new)
    m['warnings']['unspecified_company_source_terms']+=sum(r['license']=='UNSPECIFIED' for r in new)
    m['warnings']['company_references_without_coordinates']+=len(new);m['warnings']['unreviewed_new_references']+=len(new)
    m['licence_files']={p.name:{'sha256':sha(p)} for p in sorted((ROOT/'data/bulk/LICENSES').glob('*.txt'))}
    add_transport(public,base_path,m,index,[r for r in base+new if r['record_kind']!='retained_location'])
    compact(public/'boutique.json',{'version':1,'profiles':report['profiles'],'summary':report['summary']})
    m['boutique']={'path':'boutique.json','sha256':sha(public/'boutique.json'),'gzip_sha256':sha(public/'boutique.json.gz'),'gzip_bytes':(public/'boutique.json.gz').stat().st_size,'content_addressed':True}
    write(public/'manifest.json',m)
    report['evaluation']=evaluate(report,base+new,home);report['final_catalogue_counts']=m['counts'];report['retained_catalogue_records_preserved']=len(base);report['new_record_hashes']={r['id']:digest(r) for r in new}
    return report

def save_reports(report,output):
    output=Path(output);output.mkdir(parents=True,exist_ok=True)
    write(output/'triage.json',{k:v for k,v in report.items() if k not in ('profiles','proposed_references','graph')})
    write(output/'graph.json',{'version':1,'edges':report['graph'],'policy':'Bounded source membership/event signals, not inferred ownership or customer relationships.'})
    write(output/'proposals.json',{'approval_granted':False,'canonical_updates':[],'company_references':report['proposed_references']})
    write(output/'benchmark-results.json',report['evaluation'])
    sample=sorted(report['proposed_references'],key=lambda r:hashlib.sha256(r['id'].encode()).hexdigest())[:25]
    write(output/'precision-review.json',{'method':'Deterministic 25-record worksheet for primary-source review. A generated worksheet is not a completed human review or publication approval.','human_reviewed':0,'false_positive_rate':None,'records':[{'record_id':r['id'],'name':r['name'],'website':r['website'],'source_url':r['evidence'],'observed_on':r['source_observed_on'],'review_status':'pending_human_review','decision':None,'reason':None} for r in sample]})
    esc=html.escape
    rows=''.join('<tr><td>'+esc(a['name'])+'</td><td>'+esc(a['decision'])+'</td><td>'+esc(a['matching_reason'])+'</td><td><a rel="noopener noreferrer" href="'+esc(a['source_url'],quote=True)+'">Evidence</a> · '+esc(a['observed_on'])+'</td></tr>' for a in report['audit'])
    page='<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>MotionX boutique research review</title><style>body{background:#0c1420;color:#eef4fb;font:15px/1.6 system-ui;max-width:1200px;margin:auto;padding:20px}a{color:#a9d7ff}table{width:100%;border-collapse:collapse}td,th{border:1px solid #42546a;padding:8px;text-align:left;overflow-wrap:anywhere}pre{white-space:pre-wrap}a:focus-visible{outline:3px solid #ffd875}@media(max-width:650px){table,tbody,tr,td{display:block}thead{display:none}}</style><h1>Boutique discovery review</h1><p>Advisory research, not human publication approval. No new facility or capture-stage claim is approved. <a href="../../../index.html">Open atlas</a></p><h2>Coverage</h2><pre>'+esc(json.dumps(report['summary'],indent=2))+'</pre><h2>Evaluation</h2><pre>'+esc(json.dumps({k:{s:v for s,v in val.items() if s!="entries"} for k,val in report['evaluation']['splits'].items()},indent=2))+'</pre><p>'+esc(report['evaluation']['method'])+'</p><h2>Every source observation</h2><table><thead><tr><th>Company</th><th>Decision</th><th>Identity reasoning</th><th>Source and review date</th></tr></thead><tbody>'+rows+'</tbody></table></html>'
    (output/'review.html').write_text(page,encoding='utf-8')

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('command',choices=('preview','check'));p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    m,all_rows=records(ROOT/'data/public',ROOT/'studios.json');base=[r for r in all_rows if not r['id'].startswith('boutique-')];report=build_research(base);report['evaluation']=evaluate(report,base+report['proposed_references']);report['final_catalogue_counts']=m['counts'];report['retained_catalogue_records_preserved']=len(base);report['new_record_hashes']={r['id']:digest(r) for r in report['proposed_references']}
    if a.command=='check':
        with tempfile.TemporaryDirectory() as tmp:
            save_reports(report,Path(tmp))
            for path in Path(tmp).iterdir():
                if not (a.output/path.name).exists() or path.read_bytes()!=(a.output/path.name).read_bytes():raise ValueError('stale boutique report: '+path.name)
    else:save_reports(report,a.output)
    print(json.dumps(report['summary'],indent=2))
if __name__=='__main__':main()
