# OathCast: Telegraph Hackathon Season II work

Evaluation and serving work for [Telegraph](https://telegraphprotocol.com) Hackathon Season II, by the OathCast project.

**Disclosure:** this is a hackathon entry. I'm competing in Season II, which has prizes.

The miner itself lives in [fexx301/oathcast](https://github.com/fexx301/oathcast). This repo holds the evaluation side: a comparator module, truth sources, quality tests, and the experiments that didn't ship.

**New here? Start with [REPRODUCE.md](REPRODUCE.md):** a 20-minute, no-wallet walkthrough that checks every claim below.

## What's here

| Folder | Intent | What it is | Result |
|---|---|---|---|
| **[wfv-adapter-v6](wfv-adapter-v6/)** | WEATHER_FORECAST_VERIFY | Our LoRA reward adapter on Telegraph's shared foundation model, registered on-chain as reg 408 | **The Intent's first canonical scorer** (15 Nov, 21/30 on the hidden round); later replaced by another team's reg 445 (70.00% vs 66.67%). About 70% across four hidden rounds (85/120). 87.0% on our own held-out set |
| [wfv-adapter-v3](wfv-adapter-v3/), [v4](wfv-adapter-v4/), [v5](wfv-adapter-v5/), [v7](wfv-adapter-v7/) | WEATHER_FORECAST_VERIFY | The other adapter attempts, each with its spec and pass bars frozen before training | v3 (69.3%) and v4 (70.5%) stopped by our bars. v5 passed ours (89.3%) but lost its hidden round (63.3%). v7 beats v6 on our frozen test (0.929 vs 0.844) and isn't registered: it waits for the pool to reach 3 contributors (1 on 22 Nov) |
| [macro-comparator-v1](macro-comparator-v1/) | MACRO_ECONOMIC_INDICATOR | A 2.5 KB `no_std` Rust comparator WASM (zero imports), registered on-chain as reg 223 on the old Diamond, plus its hosted runnable endpoint. It isn't a live scorer: Telegraph uses one shared comparator for deterministic checks, so community comparators aren't registered (the team, 22 Nov). It stands as a verified reimplementation | Matches the kit's reference code on 17,680 grid vectors, 20,000 battery-shaped cases and 776 i64-extreme probes; matches a canonical comparator on 19,735 in-domain cases |
| [macro-truth-source-v1](macro-truth-source-v1/) | MACRO_ECONOMIC_INDICATOR | A truth source: the World Bank WDI API, called directly | 8/8 sampled cases match |
| [sanctions-truth-source-v1](sanctions-truth-source-v1/) | SANCTIONS_SCREENING_MATCH | A keyless screening API over the official OFAC SDN and non-SDN, UN and EU lists plus 507 wallets, refreshed daily | Exact names and wallets 126/126; spelling variants 139/189; clean look-alikes wrongly flagged 3/40 |
| [wfv-station-source-v1](wfv-station-source-v1/) | WEATHER_FORECAST_VERIFY | A truth source: the nearest NOAA GHCN-Daily station for a place name and date | Fixes a sign bug in ECA&D longitudes between 0° and 1° west |
| **[wfg-material-v1](wfg-material-v1/)** | WEATHER_FORECAST_GENERAL | 150 preference pairs from MET Norway and the US National Weather Service (no Open-Meteo, so our own forecast miner 64173 gets no edge); aggregate checks only, pairs withheld | **Unblocked the pool:** ours was the third eligible contributor; it became evaluable on 22 Nov (272 rows from 4 contributors). Kit gate passed; "pick the longer" 0.420 overall, but 0.84 on kind K4 (disclosed) |
| **[ssl-truth-source-v1](ssl-truth-source-v1/)** | SSL_VERIFICATION_CERT | A keyless truth source: a live TLS handshake with hostname verification against Mozilla's root list; private addresses refused | **Unblocked the pool:** ours was the third eligible contributor; evaluable since 23 Nov (epoch 41). 11/11 live tests. Revocation isn't checked (stated) |
| [wfv-miner-quality-v1](wfv-miner-quality-v1/) | WEATHER_FORECAST_VERIFY | OathCast miner v20 against NOAA stations, on 100 city-days fixed in advance under a frozen rule | **PASS:** 92/100 covered; average error on the daily high 1.35 °C; 81.5% within ±2 °C |
| [wfv-adapter-run-v1](wfv-adapter-run-v1/), [v2](wfv-adapter-run-v2/), [sanctions-adapter-v1](sanctions-adapter-v1/) | WFV, sanctions | LoRA reward adapters trained on our own pairs, each with a go/no-go rule set before training | **Did not ship.** 90%+ on error types they'd seen; 53–61% on error types they hadn't |
| **[frontier-test-v1](frontier-test-v1/)** | Gold Rush and sanctions | Our specialists against a frontier model (GPT-6.2-ASTRA) on 15 current-record questions, spec frozen first, published whatever it showed | No tools: 2 correct, 0 wrong, 11 "can't establish". With web search: 15/15. Ours: 13/15 (two real sanctions listings missed because of a parsing bug, fixed the same day; 15/15 after) |
| [shortcut-judges-v1](shortcut-judges-v1/) | WFV (any pairs) | Two cheap "shortcut judges" (pick the longer answer; pick the answer with more words in common with the prompt), overall and per error family, standard library only | On our uploaded WFV pairs: length 0.497 overall but 0.17–0.88 per family; prompt overlap 0.783, mostly legitimate (wrong station, day or variable, or a misquoted forecast); fill-value and window pairs leak. Reported as a limit |
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
