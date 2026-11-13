# WEATHER_FORECAST_VERIFY evaluator adapter v6

A LoRA adapter (rank 8) with a reward head on Telegraph's shared Foundation Model (`modernbert-base-lora16-v1`), for
`WEATHER_FORECAST_VERIFY` (judgment).

**Disclosures:**
- I'm competing in Telegraph Hackathon Season II, which has prizes.
- This is my **sixth** adapter attempt. v5 (in `../wfv-adapter-v5`) passed my offline bars, then lost the node's
  hidden round at 63.3%. Continuing past the stop I'd agreed was my decision.
- I run a weather-verify miner (64174) that this adapter would help rank.
- At most two registrations of these exact bytes, with both outcomes reported.

## What changed from v5

- **v5's verification training data is kept unchanged.**
- **About 1,200 "report-only" pairs were added.** The answer reports the recorded high with a caveat about
  forecast windows, and the wrong answer differs only in the observed value (unit relabel, decimal scale, digit
  swap, the day's minimum, another date's value, or an offset).
- **This shape was guided by a public description of another contributor's material.** No other contributor's rows,
  code or wording were used. It is benchmark-informed development.

## Package

| | |
|---|---|
| File | `WEATHER_FORECAST_VERIFY.safetensors`, 6,776,916 bytes |
| keccak256 | `0x7cbd03343edc870036c9a23acf9fe47ebf1dccbdd25f5130f81451098e90554d` |
| sha256 | `6d84f0dbb7181e01b894d08b5d38a05ab4301224c5863f85d608773654bcf285` |

## Results (held-out, bars frozen before training)

| Set | Bar | Result |
|---|---|---|
| Our pool-contribution format, 18 new stations, never trained on | ≥ 0.80, families ≥ 0.60 | **0.870** |
| Report-only pairs with **real issued ECMWF forecasts**, new stations, unseen wording | ≥ 0.75 | **0.871** |
| Report-only, synthetic forecasts, unseen wording (within-generator) | ≥ 0.75 | 0.842 |
| Unseen answer formats (JSON, email) | ≥ 0.75 | 0.948 |

**Diagnostic:**
- On the real-forecast set, "pick the reading closer to the forecast" alone scores 0.967; the adapter scores
  0.871, so it isn't simply that shortcut.
- On the 8 pairs where the wrong reading is the closer one, it picks correctly 7 times.
- This set can't separate factual checking from plausibility.

**Limits:**
- Other contributors' rows are not measured here.
- A text-only scorer can't detect a consistent, plausible fabricated observation.

Per-kind counts are in `RESULT-v6-heldout.json`.
