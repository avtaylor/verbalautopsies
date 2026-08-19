from __future__ import annotations

import html
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


def write_heatmap(table: pd.DataFrame) -> Path:
    cell_w = 92
    cell_h = 44
    left = 500
    top = 142
    right = 42
    bottom = 50
    width = left + cell_w * len(STRATA) + right
    height = top + cell_h * len(table) + bottom

    pct_values = []
    for stratum in STRATA:
        pct_values.extend(table[f"{stratum} %"].astype(str).str.rstrip("%").astype(float).tolist())
    max_pct = max(pct_values) if pct_values else 0

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#ffffff"/>',
        svg_text(24, 32, "EXP1 True Positive Overlap Codes by VA Type and Age (Level 2, Top 20)", 22, weight="700"),
        svg_text(24, 56, "Pooled any-type comparison: codes present in both EXP1 and physician code sets. Cells show count and percent of comparable cases.", 12, "#52616b"),
        svg_text(24, 96, "Cause code / name", 13, weight="700"),
    ]

    for j, stratum in enumerate(STRATA):
        x = left + j * cell_w
        label = stratum.replace(" / ", "\n")
        parts.append(svg_text(x + cell_w / 2, 94, label.split("\n")[0], 11, "#111827", "middle", "700"))
        parts.append(svg_text(x + cell_w / 2, 111, label.split("\n")[1], 11, "#111827", "middle", "700"))

    for i, row in table.iterrows():
        y = top + i * cell_h
        row_fill = "#f8fafc" if i % 2 == 0 else "#ffffff"
        parts.append(f'<rect x="16" y="{y}" width="{width - 32}" height="{cell_h}" fill="{row_fill}"/>')
        label = f"{row['cause_code']} - {row['cause_name']}"
        parts.append(svg_text(left - 14, y + 28, label[:82], 13, "#111827", "end"))
        for j, stratum in enumerate(STRATA):
            x = left + j * cell_w
            count = int(row[f"{stratum} n"])
            pct = float(str(row[f"{stratum} %"]).rstrip("%"))
            color = heat_color(pct, max_pct)
            text_fill = "#ffffff" if max_pct and pct / max_pct > 0.55 else "#111827"
            parts.append(f'<rect x="{x}" y="{y + 3}" width="{cell_w - 4}" height="{cell_h - 6}" rx="2" fill="{color}"/>')
            parts.append(svg_text(x + cell_w / 2 - 2, y + 19, count, 13, text_fill, "middle", "700"))
            parts.append(svg_text(x + cell_w / 2 - 2, y + 36, f"{pct:.1f}%", 12, text_fill, "middle"))

    parts.append("</svg>")
    out = OUTPUT_DIR / "figure_exp1_true_positive_overlap_heatmap_level2_top20_by_vatype_age.svg"
    out.write_text("\n".join(parts), encoding="utf-8")
    return out


def main() -> None:
    table = pd.read_csv(INPUT_FILE)
    print(write_heatmap(table).resolve())


if __name__ == "__main__":
    main()
