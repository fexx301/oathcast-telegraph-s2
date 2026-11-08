"""Fetch the official lists (keyless) into raw/ and build api/index.json.gz.

Usage: python3 -I build_index.py [--refetch]
"""
import csv, gzip, io, json, os, re, sys, time, urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

HERE = Path(__file__).parent
RAW = Path(os.environ.get("RAW_DIR") or HERE / "raw")  # the refresher Lambda points these at /tmp
OUT = Path(os.environ.get("INDEX_OUT") or HERE / "api" / "index.json.gz")
sys.path[:0] = [str(HERE / "api"), str(HERE)]
from _screen import key, wallet_key  # noqa: E402

OFAC = "https://sanctionslistservice.ofac.treas.gov/api/publicationpreview/exports/"
SRC = {
    "sdn.csv": OFAC + "sdn.csv",
    "alt.csv": OFAC + "alt.csv",
    "cons_prim.csv": OFAC + "cons_prim.csv",
    "cons_alt.csv": OFAC + "cons_alt.csv",
    "un.xml": "https://scsanctions.un.org/resources/xml/en/consolidated.xml",
    # The token is the Commission's published public one, not a credential.
    "eu.csv": "https://webgate.ec.europa.eu/fsd/fsf/public/files/csvFullSanctionsList_1_1/content?token=dG9rZW4tMjAxNw",
}


