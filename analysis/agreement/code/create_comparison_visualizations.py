from __future__ import annotations

import html
import math
from pathlib import Path

import pandas as pd


OUTPUT_DIR = Path("outputs") / "agreement_analysis"
EXPERIMENTS = ["EXP1", "EXP2", "EXP3", "EXP4"]
LEVELS = ["level1", "level2", "level3"]
STRATA = ["overall", "adult", "child", "infant"]

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


def pct(value: float) -> str:
    return f"{value * 100:.1f}%"


def safe_float(value: object) -> float:
    if pd.isna(value):
        return 0.0
    return float(value)


def write_csmf_accuracy_dot_plot(summary: pd.DataFrame) -> Path:
    data = summary.copy()
    data["score"] = data["csmf_accuracy_chance_corrected"].astype(float)
    if "va_type" in data.columns:
        data["plot_stratum"] = data.apply(
            lambda row: row["va_type"] if str(row["va_type"]).strip().lower() in STRATA else row["stratum"],
            axis=1,
        )
    else:
        data["plot_stratum"] = data["stratum"]
    width = 1120
    height = 720
    left = 150
    right = 80
    top = 110
    bottom = 104
    facet_gap = 52
    plot_w = (width - left - right - facet_gap * (len(STRATA) - 1)) / len(STRATA)
    plot_h = height - top - bottom
    x_min, x_max = 0.45, 1.0
    row_gap = plot_h / (len(LEVELS) * len(EXPERIMENTS) + 2)

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#ffffff"/>',
        svg_text(left, 34, "CSMF Accuracy by Experiment, Code Level, and VA Type", 24, weight="700"),
        svg_text(left, 56, "Chance-corrected CSMF accuracy for underlying cause; higher is better.", 12, "#52616b"),
    ]

    for s_idx, stratum in enumerate(STRATA):
        x0 = left + s_idx * (plot_w + facet_gap)
        parts.append(svg_text(x0 + plot_w / 2, top - 20, stratum.title(), 15, weight="700", anchor="middle"))
        for tick in [0.5, 0.75, 1.0]:
            x = x0 + (tick - x_min) / (x_max - x_min) * plot_w
            parts.append(f'<line x1="{x}" y1="{top}" x2="{x}" y2="{top + plot_h}" stroke="#cbd5e1" stroke-width="1.4"/>')
            parts.append(svg_text(x, top + plot_h + 24, f"{tick:.2f}", 11, "#111827", anchor="middle", weight="700"))

        for l_idx, level in enumerate(LEVELS):
            y_base = top + 18 + (l_idx * len(EXPERIMENTS) + l_idx * 0.9) * row_gap
            if s_idx == 0:
                parts.append(svg_text(24, y_base + row_gap * 1.5, level.upper(), 12, "#111827", weight="700"))
            for e_idx, exp in enumerate(EXPERIMENTS):
                y = y_base + e_idx * row_gap
                if s_idx == 0:
                    parts.append(svg_text(left - 18, y + 4, exp, 11, "#374151", anchor="end"))
                row = data[(data["plot_stratum"] == stratum) & (data["level"] == level) & (data["experiment"] == exp)]
                if row.empty:
                    continue
                score = float(row.iloc[0]["score"])
                x = x0 + (score - x_min) / (x_max - x_min) * plot_w
                parts.append(f'<circle cx="{x}" cy="{y}" r="7.2" fill="{EXP_COLORS[exp]}"/>')
                parts.append(svg_text(x + 11, y + 5, f"{score:.3f}", 13, "#111827", weight="700"))

    legend_x = left
    legend_y = height - 24
    for i, exp in enumerate(EXPERIMENTS):
        x = legend_x + i * 95
        parts.append(f'<circle cx="{x}" cy="{legend_y - 4}" r="7.2" fill="{EXP_COLORS[exp]}"/>')
        parts.append(svg_text(x + 15, legend_y, exp, 13))
    parts.append("</svg>")
    out = OUTPUT_DIR / "figure_csmf_accuracy_dot_plot.svg"
    out.write_text("\n".join(parts), encoding="utf-8")
    return out


