# WFV evaluator adapter decisive test v2: RESULT

Run 2026-10-30, 06:47–07:30 UTC, inside the 3 h cap. Spec: [frozen README](../wfv-adapter-test-v2/README.md), commit `9d17126` at 06:45:41Z. The first v2 fetch was at 06:48:24Z (`raw/fetch-log.jsonl`). No spend, no upload, no claim, no posting.

## Verdict: Q FAILS → the T2 shape goes back to the user (frozen outcome; no retuning, no v3 by default)

| Q criterion (all three required) | Result |
|---|---|
| Held-out-family accuracy ≥ 75% | **60.8%** (73/120) |
| Kit gate `PASS` | **FAIL**: 0.608 is below the kit's minimum of 0.65. The length baseline was 0.504, which it did beat by more than 10 points. |
| No held-out family below 60% | **F9 tolerance misapplied: 30%** (12/40) |

**D (delivery) was not run.** The outcome was already set by Q, and v1 showed that the delivery path works with the declared workarounds ([v1 RESULT](../wfv-adapter-run-v1/RESULT.md)).

## Training

Settings as frozen: 4 epochs, `grad_accum` 4, kit defaults otherwise, CPU.
- 714 train pairs and 126 validation pairs; about 712 steps; about 31 min; peak about 0.98 GB.
- Validation accuracy on the **trained** families rose 84.9% → 89.7% → 94.4% → 94.4%, so the model learned the seven trained kinds well.
- See `train-result.json` and `train.log`.

## Held-out families (report only, `test-per-family.json`)

| Family | All | Correct pick says "verified" (V) | Correct pick says "not verified" (N) |
|---|---|---|---|
| F8 arithmetic (stated error wrong) | 31/40 (77.5%) | 11/18 | 15/17 (plus 5/5 same-verdict pairs) |
| F9 tolerance misapplied | **12/40 (30.0%)** | 3/20 | 9/20 |
| F10 window mismatch (3 days) | 30/40 (75.0%) | 17/20 | 13/20 |

**Baselines on the test set:**
- the kit's length baseline: 50.4%;
- "pick the verified-saying answer": 50.4%;
- the construction checks all passed (`construction.json`).

**Reading (inferred):**
- The model generalises to errors it can check against numbers inside the answer: a stated error that contradicts the difference (F8), or a window that contradicts the question (F10).
- It doesn't reject an answer whose wrong tolerance is **internally consistent**: the stated error, the stated tolerance and the verdict all agree. It prefers such answers 70% of the time.
- Knowing the tolerance rule (±2 °C; max(1 mm, 25%)) means learning a convention that no trained family varied.
- This adds to the class limit already recorded: a judgment adapter sees only the question and the answer.

## Generator fixes made after the freeze (data only, before any model output)

The frozen construction checks failed, so the generator was fixed until they passed, as the spec allows:

1. **The builder stalled** (verdict-balance deadlock). Not-verified claims for F2/F3/F4/F5/F7/F10 are now set to the value the corrupted answer compares against, so that answer says "verified".
2. **F6:** the fill-value answer states the opposite verdict to `chosen`, so exactly half say "verified".
3. **F10's verified half** keeps only cases where the 3-day figure misses the claim.
4. **F8's not-verified half** draws the stated error inside the tolerance, provided it is 3–8 units from the true error.
5. **A balance block** switches that family's next verdict.
6. **F4's slipped claim** shows its own wrong conversion, so it is as long as the correct one.
7. **Diagnostics:** skip-reason counts were added.

**Site drop (frozen rule):** YUM returned no rows. That left 5 test sites, the minimum.

## What it means

- **Two frozen adapter tests have now failed:**
  - v1: 65%, with 130 pairs;
  - v2: 61% on unseen error kinds, with 840 pairs, despite 94% on seen kinds.
- A ModernBERT reward model trained on our templates learns the trained corruption kinds, not WFV correctness in general.
- **No adapter in the T2 entry under this decision.**
- **The pairs themselves are the useful artifact:** verdict-balanced, length-neutral, station-checked, and covering 10 corruption kinds.
  - They separate an evaluator that checks consistency from one that pattern-matches: 94% seen vs 61% unseen, and 30% on F9.
  - That is the job of the pool's hidden testing half.
  - Whether this works as material-only T2 evidence, and whether the near-duplicate filter accepts the rows, are both **untested**.
- These 960 cases have been seen and can't be reused as held-out data.

## Correction (2026-10-30, after review): the engineered claims leave a tell, so these pairs aren't upload-ready

- **The verdict-balance fix creates a pattern.** Each engineered not-verified case (F2/F3/F4/F5/F7/F10) sets the claim to exactly the value the wrong answer uses. So that `rejected` answer shows an error of about 0.0 and says "verified", while a correct "verified" answer shows a small non-zero error. In this data an exact match marks the *wrong* answer, which would teach an adapter that a perfect forecast is worse. Counts are in the commit message.
- **Some engineered prompts are implausible:** a 30.0 °C December minimum in Charlotte, or inch figures equal to millimetre readings. #76 asks for questions people would really ask.
- **The F10 "generalises" reading above is confounded,** since F10's not-verified half carries the pattern. Withdrawn as a finding.
- **Also withdrawn:** "the pairs separate an evaluator that checks consistency from one that pattern-matches". The gap between seen and unseen kinds shows only that our held-out kinds are hard for an adapter trained on our other kinds. It says nothing about measuring real miners.
- **Fixes required before any upload:**
  - jitter the engineered claims so the wrong answer's error has the same small non-zero spread as correct answers;
  - drop the implausible F4/F7 claims;
  - run the near-duplicate probe.
- **This doesn't change the verdict.** Q failed on the frozen criteria; the pattern affects the interpretation and the material's fitness, not the pass/fail.
