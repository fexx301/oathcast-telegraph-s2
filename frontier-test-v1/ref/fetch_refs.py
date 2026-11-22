"""Frontier test v1: references fetched directly from the official services (never from our miners). Run after the freeze."""
import json, subprocess, urllib.parse
from datetime import datetime, timezone
GSQ = "https://spatial-gis.information.qld.gov.au/arcgis/rest/services/GeoscientificInformation/MiningResources/MapServer/16/query"
TEN = "https://spatial-gis.information.qld.gov.au/arcgis/rest/services/Economy/CurrentQldResourceAuthorities/MapServer/{}/query"
def get(url, **q):
    u = url + "?" + urllib.parse.urlencode({**q, "f": "json"})
    r = subprocess.run(["curl", "-s", "-m", "60", u], capture_output=True, text=True)
    return u, json.loads(r.stdout)
out = {"fetched_at": datetime.now(timezone.utc).isoformat(), "sites": {}}
for site in (38722, 494270, 40172):
    u, g = get(GSQ, where=f"site_no={site}", outFields="*")
    a = g["features"][0]["attributes"]
    lat, lon = a.get("latitude"), a.get("longitude")
    rec = {"gsq_url": u, "gsq": {k: a[k] for k in a if a[k] not in (None, "")}, "tenure": {}}
    for layer, name in ((120, "mining lease"), (40, "exploration permit for mineral")):
        tu, t = get(TEN.format(layer), geometry=f"{lon},{lat}", geometryType="esriGeometryPoint", inSR=4326,
                    spatialRel="esriSpatialRelIntersects", outFields="*", returnGeometry="false")
        rec["tenure"][name] = {"url": tu, "rows": [f["attributes"] for f in t.get("features", [])]}
    out["sites"][site] = rec
json.dump(out, open("refs-qld.json", "w"), indent=1)
for s, r in out["sites"].items():
    g = r["gsq"]
    print(s, g.get("occur_name"), "|", {k: g[k] for k in g if any(x in k.lower() for x in ("size", "status", "commod"))})
    for n, t in r["tenure"].items():
        for a in t["rows"]:
            print("   ", n, "|", {k: a[k] for k in a if k.lower() in ("displayname", "authorisedholdername", "permitstatus", "approvedate", "expirydate", "permitstate")})
