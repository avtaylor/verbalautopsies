from __future__ import annotations

import html
from pathlib import Path

import pandas as pd


OUTPUT_DIR = Path("outputs") / "agreement_analysis"
EXPERIMENTS = ["EXP1", "EXP2", "EXP3", "EXP4"]
LEVELS = ["level1", "level2", "level3"]


def svg_text(x: float, y: float, text: object, size: int = 12, fill: str = "#111827", anchor: str = "start", weight: str = "400") -> str:
    return (
        f'<text x="{x}" y="{y}" text-anchor="{anchor}" font-family="Arial, sans-serif" '
        f'font-size="{size}" font-weight="{weight}" fill="{fill}">{html.escape(str(text))}</text>'
    )


def color_for(value: float) -> str:
    value = min(max(value, 0.0), 1.0)
    start = (248, 250, 252)
    mid = (125, 211, 252)
    end = (22, 101, 52)
    if value < 0.75:
        ratio = value / 0.75
        rgb = tuple(round(start[i] + (mid[i] - start[i]) * ratio) for i in range(3))
    else:
        ratio = (value - 0.75) / 0.25
        rgb = tuple(round(mid[i] + (end[i] - mid[i]) * ratio) for i in range(3))
    return f"rgb({rgb[0]},{rgb[1]},{rgb[2]})"


def text_color(value: float) -> str:
    return "#ffffff" if value >= 0.82 else "#111827"


def write_heatmap(df: pd.DataFrame, row_col: str, title: str, output: Path) -> None:
    rows = list(df[row_col].drop_duplicates())
    cell_w = 96
    cell_h = 34
    left = 210
    top = 124
    right = 42
    bottom = 50
    width = left + cell_w * len(EXPERIMENTS) + right
    height = top + cell_h * len(rows) + bottom

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#ffffff"/>',
        svg_text(left, 32, title, 22, weight="700"),
        svg_text(left, 54, "Cells show chance-corrected CSMF accuracy for underlying cause.", 12, "#52616b"),
    ]
    for j, exp in enumerate(EXPERIMENTS):
        x = left + j * cell_w
        parts.append(svg_text(x + cell_w / 2, top - 14, exp, 12, "#111827", "middle", "700"))

    for i, row_label in enumerate(rows):
        y = top + i * cell_h
        fill = "#f8fafc" if i % 2 == 0 else "#ffffff"
        parts.append(f'<rect x="16" y="{y}" width="{width - 32}" height="{cell_h}" fill="{fill}"/>')
        parts.append(svg_text(left - 12, y + 22, row_label, 11, "#111827", "end"))
        for j, exp in enumerate(EXPERIMENTS):
            x = left + j * cell_w
            value_row = df[(df[row_col] == row_label) & (df["experiment"] == exp)]
            if value_row.empty:
                continue
            value = float(value_row.iloc[0]["csmf_accuracy_chance_corrected"])
            color = color_for(value)
            parts.append(f'<rect x="{x}" y="{y + 3}" width="{cell_w - 4}" height="{cell_h - 6}" rx="2" fill="{color}"/>')
            parts.append(svg_text(x + cell_w / 2 - 2, y + 22, f"{value:.3f}", 11, text_color(value), "middle", "700"))

    parts.append("</svg>")
    output.write_text("\n".join(parts), encoding="utf-8")


def build_va_age_charts() -> list[Path]:
    data = pd.read_csv(OUTPUT_DIR / "csmf_accuracy_summary_underlying_by_va_type_age.csv")
    data["row_label"] = data["va_type"].astype(str) + " / " + data["age_group"].astype(str)
    paths = []
    for level in LEVELS:
        sub = data[data["level"] == level].copy()
        out = OUTPUT_DIR / f"figure_csmf_accuracy_by_va_type_age_{level}.svg"
        write_heatmap(sub, "row_label", f"CSMF Accuracy by VA Type and Age Group ({level.upper()})", out)
        paths.append(out)
    return paths


def build_va_sex_charts() -> list[Path]:
    data = pd.read_csv(OUTPUT_DIR / "csmf_accuracy_summary_underlying_by_va_type_sex.csv")
    data["row_label"] = data["va_type"].astype(str) + " / " + data["sex"].astype(str)
    paths = []
    for level in LEVELS:
        sub = data[data["level"] == level].copy()
        out = OUTPUT_DIR / f"figure_csmf_accuracy_by_va_type_sex_{level}.svg"
        write_heatmap(sub, "row_label", f"CSMF Accuracy by VA Type and Sex ({level.upper()})", out)
        paths.append(out)
    return paths


def build_va_age_sex_charts() -> list[Path]:
    data = pd.read_csv(OUTPUT_DIR / "csmf_accuracy_summary_underlying_by_va_type_age_sex.csv")
    data["row_label"] = data["va_type"].astype(str) + " / " + data["age_group"].astype(str) + " / " + data["sex"].astype(str)
    paths = []
    for level in LEVELS:
        sub = data[data["level"] == level].copy()
        out = OUTPUT_DIR / f"figure_csmf_accuracy_by_va_type_age_sex_{level}.svg"
        write_heatmap(sub, "row_label", f"CSMF Accuracy by VA Type, Age Group, and Sex ({level.upper()})", out)
        paths.append(out)
    return paths


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    paths = []
    paths.extend(build_va_age_charts())
    paths.extend(build_va_sex_charts())
    paths.extend(build_va_age_sex_charts())
    pd.DataFrame({"figure": [p.name for p in paths], "path": [str(p.resolve()) for p in paths]}).to_csv(
        OUTPUT_DIR / "stratified_csmf_visualization_index.csv",
        index=False,
    )
    for path in paths:
        print(path.resolve())


if __name__ == "__main__":
    main()
