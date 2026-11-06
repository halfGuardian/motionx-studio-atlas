"""Bounded, declarative location-label adapters. Extracted claims are not verified data."""
from html.parser import HTMLParser
import re
import unicodedata

CLAIMS={'Motion Capture':r'\bmotion[ -]capture\b|\bmocap\b','Performance Capture':r'\bperformance[ -]capture\b',
        'Facial Capture':r'\bfacial[ -]capture\b|\bface[ -]tracking\b','Virtual Production':r'\bvirtual[ -]production\b',
        'Volumetric Capture':r'\bvolumetric[ -]capture\b','Retargeting':r'\bretarget(?:ing|ed)?\b',
        'Motion Editing':r'\bmotion[ -]editing\b','VFX':r'\bvisual effects\b|\bvfx\b','Animation':r'\banimation\b',
        'Game Development':r'\bgame development\b|\bdevelop(?:ing|ment of) games\b','Previsualization':r'\bprevis(?:ualization)?\b'}


def norm(value):return ''.join(c for c in unicodedata.normalize('NFKD',value).casefold() if c.isalnum())


class VisibleLines(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True);self.skip=0;self.lines=[];self.chunks=[]
    def flush(self):
        value=re.sub(r'\s+',' ',''.join(self.chunks)).strip();self.chunks=[]
        if value:self.lines.append(value)
    def handle_starttag(self,tag,attrs):
        if tag in ('script','style','nav','header','footer'):self.skip+=1
        if not self.skip and tag in ('h1','h2','h3','h4','h5','h6','p','li','div','section','article','br','option'):self.flush()
    def handle_endtag(self,tag):
        if tag in ('script','style','nav','header','footer'):self.skip=max(0,self.skip-1)
        if not self.skip and tag in ('h1','h2','h3','h4','h5','h6','p','li','div','section','article','option'):self.flush()
    def handle_data(self,data):
        if not self.skip:self.chunks.append(data)


def location_labels(source,body):
    parser=VisibleLines();parser.feed(body);parser.flush()
    output=[]
    for label,place in source['place_labels'].items():
        # Exact visible labels or a single explicitly declared roster sentence are used.
        matches=[i for i,line in enumerate(parser.lines) if norm(line)==norm(label)]
        if not matches and source.get('roster_sentence_pattern'):
            matches=[i for i,line in enumerate(parser.lines) if re.search(source['roster_sentence_pattern'],line,re.I) and
                     re.search(r'(?<!\w)'+re.escape(label)+r'(?!\w)',line,re.I)]
        for position in matches[:1]:
            # Capability words must occur in this local card, not an unrelated global footer.
            following=[]
            for line in parser.lines[position+1:position+5]:
                if norm(line) in {norm(label) for label in source['place_labels']}:break
                following.append(line)
            local=' '.join(following)
            local=local[:1200]
            claims=[label for label,pattern in CLAIMS.items() if re.search(pattern,local,re.I)]
            output.append({'url':source['url'],'label':place.get('name') or label,'city':place.get('city',''),
                           'country':place.get('country',''),'unit_key':place.get('unit_key') or norm(label),
                           'observation_kind':'location_reference','claim_terms':claims,
                           'place_basis':'reviewed source-label mapping; candidate, not verified canonical data'})
    return output
