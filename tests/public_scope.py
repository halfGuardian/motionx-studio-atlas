"""Expected normal-directory counts, separate from preserved storage counts."""
import json
def visible_counts(root,counts):
    result=dict(counts);path=root/'data/public/commercial.json'
    if not path.exists():return result
    policy=json.loads(path.read_text());excluded={rid for rid,r in policy['overrides'].items() if r['excluded']}
    index=json.loads((root/'data/public/index.json').read_text())
    for r in index:
        if r[0] not in excluded:continue
        for field in ('records','class_'+r[11].lower(),'company_references' if r[12]=='company_reference' else 'source_location_observations'):
            result[field]-=1
    return result
