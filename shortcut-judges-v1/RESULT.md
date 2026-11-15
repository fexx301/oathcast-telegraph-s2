# Shortcut judges on our WFV preference pairs (2026-11-15)

Two cheap judges pick an answer per pair without checking anything; ties count half. `judges.py` (stdlib, self-check
built in) gives the overall rates and `by_family.py` gives them per family. Raw output: `overall.tsv` and
`by-family-material-v1.tsv`. Prompted by an exchange with another Evaluators-track builder (AdversarialEval) in the
Telegraph Discord.

**Disclosure:** this is part of a hackathon entry (Telegraph Hackathon Season II, which has prizes).

**The pairs themselves are withheld,** like all our pool material (see the repo README), because they sit in Telegraph's
evaluation pool. Only these aggregate rates are published. The scripts run on any JSONL file with `prompt`, `chosen`
and `rejected` fields, so you can check your own pairs:

```sh
python3 judges.py your_pairs.jsonl
python3 by_family.py your_pairs.jsonl your_meta.jsonl family   # meta: one JSON object per pair, with a family field
```

**Ties count half.** [`../wfv-material-v1/checks.json`](../wfv-material-v1/checks.json) gives `pick_longer` 0.397 for the
same rows; that counts only strict wins (119/300). There are 60 equal-length pairs, so with ties as half it is 0.497.

## Overall

| Set | n | pick longer | TF-IDF overlap with prompt |
|---|---|---|---|
| **material-v1, the pool-format rows we uploaded** | 300 | 0.497 | **0.783** |
| pool-fresh-3 (same generator, new stations) | 300 | 0.513 | 0.767 |
| test-mos-real | 240 | 0.554 | 0.617 |
| test-mos | 240 | 0.577 | 0.558 |
| test-render | 400 | 0.564 | 0.848 |
| v6 train | 4200 | 0.535 | 0.713 |

## Per family, material-v1 (uploaded rows)

| Family | What the worse answer gets wrong | n | TF-IDF | longer | worse answer misquotes the question (rows) |
|---|---|---|---|---|---|
| F1 | verdict flipped | 24 | 0.42 | 0.67 | 7/24 |
| F2 | another day | 44 | 0.89 | 0.45 | 44/44 |
| F3 | another station | 44 | 0.93 | 0.52 | 42/44 |
| F4 | unit slip | 24 | 0.62 | **0.25** | 12/24 |
| F5 | another variable (low for high) | 23 | 1.00 | **0.26** | 21/23 |
| F6 | fill value (-999) read as data | 25 | 0.88 | 0.66 | 14/25 |
| F7 | digit swap | 24 | 0.88 | **0.17** | **24/24** |
| F8 | wrong arithmetic | 24 | 0.67 | 0.62 | 13/24 |
| F9 | tolerance misread | 24 | 0.50 | **0.88** | 8/24 |
| F10 | wrong window (three days) | 44 | 0.82 | 0.49 | 8/44 |

## Reading

- **Prompt overlap is high, mostly for a legitimate reason** (corrected 2026-11-15; the first version called digit
  swaps a leak). Where the worse answer misquotes something the question states, matching the question *is* the skill:
  - wrong day (F2), station (F3) and variable (F5);
  - **digit swap (F7)**: in all 24 rows, the swapped number is the question's own forecast, restated wrongly.

  The last column counts rows where the text the worse answer changed appears in the question (a token check, so
  approximate).
- **Real leaks:** fill value (F6, 0.88) and wrong window (F10, 0.82). There the judge's win isn't explained by matching
  the question: rare tokens such as `-999` and the window wording shift the overlap. On verdict, tolerance and
  arithmetic pairs (F1, F9, F8) the judge is 0.42–0.67, near chance.
- **Length is balanced overall (0.497) but not within families (0.17–0.88).** The verdict phrases differ in length
  ("verified." vs "did not verify."), and within a family the correct verdict leans one way. A judge that could
  identify the family from the text could exploit it. Overall balance hid this, which is the same lesson as
  reporting numerical families separately.
- **Scope:** this covers the 300 material rows. We have 301 eligible rows in the pool; the 301st is not in this audit
  and is not identified here.
- **Not fixed.** The rows are already in the pool; this is reported as a limit. A future material version should
  balance the verdict direction within every family, and should check judges per family before upload.
