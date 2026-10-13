/** Scene lifecycle and motion preferences, with no browser or production state. */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const {createRequire} = require('node:module');
const root = path.resolve(__dirname, '../..'), fr = createRequire(path.join(root, 'frontend/package.json')), ts = fr('typescript');
function load(file) {
  const out = {exports:{}};
  const code = ts.transpileModule(fs.readFileSync(file, 'utf8'), {compilerOptions:{module:ts.ModuleKind.CommonJS,target:ts.ScriptTarget.ES2022}}).outputText;
  new Function('require','module','exports',code)(name => name.startsWith('.') ? load(path.resolve(path.dirname(file), name + '.ts')) : fr(name),out,out.exports);
  return out.exports;
}
const {mountForYouScene} = load(path.join(root,'frontend/src/components/workspace/forYouScene.ts'));
const {createSphereFlow} = load(path.join(root,'frontend/src/components/workspace/sphereFlow.ts'));
let now, queue, next, requests, resize, visibility, reduce, doc, programs, textures, buffers, vaos, paintUploads, draws, g;
class Surface extends EventTarget {
  constructor() {super();this.style={};this.dataset={};this.disabled=true;this.width=0;this.height=0;}
  getBoundingClientRect(){return {left:0,top:0,width:1100,height:525};}
}
function setup() {
  now=performance.now();queue=new Map();next=0;requests=[];programs=new Set();textures=new Set();buffers=new Set();vaos=new Set();paintUploads=0;draws=0;
  reduce=new EventTarget();reduce.matches=false;doc=new EventTarget();doc.hidden=false;
  global.matchMedia=query=>query.includes('reduced')?reduce:{matches:false};global.document=doc;global.devicePixelRatio=2;
  global.requestAnimationFrame=fn=>{queue.set(++next,fn);return next;};global.cancelAnimationFrame=id=>queue.delete(id);
  global.ResizeObserver=class{constructor(fn){resize=this;this.fn=fn;}observe(){this.fn();}disconnect(){this.disconnected=true;}};
  global.IntersectionObserver=class{constructor(fn){visibility=this;this.fn=fn;}observe(){this.fn([{isIntersecting:true}]);}disconnect(){this.disconnected=true;}};
  global.Image=class{set src(value){this.url=value;requests.push(this);}};
  doc.createElement=()=>({getContext:()=>({font:'',translate(){},scale(){},measureText(){return {width:1800};},fillText(){}})});
  const methods={getShaderParameter:()=>true,getProgramParameter:()=>true,getAttribLocation:()=>0,getUniformLocation:(_p,n)=>n,isContextLost:()=>false,
    createProgram:()=>{const p={};programs.add(p);return p;},deleteProgram:p=>programs.delete(p),
    createTexture:()=>{const p={};textures.add(p);return p;},deleteTexture:p=>textures.delete(p),
    createBuffer:()=>{const p={};buffers.add(p);return p;},deleteBuffer:p=>buffers.delete(p),
    createVertexArray:()=>{const p={};vaos.add(p);return p;},deleteVertexArray:p=>vaos.delete(p),createShader:()=>({}),
    drawArrays:()=>draws++,texSubImage2D:(...args)=>{if(args.at(-1).some((v,i)=>i%4===0&&v>0))paintUploads++;}};
  g=new Proxy(methods,{get:(o,k)=>k in o?o[k]:/^[A-Z_0-9]+$/.test(k)?1:()=>{}});
  const art=new Surface(),canvas=new Surface(),globe=new Surface();canvas.getContext=()=>g;
  return {art,canvas,globe};
}
async function ready() {for(const image of requests.splice(0))image.onload?.();await Promise.resolve();await Promise.resolve();}
function frame(){now+=100;const entries=[...queue.values()];queue.clear();for(const fn of entries)fn(now);}
function pointer(target,x,y){const e=new Event('pointermove');Object.assign(e,{clientX:x,clientY:y,pointerType:'mouse'});target.dispatchEvent(e);}
(async()=>{
  let els=setup();els.canvas.getContext=()=>null;mountForYouScene(els.art,els.canvas,els.globe)();assert.equal(requests.length,0);
  els=setup();let dispose=mountForYouScene(els.art,els.canvas,els.globe);await ready();assert.equal(els.art.dataset.renderer,'webgl2');assert.equal(els.globe.disabled,false);assert.equal(queue.size,1);assert.equal(programs.size,3);
  const initial=draws;frame();assert(draws>initial);assert(els.canvas.width<=1650);
  pointer(els.art,766.55,248.65);frame();assert(paintUploads>0,'entering the sphere must upload visible dye');
  els.globe.dispatchEvent(new Event('click'));frame();assert(paintUploads>0);
  reduce.matches=true;reduce.dispatchEvent(new Event('change'));assert.equal(queue.size,0);assert(els.globe.disabled);
  const before=draws;frame();assert.equal(draws,before);
  reduce.matches=false;reduce.dispatchEvent(new Event('change'));assert.equal(queue.size,1);
  doc.hidden=true;doc.dispatchEvent(new Event('visibilitychange'));assert.equal(queue.size,0);
  doc.hidden=false;doc.dispatchEvent(new Event('visibilitychange'));assert.equal(queue.size,1);
  visibility.fn([{isIntersecting:false}]);assert.equal(queue.size,0);visibility.fn([{isIntersecting:true}]);assert.equal(queue.size,1);
  els.canvas.dispatchEvent(new Event('webglcontextlost',{cancelable:true}));assert.equal(els.art.dataset.renderer,undefined);assert.equal(queue.size,0);assert(els.globe.disabled);
  els.canvas.dispatchEvent(new Event('webglcontextrestored'));await ready();assert.equal(els.art.dataset.renderer,'webgl2');assert.equal(programs.size,3);
  dispose();assert.equal(queue.size,0);assert(resize.disconnected&&visibility.disconnected);assert.equal(programs.size+textures.size+buffers.size+vaos.size,0);
  doc.dispatchEvent(new Event('visibilitychange'));reduce.dispatchEvent(new Event('change'));els.globe.dispatchEvent(new Event('click'));assert.equal(queue.size,0);
  console.log('PASS: animation, sphere input, motion preference, visibility, context restoration and complete GPU cleanup');
  els=setup();dispose=mountForYouScene(els.art,els.canvas,els.globe);const stale=[...requests];dispose();for(const image of stale)image.onload?.();await Promise.resolve();assert.equal(programs.size,0);assert.equal(queue.size,0);
  els=setup();dispose=mountForYouScene(els.art,els.canvas,els.globe);const oldBatch=requests.splice(0);els.canvas.dispatchEvent(new Event('webglcontextlost',{cancelable:true}));els.canvas.dispatchEvent(new Event('webglcontextrestored'));for(const image of oldBatch)image.onload?.();await Promise.resolve();assert.equal(programs.size,0);await ready();assert.equal(programs.size,3);dispose();
  els=setup();dispose=mountForYouScene(els.art,els.canvas,els.globe);requests[0].onerror();await Promise.resolve();await Promise.resolve();assert.equal(els.art.dataset.renderer,undefined);assert(els.globe.disabled);assert.equal(queue.size,0);dispose();
  console.log('PASS: late asset completion cannot revive an unmounted scene; failed assets retain static fallback');
  const flow=createSphereFlow();flow.splat(.99,.5,40,-30);flow.splat(.01,.5,-40,30);flow.step(.03);let peak=flow.pixels.reduce((n,v,i)=>n+(i%4===0?v:0),0);assert(peak>0);
  for(let i=0;i<600;i++)flow.step(.03);const faded=flow.pixels.reduce((n,v,i)=>n+(i%4===0?v:0),0);assert(faded<peak*.02);assert(flow.pixels.every(Number.isFinite));
  console.log('PASS: seam-crossing fluid remains bounded and fades without residual activity');
})().catch(e=>{console.error(e);process.exitCode=1;});
