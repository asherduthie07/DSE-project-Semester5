import { defineConfig } from '@playwright/test';
export default defineConfig({testDir:'./e2e',timeout:90000,expect:{timeout:20000},workers:1,reporter:'list',use:{baseURL:'http://127.0.0.1:4200',viewport:{width:1440,height:1000},headless:true,launchOptions:{args:['--use-angle=swiftshader','--enable-unsafe-swiftshader']},trace:'retain-on-failure'},outputDir:'test-results'});
