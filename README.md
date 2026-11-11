# Verbal Autopsies Cause of Death Determinations Using GPT-5

An INSPIRE 2.0 project comparing GPT-assigned causes of death with physician
determinations using Karonga HDSS verbal autopsy data in Malawi.

Open [index.html](index.html) for the project description and EXP1–EXP5.

## Repository structure

- `Data/`: six minimal cause-code files and VA-type, age/sex, codebook and
  physician Level-1-only correction inputs.
- `Code/`: reproducible flexible, exact, CCC and CSMF calculations.
- `data_preparation/`: existing questionnaire-to-text pipeline.
- `OpenAPI_calls/`: existing LLM API pipeline.

## Reproduction

```powershell
python -m pip install -r Code/requirements.txt
python Code/run_analysis.py
```

Inputs default to `Data/` and generated results to `agreement_results/`.
The runner builds its MASTER intermediate automatically.
See [Code/README.md](Code/README.md) for methods and options.

## Project

INSPIRE 2.0 CC540. Team: Albert Dube, Amelia Taylor and Paul Kambiya.
Contact: ataylor@mubas.ac.mw.
