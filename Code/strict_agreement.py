from __future__ import annotations

from pathlib import Path

import pandas as pd


MASTER_FILE = Path("outputs") / "agreement_analysis" / "master_normalized_codes.csv"
OUTPUT_DIR = Path("outputs") / "analysis_redo" / "strict_agreement"
EXPERIMENTS = ("EXP1", "EXP2", "EXP3", "EXP4", "EXP5")
CODE_TYPES = ("direct", "underlying")
CODE_LEVELS = ("level3", "level2", "level1")
BLANK = "BLANK"
LEVEL1_ONLY_CODE = "00-00-00"


def clean_code(value: object) -> str | None:
    if pd.isna(value):
        return None
    code = str(value).strip()
    return code if code and code.lower() not in {"nan", "none", "null", "na", "n/a"} else None


def code_at_level(code: str, level: str) -> str:
    parts = code.split("-")
    if level == "level3":
        return "-".join(parts[:3])
    if level == "level2":
        return "-".join(parts[:2])
    if level == "level1":
        return parts[0]
    raise ValueError(f"Unknown code level: {level}")


def cohen_kappa(reference: list[str], prediction: list[str]) -> float | None:
    n = len(reference)
    if n == 0:
        return None
    observed = sum(true == pred for true, pred in zip(reference, prediction)) / n
    labels = set(reference) | set(prediction)
    expected = sum(
        (reference.count(label) / n) * (prediction.count(label) / n)
        for label in labels
    )
    return (observed - expected) / (1 - expected) if expected < 1 else None


def classification_metrics(reference: list[str], prediction: list[str]) -> dict[str, object]:
    n = len(reference)
    labels = sorted(set(reference) | set(prediction))
    correct = sum(true == pred for true, pred in zip(reference, prediction))
    per_class: list[dict[str, object]] = []

    for label in labels:
        true_positive = sum(true == label and pred == label for true, pred in zip(reference, prediction))
        false_positive = sum(true != label and pred == label for true, pred in zip(reference, prediction))
        false_negative = sum(true == label and pred != label for true, pred in zip(reference, prediction))
        support = sum(true == label for true in reference)
        precision = true_positive / (true_positive + false_positive) if true_positive + false_positive else 0.0
        recall = true_positive / (true_positive + false_negative) if true_positive + false_negative else 0.0
        f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
        per_class.append(
            {
                "label": label,
                "support": support,
                "true_positive": true_positive,
                "false_positive": false_positive,
                "false_negative": false_negative,
                "precision": precision,
                "recall": recall,
                "f1": f1,
            }
        )

    f1_macro = sum(row["f1"] for row in per_class) / len(per_class) if per_class else None
    f1_weighted = (
        sum(row["f1"] * row["support"] for row in per_class) / n if n else None
    )
    return {
        "n_compared": n,
        "n_exact_agreement": correct,
        "accuracy": correct / n if n else None,
        "cohen_kappa": cohen_kappa(reference, prediction),
        "f1_macro": f1_macro,
        "f1_weighted": f1_weighted,
        "n_labels": len(labels),
        "per_class": per_class,
    }


def calculate_strict_agreement(master: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    summary_rows: list[dict[str, object]] = []
    class_rows: list[dict[str, object]] = []

    for experiment in EXPERIMENTS:
        for code_type in CODE_TYPES:
            phy_column = f"PHY_{code_type}"
            exp_column = f"{experiment}_{code_type}"
            eligible = master[master[phy_column].apply(clean_code).notna()].copy()

            for level in CODE_LEVELS:
                level_eligible = eligible
                if level != "level1":
                    level_eligible = eligible[eligible[phy_column].apply(clean_code) != LEVEL1_ONLY_CODE].copy()
                reference = level_eligible[phy_column].apply(
                    lambda value: code_at_level(clean_code(value), level)
                ).tolist()
                prediction = level_eligible[exp_column].apply(
                    lambda value: code_at_level(code, level)
                    if (code := clean_code(value)) and (level == "level1" or code != LEVEL1_ONLY_CODE)
                    else BLANK
                ).tolist()
                metrics = classification_metrics(reference, prediction)
                per_class = metrics.pop("per_class")
                summary_rows.append(
                    {
                        "experiment": experiment,
                        "code_type": code_type,
                        "level": level,
                        "physician_reference_records": len(level_eligible),
                        "experiment_blank_predictions": prediction.count(BLANK),
                        **metrics,
                    }
                )
                for row in per_class:
                    class_rows.append(
                        {
                            "experiment": experiment,
                            "code_type": code_type,
                            "level": level,
                            **row,
                        }
                    )

    return pd.DataFrame(summary_rows), pd.DataFrame(class_rows)


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    master = pd.read_csv(MASTER_FILE, dtype=str)
    summary, per_class = calculate_strict_agreement(master)

    summary_path = OUTPUT_DIR / "strict_agreement_summary.csv"
    class_path = OUTPUT_DIR / "strict_agreement_per_class.csv"
    summary.to_csv(summary_path, index=False)
    per_class.to_csv(class_path, index=False)

    print(summary_path.resolve())
    print(class_path.resolve())
    print(
        summary[
            ["experiment", "code_type", "level", "n_compared", "accuracy", "cohen_kappa", "f1_macro", "f1_weighted"]
        ].to_string(index=False)
    )


if __name__ == "__main__":
    main()
