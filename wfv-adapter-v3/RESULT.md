# WFV evaluator adapter v3 (minimal pairs): RESULT

Run 2026-11-13. Training took 03:32–04:17 UTC, all 4 epochs. The held-out sets were scored once, at 04:18 UTC.
Spec: [README.md](README.md), frozen at `fada15b`. Data: `85f576e`.

## Verdict: STOP under the frozen go rule

No hosting, no bond, no registration. The spec's outcome is that material-only stands, with no v4 unless the builder asks.

| Set (frozen bar) | Result | Pass? |
|---|---|---|
| material-v1, 300 pool-format rows (≥ 0.80) | **0.693** (208/300) | **no** |
| test-style, unseen R3 rendering (≥ 0.75; every kind ≥ 0.60) | 0.833 overall, but **K1 verdict flip 18/40 (45%)** | **no** (kind floor) |
| test-kind, unseen kinds K7 and K8 (≥ 0.75) | **0.919** (K7 74/80, K8 73/80) | yes |
| Kit data gate and kit test | data gate PASS; kit test 0.833 on test-style, against a length baseline of 0.525 | yes |

Validation accuracy (trained renderings and kinds, held-out sites) rose by epoch: 0.883 → 0.929 → 0.958 → 0.954.
The best val loss was at epoch 3. Files: `RESULT-v3-heldout.json`, `RESULT-v3-train.json`, `runs/v3-train.log`.

## material-v1 (pool format) by family

| Family | Correct |
|---|---|
| F1 verdict flip | 16/24 |
| F2 wrong day | 35/44 |
| **F3 wrong place** | **23/44** |
| F4 unit slip | 18/24 |
| F5 wrong variable | 19/23 |
| F6 fill value | 21/25 |
| F7 claim misread | 21/24 |
| **F8 arithmetic** | **14/24** |
| **F9 tolerance misapplied** | **10/24** |
| F10 window | 31/44 |

## What it means

- **Better than before, but short of the bar.** On the pool format, v3 scores 69.3%, against v2's 52.5% (21/40) in
  the blind-spot control. The node needs 70% on its hidden 30-pair round, after at least 11/15 on a public check.
  At a true rate of about 0.69, the chance of clearing both is roughly 0.25–0.3. Our bar was 0.80 so that
  registering would be worth it.
- **It learns the checks in our own format, not in the pool's.** It catches a wrong place (K8 91%) and a wrong
  tolerance (K3 100%) in our renderings. On the pool's phrasing it does not: F3 52%, F9 42%.
- **The unseen table format breaks one kind.** A flipped verdict scores 45% when it reads "result: NOT VERIFIED"
  instead of a prose sentence. The verdict check is tied to the wording.
- **The limit found in v1/v2 still holds, narrower.** Minimal pairs moved the adapter from learning error kinds to
  checking consistency, but only in the surface forms it trained on.
- material-v1 has now been scored as a test set. Any later attempt needs a fresh pool-format held-out set, not
  this one.

## Kit note

`train_adapter.py` crashes after saving, while printing the next-step hints (line 838, `NameError: name 'pkg'`).
The adapter and `result.json` were already written, so the result isn't affected. It's worth adding to the upstream
report alongside PR #5.
