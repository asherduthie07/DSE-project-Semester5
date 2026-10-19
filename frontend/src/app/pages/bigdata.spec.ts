import { vi } from 'vitest';
import { TestBed } from '@angular/core/testing';
import { of } from 'rxjs';
import { BigDataPage } from './bigdata';
import { ApiService } from '../core/api';

describe('infrastructure refresh',()=>{
  it('polls at 15 seconds and stops after component destruction',()=>{
    vi.useFakeTimers();
    const get=vi.fn((path:string)=>of(path.endsWith('collections')?{status:'READY',database:'test',counts:{},source_counts_match:true}:{live:{mongodb:{status:'READY',message:'ok'}},saved_mapreduce_evidence:{status:'NOT_VERIFIED'}}));
    TestBed.configureTestingModule({imports:[BigDataPage],providers:[{provide:ApiService,useValue:{get}}]});
    const fixture=TestBed.createComponent(BigDataPage);
    vi.advanceTimersByTime(0);expect(get).toHaveBeenCalledTimes(2);
    vi.advanceTimersByTime(15000);expect(get).toHaveBeenCalledTimes(4);
    fixture.destroy();vi.advanceTimersByTime(15000);expect(get).toHaveBeenCalledTimes(4);
    vi.useRealTimers();
  });
});
