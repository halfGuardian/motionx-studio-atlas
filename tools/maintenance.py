#!/usr/bin/env python3
"""Incremental, source-bound research staging. No collection or public-data writes."""
import argparse
import copy
import hashlib
import html
import json
import re
import shutil
import tempfile
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

from discovery import ROOT, read, write, digest, load_config, signals as word_signals
from checkpoints import check_queue
from global_programme import (GlobalIndex, empty_state, check_state, advance,
                              load_snapshot, normalise, bounded, MAX_STATE_BYTES)
from global_continuation import classify, GROUPS
from annecy_match import key
from boutique import host, shared
from launch_readiness import records
from validate import url_valid

HOME = ROOT / 'data/maintenance'
TECHNICAL = set(GROUPS['technical'] + ['Virtual Production', 'Previsualization', 'Previs', 'Cinematics'])


def iso(value):
    if not isinstance(value, str) or date.fromisoformat(value).isoformat() != value:
        raise ValueError('ISO calendar date required')
    return value


def config(path=HOME / 'config.json'):
    c = bounded(path)
    if set(c) != {'version', 'monthly', 'freshness', 'snapshot_registry', 'discovery_registry', 'publication_mode', 'automatic_publication'} or c['version'] != 1 or c['automatic_publication'] is not False or c['publication_mode'] != 'research_only_draft_pr_then_owner_review':
        raise ValueError('Unsafe maintenance configuration')
    m = c['monthly']; f = c['freshness']
    if set(m) != {'enabled', 'day_utc', 'interval_months', 'branch_prefix', 'maximum_open_batches'} or type(m['enabled']) is not bool or type(m['day_utc']) is not int or not 1 <= m['day_utc'] <= 28 or type(m['interval_months']) is not int or not 1 <= m['interval_months'] <= 12 or type(m['maximum_open_batches']) is not int or m['maximum_open_batches'] != 1 or not re.fullmatch(r'automation/[a-z0-9-]+-', m['branch_prefix']):
        raise ValueError('Invalid monthly cadence or branch scope')
    if set(f) != {'observation_warning_days', 'source_warning_days', 'policy_review_days', 'artifact_expiry_warning_days'} or any(type(v) is not int or not 1 <= v <= 3650 for v in f.values()):
        raise ValueError('Invalid freshness thresholds')
    local(c['snapshot_registry']); local(c['discovery_registry'])
    return c


def local(name, root=ROOT):
    p = Path(name); target = root / p
    if p.is_absolute() or '..' in p.parts or not p.parts or p.parts[0] != 'data' or target.is_symlink() or not target.resolve().is_relative_to((root / 'data').resolve()):
        raise ValueError('Only regular repository research-data paths are admitted')
    return target


def fresh_output(output):
    p = Path(output).resolve()
    if p.exists() or p == ROOT or p in ROOT.parents or p.is_relative_to((ROOT / 'data/public').resolve()) or p == (ROOT / 'studios.json').resolve():
        raise ValueError('Fresh research output outside published data required')
    return p


def publication_fingerprint():
    paths = [ROOT / 'studios.json', *sorted((ROOT / 'data/public').rglob('*'))]
    return digest({str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths if p.is_file()})


def age(as_of, observed):
    return (date.fromisoformat(iso(as_of)) - date.fromisoformat(iso(observed))).days


def effective_registry(c, as_of):
    registry = copy.deepcopy(read(local(c['discovery_registry'])))
    load_config(registry)
    for s in registry['sources']:
        if s['enabled'] and age(as_of, s['access_review']['reviewed_on']) > c['freshness']['policy_review_days']:
            s['enabled'] = False
            s['disabled_reason'] = 'Access/reuse review expired; no collection until a reviewed policy renewal.'
    return registry


def due(c, as_of, manual=False):
    d = date.fromisoformat(iso(as_of)); m = c['monthly']
    return m['enabled'] and (manual or d.day == m['day_utc'] and (d.month - 1) % m['interval_months'] == 0)


