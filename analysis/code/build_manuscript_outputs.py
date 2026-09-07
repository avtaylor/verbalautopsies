"""Assemble the nine public manuscript deliverables from aggregate analysis outputs.

This stage never reads raw narratives or record-level tables. Run the calculation
scripts first, then run this file from anywhere. Outputs are written to
``manuscript_outputs/`` at the package root.
"""
from __future__ import annotations

import html
import shutil
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs"
WORK = ROOT / "working_outputs" / "agreement_analysis"
AGGREGATE_INPUTS = ROOT / "aggregate_inputs"


def locate(relative: str) -> Path:
    """Prefer a freshly generated working output, then the checked aggregate."""
    fresh = WORK / Path(relative).name
    if fresh.exists():
        return fresh
    aggregate = AGGREGATE_INPUTS / Path(relative).name
    return aggregate if aggregate.exists() else ROOT / relative


def read(relative: str) -> pd.DataFrame:
    return pd.read_csv(locate(relative))


def write_table(df: pd.DataFrame, stem: str, title: str, *, styled: bool = False) -> None:
    df.to_csv(OUT / f"{stem}.csv", index=False)
    css = """
body{font:14px/1.4 Arial,sans-serif;margin:28px;color:#172026}table{border-collapse:collapse}
caption{font-size:18px;font-weight:700;text-align:left;margin-bottom:12px}th,td{border:1px solid #cbd5e1;padding:6px 9px;text-align:right}th:first-child,td:first-child,th:nth-child(2),td:nth-child(2){text-align:left}thead{background:#e8efec}
td.mid{background:#d9ead3}td.high{background:#38761d;color:white;font-weight:700}
"""
    rows = []
    for _, row in df.iterrows():
        cells = []
        for col, value in row.items():
            cls = ""
            if styled and col not in {"cause_code", "cause_name", "total"}:
                try:
                    pct = float(str(value).rstrip("%"))
                    if pct > 30:
                        cls = ' class="high"'
                    elif 10 <= pct <= 20:
                        cls = ' class="mid"'
                except ValueError:
                    pass
            cells.append(f"<td{cls}>{html.escape(str(value))}</td>")
        rows.append("<tr>" + "".join(cells) + "</tr>")
    heads = "".join(f"<th>{html.escape(str(c))}</th>" for c in df.columns)
    document = f"<!doctype html><html><head><meta charset='utf-8'><title>{html.escape(title)}</title><style>{css}</style></head><body><table><caption>{html.escape(title)}</caption><thead><tr>{heads}</tr></thead><tbody>{''.join(rows)}</tbody></table></body></html>"
    (OUT / f"{stem}.html").write_text(document, encoding="utf-8")


def table_2() -> None:
    source = read("exp_underlying_distribution_level1_top_level2_phy_underlying_records_wide.csv")
    for column in [name for name in source.columns if name.endswith("_n")]:
        source[column] = pd.to_numeric(source[column], errors="raise").astype("Int64")
    write_table(source, "table_2_underlying_cod_distribution", "Table 2. Underlying CoD distributions for EXP1–EXP4: Level 1 and top Level 2")


def table_3() -> None:
    source = read("agreement/excel/summary_accuracy_related_measures_all_experiments.csv")
    selected = source[["experiment", "coding_level", "n_underlying_compared", "strict_underlying_accuracy", "strict_underlying_kappa", "strict_underlying_f1_macro", "strict_underlying_f1_weighted", "flexible_any_code_overlap", "flexible_mean_jaccard", "csmf_accuracy_underlying"]].copy()
    selected.columns = ["experiment", "coding_level", "n", "strict_accuracy", "strict_kappa", "f1_macro", "f1_weighted", "flexible_overlap", "jaccard_similarity", "csmf_accuracy"]
    write_table(selected, "table_3_experiment_comparison", "Table 3. Comparison of EXP1–EXP4 by coding level")


def table_4() -> None:
    source = read("jaccard/excel/jaccard_level2_pooled_distribution_by_vatype.csv")
    source = source[["va_type", "experiment", "jaccard_bin", "n", "percent"]]
    write_table(source, "table_4_level2_jaccard_bins", "Table 4. Flexible-match Jaccard similarity bins at Level 2")


def table_5() -> None:
    source = read("EXP1/excel/exp1_true_positive_overlap_level2_top20_by_vatype_age_percent_table.csv")
    write_table(source, "table_5_exp1_top20_true_positive_overlap", "Table 5. EXP1 top 20 Level-2 true-positive overlaps by VA type and age", styled=True)


def table_6() -> None:
    source = read("csmf/excel/underlying_pccc_single_prediction_by_level.csv")
    selected = source[["experiment", "level", "n_compared", "n_agree", "accuracy_C", "N_possible_causes", "pccc"]]
    write_table(selected, "table_6_strict_underlying_pccc", "Table 6. PCCC for strict underlying CoD agreement")


