# Verbal Autopsy Narrative Generation and AI-Assisted Cause of Death Assignment

This repository contains scripts for transforming structured Verbal Autopsy (VA) questionnaire data into narrative text and using Large Language Models (LLMs) through the OpenAI API to support cause-of-death (CoD) assignment.

## Overview

Verbal Autopsy questionnaires contain structured responses to questions about the deceased answered by a close relative or someone who cared for the deceased. The variables describe symptoms, medical history, circumstances, and events preceding death. These data is collected as coded variables. The questionnaire also contains a textual account (i.e. narrative) of the death in the words of the respondent.

This repository provides tools to:
* Convert structured questionnaire responses to coded variables into human-readable narratives.
* Submit the human readable narratives to OpenAI models to generate direct, underlying, and contributory causes of death (COD). 
* Ask AI to assign codes to causes of deaths - we use the MEIRU codes in the prompt. 

The workflow contains only the main code without helper functions. The code was developed to support research into AI-assisted verbal autopsy coding and cause-of-death determination.

---

## Repository Structure

```text
.
├── CreateNarrativesFromQuestionnaire.ipynb
│   └── Generates textual representation from questionnaire variables
│
├── verbal_autopsy_OpenAIcalls.js
│   └── Generates coherent narratives from textual representation of questionnaire data
│   └── Sends narratives to OpenAI API to determine COD and processes responses
│
├── README.md
└── LICENSE
```

---

## Description of workflow supported by the code

### Step 1: Generate Narrative from Questionnaire Data

Structured questionnaire variables are transformed into narrative text. Inputs are the excel files containing the questionnaire data and the data dictionary.
Questionnaire responses are re-written using the python code into textual representation of this type:

```text
The deceased was a 83-year-old male. Hospital told COD was no. TB -interva was no. HIV/AIDS was no. Hypertension - was no. Diabetes was no. Epilepsy - was no. Fever was no. Cough was no. Breathlessness was no. Chest pain was no. Diarrhoea - was no. Vomit was no. Abdominal pain was no. Abdomen distension was no. Abdominal mass was no. Headache was no. Stiff neck was no. Confusion was no. Unconscious >24 hrs was no. Convulsions - was no. No urine was no. Urinate more often was no. Skin rash was no. Face swelling was no. Feet swelling was no. Any lumps was no. Lump neck was no. Lump armpit was no. Lump groin was no. Lump other was no. Weight loss - was no. The deceased had body stiffness. One side paralysis was no. The deceased had swallow pain. Swallow pain days: 5.0. Yellow eyes - was no. Anaemic was no. Injury - was no. Operation - was no. The deceased had attend hosp. Trad med was no. HIV test date estimated was day and month unknown. Adult Child or Neonate was vaa (adult).
```

The javascript code then calls OpenAI to generate a more cohesive narrative form teh tectual representation of the questionnaire responses:

```text
The deceased was an 83-year-old male with no reported history of tuberculosis, HIV/AIDS, hypertension, diabetes, epilepsy, or symptoms such as fever, cough, breathlessness, chest pain, diarrhea, vomiting, abdominal pain or distension, headaches, stiff neck, confusion, unconsciousness over 24 hours, convulsions, urinary issues, skin rash, swelling, lumps, or weight loss. He experienced body stiffness and had swallowing pain for 5 days. There was no yellowing of the eyes, anemia, injury, or surgery. He attended a hospital but did not use traditional medicine. The HIV test date is unknown.
```
---
### Step 2: Submit to OpenAI

The narrative text is submitted to an OpenAI model together with a prompt requesting cause-of-death determination.

The model is instructed to identify:

1. Direct (immediate) cause of death
2. Underlying cause of death (mandatory)
3. Contributory causes of death

---
The results from OpenAI is then mapped into COD codes and are stored in a json format. 
Return JSON in this format:

### Expected JSON Output

The model returns results in the following JSON format:

```json
{
  "direct_cause_of_death": {
    "selected_full_code": "",
    "selected_description": "",
    "confidence": "high | medium | low",
    "supporting_evidence": [],
    "brief_explanation": ""
  },
  "underlying_cause_of_death": {
    "selected_full_code": "",
    "selected_description": "",
    "confidence": "high | medium | low",
    "supporting_evidence": [],
    "brief_explanation": ""
  },
  "contributory_causes_of_death": [
    {
      "selected_full_code": "",
      "selected_description": "",
      "confidence": "high | medium | low",
      "supporting_evidence": [],
      "brief_explanation": ""
    }
  ],
  "overall_uncertainty": "",
  "coding_notes": ""
}
```

#### Field Descriptions

| Field                  | Description                                                                                          |
| ---------------------- | ---------------------------------------------------------------------------------------------------- |
| `selected_full_code`   | Full cause-of-death code selected from the coding framework.                                         |
| `selected_description` | Human-readable description corresponding to the selected code.                                       |
| `confidence`           | Model confidence in the assigned cause (`high`, `medium`, or `low`).                                 |
| `supporting_evidence`  | List of symptoms, clinical findings, circumstances, or narrative evidence supporting the assignment. |
| `brief_explanation`    | Short justification explaining why the cause was selected.                                           |
| `overall_uncertainty`  | Summary of any uncertainty, ambiguity, conflicting evidence, or missing information.                 |
| `coding_notes`         | Additional notes relevant to coding decisions, assumptions, or alternative diagnoses considered.     |

The `underlying_cause_of_death` field is mandatory. The model should always attempt to identify the disease or condition that initiated the chain of events leading to death, even when the direct cause of death is uncertain.


## Disclaimer

This software is intended for research purposes only.

Outputs generated by Large Language Models should be reviewed by qualified clinicians, physicians, or researchers before being used in any official mortality coding process or public health reporting system.

---

## Citation

If you use this repository in academic work, please cite:

```text
Taylor, A.
AI-assisted Cause of Death Assignment from Verbal Autopsy Data.
Kuyesera AI Lab (KAI Lab), Malawi University of Business and Applied Sciences (MUBAS).
```

---

## License

This project is distributed under the terms specified in the LICENSE file.

---

## Acknowledgements

* Malawi Epidemiology and Intervention Research Unit (MEIRU)
* OpenAI API
