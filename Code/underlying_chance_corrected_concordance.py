from __future__ import annotations

from pathlib import Path

import pandas as pd

from code_frequencies import common_hierarchy_name, parse_codebook
from strict_agreement import LEVEL1_ONLY_CODE, clean_code, code_at_level


MASTER_FILE = Path("outputs") / "agreement_analysis" / "master_normalized_codes.csv"
OUTPUT_DIR = Path("outputs") / "analysis_redo" / "underlying_chance_corrected_concordance"
CAUSE_FILE = OUTPUT_DIR / "underlying_ccc_cause_specific.csv"
SUMMARY_FILE = OUTPUT_DIR / "underlying_ccc_mean_summary.csv"
CAUSE_LIST_FILE = OUTPUT_DIR / "underlying_ccc_fixed_cause_lists.csv"

EXPERIMENTS = ("EXP1", "EXP2", "EXP3", "EXP4", "EXP5")
LEVELS = ("level1", "level2", "level3")
PANELS = ("Overall", "Adult", "Child", "Neonate/stillbirth")
VA_TYPE_LABELS = {"1": "Adult", "2": "Child", "3": "Neonate/stillbirth"}


def build_name_maps() -> dict[str, dict[str, str]]:
    codebook = parse_codebook().copy()
    maps: dict[str, dict[str, str]] = {
        "level3": dict(zip(codebook["level3_code"], codebook["level3_name"])),
    }
    for level, width in (("level2", 5), ("level1", 2)):
        codebook[level] = codebook["level3_code"].str[:width]
        maps[level] = (
            codebook.groupby(level)["level3_name"]
            .apply(lambda values: common_hierarchy_name(values.tolist()))
            .to_dict()
        )
    maps["level1"]["00"] = "Unspecifiable"
    return maps


def panel_data(master: pd.DataFrame, panel: str) -> pd.DataFrame:
    if panel == "Overall":
        return master
    return master[master["va_type_label"] == panel]


def calculate(master: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    names = build_name_maps()
    cause_rows: list[dict[str, object]] = []
    summary_rows: list[dict[str, object]] = []
    list_rows: list[dict[str, object]] = []

    master = master.copy()
    master["va_type_label"] = (
        master["vatype"].astype(str).str.replace(".0", "", regex=False).map(VA_TYPE_LABELS)
    )

    for panel in PANELS:
        data = panel_data(master, panel)
        physician_full = data["PHY_underlying"].apply(clean_code)

        for level in LEVELS:
            eligible = physician_full.notna()
            if level != "level1":
                eligible &= physician_full != LEVEL1_ONLY_CODE

            comparison = data.loc[eligible].copy()
            reference = comparison["PHY_underlying"].apply(
                lambda value: code_at_level(clean_code(value), level)
            )
            # The fixed list is defined only by physician-reference causes and
            # is shared by every experiment.
            cause_list = sorted(reference.unique())
            n_causes = len(cause_list)
            if n_causes < 2:
                raise ValueError(f"CCC requires at least two causes: {panel}, {level}")
            chance = 1.0 / n_causes

            for code in cause_list:
                list_rows.append(
                    {
                        "panel": panel,
                        "level": level,
                        "cause_code": code,
                        "cause_name": names[level].get(code, "Code absent from MEIRU code list"),
                        "physician_support": int((reference == code).sum()),
                        "n_admissible_causes": n_causes,
                    }
                )

            for experiment in EXPERIMENTS:
                prediction = comparison[f"{experiment}_underlying"].apply(clean_code)
                prediction = prediction.apply(
                    lambda code: (
                        code_at_level(code, level)
                        if code is not None and (level == "level1" or code != LEVEL1_ONLY_CODE)
                        else None
                    )
                )
                experiment_cccs: list[float] = []

                for code in cause_list:
                    true_mask = reference == code
                    support = int(true_mask.sum())
                    true_positive = int((true_mask & (prediction == code)).sum())
                    false_negative = support - true_positive
                    concordance = true_positive / support
                    ccc = (concordance - chance) / (1.0 - chance)
                    experiment_cccs.append(ccc)
                    cause_rows.append(
                        {
                            "panel": panel,
                            "experiment": experiment,
                            "code_type": "underlying",
                            "level": level,
                            "cause_code": code,
                            "cause_name": names[level].get(code, "Code absent from MEIRU code list"),
                            "physician_support": support,
                            "true_positive": true_positive,
                            "false_negative": false_negative,
                            "cause_concordance_sensitivity": concordance,
                            "n_admissible_causes": n_causes,
                            "chance_concordance": chance,
                            "cause_specific_ccc": ccc,
                        }
                    )

                summary_rows.append(
                    {
                        "panel": panel,
                        "experiment": experiment,
                        "code_type": "underlying",
                        "level": level,
                        "n_eligible_records": len(comparison),
                        "n_admissible_causes": n_causes,
                        "chance_concordance": chance,
                        "unweighted_mean_ccc": sum(experiment_cccs) / n_causes,
                    }
                )

    return pd.DataFrame(cause_rows), pd.DataFrame(summary_rows), pd.DataFrame(list_rows)


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    master = pd.read_csv(MASTER_FILE, dtype=str, keep_default_na=False)
    cause_results, summary, cause_lists = calculate(master)
    cause_results.to_csv(CAUSE_FILE, index=False)
    summary.to_csv(SUMMARY_FILE, index=False)
    cause_lists.to_csv(CAUSE_LIST_FILE, index=False)
    print(summary.to_string(index=False))


if __name__ == "__main__":
    main()
