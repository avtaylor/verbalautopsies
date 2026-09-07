from __future__ import annotations

import html
from pathlib import Path

import pandas as pd


OUTPUT_DIR = Path("outputs") / "agreement_analysis"
EXPERIMENTS = ["EXP1", "EXP2", "EXP3", "EXP4"]
LEVEL_ORDER = ["level1", "level2", "level3"]
LEVEL_LABELS = {"level1": "Level 1", "level2": "Level 2", "level3": "Level 3"}
STRATA = ["overall", "adult", "child", "infant"]

EXP_COLORS = {
    "EXP1": "#111827",
    "EXP2": "#d97706",
    "EXP3": "#059669",
    "EXP4": "#2563eb",
}


def svg_text(x: float, y: float, text: object, size: int = 12, fill: str = "#111827", anchor: str = "start", weight: str = "400") -> str:
    return (
        f'<text x="{x}" y="{y}" text-anchor="{anchor}" font-family="Arial, sans-serif" '
        f'font-size="{size}" font-weight="{weight}" fill="{fill}">{html.escape(str(text))}</text>'
    )


def svg_rotated_text(x: float, y: float, text: object, size: int = 12, fill: str = "#111827", anchor: str = "middle", weight: str = "400") -> str:
    return (
        f'<text x="{x}" y="{y}" transform="rotate(-90 {x} {y})" text-anchor="{anchor}" '
        f'font-family="Arial, sans-serif" font-size="{size}" font-weight="{weight}" '
        f'fill="{fill}">{html.escape(str(text))}</text>'
    )


def make_points(data: pd.DataFrame, exp: str, stratum: str) -> list[tuple[str, float]]:
    out = []
    for level in LEVEL_ORDER:
        row = data[(data["experiment"] == exp) & (data["stratum"] == stratum) & (data["level"] == level)]
        if row.empty:
            continue
        out.append((level, float(row.iloc[0]["any_overlap"])))
    return out


def write_line_chart(data: pd.DataFrame, stratum: str, output: Path) -> None:
    width = 980
    height = 500
    left = 82
    right = 190
    top = 102
    bottom = 84
    plot_w = width - left - right
    plot_h = height - top - bottom
    y_min = 0.45
    y_max = 1.0
    x_positions = {
        level: left + i * (plot_w / (len(LEVEL_ORDER) - 1))
        for i, level in enumerate(LEVEL_ORDER)
    }

    def y_pos(value: float) -> float:
        return top + (y_max - value) / (y_max - y_min) * plot_h

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#ffffff"/>',
        svg_text(left, 30, f"Flexible Any-Code Agreement by Coding Level: {stratum.title()}", 24, weight="700"),
        svg_text(left, 52, "Any overlap between pooled LLM codes and pooled physician codes, irrespective of cause type.", 12, "#52616b"),
    ]

    for tick in [0.5, 0.6, 0.7, 0.8, 0.9, 1.0]:
        y = y_pos(tick)
        parts.append(f'<line x1="{left}" y1="{y}" x2="{left + plot_w}" y2="{y}" stroke="#e5e7eb" stroke-width="1"/>')
        parts.append(svg_text(left - 12, y + 4, f"{tick:.1f}", 13, "#374151", "end"))
    for tick in [0.55, 0.65, 0.75, 0.85, 0.95]:
        y = y_pos(tick)
        parts.append(f'<line x1="{left}" y1="{y}" x2="{left + plot_w}" y2="{y}" stroke="#f1f5f9" stroke-width="1"/>')

    for level in LEVEL_ORDER:
        x = x_positions[level]
        parts.append(f'<line x1="{x}" y1="{top}" x2="{x}" y2="{top + plot_h}" stroke="#e5e7eb" stroke-width="1"/>')
        parts.append(svg_text(x, top + plot_h + 34, LEVEL_LABELS[level], 13, "#111827", "middle"))

    for exp in EXPERIMENTS:
        points = make_points(data, exp, stratum)
        if len(points) < 2:
            continue
        path_parts = []
        for i, (level, value) in enumerate(points):
            command = "M" if i == 0 else "L"
            path_parts.append(f"{command} {x_positions[level]} {y_pos(value)}")
        color = EXP_COLORS[exp]
        parts.append(f'<path d="{" ".join(path_parts)}" fill="none" stroke="{color}" stroke-width="2.6"/>')
        for level, value in points:
            x = x_positions[level]
            y = y_pos(value)
            parts.append(f'<circle cx="{x}" cy="{y}" r="6" fill="{color}"/>')
            parts.append(svg_text(x, y - 12, f"{value:.3f}", 12, "#111827", "middle", "700"))

    parts.append(svg_text(left + plot_w / 2, height - 24, "Coding Level", 20, "#111827", "middle"))
    parts.append(svg_rotated_text(24, top + plot_h / 2, "Flexible agreement", 18, "#111827"))

    legend_x = left + plot_w + 52
    legend_y = top + 44
    parts.append(svg_text(legend_x, legend_y - 22, "Experiment", 15, weight="700"))
    for i, exp in enumerate(EXPERIMENTS):
        y = legend_y + i * 30
        parts.append(f'<line x1="{legend_x}" y1="{y - 4}" x2="{legend_x + 28}" y2="{y - 4}" stroke="{EXP_COLORS[exp]}" stroke-width="3"/>')
        parts.append(f'<circle cx="{legend_x + 14}" cy="{y - 4}" r="5" fill="{EXP_COLORS[exp]}"/>')
        parts.append(svg_text(legend_x + 38, y, exp, 13))

    parts.append("</svg>")
    output.write_text("\n".join(parts), encoding="utf-8")


