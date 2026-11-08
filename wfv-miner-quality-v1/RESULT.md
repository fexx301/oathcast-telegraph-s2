# WFV miner quality test v1: RESULT, **PASS** (rule frozen in RULE.md, commit `2b29e25`, before the run)

The miner is OathCast v20 source (`c051cdb`, the same `src/` as production), run locally against live Open-Meteo with `{location, date}` only. The reference is the nearest NOAA GHCN-Daily station (our station Lambda), read live. Run 2026-11-07.

## Daily high (`temp_max_c`)

| | Covered | MAE | Median | ≤1 °C | ≤2 °C | ≤3 °C | Mean bias (miner − station) |
|---|---|---|---|---|---|---|---|
| **All** | **92/100** | **1.35 °C** | 1.3 | 42.4% | **81.5%** | 93.5% | −0.75 °C |
| US/CA | 50/50 | 1.24 | 1.3 | 40% | 86% | 96% | −1.04 |
| Europe | 25/30 | 1.38 | 1.2 | 48% | 84% | 92% | −0.40 |
| Asia-Pacific/other | 17/20 | 1.64 | 1.4 | 41% | 64.7% | 88% | −0.41 |

**Bar:** at least 60 covered (92), at least 75% within ±2 °C (81.5%), MAE at most 2.0 °C (1.35). **PASS.**

## Secondary measures
- Daily-low (`temp_min_c`) MAE: 1.34 °C.
- Wet/dry agreement at ≥1 mm: 67/84 (80%). By region: US/CA 40/46, Europe 19/24, other 8/14.

## Refusals
- The miner refused **0 of 100**.
- The station source had no reading for 8 (5 in Europe, 3 elsewhere), so those weren't scored.

## Worst 5 cases

| Case | Error (miner − station) | Station | Distance |
|---|---|---|---|
| Lisbon 2026-09-24 | +4.8 | Lisboa Geofísica | 0.9 km |
| Minneapolis 2026-10-26 | −4.3 | Lower St Anthony Falls | 1.3 km |
| London 2026-09-24 | −4.1 | Heathrow | 22.6 km |
| Mexico City 2026-10-05 | −3.8 | Mexico City | 6.6 km |
| Sydney 2026-09-14 | +3.7 | Sydney Harbour (Wedding Cake W.) | 5.9 km |

## Reading
- The miner gives a grid-cell estimate, not a station reading.
- It runs slightly cool against city stations (−0.75 °C on average), which fits urban heat at point stations.
- The weakest group is Asia-Pacific and other: 65% within 2 °C, with coastal and mountain sites.
- This is our own reference, not the network's scorer. It's evidence of measured accuracy, not of rank.
- Per-case rows: `results.jsonl`. Summary: `RESULT.json`.
