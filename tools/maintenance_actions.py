#!/usr/bin/env python3
"""GitHub I/O for bounded maintenance archives and research-only draft PRs.

No review, merge, deletion, workflow dispatch, crawler or public-data write API.
"""
import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import tempfile
from datetime import date
from pathlib import Path

from discovery import ROOT, read, write, digest, merge_checkpoint
from global_programme import check_state, empty_state
from maintenance import HOME, config, fresh_output, verify, seal, validate_discovery

REPOSITORY = 'halfGuardian/motionx-studio-atlas'


def run(args, runner=subprocess.run, check=True):
    # Error bodies/headers can contain credentials. Surface only the operation
    # and numeric status; GitHub's own job authorization error remains available.
    result = runner(args, capture_output=True, text=True)
    if check and result.returncode:
        reason = next((s for s in ('GitHub Actions is not permitted to create or approve pull requests', 'Resource not accessible by integration', 'HTTP 403', 'HTTP 401', 'HTTP 429', 'Could not resolve host') if s in (result.stderr or '')), 'Inspect Actions permissions/network')
        raise ValueError('Command failed (' + str(result.returncode) + '): ' + ' '.join(args[:3]) + '. ' + reason + '; no data published.')
    return result


def api(path, runner):
    return json.loads(run(['gh', 'api', 'repos/' + REPOSITORY + '/' + path], runner).stdout)


def eligible(metadata):
    return metadata.get('head_branch') == 'main' and metadata.get('path') == '.github/workflows/discovery.yml' and metadata.get('status') == 'completed' and metadata.get('event') in ('schedule', 'workflow_dispatch') and metadata.get('head_repository', {}).get('full_name') == REPOSITORY


def restore(output, runner=subprocess.run):
    """Failed scans may still hold valid partial evidence. Never skip it silently."""
    out = fresh_output(output); attempts = []
    runs = json.loads(run(['gh', 'run', 'list', '--repo', REPOSITORY, '--workflow', 'discovery.yml', '--branch', 'main', '--limit', '20', '--json', 'databaseId'], runner).stdout)
    if not isinstance(runs, list): raise ValueError('Invalid Actions history response; do not reset state')
    for row in runs:
        rid = row.get('databaseId')
        if type(rid) is not int or rid <= 0: raise ValueError('Invalid source run ID')
        meta = api('actions/runs/' + str(rid), runner)
        if not eligible(meta): continue
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / 'archive'
            result = run(['gh', 'run', 'download', str(rid), '--repo', REPOSITORY, '--name', 'atlas-maintenance', '--dir', str(target)], runner, False)
            if result.returncode == 0:
                try:
                    verify(target)
                    artifacts = api('actions/runs/' + str(rid) + '/artifacts?per_page=100', runner)
                    artifact = next(a for a in artifacts['artifacts'] if a['name'] == 'atlas-maintenance')
                    shutil.copytree(target, out / 'maintenance')
                    write(out / 'recovery.json', {'mode': 'verified_actions_artifact', 'source_run_id': rid,
                        'source_run_conclusion': meta['conclusion'], 'artifact_expires_at': artifact['expires_at'],
                        'attempts': attempts, 'history_complete': False, 'suppress_absence_signals': True,
                        'note': 'Integrity verified. Earlier or skipped history is not independently proven complete; no closure inference.', 'published_records': 0})
                    return out
                except (ValueError, OSError, KeyError, StopIteration, TypeError):
                    attempts.append({'run_id': rid, 'reason': 'invalid_or_incomplete_archive'}); continue
            attempts.append({'run_id': rid, 'reason': 'artifact_unavailable_or_expired'})
    # Merged monthly research PRs are durable checkpoints after Actions expiry.
    for folder in sorted((HOME / 'batches').glob('????-??'), reverse=True):
        try:
            verify(folder); shutil.copytree(folder, out / 'maintenance')
            write(out / 'recovery.json', {'mode': 'committed_monthly_checkpoint', 'checkpoint': str(folder.relative_to(ROOT)),
                'attempts': attempts, 'history_complete': False, 'suppress_absence_signals': True,
                'note': 'Any newer unarchived history is unavailable; it is not reconstructed or considered complete.', 'published_records': 0})
            return out
        except (ValueError, OSError, KeyError, TypeError): continue
    # Original bytes survive independently of the 90-day Actions retention.
    for original in sorted((HOME / 'inputs').glob('discovery-*'), reverse=True):
        try:
            validate_discovery(original); receipt = read(original / 'receipt.json')
            files = {p.relative_to(original).as_posix() for p in original.rglob('*.json') if p.name != 'receipt.json'}
            if set(receipt['files']) != files: raise ValueError('Incomplete committed discovery receipt')
            for name, expected in receipt['files'].items():
                if hashlib.sha256((original / name).read_bytes()).hexdigest() != expected:
                    raise ValueError('Committed discovery checkpoint corrupt')
            write(out / 'maintenance/state.json', empty_state())
            shutil.copytree(original, out / 'maintenance/discovery')
            write(out / 'recovery.json', {'mode': 'committed_discovery_bootstrap', 'source_run_id': receipt['run_id'],
                'attempts': attempts, 'history_complete': False, 'suppress_absence_signals': True,
                'note': 'Latest available hash-bound raw discovery checkpoint retained. Any newer missing history is unresolved; no successful v2 run is invented.', 'published_records': 0})
            return out
        except (ValueError, OSError, KeyError, TypeError): attempts.append({'checkpoint': original.name, 'reason': 'invalid_committed_discovery_checkpoint'})
    raise ValueError('No valid discovery checkpoint remains; owner recovery required without resetting history')


