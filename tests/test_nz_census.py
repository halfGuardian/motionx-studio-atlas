"""NZ census source-accounting and full-catalogue name-match safety checks."""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import nz_census as census


def row(id, name, country, company_id=None, cls="C", kind="company_reference", lat=None, lng=None):
    return {"id": id, "company_id": company_id or id, "name": name, "city": "",
            "country": country, "lat": lat, "lng": lng, "evidence_class": cls, "record_kind": kind}


def observation(name, source="test"):
    return {"observation_id": source + ":" + name, "source_id": source, "name": name,
            "service_labels": ["VFX"], "source_url": "https://example.org/list", "location_claim": "NZ",
            "observed_on": "2026-11-07", "source_scope": "partial"}


class SourceTests(unittest.TestCase):
    def test_42_historical_nzfc_plus_56_new_source_rows_all_accounted_for(self):
        sources, observations = census.load_observations()
        self.assertEqual([len(s["records"]) for s in sources], [42, 24, 9, 21, 2])
        self.assertEqual(len(observations), 98)
        self.assertEqual(len({o["observation_id"] for o in observations}), 98)
        self.assertTrue(all(o["source_url"].startswith("https://") for o in observations))
        self.assertTrue(all(o["observed_on"] == "2026-11-07" for o in observations))

    def test_source_pages_are_not_claimed_complete_when_missing(self):
        sources, observations = census.load_observations()
        auck = sources[1]
        self.assertEqual(auck["completeness"], "partial")
        self.assertEqual(auck["observed_pages"], [0, 1, 3, 6])
        self.assertEqual(auck["unobserved_pages"], [2, 4, 5])
        self.assertEqual(len(sources[2]["records"]), 9)
        self.assertEqual(sources[2]["completeness"], "showcase_only")
        self.assertEqual(sources[3]["completeness"], "complete_named_showreel_not_directory")
        self.assertEqual(sources[4]["completeness"], "partial_selected_only")

    def test_original_source_labels_preserved_without_capability_upgrade(self):
        _, obs = census.load_observations()
        pow_nzfc = next(x for x in obs if x["source_id"] == "nzfc-facilities" and x["name"] == "POW Studios")
        self.assertEqual(pow_nzfc["service_labels"], ["PP", "S", "A", "VFX"])
        block = [x for x in obs if x["name"] == "Blockhead"]
        self.assertEqual(len(block), 2)
        self.assertNotIn("verified", repr(block).lower())
        self.assertFalse(any("lat" in x or "lng" in x for x in obs))

    def test_alias_matching_cannot_invent_a_facility(self):
        data = census.match(
            [row("albedo", "Albedo", "New Zealand"),
             row("yukfoo", "Yukfoo", "New Zealand"),
             row("rock", "Floating Rock Studio", "New Zealand")],
            [observation("Albedo VFX"), observation("Yuk Foo"), observation("Floating Rock")])
        self.assertEqual([x["status"] for x in data], ["represented_name_match"] * 3)
        self.assertEqual([x["nz_geolocated_record_count"] for x in data], [0, 0, 0])
        self.assertEqual(data[0]["nz_record_ids"], ["albedo"])

    def test_foreign_branch_is_not_misrepresented_as_nz(self):
        m = census.match([row("melbourne", "Wētā FX", "Australia"),
                          row("vancouver", "Wētā FX", "Canada"),
                          row("wellington", "Wētā FX", "New Zealand", "weta",
                              cls="A", kind="retained_location")],
                         [observation("Wēta FX")])[0]
        self.assertEqual(m["status"], "represented_name_match")
        self.assertEqual(m["nz_record_ids"], ["wellington"])
        self.assertEqual(m["nz_reviewed_location_count"], 1)
        self.assertEqual(m["foreign_record_ids"], ["melbourne", "vancouver"])

    def test_unknown_country_does_not_become_nz(self):
        result = census.match([row("ambiguous", "Animation House", "")], [observation("Animation House")])[0]
        self.assertEqual(result["status"], "country_unknown_name_candidate")
        self.assertEqual(result["nz_record_ids"], [])

    def test_distinct_brands_and_ambiguous_identities_are_held(self):
        samples = census.match(
            [row("a", "Brand House", "New Zealand", "group1"),
             row("b", "Brand House", "New Zealand", "group2"),
             row("assembly", "Assembly", "New Zealand")],
            [observation("Brand House"), observation("Blockhead")])
        self.assertEqual(samples[0]["status"], "multiple_nz_identity_candidates")
        self.assertEqual(samples[1]["status"], "identity_review_hold")
        self.assertFalse(samples[1]["nz_record_ids"])

    def test_never_convert_a_foreign_exact_name_into_an_nz_facility(self):
        x = census.match([row("sydney", "Animation Example", "Australia")], [observation("Animation Example")])[0]
        self.assertEqual(x["status"], "foreign_only_name_collision")
        self.assertFalse(x["nz_geolocated_record_count"])
        self.assertEqual(x["foreign_record_ids"], ["sydney"])

    def test_catalogue_is_fully_loaded_and_no_baseline_records_are_lost(self):
        m, rows = census.load_atlas()
        self.assertEqual(len(rows), 42239)
        self.assertEqual(len({r["id"] for r in rows}), len(rows))
        self.assertEqual(m["counts"]["retained_locations"], 243)
        self.assertEqual(m["counts"]["company_references"], 1620)

    def test_summary_has_no_publication_approval(self):
        sources, obs = census.load_observations()
        rows = census.match([row("studio", "Albedo", "New Zealand")], obs)
        summary = census.summarise({"counts": {"records": 42239}}, sources, obs, rows)
        self.assertFalse(summary["publication_approved"])
        self.assertEqual(summary["new_atlas_records_created"], 0)
        self.assertEqual(summary["new_geocodes_created"], 0)
        self.assertEqual(summary["source_observations"], 98)
        self.assertTrue(summary["distinct_normalised_source_names"] < 98)


if __name__ == "__main__":
    unittest.main()
