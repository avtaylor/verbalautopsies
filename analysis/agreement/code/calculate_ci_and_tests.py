from __future__ import annotations

import math
import random
from itertools import combinations
from pathlib import Path

import pandas as pd


OUTPUT_DIR = Path("outputs") / "agreement_analysis"
EXPERIMENTS = ["EXP1", "EXP2", "EXP3", "EXP4"]
LEVELS = ["level1", "level2", "level3"]
N_BOOT = 1000
SEED = 20260710


def code_at_level(code: object, level: str) -> str | None:
    if pd.isna(code) or code is None or str(code).strip() == "":
        return None
    text = str(code)
    if text.lower() in {"nan", "none", "null", "na", "n/a"}:
        return None
    if level == "level1":
        return text[:2]
    if level == "level2":
        return text[:5]
    if level == "level3":
        return text
    raise ValueError(level)


def parse_set(value: object, level: str) -> set[str]:
    if pd.isna(value) or value is None:
        return set()
    text = str(value).strip()
    if not text:
        return set()
    # master_normalized_codes stores Python-list-looking strings.
    text = text.strip("[]")
    parts = [part.strip().strip("'\"") for part in text.split(",")]
    return {code_at_level(part, level) for part in parts if code_at_level(part, level)}


def pooled_phy(row: pd.Series, level: str) -> set[str]:
    out = set()
    for col in ["PHY_direct", "PHY_underlying", "PHY_contrib"]:
        code = code_at_level(row[col], level)
        if code:
            out.add(code)
    return out


def pooled_exp(row: pd.Series, exp: str, level: str) -> set[str]:
    out = set()
    for col in [f"{exp}_direct", f"{exp}_underlying"]:
        code = code_at_level(row[col], level)
        if code:
            out.add(code)
    out.update(parse_set(row[f"{exp}_contrib_set"], level))
    return out


def quantile(values: list[float], q: float) -> float:
    if not values:
        return float("nan")
    ordered = sorted(values)
    pos = (len(ordered) - 1) * q
    lo = math.floor(pos)
    hi = math.ceil(pos)
    if lo == hi:
        return ordered[lo]
    return ordered[lo] * (hi - pos) + ordered[hi] * (pos - lo)


def ci(values: list[float]) -> tuple[float, float]:
    return quantile(values, 0.025), quantile(values, 0.975)


def bootstrap_mean(values: list[float], rng: random.Random, n_boot: int = N_BOOT) -> tuple[float, float, float]:
    if not values:
        return float("nan"), float("nan"), float("nan")
    n = len(values)
    estimates = []
    for _ in range(n_boot):
        estimates.append(sum(values[rng.randrange(n)] for _ in range(n)) / n)
    lo, hi = ci(estimates)
    return sum(values) / n, lo, hi


def bootstrap_diff(values_a: list[float], values_b: list[float], rng: random.Random, n_boot: int = N_BOOT) -> tuple[float, float, float, float]:
    if not values_a or len(values_a) != len(values_b):
        return float("nan"), float("nan"), float("nan"), float("nan")
    diffs = [a - b for a, b in zip(values_a, values_b)]
    n = len(diffs)
    estimates = []
    for _ in range(n_boot):
        estimates.append(sum(diffs[rng.randrange(n)] for _ in range(n)) / n)
    lo, hi = ci(estimates)
    estimate = sum(diffs) / n
    p = 2 * min(sum(x <= 0 for x in estimates) / n_boot, sum(x >= 0 for x in estimates) / n_boot)
    return estimate, lo, hi, min(p, 1.0)


def mcnemar_exact_p(b: int, c: int) -> float:
    n = b + c
    if n == 0:
        return 1.0
    if n > 200:
        stat = (abs(b - c) - 1) ** 2 / n
        # Wilson-Hilferty approximation for chi-square(1) tail.
        z = math.sqrt(stat)
        return math.erfc(z / math.sqrt(2))
    k = min(b, c)
    prob = sum(math.comb(n, i) * (0.5 ** n) for i in range(k + 1))
    return min(1.0, 2 * prob)


def csmf_accuracy(reference: list[str], predicted: list[str]) -> float:
    cleaned = [(r, p) for r, p in zip(reference, predicted) if r and p and not pd.isna(r) and not pd.isna(p)]
    reference = [str(r) for r, _ in cleaned]
    predicted = [str(p) for _, p in cleaned]
    labels = sorted(set(reference) | set(predicted))
    if not labels:
        return float("nan")
    ref = pd.Series(reference).value_counts().reindex(labels, fill_value=0) / len(reference)
    pred = pd.Series(predicted).value_counts().reindex(labels, fill_value=0) / len(predicted)
    abs_error = float((ref - pred).abs().sum())
    min_ref = float(ref.min())
    denom = 2 * (1 - min_ref)
    return 1 - abs_error / denom if denom else float("nan")


def bootstrap_csmf(reference: list[str], predicted: list[str], rng: random.Random, n_boot: int = N_BOOT) -> tuple[float, float, float]:
    n = len(reference)
    if n == 0:
        return float("nan"), float("nan"), float("nan")
    estimates = []
    for _ in range(n_boot):
        idx = [rng.randrange(n) for _ in range(n)]
        estimates.append(csmf_accuracy([reference[i] for i in idx], [predicted[i] for i in idx]))
    lo, hi = ci(estimates)
    return csmf_accuracy(reference, predicted), lo, hi


