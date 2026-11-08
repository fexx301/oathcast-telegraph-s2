"""Offline check of app/lambda_function.py: served bytes, batch scoring vs the kit golden, malformed input."""
import base64, json, sys
sys.path.insert(0, "app")
import lambda_function as L  # noqa: E402
import test_comparator as T  # noqa: E402

ev = lambda m, p, body=None: {"requestContext": {"http": {"method": m}}, "rawPath": p, "body": body}
r = L.handler(ev("GET", "/module.wasm"), None)
assert r["statusCode"] == 200 and base64.b64decode(r["body"]) == open("macro_comparator.wasm", "rb").read()
ref, cases = T.golden(), T.battery(100, 7)
batch = [{"ground_truth_value": t, "miner_value": m, "spec": [c, tol]} for t, m, c, tol in cases]
r = L.handler(ev("POST", "/runnable", json.dumps({"batch": batch})), None)
res = json.loads(r["body"])["results"]
assert r["statusCode"] == 200 and [x["score"] for x in res] == [ref(*c) for c in cases]
assert len(r["body"]) < 64 * 1024
bad = json.loads(L.handler(ev("POST", "/runnable", json.dumps({"batch": [{"ground_truth_value": 1.5, "miner_value": 1, "spec": [0, 0]}]})), None)["body"])
assert "error" in bad["results"][0]
assert L.handler(ev("POST", "/runnable", "{}"), None)["statusCode"] == 400
assert L.handler(ev("POST", "/runnable", json.dumps({"batch": batch * 2})), None)["statusCode"] == 400
print("ok")
