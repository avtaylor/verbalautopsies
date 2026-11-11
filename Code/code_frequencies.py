from __future__ import annotations
import re
from pathlib import Path
import pandas as pd
CODEBOOK_FILE = Path(__file__).resolve().parents[1] / 'Data' / 'MEIRU_CODS_LIST.txt'
CODE_PATTERN = re.compile(r"\b(\d{1,2})\s*-\s*(\d{1,2})\s*-\s*(\d{1,2})\b")

def canonical_code(groups: tuple[str, str, str]) -> str:
    return "-".join(f"{int(part):02d}" for part in groups)

def parse_codebook() -> pd.DataFrame:
    text = CODEBOOK_FILE.read_text(encoding="utf-8-sig")
    matches = list(CODE_PATTERN.finditer(text))
    rows: list[dict[str, str]] = []
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        description = re.sub(r"\s+", " ", text[match.end() : end].replace("|", "", 1).strip())
        rows.append({"level3_code": canonical_code(match.groups()), "level3_name": description})
    codebook = pd.DataFrame(rows).drop_duplicates("level3_code")

    # This synthetic full code represents physician underlying causes supplied
    # only at Level 1 in ucod_only_level1.csv.
    if "00-00-00" not in set(codebook["level3_code"]):
        codebook.loc[len(codebook)] = ["00-00-00", "Unspecifiable: Level 1 only"]
    return codebook

def code_at_level(code: str, level: str) -> str:
    parts = code.split("-")
    if level == "level3":
        return "-".join(parts[:3])
    if level == "level2":
        return "-".join(parts[:2])
    if level == "level1":
        return parts[0]
    raise ValueError(f"Unknown level: {level}")

def common_hierarchy_name(descriptions: list[str]) -> str:
    components = [[part.strip() for part in value.split(":")] for value in descriptions]
    common: list[str] = []
    for parts in zip(*components):
        if len(set(parts)) != 1:
            break
        common.append(parts[0])
    return ": ".join(common) if common else "Name unavailable"

def build_level_names(codebook: pd.DataFrame) -> dict[str, dict[str, str]]:
    names: dict[str, dict[str, str]] = {
        "level3": dict(zip(codebook["level3_code"], codebook["level3_name"])),
        "level2": {},
        "level1": {},
    }
    for level in ("level2", "level1"):
        grouped: dict[str, list[str]] = {}
        for row in codebook.itertuples(index=False):
            grouped.setdefault(code_at_level(row.level3_code, level), []).append(row.level3_name)
        names[level] = {code: common_hierarchy_name(values) for code, values in grouped.items()}
    names["level2"]["00-00"] = "Unspecifiable"
    names["level1"]["00"] = "Unspecifiable"
    return names
