# Telegraph S2: WFV evaluator adapter v3 (minimal pairs) — frozen spec

> **Published 2026-11-22** from the builder's working notes, where this spec was frozen (the freeze commit is in that
> private notes repo). Content is unchanged except for folder names and neutral wording. Not published, like all
> our evaluation material: the pair-building scripts and `data/` (part of the pool is a hidden test set). Lines
> that mention those files are kept for the record.

Frozen 2026-11-13 UTC, before any v3 pair was generated or any model trained; the freeze time is this file's commit.
Authorized by the builder ("lets do it", contesting the WEATHER_FORECAST_VERIFY scorer). Go/no-go: end of 2026-11-14 UTC.

## Why a v3, and what changed

- v1 (65%) and v2 (60.8% on unseen error kinds, 94% on trained kinds; F9 tolerance-misapplied 30%) failed their frozen
  bars. v2 also did not transfer to the pool's prompt format (21/40 on material-v1 rows in the blind-spot control).
- v3 changes the data, not the model:
  1. **Minimal pairs.** `chosen` and `rejected` share the whole text except one decisive fact.
  2. **The tolerance is read from the question.** Questions state varied tolerances (°C, °F, mm, in, percent), so
     no fixed convention can be memorised. This targets v2's F9 failure.
  3. **Several renderings.** One is held out entirely, to measure transfer to formats never trained on.
- The idea of balanced minimal pairs is credited to AdversarialEval's public progress post (Telegraph Discord,
  2026-11-13). No code or data of theirs is used.

## Node facts this is built against (docs read 2026-11-13)

- **No WFV module is canonical.** The best candidate reaching **70% on a 30-pair hidden round** becomes canonical.
- **Before that:** a remote check of 15 public pairs, needing at least 11/15 correct.
- **zkasuran's reg 386** is the same file (`655ec4bc…`) as regs 374, 378 and 383, which scored 5/15, 8/15 and 8/15.
- **The pool** (730 rows, 5 contributors) is all forecast-check questions. 301 rows are ours (material-v1); the
  others' rows are not public.

## Data

- **Source:** NCEI GHCN-Daily station records and the Open-Meteo archive at station coordinates. These are the cached
  v2 downloads (`../wfv-adapter-run-v2/raw/`); nothing new is fetched for training.
- **Claims:** synthetic, drawn relative to the record. Each is clear of the tolerance edge (≤ 0.6× or ≥ 1.6×), and
  never exactly equal to the observation.
- **Train and val:** the 24 v2 train sites, dates 2025-10-01 to 2026-06-30. This is disjoint from material-v1's dates
  (2026-08-01 to 2026-10-20). Val uses 4 of those sites, held out from train.
- **Test sets:**
  - the 6 v2 test sites (dropped if they have no rows), dates 2026-07-01 to 2026-09-30;
  - material-v1, our 300 unique pool-format rows from a separate generator. These are **never trained on** and are
    measured once, after training.
- **Verdict balance:** each split has `chosen` saying "verified" in 50% ± 2% of pairs.
- **Length neutrality:** a corruption changes digits or words of similar length.
- **No zero-error tell:** a `rejected` answer never states an error of 0.0. A `chosen` answer's error is never 0.0
  either, because the claim never equals the observation.

**Renderings (prompt plus answer style):**

| Rendering | Style |
|---|---|
| R1 | Station memo: names the station, then claim, error, tolerance and verdict |
| R2 | Guidance check: "the GFS-style guidance called for …", answered in °F-first prose |
| R3 | Archive table: a compact key-value answer against a reanalysis value. **Test only, never trained on** |

**Kinds** (the one decisive fact that differs in `rejected`):

| Kind | Corruption | Split |
|---|---|---|
| K1 | Verdict contradicts the stated error and tolerance | train + test |
| K2 | Stated error is wrong, and the verdict follows it | train + test |
| K3 | Tolerance misapplied: states a tolerance other than the question's, consistently | train + test |
| K4 | Claim restated wrongly (digit or decimal slip), and error and verdict follow it | train + test |
| K5 | Unit slip: a °F or inch claim treated as °C or mm | train + test |
| K6 | Wrong variable: uses the low for a high claim, or the reverse | train + test |
| K7 | Wrong day: the answer's date differs from the question's | **test only** |
| K8 | Wrong place: the answer's station or city differs from the question's | **test only** |

**Sizes (targets):** train about 1,600, val about 240, test-style (R3, kinds K1–K6) about 240, test-kind (K7 and K8,
renderings R1 and R2) about 160, material-v1 300.

## Training (fixed in advance)

- Kit `telegraph-wasm-baseline` @`1ed063e2` with the declared workarounds from v2/sanctions: a local catalog entry and
  the legacy exporter.
- Settings: `--epochs 4 --grad-accum 4 --lr 1e-4 --lora-rank 8 --lora-alpha 32 --max-length 512`, CPU, using
  `--val-data val.jsonl --test-data test-style.jsonl`.
- **One run.** No retuning after any test result is seen. A crash may be rerun with the same configuration.

## Frozen go rule (all must hold; stop on any miss)

| Set | Bar |
|---|---|
| material-v1, 300 pool-format rows | **≥ 0.80** |
| test-style (R3, unseen rendering) | ≥ 0.75 |
| test-kind (K7 and K8, unseen kinds) | ≥ 0.75 |
| Any single kind, in any test set, with at least 20 pairs | ≥ 0.60 |
| Kit dataset gate and kit test | PASS |

**Why 0.80 on the pool format:** the node needs at least 11/15 and then at least 21/30. At a true 80% the chance of
passing both is about 0.8; at 75% it is about 0.55; at 70% about 0.3.

## After a pass: checks before any bond (each one blocks)

1. **Weights present.** The exported `.safetensors` has non-zero LoRA weights (the bug behind PR #5).
2. **Bit-exact executor.** The kit's `cmd/adapterexec` reproduces the kit's own scores bit for bit on 30 texts, on
   the host that will serve it.
3. **Exact bytes.** The registered file is the exported file: keccak re-checked after re-downloading from its host.
4. **User approvals:** hosting (the executor must be up only while pending), and the 0.67 MACHINA bond, which the
   user signs.

## Integrity

- Never train on our uploaded pool rows, or on anything ≥ 0.85 similar (difflib ratio on prompts) to a material-v1
  prompt. This is checked and reported.
- Other contributors' material is not used for training or tuning.
- The node's remote-check pairs are not logged for training.
- No deliberate re-rolling of the 15-pair check. At most one retry after a near miss (10/15), disclosed.
- **Disclosure if registered:** this scorer would rank our own miner 64174, and the entry says so.

## Outcomes

- **Pass:** run the checks above, then ask the builder about hosting and the bond.
- **Fail:** report it. Material-only stands. No v4 without the builder asking.
