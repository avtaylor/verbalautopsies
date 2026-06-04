function callOpenAIRewrite(text) {
  const apiKey = PropertiesService.getScriptProperties().getProperty("OPENAI_API_KEY");

  const url = "https://api.openai.com/v1/responses";

  const prompt = `
Rewrite the following verbal autopsy clinical narrative into a clearer, shorter paragraph.

Rules:
- Do not add any new information.
- Do not infer a cause of death.
- Do not use outside knowledge.
- Remove repetition.
- Keep all clinically relevant facts in the same order as the original text.
- Keep uncertain, reported, or respondent-stated information as reported.
- Improve grammar and flow.
- Round illness duration to the nearest whole day where appropriate.
- Output only the rewritten paragraph.

Text:
${text}
`;

  const payload = {
    model: "gpt-4.1-mini",
    input: prompt
  };

  const options = {
    method: "post",
    contentType: "application/json",
    headers: {
      Authorization: "Bearer " + apiKey
    },
    payload: JSON.stringify(payload),
    muteHttpExceptions: true
  };

  const response = UrlFetchApp.fetch(url, options);

  const result = JSON.parse(response.getContentText());

  if (result.error) {
    return "ERROR: " + result.error.message;
  }

  const output =
    result.output?.[0]?.content?.[0]?.text;
  //console.log("Result :"+output)
  return output || "No response returned";

}



function callOpenAICOD(text) {
  const apiKey = PropertiesService.getScriptProperties().getProperty("OPENAI_API_KEY");

  const url = "https://api.openai.com/v1/responses";

  const prompt = `
You are assisting with verbal autopsy cause-of-death coding using the MEIRU cause-of-death coding system.

Infer the causes of death based on the following narrative of a relative: 

First identify the most immediate/direct cause of death from the narrative. If one cannot be established with certainty, leave blank.
Then identify the underlying cause of death. This field is mandatory and must always be completed. Finally identify any contributory causes of death that may have contributed but were not the main underlying cause.

Rules:
- give the underlying, direct and contributory causes.
- causes of death separated by semicolon.
- Causes of death are in English.  

Text:
${text}
`;

  const payload = {
    model: "gpt-5.2",
    input: prompt
  };

  const options = {
    method: "post",
    contentType: "application/json",
    headers: {
      Authorization: "Bearer " + apiKey
    },
    payload: JSON.stringify(payload),
    muteHttpExceptions: true
  };

  const response = UrlFetchApp.fetch(url, options);

  const result = JSON.parse(response.getContentText());

  if (result.error) {
    return "ERROR: " + result.error.message;
  }

  const output =
    result.output?.[0]?.content?.[0]?.text;
  return output || "No response returned";

}


