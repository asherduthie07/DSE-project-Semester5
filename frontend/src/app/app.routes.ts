import { Routes } from '@angular/router';
export const routes: Routes = [
  {path: '', pathMatch: 'full', redirectTo: 'command-center'},
  {path: 'command-center', title: 'Command Center', loadComponent: () => import('./pages/overview').then(m => m.OverviewPage)},
  {path: 'datasets', title: 'Dataset Explorer', loadComponent: () => import('./pages/datasets').then(m => m.DatasetsPage)},
  {path: 'analytics', title: 'Disease Analytics', loadComponent: () => import('./pages/analytics').then(m => m.AnalyticsPage)},
  {path: 'prediction', title: 'Prediction Lab', loadComponent: () => import('./pages/prediction').then(m => m.PredictionPage)},
  {path: 'models', title: 'ML Laboratory', loadComponent: () => import('./pages/models').then(m => m.ModelsPage)},
  {path: 'big-data', title: 'Big Data Monitor', loadComponent: () => import('./pages/bigdata').then(m => m.BigDataPage)},
  {path: 'research', title: 'Research & Reports', loadComponent: () => import('./pages/research').then(m => m.ResearchPage)},
  {path: '**', redirectTo: 'command-center'}
];
