import { request } from '../../api/knowledge';
export type Change = { id:string; object_id:string; canonical_id:string; kind:string; observed_at:string; current_availability:string; changed_fields?:string[]; name?:string; sources?:{title:string;url:string}[]; source_published_at?:string; checked_at?:string; followed_ids:string[] };
export type Follow = { id:string; name:string; canonical_id:string; generation:string; baseline:number|null; checked:number|null; read:string[]; events:Change[]; lastCheck?:string; scanAfter?:number; unavailable?:boolean };
export type FollowState = { version:1; objects:Follow[] };
export type ChangePage = { items:Change[]; objects:{id:string;canonical_id:string;name:string;availability:string}[]; until:number; has_more:boolean; next_cursor:string|null; initialized:boolean };
const KEY='fieldtofit-follows-v1';
export const FOLLOW_CHANGED='fieldtofit-follow-changed';
const ID=/^CW-[MATSH]\d{2,}$/;
export function getFollows():FollowState {
  const raw=localStorage.getItem(KEY);
  if(!raw)return {version:1,objects:[]};
  const value=JSON.parse(raw);
  if(value.version!==1||!Array.isArray(value.objects)||value.objects.length>100||value.objects.some((o:Follow)=>!o||!ID.test(o.id)||typeof o.name!=='string'||typeof o.canonical_id!=='string'||typeof o.generation!=='string'||!Array.isArray(o.events)||!Array.isArray(o.read)||o.read.some(x=>typeof x!=='string'||!/^workspace:\d+$/.test(x))||o.events.some(e=>!e||typeof e.id!=='string'||!/^workspace:\d+$/.test(e.id)||typeof e.object_id!=='string'||typeof e.canonical_id!=='string'||typeof e.kind!=='string'||typeof e.observed_at!=='string'||!Array.isArray(e.followed_ids))||![o.baseline,o.checked].every(n=>n===null||(Number.isSafeInteger(n)&&Number(n)>=0))))throw new Error('关注清单无法读取，请保留站点数据并重试。');
  return value;
}
export async function mutateFollows(update:(s:FollowState)=>FollowState) {
  const save=()=>{const result=update(getFollows());localStorage.setItem(KEY,JSON.stringify(result));window.dispatchEvent(new Event(FOLLOW_CHANGED));};
  if(!navigator.locks)throw new Error('当前浏览器不支持安全保存，请使用支持 Web Locks 的浏览器。');
  await navigator.locks.request(KEY,save);
}
export async function changes(id:string,after:number|null,cursor?:string):Promise<ChangePage>{
  const q=new URLSearchParams({scope:'workspace',include_related:'true',object_id:id,limit:'100'});
  if(cursor)q.set('cursor',cursor);else if(after===null)q.set('initialize','true');else q.set('after',String(after));
  return request('/v1/platform/changes?'+q);
}
export async function addFollow(id:string,name:string) {
  if(!ID.test(id))throw new Error('只能关注已发布的持续关注对象。');
  await mutateFollows(s=>{
    if(s.objects.some(o=>o.id===id||o.canonical_id===id))return s;
    if(s.objects.length>=100)throw new Error('最多关注 100 个对象，请先导出或整理清单。');
    return {...s,objects:[...s.objects,{id,name,canonical_id:id,generation:crypto.randomUUID(),baseline:null,checked:null,read:[],events:[]}]};
  });
  const saved=getFollows().objects.find(o=>o.id===id);
  if(saved)await refreshFollow(saved);
}
export async function refreshFollow(original:Follow) {
  let cursor:string|undefined, after=original.checked===null?null:Math.max(original.checked,original.scanAfter??0), pages=0;
  do {
    const page=await changes(original.id,after,cursor);
    await mutateFollows(s=>({...s,objects:s.objects.map(o=>{
      if(o.id!==original.id||o.generation!==original.generation)return o;
      const identity=page.objects[0];
      // Persist acquired events before advancing the completed scan checkpoint.
      // Cached entries contain only identifiers/statuses: source prose is revalidated online.
      const all=new Map(o.events.map(e=>[e.id,e]));
      for(const e of page.items)all.set(e.id,{id:e.id,object_id:e.object_id,canonical_id:e.canonical_id,kind:e.kind,observed_at:e.observed_at,current_availability:e.current_availability,followed_ids:e.followed_ids,changed_fields:e.changed_fields});
      return {...o,name:identity.availability==='unavailable'?o.name:identity.name,canonical_id:identity.canonical_id,unavailable:identity.availability==='unavailable',
        scanAfter:page.has_more?Math.max(o.scanAfter??o.checked??0,...page.items.map(e=>Number(e.id.split(':')[1]))):undefined,
        baseline:o.baseline??page.until, checked:page.has_more?o.checked:Math.max(o.checked??0,page.until),events:[...all.values()],lastCheck:page.has_more?o.lastCheck:new Date().toISOString()};
    })}));
    cursor=page.next_cursor||undefined;
    if(++pages>=20&&cursor)throw new Error('已保存部分更新，还有内容待取，请继续检查。');
  }while(cursor);
}
export function exportFollows(){
  return {format:'fieldtofit-follow-list',version:1,origin:window.location.origin,exported_at:new Date().toISOString(),objects:getFollows().objects.map(({id,name,baseline,checked,read})=>({id,name,baseline,checked,read}))};
}
export function parseImport(body:string): {id:string;name:string;baseline:number|null;checked:number|null;read:string[]}[]{
  if(body.length>1_000_000)throw new Error('清单不能超过 1 MB。');
  const value=JSON.parse(body);
  if(value.format!=='fieldtofit-follow-list'||value.version!==1||value.origin!==window.location.origin||!Array.isArray(value.objects)||value.objects.length>100)throw new Error('仅支持本站版本 1 关注清单，最多 100 项。');
  const ids=new Set<string>();
  return value.objects.map((v:Record<string,unknown>)=>{
    if(!v||typeof v.id!=='string'||!ID.test(v.id)||ids.has(v.id)||typeof v.name!=='string'||v.name.length>200)throw new Error('对象编号、名称或重复项无效。');
    ids.add(v.id);
    const baseline=Number.isSafeInteger(v.baseline)&&Number(v.baseline)>=0?Number(v.baseline):null;
    const checked=Number.isSafeInteger(v.checked)&&Number(v.checked)>=Number(baseline)?Number(v.checked):null;
    const read=Array.isArray(v.read)?v.read.filter((x):x is string=>typeof x==='string'&&/^workspace:\d+$/.test(x)).slice(0,10000):[];
    return {id:v.id,name:v.name,baseline,checked,read};
  });
}
