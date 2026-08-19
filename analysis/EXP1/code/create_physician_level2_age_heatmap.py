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

CODE_PATTERN = re.compile(r"\b(\d{1,2})\s*-\s*(\d{1,2})\s*-\s*(\d{1,2})\b")
AGE_GROUPS = ["0", "1-4", "5-9", "10-14", "15-24", "25-44", "45-64", "65+"]
AGE_BANDS_BY_VA_TYPE = {
    "adult": {
        "bins": [14, 24, 44, 64, 200],
        "labels": ["15-24", "25-44", "45-64", "65+"],
    },
    "child": {
        "bins": [-1, 0, 4, 9, 14],
        "labels": ["0", "1-4", "5-9", "10-14"],
    },
    "infant": {
        "bins": [-1, 0],
        "labels": ["0"],
    },
}
VA_TYPE_LABELS = {
    "1": "adult",
    "2": "child",
    "3": "infant",
}
EXPERIMENTS = ["EXP1", "EXP2", "EXP3", "EXP4"]


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


def codebook_description(code: str, codebook: pd.DataFrame) -> str:
    exact = codebook[codebook["code"] == code]
    if exact.empty:
        return "Unknown"
    return exact.iloc[0]["description"]


def level2_description(level2: str, codebook: pd.DataFrame) -> str:
    matches = codebook[codebook["code"].str.startswith(level2)]
    if matches.empty:
        return "Unknown"
    exact_code = f"{level2}-00"
    exact = codebook[codebook["code"] == exact_code]
    first = exact.iloc[0]["description"] if not exact.empty else matches.iloc[0]["description"]
    parts = [part.strip() for part in first.split(":")]
    if len(parts) >= 2:
        return parts[1]
    return parts[0]


def color_for(value: float, max_value: float) -> str:
    if max_value <= 0:
        intensity = 0.0
    else:
        intensity = min(max(value / max_value, 0.0), 1.0)
    # White to teal-blue.
    start = (247, 251, 252)
    end = (21, 101, 112)
    rgb = tuple(round(start[i] + (end[i] - start[i]) * intensity) for i in range(3))
    return f"rgb({rgb[0]},{rgb[1]},{rgb[2]})"


def text_color(value: float, max_value: float) -> str:
    return "#ffffff" if max_value > 0 and value / max_value > 0.55 else "#1f2933"


def delta_color(value: float, max_abs: float) -> str:
    if max_abs <= 0:
        return "rgb(250,250,250)"
    ratio = min(abs(value) / max_abs, 1.0)
    neutral = (250, 250, 250)
    # Blue means LLM higher; red means physician higher.
    target = (38, 116, 169) if value > 0 else (184, 73, 63)
    rgb = tuple(round(neutral[i] + (target[i] - neutral[i]) * ratio) for i in range(3))
    return f"rgb({rgb[0]},{rgb[1]},{rgb[2]})"


def delta_text_color(value: float, max_abs: float) -> str:
    return "#ffffff" if max_abs > 0 and abs(value) / max_abs > 0.55 else "#1f2933"


