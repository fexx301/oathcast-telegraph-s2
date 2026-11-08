# SANCTIONS_SCREENING_MATCH_GENERAL material v1 (bounty #78)

204 preference pairs in `material.jsonl`, built by `build_sanctions.py` (design and reviewed fixes: [DESIGN.md](DESIGN.md)).

**Sources** (keyless, real records; capture times in `raw/fetch-log.jsonl`):
- OFAC SDN and Consolidated (non-SDN) lists: `Last-Modified` 2026-10-28 14:03 GMT, US government, public domain;
- the UN Security Council consolidated list: `dateGenerated` 2026-10-30T23:00Z;
- GLEIF LEI records (CC0).

**Query types:**

| Type | Query | Rows | Correct answer |
|---|---|---|---|
| Q1 | primary names (OFAC and UN) | 42 | match |
| Q2 | OFAC aliases (`alt.csv`) | 34 | match, via the alias |
| Q3 | OFAC-listed wallet addresses | 30 | match, owner named |
| Q4 | OFAC-listed vessels | 19 | match |
| Q5 | real GLEIF companies with a name token in common with a listed entity | 78 | not on these lists |

Q5 companies are not on OFAC SDN or non-SDN or the UN list (exact and normalised check against every primary and alias name). They're also excluded if:
- their name contains the listed name;
- their GLEIF parent is listed or carries the listed name;
- the shared token is the listed entity's leading, brand-like name (possible unlisted affiliate);
- they sit in a high-risk jurisdiction.

**Worse answers:**

| Kind | Wrong answer | Pairs |
|---|---|---|
| S1 | missed match | 80 |
| S2 | false positive against the real look-alike listed entry, with its real UID | 78 |
| S3 | wrong listed entry | — |
| S4 | wrong OFAC program | — |
| S5 | wrong wallet owner | — |

S1 ≈ S2, so "prefer the match-saying answer" scores about 50%.

**Checks:**
- kit `--check-data` pass (length shortcut 51.7%, surface probe 51.0%);
- local near-duplicate screen at ratio ≥ 0.96, calibrated on the node's four macro refusals;
- spot checks against the raw lists.

**Wording:** answers assert only list membership verified in the source. A no-match says "not on OFAC SDN/non-SDN or the UN list as published", never "not sanctioned", and states that EU/UK lists and 50%-rule ownership are out of scope.

**Known limits:**
- **No unlisted-wallet negatives**, so "wallet query → match" is always right in this set.
- **The Q5 look-alikes are easy** (a shared generic token, for affiliate safety). Spelling and transliteration near-matches come only through Q2 aliases.
- **EU and UK lists aren't covered.**
- **Lists change daily.** Rows are pinned to the list dates above.
