#!/usr/bin/env python3
"""Validate MotionX public location records. Python standard library only."""
import argparse
import csv
import json
import math
import ipaddress
import re
import sys
import unicodedata
from datetime import date
from pathlib import Path
from urllib.parse import urlsplit

REQUIRED = ('id', 'company_id', 'name', 'city', 'country', 'lat', 'lng',
            'website', 'evidence_state', 'coordinate_precision', 'categories',
            'capabilities', 'capability_evidence')
STATES = {'confirmed', 'likely', 'unknown'}
PRECISIONS = {'exact', 'approximate', 'city', 'region', 'unverified'}
CSV_FIELDS = ('id', 'company_id', 'name', 'city', 'country', 'lat', 'lng', 'address', 'company_name',
              'website', 'email', 'phone', 'categories', 'capabilities', 'capability_evidence',
              'evidence_state', 'evidence', 'verified_on', 'coordinate_precision', 'status', 'location_type', 'coordinate_source', 'relationships')
LOCATION_TYPES = {'production_studio', 'capture_facility', 'creative_hub', 'mixed_campus', 'production_office', 'uncertain'}
RELATION_TYPES = {'subsidiary_of', 'group_member', 'partner_of'}
ID = re.compile(r'^[a-z0-9]+(?:-[a-z0-9]+)*$')


def url_valid(value):
    try:
        u = urlsplit(value)
        hostname=(u.hostname or '').rstrip('.').casefold()
        if '\\' in value or re.fullmatch(r'(?:0x[0-9a-f]+|[0-9]+)(?:\.(?:0x[0-9a-f]+|[0-9]+))*',hostname):return False
        if hostname=='localhost' or hostname.endswith(('.localhost','.local','.internal')) or '.' not in hostname:return False
        try:
            ipaddress.ip_address(hostname)
            return False  # Public directory links use hostnames, never IP literals.
        except ValueError:pass
        if any(ord(c)<32 or ord(c)==127 for c in value) or re.search(r'[?&](?:access_token|api[_-]?key|auth|password|token)=',value,re.I):return False
        return (u.scheme == 'https' and bool(u.hostname) and not u.username
                and not u.password and not any(c.isspace() for c in value)
                and u.port != 0)
    except (ValueError, TypeError, AttributeError):
        return False


def normalized(value):
    return ''.join(c for c in unicodedata.normalize('NFKD', value).casefold()
                   if c.isalnum())


def host(url):
    if not isinstance(url, str):
        return ''
    try:
        return (urlsplit(url).hostname or '').removeprefix('www.').casefold()
    except (ValueError, TypeError):
        return ''


class DuplicateIndex:
    """Index company/name/website within a city; matches are review candidates."""
    def __init__(self, rows=()):
        self.index = {}
        for row in rows:
            self.add(row)

    @staticmethod
    def keys(row):
        if not isinstance(row, dict):
            return []
        place = (normalized(str(row.get('city', ''))), normalized(str(row.get('country', ''))))
        values = [('company/city', str(row.get('company_id', ''))),
                  ('name/city', normalized(str(row.get('name', '')))),
                  ('website/city', host(row.get('website')))]
        return [(kind, *place, value) for kind, value in values if value]

    def matches(self, row):
        found = {}
        for key in self.keys(row):
            for other in self.index.get(key, []):
                token = id(other)
                pair = found.setdefault(token, {'ids': [other.get('id'), row.get('id')], 'reasons': []})
                pair['reasons'].append(key[0])
        return list(found.values())

    def add(self, row):
        for key in self.keys(row):
            self.index.setdefault(key, []).append(row)


def possible_duplicates(rows):
    index, pairs = DuplicateIndex(), []
    for row in rows:
        pairs.extend(index.matches(row))
        index.add(row)
    return pairs


