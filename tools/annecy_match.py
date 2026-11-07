"""Company-level identity reconciliation; source matches never prove a branch.

Legal suffixes and supported canonical operating names are search keys. Fuzzy
results and uploaded alias hints remain review leads, never automatic merges.
"""
import difflib,re
from collections import defaultdict
from boutique import fold,host,record_host,shared
from bulk_ingest import country

LEGAL=re.compile(r'(?:\s+(?:co|ltd|limited|inc|incorporated|llc|gmbh|srl|sas|sasu|sarl|spa|sa|pty|sdn|bhd|uab|ou|kft|sac|corp|corporation|sl|spzoo|sp\s+z\s+o\s+o|d\s+o\s+o))+$')

def key(value):
    words=re.sub(r'[^\w]+',' ',fold(value)).strip()
    # Dotted legal suffixes are whole terminal tokens, never brand substrings.
    words=re.sub(r'\bs r l$', 'srl', words);words=re.sub(r'\bs a r l$', 'sarl', words)
    words=LEGAL.sub('',words)
    return re.sub(r'[^\w]','',words)

def place(value):
    aliases={'hong kong':'Hong Kong SAR China','usa':'United States','united states of america':'United States','czech republic':'Czechia','ivory coast':'Côte d’Ivoire','turkey':'Türkiye','russian federation':'Russia','korea, republic of':'South Korea'}
    return aliases.get(fold(value),country(value)) if value else ''

class IdentityIndex:
    def __init__(self,rows):
        self.rows={r['id']:r for r in rows};self.names=defaultdict(set);self.domains=defaultdict(set);self.tokens=defaultdict(set)
        for r in rows:
            names={r['name']}
            if r.get('company_name'):names.add(r['company_name'])
            if r.get('record_kind')=='retained_location':names.add(r['name'].split(' — ')[0])
            for name in names:
                self.names[key(name)].add(r['id'])
                for word in re.findall(r'\w+',fold(name)):
                    if len(word)>3:self.tokens[word].add(key(name))
            domain=record_host(r)
            if domain and not shared(domain):self.domains[domain].add(r['id'])

    def match(self,name,listed_country,website='',aliases=()):
        keys={key(name)}|{key(a) for a in aliases};exact=set().union(*(self.names.get(k,set()) for k in keys));h=host(website);domain=set(self.domains.get(h,set())) if h and not shared(h) else set();p=place(listed_country)
        coherent=exact&domain
        if coherent:return self.result(coherent,'name_and_domain','high','Operating-name key and non-shared website agree; no new physical branch inferred.')
        same_country={rid for rid in exact if p and place(self.rows[rid]['country'])==p}
        conflicting={rid for rid in same_country if h and record_host(self.rows[rid]) and record_host(self.rows[rid])!=h}
        compatible=same_country-conflicting
        if compatible:return self.result(compatible,'name_and_country','medium','Same operating/legal name and listed country. Official-domain/physical-branch corroboration may still be missing.')
        if exact:return self.result(exact,'identity_review','low','Name matches exist but geography or official domains conflict; no automatic merge.')
        if domain:return self.result(domain,'shared_domain_review','low','Website is represented under a different operating name. Resolve subsidiary, brand or alias before adding.')
        candidates=set()
        for word in re.findall(r'\w+',fold(name)):
            if len(word)>3:candidates.update(self.tokens.get(word,set()))
        fuzzy=[]
        for k in candidates:
            if len(k)<5:continue
            ratio=difflib.SequenceMatcher(None,key(name),k).ratio()
            if ratio>=.88:
                ids=[rid for rid in self.names[k] if p and place(self.rows[rid]['country'])==p]
                if ids:fuzzy.append((ratio,k,ids))
        fuzzy.sort(reverse=True)
        if fuzzy:return self.result({rid for _,_,ids in fuzzy[:3] for rid in ids},'possible_alias','low','Approximate same-country name similarity; requires source-backed identity review.')
        return self.result(set(),'no_match','unresolved','No exact operating/legal-name or non-shared-domain match across the full catalogue.')

    def result(self,ids,status,confidence,reason):
        ids=sorted(ids)
        return {'record_ids':ids,'company_ids':sorted({self.rows[rid]['company_id'] for rid in ids}),'match_status':status,'confidence':confidence,'reason':reason}
