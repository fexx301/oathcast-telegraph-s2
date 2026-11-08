# SANCTIONS_SCREENING_MATCH_GENERAL material v1: design (bounty #78)

**Intent** (bounty text): a query supplies a person, company or wallet and asks whether it appears on OFAC, EU, UN or other consolidated sanctions lists, including near-matches on spelling or transliteration.
- **Contract:** request `name` → `name`, `matched` (bool), `matches` (list), `lists` (list), `match_score` (0–1).
- **App needs** (#78): screen payee wallets and owners, clients and beneficial owners, counterparties, treasury addresses, vessels and owners.

**Sources** (keyless, real records; capture time and list date recorded per row):
- OFAC SDN `sdn.csv` and `alt.csv` from sanctionslistservice.ofac.treas.gov (US government, public domain);
- the UN Security Council consolidated list XML;
- GLEIF LEI records (CC0), for real *unlisted* legal entities.

**Query types:**

| Type | Query | Correct answer |
|---|---|---|
| Q1 | an SDN or UN primary name | match |
| Q2 | an alias or transliteration from `alt.csv` | match, via the alias |
| Q3 | a wallet address from SDN remarks (Digital Currency Address) | match, owner named |
| Q4 | a vessel name (SDN type vessel) | match |
| Q5 | a real GLEIF legal entity that shares a distinctive token with a listed name | **not on these lists** |

Q5 entities are checked exactly and after normalisation against every SDN primary and alias name and every UN name.

**Wording discipline:** a correct no-match answer says "not on the OFAC SDN list or the UN consolidated list as published on <date>". It never says "not sanctioned", because ownership rules (OFAC's 50% rule), EU and UK lists, and later designations are out of scope. These limits are stated in the answer.

**Worse answers** (realistic screening errors):

| Kind | Applies to | Wrong answer |
|---|---|---|
| S1 missed match | Q1–Q4 | false negative; common with aliases and transliteration |
| S2 false positive | Q5 | matched to the similar listed entity |
| S3 wrong entry | Q1–Q4 | matched to a different real listed entry sharing a name token, with its UID and program |
| S4 wrong program or list | Q1–Q4 | the right entity with a wrong program code, or a list it isn't on |
| S5 wrong wallet owner | Q3 | another real listed owner |

**Balance:**
- S1 pairs ≈ S2 pairs, so "prefer the match-saying answer" scores about 50%.
- Match and no-match templates are length-matched.
- Kit `--check-data` must pass.

**Size:** about 220 rows: 140 positives (Q1 50, Q2 35, Q3 30, Q4 25) and 80 negatives (Q5).

**Provenance:** `source_kind: "api"`; per-row source URL, list publication or generation date, capture time, entry UID or reference, `prompt_rendering: "template"`.

**Out of scope for v1:** the EU list (served through a token-bearing public URL), UK OFSI, delistings, and ownership screening.
