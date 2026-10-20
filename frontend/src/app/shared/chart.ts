import { Component, ElementRef, Input, OnChanges, OnDestroy, ViewChild, AfterViewInit, inject, effect } from '@angular/core';
import { AppearanceService } from '../visualization/appearance.service';
import { themeChart } from '../visualization/chart-theme';
import * as echarts from 'echarts/core';
import { BarChart, LineChart, HeatmapChart, ScatterChart } from 'echarts/charts';
import { GridComponent, TooltipComponent, LegendComponent, DataZoomComponent, VisualMapComponent, ToolboxComponent } from 'echarts/components';
import { CanvasRenderer } from 'echarts/renderers';
import type { EChartsCoreOption } from 'echarts/core';

echarts.use([BarChart, LineChart, HeatmapChart, ScatterChart, GridComponent, TooltipComponent, LegendComponent, DataZoomComponent, VisualMapComponent, ToolboxComponent, CanvasRenderer]);
@Component({ selector: 'ms-chart', standalone: true, template: '<div class="chart-wrap" #wrap><div class="chart-tools"><button type="button" (click)="reset()" aria-label="Reset chart zoom" title="Reset zoom">↺</button><button type="button" (click)="download()" aria-label="Export chart PNG" title="Export PNG">↓</button><button type="button" (click)="fullscreen()" aria-label="Expand chart fullscreen" title="Fullscreen">⛶</button></div><div #canvas class="chart-canvas" role="img" [attr.aria-label]="label"></div></div>', styles: ['.chart-wrap{position:relative}.chart-tools{position:absolute;right:5px;top:0;z-index:2;display:flex;gap:4px}.chart-tools button{background:#1a2c40;border:1px solid #345069;color:#a9cad8;width:27px;height:25px;border-radius:5px}.chart-tools button:hover{color:#39d9d0}.chart-wrap:fullscreen{background:#101a2b;display:grid;place-items:center}.chart-wrap:fullscreen .chart-canvas{width:90vw;height:85vh}'] })
export class ChartComponent implements AfterViewInit, OnChanges, OnDestroy {
  @Input() option: EChartsCoreOption = {};
  @Input() label = 'Interactive chart';
  @ViewChild('canvas') canvas!: ElementRef<HTMLElement>;
  @ViewChild('wrap') wrap!: ElementRef<HTMLElement>;
  private instance?: echarts.ECharts;
  private observer?: ResizeObserver;
  private appearance=inject(AppearanceService);
  private dataSignature='';private themeSignature='';
  constructor(){effect(()=>{this.appearance.palette();this.apply();});}
  private apply(){if(!this.instance)return;const data=JSON.stringify(this.option,(_,v)=>typeof v==='function'?v.toString():v),theme=JSON.stringify(this.appearance.palette());if(data===this.dataSignature&&theme===this.themeSignature)return;const next=themeChart(this.option,this.appearance.palette(),window.matchMedia?.('(prefers-reduced-motion: reduce)').matches??false);if(data===this.dataSignature){const current=this.instance.getOption();if(current['dataZoom'])next.dataZoom=current['dataZoom'];if(current['legend']){const legends=current['legend'] as any[];next.legend={...next.legend,selected:legends[0]?.selected};}}this.instance.setOption(next,true);this.dataSignature=data;this.themeSignature=theme;}
  ngAfterViewInit() {
    this.instance = echarts.init(this.canvas.nativeElement, undefined, {renderer: 'canvas'});
    this.apply();
    this.observer = new ResizeObserver(() => this.instance?.resize());
    this.observer.observe(this.canvas.nativeElement);
  }
  ngOnChanges() { this.apply(); }
  reset() { this.instance?.dispatchAction({type:'dataZoom', start:0, end:100}); }
  download() { if (!this.instance) return; const link=document.createElement('a');link.href=this.instance.getDataURL({type:'png',pixelRatio:2,backgroundColor:'#101a2b'});link.download=this.label.toLowerCase().replace(/[^a-z0-9]+/g,'-')+'.png';link.click(); }
  fullscreen() { if(document.fullscreenElement) document.exitFullscreen(); else this.wrap.nativeElement.requestFullscreen(); setTimeout(()=>this.instance?.resize(),250); }
  ngOnDestroy() { this.observer?.disconnect(); this.instance?.dispose(); }
}
export const chartBase = {backgroundColor: 'transparent', textStyle: {color: '#9AAEC5', fontFamily: 'Inter, sans-serif'}, tooltip: {trigger: 'axis', backgroundColor: '#15243a', borderColor: '#33465e', textStyle: {color: '#f1f6fc'}}, grid: {left: 44, right: 20, top: 28, bottom: 44}, xAxis: {axisLine: {lineStyle: {color: '#34445a'}}, axisLabel: {color: '#91a6be'}, splitLine: {show: false}}, yAxis: {axisLine: {show: false}, axisLabel: {color: '#91a6be'}, splitLine: {lineStyle: {color: '#223248'}}} };
