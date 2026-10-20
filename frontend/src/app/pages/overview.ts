import { Component, DestroyRef, inject, signal } from '@angular/core';
import { DecimalPipe } from '@angular/common';
import { RouterLink } from '@angular/router';
import { forkJoin } from 'rxjs';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { ApiService, BigDataStatus, ChartResponse, Comparison, DatasetList, Task, taskNames, tasks } from '../core/api';
import { ChartComponent, chartBase } from '../shared/chart';
import { HolographicChart } from '../visualization/holographic-chart';
import { DECORATIVE_WAVE } from '../visualization/geometry';
import { displayValue } from '../shared/field-metadata';
@Component({standalone:true,imports:[DecimalPipe,RouterLink,ChartComponent,HolographicChart],template:`
<div class="page-head"><div><div class="eyebrow">RESEARCH INTELLIGENCE / OVERVIEW</div><h1>Healthcare Intelligence Overview</h1><p class="subtitle">Unified analytics, machine learning and data engineering.</p></div><a class="btn secondary" routerLink="/research">Explore reports ↗</a></div>
<section class="panel glass-ultra hero-field"><div class="eyebrow">MEDISCOPE AI / HOLOGRAPHIC RESEARCH WORKSPACE</div><h2>Evidence. In a new dimension.</h2><p class="subtitle">Explore source cohorts, inspect experiments, and interrogate saved models.</p><ms-holographic-chart [data]="wave"/></section>
@if (loading()) { <div class="grid grid-4">@for(i of [1,2,3,4];track i){<div class="loading"></div>}</div> }
@if (error()) { <div class="error">{{error()}} Start the FastAPI backend to load verified research data.</div> }
@if (datasets()) {
<div class="grid grid-4">
  <div class="panel metric"><span class="metric-icon">▤</span><div class="metric-value">{{datasets()!.datasets.length}}</div><div>Available datasets</div><div class="metric-note">Independent registered sources</div></div>
  <div class="panel metric"><span class="metric-icon">⌁</span><div class="metric-value">{{diseaseRecords() | number}}</div><div>Disease cohort records</div><div class="metric-note">Separate cohorts; summed rows only</div></div>
  <div class="panel metric"><span class="metric-icon">✧</span><div class="metric-value">{{experimentCount()}}</div><div>ML experiments</div><div class="metric-note">Registered non-baseline trials</div></div>
  <div class="panel metric"><span class="metric-icon">⬡</span><div class="metric-value" [class.signal]="readyServices()>0">{{readyServices()}} / 3</div><div>Live services ready</div><div class="metric-note">MongoDB · HDFS · YARN</div></div>
</div>
<div class="grid grid-2 section-gap">
  <section class="panel chart-tall"><div class="panel-header"><div><div class="kicker">DATA LANDSCAPE</div><h2>Disease data overview</h2></div><select class="control" aria-label="Outcome dataset" [value]="task()" (change)="selectTask($event)">@for(t of tasks;track t){<option [value]="t" [selected]="t===task()">{{taskNames[t]}}</option>}</select></div>
  @if(chartOption()){<ms-chart [option]="chartOption()!" [label]="taskNames[task()] + ' outcome distribution'"/>}<div class="data-note">{{chart()?.charts?.[0]?.missingness_note}}</div></section>
  <section class="panel chart-tall"><div class="panel-header"><div><div class="kicker">HELD-OUT TEST EVALUATION</div><h2>Selected model performance</h2></div><span class="tag">{{comparison()?.selected_model?.replaceAll('_',' ')}}</span></div>
  @if(modelOption()){<ms-chart [option]="modelOption()!" label="Accuracy, precision, recall and F1 for selected model"/>}<div class="data-note">Selected using development cross-validation. Test metrics are shown for evaluation only.</div></section>
</div>
<div class="grid grid-3 section-gap">
  <section class="panel"><div class="kicker">SOURCE VOLUME</div><h2>Records by source</h2>@for(d of datasets()!.datasets;track d.id){<div class="dataset-row"><span>{{d.name}}</span><strong class="mono">@for(pair of entries(d.tables);track pair[0]){ {{pair[0]}} {{pair[1] | number}} }</strong></div>}<p class="small muted">Synthea patients and encounters are separate synthetic tables. These are not unique patient counts across sources.</p></section>
  <section class="panel"><div class="kicker">INFRASTRUCTURE</div><h2>System health</h2>@for(s of statusEntries();track s[0]){<div class="dataset-row"><span>{{s[0]}}</span><span class="tag" [class.warn]="s[1].status !== 'READY'">{{s[1].status}}</span></div>}<a routerLink="/big-data" class="small">Open Big Data Monitor ↗</a></section>
  <section class="panel"><div class="kicker">RESEARCH CONTEXT</div><h2>Evidence, with limits</h2><p class="muted small">Statistical associations and model scores are derived from historical datasets. None of the models are clinically validated.</p><div class="dataset-row"><span>Selected models</span><strong>{{selectedSummary()}}</strong></div><div class="dataset-row"><span>Full experiments</span><strong>{{experimentCount()}}</strong></div><a routerLink="/analytics" class="small">Explore Phase II findings ↗</a></section>
</div>}
`,styles:[`.dataset-row{display:flex;justify-content:space-between;gap:16px;align-items:center;border-bottom:1px solid var(--holo-border);padding:12px 0;font-size:11px;color:#9db2c7}.dataset-row strong{color:#e2edf8;text-align:right;font-size:11px}`]})
export class OverviewPage {
 wave=DECORATIVE_WAVE;
 private api=inject(ApiService);private destroy=inject(DestroyRef);tasks=tasks;taskNames=taskNames;loading=signal(true);error=signal('');datasets=signal<DatasetList|null>(null);status=signal<BigDataStatus|null>(null);task=signal<Task>('heart');charts=new Map<Task,ChartResponse>();comparisons=new Map<Task,Comparison>();chart=signal<ChartResponse|null>(null);comparison=signal<Comparison|null>(null);chartOption=signal<any>(null);modelOption=signal<any>(null);
 constructor(){forkJoin({datasets:this.api.datasets(),status:this.api.get<BigDataStatus>('/bigdata/status'),heartChart:this.api.chart('heart'),heartComparison:this.api.comparison('heart'),diabetesComparison:this.api.comparison('diabetes'),strokeComparison:this.api.comparison('stroke')}).pipe(takeUntilDestroyed(this.destroy)).subscribe({next:r=>{this.datasets.set(r.datasets);this.status.set(r.status);this.charts.set('heart',r.heartChart);this.comparisons.set('heart',r.heartComparison);this.comparisons.set('diabetes',r.diabetesComparison);this.comparisons.set('stroke',r.strokeComparison);this.update('heart');this.loading.set(false)},error:()=>{this.error.set('Overview data could not be loaded.');this.loading.set(false)}})}
 entries(o:Record<string,number>){return Object.entries(o)}
 diseaseRecords(){return this.datasets()?.datasets.filter(d=>d.id!=='synthea_csv').reduce((n,d)=>n+Object.values(d.tables).reduce((a,b)=>a+b,0),0)??0}
 experimentCount(){return [...this.comparisons.values()].reduce((n,c)=>n+c.trials.filter(t=>!t.algorithm.startsWith('dummy')).length,0)}
 selectedSummary(){return [...this.comparisons.values()].map(c=>c.selected_model.replaceAll('_',' ')).join(' · ')}
 readyServices(){return Object.values(this.status()?.live??{}).filter(x=>x.status==='READY').length}
 statusEntries(){return Object.entries(this.status()?.live??{})}
 title(v:string){return v.toUpperCase()}
 selectTask(e:Event){const t=(e.target as HTMLSelectElement).value as Task;this.task.set(t);if(this.charts.has(t)&&this.comparisons.has(t)){this.update(t);return}forkJoin({chart:this.api.chart(t),comparison:this.api.comparison(t)}).pipe(takeUntilDestroyed(this.destroy)).subscribe({next:r=>{this.charts.set(t,r.chart);this.comparisons.set(t,r.comparison);this.update(t)},error:()=>this.error.set('Selected dataset artifacts are unavailable.')})}
 update(t:Task){const c=this.charts.get(t)!;const m=this.comparisons.get(t)!;this.chart.set(c);this.comparison.set(m);const s=c.charts[0],target=t==='heart'?'heart_disease_binary':t==='stroke'?'stroke':'class';this.chartOption.set({...chartBase,xAxis:{type:'category',data:s.categories.map(v=>displayValue(t,target,v)),axisLabel:{color:'#91a6be'}},yAxis:{type:'value',name:s.unit,splitLine:{lineStyle:{color:'#223248'}}},series:[{type:'bar',data:s.values,itemStyle:{color:'#39d9d0',borderRadius:[5,5,0,0]},barMaxWidth:55}],tooltip:{trigger:'axis'}});const selected=m.trials.find(x=>x.selected);const names=['accuracy','precision','recall','f1'];this.modelOption.set({...chartBase,xAxis:{type:'value',max:1,splitLine:{lineStyle:{color:'#223248'}}},yAxis:{type:'category',data:names.map(x=>x.toUpperCase()),axisLabel:{color:'#91a6be'}},series:[{type:'bar',data:names.map((x,i)=>({value:selected?.test_metrics[x]??0,itemStyle:{color:['#39d9d0','#60a5fa','#a78bfa','#34d399'][i]}})),barMaxWidth:24,label:{show:true,position:'right',formatter:(p:any)=>Number(p.value).toFixed(3),color:'#c8d7e5'}}],tooltip:{trigger:'axis'}})}
}
