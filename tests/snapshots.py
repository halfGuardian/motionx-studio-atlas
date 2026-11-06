"""Reconstruct the audited pre-v0.9.2 database for historical batch regressions."""
import copy
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def before_v092():
    rows = before_v093()[:129]
    evidence = json.loads((ROOT/'data/research/v0.9.2-batch-1/evidence.json').read_text())
    originals = evidence['before_updates']
    return [copy.deepcopy(originals.get(r['id'], r)) for r in rows]


def before_v093():
    rows = json.loads((ROOT/'studios.json').read_text())[:141]
    originals = json.loads((ROOT/'data/research/v0.9.3-global/evidence.json').read_text())['before_updates']
    return [copy.deepcopy(originals.get(r['id'], r)) for r in rows]
