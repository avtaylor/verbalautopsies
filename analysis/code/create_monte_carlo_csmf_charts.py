from __future__ import annotations

import html
from pathlib import Path

import pandas as pd


OUTPUT_DIR = Path("outputs") / "agreement_analysis"
EXPERIMENTS = ["EXP1", "EXP2", "EXP3", "EXP4"]
EXP_COLORS = {
    "EXP1": "#2563eb",
    "EXP2": "#d97706",
    "EXP3": "#059669",
    "EXP4": "#dc2626",
}
VA_TYPES = ["overall", "adult", "child", "infant"]
NULL_LABELS = {
    "uniform_codes": "Uniform random",
    "overall_physician_prior": "Physician-prior random",
}
LEVEL_LABELS = {"level1": "Level 1", "level2": "Level 2", "level3": "Level 3"}


def svg_text(x: float, y: float, text: object, size: int = 12, fill: str = "#111827", anchor: str = "start", weight: str = "400") -> str:
    return (
        f'<text x="{x}" y="{y}" text-anchor="{anchor}" font-family="Arial, sans-serif" '
        f'font-size="{size}" font-weight="{weight}" fill="{fill}">{html.escape(str(text))}</text>'
    )


def x_scale(value: float, left: float, plot_w: float, x_min: float = 0.25, x_max: float = 1.0) -> float:
    return left + (value - x_min) / (x_max - x_min) * plot_w


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(value, high))


def write_prior_baseline_chart(summary: pd.DataFrame, level: str) -> Path:
    data = summary[(summary["level"] == level) & (summary["null_model"] == "overall_physician_prior")].copy()
    data = data[data["va_type"].isin(VA_TYPES)]
    width = 1120
    height = 940
    left = 178
    right = 160
    top = 118
    bottom = 70
    plot_w = width - left - right
    row_gap = 34
    facet_gap = 38
    x_min, x_max = 0.25, 1.0

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#ffffff"/>',
        svg_text(left, 34, f"Observed {LEVEL_LABELS[level]} CSMF Accuracy vs Monte Carlo Physician-Prior Baseline", 23, weight="700"),
        svg_text(left, 58, "Lines show simulated 95% intervals; hollow dots show null means; filled dots show observed EXP values.", 12, "#52616b"),
    ]

    for tick in [0.25, 0.5, 0.75, 1.0]:
        x = x_scale(tick, left, plot_w, x_min, x_max)
        parts.append(f'<line x1="{x}" y1="{top}" x2="{x}" y2="{height - bottom}" stroke="#e5e7eb" stroke-width="1"/>')
        parts.append(svg_text(x, height - bottom + 28, f"{tick:.2f}", 11, "#374151", "middle"))

    y = top
    for va_type in VA_TYPES:
        parts.append(svg_text(24, y + 16, va_type.title(), 14, "#111827", weight="700"))
        y += 24
        sub = data[data["va_type"] == va_type]
        for exp in EXPERIMENTS:
            row = sub[sub["experiment"] == exp]
            if row.empty:
                continue
            r = row.iloc[0]
            y_mid = y
            color = EXP_COLORS[exp]
            x_lo = clamp(x_scale(float(r["null_p2_5"]), left, plot_w, x_min, x_max), left, left + plot_w)
            x_hi = clamp(x_scale(float(r["null_p97_5"]), left, plot_w, x_min, x_max), left, left + plot_w)
            x_mean = clamp(x_scale(float(r["null_mean"]), left, plot_w, x_min, x_max), left, left + plot_w)
            x_obs = clamp(x_scale(float(r["observed_csmf_accuracy"]), left, plot_w, x_min, x_max), left, left + plot_w)
            parts.append(svg_text(left - 18, y_mid + 4, exp, 11, "#374151", "end"))
            parts.append(f'<line x1="{x_lo}" y1="{y_mid}" x2="{x_hi}" y2="{y_mid}" stroke="#94a3b8" stroke-width="5" stroke-linecap="round"/>')
            parts.append(f'<circle cx="{x_mean}" cy="{y_mid}" r="5.5" fill="#ffffff" stroke="#334155" stroke-width="2"/>')
            parts.append(f'<circle cx="{x_obs}" cy="{y_mid}" r="6.5" fill="{color}"/>')
            parts.append(svg_text(x_obs + 9, y_mid + 4, f"{float(r['observed_csmf_accuracy']):.3f}", 10, "#111827"))
            y += row_gap
        y += facet_gap

    parts.append(svg_text(left + plot_w / 2, height - 18, "CSMF accuracy", 14, "#111827", "middle", "700"))
    legend_x = width - right + 14
    legend_y = top + 4
    parts.append(f'<line x1="{legend_x}" y1="{legend_y}" x2="{legend_x + 34}" y2="{legend_y}" stroke="#94a3b8" stroke-width="5" stroke-linecap="round"/>')
    parts.append(svg_text(legend_x + 44, legend_y + 4, "Null 95% interval", 11))
    parts.append(f'<circle cx="{legend_x + 17}" cy="{legend_y + 28}" r="5.5" fill="#ffffff" stroke="#334155" stroke-width="2"/>')
    parts.append(svg_text(legend_x + 44, legend_y + 32, "Null mean", 11))
    parts.append(f'<circle cx="{legend_x + 17}" cy="{legend_y + 56}" r="6.5" fill="#2563eb"/>')
    parts.append(svg_text(legend_x + 44, legend_y + 60, "Observed", 11))
    parts.append("</svg>")

    out = OUTPUT_DIR / f"figure_monte_carlo_csmf_{level}_physician_prior.svg"
    out.write_text("\n".join(parts), encoding="utf-8")
    return out


