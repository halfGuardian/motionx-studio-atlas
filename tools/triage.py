#!/usr/bin/env python3
"""Read-only discovery triage: matching is not business/capability verification."""
import argparse
from collections import Counter, defaultdict
import copy
from datetime import date
import hashlib
import html
import json
from pathlib import Path
import re
import sys
from urllib.parse import unquote, urlsplit

from discovery import ROOT, digest, load_config, read, safe_output, write
from validate import normalized, url_valid, validate

CLASSES = ('already_represented', 'potentially_new', 'irrelevant', 'requires_research')
NON_STUDIO = {'about', 'about-us', 'contact', 'contact-us', 'privacy', 'privacy-policy', 'cookies',
              'cookie-policy', 'terms', 'terms-and-conditions', 'news', 'blog', 'careers', 'jobs',
              'services', 'work', 'our-work', 'projects', 'portfolio', 'sustainability', 'technology',
              'culture', 'people', 'accessibility', 'investors', 'animation', 'cinematics', 'performance-capture'}


def url_key(url):
    if not url_valid(url):
        return ''
    parts = urlsplit(url)
    return (parts.hostname.removeprefix('www.').casefold(), unquote(parts.path).rstrip('/'))


def scope_rows(database, company):
    return [r for r in database if company and (r['company_id'] == company or
            any(p['id'] == company for p in r.get('relationships', [])))]


def classify(candidate, source, database, rejected):
    """Conservative routing, with separate triage confidence and original unknown evidence."""
    def result(category, confidence, kind, reason, matches=(), scope='none'):
        return {'classification': category, 'triage_confidence': confidence, 'candidate_type': kind,
                'matching_scope': scope, 'reasons': [reason],
                'matched_location_ids': sorted({r['id'] for r in matches}),
                'matched_organisation_ids': sorted({r['company_id'] for r in matches})}
    if candidate.get('source_kind') == 'manual_backlog' or candidate.get('source_id') == 'v08-review-backlog':
        return result('requires_research', 'unknown', 'backlog', 'Preserved v0.8 deferred research; no new evidence resolves its stated uncertainty.')
    if not source:
        return result('requires_research', 'unknown', 'unresolved_link', 'Source no longer configured; retain observation and review provenance.')
    if candidate.get('missing_since') or candidate.get('signals'):
        return result('requires_research', 'unknown', 'change_signal', 'Missing/changed-business signal needs current primary research; no deletion or status claim inferred.')
    key = url_key(candidate['url'])
    path = key[1] if key else ''
    parts = path.strip('/').split('/')
    slug = parts[-1].casefold()
    kind = source.get('triage_kind', '')
    company = source.get('company_id', '')
    rows = scope_rows(database, company)
    branch = bool(re.search(r'/(?:location|locations)/.+$', path)) and kind == 'branch_links'
    if kind == 'organisation_roster' and path:
        return result('irrelevant', 'confirmed', 'navigation_or_service', 'Roster link leads to navigation, a service, policy, contact or article rather than an individual operator homepage/facility. Preserve it as source history.')
    # Generic service/contact/navigation pages do not establish a physical location.
    if slug in NON_STUDIO or (path.endswith('/careers/locations')):
        return result('irrelevant', 'confirmed', 'navigation_or_service', 'Generic navigation/service/contact page, not an individually identified physical studio. Retain observation for audit.')
    if candidate['url'].rstrip('/') == source.get('url', '').rstrip('/'):
        if kind == 'facility_index':
            return result('requires_research', 'unknown', 'facility_index', 'Multi-facility index; link alone does not identify each stage. Existing organisation does not prove branch completeness.', rows, 'organisation')
        return result('irrelevant', 'confirmed', 'navigation_or_service', 'Source/index link points back to itself, not a new individual facility.')
    if branch:
        if url_key(source['url'])[0] != key[0]:
            return result('requires_research', 'unknown', 'unresolved_link', 'Branch URL is outside the configured official source host; identity needs review.')
        if slug in ('paris-area', 'taiwan') or slug.endswith('-hq'):
            return result('requires_research', 'unknown', 'market_or_corporate_index', 'Area/country/HQ link does not resolve individual production facilities; review physical-site scope.')
        # Reject historical-location assumptions even if a stale careers page still links it.
        historic = [r for r in rejected if company.casefold() in r['organisation'].casefold() and
                    (normalized(slug) in normalized(r['candidate']) or normalized(candidate['label']) == normalized(r['candidate']))]
        if historic:
            value = result('requires_research', 'unknown', 'branch_link', 'Conflicts with a previously rejected/historical candidate; current operation must be re-researched.')
            value['historical_review'] = historic
            return value
        direct = [r for r in rows if key in (url_key(r['website']), url_key(r.get('evidence', '')))]
        by_place = [r for r in rows if normalized(slug) == normalized(r['city']) or
                    normalized(r['id']) == normalized(company + '-' + slug)]
        matches = direct or by_place
        if matches:
            cities = {(r['city'], r['country']) for r in matches}
            if len(cities) == 1:
                return result('already_represented', 'confirmed' if direct else 'likely', 'branch_link',
                              'Exact published source URL match.' if direct else 'Source organisation/group plus exact existing location ID/city slug match; matching only, not new verification.', matches, 'location')
            return result('requires_research', 'unknown', 'market_index', 'One link covers multiple published municipalities; do not collapse them into a single facility.', matches, 'multiple_locations')
        legacy_operator = [r for r in database if normalized(r['company_id']) == normalized(company + '-' + slug)]
        if legacy_operator:
            return result('already_represented', 'likely', 'branch_link', 'Stable operating organisation ID matches the branch slug. Existing entry may describe a specialist facility; same-site identity/branch completeness is NOT established.', legacy_operator, 'organisation')
        country_names = {normalized(r['country']) for r in database} | {'germany','india','china','france','canada','uk','usa','europe','asia','ukraine'}
        if normalized(slug) in country_names:
            return result('requires_research', 'unknown', 'market_index', 'Country/market roster link without an individual facility match; branch-level research required.')
        return result('potentially_new', 'likely', 'branch_link', 'Official branch-shaped link has no location match in the current database. Candidate only: city, country, operation and capabilities remain unverified.')
    # Structured location data still needs identity plus exact city/country to match.
    if candidate.get('city') and candidate.get('country'):
        matches = [r for r in rows if normalized(r['city']) == normalized(candidate['city']) and normalized(r['country']) == normalized(candidate['country'])]
        if matches:
            return result('already_represented', 'likely', 'structured_place', 'Organisation/group and structured city/country match existing locations; not independent verification.', matches, 'location')
        return result('potentially_new', 'likely', 'structured_place', 'Structured organisation/city/country has no existing scoped location match; research required before publication.')
    # A roster's operator homepage can match an organisation without asserting its branches.
    if kind == 'organisation_roster' and key and not path:
        matches = [r for r in database if url_key(r['website']) and url_key(r['website'])[0] == key[0]]
        if matches and len({r['company_id'] for r in matches}) == 1:
            return result('already_represented', 'likely', 'organisation_link', 'Official operator homepage matches one published operating organisation. Organisation-only match; facilities/branch coverage remain unverified.', matches, 'organisation')
        return result('requires_research', 'unknown', 'organisation_link', 'Operator homepage, not a location. Resolve operating identity and physical facilities first.', matches, 'organisation' if matches else 'none')
    return result('requires_research', 'unknown', 'unresolved_link', 'Insufficient facility/identity evidence in this observation; do not infer a studio from a navigation link.')


