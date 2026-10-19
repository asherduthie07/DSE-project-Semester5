import { vi } from 'vitest';
import { TestBed } from '@angular/core/testing';
import { of } from 'rxjs';
import { DatasetsPage } from './datasets';
import { ApiService } from '../core/api';

describe('dataset quality evidence',()=>{
  it('uses the selected Phase I table for missingness, duplicates and outliers',()=>{
    const id='uci_cleveland_heart';
    const get=vi.fn((path:string)=>of(path.endsWith('/schema')?{dataset_id:id,name:'Heart',source_sha256:'abc',tables:{heart:{rows:303,fields:[{name:'age',dtype:'int64',nullable:false,exposed_in_records:true}],record_fields:['age']}}}:path.endsWith('/summary')?{dataset_id:id,name:'Heart',source_url:'https://example.org',provenance:'source',source_sha256:'abc',tables:{heart:{rows:303,missing:{age:0,ca:4},columns:['age','ca']}},rows:{heart:303}}:path.endsWith('/quality')?{tables:{'processed.cleveland.data':{initial:{rows:303,missing:{age:0,ca:4}},final:{rows:303,missing:{age:0,ca:4}},duplicates:{exact_before:2,retained:2,removed:0},outliers_before:{chol:{count:5}},outliers_after:{chol:{count:5}}}}}:{dataset_id:id,table:'heart',source_rows:303,total:303,offset:0,limit:25,items:[{age:55}]}));
    const api={datasets:()=>of({datasets:[{id,name:'Heart',records:'source',source_url:'https://example.org',source_sha256:'abc',tables:{heart:303}}]}),get};
    TestBed.configureTestingModule({imports:[DatasetsPage],providers:[{provide:ApiService,useValue:api}]});
    const page=TestBed.createComponent(DatasetsPage).componentInstance;
    expect(page.missingTotal()).toBe(4);
    expect(page.qualityTable()?.duplicates.retained).toBe(2);
    expect(page.outliers()[0][0]).toBe('chol');
    expect(page.records()?.items.length).toBe(1);
    page.filterField.set('sex');page.filterValue.set('1');page.applyFilter();
    expect(get).toHaveBeenLastCalledWith('/datasets/uci_cleveland_heart/records',{table:'heart',offset:0,limit:25,filter_field:'sex',filter_value:'1'});
  });
});
