from __future__ import annotations

import json
import re
from itertools import combinations
from pathlib import Path
from datetime import datetime

import pandas as pd


DATA_DIR = Path(r"C:\Users\Lenovo\Downloads\MEIRU_VA_EXP")
OUTPUT_DIR = Path("outputs") / "agreement_analysis"

CODEBOOK_FILE = DATA_DIR / "MEIRU_CODS_LIST.txt"

EXPERIMENT_FILES = {
    "EXP1": DATA_DIR / "EXP1.xlsx",
    "EXP2": DATA_DIR / "EXP2.xlsx",
    "EXP3": DATA_DIR / "EXP3.xlsx",
    "EXP4": DATA_DIR / "EXP4.xlsx",
}
PHY_FILE = DATA_DIR / "PHY.xlsx"
VA_TYPE_FILE = DATA_DIR / "va_type.csv"
AGE_SEX_FILE = DATA_DIR / "age_sex.csv"


CODE_PATTERN = re.compile(r"\b(\d{1,2})\s*-\s*(\d{1,2})\s*-\s*(\d{1,2})\b")
BLANK_CODE = "BLANK"
CODE_LEVELS = ("full", "level2", "level1")


def canonical_code(groups: tuple[str, str, str]) -> str:
    return "-".join(f"{int(part):02d}" for part in groups)


def parse_codebook() -> tuple[pd.DataFrame, dict[str, str]]:
    text = CODEBOOK_FILE.read_text(encoding="utf-8-sig")
    matches = list(CODE_PATTERN.finditer(text))
    rows = []
    for i, match in enumerate(matches):
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        desc = text[start:end]
        desc = desc.replace("|", "", 1).strip()
        desc = re.sub(r"\s+", " ", desc)
        code = canonical_code(match.groups())
        rows.append({"code": code, "description": desc})

    codebook = pd.DataFrame(rows).drop_duplicates("code")
    compact_lookup: dict[str, str] = {}

    for code in codebook["code"]:
        a, b, c = [int(x) for x in code.split("-")]
        candidates = {
            code,
            code.replace("-", ""),
            f"{a}{b}{c}",
            f"{a:02d}{b:02d}{c:02d}",
        }
        if c == 0:
            candidates.add(f"{a}{b}0")
        if b == 99 and c == 0:
            candidates.add(f"{a}99")
        if c == 99:
            candidates.add(f"{a}{b}99")
        if a == 99 and b == 0 and c == 0:
            candidates.update({"99", "990", "9900"})

        for candidate in candidates:
            compact_lookup.setdefault(candidate, code)

    return codebook, compact_lookup


def normalize_one_code(value: object, compact_lookup: dict[str, str]) -> str | None:
    if pd.isna(value):
        return None

    raw = str(value).strip()
    if not raw or raw.lower() in {"nan", "none", "null", "na", "n/a"}:
        return None

    match = CODE_PATTERN.search(raw)
    if match:
        code = canonical_code(match.groups())
        return compact_lookup.get(code, code)

    digits = re.sub(r"\D", "", raw)
    if not digits:
        return None
    if digits in compact_lookup:
        return compact_lookup[digits]
    if len(digits) == 6:
        code = f"{digits[:2]}-{digits[2:4]}-{digits[4:6]}"
        return compact_lookup.get(code, code)
    return None


def normalize_code_list(value: object, compact_lookup: dict[str, str]) -> list[str]:
    if pd.isna(value):
        return []
    raw = str(value)
    codes = [canonical_code(m.groups()) for m in CODE_PATTERN.finditer(raw)]
    if not codes:
        parts = re.split(r"[,;/|]+|\band\b", raw, flags=re.I)
        codes = [normalize_one_code(part, compact_lookup) for part in parts]
    else:
        codes = [compact_lookup.get(code, code) for code in codes]
    return sorted({code for code in codes if code})


def strip_json_fence(value: str) -> str:
    text = value.strip()
    text = re.sub(r"^`{2,3}\s*json\s*", "", text, flags=re.I)
    text = re.sub(r"^`{2,3}\s*", "", text)
    text = re.sub(r"\s*`{2,3}$", "", text)
    return text.strip()


def extract_exp1_row(value: object, compact_lookup: dict[str, str]) -> tuple[str | None, str | None, list[str], str]:
    if pd.isna(value):
        return None, None, [], "empty"

    text = strip_json_fence(str(value))
    try:
        parsed = json.loads(text)
        direct = normalize_one_code(
            parsed.get("direct_cause_of_death", {}).get("selected_full_code"),
            compact_lookup,
        )
        underlying = normalize_one_code(
            parsed.get("underlying_cause_of_death", {}).get("selected_full_code"),
            compact_lookup,
        )
        contributory_items = parsed.get("contributory_causes_of_death", [])
        contributory = [
            normalize_one_code(item.get("selected_full_code"), compact_lookup)
            for item in contributory_items
            if isinstance(item, dict)
        ]
        return direct, underlying, sorted({c for c in contributory if c}), "json"
    except Exception:
        codes = [canonical_code(m.groups()) for m in CODE_PATTERN.finditer(text)]
        codes = [compact_lookup.get(code, code) for code in codes]
        direct = codes[0] if len(codes) >= 1 else None
        underlying = codes[1] if len(codes) >= 2 else None
        contributory = sorted(set(codes[2:])) if len(codes) >= 3 else []
        return direct, underlying, contributory, "regex_fallback"