def add_snapshot(state, snapshot):
    # Historical versions already present may precede a newer mutable head.
    old = [e['snapshot'] for e in state['history'] if e['source_id'] == snapshot['source_id'] and e['snapshot_id'] == snapshot['snapshot_id']]
    if old:
        if any(digest(s) != digest(snapshot) for s in old):
            raise ValueError('Immutable source/snapshot ID reused with different facts or policy')
        return state, []
    return advance(state, snapshot)


def dataset_snapshots(c):
    registry = bounded(local(c['snapshot_registry']))
    if registry.get('version') != 1 or not isinstance(registry.get('sources'), list) or len(registry['sources']) > 1000:
        raise ValueError('Invalid reviewed snapshot registry')
    seen = set()
    for entry in registry['sources']:
        sid = entry['source_id']
        if sid in seen or set(entry) - {'source_id', 'policy', 'snapshot', 'metadata', 'state'}:
            raise ValueError('Duplicate or unsupported dataset registration')
        seen.add(sid); policy = bounded(local(entry['policy']))
        snapshot = load_snapshot(local(entry['snapshot']), policy, bounded(local(entry['metadata'])) if entry.get('metadata') else None)
        historic = check_state(bounded(local(entry['state']), MAX_STATE_BYTES))
        if sid != snapshot['source_id'] or historic['sources'].get(sid) != snapshot:
            raise ValueError('Dataset source identity/state checkpoint mismatch')
        yield entry, policy, snapshot, historic


def bridge_discovery(folder, c, as_of):
    """Bounded link metadata is not a blanket dataset licence or a complete roster."""
    folder = Path(folder); validate_discovery(folder)
    q = check_queue(bounded(folder / 'queue.json')); report = bounded(folder / 'report.json')
    iso(report['observed_on'])
    if report['observed_on'] > as_of: raise ValueError('Discovery observation date is in the future')
    configured = read(local(c['discovery_registry']))
    effective = {s['id']: s for s in effective_registry(c, as_of)['sources']}
    statuses = {s['id']: s for s in report['sources']}
    snapshots = []; coverage = []
    for source in configured['sources']:
        sid = source['id']; status = statuses.get(sid)
        row = {'source_id': sid, 'url': source['url'], 'automatic_collection_configured': source['enabled'],
               'automatic_collection_effective': effective[sid]['enabled'], 'mode': 'bounded_official_metadata' if source['enabled'] else 'manual_research_only',
               'policy_reviewed_on': source.get('access_review', {}).get('reviewed_on'),
               'rights_scope': source.get('reuse_note', ''), 'status': 'not_attempted', 'complete': False}
        if not effective[sid]['enabled']:
            row.update(status='policy_review_expired' if source['enabled'] else 'disabled', reason=effective[sid].get('disabled_reason', 'Manual rights/access review required'))
        elif status:
            row.update(status=status['status'], observed_on=status['attempted_on'], observations=status.get('candidate_count', 0))
            source_rows = []
            if status['status'] == 'ok':
                for cid, candidate in q['candidates'].items():
                    if candidate['source_id'] != sid or candidate['last_seen'] != report['observed_on']:
                        continue
                    # Navigation labels are not manufactured operating identities.
                    from triage import classify as triage_candidate
                    decision = triage_candidate(candidate, source, [], [])
                    if decision['classification'] == 'irrelevant':
                        continue
                    source_rows.append(normalise({'source_record_id': cid, 'name': source.get('organisation_name') or candidate['label'],
                        'website': source['url'], 'city': candidate.get('city', ''), 'country': candidate.get('country', ''),
                        'service_claims': candidate.get('claim_terms', []), 'source_url': candidate['url'],
                        'observed_on': candidate['last_seen'], 'location_claim': ' | '.join(filter(None, (candidate.get('unit_key', ''), candidate.get('place_basis', '')))),
                        'status_claim': ' '.join(candidate.get('status_terms', []))}))
            snapshot = {'version': 1, 'source_id': sid, 'snapshot_id': digest([report['observed_on'], status, source_rows]),
                'observed_on': report['observed_on'], 'status': 'partial' if status['status'] == 'ok' else 'failed',
                'complete': False, 'expected_records': None, 'source_url': source['url'], 'license': 'UNSPECIFIED',
                'records': source_rows, 'enumeration_scope': 'Reviewed bounded official metadata; not an exhaustive company/facility roster.',
                'policy_hash': digest(source), 'input_sha256': digest([q, report]), 'automatic_publication': False,
                'rights_scope': 'Bounded metadata review only; broader redistribution rights are not granted.'}
            if snapshot['status'] == 'failed': snapshot['failure'] = status['status']
            snapshots.append(snapshot)
        coverage.append(row)
    return q, report, snapshots, coverage


