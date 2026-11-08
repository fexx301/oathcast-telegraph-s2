# Draft issue for telegraphprotocol/telegraph-wasm-baseline (NOT POSTED; needs the user's OK)

**Title:** Adapter kit: three gaps that block packaging a judgment adapter (unpinned torch export, silent weightless bake, stale compiled-in catalog)

Found 2026-10-29 while packaging a `WEATHER_FORECAST_VERIFY` adapter on macOS arm64. The kit was at `9b01a44` (main `5fa5d68` plus `cmd/adapterrunner`). Versions:

- Python 3.12 venv from `requirements.txt`: torch 2.15.0, transformers 5.22.0, peft 0.21.2, onnx 1.23.2
- rustc 1.95.0, Go 1.26.4, wasmtime 50.0.0

### 1. `export_onnx` fails on current torch: `onnxscript` isn't in requirements

`requirements.txt` doesn't pin torch. torch ≥ 2.9's `torch.onnx.export` imports `onnxscript`, so step 3 fails with `ModuleNotFoundError: No module named 'onnxscript'`.

### 2. With `onnxscript` installed, the default exporter produces a model the bake silently drops the weights from

- On current torch, `torch.onnx.export` defaults to the dynamo exporter. That exporter wrote the graph (`model.onnx`, 156 KB) and the weights separately (`model.onnx.data`, 598 MB).
- `vm_float_wasm/build.rs` / `src/baked.rs` `include_bytes!` only `TELEGRAPH_ONNX_PATH`. So `bake_wasm.sh` "succeeds" with a **2.3 MB** `baked.wasm` that has no weights in it. No error or warning is raised.
- Merging the weights into one file also fails: `onnx.checker` rejects `Split` with `num_outputs` at the declared opset 17.
- **Workaround that worked:** pass `dynamo=False` (the legacy TorchScript exporter). That gives one 599 MB ONNX that passes the checker, bakes to a 601 MB WASI command, and packages.
- **Suggested fixes:**
  - pass `dynamo=False` in `export_onnx.py`, or pin `torch<2.9`;
  - make `build.rs` refuse an ONNX that references external data, or that is implausibly small for ModernBERT-base.

### 3. `adapterbuild` refuses most live judgment intents offline

- `pkg/scoring/catalog/catalog.go` compiles in 31 judgment/hybrid intents. The live node resolves many more prefixes as judgment. For example, `GET /api/wasm?resolve=WEATHER_FORECAST_VERIFY_GENERAL` → `{"class":"judgment"}`.
- `adapterbuild --intent WEATHER_FORECAST_VERIFY --class judgment` fails with: `WEATHER_FORECAST_VERIFY is not a judgment or hybrid intent in the compiled-in catalog — refusing to guess a class`. An explicit `--class` can't override it.
- About 90 open bounty issues ask for an evaluator adapter, so this likely affects most of them.
- **Suggested fixes:** refresh the compiled-in list from the node, let `--class` stand when the catalog doesn't list an intent, or read the class from `/api/wasm?resolve=`.

We can share exact commands and logs on request.
