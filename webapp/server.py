"""Web front end for the waste classifier (no extra dependencies: Python standard library HTTP server).

    python webapp/server.py                 # http://localhost:8000
    python webapp/server.py --port 8080 --engine cnn

API
  GET  /api/info                      engine, categories, threshold, test metrics, taught-photo counts
  POST /api/classify                  body: image bytes (JPEG/PNG)  -> category, confidence, probabilities
  POST /api/teach?category=<name>     body: image bytes             -> saves a labelled photo for retraining
"""
import argparse
import io
import json
import threading
import time
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import numpy as np
from PIL import Image, ImageOps

from waste_classifier.config import CATEGORIES, CATEGORY_LABELS, RAW_DIR
from waste_classifier.engine import engine_metrics, load_engine

STATIC = Path(__file__).parent / "static"
CAPTURE_DIR = RAW_DIR / "user_captures"
MAX_BODY = 15 * 1024 * 1024
CONTENT_TYPES = {".html": "text/html; charset=utf-8", ".js": "text/javascript", ".css": "text/css",
                 ".svg": "image/svg+xml", ".png": "image/png", ".ico": "image/x-icon"}


class App:
    def __init__(self, engine, threshold):
        self.engine, self.threshold = engine, threshold
        self.lock = threading.Lock()          # one inference at a time on the GPU

    def classify(self, img: Image.Image) -> dict:
        rgb = np.asarray(img.convert("RGB"))
        t = time.perf_counter()
        with self.lock:
            probs, hint = self.engine(rgb)
            top = list(self.engine.last_concepts)
        k = int(np.argmax(probs))
        conf = float(probs[k])
        unknown = conf < self.threshold
        return {"category": None if unknown else CATEGORIES[k],
                "best_guess": CATEGORIES[k],
                "label": "Unknown — check manually" if unknown else CATEGORY_LABELS[CATEGORIES[k]],
                "confidence": conf, "unknown": unknown, "hint": hint,
                "probs": {c: float(p) for c, p in zip(CATEGORIES, probs)},
                "top": [{"name": n, "score": s} for n, s in top],
                "ms": round((time.perf_counter() - t) * 1000, 1)}

    def info(self) -> dict:
        counts = {c: len(list((CAPTURE_DIR / c).glob("*.jpg"))) if (CAPTURE_DIR / c).exists() else 0
                  for c in CATEGORIES}
        return {"engine": self.engine.name, "kind": self.engine.kind, "threshold": self.threshold,
                "categories": CATEGORIES, "labels": CATEGORY_LABELS,
                "metrics": engine_metrics(self.engine), "taught": counts}


def make_handler(app: App):
    class Handler(BaseHTTPRequestHandler):
        server_version = "WasteSorter/1.0"

        def log_message(self, fmt, *args):  # quieter console
            if "/api/classify" not in (args[0] if args else ""):
                super().log_message(fmt, *args)

        def _json(self, obj, status=HTTPStatus.OK):
            body = json.dumps(obj, default=float).encode()
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)

        def _image(self):
            n = int(self.headers.get("Content-Length", 0))
            if not 0 < n <= MAX_BODY:
                raise ValueError("image missing or larger than 15 MB")
            return ImageOps.exif_transpose(Image.open(io.BytesIO(self.rfile.read(n))))

        def do_GET(self):
            path = urlparse(self.path).path
            if path == "/api/info":
                return self._json(app.info())
            file = STATIC / ("index.html" if path in ("/", "") else path.lstrip("/").removeprefix("static/"))
            try:
                file = file.resolve()
                file.relative_to(STATIC.resolve())          # no path traversal
                data = file.read_bytes()
            except (ValueError, OSError):
                return self._json({"error": "not found"}, HTTPStatus.NOT_FOUND)
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", CONTENT_TYPES.get(file.suffix, "application/octet-stream"))
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def do_POST(self):
            url = urlparse(self.path)
            try:
                if url.path == "/api/classify":
                    return self._json(app.classify(self._image()))
                if url.path == "/api/teach":
                    cat = parse_qs(url.query).get("category", [""])[0]
                    if cat not in CATEGORIES:
                        return self._json({"error": f"category must be one of {CATEGORIES}"},
                                          HTTPStatus.BAD_REQUEST)
                    d = CAPTURE_DIR / cat
                    d.mkdir(parents=True, exist_ok=True)
                    p = d / f"{cat}_{time.strftime('%Y%m%d_%H%M%S')}_{time.time_ns() % 10**6:06d}.jpg"
                    self._image().convert("RGB").save(p, "JPEG", quality=92)
                    return self._json({"saved": p.name, "category": cat,
                                       "count": len(list(d.glob("*.jpg")))})
                return self._json({"error": "not found"}, HTTPStatus.NOT_FOUND)
            except Exception as e:
                return self._json({"error": str(e)}, HTTPStatus.BAD_REQUEST)

    return Handler


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=8000)
    ap.add_argument("--engine", choices=["siglip", "cnn"], help="default: siglip if trained, else cnn")
    ap.add_argument("--model", type=Path, help="CNN checkpoint for --engine cnn")
    ap.add_argument("--threshold", type=float, help="confidence below this is UNKNOWN")
    args = ap.parse_args()

    engine = load_engine(args.engine, args.model)
    app = App(engine, args.threshold or engine.threshold)
    server = ThreadingHTTPServer((args.host, args.port), make_handler(app))
    print(f"Engine: {engine.name} | UNKNOWN below {app.threshold:.2f}")
    print(f"Open http://{args.host if args.host != '0.0.0.0' else 'localhost'}:{args.port} in your browser "
          f"(Ctrl+C to stop)")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
