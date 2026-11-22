# WFV evaluator adapter v7: RESULT (2026-11-18)

One training run (spec `1034c41`; data frozen in `37ef749` with MANIFEST hashes, which the evaluator re-verified).
Dev macro accuracy by epoch: 0.901, 0.949, 0.975, 0.977; epoch 3 kept. The final suite was scored once for v6 and v7.

## Verdict: GO under the frozen rule (every gate passed)

| Gate (frozen) | v6 | v7 | Pass |
|---|---|---|---|
| **Primary: A+B gain ≥ 5 points, one-sided paired McNemar p ≤ 0.05** | 0.844 | **0.929** (+8.5 points; b = 58, c = 17, p < 0.0001) | yes |
| A1 arithmetic ≥ 0.80 and ≥ v6 + 10 points | 0.72 | **0.86** | yes |
| A2 verdict ≥ 0.80 | 0.83 | 0.89 | yes |
| A3 tolerance and units ≥ 0.80 | 0.99 | 1.00 | yes |
| A flattering half ≥ 0.75 | 0.82 | 0.84 | yes |
| B overall ≥ 0.80 and ≥ v6 − 3 points | 0.839 | **0.950** | yes |
| B each stratum ≥ 0.70 (B1, B2, B3) | 0.98, 0.95, 0.58 | 0.95, 0.95, 0.95 | yes |
| C overall ≥ 0.75 and ≥ v6 − 5 points | 0.900 | 0.925 | yes |

**Historical sets** (reported, not gated):

| Set | v6 | v7 |
|---|---|---|
| pool-fresh-3 | 0.870 | 0.893 |
| test-mos-real | 0.871 | 0.875 |
| test-render | 0.948 | 0.948 |
| material-v1 | 0.853 | 0.880 |

## Read with care
- **Much of the gain is B3** (missing or invalid records, where the better answer abstains): 0.58 → 0.95.
  - B3 carries a disclosed length tell: abstentions are longer than their wrong answers 85% of the time.
  - v7 was trained on abstention pairs of the same shape, so part of that gain may be length, not judgement.
  - **Sensitivity:**
    - Excluding B3, A+B1+B2 goes from 0.881 to 0.926, **+4.5 points**, below the 5-point bar.
    - On A alone: +7.0 points.
    - The predeclared gate includes B3, so the verdict stands; this is reported, not used to change it.
- **The improvement the spec targeted is real:** arithmetic, 0.72 → 0.86.
- **Site-grouped check:** 8 of 16 final sites show a net gain, 3 a net loss, 5 even. One site (EVV, mostly B3
  missing-day cases) accounts for 22 of the 58 discordant wins.
- **C is mostly plausibility:** in 118 of 120 cases the correct reading is the one closer to the forecast. The one
  corrupted-closer case is wrong for both models.
- **None of this predicts the node.** The hidden pool and the incumbent (445) can't be run locally.

## Next (spec)
1. **Delivery checks:**
   - export with the pinned tokenizer;
   - the kit's package check;
   - weights present;
   - a bit-exact executor across Mac arm64 and Linux x86;
   - publish the exact bytes.
2. **Before registering:** verify the Intent, incumbent, margin rule and foundation identifiers on the node.
3. **Register once on Nov 27–28; the builder signs.** Retry only for an operational failure.

## Delivery checks (2026-11-18, local)

| Check | Result |
|---|---|
| Pinned tokenizer | Export uses the node's `67bc76f8…c456`; on all 24,684 v7 texts it gives the same token ids as the run's tokenizer |
| Export | `runs/WEATHER_FORECAST_VERIFY.safetensors`, 6,776,916 bytes, rank 8, 178 tensors (delta only, no base weights) |
| Package check (`adapterbuild lora`, the node's Stage 1 parser) | **PASS**: class judgment, foundation `0a49b325…` (modernbert-base-lora16-v1), loaded and scored twice with identical bits (`0x40acddfc`) |
| **Hash to register** | **keccak256 `0x42c012e2a4ca7dbe99c9cb1450e60cf210ba99c790b5359c0d8671fdb13262fa`**, sha256 `99ddaf24…20ca` |
| Weights present | 178 tensors and 6.76 MB of deltas in the manifest |
| Mac arm64 executor (`adapterexec`) | 30 inputs (15 final pairs, the kit's own text rendering) scored twice, **bit-identical** |
| WASM vs PyTorch | Pair order agrees **15/15**; largest score difference 0.00019 |
| Linux x86 executor | **Pending:** on the registration host, replay `exec-check-request.json` and require 30/30 bits equal to `exec-mac-reply.json` |
| Bytes published | **Pending:** at registration, to a commit-pinned URL, with the keccak re-checked after download |

**Notes:**
- **Kit findings:**
  - The compiled-in catalog still lacks WFV, so a local-only entry was added for the check and then reverted
    (PR #5 addresses this).
  - `export_adapter` prints the SHA-256 of an in-memory serialisation (`9089fe79…`) that differs from the file it
    writes. The file's hash (`99ddaf24…`) is the one checked and to be registered.
- **Training:** finished with the known `NameError: pkg` after saving; the adapter was already written.
