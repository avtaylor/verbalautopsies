# MEIRU VA LLM cause-of-death analysis

Selected, de-identified outputs from analyses comparing four large-language-model (LLM) cause-of-death experiments with physician-coded verbal autopsy (VA) references.

**Start here:** open [`index.html`](index.html) to browse a small, curated set of headline figures and their aggregate source tables. The full file inventory is in [`FILE_MANIFEST.csv`](FILE_MANIFEST.csv).

## What is included

- `agreement/` — strict and flexible agreement summaries, confusion counts, confidence intervals, and paired tests.
- `csmf/` — cause-specific mortality fraction (CSMF) and chance-corrected accuracy summaries.
- `jaccard/` — aggregate set-overlap summaries for pooled and contributory causes.
- `EXP1/`–`EXP4/` — experiment-level aggregate distributions and stratified figures.
- `*/code/` — analysis and figure-generation scripts retained for methodological transparency.
- `inputs/INPUT_FILES.md` — descriptions of restricted upstream inputs; the inputs themselves are not included.

The folders named `excel/` contain CSV tables, despite the historical folder name.

## Data-sharing boundary

This package is intended for public sharing and contains only code, figures, and aggregate outputs. It deliberately excludes raw VA narratives, source workbooks, model responses, identifiers, and case/record-level comparison tables. For data requests contact the authors.

When this folder is placed in the main `verbalautopsies` repository as `analysis/`, `index.html` links upward to the root `data_preparation/` and `OpenAPI_calls/` folders for the questionnaire-to-text and OpenAI API code. Raw records and API credentials are not included.



## Reproduction notes

The upstream entry point is `agreement/code/analysis_llm_phy_agreement.py`. It creates a normalized record-level intermediate used by downstream CSMF, Jaccard, uncertainty, and chart scripts. That intermediate and the source data are intentionally absent, so this public package documents the workflow but is not runnable end-to-end without authorized access to restricted inputs.

Paths in the retained scripts reflect the original analysis environment and may need configuration before an authorized rerun. See [`inputs/INPUT_FILES.md`](inputs/INPUT_FILES.md) for the expected private inputs.

## Experiment labels

`EXP1` through `EXP4` identify the four evaluated LLM analysis conditions. Consult the associated study documentation before assigning substantive prompt/model descriptions to these labels.

## Responsible use

These outputs evaluate agreement with physician coding and population-level cause distributions. They should not be interpreted as clinical diagnoses or used to make decisions about individuals.
