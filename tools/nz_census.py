#!/usr/bin/env python3
"""New Zealand source-to-Atlas identity coverage; read-only and source-scoped.

This tool does NOT crawl directories, add records, infer facilities, geocode or
approve reuse. It reconciles explicitly reviewed factual source snapshots
against the *complete* 42,239-record public index, including retained locations.
"""
import argparse
import csv
import hashlib
import html
import io
import json
import re
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HOME = ROOT / "data" / "nz-census"
SNAPSHOT = HOME / "inputs" / "wave1.json"
NZFC = ROOT / "data" / "coverage" / "nzfc-2026-11-07.json"
MANIFEST = ROOT / "data" / "public" / "manifest.json"
INDEX = ROOT / "data" / "public" / "index.json"
BASELINE = ROOT / "studios.json"

# These are suggested equivalences for discovery only. They do not merge
# organisations or justify transferring facility claims between branches.
ALIASES = {
    "albedovfx": ("Albedo",),
    "insidetrack": ("The Inside Track",),
    "thesoundroom": ("The Soundroom",),
    "yukfoo": ("Yukfoo",),
    "floatingrock": ("Floating Rock Studio",),
    "causeandfx": ("Cause + FX", "Cause & FX"),
    "mukpuddy": ("Mukpuddy Animation Ltd",),
    "mukpuddyanimationltd": ("Mukpuddy",),
}
HELD_IDENTITIES = {
    "blockhead": "NZFC Blockhead entry points at Assembly, while Screen Auckland identifies distinct Blockhead; official site currently documents Sydney, not a verified active NZ facility."
}
VALID_SCOPES = {"partial", "showcase_only", "complete_named_showreel_not_directory", "partial_selected_only"}


def read(path):
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def fold(value):
    value = unicodedata.normalize("NFKD", str(value or "")).casefold()
    value = "".join(x for x in value if not unicodedata.combining(x))
    return re.sub(r"[^a-z0-9]+", "", value.replace("&", "and").replace("+", "and"))


def load_atlas():
    manifest = read(MANIFEST)
    if hashlib.sha256(INDEX.read_bytes()).hexdigest() != manifest['index']['sha256']:
        raise ValueError('Public index integrity mismatch')
    if hashlib.sha256(BASELINE.read_bytes()).hexdigest() != manifest['baseline']['sha256']:
        raise ValueError('Retained baseline integrity mismatch')
    cols = manifest["index_columns"]
    if cols[:5] != ["id", "company_id", "name", "city", "country"]:
        raise ValueError("Unrecognised index schema")
    raw = read(INDEX)
    if len(raw) != manifest["index"]["records"]:
        raise ValueError("Incomplete public index")
    records = []
    for item in raw:
        if len(item) < len(cols):
            raise ValueError("Invalid index row")
        obj = dict(zip(cols, item))
        records.append({
            "id": obj["id"], "company_id": obj["company_id"],
            "name": obj["name"], "city": obj["city"], "country": obj["country"],
            "lat": obj["lat"], "lng": obj["lng"],
            "evidence_class": obj["evidence_class"],
            "record_kind": obj["record_kind"],
        })
    for base in read(BASELINE):
        records.append({
            "id": base["id"], "company_id": base["company_id"],
            "name": base["name"], "city": base["city"], "country": base["country"],
            "lat": base.get("lat"), "lng": base.get("lng"),
            "evidence_class": "A" if base.get("evidence_state") == "confirmed" else "C",
            "record_kind": "retained_location",
        })
    if len(records) != manifest["counts"]["records"]:
        raise ValueError("Catalogue count mismatch or baseline double-counted")
    ids = [r["id"] for r in records]
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate ID in source/retained index")
    # Wave 1 is a frozen baseline audit. The continuation separately verifies
    # every retained shard and all appended references against its checkpoint.
    records = [r for r in records if not r['id'].startswith(('nzcensus-','globalcompany-'))]
    if len(records) != 42239:
        raise ValueError('Historical 42,239-record cohort changed')
    manifest = dict(manifest, counts={**manifest['counts'], 'records':42239, 'company_references':1620})
    return manifest, records


