from __future__ import annotations

from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

from flexible_agreement import (
    BOOTSTRAP_REPLICATES,
    CODE_LEVELS,
    EXPERIMENTS,
    MASTER_FILE,
    RANDOM_SEED,
    clean_code,
    set_at_level,
)


OUTPUT_DIR = Path("outputs") / "analysis_redo" / "flexible_agreement_underlying_direct_pooled"
PHY_COLUMNS = ("PHY_underlying", "PHY_direct")


def pooled_set(row: pd.Series, columns: tuple[str, ...]) -> set[str]:
    return {code for column in columns if (code := clean_code(row[column])) is not None}


def calculate_records(master: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for _, record in master.iterrows():
        physician_full = pooled_set(record, PHY_COLUMNS)
        for experiment in EXPERIMENTS:
            experiment_full = pooled_set(
                record, (f"{experiment}_underlying", f"{experiment}_direct")
            )
            for level in CODE_LEVELS:
                physician = set_at_level(physician_full, level)
                prediction = set_at_level(experiment_full, level)
                comparable = bool(physician)
                intersection = physician & prediction
                union = physician | prediction
                rows.append(
                    {
                        "ident": record["ident"],
                        "experiment": experiment,
                        "level": level,
                        "physician_codes": "; ".join(sorted(physician)),
                        "experiment_codes": "; ".join(sorted(prediction)),
                        "n_physician_codes": len(physician),
                        "n_experiment_codes": len(prediction),
                        "comparable": comparable,
                        "exact_set_agreement": bool(physician == prediction) if comparable else pd.NA,
                        "any_code_overlap": bool(intersection) if comparable else pd.NA,
                        "jaccard_similarity": len(intersection) / len(union) if comparable else np.nan,
                    }
                )
    return pd.DataFrame(rows)


def bootstrap_ci(values: np.ndarray, rng: np.random.Generator) -> tuple[float, float]:
    estimates = np.empty(BOOTSTRAP_REPLICATES, dtype=float)
    for index in range(BOOTSTRAP_REPLICATES):
        estimates[index] = rng.choice(values, size=len(values), replace=True).mean()
    return tuple(float(value) for value in np.quantile(estimates, [0.025, 0.975]))


def aggregate(records: pd.DataFrame) -> pd.DataFrame:
    rng = np.random.default_rng(RANDOM_SEED)
    rows: list[dict[str, object]] = []
    for (experiment, level), group in records.groupby(["experiment", "level"], sort=False):
        eligible = group[group["comparable"]].copy()
        measures = {
            "exact_set_agreement": eligible["exact_set_agreement"].astype(float).to_numpy(),
            "any_code_overlap": eligible["any_code_overlap"].astype(float).to_numpy(),
            "mean_jaccard_similarity": eligible["jaccard_similarity"].astype(float).to_numpy(),
        }
        row: dict[str, object] = {
            "experiment": experiment,
            "level": level,
            "eligible_physician_records": len(eligible),
            "empty_experiment_sets": int((eligible["n_experiment_codes"] == 0).sum()),
        }
        for measure, values in measures.items():
            low, high = bootstrap_ci(values, rng)
            row[measure] = float(values.mean())
            row[f"{measure}_ci_low"] = low
            row[f"{measure}_ci_high"] = high
        rows.append(row)
    result = pd.DataFrame(rows)
    result["level_order"] = result["level"].map({"level1": 1, "level2": 2, "level3": 3})
    return result.sort_values(["level_order", "experiment"]).drop(columns="level_order")


def safe_to_csv(frame: pd.DataFrame, path: Path) -> Path:
    try:
        frame.to_csv(path, index=False)
        return path
    except PermissionError:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        alternative = path.with_name(f"{path.stem}_{timestamp}{path.suffix}")
        frame.to_csv(alternative, index=False)
        return alternative


def write_methods() -> None:
    (OUTPUT_DIR / "methods.md").write_text(
        "# Pooled underlying-and-direct flexible agreement\n\n"
        "Physician underlying and direct codes were pooled into one unique set per record; "
        "experiment underlying and direct codes were pooled in the same way. Contributory "
        "codes were not included. Records were eligible when the physician pooled set was "
        "nonempty at the analysed level. An empty experiment set remained in the denominator "
        "and received zero for all three measures. `00-00-00` was retained at Level 1 and "
        "excluded at Levels 2 and 3.\n\n"
        "Exact-set agreement equals one when the two unique sets are identical. Any-code "
        "overlap equals one when their intersection is nonempty. Jaccard similarity equals "
        "the intersection size divided by the union size. Reported values are record-level "
        "means; percentile 95% confidence intervals use 5,000 bootstrap samples.\n",
        encoding="utf-8",
    )


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    master = pd.read_csv(MASTER_FILE, dtype=str, keep_default_na=False)
    records = calculate_records(master)
    summary = aggregate(records)
    record_path = safe_to_csv(records, OUTPUT_DIR / "pooled_underlying_direct_by_record.csv")
    summary_path = safe_to_csv(summary, OUTPUT_DIR / "pooled_underlying_direct_summary.csv")
    write_methods()
    print(record_path.resolve())
    print(summary_path.resolve())
    print(summary.to_string(index=False))


if __name__ == "__main__":
    main()