def validate_discovery(folder):
    folder = Path(folder); total = 0; count = 0
    if folder.is_symlink(): raise ValueError('No discovery directory links')
    for p in folder.rglob('*'):
        if p.is_symlink(): raise ValueError('No discovery archive links')
        if not p.is_file(): continue
        relative = p.relative_to(folder)
        if relative.as_posix() not in ('queue.json', 'report.json', 'recovery.json', 'receipt.json') and not (len(relative.parts) == 2 and relative.parts[0] == 'history' and p.suffix == '.json'):
            raise ValueError('Only bounded discovery JSON/history may enter a research PR')
        count += 1; total += p.stat().st_size
        if count > 10000 or p.stat().st_size > 50_000_000 or total > 250_000_000: raise ValueError('Discovery archive parsing limit')
        bounded(p)


def sector_categories(claims):
    # Exact source sectors only; never derive capture capabilities from VFX.
    known = {s.casefold(): s for values in GROUPS.values() for s in values}
    known.update({'film production': 'Film / Television Production', 'game development': 'Game Development'})
    return sorted({known[v.casefold()] for v in claims if v.casefold() in known})


def proposals(state, rows, commercial, as_of, c):
    index = GlobalIndex(rows); latest = {}; changes = defaultdict(list)
    for e in state['history']:
        sid = e['source_id']
        for r in e['snapshot']['records']:
            latest[sid, r['source_record_id']] = {**r, 'source_id': sid, 'license': e['snapshot']['license'], 'snapshot_id': e['snapshot_id'], 'policy_hash': e['snapshot']['policy_hash']}
        for signal in e['signals']:
            if signal.get('source_record_id'): changes[sid, signal['source_record_id']].append(signal)
    groups = defaultdict(list)
    for r in latest.values():
        domain = host(r['website'])
        group = [key(r['name']), r['country'], r['city'], domain if not shared(domain) else '', r.get('location_claim', ''), r['name'] if not key(r['name']) else '']
        groups[digest(group)].append(r)
    result = []
    for identity, observations in sorted(groups.items()):
        first = observations[0]; match, disposition = index.resolve(first)
        claims = sorted({v for r in observations for v in r['service_claims']})
        cats = sector_categories(claims)
        relevant = classify({'id': 'unpublished-' + identity, 'categories': cats}, commercial)
        kinds = {disposition}; warnings = []
        if any(r.get('location_claim') for r in observations): kinds.add('facility_or_city_reference_review')
        comparison = [dict(r) for r in (index.rows[i] for i in match['record_ids'])]
        found_cities = {(r['city'], r['country']) for r in comparison}
        if first['city'] and first['country'] and comparison and (first['city'], first['country']) not in found_cities:
            kinds.add('city_association_change_review')
        if comparison and any(r['name'] != first['name'] for r in comparison): kinds.add('alias_or_identity_review')
        if claims and any(v in TECHNICAL for v in claims): kinds.add('technical_capability_review')
        audio = any(re.search(r'\b(audio|sound|dubbing)\b', v, re.I) for v in claims)
        if audio:
            kinds.add('audio_only_scope_review')
            warnings.append('Audio services/name signals do not establish audio-only scope; no automatic exclusion.')
        exact_exclusions = [commercial['overrides'][r['id']] for r in comparison if r['id'] in commercial['overrides']]
        if exact_exclusions and all(e['excluded'] for e in exact_exclusions) and len(exact_exclusions) == len(comparison):
            relevant = exact_exclusions[0]
            if set(cats).intersection(GROUPS['games'] + GROUPS['visual'] + GROUPS['technical']):
                kinds.add('reviewed_audio_exclusion_conflict')
                warnings.append('New visual/game/technical assertions conflict with an existing audio-only review. Investigate multidisciplinary services; no automatic exclusion change.')
        event_list = [s for r in observations for s in changes[r['source_id'], r['source_record_id']]]
        for s in event_list:
            if s['kind'] == 'source_absence_investigation': kinds.add('source_absence_review')
            if s['kind'] == 'possible_identity_geography_service_change': kinds.add('source_assertion_change_review')
        if any(word_signals(r['status_claim']) for r in observations):
            kinds.add('business_status_assertion_review')
        if any('possible_closure' in word_signals(r['status_claim']) for r in observations):
            kinds.add('possible_closure_review')
        evidence = []
        for r in observations:
            obs_age = age(as_of, r['observed_on']); source_age = age(as_of, r['source_updated_on']) if r.get('source_updated_on') else None
            evidence.append({k: r[k] for k in ('source_id', 'source_record_id', 'snapshot_id', 'source_url', 'observed_on', 'license', 'policy_hash')} | {'source_updated_on': r.get('source_updated_on'), 'observation_age_days': obs_age, 'source_age_days': source_age})
            if obs_age > c['freshness']['observation_warning_days']: warnings.append('Observation is stale; current operation needs research.')
            if source_age is not None and source_age > c['freshness']['source_warning_days']: warnings.append('Underlying source assertion is old; a fresh fetch does not refresh the source date.')
            if r.get('source_updated_on') and r['source_updated_on'] > r['observed_on']: warnings.append('Source date is newer than observation; investigate inconsistent source metadata.')
        fields = {'name': first['name'], 'website': first['website'], 'city': first['city'], 'country': first['country'],
                  'categories': cats, 'evidence_class': 'C', 'lat': None, 'lng': None, 'capabilities': [], 'operation_status': 'unverified'}
        result.append({'proposal_id': 'maintenance-' + identity[:24], 'company_identity': key(first['name']),
            'name': first['name'], 'city': first['city'], 'country': first['country'], 'kinds': sorted(kinds),
            'matching': match, 'commercial': relevant, 'original_service_assertions': claims,
            'claim_status': 'source_assertion_not_independent_verification', 'evidence': evidence,
            'before': comparison, 'source_changes': event_list, 'proposed_minimal_fields': fields,
            'geographic_proposal': {'city': first['city'], 'country': first['country'], 'coordinates': None, 'status': 'needs_municipality_and_licensed_coordinate_review'} if first['city'] else None,
            'relationship_assertions': sorted({v for r in observations for v in r['relationship_claims']}),
            'recommendation': 'compare_source_assertions_only_preserve_existing_facts' if comparison else 'research_identity_and_rights_before_company_admission',
            'warnings': sorted(set(warnings)), 'grouping': 'Exact name/country/city/nonshared-domain factual key only; not verified company identity.',
            'human_approved': False, 'canonical_update': None, 'facility_verified': False})
    return result


