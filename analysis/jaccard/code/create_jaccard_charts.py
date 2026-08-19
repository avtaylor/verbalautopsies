from __future__ import annotations

import html
from pathlib import Path

import pandas as pd


OUTPUT_DIR = Path("outputs") / "agreement_analysis"
EXPERIMENTS = ["EXP1", "EXP2", "EXP3", "EXP4"]
LEVELS = ["level1", "level2", "level3"]
STRATA = ["overall", "adult", "child", "infant"]


def svg_text(x: float, y: float, text: object, size: int = 12, fill: str = "#111827", anchor: str = "start", weight: str = "400") -> str:
    return (
        f'<text x="{x}" y="{y}" text-anchor="{anchor}" font-family="Arial, sans-serif" '
        f'font-size="{size}" font-weight="{weight}" fill="{fill}">{html.escape(str(text))}</text>'
    )


def color_for(value: float) -> str:
    value = min(max(value, 0.0), 1.0)
    start = (248, 250, 252)
    end = (79, 70, 229)
    rgb = tuple(round(start[i] + (end[i] - start[i]) * value) for i in range(3))
    return f"rgb({rgb[0]},{rgb[1]},{rgb[2]})"


def text_color(value: float) -> str:
    return "#ffffff" if value >= 0.55 else "#111827"


def write_jaccard_heatmap(summary: pd.DataFrame, comparison_type: str, title: str, output: Path) -> None:
    data = summary[summary["comparison_type"] == comparison_type].copy()
    data = data[data["comparison"].str.contains("PHY", na=False)]
    data["experiment"] = data["comparison"].str.extract(r"^(EXP[1-4])")
    rows = [f"{stratum} / {level}" for stratum in STRATA for level in LEVELS]
    cell_w = 98
    cell_h = 34
    left = 180
    top = 124
    width = left + cell_w * len(EXPERIMENTS) + 48
    height = top + cell_h * len(rows) + 58
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#ffffff"/>',
        svg_text(left, 32, title, 22, weight="700"),
        svg_text(left, 54, "Cells show mean case-level Jaccard similarity.", 12, "#52616b"),
    ]
    for j, exp in enumerate(EXPERIMENTS):
        x = left + j * cell_w
        parts.append(svg_text(x + cell_w / 2, top - 14, exp, 12, "#111827", "middle", "700"))
    for i, row_label in enumerate(rows):
        stratum, level = row_label.split(" / ")
        y = top + i * cell_h
        fill = "#f8fafc" if i % 2 == 0 else "#ffffff"
        parts.append(f'<rect x="16" y="{y}" width="{width - 32}" height="{cell_h}" fill="{fill}"/>')
        parts.append(svg_text(left - 12, y + 22, row_label, 11, "#111827", "end"))
        for j, exp in enumerate(EXPERIMENTS):
            x = left + j * cell_w
            match = data[(data["stratum"] == stratum) & (data["level"] == level) & (data["experiment"] == exp)]
            if match.empty:
                continue
            value = float(match.iloc[0]["mean_jaccard"])
            parts.append(f'<rect x="{x}" y="{y + 3}" width="{cell_w - 4}" height="{cell_h - 6}" rx="2" fill="{color_for(value)}"/>')
            parts.append(svg_text(x + cell_w / 2 - 2, y + 22, f"{value:.3f}", 11, text_color(value), "middle", "700"))
    parts.append("</svg>")
    output.write_text("\n".join(parts), encoding="utf-8")


def write_jaccard_histograms(cases: pd.DataFrame, output: Path) -> None:
    data = cases[
        (cases["comparison_type"] == "flexible_pooled_any_type")
        & (cases["stratum"] == "overall")
        & (cases["level"] == "level2")
    ].copy()
    data["experiment"] = data["comparison"].str.extract(r"^(EXP[1-4])")
    data["jaccard"] = data["jaccard"].astype(float)
    bins = [0, 0.000001, 0.25, 0.5, 0.75, 0.999999, 1.000001]
    labels = ["0", ">0-0.25", ">0.25-0.5", ">0.5-0.75", ">0.75-<1", "1"]
    data["bin"] = pd.cut(data["jaccard"], bins=bins, labels=labels, include_lowest=True, right=False)
    counts = pd.crosstab(data["experiment"], data["bin"]).reindex(index=EXPERIMENTS, columns=labels, fill_value=0)
    props = counts.div(counts.sum(axis=1), axis=0).fillna(0)
    colors = ["#e5e7eb", "#c7d2fe", "#a5b4fc", "#818cf8", "#6366f1", "#3730a3"]

    width = 1000
    height = 440
    left = 120
    top = 104
    plot_w = 620
    bar_h = 44
    gap = 26
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#ffffff"/>',
        svg_text(left, 32, "Distribution of Case-Level Jaccard Scores", 22, weight="700"),
        svg_text(left, 54, "Flexible pooled any-type comparison, Level 2, overall.", 12, "#52616b"),
    ]
    for i, exp in enumerate(EXPERIMENTS):
        y = top + i * (bar_h + gap)
        x_cursor = left
        parts.append(svg_text(left - 16, y + 28, exp, 13, "#111827", "end", "700"))
        for j, label in enumerate(labels):
            value = float(props.loc[exp, label])
            w = value * plot_w
            parts.append(f'<rect x="{x_cursor}" y="{y}" width="{w}" height="{bar_h}" fill="{colors[j]}"/>')
            if w > 36:
                parts.append(svg_text(x_cursor + w / 2, y + 28, f"{value * 100:.0f}%", 11, "#ffffff" if j >= 3 else "#111827", "middle", "700"))
            x_cursor += w
    legend_x = left + plot_w + 50
    legend_y = top
    parts.append(svg_text(legend_x, legend_y - 20, "Jaccard bin", 14, weight="700"))
    for j, label in enumerate(labels):
        y = legend_y + j * 28
        parts.append(f'<rect x="{legend_x}" y="{y - 14}" width="22" height="22" fill="{colors[j]}"/>')
        parts.append(svg_text(legend_x + 32, y + 2, label, 12))
    parts.append("</svg>")
    output.write_text("\n".join(parts), encoding="utf-8")


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    summary = pd.read_csv(OUTPUT_DIR / "jaccard_similarity_summary.csv")
    cases = pd.read_csv(OUTPUT_DIR / "jaccard_similarity_cases.csv")
    paths = [
        OUTPUT_DIR / "figure_jaccard_flexible_pooled_any_type_heatmap.svg",
        OUTPUT_DIR / "figure_jaccard_contributory_vs_phy_heatmap.svg",
        OUTPUT_DIR / "figure_jaccard_flexible_pooled_level2_distribution.svg",
    ]
    write_jaccard_heatmap(
        summary,
        "flexible_pooled_any_type",
        "Mean Jaccard Similarity: Flexible Pooled Any-Type",
        paths[0],
    )
    write_jaccard_heatmap(
        summary,
        "contributory_vs_phy",
        "Mean Jaccard Similarity: Contributory Codes vs Physician",
        paths[1],
    )
    write_jaccard_histograms(cases, paths[2])
    pd.DataFrame({"figure": [p.name for p in paths], "path": [str(p.resolve()) for p in paths]}).to_csv(
        OUTPUT_DIR / "jaccard_visualization_index.csv",
        index=False,
    )
    for path in paths:
        print(path.resolve())


if __name__ == "__main__":
    main()
