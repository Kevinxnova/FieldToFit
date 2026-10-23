import {catalog,nodeById,type Copy,type Track} from './data';

export type FlagshipModel={id:string;company:string;name:string;source:string;date:string;date_kind:Copy;checked_at:string;role:Copy;status:Copy;notes:Copy;gaps:Record<Track,Copy>};
export type Adoption={id:string;model:string;node:string;track:Track;source:string;section:Copy;statement:Copy;boundary:Copy;reading:'body';checked_at:string;kind:'documented-use'};
export const flagships=(catalog as typeof catalog&{flagships:{revision:number;checked_at:string;scope:string[];models:FlagshipModel[];adoptions:Adoption[]}}).flagships;
export const modelById=Object.fromEntries(flagships.models.map(m=>[m.id,m]));
export const modelEdges=(id:string,track?:Track)=>flagships.adoptions.filter(e=>e.model===id&&(!track||e.track===track));
export function validModels(input:string|null){return [...new Set((input||'').split(',').filter(id=>Object.prototype.hasOwnProperty.call(modelById,id)))].slice(0,2);}
export function compareModels(a:string,b:string,track:Track){
  const left=modelEdges(a,track),right=modelEdges(b,track),l=new Set(left.map(e=>e.node)),r=new Set(right.map(e=>e.node));
  return {common:[...l].filter(id=>r.has(id)),left:[...l].filter(id=>!r.has(id)),right:[...r].filter(id=>!l.has(id))};
}
export function modelNodeLabel(id:string,zh:boolean){const n=nodeById[id]?.node;return n?n.summary.technology[zh?0:1]:id;}
