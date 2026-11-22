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


# Cyrillic -> Latin (passport-style). Without it, Cyrillic names normalise to "" and can never match (pre-test 2026-11-15).
CYR = dict(zip("абвгдеёжзийклмнопрстуфхцчшщъыьэюяіїєґў",
               "a b v g d e e zh z i y k l m n o p r s t u f kh ts ch sh shch _ y _ e yu ya i yi ye g u".split()))
CYR = {k: ("" if v == "_" else v) for k, v in CYR.items()}


def norm(s):
    s = "".join(CYR.get(c, CYR.get(c.lower(), c)) for c in s)
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().upper()
    return re.sub(r"[^A-Z0-9]+", " ", s).strip()


def key(s):
    toks = [t for t in norm(s).split() if t not in FORMS]
    return " ".join(sorted(toks))


LABELS = re.compile(r"^\s*(dob|d\.o\.b|born|date of birth|imo|mmsi|flag|nationality|citizen|passport|id|address|"
                    r"country|location|based in|registered in)\b", re.I)
LEADING = re.compile(r"^\s*((the )?(vessel|ship|tanker|mv|m/v|company|entity|individual|person|mr|mrs|ms|dr)\.?\s+)+", re.I)


def clean_query(q):
    """Strip details a question may carry around the name: bracketed text, appended dates or labelled fields,
    (DOB, IMO, ...), a trailing one-word part (country) when two or more name words remain, leading descriptors."""
    q = re.sub(r"[(\[].*?[)\]]", " ", q)
    parts = [p.strip() for p in re.split(r"[,;]", q) if p.strip()]
    # Subjects can contain digits (vessels and company names). Never discard
    # the subject as if it were an appended DOB/IMO field.
    parts = parts[:1] + [p for p in parts[1:] if not LABELS.match(p) and not re.fullmatch(r"[\d\s./-]+", p)]
    # A full name first ("Francesco Commisso, Siderno, Italy"; "Gold Global Company, Sidon, Lebanon"): the rest is
    # place detail. Dropping only the last word kept "Siderno" and pushed real matches under the threshold
    # (frontier test, 2026-11-22). A one-word first part is a surname-first name or a short form ("COMMISSO,
    # Francesco"; "VVB, PAO"), so it keeps its second part.
    if not parts:
        return ""
    first = LEADING.sub("", parts[0])
    # OFAC style "AL ASSAD, Bashar": a capitalised surname (no digits, unlike a vessel such as "HORMUZ 2"), then a given name.
    surname_first = first.isupper() and not re.search(r"\d", first) and len(parts) > 1 and not parts[1].isupper()
    if len(parts) > 1 and len(first.split()) >= 2 and not surname_first:
        # Drop place-like parts (letters only, up to three words: "Siderno", "Italy"); keep ones like "Unit 2".
        parts = parts[:1] + [p for p in parts[1:] if re.search(r"\d", p) or len(p.split()) > 3]
    elif len(parts) > 2:
        parts = parts[:2]
    if len(parts) > 1 and not surname_first and len(parts[-1].split()) == 1 and len(" ".join(parts[:-1]).split()) >= 2:
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


# Words that never identify an organisation on their own: legal forms and generic business words. A non-individual
# candidate below NEAR_EXACT must share at least one other word with the query (tester report, 2026-11-18: "VTB Bank"
# also listed "VVB, PAO" at 0.96 because "Public Joint-Stock Company" inflated the score).
GENERIC = FORMS | set("""PUBLIC JOINT STOCK OPEN CLOSED LIABILITY LIMITED BANK GROUP INTERNATIONAL TRADING TRADE
HOLDING HOLDINGS INDUSTRIES INDUSTRY ENTERPRISE ENTERPRISES SERVICES SHIPPING COMMERCIAL NATIONAL GENERAL INVESTMENT
INVESTMENTS DEVELOPMENT ENGINEERING TECHNOLOGY TECHNOLOGIES MANAGEMENT CAPITAL FINANCE FINANCIAL GLOBAL OIL GAS
ENERGY PUBLICHNOE AKTSIONERNOE OBSHCHESTVO OTKRYTOE ZAKRYTOE NEPUBLICHNOE OGRANICHENNOY OTVETSTVENNOSTYU""".split())
NEAR_EXACT = 0.99


def distinctive(k):
    return {t for t in k.split() if t not in GENERIC}


def score(a, b):
    return difflib.SequenceMatcher(None, a, b, autojunk=False).ratio()


def screen(q, exclude_lists=(), threshold=THRESHOLD, skip_name=None):  # skip_name: calibration only
    d = load()
    q = (q or "").strip()
    out = {"name": q, "matched": False, "match_score": 0.0, "matches": [],
           "lists": [{"list": l, **meta} for l, meta in d["lists"].items() if l not in exclude_lists]}
    # A wallet may arrive bare or inside text ("ETH:0x…", "wallet 1Lrx…").
    # Validate the entire token after removing sentence punctuation: malformed
    # or overlong addresses must not match a valid prefix.
    tokens = [t.strip(".?!“”‘’") for t in re.split(r"[\s,;:()\[\]'\"]+", q)]
    # The official files contain additional chains/formats beyond the syntax
    # recognizer. An exact indexed identifier must never be lost to that filter.
    wal = [t for t in tokens if WALLET.fullmatch(t) or wallet_key(t) in d["wallets"]]
    for t in wal:
        e = d["wallets"].get(wallet_key(t))
        if e is not None and d["entries"][e]["list"] not in exclude_lists:
            out.update(matched=True, match_score=1.0, query_type="wallet",
                       matches=[{**d["entries"][e], "matched_on": "wallet address", "score": 1.0}])
            return out
    if wal:
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
    qd = set().union(*(distinctive(k) for k in keys))

    def keep(e, s, i):
        if s < threshold:
            return False
        if s >= NEAR_EXACT or d["entries"][e].get("type") == "individual":
            return True
        return bool(qd & distinctive(d["names"][i][0]))
    out["matches"] = [{**d["entries"][e], "matched_on": d["names"][i][2], "score": round(s, 6)}
                      for e, (s, i) in ranked if keep(e, s, i)]
    if ranked and not out["matches"]:  # tester report: say which listed name was closest
        e, (s, i) = ranked[0]
        out["closest"] = {"name": d["entries"][e]["name"], "matched_on": d["names"][i][2], "list": d["entries"][e]["list"],
                          "score": round(s, 6)}
    out["match_score"] = round(ranked[0][1][0], 6) if ranked else 0.0
    out["matched"] = bool(out["matches"])
    return out
