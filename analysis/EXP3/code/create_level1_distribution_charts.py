from __future__ import annotations

import html
import re
from pathlib import Path

import pandas as pd

from analysis_llm_phy_agreement import load_experiment


DATA_DIR = Path(r"C:\Users\Lenovo\Downloads\MEIRU_VA_EXP")
OUTPUT_DIR = Path("outputs") / "agreement_analysis"

CODEBOOK_FILE = DATA_DIR / "MEIRU_CODS_LIST.txt"
PHY_FILE = DATA_DIR / "PHY.xlsx"
AGE_SEX_FILE = DATA_DIR / "age_sex.csv"
VA_TYPE_FILE = DATA_DIR / "va_type.csv"

CODE_PATTERN = re.compile(r"\b(\d{1,2})\s*-\s*(\d{1,2})\s*-\s*(\d{1,2})\b")
EXPERIMENTS = ["EXP1", "EXP2", "EXP3", "EXP4"]

VA_TYPE_LABELS = {
    "1": "adults",
    "2": "children",
    "3": "infants",
}

AGE_BANDS = {
    "adults": {
        "bins": [14, 24, 44, 64, 200],
        "labels": ["15-24", "25-44", "45-64", "65+"],
    },
    "children": {
        "bins": [-1, 0, 4, 9, 14, 15],
        "labels": ["0", "1-4", "5-9", "10-14", "15"],
    },
    "infants": {
        "bins": [-1, 0],
        "labels": ["0"],
    },
    "overall": {
        "bins": [-1, 0, 4, 9, 14, 24, 44, 64, 200],
        "labels": ["0", "1-4", "5-9", "10-14", "15-24", "25-44", "45-64", "65+"],
    },
}

LEVEL1_COLORS = {
    "00": "#9aa5b1",
    "01": "#f97068",
    "02": "#7fb800",
    "03": "#b76ef0",
    "04": "#08b8b8",
    "05": "#f4b942",
    "99": "#5c677d",
}


def canonical_code(groups: tuple[str, str, str]) -> str:
    return "-".join(f"{int(part):02d}" for part in groups)


def parse_codebook() -> tuple[pd.DataFrame, dict[str, str]]:
    text = CODEBOOK_FILE.read_text(encoding="utf-8-sig")
    matches = list(CODE_PATTERN.finditer(text))
    rows = []
    for i, match in enumerate(matches):
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        desc = re.sub(r"\s+", " ", text[start:end].replace("|", "", 1).strip())
        rows.append({"code": canonical_code(match.groups()), "description": desc})
    codebook = pd.DataFrame(rows).drop_duplicates("code")

    compact_lookup: dict[str, str] = {}
    for code in codebook["code"]:
        a, b, c = [int(x) for x in code.split("-")]
        candidates = {code, code.replace("-", ""), f"{a}{b}{c}", f"{a:02d}{b:02d}{c:02d}"}
        if c == 0:
            candidates.add(f"{a}{b}0")
        if b == 99 and c == 0:
            candidates.add(f"{a}99")
        if c == 99:
            candidates.add(f"{a}{b}99")
        if a == 99 and b == 0 and c == 0:
            candidates.update({"99", "990", "9900"})
        for candidate in candidates:
            compact_lookup.setdefault(candidate, code)
    return codebook, compact_lookup


def normalize_code(value: object, compact_lookup: dict[str, str]) -> str | None:
    if pd.isna(value):
        return None
    raw = str(value).strip()
    if not raw or raw.lower() in {"nan", "none", "null", "na", "n/a"}:
        return None
    match = CODE_PATTERN.search(raw)
    if match:
        code = canonical_code(match.groups())
        return compact_lookup.get(code, code)
    digits = re.sub(r"\D", "", raw)
    if digits in compact_lookup:
        return compact_lookup[digits]
    if len(digits) == 6:
        code = f"{digits[:2]}-{digits[2:4]}-{digits[4:6]}"
        return compact_lookup.get(code, code)
    return None


def level1_name(level1: str, codebook: pd.DataFrame) -> str:
    exact = codebook[codebook["code"] == f"{level1}-00-00"]
    if not exact.empty:
        return exact.iloc[0]["description"].split(":", 1)[0].strip()
    matches = codebook[codebook["code"].str.startswith(level1)]
    if matches.empty:
        return f"Level {level1}"
    return matches.iloc[0]["description"].split(":", 1)[0].strip()