def load_observations():
    data = read(SNAPSHOT)
    nzfc = read(NZFC)
    if data["reviewed_on"] != nzfc["observed_on"]:
        raise ValueError("Incompatible source checkpoint dates")
    sources = [{
        "id": "nzfc-facilities",
        "name": "NZ Film Commission facilities",
        "url": nzfc["source_url"], "completeness": "complete_source_snapshot",
        "detail": "All 42 published categories reconstructed in the v1.4 factual snapshot; identity and operation not human verified.",
        "records": [{
            "id": "nzfc-" + r["source_record_id"],
            "name": r["name"],
            "labels": r["nzfc_service_codes"],
            "source_url": nzfc["source_url"],
            "location_claim": "New Zealand vendor listing; no verified branch",
        } for r in nzfc["records"]]
    }]
    for s in data["sources"]:
        if s["completeness"] not in VALID_SCOPES:
            raise ValueError("Source must be explicitly bounded")
        if len(s["records"]) != s["observed_records"]:
            raise ValueError("Source enumeration mismatch: " + s["id"])
        sources.append(s)
    observations = []
    seen = set()
    for s in sources:
        for row in s["records"]:
            key = s["id"] + ":" + row["id"]
            if key in seen:
                raise ValueError("Duplicate source observation: " + key)
            seen.add(key)
            if not row.get("name") or not row.get("source_url", "").startswith("https://"):
                raise ValueError("Missing source identity/evidence for: " + key)
            observations.append({
                "observation_id": key,
                "source_id": s["id"],
                "name": row["name"],
                "service_labels": row["labels"],
                "source_url": row["source_url"],
                "detail_url": row.get("detail_url", ""),
                "site_url": row.get("site_url", ""),
                "location_claim": row["location_claim"],
                "observed_on": data["reviewed_on"],
                "source_scope": s["completeness"]
            })
    if len(sources) != 5 or len(observations) != 98:
        raise ValueError("Wave 1 expects 42 historical NZFC + 56 new source observations; do not silently change denominator")
    return sources, observations


def match(rows, observations):
    names = defaultdict(list)
    for r in rows:
        names[fold(r["name"])].append(r)
    result = []
    for o in observations:
        key = fold(o["name"])
        candidate_keys = [key] + [fold(x) for x in ALIASES.get(key, ())]
        seen = set()
        candidates = []
        for n in candidate_keys:
            for r in names.get(n, []):
                if r["id"] not in seen:
                    seen.add(r["id"])
                    candidates.append(r)
        nz = [r for r in candidates if fold(r["country"]) == "newzealand"]
        outside = [r for r in candidates if r["country"] and fold(r["country"]) != "newzealand"]
        no_country = [r for r in candidates if not r["country"]]
        if key in HELD_IDENTITIES:
            status = "identity_review_hold"
            rationale = HELD_IDENTITIES[key]
        elif nz:
            orgs = {r["company_id"] for r in nz}
            status = "represented_name_match" if len(orgs) == 1 else "multiple_nz_identity_candidates"
            rationale = ("NZ name or bounded alias appears in full catalogue; current operation and source-to-branch alignment not established."
                         if len(orgs) == 1 else "Multiple NZ organisation identities share a candidate name; human resolution required.")
        elif no_country:
            status = "country_unknown_name_candidate"
            rationale = "Name exists but catalogue geography is unspecified; cannot assert NZ branch."
        elif outside:
            status = "foreign_only_name_collision"
            rationale = "Only foreign-country matches exist; do not transfer their location to NZ."
        else:
            status = "no_name_match"
            rationale = "No exact/declared-alias identity in the 42,239 records; possible unrecognised alias remains."
        result.append({
            **o, "status": status, "rationale": rationale,
            "nz_record_ids": sorted(r["id"] for r in nz),
            "nz_identity_count": len({r["company_id"] for r in nz}),
            "nz_geolocated_record_count": sum(
                isinstance(r["lat"], (float, int)) and isinstance(r["lng"], (float, int))
                for r in nz
            ),
            "nz_reviewed_location_count": sum(r["evidence_class"] == "A" for r in nz),
            "foreign_record_ids": sorted(r["id"] for r in outside)[:12],
            "unknown_country_record_ids": sorted(r["id"] for r in no_country)[:12],
            "alias_keys_considered": [x for x in candidate_keys[1:] if x != key],
        })
    return result