def seal(folder):
    folder = Path(folder); files = {}; total = 0
    for p in sorted(folder.rglob('*')):
        if p.is_symlink(): raise ValueError('No links in a maintenance archive')
        if not p.is_file() or p == folder / 'integrity.json': continue
        total += p.stat().st_size
        if total > 250_000_000 or p.stat().st_size > MAX_STATE_BYTES: raise ValueError('Archive size limit; partition with review, never drop history')
        files[p.relative_to(folder).as_posix()] = hashlib.sha256(p.read_bytes()).hexdigest()
    value = {'version': 1, 'files': files, 'content_hash': digest(files), 'human_approved': False, 'canonical_updates': []}
    write(folder / 'integrity.json', value); return value


def verify(folder):
    folder = Path(folder); expected = bounded(folder / 'integrity.json')
    if folder.is_symlink(): raise ValueError('No maintenance directory links')
    if expected.get('human_approved') is not False or expected.get('canonical_updates') != [] or expected.get('content_hash') != digest(expected.get('files')):
        raise ValueError('Invalid maintenance archive manifest')
    actual = {}; total = 0
    for p in folder.rglob('*'):
        if p.is_symlink(): raise ValueError('No archive links')
        if p.is_file() and p != folder / 'integrity.json':
            total += p.stat().st_size
            if len(actual) >= 20000 or total > 250_000_000: raise ValueError('Archive verification size limit')
            actual[p.relative_to(folder).as_posix()] = hashlib.sha256(p.read_bytes()).hexdigest()
    if actual != expected['files']: raise ValueError('Corrupt, missing or extra maintenance archive content')
    check_state(bounded(folder / 'state.json', MAX_STATE_BYTES))
    validate_discovery(folder / 'discovery')
    report = bounded(folder / 'report.json')
    if report.get('version') != 2 or any(report['summary'].get(k) != 0 for k in ('canonical_updates', 'added_approved_records', 'new_verified_facilities', 'new_verified_capabilities')) or report['summary'].get('human_approved') is not False or report['summary'].get('global_complete') is not False or report['summary'].get('live_publish_status') != 'unchanged':
        raise ValueError('Research archive cannot approve or publish company facts')
    for p in report['proposals']:
        fields = p['proposed_minimal_fields']
        if p.get('human_approved') is not False or p.get('facility_verified') is not False or p.get('canonical_update') is not None or fields.get('evidence_class') != 'C' or fields.get('lat') is not None or fields.get('lng') is not None or fields.get('capabilities') != []:
            raise ValueError('Proposals must remain unapproved, unpinned research')
    return expected


