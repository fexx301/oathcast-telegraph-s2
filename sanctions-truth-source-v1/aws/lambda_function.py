"""AWS Lambda (Function URL) handler: GET /screen?name=... -> SANCTIONS_SCREENING_MATCH fields as JSON."""
import json
from _screen import screen


def handler(event, context):
    name = (event.get("queryStringParameters") or {}).get("name") or ""
    if not name.strip() or len(name) > 256:
        code, body = 400, {"error": "name is required (1-256 characters)"}
    else:
        code, body = 200, screen(name)
    return {"statusCode": code, "headers": {"Content-Type": "application/json", "Cache-Control": "public, max-age=300"},
            "body": json.dumps(body)}