def load_experiment(name: str, compact_lookup: dict[str, str]) -> pd.DataFrame:
    df = pd.read_excel(EXPERIMENT_FILES[name], sheet_name=name, dtype=str)
    out = pd.DataFrame({"ident": df["ident"].astype(str).str.strip()})

    if name == "EXP1":
        extracted = df["MERGED"].apply(lambda x: extract_exp1_row(x, compact_lookup))
        out[f"{name}_direct"] = [x[0] for x in extracted]
        out[f"{name}_underlying"] = [x[1] for x in extracted]
        out[f"{name}_contrib_set"] = [x[2] for x in extracted]
        out[f"{name}_parse_method"] = [x[3] for x in extracted]
        return out

    out[f"{name}_direct"] = df["LLM_DIRECT_CODE"].apply(lambda x: normalize_one_code(x, compact_lookup))
    out[f"{name}_underlying"] = df["LLM_UNDERLYING_CODE"].apply(lambda x: normalize_one_code(x, compact_lookup))
    out[f"{name}_contrib_set"] = df["LLM_CONTRIBUTORY_CODES"].apply(lambda x: normalize_code_list(x, compact_lookup))
    out[f"{name}_parse_method"] = "columns"
    return out


def load_phy(compact_lookup: dict[str, str]) -> pd.DataFrame:
    df = pd.read_excel(PHY_FILE, sheet_name="PHY", dtype=str)
    return pd.DataFrame(
        {
            "ident": df["ident"].astype(str).str.strip(),
            "PHY_direct": df["PHY_DIRECT"].apply(lambda x: normalize_one_code(x, compact_lookup)),
            "PHY_underlying": df["PHYSICIAN_UNDERLYING_CODES"].apply(lambda x: normalize_one_code(x, compact_lookup)),
            "PHY_contrib": df["PHY_CONTRB"].apply(lambda x: normalize_one_code(x, compact_lookup)),
        }
    )


def build_master(compact_lookup: dict[str, str]) -> pd.DataFrame:
    master = load_phy(compact_lookup)
    for name in EXPERIMENT_FILES:
        master = master.merge(load_experiment(name, compact_lookup), on="ident", how="outer", validate="one_to_one")

    va_type = pd.read_csv(VA_TYPE_FILE, dtype=str)
    age_sex = pd.read_csv(AGE_SEX_FILE, dtype=str)
    master = master.merge(va_type, on="ident", how="left", validate="one_to_one")
    master = master.merge(age_sex, on="ident", how="left", validate="one_to_one")
    master["Age_num"] = pd.to_numeric(master["Age"], errors="coerce")
    master["age_group"] = pd.cut(
        master["Age_num"],
        bins=[-1, 0, 4, 14, 49, 64, 200],
        labels=["0", "1-4", "5-14", "15-49", "50-64", "65+"],
    ).astype(str)
    return master


def code_at_level(code: object, level: str) -> str:
    if pd.isna(code) or code is None or str(code).strip() == "":
        return BLANK_CODE
    text = str(code).strip()
    if text == BLANK_CODE:
        return BLANK_CODE
    if level == "full":
        return text
    if level == "level2":
        return text[:5] if len(text) >= 5 else text
    if level == "level1":
        return text[:2] if len(text) >= 2 else text
    raise ValueError(f"Unsupported code level: {level}")


def code_set_at_level(codes: object, level: str) -> set[str]:
    if not isinstance(codes, list) or not codes:
        return {BLANK_CODE}
    transformed = {code_at_level(code, level) for code in codes if code_at_level(code, level) != BLANK_CODE}
    return transformed or {BLANK_CODE}


def nonblank_code_set(codes: object, level: str) -> set[str]:
    return {code for code in code_set_at_level(codes, level) if code != BLANK_CODE}


def safe_divide(numerator: int | float, denominator: int | float) -> float | None:
    return numerator / denominator if denominator else None


def cohen_kappa_from_labels(y_true: list[str], y_pred: list[str]) -> float | None:
    n = len(y_true)
    if n == 0:
        return None
    labels = sorted(set(y_true) | set(y_pred))
    observed = sum(t == p for t, p in zip(y_true, y_pred)) / n
    true_counts = pd.Series(y_true).value_counts().to_dict()
    pred_counts = pd.Series(y_pred).value_counts().to_dict()
    expected = sum((true_counts.get(label, 0) / n) * (pred_counts.get(label, 0) / n) for label in labels)
    if expected == 1:
        return 1.0 if observed == 1 else None
    return (observed - expected) / (1 - expected)


def single_label_classification_metrics(y_true: list[str], y_pred: list[str]) -> dict[str, object]:
    labels = sorted(set(y_true) | set(y_pred))
    n = len(y_true)
    correct = sum(t == p for t, p in zip(y_true, y_pred))
    per_label = []
    total_support = 0
    weighted_precision = 0.0
    weighted_recall = 0.0
    weighted_f1 = 0.0
    macro_precision_values = []
    macro_recall_values = []
    macro_f1_values = []

    for label in labels:
        tp = sum(t == label and p == label for t, p in zip(y_true, y_pred))
        fp = sum(t != label and p == label for t, p in zip(y_true, y_pred))
        fn = sum(t == label and p != label for t, p in zip(y_true, y_pred))
        support = tp + fn
        precision = safe_divide(tp, tp + fp)
        recall = safe_divide(tp, tp + fn)
        f1 = safe_divide(2 * precision * recall, precision + recall) if precision is not None and recall is not None else None
        precision_value = precision if precision is not None else 0.0
        recall_value = recall if recall is not None else 0.0
        f1_value = f1 if f1 is not None else 0.0
        macro_precision_values.append(precision_value)
        macro_recall_values.append(recall_value)
        macro_f1_values.append(f1_value)
        weighted_precision += precision_value * support
        weighted_recall += recall_value * support
        weighted_f1 += f1_value * support
        total_support += support
        per_label.append(
            {
                "class": label,
                "support": support,
                "tp": tp,
                "fp": fp,
                "fn": fn,
                "precision": precision,
                "recall": recall,
                "f1": f1,
            }
        )

    return {
        "n_compared": n,
        "n_agree": correct,
        "accuracy": safe_divide(correct, n),
        "cohen_kappa": cohen_kappa_from_labels(y_true, y_pred),
        "precision_macro": sum(macro_precision_values) / len(labels) if labels else None,
        "recall_macro": sum(macro_recall_values) / len(labels) if labels else None,
        "f1_macro": sum(macro_f1_values) / len(labels) if labels else None,
        "precision_weighted": safe_divide(weighted_precision, total_support),
        "recall_weighted": safe_divide(weighted_recall, total_support),
        "f1_weighted": safe_divide(weighted_f1, total_support),
        "precision_micro": safe_divide(correct, n),
        "recall_micro": safe_divide(correct, n),
        "f1_micro": safe_divide(correct, n),
        "per_class": per_label,
    }