def summarise(manifest, sources, observations, reconciled):
    by_source = {}
    for s in sources:
        candidates = [r for r in reconciled if r["source_id"] == s["id"]]
        by_source[s["id"]] = {
            "name": s["name"], "source_url": s["url"], "source_scope": s["completeness"],
            "observed_rows": len(candidates), "outcomes": dict(sorted(Counter(r["status"] for r in candidates).items())),
            "not_name_matched": [r["name"] for r in candidates if r["status"] == "no_name_match"],
            "identity_review": [r["name"] for r in candidates if r["status"] in (
                "identity_review_hold", "multiple_nz_identity_candidates",
                "country_unknown_name_candidate", "foreign_only_name_collision"
            )]
        }
    return {
        "atlas_records_scanned": manifest["counts"]["records"],
        "complete_index_records_examined": manifest["counts"]["records"],
        "source_observations": len(reconciled),
        "distinct_normalised_source_names": len({fold(o["name"]) for o in observations}),
        "source_snapshot_date": "2026-11-07",
        "source_wide_license": "UNSPECIFIED",
        "publication_approved": False,
        "new_atlas_records_created": 0,
        "new_geocodes_created": 0,
        "new_facility_claims_verified": 0,
        "matching_method": "Full-record exact-name/explicit-alias candidates; NZ country filtered; no website-only merge or inferred branch.",
        "source_outcomes": by_source,
        "total_statuses": dict(sorted(Counter(r["status"] for r in reconciled).items())),
        "limitations": [
            "These are source observation rows, not counts of independent active NZ businesses.",
            "Source listing is not independent current-operation or site-capability verification.",
            "Source record categories remain source claims, not Atlas confirmed capabilities.",
            "Screen Auckland pages 2,4,5 are not represented; directory coverage is partial.",
            "Wellington dynamic full directory could not be enumerated; only its nine showcase cards were reviewed.",
            "Regional showreel participants have not been audited for exact service specialization.",
            "Otago/Southland scan sampled two relevant directory entries and is not exhaustive.",
            "Name matching does not resolve all mergers, legal aliases, parent groups and foreign branch conflicts.",
            "Human review and source-rights assessment pending; no automatic publication.",
        ]
    }


def escape(s):
    return html.escape(str(s), quote=True)


