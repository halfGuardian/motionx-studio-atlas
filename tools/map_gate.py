#!/usr/bin/env python3
"""Reproduce the final 182-company map gate. No discovery or publication."""
import argparse
import copy
import csv
import html
import json
import math
import tempfile
import zipfile
from collections import Counter
from datetime import date
from pathlib import Path

from discovery import ROOT, read, write, digest
from bulk_catalog import compact, sha
from launch_readiness import records
from validate import url_valid
from nz_quality_gate import csv_safe

HOME = ROOT / 'data/release-candidate/map-gate'
REVIEWED_HEAD = '29364389eb69f1da480a15b27b8c28f3bbba7923'
BASES = {'official_company_city', 'public_sector_company_location',
         'company_profile_city', 'historical_company_location',
         'indexed_company_city', 'registered_company_city',
         'metropolitan_company_city', 'industry_company_city',
         'insufficient_city_evidence'}


def actual_date(value):
    try:
        return date.fromisoformat(value).isoformat() == value and value <= date.today().isoformat()
    except (TypeError, ValueError):
        return False


def descriptor(home=HOME):
    return {'version': 1, 'reviewed_head': REVIEWED_HEAD,
            'report_path': 'data/release-candidate/map-gate/reports/dashboard.html',
            'input_hashes': {name: sha(home / 'inputs' / name) for name in
                             ('checkpoint.json', 'city-reviews.json', 'city-coordinates.json', 'gazetteer-receipt.json')},
            'human_approved': False, 'publication_approved': False}


