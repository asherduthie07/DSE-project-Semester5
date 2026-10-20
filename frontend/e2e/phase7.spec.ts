import { test, expect } from '@playwright/test';
import { mkdirSync } from 'node:fs';
import path from 'node:path';

test('Phase VII research charts load verified outputs and remain usable on mobile', async ({page, request}) => {
  const api = await request.get('/api/v1/research-lab/stroke');
  expect(api.ok()).toBeTruthy();
  const saved = await api.json();
  const errors:string[]=[];page.on('pageerror',error=>errors.push(error.message));
  for (const width of [1440,390]) {
    await page.setViewportSize({width,height:900});
    await page.goto('/research-lab');
    await expect(page.getByRole('heading',{name:'Research Laboratory'})).toBeVisible();
    await page.getByLabel('Select research task').selectOption('stroke');
    await expect(page.getByText(saved.split_sha256.slice(0,12))).toBeVisible();
    await expect(page.locator('ms-chart canvas')).toHaveCount(4);
    await expect(page.getByText('False positives',{exact:false}).first()).toBeVisible();
    await page.getByLabel('Calibration strategy').selectOption('missing_indicator');
    expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1)).toBe(true);
    const folder=path.resolve('../docs/screenshots/phase7');mkdirSync(folder,{recursive:true});
    await page.screenshot({path:path.join(folder,`research-lab-${width}.png`),fullPage:true});
  }
  expect(errors).toEqual([]);
});
