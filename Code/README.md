# Agreement analysis

Run with Python 3.10 or newer from the repository root:

```powershell
python -m pip install -r Code/requirements.txt
python Code/run_analysis.py
```

All inputs are in `Data/`. Results default to `agreement_results/`.
The MASTER file is generated automatically; no original MASTER is needed.
Paths are based on the scripts' location, so another working directory also works.

```powershell
python Code/run_analysis.py --data-dir "C:/path/to/Data" --output-dir "C:/path/to/results"
```

## Analyses

- Flexible agreement: exact-set agreement, any overlap and mean per-record
  Jaccard at Levels 1–3. Includes both all-cause pooling and direct/underlying
  pooling. Bootstrap intervals use 5,000 replicates and seed 20261027.
- Exact agreement: direct and underlying codes separately, with kappa and F1.
- CCC: underlying causes, Overall and by VA type, using a physician-observed
  cause list fixed across experiments within each panel/level.
- CSMF: direct and underlying cause fractions, absolute differences, similarity
  and the existing chance-corrected accuracy calculation.

The runner checks VA type against PHY and joins age/sex for demographic context.
Age/sex do not change the current four agreement calculations. Empty experiment
predictions count as disagreement when physician reference codes are eligible.
CSMF normalizes nonblank predictions separately and reports blank counts.

## Data preparation

The supplied cause-code files are already normalized. To regenerate them from
the original EXP1–EXP5 and PHY workbooks, put those workbooks and the four
supporting files in a separate source directory and run:

```powershell
python Code/prepare_data.py --source-dir "C:/path/to/originals"
```

Preparation extracts EXP1 codes from MERGED and other experiment codes from
their dedicated columns. Experiment `99-00-00` becomes `00-00-00`; physician
underlying codes listed in `ucod_only_level1.csv` also become `00-00-00`.
That code is retained at Level 1 only. These corrections are already applied
in the supplied CSVs and are not applied twice by the analysis runner.

Supporting inputs are `va_type.csv`, `age_sex.csv`, `MEIRU_CODS_LIST.txt` and
`ucod_only_level1.csv`. The manifest records the files' schemas and hashes.
No narratives, confidence values, explanations or evidence are required.
