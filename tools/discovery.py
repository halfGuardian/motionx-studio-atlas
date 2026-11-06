#!/usr/bin/env python3
"""Bounded discovery and approval-bound proposals; never writes studios.json."""
import argparse
import copy
import csv
from datetime import date
import hashlib
from html.parser import HTMLParser
import ipaddress
import json
from pathlib import Path
import re
import socket
import sys
import time
from urllib import error, parse, request, robotparser
import xml.etree.ElementTree as ET

from import_csv import plan_import
from validate import CSV_FIELDS, DuplicateIndex, url_valid, validate

ROOT = Path(__file__).resolve().parents[1]
USER_AGENT = 'MotionXDiscovery/0.9.3'
MAX_BYTES = 2_000_000
MAX_ITEMS = 2000
CHECKS = ('location', 'city_country', 'sectors', 'capabilities', 'coordinates', 'identity')


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def write(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + '\n', encoding='utf-8')
    temporary.replace(path)


def public_url(url):
    if not url_valid(url):
        raise ValueError('source must be an HTTPS URL without credentials')
    parts = parse.urlsplit(url)
    if parts.port not in (None, 443):
        raise ValueError('only HTTPS port 443 is allowed')
    host = parts.hostname
    if host == 'localhost' or '.' not in host:
        raise ValueError('source must have a public hostname')
    try:
        if not ipaddress.ip_address(host).is_global:
            raise ValueError('private/reserved IP sources are not allowed')
    except ValueError as exc:
        if 'not allowed' in str(exc):
            raise
    if parts.query or parts.fragment:
        raise ValueError('configured sources cannot contain queries or fragments')
    return host


def load_config(config):
    if config.get('version') != 1 or not isinstance(config.get('sources'), list):
        raise ValueError('invalid source configuration')
    if len(config['sources']) > 50:
        raise ValueError('limit a collection run to 50 explicitly configured sources')
    seen = set()
    for source in config['sources']:
        if not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', source.get('id', '')) or source['id'] in seen:
            raise ValueError('invalid or duplicate source ID')
        seen.add(source['id'])
        if type(source.get('enabled')) is not bool or source.get('kind') not in ('official', 'directory'):
            raise ValueError('sources require enabled and official/directory kind')
        if source.get('adapter') not in ('links', 'jsonld', 'feed', 'location_labels') or not source.get('reuse_note'):
            raise ValueError('source requires an adapter and public reuse/automation note')
        public_url(source['url'])
        if config.get('require_access_review') and source['enabled']:
            review=source.get('access_review', {})
            if review.get('decision') != 'bounded_metadata_reviewed' or not review.get('reviewed_on') or not review.get('note') or not review.get('policy_urls'):
                raise ValueError('enabled sources require a recorded robots/reuse policy review')
        if source.get('adapter') == 'location_labels' and not source.get('place_labels'):
            raise ValueError('location-label adapters require reviewed source-specific labels')
        if source['adapter'] == 'links':
            pattern = source.get('link_pattern', '')
            if not pattern or len(pattern) > 300:
                raise ValueError('links adapter requires a bounded URL pattern')
            re.compile(pattern)
            if source.get('link_label_pattern'):
                if len(source['link_label_pattern']) > 300:
                    raise ValueError('link label pattern exceeds limit')
                re.compile(source['link_label_pattern'])
    return config


class NoUnsafeRedirect(request.HTTPRedirectHandler):
    def __init__(self, host):
        self.host = host

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        # Redirects may change path, but never origin or credentials.
        if public_url(newurl) != self.host:
            raise ValueError('redirect to an unapproved host')
        return super().redirect_request(req, fp, code, msg, headers, newurl)


