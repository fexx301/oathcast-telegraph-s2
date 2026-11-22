# Telegraph S2: WFV evaluator adapter v7 — frozen spec

> **Published 2026-11-22** from the builder's working notes, where this spec was frozen (the freeze commit is in that
> private notes repo). Content is unchanged except for folder names and neutral wording. Not published, like all
> our evaluation material: the pair-building scripts and `data/` (part of the pool is a hidden test set). Lines
> that mention those files are kept for the record.

Frozen 2026-11-17 UTC, before any v7 data, test case or training run exists; the freeze is this file's commit.
Authorised by the builder (2026-11-17). Design source: an independent pre-spec review (kept local),
checked against the files (the unit tell was confirmed in 28/40 of v6's M-relabel test pairs).

**Disclosure:** this is the seventh WFV adapter attempt. v6 (reg 408) was the first canonical module, then was
superseded by Counterproof's reg 445 (70.00% vs 66.67% on the same 30 pairs). The entry reports every attempt,
including v6's breach of the stop agreed after v5.

## What v7 claims to improve, and what it doesn't
- **Claim tested here:** v7 checks numerical, source and window consistency more robustly than v6 on new cases and
  unfamiliar answer forms, without losing report-only performance.
- **Not claimed:** that v7 beats 445 or any incumbent. That is decided only on the node, on a sample we can't see.
- Local results describe this suite only; they are not a forecast of the hidden pool.

## Training (one run)
- **Same foundation, kit and settings as v6:** `modernbert-base-lora16-v1`, LoRA rank 8, alpha 32, dropout 0.1, lr 1e-4,
  4 epochs max, grad-accum 4, max length 512, seed 20261118.
- **Corpus = v6's 4,200 pairs, transformed, plus a targeted supplement of at most 1,500 pairs:**
  1. **Label audit (all rows):** an independent checker parses the *displayed* forecast, observation, error and
     tolerance and recomputes the verdict with an explicit rounding tolerance (half a unit in the last displayed
     digit). Rows that fail are dropped, with a reason. They are never repaired by hand.
  2. **Unit-tell removal:** M-relabel pairs are rebuilt so that the rejected answer keeps the chosen answer's unit
     tokens and number of values, corrupting only the relation (for example "31.1 °C (88 °F)" against
     "31.1 °C (31 °F)"). Fahrenheit-only correct answers are included at an equal rate.
  3. **Supplement:**
     - coherent arithmetic and verdict pairs, where every dependent word flips with the fact;
     - counter-proximity pairs, where the correct answer's observation is farther from the forecast and explicit
       evidence decides;
     - new answer forms: concise lines, reordered fields, multiple observations, mixed units, omitted verdicts,
       justified "can't determine".
- **Splits** are made by underlying station and date case; every rendering of a case stays in one split.
- **Excluded:** uploaded pool rows, rows reconstructed from other contributors, any case or template in a final set,
  and near-duplicates (≥ 0.85) of all of these.
- **Recorded before training:** row counts, mix weights, corpus SHA-256, split manifest.

## Checkpoint selection
- **Dev set:** about 300 new cases across the A, B and C strata below, from distinct stations and dates.
- **Selection:** macro pairwise accuracy across those strata; ties go to the earliest epoch. The final sets are never
  used for selection.

## Final suite (600 distinct cases, built and hashed before training ends; scored once each for v6 and v7)
New stations and dates, none in any earlier set. Test-only template families. Labels come from the independent
displayed-value checker. A tie in a pair's two scores counts as wrong, as on the node.

| Set | Construction | Bar for v7 |
|---|---|---|
| **A: numerical consistency (300)** | 100 absolute-error checks; 100 verdict checks; 100 tolerance and unit-relation checks. Includes ≥ 60 counter-proximity cases | ≥ 80% in each 100-case stratum; arithmetic stratum ≥ v6 + 10 points; counter-proximity ≥ 75% |
| **B: task and format transfer (180)** | 60 source or variable selection; 60 time window; 60 missing or incomplete evidence (a justified abstention can be the better answer) | ≥ 80% overall; no stratum below 70%; overall no more than 3 points below v6 |
| **C: report-only (120)** | Real issued forecasts with station observations, 6 kinds × 20, new renderings, three proximity buckets (correct closer, corrupted closer, tie) reported | ≥ 75% overall and no more than 5 points below v6; per-kind results reported, not gated |

- **Primary gate:** on A+B (480 cases), v7 − v6 ≥ **5 points**, and a one-sided exact paired McNemar test at
  **p ≤ 0.05** on the discordant pairs. Publish b, c, both right and both wrong. Also report a site-grouped
  sensitivity check.
- **GO = the primary gate and every table bar pass,** plus the delivery checks: weights present, the pinned-tokenizer
  export, the kit package check, a bit-exact executor, and the exact bytes published.
- **If the suite can't be built at the fixed counts in time, stop.** Denominators are never shrunk after inspection.

## Shortcut screens (descriptive, reported per family and rendering; not gates)
Character and token length, verdict phrase, unit tokens, and number-only overlap with the prompt. Legitimate
question-matching (a misquoted forecast, date or station) is labelled as such, not as a leak.

## Historical sets (reported, never used for selection)
pool-fresh-3, pool-fresh-2, pool-fresh, material-v1, test-mos-real, test-mos and test-render, for v6 and v7.

## Registration (only after GO)
- **Before registering, verify on the node:** the Intent, the incumbent, the corpus, the margin rule, the foundation,
  tokenizer and engine identifiers, and package acceptance. A material change reopens this contract.
- **Window:** Nov 27–28. One registration of the GO bytes; the bond is about 0.6 MACHINA, and the builder signs.
- **Retry: operational only.** Allowed for a documented node, transport or infrastructure failure, or an incomplete
  evaluation, with the same bytes. **A completed loss is final:** no reroll, no revised weights, no third attempt.
- The executor host stays up until the registration leaves pending, and is then terminated.

## Outcome reporting
- **Format:** "v7 improved by X on the preregistered suite; it did or did not meet every gate; the node measured Y
  against incumbent Z on the same sample and did or did not promote it."
- Every attempt is published, failures included, along with v6's first-canonical record and its supersession.

## Out of scope
v8; seed, rank or mixture sweeps; ensembles (the kit packages one adapter); hidden-pool access; other contributors'
rows; uploading to the pool to reshape the contest; tuning to our own miner's wording.

## Budget and stops
- **About 2 days:** construction and audit about 1 day; training about 2.5 h; evaluation and packaging about half a
  day.
- **Order of cuts:** optional diagnostics and presentation go first. Fresh final cases, label checks and
  compatibility evidence are never cut.
- **Deadlines:** if training and evaluation aren't done by Nov 23, or the label audit fails, there is no
  registration, and the attempt is reported.

## Amendments before any case was generated (2026-11-17)
1. **Stations:** `stations.json`, frozen in `ec47c11` before any fetch. 41 never-used NOAA first-order stations were
   split by seed: final 16, dev 8, supplement 17. CMH (dev) and PVD (supplement) failed the NAME rule and were
   dropped, not replaced, leaving final 16, dev 7 and supplement 16. Days run 2026-08-01 to 2026-11-08.
2. **"Counter-proximity" in set A, defined:**
   - In A's three strata, both answers report the same observation, so plain forecast proximity can't separate them.
   - The trap instead is the *flattering* error: the wrong answer claims the forecast verified (an understated
     error, a flipped verdict, a looser tolerance) when it didn't.
   - Each stratum is balanced 50/50 between flattering and unflattering wrong answers. The counter-proximity bar
     (≥ 75%) applies to the flattering half: 150 cases, at least the 60 required.
3. **Set B strata, defined:**
   - **B1:** the wrong variable (the low for the high), or the grid estimate presented as the station reading.
   - **B2:** a three-day window, or another date.
   - **B3:** missing or invalid evidence (a fill value or a missing station day). The better answer says the record
     can't settle it; the worse one gives a verdict from the invalid value.
4. **Templates:** final renderings are written only for the final suite. Dev uses training-family renderings. No
   final template appears in training or dev.
5. **Selection under the kit (pre-training):** the kit keeps the epoch with the best *overall* pairwise accuracy on
   `--val-data`, the earliest on a tie. To make overall accuracy equal the spec's *macro* accuracy across strata,
   `data/dev-weighted.jsonl` replicates dev rows so every stratum carries 120 rows: A ×3, B ×4, C ×2, 840 in all.
   It changes selection weighting only; nothing is trained on it. Kit settings are as v6's log records them
   (es_patience 1, es_min_delta 0.001, es_metric pairwise_accuracy), with seed 20261118 as the spec declares.
   `--test-data` is v6's historical test-mos-real, never the final suite.
6. **Built before training** (`MANIFEST.json` hashes):
   - `train-v7` 5,246 pairs: v6's 3,998 kept rows, 198 rebuilt relabel pairs, and a 1,050-pair supplement. 2 audit
     drops and 2 unrebuildable relabel rows are excluded.
   - dev 270 cases.
   - final A 300, B 180, C 120.
   - **Shortcut screens on the final suite,** descriptive (`data/shortcut-screens-final.json`):
     - A1 and A2 sit at chance on length, TF-IDF and number overlap.
     - A3, B1 and B2 overlap is legitimate question-matching.
     - **Disclosed tells:** B3 abstentions are longer than their wrong answers (85%); B2's three-day wrong answers are
       longer (a shorter-wins judge scores 92%).
     - **C:** 118 of 120 have the correct reading closer to the forecast, so C largely measures plausibility. Reported
       as such.
   - **Final-vs-training prompt similarity:** maximum 0.751, under the 0.85 bar.

## Registration amendments after GO (2026-11-20; the bytes, the suite and the GO verdict are unchanged)
Two network changes since GO count as material under "Registration" above, so the registration plan is rewritten
here. Nothing about the model changes: no retraining, no new weights, the same keccak `0x42c012e2…62fa`.

7. **Contract.**
   - Register on the new Diamond `0x72a70e949362670bf8bcead24efc5b8f950aa08b` (Ethereum Sepolia), live since
     17 Nov 2026. Source: anjoman.ai/docs/protocol/addresses-and-params, "New Diamond, 17 November 2026".
   - The old Diamond `0x3624…b99b` is retired, and no node reads registrations sent there.
   - `registerWasm(keccak, url, prefix, feeAddress, runnableUrl)` keeps its signature. A dry run from `0xe9d1…`
     on 20 Nov got past the selector and stopped at "ERC20: insufficient allowance".
8. **Bond: 5 test USDC, not MACHINA.**
   - The new Diamond has no MACHINA token. `entityBonds()` returns the adapter bond, 5,000,000 USDC base units,
     as its third value; re-read it on the day. The 1.445 MACHINA freed from 408 doesn't apply here.
   - The owner `0xe9d1…` holds 2 test USDC and 0 allowance. Test USDC `0xcc19…7` can be minted by anyone.
   - Steps, all signed by the builder:
     1. mint 10 test USDC to `0xe9d1…`;
     2. `approve(newDiamond, 5000000)`;
     3. dry-run `registerWasm`;
     4. register.
9. **Pool gate (new).** The WFV adapter pool was replaced on 19 Nov 22:05 UTC.

   | | Before (snapshot `9960327e…`, Nov 18) | After (snapshot `6dea4964…`) |
   |---|---|---|
   | Eligible rows | 863 | 68 |
   | Submitters | 6 | 1 |
   | Qualification / ranking | | 31 / 37 |

   - The node reports `min_submitters: 3`; the docs say registrations wait for material from at least 5 contributors.
   - **Register only when `GET /api/evalpool/status?intent_id=WEATHER_FORECAST_VERIFY` shows `eligible_submitters`
     at or above `min_submitters`.** Until then a registration only waits: the bond stays locked and the executor
     host runs idle.
   - Check it once a day from Nov 21. If the gate isn't met by Nov 28 23:59 UTC, there is no registration, and the
     attempt is reported as blocked by the pool, not as lost.
10. **The contest sample comes from the new pool.** v7's GO was measured on our own preregistered suite, so its
    margin over v6 says nothing direct about 120 on the node's sample.
    - On the day, record the active snapshot's version, rows, submitters and qualification/ranking split next to
      the result.
    - No retraining, reweighting or tuning to the new pool; that stays out of scope.
    - **Not done by us:** uploading WFV adapter material to lift the submitter count. That falls under "uploading to
      the pool to reshape the contest" and is out of scope unless the builder decides otherwise.
11. **Unchanged:**
    - **Incumbent:** reg 120, active canonical at 76.67% on 30 pairs. Margin: 120's score on the same sample plus 2
      points, and at least 70%.
    - **Day-of checks:** foundation, tokenizer and engine hashes and package acceptance, re-verified on the day.
    - **Linux x86 executor:** 30/30 bits equal to `runs/exec-mac-reply.json`. Start the host only after the pool
      gate passes; terminate it once the registration leaves pending.
    - **Bytes:** published at a commit-pinned URL with the builder's push OK.
    - **Retry rule:** operational only; a completed loss is final.
