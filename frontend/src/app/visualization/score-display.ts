import { Component, computed, input } from '@angular/core';
import { Prediction } from '../core/api';
import { HolographicChart } from './holographic-chart';
import { SceneData } from './geometry';
@Component({selector:'ms-score-display',standalone:true,imports:[HolographicChart],template:`<ms-holographic-chart [data]="scene()"/>`})
export class ScoreDisplay {prediction=input.required<Prediction>();scene=computed<SceneData>(()=>({kind:'score',title:'Saved model output',axes:[{label:''},{label:''},{label:''}],points:[],score:this.prediction().estimated_model_score,note:`Ring fraction = actual model score. Threshold ${this.prediction().decision_threshold}; ${this.prediction().model_name} / ${this.prediction().model_version}. This is not clinical diagnostic certainty.`}));}
