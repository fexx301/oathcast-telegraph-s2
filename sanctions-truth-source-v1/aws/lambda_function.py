"""AWS Lambda (Function URL) handler: GET /screen?name=... -> SANCTIONS_SCREENING_MATCH fields as JSON,
plus a one-sentence `summary` and a `confidence` (the miner's label and confidence fields)."""
import json
from datetime import datetime
from email.utils import parsedate_to_datetime
from _screen import THRESHOLD, screen


def day(published):
    """List publication stamps come in three formats (RFC 2822, ISO 8601, DD/MM/YYYY); show YYYY-MM-DD."""
    for parse in (lambda s: parsedate_to_datetime(s), lambda s: datetime.fromisoformat(s.replace("Z", "+00:00")),
                  lambda s: datetime.strptime(s, "%d/%m/%Y")):
        try:
            return parse(published).strftime("%Y-%m-%d")
        except (TypeError, ValueError):
            pass
    return published


def summarise(out):
    checked = "; ".join(f'{l["list"]} (published {day(l.get("published", "?"))})' for l in out["lists"])
    if out["matched"]:
        m = out["matches"][0]
        progs = f', programs {", ".join(m["programs"])}' if m.get("programs") else ""
        text = (f'Match: "{out["name"]}" matches "{m["matched_on"]}" ({m["type"]}) on {m["list"]}, '
                f'score {m["score"]:.2f}{progs}. Checked: {checked}. A name match needs identity review before acting.')
        conf = out["match_score"]
    else:
        text = (f'No match: "{out["name"]}" has no listed name or wallet at or above {THRESHOLD} '
                f'(closest {out["match_score"]:.2f}). Checked: {checked}. Not a clearance; UK lists are not covered.')
        conf = 1 - out["match_score"]
    return {**out, "summary": text, "confidence": round(conf, 6)}


def handler(event, context):
    name = (event.get("queryStringParameters") or {}).get("name") or ""
    if not name.strip() or len(name) > 256:
        code, body = 400, {"error": "name is required (1-256 characters)"}
    else:
        code, body = 200, summarise(screen(name))
    return {"statusCode": code, "headers": {"Content-Type": "application/json", "Cache-Control": "public, max-age=300"},
            "body": json.dumps(body)}