def inputs(rows, home=HOME):
    checkpoint = read(home / 'inputs/checkpoint.json')
    if checkpoint['reviewed_head'] != REVIEWED_HEAD or checkpoint['publication_approved'] is not False:
        raise ValueError('Incorrect reviewed head or fabricated approval')
    hashes = {r['id']: digest(r) for r in sorted(rows, key=lambda r: r['id'])}
    if len(rows) != checkpoint['records'] or digest(hashes) != checkpoint['full_record_hashes_sha256']:
        raise ValueError('An original release record, identity, coordinate or evidence field changed')
    for name, expected in checkpoint['archived_files'].items():
        p = Path(name)
        if p.is_absolute() or '..' in p.parts or sha(home / 'inputs/pr19-2936438' / p) != expected:
            raise ValueError('Reviewed release history changed')
    city_input = read(home / 'inputs/city-reviews.json')
    coordinate_input = read(home / 'inputs/city-coordinates.json')
    receipt = read(home / 'inputs/gazetteer-receipt.json')
    if city_input['human_approved'] is not False or city_input['publication_approved'] is not False:
        raise ValueError('No fabricated geographic approval')
    if not actual_date(city_input['reviewed_on_utc']) or not actual_date(receipt['observed_on_utc']):
        raise ValueError('Invalid actual source review date')
    if receipt['origin_licence'] != 'CC-BY-4.0' or receipt['packaging_licence'] != 'MIT':
        raise ValueError('Coordinate rights cannot grant company-source rights')
    new = {r['id']: r for r in rows if r['id'].startswith('globalcompany-')}
    expected = {rid for rid, r in new.items() if r['city']}
    decisions = city_input['records']
    if len(new) != 182 or len(decisions) != 106 or {d['record_id'] for d in decisions} != expected:
        raise ValueError('All 106 recorded city associations must be assessed once')
    seen = set()
    for d in decisions:
        rid = d['record_id']; r = new[rid]
        fields = {'record_id', 'original_record_sha256', 'name', 'recorded_city', 'country', 'decision',
                  'reason_code', 'reason', 'evidence', 'source_support', 'confidence', 'access',
                  'reviewed_on_utc', 'precision', 'human_approved', 'facility_verified', 'current_operation'}
        if set(d) != fields or d['precision'] not in ('city', 'region') or d['confidence'] not in ('insufficient', 'historical_source_association', 'indexed_source_association', 'source_supported_company_association'):
            raise ValueError('Unsupported or private geographic review fields')
        if rid in seen or d['original_record_sha256'] != hashes[rid] or (d['name'], d['recorded_city'], d['country']) != (r['name'], r['city'], r['country']):
            raise ValueError('City-review identity or original municipality changed')
        seen.add(rid)
        if d['decision'] not in ('prepare_city_reference', 'retain_unpinned') or not d['reason'] or not d['reason_code']:
            raise ValueError('Every city needs an explicit geographic decision and reason')
        if d['human_approved'] is not False or d['facility_verified'] is not False or d['current_operation'] != 'unverified':
            raise ValueError('Company city evidence is not facility or operating verification')
        if d['source_support'] not in BASES or not actual_date(d['reviewed_on_utc']) or not d['evidence']:
            raise ValueError('Unsupported city evidence basis/date')
        for e in d['evidence']:
            if not {'url', 'basis', 'reviewed_on_utc'} <= set(e) <= {'url', 'basis', 'reviewed_on_utc', 'source_year'} or not url_valid(e['url']) or e['basis'] not in BASES or not actual_date(e['reviewed_on_utc']):
                raise ValueError('Unsafe or unrelated city evidence; agency footers are not company evidence')
            if 'source_year' in e and (type(e['source_year']) is not int or not 1900 <= e['source_year'] <= date.today().year):
                raise ValueError('Invalid historical source year')
        if d['decision'] == 'prepare_city_reference' and d['source_support'] == 'insufficient_city_evidence':
            raise ValueError('Insufficient geography cannot receive a marker')
    points = coordinate_input['points']
    for key, p in points.items():
        s = p['source_record']
        if set(s) != {'geonameid', 'name', 'latitude', 'longitude', 'countrycode', 'admin1code', 'timezone'} or type(s['geonameid']) is not int or s['geonameid'] <= 0 or p['method'] not in ('direct_geonames_public_page', 'geonamescache_3.0.2_projection'):
            raise ValueError('Invalid or private coordinate projection fields')
        if key != p['country_code'] + '/' + p['recorded_city'] or s['countrycode'] != p['country_code']:
            raise ValueError('Gazetteer country/municipality mismatch')
        if p['coordinate_license'] != 'CC-BY-4.0' or not url_valid(p['coordinate_source']) or not url_valid(p['license_url']):
            raise ValueError('Unsubstantiated coordinate licence/source')
        if any(type(s[k]) not in (float, int) or not math.isfinite(s[k]) for k in ('latitude', 'longitude')) or abs(s['latitude']) > 90 or abs(s['longitude']) > 180:
            raise ValueError('Invalid gazetteer coordinate')
        if str(s['geonameid']) not in p['coordinate_source'] or not actual_date(p['reviewed_on_utc']) or not p['selection_reason']:
            raise ValueError('Missing coordinate identity/review')
    return checkpoint, new, {d['record_id']: d for d in decisions}, points


