from __future__ import annotations

import ast
import html
import re
from pathlib import Path

import pandas as pd


DATA_DIR = Path(r"C:\Users\Lenovo\Downloads\MEIRU_VA_EXP")
OUTPUT_DIR = Path("outputs") / "agreement_analysis"
MASTER_FILE = OUTPUT_DIR / "master_normalized_codes.csv"
CODEBOOK_FILE = DATA_DIR / "MEIRU_CODS_LIST.txt"

CODE_PATTERN = re.compile(r"\b(\d{1,2})\s*-\s*(\d{1,2})\s*-\s*(\d{1,2})\b")
LEVELS = ["level1", "level2", "level3"]
VA_TYPE_LABELS = {"1": "adult", "2": "child", "3": "infant"}
SEX_LABELS = {"0": "female", "1": "male", "Female": "female", "Male": "male", "F": "female", "M": "male"}
STRATA = ["adult / female", "adult / male", "child / female", "child / male", "infant / female", "infant / male"]


def canonical_code(groups: tuple[str, str, str]) -> str:
    return "-".join(f"{int(part):02d}" for part in groups)


def parse_codebook() -> pd.DataFrame:
    text = CODEBOOK_FILE.read_text(encoding="utf-8-sig")
    matches = list(CODE_PATTERN.finditer(text))
    rows = []
    for i, match in enumerate(matches):
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        desc = re.sub(r"\s+", " ", text[start:end].replace("|", "", 1).strip())
        rows.append({"code": canonical_code(match.groups()), "description": desc})
    return pd.DataFrame(rows).drop_duplicates("code")


def code_at_level(code: object, level: str) -> str | None:
    if pd.isna(code) or code is None:
        return None
    text = str(code).strip()
    if not text or text.lower() in {"nan", "none", "null", "na", "n/a"}:
        return None
    if level == "level1":
        return text[:2]
    if level == "level2":
        return text[:5]
    if level == "level3":
        return text
    raise ValueError(level)


def code_name(code: str, level: str, codebook: pd.DataFrame) -> str:
    if level == "level1":
        match = codebook[codebook["code"] == f"{code}-00-00"]
        if match.empty:
            match = codebook[codebook["code"].str.startswith(code)]
        return match.iloc[0]["description"].split(":", 1)[0].strip() if not match.empty else "Unknown"
    if level == "level2":
        match = codebook[codebook["code"] == f"{code}-00"]
        if match.empty:
            match = codebook[codebook["code"].str.startswith(code)]
        if match.empty:
            return "Unknown"
        parts = [part.strip() for part in match.iloc[0]["description"].split(":")]
        return parts[1] if len(parts) >= 2 else parts[0]
    match = codebook[codebook["code"] == code]
    return match.iloc[0]["description"] if not match.empty else "Unknown"


def parse_code_list(value: object) -> list[str]:
    if pd.isna(value) or value is None:
        return []
    if isinstance(value, list):
        return [str(x) for x in value if str(x)]
    text = str(value).strip()
    if not text:
        return []
    try:
        parsed = ast.literal_eval(text)
        if isinstance(parsed, list):
            return [str(x) for x in parsed if str(x)]
    except Exception:
        pass
    return [part.strip() for part in text.split(",") if part.strip()]


def singleton(value: object, level: str) -> set[str]:
    code = code_at_level(value, level)
    return {code} if code else set()


def list_set(value: object, level: str) -> set[str]:
    return {code_at_level(code, level) for code in parse_code_list(value) if code_at_level(code, level)}


def phy_set(row: pd.Series, level: str) -> set[str]:
    out = set()
    for col in ["PHY_direct", "PHY_underlying", "PHY_contrib"]:
        out.update(singleton(row[col], level))
    return out


def exp1_set(row: pd.Series, level: str) -> set[str]:
    out = set()
    out.update(singleton(row["EXP1_direct"], level))
    out.update(singleton(row["EXP1_underlying"], level))
    out.update(list_set(row["EXP1_contrib_set"], level))
    return out


def svg_text(x: float, y: float, text: object, size: int = 12, fill: str = "#111827", anchor: str = "start", weight: str = "400") -> str:
    return (
        f'<text x="{x}" y="{y}" text-anchor="{anchor}" font-family="Arial, sans-serif" '
        f'font-size="{size}" font-weight="{weight}" fill="{fill}">{html.escape(str(text))}</text>'
    )


def heat_color(value: float, max_value: float) -> str:
    ratio = min(max(value / max_value, 0), 1) if max_value else 0
    start = (248, 250, 252)
    end = (22, 101, 52)
    rgb = tuple(round(start[i] + (end[i] - start[i]) * ratio) for i in range(3))
    return f"rgb({rgb[0]},{rgb[1]},{rgb[2]})"