def chart_2() -> None:
    figures = [
        ("Overall", "agreement/charts/figure_flexible_any_code_agreement_by_level_overall.svg"),
        ("Adult", "agreement/charts/figure_flexible_any_code_agreement_by_level_adult.svg"),
        ("Child", "agreement/charts/figure_flexible_any_code_agreement_by_level_child.svg"),
        ("Infant", "agreement/charts/figure_flexible_any_code_agreement_by_level_infant.svg"),
    ]
    local_figures = []
    for label, path in figures:
        name = f"chart_2_panel_{label.lower()}.svg"
        shutil.copy2(locate(path), OUT / name)
        local_figures.append((label, name))
    panels = "".join(f"<figure><figcaption>{label}</figcaption><img src='{name}' alt='{label} flexible any-code agreement'></figure>" for label, name in local_figures)
    page = f"<!doctype html><html><head><meta charset='utf-8'><title>Figure 2</title><style>body{{font:16px Arial;margin:36px;color:#172026}}h1{{margin:0 0 34px;line-height:1.25}}main{{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:42px 34px}}figure{{margin:0;border:1px solid #cbd5e1;padding:24px 20px 20px}}figcaption{{font-weight:700;font-size:18px;margin:0 0 20px}}img{{display:block;width:100%;height:auto;margin-top:8px}}@media(max-width:800px){{main{{grid-template-columns:1fr}}}}</style></head><body><h1>Figure 2. Flexible any-code agreement by coding level and VA type</h1><main>{panels}</main></body></html>"
    (OUT / "figure_2_flexible_any_code_agreement_ensemble.html").write_text(page, encoding="utf-8")


def line_chart(data: pd.DataFrame, metric: str, va_type: str, title: str, filename: str) -> None:
    experiments = ["EXP1", "EXP2", "EXP3", "EXP4"]
    levels = ["level1", "level2", "level3"]
    colours = {"EXP1": "#2563eb", "EXP2": "#d97706", "EXP3": "#059669", "EXP4": "#dc2626"}
    width, height, left, right, top, bottom = 760, 500, 92, 150, 92, 78
    plot_w, plot_h = width - left - right, height - top - bottom
    subset = data[data["va_type"].astype(str).str.lower() == va_type].copy()
    values = pd.to_numeric(subset[metric], errors="coerce")
    y_min = max(0.0, float(values.min()) - 0.08)
    y_max = min(1.0, float(values.max()) + 0.08)
    if y_max <= y_min:
        y_min, y_max = 0.0, 1.0
    x = {level: left + i * plot_w / 2 for i, level in enumerate(levels)}
    y = lambda value: top + (y_max - value) / (y_max - y_min) * plot_h
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">', '<rect width="100%" height="100%" fill="#fff"/>', f'<text x="{left}" y="34" font-family="Arial" font-size="21" font-weight="700">{html.escape(title)}</text>', '<text x="92" y="58" font-family="Arial" font-size="12" fill="#52616b">One line per experiment; higher values indicate closer agreement.</text>']
    for i in range(5):
        value = y_min + i * (y_max - y_min) / 4
        yy = y(value)
        parts += [f'<line x1="{left}" y1="{yy}" x2="{left+plot_w}" y2="{yy}" stroke="#e2e8f0"/>', f'<text x="{left-14}" y="{yy+4}" text-anchor="end" font-family="Arial" font-size="11">{value:.2f}</text>']
    for level in levels:
        parts.append(f'<text x="{x[level]}" y="{top+plot_h+34}" text-anchor="middle" font-family="Arial" font-size="13">{level.replace("level", "Level ")}</text>')
    for exp in experiments:
        rows = subset[subset["experiment"] == exp].set_index("level")
        points = [(x[level], y(float(rows.loc[level, metric]))) for level in levels if level in rows.index]
        if not points:
            continue
        path = " ".join(f'{"M" if i == 0 else "L"} {px:.1f} {py:.1f}' for i, (px, py) in enumerate(points))
        parts.append(f'<path d="{path}" fill="none" stroke="{colours[exp]}" stroke-width="2.8"/>')
        for px, py in points:
            parts.append(f'<circle cx="{px:.1f}" cy="{py:.1f}" r="5" fill="{colours[exp]}"/>')
    parts.append(f'<text x="26" y="{top+plot_h/2}" transform="rotate(-90 26 {top+plot_h/2})" text-anchor="middle" font-family="Arial" font-size="14" font-weight="700">Score</text>')
    for i, exp in enumerate(experiments):
        yy = top + 18 + i * 32
        parts += [f'<line x1="{left+plot_w+32}" y1="{yy}" x2="{left+plot_w+60}" y2="{yy}" stroke="{colours[exp]}" stroke-width="3"/>', f'<text x="{left+plot_w+70}" y="{yy+4}" font-family="Arial" font-size="12">{exp}</text>']
    parts.append('</svg>')
    (OUT / filename).write_text("\n".join(parts), encoding="utf-8")


