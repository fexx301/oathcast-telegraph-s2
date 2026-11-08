"""Place name + past date -> what the nearest GHCN-Daily weather station recorded (NOAA NCEI, keyless)."""
import datetime as dt, gzip, json, math, re, unicodedata, urllib.parse, urllib.request
from pathlib import Path

INDEX = Path(__file__).with_name("index.json.gz")
NCEI = "https://www.ncei.noaa.gov/access/services/data/v1"
MAX_KM, MAX_STATIONS = 50, 6


def fold(s):
    s = unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", " ", s).strip()


_idx = None


def load():
    global _idx
    if _idx is None:
        _idx = json.loads(gzip.decompress(INDEX.read_bytes()))
    return _idx


def resolve(location):
    """Most populous GeoNames city with that name, narrowed by any ', country' / ', state' qualifiers."""
    d = load()
    parts = [p.strip() for p in re.split(r"[,;]", location) if p.strip()]
    if not parts:
        return None
    cand = d["names"].get(fold(parts[0])) or d["names"].get(fold(location)) or []
    for q in parts[1:]:
        fq = fold(q)
        if fq in d["countries"]:
            keep = [i for i in cand if d["cities"][i][1] == d["countries"][fq]]
        else:
            keep = [i for i in cand if (a := d["admin1"].get(f"{d['cities'][i][1]}.{d['cities'][i][2]}"))
                    and (fq in (fold(a[0]), fold(a[1])) or fq == fold(d["cities"][i][2]))]
        if keep or fq in d["countries"]:
            cand = keep  # an unknown qualifier ("downtown") is ignored; a known one that matches nothing empties
    if not cand:
        return None
    i = max(cand, key=lambda i: d["cities"][i][5])
    name, cc, a1, lat, lon, pop = d["cities"][i]
    a = d["admin1"].get(f"{cc}.{a1}")
    return {"name": name, "admin1": a[0] if a else a1, "country": cc, "lat": lat, "lon": lon, "population": pop}


def km(lat1, lon1, lat2, lon2):
    p1, p2, dl = math.radians(lat1), math.radians(lat2), math.radians(lon2 - lon1)
    a = math.sin((p2 - p1) / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 6371.0 * 2 * math.asin(math.sqrt(a))


def nearest(lat, lon, year):
    out = []
    for sid, slat, slon, sname, y0, y1 in load()["stations"]:
        if abs(slat - lat) > 0.5 or not (y0 <= year <= y1):
            continue
        k = km(lat, lon, slat, slon)
        if k <= MAX_KM:
            out.append((k, sid, sname, slat, slon))
    return sorted(out)[:MAX_STATIONS]


def parse_date(s):
    try:
        d = dt.date.fromisoformat((s or "").strip()[:10])
    except ValueError:
        return None
    return d if d < dt.datetime.now(dt.timezone.utc).date() else None


def ncei(stations, day):
    q = {"dataset": "daily-summaries", "stations": ",".join(stations), "startDate": day, "endDate": day,
         "dataTypes": "TMAX,TMIN,PRCP", "units": "metric", "format": "json"}
    url = NCEI + "?" + urllib.parse.urlencode(q)
    with urllib.request.urlopen(url, timeout=20) as r:
        return url, json.load(r)


def num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def verify(location, date, fetch=ncei):
    """Returns (http_status, body)."""
    day = parse_date(date)
    if not (location or "").strip() or day is None:
        return 400, {"error": "location (place name) and a past date (YYYY-MM-DD) are required"}
    place = resolve(location)
    if place is None:
        return 404, {"error": f"place not found: {location}"}
    near = nearest(place["lat"], place["lon"], day.year)
    if not near:
        return 404, {"error": f"no GHCN-Daily station with TMAX within {MAX_KM} km of {place['name']}", "place": place}
    url, rows = fetch([s[1] for s in near], day.isoformat())
    by = {r.get("STATION"): r for r in rows if num(r.get("TMAX")) is not None}
    for k, sid, sname, slat, slon in near:
        r = by.get(sid)
        if r:
            return 200, {
                "location": f"{place['name']}, {place['admin1']}, {place['country']}", "date": day.isoformat(),
                "temp_max_c": num(r["TMAX"]), "temp_min_c": num(r.get("TMIN")), "precipitation_mm": num(r.get("PRCP")),
                "condition": None,
                "station": {"id": sid, "name": sname, "distance_km": round(k, 1), "lat": slat, "lon": slon},
                "place": place, "source": url, "dataset": "NOAA NCEI GHCN-Daily (daily-summaries)"}
    return 404, {"error": f"no TMAX recorded on {day} at the {len(near)} nearest stations (GHCN-Daily lags ~2-5 days)",
                 "place": place, "stations_tried": [s[1] for s in near]}
