from __future__ import annotations

from pathlib import Path

import pandas as pd

from analysis_llm_phy_agreement import (
    BLANK_CODE,
    CODE_LEVELS,
    DATA_DIR,
    OUTPUT_DIR,
    advanced_evaluation_outputs,
    build_master,
    code_at_level,
    code_set_at_level,
    flexible_overlap_outputs,
    load_experiment,
    parse_codebook,
    single_label_classification_metrics,
)
from calculate_csmf_accuracy import csmf_metrics


EXP = "EXP1"


def narrative_ids() -> set[str]:
    narratives = pd.read_excel(
        DATA_DIR / "All_Naratives.xlsx",
        sheet_name="All_Narratives",
        dtype=str,
        usecols=["ident", "va_narrative"],
    )
    narratives["ident"] = narratives["ident"].astype(str).str.strip()
    has_original = narratives["va_narrative"].notna() & narratives["va_narrative"].astype(str).str.strip().ne("")
    return set(narratives.loc[has_original, "ident"])


def pccc_table(master: pd.DataFrame, codebook: pd.DataFrame) -> pd.DataFrame:
    possible = {
        "level1": codebook["code"].str[:2].nunique(),
        "level2": codebook["code"].str[:5].nunique(),
        "full": codebook["code"].nunique(),
    }
    rows = []
    comparable = master[master["PHY_underlying"].apply(lambda x: code_at_level(x, "level1") != BLANK_CODE)].copy()
    for level in CODE_LEVELS:
        ref = comparable["PHY_underlying"].apply(lambda x: code_at_level(x, level))
        pred = comparable[f"{EXP}_underlying"].apply(lambda x: code_at_level(x, level))
        n = len(comparable)
        agree = int((ref == pred).sum())
        accuracy = agree / n if n else None
        n_possible = possible[level]
        pccc = (accuracy - (1 / n_possible)) / (1 - (1 / n_possible)) if accuracy is not None and n_possible > 1 else None
        rows.append(
            {
                "experiment": EXP,
                "level": "level3" if level == "full" else level,
                "n_compared": n,
                "n_agree": agree,
                "accuracy_C": accuracy,
                "N_possible_causes": n_possible,
                "k": 1,
                "pccc": pccc,
            }
        )
    return pd.DataFrame(rows)


def jaccard_summary(master: pd.DataFrame) -> pd.DataFrame:
    rows = []
    comparable = master[master["PHY_underlying"].apply(lambda x: code_at_level(x, "level1") != BLANK_CODE)].copy()
    for level in CODE_LEVELS:
        scores = []
        exact = 0
        any_overlap = 0
        for _, row in comparable.iterrows():
            left = (
                code_set_at_level(row[f"{EXP}_direct"], level)
                | code_set_at_level(row[f"{EXP}_underlying"], level)
                | code_set_at_level(row[f"{EXP}_contrib_set"], level)
            )
            right = (
                code_set_at_level(row["PHY_direct"], level)
                | code_set_at_level(row["PHY_underlying"], level)
                | code_set_at_level(row["PHY_contrib"], level)
            )
            left.discard(BLANK_CODE)
            right.discard(BLANK_CODE)
            if not left and not right:
                continue
            score = len(left & right) / len(left | right) if (left | right) else None
            if score is None:
                continue
            scores.append(score)
            exact += int(left == right)
            any_overlap += int(bool(left & right))
        s = pd.Series(scores, dtype=float)
        rows.append(
            {
                "comparison_type": "flexible_pooled_any_type",
                "comparison": f"{EXP}_pooled_any_type vs PHY_pooled_any_type",
                "level": "level3" if level == "full" else level,
                "n_compared": int(len(s)),
                "mean_jaccard": float(s.mean()) if len(s) else None,
                "median_jaccard": float(s.median()) if len(s) else None,
                "q25_jaccard": float(s.quantile(0.25)) if len(s) else None,
                "q75_jaccard": float(s.quantile(0.75)) if len(s) else None,
                "n_exact_set_match": exact,
                "exact_set_match": exact / len(s) if len(s) else None,
                "n_any_overlap": any_overlap,
                "any_overlap": any_overlap / len(s) if len(s) else None,
            }
        )
    return pd.DataFrame(rows)


def csmf_table(master: pd.DataFrame) -> pd.DataFrame:
    rows = []
    comparable = master[master["PHY_underlying"].apply(lambda x: code_at_level(x, "level1") != BLANK_CODE)].copy()
    for level in CODE_LEVELS:
        ref = comparable["PHY_underlying"].dropna().apply(lambda x: code_at_level(x, level))
        pred = comparable[f"{EXP}_underlying"].dropna().apply(lambda x: code_at_level(x, level))
        metrics, _ = csmf_metrics(ref, pred)
        rows.append({"experiment": EXP, "level": "level3" if level == "full" else level, **metrics})
    return pd.DataFrame(rows)


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    codebook, compact_lookup = parse_codebook()
    master = build_master(compact_lookup)
    ids = narrative_ids()
    master = master[master["ident"].astype(str).str.strip().isin(ids)].copy()

    evaluations = {"EXP1 narrative-present sensitivity": [EXP]}
    metrics, per_class, confusion_pairs, confusion_cases = advanced_evaluation_outputs(master, evaluations)
    flexible_metrics, no_overlap, fpfn_frequency, fpfn_cases = flexible_overlap_outputs(master, evaluations)
    pccc = pccc_table(master, codebook)
    jaccard = jaccard_summary(master)
    csmf = csmf_table(master)

    outputs = {
        "exp1_narrative_present_metrics_by_level.csv": metrics,
        "exp1_narrative_present_per_class_metrics_by_level.csv": per_class,
        "exp1_narrative_present_confusion_pairs_by_level.csv": confusion_pairs,
        "exp1_narrative_present_confusion_cases_by_level.csv": confusion_cases,
        "exp1_narrative_present_flexible_any_type_overlap_by_level.csv": flexible_metrics,
        "exp1_narrative_present_flexible_no_overlap_cases_by_level.csv": no_overlap,
        "exp1_narrative_present_flexible_fpfn_frequency_by_level.csv": fpfn_frequency,
        "exp1_narrative_present_flexible_fpfn_cases_by_level.csv": fpfn_cases,
        "exp1_narrative_present_pccc_by_level.csv": pccc,
        "exp1_narrative_present_jaccard_by_level.csv": jaccard,
        "exp1_narrative_present_csmf_accuracy_by_level.csv": csmf,
    }
    for name, df in outputs.items():
        path = OUTPUT_DIR / name
        df.to_csv(path, index=False)
        print(path.resolve())

    print("\nStrict underlying EXP1 narrative-present subset:")
    strict = metrics[(metrics["metric_type"] == "underlying") & (metrics["comparison"] == "EXP1_underlying vs PHY_underlying")]
    print(strict[["level", "n_compared", "accuracy", "cohen_kappa", "f1_macro", "f1_weighted"]].to_string(index=False))
    print("\nPCCC:")
    print(pccc.to_string(index=False))


if __name__ == "__main__":
    main()