def write_heatmap(table: pd.DataFrame, level: str, codebook: pd.DataFrame, top_n: int | None = None, suffix: str | None = None) -> Path:
    counts = table.pivot_table(index="cause_code", columns="stratum", values="n_true_positive_cases", aggfunc="sum").reindex(columns=STRATA).fillna(0)
    percents = table.pivot_table(index="cause_code", columns="stratum", values="percent_of_comparable_cases", aggfunc="sum").reindex(columns=STRATA).fillna(0)
    order = counts.sum(axis=1).sort_values(ascending=False).index.tolist()
    if top_n is not None:
        order = order[:top_n]
    counts = counts.loc[order]
    percents = percents.loc[order]
    labels = {code: f"{code} - {code_name(code, level, codebook)}" for code in order}
    max_value = float(percents.max().max()) if len(percents) else 0.0

    compact = top_n is not None
    cell_w = 112 if compact else 96
    cell_h = 44 if compact else 34
    left = 300 if level == "level1" else 500 if level == "level2" and compact else 420 if level == "level2" else 500
    top = 128
    width = left + cell_w * len(STRATA) + 220
    height = top + cell_h * len(order) + 58
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#ffffff"/>',
        svg_text(24, 32, f"EXP1 True Positive Overlap Codes by VA Type and Sex ({level.upper()}{', Top ' + str(top_n) if top_n else ''})", 22, weight="700"),
        svg_text(24, 54, "Pooled any-type comparison: codes present in both EXP1 and physician code sets. Cells show count and percent of comparable cases.", 12, "#52616b"),
    ]
    for j, stratum in enumerate(STRATA):
        x = left + j * cell_w
        parts.append(svg_text(x + cell_w / 2, top - 14, stratum, 12 if compact else 10, "#111827", "middle", "700"))
    for i, code in enumerate(order):
        y = top + i * cell_h
        fill_row = "#f8fafc" if i % 2 == 0 else "#ffffff"
        parts.append(f'<rect x="16" y="{y}" width="{width - 32}" height="{cell_h}" fill="{fill_row}"/>')
        parts.append(svg_text(left - 14, y + (28 if compact else 22), labels[code][:82 if compact else 76], 13 if compact else 10, "#111827", "end"))
        for j, stratum in enumerate(STRATA):
            x = left + j * cell_w
            pct = float(percents.loc[code, stratum])
            count = int(counts.loc[code, stratum])
            color = heat_color(pct, max_value)
            text_fill = "#ffffff" if max_value and pct / max_value > 0.55 else "#111827"
            parts.append(f'<rect x="{x}" y="{y + 3}" width="{cell_w - 4}" height="{cell_h - 6}" rx="2" fill="{color}"/>')
            parts.append(svg_text(x + cell_w / 2 - 2, y + (19 if compact else 16), count, 13 if compact else 9, text_fill, "middle", "700"))
            parts.append(svg_text(x + cell_w / 2 - 2, y + (36 if compact else 29), f"{pct * 100:.1f}%", 12 if compact else 8, text_fill, "middle"))
    parts.append("</svg>")
    out = OUTPUT_DIR / f"figure_exp1_true_positive_overlap_heatmap_{suffix or level}.svg"
    out.write_text("\n".join(parts), encoding="utf-8")
    return out


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    codebook = parse_codebook()
    master = pd.read_csv(MASTER_FILE, dtype=str)
    master["va_type_label"] = master["vatype"].map(VA_TYPE_LABELS).fillna(master["vatype"])
    master["sex_label"] = master["Sex"].map(SEX_LABELS).fillna(master["Sex"])
    master["stratum"] = master["va_type_label"].fillna("missing_va_type") + " / " + master["sex_label"].fillna("missing_sex")

    rows = []
    case_rows = []
    for level in LEVELS:
        denominators = {stratum: 0 for stratum in STRATA}
        counts: dict[tuple[str, str], int] = {}
        for _, row in master.iterrows():
            stratum = row["stratum"]
            if stratum not in STRATA:
                continue
            phy = phy_set(row, level)
            if not phy:
                continue
            denominators[stratum] += 1
            llm = exp1_set(row, level)
            overlap = sorted(phy & llm)
            for code in overlap:
                counts[(code, stratum)] = counts.get((code, stratum), 0) + 1
                case_rows.append(
                    {
                        "level": level,
                        "ident": row["ident"],
                        "stratum": stratum,
                        "true_positive_code": code,
                        "true_positive_name": code_name(code, level, codebook),
                    }
                )
        for (code, stratum), count in counts.items():
            rows.append(
                {
                    "level": level,
                    "cause_code": code,
                    "cause_name": code_name(code, level, codebook),
                    "stratum": stratum,
                    "n_true_positive_cases": count,
                    "denominator_comparable_cases": denominators[stratum],
                    "percent_of_comparable_cases": count / denominators[stratum] if denominators[stratum] else None,
                }
            )
    summary = pd.DataFrame(rows)
    cases = pd.DataFrame(case_rows)
    summary.to_csv(OUTPUT_DIR / "exp1_true_positive_overlap_summary_by_level_va_type_sex.csv", index=False)
    cases.to_csv(OUTPUT_DIR / "exp1_true_positive_overlap_cases_by_level.csv", index=False)
    paths = [write_heatmap(summary[summary["level"] == level], level, codebook) for level in LEVELS]
    paths.append(write_heatmap(summary[summary["level"] == "level2"], "level2", codebook, top_n=20, suffix="level2_top20"))
    pd.DataFrame({"figure": [p.name for p in paths], "path": [str(p.resolve()) for p in paths]}).to_csv(
        OUTPUT_DIR / "exp1_true_positive_overlap_heatmap_index.csv",
        index=False,
    )
    print((OUTPUT_DIR / "exp1_true_positive_overlap_summary_by_level_va_type_sex.csv").resolve())
    print((OUTPUT_DIR / "exp1_true_positive_overlap_cases_by_level.csv").resolve())
    for path in paths:
        print(path.resolve())


if __name__ == "__main__":
    main()
