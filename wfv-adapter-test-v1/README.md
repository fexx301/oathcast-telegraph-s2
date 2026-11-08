# Telegraph S2: WFV evaluator adapter decisive test v1

Frozen 2026-10-29 ~22:20 UTC, before any weather values were fetched. Authorized by the user ("yes go for the evaluators prize, run the test"). The cap runs **3 h from 22:01 UTC, ending Oct 30 01:01 UTC**. No spend, no upload, no claim, no posting.

**Question:** can we deliver a `WEATHER_FORECAST_VERIFY` evaluator adapter that:
- (D) runs as a node-shaped package on our hardware; and
- (Q) prefers correct WFV answers over wrong ones, including on **kinds of wrong answer it never trained on**?

**Consequence:**
- Both legs pass: build the adapter and the material as the T2 entry.
- Either leg fails: T2 is material only, with no adapter.

Event context: event note, Oct 29 section and "Next action (revised 2026-10-29)".

## Kit (pinned)

- The kit is `telegraphprotocol/telegraph-wasm-baseline` at `9b01a44`: main `5fa5d68` plus `cmd/adapterrunner`, which is only on that branch.
- Base model: public `answerdotai/ModernBERT-base`. No unpublished weights or evaluation cases are requested or used, per the kit's README rule.
- Training runs locally on an M4 Pro (24 GB), using MPS.

## Data (built after this freeze; values fetched live)

**Observations:**
- **Station:** NOAA NCEI GHCN-Daily (`daily-summaries`, keyless, metric), US first-order airport stations: TMAX, TMIN, PRCP for the local-standard calendar day.
- **Grid:** the Open-Meteo archive, default best match, with `timezone=Etc/GMT+N` at the station's standard offset (the same LST day), queried at the station's coordinates.
- None of the 16 v1/v2 study sites are used, and none of v2's reserved dates (2026-01-20, 04-23, 08-19).

**Sites, split:**
- Train: BOS, ATL, DEN, PHX, MSP, SLC, BNA, PDX, LAS, DFW, ORD, JAX.
- Test: BUF, BIS, ANC, HNL.

**Dates, split:** train days come from 2026-01-01 to 06-30; test days from 2026-07-01 to 09-30. So test sites and test dates are both unseen.

**Claims:**
- Hypothetical forecasts, generated with fixed seed 20261029: half within tolerance, half outside.
- Tolerance is 2 °C for temperature, and max(1 mm, 25% of the claim) for precipitation.
- About 40% of prompts state the claim in °F or inches, across all families.

**A case is kept only if** station and grid give the **same verdict, clear of the edge**:
- error ≤ 0.6 × tolerance for "verified";
- error ≥ 1.6 × tolerance for "not verified".

`chosen` cites the station record.

**Prompts:** six app-shaped templates, all inside the Intent (a forecast claim plus a past window): vendor check, hedge trigger, parametric cover, site check, spray-window rain, and the plain question.

**Answers:**
- **`chosen`** gives the station value with its ID, the grid estimate, the error, the tolerance, the verdict, and that the forecast's issue time isn't attested. Three phrasings, rotated.
- **`rejected`** is the same answer with one corruption.

**Provenance:** the source is the station-data URL. `source_kind` is `synthetic` (template text over real data), so rows would be `unverified` in the pool.

## Corruption families (split fixed here)

| Family | Corruption | Split |
|---|---|---|
| F1 verdict flip | Numbers right; verdict and within/outside reversed | train |
| F2 wrong day | Answer reports a different date than asked | train |
| F3 wrong place | Answer names a different city and station | train |
| F5 wrong variable | Answer reports a different variable (low for high, rain for temperature) | train |
| F4 unit slip | Claim in °F read as °C (or inches as mm); verdict computed from the slip | **test only** |
| F6 fill value | A missing-data fill (-999.9 / -9999) reported as the observation, with a verdict | **test only** |
| F7 claim misread | The claim restated wrongly (digits swapped, or ×10); verdict computed from it | **test only** |

**Sizes:**
- About 150 train pairs (F1/F2/F3/F5, balanced) from train sites and dates.
- 60 test pairs (20 each of F4/F6/F7) from test sites and dates.
- Verified and not-verified `chosen` are balanced in both sets.

## Legs and acceptance

**Q (quality):**
- The kit's `--check-data` must pass on the train file.
- Train with the kit's defaults (`train_adapter`, ModernBERT LoRA). Validation is the kit's internal 15% hold-out of train.
- The final gate is `--test-data` = the 60 held-out-family pairs.
- **Pass:** test preference accuracy ≥ 75% **and** at least 10 points above the "pick the longer answer" baseline on the same pairs.
- Per-family accuracy is reported. It decides nothing.

**D (delivery), using the adapter trained in Q.** Every step must succeed:
- `export_onnx` → `bake_wasm.sh` → `adapterbuild`, for the judgment class.
- Under `wasmtime`, the package prints exactly one `HEX : 0x…` line.
- Three repeat runs on the same input are bit-identical.
- `adapterrunner`'s `/runnable` returns the same bits as the direct run.
- The packaged WASM orders at least 9 of 10 test pairs the same way the PyTorch model does.

**Recorded, not gating:**
- per-score latency at about 512 tokens, and peak memory;
- package size;
- the node's 2-minute batch deadline as a hosting risk.

**Outcomes:**
- Both pass: adapter plus material.
- Q fails: material only.
- D fails: material only. The adapter waits on the delivery fix, outside this cap.
- Cap reached with a leg incomplete: that leg is **unproven at cutoff**, so material only. No extension.

## Limits (disclose in any entry)

- A judgment-class reward model sees only the question and the answer, never the observation. It can learn consistency, faithfulness (place, day, variable, units), plausibility and honest sourcing. **It cannot detect a fabricated observation that is stated consistently.** This holds for any WFV adapter under the current scoring class.
- Claims are hypothetical, and the text is assistant-written from templates. One station network (US ASOS) and one reanalysis; the station day window is taken as the LST calendar day (not re-proved here).
- Our OathCast miner serves WFV from Open-Meteo. This relationship must be disclosed. `chosen` cites the station so that an Open-Meteo-only answer isn't favoured by construction.
- Passing locally doesn't mean the network accepts the adapter. The node needs material from at least 5 contributors and scores on its hidden pool, where an adapter needs at least 70%.
