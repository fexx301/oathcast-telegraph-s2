"""Fetch GeoNames cities + GHCN-Daily station files (keyless) into raw/ and build index.json.gz.

Usage: python3 -I build_index.py [--refetch]
"""
import gzip, io, json, os, sys, time, urllib.request, zipfile
from pathlib import Path

HERE = Path(__file__).parent
RAW = Path(os.environ.get("RAW_DIR") or HERE / "raw")
OUT = Path(os.environ.get("INDEX_OUT") or HERE / "app" / "index.json.gz")
SRC = {
    "cities15000.zip": "https://download.geonames.org/export/dump/cities15000.zip",
    "countryInfo.txt": "https://download.geonames.org/export/dump/countryInfo.txt",
    "admin1CodesASCII.txt": "https://download.geonames.org/export/dump/admin1CodesASCII.txt",
    "ghcnd-stations.txt": "https://www.ncei.noaa.gov/pub/data/ghcn/daily/ghcnd-stations.txt",
    "ghcnd-inventory.txt": "https://www.ncei.noaa.gov/pub/data/ghcn/daily/ghcnd-inventory.txt",
    # Full GeoNames gazetteers for the countries whose ECA&D longitudes can lose their sign (see fix_signs).
    "GB.zip": "https://download.geonames.org/export/dump/GB.zip",
    "ES.zip": "https://download.geonames.org/export/dump/ES.zip",
    "FR.zip": "https://download.geonames.org/export/dump/FR.zip",
}
GAZ = {"UK": "GB", "SP": "ES", "FR": "FR"}  # GHCN (FIPS) prefix -> GeoNames file
SIGN_KM = 15  # a same-named gazetteer place must lie this close to the chosen position
MIN_LASTYEAR = 2025  # stations still reporting TMAX


def fetch(refetch):
    RAW.mkdir(parents=True, exist_ok=True)
    logp = RAW / "fetch-log.json"
    log = json.loads(logp.read_text()) if logp.exists() else {}
    for fn, url in SRC.items():
        if (RAW / fn).exists() and not refetch:
            continue
        for attempt in range(3):
            try:
                with urllib.request.urlopen(url, timeout=600) as r:
                    body, lm = r.read(), r.headers.get("Last-Modified")
                break
            except OSError as e:
                print("retry", fn, e)
                if attempt == 2:
                    raise
        (RAW / fn).write_bytes(body)
        log[fn] = {"url": url, "captured_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "bytes": len(body),
                   "last_modified": lm}
        logp.write_text(json.dumps(log, indent=1))
        print("fetched", fn, len(body))
    return log


def fix_signs(stations, fold):
    """ECA&D ids lose the sign of a longitude between 0 and -1 degree, so 0 < lon < 1 can be either sign.
    Keep the sign that puts the station within SIGN_KM of a gazetteer place sharing its name; else drop it."""
    import math, re
    amb = [st for st in stations if st[0][2] == "E" and 0 < st[2] < 1]
    places = {}
    for cc in {GAZ[st[0][:2]] for st in amb if st[0][:2] in GAZ}:
        with zipfile.ZipFile(RAW / f"{cc}.zip") as z:
            for line in z.read(f"{cc}.txt").decode("utf-8").splitlines():
                p = line.split("\t")
                for n in {p[1], p[2], *p[3].split(",")}:
                    if n:
                        places.setdefault((cc, fold(n)), []).append((float(p[4]), float(p[5])))

    def km(lat1, lon1, lat2, lon2):
        a = (math.sin(math.radians(lat2 - lat1) / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2))
             * math.sin(math.radians(lon2 - lon1) / 2) ** 2)
        return 12742 * math.asin(math.sqrt(a))
    fixed, dropped = {}, []
    for st in amb:
        cc = GAZ.get(st[0][:2])
        names = {fold(n) for n in [st[3], *re.split(r"[/(),]| - ", st[3])]} - {""}
        pts = [pt for n in names for pt in places.get((cc, n), [])] if cc else []
        best = min(((km(st[1], sg * st[2], *pt), sg) for pt in pts for sg in (1, -1)), default=None)
        if best and best[0] <= SIGN_KM:
            fixed[st[0]] = best[1] * st[2]
        else:
            dropped.append(st[0])
    print("ECA&D signs resolved:", sum(v < 0 for v in fixed.values()), "west,", sum(v > 0 for v in fixed.values()), "east")
    out = [st[:2] + [fixed.get(st[0], st[2])] + st[3:] for st in stations if st[0] not in set(dropped)]
    return out, len(dropped)


