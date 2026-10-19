import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable, shareReplay, timeout, catchError, throwError } from 'rxjs';

export type Task = 'heart' | 'diabetes' | 'stroke';
export type DatasetId = 'uci_cleveland_heart' | 'uci_early_diabetes' | 'kaggle_stroke' | 'synthea_csv';
export const diseaseDatasets: Record<Task, DatasetId> = { heart: 'uci_cleveland_heart', diabetes: 'uci_early_diabetes', stroke: 'kaggle_stroke' };
export const taskNames: Record<Task, string> = { heart: 'Heart disease', diabetes: 'Diabetes', stroke: 'Stroke' };
export const tasks: Task[] = ['heart', 'diabetes', 'stroke'];
export interface ComponentStatus { status: 'READY' | 'DEGRADED' | 'UNAVAILABLE' | 'NOT_VERIFIED'; message: string }
export interface Dataset { id: DatasetId; name: string; records: string; source_url: string; source_sha256: string; tables: Record<string, number> }
export interface DatasetList { datasets: Dataset[] }
export interface DatasetSchema { dataset_id: string; name: string; source_sha256: string; tables: Record<string, { rows: number; fields: {name: string; dtype: string; nullable: boolean; exposed_in_records: boolean}[]; record_fields: string[] }> }
export interface DatasetSummary { dataset_id: string; name: string; source_url: string; provenance: string; source_sha256: string; tables: Record<string, { rows: number; missing: Record<string, number>; columns: string[]; duplicates?: number }>; rows: Record<string, number> }
export interface RecordPage { dataset_id: string; table: string; source_rows: number; total: number; offset: number; limit: number; items: Record<string, unknown>[] }
export interface ChartSeries { id: string; label: string; categories: string[]; values: number[]; unit: string; sample_size: number; missingness_note: string }
export interface ChartResponse { dataset_id: string; charts: ChartSeries[]; approved_figures: string[]; source_url: string; caveat: string }
export interface Hypothesis { id: string; question: string; null: string; alternative: string; method: string; p_value: number; effect_name: string; effect_size: number; ci_low: number; ci_high: number; ci_parameter: string; positive_n: number; negative_n: number; interpretation: string; limitation: string }
export interface Trial { algorithm: string; selected: boolean; best_params: Record<string, unknown>; cv_mean: number; cv_std: number; cv_fold_scores: number[]; test_metrics: Record<string, number | number[][] | null>; decision_threshold: number }
export interface Comparison { task: Task; cv_strategy: string; selection_score: string; selected_model: string; trials: Trial[]; warning: string }
export interface ModelDetail { task: Task; selected_model: string; artifact_version: string; selection_score: string; selection_reason: string; cv_strategy: string; available_for_prediction: boolean; warning: string }
export interface Curve { roc?: {fpr: number[]; tpr: number[]}; precision_recall?: {recall: number[]; precision: number[]}; roc_auc?: number; average_precision?: number }
export interface PredictionField { name: string; type: 'number' | 'category'; integer?: boolean; minimum?: number; maximum?: number; exclusive_minimum?: boolean; nullable: boolean; allowed?: (string | number)[] }
export interface PredictionSchema { task: Task; features: PredictionField[]; selected_model: string; artifact_version: string; warning: string }
export interface Prediction { task: Task; predicted_class: number; predicted_source_label: string | number; estimated_model_score: number; decision_threshold: number; model_name: string; model_version: string; explanation: { method: string; top_changes: Record<string, unknown>[]; caveat: string }; warning: string }
export interface BigDataStatus { live: Record<string, ComponentStatus>; saved_mapreduce_evidence: Record<string, unknown> }
export interface ReportList { reports: {key:string; title:string; available:boolean}[]; charts: {key:string; path:string; available:boolean}[]; powerbi: {static_artifacts:boolean; desktop_runtime:string; service_publishing:string} }

@Injectable({providedIn: 'root'})
export class ApiService {
  private http = inject(HttpClient);
  private base = '/api/v1';
  private cache = new Map<string, Observable<unknown>>();
  get<T>(path: string, params?: Record<string, string | number>, stable = false): Observable<T> {
    const query = params ? new HttpParams({fromObject: params}) : undefined;
    const key = path + (query ? '?' + query.toString() : '');
    if (stable && this.cache.has(key)) return this.cache.get(key) as Observable<T>;
    const request = this.http.get<T>(this.base + path, {params: query}).pipe(timeout(12000), catchError(error => { if (stable) this.cache.delete(key); return throwError(() => error); }), shareReplay({bufferSize: 1, refCount: true}));
    if (stable) this.cache.set(key, request);
    return request;
  }
  predict(task: Task, features: Record<string, string | number | null>): Observable<Prediction> {
    return this.http.post<Prediction>(`${this.base}/predictions/${task}`, {features}).pipe(timeout(20000));
  }
  datasets() { return this.get<DatasetList>('/datasets', undefined, true); }
  chart(task: Task) { return this.get<ChartResponse>(`/analytics/${diseaseDatasets[task]}/charts`, undefined, true); }
  comparison(task: Task) { return this.get<Comparison>(`/models/${task}/comparison`, undefined, true); }
}
