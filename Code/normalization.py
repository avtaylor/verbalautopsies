from __future__ import annotations
import json
import re
from pathlib import Path
import pandas as pd
CODEBOOK_FILE = Path(__file__).resolve().parents[1] / 'Data' / 'MEIRU_CODS_LIST.txt'
CODE_PATTERN = re.compile(r"\b(\d{1,2})\s*-\s*(\d{1,2})\s*-\s*(\d{1,2})\b")
EXPERIMENT_FILES = {}
PHY_FILE = None

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
    # Ignore empty/formula-only worksheet rows; identifiers remain mandatory and
    # duplicate nonblank identifiers are still rejected by the master merge.
    df = df[df["ident"].notna() & df["ident"].str.strip().ne("")].copy()
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
