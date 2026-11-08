"""AWS Lambda (Function URL) handler: GET /verify?location=<place>&date=YYYY-MM-DD -> recorded weather as JSON."""
import json
from _wfv import verify


def handler(event, context):
    q = event.get("queryStringParameters") or {}
    code, body = verify(q.get("location", ""), q.get("date", ""))
    return {"statusCode": code, "headers": {"Content-Type": "application/json", "Cache-Control": "public, max-age=3600"},
            "body": json.dumps(body)}
