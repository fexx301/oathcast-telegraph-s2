"""Build SANCTIONS_SCREENING_MATCH preference pairs for adapter training and held-out tests.

Real records only: OFAC SDN + alt.csv (public domain; with DOB, nationality, IMO and wallet remarks), plus real
unlisted GLEIF companies (CC0) cached by material v1. Questions are templated; answers are screening reports.

Every pair's worse answer has an error a reader can see from the question and answer alone: a quoted name, DOB,
nationality, IMO or wallet that contradicts the verdict, an internally inconsistent JSON response, or an
unscoped all-clear. Each kind is mirrored (the correct verdict is "match" in half and "no match" in the other
half) so verdict words alone can't separate better from worse.

Splits (frozen before training; see README):
  train / val  formats F1-F3, kinds K1 K3 K4 K5 K6 K7
  test_format  format F4 (memo) only, kinds as train            -> unseen answer format
  test_kind    kinds K2 (nationality) and K8 (alias logic) only -> unseen error kinds
Usage: python3 -I build_pairs.py   (writes data/*.jsonl and data/manifest.json)
"""
import csv, gzip, json, random, re, sys
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).parent
TS = HERE.parent / "telegraph-s2-sanctions-truth-source-v1"
MAT = HERE.parent / "telegraph-s2-sanctions-material-v1"
sys.path.insert(0, str(TS / "api"))
import _screen  # noqa: E402

RNG = random.Random(20261106)
LIST_DATE = "2026-10-28"
OUT = HERE / "data"
MONTHS = "Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split()


def load_sdn():
    ents = {}
    for r in csv.reader(open(TS / "raw" / "sdn.csv", encoding="latin-1")):
        if len(r) < 12:
            continue
        rem, typ = r[11], (r[2].strip() if r[2].strip() != "-0-" else "entity")
        dob = re.search(r"DOB (\d{1,2} \w{3} \d{4})", rem)
        nat = re.search(r"nationality ([A-Z][A-Za-z ]+?)(?:;|\.|$)", rem)
        imo = re.search(r"IMO (\d{7})", rem)
        wal = re.findall(r"Digital Currency Address - (\w+) ([A-Za-z0-9]{20,})", rem)
        ents[r[0]] = {"uid": r[0], "name": r[1].strip(), "type": typ, "programs": r[3].split() if r[3].strip() != "-0-" else [],
                      "dob": dob.group(1) if dob else None, "nat": nat.group(1).strip() if nat else None,
                      "imo": imo.group(1) if imo else None, "wallets": wal, "aliases": []}
    for r in csv.reader(open(TS / "raw" / "alt.csv", encoding="latin-1")):
        if len(r) >= 4 and r[0] in ents and r[3].strip() and r[2].strip() in ("aka", "fka"):
            ents[r[0]]["aliases"].append(r[3].strip())
    for e in ents.values():
        e["programs"] = [p.strip("[]") for p in e["programs"] if p.strip("[]")] or ["SDN"]
    return list(ents.values())


def gleif_names():
    out = set()
    for f in (MAT / "raw" / "gleif").glob("*.json"):
        d = json.loads(f.read_text()).get("data")
        if isinstance(d, list):
            for r in d:
                ent = r["attributes"]["entity"]
                out.add((ent["legalName"]["name"], ent["legalAddress"]["country"], r["id"]))
    return sorted(out)


def other_dob(d):
    day, mon, yr = d.split()
    return f"{day} {mon} {int(yr) + RNG.choice([-9, -6, -4, -3, -2, 2, 3, 5, 7, 11])}"


def mutate(addr):
    i = RNG.randrange(4, len(addr) - 2)
    alphabet = "0123456789abcdef" if addr.startswith("0x") else "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
    return addr[:i] + RNG.choice([c for c in alphabet if c != addr[i]]) + addr[i + 1:]


def other_imo(n):
    return str(int(n) + RNG.choice([-71, -13, 9, 24, 102, 340])).zfill(7)


# ---------------- prompts ----------------
DESKS = ["Our stablecoin desk received a redemption request from", "Onboarding a new corporate client:",
         "Before releasing the wire, our payments team needs to screen", "Exchange compliance: a withdrawal is going to",
         "Trade finance check on the counterparty", "KYC refresh for an existing customer,", "A broker introduced",
         "Treasury wants to pay an invoice from", "Charter desk: we are about to fix a voyage with", "Legal asked us to screen"]
ASKS = ["Screen it against sanctions lists and tell me if there's a match.", "Is this a sanctions match? Give the list entry if so.",
        "Check OFAC, UN and EU lists and report the result.", "Run a sanctions screen and explain the result.",
        "Does this hit any consolidated sanctions list?", "Screen and give a clear match / no-match answer with the basis."]


def prompt(subject):
    return f"{RNG.choice(DESKS)} {subject}. {RNG.choice(ASKS)}"