def multilabel_metrics(y_true_sets: list[set[str]], y_pred_sets: list[set[str]]) -> dict[str, object]:
    labels = sorted(set().union(*y_true_sets, *y_pred_sets)) if y_true_sets or y_pred_sets else []
    rows = []
    total_tp = total_fp = total_fn = 0
    weighted_precision = weighted_recall = weighted_f1 = 0.0
    total_support = 0
    label_kappas = []

    for label in labels:
        true_binary = [label in values for values in y_true_sets]
        pred_binary = [label in values for values in y_pred_sets]
        tp = sum(t and p for t, p in zip(true_binary, pred_binary))
        fp = sum((not t) and p for t, p in zip(true_binary, pred_binary))
        fn = sum(t and (not p) for t, p in zip(true_binary, pred_binary))
        support = tp + fn
        precision = safe_divide(tp, tp + fp)
        recall = safe_divide(tp, tp + fn)
        f1 = safe_divide(2 * precision * recall, precision + recall) if precision is not None and recall is not None else None
        kappa = cohen_kappa_from_labels(
            ["1" if value else "0" for value in true_binary],
            ["1" if value else "0" for value in pred_binary],
        )
        if kappa is not None:
            label_kappas.append((kappa, support))
        total_tp += tp
        total_fp += fp
        total_fn += fn
        weighted_precision += (precision or 0.0) * support
        weighted_recall += (recall or 0.0) * support
        weighted_f1 += (f1 or 0.0) * support
        total_support += support
        rows.append(
            {
                "class": label,
                "support": support,
                "tp": tp,
                "fp": fp,
                "fn": fn,
                "precision": precision,
                "recall": recall,
                "f1": f1,
                "cohen_kappa_one_vs_rest": kappa,
            }
        )

    exact = sum(t == p for t, p in zip(y_true_sets, y_pred_sets))
    overlap = sum(bool(t & p) for t, p in zip(y_true_sets, y_pred_sets))
    n = len(y_true_sets)
    precision_micro = safe_divide(total_tp, total_tp + total_fp)
    recall_micro = safe_divide(total_tp, total_tp + total_fn)
    f1_micro = (
        safe_divide(2 * precision_micro * recall_micro, precision_micro + recall_micro)
        if precision_micro is not None and recall_micro is not None
        else None
    )
    macro_kappa = safe_divide(sum(k for k, _ in label_kappas), len(label_kappas))
    weighted_kappa = safe_divide(sum(k * support for k, support in label_kappas), sum(support for _, support in label_kappas))
    return {
        "n_compared": n,
        "n_agree": exact,
        "accuracy": safe_divide(exact, n),
        "n_any_overlap": overlap,
        "any_overlap": safe_divide(overlap, n),
        "cohen_kappa": macro_kappa,
        "cohen_kappa_weighted_by_support": weighted_kappa,
        "precision_micro": precision_micro,
        "recall_micro": recall_micro,
        "f1_micro": f1_micro,
        "precision_macro": safe_divide(sum((row["precision"] or 0.0) for row in rows), len(rows)),
        "recall_macro": safe_divide(sum((row["recall"] or 0.0) for row in rows), len(rows)),
        "f1_macro": safe_divide(sum((row["f1"] or 0.0) for row in rows), len(rows)),
        "precision_weighted": safe_divide(weighted_precision, total_support),
        "recall_weighted": safe_divide(weighted_recall, total_support),
        "f1_weighted": safe_divide(weighted_f1, total_support),
        "per_class": rows,
    }


def agreement_rate(df: pd.DataFrame, left: str, right: str) -> dict[str, object]:
    valid = df[left].notna() & df[right].notna()
    n = int(valid.sum())
    agree = int((df.loc[valid, left] == df.loc[valid, right]).sum())
    return {
        "comparison": f"{left} vs {right}",
        "n_compared": n,
        "n_agree": agree,
        "agreement": agree / n if n else None,
        "left_missing": int(df[left].isna().sum()),
        "right_missing": int(df[right].isna().sum()),
    }


def contrib_phy_in_llm(df: pd.DataFrame, exp: str) -> dict[str, object]:
    phy_col = "PHY_contrib"
    set_col = f"{exp}_contrib_set"
    valid = df[phy_col].notna() & df[set_col].apply(lambda x: isinstance(x, list) and len(x) > 0)
    agree = int(df.loc[valid].apply(lambda r: r[phy_col] in r[set_col], axis=1).sum())
    n = int(valid.sum())
    return {
        "comparison": f"{exp}_contrib_set contains PHY_contrib",
        "n_compared": n,
        "n_agree": agree,
        "agreement": agree / n if n else None,
        "left_missing": int(df[set_col].apply(lambda x: not isinstance(x, list) or len(x) == 0).sum()),
        "right_missing": int(df[phy_col].isna().sum()),
    }


