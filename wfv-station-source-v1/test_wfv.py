"""Offline self-test: resolver, qualifiers, date checks and station fallback with a canned NCEI answer."""
import sys
sys.path.insert(0, "app")
import _wfv as W  # noqa: E402

assert W.resolve("Paris")["country"] == "FR"
assert W.resolve("Paris, Texas")["admin1"] == "Texas"
assert W.resolve("Paris, TX")["admin1"] == "Texas"
assert W.resolve("Austin, TX, USA")["country"] == "US"
assert W.resolve("São Paulo")["country"] == "BR" and W.resolve("Sao Paulo")["country"] == "BR"
assert W.resolve("Paris, Japan") is None  # a known country that matches nothing empties the candidates
assert W.resolve("Denver, downtown")["admin1"] == "Colorado"  # an unknown qualifier is ignored
assert W.verify("New York", "2999-01-01")[0] == 400 and W.verify("", "2026-10-25")[0] == 400
assert W.verify("New York", "25/10/2026")[0] == 400
assert W.verify("Atlantis Undersea", "2026-10-25")[0] == 404
st = {s[0]: s for s in W.load()["stations"]}  # ECA&D longitude signs resolved against the gazetteer
assert st["UKE00107650"][2] < 0 and st["SPE00120584"][2] < 0  # Heathrow, Valencia airport: west of 0
assert st["UKE00105657"][2] > 0 and st["SPE00120242"][2] > 0  # Goudhurst, Lleida: east of 0
assert W.nearest(*[W.resolve("London")[k] for k in ("lat", "lon")], 2026)  # London has 2026 stations again

near = W.nearest(*[W.resolve("New York")[k] for k in ("lat", "lon")], 2026)
first, second = near[0][1], near[1][1]
# Nearest station has no TMAX that day -> the next station with one is used.
fake = lambda st, day: ("u", [{"STATION": first, "TMIN": "5.0"}, {"STATION": second, "TMAX": "18.3", "TMIN": "9.4", "PRCP": "1.2"}])
code, b = W.verify("New York", "2026-10-25", fetch=fake)
assert code == 200 and b["station"]["id"] == second and b["temp_max_c"] == 18.3 and b["precipitation_mm"] == 1.2, b
code, b = W.verify("New York", "2026-10-25", fetch=lambda st, day: ("u", []))
assert code == 404, b
print("ok")
