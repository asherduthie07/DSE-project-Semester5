import { vi } from 'vitest';
import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { of } from 'rxjs';
import { PredictionPage } from './prediction';
import { ApiService, PredictionSchema } from '../core/api';

describe('prediction form',()=>{
  const schema:PredictionSchema={task:'heart',selected_model:'logistic_regression',artifact_version:'v1',warning:'Research only',features:[{name:'age',type:'number',integer:true,minimum:0,maximum:120,nullable:false},{name:'sex',type:'category',allowed:['0','1'],nullable:false}]};
  let predict=vi.fn().mockReturnValue(of({task:'heart',predicted_class:1,estimated_model_score:.7,decision_threshold:.5,model_name:'logistic_regression',model_version:'v1',predicted_source_label:1,explanation:{method:'saved',top_changes:[],caveat:'noncausal'},warning:'Research only'}));
  beforeEach(async()=>{predict.mockClear();await TestBed.configureTestingModule({imports:[PredictionPage],providers:[provideHttpClient(),{provide:ApiService,useValue:{get:()=>of(schema),predict}}]}).compileComponents()});
  it('requires exact schema fields and rejects out-of-range input',()=>{
    const page=TestBed.createComponent(PredictionPage).componentInstance;
    expect(page.validate()).toContain('age');
    page.values.set({age:150,sex:'1'});expect(page.validate()).toContain('age');
    page.values.set({age:55,sex:'invalid'});expect(page.validate()).toContain('sex');
  });
  it('submits a valid case to the actual prediction method',()=>{
    const page=TestBed.createComponent(PredictionPage).componentInstance;
    page.values.set({age:55,sex:'1'});page.run();
    expect(predict).toHaveBeenCalledWith('heart',{age:55,sex:'1'});
    expect(page.result()?.predicted_class).toBe(1);
  });
});