def month(value):
    if not re.fullmatch(r'\d{4}-(?:0[1-9]|1[0-2])', value): raise ValueError('Period must be YYYY-MM')
    return value


def join_discovery(primary, maintenance):
    """Recover the complete raw candidate union after either artifact expires."""
    primary = Path(primary); other = Path(maintenance) / 'discovery'
    validate_discovery(primary); validate_discovery(other)
    from checkpoints import check_queue
    left = check_queue(read(primary / 'queue.json')); right = check_queue(read(other / 'queue.json'))
    merged, _ = merge_checkpoint(left, right)
    conflicts = []
    for cid, candidate in right['candidates'].items():
        if cid in left['candidates'] and candidate['last_seen'] > left['candidates'][cid]['last_seen']:
            merged['candidates'][cid] = {**candidate, 'first_seen': min(candidate['first_seen'], left['candidates'][cid]['first_seen'])}
        elif cid in left['candidates'] and candidate['last_seen'] == left['candidates'][cid]['last_seen'] and candidate['content_hash'] != left['candidates'][cid]['content_hash']:
            conflicts.append(cid)
    for folder in (primary, other):
        # Snapshot the old mutable views before writing the merged queue.
        for p in list(folder.rglob('*.json')):
            if p.parent == primary / 'history': continue
            body = p.read_bytes(); target = primary / 'history' / (hashlib.sha256(body).hexdigest() + '.json')
            target.parent.mkdir(exist_ok=True); target.write_bytes(body)
    write(primary / 'queue.json', merged)
    recovery = read(primary / 'recovery.json') if (primary / 'recovery.json').exists() else {}
    write(primary / 'recovery.json', {**recovery, 'continuity_version': 2, 'history_complete': False, 'suppress_absence_signals': True, 'checkpoint_union_preserved': True})
    return {'retained_candidates': len(merged['candidates']), 'same_date_conflicts_for_review': conflicts, 'published_records': 0, 'history_complete': False}


def confined(path, relative):
    return path == relative or path.startswith(relative + '/')


