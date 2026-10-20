import { AfterViewInit, Component, ElementRef, EventEmitter, inject, Output, ViewChild } from '@angular/core';
import { AppearanceService, PRESETS, Appearance } from './appearance.service';
@Component({selector:'ms-background-studio',standalone:true,template:`
<dialog #dialog class="studio-dialog" aria-labelledby="studio-title" (close)="closed.emit()" (click)="backdrop($event)">
  <div class="flex-between"><div><div class="eyebrow">PERSONALIZE YOUR WORKSPACE</div><h2 id="studio-title">Background Studio</h2></div><button class="btn ghost" autofocus (click)="dialog.close()" aria-label="Close Background Studio">✕</button></div>
  <img class="background-preview" [src]="appearance.background()" alt="Current workspace background preview">
  <p class="small muted" role="status">{{appearance.message()}}</p>
  <div class="studio-presets">@for(p of presets;track p.url){<button class="btn secondary" (click)="appearance.select(p.url)">{{p.name}}</button>}</div>
  <label class="control-label section-gap">Upload image · stays in this browser session<input class="control" type="file" accept="image/jpeg,image/png,image/webp" (change)="upload($event)"></label>
  <label class="studio-toggle"><input type="checkbox" [checked]="appearance.settings().auto" (change)="appearance.change('auto',$any($event.target).checked)"> Match colors to background</label>
  @for(c of controls;track c.key){<label class="studio-slider" [for]="'appearance-'+c.key"><span>{{c.label}} <output>{{appearance.settings()[c.key]}}</output></span><input [id]="'appearance-'+c.key" [attr.aria-label]="c.label" type="range" [min]="c.min" [max]="c.max" [step]="c.step" [value]="appearance.settings()[c.key]" (input)="set(c.key,$event)"></label>}
  <label class="control-label">3D quality<select class="control" [value]="appearance.settings().quality" (change)="appearance.change('quality',$any($event.target).value)"><option value="auto">Adaptive</option><option value="low">Economy</option><option value="high">High</option></select></label>
  <button class="btn" (click)="appearance.reset()">Restore exact defaults</button>
</dialog>`,styles:[`.studio-dialog{width:min(500px,calc(100vw - 24px));max-height:90vh;overflow:auto;color:var(--holo-text);background:#08121ff5;border:1px solid var(--holo-border);border-radius:20px;padding:25px;box-shadow:0 30px 100px #0009}.studio-dialog::backdrop{background:#0009;backdrop-filter:blur(4px)}.background-preview{width:100%;height:135px;object-fit:cover;border-radius:10px}.studio-presets{display:flex;gap:8px;flex-wrap:wrap}.studio-slider{display:block;margin:17px 0;font-size:12px}.studio-slider span{display:flex;justify-content:space-between}.studio-slider input{width:100%;accent-color:var(--holo-primary)}.studio-toggle{display:flex;gap:9px;font-size:12px}.control-label input,.control-label select{display:block;width:100%;margin:8px 0}.studio-toggle input{accent-color:var(--holo-primary)}`]})
export class BackgroundStudio implements AfterViewInit {
  appearance=inject(AppearanceService);presets=PRESETS;@ViewChild('dialog') dialog!:ElementRef<HTMLDialogElement>;@Output() closed=new EventEmitter<void>();
  controls:{key:Exclude<keyof Appearance,'auto'|'quality'>;label:string;min:number;max:number;step:number}[]=[
    {key:'brightness',label:'Background brightness',min:.2,max:1,step:.05},{key:'blur',label:'Background blur (px)',min:0,max:12,step:.1},{key:'position',label:'Background position (%)',min:0,max:100,step:1},
    {key:'glass',label:'Glass opacity',min:0,max:.8,step:.01},{key:'glassBlur',label:'Glass blur (px)',min:0,max:20,step:1},{key:'glow',label:'Glow intensity',min:0,max:1,step:.1},{key:'particles',label:'Particle intensity',min:0,max:1,step:.1}];
  ngAfterViewInit(){this.dialog.nativeElement.showModal();}
  backdrop(e:MouseEvent){if(e.target===this.dialog.nativeElement){const b=this.dialog.nativeElement.getBoundingClientRect();if(e.clientX<b.left||e.clientX>b.right||e.clientY<b.top||e.clientY>b.bottom)this.dialog.nativeElement.close();}}
  set(key:typeof this.controls[number]['key'],e:Event){this.appearance.change(key,Number((e.target as HTMLInputElement).value));}
  upload(e:Event){const file=(e.target as HTMLInputElement).files?.[0];if(file)void this.appearance.upload(file);}
}