# ---------------- answer formats ----------------
def render(fmt, verdict, query, entry=None, basis="", note="", nearest=None):
    """verdict: 'match' | 'nomatch' | 'possible'. entry: the matched listing; nearest: the closest listing a no-match cites."""
    c = entry or nearest
    cite = f"'{c['name']}' (OFAC SDN UID {c['uid']}; program {', '.join(c['programs'][:2])})" if c else ""
    if fmt == "F2":  # the intent's JSON response
        matched = verdict == "match"
        body = {"name": query, "matched": matched,
                "matches": ([{"list": "OFAC SDN", "id": entry["uid"], "name": entry["name"], "programs": entry["programs"][:2],
                              **entry.get("extra", {})}] if entry else []),
                "lists": [{"list": "OFAC SDN", "published": LIST_DATE}, {"list": "UN Security Council Consolidated", "published": "2026-11-02"}],
                "match_score": entry.get("score", 1.0 if matched else 0.0) if entry else 0.0}
        if nearest:
            body["nearest"] = {"list": "OFAC SDN", "id": nearest["uid"], "name": nearest["name"], **nearest.get("extra", {})}
        if basis:
            body["note"] = basis + (" " + note if note else "")
        return json.dumps(body, ensure_ascii=False)
    head = {"match": "MATCH", "nomatch": "NO MATCH", "possible": "POSSIBLE MATCH, NOT CONFIRMED"}[verdict]
    if fmt == "F3":  # terse verdict line
        return f"{head}: {query}" + (f" -> {cite}" if entry else f" (nearest: {cite})" if cite else "") + (f". {basis}" if basis else "") + (f" {note}" if note else "")
    if fmt == "F4":  # analyst memo (held out of training)
        lines = [f"Subject: {query}", f"Outcome: {head.lower()}"]
        if cite:
            lines.append(f"Listing reviewed: {cite}" if entry else f"Nearest listing: {cite}")
        if basis:
            lines.append(f"Reasoning: {basis}")
        lines.append(f"Coverage: OFAC SDN ({LIST_DATE}) and UN consolidated list. {note or 'Ownership (50% rule) not assessed.'}")
        return "\n- ".join(lines)
    # F1 prose
    s = f"Screening result: {head.lower()} for '{query}'."
    if cite:
        s += f" Listing: {cite}." if entry else f" Nearest listing: {cite}."
    if basis:
        s += f" {basis}"
    return s + f" Lists: OFAC SDN as of {LIST_DATE} and the UN consolidated list. {note}".rstrip()


SCOPED = "Not a clearance: other lists and ownership links were not checked."
SCOPE_PAIRS = [
    ("This does not confirm the party is unsanctioned everywhere; further checks are needed before it is cleared.",
     "This confirms the party is unsanctioned everywhere; no further checks are needed, so it is cleared."),
    ("A no-match here is not a clearance under every regime; ownership and other lists still need checking.",
     "A no-match here is a clearance under every regime; ownership and other lists need no checking."),
    ("Absent from these two lists only; that does not establish the party is free of all sanctions exposure.",
     "Absent from these two lists, which establishes the party is free of all sanctions exposure.")]


def ent_view(e, **extra):
    return {"name": e["name"], "uid": e["uid"], "programs": e["programs"], "extra": extra}


# ---------------- kinds ----------------
def k1_dob(e, fmt):
    """Name + DOB given. Same DOB -> match; different DOB -> possible namesake, not confirmed."""
    given = e["dob"] if RNG.random() < 0.5 else other_dob(e["dob"])
    p = prompt(f"'{e['name']}', DOB {given}")
    same = given == e["dob"]
    ev = ent_view(e, dob=e["dob"])
    if same:
        good = render(fmt, "match", e["name"], ev, f"Name and DOB {e['dob']} both match the listing.", SCOPED)
        bad = render(fmt, "possible", e["name"], ev, f"Listed DOB {e['dob']} differs from the given DOB {given}, so this is likely a namesake.", SCOPED)
    else:
        good = render(fmt, "possible", e["name"], ev, f"Listed DOB {e['dob']} differs from the given DOB {given}, so this is likely a namesake.", "Escalate for review. " + SCOPED)
        bad = render(fmt, "match", e["name"], ev, f"Name and DOB {e['dob']} both match the listing.", "Escalate for review. " + SCOPED)
    return p, good, bad