def extend_visibility(base, rows, home=HOME):
    checkpoint, new, decisions, points = inputs(rows, home)
    before = read(home / 'inputs/pr19-2936438/data/public/visibility.json')
    if base != before:
        raise ValueError('Previously reviewed city references or geographic history changed')
    value = copy.deepcopy(base); audit = []
    reviewed_on = read(home / 'inputs/city-reviews.json')['reviewed_on_utc']
    for rid, r in sorted(new.items()):
        d = decisions.get(rid)
        prepared = d is not None and d['decision'] == 'prepare_city_reference'
        reason = d['reason'] if d else 'No city is recorded for this company. Country, event attendance or a similarly named organisation does not justify a capital, branch or map coordinate.'
        point = None
        if prepared:
            candidates = [p for p in points.values() if (p['recorded_city'], p['country']) == (r['city'], r['country'])]
            if len(candidates) != 1 or rid in value['references']:
                raise ValueError('A company needs exactly one supported municipality; never overwrite a reviewed reference')
            p = candidates[0]; s = p['source_record']
            point = {'lat': s['latitude'], 'lng': s['longitude'], 'city': r['city'], 'country': r['country'],
                     'precision': d['precision'], 'coordinate_source': p['coordinate_source'],
                     'coordinate_license': 'CC-BY-4.0', 'license_url': p['license_url'],
                     'geonameid': s['geonameid'], 'company_evidence': d['evidence'][0]['url'],
                     'company_evidence_sources': d['evidence'], 'source_support': d['source_support'],
                     'confidence': d['confidence'], 'observed_on': d['reviewed_on_utc'],
                     'evidence_class': 'C', 'human_approved': False, 'facility_verified': False,
                     'attribution': 'GeoNames, CC BY 4.0. City-reference projection via geonamescache 3.0.2 (MIT packaging notice retained), except the directly reviewed Gwacheon entry. Coordinates unchanged. Company-source rights remain UNSPECIFIED.',
                     'explanation': reason + ' Separate approximate company city/urban-area reference, not a verified studio entrance, current physical branch or confirmed facility capability. Original coordinates remain null and current operation is unverified.'}
            value['references'][rid] = point
            value['company_audit'][rid] = 'reviewed_city_reference'
        elif d:
            value['company_audit'][rid] = 'identity_geography_conflict' if d['reason_code'] in ('municipality_conflict', 'ambiguous_registry_city') else 'insufficient_evidence'
        audit.append({'record_id': rid, 'name': r['name'], 'city': r['city'], 'country': r['country'],
                      'original_record_sha256': digest(r), 'state': 'city_reference' if prepared else 'unpinned',
                      'reason_code': d['reason_code'] if d else 'no_recorded_city', 'reason': reason,
                      'evidence': d['evidence'] if d else [], 'confidence': d['confidence'] if d else 'insufficient',
                      'source_support': d['source_support'] if d else 'no_recorded_city',
                      'coordinate': point, 'reviewed_on_utc': reviewed_on,
                      'human_approved': False, 'facility_verified': False, 'current_operation': 'unverified'})
    mapped = sum(r['state'] == 'city_reference' for r in audit)
    summary = {'reviewed_head': REVIEWED_HEAD, 'admitted_companies': len(new), 'recorded_city_associations_audited': len(decisions),
               'city_associations_with_display_reference': mapped, 'city_associations_still_unpinned': len(decisions) - mapped,
               'companies_without_recorded_city': len(new) - len(decisions), 'admitted_companies_unpinned': len(new) - mapped,
               'new_display_points': mapped, 'distinct_city_country_references': len(points),
               'preserved_prior_display_points': len(before['references']) + sum(map(len, before['additional_references'].values())),
               'total_company_display_points': len(value['references']) + sum(map(len, value['additional_references'].values())),
               'unpinned_reason_counts': dict(sorted(Counter(r['reason_code'] for r in audit if r['state'] == 'unpinned').items())),
               'canonical_records_changed': 0, 'canonical_coordinates_changed': 0, 'new_confirmed_capabilities': 0,
               'human_approved': False, 'publication_approved': False}
    value['intake_map_gate'] = {r['record_id']: {k: r[k] for k in ('state', 'reason', 'reason_code', 'source_support', 'confidence', 'reviewed_on_utc')} for r in audit}
    value['intake_map_summary'] = summary
    value['summary'].update(reviewed_display_references=summary['total_company_display_points'],
                            still_without_display_reference=len(value['company_audit']) - len(value['references']),
                            geographic_dispositions=dict(sorted(Counter(value['company_audit'].values()).items())))
    # Row arrival order differs between a full replay and a loaded shard set.
    # Canonicalise object keys so both paths produce identical bytes and hashes.
    value = json.loads(json.dumps(value, ensure_ascii=False, sort_keys=True, allow_nan=False))
    return value, {'version': 1, 'summary': summary, 'records': audit, 'scope': 'Draft display-only city associations. No authorised publication, verified facility, original coordinate change or new company admission.', 'inputs': descriptor(home)}


