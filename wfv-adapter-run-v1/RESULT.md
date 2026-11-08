# WFV evaluator adapter decisive test v1: RESULT

Run 2026-10-29, 22:01–22:35 UTC (34 min, well inside the 3 h cap). Spec: [frozen README](../wfv-adapter-test-v1/README.md) (`SHA256SUMS`, commit `af909bd`). No spend, no upload, no claim, no posting.

## Verdict: adapter half FAILS → T2 entry is evaluation material only (per the frozen outcome table)

| Leg | Frozen bar | Result |
|---|---|---|
| **Q quality** | ≥ 75% on held-out corruption families, and ≥ 10 points above "pick the longer" | **FAIL: 65.0% (39/60).** The kit's own gate also failed: it requires beating its length-only baseline (70.8%) by 10 points. |
| **D delivery (stock kit)** | `export_onnx` → bake → `adapterbuild` all succeed | **FAIL.** Three kit/toolchain blockers (below). |
| D delivery (with 3 diagnostic workarounds) | one HEX line, repeats bit-identical, runner = direct, ≥ 9/10 same order | All pass: 10/10 same order (diagnostic only; doesn't count as a pass) |

## Q details

**Data:**
- 152 train pairs over families F1 verdict flip, F2 wrong day, F3 wrong place and F5 wrong variable, from 12 sites, Jan–Jun 2026.
- 60 test pairs over families F4 unit slip, F6 fill value and F7 claim misread, from 4 other sites, Jul–Sep 2026.
- Real NCEI GHCN-Daily and Open-Meteo values (32 keyless GETs, logged in `raw/fetch-log.jsonl`). Station and grid verdicts agree, clear of the tolerance edge.

**The kit's data gate passed:** 100% unique negatives, length shortcut 60.9%, surface probe 56.4%, no leakage.

**Training:** kit defaults, CPU (the kit only uses CUDA or the CPU): 3 epochs, 24 optimizer steps, about 5 min, peak about 1.4 GB.
- Validation (15% of train, the same families) reached only 63.6% accuracy, with loss 0.676 (chance is 0.693). The model barely learned even the families it trained on.
- See `train-result.json` and `train.log`.

**Per family (report only, `test-per-family.json`):**

| Family | Accuracy |
|---|---|
| F4 unit slip | 19/20 |
| F7 claim misread | 15/20 |
| F6 fill value | **5/20** (below chance) |
| chosen = verified | 25/30 |
| chosen = not verified | 14/30 |

**Length baselines on the test set:**
- pick-longer: 28.3%
- pick-shorter: 70.0% (F7: 85%)
- the kit's length baseline: 70.8%

**Reading:** with 130 training pairs and the default 24 steps, the model learned a weak signal plus a lean toward "verified" answers. Whether more data or steps would pass is **untested**; the frozen rule allows no retuning in this test.

## D details: kit blockers found (stock kit `9b01a44`, torch 2.15.0)

1. **`requirements.txt` lacks `onnxscript`**, so `export_onnx` raises `ModuleNotFoundError` on current torch.
2. **With `onnxscript` installed, torch's default dynamo exporter writes the weights as external data.** The bake embeds only the 156 KB graph and "succeeds" with a 2.3 MB weightless `baked.wasm`, with no error. The merged single file also fails `onnx.checker` (`Split num_outputs` at opset 17). Workaround: `dynamo=False`.
3. **`adapterbuild`'s compiled-in catalog lists only 31 intents and refuses `WEATHER_FORECAST_VERIFY`** ("not a judgment or hybrid intent … refusing to guess"). `--class judgment` can't override it, although the live node resolves WFV as judgment. Workaround: a one-line local catalog patch, labelled in the spike.

A draft upstream report is in [UPSTREAM-ISSUE-DRAFT.md](UPSTREAM-ISSUE-DRAFT.md). **It isn't posted;** posting needs the user's OK.

**Diagnostic package (with workarounds):**
- `WEATHER_FORECAST_VERIFY.wasm`, 601,257,641 B
- sha256 `d0660d12…c8c3b`, keccak256 `0x57118b85…21de8a`
- The bake peaked at 3.6 GB RAM.

**Runtime (`delivery.json`):**
- every run printed exactly one HEX line;
- three repeats were bit-identical;
- `adapterrunner` returned the same bits as a direct run;
- WASM and PyTorch ordered 10/10 sampled pairs the same way, with values matching to about 1e-5.

**Hosting risk (recorded, not gating):**
- About 6.4 s per score for a ~130-token input, and 17.3 s at 512 tokens.
- About 4.1 GB peak RSS per execution (wasmtime, concurrency 1, M4 Pro).
- The node's registration check sends batches of up to 100 inputs with a 2-minute total deadline. Meeting that at 512 tokens would need about 15 parallel executions, roughly 60 GB of RAM. This plausibly explains the many `remote executor check failed` rejections in the Oct 29 registry snapshot (inferred).

## What this means

- **T2 = evaluation material (preference pairs) for `WEATHER_FORECAST_VERIFY_GENERAL`.** It can be built with this pipeline's verified station/grid method; it still needs a wider prompt variety and the near-duplicate check.
- No adapter in this entry.
- The kit findings are a reusable give-back: the Evaluators rubric credits integration clarity, and the bounty board lists "fix integrations".
- **An adapter could be reconsidered** only with a new frozen test, more data or steps, and a hosting plan that meets the 2-minute check. That would be a new decision, not an extension of this one.
- **Limits:**
  - Template text means the rows are `unverified` (`synthetic`).
  - Claims are hypothetical.
  - Single network: US ASOS stations plus one reanalysis.
  - A judgment adapter can't detect a fabricated observation that is stated consistently.

## Corrections (2026-10-29, after the run)

- **The freeze time was misstated.** The frozen README says "Frozen ~22:20 UTC". The freeze commit `af909bd` is timestamped 2026-10-29T22:15:16Z, and the first data fetch was at 22:17:20Z (`raw/fetch-log.jsonl`). The spec was frozen about 2 minutes before any value was fetched. The README stays unedited, because SHA256SUMS covers it.
- **The outcome table's "material only" is a recommendation pending the user's choice.** The user approved going for the Evaluators prize with the adapter; they haven't agreed to a material-only entry.
- **These 212 pairs have now been seen.** A v2 test may reuse the pipeline, but not these cases as its held-out set.
- **The material route has an unproven dependency.** The pool rejects prompts that are 85% or more similar to an existing one, and the docs don't define the metric. Prompts from 6 templates may collide. Only an upload can show it.
