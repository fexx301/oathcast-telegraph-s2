# WEATHER_FORECAST_VERIFY evaluator adapter v5

A LoRA adapter (rank 8) with a reward head on Telegraph's shared Foundation Model (`modernbert-base-lora16-v1`), for
the judgment Intent family `WEATHER_FORECAST_VERIFY`. It scores forecast-verification answers. It prefers an answer
whose verdict, error, tolerance, units, place, day and window agree with the question and with each other.

**Disclosures:**
- I'm competing in Telegraph Hackathon Season II, which has prizes.
- This is my **fifth** adapter attempt. The first four failed rules I froze in advance, and their results are in this
  repo and below.
- I also run a weather-verify miner (64174). If this adapter is accepted, it would help rank that miner.

## Package

| | |
|---|---|
| File | `WEATHER_FORECAST_VERIFY.safetensors`, 6,776,916 bytes |
| keccak256 | `0xb02c020f979340a13222d07216d81c13c0d5b05ee74d64e66107a54aa7b554d4` |
| sha256 | `e352244d5bcf82f8df98cfca9f45d12f7793d1ccb2f6ef7f0c1ed55c20876ead` |
| Foundation | `0a49b325…` |
| Tokenizer | `67bc76f8…` |
| Class | judgment |

## Results (held-out sets, frozen bars set before training)

| Set | Bar | Result |
|---|---|---|
| 300 new rows in our pool-contribution format (same generator, new dates), never trained on | ≥ 0.80, every error family ≥ 0.60 | **0.893**; lowest families 19/26 |
| Two answer formats never trained on (JSON, email) | ≥ 0.75 | **0.960** |

Earlier attempts on comparable pool-format sets: v3 0.693, v4 0.705, v5 0.893. v5 changed the training data:
- verdict flips that only the numbers reveal;
- zero errors;
- mixed °F/°C;
- station plus grid values;
- three-day windows and fill values;
- cross-format pairs.

It also selected its checkpoint by development accuracy. Per-family counts are in `RESULT-v5-heldout.json`.

**Limits:**
- All pool-format test sets come from the generator behind our own contribution, so performance on other
  contributors' rows is not measured here.
- A text-only scorer cannot tell a consistent, plausible fabricated observation from a real one.

Training pairs and generators are withheld, so the evaluation pool's questions aren't exposed.

## Node result (2026-11-13): rejected in the hidden round

- **Registered** as reg 396. It passed the remote 15-pair check and the bit-exact confirmation.
- **Hidden round:** win rate **63.3%** (19/30), below the 70% floor, so it lost. No module is canonical for the
  Intent.
- **What it shows:** 89% on our own contribution's format became 63% on the hidden pool, which is mostly other
  contributors' rows. The adapter learned our format's checks better than it transferred to theirs.
- **This was the final attempt;** the registration is being withdrawn.
