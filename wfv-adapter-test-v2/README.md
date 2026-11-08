# Telegraph S2: WFV evaluator adapter decisive test v2

Frozen 2026-10-30 UTC, before any v2 weather values were fetched; the exact freeze time is the commit timestamp. Authorized by the user ("start on 1 and 3", choosing option 1: a second frozen adapter test). The cap is **3 h, from 06:47 to 09:47 UTC**. No spend, no upload, no claim, no posting.

**v1 is history** ([result](../wfv-adapter-run-v1/RESULT.md)): 65% on held-out families with 130 pairs and 24 steps. Its 212 cases are excluded here.

**Question:** with about 1,000 pairs and more training steps, does a WFV adapter prefer correct answers on **corruption families it never trained on**, and does its package run?

**Consequence:**
- Pass: the adapter plus material is the proposed T2 entry, put to the user.
- Fail: T2 shape goes back to the user (material only, or drop). There is no v3 by default.

## Kit and workarounds (fixed in advance)

- Kit `9b01a44`, the same venv as v1 (torch 2.15.0, `onnxscript` added).
- **Declared workarounds for the reported kit gaps:**
  - export with the legacy exporter (`dynamo=False`);
  - a one-line local catalog entry for `WEATHER_FORECAST_VERIFY`.
- No other kit changes. Training runs on the CPU (the kit has no MPS path).

## Data

**Sources:** the same as v1. NCEI GHCN-Daily (US first-order airport stations, metric, LST calendar day) and the Open-Meteo archive at station coordinates with `timezone=Etc/GMT+N`.

**Sites:** none from v1 or the truth-source studies.
- **Train (24):** LAX, IAH, MSY, STL, CLE, DTW, PIT, PHL, DCA, CLT, RDU, TPA, MEM, OKC, ELP, TUS, BOI, RNO, SAC, GEG, FAR, LIT, SAT, IND.
- **Test (6):** FAI, OGG, MSO, CRP, CAR, YUM.
- A site is **dropped, not replaced**, if its station returns no rows, **or if the NCEI `NAME` doesn't contain the expected city or airport token** (a guard against a mistyped ID naming another place, which would look like an F3 wrong-place corruption). The test needs at least 5 test sites, or it stops as invalid.

**Dates:** train 2025-10-01 to 2026-06-30; test 2026-07-01 to 2026-09-30. The study-v2 reserved dates (2026-01-20, 04-23, 08-19) are excluded.

**Cases:**
- Same claim, tolerance and edge rules as v1. Station and grid must agree on the verdict and be clear of the edge (≤ 0.6× or ≥ 1.6× the tolerance).
- Seed 20261030.
- About 40% of claims in °F or inches.
- One pair per site-day.
- Verified and not-verified `chosen` balanced in each split.

**Text:**
- 12 prompt templates and 5 answer phrasings, all inside the Intent (a forecast claim plus a past window).
- Every answer states its window explicitly ("one local standard day"), so a window corruption doesn't change the length.
- Provenance: `synthetic`, with the station-data URL.

## Families

**Train: v1's seven, with v1's definitions.**

| Family | Corruption |
|---|---|
| F1 | verdict flip |
| F2 | wrong day |
| F3 | wrong place |
| F4 | unit slip |
| F5 | wrong variable |
| F6 | fill value |
| F7 | claim misread |

**Test only (new kinds, never trained on):**

| Family | Corruption |
|---|---|
| F8 arithmetic | The stated error is wrong (off by 3–8 units from the true difference). The verdict follows the stated error, so it contradicts the numbers. |
| F9 tolerance misapplied | A wrong tolerance is stated (for example ±0.5 °C or ±10 °C, ±0.2 mm or ±25 mm), chosen so the verdict flips. Skipped if no flip is possible. |
| F10 window mismatch | The answer covers the three local days ending on the asked date (precipitation total, or the mean of daily highs/lows), says so, and judges the claim on that. |

**Sizes:**
- Train: 7 × 120 = 840 pairs, of which the kit holds out 15% for validation.
- Test: 3 × 40 = 120 pairs.

**Construction checks** (data only, before any model output; failing ones are fixed in the generator):
- the kit's `--check-data` passes on train;
- in every family of both splits, pick-longer is right on 30–70% of pairs;
- the test set's length baseline **as the kit computes it** (`--check-data` run on the test file, a data-only check) is ≤ 65%. The test file's surface probe isn't required to pass: F10's window wording trips it by design, and no model trains on F10;
- **verdict balance** (v1's shortcut: 25/30 accuracy when `chosen` said "verified", 14/30 when it didn't). Among pairs whose `chosen` and `rejected` give different verdicts, the "verified"-saying answer must be the correct pick on 45–55% of train and 40–60% of each family.
  - The generator enforces this from the data alone: for F2/F3, it picks the alternate day or place whose recomputed verdict keeps the balance; half of F6's fill-value answers say "verified".
  - A "pick the verified-saying answer" baseline on the test set is reported beside the length baseline.

## Training (fixed in advance)

- `train_adapter --epochs 4 --grad-accum 4`, every other setting at the kit default (lr 1e-4, batch 1, max length 512, the kit's early stopping).
- About 180 optimizer steps per epoch.
- The final gate is `--test-data` = the 120 test pairs.

## Acceptance

**Q (quality) passes only if all of these hold:**
1. test accuracy is at least 75%;
2. the kit gate's verdict is `PASS` (at least 65%, and at least 10 points above the kit's length baseline);
3. **no held-out family is below 60%.** v1 had one family at 25%.

**D (delivery), with the declared workarounds, on the trained adapter.** Every check must hold:
- export, bake and package succeed;
- every run prints exactly one `HEX` line;
- three repeats are bit-identical;
- the runner returns the same bits as a direct run;
- the WASM orders at least 9 of 10 test pairs the same way PyTorch does.

Latency, memory and size are recorded, not gating.

**Outcomes:**
- Both legs pass: propose adapter plus material to the user.
- Any leg fails, or the cap is reached first: **unproven at cutoff.** The T2 shape goes back to the user. No retuning, no reruns on these test cases, no extension.

## Limits

These are v1's, unchanged:
- A judgment adapter sees only the question and the answer, never the observation. It can't catch a fabricated observation that is stated consistently.
- Claims are hypothetical, and the text comes from templates (`unverified` rows).
- One station network and one reanalysis.
- Our OathCast miner reads Open-Meteo, which must be disclosed. `chosen` cites the station.
- A local pass isn't network acceptance: that needs 5 contributors, a 70% score on the hidden pool, and hosting that meets the 2-minute check.