def write_csmf_difference_bars(detail: pd.DataFrame, level: str = "level2", stratum: str = "overall", top_n: int = 12) -> list[Path]:
    paths = []
    data = detail[(detail["level"] == level) & (detail["stratum"] == stratum)].copy()
    for exp in EXPERIMENTS:
        sub = data[data["experiment"] == exp].copy()
        sub["difference"] = sub["difference"].astype(float)
        sub["abs_difference"] = sub["difference"].abs()
        sub = sub.sort_values("abs_difference", ascending=False).head(top_n).sort_values("difference")
        width = 1120
        height = 520
        left = 420
        right = 110
        top = 104
        bottom = 58
        plot_w = width - left - right
        plot_h = height - top - bottom
        max_abs = max(float(sub["difference"].abs().max()), 0.01)
        zero_x = left + plot_w / 2
        scale = (plot_w / 2) / max_abs
        bar_h = plot_h / max(len(sub), 1) * 0.68
        gap = plot_h / max(len(sub), 1) * 0.32
        parts = [
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
            '<rect width="100%" height="100%" fill="#ffffff"/>',
            svg_text(left, 32, f"{exp} vs Physician: Largest Level 2 CSMF Differences", 22, weight="700"),
            svg_text(left, 54, "Percentage-point difference in underlying cause distribution: LLM minus physician.", 12, "#52616b"),
            f'<line x1="{zero_x}" y1="{top - 8}" x2="{zero_x}" y2="{top + plot_h}" stroke="#111827" stroke-width="1"/>',
        ]
        for tick in [-max_abs, -max_abs / 2, 0, max_abs / 2, max_abs]:
            x = zero_x + tick * scale
            parts.append(f'<line x1="{x}" y1="{top + plot_h}" x2="{x}" y2="{top + plot_h + 5}" stroke="#374151"/>')
            parts.append(svg_text(x, top + plot_h + 22, f"{tick * 100:+.0f}", 10, "#374151", anchor="middle"))

        for i, row in enumerate(sub.itertuples(index=False)):
            y = top + i * (bar_h + gap)
            value = float(row.difference)
            x = zero_x if value >= 0 else zero_x + value * scale
            w = abs(value * scale)
            color = "#2563eb" if value >= 0 else "#dc2626"
            label = f"{row.cause_code} - {row.cause_name}"
            parts.append(svg_text(left - 30, y + bar_h * 0.68, label[:58], 11, "#111827", anchor="end"))
            parts.append(f'<rect x="{x}" y="{y}" width="{w}" height="{bar_h}" fill="{color}"/>')
            if value >= 0:
                parts.append(svg_text(x + w + 10, y + bar_h * 0.68, f"{value * 100:+.1f}", 10, "#374151", anchor="start"))
            elif w >= 36:
                parts.append(svg_text(x + 7, y + bar_h * 0.68, f"{value * 100:+.1f}", 10, "#ffffff", anchor="start", weight="700"))
            else:
                parts.append(svg_text(x - 10, y + bar_h * 0.68, f"{value * 100:+.1f}", 10, "#374151", anchor="end"))
        parts.append(svg_text(left + plot_w / 2, height - 16, "Percentage-point difference", 13, "#111827", anchor="middle"))
        parts.append("</svg>")
        out = OUTPUT_DIR / f"figure_{exp.lower()}_vs_phy_csmf_difference_bars_{level}_{stratum}.svg"
        out.write_text("\n".join(parts), encoding="utf-8")
        paths.append(out)
    return paths


def heat_color(value: float, max_value: float) -> str:
    if max_value <= 0:
        ratio = 0
    else:
        ratio = min(max(value / max_value, 0), 1)
    start = (248, 250, 252)
    end = (30, 91, 128)
    rgb = tuple(round(start[i] + (end[i] - start[i]) * ratio) for i in range(3))
    return f"rgb({rgb[0]},{rgb[1]},{rgb[2]})"


def write_agreement_metrics_heatmap(metrics: pd.DataFrame) -> Path:
    data = metrics[(metrics["level"] == "level2") & (metrics["metric_type"].isin(["underlying", "direct", "contributory"]))].copy()
    data = data[data["comparison"].str.contains("PHY", na=False)]
    metric_cols = ["accuracy", "cohen_kappa", "recall_macro", "f1_macro", "recall_weighted", "f1_weighted"]
    rows = data[["metric_type", "comparison"] + metric_cols].drop_duplicates(subset=["metric_type", "comparison"])
    rows["label"] = rows.apply(compact_agreement_label, axis=1)
    metric_order = {"underlying": 0, "direct": 1, "contributory": 2}
    rows["metric_order"] = rows["metric_type"].map(metric_order)
    rows["experiment_order"] = rows["comparison"].str.extract(r"^(EXP[1-4])")[0].str.extract(r"EXP(\d)")[0].astype(int)
    rows = rows.sort_values(["metric_order", "experiment_order", "comparison"]).drop(columns=["metric_order", "experiment_order"])
    width = 1180
    height = 78 + 30 * len(rows) + 70
    left = 430
    top = 108
    cell_w = 112
    cell_h = 26
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#ffffff"/>',
        svg_text(left, 32, "Agreement Metrics Heatmap vs Physician (Level 2)", 22, weight="700"),
        svg_text(left, 54, "Darker cells indicate higher values.", 12, "#52616b"),
    ]
    for j, col in enumerate(metric_cols):
        parts.append(svg_text(left + j * cell_w + cell_w / 2, top - 16, col.replace("_", " "), 10, "#111827", anchor="middle", weight="700"))
    for i, row in enumerate(rows.itertuples(index=False)):
        y = top + i * cell_h
        parts.append(svg_text(left - 12, y + 17, row.label, 10, "#111827", anchor="end"))
        for j, col in enumerate(metric_cols):
            value = safe_float(getattr(row, col))
            x = left + j * cell_w
            color = heat_color(value, 1)
            text_fill = "#ffffff" if value > 0.55 else "#111827"
            parts.append(f'<rect x="{x}" y="{y}" width="{cell_w - 3}" height="{cell_h - 3}" fill="{color}"/>')
            parts.append(svg_text(x + cell_w / 2, y + 16, f"{value:.2f}", 10, text_fill, anchor="middle", weight="700"))
    parts.append("</svg>")
    out = OUTPUT_DIR / "figure_agreement_metrics_heatmap_level2.svg"
    out.write_text("\n".join(parts), encoding="utf-8")
    return out


