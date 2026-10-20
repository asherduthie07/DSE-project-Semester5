import { Component, Input, OnChanges, OnDestroy, computed, inject, signal } from '@angular/core';
import { Subscription, forkJoin, from, map, mergeMap, of, switchMap, toArray } from 'rxjs';
import { ApiService, ChartResponse, DatasetId, RecordPage } from '../core/api';
import { HolographicChart } from './holographic-chart';
import { NUMERIC_AXES, OUTCOME, SceneData, categoricalBars, density, ridges, scatter } from './geometry';
import { displayValue, fieldLabel } from '../shared/field-metadata';
export function monthlyLandscape(rows:{month:string;encounters:number}[]):SceneData {
 const years=[...new Set(rows.map(r=>r.month.slice(0,4)))].sort().slice(-10);const subset=rows.filter(r=>years.includes(r.month.slice(0,4)));
 return {kind:'ridge',title:'Synthetic encounter timeline',axes:[{label:'Calendar month',categories:['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']},{label:'Encounters',min:0},{label:'Recorded year',categories:years}],points:subset.map(r=>({x:Number(r.month.slice(5))-1,y:r.encounters,z:years.indexOf(r.month.slice(0,4)),label:r.month,group:r.month.slice(0,4)})),sampleSize:subset.reduce((s,r)=>s+r.encounters,0),note:'Saved Phase II monthly encounter counts, latest ten recorded years. Each ridge is a calendar year; missing months are omitted, not interpolated as observations. Counts are encounters, not unique patients.'};
}
@Component({selector:'ms-data-explorer',standalone:true,imports:[HolographicChart],template:`
<section class="panel section-gap"><div class="panel-header"><div><div class="kicker">VISUALIZATION STUDIO / SOURCE DATA</div><h2>Explore the research landscape</h2></div><span class="tag">{{sourceRows()}} source rows</span></div>
 <div class="visual-toolbar">
 @if(axes().length){
  <label>View<select class="control" [value]="kind()" (change)="kind.set($any($event.target).value)"><option value="scatter">3D measured scatter</option><option value="density">Bivariate density estimate</option><option value="ridge">Outcome ridgelines</option></select></label>
  @for(axis of kind()==='ridge'?[0]:kind()==='density'?[0,2]:[0,1,2];track axis){<label>{{['X axis','Y axis','Z axis'][axis]}}<select class="control" [value]="selectedAxes()[axis]" (change)="setAxis(axis,$any($event.target).value)">@for(a of axes();track a){<option [value]="a" [selected]="a===selectedAxes()[axis]">{{fieldLabel(dataset,a)}}</option>}</select></label>}
  <label>Recorded class<select class="control" [value]="classFilter()" (change)="classFilter.set($any($event.target).value)"><option value="all">All classes</option>@for(c of classes();track c){<option [value]="c" [selected]="c===classFilter()">{{displayValue(dataset,outcome(),c)}}</option>}</select></label>
 }@else if(dataset==='uci_early_diabetes'){
  <label>Symptom<select class="control" [value]="feature()" (change)="feature.set($any($event.target).value)">@for(f of symptoms;track f){<option [value]="f" [selected]="f===feature()">{{fieldLabel(dataset,f)}}</option>}</select></label>
 }@else if(dataset==='synthea_csv'){
  <label>Saved analysis<select class="control" [value]="kind()" (change)="kind.set($any($event.target).value)"><option value="bars">Encounter categories</option><option value="temporal">Temporal ridgelines</option></select></label>
 }
 </div>
 @if(loading()){<p class="data-note" role="status">Loading bounded API pages… {{loaded()}} records received.</p>}
 @if(error()){<p class="error" role="alert">{{error()}}</p>}
 @if(!loading()&&!error()&&scene();as scene){<ms-holographic-chart [data]="scene"/>}
 <p class="visual-caption">{{rows().length?rows().length+' records fetched; ':''}}{{sourceRows()>6000&&dataset!=='synthea_csv'?'Limited to the first 6,000 source rows; not a random sample.':'Historical source snapshot, not live patient monitoring.'}} {{kind()==='scatter'?'Color encodes recorded outcome. Precision scatter projects X/Y; the data table retains Z.':''}}</p>
</section>`})
export class DataExplorer implements OnChanges,OnDestroy {
 fieldLabel=fieldLabel;displayValue=displayValue;outcome=()=>OUTCOME[this.dataset];
 @Input({required:true}) dataset:DatasetId='uci_cleveland_heart';private api=inject(ApiService);private subscription?:Subscription;
 private current=signal<DatasetId>('uci_cleveland_heart');rows=signal<Record<string,unknown>[]>([]);sourceRows=signal(0);loaded=signal(0);loading=signal(false);error=signal('');selectedAxes=signal<string[]>(['age','thalach','chol']);kind=signal('scatter');classFilter=signal('all');feature=signal('Polyuria');monthly=signal<{month:string;encounters:number}[]>([]);aggregate=signal<ChartResponse|null>(null);
 symptoms=['Polyuria','Polydipsia','sudden weight loss','weakness','Polyphagia','Genital thrush','visual blurring','Itching','Irritability','delayed healing','partial paresis','muscle stiffness','Alopecia','Obesity'];
 axes=computed(()=>NUMERIC_AXES[this.current()]??[]);classes=computed(()=>[...new Set(this.rows().map(r=>String(r[OUTCOME[this.current()]]??'Unknown')))].sort());
 scene=computed<SceneData|null>(()=>{
   if(this.current()==='synthea_csv'){if(this.kind()==='temporal')return monthlyLandscape(this.monthly());const s=this.aggregate()?.charts[0];return s?{kind:'bars',title:'Synthetic encounter categories',axes:[{label:'Encounter class',categories:s.categories},{label:'Encounters',min:0},{label:'Saved cohort',categories:['All encounters']}],points:s.values.map((y,x)=>({x,y,z:0,label:s.categories[x],group:'Synthetic encounters'})),sampleSize:s.sample_size,note:s.missingness_note+' Encounters are not unique patients.'}:null;}
   if(!this.rows().length)return null;if(this.current()==='uci_early_diabetes')return categoricalBars(this.rows(),this.feature(),'class');
   const a=this.selectedAxes();const mapped=this.kind()==='density'?[a[0],a[2],a[2]]:this.kind()==='ridge'?[a[0],a[0],a[0]]:a;
   const source=scatter(this.rows(),mapped,OUTCOME[this.current()],this.classFilter());return this.kind()==='density'?density(source):this.kind()==='ridge'?ridges(source):source;
 });
 ngOnChanges(){this.load();}
 setAxis(index:number,value:string){this.selectedAxes.update(a=>a.map((v,i)=>i===index?value:v));}
 load(){this.subscription?.unsubscribe();this.current.set(this.dataset);this.rows.set([]);this.error.set('');this.loaded.set(0);this.loading.set(true);this.classFilter.set('all');this.selectedAxes.set((NUMERIC_AXES[this.dataset]??[]).slice(0,3));this.kind.set(this.dataset==='synthea_csv'?'bars':'scatter');
  if(this.dataset==='synthea_csv'){this.subscription=forkJoin({chart:this.api.get<ChartResponse>(`/analytics/${this.dataset}/charts`,undefined,true),monthly:this.api.get<{rows:{month:string;encounters:number}[]}>(`/analytics/${this.dataset}/distributions`,{table:'monthly_encounters'},true)}).subscribe({next:r=>{this.aggregate.set(r.chart);this.monthly.set(r.monthly.rows);this.sourceRows.set(r.chart.charts[0].sample_size);this.loading.set(false);},error:()=>{this.error.set('Saved Synthea aggregates unavailable.');this.loading.set(false);}});return;}
  const path=`/datasets/${this.dataset}/records`;
  this.subscription=this.api.get<RecordPage>(path,{limit:100,offset:0},true).pipe(switchMap(first=>{this.sourceRows.set(first.source_rows);this.loaded.set(first.items.length);const offsets=Array.from({length:Math.max(0,Math.ceil(Math.min(first.total,6000)/100)-1)},(_,i)=>(i+1)*100);return offsets.length?from(offsets).pipe(mergeMap(offset=>this.api.get<RecordPage>(path,{limit:100,offset},true).pipe(map(page=>{this.loaded.update(n=>n+page.items.length);return page;})),4),toArray(),map(pages=>[first,...pages].sort((a,b)=>a.offset-b.offset).flatMap(p=>p.items))):of(first.items);})).subscribe({next:rows=>{this.rows.set(rows);this.loading.set(false);},error:()=>{this.error.set('Source records could not be loaded. No partial sample is plotted.');this.loading.set(false);}});
 }
 ngOnDestroy(){this.subscription?.unsubscribe();}
}
