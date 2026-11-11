from __future__ import annotations

import ast
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd


MASTER_FILE = Path("outputs") / "agreement_analysis" / "master_normalized_codes.csv"
OUTPUT_DIR = Path("outputs") / "analysis_redo" / "flexible_agreement"
EXPERIMENTS = ("EXP1", "EXP2", "EXP3", "EXP4", "EXP5")
PHY_COLUMNS = ("PHY_direct", "PHY_underlying", "PHY_contrib")
BOOTSTRAP_REPLICATES = 5_000
RANDOM_SEED = 20261027
CODE_LEVELS = ("level3", "level2", "level1")
LEVEL1_ONLY_CODE = "00-00-00"


def clean_code(value: object) -> str | None:
    if pd.isna(value):
        return None
    code = str(value).strip()
    if not code or code.lower() in {"nan", "none", "null", "na", "n/a"}:
        return None
    return code


def parse_code_list(value: object) -> set[str]:
    if pd.isna(value):
        return set()
    if isinstance(value, (list, tuple, set)):
        values = value
    else:
        text = str(value).strip()
        if not text:
            return set()
        try:
            parsed = ast.literal_eval(text)
            values = parsed if isinstance(parsed, (list, tuple, set)) else [parsed]
        except (ValueError, SyntaxError):
            values = text.replace(";", ",").split(",")
    return {code for item in values if (code := clean_code(item)) is not None}


def physician_set(row: pd.Series) -> set[str]:
    return {code for col in PHY_COLUMNS if (code := clean_code(row[col])) is not None}


def experiment_set(row: pd.Series, experiment: str) -> set[str]:
    codes = {
        code
        for col in (f"{experiment}_direct", f"{experiment}_underlying")
        if (code := clean_code(row[col])) is not None
    }
    return codes | parse_code_list(row[f"{experiment}_contrib_set"])


def code_at_level(code: str, level: str) -> str:
    parts = code.split("-")
    if level == "level3":
        return "-".join(parts[:3])
    if level == "level2":
        return "-".join(parts[:2])
    if level == "level1":
        return parts[0]
    raise ValueError(f"Unknown code level: {level}")


def set_at_level(codes: set[str], level: str) -> set[str]:
    return {
        code_at_level(code, level)
        for code in codes
        if level == "level1" or code != LEVEL1_ONLY_CODE
    }


def bootstrap_ci(values: np.ndarray, rng: np.random.Generator) -> tuple[float, float]:
    """Percentile bootstrap CI for a record-level mean or binary rate."""
    if len(values) == 0:
        return np.nan, np.nan
    estimates = np.empty(BOOTSTRAP_REPLICATES, dtype=float)
    for i in range(BOOTSTRAP_REPLICATES):
        estimates[i] = rng.choice(values, size=len(values), replace=True).mean()
    low, high = np.quantile(estimates, [0.025, 0.975])
    return float(low), float(high)


def calculate_record_metrics(master: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for _, record in master.iterrows():
        phy_full = physician_set(record)
        for experiment in EXPERIMENTS:
            exp_full = experiment_set(record, experiment)
            for level in CODE_LEVELS:
                phy = set_at_level(phy_full, level)
                exp = set_at_level(exp_full, level)
                # Inclusion depends only on the physician reference. An empty
                # experiment set remains in the denominator as disagreement.
                comparable = bool(phy)
                intersection = phy & exp
                union = phy | exp
                rows.append(
                    {
                        "ident": record["ident"],
                        "experiment": experiment,
                        "level": level,
                        "physician_codes": "; ".join(sorted(phy)),
                        "experiment_codes": "; ".join(sorted(exp)),
                        "n_physician_codes": len(phy),
                        "n_experiment_codes": len(exp),
                        "comparable": comparable,
                        # Set equality ignores order and duplicate occurrences,
                        # but requires the same unique codes.
                        "exact_set_agreement": bool(phy == exp) if comparable else pd.NA,
                        "any_set_overlap": bool(intersection) if comparable else pd.NA,
                        "intersection_size": len(intersection) if comparable else pd.NA,
                        "union_size": len(union) if comparable else pd.NA,
                        "jaccard_similarity": len(intersection) / len(union) if comparable else np.nan,
                    }
                )
    return pd.DataFrame(rows)


def aggregate_metrics(record_metrics: pd.DataFrame) -> pd.DataFrame:
    rng = np.random.default_rng(RANDOM_SEED)
    rows: list[dict[str, object]] = []
    for (experiment, level), group in record_metrics.groupby(["experiment", "level"], sort=False):
        comparable = group[group["comparable"]].copy()
        measures = {
            "exact_set_agreement_rate": comparable["exact_set_agreement"].astype(float).to_numpy(),
            "any_set_overlap_rate": comparable["any_set_overlap"].astype(float).to_numpy(),
            "mean_jaccard_similarity": comparable["jaccard_similarity"].astype(float).to_numpy(),
        }
        row: dict[str, object] = {
            "experiment": experiment,
            "level": level,
            "total_records": len(group),
            "comparable_records": len(comparable),
            "excluded_noncomparable_records": len(group) - len(comparable),
        }
        for name, values in measures.items():
            low, high = bootstrap_ci(values, rng)
            row[name] = float(values.mean()) if len(values) else np.nan
            row[f"{name}_ci_low"] = low
            row[f"{name}_ci_high"] = high
        rows.append(row)
    return pd.DataFrame(rows)


def write_methods_note() -> None:
    note = """# Flexible agreement analysis

For each record, physician direct, underlying, and contributory codes are pooled
into one set. Each experiment's direct, underlying, and contributory codes are
pooled in the same way. Code type, order, and duplicate occurrences are ignored.

Records are included whenever the physician set contains at least one code. An
empty experiment set remains in the denominator and receives zero for exact-set
agreement, any overlap, and Jaccard similarity.

Metrics are calculated at Level 3 (all three two-digit code parts), Level 2
(the first two parts/four digits), and Level 1 (the first part/two digits).

- Exact-set agreement is 1 only when the two sets contain the same unique codes.
- Any-set overlap is 1 when the sets share at least one code.
- Jaccard similarity is intersection size divided by union size.

The recommended primary dataset-level measure is mean per-record Jaccard
similarity. It rewards shared codes while penalizing both missing and extra codes.
Exact-set and any-overlap rates are retained as strict and permissive secondary
measures. All aggregate measures include record-level percentile bootstrap 95%
confidence intervals using 5,000 replicates and a fixed random seed.
"""
    (OUTPUT_DIR / "methods.md").write_text(note, encoding="utf-8")


def safe_to_csv(df: pd.DataFrame, path: Path) -> Path:
    try:
        df.to_csv(path, index=False)
        return path
    except PermissionError:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        versioned_path = path.with_name(f"{path.stem}_{timestamp}{path.suffix}")
        df.to_csv(versioned_path, index=False)
        return versioned_path


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    master = pd.read_csv(MASTER_FILE, dtype=str)
    record_metrics = calculate_record_metrics(master)
    aggregate = aggregate_metrics(record_metrics)

    record_path = OUTPUT_DIR / "flexible_agreement_by_record.csv"
    aggregate_path = OUTPUT_DIR / "flexible_agreement_summary.csv"
    record_path = safe_to_csv(record_metrics, record_path)
    aggregate_path = safe_to_csv(aggregate, aggregate_path)
    write_methods_note()

    print(record_path.resolve())
    print(aggregate_path.resolve())
    print(aggregate.to_string(index=False))


if __name__ == "__main__":
    main()
