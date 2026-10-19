import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { ApiService } from './api';

describe('typed API layer',()=>{
  let api:ApiService;let http:HttpTestingController;
  beforeEach(()=>{TestBed.configureTestingModule({providers:[provideHttpClient(),provideHttpClientTesting()]});api=TestBed.inject(ApiService);http=TestBed.inject(HttpTestingController)});
  afterEach(()=>http.verify());
  it('uses versioned routes and caches stable artifacts',()=>{
    let first=0,second=0;
    api.datasets().subscribe(()=>first++);api.datasets().subscribe(()=>second++);
    const req=http.expectOne('/api/v1/datasets');req.flush({datasets:[]});
    expect(first).toBe(1);expect(second).toBe(1);
  });
  it('retries a stable artifact after a transient API error',()=>{
    api.datasets().subscribe({error:()=>{}});
    http.expectOne('/api/v1/datasets').flush({message:'down'},{status:503,statusText:'Unavailable'});
    api.datasets().subscribe();
    http.expectOne('/api/v1/datasets').flush({datasets:[]});
  });
  it('posts features only to the selected research prediction route',()=>{
    const features={age:55};api.predict('heart',features).subscribe();
    const req=http.expectOne('/api/v1/predictions/heart');expect(req.request.method).toBe('POST');expect(req.request.body).toEqual({features});req.flush({task:'heart'});
  });
  it('keeps record requests bounded with server pagination',()=>{
    api.get('/datasets/kaggle_stroke/records',{table:'stroke',offset:25,limit:25}).subscribe();
    const req=http.expectOne(r=>r.url==='/api/v1/datasets/kaggle_stroke/records');expect(req.request.params.get('limit')).toBe('25');expect(req.request.params.get('offset')).toBe('25');req.flush({items:[]});
  });
});
