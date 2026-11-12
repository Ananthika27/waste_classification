"""Download the RealWaste dataset (CC BY 4.0) from its Hugging Face mirror into data/raw/realwaste/<Class>/.

RealWaste: S. Single, S. Iranmanesh, R. Raad, "RealWaste: A Novel Real-Life Data Set for
Landfill Waste Classification Using Deep Learning", Information 14(12), 2023.
Original: https://archive.ics.uci.edu/dataset/908/realwaste

    python scripts/download_realwaste.py
"""
import argparse
import json
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from waste_classifier.config import RAW_DIR

REPO = "shahzaibvohra/realwaste"
API = f"https://huggingface.co/api/datasets/{REPO}"
FILE_URL = f"https://huggingface.co/datasets/{REPO}/resolve/main/{{}}"
HEADERS = {"User-Agent": "waste-classifier-downloader"}


def fetch(url: str) -> bytes:
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read()


def download(name: str, out_dir: Path) -> str:
    cls = name.rsplit("_", 1)[0]                      # "Food Organics_12.jpg" -> "Food Organics"
    dest = out_dir / cls / name
    if dest.exists() and dest.stat().st_size > 0:
        return "skipped"
    dest.parent.mkdir(parents=True, exist_ok=True)
    for attempt in range(3):
        try:
            data = fetch(FILE_URL.format(urllib.parse.quote(name)))
            dest.write_bytes(data)
            return "ok"
        except Exception as e:  # network hiccup: retry
            err = e
    return f"failed: {err}"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", type=Path, default=RAW_DIR / "realwaste")
    ap.add_argument("--workers", type=int, default=16)
    args = ap.parse_args()

    files = [s["rfilename"] for s in json.loads(fetch(API))["siblings"]
             if s["rfilename"].lower().endswith((".jpg", ".jpeg", ".png"))]
    print(f"{len(files)} images to download into {args.out}")

    results = {"ok": 0, "skipped": 0, "failed": 0}
    with ThreadPoolExecutor(args.workers) as pool:
        for i, (name, status) in enumerate(zip(files, pool.map(lambda n: download(n, args.out), files)), 1):
            key = status.split(":")[0]
            results[key] += 1
            if key == "failed":
                print("  ", name, status)
            if i % 500 == 0:
                print(f"  {i}/{len(files)}")
    print(results)
    for d in sorted(p for p in args.out.iterdir() if p.is_dir()):
        print(f"  {d.name:22s} {len(list(d.iterdir()))}")


if __name__ == "__main__":
    main()
