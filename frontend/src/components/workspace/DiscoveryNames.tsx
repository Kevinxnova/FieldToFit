import {useState} from 'react';
import {request,send,useRemote} from '../../api/knowledge';
const api='/v1/admin/workspace/names';
const outcomes:Record<string,string>={recommend:'已核验建议推荐',investigate:'继续核验',not_recommended:'同证据不再推荐'};
type Material={url:string;title?:string;body:string;locator?:string};
type Lead={ref:string;title:string;url:string;family:string;mention:{name:string;field:string;start:number;end:number;quote:string;method:string};materials:Material[]};
type Identity={key:string;refs:string[];basis:string;evidence:string[];author?:string;organization?:string;version?:string;change?:string};
type Review={outcome?:string;reason?:string;identities?:Identity[];materials?:Material[];reviewed_at?:string};
type Group={id:string;name:string;version:string;families:number;trigger:string[];leads:Lead[];fingerprint:string;review:Review;suppressed:boolean;known_objects:{id:string;name:string}[]};
type Board={items:Group[];total:number;offset:number;next_offset:number|null;targets:{id:string}[];candidate_backlog:number};
export function DiscoveryNames(){
 const [offset,setOffset]=useState(0),[active,setActive]=useState(''),[busy,setBusy]=useState(false),[error,setError]=useState(''),[history,setHistory]=useState<any[]>([]),[reason,setReason]=useState('');
 const data=useRemote<Board>(api+'?offset='+offset,true);
 const selected=data.data?.items.find(g=>g.id===active);
 async function act(path:string,body:unknown){setBusy(true);setError('');try{await send(api+path,body,'POST',true);data.reload();}catch(e){setError((e as Error).message);}finally{setBusy(false);}}
 return <section className="management-panel"><h2>新名称线索组</h2><p>把近期反复出现的名称放在一起，先核对同名、版本和官方出处，再给出推荐。这里只保存私密线索。</p><button className="button" disabled={busy} onClick={()=>act('/prepare',{})}>准备今日追源队列</button><button className="button" onClick={data.reload}>刷新名称组</button>{(error||data.error)&&<p className="error-text" role="alert">{error||data.error}</p>}
 <p className="muted">今日已安排 {data.data?.targets.length||0} / 10 组；每组最多3次检索、5份材料。候选读取积压 {data.data?.candidate_backlog||0} 项。需本地助手核对原文；未核验项保留待处理。</p>
 <ul>{data.data?.items.map(g=><li key={g.id}><button className="text-button" aria-expanded={active===g.id} onClick={()=>{setActive(active===g.id?'':g.id);setHistory([]);setReason('');}}>{g.name} {g.version} · {g.families} 组原始入口 · {g.review.outcome==='recommend'?'已核验建议推荐':g.suppressed?'同证据不再推荐':g.review.outcome==='investigate'?'继续核验':'待消歧追源'}{data.data?.targets.some(t=>t.id===g.id)?' · 今日队列':''}</button></li>)}</ul>
 {data.data?.total===0&&<p>暂无满足触发条件的名称组。</p>}
 {selected&&<div><h3>{selected.name} {selected.version}</h3><p>{selected.trigger.join('；')}。同名仍可能属于不同项目。</p>{selected.known_objects.length>0&&<p>命中已审名称：{selected.known_objects.map(o=>o.id+' '+o.name).join('、')}</p>}
 {selected.leads.map(l=><details key={l.ref}><summary>{l.title}</summary><p><a href={l.url} target="_blank" rel="noreferrer">原始线索 ↗</a></p><p>名称原文：{l.mention.quote} · {l.mention.field} {l.mention.start}–{l.mention.end}</p>{l.materials.map((m,i)=><details key={i}><summary>{m.title||'已获取材料'} · {m.locator}</summary><pre style={{whiteSpace:'pre-wrap',overflowWrap:'anywhere'}}>{m.body}</pre></details>)}</details>)}
 {selected.review.reason&&<p>核验结论：{selected.review.reason}</p>}{selected.review.identities?.map((i,n)=><div key={n}><h4>{i.key}</h4><p>{i.basis}</p><p>{[i.author&&'作者：'+i.author,i.organization&&'组织：'+i.organization,i.version&&'版本：'+i.version,i.change&&'变化：'+i.change].filter(Boolean).join('；')}</p>{i.evidence.map(u=><p key={u}><a href={u} target="_blank" rel="noreferrer">官方出处 ↗</a></p>)}</div>)}
 {selected.review.materials?.map((m,i)=><details key={'review-material-'+i}><summary>核验原文 · {m.title||m.url}</summary><p>{m.locator}</p><pre style={{whiteSpace:'pre-wrap',overflowWrap:'anywhere'}}>{m.body}</pre></details>)}
 <button className="button" disabled={busy} onClick={async()=>{try{const r=await request<{items:any[]}>(api+'/'+selected.id+'/history',{},true);setHistory(r.items);}catch(e){setError((e as Error).message);}}}>查看核验与撤销历史</button>{history.map(h=><details key={h.id}><summary>{h.created_at} · {h.data.action==='reopen'?'重新核验':h.data.action==='trace'?(h.data.status==='read'?'已读取原文':'追源待核验'):(outcomes[h.data.outcome]||'核验记录')}</summary><p>{h.data.reason||h.data.error||h.data.url}</p></details>)}
 {selected.review.outcome&&<label className="management-field"><span>重新核验理由</span><textarea value={reason} onChange={e=>setReason(e.target.value)}/><button className="button" disabled={busy||!reason.trim()} onClick={()=>act('/'+selected.id+'/reopen',{fingerprint:selected.fingerprint,reason})}>撤销当前结论，重新核验</button></label>}</div>}
 <div className="management-pager"><span>共 {data.data?.total||0} 组</span><button className="button" disabled={!offset} onClick={()=>{setOffset(Math.max(0,offset-30));setActive('');}}>上一页</button><button className="button" disabled={data.data?.next_offset==null} onClick={()=>{setOffset(data.data!.next_offset!);setActive('');}}>下一页</button></div></section>;
}
