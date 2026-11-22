# Telegraph S2: WFV evaluator adapter v4 (many renderings) — frozen spec

> **Published 2026-11-22** from the builder's working notes, where this spec was frozen (the freeze commit is in that
> private notes repo). Content is unchanged except for folder names and neutral wording. Not published, like all
> our evaluation material: the pair-building scripts and `data/` (part of the pool is a hidden test set). Lines
> that mention those files are kept for the record.

Frozen 2026-11-13 UTC, before any v4 pair or fresh test row was generated; the freeze time is this file's commit.
Authorized by the builder ("do attempt 4") after v3 stopped ([v3 RESULT](../wfv-adapter-v3/RESULT.md)).

## What v3 taught

- Minimal pairs work **inside the wordings trained on**: a wrong tolerance scored 100%, a wrong place 91%.
- They fail **in other wordings**: on the pool format, a wrong tolerance scored 42% and a wrong place 52%; in a table
  format, a flipped verdict scored 45%.
- So v4 changes one thing: the **variety of renderings**. Six trained renderings replace two. Verdicts are written in
  many forms (a sentence, PASS/FAIL, yes/no bullets, HIT/MISS, a table field). Every kind, including wrong day and
  wrong place, is trained.

## Held-out sets (none trained on)

| Set | What it is | Bar |
|---|---|---|
| **pool-fresh** | **The material-v1 generator re-run on new dates**, 2026-10-21 to 2026-11-08, with a new seed. Same question and answer format as our 301 pool rows, but new cases | **≥ 0.80** |
| **test-render** | Two renderings never trained on: R7, a JSON object, and R8, an email; all kinds | ≥ 0.75 |
| Kind floor | any single kind in either set above, with at least 20 pairs | ≥ 0.60 |
| material-v1 (old) | Already used once as v3's test, so **report only, not a gate** | — |

- **Kit data gate and kit test:** PASS.
- **Why pool-fresh is fair:** it comes from a separate generator (material-v1's), not from the v4 training
  generator. Its dates are disjoint from training (2025-10-01 to 2026-06-30).
- **Integrity check:** no v4 training prompt may be ≥ 0.85 similar (difflib ratio) to any pool-fresh or material-v1
  prompt, and no training `chosen` answer ≥ 0.85 similar to a pool-fresh `chosen` answer. Either one fails the
  construction checks.

## Data

- **Same sources and splits as v3:** the cached v2 downloads; train on 20 sites, val on 4 held-out sites, dates
  2025-10-01 to 2026-06-30.
- **Same kinds as v3, K1 to K8, all trained.**
- **Renderings:** trained R1 (station memo), R2 (guidance prose), R3 (archive table), R4 (check card with PASS/FAIL),
  R5 (bullets with yes/no), R6 (terse one line with HIT/MISS); held out R7 and R8.
- **Same construction rules as v3:** minimal pairs, verdicts balanced to 50% ± 2%, no zero-error answers, length
  neutral, claims clear of the tolerance edge.
- **Sizes:** train about 2,400, val about 300, test-render about 320 (20 per kind per rendering), pool-fresh up to
  300.

## Training (fixed in advance)

- The same kit, environment and settings as v3: `--epochs 4 --grad-accum 4 --lr 1e-4 --lora-rank 8 --lora-alpha 32
  --max-length 512`, CPU, with `--val-data val.jsonl --test-data test-render.jsonl`.
- **One run.** No retuning after seeing any test result. A crash may be rerun with the same configuration.

## After a pass

The same blocking checks as v3: weights present, a bit-exact executor, exact bytes. Then ask the builder about hosting
and the bond, which the builder signs.

## Integrity and disclosure

- The same rules as v3.
- If registered, the entry discloses that **this is a fourth attempt** and that the scorer ranks our own miner.

## Outcomes

- **Pass:** the blocking checks, then the builder's decision.
- **Fail:** report it. No v5 without the builder asking.
