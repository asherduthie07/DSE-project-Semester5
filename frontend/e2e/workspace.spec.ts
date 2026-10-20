import { test, expect } from '@playwright/test';
import { mkdirSync } from 'node:fs';
import path from 'node:path';
const shots=path.resolve('../docs/screenshots/phase6c');
const routes=['command-center','datasets','analytics','prediction','models','big-data','research'];
test.beforeAll(()=>mkdirSync(shots,{recursive:true}));
test('seven real API routes, four widths, background and console',async({page})=>{
 test.setTimeout(240000);const errors:string[]=[];page.on('pageerror',error=>errors.push(error.message));
 for(const width of [1440,1280,768,390]){await page.setViewportSize({width,height:1000});for(const route of routes){await page.goto('/'+route);await expect(page.locator('h1')).toBeVisible();await expect(page.locator('.loading')).toHaveCount(0);await expect(page.locator('.workspace-background')).toHaveCSS('background-size','cover');await expect.poll(()=>page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1)).toBe(true);if(['datasets','analytics','models','big-data','command-center'].includes(route))await expect(page.locator('.holo-viewport canvas')).toHaveCount(1);await page.screenshot({path:path.join(shots,`${route}-${width}.png`),fullPage:true});}}
 expect(errors).toEqual([]);
});
test('background studio extracts colors, resets and supports keyboard close',async({page})=>{
 await page.goto('/command-center');await expect(page.locator('.holo-viewport canvas')).toHaveCount(1);const before=await page.evaluate(()=>getComputedStyle(document.documentElement).getPropertyValue('--holo-primary'));
 await page.getByRole('button',{name:'Background Studio'}).click();await expect(page.getByRole('dialog')).toBeVisible();await page.getByRole('button',{name:'Deep spectral field'}).click();await expect.poll(()=>page.evaluate(()=>getComputedStyle(document.documentElement).getPropertyValue('--holo-primary'))).not.toBe(before);
  const brightness=page.getByRole('slider',{name:'Background brightness'});await brightness.focus();await brightness.press('Home');for(let i=0;i<6;i++)await brightness.press('ArrowRight');await expect(page.locator('.workspace-background')).toHaveCSS('filter','brightness(0.5) blur(2.4px)');await page.screenshot({path:path.join(shots,'background-studio.png')});
 await page.getByRole('button',{name:'Restore exact defaults'}).click();await expect.poll(()=>page.evaluate(()=>getComputedStyle(document.documentElement).getPropertyValue('--holo-primary'))).toBe(before);await page.keyboard.press('Escape');await expect(page.getByRole('dialog')).toHaveCount(0);
});
test('real 3D geometry, camera interactions, 2D switch and cohort selection',async({page})=>{
 await page.goto('/analytics');const canvas=page.locator('.holo-viewport canvas');await expect(canvas).toHaveCount(1);await expect(page.getByText('303 records fetched;', {exact:false})).toBeVisible();
 const first=await canvas.screenshot();await page.getByRole('button',{name:'Rotate',exact:true}).click();expect((await canvas.screenshot()).equals(first)).toBe(false);await page.getByRole('button',{name:'Zoom in 3D'}).click();await page.getByRole('button',{name:'Reset camera / fit'}).click();
 await page.getByRole('button',{name:'Precision 2D',exact:true}).click();await expect(canvas).toHaveCount(0);await page.getByRole('button',{name:'Holographic 3D',exact:true}).click();await expect(canvas).toHaveCount(1);
 await page.getByLabel('Select disease dataset').selectOption('stroke');await expect(page.getByText('5110 records fetched;', {exact:false})).toBeVisible();await expect(page.getByText('201 excluded for missing/non-numeric axes.',{exact:false})).toBeVisible();
  await page.getByRole('combobox',{name:'View',exact:true}).selectOption('density');await expect(page.getByText('Scott bandwidth',{exact:false})).toBeVisible();await page.screenshot({path:path.join(shots,'stroke-density.png'),fullPage:true});
  await page.getByLabel('Select disease dataset').selectOption('diabetes');await expect(page.getByText('520 records fetched;', {exact:false})).toBeVisible();await expect(page.getByRole('combobox',{name:'Symptom',exact:true})).toBeVisible();
});
test('prediction uses the saved pipeline and returns the real score',async({page})=>{
 await page.goto('/prediction');await page.getByRole('button',{name:'Load fictional sample'}).click();await expect(page.getByRole('spinbutton',{name:'Age',exact:true})).not.toHaveValue('');const response=page.waitForResponse(r=>r.url().endsWith('/predictions/heart')&&r.request().method()==='POST');await page.getByRole('button',{name:'Run prediction'}).click();const actual=await (await response).json();await expect(page.getByText('Saved model class '+actual.predicted_class)).toBeVisible();expect(actual.estimated_model_score).toBeCloseTo(.4453247126343259,10);await expect(page.locator('ms-score-display canvas')).toHaveCount(1);await page.screenshot({path:path.join(shots,'prediction-result.png'),fullPage:true});
});
test('WebGL failure preserves precision geometry and data table',async({page})=>{
 await page.addInitScript(()=>{const original=HTMLCanvasElement.prototype.getContext;HTMLCanvasElement.prototype.getContext=function(type:any,...args:any[]):any {if(String(type).includes('webgl'))return null;return (original as any).call(this,type,...args);};});
 await page.goto('/analytics');await expect(page.getByText('WebGL unavailable on this device.',{exact:false})).toBeVisible();await page.getByText('Accessible data table',{exact:false}).click();await expect(page.locator('.visual-table tbody tr')).toHaveCount(50);await page.screenshot({path:path.join(shots,'webgl-fallback.png'),fullPage:true});
});
