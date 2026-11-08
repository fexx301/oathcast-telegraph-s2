"""Screening core: name or wallet -> SANCTIONS_SCREENING_MATCH response fields. Pure stdlib."""
import difflib, gzip, json, re, unicodedata
from pathlib import Path

INDEX = Path(__file__).with_name("index.json.gz")
THRESHOLD = 0.84  # chosen by calibrate.py on its calibration half (calibration.json)
# Legal-form words carry no identity; dropping them stops "X LLC" matching every "Y LLC".
FORMS = set("""LLC LTD LIMITED JSC OJSC CJSC PJSC AO OAO ZAO PAO OOO TOO INC CORP CORPORATION CO COMPANY PLC SA SAS SARL SRL
SPA BV NV GMBH AG KG LLP LP FZE FZCO FZ DMCC PTE PVT SDN BHD SL SAL AS OY AB THE OF AND""".split())
WALLET = re.compile(r"^(0x[0-9a-fA-F]{40}|T[1-9A-HJ-NP-Za-km-z]{33}|[13][1-9A-HJ-NP-Za-km-z]{25,34}|"
                    r"bc1[02-9ac-hj-np-z]{11,71}|[LM][1-9A-HJ-NP-Za-km-z]{26,33}|[1-9A-HJ-NP-Za-km-z]{32,44}|4[0-9A-Za-z]{94})$")


def norm(s):
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().upper()
    return re.sub(r"[^A-Z0-9]+", " ", s).strip()


def key(s):
    toks = [t for t in norm(s).split() if t not in FORMS]
    return " ".join(sorted(toks))


LABELS = re.compile(r"^\s*(dob|d\.o\.b|born|date of birth|imo|mmsi|flag|nationality|citizen|passport|id|address|"
                    r"country|location|based in|registered in)\b", re.I)
LEADING = re.compile(r"^\s*((the )?(vessel|ship|tanker|mv|m/v|company|entity|individual|person|mr|mrs|ms|dr)\.?\s+)+", re.I)


def clean_query(q):
    """Strip details a question may carry around the name: bracketed text, comma parts with digits or labels
    (DOB, IMO, ...), a trailing one-word part (country) when two or more name words remain, leading descriptors."""
    q = re.sub(r"[(\[].*?[)\]]", " ", q)
    parts = [p.strip() for p in re.split(r"[,;]", q) if p.strip()]
    parts = [p for p in parts if not re.search(r"\d", p) and not LABELS.match(p)] or parts[:1]
    if len(parts) > 1 and len(parts[-1].split()) == 1 and len(" ".join(parts[:-1]).split()) >= 2:
        parts = parts[:-1]
    return LEADING.sub("", ", ".join(parts))


def wallet_key(s):
    s = s.strip()
    return s.lower() if s.lower().startswith("0x") else s


_idx = None


def load():
    global _idx
    if _idx is None:
        d = json.loads(gzip.decompress(INDEX.read_bytes()))
        inv = {}
        for i, (k, _, _) in enumerate(d["names"]):
            for t in set(k.split()):
                inv.setdefault(t, []).append(i)
        d["inv"] = inv
        _idx = d
    return _idx


def score(a, b):
    return difflib.SequenceMatcher(None, a, b, autojunk=False).ratio()


def screen(q, exclude_lists=(), threshold=THRESHOLD, skip_name=None):  # skip_name: calibration only
    d = load()
    q = (q or "").strip()
    out = {"name": q, "matched": False, "match_score": 0.0, "matches": [],
           "lists": [{"list": l, **meta} for l, meta in d["lists"].items() if l not in exclude_lists]}
    # A wallet may arrive bare or inside text ("ETH:0x…", "wallet 1Lrx…").
    wal = [t for t in re.split(r"[\s,;:()\[\]'\"]+", q) if WALLET.match(t)]
    for t in wal:
        e = d["wallets"].get(wallet_key(t))
        if e is not None and d["entries"][e]["list"] not in exclude_lists:
            out.update(matched=True, match_score=1.0, query_type="wallet",
                       matches=[{**d["entries"][e], "matched_on": "wallet address", "score": 1.0}])
            return out
    if wal and len(wal) == len(q.split()):
        out["query_type"] = "wallet"
        return out
    keys = {x for x in (key(q), key(clean_query(q))) if x}
    if not keys:
        return out
    toks = {t for x in keys for t in x.split()}
    # Candidates share at least one token; rare tokens first keeps common words ("MOHAMMAD") from flooding.
    cand = set()
    for t in sorted(toks, key=lambda t: len(d["inv"].get(t, ()))):
        cand.update(d["inv"].get(t, ()))
        if len(cand) > 4000:
            break
    best = {}
    for i in cand:
        nk, e, _ = d["names"][i]
        if i == skip_name or d["entries"][e]["list"] in exclude_lists:
            continue
        s = max(score(k, nk) for k in keys)
        if s > best.get(e, (0,))[0]:
            best[e] = (s, i)
    ranked = sorted(best.items(), key=lambda x: -x[1][0])[:5]
    out["query_type"] = "name"
    out["matches"] = [{**d["entries"][e], "matched_on": d["names"][i][2], "score": round(s, 6)}
                      for e, (s, i) in ranked if s >= threshold]
    out["match_score"] = round(ranked[0][1][0], 6) if ranked else 0.0
    out["matched"] = bool(out["matches"])
    return out
