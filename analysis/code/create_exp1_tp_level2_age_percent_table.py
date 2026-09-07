from __future__ import annotations

from pathlib import Path

import pandas as pd


OUTPUT_DIR = Path("outputs") / "agreement_analysis"
INPUT_FILE = OUTPUT_DIR / "exp1_true_positive_overlap_level2_top20_by_vatype_age_table.csv"
STRATA = [
    "adult / 15-24",
    "adult / 25-44",
    "adult / 45-64",
    "adult / 65+",
    "child / 0",
    "child / 1-4",
    "child / 5-9",
    "child / 10-14",
    "infant / 0",
]


def main() -> None:
    source = pd.read_csv(INPUT_FILE)
    total_true_positive = float(source["total_true_positive_cases"].sum())
    rows = []

    for _, row in source.iterrows():
        count = int(row["total_true_positive_cases"])
        rows.append(
            {
                "cause_code": row["cause_code"],
                "cause_name": row["cause_name"],
                "total": f"{count} ({count / total_true_positive * 100:.1f}%)",
                **{stratum: row[f"{stratum} %"] for stratum in STRATA},
            }
        )

    table = pd.DataFrame(rows)
    csv_path = OUTPUT_DIR / "exp1_true_positive_overlap_level2_top20_by_vatype_age_percent_table.csv"
    md_path = OUTPUT_DIR / "exp1_true_positive_overlap_level2_top20_by_vatype_age_percent_table.md"
    table.to_csv(csv_path, index=False)

    columns = table.columns.tolist()
    lines = [
        "# EXP1 Level 2 Top 20 True Positive Overlap by VA Type and Age - Percent Table",
        "",
        "| " + " | ".join(columns) + " |",
        "| " + " | ".join(["---"] * len(columns)) + " |",
    ]
    for _, row in table.iterrows():
        lines.append("| " + " | ".join(str(row[col]) for col in columns) + " |")
    md_path.write_text("\n".join(lines), encoding="utf-8")

    print(csv_path.resolve())
    print(md_path.resolve())
    print(table.to_string(index=False))


if __name__ == "__main__":
    main()