def triage(queue, observation_report, database, config, rejected=(), observed_on=None):
    errors, _ = validate(database)
    if errors:
        raise ValueError('invalid canonical database')
    load_config(config)
    if queue.get('version') != 1 or not isinstance(queue.get('candidates'), dict):
        raise ValueError('invalid discovery queue')
    if len(queue['candidates']) > 100_000:
        raise ValueError('queue exceeds triage limit')
    if not isinstance(observation_report.get('sources'), list):
        raise ValueError('invalid discovery run report')
    sources = {s['id']: s for s in config['sources']}
    outcomes, duplicates = [], defaultdict(list)
    for cid, candidate in sorted(queue['candidates'].items()):
        if not isinstance(candidate, dict) or candidate.get('id') != cid or not url_valid(candidate.get('url')):
            raise ValueError('invalid candidate identity/URL')
        for key in ('label', 'source_id', 'confidence', 'content_hash'):
            if not isinstance(candidate.get(key), str):
                raise ValueError('invalid candidate metadata')
        for key in ('first_seen', 'last_seen'):
            date.fromisoformat(candidate[key])
        source = sources.get(candidate['source_id'], {})
        outcome = classify(candidate, source, database, rejected)
        result = {'id': cid, **outcome, 'observation': copy.deepcopy(candidate),
                  'source_url': source.get('url') or candidate.get('sources', [candidate['url']])[0],
                  'source_enabled': source.get('enabled', False), 'candidate_hash': digest(candidate)}
        if source.get('disabled_reason'):
            result['reasons'].append('Automated source disabled: ' + source['disabled_reason'])
        outcomes.append(result)
        duplicates[(url_key(candidate['url']), normalized(candidate.get('city', '')), normalized(candidate.get('country', '')))].append(cid)
    groups = [ids for ids in duplicates.values() if len(ids) > 1]
    by_id = {r['id']: r for r in outcomes}
    for ids in groups:
        for cid in ids:
            by_id[cid]['duplicate_observation_ids'] = [other for other in ids if other != cid]
    counts = {name: sum(r['classification'] == name for r in outcomes) for name in CLASSES}
    coverage = []
    for sid in sorted({r['observation']['source_id'] for r in outcomes} | set(sources)):
        records = [r for r in outcomes if r['observation']['source_id'] == sid]
        last_run = next((s for s in observation_report['sources'] if s['id'] == sid), {})
        coverage.append({'source_id': sid, 'enabled': sources.get(sid, {}).get('enabled', False),
                         'last_run_status': last_run.get('status', 'backlog_or_not_attempted'),
                         'last_run_observations': last_run.get('candidate_count', 0), 'retained_candidates': len(records),
                         'counts': dict(Counter(r['classification'] for r in records)),
                         'candidate_types': dict(Counter(r['candidate_type'] for r in records))})
    return {'version': 1, 'triaged_on': observed_on or date.today().isoformat(), 'queue_hash': digest(queue),
            'database_hash': digest(database), 'discovery_report_hash': digest(observation_report), 'config_hash': digest(config),
            'published_location_count': len(database), 'published_organisation_count': len({r['company_id'] for r in database}),
            'candidate_count': len(outcomes), 'counts': counts,
            'counting_policy': 'Counts are observations, including backlog and duplicates, not unique facilities. Organisation-only matches do not establish branch completeness.',
            'duplicate_observation_groups': groups, 'source_coverage': coverage, 'candidates': outcomes,
            'published_records': 0, 'approval_changes': 0}