class Fetcher:
    """No recursive crawl, login, cookies, scripts or robots bypass."""
    def __init__(self):
        self.last = {}
        self.robots = {}

    def response(self, url, host, delay=1):
        # Reject private DNS answers; the configured network proxy/policy remains in force.
        answers = socket.getaddrinfo(host, 443, type=socket.SOCK_STREAM)
        if not answers or any(not ipaddress.ip_address(a[4][0]).is_global for a in answers):
            raise ValueError('source DNS is not public')
        time.sleep(max(0, delay - (time.monotonic() - self.last.get(host, 0))))
        self.last[host] = time.monotonic()
        opener = request.build_opener(NoUnsafeRedirect(host))
        req = request.Request(url, headers={'User-Agent': USER_AGENT, 'Accept-Encoding': 'identity'})
        with opener.open(req, timeout=15) as response:
            body = response.read(MAX_BYTES + 1)
            if len(body) > MAX_BYTES:
                raise ValueError('source exceeds 2 MB limit')
            return body, response.headers.get_content_type(), response.headers.get_content_charset() or 'utf-8'

    def __call__(self, source):
        host = public_url(source['url'])
        if host not in self.robots:
            robots_url = f'https://{host}/robots.txt'
            robot = robotparser.RobotFileParser(robots_url)
            try:
                body, _, encoding = self.response(robots_url, host)
                robot.parse(body.decode(encoding, errors='replace').splitlines())
            except error.HTTPError as exc:
                if exc.code == 404:
                    robot.parse([])
                else:
                    raise ValueError(f'robots unavailable: HTTP {exc.code}') from exc
            self.robots[host] = robot
        robot = self.robots[host]
        if not robot.can_fetch(USER_AGENT, source['url']):
            raise ValueError('robots disallows this source')
        delay = max(1, robot.crawl_delay(USER_AGENT) or 0)
        rate = robot.request_rate(USER_AGENT)
        if rate:
            delay = max(delay, rate.seconds / rate.requests)
        if delay > 60:
            raise ValueError('robots rate requires a slower/manual collection run')
        body, content_type, encoding = self.response(source['url'], host, delay)
        allowed = ('text/html', 'application/xhtml+xml') if source['adapter'] != 'feed' else ('application/rss+xml', 'application/atom+xml', 'application/xml', 'text/xml')
        if content_type not in allowed:
            raise ValueError('unsupported content type')
        return body.decode(encoding, errors='replace')


def clean(text):
    text = re.sub(r'\S+@\S+|https?://\S+', '', text)
    text = re.sub(r'(?<!\w)\+?\d[\d\s().-]{6,}\d(?!\w)', '', text)
    return re.sub(r'\s+', ' ', text).strip()[:180]


def link_url(base, href):
    url = parse.urljoin(base, href)
    if not url_valid(url):
        return None
    parts = parse.urlsplit(url)
    # Candidate links are evidence pointers only; they are NEVER automatically fetched.
    return parse.urlunsplit((parts.scheme, parts.netloc.lower(), parts.path or '/', '', ''))


def link_allowed(source, url, label):
    return bool(re.search(source['link_pattern'], url) and
                (not source.get('link_label_pattern') or re.search(source['link_label_pattern'], clean(label))))


