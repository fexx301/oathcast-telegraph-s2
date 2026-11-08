# WFV miner quality test v1: frozen rule (written and committed before any run)

**Question:** how close are OathCast's `temp_max_c` answers (miner 64174, release v20) to what NOAA stations recorded, on city-days fixed in advance?

## Sides
- **Miner:** OathCast `ForecastService.verify_forecast` from source commit `c051cdb`, the same `src/` as production v20 (source SHA-256 `c56883e0…`). It runs locally against live Open-Meteo, with the request `{location, date}` only, exactly as the Intent sends it.
- **Reference:** our station truth source (`telegraph-wfv-station` Lambda): the nearest GHCN-Daily station within 50 km with a TMAX that day, read live from NOAA NCEI. It's independent of Open-Meteo.
- **Known gap, stated up front:** the miner gives a grid-cell model estimate (9–25 km); the station is a point. Some disagreement is expected from geography alone (coasts, elevation, urban heat). The test measures that gap; it doesn't hide it.

## Cases (fixed now; no substitutions after the run)
100 city-days in three groups, with dates chosen where the reference has coverage (README coverage table):
- **US/CA:** 25 cities × {2026-10-12, 2026-10-26} = 50.
- **Europe:** 15 cities × {2026-09-08, 2026-09-24} = 30. ECA&D data stops 2026-09-30.
- **Asia-Pacific/Americas other:** 10 cities × {2026-09-14, 2026-10-05} = 20.

The city lists are in `run.py` `CASES`, committed with this file.

## Metrics
- **Coverage:** the share of the 100 where both sides answered. A refusal on either side is reported, not scored.
- **On covered cases:** the absolute error |miner − station| for `temp_max_c`. Report the MAE, the median, the share ≤1 °C, ≤2 °C and ≤3 °C, and the worst 5 with station distance. Break all of it down by group.
- **Secondary:** wet/dry agreement at ≥1 mm `precipitation_mm`, and the MAE for `temp_min_c`.
- **Miner refusals:** listed with their codes.

## Bar (frozen)
- **PASS** if, on covered cases, **≥75% are within ±2 °C** and **the MAE ≤ 2.0 °C**, with **coverage ≥ 60/100**.
- Otherwise **FAIL**, reported as measured.
- Either way, the numbers go into the H2 Miners draft §3.1 as they are. No re-runs with changed cases, dates or bars.