def compact_agreement_label(row: pd.Series) -> str:
    exp = row["comparison"].split("_", 1)[0]
    metric_type = str(row["metric_type"]).replace("_", " ")
    return f"{exp} vs PHY ({metric_type})"


def write_confusion_bubble_plots(confusions: pd.DataFrame, level: str = "level2", metric_type: str = "underlying") -> list[Path]:
    paths = []
    data = confusions[(confusions["level"] == level) & (confusions["metric_type"] == metric_type)].copy()
    data = data[data["comparison"].str.contains("PHY", na=False)]
    for exp in EXPERIMENTS:
        sub = data[data["comparison"].str.contains(exp, na=False)].copy()
        if sub.empty:
            continue
        sub["n_cases"] = sub["n_cases"].astype(int)
        top_refs = sub.groupby("reference")["n_cases"].sum().sort_values(ascending=False).head(12).index.tolist()
        top_preds = sub.groupby("predicted")["n_cases"].sum().sort_values(ascending=False).head(12).index.tolist()
        sub = sub[sub["reference"].isin(top_refs) & sub["predicted"].isin(top_preds)]
        width = 960
        height = 840
        left = 150
        top = 122
        cell = 48
        max_n = max(int(sub["n_cases"].max()), 1)
        parts = [
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
            '<rect width="100%" height="100%" fill="#ffffff"/>',
            svg_text(left, 34, f"{exp} vs Physician Level 2 Underlying Confusions", 22, weight="700"),
            svg_text(left, 56, "Bubble size shows number of cases where PHY and LLM selected different Level 2 codes.", 12, "#52616b"),
        ]
        for i, ref in enumerate(top_refs):
            y = top + i * cell
            parts.append(svg_text(left - 14, y + 5, ref, 11, "#111827", anchor="end"))
            parts.append(f'<line x1="{left}" y1="{y}" x2="{left + len(top_preds) * cell}" y2="{y}" stroke="#eef2f7"/>')
        for j, pred in enumerate(top_preds):
            x = left + j * cell
            parts.append(svg_text(x + 2, top - 12, pred, 11, "#111827", anchor="middle"))
            parts.append(f'<line x1="{x}" y1="{top - 6}" x2="{x}" y2="{top + len(top_refs) * cell}" stroke="#eef2f7"/>')
        for row in sub.itertuples(index=False):
            x = left + top_preds.index(row.predicted) * cell
            y = top + top_refs.index(row.reference) * cell
            r = 4 + 18 * math.sqrt(int(row.n_cases) / max_n)
            parts.append(f'<circle cx="{x}" cy="{y}" r="{r}" fill="#2563eb" fill-opacity="0.62"/>')
            if int(row.n_cases) >= max(10, max_n * 0.25):
                parts.append(svg_text(x, y + 4, row.n_cases, 9, "#ffffff", anchor="middle", weight="700"))
        parts.append(svg_text(left + len(top_preds) * cell / 2, height - 42, "LLM predicted Level 2 code", 13, "#111827", anchor="middle"))
        parts.append(svg_text(30, top + len(top_refs) * cell / 2, "Physician reference Level 2 code", 13, "#111827", anchor="middle"))
        parts.append("</svg>")
        out = OUTPUT_DIR / f"figure_{exp.lower()}_vs_phy_confusion_bubble_underlying_{level}.svg"
        out.write_text("\n".join(parts), encoding="utf-8")
        paths.append(out)
    return paths


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    csmf_summary = pd.read_csv(OUTPUT_DIR / "csmf_accuracy_summary_underlying.csv")
    csmf_detail = pd.read_csv(OUTPUT_DIR / "csmf_accuracy_detail_underlying.csv")
    metrics_candidates = sorted(OUTPUT_DIR.glob("metrics_kappa_precision_recall_f1_by_level*.csv"), key=lambda p: p.stat().st_mtime, reverse=True)
    metrics = pd.read_csv(metrics_candidates[0])
    confusions = pd.read_csv(OUTPUT_DIR / "confusion_pairs_by_level.csv")

    paths = []
    paths.append(write_csmf_accuracy_dot_plot(csmf_summary))
    paths.extend(write_csmf_difference_bars(csmf_detail, "level2", "overall"))
    paths.append(write_agreement_metrics_heatmap(metrics))
    paths.extend(write_confusion_bubble_plots(confusions, "level2", "underlying"))

    index = pd.DataFrame({"figure": [path.name for path in paths], "path": [str(path.resolve()) for path in paths]})
    index.to_csv(OUTPUT_DIR / "comparison_visualization_index.csv", index=False)
    for path in paths:
        print(path.resolve())


if __name__ == "__main__":
    main()
