import { test, expect } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';
import { writeFileSync } from 'node:fs';
import { readFileSync } from 'node:fs';
import path from 'node:path';
test('all saved model tasks retain registry metrics and selected matrices',async({page,request})=>{
 await page.goto('/models');
 for(const task of ['heart','diabetes','stroke']){await page.getByLabel('Select model task').selectOption(task);const comparison=await (await request.get(`/api/v1/models/${task}/comparison`)).json();const matrices=await (await request.get(`/api/v1/models/${task}/confusion-matrices`)).json();await expect(page.getByLabel('Confusion matrix model')).toHaveValue(comparison.selected_model);await expect(page.locator('.matrix-cell strong')).toHaveText(matrices.matrices[comparison.selected_model].matrix.flat().map(String));for(const algorithm of ['logistic regression','decision tree','random forest','knn'])await expect(page.locator('td strong').filter({hasText:algorithm}).first()).toBeVisible();}
});
test('Synthea temporal data and current infrastructure are real API outputs',async({page,request})=>{
 await page.goto('/datasets');await page.getByLabel('Select dataset').selectOption('synthea_csv');await page.getByRole('combobox',{name:'Saved analysis',exact:true}).selectOption('temporal');await expect(page.getByText('latest ten recorded years',{exact:false})).toBeVisible();await page.screenshot({path:path.resolve('../docs/screenshots/phase6c/synthea-ridgelines.png'),fullPage:true});
 const status=await (await request.get('/api/v1/bigdata/status')).json();await page.goto('/big-data');for(const entry of Object.values(status.live) as {status:string;message:string}[])await expect(page.locator('.service-card').filter({hasText:entry.message})).toContainText(entry.status);await expect(page.getByText('53,346',{exact:false}).first()).toBeVisible();
});
test('keyboard dialog, mobile navigation and WCAG automated checks',async({page})=>{
 await page.setViewportSize({width:390,height:844});await page.goto('/prediction');await expect(page.locator('.form-grid')).toBeVisible();await page.getByRole('button',{name:'Open menu'}).click();await page.getByRole('link',{name:'Research & Reports',exact:true}).click();await expect(page.locator('h1')).toHaveText('Research & Reports');await page.getByRole('button',{name:'Background Studio'}).click();await expect(page.getByRole('button',{name:'Close Background Studio'})).toBeFocused();
 const result=await new AxeBuilder({page}).withTags(['wcag2a','wcag2aa','wcag21aa']).analyze();expect(result.violations.map(v=>({id:v.id,nodes:v.nodes.map(n=>n.target)}))).toEqual([]);await page.keyboard.press('Escape');await expect(page.getByRole('button',{name:'Background Studio'})).toBeFocused();
});
test('scene disposal, motion pause, local upload and measured browser timing',async({page})=>{
 await page.addInitScript(()=>{(window as any).__released=0;const original=HTMLCanvasElement.prototype.getContext;HTMLCanvasElement.prototype.getContext=function(type:any,...args:any[]):any {const context=(original as any).call(this,type,...args);if(type==='webgl2'&&context&&!context.__observed){context.__observed=true;const get=context.getExtension.bind(context);context.getExtension=(name:string)=>{const extension=get(name);if(name==='WEBGL_lose_context'&&extension){const lose=extension.loseContext.bind(extension);return {loseContext:()=>{(window as any).__released++;lose();},restoreContext:extension.restoreContext.bind(extension)};}return extension;};}return context;};});
 await page.goto('/command-center');const canvas=page.locator('.holo-viewport canvas');await expect(canvas).toHaveCount(1);await page.getByRole('button',{name:'Pause animation'}).click();const before=await canvas.screenshot();await page.waitForTimeout(200);expect((await canvas.screenshot()).equals(before)).toBe(true);
 const timings=await page.evaluate(()=>new Promise<{meanFrameMs:number;maxFrameMs:number;heapBytes:number|null}>(resolve=>{const frames:number[]=[];let previous=performance.now();const tick=(now:number)=>{frames.push(now-previous);previous=now;if(frames.length<60)requestAnimationFrame(tick);else resolve({meanFrameMs:frames.reduce((a,b)=>a+b,0)/frames.length,maxFrameMs:Math.max(...frames),heapBytes:(performance as any).memory?.usedJSHeapSize??null});};requestAnimationFrame(tick);}));writeFileSync(path.resolve('../docs/screenshots/phase6c/browser-timing.json'),JSON.stringify({renderer:'Headless Chromium SwiftShader software rendering; not native GPU benchmark',...timings},null,2));
 await page.getByRole('button',{name:'Background Studio'}).click();await page.locator('input[type=file]').setInputFiles(path.resolve('background-image/reference-image.jpg'));await expect(page.locator('.background-preview')).toHaveAttribute('src',/^blob:/);await expect(page.locator('.workspace-background')).toHaveCSS('background-image',/blob:/);await expect(page.getByRole('status').first()).toContainText('Palette extracted locally');await page.getByRole('button',{name:'Restore exact defaults'}).click();await expect(page.locator('.workspace-background')).toHaveCSS('background-image',/\/3\.jpg/);await page.keyboard.press('Escape');
 await page.getByRole('link',{name:'Disease Analytics',exact:true}).click();await expect.poll(()=>page.evaluate(()=>(window as any).__released)).toBeGreaterThan(0);await expect(canvas).toHaveCount(1);const released=await page.evaluate(()=>(window as any).__released);await page.getByRole('button',{name:'Precision 2D',exact:true}).click();await expect.poll(()=>page.evaluate(()=>(window as any).__released)).toBeGreaterThan(released);await expect(canvas).toHaveCount(0);
});
test('default background survives stale preferences, serves pixels, and leaves panels clear',async({page,request})=>{
 const image=await request.get('/backgrounds/3.jpg');expect(image.status()).toBe(200);expect(image.headers()['content-type']).toContain('image/jpeg');expect((await image.body()).length).toBe(79924);
 await page.addInitScript(()=>localStorage.setItem('mediscope-background-v1','blob:missing-from-another-session'));
 for(const route of ['command-center','datasets','analytics','prediction','models','big-data','research']){
  await page.goto('/'+route);await expect(page.locator('.workspace-background')).toHaveCSS('background-image',/\/3\.jpg/);await expect(page.locator('.panel').first()).toBeVisible();
  const state=await page.evaluate(()=>{const background=document.querySelector('.workspace-background')!,panel=document.querySelector('.panel')!;return {size:getComputedStyle(background).backgroundSize,alpha:getComputedStyle(panel).backgroundColor,image:localStorage.getItem('mediscope-background-v1')};});
  expect(state.size).toBe('cover');expect(state.image).toBe('/backgrounds/3.jpg');expect(state.alpha).toMatch(/^(rgba\(.*[, ]0\)|color\(srgb .*\/ 0\)|transparent)$/);
 }
 await page.evaluate(()=>window.scrollTo(0,0));await page.screenshot({path:path.resolve('../docs/screenshots/phase6c/background-fixed.png'),fullPage:true});
 await page.evaluate(()=>window.scrollTo(0,document.body.scrollHeight));expect(await page.locator('.workspace-background').evaluate(el=>{const b=el.getBoundingClientRect();return b.top<=0&&b.bottom>=innerHeight;})).toBe(true);
 await page.screenshot({path:path.resolve('../docs/screenshots/phase6c/background-scroll.png')});
});
test('global background shows through navigation and every dashboard surface',async({page})=>{
 await page.addInitScript(()=>localStorage.clear());
 for(const route of ['command-center','datasets','analytics','prediction','models','big-data','research']){
  await page.goto('/'+route);await expect(page.locator('.panel').first()).toBeVisible();
  const layers=await page.evaluate(()=>{const alpha=(element:Element)=>{const color=getComputedStyle(element).backgroundColor;const match=color.match(/\/\s*([\d.]+)\)|,\s*([\d.]+)\)/);return Number(match?.[1]??match?.[2]??1);};return {background:getComputedStyle(document.querySelector('.workspace-background')!).backgroundImage,sidebar:alpha(document.querySelector('.sidebar')!),header:alpha(document.querySelector('.topbar')!),panels:[...document.querySelectorAll('.panel')].map(alpha)};});
  expect(layers.background).toContain('/3.jpg');expect(layers.sidebar).toBe(0);expect(layers.header).toBe(0);expect(layers.panels.length).toBeGreaterThan(0);expect(Math.max(...layers.panels)).toBe(0);
  if(route==='command-center'||route==='research')await page.screenshot({path:path.resolve('../docs/screenshots/phase6c',`transparent-${route}.png`)});
 }
});
test('human-readable choices send unchanged fixture values for all three saved models',async({page,request})=>{
 await page.goto('/prediction');
 for(const task of ['heart','diabetes','stroke']){
  await page.getByLabel('Prediction task').selectOption(task);const fixture=JSON.parse(readFileSync(path.resolve('../examples',`${task}_case.json`),'utf8'));
  await page.getByRole('button',{name:'Load fictional sample'}).click();
  const gender=task==='heart'?page.getByRole('combobox',{name:'Recorded Sex'}):page.getByRole('combobox',{name:'Gender',exact:true});
  await expect(gender).toHaveValue(task==='heart'?String(fixture.sex):task==='diabetes'?fixture.Gender:fixture.gender);
  expect(await gender.locator('option').allTextContents()).toContain('Female');expect(await gender.locator('option').allTextContents()).toContain('Male');
  expect((await gender.locator('option').allTextContents()).includes('Other')).toBe(task==='stroke');
  if(task==='stroke')await expect(page.getByRole('combobox',{name:'Hypertension history'})).toHaveValue(String(fixture.hypertension));
  const direct=await (await request.post(`/api/v1/predictions/${task}`,{data:{features:fixture}})).json();
  const posted=page.waitForRequest(r=>r.url().endsWith(`/predictions/${task}`)&&r.method()==='POST');const response=page.waitForResponse(r=>r.url().endsWith(`/predictions/${task}`)&&r.request().method()==='POST');
  await page.getByRole('button',{name:'Run prediction'}).click();const body=(await posted).postDataJSON();expect(body.features).toEqual(fixture);const fromForm=await (await response).json();expect(fromForm.predicted_class).toBe(direct.predicted_class);expect(fromForm.estimated_model_score).toBe(direct.estimated_model_score);expect(fromForm.decision_threshold).toBe(direct.decision_threshold);
  await expect(page.getByText('Saved model class '+direct.predicted_class)).toBeVisible();
  const score=await page.locator('.result-details').first().textContent();expect(score).toContain(Number(direct.estimated_model_score).toFixed(3));
  await page.evaluate(()=>scrollTo(0,0));await page.screenshot({path:path.resolve('../docs/screenshots/phase6c',`readable-${task}-prediction.png`),fullPage:true});
 }
});
test('dataset preview and server filters show labels but retain exact source codes',async({page})=>{
 await page.goto('/datasets');await expect(page.getByRole('button',{name:/Recorded Sex/}).first()).toBeVisible();
 await page.getByLabel('Server filter field').selectOption('sex');await expect(page.getByLabel('Exact server filter value')).toContainText('Male');await page.getByLabel('Exact server filter value').selectOption('1');
 const filtered=page.waitForResponse(r=>r.url().includes('filter_field=sex')&&r.url().includes('filter_value=1'));
 await page.getByRole('button',{name:'Apply',exact:true}).click();await filtered;await expect(page.locator('.table-scroll tbody tr').first()).toContainText('Male');
 await page.getByLabel('Select dataset').selectOption('uci_early_diabetes');await expect(page.getByRole('button',{name:/Gender/}).first()).toBeVisible();await expect(page.locator('.table-scroll tbody tr').first()).toContainText(/Female|Male/);
 await page.getByLabel('Select dataset').selectOption('kaggle_stroke');await expect(page.getByRole('button',{name:/Hypertension history/}).first()).toBeVisible();await expect(page.locator('.table-scroll tbody tr').first()).toContainText(/Yes|No/);
 await page.getByLabel('Select dataset').selectOption('synthea_csv');await expect(page.getByRole('button',{name:/Gender/}).first()).toBeVisible();await expect(page.locator('.table-scroll tbody tr').first()).toContainText(/Female|Male/);
});