def markdown(report):
    def text(value):
        return html.escape(str(value)).replace('|', '\\|').replace('\n', ' ').replace('`', '\\`')
    lines = ['# Discovery triage', '', f"Published database: **{report['published_location_count']} locations / {report['published_organisation_count']} organisations** (unchanged).", '',
             '| Classification | Candidates |', '| --- | ---: |',
             *[f'| {name} | {count} |' for name, count in report['counts'].items()], '',
             report['counting_policy'], '', 'Triage confidence describes matching/routing, not business operation or capability evidence. Original discovery confidence remains unchanged. No records or claims are approved.', '',
             '## Source coverage', '', '| Source | Last run | Observations | Retained | Types |', '| --- | --- | ---: | ---: | --- |']
    for source in report['source_coverage']:
        lines.append(f"| {text(source['source_id'])} | {text(source['last_run_status'])} | {source['last_run_observations']} | {source['retained_candidates']} | {text(json.dumps(source['candidate_types'], sort_keys=True))} |")
    lines += ['', '## Candidate decisions', '', '| Candidate / source | Classification / scope | Matching reasons / IDs |', '| --- | --- | --- |']
    for row in report['candidates']:
        candidate = row['observation']
        lines.append(f"| {text(candidate['label'])} — {text(candidate['url'])} ({text(candidate['last_seen'])}) | {row['classification']} / {row['matching_scope']} | {text('; '.join(row['reasons']))} {text(', '.join(row['matched_location_ids']))} |")
    return '\n'.join(lines) + '\n'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--queue', type=Path, required=True)
    parser.add_argument('--report', type=Path, required=True)
    parser.add_argument('--database', type=Path, default=ROOT/'studios.json')
    parser.add_argument('--config', type=Path, default=ROOT/'data/discovery/sources.json')
    parser.add_argument('--historical-reviews', type=Path, default=ROOT/'data/research/v0.8-global-expansion/review-queue.json')
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--inventory', action='store_true', help='emit compact per-candidate routing for job-log inspection')
    args = parser.parse_args()
    try:
        safe_output(args.output, [args.queue, args.report, args.database, args.config, args.historical_reviews])
        if args.output.exists():
            raise ValueError('choose a fresh output directory')
        rejected = [r for r in read(args.historical_reviews) if r['decision'] == 'reject']
        result = triage(read(args.queue), read(args.report), read(args.database), read(args.config), rejected)
        result['input_sha256'] = {key: hashlib.sha256(path.read_bytes()).hexdigest() for key, path in [('queue', args.queue), ('report', args.report), ('database', args.database)]}
        write(args.output/'triage.json', result)
        (args.output/'summary.md').write_text(markdown(result), encoding='utf-8')
        # Preserve original queue, source report, history and approvals byte-for-byte.
        for path, name in [(args.queue, 'queue.json'), (args.report, 'report.json')]:
            (args.output/name).write_bytes(path.read_bytes())
        print('TRIAGE_COUNTS ' + json.dumps(result['counts'], sort_keys=True))
        print('TRIAGE_SOURCES ' + json.dumps(result['source_coverage'], sort_keys=True))
        if args.inventory:
            for row in result['candidates']:
                print('TRIAGE_RECORD ' + json.dumps({k: row[k] for k in ('id','classification','matching_scope','matched_location_ids','reasons')} | {'url':row['observation']['url'],'label':row['observation']['label']}, ensure_ascii=True))
        return 0
    except (OSError, ValueError, TypeError, KeyError) as exc:
        print(f'Triage blocked: {exc}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
