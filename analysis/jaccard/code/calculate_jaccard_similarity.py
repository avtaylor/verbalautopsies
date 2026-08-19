from __future__ import annotations

import re
from itertools import combinations
from pathlib import Path

import pandas as pd

from analysis_llm_phy_agreement import load_experiment


DATA_DIR = Path(r"C:\Users\Lenovo\Downloads\MEIRU_VA_EXP")
OUTPUT_DIR = Path("outputs") / "agreement_analysis"

CODEBOOK_FILE = DATA_DIR / "MEIRU_CODS_LIST.txt"
PHY_FILE = DATA_DIR / "PHY.xlsx"
VA_TYPE_FILE = DATA_DIR / "va_type.csv"

CODE_PATTERN = re.compile(r"\b(\d{1,2})\s*-\s*(\d{1,2})\s*-\s*(\d{1,2})\b")
EXPERIMENTS = ["EXP1", "EXP2", "EXP3", "EXP4"]
LEVELS = ["level1", "level2", "level3"]
VA_TYPE_LABELS = {"1": "adult", "2": "child", "3": "infant"}


def canonical_code(groups: tuple[str, str, str]) -> str:
    return "-".join(f"{int(part):02d}" for part in groups)


def parse_codebook() -> dict[str, str]:
    text = CODEBOOK_FILE.read_text(encoding="utf-8-sig")
    matches = list(CODE_PATTERN.finditer(text))
    codes = [canonical_code(match.groups()) for match in matches]
    compact_lookup: dict[str, str] = {}
    for code in codes:
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
    return compact_lookup


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


def set_at_level(codes: object, level: str) -> set[str]:
    if not isinstance(codes, list) or not codes:
        return set()
    return {code_at_level(code, level) for code in codes if isinstance(code, str) and code}


def singleton_set_at_level(code: object, level: str) -> set[str]:
    if pd.isna(code) or code is None:
        return set()
    return {code_at_level(str(code), level)}


def jaccard(left: set[str], right: set[str]) -> float | None:
    union = left | right
    if not union:
        return None
    return len(left & right) / len(union)


def build_master(compact_lookup: dict[str, str]) -> pd.DataFrame:
    phy = pd.read_excel(PHY_FILE, sheet_name="PHY", dtype=str)
    master = pd.DataFrame(
        {
            "ident": phy["ident"].astype(str).str.strip(),
            "PHY_direct": phy["PHY_DIRECT"].apply(lambda x: normalize_code(x, compact_lookup)),
            "PHY_underlying": phy["PHYSICIAN_UNDERLYING_CODES"].apply(lambda x: normalize_code(x, compact_lookup)),
            "PHY_contrib": phy["PHY_CONTRB"].apply(lambda x: normalize_code(x, compact_lookup)),
        }
    )
    for exp in EXPERIMENTS:
        exp_df = load_experiment(exp, compact_lookup)
        master = master.merge(exp_df, on="ident", how="left", validate="one_to_one")
    va_type = pd.read_csv(VA_TYPE_FILE, dtype=str)
    master = master.merge(va_type[["ident", "vatype"]], on="ident", how="left", validate="one_to_one")
    master["va_type_label"] = master["vatype"].map(VA_TYPE_LABELS).fillna(master["vatype"])
    return master


def phy_pooled(row: pd.Series, level: str) -> set[str]:
    codes = set()
    for col in ["PHY_direct", "PHY_underlying", "PHY_contrib"]:
        codes.update(singleton_set_at_level(row[col], level))
    return codes


def exp_pooled(row: pd.Series, exp: str, level: str) -> set[str]:
    codes = set()
    codes.update(singleton_set_at_level(row[f"{exp}_direct"], level))
    codes.update(singleton_set_at_level(row[f"{exp}_underlying"], level))
    codes.update(set_at_level(row[f"{exp}_contrib_set"], level))
    return codes


