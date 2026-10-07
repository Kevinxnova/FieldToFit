import type { NewsItem } from './NewsReading';
export type SourcePost = {
  url:string;kind:'primary'|'supplement'|'reply'|'correction';author_name:string;author_handle:string;
  text_en:string;translation_zh:string;text_scope:'full'|'excerpt';announced_at:string;
  timestamp_basis:string;evidence_url:string;retrieval_method:string;checked_at:string;reuse_basis:string;
  avatar?:{url:string;source_url:string;evidence_url:string;checked_at:string;retrieval_method:string};
  context?:{kind:'reply'|'quote';url:string;author_name:string;author_handle:string;text_en:string;translation_zh:string;text_scope:'full'|'excerpt'};
};
export type CodexEvent = {
  event_key:string;group:'codex'|'other_openai';type:string;official_day:number|null;
  date_precision:'instant'|'source_date';announced_at:string|null;timestamp_basis:string;date:string;calendar_day:number;
  overview_zh?:string;overview_en?:string;source_posts?:SourcePost[];
  roundup?:{source_url:string;official_day:number;steps:RoundupStep[]};
  reset?:{scope:string;plans:string;source_url:string;effective_at:string};
};
export type RoundupStep={number:number;news_id:string};
export type CodexRoundup={source_news_id:string;official_day:number;date:string;calendar_day:number;source_post:SourcePost;steps:RoundupStep[];total_steps:number};
export type CodexDay={date:string;calendar_day:number;codex_ids:string[];other_openai_ids:string[];ordered_ids?:string[]};
export type CodexTopic = {
  id:string;title:string;title_en:string;subtitle:string;subtitle_en:string;start_date:string;end_date:string;timezone:string;
  pledge:{url:string;evidence_url:string;announced_at:string;timestamp_basis:string;summary:string;summary_en:string};
  days:CodexDay[];total:number;roundups?:CodexRoundup[];
};
export const codexTypes:Record<string,[string,string]>={feature:['功能','Feature'],model:['模型','Model'],speed:['效率','Performance'],fix:['修复','Fix'],reset:['额度重置','Usage reset'],announcement:['发布','Release']};
export function overview(item:NewsItem,zh:boolean){return (zh?item.codex_28_days?.overview_zh:item.codex_28_days?.overview_en)||item.title;}
export function dayItems(day:CodexDay,byId:Map<string,NewsItem>){return (day.ordered_ids||[...day.codex_ids,...day.other_openai_ids]).flatMap(id=>byId.get(id)?[byId.get(id)!]:[]);}
export function monthCells(month:string){
  const [year,number]=month.split('-').map(Number);const first=new Date(Date.UTC(year,number-1,1));
  const offset=(first.getUTCDay()+6)%7;const size=Math.ceil((offset+new Date(Date.UTC(year,number,0)).getUTCDate())/7)*7;
  return Array.from({length:size},(_,i)=>{const date=new Date(Date.UTC(year,number-1,i-offset+1));return {date:date.toISOString().slice(0,10),number:date.getUTCDate(),inMonth:date.getUTCMonth()===number-1};});
}
export function weekStart(day:string){const date=new Date(day+'T00:00:00Z');date.setUTCDate(date.getUTCDate()-(date.getUTCDay()+6)%7);return date.toISOString().slice(0,10);}
