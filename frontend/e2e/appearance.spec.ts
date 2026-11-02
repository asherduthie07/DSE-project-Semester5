import { test, expect } from '@playwright/test';
import path from 'node:path';

test('frosted defaults migrate once and later choices persist', async ({page}) => {
  await page.addInitScript(() => {
    if (!localStorage.getItem('appearance-test-seeded')) {
      localStorage.setItem('mediscope-appearance-v1', JSON.stringify({brightness:1,blur:2.4,glass:0,glassBlur:0,glow:.6}));
      localStorage.setItem('appearance-test-seeded','1');
    }
  });
  await page.goto('/command-center');
  await expect(page.locator('.workspace-background')).toHaveCSS('filter','brightness(0.65) blur(12px)');
  await page.getByRole('button',{name:'Background Studio'}).click();
  const glass = page.getByRole('slider',{name:'Glass opacity',exact:true});
  await expect(glass).toHaveValue('0.5');
  await expect(page.getByRole('slider',{name:'Glow intensity'})).toHaveValue('0.6');
  await glass.fill('0.35');
  await page.reload();
  await page.getByRole('button',{name:'Background Studio'}).click();
  await expect(glass).toHaveValue('0.35');
  await page.getByRole('button',{name:'Restore exact defaults'}).click();
  await expect(glass).toHaveValue('0.5');
});

test('two slow layers cover the viewport and respect reduced motion', async ({page}) => {
  for (const width of [1440,390]) {
    await page.setViewportSize({width,height:844});
    await page.goto('/prediction');
    await expect(page.locator('.panel').first()).toBeVisible();
    // Ensure a long page even when the live API is unavailable.
    await page.evaluate(() => document.querySelector('main')!.style.minHeight='3000px');
    const offsets:number[][]=[];
    for (const progress of [0,.5,1]) {
      await page.evaluate(p=>scrollTo(0,(document.documentElement.scrollHeight-innerHeight)*p),progress);
      await expect.poll(()=>page.evaluate(()=>{
        const range=document.documentElement.scrollHeight-innerHeight;
        const expected=range ? -(scrollY/range)*Math.min(range*.15,innerHeight*.12) : 0;
        const actual=new DOMMatrix(getComputedStyle(document.querySelector('.workspace-background')!).transform).m42;
        return Math.abs(actual-expected);
      })).toBeLessThan(.5);
      const state=await page.evaluate(()=>{
        const a=document.querySelector('.workspace-background')!,b=document.querySelector('.workspace-glows')!;
        const rect=a.getBoundingClientRect();
        return {offsets:[new DOMMatrix(getComputedStyle(a).transform).m42,new DOMMatrix(getComputedStyle(b).transform).m42],covers:rect.top<=0&&rect.bottom>=innerHeight,overflow:document.documentElement.scrollWidth>innerWidth};
      });
      expect(state.covers).toBe(true);expect(state.overflow).toBe(false);offsets.push(state.offsets);
    }
    expect(offsets[1][0]).toBeLessThan(offsets[0][0]);expect(offsets[2][0]).toBeLessThan(offsets[1][0]);
    expect(offsets[2][1]).toBeLessThan(offsets[2][0]);
    await page.evaluate(()=>scrollTo(0,0));
    await expect.poll(()=>page.evaluate(()=>scrollY)).toBe(0);
    await page.screenshot({path:path.resolve(`../docs/screenshots/frosted-${width}.png`)});
    await page.emulateMedia({reducedMotion:'reduce'});
    await expect(page.locator('.workspace-background')).toHaveCSS('transform','none');
    await expect(page.locator('.workspace-glows')).toHaveCSS('transform','none');
    await page.emulateMedia({reducedMotion:'no-preference'});
  }
});
