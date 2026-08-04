#!/usr/bin/env python3
"""Local unit tests for property-rd pure logic (no google/vault deps).

Run:  python3 test_property_rd.py            # unittest
      pytest test_property_rd.py -q          # also fine
"""
import json
import os
import sys
import unittest
from xml.dom import minidom

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sheet_io import (  # noqa: E402
    ascii_fold, coord_bucket, dedupe_records, haversine_km, key_name,
    normalize_name, parse_num, parse_psf, records_from_rows,
    strip_locality_tokens,
)
from kml_generator import (  # noqa: E402
    build_kml, description_for, effective_type, label_for, norm_type,
    reclassify,
)
import coords_from_urls  # noqa: E402


class TestHaversine(unittest.TestCase):
    def test_sammy_palm_hills_63km(self):
        # Thylagere subject land -> Sammy's Palm Hills (Beedaganahalli)
        d = haversine_km(13.3216384, 77.6789048,
                         13.356528, 77.725266)
        self.assertTrue(5.5 < d < 7.0, f"got {d} km (expect ~6.3)")

    def test_zero(self):
        self.assertAlmostEqual(haversine_km(13.0, 77.0, 13.0, 77.0), 0.0)


class TestNormalize(unittest.TestCase):
    def test_strip_locality_suffix(self):
        a = "Assetz City Of Palms Ivc"
        b = "Assetz City of Palms IVC Road, Bangalore North"
        self.assertEqual(key_name(a), key_name(b))

    def test_normalize(self):
        self.assertEqual(normalize_name("Prestige  Crystal Lawns!"),
                         "prestigecrystallawns")


class TestAsciiFold(unittest.TestCase):
    def test_rupee_and_dash(self):
        s = "Rs 1,700-2,800/sqft"  # unchanged
        self.assertEqual(ascii_fold(s), s)
        self.assertEqual(ascii_fold("\u20b91.38-3.40 Cr"),
                         "Rs 1.38-3.40 Cr")
        self.assertEqual(ascii_fold("DEVA\u2013NANDI"), "DEVA-NANDI")
        self.assertEqual(ascii_fold("a\u00e9b"), "a?b")


class TestParse(unittest.TestCase):
    def test_parse_num_cr(self):
        # parse_num returns absolute Rupees: 1.38 Cr -> 13,800,000
        self.assertAlmostEqual(parse_num("Rs 1.38-3.40 Cr"), 1.38e7)
        self.assertAlmostEqual(parse_num("Rs 72L"), 7.2e6)

    def test_parse_psf(self):
        self.assertEqual(parse_psf("Rs 9,200 - 9,500/sqft"), 9200)
        self.assertIsNone(parse_psf(""))

    def test_coord_bucket(self):
        self.assertEqual(coord_bucket(13.123451, 77.123451),
                         coord_bucket(13.123452, 77.123452))


class TestRecords(unittest.TestCase):
    RND_ROWS = [
        ["#", "Project", "Type", "Locality", "Listing Price", "Per Sqft",
         "Lat", "Lng", "Dist km", "Maps link", "Source URL", "Done"],
        ["1", "Prestige Crystal Lawns", "Plotted", "Devanahalli",
         "Rs 1.38-3.40 Cr", "Rs 8,999", "13.35", "77.70", "8.2",
         "https://maps.app.goo.gl/x", "https://99acres.com/abc", "false"],
    ]

    def test_schema_b_synonyms(self):
        recs = records_from_rows(self.RND_ROWS)
        r = recs[0]
        self.assertEqual(r["project"], "Prestige Crystal Lawns")
        self.assertEqual(r["psf"], "Rs 8,999")
        self.assertEqual(r["total"], "Rs 1.38-3.40 Cr")
        self.assertEqual(r["lat"], "13.35")

    def test_dedupe_keeps_richer(self):
        rich = {"project": "Sobha Oakshire", "psf": "Rs 6,500",
                "total": "Rs 6.45 Cr", "source_url": "u1"}
        poor = {"project": "Sobha Oakshire", "psf": "", "total": ""}
        out = dedupe_records([poor, rich])
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0]["source_url"], "u1")


class TestType(unittest.TestCase):
    def test_norm(self):
        self.assertEqual(effective_type({"type": "Villa", "project": "A"}),
                         "villa")
        self.assertEqual(effective_type({"type": "Residential Plot"}),
                         "plot")
        self.assertEqual(effective_type({"type": "Apartment"}), "apartment")

    def test_reclass_from_name(self):
        self.assertEqual(
            effective_type({"type": "new_project",
                            "project": "Lodha Villa Estates", "total": ""}),
            "villa")

    def test_reclass_from_price(self):
        self.assertEqual(
            effective_type({"type": "Other",
                            "project": "Nandi Garden",
                            "total": "60x40 plots Rs 45L"}),
            "plot")
        self.assertEqual(
            effective_type({"type": "Other",
                            "project": "Vantage Heights",
                            "total": "2/3 BHK, 1280 sqft"}),
            "apartment")


