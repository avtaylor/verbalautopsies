# Selected manuscript analysis

This slimmed-down folder contains only the aggregate tables and charts included in the manuscript, the code needed to reproduce them, and the minimal aggregate inputs needed to rebuild the presentation artifacts without sharing record-level VA data.

## Contents

- `outputs/` — Tables 2–6, Chart 2, and Figures 3–5.
- `code/` — agreement, Jaccard, CSMF, PCCC, Monte Carlo, and manuscript assembly scripts.
- `aggregate_inputs/` — minimal de-identified aggregate inputs used by the final assembly step.

See [`code/README.md`](code/README.md) for execution order. The scripts that calculate metrics from the original source data require authorized private inputs. Raw questionnaires, narratives, identifiers, physician workbooks, model responses, and record-level intermediate tables are not included.

## Manuscript deliverables

1. Table 2: Underlying CoD distributions at Level 1 and top Level 2.
2. Table 3: EXP1–EXP4 comparison using strict underlying agreement, flexible any-code agreement, Jaccard similarity, and CSMF accuracy at Levels 1–3.
3. Figure 2: Flexible any-code agreement by coding level for overall, adult, child, and infant VA groups.
4. Table 4: Level-2 flexible-match Jaccard similarity bins.
5. Table 5: EXP1 top-20 Level-2 true-positive overlap by VA type and age.
6. Figure 3: Largest EXP1 versus physician Level-2 underlying distribution differences by VA type.
7. Figure 4: Six line charts showing PCCC and CSMF accuracy for adult, child and infant VA groups, with one line per experiment.
8. Table 6: PCCC for strict underlying CoD agreement.
9. Figure 5: Observed Level-2 CSMF accuracy versus the Monte Carlo physician-prior baseline.

## AI-assisted coding disclosure

AI-assisted coding using Codex was used to generate code for some of the charts. All AI-generated code was reviewed manually, tested against the data, and verified by the human authors to ensure its correctness.