def k2_nat(e, fmt):
    """Held-out kind: name + nationality."""
    nats = ["Iran", "Russia", "Syria", "Venezuela", "Cuba", "Lebanon", "Iraq", "China", "Turkey", "United Arab Emirates", "Belarus"]
    given = e["nat"] if RNG.random() < 0.5 else RNG.choice([n for n in nats if n != e["nat"]])
    p = prompt(f"'{e['name']}', a national of {given}")
    ev = ent_view(e, nationality=e["nat"])
    a = render(fmt, "match", e["name"], ev, f"Name and nationality ({e['nat']}) both match the listing.", SCOPED)
    b = render(fmt, "possible", e["name"], ev, f"The listing gives nationality {e['nat']}, not {given}; possibly a different person.", SCOPED)
    return (p, a, b) if given == e["nat"] else (p, b, a)


def k3_wallet(e, fmt):
    cur, addr = RNG.choice(e["wallets"])
    if RNG.random() < 0.5:
        q = addr
        p = prompt(f"the {cur} wallet {q}")
        good = render(fmt, "match", q, ent_view(e, address=addr), f"Exact address match: {addr} is listed for this party.", SCOPED)
        bad = render(fmt, "nomatch", q, None, f"Nearest listed address is {addr}, which differs, so no match.", SCOPED, ent_view(e, address=addr))
    else:
        q = mutate(addr)
        p = prompt(f"the {cur} wallet {q}")
        good = render(fmt, "nomatch", q, None, f"Nearest listed address is {addr}, which differs, so no match.", SCOPED, ent_view(e, address=addr))
        bad = render(fmt, "match", q, ent_view(e, address=addr), f"Exact address match: {addr} is listed for this party.", SCOPED)
    return p, good, bad


def k4_imo(e, fmt):
    given = e["imo"] if RNG.random() < 0.5 else other_imo(e["imo"])
    p = prompt(f"the vessel {e['name']} (IMO {given})")
    ev = ent_view(e, imo=e["imo"])
    a = render(fmt, "match", e["name"], ev, f"Vessel name and IMO {e['imo']} match the listing.", SCOPED)
    b = render(fmt, "nomatch", e["name"], None, f"A listed vessel {e['name']} has IMO {e['imo']}, not {given}: a different ship.", SCOPED, ev)
    return (p, a, b) if given == e["imo"] else (p, b, a)


def k6_json(e, fmt):
    """JSON whose matched flag, matches and match_score agree vs. disagree (always F2). Verdict balanced 50/50."""
    is_match = RNG.random() < 0.5
    q = e["name"] if is_match else e["name"] + " " + RNG.choice(["TRADING", "HOLDINGS", "GROUP", "INTERNATIONAL"])
    p = prompt(f"'{q}'")
    hit = {"list": "OFAC SDN", "id": e["uid"], "name": e["name"], "programs": e["programs"][:2]}
    hi, lo = round(RNG.uniform(0.86, 1.0), 2), round(RNG.uniform(0.05, 0.35), 2)
    lists = json.loads(render("F2", "nomatch", q))["lists"]
    good = {"name": q, "matched": is_match, "matches": [hit] if is_match else [], "lists": lists,
            "match_score": hi if is_match else lo}
    if not is_match:
        good["nearest"] = hit
    bad = dict(good)
    if RNG.random() < 0.5:
        bad["matched"] = not is_match  # flag contradicts matches and score
    else:
        bad["match_score"] = lo if is_match else hi  # score contradicts the flag
    return p, json.dumps(good, ensure_ascii=False), json.dumps(bad, ensure_ascii=False)


def k7_scope(company, sib, fmt):
    name, cc, lei = company
    p = prompt(f"'{name}' ({cc})")
    good, bad = RNG.choice(SCOPE_PAIRS)
    return p, render(fmt, "nomatch", name, None, "No listed name or alias is close.", good, ent_view(sib)), \
        render(fmt, "nomatch", name, None, "No listed name or alias is close.", bad, ent_view(sib))


def k8_alias(e, fmt):
    """Held-out kind: an alias is a match; treating aliases as non-matches is the error."""
    a = RNG.choice(e["aliases"])
    p = prompt(f"'{a}'")
    good = render(fmt, "match", a, ent_view(e), f"'{a}' is a listed alias of '{e['name']}'; aliases count as matches.", SCOPED)
    bad = render(fmt, "nomatch", a, None, f"'{a}' is only listed as an alias of '{e['name']}', so it is not a match.", SCOPED, ent_view(e))
    return p, good, bad


