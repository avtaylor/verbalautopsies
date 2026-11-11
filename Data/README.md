# Minimal agreement data

EXP1.csv through EXP5.csv each contain 5,150 records and four columns:
identifier, direct cause, underlying cause, and contributory cause set.
PHY.csv contains 5,150 records and five columns: identifier, direct cause,
underlying cause, contributory cause, and VA type for the stratified CCC panels.

The files were recreated from the original workbooks using the existing study
normalization rules. Every retained value was verified against the existing
normalized master. Original workbooks are unchanged. Read CSV columns as strings
to preserve identifiers and code formatting.

Narratives, evidence, explanations, confidence values, age, sex, descriptions,
and other unused fields are excluded from the six cause files. The manifest records exact schemas, row
counts and SHA-256 hashes. These files retain study identifiers for joining.

Preparation and analysis code: `../Code/`.

Supporting inputs copied unchanged from the original source folder:

- `va_type.csv`: VA-type source, checked against PHY by the analysis runner.
- `age_sex.csv`: age and sex, joined into the analysis intermediate.
- `MEIRU_CODS_LIST.txt`: code definitions and labels for normalization, CCC and CSMF.
- `ucod_only_level1.csv`: physician underlying Level-1-only corrections used
  during preparation; already applied in the trimmed PHY file.

The runner needs no input outside this folder. Age and sex are available for
demographic stratification; the current agreement calculations remain unchanged.
