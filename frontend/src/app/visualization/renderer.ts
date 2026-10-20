import * as T from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { Axis, SceneData, axisBounds, normalized } from './geometry';
import { Palette } from './palette';

/** One owned renderer per studio. No global loop or shared mutable scene. */
export class HolographicRenderer {
  private renderer:T.WebGLRenderer;private scene=new T.Scene();private camera=new T.PerspectiveCamera(42,1,.1,100);
  private controls:OrbitControls;private root=new T.Group();private observer:ResizeObserver;private visible=true;private active=true;private raf=0;private last=0;private disposed=false;
  private hoverTargets:T.Object3D[]=[];private ray=new T.Raycaster();private wave?:T.Points;private waveBase?:Float32Array;private textures:T.Texture[]=[];private animated=false;
  private waveLines?:T.LineSegments;
  constructor(private host:HTMLElement,private inspect:(index:number|null,pinned:boolean)=>void,private lost:()=>void,quality:string){
    this.renderer=new T.WebGLRenderer({alpha:true,antialias:quality!=='low',powerPreference:'low-power'});
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio||1,quality==='high'?2:1.25));
    this.host.append(this.renderer.domElement);this.renderer.domElement.setAttribute('aria-label','Interactive three dimensional plot; use the precision view for keyboard data access');
    this.camera.position.set(10,7,11);this.controls=new OrbitControls(this.camera,this.renderer.domElement);this.controls.enableDamping=false;this.controls.minDistance=4;this.controls.maxDistance=45;
    this.controls.addEventListener('change',this.render);this.scene.add(this.root);this.scene.add(new T.HemisphereLight(0xffffff,0x314570,2.4));
    this.observer=new ResizeObserver(this.resize);this.observer.observe(host);this.resize();
    this.renderer.domElement.addEventListener('pointermove',this.pointer);this.renderer.domElement.addEventListener('click',this.pointer);this.renderer.domElement.addEventListener('webglcontextlost',this.contextLost);document.addEventListener('visibilitychange',this.visibility);
    this.ray.params.Points={threshold:.15};
  }
  private contextLost=(e:Event)=>{e.preventDefault();this.lost();};
  private visibility=()=>{this.schedule();};
  private resize=()=>{const w=Math.max(1,this.host.clientWidth),h=Math.max(1,this.host.clientHeight);this.renderer.setSize(w,h);this.camera.aspect=w/h;this.camera.updateProjectionMatrix();this.render();};
  private render=()=>{if(!this.disposed&&this.visible&&!document.hidden)this.renderer.render(this.scene,this.camera);};
  setQuality(quality:string){const low=quality==='low'||quality==='auto'&&(navigator.hardwareConcurrency??4)<=4;this.renderer.setPixelRatio(Math.min(window.devicePixelRatio||1,low?1:quality==='high'?2:1.25));this.resize();}
  private pointer=(e:MouseEvent)=>{const b=this.renderer.domElement.getBoundingClientRect();this.ray.setFromCamera(new T.Vector2((e.clientX-b.left)/b.width*2-1,-(e.clientY-b.top)/b.height*2+1),this.camera);const hit=this.ray.intersectObjects(this.hoverTargets,false)[0];this.inspect(hit?hit.instanceId??hit.index??hit.object.userData['index']??null:null,e.type==='click');};
  private clear(){this.root.traverse(o=>{const mesh=o as T.Mesh;if(mesh.geometry)mesh.geometry.dispose();if(mesh.material)for(const m of Array.isArray(mesh.material)?mesh.material:[mesh.material])m.dispose();});this.root.clear();this.textures.forEach(t=>t.dispose());this.textures=[];this.hoverTargets=[];this.wave=undefined;}
  private label(text:string,at:T.Vector3,color:string){const c=document.createElement('canvas');c.width=512;c.height=64;const ctx=c.getContext('2d');if(!ctx)return;ctx.font=(text.length>20?'24':'36')+'px sans-serif';ctx.fillStyle=color;ctx.textAlign='center';ctx.fillText(text.slice(0,45),256,44);const texture=new T.CanvasTexture(c);this.textures.push(texture);const s=new T.Sprite(new T.SpriteMaterial({map:texture,transparent:true,depthTest:false}));s.position.copy(at);s.scale.set(6,.75,1);this.root.add(s);}
  update(data:SceneData,palette:Palette,particles:number){
    this.clear();this.animated=data.kind==='wave';const color=new T.Color(palette.primary),bounds=axisBounds(data);
    if(data.kind==='wave'){
      const size=particles<.4?26:42,positions:number[]=[],colors:number[]=[];
      for(let z=0;z<size;z++)for(let x=0;x<size;x++){const xx=(x/(size-1)-.5)*14,zz=(z/(size-1)-.5)*9;positions.push(xx,Math.sin(xx*.7)*Math.cos(zz*.55)*1.1,zz);const c=new T.Color(palette.primary).lerp(new T.Color(palette.secondary),x/(size-1));colors.push(c.r,c.g,c.b);}
      const geo=new T.BufferGeometry();geo.setAttribute('position',new T.Float32BufferAttribute(positions,3));geo.setAttribute('color',new T.Float32BufferAttribute(colors,3));
      this.wave=new T.Points(geo,new T.PointsMaterial({size:.045+particles*.035,vertexColors:true,transparent:true,opacity:particles,depthWrite:false}));this.waveBase=new Float32Array(positions);this.root.add(this.wave);
      const lines:number[]=[];for(let z=0;z<size;z++)for(let x=0;x<size-1;x++){const a=(z*size+x)*3,b=a+3;lines.push(...positions.slice(a,a+3),...positions.slice(b,b+3));}
      const line=new T.LineSegments(new T.BufferGeometry().setAttribute('position',new T.Float32BufferAttribute(lines,3)),new T.LineBasicMaterial({color:palette.secondary,transparent:true,opacity:.16*particles,depthWrite:false}));this.root.add(line);this.waveLines=line;
      this.camera.position.set(10,7,14);
    }else if(data.kind==='score'){
      const ring=new T.Mesh(new T.TorusGeometry(2.8,.08,8,96),new T.MeshBasicMaterial({color:palette.secondary,transparent:true,opacity:.2}));this.root.add(ring);
      const arc=new T.Mesh(new T.TorusGeometry(2.8,.14,12,96,Math.PI*2*Math.max(0,Math.min(1,data.score??0))),new T.MeshBasicMaterial({color}));arc.rotation.z=Math.PI/2;this.root.add(arc);
      const sphere=new T.Mesh(new T.SphereGeometry(2.2,24,16),new T.MeshBasicMaterial({color:palette.primary,wireframe:true,transparent:true,opacity:.15}));this.root.add(sphere);this.label((data.score??0).toFixed(4),new T.Vector3(0,0,0),palette.highlight);
    }else{
      const grid=new T.GridHelper(8,8,palette.primary,palette.primary);grid.position.y=-4;(grid.material as T.Material).transparent=true;(grid.material as T.Material).opacity=.18;this.root.add(grid);
      data.axes.forEach((axis:Axis,i)=>{const a=new T.Vector3(-4,-4,-4),b=a.clone();b.setComponent(i,4);this.root.add(new T.Line(new T.BufferGeometry().setFromPoints([a,b]),new T.LineBasicMaterial({color:palette.primary,transparent:true,opacity:.55})));
        const title=b.clone();title.setComponent(i,5.1);this.label(['X','Y','Z'][i]+' · '+axis.label,title,palette.highlight);});
      const groups=[...new Set(data.points.map(p=>p.group))];const pointColor=(g:string)=>new T.Color(palette.chart[groups.indexOf(g)%palette.chart.length]);
      if(data.kind==='bars'||data.kind==='scatter'||data.kind==='network'){
        const geometry=data.kind==='bars'?new T.BoxGeometry(1,1,1):new T.SphereGeometry(data.kind==='network'?.24:.07,8,6);const material=new T.MeshStandardMaterial({color:0xffffff,metalness:.3,roughness:.35,transparent:true,opacity:.82});
        const mesh=new T.InstancedMesh(geometry,material,data.points.length);const dummy=new T.Object3D();
        data.points.forEach((p,i)=>{const [x,y,z]=normalized(p,bounds);dummy.position.set(x,data.kind==='bars'?(-4+y)/2:y,z);dummy.scale.set(data.kind==='bars'?.42:1,data.kind==='bars'?Math.max(.005,y+4):1,data.kind==='bars'?.42:1);dummy.updateMatrix();mesh.setMatrixAt(i,dummy.matrix);mesh.setColorAt(i,pointColor(p.group));if(data.kind==='network')this.label(p.label,new T.Vector3(x,y+.5,z),palette.highlight);});this.root.add(mesh);this.hoverTargets.push(mesh);
        if(data.edges){for(const [a,b] of data.edges){const pa=data.points[a],pb=data.points[b];if(pa&&pb)this.root.add(new T.Line(new T.BufferGeometry().setFromPoints([new T.Vector3(...normalized(pa,bounds)),new T.Vector3(...normalized(pb,bounds))]),new T.LineBasicMaterial({color:palette.secondary,transparent:true,opacity:.4})));}}
      }else if(data.kind==='surface'&&data.grid){
        const positions=data.points.flatMap(p=>normalized(p,bounds));const indices:number[]=[],colors:number[]=[];data.points.forEach(p=>{const c=pointColor(p.group).lerp(new T.Color(palette.secondary),(p.y-bounds[1][0])/(bounds[1][1]-bounds[1][0]));colors.push(c.r,c.g,c.b);});
        for(let z=0;z<data.grid-1;z++)for(let x=0;x<data.grid-1;x++){const a=z*data.grid+x;indices.push(a,a+1,a+data.grid,a+1,a+data.grid+1,a+data.grid);}
        const g=new T.BufferGeometry();g.setAttribute('position',new T.Float32BufferAttribute(positions,3));g.setAttribute('color',new T.Float32BufferAttribute(colors,3));g.setIndex(indices);g.computeVertexNormals();this.root.add(new T.Mesh(g,new T.MeshBasicMaterial({vertexColors:true,transparent:true,opacity:.35,side:T.DoubleSide,depthWrite:false})));
        this.root.add(new T.LineSegments(new T.WireframeGeometry(g),new T.LineBasicMaterial({color:palette.primary,transparent:true,opacity:.22})));const points=new T.Points(g.clone(),new T.PointsMaterial({size:.05,color:palette.highlight}));this.root.add(points);this.hoverTargets.push(points);
      }else if(data.kind==='ridge'){
        groups.forEach(g=>{const points=data.points.filter(p=>p.group===g);this.root.add(new T.Line(new T.BufferGeometry().setFromPoints(points.map(p=>new T.Vector3(...normalized(p,bounds)))),new T.LineBasicMaterial({color:pointColor(g)})));});
        const points=new T.Points(new T.BufferGeometry().setFromPoints(data.points.map(p=>new T.Vector3(...normalized(p,bounds)))),new T.PointsMaterial({size:.12,color:palette.highlight}));this.root.add(points);this.hoverTargets.push(points);
      }
    }
    this.render();this.schedule();
  }
  reset(){this.camera.position.set(10,7,11);this.controls.target.set(0,0,0);this.controls.update();this.render();}
  zoom(factor:number){this.camera.position.sub(this.controls.target).multiplyScalar(factor).add(this.controls.target);this.controls.update();this.render();}
  rotate(){this.camera.position.applyAxisAngle(new T.Vector3(0,1,0),Math.PI/12);this.controls.update();this.render();}
  setActive(active:boolean,visible=true){this.active=active;this.visible=visible;this.schedule();if(visible)this.render();}
  private schedule(){cancelAnimationFrame(this.raf);if(this.animated&&this.active&&this.visible&&!document.hidden&&!this.disposed)this.raf=requestAnimationFrame(this.tick);}
  private tick=(time:number)=>{if(time-this.last>40&&this.wave&&this.waveBase){for(const geometry of [this.wave.geometry,this.waveLines?.geometry]){if(!geometry)continue;const attr=geometry.getAttribute('position') as T.BufferAttribute;for(let i=0;i<attr.count;i++){const x=attr.getX(i),z=attr.getZ(i);attr.setY(i,Math.sin(x*.7+time*.00018)*Math.cos(z*.55)*1.1);}attr.needsUpdate=true;}this.render();this.last=time;}this.schedule();};
  png(){this.render();return this.renderer.domElement.toDataURL('image/png');}
  dispose(){if(this.disposed)return;this.disposed=true;cancelAnimationFrame(this.raf);this.observer.disconnect();document.removeEventListener('visibilitychange',this.visibility);this.renderer.domElement.removeEventListener('pointermove',this.pointer);this.renderer.domElement.removeEventListener('click',this.pointer);this.renderer.domElement.removeEventListener('webglcontextlost',this.contextLost);this.controls.removeEventListener('change',this.render);this.controls.dispose();this.clear();this.renderer.dispose();this.renderer.forceContextLoss();this.renderer.domElement.remove();}
}