def save(report, output):
    output = Path(output); output.mkdir(parents=True, exist_ok=True)
    write(output / 'acceptance.json', report)
    write(output / 'summary.json', report['summary'])
    with (output / 'companies.csv').open('w', encoding='utf-8', newline='') as f:
        fields = ['record_id', 'name', 'city', 'country', 'state', 'reason_code', 'reason', 'confidence', 'evidence', 'coordinate']
        w = csv.DictWriter(f, fieldnames=fields, lineterminator='\n'); w.writeheader()
        for r in report['records']:
            w.writerow({k: csv_safe(json.dumps(r[k], ensure_ascii=False) if isinstance(r[k], (dict, list)) else r[k]) for k in fields})
    esc = lambda s: html.escape(str(s), quote=True)
    cards = []
    for r in sorted(report['records'], key=lambda r: (r['state'], r['country'], r['name'])):
        links = ' · '.join('<a rel="noopener noreferrer" href="' + esc(e['url']) + '">' + esc(e['basis'].replace('_', ' ')) + '</a>' for e in r['evidence'])
        coords = '<p>GeoNames ' + esc(r['coordinate']['geonameid']) + ', CC BY 4.0 · ' + esc(r['coordinate']['precision']) + ' reference; original coordinates remain null.</p>' if r['coordinate'] else '<p>Unpinned; remains searchable in the same atlas.</p>'
        cards.append('<article data-map-review data-state="' + r['state'] + '"><h2>' + esc(r['name']) + '</h2><p>' + esc((r['city'] or 'City not recorded') + ', ' + r['country']) + '</p><p><strong>' + esc(r['state'].replace('_', ' ')) + '</strong> · ' + esc(r['confidence'].replace('_', ' ')) + '</p><p>' + esc(r['reason']) + '</p>' + coords + '<p>' + links + '</p><a href="../../../../index.html#/location/' + esc(r['record_id']) + '">Open existing company profile</a></article>')
    page = r'''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>MotionX final map acceptance</title><style>body{background:#101822;color:#edf1f8;font:16px/1.6 system-ui;max-width:1050px;margin:auto;padding:20px;overflow-wrap:anywhere}a{color:#addcff}article{border:1px solid #52617a;padding:18px;margin:18px 0;border-radius:10px}pre{white-space:pre-wrap}input,select{font:inherit;min-height:44px;max-width:100%;background:#172333;color:inherit;padding:8px;border:1px solid #8798ad}label{display:block;margin:12px 0}:focus-visible{outline:3px solid #ffd77a}[hidden]{display:none}@media(max-width:650px){body{padding:12px}}</style><h1>Final map and directory acceptance</h1><p>Every admitted company remains a provisional Class C reference. A city/urban-area point is not a studio entrance, confirmed facility capability or independent current-operation verification. No human approval is asserted.</p><nav><a href="../../../../index.html">Open atlas</a> · <a href="acceptance.json">Complete geographic audit</a> · <a href="companies.csv">All 182 decisions (CSV)</a> · <a href="../../OWNER-APPROVAL.md">Single owner decision</a></nav><pre>SUMMARY</pre><label>Find company, city or evidence<input id="mapReviewSearch" type="search"></label><label>Map status<select id="mapReviewState"><option value="">All 182 companies</option><option value="city_reference">Approximate references</option><option value="unpinned">Unpinned companies</option></select></label><p id="mapReviewCount" role="status" aria-live="polite"></p>CARDS<script>(()=>{const rows=[...document.querySelectorAll('[data-map-review]')],q=document.getElementById('mapReviewSearch'),s=document.getElementById('mapReviewState'),c=document.getElementById('mapReviewCount');function render(){const terms=q.value.normalize('NFKD').toLowerCase().trim().split(/\s+/).filter(Boolean);let n=0;for(const r of rows){r.hidden=!!(s.value&&r.dataset.state!==s.value||!terms.every(t=>r.textContent.normalize('NFKD').toLowerCase().includes(t)));if(!r.hidden)n++;}c.textContent=n+' of '+rows.length+' company decisions shown. Approval remains pending.';}q.addEventListener('input',render);s.addEventListener('change',render);render();})();</script></html>'''
    page = page.replace('SUMMARY', esc(json.dumps(report['summary'], indent=2))).replace('CARDS', ''.join(cards))
    (output / 'dashboard.html').write_text(page, encoding='utf-8')