def write_overall_null_comparison(summary: pd.DataFrame, level: str) -> Path:
    data = summary[(summary["level"] == level) & (summary["va_type"] == "overall")].copy()
    data = data[data["null_model"].isin(NULL_LABELS)]
    width = 1060
    height = 520
    left = 220
    right = 115
    top = 104
    bottom = 72
    plot_w = width - left - right
    row_gap = 40
    null_gap = 16
    x_min, x_max = 0.25, 1.0

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#ffffff"/>',
        svg_text(left, 34, f"Overall {LEVEL_LABELS[level]} CSMF Accuracy Against Monte Carlo Null Models", 23, weight="700"),
        svg_text(left, 58, "Observed values are compared with uniform random coding and physician-prior random coding.", 12, "#52616b"),
    ]

    for tick in [0.25, 0.5, 0.75, 1.0]:
        x = x_scale(tick, left, plot_w, x_min, x_max)
        parts.append(f'<line x1="{x}" y1="{top}" x2="{x}" y2="{height - bottom}" stroke="#e5e7eb" stroke-width="1"/>')
        parts.append(svg_text(x, height - bottom + 28, f"{tick:.2f}", 11, "#374151", "middle"))

    y = top + 12
    for exp in EXPERIMENTS:
        parts.append(svg_text(32, y + 20, exp, 13, "#111827", weight="700"))
        exp_data = data[data["experiment"] == exp]
        observed = float(exp_data.iloc[0]["observed_csmf_accuracy"]) if not exp_data.empty else None
        for null_model in ["uniform_codes", "overall_physician_prior"]:
            row = exp_data[exp_data["null_model"] == null_model]
            if row.empty:
                continue
            r = row.iloc[0]
            y_mid = y
            x_lo = clamp(x_scale(float(r["null_p2_5"]), left, plot_w, x_min, x_max), left, left + plot_w)
            x_hi = clamp(x_scale(float(r["null_p97_5"]), left, plot_w, x_min, x_max), left, left + plot_w)
            x_mean = clamp(x_scale(float(r["null_mean"]), left, plot_w, x_min, x_max), left, left + plot_w)
            parts.append(svg_text(left - 18, y_mid + 4, NULL_LABELS[null_model], 11, "#374151", "end"))
            parts.append(f'<line x1="{x_lo}" y1="{y_mid}" x2="{x_hi}" y2="{y_mid}" stroke="#94a3b8" stroke-width="5" stroke-linecap="round"/>')
            parts.append(f'<circle cx="{x_mean}" cy="{y_mid}" r="5.5" fill="#ffffff" stroke="#334155" stroke-width="2"/>')
            if observed is not None:
                x_obs = clamp(x_scale(observed, left, plot_w, x_min, x_max), left, left + plot_w)
                parts.append(f'<circle cx="{x_obs}" cy="{y_mid}" r="6.5" fill="{EXP_COLORS[exp]}"/>')
                parts.append(svg_text(x_obs + 9, y_mid + 4, f"{observed:.3f}", 10, "#111827"))
            y += row_gap - null_gap
        y += row_gap

    parts.append(svg_text(left + plot_w / 2, height - 18, "CSMF accuracy", 14, "#111827", "middle", "700"))
    parts.append("</svg>")

    out = OUTPUT_DIR / f"figure_monte_carlo_csmf_{level}_overall_nulls.svg"
    out.write_text("\n".join(parts), encoding="utf-8")
    return out


def main() -> None:
    summary = pd.read_csv(OUTPUT_DIR / "monte_carlo_csmf_accuracy_baselines_1000sim.csv")
    paths = []
    for level in ["level1", "level2", "level3"]:
        paths.append(write_prior_baseline_chart(summary, level))
        paths.append(write_overall_null_comparison(summary, level))
    for path in paths:
        print(path.resolve())


if __name__ == "__main__":
    main()