def bootstrap_csmf_diff(ref: list[str], pred_a: list[str], pred_b: list[str], rng: random.Random, n_boot: int = N_BOOT) -> tuple[float, float, float, float]:
    n = len(ref)
    estimates = []
    for _ in range(n_boot):
        idx = [rng.randrange(n) for _ in range(n)]
        ref_i = [ref[i] for i in idx]
        estimates.append(csmf_accuracy(ref_i, [pred_a[i] for i in idx]) - csmf_accuracy(ref_i, [pred_b[i] for i in idx]))
    estimate = csmf_accuracy(ref, pred_a) - csmf_accuracy(ref, pred_b)
    lo, hi = ci(estimates)
    p = 2 * min(sum(x <= 0 for x in estimates) / n_boot, sum(x >= 0 for x in estimates) / n_boot)
    return estimate, lo, hi, min(p, 1.0)


def main() -> None:
    rng = random.Random(SEED)
    master = pd.read_csv(OUTPUT_DIR / "master_normalized_codes.csv", dtype=str)
    ci_rows = []
    test_rows = []

    for level in LEVELS:
        comparable = master[master["PHY_underlying"].notna()].copy()
        ref = comparable["PHY_underlying"].apply(lambda x: code_at_level(x, level)).tolist()
        exact_vectors: dict[str, list[float]] = {}
        csmf_preds: dict[str, list[str]] = {}
        flexible_vectors: dict[str, list[float]] = {}
        jaccard_vectors: dict[str, list[float]] = {}

        for exp in EXPERIMENTS:
            pred = comparable[f"{exp}_underlying"].apply(lambda x: code_at_level(x, level)).tolist()
            valid = [(r, p) for r, p in zip(ref, pred) if r and p]
            exact = [1.0 if r == p else 0.0 for r, p in valid]
            exact_vectors[exp] = exact
            csmf_preds[exp] = [p for _, p in valid]
            ref_valid = [r for r, _ in valid]

            estimate, lo, hi = bootstrap_mean(exact, rng)
            ci_rows.append({"metric": "underlying_exact_agreement", "level": level, "experiment": exp, "n": len(exact), "estimate": estimate, "ci_low": lo, "ci_high": hi})
            estimate, lo, hi = bootstrap_csmf(ref_valid, csmf_preds[exp], rng)
            ci_rows.append({"metric": "csmf_accuracy", "level": level, "experiment": exp, "n": len(ref_valid), "estimate": estimate, "ci_low": lo, "ci_high": hi})

            flex = []
            jac = []
            for _, row in master.iterrows():
                phy = pooled_phy(row, level)
                if not phy:
                    continue
                llm = pooled_exp(row, exp, level)
                flex.append(1.0 if phy & llm else 0.0)
                union = phy | llm
                jac.append(len(phy & llm) / len(union) if union else 0.0)
            flexible_vectors[exp] = flex
            jaccard_vectors[exp] = jac
            estimate, lo, hi = bootstrap_mean(flex, rng)
            ci_rows.append({"metric": "flexible_any_code_overlap", "level": level, "experiment": exp, "n": len(flex), "estimate": estimate, "ci_low": lo, "ci_high": hi})
            estimate, lo, hi = bootstrap_mean(jac, rng)
            ci_rows.append({"metric": "pooled_jaccard_mean", "level": level, "experiment": exp, "n": len(jac), "estimate": estimate, "ci_low": lo, "ci_high": hi})

        for a, b in combinations(EXPERIMENTS, 2):
            # McNemar for paired exact underlying correctness.
            pred_a = comparable[f"{a}_underlying"].apply(lambda x: code_at_level(x, level)).tolist()
            pred_b = comparable[f"{b}_underlying"].apply(lambda x: code_at_level(x, level)).tolist()
            paired = [(r, pa, pb) for r, pa, pb in zip(ref, pred_a, pred_b) if r and pa and pb]
            b_count = sum((r == pa) and (r != pb) for r, pa, pb in paired)
            c_count = sum((r != pa) and (r == pb) for r, pa, pb in paired)
            test_rows.append({"test": "mcnemar_exact_underlying", "level": level, "comparison": f"{a} vs {b}", "n_pairs": len(paired), "a_correct_b_wrong": b_count, "a_wrong_b_correct": c_count, "p_value": mcnemar_exact_p(b_count, c_count)})

            for metric, vectors in [("flexible_any_code_overlap", flexible_vectors), ("pooled_jaccard_mean", jaccard_vectors)]:
                diff, lo, hi, p = bootstrap_diff(vectors[a], vectors[b], rng)
                test_rows.append({"test": "paired_bootstrap_difference", "metric": metric, "level": level, "comparison": f"{a} - {b}", "n_pairs": len(vectors[a]), "difference": diff, "ci_low": lo, "ci_high": hi, "p_value": p})

            ref_valid = [r for r, pa, pb in paired]
            pred_a_valid = [pa for r, pa, pb in paired]
            pred_b_valid = [pb for r, pa, pb in paired]
            diff, lo, hi, p = bootstrap_csmf_diff(ref_valid, pred_a_valid, pred_b_valid, rng)
            test_rows.append({"test": "paired_bootstrap_difference", "metric": "csmf_accuracy", "level": level, "comparison": f"{a} - {b}", "n_pairs": len(ref_valid), "difference": diff, "ci_low": lo, "ci_high": hi, "p_value": p})

    ci_df = pd.DataFrame(ci_rows)
    tests_df = pd.DataFrame(test_rows)
    ci_path = OUTPUT_DIR / f"ci_bootstrap_key_metrics_{N_BOOT}resamples.csv"
    tests_path = OUTPUT_DIR / f"statistical_tests_paired_comparisons_{N_BOOT}resamples.csv"
    ci_df.to_csv(ci_path, index=False)
    tests_df.to_csv(tests_path, index=False)
    print(ci_path.resolve())
    print(tests_path.resolve())
    print(ci_df.head(20).to_string(index=False))


if __name__ == "__main__":
    main()
