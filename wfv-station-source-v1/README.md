# WEATHER_FORECAST_VERIFY_GENERAL truth source v1 (bounty #76, hybrid since 2026-11-03)

A keyless API that we operate. It returns what the nearest NOAA weather station recorded, which is what the intent asks ("what did stations actually record"):

`GET https://wdauaeyvk7mcfzuxewk3mqkhvu0klqwo.lambda-url.eu-north-1.on.aws/verify?location=<place>&date=YYYY-MM-DD`

AWS Lambda `telegraph-wfv-station` (eu-north-1, reserved concurrency 5; `aws/deploy.sh`).

**How it answers:**
1. **Place:** resolves the place name with a bundled GeoNames `cities15000` gazetteer (CC BY 4.0). It takes the most populous match; `, country` or `, state` qualifiers narrow it, and unknown qualifiers are ignored.
2. **Stations:** picks up to 6 GHCN-Daily stations within 50 km that reported TMAX in that year (`ghcnd-stations` and `ghcnd-inventory`, filtered to stations reporting through 2025 or later: 12,559).
3. **Reading:** reads that day's TMAX, TMIN and PRCP live from NOAA NCEI `daily-summaries` (keyless, metric), and uses the nearest station that has a TMAX.
4. **Reply:** the scored `temp_max_c`, plus `temp_min_c`, `precipitation_mm`, the station's id, name and distance, and the NCEI URL. It returns 404 when there's no station or no reading, which the node drops from the median.

**Independent of our miner:** OathCast answers from Open-Meteo (model and reanalysis grids). This source uses only station observations, so it can disagree with grid answers, our own miner's included (Lisbon 2026-09-15: station 27.1 °C vs the NASA POWER grid's 22.9 °C).

**Data fix:** ECA&D-sourced station copies (ids with "E" as the third letter) lose the minus sign on longitudes between 0° and 1° west. For example, UKE00107650 HEATHROW is listed at +0.4489 but is really −0.461. Of the 49 stations with an ambiguous 0–1° longitude (Spain 28, UK 16, France 5), the builder keeps the sign that puts the station within 15 km of a same-named place in the full GeoNames gazetteer for its country (`GB`, `ES`, `FR`). That resolved 39 (14 west, such as Heathrow, Rothamsted, Wisley, Valencia, Caen; 25 east, such as Goudhurst, Cambridge, Lleida, Tours), all checked by hand against known locations. The other 10 are dropped. The first version (2026-11-03) dropped all 49, which left London with no 2026 station.

**Coverage, measured 2026-11-05 on 32 major cities:**

| Date | Readings |
|---|---|
| 2026-10-28 (one week back) | 14/32 |
| 2026-09-20 | 18/32 |

| Region | Coverage |
|---|---|
| US and Canada | Current to within days |
| ECA&D Europe (London, Paris, Berlin, Madrid, Lisbon, Valencia…) | Through 2026-09-30 (about 5 weeks behind) |
| Japan, Australia, Mexico | Lags weeks; varies by station |
| Beijing, Shanghai, Delhi, Mumbai, Moscow, Cairo, Lagos, Nairobi, Johannesburg, Dubai, São Paulo, Buenos Aires, Singapore | No station within 50 km with 2026 TMAX in GHCN-Daily; NOAA GSOD has no 2026 rows either |

A place or date without a reading returns 404, so the node drops this source for that question.

**Checks:**
- `test_wfv.py` runs offline: resolver, qualifiers, date validation, fallback to the next station, and the resolved ECA&D signs (Heathrow and Valencia west of 0°, Goudhurst and Lleida east).
- A live spot list: New York → Central Park 17.8 °C (2026-10-25); Paris, Texas → Paris; Austin, TX → Camp Mabry; Lisbon → Lisboa Geofísica.

**Limits:**
- The day boundary is GHCN's observation day.
- `condition` isn't provided.
- The station metadata is a snapshot from 2026-11-03; there's no automatic refresh (stations change slowly).
- The tie-break is by population, so "Springfield" means the largest Springfield.

**Files:**
- `build_index.py`, plus `app/_wfv.py` and `app/lambda_function.py`.
- `truth-source.yaml`; `items.jsonl` is the upload row (Anjoman → Evaluate, under `WEATHER_FORECAST_VERIFY_GENERAL`).
