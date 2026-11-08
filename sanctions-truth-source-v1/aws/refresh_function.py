"""Daily refresher Lambda: re-fetch the official lists, rebuild the index, check it, and swap it into the screen Lambda.
Any failure leaves the live index as it was."""
import gzip, io, json, os, zipfile
from pathlib import Path

os.environ.setdefault("RAW_DIR", "/tmp/raw")
os.environ.setdefault("INDEX_OUT", "/tmp/index.json.gz")
import build_index  # noqa: E402

HERE = Path(__file__).parent
TARGET = os.environ.get("SCREEN_FUNCTION", "telegraph-sanctions-screen")
# Floors well under today's counts (19,484 / 486 / 1,007 / 6,269; 507 wallets): a truncated or changed file fails here.
FLOORS = {"OFAC SDN": 15000, "OFAC Consolidated (non-SDN)": 300, "UN Security Council Consolidated": 800,
          "EU Consolidated Financial Sanctions": 5000}
KNOWN = ["MALEKI, Azizollah", "0x931546D9e66836AbF687d2bc64B30407bAc8C568", "LUNA LUSTER"]  # listed on 2026-11-03
CLEAN = ["Apple Inc", "TEXCHEM INDUSTRIES"]


def check(summary):
    low = {l: n for l, n in FLOORS.items() if summary["entries"].get(l, 0) < n}
    assert not low and summary["wallets"] >= 400, ("counts below floor", summary["entries"], summary["wallets"])
    import _screen
    _screen.INDEX, _screen._idx = Path(os.environ["INDEX_OUT"]), None
    bad = [q for q in KNOWN if not _screen.screen(q)["matched"]] + [q for q in CLEAN if _screen.screen(q)["matched"]]
    assert not bad, ("known-answer check failed", bad)


def handler(event, context):
    summary = build_index.build(build_index.fetch(refetch=True))
    check(summary)
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        z.write(HERE / "lambda_function.py", "lambda_function.py")
        z.write(HERE / "_screen.py", "_screen.py")
        z.write(os.environ["INDEX_OUT"], "index.json.gz")
    import boto3  # in the Lambda runtime
    boto3.client("lambda").update_function_code(FunctionName=TARGET, ZipFile=buf.getvalue())
    return {"updated": TARGET, "lists": summary["lists"], "entries": summary["entries"], "wallets": summary["wallets"]}