def main():
    ents = load_sdn()
    by_tok = defaultdict(list)
    for e in ents:
        for t in set(_screen.key(e["name"]).split()):
            if len(t) > 3:
                by_tok[t].append(e)
    comps = []
    for name, cc, lei in gleif_names():
        r = _screen.screen(name)
        if r["matched"] or r["match_score"] >= 0.8:
            continue  # keep only companies clearly not on the lists
        toks = [t for t in _screen.key(name).split() if len(t) > 3 and by_tok.get(t)]
        if toks:
            comps.append(((name, cc, lei), RNG.choice(by_tok[toks[0]])))
    RNG.shuffle(comps)
    pool = {"K1": [e for e in ents if e["dob"] and e["type"] == "individual"],
            "K2": [e for e in ents if e["nat"] and e["type"] == "individual"],
            "K3": [e for e in ents if e["wallets"]],
            "K4": [e for e in ents if e["imo"]],
            "K5": [e for e in ents if len(e["name"]) > 6],
            "K6": [e for e in ents if len(e["name"]) > 6],
            "K8": [e for e in ents if e["aliases"]]}
    for k in pool:
        RNG.shuffle(pool[k])
    target = {"K1": 600, "K2": 150, "K3": 300, "K4": 450, "K5": 600, "K6": 400, "K7": 0, "K8": 150}
    rows = []
    used = Counter()

    def sibling(e):
        for t in sorted(set(_screen.key(e["name"]).split()), key=len, reverse=True):
            c = [x for x in by_tok.get(t, []) if x["uid"] != e["uid"] and x["name"] != e["name"]]
            if c:
                return RNG.choice(c)
    ci = 0
    for kind, n in target.items():
        for i in range(n):
            fmt = RNG.choice(["F1", "F2", "F3", "F4"]) if kind != "K6" else "F2"
            if kind == "K7":
                comp, sib = comps[ci % len(comps)]; ci += 1
                p, g, b = k7_scope(comp, sib, fmt); src = comp
            elif kind == "K5":
                e = pool[kind][i % len(pool[kind])]
                o = sibling(e)
                if not o:
                    continue
                comp, sib = comps[ci % len(comps)]; ci += 1
                p, g, b = _k5_listed(e, o, fmt) if RNG.random() < 0.5 else _k5_company(comp, sib, fmt)
                src = e["uid"]
            else:
                e = pool[kind][i % len(pool[kind])]
                p, g, b = {"K1": k1_dob, "K2": k2_nat, "K3": k3_wallet, "K4": k4_imo, "K6": k6_json, "K8": k8_alias}[kind](e, fmt)
                src = e["uid"]
            if g == b:
                continue
            rows.append({"prompt": p, "chosen": g, "rejected": b, "label_kind": "preference_pair", "_kind": kind, "_fmt": fmt, "_src": str(src)})
            used[kind] += 1
    # de-duplicate identical prompts
    seen, uniq = set(), []
    for r in rows:
        if r["prompt"] not in seen:
            seen.add(r["prompt"]); uniq.append(r)
    RNG.shuffle(uniq)
    split = {"train": [], "val": [], "test_format": [], "test_kind": []}
    for r in uniq:
        if r["_kind"] in ("K2", "K8"):
            split["test_kind"].append(r)
        elif r["_fmt"] == "F4":
            split["test_format"].append(r)
        else:
            (split["val"] if RNG.random() < 0.12 else split["train"]).append(r)
    # no source entity shared between train and any test split
    test_src = {r["_src"] for s in ("test_format", "test_kind") for r in split[s]}
    split["train"] = [r for r in split["train"] if r["_src"] not in test_src]
    OUT.mkdir(exist_ok=True)
    man = {}
    for s, rs in split.items():
        with open(OUT / f"{s}.jsonl", "w") as f:
            for r in rs:
                f.write(json.dumps({k: v for k, v in r.items() if not k.startswith("_")}, ensure_ascii=False) + "\n")
        with open(OUT / f"{s}.meta.jsonl", "w") as f:
            for r in rs:
                f.write(json.dumps({"kind": r["_kind"], "fmt": r["_fmt"], "src": r["_src"]}) + "\n")
        man[s] = {"n": len(rs), "kinds": dict(Counter(r["_kind"] for r in rs)), "formats": dict(Counter(r["_fmt"] for r in rs))}
    man["companies_kept"] = len(comps)
    (OUT / "manifest.json").write_text(json.dumps(man, indent=1))
    print(json.dumps(man, indent=1))


def _k5_listed(e, o, fmt):
    p = prompt(f"'{e['name']}'")
    good = render(fmt, "match", e["name"], ent_view(e), "Exact name match.", SCOPED)
    if RNG.random() < 0.5:
        return p, good, render(fmt, "match", e["name"], ent_view(o), "Exact name match.", SCOPED)  # wrong entry
    # calls the identical listed name "a different party"
    return p, good, render(fmt, "nomatch", e["name"], None, f"Nearest listed name is '{e['name']}', a different party.", SCOPED, ent_view(e))


def _k5_company(comp, sib, fmt):
    name, cc, lei = comp
    p = prompt(f"'{name}' ({cc}, LEI {lei})")
    return p, render(fmt, "nomatch", name, None, f"Nearest listed name is '{sib['name']}', a different party.", SCOPED, ent_view(sib)), \
        render(fmt, "match", name, ent_view(sib), "Exact name match.", SCOPED)


if __name__ == "__main__":
    main()