class TestLabels(unittest.TestCase):
    def test_label_with_psf(self):
        self.assertEqual(
            label_for({"project": "Goldcrest", "psf": "Rs 9,200"}),
            "Goldcrest | Rs 9,200/sqft")

    def test_label_approx_from_total_area(self):
        self.assertEqual(
            label_for({"project": "X", "total": "Rs 69,40,000",
                       "area": "4085 sqft"}),
            "X | Rs 1,699/sqft (approx)")

    def test_label_no_price(self):
        rec = {"name": "Queens Park", "psf": ""}
        self.assertEqual(label_for(rec), "Queens Park")


class TestDescription(unittest.TestCase):
    def test_includes_source_urls(self):
        rec = {"project": "P1", "type": "Apartment", "developer": "D",
               "locality": "L", "psf": "Rs 9,000", "total": "Rs 1 Cr"}
        sources = [
            {"portal": "99acres", "price": "9,000", "total": "Rs 1 Cr",
             "date": "2026-08-03", "url": "https://99acres.com/a?tag=1"},
            {"portal": "MagicBricks", "price": "9,200",
             "url": "https://magicbricks.com/b?tag=1"},
        ]
        desc = description_for(rec, sources)
        self.assertIn("https://99acres.com/a?tag=1", desc)
        self.assertIn("https://magicbricks.com/b?tag=1", desc)
        self.assertIn("Pricing sources:", desc)


class TestKML(unittest.TestCase):
    def _sample(self):
        comps = [
            {"project": "Prestige Crystal Lawns", "type": "Plotted Development",
             "developer": "Prestige", "locality": "Devanahalli",
             "psf": "Rs 8,999", "total": "Rs 1.38 Cr", "lat": 13.25,
             "lon": 77.45, "_sources": [
                 {"portal": "99acres", "price": "8,999",
                  "url": "https://99acres.com/cgl?tag=1"}]},
            {"name": "Lodha Fiorana", "type": "Apartment", "lat": 13.26,
             "lon": 77.46, "psf": ""},  # no coords? no — has coords, no psf
        ]
        pois = [{"name": "Columbia Asia Hospital", "type": "hospital",
                 "lat": 13.27, "lon": 77.45}]
        subject = {"name": "Thylagere Land", "lat": 13.3216384,
                   "lon": 77.6789048}
        return comps, pois, subject

    def test_kml_valid_and_detailed(self):
        comps, pois, subject = self._sample()
        kml, stats = build_kml(comps, pois, subject=subject, labels="price")
        minidom.parseString(kml)  # must be well-formed
        self.assertEqual(stats["placemarks"], 4)  # subject + 2 comps + poi
        self.assertIn("<href>https://transcribe.ahfl.in/kml-icons/"
                      "pushpin/blue-pushpin.png</href>", kml)
        self.assertIn("<href>https://transcribe.ahfl.in/kml-icons/shapes/"
                      "star.png</href>", kml)
        # description carries the pricing source URL
        self.assertIn("https://99acres.com/cgl?tag=1", kml)
        # label carries psf
        self.assertIn("Prestige Crystal Lawns | Rs 8,999/sqft", kml)
        # ASCII only
        self.assertTrue(kml.isascii(), "KML must be ASCII-only")

    def test_no_coords_reported(self):
        comps = [{"name": "Pre-Launch X", "type": "new_project"}]
        kml, stats = build_kml(comps, [], subject=None)
        self.assertIn("Pre-Launch X", stats["no_coords"])
        self.assertEqual(stats["placemarks"], 0)


class TestCoords(unittest.TestCase):
    def test_parse_patterns(self):
        cases = {
            "https://www.google.com/maps/place/X/@12.8566,77.6584,15z":
                (12.8566, 77.6584),
            "https://maps.google.com/?q=12.8566,77.6584": (12.8566, 77.6584),
            "https://maps.google.com/?ll=12.8566,77.6584": (12.8566, 77.6584),
            "https://www.google.com/maps/search/x?center=12.85,77.65":
                (12.85, 77.65),
            "https://www.google.com/maps/place/X/@13.25,77.45!3d13.26!4d77.46":
                (13.26, 77.46),
        }
        for url, expected in cases.items():
            got = coords_from_urls.extract(url, follow=False)
            self.assertEqual(got, expected, url)
        self.assertIsNone(coords_from_urls.extract(
            "https://maps.app.goo.gl/AbCdEf", follow=False))


if __name__ == "__main__":
    unittest.main(verbosity=2)