def fetch(refetch):
    RAW.mkdir(exist_ok=True)
    log = {}
    if (RAW / "fetch-log.json").exists():
        log = json.loads((RAW / "fetch-log.json").read_text())
    for fn, url in SRC.items():
        if (RAW / fn).exists() and not refetch:
            continue
        for attempt in range(3):  # the EU server resets long downloads now and then
            try:
                with urllib.request.urlopen(url, timeout=900) as r:
                    body = r.read()
                    lm = r.headers.get("Last-Modified")
                break
            except OSError as e:
                print("retry", fn, e)
                if attempt == 2:
                    raise
        (RAW / fn).write_bytes(body)
        log[fn] = {"url": url, "captured_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                   "bytes": len(body), "last_modified": lm}
        print("fetched", fn, len(body))
        (RAW / "fetch-log.json").write_text(json.dumps(log, indent=1))
    return log


def clean(v):
    v = (v or "").strip()
    return "" if v == "-0-" else v


def build(log):
    entries, names, wallets, seen = [], [], {}, set()

    def add_entry(lst, ident, name, typ, programs):
        entries.append({"list": lst, "id": str(ident), "name": name, "type": typ, "programs": programs})
        return len(entries) - 1

    def add_name(e, n):
        k = key(n)
        if k and (e, k) not in seen:
            seen.add((e, k))
            names.append([k, e, n])

    # OFAC SDN + its aliases + wallet addresses from remarks
    uid2e = {}
    with (RAW / "sdn.csv").open(encoding="latin-1", newline="") as f:
        for row in csv.reader(f):
            if len(row) < 12 or not row[0].strip().isdigit():
                continue
            progs = [p.strip(" []") for p in clean(row[3]).split("] [") if p.strip(" []")]
            e = add_entry("OFAC SDN", row[0].strip(), clean(row[1]), clean(row[2]) or "entity", progs)
            uid2e[row[0].strip()] = e
            add_name(e, clean(row[1]))
            for cur, addr in re.findall(r"Digital Currency Address - ([A-Z0-9]+) ([A-Za-z0-9]{20,})", clean(row[11])):
                wallets[wallet_key(addr)] = e
    with (RAW / "alt.csv").open(encoding="latin-1", newline="") as f:
        for row in csv.reader(f):
            if len(row) >= 4 and row[0].strip() in uid2e and clean(row[3]):
                add_name(uid2e[row[0].strip()], clean(row[3]))
    # OFAC Consolidated (non-SDN)
    cuid = {}
    with (RAW / "cons_prim.csv").open(encoding="latin-1", newline="") as f:
        for row in csv.reader(f):
            if len(row) >= 4 and row[0].strip().isdigit() and clean(row[1]):
                progs = [p.strip(" []") for p in clean(row[3]).split("] [") if p.strip(" []")]
                e = add_entry("OFAC Consolidated (non-SDN)", row[0].strip(), clean(row[1]), clean(row[2]) or "entity", progs)
                cuid[row[0].strip()] = e
                add_name(e, clean(row[1]))
    with (RAW / "cons_alt.csv").open(encoding="latin-1", newline="") as f:
        for row in csv.reader(f):
            if len(row) >= 4 and row[0].strip() in cuid and clean(row[3]):
                add_name(cuid[row[0].strip()], clean(row[3]))
    # UN Security Council consolidated list
    root = ET.parse(RAW / "un.xml").getroot()
    un_date = root.get("dateGenerated")
    for tag, typ, alias_tag in (("INDIVIDUAL", "individual", "INDIVIDUAL_ALIAS"), ("ENTITY", "entity", "ENTITY_ALIAS")):
        for x in root.iter(tag):
            parts = [(x.findtext(k) or "").strip() for k in ("FIRST_NAME", "SECOND_NAME", "THIRD_NAME", "FOURTH_NAME")]
            name, ref = " ".join(p for p in parts if p), (x.findtext("REFERENCE_NUMBER") or "").strip()
            if not (name and ref):
                continue
            e = add_entry("UN Security Council Consolidated", ref, name, typ, [(x.findtext("UN_LIST_TYPE") or "").strip()])
            add_name(e, name)
            for a in x.iter(alias_tag):
                if (a.findtext("ALIAS_NAME") or "").strip():
                    add_name(e, a.findtext("ALIAS_NAME").strip())
    # EU consolidated financial sanctions list
    eu_e, eu_date = {}, None
    text = (RAW / "eu.csv").read_bytes().decode("utf-8-sig")
    for row in csv.DictReader(io.StringIO(text), delimiter=";"):
        lid, whole = row["Entity_LogicalId"], (row["NameAlias_WholeName"] or "").strip()
        eu_date = eu_date or row["fileGenerationDate"]
        if lid not in eu_e:
            typ = {"P": "individual", "E": "entity"}.get(row["Entity_SubjectType"], row["Entity_SubjectType"])
            eu_e[lid] = add_entry("EU Consolidated Financial Sanctions", row["Entity_EU_ReferenceNumber"] or lid,
                                  whole, typ, [row["Entity_Regulation_Programme"]])
        if whole:
            if not entries[eu_e[lid]]["name"]:
                entries[eu_e[lid]]["name"] = whole
            add_name(eu_e[lid], whole)

    lists = {
        "OFAC SDN": {"source": SRC["sdn.csv"], "published": log["sdn.csv"]["last_modified"], "captured_at": log["sdn.csv"]["captured_at"]},
        "OFAC Consolidated (non-SDN)": {"source": SRC["cons_prim.csv"], "published": log["cons_prim.csv"]["last_modified"],
                                        "captured_at": log["cons_prim.csv"]["captured_at"]},
        "UN Security Council Consolidated": {"source": SRC["un.xml"], "published": un_date, "captured_at": log["un.xml"]["captured_at"]},
        "EU Consolidated Financial Sanctions": {"source": SRC["eu.csv"].split("?")[0], "published": eu_date,
                                                "captured_at": log["eu.csv"]["captured_at"]},
    }
    idx = {"lists": lists, "entries": entries, "names": names, "wallets": wallets}
    OUT.write_bytes(gzip.compress(json.dumps(idx, separators=(",", ":")).encode(), 9))
    by = {}
    for x in entries:
        by[x["list"]] = by.get(x["list"], 0) + 1
    summary = {"entries": by, "names": len(names), "wallets": len(wallets), "lists": lists}
    print(json.dumps(summary, indent=1))
    return summary


if __name__ == "__main__":
    build(fetch("--refetch" in sys.argv))