def write_svg(
    counts: pd.DataFrame,
    percents: pd.DataFrame,
    labels: list[str],
    columns: list[str],
    title: str,
    subtitle: str,
    output: Path,
) -> None:
    cell_w = 92
    cell_h = 38
    label_w = 520
    top_h = 140
    right_pad = 34
    bottom_pad = 40
    width = label_w + cell_w * len(columns) + right_pad
    height = top_h + cell_h * len(labels) + bottom_pad
    max_pct = float(percents.max().max()) if len(percents) else 0.0

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#ffffff"/>',
        f'<text x="24" y="32" font-family="Arial, sans-serif" font-size="20" font-weight="700" fill="#172026">{html.escape(title)}</text>',
        f'<text x="24" y="56" font-family="Arial, sans-serif" font-size="12" fill="#52616b">{html.escape(subtitle)}</text>',
        '<text x="24" y="88" font-family="Arial, sans-serif" font-size="12" font-weight="700" fill="#172026">Cause code / name</text>',
    ]

    for i, age_group in enumerate(columns):
        x = label_w + i * cell_w
        parts.append(
            f'<text x="{x + cell_w / 2}" y="88" text-anchor="middle" font-family="Arial, sans-serif" font-size="12" font-weight="700" fill="#172026">{html.escape(age_group)}</text>'
        )

    for r, label in enumerate(labels):
        y = top_h + r * cell_h
        fill = "#f8fafb" if r % 2 == 0 else "#ffffff"
        parts.append(f'<rect x="18" y="{y}" width="{width - 36}" height="{cell_h}" fill="{fill}"/>')
        parts.append(
            f'<text x="24" y="{y + 24}" font-family="Arial, sans-serif" font-size="11" fill="#172026">{html.escape(label)}</text>'
        )
        level2 = label.split(" ", 1)[0]
        for c, age_group in enumerate(columns):
            x = label_w + c * cell_w
            pct = float(percents.loc[level2, age_group]) if level2 in percents.index else 0.0
            count = int(counts.loc[level2, age_group]) if level2 in counts.index else 0
            color = color_for(pct, max_pct)
            tcolor = text_color(pct, max_pct)
            parts.append(f'<rect x="{x}" y="{y + 3}" width="{cell_w - 4}" height="{cell_h - 6}" rx="2" fill="{color}"/>')
            parts.append(
                f'<text x="{x + cell_w / 2 - 2}" y="{y + 18}" text-anchor="middle" font-family="Arial, sans-serif" font-size="10" font-weight="700" fill="{tcolor}">{count}</text>'
            )
            parts.append(
                f'<text x="{x + cell_w / 2 - 2}" y="{y + 31}" text-anchor="middle" font-family="Arial, sans-serif" font-size="9" fill="{tcolor}">{pct:.1f}%</text>'
            )

    parts.append("</svg>")
    output.write_text("\n".join(parts), encoding="utf-8")


def write_delta_svg(delta: pd.DataFrame, labels: list[str], columns: list[str], title: str, output: Path) -> None:
    cell_w = 92
    cell_h = 34
    label_w = 520
    top_h = 140
    right_pad = 34
    bottom_pad = 40
    width = label_w + cell_w * len(columns) + right_pad
    height = top_h + cell_h * len(labels) + bottom_pad
    max_abs = float(delta.abs().max().max()) if len(delta) else 0.0
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#ffffff"/>',
        f'<text x="24" y="32" font-family="Arial, sans-serif" font-size="20" font-weight="700" fill="#172026">{html.escape(title)}</text>',
        '<text x="24" y="56" font-family="Arial, sans-serif" font-size="12" fill="#52616b">Cells show percentage-point difference: LLM minus physician. Blue = LLM higher; red = physician higher.</text>',
        '<text x="24" y="88" font-family="Arial, sans-serif" font-size="12" font-weight="700" fill="#172026">Cause code / name</text>',
    ]
    for i, age_group in enumerate(columns):
        x = label_w + i * cell_w
        parts.append(
            f'<text x="{x + cell_w / 2}" y="88" text-anchor="middle" font-family="Arial, sans-serif" font-size="12" font-weight="700" fill="#172026">{html.escape(age_group)}</text>'
        )
    for r, label in enumerate(labels):
        y = top_h + r * cell_h
        fill = "#f8fafb" if r % 2 == 0 else "#ffffff"
        parts.append(f'<rect x="18" y="{y}" width="{width - 36}" height="{cell_h}" fill="{fill}"/>')
        parts.append(
            f'<text x="24" y="{y + 22}" font-family="Arial, sans-serif" font-size="11" fill="#172026">{html.escape(label)}</text>'
        )
        code = label.split(" ", 1)[0]
        for c, age_group in enumerate(columns):
            x = label_w + c * cell_w
            value = float(delta.loc[code, age_group]) if code in delta.index else 0.0
            color = delta_color(value, max_abs)
            tcolor = delta_text_color(value, max_abs)
            parts.append(f'<rect x="{x}" y="{y + 3}" width="{cell_w - 4}" height="{cell_h - 6}" rx="2" fill="{color}"/>')
            parts.append(
                f'<text x="{x + cell_w / 2 - 2}" y="{y + 22}" text-anchor="middle" font-family="Arial, sans-serif" font-size="10" font-weight="700" fill="{tcolor}">{value:+.1f}</text>'
            )
    parts.append("</svg>")
    output.write_text("\n".join(parts), encoding="utf-8")


