"""GET /screen?name=<person, company, vessel or wallet> -> SANCTIONS_SCREENING_MATCH fields as JSON."""
import json, os, sys
from http.server import BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse

sys.path.insert(0, os.path.dirname(__file__))
from _screen import screen  # noqa: E402


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        name = (parse_qs(urlparse(self.path).query).get("name") or [""])[0]
        if not name.strip() or len(name) > 256:
            code, body = 400, {"error": "name is required (1-256 characters)"}
        else:
            code, body = 200, screen(name)
        data = json.dumps(body).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Cache-Control", "public, max-age=300")
        self.end_headers()
        self.wfile.write(data)