def render_html(summary, results):
    source_rows = "".join(
        "<tr><td>" + escape(k) + "</td><td>" + escape(v["source_scope"]) +
        "</td><td>" + str(v["observed_rows"]) + "</td><td>" +
        escape(", ".join(k + ": " + str(n) for k, n in v["outcomes"].items())) +
        "</td></tr>" for k, v in summary["source_outcomes"].items()
    )
    items = "".join(
        '<tr data-status="' + escape(r["status"]) + '"><td>' + escape(r["source_id"]) +
        '</td><th scope="row">' + escape(r["name"]) + '</th><td>' +
        escape(", ".join(r["service_labels"])) + '</td><td>' + escape(r["status"]) +
        '</td><td>' + (", ".join('<a href="../../../index.html#/location/' + escape(x) +
        '">' + escape(x) + "</a>" for x in r["nz_record_ids"][:6]) or "Not matched to an NZ catalogue name") +
        '</td><td><a href="' + escape(r["source_url"]) + '">Original directory page</a></td></tr>'
        for r in results
    )
    return """<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>MotionX · NZ source coverage audit</title><style>
:root{color-scheme:dark;font:14px/1.5 system-ui;background:#101822;color:#edf1f8}body{max-width:1320px;margin:auto;padding:24px}
a{color:#addcff}table{border-collapse:collapse;width:100%;margin:15px 0 35px}th,td{border-bottom:1px solid #43516a;padding:11px;text-align:left;vertical-align:top}
thead{background:#23374b}input{background:#172333;border:1px solid #788ca5;border-radius:5px;color:inherit;padding:12px;max-width:100%;min-width:270px}
label{display:block;font-weight:bold}p{max-width:900px;color:#becad9}.scroll{overflow:auto}table{min-width:900px}
.status{padding:12px;border:1px solid #5a6b82;border-radius:8px}a:focus-visible,input:focus-visible{outline:3px solid #ffd77a}
</style><h1>New Zealand source-to-Atlas audit · Wave 1</h1>
<p>Observed 7 Nov 2026. A name match does not prove a current physical studio. Partial source views remain partial, and rejected/ambiguous identities are not silently removed. No Atlas entries or map pins were added automatically.</p>
<p class="status"><strong>""" + escape(str(summary["source_observations"])) + """ source observations</strong> across five bounded source snapshots; """ + escape(str(summary["distinct_normalised_source_names"])) + """ distinct normalised names. Of the original 42,239 records, zero were rewritten.</p>
<h2>Per-source accounting</h2><div class="scroll"><table><thead><tr><th>Source</th><th>Coverage scope</th><th>Rows</th><th>Matching dispositions</th></tr></thead><tbody>""" + source_rows + """</tbody></table></div>
<h2>All observed company names</h2><label for="filter">Filter by name, source or status</label><input id="filter" type="search" placeholder="Try Blockhead or no_name_match"><p id="visible" role="status"></p>
<div class="scroll"><table><thead><tr><th>Source</th><th>Name</th><th>Source service labels</th><th>Atlas name-match disposition</th><th>NZ Atlas records</th><th>Evidence</th></tr></thead><tbody id="rows">""" + items + """</tbody></table></div>
<p>Full evidence and foreign/unknown-country candidate IDs: <a href="reconciliation.json">Machine reconciliation</a>.
Source-specific permissions and human verification remain pending.</p>
<script>
const q=document.querySelector('#filter'),rs=[...document.querySelectorAll('#rows tr')],count=document.querySelector('#visible');
function run(){let n=0;for(const r of rs){const ok=r.textContent.toLowerCase().includes(q.value.toLowerCase().trim());r.hidden=!ok;if(ok)n++}count.textContent=n+' of '+rs.length+' rows shown.'}
q.addEventListener('input',run);run();
</script></html>"""


def write_reports(output, summary, rows):
    output.mkdir(parents=True, exist_ok=True)
    (output / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (output / "reconciliation.json").write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    columns = ["observation_id", "source_id", "name", "service_labels", "status", "nz_record_ids",
               "nz_identity_count", "nz_geolocated_record_count", "nz_reviewed_location_count",
               "source_url", "location_claim", "rationale"]
    # CSV injection safety: prefix formula-significant strings, preserving audit data.
    def safe(value):
        s = ", ".join(value) if isinstance(value, list) else str(value)
        return "'" + s if s.lstrip().startswith(("=", "+", "-", "@", "\t", "\r")) else s
    with (output / "reconciliation.csv").open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(columns)
        for row in rows:
            writer.writerow([safe(row.get(c, "")) for c in columns])
    (output / "coverage.html").write_text(render_html(summary, rows), encoding="utf-8")


def run(output=None):
    manifest, atlas = load_atlas()
    sources, observations = load_observations()
    reconciled = match(atlas, observations)
    summary = summarise(manifest, sources, observations, reconciled)
    if output:
        write_reports(output, summary, reconciled)
    print("NZ CENSUS WAVE 1")
    print(json.dumps({
        "complete_index_examined": summary["complete_index_records_examined"],
        "source_observations": summary["source_observations"],
        "distinct_source_names": summary["distinct_normalised_source_names"],
        "outcomes": summary["total_statuses"],
        "by_source": {k: {"rows": v["observed_rows"], "scope": v["source_scope"],
                          "outcomes": v["outcomes"], "no_name_match": v["not_name_matched"],
                          "needs_identity_review": v["identity_review"]}
                      for k, v in summary["source_outcomes"].items()},
        "foreign_only_details": [{"name": r["name"], "source": r["source_id"], "record_ids": r["foreign_record_ids"]}
                                 for r in reconciled if r["status"] == "foreign_only_name_collision"],
        "new_atlas_records_created": 0, "publication_approved": False
    }, ensure_ascii=False, indent=2))
    return summary


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("command", choices=("check", "prepare"), nargs="?", default="check")
    cli.add_argument("--output", type=Path, default=HOME / "reports")
    args = cli.parse_args()
    run(args.output if args.command == "prepare" else None)
