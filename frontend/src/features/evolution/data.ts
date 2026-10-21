import raw from '../../../../backend/llm_evolution/catalog.json';
export type Copy = [string,string];
export type Track = 'train'|'inference'|'systems';
export type Question = {id:string;track:Track;route:string;revision:number;updated_at:string;change_reason:Copy;title:Copy;goal:Copy;problem:Copy;mechanism:Copy;formula:string;example:Copy;limit:Copy;figure:{kind:string;labels:Copy[];caption:Copy};sources:string[];related:string[]};
export type Milestone = {id:string;date:string;title:string;source:string;question:string;relation:string;revision:number;mechanism:Copy;evidence:Copy};
export type EvolutionRoute = {id:string;track:Track;group:string;highlight:boolean;title:Copy;problem:Copy;method:Copy;limit:Copy;nodes:Milestone[];cases:{id:string;company:string;model:string;year:string;source:string;evidence:Copy;relation:string}[];questions:string[]};
export type Catalog = {revision:number;updated_at:string;period:string;tracks:{id:Track;name:string;label:Copy;description:Copy}[];groups:Record<string,Copy>;companies:Record<string,string>;sources:Record<string,{id:string;title:string;url:string;date:string;checked_at:string}>;routes:EvolutionRoute[];questions:Question[]};
export const catalog = raw as unknown as Catalog;
export const ROOT = '/for-you/evolution';
export const QUESTIONS = ROOT+'/questions';
export const questionById = Object.fromEntries(catalog.questions.map(q=>[q.id,q]));
export function kvMiB(batch:number,layers:number,tokens:number,heads:number,dimension:number,bytes:number) {
  const values=[batch,layers,tokens,heads,dimension,bytes];
  const result=2*values.reduce((a,b)=>a*b,1)/2**20;
  return values.every(v=>Number.isFinite(v)&&v>0)&&Number.isFinite(result) ? result : null;
}
