"""Pick the name threshold on one half, report it on the other. Rule fixed before running:
threshold in 0.80..0.98 (step 0.01) maximising TPR - FPR on the calibration half; ties -> higher.

Positives (spelling/transliteration near-matches, leave-one-out): OFAC SDN individuals with a second name whose
normalised form differs from the primary but shares a token with it (so it is a spelling variant, not a different
alias). The variant is screened with that one spelling hidden; a hit is any name of the same person at >= threshold.
Seeded sample of 400.
Negatives: material v1's Q5 GLEIF look-alikes (verified not on OFAC SDN/non-SDN or UN), minus any exact EU name.
Sanity: material v1's Q1/Q2/Q4 exact listed names and Q3 listed wallets must all match at the chosen threshold.

History: v1 used EU names linked to UN references (calibration-v1-flawed.json). Most were translations of group
names into other EU languages, not spelling variants; restricted to individuals it left only 4 rows. Replaced.
"""
import hashlib, json, random, sys
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE / "api"))
import _screen as S  # noqa: E402

d = S.load()
mat = [json.loads(l) for l in open(HERE.parent / "telegraph-s2-sanctions-material-v1" / "material.jsonl")]
obs = [r["provenance"]["observation"] for r in mat]
half = lambda s: int(hashlib.sha256(s.encode()).hexdigest(), 16) % 2  # 0 = calibration, 1 = test

by_e = {}
for i, (k, e, n) in enumerate(d["names"]):
    if d["entries"][e]["list"] == "OFAC SDN" and d["entries"][e]["type"] == "individual":
        by_e.setdefault(e, []).append(i)
pool = []
for e, ids in by_e.items():
    prim = S.key(d["entries"][e]["name"])
    for i in ids:
        k = d["names"][i][0]
        if k != prim and set(k.split()) & set(prim.split()):
            pool.append((i, e))
random.Random(20261103).shuffle(pool)
pos = pool[:400]
eu_keys = {k for k, e, _ in d["names"] if d["entries"][e]["list"].startswith("EU")}
neg = [o["query"] for o in obs if o["query_type"] == "Q5" and S.key(o["query"]) not in eu_keys]

pos_s = [(d["names"][i][2], e, S.screen(d["names"][i][2], threshold=0.0, skip_name=i)) for i, e in pos]
neg_s = [(n, S.screen(n, threshold=0.0)) for n in neg]


def rates(t, h):
    P = [(r, e) for n, e, r in pos_s if half(n) == h]
    N = [r for n, r in neg_s if half(n) == h]
    tp = sum(r["match_score"] >= t for r, e in P)
    right = sum(any(m["score"] >= t and m["list"] == "OFAC SDN" and m["id"] == d["entries"][e]["id"] for m in r["matches"]) for r, e in P)
    fp = sum(r["match_score"] >= t for r in N)
    return {"matched": tp, "right_person": right, "pos": len(P), "fp": fp, "neg": len(N)}


j = lambda r: r["matched"] / max(1, r["pos"]) - r["fp"] / max(1, r["neg"])
grid = [round(0.80 + i / 100, 2) for i in range(19)]
best = max(grid, key=lambda t: (j(rates(t, 0)), t))
sanity = [o for o in obs if o["query_type"] in ("Q1", "Q2", "Q3", "Q4")]
miss = [o["query"] for o in sanity if not S.screen(o["query"], threshold=best)["matched"]]
res = {"threshold": best, "calibration": rates(best, 0), "test": rates(best, 1),
       "grid_test": {t: rates(t, 1) for t in grid},
       "sanity_listed_exact_and_wallets": {"n": len(sanity), "missed": miss},
       "positive_pool": len(pool)}
print(json.dumps(res, indent=1))
(HERE / "calibration.json").write_text(json.dumps(res, indent=1))
assert not miss, miss

# Question-shaped inputs the request builder may pass through (catalogue example style).
SHAPED = {"Azizollah Maleki, DOB 1965, Iran": True, "MALEKI Azizollah (Iran)": True, "vessel LUNA LUSTER, IMO 9187629": True,
          "ETH:0x931546D9e66836AbF687d2bc64B30407bAc8C568": True, "0x0000000000000000000000000000000000000001": False,
          "TEXCHEM INDUSTRIES, India": False}
bad = {q: v for q, v in SHAPED.items() if S.screen(q)["matched"] != v}
assert not bad, bad
print("shaped inputs ok")