def save_report(report, out):
    write(out / 'report.json', report)
    esc = lambda v: html.escape(str(v), quote=True)
    cards = []
    for p in sorted(report['proposals'], key=lambda p: (p['country'], p['name'], p['city'])):
        links = ' · '.join('<a rel="noopener noreferrer" href="' + esc(e['source_url']) + '">' + esc(e['source_id']) + '</a>' for e in p['evidence'])
        cards.append('<article data-proposal><h2>' + esc(p['name']) + '</h2><p>' + esc(p['city'] or 'City unresolved') + ', ' + esc(p['country'] or 'Country unresolved') + '</p><p>' + esc(', '.join(p['kinds'])) + '</p><p>' + esc(p['commercial']['role']) + ' · eligibility only; purchasing intent unknown.</p><p>' + links + '</p><details><summary>Evidence, before/after assertions and review questions</summary><pre>' + esc(json.dumps(p, ensure_ascii=False, indent=2)) + '</pre></details></article>')
    page = '''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>MotionX maintenance review</title><style>body{background:#101822;color:#edf1f8;font:16px/1.6 system-ui;max-width:1100px;margin:auto;padding:18px;overflow-wrap:anywhere}a{color:#addcff}article{border:1px solid #63718a;padding:16px;margin:16px 0}pre{white-space:pre-wrap;overflow-wrap:anywhere}input{font:inherit;min-height:44px;max-width:100%}:focus-visible{outline:3px solid #ffd77a}[hidden]{display:none}</style><h1>Unapproved global maintenance review</h1><p>Research only. Source assertions, similarity matches and tests do not verify current companies, facilities, closure or capabilities. No publication or human approval has occurred.</p><a href="report.json">Complete audit</a> · <a href="summary.md">Change digest and operating instructions</a><pre>SUMMARY</pre><label>Search company, country, claim or review status <input id="maintenanceSearch" type="search"></label><p role="status" aria-live="polite" id="reviewCount"></p>CARDS<script>(()=>{const rows=[...document.querySelectorAll('[data-proposal]')],q=document.getElementById('maintenanceSearch'),c=document.getElementById('reviewCount');function draw(){let n=0;const words=q.value.toLowerCase().trim().split(/\\s+/).filter(Boolean);for(const r of rows){r.hidden=!words.every(w=>r.textContent.toLowerCase().includes(w));if(!r.hidden)n++;}c.textContent=n+' of '+rows.length+' proposals. Owner review required.';}q.addEventListener('input',draw);draw();})();</script></html>'''
    coverage = '<details id="sourceCoverage"><summary>Automatic versus manual coverage and source attribution</summary>'
    for source in report['source_coverage']:
        licence = source.get('license_url')
        coverage += '<p><strong>' + esc(source['source_id']) + '</strong> · ' + esc(source['mode']) + ' · ' + esc(source['status']) + '<br>' + esc(source.get('attribution') or source.get('rights_scope', ''))
        if licence: coverage += ' · <a rel="noopener noreferrer" href="' + esc(licence) + '">' + esc(source['license']) + '</a>'
        coverage += '</p>'
    coverage += '</details>'
    alerts = '<section aria-label="Maintenance alerts"><h2>Source and continuity alerts</h2><ul>'
    alerts += ''.join('<li>' + esc(a['severity'] + ' · ' + a['code'] + ': ' + a['reason']) + '</li>' for a in report['alerts']) or '<li>No new source alerts. This does not verify businesses or global coverage.</li>'
    alerts += '</ul></section>'
    page = page.replace('<pre>SUMMARY</pre>', '<pre>SUMMARY</pre>' + alerts + coverage)
    page = page.replace('<a href="report.json">Complete audit</a>', '<a href="report.json">Complete audit</a> · <a href="discovery/report.json">Original source change digest</a>')
    (out / 'review.html').write_text(page.replace('SUMMARY', esc(json.dumps(report['summary'], indent=2))).replace('CARDS', ''.join(cards)), encoding='utf-8')
    lines = ['# MotionX maintenance — owner review required', '', json.dumps(report['summary'], indent=2), '', '## Alerts', '']
    lines += ['- ' + a['code'] + ': ' + a['reason'] for a in report['alerts']]
    lines += ['', '## Review this batch', '', 'Open review.html over local HTTP. Inspect source rights, original dates, identity matches, technical claims and before/after values. No proposed fields are applied to the public Atlas. Resolve exceptions or prepare a separate exact-content data PR using the established reviewed publication workflow. Review that data PR and manually authorise its merge; merging this research batch only archives research. Tests, bots and draft status are not owner approval. Never infer closure or exclusion from names, missing links or fetch failures.', '', 'This report is not a global census. Weekly source failures and stale/expiring archives require attention; download/archive the full bundle before its 90-day expiry.']
    (out / 'summary.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')


