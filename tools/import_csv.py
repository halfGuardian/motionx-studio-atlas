#!/usr/bin/env python3
"""Append a research CSV to studios.json; preview by default, never update records."""
import argparse
import json
import os
import sys
import tempfile
from pathlib import Path

from validate import DuplicateIndex, read_records, validate


def plan_import(existing, incoming, allow_distinct=()):
    errors, warnings = validate(existing)
    report = {'new_records': [], 'unchanged_records': [], 'potential_duplicates': [],
              'rejected_records': [], 'validation_warnings': warnings,
              'database_errors': errors, 'written': False}
    if errors:
        return existing, report
    combined = list(existing)
    by_id = {r['id']: r for r in existing}
    duplicate_index = DuplicateIndex(existing)
    for number, record in enumerate(incoming, 2):
        errors, warnings = validate([record])
        report['validation_warnings'].extend(warnings)
        ref = record.get('id') if isinstance(record, dict) else None
        if errors:
            report['rejected_records'].append({'line': number, 'id': ref, 'errors': errors})
            continue
        if ref in by_id:
            if record == by_id[ref]:
                report['unchanged_records'].append(ref)
            else:
                report['rejected_records'].append({'line': number, 'id': ref,
                    'errors': ['ID exists with different content; review an explicit edit separately']})
            continue
        # Includes earlier accepted rows in this batch, preventing within-batch duplicates.
        candidates = duplicate_index.matches(record)
        if candidates:
            report['potential_duplicates'].append({'id': ref, 'matches': candidates,
                                                   'allowed_as_distinct': ref in allow_distinct})
            if ref not in allow_distinct:
                continue
        combined.append(record)
        duplicate_index.add(record)
        by_id[ref] = record
        report['new_records'].append(ref)
    errors, warnings = validate(combined)
    report['database_errors'] = errors
    report['validation_warnings'] = list(dict.fromkeys(report['validation_warnings'] + warnings))
    return combined, report


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('csv', type=Path)
    p.add_argument('--database', type=Path, default=Path(__file__).resolve().parents[1] / 'studios.json')
    mode = p.add_mutually_exclusive_group()
    mode.add_argument('--dry-run', action='store_true', help='preview only (default)')
    mode.add_argument('--apply', action='store_true', help='write only if all rows pass review')
    p.add_argument('--report', type=Path, help='optional JSON report path')
    p.add_argument('--allow-distinct-location', action='append', default=[], metavar='ID',
                   help='explicitly approve a flagged location as distinct; never bypasses ID conflicts')
    a = p.parse_args()
    if a.csv.resolve() == a.database.resolve() or (a.report and a.report.resolve() in {a.csv.resolve(), a.database.resolve()}):
        p.error('CSV, database and report must be different files')
    try:
        original = a.database.read_bytes()
        existing = json.loads(original)
        incoming = read_records(a.csv)
        combined, report = plan_import(existing, incoming, a.allow_distinct_location)
    except (OSError, ValueError) as exc:
        report = {'new_records': [], 'unchanged_records': [], 'potential_duplicates': [],
                  'rejected_records': [], 'validation_warnings': [],
                  'database_errors': [str(exc)], 'written': False}
    blocked = bool(report['database_errors'] or report['rejected_records'] or
                   any(not d['allowed_as_distinct'] for d in report['potential_duplicates']))
    report['mode'] = 'apply' if a.apply else 'dry-run'
    report['ready_to_apply'] = not blocked
    if a.apply and not blocked and report['new_records']:
        # Write beside the database and replace atomically; abort if the input changed.
        temporary = None
        try:
            with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', dir=a.database.parent,
                                             prefix='.motionx-import-', delete=False) as stream:
                temporary = Path(stream.name)
                json.dump(combined, stream, indent=2, ensure_ascii=False, allow_nan=False)
                stream.write('\n')
                stream.flush()
                os.fsync(stream.fileno())
            temporary.chmod(a.database.stat().st_mode & 0o777)
            if a.database.read_bytes() != original:
                raise ValueError('database changed during import; retry with a fresh preview')
            temporary.replace(a.database)
            report['written'] = True
        except (OSError, ValueError) as exc:
            report['database_errors'].append(str(exc))
            blocked = True
        finally:
            if temporary and temporary.exists():
                temporary.unlink()
    output = json.dumps(report, indent=2, ensure_ascii=False) + '\n'
    print(output, end='')
    if a.report:
        a.report.write_text(output, encoding='utf-8')
    return 1 if blocked else 0


if __name__ == '__main__':
    sys.exit(main())
