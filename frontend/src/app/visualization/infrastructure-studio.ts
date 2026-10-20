import { Component, computed, input } from '@angular/core';
import { BigDataStatus } from '../core/api';
import { SceneData } from './geometry';
import { HolographicChart } from './holographic-chart';
export function topology(status:BigDataStatus,stale=false):SceneData {
 const nodes=[['MongoDB',-3,1,0,'mongodb'],['HDFS NameNode',0,3,0,'hdfs'],['HDFS DataNode',0,0,2,'documented'],['YARN ResourceManager',3,3,0,'yarn'],['YARN NodeManager',3,0,2,'documented']] as const;
 return {kind:'network',title:'Documented service topology',axes:[{label:'Conceptual layout X'},{label:'Conceptual layout Y'},{label:'Conceptual layout Z'}],points:nodes.map(([label,x,y,z,key])=>({x,y,z,label,group:key==='documented'?'Documented node; individual health not exposed':stale?'STALE · refresh failed':status.live[key]?.status??'UNAVAILABLE'})),edges:[[1,2],[3,4]],note:'Spatial placement is conceptual, not a measurement or network latency. Lines show documented master/worker relationships. Endpoint health is current only after a successful refresh; child-node health is not independently exposed. MongoDB is a separate service.'};
}
@Component({selector:'ms-infrastructure-studio',standalone:true,imports:[HolographicChart],template:`<section class="panel section-gap"><div class="kicker">INFRASTRUCTURE / TOPOLOGY</div><ms-holographic-chart [data]="scene()"/></section>`})
export class InfrastructureStudio {status=input.required<BigDataStatus>();stale=input(false);scene=computed(()=>topology(this.status(),this.stale()));}
