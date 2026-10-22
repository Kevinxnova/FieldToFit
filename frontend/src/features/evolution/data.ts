import raw from '../../../../backend/llm_evolution/catalog.json';
export type Copy = [string,string];
export type Track = 'train'|'inference'|'systems';
export type Question = {id:string;track:Track;route:string;revision:number;updated_at:string;change_reason:Copy;title:Copy;goal:Copy;problem:Copy;mechanism:Copy;formula:string;example:Copy;limit:Copy;figure:{kind:string;labels:Copy[];caption:Copy};sources:string[];related:string[]};
export type Milestone = {id:string;date:string;title:string;source:string;question:string;relation:string;revision:number;mechanism:Copy;evidence:Copy;kind:"method"|"model"|"engineering";highlight:boolean;problem:Copy;limit:Copy;date_kind:string;formula?:string;references:{source:string;section:Copy}[]};
export type EvolutionRoute = {id:string;track:Track;group:string;highlight:boolean;title:Copy;problem:Copy;method:Copy;limit:Copy;nodes:Milestone[];cases:{id:string;company:string;model:string;year:string;source:string;evidence:Copy;relation:string;nodes:string[]}[];questions:string[]};
export type RelationKind = "improvement"|"alternative"|"combination"|"adoption"|"cross-track";
export type Relation = {id:string;from_node:string;to_node:string;kind:RelationKind;reason:Copy;sources:string[]};
export type Catalog = {revision:number;updated_at:string;period:string;tracks:{id:Track;name:string;label:Copy;description:Copy}[];groups:Record<string,Copy>;companies:Record<string,string>;sources:Record<string,{id:string;title:string;url:string;date:string;checked_at:string;kind:string;revised_at?:string}>;relations:Relation[];routes:EvolutionRoute[];questions:Question[]};
export const catalog = raw as unknown as Catalog;
export const ROOT = '/for-you/evolution';
export const QUESTIONS = ROOT+'/questions';
export const questionById = Object.fromEntries(catalog.questions.map(q=>[q.id,q]));
export function kvMiB(batch:number,layers:number,tokens:number,heads:number,dimension:number,bytes:number) {
  const values=[batch,layers,tokens,heads,dimension,bytes];
  const result=2*values.reduce((a,b)=>a*b,1)/2**20;
  return values.every(v=>Number.isFinite(v)&&v>0)&&Number.isFinite(result) ? result : null;
}

export const nodeById = Object.fromEntries(catalog.routes.flatMap(route=>route.nodes.map(node=>[node.id,{node,route}])));
export type Period = 'all'|'recent';
export const relationCopy:Record<RelationKind,Copy> = {improvement:['改进','Improvement'],alternative:['替代路线','Alternative'],combination:['组合','Combination'],adoption:['采用','Adoption'],'cross-track':['跨主线支撑','Cross-track support']};
export const nodeKindCopy:Record<Milestone['kind'],Copy> = {method:['方法研究','Method'],model:['型号实践','Model practice'],engineering:['工程实现','Engineering']};
export function visibleNodes(route:EvolutionRoute,all:boolean,period:Period) {
  return route.nodes.filter(n=>(all||n.highlight)&&(period==='all'||n.date.slice(0,4)>='2025'));
}
export function nodeDestination(id:string) {
  const target=nodeById[id];
  return target ? ROOT+'?view=all&track='+target.route.track+'&period='+(target.node.date.slice(0,4)>='2025'?'recent':'all')+'&node='+encodeURIComponent(id) : ROOT;
}
export function timeBand(date:string) {
  const year=Number(date.slice(0,4));
  if(year<2020)return '2017–2019';
  if(year<2023)return '2020–2022';
  if(year<2025)return '2023–2024';
  return String(year)+(date.length<7?'':Number(date.slice(5,7))<=6?' H1':' H2');
}
export function nodeCases(route:EvolutionRoute,id:string) {return route.cases.filter(c=>c.nodes.includes(id));}