def propose(folder, period, runner=subprocess.run, root=ROOT, c=None):
    """One open batch, one stable branch/period. Non-force updates to drafts only."""
    c = c or config(); period = month(period); folder = Path(folder); verify(folder)
    if os.environ.get('GITHUB_REPOSITORY', REPOSITORY) != REPOSITORY:
        raise ValueError('Unexpected repository; no writes')
    branch = c['monthly']['branch_prefix'] + period; relative = 'data/maintenance/batches/' + period
    if run(['git', 'status', '--porcelain'], runner).stdout.strip(): raise ValueError('Clean checkout required')
    for previous in sorted((root / 'data/maintenance/batches').glob('????-??'), reverse=True):
        if previous.name == period: continue
        verify(previous)
        if read(previous / 'report.json')['content_fingerprint'] == read(folder / 'report.json')['content_fingerprint']:
            return {'status': 'no_new_research_content', 'publication': False}
        break
    current = json.loads(run(['gh', 'pr', 'list', '--repo', REPOSITORY, '--state', 'all', '--head', branch, '--json', 'number,state,isDraft,isCrossRepository,baseRefName,headRefOid'], runner).stdout)
    if len(current) > 1: raise ValueError('Multiple PRs for this batch; owner reconciliation required')
    if current and current[0]['state'] != 'OPEN': return {'status': 'period_already_closed', 'publication': False}
    if current and (not current[0]['isDraft'] or current[0].get('isCrossRepository') is not False or current[0]['baseRefName'] != 'main'):
        raise ValueError('Batch is in human review or retargeted; automation will not change it')
    open_prs = json.loads(run(['gh', 'pr', 'list', '--repo', REPOSITORY, '--state', 'open', '--limit', '100', '--json', 'number,headRefName'], runner).stdout)
    if len(open_prs) == 100: raise ValueError('Open PR inventory truncated; cannot safely enforce one open batch')
    if any(p['headRefName'].startswith(c['monthly']['branch_prefix']) and p['headRefName'] != branch for p in open_prs):
        return {'status': 'previous_batch_awaits_owner_review', 'publication': False}
    if current:
        run(['git', 'fetch', 'origin', branch], runner); run(['git', 'switch', '-C', branch, 'FETCH_HEAD'], runner)
        if run(['git', 'rev-parse', 'HEAD'], runner).stdout.strip() != current[0]['headRefOid']:
            raise ValueError('PR head changed during preparation; retry without overwriting it')
        changed = run(['git', 'diff', '--name-only', 'origin/main...HEAD'], runner).stdout.splitlines()
        if any(not confined(p, relative) for p in changed): raise ValueError('Existing branch has changes outside its batch; owner review required')
    else:
        # A push succeeded but PR creation may have failed. Resume that branch
        # after identical scope checks instead of force-pushing a replacement.
        remote = run(['git', 'ls-remote', '--heads', 'origin', 'refs/heads/' + branch], runner).stdout.strip()
        if remote:
            run(['git', 'fetch', 'origin', branch], runner); run(['git', 'switch', '-C', branch, 'FETCH_HEAD'], runner)
            if any(not confined(p, relative) for p in run(['git', 'diff', '--name-only', 'origin/main...HEAD'], runner).stdout.splitlines()):
                raise ValueError('Unattached batch branch contains unexpected changes')
        else: run(['git', 'switch', '-c', branch], runner)
    target = root / relative; report = read(folder / 'report.json')
    remove_after_archive = []
    if target.exists():
        verify(target); old = read(target / 'report.json'); a = check_state(read(target / 'state.json')); b = check_state(read(folder / 'state.json'))
        if b['history'][:len(a['history'])] != a['history']:
            raise ValueError('Older/missing state cannot overwrite batch history')
        if old['content_fingerprint'] == report['content_fingerprint']:
            if current: return {'status': 'unchanged', 'pr_number': current[0]['number'], 'publication': False}
            # Recover an existing pushed branch whose PR creation was denied.
        else:
            write(folder / 'revisions' / (digest(old) + '.json'), old)
        # Preserve every previous review revision and raw history file.
        for p in target.rglob('*'):
            if not p.is_file(): continue
            rel = p.relative_to(target)
            if rel.parts[0] in ('revisions',) or rel.parts[:2] == ('discovery', 'history'):
                destination = folder / rel
                if destination.exists() and destination.read_bytes() != p.read_bytes(): raise ValueError('Historical archive path collision')
                destination.parent.mkdir(parents=True, exist_ok=True); shutil.copyfile(p, destination)
            elif rel.parts[0] == 'discovery':
                # Archive superseded queue/report/receipt bytes before changing
                # the mutable view. Nothing historical is discarded.
                destination = folder / 'discovery/history' / (hashlib.sha256(p.read_bytes()).hexdigest() + '.json')
                destination.parent.mkdir(parents=True, exist_ok=True); shutil.copyfile(p, destination)
                if not (folder / rel).exists(): remove_after_archive.append(target / rel)
    seal(folder); target.mkdir(parents=True, exist_ok=True)
    shutil.copytree(folder, target, dirs_exist_ok=True)
    for p in remove_after_archive: p.unlink()  # exact bytes preserved above
    verify(target)
    run(['git', 'add', '--', relative], runner)
    staged = run(['git', 'diff', '--cached', '--name-only'], runner).stdout.splitlines()
    if any(not confined(p, relative) for p in staged): raise ValueError('Refusing non-research changes')
    if staged:
        run(['git', '-c', 'user.name=github-actions[bot]', '-c', 'user.email=41898282+github-actions[bot]@users.noreply.github.com', 'commit', '-m', 'Stage monthly Atlas research ' + period], runner)
        if current:
            latest = json.loads(run(['gh', 'pr', 'view', str(current[0]['number']), '--repo', REPOSITORY, '--json', 'isDraft,headRefOid'], runner).stdout)
            if latest.get('isDraft') is not True or latest.get('headRefOid') != current[0]['headRefOid']:
                raise ValueError('Owner review/head changed before push; no remote update')
        run(['git', 'push', 'origin', 'HEAD:refs/heads/' + branch], runner)
    body = ('Monthly research only; company data and live Atlas remain unchanged.\n\n'
        + json.dumps(report['summary'], indent=2) + '\n\nBundle hash: `' + read(folder / 'integrity.json')['content_hash'] + '`.'
        + '\n\nRead `' + relative + '/review.html` and `report.json` (also downloadable in Actions). Review identity matches, exact minimal proposals, source rights/dates, before/after assertions, audio-only evidence and location uncertainty. No source absence, name, test, bot or draft establishes business truth or owner approval.'
        + '\n\nMerging this PR archives research only. To publish company changes, prepare a separate exact-content data PR through the existing reviewed pipeline, inspect all public-asset diffs and manually authorise merge. Required-review enforcement must be configured/verified by the owner; draft status does not enforce it. GITHUB_TOKEN PRs may not trigger CI automatically. Before approval, run Actions > Validate public atlas > Run workflow on branch `' + branch + '` with `expected_sha` set to this PR\'s current full 40-character head SHA. Both validation and browser jobs must pass on that exact commit; repeat after any new commit. A successful main-branch run is insufficient. No automatic merge, deletion, closure, coordinate assignment or capability approval.\n')
    with tempfile.TemporaryDirectory() as tmp:
        body_path = Path(tmp) / 'body.md'; body_path.write_text(body, encoding='utf-8')
        if current: result = run(['gh', 'pr', 'edit', str(current[0]['number']), '--repo', REPOSITORY, '--body-file', str(body_path)], runner)
        else: result = run(['gh', 'pr', 'create', '--repo', REPOSITORY, '--draft', '--base', 'main', '--head', branch, '--title', 'MotionX Atlas maintenance — ' + period + ' owner review', '--body-file', str(body_path)], runner)
    return {'status': 'updated_draft' if current else 'created_draft', 'url': result.stdout.strip(), 'publication': False}


def main():
    p = argparse.ArgumentParser(description=__doc__); p.add_argument('command', choices=('restore', 'propose', 'join')); p.add_argument('--output', type=Path); p.add_argument('--folder', type=Path); p.add_argument('--discovery', type=Path); p.add_argument('--period', default=date.today().strftime('%Y-%m')); a = p.parse_args()
    try:
        if a.command == 'restore':
            if not a.output: p.error('--output required')
            out = restore(a.output); print(json.dumps(read(out / 'recovery.json')))
        elif a.command == 'join':
            if not a.folder or not a.discovery: p.error('--folder and --discovery required')
            print(json.dumps(join_discovery(a.discovery, a.folder)))
        else:
            if not a.folder: p.error('--folder required')
            print(json.dumps(propose(a.folder, a.period)))
    except (ValueError, OSError, KeyError, TypeError) as e:
        print('::error::Maintenance stopped safely: ' + str(e).replace('%', '%25').replace('\n', '%0A').replace('\r', '%0D')); raise SystemExit(1)


if __name__ == '__main__': main()
