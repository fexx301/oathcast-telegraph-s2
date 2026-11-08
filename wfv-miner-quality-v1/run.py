"""WFV miner quality test v1 (rule: RULE.md). Miner = OathCast v20 source run locally; reference = station Lambda.

Usage: PYTHONPATH=<oathcast>/src <oathcast>/.venv/bin/python run.py
Writes results.jsonl (one row per case) and RESULT.json (summary).
"""
import json, statistics, sys, time, urllib.error, urllib.parse, urllib.request
from pathlib import Path

from oathcast import service as S
from oathcast.verify import VerifyError

HERE = Path(__file__).resolve().parent
STATION = "https://wdauaeyvk7mcfzuxewk3mqkhvu0klqwo.lambda-url.eu-north-1.on.aws/verify"

US_CA = ["New York", "Chicago, Illinois", "Los Angeles", "Houston", "Phoenix", "Philadelphia", "San Antonio",
         "San Diego", "Dallas", "Denver", "Seattle", "Boston", "Atlanta", "Miami", "Minneapolis", "Detroit",
         "Las Vegas", "Portland, Oregon", "Salt Lake City", "Kansas City, Missouri", "Nashville", "Toronto",
         "Montreal", "Vancouver", "Calgary"]
EUROPE = ["London", "Paris", "Berlin", "Madrid", "Lisbon", "Rome", "Vienna", "Amsterdam", "Stockholm", "Oslo",
          "Dublin", "Prague", "Warsaw", "Zurich", "Edinburgh"]
OTHER = ["Tokyo", "Osaka", "Sydney", "Melbourne", "Perth", "Brisbane", "Mexico City", "Monterrey", "Auckland",
         "Honolulu"]
CASES = ([(c, d, "us_ca") for c in US_CA for d in ("2026-10-12", "2026-10-26")]
         + [(c, d, "europe") for c in EUROPE for d in ("2026-09-08", "2026-09-24")]
         + [(c, d, "other") for c in OTHER for d in ("2026-09-14", "2026-10-05")])
assert len(CASES) == 100


def station(loc, date):
    url = f"{STATION}?{urllib.parse.urlencode({'location': loc, 'date': date})}"
    for attempt in range(3):
        try:
            with urllib.request.urlopen(url, timeout=60) as r:
                return json.loads(r.read())
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return {"_refused": 404, "_body": e.read()[:200].decode(errors="replace")}
            err = f"http {e.code}"
        except Exception as e:  # noqa: BLE001 - network blips get two retries, then are reported
            err = type(e).__name__
        time.sleep(3 * (attempt + 1))
    return {"_refused": err}


def main():
    svc = S.ForecastService(provider_order=["open_meteo"], verify_enabled=True, require_auth=False)
    rows = []
    for loc, date, group in CASES:
        try:
            m = svc.verify_forecast({"location": loc, "date": date}, request_id="quality-v1").public_response
        except VerifyError as e:
            m = {"_refused": e.code}
        except Exception as e:  # noqa: BLE001
            m = {"_refused": type(e).__name__}
        s = station(loc, date)
        row = {"location": loc, "date": date, "group": group, "miner": m, "station": s}
        if "_refused" not in m and "_refused" not in s and s.get("temp_max_c") is not None:
            row["err_max"] = round(m["temp_max_c"] - s["temp_max_c"], 2)
            if s.get("temp_min_c") is not None:
                row["err_min"] = round(m["temp_min_c"] - s["temp_min_c"], 2)
            if s.get("precipitation_mm") is not None:
                row["wet_agree"] = (m["precipitation_mm"] >= 1) == (s["precipitation_mm"] >= 1)
        rows.append(row)
        print(loc, date, row.get("err_max", "—"), flush=True)
        time.sleep(0.5)
    (HERE / "results.jsonl").write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows))

    def summary(rs):
        cov = [r for r in rs if "err_max" in r]
        e = [abs(r["err_max"]) for r in cov]
        if not e:
            return {"n": len(rs), "covered": 0}
        mins = [abs(r["err_min"]) for r in cov if "err_min" in r]
        wet = [r["wet_agree"] for r in cov if "wet_agree" in r]
        return {"n": len(rs), "covered": len(cov), "mae": round(statistics.mean(e), 2),
                "median": round(statistics.median(e), 2),
                "within_1": round(sum(x <= 1 for x in e) / len(e), 3),
                "within_2": round(sum(x <= 2 for x in e) / len(e), 3),
                "within_3": round(sum(x <= 3 for x in e) / len(e), 3),
                "bias_mean": round(statistics.mean(r["err_max"] for r in cov), 2),
                "mae_min": round(statistics.mean(mins), 2) if mins else None,
                "wet_dry_agree": f"{sum(wet)}/{len(wet)}"}

    overall = summary(rows)
    result = {
        "rule": "RULE.md (frozen before the run)",
        "overall": overall,
        "by_group": {g: summary([r for r in rows if r["group"] == g]) for g in ("us_ca", "europe", "other")},
        "miner_refusals": [(r["location"], r["date"], r["miner"]["_refused"]) for r in rows if "_refused" in r["miner"]],
        "station_refusals": sum("_refused" in r["station"] for r in rows),
        "worst5": sorted(({"location": r["location"], "date": r["date"], "err_max": r["err_max"],
                           "station": r["station"].get("station", {}) if isinstance(r["station"].get("station"), dict)
                           else {k: r["station"].get(k) for k in ("station_id", "station_name", "distance_km")}}
                          for r in rows if "err_max" in r), key=lambda x: -abs(x["err_max"]))[:5],
    }
    result["pass"] = (overall.get("covered", 0) >= 60 and overall.get("within_2", 0) >= 0.75
                      and overall.get("mae", 99) <= 2.0)
    (HERE / "RESULT.json").write_text(json.dumps(result, indent=1, ensure_ascii=False) + "\n")
    print(json.dumps(result, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    sys.exit(main())
