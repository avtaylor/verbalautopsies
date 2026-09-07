from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

from analysis_llm_phy_agreement import load_experiment


DATA_DIR = Path(r"C:\Users\Lenovo\Downloads\MEIRU_VA_EXP")
OUTPUT_DIR = Path("outputs") / "agreement_analysis"

CODEBOOK_FILE = DATA_DIR / "MEIRU_CODS_LIST.txt"
PHY_FILE = DATA_DIR / "PHY.xlsx"
VA_TYPE_FILE = DATA_DIR / "va_type.csv"
AGE_SEX_FILE = DATA_DIR / "age_sex.csv"

CODE_PATTERN = re.compile(r"\b(\d{1,2})\s*-\s*(\d{1,2})\s*-\s*(\d{1,2})\b")
EXPERIMENTS = ["EXP1", "EXP2", "EXP3", "EXP4"]
LEVELS = ["level1", "level2", "level3"]
VA_TYPE_LABELS = {
    "1": "adult",
    "2": "child",
    "3": "infant",
}
SEX_LABELS = {
    "0": "female",
    "1": "male",
}
AGE_BANDS = {
    "adult": {
        "bins": [14, 24, 44, 64, 200],
        "labels": ["15-24", "25-44", "45-64", "65+"],
    },
    "child": {
        "bins": [-1, 0, 4, 9, 14],
        "labels": ["0", "1-4", "5-9", "10-14"],
    },
    "infant": {
        "bins": [-1, 0],
        "labels": ["0"],
    },
    "overall": {
        "bins": [-1, 0, 4, 9, 14, 24, 44, 64, 200],
        "labels": ["0", "1-4", "5-9", "10-14", "15-24", "25-44", "45-64", "65+"],
    },
}


def canonical_code(groups: tuple[str, str, str]) -> str:
    return "-".join(f"{int(part):02d}" for part in groups)


def parse_codebook() -> tuple[pd.DataFrame, dict[str, str]]:
    text = CODEBOOK_FILE.read_text(encoding="utf-8-sig")
    matches = list(CODE_PATTERN.finditer(text))
    rows = []
    for i, match in enumerate(matches):
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        desc = re.sub(r"\s+", " ", text[start:end].replace("|", "", 1).strip())
        rows.append({"code": canonical_code(match.groups()), "description": desc})
    codebook = pd.DataFrame(rows).drop_duplicates("code")

    compact_lookup: dict[str, str] = {}
    for code in codebook["code"]:
        a, b, c = [int(x) for x in code.split("-")]
        candidates = {code, code.replace("-", ""), f"{a}{b}{c}", f"{a:02d}{b:02d}{c:02d}"}
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


def normalize_code(value: object, compact_lookup: dict[str, str]) -> str | None:
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
    if digits in compact_lookup:
        return compact_lookup[digits]
    if len(digits) == 6:
        code = f"{digits[:2]}-{digits[2:4]}-{digits[4:6]}"
        return compact_lookup.get(code, code)
    return None


def code_at_level(code: str, level: str) -> str:
    if level == "level1":
        return code[:2]
    if level == "level2":
        return code[:5]
    if level == "level3":
        return code
    raise ValueError(f"Unknown level: {level}")


def level_name(code: str, level: str, codebook: pd.DataFrame) -> str:
    if level == "level1":
        match = codebook[codebook["code"] == f"{code}-00-00"]
        if match.empty:
            match = codebook[codebook["code"].str.startswith(code)]
        if match.empty:
            return "Unknown"
        return match.iloc[0]["description"].split(":", 1)[0].strip()

    if level == "level2":
        match = codebook[codebook["code"] == f"{code}-00"]
        if match.empty:
            match = codebook[codebook["code"].str.startswith(code)]
        if match.empty:
            return "Unknown"
        parts = [part.strip() for part in match.iloc[0]["description"].split(":")]
        return parts[1] if len(parts) >= 2 else parts[0]

    match = codebook[codebook["code"] == code]
    return match.iloc[0]["description"] if not match.empty else "Unknown"


