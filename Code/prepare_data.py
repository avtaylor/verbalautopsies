"""Create six minimal normalized CSV copies from the original private workbooks."""
from __future__ import annotations
import argparse
import hashlib
import json
import shutil
from pathlib import Path
import pandas as pd
import normalization as norm

DEFAULT_DATA = Path(__file__).resolve().parents[1] / 'Data'
SUPPORT_FILES = ('va_type.csv', 'age_sex.csv', 'ucod_only_level1.csv', 'MEIRU_CODS_LIST.txt')

def copy_support_files(source, target):
    target.mkdir(parents=True, exist_ok=True)
    for name in SUPPORT_FILES:
        shutil.copyfile(source / name, target / name)

def update_manifest(target):
    path = target / 'manifest.json'
    manifest = json.loads(path.read_text(encoding='utf-8'))
    for name in SUPPORT_FILES:
        entry = {'sha256': hashlib.sha256((target / name).read_bytes()).hexdigest()}
        if name.endswith('.csv'):
            frame = pd.read_csv(target / name, dtype=str)
            entry.update(rows=len(frame), columns=list(frame.columns))
        manifest['files'][name] = entry
    path.write_text(json.dumps(manifest, indent=2), encoding='utf-8')

def validate(frame, name):
    if frame['ident'].isna().any() or frame['ident'].str.strip().eq('').any():
        raise ValueError(f'{name}: missing identifiers')
    if frame['ident'].duplicated().any():
        raise ValueError(f'{name}: duplicate identifiers')

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-dir', required=True, type=Path)
    parser.add_argument('--data-dir', type=Path, default=DEFAULT_DATA)
    args = parser.parse_args()
    source, target = args.source_dir.resolve(), args.data_dir.resolve()
    if source == target:
        raise ValueError('Use a separate destination for trimmed copies')
    copy_support_files(source, target)
    norm.CODEBOOK_FILE = target / 'MEIRU_CODS_LIST.txt'
    norm.EXPERIMENT_FILES = {f'EXP{i}': source / f'EXP{i}.xlsx' for i in range(1, 6)}
    norm.PHY_FILE = source / 'PHY.xlsx'
    _, lookup = norm.parse_codebook()
    frames = {}
    phy = norm.load_phy(lookup)
    validate(phy, 'PHY')
    overrides = pd.read_csv(target / 'ucod_only_level1.csv', dtype=str)['ident'].dropna().str.strip()
    if not set(overrides).issubset(set(phy['ident'])):
        raise ValueError('Physician Level-1-only overrides contain unmatched identifiers')
    phy.loc[phy['ident'].isin(overrides), 'PHY_underlying'] = '00-00-00'
    va = pd.read_csv(target / 'va_type.csv', dtype=str)[['ident', 'vatype']]
    va['ident'] = va['ident'].str.strip()
    validate(va, 'va_type')
    phy = phy.merge(va, on='ident', how='left', validate='one_to_one')
    if not phy['vatype'].isin(['1', '2', '3']).all():
        raise ValueError('Missing or unknown VA type')
    frames['PHY'] = phy
    for name in norm.EXPERIMENT_FILES:
        frame = norm.load_experiment(name, lookup).drop(columns=f'{name}_parse_method')
        validate(frame, name)
        for kind in ['direct', 'underlying']:
            col = f'{name}_{kind}'
            frame[col] = frame[col].replace('99-00-00', '00-00-00')
        frame[f'{name}_contrib_set'] = frame[f'{name}_contrib_set'].apply(
            lambda codes: sorted({'00-00-00' if c == '99-00-00' else c for c in codes}))
        frames[name] = frame
    target.mkdir(parents=True, exist_ok=True)
    manifest = {'format': 'UTF-8 CSV; read all columns as strings', 'files': {}}
    for name, frame in frames.items():
        path = target / f'{name}.csv'
        frame.to_csv(path, index=False)
        check = pd.read_csv(path, dtype=str, keep_default_na=False)
        expected = frame.fillna('').astype(str)
        pd.testing.assert_frame_equal(check, expected, check_dtype=False)
        manifest['files'][path.name] = {'rows': len(frame), 'columns': list(frame.columns),
            'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}
        print(f'{name}: {len(frame)} records, {len(frame.columns)} columns')
    (target / 'manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    update_manifest(target)

if __name__ == '__main__':
    main()
