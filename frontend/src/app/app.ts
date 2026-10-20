import { Component, DestroyRef, inject, signal } from '@angular/core';
import { Router, RouterLink, RouterLinkActive, RouterOutlet, NavigationEnd } from '@angular/router';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { filter, interval, startWith, switchMap, catchError, of } from 'rxjs';
import { ApiService, ComponentStatus } from './core/api';
import { AppearanceService } from './visualization/appearance.service';
import { BackgroundStudio } from './visualization/background-studio';

const nav = [
  {path: '/command-center', label: 'Command Center', icon: 'M3 3h7v7H3z M14 3h7v7h-7z M3 14h7v7H3z M14 14h7v7h-7z', group: 'WORKSPACE'},
  {path: '/datasets', label: 'Dataset Explorer', icon: 'M4 4h16v16H4z M4 10h16 M10 4v16', group: ''},
  {path: '/analytics', label: 'Disease Analytics', icon: 'M3 17l5-6 4 3 5-8 4 4 M3 21h18', group: ''},
  {path: '/prediction', label: 'Prediction Lab', icon: 'M12 2l2.5 7.5L22 12l-7.5 2.5L12 22l-2.5-7.5L2 12l7.5-2.5z', group: 'INTELLIGENCE'},
  {path: '/models', label: 'ML Laboratory', icon: 'M3 3h18v18H3z M8 3v18 M3 9h18 M3 15h18', group: ''},
  {path: '/big-data', label: 'Big Data Monitor', icon: 'M12 2l9 5v10l-9 5-9-5V7z M3 7l9 5 9-5 M12 12v10', group: 'SYSTEMS'},
  {path: '/research', label: 'Research & Reports', icon: 'M5 3h11l3 3v15H5z M8 9h8 M8 13h8 M8 17h5', group: ''}
];
@Component({selector: 'app-root', standalone: true, imports: [RouterOutlet, RouterLink, RouterLinkActive, BackgroundStudio], templateUrl: './app.html', styleUrl: './app.css'})
export class App {
  appearance=inject(AppearanceService); studio=signal(false);
  private router = inject(Router);
  private api = inject(ApiService);
  private destroy = inject(DestroyRef);
  nav = nav;
  collapsed = signal(false);
  drawer = signal(false);
  page = signal('Command Center');
  apiState = signal<ComponentStatus>({status: 'UNAVAILABLE', message: 'Checking API'});
  infraReady = signal<number | null>(null);
  refreshTime = signal<Date | null>(null);
  constructor() {
    this.router.events.pipe(filter(e => e instanceof NavigationEnd), takeUntilDestroyed(this.destroy)).subscribe(() => {
      this.page.set(nav.find(n => n.path === this.router.url)?.label ?? 'Command Center');
      this.drawer.set(false);
    });
    interval(30000).pipe(startWith(0), switchMap(() => this.api.get<{status: ComponentStatus['status']}>('/health').pipe(catchError(() => of({status: 'UNAVAILABLE' as const})))), takeUntilDestroyed(this.destroy)).subscribe(r => {
      this.apiState.set({status: r.status, message: r.status === 'READY' ? 'API connected' : 'API disconnected'});
      if (r.status === 'READY') this.refreshTime.set(new Date());
    });
    interval(30000).pipe(startWith(0), switchMap(() => this.api.get<{components: Record<string, ComponentStatus>}>('/system/readiness').pipe(catchError(() => of(null)))), takeUntilDestroyed(this.destroy)).subscribe(r => { this.infraReady.set(r ? ['mongodb','hdfs','yarn'].filter(k => r.components?.[k]?.status === 'READY').length : null); });
  }
}
