import { TestBed } from '@angular/core/testing';
import { of } from 'rxjs';
import { ModelsPage } from './models';
import { ApiService } from '../core/api';

describe('model evaluation mapping',()=>{
  it('uses saved CV folds separately from held-out metrics',()=>{
    const trial={algorithm:'logistic_regression',selected:true,best_params:{},cv_mean:.8,cv_std:.1,cv_fold_scores:[.7,.8,.9,.8,.8],test_metrics:{f1:.75,accuracy:.82},decision_threshold:.5};
    const api={comparison:()=>of({task:'heart',cv_strategy:'5 folds',selection_score:'f1',selected_model:'logistic_regression',trials:[trial],warning:'Research'}),get:(path:string)=>of(path.endsWith('confusion-matrices')?{matrices:{logistic_regression:{matrix:[[27,6],[2,26]],test_n:61,positive_n:28,negative_n:33}}}:path.endsWith('curves')?{curves:{}}:path.endsWith('explanations')?{explanation:{method:'saved',scoring:'f1',permutation:[],shap:'not performed',caveat:'noncausal',validation_rows:49}}:{task:'heart',selected_model:'logistic_regression',selection_score:'f1',selection_reason:'development',cv_strategy:'5 folds',available_for_prediction:true,warning:'Research'})};
    TestBed.configureTestingModule({imports:[ModelsPage],providers:[{provide:ApiService,useValue:api}]});
    const page=TestBed.createComponent(ModelsPage).componentInstance;
    expect((page.cvOption() as any).series[0].data).toEqual([.7,.8,.9,.8,.8]);
    expect((page.metricOption() as any).series[0].data[0].value).toBe(.75);
    expect(page.matrix()).toEqual([[27,6],[2,26]]);
  });
});
