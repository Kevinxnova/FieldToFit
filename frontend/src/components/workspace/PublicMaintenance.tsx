import { Link, useLocation } from 'react-router-dom';
import { useRemote } from '../../api/knowledge';
import { useWorkspace } from './UI';
export type Maintenance = {id:string;canonical_id:string;availability:string;status_revision?:string;relationships:{id:string;name:string;url:string;relation:string;direction:string;version:string;evidence:string}[];materials:{id:string;availability:string;last_checked_at:string;last_success_at:string;failure_days:number;error:string;needs_review:boolean;public_note?:string;changed?:boolean}[]};
const relations:Record<string,string>={publisher:'发布方',family:'所属系列',version:'版本',release:'发布与更新',implementation:'官方实现',integration:'集成关系',related:'相关资料'};
export function PublicMaintenance({value}:{value?:Maintenance}){
 const {pick}=useWorkspace();if(!value)return null;
 const issues=value.materials.filter(m=>m.availability==='check_failed'||m.needs_review||m.public_note);
 if(!value.relationships.length&&!issues.length)return null;
 return <section className="public-maintenance">
 {value.relationships.length>0&&<details><summary>{pick('相关对象与动态','Related objects and developments')} · {value.relationships.length}</summary><ul>{value.relationships.map(r=><li key={r.id}><a href={r.url}>{r.name}</a> · {pick(relations[r.relation]||r.relation,r.relation)}{r.direction==='incoming'?pick('（由关联对象指向本项）',' (incoming)'):''}{r.version?' · '+r.version:''} · <a href={r.evidence} target="_blank" rel="noreferrer">{pick('关系依据','Evidence')}</a></li>)}</ul></details>}
 {issues.length>0&&<details><summary>{pick('材料访问与复核状态','Material access and review')} · {issues.length}</summary><p>{pick('访问检查与内容核验分开记录；旧材料保留原有日期。','Access checks are separate from factual review. Stored materials retain their original dates.')}</p><ul>{issues.map(m=><li key={m.id}><strong>{m.id}</strong> · {m.availability==='check_failed'?pick('本次未能访问来源','Source access failed'):pick('来源可访问','Source reachable')}{m.needs_review?pick(' · 待复核',' · Review pending'):''}<p>{pick('最后检查：','Last check: ')}{m.last_checked_at} · {pick('最后成功：','Last success: ')}{m.last_success_at||pick('尚无成功记录','Not recorded')}{m.failure_days>0?pick(` · 连续 ${m.failure_days} 个自然日失败`,` · ${m.failure_days} consecutive failed days`):''}</p>{m.error&&<p>{m.error}</p>}{m.public_note&&<p>{m.public_note}</p>}</li>)}</ul></details>}
 </section>;
}
export function AliasNotice(){
 const location=useLocation(),{pick}=useWorkspace();
 const match=/^#(?:news|watch)-((?:d-\d+|cw-[matsh]\d+))$/i.exec(location.hash),id=match?.[1].toUpperCase();
 const result=useRemote<Maintenance>(id?'/v1/platform/content/'+id+'/status':null);
 const status=result.data;
 if(!status||status.availability==='available')return null;
 const href='/for-you#'+(status.canonical_id.startsWith('D-')?'news-':'watch-')+status.canonical_id.toLowerCase();
 return <p className="platform-notice" role="status">{status.availability==='merged'?<>{pick('此旧编号已归入现有资料，历史编号仍保留。','This ID has been merged; the original identity remains traceable.')} <Link to={href}>{pick('查看当前资料','Open current profile')} · {status.canonical_id}</Link></>:pick('这项资料已退出当前展示或不可用，不能据此认定其仍适用。','This item is unavailable or no longer in the current collection.')}</p>;
}
