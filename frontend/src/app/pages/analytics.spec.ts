import { TestBed } from '@angular/core/testing';
import { of } from 'rxjs';
import { AnalyticsPage } from './analytics';
import { ApiService } from '../core/api';

describe('saved analytics chart mapping',()=>{
  it('maps API outcome counts and Pearson pairs without recomputation',()=>{
    const api={chart:()=>of({dataset_id:'uci_cleveland_heart',charts:[{id:'outcome',label:'Recorded outcome',categories:['0','1'],values:[164,139],unit:'records',sample_size:303,missingness_note:'saved'}],approved_figures:[],source_url:'https://example.org',caveat:'research'}),get:(path:string)=>of(path.endsWith('distributions')?{rows:[{group:'all',feature:'sex',category:'0',count:97,pct_all:32}]}:path.endsWith('correlations')?{tables:{correlations:[{method:'pearson',left:'age',right:'chol',coefficient:.2,n:303}]},missing_policy:'pairwise'}:{hypotheses:[]})};
    TestBed.configureTestingModule({imports:[AnalyticsPage],providers:[{provide:ApiService,useValue:api}]});
    const page=TestBed.createComponent(AnalyticsPage).componentInstance;
    const option=page.outcomeOption() as any;expect(option.series[0].data).toEqual([164,139]);
    const heatmap=page.correlationOption() as any;expect(heatmap.series[0].data).toEqual([[0,1,.2],[1,0,.2]]);
    expect(page.hypotheses().length).toBe(0);
  });
});
