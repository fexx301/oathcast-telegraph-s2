# SANCTIONS_SCREENING_MATCH_GENERAL truth source v1 (bounty #78)

A free, keyless screening API that we operate, built only from the official list files:

`GET https://ngrgakvwtxioa2kkdllvhn5pza0fxqcb.lambda-url.eu-north-1.on.aws/screen?name=<name or wallet>`

Hosted on AWS Lambda (`telegraph-sanctions-screen`, eu-north-1, public Function URL, reserved concurrency 5; `aws/deploy.sh`), moved there on 2026-11-03 at the user's request. The first upload pointed at a Vercel deployment (`truth-source-vercel.yaml`). That deployment was deleted on 2026-11-03 after the AWS row was in, so one contributor doesn't hold two sources in the median.

It returns the intent's response fields: `name`, `matched` (bool, scored), `matches`, `lists` (with publication and capture dates) and `match_score` (0–1).

**Lists** (in `raw/fetch-log.json`; raw files aren't committed):

| List | Entries | Published |
|---|---|---|
| OFAC SDN (with aliases and 507 wallet addresses from remarks) | 19,484 | 2026-10-28 |
| OFAC Consolidated (non-SDN) | 486 | 2026-10-28 |
| UN Security Council consolidated | 1,007 | 2026-11-02 |
| EU consolidated financial sanctions | 6,269 | 2026-10-23 |

**Matching:**
- **Wallets:** exact address match (`0x` addresses are compared case-insensitively).
- **Names:** accents and punctuation stripped, legal-form words dropped, tokens sorted, then a `difflib` ratio against every listed name and alias that shares a token. `matched` is true at score ≥ **0.84**.
- **Question-shaped input:** a wallet is found anywhere in the text (for example `ETH:0x…`). Bracketed text, comma parts with digits or labels (DOB, IMO), a trailing one-word country and leading descriptors ("vessel", "Mr") are stripped. The score is the better of the raw and cleaned name. Checked in `calibrate.py`; the calibration numbers barely moved (139→140/189 before vs after).

**Calibration** (`calibrate.py` → `calibration.json`; the threshold rule was fixed before the run):
- **Positives:** leave-one-out spelling variants of OFAC SDN individuals. An alias that shares a token with the primary name is screened with that one spelling hidden.
- **Negatives:** material v1's GLEIF look-alike companies, which aren't listed.
- **Split:** half chooses the threshold; the other half is the test.

| Held-out test half | Result |
|---|---|
| Spelling variants matched | 140/189 (74%); the right person in 112 |
| Clean look-alikes flagged | 3/40 (8%) |
| Exact listed names, aliases, vessels and wallets from material v1 | 126/126 |

The first calibration design (`calibration-v1-flawed.json`) used EU names linked to UN references. Most of those were translations of group names into other EU languages, and restricting it to individuals left only 4 rows, so it was replaced. After the test half had been seen, the only change was the question-shaped input cleanup, added for the request builder's input format and not to cut false positives. It moved the test result from 139 to 140/189, with false positives unchanged at 3/40.

**Against sanctions.network** (same 45 queries as [probe v1](../sanctions-truth-probe-v1/RESULT.md)):

| | Ours | sanctions.network |
|---|---|---|
| Listed names, aliases and vessels | 20/20 matched | 19/19 non-empty (1 failed) |
| Listed wallets | 5/5 | 0/4 (1 failed) |
| Clean look-alikes | 1/20 flagged | 12/13 non-empty (7 failed) |

Our positives come from the same official files this API indexes, so exact hits are expected. The leave-one-out test above is the fairer measure.

**Known limits:**
- False positives come from generic industry or legal-form words: PETROCHEMICAL, INFORMATION TECHNOLOGIES, SHIPMANAGEMENT, and the Hungarian "Korlátolt Felelősségű Társaság" (a limited-company form).
- No UK list.
- Names in non-Latin scripts reduce to nothing after normalisation and never match.
- There's no ownership or 50%-rule screening.
- **Lists refresh daily at 06:15 UTC** (deployed 2026-11-03; first run passed). `aws/refresh_function.py` re-fetches all lists, rebuilds the index and swaps it into the screen Lambda. It keeps the live index if any list fetch fails, a count falls below its floor, or a known-answer check fails (tested locally). `sh aws/deploy-refresh.sh` creates it and the schedule. A manual refresh is `aws lambda invoke --region eu-north-1 --function-name telegraph-sanctions-refresh out.json`.

**Files:**
- `build_index.py`: fetches the lists and builds `api/index.json.gz`.
- `api/_screen.py`: the screening core.
- `api/screen.py`: the HTTP handler.
- `aws/`: the Lambda handler and deploy script.
- `truth-source.yaml` / `items.jsonl`: the AWS YAML (with `intent_mapping`) and its upload row.
- `truth-source-vercel.yaml` / `items-vercel.jsonl`: the first upload, which points at Vercel.

**Upload** (the user's signed step): in Anjoman → Evaluate, add `items.jsonl` under `SANCTIONS_SCREENING_MATCH_GENERAL`.