def build_tables(
    df: pd.DataFrame,
    codebook: pd.DataFrame,
    code_level: str,
) -> tuple[pd.DataFrame, pd.DataFrame, list[str], list[str]]:
    if code_level == "level2":
        df = df.copy()
        df["cause_level"] = df["underlying_code"].str[:5]
        name_col = "level2_name"
        label_rows = [
            {
                "cause_code": cause,
                name_col: level2_description(cause, codebook),
            }
            for cause in sorted(df["cause_level"].dropna().unique())
        ]
    elif code_level == "level3":
        df = df.copy()
        df["cause_level"] = df["underlying_code"]
        name_col = "level3_name"
        label_rows = [
            {
                "cause_code": cause,
                name_col: codebook_description(cause, codebook),
            }
            for cause in sorted(df["cause_level"].dropna().unique())
        ]
    else:
        raise ValueError(f"Unsupported code_level: {code_level}")

    counts = pd.crosstab(df["cause_level"], df["age_group"]).reindex(columns=AGE_GROUPS, fill_value=0)
    counts = counts.loc[counts.sum(axis=1).sort_values(ascending=False).index]
    columns = [col for col in AGE_GROUPS if counts[col].sum() > 0]
    counts = counts[columns]
    percents = counts.div(counts.sum(axis=0).replace(0, pd.NA), axis=1).fillna(0) * 100

    label_df = pd.DataFrame(label_rows)
    label_df["total"] = label_df["cause_code"].map(counts.sum(axis=1).to_dict()).fillna(0).astype(int)
    label_df = label_df[label_df["total"] > 0].sort_values("total", ascending=False)
    counts = counts.loc[label_df["cause_code"]]
    percents = percents.loc[label_df["cause_code"]]
    labels = [f"{row.cause_code} - {getattr(row, name_col)}" for row in label_df.itertuples(index=False)]

    counts_out = label_df.merge(counts.reset_index().rename(columns={"cause_level": "cause_code"}), on="cause_code", how="left")
    pct_out = label_df.merge(
        percents.round(2).reset_index().rename(columns={"cause_level": "cause_code"}),
        on="cause_code",
        how="left",
    )
    return counts_out, pct_out, labels, columns


def write_heatmap_set(
    df: pd.DataFrame,
    codebook: pd.DataFrame,
    code_level: str,
    suffix: str,
    title: str,
    file_prefix: str,
    subtitle_prefix: str,
) -> None:
    counts_out, pct_out, labels, columns = build_tables(df, codebook, code_level)
    count_cols = ["cause_code"] + [c for c in counts_out.columns if c in columns]
    counts = counts_out[count_cols].set_index("cause_code")
    percents = pct_out[count_cols].set_index("cause_code")
    counts_out.to_csv(OUTPUT_DIR / f"{file_prefix}_underlying_{code_level}_age_group_counts_{suffix}.csv", index=False)
    pct_out.to_csv(OUTPUT_DIR / f"{file_prefix}_underlying_{code_level}_age_group_percent_within_age_{suffix}.csv", index=False)
    write_svg(
        counts,
        percents,
        labels,
        columns,
        title,
        f"{subtitle_prefix} underlying cause only. Cells show count and percent within each age group; color intensity follows percent.",
        OUTPUT_DIR / f"{file_prefix}_underlying_{code_level}_age_group_heatmap_{suffix}.svg",
    )


