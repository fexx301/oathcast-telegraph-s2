# MACRO_ECONOMIC_INDICATOR_GENERAL truth source v1 (bounty #94, deterministic since 2026-11-03)

The World Bank Indicators API, called directly. It's keyless, CC BY 4.0, and serves exactly the series the intent names:

`GET https://api.worldbank.org/v2/country/{ISO3}/indicator/SL.UEM.TOTL.ZS?date={year}&format=json` → `[meta, [{"value": 3.881, ...}]]`

**Mapping:** `intent_mapping` fills `country` as ISO3 and `date` from `year`, and sets `format` to the constant `json`. It reads the scored `rate_pct` from `1.0.value`. There's no `unit`, since World Bank already reports percent. A year with no data returns `null`, and the node drops that source from the median.

**Check:** 8 seeded cases from material v1 (`cases.tsv`), fetched in this request shape on 2026-11-03, match the recorded values exactly (`check.tsv`).

**Not ours:** we don't operate this API. Its terms and uptime are the World Bank's.

**Risk:** if another contributor already uploaded the same endpoint with the same parameters, this row comes back `duplicate_case`.

**Files:** `truth-source.yaml`; `items.jsonl` is the upload row.

**Upload** (the user's signed step): Anjoman → Evaluate, under `MACRO_ECONOMIC_INDICATOR_GENERAL`.
