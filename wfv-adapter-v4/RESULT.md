# WFV evaluator adapter v4 (six renderings): RESULT

Run 2026-11-13: training 06:50–07:41 UTC, with the held-out sets scored once immediately after.
Spec: [README.md](README.md), frozen at `394c587`. Data and scorer: `5c961f5`.

## Verdict: STOP under the frozen go rule

No hosting, no bond, no registration. No v5 unless the builder asks.

| Set (frozen bar) | Result | Pass? |
|---|---|---|
| **pool-fresh**, 278 new rows from the material-v1 generator (≥ 0.80; every family ≥ 0.60) | **0.705** (196/278); five families below 0.60 | **no** |
| test-render, unseen JSON and email renderings (≥ 0.75; every kind ≥ 0.60) | **0.916**; lowest kind K1 at 25/40 | yes |
| material-v1 (old, report only) | 0.663 | — |
| Kit data gate and kit test | data gate PASS; kit test 0.916 | yes |

- **Early stopping kept epoch 0.** Val loss was 0.1985 at epoch 0, then rose to 0.2251 and 0.2802, so the kit stopped
  after epoch 2.
- **Kit exit code 1:** the same post-save `NameError: pkg` as v3. The adapter and `result.json` were already
  written.

## pool-fresh by family (v3's material-v1 score in brackets)

| Family | Correct |
|---|---|
| **F1 verdict flip** | **9/21** (v3: 16/24) |
| F2 wrong day | 44/45 (35/44) |
| F3 wrong place | 40/45 (23/44) |
| F4 unit slip | 13/18 (18/24) |
| F5 wrong variable | 17/19 (19/23) |
| **F6 fill value** | **11/22** (21/25) |
| F7 claim misread | 21/21 (21/24) |
| **F8 arithmetic** | **11/21** (14/24) |
| **F9 tolerance misapplied** | **10/21** (10/24) |
| **F10 window (3 days)** | **20/45** (31/44) |

## What it means (corrected 2026-11-13 after an independent review; each point checked against the files)

- **Numerical checks are weak even in our own unseen formats.** On JSON/email, verdict flip scored 25/40 and arithmetic
  29/40 (67.5% together), against 239/240 on every other kind. So the 91.6% headline hides a numerical-reasoning gap
  that exists before any pool wording is involved.
- **The pool's verdict flip is a numerical test; ours was partly verbal.**
  - The material-v1 generator flips both the verdict and the "within/outside" word (`inout` follows `ok`), so the
    wrong answer is verbally coherent and only the numbers reveal it.
  - Half of our K1 training negatives flipped only the verdict, which a verbal contradiction can solve.
- **Our generator excluded something the pool has.** v3/v4 never show a zero error, which was a guard against the
  v2 exact-match tell. But 50 of 278 pool-fresh `chosen` answers (18%) show an error of 0.0, including 5 of the 21
  F1 pairs.
- **Pool answers are structurally richer.** They carry a station and a grid value, °F observations with °C errors,
  and window wording. Training mostly had one observation in one unit system.
- **Not the cause:** truncation (the longest input is about 211 tokens against a 512-token limit) or checkpoint
  choice (val accuracy only moved 271 → 275/300 after epoch 0).
- **Withdrawn:**
  - "v4 improved on v3." The two figures come from different test sets. On the same material-v1 set, v4 fell from
    0.693 to 0.663.
  - "Untrained kinds stay at chance." v3's unseen day/place kinds scored 92%. Window and fill-value failures
    justify adding coverage; they don't show that transfer is impossible.
- **Still stands, narrowed:** text alone cannot tell a plausible fabricated observation from a real one. That
  doesn't explain failures on arithmetic stated in the answer.
- pool-fresh has now been scored once as a test set.
