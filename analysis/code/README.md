# Analysis code for selected manuscript outputs

[Repo Link](analysis/code)

This folder contains the statistical scripts needed for Tables 2–6 and Figures 2–5. Final public artefacts are written to `analysis/outputs/`. Raw verbal-autopsy narratives, workbooks, identifiers, and record-level generated files remain outside this public repository.

## Order of execution

1. `analysis_llm_phy_agreement.py` — normalize authorized private inputs and calculate strict/flexible agreement aggregates.
2. `calculate_jaccard_similarity.py` — calculate pooled any-code Jaccard scores and aggregate summaries.
3. `calculate_csmf_accuracy.py` — calculate CSMF accuracy by level and VA type.
4. `calculate_monte_carlo_csmf_baselines.py` — calculate the physician-prior Monte Carlo baseline.
5. Run the selected table/figure generators:
   - `create_phy_underlying_distribution_by_vatype_table.py` (Table 2)
   - `create_flexible_agreement_line_charts.py` (Chart 2 panels)
   - `create_jaccard_by_vatype_distributions.py` (Table 4 bins)
   - `create_exp1_true_positive_heatmaps.py`, then `create_exp1_tp_level2_age_percent_table.py` and `create_exp1_tp_level2_age_percent_svg.py` (Table 5)
   - `create_comparison_visualizations.py` (Figures 3 and 4 source charts)
   - `create_pccc_level_vatype_chart.py` (Table 6 supporting calculation)
   - `create_monte_carlo_csmf_charts.py` (Figure 5)
6. `build_manuscript_outputs.py` — select columns, apply Table 5 colouring, create the four-panel Figure 2 page and six Figure 4 line charts, and write final artefacts into `analysis/outputs/`. It prefers fresh files from `analysis/working_outputs/agreement_analysis/` and otherwise uses the checked files in `analysis/aggregate_inputs/`.

The calculation scripts retain the original input schema and currently set `DATA_DIR` near the top of each file. Change that value to an authorized local data directory before running. Generated record-level intermediates are restricted working files and must not be copied into the public package.

## Table 5 styling rule

Percentages are calculated within each VA-type/age column. Cells from 10% through 20% inclusive use light green. Cells greater than 30% use dark green with bold white text. Values above 20% through 30% are intentionally uncoloured.

## Requirements

Python 3.10+ with `pandas`, `numpy`, and an Excel reader such as `openpyxl` for the private `.xlsx` inputs.
