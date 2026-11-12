"""Download freely licensed medical-waste-type photos from Wikimedia Commons.

Saves 512-px thumbnails into data/raw/medical_commons/<subtype>/ and writes
attribution.csv (title, author, license, source URL) so every image can be credited.

    python scripts/download_medical_commons.py
"""
import argparse
import csv
import json
import re
import time
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from waste_classifier.config import RAW_DIR

API = "https://commons.wikimedia.org/w/api.php"
HEADERS = {"User-Agent": "waste-classifier-research/0.1 (educational project)"}

# subtype -> Commons categories
CATEGORIES = {
    "syringe_needle": ["Syringes", "Hypodermic needles", "Disposable syringes", "Insulin syringes"],
    "blister_pack":   ["Blister packs"],
    "mask":           ["Surgical masks", "Face masks during the COVID-19 pandemic"],
    "gloves":         ["Medical gloves", "Disposable gloves", "Nitrile gloves"],
    "pill_bottle":    ["Pill bottles"],
    "swab_bandage":   ["Cotton swabs", "Adhesive bandages", "Bandages", "Gauze"],
    "ampoule_vial":   ["Ampoules", "Vials"],
}


def get_json(params, tries=6):
    url = API + "?" + urllib.parse.urlencode({**params, "format": "json"})
    for i in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=HEADERS), timeout=60) as r:
                return json.load(r)
        except Exception:
            time.sleep(2 ** i)
    return {}


def list_files(category):
    """All bitmap files in a category, with a 512-px thumbnail URL and license metadata."""
    out, cont = [], {}
    while True:
        data = get_json({"action": "query", "generator": "categorymembers",
                         "gcmtitle": f"Category:{category}", "gcmtype": "file", "gcmlimit": 200,
                         "prop": "imageinfo", "iiprop": "url|mime|extmetadata", "iiurlwidth": 512, **cont})
        for page in data.get("query", {}).get("pages", {}).values():
            info = (page.get("imageinfo") or [{}])[0]
            if info.get("mime") not in ("image/jpeg", "image/png"):
                continue
            meta = info.get("extmetadata", {})
            clean = lambda k: re.sub("<[^>]+>", "", meta.get(k, {}).get("value", "")).strip()
            out.append({"title": page["title"], "thumb": info.get("thumburl"),
                        "page": info.get("descriptionurl"), "author": clean("Artist"),
                        "license": clean("LicenseShortName")})
        if "continue" not in data:
            return out
        cont = {k: v for k, v in data["continue"].items()}
        time.sleep(0.5)


def download(item, dest):
    if dest.exists():
        return True
    for i in range(5):
        try:
            req = urllib.request.Request(item["thumb"], headers=HEADERS)
            with urllib.request.urlopen(req, timeout=60) as r:
                dest.write_bytes(r.read())
            return True
        except Exception:
            time.sleep(2 ** i)
    return False


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", type=Path, default=RAW_DIR / "medical_commons")
    ap.add_argument("--workers", type=int, default=3)
    args = ap.parse_args()

    rows, seen = [], set()
    for subtype, cats in CATEGORIES.items():
        items = []
        for c in cats:
            found = [x for x in list_files(c) if x["title"] not in seen and x["thumb"]]
            seen.update(x["title"] for x in found)
            items += found
            print(f"  {subtype:15s} {c:45s} {len(found)}")
            time.sleep(1)
        (args.out / subtype).mkdir(parents=True, exist_ok=True)
        dests = [args.out / subtype / (re.sub(r"[^\w.-]", "_", x["title"][5:])[:120].rsplit(".", 1)[0] + ".jpg")
                 for x in items]
        with ThreadPoolExecutor(args.workers) as pool:
            ok = list(pool.map(download, items, dests))
        for x, d, good in zip(items, dests, ok):
            if good:
                rows.append({"subtype": subtype, "file": str(d.relative_to(args.out)), **x})
        print(f"{subtype}: {sum(ok)}/{len(items)} downloaded")

    with open(args.out / "attribution.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["subtype", "file", "title", "author", "license", "page", "thumb"])
        w.writeheader()
        w.writerows(rows)
    print(f"Total {len(rows)} images. Attribution in {args.out / 'attribution.csv'}")


if __name__ == "__main__":
    main()
