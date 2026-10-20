import type { DatasetId, Task, PredictionField } from '../core/api';

/** Presentation-only vocabulary. Values are always the exact source/API values. */
export interface FieldVocabulary { label: string; description?: string; options?: Readonly<Record<string,string>> }
const yesNo={0:'No',1:'Yes'} as const;
const present={0:'Not recorded as present',1:'Recorded as present'} as const;
const heart:Record<string,FieldVocabulary>={
  age:{label:'Age',description:'Age in years.'},sex:{label:'Recorded Sex',description:'Sex as recorded in the Cleveland source.',options:{0:'Female',1:'Male'}},
  cp:{label:'Chest pain type',options:{1:'Typical angina',2:'Atypical angina',3:'Non-anginal pain',4:'Asymptomatic'}},
  trestbps:{label:'Resting blood pressure',description:'mm Hg on admission.'},chol:{label:'Serum cholesterol',description:'mg/dL.'},
  fbs:{label:'Fasting blood sugar >120 mg/dL',options:{0:'No',1:'Yes'}},
  restecg:{label:'Resting ECG result',options:{0:'Normal',1:'ST–T wave abnormality',2:'Probable/definite left ventricular hypertrophy'}},
  thalach:{label:'Maximum heart rate achieved'},exang:{label:'Exercise-induced angina',options:yesNo},
  oldpeak:{label:'Exercise-related ST depression'},slope:{label:'Peak exercise ST slope',options:{1:'Upsloping',2:'Flat',3:'Downsloping'}},
  ca:{label:'Major vessels shown by fluoroscopy',description:'Count of major vessels; source values 0–3.',options:{0:'0 vessels',1:'1 vessel',2:'2 vessels',3:'3 vessels'}},
  thal:{label:'Thalassemia test result',options:{3:'Normal',6:'Fixed defect',7:'Reversible defect'}},
  heart_disease_binary:{label:'Recorded heart disease',options:present},
  num:{label:'Original heart disease code',description:'Original Cleveland 0–4 code; codes 1–4 are not converted to unverified severity names.'},
};
const symptoms=['Polyuria','Polydipsia','sudden weight loss','weakness','Polyphagia','Genital thrush','visual blurring','Itching','Irritability','delayed healing','partial paresis','muscle stiffness','Alopecia','Obesity'];
const diabetes:Record<string,FieldVocabulary>={Age:{label:'Age',description:'Age in years.'},Gender:{label:'Gender',options:{Female:'Female',Male:'Male'}},class:{label:'Recorded diabetes class',options:{Negative:'Negative',Positive:'Positive'}}};
for(const name of symptoms)diabetes[name]={label:name[0].toUpperCase()+name.slice(1),description:'Symptom response recorded in the source questionnaire.',options:{No:'No',Yes:'Yes'}};
const stroke:Record<string,FieldVocabulary>={
  gender:{label:'Gender',options:{Female:'Female',Male:'Male',Other:'Other'}},age:{label:'Age',description:'Age in years.'},
  hypertension:{label:'Hypertension history',options:yesNo},heart_disease:{label:'Heart disease history',options:yesNo},
  ever_married:{label:'Ever married',options:{No:'No',Yes:'Yes'}},
  work_type:{label:'Work type',options:{Govt_job:'Government job',Never_worked:'Never worked',Private:'Private', 'Self-employed':'Self-employed',children:'Children'}},
  Residence_type:{label:'Residence type',options:{Rural:'Rural',Urban:'Urban'}},
  avg_glucose_level:{label:'Average glucose level'},bmi:{label:'BMI',description:'May be unavailable in the source record.'},
  smoking_status:{label:'Smoking status',options:{'formerly smoked':'Formerly smoked','never smoked':'Never smoked',smokes:'Smokes'}},
  stroke:{label:'Recorded stroke',options:{0:'No recorded stroke',1:'Recorded stroke'}},
};
const synthea:Record<string,FieldVocabulary>={GENDER:{label:'Gender',options:{M:'Male',F:'Female'}},MARITAL:{label:'Marital status',options:{M:'Married',S:'Single'}}};
const taskMap:Record<Task,Record<string,FieldVocabulary>>={heart,diabetes,stroke};
const datasetMap:Partial<Record<DatasetId,Record<string,FieldVocabulary>>>={uci_cleveland_heart:heart,uci_early_diabetes:diabetes,kaggle_stroke:stroke,synthea_csv:synthea};
export function vocabulary(scope:Task|DatasetId,field:string):FieldVocabulary|undefined{return (scope in taskMap?taskMap[scope as Task]:datasetMap[scope as DatasetId])?.[field];}
export function fieldLabel(scope:Task|DatasetId,field:string):string{return vocabulary(scope,field)?.label??field.replaceAll('_',' ');}
export function displayValue(scope:Task|DatasetId,field:string,value:unknown):string {
  if(value===null||value===undefined||value==='')return 'Missing / unknown';
  const options=vocabulary(scope,field)?.options;
  const exact=options?.[String(value)];if(exact!==undefined)return exact;
  // Phase IV explanations can serialize an integral categorical reference as "3.0".
  // Normalize that representation only for display, and only against a known code.
  if(typeof value==='string'&&/^-?\d+\.0+$/.test(value)){const label=options?.[String(Number(value))];if(label!==undefined)return label;}
  return String(value);
}
export function allowedOptions(scope:Task,field:PredictionField):{value:string;label:string}[] {
  return (field.allowed??[]).map(value=>({value:String(value),label:displayValue(scope,field.name,value)}));
}
