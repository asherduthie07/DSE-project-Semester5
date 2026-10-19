import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { of } from 'rxjs';
import { App } from './app';
import { ApiService } from './core/api';

describe('research shell', () => {
  beforeEach(async () => {
    await TestBed.configureTestingModule({imports:[App],providers:[provideRouter([]),{provide:ApiService,useValue:{get:()=>of({status:'READY'})}}]}).compileComponents();
  });
  it('shows all seven research routes and a real connection state', () => {
    const fixture=TestBed.createComponent(App);fixture.detectChanges();
    const text=(fixture.nativeElement as HTMLElement).textContent??'';
    for(const title of ['Command Center','Dataset Explorer','Disease Analytics','Prediction Lab','ML Laboratory','Big Data Monitor','Research & Reports']) expect(text).toContain(title);
    expect(text).toContain('System online');
  });
  it('collapses the sidebar with an accessible button', () => {
    const fixture=TestBed.createComponent(App);fixture.detectChanges();
    const button=(fixture.nativeElement as HTMLElement).querySelector('[aria-label="Collapse sidebar"]') as HTMLButtonElement;
    button.click();fixture.detectChanges();
    expect((fixture.nativeElement as HTMLElement).querySelector('.sidebar-collapsed')).not.toBeNull();
  });
});