def load_source(source: str, compact_lookup: dict[str, str]) -> pd.DataFrame:
    if source == "physician":
        phy = pd.read_excel(PHY_FILE, sheet_name="PHY", dtype=str)
        df = phy[["ident", "PHYSICIAN_UNDERLYING_CODES"]].copy()
        df["underlying_code"] = df["PHYSICIAN_UNDERLYING_CODES"].apply(lambda x: normalize_code(x, compact_lookup))
        return df[["ident", "underlying_code"]]

    exp = source.upper()
    df = load_experiment(exp, compact_lookup)[["ident", f"{exp}_underlying"]].rename(
        columns={f"{exp}_underlying": "underlying_code"}
    )
    return df


def prepare_source(source: str, compact_lookup: dict[str, str]) -> pd.DataFrame:
    age = pd.read_csv(AGE_SEX_FILE, dtype=str)
    va_type = pd.read_csv(VA_TYPE_FILE, dtype=str)
    df = load_source(source, compact_lookup)
    df["ident"] = df["ident"].astype(str).str.strip()
    df = df.merge(age[["ident", "Age"]], on="ident", how="left", validate="one_to_one")
    df = df.merge(va_type[["ident", "vatype"]], on="ident", how="left", validate="one_to_one")
    df = df[df["underlying_code"].notna()].copy()
    df["Age_num"] = pd.to_numeric(df["Age"], errors="coerce")
    df["level1"] = df["underlying_code"].str[:2]
    return df


def add_age_group(df: pd.DataFrame, group_name: str) -> pd.DataFrame:
    spec = AGE_BANDS[group_name]
    out = df.copy()
    out["age_group"] = pd.cut(out["Age_num"], bins=spec["bins"], labels=spec["labels"]).astype(str)
    return out[out["age_group"].isin(spec["labels"])].copy()


def distribution_table(df: pd.DataFrame, group_name: str, codebook: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    columns = AGE_BANDS[group_name]["labels"]
    counts = pd.crosstab(df["age_group"], df["level1"]).reindex(index=columns, fill_value=0)
    counts = counts.loc[counts.sum(axis=1) > 0]
    used_codes = sorted([col for col in counts.columns if counts[col].sum() > 0])
    counts = counts[used_codes]
    props = counts.div(counts.sum(axis=1).replace(0, pd.NA), axis=0).fillna(0)

    label_map = {code: level1_name(code, codebook) for code in used_codes}
    counts = counts.rename(columns=label_map)
    props = props.rename(columns=label_map)
    return counts, props


def write_stacked_svg(props: pd.DataFrame, counts: pd.DataFrame, title: str, output: Path) -> None:
    width = 1000
    height = 560
    margin_left = 95
    margin_right = 300
    margin_top = 96
    margin_bottom = 90
    plot_w = width - margin_left - margin_right
    plot_h = height - margin_top - margin_bottom
    bar_gap = 18
    n = max(len(props.index), 1)
    bar_w = (plot_w - bar_gap * (n - 1)) / n
    causes = list(props.columns)
    code_by_name = {level1_name(code, pd.DataFrame()): code for code in []}

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#ffffff"/>',
        f'<text x="{margin_left}" y="32" font-family="Arial, sans-serif" font-size="24" fill="#111827">{html.escape(title)}</text>',
    ]

    for tick in [0, 0.25, 0.5, 0.75, 1.0]:
        y = margin_top + plot_h * (1 - tick)
        parts.append(f'<line x1="{margin_left}" y1="{y}" x2="{margin_left + plot_w}" y2="{y}" stroke="#e5e7eb" stroke-width="1"/>')
        parts.append(
            f'<text x="{margin_left - 12}" y="{y + 4}" text-anchor="end" font-family="Arial, sans-serif" font-size="14" fill="#374151">{int(tick * 100)}%</text>'
        )

    minor_ticks = [0.125, 0.375, 0.625, 0.875]
    for tick in minor_ticks:
        y = margin_top + plot_h * (1 - tick)
        parts.append(f'<line x1="{margin_left}" y1="{y}" x2="{margin_left + plot_w}" y2="{y}" stroke="#f1f5f9" stroke-width="1"/>')

    for i, age_group in enumerate(props.index):
        x = margin_left + i * (bar_w + bar_gap)
        y_cursor = margin_top + plot_h
        for cause in causes:
            value = float(props.loc[age_group, cause])
            if value <= 0:
                continue
            h = value * plot_h
            y = y_cursor - h
            color = LEVEL1_COLORS.get(level1_code_from_name(cause), "#94a3b8")
            parts.append(f'<rect x="{x}" y="{y}" width="{bar_w}" height="{h}" fill="{color}"/>')
            if h >= 22 and value >= 0.035:
                label_color = "#ffffff" if value >= 0.16 else "#111827"
                parts.append(
                    f'<text x="{x + bar_w / 2}" y="{y + h / 2 + 4}" text-anchor="middle" font-family="Arial, sans-serif" font-size="12" font-weight="700" fill="{label_color}">{value * 100:.0f}%</text>'
                )
            y_cursor = y
        parts.append(
            f'<text x="{x + bar_w / 2}" y="{margin_top + plot_h + 28}" text-anchor="middle" font-family="Arial, sans-serif" font-size="14" fill="#1f2937">{html.escape(str(age_group))}</text>'
        )

    parts.append(
        f'<text x="{margin_left + plot_w / 2}" y="{height - 30}" text-anchor="middle" font-family="Arial, sans-serif" font-size="20" fill="#111827">Age group</text>'
    )
    parts.append(
        f'<text x="24" y="{margin_top + plot_h / 2}" transform="rotate(-90 24,{margin_top + plot_h / 2})" text-anchor="middle" font-family="Arial, sans-serif" font-size="20" fill="#111827">Proportion</text>'
    )

    legend_x = margin_left + plot_w + 35
    legend_y = margin_top + 70
    parts.append(
        f'<text x="{legend_x}" y="{legend_y - 22}" font-family="Arial, sans-serif" font-size="18" fill="#111827">Level 1 cause</text>'
    )
    for i, cause in enumerate(causes):
        y = legend_y + i * 28
        color = LEVEL1_COLORS.get(level1_code_from_name(cause), "#94a3b8")
        parts.append(f'<rect x="{legend_x}" y="{y - 14}" width="22" height="22" fill="{color}"/>')
        parts.append(
            f'<text x="{legend_x + 34}" y="{y + 2}" font-family="Arial, sans-serif" font-size="14" fill="#111827">{html.escape(cause)}</text>'
        )

    parts.append("</svg>")
    output.write_text("\n".join(parts), encoding="utf-8")