def validate(rows):
    errors, warnings, seen = [], [], set()
    company_names = {}
    if not isinstance(rows, list):
        return ['database must be a JSON array'], []
    for i, r in enumerate(rows, 1):
        if not isinstance(r, dict):
            errors.append(f'row-{i}: record must be an object')
            continue
        ref = r.get('id') or f'row-{i}'
        if 'company_name' in r:
            value = r['company_name']
            company = r.get('company_id')
            if not isinstance(value,str) or not value.strip():errors.append(f'{ref}: invalid company_name')
            elif company_names.get(company,value)!=value:errors.append(f'{ref}: conflicting operating organisation name')
            else:company_names[company]=value
        def error(message):
            errors.append(f'{ref}: {message}')
        for k in REQUIRED:
            if k not in r or r[k] is None or r[k] == '':
                error(f'missing {k}')
        for k in ('id', 'company_id'):
            if not isinstance(r.get(k), str) or not ID.fullmatch(r[k]):
                error(f'{k} must be a lowercase hyphenated identifier')
        if isinstance(ref, str):
            if ref in seen:
                error('duplicate id')
            seen.add(ref)
        for k in ('name', 'city', 'country', 'coordinate_precision', 'evidence_state'):
            if not isinstance(r.get(k), str) or not r[k].strip():
                error(f'{k} must be a nonempty string')
        for k in ('address', 'status', 'email', 'phone', 'evidence', 'verified_on'):
            if k in r and not isinstance(r[k], str):
                error(f'{k} must be a string')
        for k, limit in (('lat', 90), ('lng', 180)):
            value = r.get(k)
            if (isinstance(value, bool) or not isinstance(value, (int, float))
                    or not -limit <= value <= limit or not math.isfinite(value)):
                error(f'invalid {k}: expected finite number within +/-{limit}')
        if r.get('evidence_state') not in tuple(STATES):
            error('evidence_state must be confirmed/likely/unknown')
        if r.get('coordinate_precision') not in tuple(PRECISIONS):
            error('invalid coordinate_precision')
        for k in ('categories', 'capabilities'):
            values = r.get(k)
            if (not isinstance(values, list) or any(not isinstance(v, str) or not v.strip() for v in values)):
                error(f'{k} must be an array of nonempty strings')
            elif len(values) != len(set(values)):
                error(f'{k} contains duplicates')
        if isinstance(r.get('categories'), list) and not r['categories']:
            error('categories must contain at least one sector')
        for k in ('website', 'evidence'):
            if (k == 'website' or r.get(k)) and not url_valid(r.get(k)):
                error(f'{k} must be a valid https URL without credentials')
        if r.get('evidence_state') in ('confirmed', 'likely') and not r.get('evidence'):
            error('confirmed/likely evidence requires a source URL')
        def check_date(value, label):
            if not value:
                return
            try:
                if not isinstance(value, str) or not re.fullmatch(r'\d{4}-\d{2}-\d{2}', value):
                    raise ValueError()
                parsed = date.fromisoformat(value)
                if parsed > date.today():
                    warnings.append(f'{ref}: {label} is in the future; review')
            except (ValueError, TypeError):
                error(f'invalid {label}; use YYYY-MM-DD')
        if 'location_type' in r and r['location_type'] not in tuple(LOCATION_TYPES):
            error('invalid location_type')
        if 'coordinate_source' in r and not url_valid(r['coordinate_source']):
            error('coordinate_source must be a valid https URL')
        if 'relationships' in r:
            relations = r['relationships']
            if not isinstance(relations, list):
                error('relationships must be an array')
            else:
                relation_ids = set()
                for relation in relations:
                    if not isinstance(relation, dict):
                        error('relationship must be an object')
                        continue
                    rid = relation.get('id')
                    if not isinstance(rid, str) or not ID.fullmatch(rid) or rid == r.get('company_id'):
                        error('invalid relationship organisation id')
                    elif rid in relation_ids:
                        error('duplicate relationship organisation id')
                    else:
                        relation_ids.add(rid)
                    if relation.get('type') not in tuple(RELATION_TYPES):
                        error('invalid relationship type')
                    if not isinstance(relation.get('name'), str) or not relation['name'].strip():
                        error('relationship requires organisation name')
                    if not url_valid(relation.get('evidence')):
                        error('relationship requires https evidence')
                    if not isinstance(relation.get('verified_on'), str) or not relation['verified_on']:
                        error('relationship requires review date')
                    check_date(relation.get('verified_on'), 'relationship.verified_on')
        check_date(r.get('verified_on'), 'verified_on')
        if r.get('evidence_state') in ('confirmed', 'likely') and not r.get('verified_on'):
            error('confirmed/likely evidence requires verified_on')
        evidence = r.get('capability_evidence')
        caps = r.get('capabilities', [])
        if not isinstance(evidence, dict):
            error('capability_evidence must be an object keyed by capability')
        elif isinstance(caps, list) and all(isinstance(c, str) for c in caps):
            if set(evidence) != set(caps):
                error('capability_evidence keys must match capabilities')
            for cap, item in evidence.items():
                if not isinstance(item, dict):
                    error(f'{cap}: capability evidence must be an object')
                    continue
                for field in ('evidence', 'verified_on'):
                    if field in item and not isinstance(item[field], str):
                        error(f'{cap}: {field} must be a string')
                if item.get('state') not in tuple(STATES):
                    error(f'{cap}: invalid capability evidence state')
                if item.get('evidence') and not url_valid(item['evidence']):
                    error(f'{cap}: invalid evidence URL')
                check_date(item.get('verified_on'), f'{cap}.verified_on')
                if item.get('state') in ('confirmed', 'likely') and (not item.get('evidence') or not item.get('verified_on')):
                    error(f'{cap}: confirmed/likely requires evidence and verified_on')
        if r.get('coordinate_precision') != 'exact':
            warnings.append(f'{ref}: approximate coordinates ({r.get("coordinate_precision")}); not a verified street address')
        elif not r.get('address') or not r.get('evidence') or not r.get('verified_on'):
            error('exact coordinates require address, evidence and verified_on')
        if r.get('evidence_state') == 'unknown':
            warnings.append(f'{ref}: legacy/unreviewed evidence; source presence is not independent verification')
    for pair in possible_duplicates(rows):
        warnings.append(f'possible duplicate: {pair["ids"]} ({", ".join(pair["reasons"])})')
    return errors, warnings


