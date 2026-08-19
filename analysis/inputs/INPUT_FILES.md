# Input files required to reproduce the analysis

Raw data files are intentionally not copied into this GitHub-ready folder because they may contain individual-level verbal autopsy records. Place the following files in `C:\Users\Lenovo\Downloads\MEIRU_VA_EXP` or update `DATA_DIR` in `analysis_llm_phy_agreement.py`:

- `MEIRU_CODS_LIST.txt`
- `EXP1.xlsx` with sheet `EXP1`; parsed from the `MERGED` column
- `EXP2.xlsx` with sheet `EXP2`
- `EXP3.xlsx` with sheet `EXP3`
- `EXP4.xlsx` with sheet `EXP4`
- `PHY.xlsx` with sheet `PHY`
- `va_type.csv`
- `age_sex.csv`

The generated normalized analytic input for downstream scripts is `outputs/agreement_analysis/master_normalized_codes.csv`. This file is not included here by default because it is record-level.
