"""Lossless transport for the public search index; never changes record identity."""
import base64, gzip, io, json, re
from pathlib import Path
from bulk_catalog import compact, sha

ENCODING = 'motionx-columnar-v1'
TABLE_COLUMNS = (3, 4, 7, 8, 9, 10, 11, 12)

def short_id(value):
    match = re.fullmatch(r'overture-([a-f0-9]{8})-([a-f0-9]{4})-([a-f0-9]{4})-([a-f0-9]{4})-([a-f0-9]{12})', value)
    if match:
        return '~u' + base64.b64encode(bytes.fromhex(''.join(match.groups()))).decode().rstrip('=')
    for prefix, code in (('overture-org-', '~o'), ('gamedb-org-', '~g'), ('gamedb-', '~c')):
        suffix = value.removeprefix(prefix)
        if value.startswith(prefix) and re.fullmatch(r'[a-f0-9]{24}' if code != '~c' else r'[a-f0-9]{28}', suffix):
            return code + base64.b64encode(bytes.fromhex(suffix)).decode().rstrip('=')
    return value

def full_id(value):
    if not value.startswith('~'):
        return value
    raw = base64.b64decode(value[2:] + '=' * (-len(value[2:]) % 4), validate=True).hex()
    if value[:2] == '~u' and len(raw) == 32:
        return 'overture-' + '-'.join((raw[:8], raw[8:12], raw[12:16], raw[16:20], raw[20:]))
    prefix = {'~o': 'overture-org-', '~g': 'gamedb-org-', '~c': 'gamedb-'}.get(value[:2])
    if not prefix or len(raw) != (28 if value[:2] == '~c' else 24):
        raise ValueError('invalid packed identity')
    return prefix + raw

def review_flags(row):
    """Advisory routing only. No score or bit grants verification or approval."""
    flags = 1 if row.get('potential_duplicates') else 0
    if row.get('source_status') in ('permanently_closed', 'temporarily_closed', 'Closed', 'Acquired'): flags |= 2
    if not row.get('city') or not row.get('country') or row.get('lat') is None: flags |= 4
    if row.get('license') == 'UNSPECIFIED' or any('redistribution' in reason for reason in row.get('research_reasons', [])): flags |= 8
    if not any(e.get('state') == 'confirmed' for e in row.get('capability_evidence', {}).values()): flags |= 16
    return flags

def pack(index, flags=None):
    ordered = sorted(index, key=lambda r: (r[4], r[3], r[2], r[0]))
    rows = [[short_id(v) if i < 2 else v for i, v in enumerate(row)] + [(flags or {}).get(row[0], 0)] for row in ordered]
    columns = list(map(list, zip(*rows))) if rows else [[] for _ in range(14)]
    tables = {}
    for k in TABLE_COLUMNS:
        lookup, values, codes = {}, [], []
        for value in columns[k]:
            key = json.dumps(value, ensure_ascii=False, separators=(',', ':'))
            if key not in lookup:
                lookup[key] = len(values); values.append(value)
            codes.append(lookup[key])
        tables[str(k)] = values; columns[k] = codes
    return {'encoding': ENCODING, 'rows': len(rows), 'tables': tables, 'columns': columns}

def unpack(value):
    if value.get('encoding') != ENCODING or len(value['columns']) != 14 or any(len(c) != value['rows'] for c in value['columns']):
        raise ValueError('invalid columnar index')
    rows = []
    for number in range(value['rows']):
        row = [value['tables'][str(k)][c[number]] if str(k) in value['tables'] else c[number] for k, c in enumerate(value['columns'])]
        row[:2] = [full_id(v) for v in row[:2]]; rows.append(row)
    return rows

def add_transport(output, baseline, manifest, index, records):
    """Add transport files without changing original index, details or baseline."""
    output, baseline = Path(output), Path(baseline)
    packed = pack(index, {r['id']: review_flags(r) for r in records})
    if sorted((r[:13] for r in unpack(packed)), key=lambda r:r[0]) != sorted(index, key=lambda r:r[0]):
        raise ValueError('lossless index round-trip failed')
    path = output/'index.compact.json'; compact(path, packed)
    manifest['index']['compact'] = {'path': path.name, 'encoding': ENCODING, 'records': len(index), 'sha256': sha(path), 'gzip_sha256': sha(output/(path.name+'.gz')), 'bytes': path.stat().st_size, 'gzip_bytes': (output/(path.name+'.gz')).stat().st_size, 'content_addressed': True}
    raw = baseline.read_bytes(); (output/'baseline.json').write_bytes(raw)
    buffer=io.BytesIO()
    with gzip.GzipFile(filename='',fileobj=buffer,mode='wb',mtime=0) as stream:stream.write(raw)
    (output/'baseline.json.gz').write_bytes(buffer.getvalue())
    manifest['baseline']['compressed'] = {'path': 'baseline.json', 'sha256': sha(baseline), 'gzip_sha256': sha(output/'baseline.json.gz'), 'bytes': len(raw), 'gzip_bytes': (output/'baseline.json.gz').stat().st_size, 'content_addressed': True}
    return manifest
