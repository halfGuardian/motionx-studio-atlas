# Source-to-Atlas coverage contract · follow-up after v1.3

**Purpose.** A directory of 42,239 research records is not evidence that MotionX has covered 42,239 distinct active studio businesses, let alone 42,239 verified facilities. Source-intake totals, searchable company references and map pins are separate measures. A successful ingestion run must not be reported as success if relevant source names remain absent from the user-facing directory.

## Verified source snapshot: NZ Film Commission

Source: https://www.nzfilm.co.nz/inbound-productions/filming-in-nz/facilities
Snapshot/reviewed observation date: **7 November 2026**.
The earlier v1.2 factual projection contains **42 entries**, all with recorded triage decisions:
- 27 new Class C company-only references
- 3 repeat observations reconciled to a prior new reference
- 2 already represented in the preceding Atlas
- 9 excluded under the animation/VFX boutique relevance policy (sound/DIT/general post); these remain visible in the source audit
- 1 held for a mismatched identity: **Blockhead** links to **Assembly** on the NZFC source snapshot. Do not silently conflate these brands.

**32 of the 42 are represented as catalogue identities.** That is not 32 verified physical NZ locations. No new facility coordinates or capture-stage claims were added by this source. The nine excluded entries are genuine source listings and should be visible in audits even though they are outside the current boutique subset.

[Browse every NZFC source row and its disposition](../boutique/reports/nzfc-coverage.html). The main Atlas displays a count of currently matching records without pins and an explicit link to its searchable company-reference list.

A separate historical matching issue: the NZFC **Wētā FX** company listing matched the same-domain operating group across Wellington, Melbourne and Vancouver. The prior audit's sorted record_id points at Melbourne, even though this source is NZ-specific. The NZFC coverage page deliberately links Wellington. Future *location-specific* source matching must prefer geographic consistency without splitting an established company or applying NZ-specific evidence to overseas facilities. Do not rewrite hash-bound v1.2 source reports in place.

## Priority sources and current limits

| Source | Source intake | Research outcome | What remains |
| --- | --- | --- | --- |
| NZ Film Commission facilities directory | Complete 42-row snapshot | 32 represented, 9 outside boutique scope, 1 identity hold | Physical locations, current operation and rights review; Blockhead identity |
| NZFC Annecy 2026 delegation | Complete 17-row snapshot | 8 new company references (other decisions in historical triage) | Event attendance is not permanent studio evidence |
| European Animation Studios Directory (author-offered CC BY 4.0 data) | Complete 424-row projection | 235 new references in v1.2 | Current status, studio identities and physical branches |
| Animation Ireland listing | Complete 47-row snapshot | 30 new references in v1.2 | Current status and source-wide reuse terms |
| Annecy/MIFA 2024 exhibitors | All 1,074 event rows reconciled; targeted research on 566 | 172 new Class C references in v1.3 | **727 unresolved**, historical event participation not current facility evidence |
| VFX Professionals Guild NZ | Public description of 45-business list, not the actual list | No 45-row list imported | Ask owner for permitted access; do not claim complete coverage |
| Screen Wellington directory | Partial crosscheck | Source corroboration, no complete enumeration audit | Record an authorised snapshot and reconcile the full published vendor list |

Counts above have differing denominators and overlap. Never add them together to imply unique operating studios. Historic source snapshots are not automatically updated or independently validated.

## Mandatory future pipeline for each priority source

1. **Enumerate the source** with allowed access, recorded date, source URL, coverage scope and reuse/robots policy. If only a partial index/search excerpt is available, label the intake **partial**, never **complete**.
2. **Reconcile every listed name** with the complete existing Atlas by stable name/domain/aliases, country and legal brand. Record one of: represented, provisional new, duplicate, out of scope, identity hold, or unresolved. Do not merge parent/brand or country branches by domain alone.
3. **Publish a source-level matrix** of all names, input row count, current classification, evidence URL, reason for exclusion or hold, and a clickable search/profile link when represented. Missing names must not disappear from the report.
4. **Expose company-only results in the product** even when no map position is justified. Show map coverage separately. Never make up map pins to improve apparent coverage.
5. **Run regression checks** for source row preservation, disposition totals, index/search visibility, missing/incorrect profile links, source-country mismatches and evidence-class constraints. A green crawler or large record count alone is inadequate.
6. **Track human checks separately**: active operations, geography, rights, facility capabilities, and a precision sample. Automated decisions cannot be labelled as human verification; source page existence does not imply a confirmed stage or purchasable service.
7. **Update with a new source/version checkpoint**, never silently rewrite hash-bound historical v1.2/v1.3 release evidence. New observations get new dates; unchanged historic snapshots retain their original observed dates.

## Release risks still open

The v1.3 Annecy human review worksheet remains incomplete (37 rows, no human precision measurement). Main branch protection/required review rules were reported absent in the previous read-only audit. Repository and GitHub Pages visibility are independent of a claim of permission to republish source content. Source-wide reuse terms for NZFC remain **UNSPECIFIED**. Current v1.4 changes are visibility/audit fixes, not automatic publication approval for facility claims.
