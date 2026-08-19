from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from calculate_csmf_accuracy import (
    EXPERIMENTS,
    LEVELS,
    OUTPUT_DIR,
    build_master,
    build_strata,
    code_at_level,
    csmf_metrics,
    parse_codebook,
)


N_SIMULATIONS = 1000
RANDOM_SEED = 20260712
STRATA_MODE = "va_type"


def sample_codes(rng: np.random.Generator, labels: list[str], probabilities: np.ndarray, n: int) -> pd.Series:
    if n <= 0 or not labels:
        return pd.Series(dtype=object)
    return pd.Series(rng.choice(labels, size=n, replace=True, p=probabilities))


def distribution(reference: pd.Series, labels: list[str], mode: str, overall_reference: pd.Series | None = None) -> np.ndarray:
    if mode == "uniform":
        return np.repeat(1 / len(labels), len(labels))

    source = overall_reference if mode == "overall_physician_prior" else reference
    counts = source.value_counts().reindex(labels, fill_value=0).astype(float)
    total = counts.sum()
    if total <= 0:
        return np.repeat(1 / len(labels), len(labels))
    return (counts / total).to_numpy()


def empirical_p_value(simulated: np.ndarray, observed: float) -> float:
    return float((np.sum(simulated >= observed) + 1) / (len(simulated) + 1))


def percentile_rank(simulated: np.ndarray, observed: float) -> float:
    return float(np.mean(simulated <= observed))


def run_simulations() -> tuple[pd.DataFrame, pd.DataFrame]:
    _, compact_lookup = parse_codebook()
    master = build_master(compact_lookup)
    strata = build_strata(master, STRATA_MODE)
    rng = np.random.default_rng(RANDOM_SEED)

    summary_rows: list[dict[str, object]] = []
    draw_rows: list[dict[str, object]] = []

    overall_phy_by_level = {
        level: master.loc[master["PHY_underlying"].notna(), "PHY_underlying"].apply(lambda code: code_at_level(code, level))
        for level in LEVELS
    }

    for stratum_values, data in strata:
        comparable = data[data["PHY_underlying"].notna()].copy()
        for level in LEVELS:
            reference = comparable["PHY_underlying"].dropna().apply(lambda code: code_at_level(code, level))
            if reference.empty:
                continue

            labels = sorted(reference.dropna().unique().tolist())
            if not labels:
                continue

            overall_reference = overall_phy_by_level[level]
            null_specs = {
                "uniform_codes": distribution(reference, labels, "uniform"),
                "overall_physician_prior": distribution(reference, labels, "overall_physician_prior", overall_reference),
                "stratum_physician_prior": distribution(reference, labels, "stratum_physician_prior"),
            }

            for exp in EXPERIMENTS:
                predicted = comparable[f"{exp}_underlying"].dropna().apply(lambda code: code_at_level(code, level))
                observed_metrics, _ = csmf_metrics(reference, predicted)
                observed = float(observed_metrics["csmf_accuracy_chance_corrected"])
                n_predicted = int(observed_metrics["n_predicted"])

                for null_model, probabilities in null_specs.items():
                    simulated = np.empty(N_SIMULATIONS, dtype=float)
                    for i in range(N_SIMULATIONS):
                        random_predicted = sample_codes(rng, labels, probabilities, n_predicted)
                        sim_metrics, _ = csmf_metrics(reference, random_predicted)
                        simulated[i] = float(sim_metrics["csmf_accuracy_chance_corrected"])
                        draw_rows.append(
                            {
                                **stratum_values,
                                "level": level,
                                "experiment": exp,
                                "null_model": null_model,
                                "simulation": i + 1,
                                "csmf_accuracy": simulated[i],
                            }
                        )

                    summary_rows.append(
                        {
                            **stratum_values,
                            "level": level,
                            "experiment": exp,
                            "null_model": null_model,
                            "n_simulations": N_SIMULATIONS,
                            "n_reference": int(observed_metrics["n_reference"]),
                            "n_predicted": n_predicted,
                            "observed_csmf_accuracy": observed,
                            "null_mean": float(np.mean(simulated)),
                            "null_sd": float(np.std(simulated, ddof=1)),
                            "null_p2_5": float(np.quantile(simulated, 0.025)),
                            "null_p50": float(np.quantile(simulated, 0.5)),
                            "null_p97_5": float(np.quantile(simulated, 0.975)),
                            "observed_minus_null_mean": observed - float(np.mean(simulated)),
                            "observed_percentile_vs_null": percentile_rank(simulated, observed),
                            "empirical_p_sim_ge_observed": empirical_p_value(simulated, observed),
                        }
                    )

    return pd.DataFrame(summary_rows), pd.DataFrame(draw_rows)


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    summary, draws = run_simulations()
    summary_path = OUTPUT_DIR / f"monte_carlo_csmf_accuracy_baselines_{N_SIMULATIONS}sim.csv"
    draws_path = OUTPUT_DIR / f"monte_carlo_csmf_accuracy_draws_{N_SIMULATIONS}sim.csv"
    summary.to_csv(summary_path, index=False)
    draws.to_csv(draws_path, index=False)
    print(summary_path.resolve())
    print(draws_path.resolve())
    print(
        summary[
            (summary["stratum"] == "overall")
            & (summary["level"] == "level2")
            & (summary["null_model"].isin(["uniform_codes", "overall_physician_prior"]))
        ][
            [
                "experiment",
                "null_model",
                "observed_csmf_accuracy",
                "null_mean",
                "null_p2_5",
                "null_p97_5",
                "observed_percentile_vs_null",
                "empirical_p_sim_ge_observed",
            ]
        ].to_string(index=False)
    )


if __name__ == "__main__":
    main()
