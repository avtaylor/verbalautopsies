from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

from analysis_llm_phy_agreement import DATA_DIR, OUTPUT_DIR, load_phy, parse_codebook


VA_TYPE_LABELS = {"1": "Adult", "2": "Child", "3": "Neonate"}
VA_TYPES = ["Adult", "Child", "Neonate"]
CODE_PATTERN = re.compile(r"\b(\d{1,2})\s*-\s*(\d{1,2})\s*-\s*(\d{1,2})\b")


def level1_name(code: str) -> str:
    names = {
        "00": "Unspecified",
        "01": "Communicable disease",
        "02": "Direct maternal cause",
        "03": "Non communicable disease",
        "04": "External cause",
        "05": "Causes specific to infancy",
        "99": "Other",
    }
    return names.get(code, "Unknown")


def level2_name(code: str, codebook: pd.DataFrame) -> str:
    exact = codebook[codebook["code"].eq(f"{code}-00")]
    match = exact if not exact.empty else codebook[codebook["code"].str.startswith(code)]
    if match.empty:
        return "Unknown"
    parts = [part.strip() for part in match.iloc[0]["description"].split(":")]
    return parts[1] if len(parts) >= 2 else parts[0]


def add_distribution_rows(
    rows: list[dict[str, object]],
    data: pd.DataFrame,
    level: str,
    codebook: pd.DataFrame,
) -> None:
    code_col = f"{level}_code"
    name_func = level1_name if level == "level1" else lambda code: level2_name(code, codebook)
    order = data.groupby(code_col).size().sort_values(ascending=False).index.tolist()

    for code in order:
        row = {
            "level": "Level 1" if level == "level1" else "Level 2",
            "cause_code": code,
            "cause_name": name_func(code),
        }
        for va_type in VA_TYPES:
            sub = data[data["va_type"] == va_type]
            denom = len(sub)
            n = int((sub[code_col] == code).sum())
            row[f"{va_type}_n"] = n
            row[f"{va_type}_percent"] = round(n / denom * 100, 1) if denom else 0.0
        rows.append(row)


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    codebook, compact_lookup = parse_codebook()
    phy = load_phy(compact_lookup)
    va_type = pd.read_csv(DATA_DIR / "va_type.csv", dtype=str)
    va_type["ident"] = va_type["ident"].astype(str).str.strip()
    va_type["va_type"] = va_type["vatype"].map(VA_TYPE_LABELS).fillna(va_type["vatype"])

    phy = phy[phy["PHY_underlying"].notna()].copy()
    phy["ident"] = phy["ident"].astype(str).str.strip()
    phy = phy.merge(va_type[["ident", "va_type"]], on="ident", how="left")
    phy = phy[phy["va_type"].isin(VA_TYPES)].copy()
    phy["level1_code"] = phy["PHY_underlying"].str[:2]
    phy["level2_code"] = phy["PHY_underlying"].str[:5]

    rows: list[dict[str, object]] = []
    add_distribution_rows(rows, phy, "level1", codebook)
    add_distribution_rows(rows, phy, "level2", codebook)

    table = pd.DataFrame(rows)
    csv_path = OUTPUT_DIR / "phy_underlying_distribution_level1_level2_by_vatype.csv"
    md_path = OUTPUT_DIR / "phy_underlying_distribution_level1_level2_by_vatype.md"
    table.to_csv(csv_path, index=False)

    columns = table.columns.tolist()
    lines = [
        "# Physician Underlying COD Distribution by VA Type",
        "",
        "Percentages are column-wise within each VA type among records with physician underlying codes.",
        "",
        "| " + " | ".join(columns) + " |",
        "| " + " | ".join(["---"] * len(columns)) + " |",
    ]
    for _, row in table.iterrows():
        lines.append("| " + " | ".join(str(row[col]) for col in columns) + " |")
    md_path.write_text("\n".join(lines), encoding="utf-8")

    print(csv_path.resolve())
    print(md_path.resolve())
    print(
        table.to_string(
            index=False,
            formatters={
                "Adult_percent": "{:.1f}".format,
                "Child_percent": "{:.1f}".format,
                "Neonate_percent": "{:.1f}".format,
            },
        )
    )


if __name__ == "__main__":
    main()