def build(log):
    sys.path[:0] = [str(HERE / "app"), str(HERE)]
    from _wfv import fold  # noqa: E402
    # Stations with TMAX reported through MIN_LASTYEAR or later.
    tmax = {}
    for line in (RAW / "ghcnd-inventory.txt").read_text().splitlines():
        p = line.split()
        if len(p) == 6 and p[3] == "TMAX" and int(p[5]) >= MIN_LASTYEAR:
            tmax[p[0]] = (int(p[4]), int(p[5]))
    stations = []
    for line in (RAW / "ghcnd-stations.txt").read_text().splitlines():
        sid = line[0:11]
        if sid in tmax:
            stations.append([sid, round(float(line[12:20]), 4), round(float(line[21:30]), 4), line[41:71].strip(),
                             tmax[sid][0], tmax[sid][1]])
    # ECA&D-sourced ids (third letter "E", e.g. UKE00107650 HEATHROW at +0.4489, really -0.461) lose the sign of
    # longitudes between 0 and -1 degree ("-0:27" -> 0.45). Such a longitude is ambiguous, so drop those stations.
    stations, dropped = fix_signs(stations, fold)
    print("ECA&D stations with ambiguous 0..1 longitude dropped (no same-named place within", SIGN_KM, "km):", dropped)
    countries = {}
    for line in (RAW / "countryInfo.txt").read_text(encoding="utf-8").splitlines():
        if line.startswith("#") or not line.strip():
            continue
        p = line.split("\t")
        for n in (p[0], p[1], p[4]):  # ISO2, ISO3, name
            countries[fold(n)] = p[0]
    countries.update({fold(k): v for k, v in {"USA": "US", "United States of America": "US", "America": "US",
                                               "UK": "GB", "Britain": "GB", "England": "GB", "Scotland": "GB",
                                               "Wales": "GB", "Russia": "RU", "South Korea": "KR",
                                               "North Korea": "KP", "Czech Republic": "CZ", "Holland": "NL"}.items()})
    admin1 = {}
    for line in (RAW / "admin1CodesASCII.txt").read_text(encoding="utf-8").splitlines():
        p = line.split("\t")
        if len(p) >= 3:
            admin1[p[0]] = [p[1], p[2]]  # US admin1 codes are the state postal codes (US.TX)
    cities, names = [], {}
    with zipfile.ZipFile(RAW / "cities15000.zip") as z:
        text = z.read("cities15000.txt").decode("utf-8")
    for line in text.splitlines():
        p = line.split("\t")
        i = len(cities)
        cities.append([p[1], p[8], p[10], round(float(p[4]), 4), round(float(p[5]), 4), int(p[14] or 0)])
        alts = [a for a in p[3].split(",") if a and len(a) <= 40]
        for n in {p[1], p[2], *alts}:
            k = fold(n)
            if k:
                names.setdefault(k, []).append(i)
    idx = {"stations": stations, "cities": cities, "names": names, "countries": countries, "admin1": admin1,
           "sources": {k: {"url": v["url"], "captured_at": v["captured_at"], "last_modified": v["last_modified"]}
                       for k, v in log.items()}}
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_bytes(gzip.compress(json.dumps(idx, separators=(",", ":")).encode(), 9))
    summary = {"stations": len(stations), "cities": len(cities), "names": len(names), "bytes": OUT.stat().st_size}
    print(json.dumps(summary))
    return summary


if __name__ == "__main__":
    build(fetch("--refetch" in sys.argv))
