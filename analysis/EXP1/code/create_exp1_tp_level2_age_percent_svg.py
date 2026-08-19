from __future__ import annotations

import html
from pathlib import Path

import pandas as pd


OUTPUT_DIR = Path("outputs") / "agreement_analysis"
INPUT_FILE = OUTPUT_DIR / "exp1_true_positive_overlap_level2_top20_by_vatype_age_percent_table.csv"
AGE_COLUMNS = [
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


def pct_value(value: object) -> float:
    return float(str(value).strip().rstrip("%"))


def main() -> None:
    table = pd.read_csv(INPUT_FILE)

    cell_w = 92
    total_w = 108
    cell_h = 44
    left = 500
    top = 142
    right = 42
    bottom = 50
    width = left + total_w + cell_w * len(AGE_COLUMNS) + right
    height = top + cell_h * len(table) + bottom
    max_pct = max(pct_value(value) for col in AGE_COLUMNS for value in table[col])

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#ffffff"/>',
        svg_text(24, 32, "EXP1 Level 2 True Positive Overlap by VA Type and Age (Top 20)", 22, weight="700"),
        svg_text(24, 56, "Cells show percent of comparable cases. Total column shows count and percent of Top 20 overlaps.", 12, "#52616b"),
        svg_text(24, 96, "Cause code / name", 13, weight="700"),
        svg_text(left + total_w / 2, 104, "Total", 12, "#111827", "middle", "700"),
    ]

    for j, col in enumerate(AGE_COLUMNS):
        x = left + total_w + j * cell_w
        va_type, age = col.split(" / ", 1)
        parts.append(svg_text(x + cell_w / 2, 94, va_type, 11, "#111827", "middle", "700"))
        parts.append(svg_text(x + cell_w / 2, 111, age, 11, "#111827", "middle", "700"))

    for i, row in table.iterrows():
        y = top + i * cell_h
        row_fill = "#f8fafc" if i % 2 == 0 else "#ffffff"
        parts.append(f'<rect x="16" y="{y}" width="{width - 32}" height="{cell_h}" fill="{row_fill}"/>')
        label = f"{row['cause_code']} - {row['cause_name']}"
        parts.append(svg_text(left - 14, y + 28, label[:82], 13, "#111827", "end"))
        parts.append(f'<rect x="{left}" y="{y + 3}" width="{total_w - 4}" height="{cell_h - 6}" rx="2" fill="#eef2f7"/>')
        parts.append(svg_text(left + total_w / 2 - 2, y + 28, row["total"], 12, "#111827", "middle", "700"))

        for j, col in enumerate(AGE_COLUMNS):
            x = left + total_w + j * cell_w
            pct = pct_value(row[col])
            color = heat_color(pct, max_pct)
            text_fill = "#ffffff" if max_pct and pct / max_pct > 0.55 else "#111827"
            parts.append(f'<rect x="{x}" y="{y + 3}" width="{cell_w - 4}" height="{cell_h - 6}" rx="2" fill="{color}"/>')
            parts.append(svg_text(x + cell_w / 2 - 2, y + 28, f"{pct:.1f}%", 13, text_fill, "middle", "700"))

    parts.append("</svg>")
    out = OUTPUT_DIR / "figure_exp1_true_positive_overlap_level2_top20_by_vatype_age_percent.svg"
    out.write_text("\n".join(parts), encoding="utf-8")
    print(out.resolve())


if __name__ == "__main__":
    main()
