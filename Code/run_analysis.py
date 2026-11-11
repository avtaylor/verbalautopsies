"""Run the four agreement method families using the self-contained data folder."""
from __future__ import annotations
import argparse
import importlib
import json
import platform
from pathlib import Path
import numpy as np
import pandas as pd
from prepare_data import DEFAULT_DATA, validate

def build_master(data_dir):
    master = None
    for name in ['PHY', 'EXP1', 'EXP2', 'EXP3', 'EXP4', 'EXP5']:
        columns = (['ident', 'PHY_direct', 'PHY_underlying', 'PHY_contrib', 'vatype']
                   if name == 'PHY' else
                   ['ident', f'{name}_direct', f'{name}_underlying', f'{name}_contrib_set'])
        frame = pd.read_csv(data_dir / f'{name}.csv', dtype=str, keep_default_na=False)
        if list(frame.columns) != columns:
            raise ValueError(f'{name}: expected only {columns}')
        validate(frame, name)
        master = frame if master is None else master.merge(
            frame, on='ident', how='outer', validate='one_to_one')
    va = pd.read_csv(data_dir / 'va_type.csv', dtype=str, keep_default_na=False)[['ident', 'vatype']]
    va['ident'] = va['ident'].str.strip()
    validate(va, 'va_type')
    master = master.merge(va, on='ident', how='left', validate='one_to_one', suffixes=('_phy', ''))
    known = master['vatype_phy'].fillna('').ne('')
    if not master.loc[known, 'vatype_phy'].eq(master.loc[known, 'vatype']).all():
        raise ValueError('va_type.csv disagrees with the VA type in PHY.csv')
    if not master['vatype'].isin(['1', '2', '3']).all():
        raise ValueError('Missing or unknown VA type in va_type.csv')
    master = master.drop(columns='vatype_phy')
    demographics = pd.read_csv(data_dir / 'age_sex.csv', dtype=str, keep_default_na=False)
    demographics['ident'] = demographics['ident'].str.strip()
    validate(demographics, 'age_sex')
    master = master.merge(demographics[['ident', 'Age', 'Sex']], on='ident',
                          how='left', validate='one_to_one')
    return master

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data-dir', type=Path, default=DEFAULT_DATA)
    parser.add_argument('--output-dir', type=Path,
                        default=DEFAULT_DATA.parent / 'agreement_results')
    parser.add_argument('--bootstrap-replicates', type=int, default=5000)
    args = parser.parse_args()
    if args.bootstrap_replicates < 1:
        parser.error('--bootstrap-replicates must be positive')
    out = args.output_dir.resolve()
    if out == args.data_dir.resolve():
        parser.error('Results must have a separate output directory')
    out.mkdir(parents=True, exist_ok=True)
    import code_frequencies
    code_frequencies.CODEBOOK_FILE = args.data_dir.resolve() / 'MEIRU_CODS_LIST.txt'
    master_path = out / 'master_normalized_codes.csv'
    master = build_master(args.data_dir)
    master.to_csv(master_path, index=False)
    tasks = [
        ('strict_agreement', 'exact'),
        ('underlying_chance_corrected_concordance', 'ccc'),
        ('csmf_underlying_direct', 'csmf'),
        ('flexible_agreement', 'flexible_all_causes'),
        ('flexible_agreement_underlying_direct_pooled', 'flexible_underlying_direct'),
    ]
    for module_name, folder in tasks:
        module = importlib.import_module(module_name)
        module.MASTER_FILE = master_path
        module.OUTPUT_DIR = out / folder
        if hasattr(module, 'BOOTSTRAP_REPLICATES'):
            module.BOOTSTRAP_REPLICATES = args.bootstrap_replicates
        if module_name == 'underlying_chance_corrected_concordance':
            module.CAUSE_FILE = module.OUTPUT_DIR / 'underlying_ccc_cause_specific.csv'
            module.SUMMARY_FILE = module.OUTPUT_DIR / 'underlying_ccc_mean_summary.csv'
            module.CAUSE_LIST_FILE = module.OUTPUT_DIR / 'underlying_ccc_fixed_cause_lists.csv'
        print(f'Running {folder}', flush=True)
        module.main()
        if hasattr(module, 'BOOTSTRAP_REPLICATES'):
            note = module.OUTPUT_DIR / 'methods.md'
            if note.exists():
                note.write_text(note.read_text(encoding='utf-8').replace(
                    '5,000', f'{args.bootstrap_replicates:,}'), encoding='utf-8')
    (out / 'run_settings.json').write_text(
        json.dumps({'bootstrap_replicates': args.bootstrap_replicates,
                    'random_seed': 20261027, 'records': len(master),
                    'python': platform.python_version(), 'numpy': np.__version__,
                    'pandas': pd.__version__}, indent=2),
        encoding='utf-8')

if __name__ == '__main__':
    main()
