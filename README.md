# OathCast: Telegraph Hackathon Season II work

Evaluation and serving work for [Telegraph](https://telegraphprotocol.com) Hackathon Season II, by the OathCast project.

**Disclosure:** this is a hackathon entry. I'm competing in Season II, which has prizes.

The miner itself lives in [fexx301/oathcast](https://github.com/fexx301/oathcast). This repo holds the evaluation side: a comparator module, truth sources, quality tests, and the experiments that didn't ship.

## What's here

| Folder | Intent | What it is | Result |
|---|---|---|---|
| [macro-comparator-v1](macro-comparator-v1/) | MACRO_ECONOMIC_INDICATOR | A 2.5 KB `no_std` Rust comparator WASM (zero imports), registered on-chain as reg 223, plus its hosted runnable endpoint | Matches the kit's reference code on 17,680 grid vectors, 20,000 battery-shaped cases and 776 i64-extreme probes; matches a canonical comparator on 19,735 in-domain cases |
| [macro-truth-source-v1](macro-truth-source-v1/) | MACRO_ECONOMIC_INDICATOR | A truth source: the World Bank WDI API, called directly | 8/8 sampled cases match |
| [sanctions-truth-source-v1](sanctions-truth-source-v1/) | SANCTIONS_SCREENING_MATCH | A keyless screening API over the official OFAC SDN and non-SDN, UN and EU lists plus 507 wallets, refreshed daily | Exact names and wallets 126/126; spelling variants 140/189; clean look-alikes wrongly flagged 3/40 |
| [wfv-station-source-v1](wfv-station-source-v1/) | WEATHER_FORECAST_VERIFY | A truth source: the nearest NOAA GHCN-Daily station for a place name and date | Fixes a sign bug in ECA&D longitudes between 0° and 1° west |
| [wfv-miner-quality-v1](wfv-miner-quality-v1/) | WEATHER_FORECAST_VERIFY | OathCast miner v20 against NOAA stations, on 100 city-days fixed in advance under a frozen rule | **PASS:** 92/100 covered; average error on the daily high 1.35 °C; 81.5% within ±2 °C |
| [wfv-adapter-run-v1](wfv-adapter-run-v1/), [v2](wfv-adapter-run-v2/), [sanctions-adapter-v1](sanctions-adapter-v1/) | WFV, sanctions | LoRA reward adapters trained on our own pairs, each with a go/no-go rule set before training | **Did not ship.** 90%+ on error types they'd seen; 53–61% on error types they hadn't |
| [wfv-adapter-run-v1/UPSTREAM-ISSUE-DRAFT.md](wfv-adapter-run-v1/UPSTREAM-ISSUE-DRAFT.md) | (kit) | A bug report on the baseline kit: a silent weightless bake, a missing dependency, a stale catalog | Led to [telegraph-wasm-baseline#5](https://github.com/telegraphprotocol/telegraph-wasm-baseline/pull/5) |

## Withheld on purpose
The **evaluation material** we contributed (preference pairs for WFV, sanctions and macro) is **not published**, and neither are the scripts that generate it. Those pairs sit in Telegraph's evaluation pool, part of which is a hidden testing set, and publishing them would expose evaluation questions. The material folders keep only their aggregate checks and design notes.

## Reproduce the comparator test
```sh
cd macro-comparator-v1
cargo build --release --target wasm32-unknown-unknown    # or use the committed macro_comparator.wasm
sh oracle/fetch_zkasuran.sh                               # third-party oracle, fetched rather than redistributed
uv run --no-project --with wasmtime python -I test_comparator.py macro_comparator.wasm
```

## Licences
- **Our code:** MIT (see [LICENSE](LICENSE)).
- `macro-comparator-v1/oracle/kit_hybrid_992f265.py` comes from [telegraphprotocol/telegraph-wasm-baseline](https://github.com/telegraphprotocol/telegraph-wasm-baseline) @`992f265`, MIT.
- **Data:**
  - World Bank WDI: CC BY 4.0.
  - GeoNames: CC BY 4.0.
  - NOAA GHCN-Daily: public domain (US government).
  - OFAC lists: public (US Treasury).
  - UN and EU consolidated lists: published openly by the UN and EU.
