import { Injectable, effect, signal } from '@angular/core';
import { FALLBACK_PALETTE, extractPalette } from './palette';
// The production and development builders copy public/ to the web root.
export const MAIN_BACKGROUND='/backgrounds/3.jpg';
const PREVIOUS_BACKGROUND='/backgrounds/main-background-image.jpg';
export const PRESETS=[{name:'Main · digital grid',url:MAIN_BACKGROUND},{name:'Cyan horizon',url:PREVIOUS_BACKGROUND},{name:'Deep spectral field',url:'/backgrounds/spectral-field.svg'}];
export interface Appearance { auto:boolean;brightness:number;blur:number;position:number;glass:number;glassBlur:number;glow:number;particles:number;quality:'auto'|'low'|'high' }
export const DEFAULT_APPEARANCE:Appearance={auto:true,brightness:1,blur:2.4,position:50,glass:0,glassBlur:0,glow:.35,particles:.5,quality:'auto'};
export function sanitizeAppearance(raw:Partial<Appearance>):Appearance {
  const value={...DEFAULT_APPEARANCE};
  for(const [key,min,max] of [['brightness',.2,1],['blur',0,12],['position',0,100],['glass',0,.8],['glassBlur',0,20],['glow',0,1],['particles',0,1]] as const) {
    if(typeof raw[key]==='number' && Number.isFinite(raw[key])) value[key]=Math.max(min,Math.min(max,raw[key]!));
  }
  if(typeof raw.auto==='boolean') value.auto=raw.auto;
  if(['auto','low','high'].includes(raw.quality??'')) value.quality=raw.quality!;
  return value;
}
@Injectable({providedIn:'root'})
export class AppearanceService {
  settings=signal<Appearance>(this.restore()); background=signal(this.restoreBackground()); palette=signal(FALLBACK_PALETTE);
  message=signal('Loading supplied background…'); ready=signal(false); private request=0; private objectUrl=''; private hasPalette=false;
  constructor(){
    effect(()=>{const s=this.settings(),p=this.palette(),style=document.documentElement.style;
      for(const [name,value] of Object.entries({primary:p.primary,secondary:p.secondary,accent:p.accent,highlight:p.highlight,glow:p.primary,border:`color-mix(in srgb, ${p.primary} 32%, transparent)`,surface:`color-mix(in srgb, ${p.dark} ${s.glass*100}%, transparent)`,'surface-shell':`color-mix(in srgb, ${p.dark} ${s.glass*100}%, transparent)`,'surface-readable':`color-mix(in srgb, ${p.dark} ${s.glass*100}%, transparent)`,'surface-hover':`color-mix(in srgb, ${p.dark} ${s.glass*100}%, transparent)`,text:'#f4f8ff','text-muted':'#c1d0e2',grid:`color-mix(in srgb, ${p.primary} 18%, transparent)`}))style.setProperty('--holo-'+name,value);
      p.chart.forEach((c,i)=>style.setProperty('--holo-chart-'+(i+1),c));
      style.setProperty('--glass-blur',s.glassBlur+'px');style.setProperty('--glow-strength',String(s.glow));
      try{localStorage.setItem('mediscope-appearance-v1',JSON.stringify(s));}catch{/* Storage optional. */}
    });
    effect(()=>{const auto=this.settings().auto;void this.load(this.background(),auto);});
    effect(()=>{const url=this.background();try{localStorage.setItem('mediscope-background-v1',url.startsWith('blob:')?MAIN_BACKGROUND:url);}catch{/* Storage optional. */}});
  }
  private restore():Appearance {try{const raw=JSON.parse(localStorage.getItem('mediscope-appearance-v1')??'{}');if(localStorage.getItem('mediscope-transparent-v3')!=='1'){if(raw.glass===.72||raw.glass===.48)raw.glass=DEFAULT_APPEARANCE.glass;if(raw.brightness===.75)raw.brightness=DEFAULT_APPEARANCE.brightness;if(raw.glassBlur===10)raw.glassBlur=DEFAULT_APPEARANCE.glassBlur;localStorage.setItem('mediscope-transparent-v3','1');}if(localStorage.getItem('mediscope-background-blur-v4')!=='1'){raw.blur=DEFAULT_APPEARANCE.blur;localStorage.setItem('mediscope-background-blur-v4','1');}return sanitizeAppearance(raw);}catch{return {...DEFAULT_APPEARANCE};}}
  private restoreBackground():string {try{const saved=localStorage.getItem('mediscope-background-v1');if(localStorage.getItem('mediscope-background-v5')!=='1'){localStorage.setItem('mediscope-background-v5','1');if(saved===PREVIOUS_BACKGROUND)return MAIN_BACKGROUND;}return PRESETS.some(p=>p.url===saved)?saved!:MAIN_BACKGROUND;}catch{return MAIN_BACKGROUND;}}
  change<K extends keyof Appearance>(key:K,value:Appearance[K]){this.settings.update(s=>sanitizeAppearance({...s,[key]:value}));}
  select(url:string){if(!PRESETS.some(p=>p.url===url))return;this.releaseUpload();this.background.set(url);}
  async upload(file:File){
    if(!['image/jpeg','image/png','image/webp'].includes(file.type)||file.size===0||file.size>10*1024*1024){this.message.set('Choose a nonempty JPEG, PNG or WebP up to 10 MB.');return;}
    this.releaseUpload();this.objectUrl=URL.createObjectURL(file);this.background.set(this.objectUrl);
  }
  private releaseUpload(){if(this.objectUrl)URL.revokeObjectURL(this.objectUrl);this.objectUrl='';}
  reset(){this.releaseUpload();this.settings.set({...DEFAULT_APPEARANCE});this.background.set(MAIN_BACKGROUND);}
  private async load(url:string,auto:boolean){
    const version=++this.request;this.ready.set(false);
    try{
      const img=new Image();img.decoding='async';img.src=url;await img.decode();if(version!==this.request)return;
      this.ready.set(true);
      if(auto||!this.hasPalette){const canvas=document.createElement('canvas');canvas.width=64;canvas.height=64;const ctx=canvas.getContext('2d',{willReadFrequently:true});if(!ctx)throw new Error('Canvas unavailable');ctx.drawImage(img,0,0,64,64);this.palette.set(extractPalette(ctx.getImageData(0,0,64,64).data));this.hasPalette=true;}
      this.message.set(auto?'Palette extracted locally from this image.':'Automatic palette matching paused.');
    }catch{if(version===this.request){this.palette.set(FALLBACK_PALETTE);if(!this.ready()&&url!==MAIN_BACKGROUND){this.releaseUpload();this.background.set(MAIN_BACKGROUND);this.message.set('Saved or selected image was unavailable. Restored the default background.');}else{this.message.set(this.ready()?'Image visible; color sampling failed, so the readable fallback palette is active.':'Default image unavailable; check the bundled asset.');}}}
  }
}