def level1_code_from_name(name: str) -> str:
    mapping = {
        "Unspecifiable": "00",
        "Communicable disease": "01",
        "Direct maternal cause": "02",
        "Non communicable disease": "03",
        "External cause": "04",
        "Causes specific to infancy": "05",
        "Other specific unlisted": "99",
    }
    return mapping.get(name, "")


def write_source_group(source: str, df: pd.DataFrame, group_name: str, codebook: pd.DataFrame) -> None:
    grouped = add_age_group(df, group_name)
    counts, props = distribution_table(grouped, group_name, codebook)
    if counts.empty:
        return
    safe_source = source.lower()
    counts.to_csv(OUTPUT_DIR / f"{safe_source}_underlying_level1_distribution_counts_{group_name}.csv")
    (props * 100).round(2).to_csv(OUTPUT_DIR / f"{safe_source}_underlying_level1_distribution_percent_{group_name}.csv")
    title_source = "Physician" if source == "physician" else source.upper()
    title_group = "Adults" if group_name == "adults" else group_name.title()
    write_stacked_svg(
        props,
        counts,
        f"Distribution of {title_source} Level 1 Causes by Age Group: {title_group}",
        OUTPUT_DIR / f"{safe_source}_underlying_level1_distribution_stacked_bar_{group_name}.svg",
    )


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    codebook, compact_lookup = parse_codebook()
    sources = ["physician", "exp1", "exp2", "exp3", "exp4"]
    for source in sources:
        df = prepare_source(source, compact_lookup)
        for group_name, vatype in [("overall", None), ("adults", "1"), ("children", "2"), ("infants", "3")]:
            subset = df if vatype is None else df[df["vatype"] == vatype].copy()
            write_source_group(source, subset, group_name, codebook)

    for file in sorted(OUTPUT_DIR.glob("*_underlying_level1_distribution_stacked_bar_*.svg")):
        print(file.resolve())


if __name__ == "__main__":
    main()
