"""Self-check for the handler's summary and confidence (runs on the local index). Usage: python3 aws/check_handler.py"""
import json, sys
from pathlib import Path
here = Path(__file__).resolve().parent
sys.path[:0] = [str(here), str(here.parent / "api")]
import lambda_function as lf

def call(q):
    r = lf.handler({"queryStringParameters": {"name": q}}, None)
    return r["statusCode"], json.loads(r["body"])

assert lf.day("Wed, 28 Oct 2026 14:03:09 GMT") == "2026-10-28"
assert lf.day("2026-11-02T23:00:04.371Z") == "2026-11-02"
assert lf.day("23/10/2026") == "2026-10-23"
c, b = call("MALEKI, Azizollah")
assert c == 200 and b["matched"] and b["summary"].startswith("Match:") and b["confidence"] == b["match_score"], b["summary"]
assert "OFAC SDN (published 20" in b["summary"]
c, b = call("Apple Inc")
assert c == 200 and not b["matched"] and b["summary"].startswith("No match:") and abs(b["confidence"] - (1 - b["match_score"])) < 1e-9
c, b = call("")
assert c == 400
print("handler self-check passed")
print(call("MALEKI, Azizollah")[1]["summary"])
