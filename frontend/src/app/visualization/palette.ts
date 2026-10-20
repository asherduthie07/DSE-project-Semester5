export type RGB = [number, number, number];
export interface Palette { primary: string; secondary: string; accent: string; highlight: string; dark: string; chart: string[] }
export function luminance(rgb: RGB): number {
  const c = rgb.map(v => { const x = v / 255; return x <= .04045 ? x / 12.92 : ((x + .055) / 1.055) ** 2.4; });
  return c[0] * .2126 + c[1] * .7152 + c[2] * .0722;
}
export function contrast(a: RGB, b: RGB): number { const x = luminance(a), y = luminance(b); return (Math.max(x,y)+.05)/(Math.min(x,y)+.05); }
export function hex(rgb: RGB): string { return '#' + rgb.map(v => Math.round(v).toString(16).padStart(2, '0')).join(''); }
export function hsl(h: number, s: number, l: number): RGB {
  const a = s * Math.min(l, 1-l);
  const f = (n: number) => { const k = (n + h / 30) % 12; return Math.round(255 * (l - a * Math.max(-1, Math.min(k-3,9-k,1)))); };
  return [f(0),f(8),f(4)];
}
function hue([r,g,b]: RGB): number {
  const max=Math.max(r,g,b), min=Math.min(r,g,b), d=max-min;
  if (!d) return 205;
  return ((max===r?(g-b)/d:max===g?(b-r)/d+2:(r-g)/d+4)*60+360)%360;
}
/** 4-bit RGB histogram, weighted toward chromatic pixels; deterministic, no network. */
export function extractPalette(pixels: ArrayLike<number>): Palette {
  const buckets = new Map<string,{rgb:RGB;n:number}>();
  for(let i=0;i+3<pixels.length;i+=4) {
    if(pixels[i+3]<128) continue;
    const rgb:RGB=[pixels[i],pixels[i+1],pixels[i+2]];
    const light=luminance(rgb); if(light<.008 || light>.92) continue;
    const key=rgb.map(v=>v>>4).join(','); const old=buckets.get(key);
    if(old) old.n++; else buckets.set(key,{rgb,n:1});
  }
  const ranked=[...buckets.values()].sort((a,b)=>b.n*(1+(Math.max(...b.rgb)-Math.min(...b.rgb))/70)-a.n*(1+(Math.max(...a.rgb)-Math.min(...a.rgb))/70));
  const base=ranked[0]?.rgb??[30,130,230] as RGB;
  const h=hue(base); const secondary=ranked.find(c=>{const d=Math.abs(hue(c.rgb)-h);return Math.min(d,360-d)>35;});
  const h2=secondary?hue(secondary.rgb):(h+55)%360;
  const chart=[h,h2,(h+135)%360,(h+215)%360,(h+285)%360].map(x=>hex(hsl(x,.75,.72)));
  return {primary:hex(hsl(h,.85,.72)),secondary:hex(hsl(h2,.75,.74)),accent:chart[2],highlight:hex(hsl(h,.55,.92)),dark:hex(hsl(h,.6,.045)),chart};
}
export const FALLBACK_PALETTE=extractPalette([]);
