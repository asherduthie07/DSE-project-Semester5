/* Runtime smoke for six dashboard sections with real export JSON and a minimal DOM stub.
   This verifies JavaScript data wiring; it is not a visual browser rendering test. */
"use strict";
const fs=require("fs"),vm=require("vm"),cp=require("child_process"),path=require("path");
const root=path.resolve(__dirname,"..");
const csvScript=`import csv,json,pathlib\np=pathlib.Path('powerbi/exports/v1')\nprint(json.dumps({f.stem:list(csv.DictReader(f.open(encoding='utf-8',newline=''))) for f in p.glob('*.csv')}))`;
const data=JSON.parse(cp.execFileSync("python3",["-c",csvScript],{cwd:root,encoding:"utf8"}));
const elements=new Map();
class Element {
  constructor(id=""){this.id=id;this.children=[];this._html="";this.textContent="";this.hidden=false;this.dataset={};this.className="";this.classList={toggle:()=>{}};}
  set innerHTML(value){this._html=value;this.children=[];}
  get innerHTML(){return this._html;}
  append(...items){this.children.push(...items);}
  insertAdjacentHTML(_position,value){this._html+=value;}
}
for(const id of ["charts","cards","toolbar","detail","insight","page-title","page-subtitle","loading","content","error"]){elements.set(id,new Element(id));}
const pages=["overview","heart","diabetes","stroke","hospital","quality"];
const nav=pages.map(page=>{const element=new Element();element.dataset.page=page;return element;});
const calls=[];
let onload;
const context={
  document:{getElementById:id=>elements.get(id)||new Element(id),createElement:tag=>new Element(tag),querySelectorAll:()=>nav},
  Plotly:{newPlot:(id,traces,layout)=>{if(!id||!Array.isArray(traces)||!layout)throw Error("Malformed chart");calls.push({id,traces});}},
  fetch:async url=>{const name=url.replace("/api/table/","");return {ok:!!data[name],status:data[name]?200:404,json:async()=>data[name]};},
  window:{addEventListener:(name,callback)=>{if(name==="DOMContentLoaded")onload=callback;}},
  location:{hash:""},console,Number,Set,Map,
};
vm.runInNewContext(fs.readFileSync(path.join(root,"dashboard/app.js"),"utf8"),context,{filename:"dashboard/app.js"});
(async()=>{
  await onload();
  if(elements.get("error").textContent)throw Error(elements.get("error").textContent);
  const counts={overview:calls.length};
  for(const button of nav.slice(1)){const before=calls.length;button.onclick();counts[button.dataset.page]=calls.length-before;if(counts[button.dataset.page]===0)throw Error("No charts: "+button.dataset.page);}
  if(counts.overview===0)throw Error("No overview charts");
  console.log(JSON.stringify({status:"PASS",scope:"JS data wiring only",charts_by_page:counts}));
})().catch(error=>{console.error(error);process.exitCode=1;});