def figure_4() -> None:
    pccc = read("underlying_pccc_single_prediction_by_vatype.csv")
    csmf = read("csmf_accuracy_summary_underlying_by_va_type.csv")
    files = []
    for va_type in ["adult", "child", "infant"]:
        pccc_name = f"figure_4_pccc_{va_type}.svg"
        csmf_name = f"figure_4_csmf_{va_type}.svg"
        line_chart(pccc, "pccc", va_type, f"PCCC: {va_type.title()} VA", pccc_name)
        line_chart(csmf, "csmf_accuracy_chance_corrected", va_type, f"CSMF accuracy: {va_type.title()} VA", csmf_name)
        files.extend([(f"PCCC: {va_type.title()}", pccc_name), (f"CSMF accuracy: {va_type.title()}", csmf_name)])
    panels = "".join(f"<figure><figcaption>{label}</figcaption><img src='{name}' alt='{label} by experiment and coding level'></figure>" for label, name in files)
    page = f"<!doctype html><html><head><meta charset='utf-8'><title>Figure 4</title><style>body{{font:16px Arial;margin:36px;color:#172026}}main{{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:34px}}figure{{margin:0;border:1px solid #cbd5e1;padding:18px}}figcaption{{font-weight:700;margin-bottom:12px}}img{{display:block;width:100%;height:auto}}</style></head><body><h1>Figure 4. PCCC and CSMF accuracy by experiment, coding level and VA type</h1><main>{panels}</main></body></html>"
    (OUT / "figure_4_pccc_csmf_line_charts.html").write_text(page, encoding="utf-8")


def figure_3() -> None:
    data = read("EXP1/excel/exp1_vs_physician_underlying_level2_distribution_difference_top10_by_vatype.csv")
    groups = [name for name in ["adult", "child", "infant"] if name in set(data["va_type"])]
    width, panel_w, left, top, row_h = 1500, 430, 170, 105, 31
    height = top + 10 * row_h + 70
    max_abs = max(float(data["difference_pp"].abs().max()), 1.0)
    scale = (panel_w / 2 - 22) / max_abs
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">', '<rect width="100%" height="100%" fill="#fff"/>', '<text x="24" y="34" font-family="Arial" font-size="22" font-weight="700">Figure 3. Largest Differences Between EXP1 and Physician-Assigned Level 2 Underlying Cause Distributions by VA Type</text>', '<text x="24" y="58" font-family="Arial" font-size="12" fill="#52616b">Percentage-point difference (EXP1 minus physician); ten largest absolute differences within each VA type.</text>']
    for g, va in enumerate(groups):
        sub = data[data["va_type"] == va].sort_values("difference_pp")
        x0 = left + g * panel_w
        zero = x0 + panel_w / 2
        parts += [f'<text x="{zero}" y="86" text-anchor="middle" font-family="Arial" font-size="15" font-weight="700">{html.escape(va.title())}</text>', f'<line x1="{zero}" y1="{top-8}" x2="{zero}" y2="{top+10*row_h}" stroke="#334155"/>']
        for i, row in enumerate(sub.itertuples(index=False)):
            y = top + i * row_h
            value = float(row.difference_pp)
            bar_x = zero if value >= 0 else zero + value * scale
            bar_w = abs(value * scale)
            color = "#16856b" if value >= 0 else "#c75050"
            label = f"{row.cause_code} {row.cause_name}"[:42]
            parts += [f'<text x="{zero-8}" y="{y+16}" text-anchor="end" font-family="Arial" font-size="10">{html.escape(label)}</text>', f'<rect x="{bar_x}" y="{y+3}" width="{bar_w}" height="18" fill="{color}"/>', f'<text x="{zero + value*scale + (6 if value >= 0 else -6)}" y="{y+16}" text-anchor="{"start" if value >= 0 else "end"}" font-family="Arial" font-size="10">{value:+.1f}</text>']
    parts.append('</svg>')
    (OUT / "figure_3_exp1_vs_physician_level2_differences.svg").write_text("\n".join(parts), encoding="utf-8")


def copy_figures() -> None:
    targets = {
        "csmf/charts/figure_level2_csmf_observed_vs_mc_physician_prior.svg": "figure_5_observed_vs_monte_carlo.svg",
    }
    for source, name in targets.items():
        shutil.copy2(locate(source), OUT / name)


def main() -> None:
    OUT.mkdir(exist_ok=True)
    for obsolete in ["chart_2_flexible_any_code_agreement_ensemble.html", "figure_4_csmf_accuracy.svg"]:
        (OUT / obsolete).unlink(missing_ok=True)
    table_2(); table_3(); chart_2(); table_4(); table_5(); figure_3(); figure_4(); copy_figures(); table_6()
    print(f"Wrote manuscript deliverables to {OUT}")


if __name__ == "__main__":
    main()