def write_individual_chart(data: pd.DataFrame, exp: str, stratum: str, output: Path) -> None:
    width = 980
    height = 500
    left = 82
    right = 70
    top = 102
    bottom = 84
    plot_w = width - left - right
    plot_h = height - top - bottom
    y_min = 0.45
    y_max = 1.0
    x_positions = {level: left + i * (plot_w / 2) for i, level in enumerate(LEVEL_ORDER)}

    def y_pos(value: float) -> float:
        return top + (y_max - value) / (y_max - y_min) * plot_h

    points = make_points(data, exp, stratum)
    color = EXP_COLORS[exp]
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#ffffff"/>',
        svg_text(left, 30, f"Flexible Any-Code Agreement by Coding Level: {exp} {stratum.title()}", 24, weight="700"),
    ]
    for tick in [0.5, 0.6, 0.7, 0.8, 0.9, 1.0]:
        y = y_pos(tick)
        parts.append(f'<line x1="{left}" y1="{y}" x2="{left + plot_w}" y2="{y}" stroke="#e5e7eb" stroke-width="1"/>')
        parts.append(svg_text(left - 12, y + 4, f"{tick:.1f}", 13, "#374151", "end"))
    for level in LEVEL_ORDER:
        x = x_positions[level]
        parts.append(f'<line x1="{x}" y1="{top}" x2="{x}" y2="{top + plot_h}" stroke="#e5e7eb" stroke-width="1"/>')
        parts.append(svg_text(x, top + plot_h + 34, LEVEL_LABELS[level], 13, "#111827", "middle"))
    path_parts = []
    for i, (level, value) in enumerate(points):
        path_parts.append(f"{'M' if i == 0 else 'L'} {x_positions[level]} {y_pos(value)}")
    parts.append(f'<path d="{" ".join(path_parts)}" fill="none" stroke="{color}" stroke-width="2.8"/>')
    for level, value in points:
        x = x_positions[level]
        y = y_pos(value)
        parts.append(f'<circle cx="{x}" cy="{y}" r="7" fill="{color}"/>')
        parts.append(svg_text(x, y - 14, f"{value:.3f}", 14, "#111827", "middle", "700"))
    parts.append(svg_text(left + plot_w / 2, height - 24, "Coding Level", 20, "#111827", "middle"))
    parts.append(svg_rotated_text(24, top + plot_h / 2, "Flexible agreement", 18, "#111827"))
    parts.append("</svg>")
    output.write_text("\n".join(parts), encoding="utf-8")


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    summary = pd.read_csv(OUTPUT_DIR / "jaccard_similarity_summary.csv")
    data = summary[summary["comparison_type"] == "flexible_pooled_any_type"].copy()
    data = data[data["comparison"].str.contains("PHY", na=False)]
    data["experiment"] = data["comparison"].str.extract(r"^(EXP[1-4])")

    paths = []
    for stratum in STRATA:
        path = OUTPUT_DIR / f"figure_flexible_any_code_agreement_by_level_{stratum}.svg"
        write_line_chart(data, stratum, path)
        paths.append(path)
    for exp in EXPERIMENTS:
        path = OUTPUT_DIR / f"figure_flexible_any_code_agreement_by_level_{exp.lower()}_overall.svg"
        write_individual_chart(data, exp, "overall", path)
        paths.append(path)

    pd.DataFrame({"figure": [p.name for p in paths], "path": [str(p.resolve()) for p in paths]}).to_csv(
        OUTPUT_DIR / "flexible_any_code_agreement_line_chart_index.csv",
        index=False,
    )
    for path in paths:
        print(path.resolve())


if __name__ == "__main__":
    main()