def summarize_scores(scores: list[float], exact_flags: list[bool], overlap_flags: list[bool]) -> dict[str, object]:
    s = pd.Series(scores, dtype=float)
    n = len(scores)
    return {
        "n_compared": n,
        "mean_jaccard": float(s.mean()) if n else None,
        "median_jaccard": float(s.median()) if n else None,
        "q25_jaccard": float(s.quantile(0.25)) if n else None,
        "q75_jaccard": float(s.quantile(0.75)) if n else None,
        "n_exact_set_match": sum(exact_flags),
        "exact_set_match": sum(exact_flags) / n if n else None,
        "n_any_overlap": sum(overlap_flags),
        "any_overlap": sum(overlap_flags) / n if n else None,
    }


def add_summary(
    rows: list[dict[str, object]],
    case_rows: list[dict[str, object]],
    data: pd.DataFrame,
    comparison_type: str,
    comparison: str,
    level: str,
    left_getter,
    right_getter,
    reference_required: bool,
    stratum: str,
) -> None:
    scores: list[float] = []
    exact_flags: list[bool] = []
    overlap_flags: list[bool] = []
    for _, row in data.iterrows():
        left = left_getter(row, level)
        right = right_getter(row, level)
        if reference_required and not right:
            continue
        score = jaccard(left, right)
        if score is None:
            continue
        scores.append(score)
        exact_flags.append(left == right)
        overlap_flags.append(bool(left & right))
        case_rows.append(
            {
                "stratum": stratum,
                "comparison_type": comparison_type,
                "comparison": comparison,
                "level": level,
                "ident": row["ident"],
                "left_codes": ", ".join(sorted(left)),
                "right_codes": ", ".join(sorted(right)),
                "intersection_codes": ", ".join(sorted(left & right)),
                "union_codes": ", ".join(sorted(left | right)),
                "jaccard": score,
                "exact_set_match": left == right,
                "any_overlap": bool(left & right),
            }
        )
    rows.append(
        {
            "stratum": stratum,
            "comparison_type": comparison_type,
            "comparison": comparison,
            "level": level,
            **summarize_scores(scores, exact_flags, overlap_flags),
        }
    )


def calculate(master: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    summary_rows: list[dict[str, object]] = []
    case_rows: list[dict[str, object]] = []
    strata = {"overall": master}
    for label in ["adult", "child", "infant"]:
        strata[label] = master[master["va_type_label"] == label]

    for stratum, data in strata.items():
        for level in LEVELS:
            for exp in EXPERIMENTS:
                add_summary(
                    summary_rows,
                    case_rows,
                    data,
                    "flexible_pooled_any_type",
                    f"{exp}_pooled_any_type vs PHY_pooled_any_type",
                    level,
                    lambda row, lvl, e=exp: exp_pooled(row, e, lvl),
                    phy_pooled,
                    True,
                    stratum,
                )
                add_summary(
                    summary_rows,
                    case_rows,
                    data,
                    "contributory_vs_phy",
                    f"{exp}_contrib_set vs PHY_contrib",
                    level,
                    lambda row, lvl, e=exp: set_at_level(row[f"{e}_contrib_set"], lvl),
                    lambda row, lvl: singleton_set_at_level(row["PHY_contrib"], lvl),
                    True,
                    stratum,
                )

            for left, right in combinations(EXPERIMENTS, 2):
                add_summary(
                    summary_rows,
                    case_rows,
                    data,
                    "contributory_llm_pair",
                    f"{left}_contrib_set vs {right}_contrib_set",
                    level,
                    lambda row, lvl, e=left: set_at_level(row[f"{e}_contrib_set"], lvl),
                    lambda row, lvl, e=right: set_at_level(row[f"{e}_contrib_set"], lvl),
                    False,
                    stratum,
                )
    return pd.DataFrame(summary_rows), pd.DataFrame(case_rows)


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    compact_lookup = parse_codebook()
    master = build_master(compact_lookup)
    summary, cases = calculate(master)
    summary.to_csv(OUTPUT_DIR / "jaccard_similarity_summary.csv", index=False)
    cases.to_csv(OUTPUT_DIR / "jaccard_similarity_cases.csv", index=False)
    print((OUTPUT_DIR / "jaccard_similarity_summary.csv").resolve())
    print((OUTPUT_DIR / "jaccard_similarity_cases.csv").resolve())
    print(summary.head(24).to_string(index=False))


if __name__ == "__main__":
    main()
