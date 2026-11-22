# Frontier-model test v1: RESULT (2026-11-22)

**Spec frozen before any question was asked:** [README](README.md), commit `1012455`. Frontier model:
**GPT-6.2-ASTRA** (OpenAI's top GPT model, as shown in the app), in fresh sessions run through Codex CLI by the user.

## Headline
| Answerer | Correct | Partial | Wrong | Can't establish |
|---|---|---|---|---|
| GPT-6.2-ASTRA, run A (no tools) | 2 | 2 | **0** | **11** |
| GPT-6.2-ASTRA, run B (web search) | **15** | 0 | 0 | 0 |
| Our specialists (frozen run) | 13 | 0 | **2** | 0 |
| Our specialists, post-fix check (not part of the frozen run) | 15 | 0 | 0 | 0 |

**What it shows, plainly:**
1. **Without tools, the frontier model can't answer current-record questions, and it says so rather than
   inventing.** In run A it named no current lease holder, none of the survey's figures, and none of the five
   sanctions listings. Its only correct answers were older public facts: a 2024 native title determination and
   Mount Morgan's 250 t.
2. **With web search, it answered all 15 correctly,** pointing at the same official registers our specialists read
   (Queensland's ArcGIS services, the NNTT, OFAC's notices, the GSQ database).
3. **Our specialists got 13 of 15 in the frozen run.** The sanctions miner missed two real listings (Francesco
   Commisso, 19 Nov; Gold Global Company, 18 Nov), though its lists were current to 20 Nov:
   - **Cause:** a "Name, City, Country" question kept the city in the query, and the match score fell to 0.818
     against a 0.84 threshold.
   - **Fixed and deployed the same evening;** regression tests 9/9.
   - **Calibration, like for like:** exact listed names 126/126, look-alikes flagged 3/40, spelling variants 139/189
     (was 140), right person 112.
   - **Post-fix check:** 5/5.

So on these 15 questions, **a web-enabled frontier agent matched our specialists on accuracy**. Our honest advantages
are elsewhere, and only where measured:

| | Our specialists | GPT-6.2-ASTRA with web search |
|---|---|---|
| Time | Sanctions screen: warm p95 0.84 s per name (pre-registration test, 15 Nov). Gold Rush: 7–55 s per paid answer (median about 35 s), and one land answer covers tenure, native title and heritage for a site | About 10 minutes for the 15 answers (about 40 s each) |
| Cost | $0.01 per paid answer, known in advance, with a receipt and a node delivery record. These 15 questions drew on 9 Gold Rush answers already bought ($0.09) and the free screening endpoint (5 × $0.01 through Telegraph) | Not shown by the app |
| Output | Structured fields (holder, permit, status, dates, record ID, check date) an app can use directly | Prose with links |
| Repeatability | The same query gives the same answer from the same record; built to run across 8,132 sites or any name list | An agent run; each answer depends on its search path |

## Every answer, graded
References were fetched after the runs, directly from the official sources (`ref/`): Queensland's current resource
authorities, the NNTT spatial data, the Queensland Heritage Register, the GSQ site layer and the **MINOCC 2017
database** (`refs-minocc.json`; archive sha256 `6ad8fef2…fe43`), the Queensland Government's Mount Morgan page, and
**OFAC's SDN file as published 20 Nov**.

| Q | Reference | Run A | Run B | Ours (frozen) |
|---|---|---|---|---|
| 1 | ML 10208, Citigold, expires 31 Dec 2035 | can't establish | correct | correct (ML 10208, Citigold, 2035-12-31) |
| 2 | ML 5623, Heritage Minerals, Granted (renewal lodged) | can't establish | correct | correct |
| 3 | EPM 28416, New Gympie Gold | can't establish | correct | correct |
| 4 | Gudjala People; native title exists, non-exclusive (within 2 km; one area extinguished) | partial (people only) | correct | correct (QCD2016/013, /014 and QCD2014/007 non-exclusive; ILUAs over the site) |
| 5 | Kabi Kabi First Nation, 17 Jun 2024, non-exclusive | correct | correct | correct |
| 6 | 51,482.73 kg of gold; worked 1879–1917 | can't establish | correct | correct |
| 7 | Giant (>150 t); site 494270 | can't establish | correct | correct |
| 8 | 2008 (mining ceased Dec 2008) | can't establish | correct | correct |
| 9 | No. 1 Scottish Gympie Mine and Battery, over the site point | partial (named it; unsure it's at the site) | correct | correct |
| 10 | About 250 t, 1882 to Nov 1990 | correct | correct | correct |
| 11 | Listed: SDGT, IFSR (20 Nov) | can't establish | correct | correct |
| 12 | Listed: ILLICIT-DRUGS-EO14059 (19 Nov) | can't establish | correct | **wrong (no match)**; post-fix: correct |
| 13 | Listed: SDGT (18 Nov) | can't establish | correct | **wrong (no match)**; post-fix: correct |
| 14 | Listed: SDGT (18 Nov) | can't establish | correct | correct |
| 15 | Not listed | can't establish | correct | correct |

**Files:**
- answers verbatim: `run-A.txt`, `run-B.txt`, `ours-goldrush.json` (from Gold Rush's public ledger, with receipts),
  `ours-sanctions.jsonl` (frozen run), `ours-sanctions-postfix.jsonl`;
- references: `ref/refs-qld.json` and `ref/refs-minocc.json` (OFAC's file is cited by URL; it's 5.8 MB).

## Limits
- **15 questions, chosen by us,** on facts our specialists were built for. It shows where a general model needs live
  records, not that it's weaker in general.
- **Run A's "no tools" was set by instruction**, with an empty starting folder as the backstop. The model's own
  compliance wasn't otherwise checked.
- **Run B's cost wasn't shown;** its time is the user's estimate.
- **Our Gold Rush answers were bought before the test** (the reports already existed). The sanctions answers came
  from the miner's public endpoint, which is the same engine the Telegraph miner serves, not from paid Telegraph
  calls.