class Page(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.links, self.structured = [], []
        self.anchor = None
        self.jsonld = None
        self.skip = 0

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag in ('script', 'style'):
            self.skip += 1
            if tag == 'script' and attrs.get('type') == 'application/ld+json':
                self.jsonld = []
        if not self.skip and tag == 'a':
            self.anchor = [attrs.get('href', ''), []]

    def handle_endtag(self, tag):
        if tag in ('script', 'style'):
            if tag == 'script' and self.jsonld is not None:
                try:
                    self.structured.append(json.loads(''.join(self.jsonld)))
                except ValueError:
                    pass
                self.jsonld = None
            self.skip = max(0, self.skip - 1)
        if tag == 'a' and self.anchor:
            self.links.append((self.anchor[0], ''.join(self.anchor[1])))
            self.anchor = None

    def handle_data(self, data):
        if self.jsonld is not None:
            self.jsonld.append(data)
        elif not self.skip and self.anchor:
            self.anchor[1].append(data)


def extract(source, text):
    found = []
    if source['adapter'] == 'location_labels':
        from source_adapters import location_labels
        found = location_labels(source, text)
    elif source['adapter'] == 'feed':
        if re.search(r'<!DOCTYPE|<!ENTITY', text, re.I):
            raise ValueError('DTD/entity feeds are not supported')
        root = ET.fromstring(text)
        for item in root.iter():
            if item.tag.split('}')[-1] not in ('item', 'entry'):
                continue
            values = {e.tag.split('}')[-1]: e for e in item}
            title = values.get('title')
            link = values.get('link')
            if title is not None and link is not None:
                found.append({'url': link.attrib.get('href') or link.text or '', 'label': ''.join(title.itertext())})
    else:
        page = Page(); page.feed(text)
        if source['adapter'] == 'links':
            for href, label in page.links:
                url = link_url(source['url'], href)
                if url and link_allowed(source, url, label):
                    found.append({'url': url, 'label': label})
            if source.get('supplemental_place_labels'):
                from source_adapters import location_labels,norm
                # Some reviewed roster members have visible text but no branch href.
                labels={label:place for label,place in source['supplemental_place_labels'].items()
                        if not any(norm(label) in norm(item['label']) for item in found)}
                found.extend(location_labels({**source,'place_labels':labels},text))
        else:
            def walk(node):
                if isinstance(node, list):
                    for child in node: walk(child)
                elif isinstance(node, dict):
                    kinds = node.get('@type', [])
                    if isinstance(kinds, str): kinds = [kinds]
                    address = node.get('address')
                    if any(t in ('Organization', 'LocalBusiness', 'ProfessionalService') for t in kinds) and isinstance(address, dict):
                        country = address.get('addressCountry', '')
                        if isinstance(country, dict): country = country.get('name', '')
                        found.append({'url': node.get('url') or source['url'], 'label': node.get('name', ''),
                                      'city': address.get('addressLocality', ''), 'country': country})
                    for child in node.values():
                        if isinstance(child, (dict, list)): walk(child)
            for node in page.structured: walk(node)
    output = {}
    for item in found:
        url = link_url(source['url'], item['url'])
        label = clean(item['label']) if isinstance(item['label'], str) else ''
        if not url or not label:
            continue
        value = {'url': url, 'label': label, 'city': clean(str(item.get('city', ''))), 'country': clean(str(item.get('country', '')))}
        for field in ('unit_key','observation_kind','claim_terms','place_basis','status_terms'):
            if field in item:value[field]=item[field]
        identity=[url, value['city'], value['country']]
        if value.get('unit_key'):identity.append(value['unit_key'])
        key = digest(identity)
        output.setdefault(key, value)
        if len(output) > MAX_ITEMS:
            raise ValueError('too many extracted candidates; narrow the source adapter')
    return list(output.values())


def signals(label):
    patterns = {'possible_closure': r'\b(clos(?:e[ds]?|ing|ure)|shut(?:s|ting)? down|ceas(?:e[ds]?|ing))\b',
                'possible_acquisition': r'\b(acquir\w*|acquisition|merg\w*)\b',
                'possible_opening': r'\bupcoming\b|\b(open(?:s|ed|ing)?|launch(?:es|ed|ing)?)\b.*\b(studio|facility|stage|branch)\b|\bnew (?:studio|facility|stage|branch)\b',
                'possible_rebrand': r'\b(rebrand\w*|renam\w*|formerly)\b',
                'possible_relocation': r'\b(relocat\w*|mov(?:e[ds]?|ing) (?:to|from)|new (?:studio|office|branch|facility))\b'}
    return [key for key, pattern in patterns.items() if re.search(pattern, label, re.I)]


def scan(config, previous, database, fetcher=None, today=None, detect_absence=True):
    load_config(config)
    today = today or date.today().isoformat()
    fetcher = fetcher or Fetcher()
    state = copy.deepcopy(previous)
    if state.get('version') != 1 or not isinstance(state.get('candidates'), dict):
        raise ValueError('invalid discovery state')
    state.setdefault('sources', {})
    report = {'observed_on': today, 'events': [], 'sources': [], 'published_records': 0}
    for source in config['sources']:
        if not source['enabled']:
            continue
        status = {'id': source['id'], 'url': source['url'], 'attempted_on': today}
        try:
            body = fetcher(source)
            observations = extract(source, body)
            extraction_hash = digest({k: source.get(k) for k in ('url', 'adapter', 'link_pattern', 'link_label_pattern', 'place_labels', 'roster_sentence_pattern', 'supplemental_place_labels')})
            old_status = state['sources'].get(source['id'], {})
            rules_changed = bool(old_status) and old_status.get('extraction_hash') != extraction_hash
            if rules_changed:
                report['events'].append({'source_id': source['id'], 'type': 'extraction_rules_changed', 'note': 'Retain omitted candidates; filtering changes are not disappearance evidence.'})
            seen = set()
            for item in observations:
                identity=[source['id'], item['url'], item['city'], item['country']]
                if item.get('unit_key'):identity.append(item['unit_key'])
                cid = 'discovery-' + digest(identity)[:24]
                seen.add(cid)
                old = state['candidates'].get(cid)
                content_hash = digest(item)
                event = 'new_candidate' if old is None else 'evidence_changed' if old['content_hash'] != content_hash else 'reappeared' if old.get('missing_since') else None
                candidate = {**item, 'id': cid, 'source_id': source['id'], 'source_kind': source['kind'],
                             'hint_company_id': source.get('company_id', ''), 'confidence': 'unknown',
                             'first_seen': old['first_seen'] if old else today, 'last_seen': today,
                             'content_hash': content_hash, 'signals': signals(item['label']+' '+' '.join(item.get('status_terms',[]))),
                             'review_status': 'pending', 'missing_since': None}
                # The matching is advisory only; source IDs/labels never become public studio IDs.
                candidate['existing_matches'] = [r['id'] for r in database if
                    item['url'].rstrip('/') in (r['website'].rstrip('/'), r.get('evidence', '').rstrip('/')) or
                    (item['city'] and item['country'] and item['city'].casefold() == r['city'].casefold() and item['country'].casefold() == r['country'].casefold() and source.get('company_id') == r['company_id'])]
                state['candidates'][cid] = candidate
                if event:
                    report['events'].append({'id': cid, 'type': event, 'previous_hash': old['content_hash'] if old else None, 'content_hash': content_hash, 'signals': candidate['signals']})
            # Empty/failed extraction may indicate a redesign, never a mass closure.
            if observations and not rules_changed and detect_absence:
                for cid, candidate in state['candidates'].items():
                    if source['adapter'] == 'location_labels' and candidate.get('observation_kind') != 'location_reference':
                        continue
                    if source['adapter'] == 'links' and candidate.get('observation_kind')!='location_reference' and not link_allowed(source, candidate['url'], candidate['label']):
                        continue  # historical filtered-out navigation is not a missing studio
                    if candidate['source_id'] == source['id'] and cid not in seen and not candidate.get('missing_since'):
                        candidate['missing_since'] = today
                        report['events'].append({'id': cid, 'type': 'missing_from_source', 'note': 'Review required; absence is not closure evidence.'})
            status.update(status='ok' if observations else 'extraction_empty', candidate_count=len(observations), body_sha256=hashlib.sha256(body.encode()).hexdigest(), extraction_hash=extraction_hash)
            if state['sources'].get(source['id'], {}).get('body_sha256') not in (None, status['body_sha256']):
                report['events'].append({'source_id': source['id'], 'type': 'page_changed', 'note': 'Page bytes changed; business status is not inferred.'})
        except (OSError, ValueError, LookupError, ET.ParseError) as exc:
            # Never store response bodies, request headers or arbitrary error text in public reports.
            status.update(status='fetch_or_parse_error', error_type=type(exc).__name__, note='Source unavailable, blocked or unsupported; retain candidates and review access/adapter.')
        old_status = state['sources'].get(source['id'], {})
        state['sources'][source['id']] = {**old_status, **status}
        report['sources'].append(status)
    report['pending_candidates'] = len(state['candidates'])
    return state, report


def seed_backlog(queue):
    candidates = {}
    for item in queue:
        if item['decision'] != 'defer':
            continue
        observation = {'url': item['sources'][0], 'label': item['organisation'] + ' — ' + item['candidate'], 'city': '', 'country': ''}
        cid = 'backlog-' + digest([item['organisation'], item['candidate']])[:24]
        candidates[cid] = {**observation, 'id': cid, 'source_id': 'v08-review-backlog', 'source_kind': 'manual_backlog',
                           'hint_company_id': '', 'confidence': 'unknown', 'first_seen': item['reviewed_on'],
                           'last_seen': item['reviewed_on'], 'content_hash': digest(observation), 'signals': [],
                           'review_status': 'pending', 'missing_since': None, 'existing_matches': [],
                           'reason': item['reason'], 'sources': item['sources']}
    return {'version': 1, 'sources': {}, 'candidates': candidates}


def prepare(database, queue, records, reviews, today=None):
    """Build a proposal only after explicit, content-bound human review of each row."""
    today = date.fromisoformat(today or date.today().isoformat())
    errors, warnings = validate(database)
    if errors:
        raise ValueError('canonical database is invalid')
    if not records or not isinstance(records, list) or not isinstance(reviews, list):
        raise ValueError('nonempty records and approval lists required')
    if len(records) != len(reviews) or len({r.get('record_id') for r in reviews}) != len(reviews):
        raise ValueError('exactly one approval per record required')
    approvals = {r['record_id']: r for r in reviews}
    if len({r.get('id') for r in records}) != len(records):
        raise ValueError('duplicate proposed record ID')
    baseline = digest(database)
    by_id = {r['id']: r for r in database}
    additions, updates, distinct = [], [], []
    audit = []
    for record in records:
        if set(record) - (set(CSV_FIELDS) | {'legacy_research'}):
            raise ValueError('unknown record fields are excluded from automated proposals')
        errors, _ = validate([record])
        if errors:
            raise ValueError('invalid proposed record: ' + '; '.join(errors))
        review = approvals.get(record['id'], {})
        candidate = queue.get('candidates', {}).get(review.get('candidate_id'))
        if not candidate or candidate.get('missing_since'):
            raise ValueError('candidate missing or withdrawn; re-research required')
        if review.get('decision') != 'approved' or not isinstance(review.get('reviewed_by'), str) or not review['reviewed_by'].strip() or not review.get('reason'):
            raise ValueError('explicit named approval and public rationale required')
        reviewed = date.fromisoformat(review.get('reviewed_on', ''))
        observed = date.fromisoformat(candidate['last_seen'])
        if not 0 <= (today - reviewed).days <= 30 or not 0 <= (today - observed).days <= 30 or reviewed < observed:
            raise ValueError('review/evidence stale, future dated or predates observation')
        if any(review.get('checks', {}).get(check) is not True for check in CHECKS):
            raise ValueError('all evidence checks require explicit review')
        if review.get('candidate_hash') != digest(candidate) or review.get('record_hash') != digest(record) or review.get('database_hash') != baseline:
            raise ValueError('approval does not match candidate, record or current database')
        if record.get('evidence_state') not in ('confirmed', 'likely') or record.get('verified_on') != reviewed.isoformat():
            raise ValueError('publication requires dated location evidence, not discovery confidence')
        if record.get('email') or record.get('phone'):
            raise ValueError('automated proposals exclude personal/contact fields')
        action = review.get('action')
        if action == 'add':
            if record['id'] in by_id:
                raise ValueError('add cannot overwrite an existing record')
            additions.append(record)
            if review.get('allow_distinct_location') is True:
                if not review.get('distinct_reason'):
                    raise ValueError('distinct facility override requires a rationale')
                distinct.append(record['id'])
        elif action == 'update':
            if record['id'] not in by_id or review.get('previous_record_hash') != digest(by_id[record['id']]):
                raise ValueError('update requires matching previous record hash')
            if record['company_id'] != by_id[record['id']]['company_id'] and not review.get('identity_change_reason'):
                raise ValueError('organisation identity change requires rationale')
            updates.append(record)
        else:
            raise ValueError('only explicit add/update actions supported; no automatic deletion')
        audit.append(review)
    replacements = {r['id']: r for r in updates}
    revised = [replacements.get(r['id'], r) for r in database]
    # Updates also need duplicate review against OTHER locations; no silent consolidation.
    for record in updates:
        matches = DuplicateIndex(r for r in revised if r['id'] != record['id']).matches(record)
        review = approvals[record['id']]
        if matches and not (review.get('allow_distinct_location') is True and review.get('distinct_reason')):
            raise ValueError('updated record has potential duplicates; explicit review required')
    combined, preview = plan_import(revised, additions, distinct)
    if preview['database_errors'] or preview['rejected_records'] or any(not d['allowed_as_distinct'] for d in preview['potential_duplicates']):
        raise ValueError('proposal blocked by importer validation/duplicate checks')
    _, repeat = plan_import(combined, additions, distinct)
    if repeat['new_records'] or repeat['rejected_records'] or repeat['database_errors']:
        raise ValueError('repeat import is not idempotent')
    return combined, {'baseline_hash': baseline, 'proposed_hash': digest(combined), 'approved_additions': [r['id'] for r in additions],
                      'approved_updates': [r['id'] for r in updates], 'approvals': audit, 'import_preview': preview, 'import_repeat': repeat,
                      'reviewed_candidates': {r['candidate_id']: queue['candidates'][r['candidate_id']] for r in audit},
                      'record_changes': [{'id': r['id'], 'before': by_id.get(r['id']), 'after': r} for r in records],
                      'validation_warnings': validate(combined)[1], 'publication': 'proposal_only; human PR review and merge required'}, additions


def safe_output(output, inputs):
    target = Path(output).resolve()
    for path in [ROOT / 'studios.json', *inputs]:
        path = Path(path).resolve()
        if target == path or target in path.parents:
            raise ValueError('output must not replace an input or canonical database')


def archive_history(previous_run, output):
    """Carry immutable raw queue/report snapshots forward with every artifact."""
    previous_run, output = Path(previous_run), Path(output)
    paths = [previous_run/'queue.json', previous_run/'report.json', previous_run/'recovery.json']
    paths += sorted((previous_run/'history').glob('*.json'))
    for path in paths:
        if path.is_symlink():
            raise ValueError('history must contain regular local files')
        if not path.is_file():
            continue
        body = path.read_bytes()
        json.loads(body)  # preserve exact bytes only after checking valid JSON
        folder = output/'history'
        folder.mkdir(parents=True, exist_ok=True)
        (folder/(hashlib.sha256(body).hexdigest()+'.json')).write_bytes(body)


def merge_checkpoint(state, checkpoint):
    """Add committed PR discoveries without replacing newer run evidence or approvals."""
    for queue in (state,checkpoint):
        if queue.get('version')!=1 or not isinstance(queue.get('candidates'),dict):
            raise ValueError('invalid discovery checkpoint')
    merged=copy.deepcopy(state);added=[];earlier=[]
    for cid,candidate in checkpoint['candidates'].items():
        if not isinstance(candidate,dict) or candidate.get('id')!=cid or not url_valid(candidate.get('url')):
            raise ValueError('invalid checkpoint candidate')
        first=date.fromisoformat(candidate['first_seen'])
        if cid not in merged['candidates']:
            merged['candidates'][cid]=copy.deepcopy(candidate);added.append(cid)
        elif first<date.fromisoformat(merged['candidates'][cid]['first_seen']):
            merged['candidates'][cid]['first_seen']=first.isoformat();earlier.append(cid)
    return merged,{'added_candidate_ids':added,'earlier_first_seen_ids':earlier,
                   'note':'Existing run evidence/reviews retained; checkpoint is not business or publication approval.'}


def review_template(database, queue, records, candidate_ids):
    if len(records) != len(candidate_ids) or not records:
        raise ValueError('provide one candidate ID per proposed record, in the same order')
    by_id = {r['id']: r for r in database}
    reviews = []
    for record, cid in zip(records, candidate_ids):
        candidate = queue['candidates'][cid]
        old = by_id.get(record['id'])
        reviews.append({'record_id': record['id'], 'candidate_id': cid,
                        'action': 'update' if old else 'add', 'decision': 'pending',
                        'candidate_hash': digest(candidate), 'record_hash': digest(record),
                        'database_hash': digest(database), 'previous_record_hash': digest(old) if old else None,
                        'reviewed_by': '', 'reviewed_on': '', 'reason': '',
                        'checks': {check: False for check in CHECKS},
                        'allow_distinct_location': False, 'distinct_reason': ''})
    return reviews


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    scan_cmd = commands.add_parser('scan', help='fetch explicitly enabled sources; queue only')
    scan_cmd.add_argument('--config', type=Path, default=ROOT / 'data/discovery/sources.json')
    scan_cmd.add_argument('--state', type=Path, default=ROOT / 'data/discovery/backlog.json')
    scan_cmd.add_argument('--database', type=Path, default=ROOT / 'studios.json')
    scan_cmd.add_argument('--output', type=Path, required=True)
    scan_cmd.add_argument('--previous-run', type=Path, help='archive prior queue/report and carry history forward')
    scan_cmd.add_argument('--suppress-missing',action='store_true',help='after partial recovery, do not infer missing-evidence events')
    scan_cmd.add_argument('--checkpoint',type=Path,help='merge missing committed PR observations without resetting run history')
    proposal = commands.add_parser('prepare', help='prepare an approved proposal, never publish')
    for flag in ('queue', 'records', 'reviews'):
        proposal.add_argument('--' + flag, type=Path, required=True)
    proposal.add_argument('--database', type=Path, default=ROOT / 'studios.json')
    proposal.add_argument('--output', type=Path, required=True)
    template = commands.add_parser('review-template', help='snapshot a bundle with PENDING reviews; grants no approval')
    for flag in ('queue', 'records'):
        template.add_argument('--' + flag, type=Path, required=True)
    template.add_argument('--candidate', action='append', required=True, help='one ID per record, in order')
    template.add_argument('--database', type=Path, default=ROOT / 'studios.json')
    template.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    try:
        paths = [v for k, v in vars(args).items() if isinstance(v, Path) and k != 'output']
        safe_output(args.output, paths)
        # Require a new directory: don't leave stale outputs after failed preparation.
        if args.output.exists():
            raise ValueError('output directory already exists; choose a fresh run directory')
        database = read(args.database)
        if args.command == 'scan':
            errors, _ = validate(database)
            if errors: raise ValueError('invalid canonical database')
            previous=read(args.state);checkpoint_audit=None
            if args.checkpoint:previous,checkpoint_audit=merge_checkpoint(previous,read(args.checkpoint))
            state, report = scan(read(args.config), previous, database, detect_absence=not args.suppress_missing)
            if checkpoint_audit:report['checkpoint_merge']=checkpoint_audit
            write(args.output / 'queue.json', state)
            write(args.output / 'report.json', report)
            if args.previous_run:
                archive_history(args.previous_run, args.output)
            if args.checkpoint:
                body=args.checkpoint.read_bytes();folder=args.output/'history';folder.mkdir(exist_ok=True)
                (folder/(hashlib.sha256(body).hexdigest()+'.json')).write_bytes(body)
            print(json.dumps({'pending': report['pending_candidates'], 'source_status': report['sources'], 'published': 0}))
        elif args.command == 'review-template':
            queue, records = read(args.queue), read(args.records)
            reviews = review_template(database, queue, records, args.candidate)
            write(args.output / 'queue.json', queue)
            write(args.output / 'records.json', records)
            write(args.output / 'reviews.json', reviews)
            print('Review bundle created with PENDING decisions and unchecked evidence. Not approved.')
        else:
            combined, report, additions = prepare(database, read(args.queue), read(args.records), read(args.reviews))
            write(args.output / 'studios.json', combined)
            write(args.output / 'report.json', report)
            with (args.output / 'batch.csv').open('w', encoding='utf-8', newline='') as stream:
                writer = csv.DictWriter(stream, fieldnames=CSV_FIELDS, extrasaction='ignore')
                writer.writeheader()
                for row in additions:
                    row = copy.deepcopy(row)
                    for key in ('categories', 'capabilities'): row[key] = '|'.join(row[key])
                    for key in ('capability_evidence', 'relationships'):
                        if key in row: row[key] = json.dumps(row[key], ensure_ascii=False)
                    writer.writerow(row)
            print(json.dumps({'new': report['approved_additions'], 'updates': report['approved_updates'], 'published': 0}))
        return 0
    except (OSError, ValueError, TypeError, KeyError) as exc:
        print(f'Discovery blocked: {exc}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
