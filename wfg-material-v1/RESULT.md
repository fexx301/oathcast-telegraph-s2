# WEATHER_FORECAST_GENERAL material v1: RESULT (2026-11-22)

**Verdict: all blocking checks pass. Ready for the user to upload in Anjoman.** The spec (kept private with the pairs, like our
other material) was frozen at `07e89b3` before any pair existed.

| Check (spec) | Result | Bar |
|---|---|---|
| Kit `--check-data` | **PASS**: surface probe 54.5%, length shortcut 58.0%, held-out leak 0%, unique negatives 100% | pass |
| "Pick the longer" (our judge) | **0.420** | 0.40–0.60 |
| Near-duplicates at ≥ 0.96 | 0 | 0 |
| Kinds balanced | 21–22 each | ±3 |
| Spot check, 20 random pairs vs cached source responses | 20/20 consistent (issue time, place, source) | 20/20 |
| Answer-order check | not applicable (JSONL names the better and worse answer; there's no order) | — |

**150 pairs** over 50 places in six regions. Forecast values come from MET Norway (44 non-US places) and the US
National Weather Service (6 US places), fetched once at build time into `raw/`. **No Open-Meteo value appears.**

**Per kind ("pick the longer"; prompt-overlap, descriptive):** K1 0.36; K2 0.36; K3 0.31; K4 0.84; K5 0.43; K6 0.24;
K7 0.39. Prompt overlap is legitimately high for K1 (wrong place), K2 (wrong dates) and K7 (wrong window), because
the error is a mismatch with the question. Where the two answers tie, the judge picks the first; that inflates the
other kinds' figures.

**Build history** (rebuilt from the same cached forecasts each time; no refetch):
1. **K4's worse answer only dropped a field** where the source has no humidity (NWS), making it shorter. It now
   swaps in an unrequested field the source has; better answers add one 30% of the time.
2. **"Pick the longer" was 0.390** (K6's impossible values have more digits). Each answer now gets its own writing
   style.
3. **That briefly raised the surface probe to 62.7%,** because the two styles landed unevenly across sides by chance.
   Styles are now balanced by construction across the sides; the probe is back to 54.5%.

The kit gate never failed, so the stop rule didn't apply.

**Outcome:** uploaded in Anjoman on 22 Nov (150 stored; 135 admitted, 15 held by the pool's share cap). Ours was the
third eligible contributor, so the pool became **evaluable**: snapshot published 2026-11-22 13:15 UTC, 272 rows from 4
contributors. The pairs and their generator stay private (they're evaluation questions).