def prepare(discovery, output, state_path=None, c=None, as_of=None, recovery_path=None):
    c = c or config(); as_of = iso(as_of or date.today().isoformat()); out = fresh_output(output)
    if out.is_relative_to(Path(discovery).resolve()): raise ValueError('Output cannot be inside its discovery input')
    before = publication_fingerprint(); state = check_state(bounded(state_path, MAX_STATE_BYTES)) if state_path else empty_state()
    state = copy.deepcopy(state); all_signals = []; alerts = []; dataset_coverage = []
    for entry, policy, snapshot, historic in dataset_snapshots(c):
        for e in historic['history']:
            if e['source_id'] == entry['source_id']:
                state, new_signals = add_snapshot(state, e['snapshot']); all_signals += new_signals
        dataset_coverage.append({'source_id': snapshot['source_id'], 'mode': 'reviewed_offline_dataset', 'automatic_collection_configured': False,
            'status': snapshot['status'], 'complete': snapshot['complete'], 'enumeration_scope': snapshot['enumeration_scope'],
            'observed_on': snapshot['observed_on'], 'records': len(snapshot['records']), 'license': policy['license'],
            'license_url': policy['license_url'], 'attribution': policy['attribution'], 'url': snapshot['source_url'], 'policy_hash': digest(policy)})
    q, source_report, snapshots, coverage = bridge_discovery(discovery, c, as_of)
    for s in snapshots:
        state, new_signals = add_snapshot(state, s); all_signals += new_signals
    for s in coverage + dataset_coverage:
        if s['status'] in ('fetch_or_parse_error', 'extraction_empty', 'policy_review_expired', 'failed', 'partial') or s['automatic_collection_configured'] and s['status'] == 'not_attempted':
            alerts.append({'code': 'source_attention', 'severity': 'error' if s['status'] in ('fetch_or_parse_error', 'failed', 'extraction_empty', 'policy_review_expired') else 'warning', 'reason': s['source_id'] + ': ' + s['status'] + '. Retain history; no closure inferred.'})
        if s.get('observed_on') and age(as_of, s['observed_on']) > c['freshness']['observation_warning_days']:
            alerts.append({'code': 'stale_snapshot', 'severity': 'warning', 'reason': s['source_id'] + ': source observation is stale.'})
    recovery = bounded(Path(discovery) / 'recovery.json') if (Path(discovery) / 'recovery.json').exists() else {'history_complete': False, 'suppress_absence_signals': True}
    if recovery.get('continuity_version') != 2:
        recovery = {**recovery, 'history_complete': False, 'suppress_absence_signals': True, 'legacy_completeness_flag_not_proof': True}
    state_recovery = bounded(recovery_path) if recovery_path else {'mode': 'explicit_initial_state', 'history_complete': False}
    if state_recovery.get('artifact_expires_at'):
        expires = state_recovery['artifact_expires_at'][:10]
        if age(expires, as_of) <= c['freshness']['artifact_expiry_warning_days']:
            alerts.append({'code': 'artifact_expiring', 'severity': 'warning', 'reason': 'Discovery state artifact expires soon. Merge an owner-reviewed research checkpoint or retain a complete offline archive.'})
    if state_recovery.get('mode') != 'verified_actions_artifact':
        alerts.append({'code': 'state_recovery_attention', 'severity': 'warning', 'reason': 'Using a committed checkpoint/bootstrap. Any missing newer artifact history remains explicitly unresolved.'})
    if not recovery.get('history_complete'):
        alerts.append({'code': 'incomplete_discovery_history', 'severity': 'warning', 'reason': 'Raw history is partial or recovered; absence cannot establish closure. Preserve every available checkpoint.'})
    m, rows = records(ROOT / 'data/public', ROOT / 'studios.json'); commercial = read(ROOT / 'data/public/commercial.json')
    proposed = proposals(state, rows, commercial, as_of, c)
    source_rights = {s['source_id']: s for s in dataset_coverage}
    for proposal in proposed:
        for evidence in proposal['evidence']:
            rights = source_rights.get(evidence['source_id'], {})
            historical_policy = bool(rights and rights['policy_hash'] != evidence['policy_hash'])
            if historical_policy:
                rights = {}
                proposal['warnings'].append('Historical source policy differs. Recover its original attribution/reuse receipt; current rights do not retroactively license older observations.')
            evidence.update(license_url=rights.get('license_url'), attribution=rights.get('attribution'),
                            rights_scope='Pinned licensed factual snapshot only' if rights else 'Historical policy receipt requires review' if historical_policy else 'Bounded official metadata; broader source rights remain unspecified')
    summary = {'as_of_utc': as_of, 'catalogue_records': len(rows), 'retained_discovery_candidates': len(q['candidates']),
        'newly_observed_source_leads': sum(s['kind'] == 'newly_observed' for s in all_signals), 'prepared_research_proposals': len(proposed),
        'reviewed_company_proposals': 0, 'existing_match_proposals': sum(bool(p['matching']['record_ids']) for p in proposed),
        'unresolved_proposals': sum(not p['matching']['record_ids'] or any('review' in k for k in p['kinds']) for p in proposed),
        'grouped_source_observations': sum(len(p['evidence']) for p in proposed), 'duplicate_observations_grouped': sum(len(p['evidence']) - 1 for p in proposed),
        'new_change_signals': len(all_signals), 'history_events_retained': len(state['history']),
        'automatic_official_sources_configured': sum(s['automatic_collection_configured'] for s in coverage),
        'manual_official_sources': sum(not s['automatic_collection_configured'] for s in coverage),
        'offline_dataset_sources': len(dataset_coverage), 'added_approved_records': 0, 'new_verified_facilities': 0,
        'new_verified_capabilities': 0, 'canonical_updates': 0, 'live_publish_status': 'unchanged', 'global_complete': False, 'human_approved': False}
    report = {'version': 2, 'summary': summary, 'source_coverage': coverage + dataset_coverage, 'alerts': alerts,
        'proposals': proposed, 'new_signals': all_signals, 'raw_queue_sha256': digest(q), 'discovery_recovery': recovery,
        'canonical_fingerprint': before, 'state_recovery': state_recovery, 'rights': 'Per-source restrictions retained. Bounded discovery metadata grants no blanket database reuse rights.'}
    stable_proposals = copy.deepcopy(proposed)
    age_warnings = {'Observation is stale; current operation needs research.', 'Underlying source assertion is old; a fresh fetch does not refresh the source date.'}
    for proposal in stable_proposals:
        proposal['warnings'] = [w for w in proposal['warnings'] if w not in age_warnings]
        for evidence in proposal['evidence']:
            evidence.pop('observation_age_days', None); evidence.pop('source_age_days', None)
    report['content_fingerprint'] = digest({'state': state, 'raw_queue': q, 'policies': coverage + dataset_coverage, 'canonical': before, 'proposal_semantics': stable_proposals})
    write(out / 'state.json', state); save_report(report, out)
    shutil.copytree(discovery, out / 'discovery')
    seal(out)
    if publication_fingerprint() != before: raise ValueError('Published data changed during maintenance')
    return report


