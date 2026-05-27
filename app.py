from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
from urllib.parse import unquote, urlparse

from resolution_capsule import build_capsule

ROOT = Path(__file__).parent
PUBLIC = ROOT / "public"


class Handler(SimpleHTTPRequestHandler):
    def translate_path(self, path):
        parsed = urlparse(path)
        requested = unquote(parsed.path).lstrip("/") or "index.html"
        candidate = (PUBLIC / requested).resolve()
        if PUBLIC.resolve() not in candidate.parents and candidate != PUBLIC.resolve():
            return str(PUBLIC / "404.html")
        return str(candidate)

    def do_POST(self):
        if self.path != "/api/capsule":
            self.send_error(404)
            return

        length = int(self.headers.get("content-length", "0"))
        try:
            payload = json.loads(self.rfile.read(length))
            response = build_capsule(payload)
        except Exception as exc:
            self.send_response(400)
            self.send_header("content-type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(exc)}).encode())
            return

        self.send_response(200)
        self.send_header("content-type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(response).encode())


if __name__ == "__main__":
    server = ThreadingHTTPServer(("127.0.0.1", 8000), Handler)
    print("Resolution Capsule MVP running at http://127.0.0.1:8000")
    server.serve_forever()
