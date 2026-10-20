import { displayValue, fieldLabel } from '../shared/field-metadata';
export interface Axis {label:string;categories?:string[];min?:number;max?:number}
export interface Datum {x:number;y:number;z:number;label:string;group:string}
export interface SceneData {kind:'scatter'|'bars'|'surface'|'ridge'|'wave'|'network'|'score';title:string;axes:[Axis,Axis,Axis];points:Datum[];note:string;sampleSize?:number;excluded?:number;grid?:number;edges?:[number,number][];score?:number}
export const NUMERIC_AXES:Record<string,string[]>={uci_cleveland_heart:['age','thalach','chol','trestbps','oldpeak'],kaggle_stroke:['age','bmi','avg_glucose_level']};
export const OUTCOME:Record<string,string>={uci_cleveland_heart:'heart_disease_binary',kaggle_stroke:'stroke',uci_early_diabetes:'class'};
export function scatter(rows:Record<string,unknown>[],axes:string[],outcome:string,filter='all'):SceneData {
  const scope=outcome==='heart_disease_binary'?'heart':outcome==='stroke'?'stroke':'diabetes';
  const selected=rows.filter(r=>filter==='all'||String(r[outcome])===filter);
  const valid=selected.filter(r=>axes.every(a=>typeof r[a]==='number'&&Number.isFinite(r[a])));
  return {kind:'scatter',title:'Measured feature space',axes:axes.map(label=>({label:fieldLabel(scope,label)})) as SceneData['axes'],points:valid.map(r=>({x:r[axes[0]] as number,y:r[axes[1]] as number,z:r[axes[2]] as number,group:displayValue(scope,outcome,r[outcome]),label:`Observation ${rows.indexOf(r)+1}`})),sampleSize:valid.length,excluded:selected.length-valid.length,note:'Observed values only. Complete cases for the selected axes; missing values are excluded, never imputed. Row numbers identify this fetched snapshot.'};
}
export function categoricalBars(rows:Record<string,unknown>[],feature:string,outcome:string):SceneData {
  const categories=[...new Set(rows.map(r=>String(r[feature]??'Missing')))].sort(), groups=[...new Set(rows.map(r=>String(r[outcome]??'Unknown')))].sort();
  const points:Datum[]=[];
  categories.forEach((c,x)=>groups.forEach((g,z)=>points.push({x,z,y:rows.filter(r=>String(r[feature]??'Missing')===c&&String(r[outcome]??'Unknown')===g).length,label:`${feature}: ${c}; ${outcome}: ${g}`,group:g})));
  return {kind:'bars',title:'Categorical frequency',axes:[{label:fieldLabel('diabetes',feature),categories},{label:'Observed count',min:0},{label:fieldLabel('diabetes',outcome),categories:groups}],points,sampleSize:rows.length,note:'Categories are discrete labels. Column height is an observed count; horizontal spacing does not represent biological distance.'};
}
export function density(source:SceneData):SceneData {
  const p=source.points,n=p.length,size=20;
  if(n<3)return {...source,kind:'surface',points:[],note:'At least three complete observations are required for density estimation.'};
  const xs=p.map(v=>v.x),zs=p.map(v=>v.z);const extent=(a:number[])=>[Math.min(...a),Math.max(...a)];const [xmin,xmax]=extent(xs),[zmin,zmax]=extent(zs);
  const bandwidth=(a:number[],range:number)=>{const m=a.reduce((s,x)=>s+x,0)/n;return Math.max(Math.sqrt(a.reduce((s,x)=>s+(x-m)**2,0)/(n-1))*n**(-1/6),range/100,1e-6);};
  const hx=bandwidth(xs,xmax-xmin),hz=bandwidth(zs,zmax-zmin);const points:Datum[]=[];
  for(let z=0;z<size;z++)for(let x=0;x<size;x++){const xv=xmin+(xmax-xmin||1)*x/(size-1),zv=zmin+(zmax-zmin||1)*z/(size-1);const y=p.reduce((s,q)=>s+Math.exp(-.5*(((xv-q.x)/hx)**2+((zv-q.z)/hz)**2)),0)/(n*2*Math.PI*hx*hz);points.push({x:xv,y,z:zv,label:'Estimated density',group:'Gaussian KDE'});}
  return {kind:'surface',title:'Bivariate density estimate',axes:[source.axes[0],{label:'Estimated joint density',min:0},source.axes[2]],points,grid:size,sampleSize:n,excluded:source.excluded,note:`Estimated, not directly observed: product Gaussian KDE on a 20 × 20 grid. Scott bandwidth n^(-1/6) × sample SD, minimum range/100. Bandwidths ${hx.toPrecision(4)} and ${hz.toPrecision(4)} in axis units. No boundary correction; visual mesh uses linear triangles.`};
}
export function ridges(source:SceneData):SceneData {
  const groups=[...new Set(source.points.map(p=>p.group))].sort();const values=source.points.map(p=>p.x);const min=Math.min(...values),max=Math.max(...values),width=(max-min||1)/12;
  const points:Datum[]=[];groups.forEach((g,z)=>{for(let b=0;b<12;b++){const lo=min+b*width,hi=min+(b+1)*width;points.push({x:lo+width/2,y:source.points.filter(p=>p.group===g&&p.x>=lo&&(b===11?p.x<=hi:p.x<hi)).length,z,label:`${g} · [${lo.toPrecision(4)}, ${hi.toPrecision(4)}${b===11?']':')'}`,group:g});}});
  return {kind:'ridge',title:'Observed distribution ridgelines',axes:[source.axes[0],{label:'Bin count',min:0},{label:'Recorded outcome',categories:groups}],points,sampleSize:source.points.length,note:'12 equal-width histogram bins with a shared range. Lines connect bin centers for display; they are not a fitted density. Group spacing is categorical.'};
}
export function axisBounds(data:SceneData):[number,number][] {return ['x','y','z'].map((k,i)=>{const v=data.points.map(p=>p[k as 'x'|'y'|'z']);let min=data.axes[i].min??(data.axes[i].categories?0:Math.min(...v)),max=data.axes[i].max??(data.axes[i].categories?data.axes[i].categories!.length-1:Math.max(...v));if(!Number.isFinite(min))min=0;if(!Number.isFinite(max))max=1;if(min===max){max=min+1;}return [min,max];});}
export function normalized(p:Datum,bounds:[number,number][]):[number,number,number]{return [p.x,p.y,p.z].map((v,i)=>(v-bounds[i][0])/(bounds[i][1]-bounds[i][0])*8-4) as [number,number,number];}
export const DECORATIVE_WAVE:SceneData={kind:'wave',title:'Spectral field',axes:[{label:''},{label:''},{label:''}],points:[],note:'Abstract decorative particle mesh · no scientific measurements.'};
