from __future__ import annotations

import html
from pathlib import Path

import pandas as pd


OUTPUT_DIR = Path("outputs") / "agreement_analysis"
EXPERIMENTS = ["EXP1", "EXP2", "EXP3", "EXP4"]
VA_TYPES = ["adult", "child", "infant"]
BIN_LABELS = ["0", ">0-0.25", ">0.25-0.5", ">0.5-0.75", ">0.75-<1", "1"]
BIN_COLORS = ["#e5e7eb", "#c7d2fe", "#a5b4fc", "#818cf8", "#6366f1", "#3730a3"]


def svg_text(x: float, y: float, text: object, size: int = 12, fill: str = "#111827", anchor: str = "start", weight: str = "400") -> str:
    return (
        f'<text x="{x}" y="{y}" text-anchor="{anchor}" font-family="Arial, sans-serif" '
        f'font-size="{size}" font-weight="{weight}" fill="{fill}">{html.escape(str(text))}</text>'
    )


def make_bins(df: pd.DataFrame) -> pd.DataFrame:
    bins = [-1e-9, 1e-9, 0.25, 0.5, 0.75, 0.999999, 1.000001]
    df = df.copy()
    df["jaccard_bin"] = pd.cut(
        df["jaccard"].astype(float),
        bins=bins,
        labels=BIN_LABELS,
        include_lowest=True,
        right=True,
    )
    return df


def write_stacked_chart(summary: pd.DataFrame, va_type: str, output: Path) -> None:
    sub = summary[summary["va_type"] == va_type].copy()
    width = 980
    height = 430
    left = 120
    top = 104
    plot_w = 610
    bar_h = 44
    gap = 26
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#ffffff"/>',
        svg_text(left, 32, f"Level 2 Pooled Jaccard Distribution by Experiment: {va_type.title()}", 22, weight="700"),
        svg_text(left, 54, "Flexible pooled any-type comparison against physician codes.", 12, "#52616b"),
    ]
    for i, exp in enumerate(EXPERIMENTS):
        y = top + i * (bar_h + gap)
        x_cursor = left
        parts.append(svg_text(left - 16, y + 28, exp, 13, "#111827", "end", "700"))
        exp_rows = sub[sub["experiment"] == exp]
        for j, bin_label in enumerate(BIN_LABELS):
            row = exp_rows[exp_rows["jaccard_bin"] == bin_label]
            value = float(row.iloc[0]["percent"]) if not row.empty else 0.0
            w = value * plot_w
            parts.append(f'<rect x="{x_cursor}" y="{y}" width="{w}" height="{bar_h}" fill="{BIN_COLORS[j]}"/>')
            if w > 34:
                parts.append(svg_text(x_cursor + w / 2, y + 28, f"{value * 100:.0f}%", 11, "#ffffff" if j >= 3 else "#111827", "middle", "700"))
            x_cursor += w
    legend_x = left + plot_w + 50
    legend_y = top
    parts.append(svg_text(legend_x, legend_y - 20, "Jaccard bin", 14, weight="700"))
    for j, label in enumerate(BIN_LABELS):
        y = legend_y + j * 28
        parts.append(f'<rect x="{legend_x}" y="{y - 14}" width="22" height="22" fill="{BIN_COLORS[j]}"/>')
        parts.append(svg_text(legend_x + 32, y + 2, label, 12))
    parts.append("</svg>")
    output.write_text("\n".join(parts), encoding="utf-8")


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    cases = pd.read_csv(OUTPUT_DIR / "jaccard_similarity_cases.csv")
    sub = cases[
        (cases["comparison_type"] == "flexible_pooled_any_type")
        & (cases["level"] == "level2")
        & (cases["stratum"].isin(VA_TYPES))
    ].copy()
    sub["experiment"] = sub["comparison"].str.extract(r"^(EXP[1-4])")
    sub["va_type"] = sub["stratum"]
    sub = make_bins(sub)

    counts = (
        sub.groupby(["va_type", "experiment", "jaccard_bin"], observed=False)
        .size()
        .reset_index(name="n")
    )
    totals = counts.groupby(["va_type", "experiment"])["n"].transform("sum")
    counts["percent"] = counts["n"] / totals
    counts.to_csv(OUTPUT_DIR / "jaccard_level2_pooled_distribution_by_vatype.csv", index=False)

    summary = (
        sub.groupby(["va_type", "experiment"])["jaccard"]
        .agg(["count", "mean", "median"])
        .reset_index()
        .rename(columns={"count": "n", "mean": "mean_jaccard", "median": "median_jaccard"})
    )
    perfect = sub[sub["jaccard"].astype(float) == 1].groupby(["va_type", "experiment"]).size().rename("n_perfect")
    zero = sub[sub["jaccard"].astype(float) == 0].groupby(["va_type", "experiment"]).size().rename("n_zero")
    summary = summary.merge(perfect, on=["va_type", "experiment"], how="left").merge(zero, on=["va_type", "experiment"], how="left")
    summary[["n_perfect", "n_zero"]] = summary[["n_perfect", "n_zero"]].fillna(0).astype(int)
    summary["perfect_match_percent"] = summary["n_perfect"] / summary["n"]
    summary["zero_overlap_percent"] = summary["n_zero"] / summary["n"]
    summary.to_csv(OUTPUT_DIR / "jaccard_level2_pooled_summary_by_vatype.csv", index=False)

    paths = []
    for va_type in VA_TYPES:
        out = OUTPUT_DIR / f"figure_jaccard_level2_pooled_distribution_{va_type}.svg"
        write_stacked_chart(counts, va_type, out)
        paths.append(out)
    pd.DataFrame({"figure": [p.name for p in paths], "path": [str(p.resolve()) for p in paths]}).to_csv(
        OUTPUT_DIR / "jaccard_level2_pooled_distribution_by_vatype_index.csv",
        index=False,
    )
    print((OUTPUT_DIR / "jaccard_level2_pooled_distribution_by_vatype.csv").resolve())
    print((OUTPUT_DIR / "jaccard_level2_pooled_summary_by_vatype.csv").resolve())
    for path in paths:
        print(path.resolve())


if __name__ == "__main__":
    main()
