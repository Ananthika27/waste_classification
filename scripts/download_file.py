"""Download a large file over an unstable connection: HTTP Range requests, append-only, retries forever.

    python scripts/download_file.py URL OUTPUT_PATH
"""
import sys
import time
import urllib.request
from pathlib import Path

url, out = sys.argv[1], Path(sys.argv[2])
part = out.with_suffix(out.suffix + ".part")
headers = {"User-Agent": "waste-classifier-downloader"}

total = None
while True:
    done = part.stat().st_size if part.exists() else 0
    if total is not None and done >= total:
        break
    try:
        req = urllib.request.Request(url, headers={**headers, "Range": f"bytes={done}-"})
        with urllib.request.urlopen(req, timeout=30) as r:
            if r.status == 200 and done:          # server ignored Range: start over safely
                done = 0
                part.unlink()
            size = int(r.headers.get("Content-Length", 0))
            total = done + size if size else total
            with open(part, "ab") as f:
                while chunk := r.read(1 << 20):
                    f.write(chunk)
                    done += len(chunk)
                    print(f"\r{done / 1e6:8.1f} / {(total or 0) / 1e6:.1f} MB", end="", flush=True)
        if total is None or done >= total:
            break
    except Exception as e:
        print(f"\n retry after error: {e}", flush=True)
        time.sleep(3)

part.rename(out)
print(f"\nSaved {out}")