def add_age_type(df: pd.DataFrame, age: pd.DataFrame, va_type: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["ident"] = df["ident"].astype(str).str.strip()
    df = df.merge(age[["ident", "Age"]], on="ident", how="left", validate="one_to_one")
    df = df.merge(va_type[["ident", "vatype"]], on="ident", how="left", validate="one_to_one")
    df = df[df["underlying_code"].notna()].copy()
    df["Age_num"] = pd.to_numeric(df["Age"], errors="coerce")
    df["va_type_label"] = df["vatype"].map(VA_TYPE_LABELS).fillna(df["vatype"])
    for label, spec in AGE_BANDS_BY_VA_TYPE.items():
        mask = df["va_type_label"] == label
        df.loc[mask, "age_group"] = pd.cut(
            df.loc[mask, "Age_num"],
            bins=spec["bins"],
            labels=spec["labels"],
        ).astype(str)
    return df[df["age_group"].isin(AGE_GROUPS)].copy()


def write_all_heatmaps_for_source(
    df: pd.DataFrame,
    codebook: pd.DataFrame,
    file_prefix: str,
    title_prefix: str,
    subtitle_prefix: str,
) -> None:
    for code_level in ["level2", "level3"]:
        write_heatmap_set(
            df,
            codebook,
            code_level,
            "overall",
            f"{title_prefix} Underlying Cause Distribution by Age Group ({code_level.upper()}, Overall)",
            file_prefix,
            subtitle_prefix,
        )
        for vatype, label in VA_TYPE_LABELS.items():
            subset = df[df["vatype"] == vatype].copy()
            write_heatmap_set(
                subset,
                codebook,
                code_level,
                label,
                f"{title_prefix} Underlying Cause Distribution by Age Group ({code_level.upper()}, {label.title()} VA)",
                file_prefix,
                subtitle_prefix,
            )


def label_for_code(code: str, codebook: pd.DataFrame, code_level: str) -> str:
    if code_level == "level2":
        return f"{code} - {level2_description(code, codebook)}"
    return f"{code} - {codebook_description(code, codebook)}"


def write_delta_heatmap(exp: str, codebook: pd.DataFrame, code_level: str, suffix: str) -> None:
    phy_path = OUTPUT_DIR / f"physician_underlying_{code_level}_age_group_percent_within_age_{suffix}.csv"
    exp_path = OUTPUT_DIR / f"{exp.lower()}_underlying_{code_level}_age_group_percent_within_age_{suffix}.csv"
    if not phy_path.exists() or not exp_path.exists():
        return
    phy = pd.read_csv(phy_path)
    llm = pd.read_csv(exp_path)
    columns = [col for col in AGE_GROUPS if col in phy.columns or col in llm.columns]
    phy_pct = phy.set_index("cause_code").reindex(columns=columns).fillna(0)
    llm_pct = llm.set_index("cause_code").reindex(columns=columns).fillna(0)
    all_codes = sorted(set(phy_pct.index) | set(llm_pct.index))
    phy_pct = phy_pct.reindex(all_codes).fillna(0)
    llm_pct = llm_pct.reindex(all_codes).fillna(0)
    delta = llm_pct - phy_pct
    order = delta.abs().sum(axis=1).sort_values(ascending=False).index
    delta = delta.loc[order]
    labels = [label_for_code(code, codebook, code_level) for code in delta.index]
    out_csv = OUTPUT_DIR / f"{exp.lower()}_vs_physician_underlying_{code_level}_age_group_percent_point_delta_{suffix}.csv"
    delta.round(2).reset_index(names="cause_code").to_csv(out_csv, index=False)
    write_delta_svg(
        delta,
        labels,
        columns,
        f"{exp} vs Physician Underlying Cause Distribution Difference ({code_level.upper()}, {suffix.title()})",
        OUTPUT_DIR / f"{exp.lower()}_vs_physician_underlying_{code_level}_age_group_delta_heatmap_{suffix}.svg",
    )


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    codebook, compact_lookup = parse_codebook()
    phy = pd.read_excel(PHY_FILE, sheet_name="PHY", dtype=str)
    age = pd.read_csv(AGE_SEX_FILE, dtype=str)
    va_type = pd.read_csv(DATA_DIR / "va_type.csv", dtype=str)

    df = phy[["ident", "PHYSICIAN_UNDERLYING_CODES"]].copy()
    df["ident"] = df["ident"].astype(str).str.strip()
    df["underlying_code"] = df["PHYSICIAN_UNDERLYING_CODES"].apply(lambda x: normalize_code(x, compact_lookup))
    df = add_age_type(df[["ident", "underlying_code"]], age, va_type)
    write_all_heatmaps_for_source(df, codebook, "physician", "Physician", "Physician")

    for exp in EXPERIMENTS:
        exp_df = load_experiment(exp, compact_lookup)[["ident", f"{exp}_underlying"]].rename(
            columns={f"{exp}_underlying": "underlying_code"}
        )
        exp_df = add_age_type(exp_df, age, va_type)
        write_all_heatmaps_for_source(exp_df, codebook, exp.lower(), exp, exp)

    for exp in EXPERIMENTS:
        for code_level in ["level2", "level3"]:
            for suffix in ["overall", *VA_TYPE_LABELS.values()]:
                write_delta_heatmap(exp, codebook, code_level, suffix)

    for file in sorted(OUTPUT_DIR.glob("*_underlying_*_age_group_heatmap_*.svg")):
        print(file.resolve())
    for file in sorted(OUTPUT_DIR.glob("*_vs_physician_underlying_*_age_group_delta_heatmap_*.svg")):
        print(file.resolve())


if __name__ == "__main__":
    main()