def read_records(path):
    path = Path(path)
    if path.suffix.lower() != '.csv':
        return json.loads(path.read_text(encoding='utf-8'))
    with path.open(encoding='utf-8-sig', newline='') as stream:
        reader = csv.DictReader(stream)
        if not reader.fieldnames or len(reader.fieldnames) != len(set(reader.fieldnames)):
            raise ValueError('CSV requires unique column headings')
        if set(reader.fieldnames) - set(CSV_FIELDS):
            raise ValueError('CSV contains unsupported columns; use the public research template')
        if set(REQUIRED) - set(reader.fieldnames):
            raise ValueError('CSV is missing required columns; use the public research template')
        rows = list(reader)
    for row in rows:
        if None in row or any(v is None for v in row.values()):
            raise ValueError('CSV row has incorrect number of columns')
        for key in ('lat', 'lng'):
            try:
                row[key] = float(row.get(key, ''))
            except ValueError:
                pass
        for key in ('categories', 'capabilities'):
            row[key] = [v.strip() for v in row.get(key, '').split('|') if v.strip()]
        for key in ('location_type', 'coordinate_source', 'relationships', 'company_name'):
            if key in row and not row[key]:
                del row[key]
        if 'relationships' in row:
            try:
                row['relationships'] = json.loads(row['relationships'])
            except json.JSONDecodeError:
                row['relationships'] = None
        try:
            row['capability_evidence'] = json.loads(row.get('capability_evidence') or '{}')
        except json.JSONDecodeError:
            row['capability_evidence'] = None  # Per-record validation rejection.
    return rows


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('input', help='JSON array or research CSV')
    p.add_argument('--output', help='write validated JSON array')
    p.add_argument('--report', help='write JSON report')
    a = p.parse_args()
    if a.report and Path(a.report).resolve() in {Path(a.input).resolve(), Path(a.output).resolve() if a.output else Path(a.input).resolve()}:
        p.error('report must be different from input and output')
    try:
        rows = read_records(a.input)
        errors, warnings = validate(rows)
    except (OSError, ValueError) as exc:
        rows, errors, warnings = [], [str(exc)], []
    report = {'records': len(rows) if isinstance(rows, list) else 0,
              'companies': len({r.get('company_id') for r in rows if isinstance(r, dict) and isinstance(r.get('company_id'), str)}) if isinstance(rows, list) else 0,
              'errors': errors, 'warnings': warnings, 'accepted': not errors}
    output = json.dumps(report, indent=2, ensure_ascii=False) + '\n'
    print(output, end='')
    if a.report:
        Path(a.report).write_text(output, encoding='utf-8')
    if a.output and not errors:
        Path(a.output).write_text(json.dumps(rows, indent=2, ensure_ascii=False, allow_nan=False) + '\n', encoding='utf-8')
    return 1 if errors else 0


if __name__ == '__main__':
    sys.exit(main())