def set_overlap_metrics(df: pd.DataFrame, left: str, right: str) -> dict[str, object]:
    valid = df[left].apply(lambda x: isinstance(x, list) and len(x) > 0) & df[right].apply(
        lambda x: isinstance(x, list) and len(x) > 0
    )
    sub = df.loc[valid, [left, right]]
    exact = int(sub.apply(lambda r: set(r[left]) == set(r[right]), axis=1).sum())
    overlap = int(sub.apply(lambda r: bool(set(r[left]) & set(r[right])), axis=1).sum())
    n = int(valid.sum())
    return {
        "comparison": f"{left} vs {right}",
        "n_compared": n,
        "n_agree": overlap,
        "agreement": overlap / n if n else None,
        "n_exact_set_agree": exact,
        "exact_set_agreement": exact / n if n else None,
        "n_any_overlap": overlap,
        "any_overlap": overlap / n if n else None,
    }


def summarize_block(master: pd.DataFrame, label: str, exps: list[str]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for exp in exps:
        rows.append({"evaluation": label, "metric_type": "direct", **agreement_rate(master, f"{exp}_direct", "PHY_direct")})
        rows.append(
            {
                "evaluation": label,
                "metric_type": "underlying",
                **agreement_rate(master, f"{exp}_underlying", "PHY_underlying"),
            }
        )
        rows.append({"evaluation": label, "metric_type": "contributory", **contrib_phy_in_llm(master, exp)})

    for left, right in combinations(exps, 2):
        rows.append({"evaluation": label, "metric_type": "direct_llm_pair", **agreement_rate(master, f"{left}_direct", f"{right}_direct")})
        rows.append(
            {
                "evaluation": label,
                "metric_type": "underlying_llm_pair",
                **agreement_rate(master, f"{left}_underlying", f"{right}_underlying"),
            }
        )
        rows.append(
            {
                "evaluation": label,
                "metric_type": "contributory_llm_pair",
                **set_overlap_metrics(master, f"{left}_contrib_set", f"{right}_contrib_set"),
            }
        )
    return rows


def stratified_summary(master: pd.DataFrame, summary_rows: list[dict[str, object]]) -> pd.DataFrame:
    rows = []
    exp_names = ["EXP1", "EXP2", "EXP3", "EXP4"]
    strata = ["vatype", "Sex", "age_group"]
    for stratum in strata:
        for value, group in master.groupby(stratum, dropna=False):
            for exp in exp_names:
                for metric_name, result in [
                    ("direct", agreement_rate(group, f"{exp}_direct", "PHY_direct")),
                    ("underlying", agreement_rate(group, f"{exp}_underlying", "PHY_underlying")),
                    ("contributory", contrib_phy_in_llm(group, exp)),
                ]:
                    rows.append(
                        {
                            "stratum": stratum,
                            "stratum_value": value,
                            "experiment": exp,
                            "metric_type": metric_name,
                            **result,
                        }
                    )
    return pd.DataFrame(rows)


def add_metric_rows(
    rows: list[dict[str, object]],
    class_rows: list[dict[str, object]],
    evaluation: str,
    metric_type: str,
    comparison: str,
    level: str,
    metrics: dict[str, object],
    class_metric_kind: str,
) -> None:
    scalar_keys = [
        "n_compared",
        "n_agree",
        "accuracy",
        "n_any_overlap",
        "any_overlap",
        "cohen_kappa",
        "cohen_kappa_weighted_by_support",
        "precision_micro",
        "recall_micro",
        "f1_micro",
        "precision_macro",
        "recall_macro",
        "f1_macro",
        "precision_weighted",
        "recall_weighted",
        "f1_weighted",
        "n_excluded_blank_reference",
    ]
    row = {
        "evaluation": evaluation,
        "metric_type": metric_type,
        "comparison": comparison,
        "level": level,
    }
    for key in scalar_keys:
        row[key] = metrics.get(key)
    rows.append(row)

    for class_row in metrics.get("per_class", []):
        class_rows.append(
            {
                "evaluation": evaluation,
                "metric_type": metric_type,
                "comparison": comparison,
                "level": level,
                "class_metric_kind": class_metric_kind,
                **class_row,
            }
        )


def append_single_label_confusions(
    master: pd.DataFrame,
    pair_rows: list[dict[str, object]],
    case_rows: list[dict[str, object]],
    evaluation: str,
    metric_type: str,
    comparison: str,
    level: str,
    pred_col: str,
    true_col: str,
) -> None:
    temp = master[["ident", "vatype", "Sex", "Age", pred_col, true_col]].copy()
    temp["predicted"] = temp[pred_col].apply(lambda x: code_at_level(x, level))
    temp["reference"] = temp[true_col].apply(lambda x: code_at_level(x, level))
    temp = temp[temp["reference"] != BLANK_CODE]
    temp = temp[temp["predicted"] != temp["reference"]]
    pairs = temp.groupby(["reference", "predicted"], dropna=False).size().reset_index(name="n_cases")
    for _, row in pairs.iterrows():
        pair_rows.append(
            {
                "evaluation": evaluation,
                "metric_type": metric_type,
                "comparison": comparison,
                "level": level,
                "reference": row["reference"],
                "predicted": row["predicted"],
                "n_cases": int(row["n_cases"]),
            }
        )
    for _, row in temp.iterrows():
        case_rows.append(
            {
                "ident": row["ident"],
                "evaluation": evaluation,
                "metric_type": metric_type,
                "comparison": comparison,
                "level": level,
                "reference": row["reference"],
                "predicted": row["predicted"],
                "missed_codes": "",
                "extra_codes": "",
                "vatype": row["vatype"],
                "Sex": row["Sex"],
                "Age": row["Age"],
            }
        )


def append_multilabel_confusions(
    master: pd.DataFrame,
    pair_rows: list[dict[str, object]],
    case_rows: list[dict[str, object]],
    evaluation: str,
    metric_type: str,
    comparison: str,
    level: str,
    pred_col: str,
    true_col: str,
) -> None:
    missed_counts: dict[tuple[str, str], int] = {}
    extra_counts: dict[tuple[str, str], int] = {}
    for _, row in master.iterrows():
        predicted = code_set_at_level(row[pred_col], level)
        reference = code_set_at_level(row[true_col], level) if isinstance(row[true_col], list) else {code_at_level(row[true_col], level)}
        if reference == {BLANK_CODE}:
            continue
        if predicted == reference:
            continue
        missed = sorted(reference - predicted)
        extra = sorted(predicted - reference)
        for code in missed:
            missed_counts[(code, "MISSED_BY_LLM")] = missed_counts.get((code, "MISSED_BY_LLM"), 0) + 1
        for code in extra:
            extra_counts[(code, "EXTRA_FROM_LLM")] = extra_counts.get((code, "EXTRA_FROM_LLM"), 0) + 1
        case_rows.append(
            {
                "ident": row["ident"],
                "evaluation": evaluation,
                "metric_type": metric_type,
                "comparison": comparison,
                "level": level,
                "reference": ", ".join(sorted(reference)),
                "predicted": ", ".join(sorted(predicted)),
                "missed_codes": ", ".join(missed),
                "extra_codes": ", ".join(extra),
                "vatype": row["vatype"],
                "Sex": row["Sex"],
                "Age": row["Age"],
            }
        )
    for (code, direction), count in {**missed_counts, **extra_counts}.items():
        pair_rows.append(
            {
                "evaluation": evaluation,
                "metric_type": metric_type,
                "comparison": comparison,
                "level": level,
                "reference": code if direction == "MISSED_BY_LLM" else "",
                "predicted": code if direction == "EXTRA_FROM_LLM" else "",
                "confusion_type": direction,
                "n_cases": count,
            }
        )


def advanced_evaluation_outputs(master: pd.DataFrame, evaluations: dict[str, list[str]]) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    metric_rows: list[dict[str, object]] = []
    class_rows: list[dict[str, object]] = []
    confusion_pair_rows: list[dict[str, object]] = []
    confusion_case_rows: list[dict[str, object]] = []

    def single_comparison(evaluation: str, metric_type: str, pred_col: str, true_col: str) -> None:
        comparison = f"{pred_col} vs {true_col}"
        for level in CODE_LEVELS:
            comparable = master[true_col].apply(lambda x: code_at_level(x, level) != BLANK_CODE)
            y_pred = master.loc[comparable, pred_col].apply(lambda x: code_at_level(x, level)).tolist()
            y_true = master.loc[comparable, true_col].apply(lambda x: code_at_level(x, level)).tolist()
            metrics = single_label_classification_metrics(y_true, y_pred)
            metrics["n_excluded_blank_reference"] = int((~comparable).sum())
            add_metric_rows(metric_rows, class_rows, evaluation, metric_type, comparison, level, metrics, "single_label")
            append_single_label_confusions(
                master, confusion_pair_rows, confusion_case_rows, evaluation, metric_type, comparison, level, pred_col, true_col
            )

    def multilabel_comparison(evaluation: str, metric_type: str, pred_col: str, true_col: str) -> None:
        comparison = f"{pred_col} vs {true_col}"
        for level in CODE_LEVELS:
            if master[true_col].apply(lambda x: isinstance(x, list)).any():
                comparable = master[true_col].apply(lambda x: bool(nonblank_code_set(x, level)))
                y_true_sets = [code_set_at_level(value, level) for value in master.loc[comparable, true_col]]
            else:
                comparable = master[true_col].apply(lambda x: code_at_level(x, level) != BLANK_CODE)
                y_true_sets = [{code_at_level(value, level)} for value in master.loc[comparable, true_col]]
            y_pred_sets = [code_set_at_level(value, level) for value in master.loc[comparable, pred_col]]
            metrics = multilabel_metrics(y_true_sets, y_pred_sets)
            metrics["n_excluded_blank_reference"] = int((~comparable).sum())
            add_metric_rows(metric_rows, class_rows, evaluation, metric_type, comparison, level, metrics, "multi_label")
            append_multilabel_confusions(
                master, confusion_pair_rows, confusion_case_rows, evaluation, metric_type, comparison, level, pred_col, true_col
            )

    for evaluation, exps in evaluations.items():
        for exp in exps:
            single_comparison(evaluation, "direct", f"{exp}_direct", "PHY_direct")
            single_comparison(evaluation, "underlying", f"{exp}_underlying", "PHY_underlying")
            multilabel_comparison(evaluation, "contributory", f"{exp}_contrib_set", "PHY_contrib")

        for left, right in combinations(exps, 2):
            single_comparison(evaluation, "direct_llm_pair", f"{left}_direct", f"{right}_direct")
            single_comparison(evaluation, "underlying_llm_pair", f"{left}_underlying", f"{right}_underlying")
            multilabel_comparison(evaluation, "contributory_llm_pair", f"{left}_contrib_set", f"{right}_contrib_set")

    metrics = pd.DataFrame(metric_rows)
    per_class = pd.DataFrame(class_rows)
    confusion_pairs = pd.DataFrame(confusion_pair_rows)
    if not confusion_pairs.empty and "n_cases" in confusion_pairs:
        confusion_pairs = confusion_pairs.sort_values(["evaluation", "metric_type", "level", "n_cases"], ascending=[True, True, True, False])
    confusion_cases = pd.DataFrame(confusion_case_rows)
    return metrics, per_class, confusion_pairs, confusion_cases


def pooled_phy_set(row: pd.Series, level: str) -> set[str]:
    codes = {
        code_at_level(row["PHY_direct"], level),
        code_at_level(row["PHY_underlying"], level),
        code_at_level(row["PHY_contrib"], level),
    }
    return {code for code in codes if code != BLANK_CODE}


def pooled_llm_set(row: pd.Series, exp: str, level: str) -> set[str]:
    codes = {
        code_at_level(row[f"{exp}_direct"], level),
        code_at_level(row[f"{exp}_underlying"], level),
    }
    codes.update(nonblank_code_set(row[f"{exp}_contrib_set"], level))
    return {code for code in codes if code != BLANK_CODE}


def flexible_overlap_outputs(master: pd.DataFrame, evaluations: dict[str, list[str]]) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    metric_rows: list[dict[str, object]] = []
    case_rows: list[dict[str, object]] = []
    fpfn_case_rows: list[dict[str, object]] = []
    fpfn_frequency_rows: list[dict[str, object]] = []
    seen: set[tuple[str, str]] = set()

    for evaluation, exps in evaluations.items():
        for exp in exps:
            key = (evaluation, exp)
            if key in seen:
                continue
            seen.add(key)
            for level in CODE_LEVELS:
                temp = master[["ident", "vatype", "Sex", "Age"]].copy()
                temp["phy_codes"] = master.apply(lambda row: pooled_phy_set(row, level), axis=1)
                temp["llm_codes"] = master.apply(lambda row: pooled_llm_set(row, exp, level), axis=1)
                comparable = temp["phy_codes"].apply(bool)
                temp = temp.loc[comparable].copy()
                true_sets = temp["phy_codes"].tolist()
                pred_sets = temp["llm_codes"].apply(lambda codes: codes if codes else {BLANK_CODE}).tolist()
                metrics = multilabel_metrics(true_sets, pred_sets)
                metrics["n_excluded_blank_reference"] = int((~comparable).sum())
                row = {
                    "evaluation": evaluation,
                    "experiment": exp,
                    "comparison": f"{exp}_pooled_any_type vs PHY_pooled_any_type",
                    "level": level,
                    "n_excluded_blank_reference": metrics.get("n_excluded_blank_reference"),
                    "n_compared": metrics.get("n_compared"),
                    "n_exact_set_agree": metrics.get("n_agree"),
                    "exact_set_agreement": metrics.get("accuracy"),
                    "n_any_overlap": metrics.get("n_any_overlap"),
                    "any_overlap": metrics.get("any_overlap"),
                    "cohen_kappa": metrics.get("cohen_kappa"),
                    "precision_micro": metrics.get("precision_micro"),
                    "recall_micro": metrics.get("recall_micro"),
                    "f1_micro": metrics.get("f1_micro"),
                    "precision_macro": metrics.get("precision_macro"),
                    "recall_macro": metrics.get("recall_macro"),
                    "f1_macro": metrics.get("f1_macro"),
                    "precision_weighted": metrics.get("precision_weighted"),
                    "recall_weighted": metrics.get("recall_weighted"),
                    "f1_weighted": metrics.get("f1_weighted"),
                }
                metric_rows.append(row)

                confused = temp[temp.apply(lambda row: not bool(row["phy_codes"] & row["llm_codes"]), axis=1)]
                for _, case in confused.iterrows():
                    case_rows.append(
                        {
                            "ident": case["ident"],
                            "evaluation": evaluation,
                            "experiment": exp,
                            "comparison": f"{exp}_pooled_any_type vs PHY_pooled_any_type",
                            "level": level,
                            "phy_codes": ", ".join(sorted(case["phy_codes"])),
                            "llm_codes": ", ".join(sorted(case["llm_codes"])) if case["llm_codes"] else BLANK_CODE,
                            "vatype": case["vatype"],
                            "Sex": case["Sex"],
                            "Age": case["Age"],
                        }
                    )

                fpfn_counts: dict[tuple[str, str], int] = {}
                for _, case in temp.iterrows():
                    phy_codes = set(case["phy_codes"])
                    llm_codes = set(case["llm_codes"])
                    if not llm_codes:
                        llm_codes = {BLANK_CODE}
                    false_negative_codes = sorted(phy_codes - llm_codes)
                    false_positive_codes = sorted((llm_codes - phy_codes) - {BLANK_CODE})
                    true_positive_codes = sorted(phy_codes & llm_codes)

                    for code in false_negative_codes:
                        fpfn_counts[("false_negative_phy_code_missed_by_llm", code)] = (
                            fpfn_counts.get(("false_negative_phy_code_missed_by_llm", code), 0) + 1
                        )
                    for code in false_positive_codes:
                        fpfn_counts[("false_positive_llm_extra_code_not_in_phy", code)] = (
                            fpfn_counts.get(("false_positive_llm_extra_code_not_in_phy", code), 0) + 1
                        )
                    for code in true_positive_codes:
                        fpfn_counts[("true_positive_code_found_by_both", code)] = (
                            fpfn_counts.get(("true_positive_code_found_by_both", code), 0) + 1
                        )

                    if false_negative_codes or false_positive_codes:
                        fpfn_case_rows.append(
                            {
                                "ident": case["ident"],
                                "evaluation": evaluation,
                                "experiment": exp,
                                "comparison": f"{exp}_pooled_any_type vs PHY_pooled_any_type",
                                "level": level,
                                "phy_codes": ", ".join(sorted(phy_codes)),
                                "llm_codes": ", ".join(sorted(llm_codes)),
                                "true_positive_overlap_codes": ", ".join(true_positive_codes),
                                "false_negative_phy_codes_missed_by_llm": ", ".join(false_negative_codes),
                                "false_positive_llm_extra_codes_not_in_phy": ", ".join(false_positive_codes),
                                "n_true_positive_codes": len(true_positive_codes),
                                "n_false_negative_codes": len(false_negative_codes),
                                "n_false_positive_codes": len(false_positive_codes),
                                "vatype": case["vatype"],
                                "Sex": case["Sex"],
                                "Age": case["Age"],
                            }
                        )

                for (error_type, code), count in fpfn_counts.items():
                    fpfn_frequency_rows.append(
                        {
                            "evaluation": evaluation,
                            "experiment": exp,
                            "comparison": f"{exp}_pooled_any_type vs PHY_pooled_any_type",
                            "level": level,
                            "error_type": error_type,
                            "code": code,
                            "n_cases": count,
                        }
                    )

    frequency = pd.DataFrame(fpfn_frequency_rows)
    if not frequency.empty:
        frequency = frequency.sort_values(
            ["evaluation", "experiment", "level", "error_type", "n_cases"],
            ascending=[True, True, True, True, False],
        )
    cases = pd.DataFrame(fpfn_case_rows)
    return pd.DataFrame(metric_rows), pd.DataFrame(case_rows), frequency, cases


def add_descriptions(df: pd.DataFrame, codebook: pd.DataFrame) -> pd.DataFrame:
    desc = codebook.set_index("code")["description"].to_dict()
    for col in [c for c in df.columns if c.endswith("_direct") or c.endswith("_underlying") or c in {"PHY_direct", "PHY_underlying", "PHY_contrib"}]:
        df[f"{col}_description"] = df[col].map(desc)
    for col in [c for c in df.columns if c.endswith("_contrib_set")]:
        df[f"{col}_text"] = df[col].apply(lambda codes: ", ".join(codes) if isinstance(codes, list) else "")
    return df


def write_report(
    summary: pd.DataFrame,
    advanced_metrics: pd.DataFrame,
    flexible_metrics: pd.DataFrame,
    quality: pd.DataFrame,
    output_file: Path,
) -> None:
    key = summary[summary["metric_type"].isin(["direct", "underlying", "contributory"])].copy()
    key["agreement_pct"] = (key["agreement"] * 100).round(1)
    llm_pairs = summary[summary["metric_type"].str.contains("llm_pair", na=False)].copy()
    llm_pairs["agreement_pct"] = (llm_pairs["agreement"] * 100).round(1)
    if "exact_set_agreement" in llm_pairs:
        llm_pairs["exact_set_agreement_pct"] = (llm_pairs["exact_set_agreement"] * 100).round(1)
    report_table = markdown_table(
        key[["evaluation", "metric_type", "comparison", "n_compared", "n_agree", "agreement_pct"]]
    )
    pair_table = markdown_table(
        llm_pairs[
            [
                "evaluation",
                "metric_type",
                "comparison",
                "n_compared",
                "n_agree",
                "agreement_pct",
                "n_exact_set_agree",
                "exact_set_agreement_pct",
            ]
        ]
    )
    quality_table = markdown_table(quality)
    advanced_overview = advanced_metrics[
        (advanced_metrics["level"].isin(["full", "level2", "level1"]))
        & (advanced_metrics["metric_type"].isin(["direct", "underlying", "contributory"]))
    ].copy()
    advanced_overview = advanced_overview[
        [
            "evaluation",
            "metric_type",
            "level",
            "comparison",
            "accuracy",
            "cohen_kappa",
            "precision_macro",
            "recall_macro",
            "f1_macro",
            "precision_weighted",
            "recall_weighted",
            "f1_weighted",
        ]
    ]
    for col in [
        "accuracy",
        "cohen_kappa",
        "precision_macro",
        "recall_macro",
        "f1_macro",
        "precision_weighted",
        "recall_weighted",
        "f1_weighted",
    ]:
        advanced_overview[col] = advanced_overview[col].apply(lambda x: round(x, 4) if pd.notna(x) else x)
    advanced_table = markdown_table(advanced_overview)
    flexible_overview = flexible_metrics.copy()
    for col in [
        "exact_set_agreement",
        "any_overlap",
        "cohen_kappa",
        "precision_micro",
        "recall_micro",
        "f1_micro",
        "precision_macro",
        "recall_macro",
        "f1_macro",
        "precision_weighted",
        "recall_weighted",
        "f1_weighted",
    ]:
        flexible_overview[col] = flexible_overview[col].apply(lambda x: round(x, 4) if pd.notna(x) else x)
    flexible_table = markdown_table(flexible_overview)
    lines = [
        "# LLM vs Physician Cause-of-Death Coding Agreement",
        "",
        "## Evaluation Design",
        "",
        "- Evaluation 1: EXP1 versus PHY, combined narrative.",
        "- Evaluation 2: EXP3 versus PHY, original verbal narrative only.",
        "- Evaluation 3: EXP2 versus EXP1 versus PHY, questionnaire data without verbal narrative.",
        "- Evaluation 4: EXP2 versus EXP4 versus PHY, semantically restructured questionnaire text.",
        "",
        "## Main Agreement Summary",
        "",
        report_table,
        "",
        "## LLM-to-LLM Agreement",
        "",
        pair_table,
        "",
        "## Kappa, Precision, Recall, F1",
        "",
        advanced_table,
        "",
        "## Flexible Any-Type Overlap",
        "",
        flexible_table,
        "",
        "## Data Quality",
        "",
        quality_table,
        "",
        "Notes: Blank PHY reference determinations are excluded from the kappa/precision/recall/F1 comparisons. Level 1 uses the first two digits of the code; Level 2 uses the first four digits (shown as NN-NN). Direct and underlying metrics are single-label multiclass metrics. Contributory metrics are multi-label because LLM contributory output can contain multiple codes; contributory kappa is the macro average of one-vs-rest label kappas. Flexible any-type overlap pools direct, underlying, and contributory codes within each case before comparison.",
        "",
    ]
    output_file.write_text("\n".join(lines), encoding="utf-8")


def markdown_table(df: pd.DataFrame) -> str:
    display = df.copy()
    display = display.where(pd.notna(display), "")
    headers = [str(col) for col in display.columns]
    rows = [[str(value) for value in row] for row in display.to_numpy()]

    def clean(value: str) -> str:
        return value.replace("|", "\\|").replace("\n", " ")

    lines = [
        "| " + " | ".join(clean(h) for h in headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(clean(v) for v in row) + " |")
    return "\n".join(lines)


def safe_to_csv(df: pd.DataFrame, path: Path) -> Path:
    try:
        df.to_csv(path, index=False)
        return path
    except PermissionError:
        stamped = path.with_name(f"{path.stem}_{datetime.now().strftime('%Y%m%d_%H%M%S')}{path.suffix}")
        df.to_csv(stamped, index=False)
        return stamped


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    codebook, compact_lookup = parse_codebook()
    master = build_master(compact_lookup)
    master = add_descriptions(master, codebook)

    evaluations = {
        "Evaluation 1: EXP1 vs PHY": ["EXP1"],
        "Evaluation 2: EXP3 vs PHY": ["EXP3"],
        "Evaluation 3: EXP2 vs EXP1 vs PHY": ["EXP2", "EXP1"],
        "Evaluation 4: EXP2 vs EXP4 vs PHY": ["EXP2", "EXP4"],
    }
    summary_rows = []
    for label, exps in evaluations.items():
        summary_rows.extend(summarize_block(master, label, exps))
    summary = pd.DataFrame(summary_rows)
    advanced_metrics, per_class_metrics, confusion_pairs, confusion_cases = advanced_evaluation_outputs(master, evaluations)
    (
        flexible_metrics,
        flexible_no_overlap_cases,
        flexible_fpfn_frequency,
        flexible_fpfn_cases,
    ) = flexible_overlap_outputs(master, evaluations)

    quality_rows = [
        {"item": "records_in_master", "value": len(master)},
        {"item": "unique_idents_in_master", "value": master["ident"].nunique()},
    ]
    for exp in ["EXP1", "EXP2", "EXP3", "EXP4"]:
        quality_rows.append(
            {
                "item": f"{exp}_parse_methods",
                "value": master[f"{exp}_parse_method"].value_counts(dropna=False).to_dict(),
            }
        )
    for col in ["PHY_direct", "PHY_underlying", "PHY_contrib"]:
        quality_rows.append({"item": f"{col}_missing", "value": int(master[col].isna().sum())})
    quality = pd.DataFrame(quality_rows)

    stratified = stratified_summary(master, summary_rows)

    written_files = [
        safe_to_csv(master, OUTPUT_DIR / "master_normalized_codes.csv"),
        safe_to_csv(codebook, OUTPUT_DIR / "codebook_parsed.csv"),
        safe_to_csv(summary, OUTPUT_DIR / "agreement_summary.csv"),
        safe_to_csv(stratified, OUTPUT_DIR / "agreement_stratified.csv"),
        safe_to_csv(advanced_metrics, OUTPUT_DIR / "metrics_kappa_precision_recall_f1_by_level.csv"),
        safe_to_csv(per_class_metrics, OUTPUT_DIR / "per_class_metrics_by_level.csv"),
        safe_to_csv(confusion_pairs, OUTPUT_DIR / "confusion_pairs_by_level.csv"),
        safe_to_csv(confusion_cases, OUTPUT_DIR / "confused_cases_by_level.csv"),
        safe_to_csv(flexible_metrics, OUTPUT_DIR / "flexible_any_type_overlap_metrics_by_level.csv"),
        safe_to_csv(flexible_no_overlap_cases, OUTPUT_DIR / "flexible_any_type_no_overlap_cases_by_level.csv"),
        safe_to_csv(flexible_fpfn_frequency, OUTPUT_DIR / "flexible_any_type_false_positive_false_negative_frequency_by_level.csv"),
        safe_to_csv(flexible_fpfn_cases, OUTPUT_DIR / "flexible_any_type_false_positive_false_negative_cases_by_level.csv"),
        safe_to_csv(quality, OUTPUT_DIR / "data_quality_summary.csv"),
    ]
    write_report(summary, advanced_metrics, flexible_metrics, quality, OUTPUT_DIR / "agreement_report.md")

    print(f"Wrote outputs to {OUTPUT_DIR.resolve()}")
    print("CSV files:")
    for file in written_files:
        print(file.resolve())
    print(summary[["evaluation", "metric_type", "comparison", "n_compared", "n_agree", "agreement"]].to_string(index=False))


if __name__ == "__main__":
    main()
