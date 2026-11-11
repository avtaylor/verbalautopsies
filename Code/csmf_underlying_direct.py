from __future__ import annotations

from pathlib import Path

import pandas as pd

from code_frequencies import build_level_names, parse_codebook
from strict_agreement import (
    BLANK,
    CODE_LEVELS,
    CODE_TYPES,
    EXPERIMENTS,
    LEVEL1_ONLY_CODE,
    clean_code,
    code_at_level,
)


MASTER_FILE = Path("outputs") / "agreement_analysis" / "master_normalized_codes.csv"
OUTPUT_DIR = Path("outputs") / "analysis_redo" / "csmf_underlying_direct"


def csmf_metrics(reference: pd.Series, prediction: pd.Series) -> tuple[dict[str, object], pd.DataFrame]:
    reference_nonblank = reference[reference != BLANK]
    prediction_nonblank = prediction[prediction != BLANK]
    labels = sorted(set(reference_nonblank) | set(prediction_nonblank))

    reference_counts = reference_nonblank.value_counts().reindex(labels, fill_value=0)
    prediction_counts = prediction_nonblank.value_counts().reindex(labels, fill_value=0)
    n_reference = int(reference_counts.sum())
    n_prediction = int(prediction_counts.sum())
    reference_fractions = reference_counts / n_reference if n_reference else reference_counts * 0
    prediction_fractions = prediction_counts / n_prediction if n_prediction else prediction_counts * 0

    absolute_errors = (reference_fractions - prediction_fractions).abs()
    sum_absolute_error = float(absolute_errors.sum())
    csmf_similarity = 1 - 0.5 * sum_absolute_error
    minimum_reference_fraction = float(reference_fractions.min()) if len(reference_fractions) else 0.0
    chance_denominator = 2 * (1 - minimum_reference_fraction)
    chance_corrected = (
        1 - sum_absolute_error / chance_denominator if chance_denominator else None
    )

    detail = pd.DataFrame(
        {
            "cause_code": labels,
            "physician_count": reference_counts.values,
            "experiment_count": prediction_counts.values,
            "physician_csmf": reference_fractions.values,
            "experiment_csmf": prediction_fractions.values,
            "csmf_difference": prediction_fractions.values - reference_fractions.values,
            "absolute_csmf_difference": absolute_errors.values,
        }
    )
    summary = {
        "physician_nonblank_records": n_reference,
        "experiment_nonblank_records": n_prediction,
        "experiment_blank_records": int((prediction == BLANK).sum()),
        "n_causes_union": len(labels),
        "sum_absolute_csmf_error": sum_absolute_error,
        "csmf_similarity": csmf_similarity,
        "csmf_accuracy_chance_corrected": chance_corrected,
    }
    return summary, detail


def calculate(master: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    level_names = build_level_names(parse_codebook())
    summary_rows: list[dict[str, object]] = []
    detail_rows: list[dict[str, object]] = []

    for experiment in EXPERIMENTS:
        for code_type in CODE_TYPES:
            physician_column = f"PHY_{code_type}"
            experiment_column = f"{experiment}_{code_type}"
            physician_nonblank = master[master[physician_column].apply(clean_code).notna()].copy()

            for level in CODE_LEVELS:
                eligible = physician_nonblank
                if level != "level1":
                    eligible = physician_nonblank[
                        physician_nonblank[physician_column].apply(clean_code) != LEVEL1_ONLY_CODE
                    ].copy()

                reference = eligible[physician_column].apply(
                    lambda value: code_at_level(clean_code(value), level)
                )
                prediction = eligible[experiment_column].apply(
                    lambda value: (
                        code_at_level(code, level)
                        if (code := clean_code(value))
                        and (level == "level1" or code != LEVEL1_ONLY_CODE)
                        else BLANK
                    )
                )
                summary, detail = csmf_metrics(reference, prediction)
                summary_rows.append(
                    {
                        "experiment": experiment,
                        "code_type": code_type,
                        "level": level,
                        "physician_reference_cohort": len(eligible),
                        **summary,
                    }
                )

                detail.insert(0, "level", level)
                detail.insert(0, "code_type", code_type)
                detail.insert(0, "experiment", experiment)
                detail["cause_name"] = detail["cause_code"].map(level_names[level]).fillna(
                    "Code absent from MEIRU code list"
                )
                detail_rows.extend(detail.to_dict("records"))

    return pd.DataFrame(summary_rows), pd.DataFrame(detail_rows)


def write_methods_note() -> None:
    note = """# CSMF analysis for underlying and direct codes

Underlying and direct causes are analysed separately for EXP1-EXP5 at Levels
1, 2 and 3. The analysis cohort contains records with a nonblank physician code
of the relevant type. `00-00-00` is retained at Level 1 and excluded at Levels
2 and 3. An experiment `00-00-00` is also treated as blank at Levels 2 and 3.

Cause-specific mortality fractions are calculated separately among nonblank
physician and nonblank experiment assignments within the physician-defined
cohort. Consequently, each distribution sums to one; the number of blank
experiment assignments is reported separately.

CSMF similarity is `1 - 0.5 * sum(abs(PHY CSMF - EXP CSMF))`. The output also
retains the project's previously used chance-corrected CSMF accuracy measure.
"""
    (OUTPUT_DIR / "methods.md").write_text(note, encoding="utf-8")


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    master = pd.read_csv(MASTER_FILE, dtype=str)
    summary, detail = calculate(master)

    summary_path = OUTPUT_DIR / "csmf_summary_underlying_direct_all_levels.csv"
    detail_path = OUTPUT_DIR / "csmf_detail_underlying_direct_all_levels.csv"
    summary.to_csv(summary_path, index=False)
    detail.to_csv(detail_path, index=False)
    write_methods_note()

    print(summary_path.resolve())
    print(detail_path.resolve())
    print(summary.to_string(index=False))


if __name__ == "__main__":
    main()
