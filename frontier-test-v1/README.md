# Telegraph S2: frontier-model test v1 — spec

**FROZEN 2026-11-22, approved by the user ("approved").** This commit is the freeze. No question is put to
any model, and no reference is fetched for scoring, before it.

## Why
Ahmed (22 Nov, to all participants): "test against strong frontier models. Show real cases where they get something
wrong or cannot establish the answer … include evidence, costs and limitations." None of our entries has done this.

## What is compared
- **Our specialists:**
  - **Gold Rush** (miners 64176 and NFT KING's 7310050), using the reports already bought (receipts on record; no
    new cost);
  - **sanctions miner 64175**, through its public screening endpoint (`/screen`), which is the same endpoint and
    engine the Telegraph miner serves. No cost.
- **A frontier model:** OpenAI's top GPT model, through the user's agent Astra. The exact model name the app shows
  is recorded.
  - **Run A, no tools:** web search, browsing and files off. This tests what the model knows.
  - **Run B, web search on:** the realistic competitor. If an answer cites our Gold Rush app or Takar's dossiers,
    it's flagged as our own data echoed back.
  - **Every run is a fresh session** with no memory carried over. Tool use is controlled by an instruction at the top
    of each run (below); starting it in an empty folder is a backstop, so there's nothing of ours to find even if the
    instruction were ignored. The questions are pasted exactly as written below, one at a time, and the answers copied
    back verbatim.
  - **Instruction for run A** (pasted once at the start):
    > Answer each question from your own knowledge only. Do not search the web, browse, open links or read any files.
    > If you don't know or can't be sure, say so.
  - **Instruction for run B** (pasted once at the start):
    > Answer each question. You may search the web. Cite the sources you used. If you can't establish the answer, say
    > so.

## The 15 questions (fixed by this commit)
Mining records (Queensland, public registers):
1. Who currently holds the mining lease over the Brilliant Lode gold mine at Charters Towers, Queensland, and when does it expire?
2. Which mining lease covers the old Mount Morgan gold mine in Queensland today, who holds it, and what is its status?
3. Which exploration permit covers the Gympie gold mine site in Queensland today, and who holds it?
4. Is there a native title determination over the area around the Brilliant Lode mine at Charters Towers? If so, for which people, and are the rights exclusive?
5. Is there a native title determination around the Gympie gold mine site in Queensland? If so, for which people, when was it made, and are the rights exclusive?
6. How much gold does the Geological Survey of Queensland record for the Brilliant Lode mine at Charters Towers, and up to which year?
7. What gold size class does the Geological Survey of Queensland assign to Mount Morgan, and what is its survey site number?
8. According to the Geological Survey of Queensland, in which year did mining last take place at the Gympie gold mine site?
9. Is there a Queensland heritage-listed place right at the old Gympie gold mine site? If so, what is it called?
10. How much gold did Mount Morgan produce according to the Queensland Government, and over what period?

Sanctions (OFAC Specially Designated Nationals list, as published on the day of the run):
11. Is Mojtaba Arabnejad, born 4 June 1984 in Iran, on the US OFAC sanctions list? If so, under which program?
12. Is Francesco Commisso, born 3 October 1956 in Siderno, Italy, sanctioned by the US Treasury? If so, under which program?
13. Is the company Gold Global Company of Sidon, Lebanon, on the US OFAC sanctions list?
14. Is Hassan Khechen, born 19 July 1986 in Lebanon, on the US OFAC sanctions list?
15. Is Arabnejad Trading LLC of Dubai on the US OFAC sanctions list?

## References (fetched after the runs, directly from the official source; never from our own miners)
- **Questions 1–5 and 9:**
  - tenure: Queensland's current resource authorities service (`spatial-gis.information.qld.gov.au`, point query at
    the GSQ site location);
  - native title: the National Native Title Tribunal's spatial data;
  - heritage: the Queensland Heritage Register service.
- **Questions 6–8:** the GSQ MINOCC record (ArcGIS layer 16 and the MINOCC 2017 tables).
- **Question 10:** the Queensland Government's published page for Mount Morgan.
- **Questions 11–15:** OFAC's SDN list file and the recent-actions notices for 18–20 Nov 2026.

## Scoring (the same rule for every answer, ours included)
Each answer gets exactly one grade:
- **Correct:** every fact asked matches the reference.
- **Partial:** some facts match and none is wrong.
- **Wrong:** states at least one fact that contradicts the reference (a confident error).
- **Can't establish:** says it doesn't know or can't verify, without stating a wrong fact.

**Reported:** counts per grade for each answerer and condition, every answer verbatim beside its reference, and the
cost of each answer (our receipts at $0.01 each; the model's cost as stated by its app).

**Limits stated up front:**
- the sample is 15 questions chosen by us, about facts our specialists were built for;
- it shows where a general model lacks live records, not that it's worse in general.

## Publishing
Results are published in `fexx301/oathcast-telegraph-s2` (`frontier-test-v1/`) **whatever they show**, including
any question our specialists get wrong.

## Budget
About 2–3 hours of the assistant's time, plus the user's runs (about 30 pastes). No new paid calls.