def csmf_metrics(reference: pd.Series, predicted: pd.Series) -> tuple[dict[str, object], pd.DataFrame]:
    labels = sorted(set(reference.dropna()) | set(predicted.dropna()))
    n_reference = int(reference.notna().sum())
    n_predicted = int(predicted.notna().sum())
    ref_counts = reference.value_counts().reindex(labels, fill_value=0)
    pred_counts = predicted.value_counts().reindex(labels, fill_value=0)
    ref_frac = ref_counts / n_reference if n_reference else ref_counts * 0
    pred_frac = pred_counts / n_predicted if n_predicted else pred_counts * 0

    abs_error_sum = float((ref_frac - pred_frac).abs().sum())
    simple_similarity = 1 - 0.5 * abs_error_sum
    min_ref = float(ref_frac.min()) if len(ref_frac) else 0.0
    denom = 2 * (1 - min_ref)
    chance_corrected = 1 - (abs_error_sum / denom) if denom else None

    detail = pd.DataFrame(
        {
            "cause_code": labels,
            "phy_count": ref_counts.values,
            "llm_count": pred_counts.values,
            "phy_csmf": ref_frac.values,
            "llm_csmf": pred_frac.values,
            "difference": pred_frac.values - ref_frac.values,
            "abs_difference": abs(pred_frac.values - ref_frac.values),
        }
    )
    return (
        {
            "n_reference": n_reference,
            "n_predicted": n_predicted,
            "n_causes_union": len(labels),
            "sum_abs_csmf_error": abs_error_sum,
            "csmf_similarity": simple_similarity,
            "csmf_accuracy_chance_corrected": chance_corrected,
        },
        detail,
    )


def build_master(compact_lookup: dict[str, str]) -> pd.DataFrame:
    phy = pd.read_excel(PHY_FILE, sheet_name="PHY", dtype=str)
    master = pd.DataFrame(
        {
            "ident": phy["ident"].astype(str).str.strip(),
            "PHY_underlying": phy["PHYSICIAN_UNDERLYING_CODES"].apply(lambda x: normalize_code(x, compact_lookup)),
        }
    )
    for exp in EXPERIMENTS:
        exp_df = load_experiment(exp, compact_lookup)[["ident", f"{exp}_underlying"]]
        master = master.merge(exp_df, on="ident", how="left", validate="one_to_one")
    va_type = pd.read_csv(VA_TYPE_FILE, dtype=str)
    master = master.merge(va_type[["ident", "vatype"]], on="ident", how="left", validate="one_to_one")
    age_sex = pd.read_csv(AGE_SEX_FILE, dtype=str)
    master = master.merge(age_sex[["ident", "Age", "Sex"]], on="ident", how="left", validate="one_to_one")
    master["Age_num"] = pd.to_numeric(master["Age"], errors="coerce")
    master["va_type_label"] = master["vatype"].map(VA_TYPE_LABELS).fillna(master["vatype"])
    master["sex_label"] = master["Sex"].map(SEX_LABELS).fillna(master["Sex"])
    master["age_group_overall"] = pd.cut(
        master["Age_num"],
        bins=AGE_BANDS["overall"]["bins"],
        labels=AGE_BANDS["overall"]["labels"],
    ).astype(str)
    for label, spec in AGE_BANDS.items():
        if label == "overall":
            continue
        mask = master["va_type_label"] == label
        master.loc[mask, "age_group_va_type"] = pd.cut(
            master.loc[mask, "Age_num"],
            bins=spec["bins"],
            labels=spec["labels"],
        ).astype(str)
    return master


