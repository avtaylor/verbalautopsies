# OpenAI API Calls

This folder contains code for sending verbal autopsy text inputs to the OpenAI API for cause-of-death assignment.

## Main file

- `verbal_autopsy_OpenAIcalls.js`: submits verbal autopsy narratives or questionnaire-derived text to OpenAI and processes structured cause-of-death outputs.

## Credentials

No API keys are stored in this repository. The script reads `OPENAI_API_KEY` from script properties or the configured runtime environment.

## Output role in the workflow

The API call outputs are later standardized and compared with physician-coded direct, underlying, and contributory causes of death in the analysis pipeline.