function getMEIRUCOD(text) {
  const apiKey = PropertiesService.getScriptProperties().getProperty("OPENAI_API_KEY");

  const url = "https://api.openai.com/v1/responses";

const codebook=`
00 - 01 - 00 | Unspecifiable: No information (VAQ not available)
00 - 02 - 00 | Unspecifiable: Specific information missing on VAQ
00 - 03 - 00 | Unspecifiable: No significant pathology that would explain the death
00 - 04 - 00 | Unspecifiable: Multiple significant pathology, single COD can't be isolated
01 - 00 - 00 | Communicable disease: Unspecifiable
01 - 01 - 00 | Communicable disease: Acute febrile illness: Unspecifiable
01 - 01 - 01 | Communicable disease: Acute febrile illness: Malaria
01 - 01 - 02 | Communicable disease: Acute febrile illness: Menigitis
01 - 01 - 03 | Communicable disease: Acute febrile illness: Measles
01 - 01 - 04 | Communicable disease: Acute febrile illness: Pneumonia
01 - 01 - 05 | Communicable disease: Acute febrile illness: Diarrhoea with fever
01 - 01 - 06 | Communicable disease: Acute febrile illness: Sepsis
01 - 01 - 99 | Communicable disease: Acute febrile illness: Other specific unlisted
01 - 03 - 00 | Communicable disease: Hepatitis
01 - 04 - 00 | Communicable disease: TB/AIDS: Unspecifiable
01 - 04 - 01 | Communicable disease: TB/AIDS: Pulmonary TB
01 - 04 - 02 | Communicable disease: TB/AIDS: AIDS
01 - 04 - 03 | Communicable disease: TB/AIDS: Extrapulmonary TB
01 - 04 - 99 | Communicable disease: TB/AIDS: Other specific unlisted
01 - 05 - 00 | Communicable disease: Diarrhoeal disease without fever
01 - 06 - 00 | Communicable disease: Tetanus (exc. neonatal tetanus)
01 - 07 - 00 | Communicable disease: Rabies
01 - 99 - 00 | Communicable disease: Other specific unlisted
02 - 00 - 00 | Direct maternal cause: Unspecifiable
02 - 01 - 00 | Direct maternal cause: Abortion
02 - 02 - 00 | Direct maternal cause: Eclampsia
02 - 03 - 00 | Direct maternal cause: Ante/postpartum haemorrhage
02 - 04 - 00 | Direct maternal cause: Obstructed labour
02 - 05 - 00 | Direct maternal cause: Puerperal sepsis
02 - 06 - 00 | Direct maternal cause: Anaemia in pregnancy
02 - 99 - 00 | Direct maternal cause: Other specific unlisted
03 - 00 - 00 | Non communicable disease: Unspecifiable
03 - 01 - 00 | Non communicable disease: Cardiovascular disorder: Unspecifiable
03 - 01 - 01 | Non communicable disease: Cardiovascular disorder: Hypertension 
03 - 01 - 02 | Non communicable disease: Cardiovascular disorder: Congestive heart disease
03 - 01 - 03 | Non communicable disease: Cardiovascular disorder: Ischaemic heart disease
03 - 01 - 04 | Non communicable disease: Cardiovascular disorder: Cerebro vascular disease
03 - 01 - 99 | Non communicable disease: Cardiovascular disorder: Other specific unlisted
03 - 02 - 00 | Non communicable disease: Respiratory disorder: Unspecifiable
03 - 02 - 01 | Non communicable disease: Respiratory disorder: Chronic obstructive pulmonary disease
03 - 02 - 02 | Non communicable disease: Respiratory disorder: Asthma
03 - 02 - 99 | Non communicable disease: Respiratory disorder: Other specific unlisted
03 - 03 - 00 | Non communicable disease: Gastro intestinal disorder: Unspecifiable
03 - 03 - 01 | Non communicable disease: Gastro intestinal disorder: Peptic ulcer disease
03 - 03 - 02 | Non communicable disease: Gastro intestinal disorder: Liver cirrhosis
03 - 03 - 03 | Non communicable disease: Gastro intestinal disorder: Acute abdomen including obstruction
03 - 03 - 99 | Non communicable disease: Gastro intestinal disorder: Other specific unlisted
03 - 04 - 00 | Non communicable disease: Central nervous system disorder: Unspecifiable
03 - 04 - 01 | Non communicable disease: Central nervous system disorder: Mental/behavioural disorder
03 - 04 - 02 | Non communicable disease: Central nervous system disorder: Epilepsy
03 - 04 - 99 | Non communicable disease: Central nervous system disorder: Other specific unlisted
03 - 05 - 00 | Non communicable disease: Endocrine disorders: Unspecifiable
03 - 05 - 01 | Non communicable disease: Endocrine disorders: Diabetes
03 - 05 - 99 | Non communicable disease: Endocrine disorders: Other specific unlisted
03 - 06 - 00 | Non communicable disease: Neoplasm: Unspecifiable
03 - 06 - 01 | Non communicable disease: Neoplasm: Breast
03 - 06 - 02 | Non communicable disease: Neoplasm: Cervix/uterus
03 - 06 - 03 | Non communicable disease: Neoplasm: Liver
03 - 06 - 04 | Non communicable disease: Neoplasm: Gastro intestinal tract including abdominal but excluding liver
03 - 06 - 05 | Non communicable disease: Neoplasm: Lung
03 - 06 - 06 | Non communicable disease: Neoplasm: Oral
03 - 06 - 07 | Non communicable disease: Neoplasm: Oesophagus
03 - 06 - 99 | Non communicable disease: Neoplasm: Other specific unlisted
03 - 07 - 00 | Non communicable disease: Genito urinary disorders: Unspecifiable
03 - 07 - 01 | Non communicable disease: Genito urinary disorders: Kidney disorder
03 - 07 - 99 | Non communicable disease: Genito urinary disorders: Other specific unlisted
03 - 08 - 00 | Non communicable disease: Anaemia: Unspecifiable
03 - 08 - 01 | Non communicable disease: Anaemia: Caused by chronic communicable disease
03 - 08 - 99 | Non communicable disease: Anaemia: Other specific unlisted
03 - 09 - 00 | Non communicable disease: Nutritional disorder: Unspecifiable
03 - 09 - 01 | Non communicable disease: Nutritional disorder: Malnutrition
03 - 09 - 99 | Non communicable disease: Nutritional disorder: Other specific unlisted
03 - 99 - 00 | Non communicable disease: Other specific unlisted
04 - 00 - 00 | External cause: Unspecifiable
04 - 01 - 00 | External cause: Transport
04 - 02 - 00 | External cause: Fall
04 - 03 - 00 | External cause: Drowning/submersion
04 - 04 - 00 | External cause: Exposure to smoke/fire/flames
04 - 05 - 00 | External cause: Poisoning/exposure to noxious substance
04 - 06 - 00 | External cause: Use of weapon
04 - 07 - 00 | External cause: Contact with venomous animals and plants
04 - 08 - 00 | External cause: Hanging
04 - 09 - 00 | External cause: Choking
04 - 99 - 00 | External cause: Other specific unlisted
05 - 00 - 00 | Causes specific to infancy: Unspecifiable
05 - 01 - 00 | Causes specific to infancy: Miscarriage/abortion
05 - 02 - 00 | Causes specific to infancy: Stillbirth
05 - 03 - 00 | Causes specific to infancy: Prematurity/low birth weight
05 - 04 - 00 | Causes specific to infancy: Congenital abnormality
05 - 05 - 00 | Causes specific to infancy: Birth injury/asphyxia
05 - 06 - 00 | Causes specific to infancy: Neonatal sepsis
05 - 08 - 00 | Causes specific to infancy: Sudden infant death syndrome
05 - 09 - 00 | Causes specific to infancy: Neonatal tetanus
05 - 99 - 00 | Causes specific to infancy: Other specific unlisted
99 - 00 - 00 | Other specific unlisted
`;

const prompt = `
Your task is to map the causes of death given to the single best MEIRU code. You will receive underlying, direct and contributory causes of death.

Rules:
- Use only the MEIRU codes provided in the codebook below.
- Do not invent new codes.
- Do not use outside information.
- Base the decision only on the causes of death given.
- Return only valid JSON.

MEIRU codebook:
${codebook}

Case narrative:
${text}

Return JSON in this format:

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
`;

const payload = {
    model: "gpt-4.1",
    input: prompt
  };

  const options = {
    method: "post",
    contentType: "application/json",
    headers: {
      Authorization: "Bearer " + apiKey
    },
    payload: JSON.stringify(payload),
    muteHttpExceptions: true
  };

  const response = UrlFetchApp.fetch(url, options);

  const result = JSON.parse(response.getContentText());

  if (result.error) {
    return "ERROR: " + result.error.message;
  }

  const output =
    result.output?.[0]?.content?.[0]?.text;
  return output || "No response returned";

}
