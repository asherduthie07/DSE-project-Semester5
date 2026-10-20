import { Palette } from './palette';
/** Recolor style fields only. Data arrays, numbers, formatters and axes remain intact. */
export function themeChart(option:any,p:Palette,reduced=false):any {
 const colors:Record<string,string>={'#39d9d0':p.chart[0],'#60a5fa':p.chart[1],'#a78bfa':p.chart[2],'#34d399':p.chart[3],'#fbbf24':p.chart[3],'#71869f':p.chart[4],'#527fa9':p.chart[1],'#223248':'#ffffff1f','#34445a':'#ffffff44','#91a6be':'#c1d0e2','#9aaec5':'#c1d0e2','#243c51':p.dark};
 const walk=(v:any,key=''):any=>Array.isArray(v)?v.map(x=>walk(x,key)):v&&typeof v==='object'?Object.fromEntries(Object.entries(v).map(([k,x])=>[k,walk(x,k)])):typeof v==='string'&&['color','backgroundColor','borderColor','shadowColor'].includes(key)?colors[v.toLowerCase()]??v:v;
 const next=walk(option);const axis=(a:any)=>({...a,axisLabel:{...a?.axisLabel,color:'#c1d0e2'},nameTextStyle:{...a?.nameTextStyle,color:'#c1d0e2'},axisLine:{...a?.axisLine,lineStyle:{...a?.axisLine?.lineStyle,color:'#b6c9df80'}}});
 const axes=(a:any)=>Array.isArray(a)?a.map(axis):axis(a);
 return {...next,color:p.chart,backgroundColor:'transparent',animation:!reduced,animationDurationUpdate:250,textStyle:{...next.textStyle,color:'#c1d0e2'},xAxis:axes(next.xAxis),yAxis:axes(next.yAxis),...(next.legend?{legend:{...next.legend,type:'scroll',top:0,right:100,textStyle:{color:'#c1d0e2'}},grid:{...next.grid,top:Math.max(48,next.grid?.top??0)}}:{}),tooltip:{...next.tooltip,backgroundColor:'#07121ff5',borderColor:p.primary,textStyle:{color:'#f4f8ff'}}};
}
