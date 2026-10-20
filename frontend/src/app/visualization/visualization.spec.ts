import { TestBed } from '@angular/core/testing';
import { vi } from 'vitest';
import { contrast, extractPalette, FALLBACK_PALETTE, RGB } from './palette';
import { DEFAULT_APPEARANCE, MAIN_BACKGROUND, AppearanceService, sanitizeAppearance } from './appearance.service';
import { scatter, density, ridges, categoricalBars, axisBounds, normalized, NUMERIC_AXES } from './geometry';
import { themeChart } from './chart-theme';
import { modelGeometry } from './model-studio';
import { monthlyLandscape } from './data-explorer';
import { topology } from './infrastructure-studio';
import { Comparison } from '../core/api';

describe('background palette and accessibility',()=>{
 it('extracts distinct useful palettes from actual sampled pixels',()=>{const red=extractPalette([230,40,20,255,230,40,20,255]),blue=extractPalette([20,40,230,255]);expect(red.primary).not.toBe(blue.primary);expect(new Set(red.chart).size).toBe(5);});
 it('handles empty, transparent, black and white images deterministically',()=>{for(const p of [[],[0,0,0,255],[255,255,255,255],[255,0,0,0]])expect(extractPalette(p)).toEqual(FALLBACK_PALETTE);});
 it('maintains muted text contrast on readable glass over a bright image',()=>{for(let h=0;h<255;h+=17){const p=extractPalette([h,255-h,100,255]);const rgb=p.dark.slice(1).match(/../g)!.map(c=>parseInt(c,16)) as RGB;const composite=rgb.map(v=>v*.72+255*.28) as RGB;expect(contrast([193,208,226],composite)).toBeGreaterThan(4.5);}});
 it('bounds malformed stored controls and preserves defaults',()=>{expect(sanitizeAppearance({glass:-1,blur:999,quality:'bad' as any,brightness:NaN})).toEqual({...DEFAULT_APPEARANCE,blur:12});});
 it('migrates former default tint and dimming without discarding other preferences',()=>{localStorage.setItem('mediscope-appearance-v1',JSON.stringify({...DEFAULT_APPEARANCE,glass:.48,brightness:.75,glassBlur:10,glow:.6}));localStorage.removeItem('mediscope-transparent-v3');const service=TestBed.inject(AppearanceService);expect(service.settings()).toMatchObject({glass:0,brightness:1,glassBlur:0,glow:.6});});
 it('applies the new background blur to saved settings once',()=>{localStorage.setItem('mediscope-appearance-v1',JSON.stringify({...DEFAULT_APPEARANCE,blur:0,glow:.6}));localStorage.removeItem('mediscope-background-blur-v4');const service=TestBed.inject(AppearanceService);expect(service.settings()).toMatchObject({blur:2.4,glow:.6});});
 it('themes chart data item styles without changing numeric values or source objects',()=>{const original={series:[{type:'bar',data:[{value:.8473,itemStyle:{color:'#39d9d0'}}]}]};const themed=themeChart(original,extractPalette([255,30,30,255]));expect(themed.series[0].data[0].value).toBe(.8473);expect(themed.series[0].data[0].itemStyle.color).not.toBe('#39d9d0');expect(original.series[0].data[0].itemStyle.color).toBe('#39d9d0');});
 it('loads default and preset images locally, restores defaults, and keeps inputs out of storage',async()=>{
   const sources:string[]=[];vi.stubGlobal('Image',class {set src(v:string){sources.push(v);}decode(){return Promise.resolve();}});
   const spy=vi.spyOn(HTMLCanvasElement.prototype,'getContext').mockReturnValue({drawImage:vi.fn(),getImageData:()=>({data:[200,40,20,255]})} as any);
   localStorage.clear();TestBed.configureTestingModule({});const service=TestBed.inject(AppearanceService);TestBed.tick();await Promise.resolve();expect(sources).toContain(MAIN_BACKGROUND);expect(service.ready()).toBe(true);
   service.select('/backgrounds/spectral-field.svg');TestBed.tick();await Promise.resolve();expect(service.background()).toContain('spectral');expect(localStorage.getItem('mediscope-background-v1')).toContain('spectral');service.change('glassBlur',0);service.reset();TestBed.tick();expect(service.settings()).toEqual(DEFAULT_APPEARANCE);expect(service.background()).toBe(MAIN_BACKGROUND);expect(localStorage.getItem('mediscope-appearance-v1')).not.toContain('features');spy.mockRestore();vi.unstubAllGlobals();
 });
 it('rejects stale stored URLs and restores default after a missing bundled preset',async()=>{
   localStorage.setItem('mediscope-background-v1','blob:stale');vi.stubGlobal('Image',class {private url='';set src(v:string){this.url=v;}decode(){return this.url.includes('spectral')?Promise.reject(new Error('missing')):Promise.resolve();}});
   TestBed.configureTestingModule({});const service=TestBed.inject(AppearanceService);expect(service.background()).toBe(MAIN_BACKGROUND);TestBed.tick();await Promise.resolve();service.select('/backgrounds/spectral-field.svg');TestBed.tick();await Promise.resolve();await Promise.resolve();expect(service.background()).toBe(MAIN_BACKGROUND);vi.unstubAllGlobals();
 });
});
describe('scientifically faithful geometry',()=>{
 const rows=[{age:30,bmi:20,glucose:100,outcome:0},{age:60,bmi:null,glucose:200,outcome:1},{age:50,bmi:30,glucose:150,outcome:1},{age:70,bmi:40,glucose:180,outcome:0}];
 it('preserves observations and excludes missing BMI without converting null to zero',()=>{const data=scatter(rows,['age','bmi','glucose'],'outcome');expect(data.sampleSize).toBe(3);expect(data.excluded).toBe(1);expect(data.points[1]).toMatchObject({x:50,y:30,z:150});expect(normalized(data.points[0],axisBounds(data))).toEqual([-4,-4,-4]);});
 it('filters by recorded class without changing the source',()=>{const data=scatter(rows,['age','bmi','glucose'],'outcome','1');expect(data.sampleSize).toBe(1);expect(data.excluded).toBe(1);expect(rows[1].bmi).toBeNull();});
 it('does not offer categorical numeric codes as continuous axes',()=>{expect(NUMERIC_AXES['uci_early_diabetes']).toBeUndefined();expect(NUMERIC_AXES['uci_cleveland_heart']).not.toContain('cp');});
 it('categorical columns reconcile to the observed denominator',()=>{const data=categoricalBars([{symptom:'Yes',class:'Positive'},{symptom:'No',class:'Negative'},{symptom:'Yes',class:'Positive'}],'symptom','class');expect(data.points.reduce((s,p)=>s+p.y,0)).toBe(3);expect(data.axes[0].categories).toEqual(['No','Yes']);});
 it('histogram ridges preserve every complete observation including the maximum',()=>{const data=ridges(scatter(rows,['age','bmi','glucose'],'outcome'));expect(data.points.reduce((s,p)=>s+p.y,0)).toBe(3);});
 it('labels estimated density and documents bandwidth; all grid values are finite',()=>{const data=density(scatter(rows,['age','bmi','glucose'],'outcome'));expect(data.points).toHaveLength(400);expect(data.note).toContain('Scott bandwidth');expect(data.points.every(p=>Number.isFinite(p.y)&&p.y>=0)).toBe(true);expect(data.sampleSize).toBe(3);});
 it('keeps Synthea monthly counts distinct from patients',()=>{const data=monthlyLandscape([{month:'2020-01',encounters:12},{month:'2020-03',encounters:5}]);expect(data.sampleSize).toBe(17);expect(data.points).toHaveLength(2);expect(data.points.map(p=>p.x)).toEqual([0,2]);expect(data.note).toContain('not unique patients');});
 it('copies model metrics exactly and omits absent scores instead of fabricating zero',()=>{const comparison:Comparison={task:'heart',selection_score:'f1',cv_strategy:'five folds',selected_model:'knn',warning:'Research only',trials:[{algorithm:'knn',selected:true,best_params:{},cv_mean:.76,cv_std:.1,decision_threshold:.5,test_metrics:{f1:.8123,precision:null},cv_fold_scores:[.8,.9,.7,.6,.8]}]};const data=modelGeometry(comparison,'metrics');expect(data.points).toHaveLength(1);expect(data.points[0].y).toBe(.8123);expect(modelGeometry(comparison,'confusion',[[27,6],[2,26]]).sampleSize).toBe(61);});
 it('never implies child node availability or retains fresh status after refresh failure',()=>{const data=topology({live:{hdfs:{status:'READY',message:'ok'}},saved_mapreduce_evidence:{}},true);expect(data.points[1].group).toContain('STALE');expect(data.points[2].group).toContain('not exposed');expect(data.note).toContain('conceptual');});
});
