"""AWS Lambda (Function URL) for the comparator module.

GET  /module.wasm  -> the exact registered bytes (wasmUrl).
POST /runnable     -> the node's batch request, scored by those same bytes under wasmtime (wasmRunnableUrl).
  {"batch": [{"ground_truth_value": i64, "miner_value": i64, "spec": [code, tolerance]}, ...]}
  -> {"results": [{"score": bps} | {"error": "..."}, ...]}
"""
import base64, json, struct
from pathlib import Path
import wasmtime

WASM = (Path(__file__).parent / "macro_comparator.wasm").read_bytes()
I64 = (-(1 << 63), (1 << 63) - 1)
MAX_BATCH = 100
_engine = wasmtime.Engine()
_module = wasmtime.Module(_engine, WASM)


def _i64(v):
    if isinstance(v, bool) or not isinstance(v, int) or not I64[0] <= v <= I64[1]:
        raise ValueError("not an i64")
    return v


def score_batch(batch):
    store = wasmtime.Store(_engine)  # a fresh instance per request: no state carried between calls
    ex = wasmtime.Instance(store, _module, []).exports(store)
    mem, alloc, free, score = ex["memory"], ex["imw_alloc"], ex["imw_free"], ex["imw_score_deterministic"]
    out = []
    for q in batch:
        try:
            truth, miner = _i64(q["ground_truth_value"]), _i64(q["miner_value"])
            code, tol = (_i64(x) for x in q["spec"][:2])
            p = alloc(store, 16)
            mem.write(store, struct.pack("<qq", code, tol), p)
            s = score(store, truth, miner, p)
            free(store, p, 16)
            out.append({"score": s} if 0 <= s <= 10000 else {"error": f"module refused input ({s})"})
        except (KeyError, TypeError, ValueError, IndexError) as e:
            out.append({"error": f"bad question: {e}"})
    return out


def _reply(code, body, ctype="application/json"):
    return {"statusCode": code, "headers": {"Content-Type": ctype}, "body": json.dumps(body)}


def handler(event, context):
    http = event.get("requestContext", {}).get("http", {})
    method, path = http.get("method", "GET"), event.get("rawPath", "/")
    if method == "GET" and path == "/module.wasm":
        return {"statusCode": 200, "isBase64Encoded": True, "body": base64.b64encode(WASM).decode(),
                "headers": {"Content-Type": "application/wasm", "Cache-Control": "public, max-age=31536000, immutable"}}
    if method == "POST" and path == "/runnable":
        raw = event.get("body") or ""
        try:
            req = json.loads(base64.b64decode(raw) if event.get("isBase64Encoded") else raw)
            batch = req["batch"]
            assert isinstance(batch, list) and 0 < len(batch) <= MAX_BATCH
        except Exception:
            return _reply(400, {"error": 'expected {"batch": [question, ...]} with 1 to 100 questions'})
        return _reply(200, {"results": score_batch(batch)})
    return _reply(404, {"error": "GET /module.wasm or POST /runnable"})
