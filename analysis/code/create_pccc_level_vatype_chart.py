from __future__ import annotations

import html
from pathlib import Path

import pandas as pd


OUTPUT_DIR = Path("outputs") / "agreement_analysis"
EXPERIMENTS = ["EXP1", "EXP2", "EXP3", "EXP4"]
LEVELS = ["level1", "level2", "level3"]
LEVEL_LABELS = {"level1": "Level 1", "level2": "Level 2", "level3": "Level 3"}
VA_TYPES = ["adult", "child", "infant"]
EXP_COLORS = {
    "EXP1": "#2563eb",
    "EXP2": "#d97706",
    "EXP3": "#059669",
    "EXP4": "#dc2626",
}


def svg_text(x: float, y: float, text: object, size: int = 12, fill: str = "#111827", anchor: str = "start", weight: str = "400") -> str:
    return (
        f'<text x="{x}" y="{y}" text-anchor="{anchor}" font-family="Arial, sans-serif" '
        f'font-size="{size}" font-weight="{weight}" fill="{fill}">{html.escape(str(text))}</text>'
    )


def y_scale(value: float, top: float, plot_h: float) -> float:
    return top + (1.0 - value) * plot_h


def write_chart(data: pd.DataFrame) -> Path:
    width = 1060
    height = 560
    left = 86
    right = 160
    top = 104
    bottom = 82
    facet_gap = 54
    plot_w = (width - left - right - facet_gap * (len(VA_TYPES) - 1)) / len(VA_TYPES)
    plot_h = height - top - bottom
    x_step = plot_w / (len(LEVELS) - 1)
    offsets = {"EXP1": -10, "EXP2": -3.3, "EXP3": 3.3, "EXP4": 10}

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#ffffff"/>',
        svg_text(left, 34, "Underlying COD PCCC by Coding Level and VA Type", 24, weight="700"),
        svg_text(left, 58, "Single-prediction PCCC-style measure for strict LLM underlying code vs physician underlying code.", 12, "#52616b"),
    ]

    for v_idx, va_type in enumerate(VA_TYPES):
        x0 = left + v_idx * (plot_w + facet_gap)
        parts.append(svg_text(x0 + plot_w / 2, top - 22, va_type.title(), 15, weight="700", anchor="middle"))

        for tick in [0.0, 0.25, 0.50, 0.75, 1.0]:
            y = y_scale(tick, top, plot_h)
            parts.append(f'<line x1="{x0}" y1="{y}" x2="{x0 + plot_w}" y2="{y}" stroke="#e5e7eb" stroke-width="1"/>')
            if v_idx == 0:
                parts.append(svg_text(left - 12, y + 4, f"{tick:.2f}", 11, "#374151", "end"))

        for i, level in enumerate(LEVELS):
            x = x0 + i * x_step
            parts.append(f'<line x1="{x}" y1="{top}" x2="{x}" y2="{top + plot_h}" stroke="#f1f5f9" stroke-width="1"/>')
            parts.append(svg_text(x, top + plot_h + 30, LEVEL_LABELS[level], 12, "#111827", "middle"))

        for exp in EXPERIMENTS:
            points = []
            for i, level in enumerate(LEVELS):
                row = data[(data["va_type"] == va_type) & (data["experiment"] == exp) & (data["level"] == level)]
                if row.empty:
                    continue
                x = x0 + i * x_step + offsets[exp]
                y = y_scale(float(row.iloc[0]["pccc"]), top, plot_h)
                points.append((x, y, float(row.iloc[0]["pccc"])))
            if len(points) > 1:
                path = " ".join(f"{'M' if i == 0 else 'L'} {x} {y}" for i, (x, y, _) in enumerate(points))
                parts.append(f'<path d="{path}" fill="none" stroke="{EXP_COLORS[exp]}" stroke-width="2.4"/>')
            for x, y, value in points:
                parts.append(f'<circle cx="{x}" cy="{y}" r="5.2" fill="{EXP_COLORS[exp]}"/>')
                parts.append(svg_text(x, y - 10, f"{value:.2f}", 9, "#111827", "middle", "700"))

    parts.append(
        f'<text x="28" y="{top + plot_h / 2}" transform="rotate(-90 28 {top + plot_h / 2})" '
        'text-anchor="middle" font-family="Arial, sans-serif" font-size="15" font-weight="700" fill="#111827">PCCC</text>'
    )
    parts.append(svg_text(left + (width - left - right) / 2, height - 18, "Coding level", 14, "#111827", "middle", "700"))

    legend_x = width - right + 22
    legend_y = top + 12
    parts.append(svg_text(legend_x, legend_y - 14, "Experiment", 13, weight="700"))
    for i, exp in enumerate(EXPERIMENTS):
        y = legend_y + i * 28
        parts.append(f'<line x1="{legend_x}" y1="{y - 4}" x2="{legend_x + 28}" y2="{y - 4}" stroke="{EXP_COLORS[exp]}" stroke-width="2.5"/>')
        parts.append(f'<circle cx="{legend_x + 14}" cy="{y - 4}" r="5.2" fill="{EXP_COLORS[exp]}"/>')
        parts.append(svg_text(legend_x + 38, y, exp, 12))

    parts.append("</svg>")
    out = OUTPUT_DIR / "figure_underlying_pccc_by_level_vatype.svg"
    out.write_text("\n".join(parts), encoding="utf-8")
    return out


def main() -> None:
    source = pd.read_csv(OUTPUT_DIR / "underlying_pccc_single_prediction_by_vatype_age.csv")
    rows = []
    for va_type in VA_TYPES:
        for exp in EXPERIMENTS:
            for level in LEVELS:
                sub = source[(source["va_type"] == va_type) & (source["experiment"] == exp) & (source["level"] == level)]
                n_total = int(sub["n_compared"].sum())
                n_agree = int(sub["n_agree"].sum())
                n_possible = int(sub["N_possible_causes"].iloc[0])
                accuracy = n_agree / n_total if n_total else None
                pccc = (accuracy - (1 / n_possible)) / (1 - (1 / n_possible)) if n_total and n_possible > 1 else None
                rows.append(
                    {
                        "va_type": va_type,
                        "experiment": exp,
                        "level": level,
                        "n_compared": n_total,
                        "n_agree": n_agree,
                        "accuracy_C": accuracy,
                        "N_possible_causes": n_possible,
                        "k": 1,
                        "pccc": pccc,
                    }
                )

    table = pd.DataFrame(rows)
    table_path = OUTPUT_DIR / "underlying_pccc_single_prediction_by_vatype.csv"
    table.to_csv(table_path, index=False)
    print(table_path.resolve())
    print(write_chart(table).resolve())


if __name__ == "__main__":
    main()
