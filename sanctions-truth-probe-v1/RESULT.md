# sanctions.network as a SANCTIONS_SCREENING_MATCH truth source: probe v1 (2026-11-03)

**Question:** can the one keyless sanctions search API give the node a reliable `matched` (bool) reference?

**Method:** 45 queries sampled (seed 7) from our labelled material v1 (`queries.tsv`): 8 OFAC/UN primary names, 8 OFAC aliases, 5 OFAC-listed wallets, 4 OFAC-listed vessels (all truly listed), and 20 GLEIF look-alike companies (verified not on OFAC SDN/non-SDN or UN). Each sent once with plain `curl` to `GET https://api.sanctions.network/rpc/search_sanctions?name=…`, 0.5 s apart, 30 s timeout. Raw bodies: `results.tsv`.

**Results:**

| Group | Answered | Non-empty | Note |
|---|---|---|---|
| Listed names/aliases/vessels (Q1, Q2, Q4) | 19/20 | 19/19 | Fuzzy; up to 100 rows. The true entry is the top hit in ~8 of 19; for common names (MOHAMMAD AHMADI, NOVIKOV, BABAKOV) the top two are other people. |
| Listed wallets (Q3) | 4/5 | **0/4** | Crypto addresses aren't indexed. |
| Not-listed look-alikes (Q5) | 13/20 | **12/13** | Non-empty for almost every clean company (e.g. TEXCHEM INDUSTRIES → 100 rows). |
| Failures | 9/45 | — | 504s and empty bodies (timeouts). |

**Reading:** "non-empty list ⇒ matched" would call ~92% of clean companies matched and miss every wallet. A model reading the list may do better, but the API gives no score or match flag to anchor it. ~20% of calls failed, which the node drops from the median.

**Other keyless sources checked:** OpenSanctions API and trade.gov Consolidated Screening List both return 401 (key required). sanctions.network's exact filter (`/sanctions?names=cs.{"…"}`) is case- and order-sensitive ("Azizollah MALEKI" hits, "MALEKI, Azizollah" misses).

**Limits:** small sample; one pass; no retry; not a test of the node's actual parser.
