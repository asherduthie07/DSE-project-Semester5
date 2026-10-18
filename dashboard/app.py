"""Small local HTTP server for the six-section Plotly dashboard."""

from __future__ import annotations

import argparse
import csv
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from mediscope.cli import PROJECT_ROOT
from mediscope.visualization.exports import EXPORT_NAMES, EXPORT_VERSION, verify_exports

APP_DIR = Path(__file__).resolve().parent
EXPORT_DIR = PROJECT_ROOT / "powerbi" / "exports" / EXPORT_VERSION
PLOTLY_FILE = APP_DIR / "assets" / "plotly-3.1.0.min.js"
PLOTLY_SHA256 = "122e3be346d66616944d0b83eaaf7242581508c3c1cfa0995a17af0d83eff770"


def check_dashboard() -> dict[str, object]:
    """Verify every needed file without starting a web server."""
    from mediscope.cli import sha256

    exports = verify_exports()
    for name in ("index.html", "app.js", "styles.css"):
        if not (APP_DIR / name).is_file():
            raise FileNotFoundError(APP_DIR / name)
    if not PLOTLY_FILE.is_file() or sha256(PLOTLY_FILE) != PLOTLY_SHA256:
        raise ValueError("Bundled Plotly.js file is missing or changed")
    return {"status": "PASS", "exports": exports["files"], "plotly_sha256": PLOTLY_SHA256,
            "raw_datasets_required": False}


class Handler(BaseHTTPRequestHandler):
    """Restrict requests to bundled application files and validated CSV APIs."""

    def do_GET(self) -> None:  # noqa: N802 - BaseHTTPRequestHandler protocol name
        route = urlparse(self.path).path
        if route.startswith("/api/table/"):
            name = route.removeprefix("/api/table/")
            if name not in EXPORT_NAMES:
                self.send_error(404, "Unknown table")
                return
            with (EXPORT_DIR / f"{name}.csv").open(encoding="utf-8", newline="") as stream:
                payload = json.dumps(list(csv.DictReader(stream)), separators=(",", ":"), allow_nan=False).encode("utf-8")
            self._send(payload, "application/json; charset=utf-8")
            return
        static = {"/": (APP_DIR / "index.html", "text/html; charset=utf-8"),
                  "/app.js": (APP_DIR / "app.js", "text/javascript; charset=utf-8"),
                  "/styles.css": (APP_DIR / "styles.css", "text/css; charset=utf-8"),
                  "/assets/plotly-3.1.0.min.js": (PLOTLY_FILE, "text/javascript; charset=utf-8"),
                  "/figures/note-wordcloud.png": (PROJECT_ROOT / "reports" / "figures" / "phase3" / "synthea_independent_note_wordcloud.png", "image/png")}
        if route not in static or not static[route][0].is_file():
            self.send_error(404, "Not found")
            return
        path, content_type = static[route]
        self._send(path.read_bytes(), content_type)

    def _send(self, payload: bytes, content_type: str) -> None:
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(payload)


def main() -> int:
    parser = argparse.ArgumentParser(description="MediScope local Phase III analytics preview")
    parser.add_argument("--check", action="store_true", help="Validate bundled data and assets, then exit")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    status = check_dashboard()
    if args.check:
        print(json.dumps(status, indent=2))
        return 0
    server = ThreadingHTTPServer((args.host, args.port), Handler)
    print(f"MediScope local analytics preview: http://{args.host}:{args.port}/", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