def verify_gazetteer(wheel, home=HOME):
    receipt = read(home / 'inputs/gazetteer-receipt.json')
    if sha(wheel) != receipt['distribution_sha256']:
        raise ValueError('Wrong coordinate distribution archive')
    with zipfile.ZipFile(wheel) as z:
        raw = z.read(receipt['data_path'])
    import hashlib
    if hashlib.sha256(raw).hexdigest() != receipt['data_sha256']:
        raise ValueError('Coordinate dataset changed')
    cities = json.loads(raw); verified = 0
    for p in read(home / 'inputs/city-coordinates.json')['points'].values():
        if p['method'] != 'geonamescache_3.0.2_projection':
            continue
        s = cities[str(p['source_record']['geonameid'])]
        if digest(s) != p['source_record_sha256'] or any(s[k] != v for k, v in p['source_record'].items()):
            raise ValueError('City coordinate projection differs from the licensed source')
        verified += 1
    return {'package_coordinates_verified': verified, 'direct_geonames_entries': 1, 'distribution_sha256': receipt['distribution_sha256']}


def check(home=HOME):
    import release_candidate as rc
    m, rows = records(ROOT / 'data/public', ROOT / 'studios.json')
    checkpoint = read(home / 'inputs/checkpoint.json')
    if sha(ROOT / 'studios.json') != checkpoint['root_sha256']:
        raise ValueError('Canonical root database changed')
    for name, expected in checkpoint['unchanged_public_files'].items():
        if sha(ROOT / name) != expected:
            raise ValueError('Original public identity/index/detail data changed: ' + name)
    base, _ = rc.geography(rows, include_map_gate=False)
    value, report = extend_visibility(base, rows, home)
    if read(ROOT / 'data/public/visibility.json') != value or m['release_candidate'].get('map_acceptance_gate') != descriptor(home):
        raise ValueError('Actual atlas does not match the geographic acceptance inputs')
    with tempfile.TemporaryDirectory() as folder:
        save(report, folder)
        for p in Path(folder).iterdir():
            if p.read_bytes() != (home / 'reports' / p.name).read_bytes():
                raise ValueError('Stale final map report: ' + p.name)
    return report


def prepare(home=HOME):
    import release_candidate as rc
    public = ROOT / 'data/public'; m, rows = records(public, ROOT / 'studios.json')
    if m['release_candidate'].get('map_acceptance_gate'):
        report = check(home)
        value = read(public / 'visibility.json')
        canonical = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False) + '\n'
        if (public / 'visibility.json').read_text(encoding='utf-8') == canonical:
            return report
        # Only an already-valid projection may be normalised; no field changes.
        rc.check_data(public, ROOT / 'studios.json')
        value = json.loads(canonical)
        compact(public / 'visibility.json', value)
        m['global_visibility'].update(sha256=sha(public / 'visibility.json'), gzip_sha256=sha(public / 'visibility.json.gz'), gzip_bytes=(public / 'visibility.json.gz').stat().st_size)
        write(public / 'manifest.json', m)
        rc.save(rc.check_data(public, ROOT / 'studios.json'), ROOT / 'data/release-candidate/reports')
        return check(home)
    checkpoint = read(home / 'inputs/checkpoint.json')
    if sha(public / 'manifest.json') != checkpoint['archived_files']['data/public/manifest.json'] or sha(public / 'visibility.json') != checkpoint['archived_files']['data/public/visibility.json']:
        raise ValueError('Start from the exact reviewed PR #19 public assets')
    base, _ = rc.geography(rows, include_map_gate=False)
    value, report = extend_visibility(base, rows, home)
    compact(public / 'visibility.json', value)
    m['global_visibility'].update(sha256=sha(public / 'visibility.json'), gzip_sha256=sha(public / 'visibility.json.gz'), gzip_bytes=(public / 'visibility.json.gz').stat().st_size)
    m['release_candidate']['map_acceptance_gate'] = descriptor(home)
    write(public / 'manifest.json', m); save(report, home / 'reports')
    rc.save(rc.check_data(public, ROOT / 'studios.json'), ROOT / 'data/release-candidate/reports')
    return check(home)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=('prepare-draft', 'check', 'verify-gazetteer'))
    parser.add_argument('--wheel', type=Path)
    args = parser.parse_args()
    if args.command == 'verify-gazetteer':
        if not args.wheel:
            parser.error('--wheel is required')
        result = verify_gazetteer(args.wheel)
    else:
        result = (prepare() if args.command == 'prepare-draft' else check())['summary']
    print(json.dumps(result, indent=2))