def calculate_csmf_for_strata(
    master: pd.DataFrame,
    codebook: pd.DataFrame,
    strata: list[tuple[dict[str, str], pd.DataFrame]],
) -> tuple[pd.DataFrame, pd.DataFrame]:
    summary_rows = []
    detail_rows = []
    for stratum_values, data in strata:
        for level in LEVELS:
            comparable = data[data["PHY_underlying"].notna()].copy()
            for exp in EXPERIMENTS:
                aligned = comparable[["PHY_underlying", f"{exp}_underlying"]].copy()
                ref_series = aligned["PHY_underlying"].dropna().apply(lambda x: code_at_level(x, level))
                pred_series = aligned[f"{exp}_underlying"].dropna().apply(lambda x: code_at_level(x, level))
                metrics, detail = csmf_metrics(ref_series, pred_series)
                summary_rows.append(
                    {
                        **stratum_values,
                        "level": level,
                        "experiment": exp,
                        **metrics,
                    }
                )
                detail["level"] = level
                detail["experiment"] = exp
                detail["cause_name"] = detail["cause_code"].apply(lambda code: level_name(code, level, codebook))
                for key, value in stratum_values.items():
                    detail[key] = value
                detail_rows.extend(detail.to_dict("records"))
    return pd.DataFrame(summary_rows), pd.DataFrame(detail_rows)


def build_strata(master: pd.DataFrame, mode: str) -> list[tuple[dict[str, str], pd.DataFrame]]:
    strata: list[tuple[dict[str, str], pd.DataFrame]] = []
    if mode == "va_type":
        strata.append(({"stratum": "overall", "va_type": "overall"}, master))
        for label in ["adult", "child", "infant"]:
            strata.append(({"stratum": "va_type", "va_type": label}, master[master["va_type_label"] == label]))
    elif mode == "va_type_age":
        for (va_type, age_group), group in master.groupby(["va_type_label", "age_group_va_type"], dropna=False):
            if pd.isna(age_group) or str(age_group) == "nan":
                continue
            strata.append(({"stratum": "va_type_age", "va_type": va_type, "age_group": str(age_group)}, group))
    elif mode == "va_type_sex":
        for (va_type, sex), group in master.groupby(["va_type_label", "sex_label"], dropna=False):
            if pd.isna(sex) or str(sex) == "nan":
                continue
            strata.append(({"stratum": "va_type_sex", "va_type": va_type, "sex": sex}, group))
    elif mode == "va_type_age_sex":
        for (va_type, age_group, sex), group in master.groupby(["va_type_label", "age_group_va_type", "sex_label"], dropna=False):
            if pd.isna(age_group) or str(age_group) == "nan" or pd.isna(sex) or str(sex) == "nan":
                continue
            strata.append(
                (
                    {
                        "stratum": "va_type_age_sex",
                        "va_type": va_type,
                        "age_group": str(age_group),
                        "sex": sex,
                    },
                    group,
                )
            )
    else:
        raise ValueError(f"Unknown strata mode: {mode}")
    return strata


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    codebook, compact_lookup = parse_codebook()
    master = build_master(compact_lookup)

    written = []
    for mode in ["va_type", "va_type_age", "va_type_sex", "va_type_age_sex"]:
        summary, detail = calculate_csmf_for_strata(master, codebook, build_strata(master, mode))
        summary_path = OUTPUT_DIR / f"csmf_accuracy_summary_underlying_by_{mode}.csv"
        detail_path = OUTPUT_DIR / f"csmf_accuracy_detail_underlying_by_{mode}.csv"
        summary.to_csv(summary_path, index=False)
        detail.to_csv(detail_path, index=False)
        written.extend([summary_path, detail_path])

    # Preserve the original filenames as aliases for the VA-type summary.
    va_summary = pd.read_csv(OUTPUT_DIR / "csmf_accuracy_summary_underlying_by_va_type.csv")
    va_detail = pd.read_csv(OUTPUT_DIR / "csmf_accuracy_detail_underlying_by_va_type.csv")
    va_summary.to_csv(OUTPUT_DIR / "csmf_accuracy_summary_underlying.csv", index=False)
    va_detail.to_csv(OUTPUT_DIR / "csmf_accuracy_detail_underlying.csv", index=False)
    written.extend([OUTPUT_DIR / "csmf_accuracy_summary_underlying.csv", OUTPUT_DIR / "csmf_accuracy_detail_underlying.csv"])

    for path in written:
        print(path.resolve())
    print(va_summary.to_string(index=False))


if __name__ == "__main__":
    main()
