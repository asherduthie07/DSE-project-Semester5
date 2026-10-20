import { routes } from './app.routes';

describe('lazy research navigation',()=>{
  it('registers the existing sections and research laboratory with lazy components',async()=>{
    const expected=['command-center','datasets','analytics','prediction','models','big-data','research','research-lab'];
    const pages=routes.filter(r=>expected.includes(r.path??''));
    expect(pages.map(r=>r.path)).toEqual(expected);
    expect(pages.every(r=>typeof r.loadComponent==='function')).toBe(true);
    const components=await Promise.all(pages.map(r=>r.loadComponent!()));
    expect(components.every(Boolean)).toBe(true);
  });
});