def main():
    p = argparse.ArgumentParser(description=__doc__); p.add_argument('command', choices=('prepare', 'verify', 'health', 'due', 'policy-config'))
    p.add_argument('--discovery', type=Path); p.add_argument('--state', type=Path); p.add_argument('--output', type=Path)
    p.add_argument('--recovery', type=Path)
    p.add_argument('--config', type=Path, default=HOME / 'config.json'); p.add_argument('--as-of', default=date.today().isoformat()); p.add_argument('--manual', action='store_true')
    a = p.parse_args(); c = config(a.config); iso(a.as_of)
    if a.as_of > date.today().isoformat(): raise ValueError('Future actual report date is not permitted')
    if a.command == 'due': print('true' if due(c, a.as_of, a.manual) else 'false'); return
    if a.command == 'policy-config':
        if not a.output: raise ValueError('Fresh effective configuration required')
        fresh_output(a.output)
        write(a.output, effective_registry(c, a.as_of)); return
    if not a.output: p.error('--output required')
    if a.command == 'verify': print(json.dumps(verify(a.output))); return
    if a.command == 'health':
        verify(a.output); r = read(a.output / 'report.json')
        for alert in r['alerts']:
            print('::' + ('error' if alert['severity'] == 'error' else 'warning') + '::' + alert['code'] + ': ' + alert['reason'].replace('%', '%25').replace('\n', '%0A').replace('\r', '%0D'))
        raise SystemExit(int(any(x['severity'] == 'error' for x in r['alerts'])))
    if not a.discovery: p.error('--discovery required')
    print(json.dumps(prepare(a.discovery, a.output, a.state, c, a.as_of, a.recovery)['summary'], indent=2))


if __name__ == '__main__': main()
