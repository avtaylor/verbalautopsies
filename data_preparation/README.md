# Data Preparation

This folder contains code for transforming structured verbal autopsy questionnaire variables into text narratives that can be supplied to a large language model.

## Main file

- `CreateNarrativesFromQuestionnaireVars.ipynb`: prepares questionnaire variables as text. The notebook converts coded questionnaire responses into human-readable text representations while preserving positive and negative responses relevant to cause-of-death determination.

## Inputs

The notebook expects authorized local access to the restricted verbal autopsy questionnaire data and the associated data dictionary. These data files are not included in this public repository.

## Output role in the workflow

The generated questionnaire-as-text outputs are used as inputs to the LLM experiments, including questionnaire-only and reconstructed-narrative conditions.
