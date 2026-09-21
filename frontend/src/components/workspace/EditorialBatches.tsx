import { useState } from 'react';
import { send as rawSend, useRemote } from '../../api/knowledge';
type Obj=Record<string,any>;
const send=<T,>(path:string,data:unknown)=>rawSend<T>(path,data,'POST',true);
const api='/v1/admin/workspace';
const labels:Record<string,string>={pending:'待决定',continue:'继续整理',later:'稍后',declined:'不采用',published:'已发布',withdrawn:'已下架',running:'正在整理日报',prepared:'正文已准备，交付待核实',delivered:'已核实交付',failed:'执行失败',missing:'今日无记录'};
export function EditorialBatches({open}:{open:(kind:string,id:string)=>void}){
 const list=useRemote<Obj>(api+'/batches',true),[active,setActive]=useState(''),[error,setError]=useState(''),[busy,setBusy]=useState(false);
 const selected=active||list.data?.items[0]?.id||'';const detail=useRemote<Obj>(selected?api+'/batches/'+selected:null,true);
 const run=async(fn:()=>Promise<unknown>)=>{setBusy(true);setError('');try{await fn();list.reload();detail.reload();}catch(e){setError((e as Error).message);}finally{setBusy(false);}};
 return <section className="platform-panel editorial-batches"><h2>更新批次与日报</h2><p>本地推荐和网站选中项在此汇总。记录决定、待办及发布去向；生成正文不等于已经送达日报。</p>
 {list.data?.notice&&<p role="status" className="error-text">{list.data.notice}</p>}
 {(error||list.error||detail.error)&&<p role="alert">{error||list.error||detail.error}</p>}
 <div className="platform-actions"><button className="button" disabled={busy} onClick={()=>run(async()=>{const b=await send<Obj>(api+'/batches',{});setActive(b.id);})}>创建今日批次</button><button className="button" disabled={busy||!selected} onClick={()=>run(()=>send(api+'/batches/'+selected+'/intake',{}))}>接入网站已选候选</button><button className="text-button" onClick={()=>{list.reload();detail.reload();}}>刷新批次</button></div>
 <label>查看批次<select value={selected} onChange={e=>setActive(e.target.value)}><option value="">尚无批次</option>{list.data?.items.map((b:Obj)=><option key={b.id} value={b.id}>{b.title} · {labels[b.delivery_state]||b.delivery_state}</option>)}</select></label>
 {!!list.data?.due.length&&<p>到期复查 {list.data.due.length} 项：{list.data.due.map((t:Obj)=>t.proposal.title).join('、')}</p>}
 {detail.data&&<><SelectionReview key={selected} batch={selected}/><p>日报状态：{labels[detail.data.delivery_state]}；{detail.data.updated_at||detail.data.created_at}</p>{detail.data.receipt&&<p>交付凭据：{detail.data.receipt}</p>}<p className="muted">只有实际核实后的消息标识或交付记录才能确认送达。此处不会自动发送消息。</p>
 {detail.data.items.length===0&&<p>本批暂无推荐。可接入已选候选，或由本地整理流程写入提案。</p>}
 {detail.data.items.map((t:Obj)=><Topic key={t.id+':'+t.version} topic={t} busy={busy} run={run} open={open}/>)}
 </>}
 </section>;
}
function Topic({topic:t,busy,run,open}:{topic:Obj;busy:boolean;run:(f:()=>Promise<unknown>)=>Promise<void>;open:(kind:string,id:string)=>void}){
 const [note,setNote]=useState(''),[review,setReview]=useState(''),[kind,setKind]=useState(t.kind||'watch'),[type,setType]=useState('tool'),[target,setTarget]=useState(t.item_id||'');
 const decide=(decision:string)=>run(()=>send(api+'/topics/'+t.id+'/decide',{version:t.version,decision,review_on:review,note}));
 return <article className="management-candidate"><h3>{t.proposal.title}</h3><p>{t.proposal.reason}</p><p>{t.proposal.summary}</p><p>处理状态：{labels[t.decision]||t.decision}{t.review_on?' · 复查 '+t.review_on:''}</p><a href={t.event_url} target="_blank" rel="noreferrer">核对原始出处 ↗</a>
 <details><summary>具体上站提案</summary><pre className="management-json-preview">{JSON.stringify(t.proposal,null,2)}</pre></details>
 <label>决定备注<input value={note} onChange={e=>setNote(e.target.value)}/></label><label>稍后复查日期<input type="date" value={review} onChange={e=>setReview(e.target.value)}/></label>
 <div className="platform-actions"><button className="button" disabled={busy} onClick={()=>decide('continue')}>继续整理</button><button className="button" disabled={busy||!review} onClick={()=>decide('later')}>稍后</button><button className="text-button" disabled={busy} onClick={()=>decide('declined')}>不采用</button></div>
 {t.decision==='continue'&&<fieldset><legend>关联内容草稿</legend><label>放置位置<select value={kind} onChange={e=>setKind(e.target.value)}><option value="watch">持续关注</option><option value="news">近期动态</option></select></label><label>资源类型<select value={type} onChange={e=>setType(e.target.value)}>{['model','tool','agent','skill','harness'].map(x=><option key={x}>{x}</option>)}</select></label><label>已有内容编号（新增留空）<input value={target} onChange={e=>setTarget(e.target.value)}/></label><button className="button" disabled={busy} onClick={()=>run(async()=>{const r=await send<Obj>(api+'/topics/'+t.id+'/attach',{version:t.version,kind,type,target_id:target});open(r.kind,r.id);})}>进入内容整理</button></fieldset>}
 {t.item_id&&<p>关联 {t.item_id} · <button className="text-button" onClick={()=>open(t.kind,t.item_id)}>查看内容与发布历史</button>{t.decision==='published'&&<a href={'/for-you#'+(t.kind==='news'?'news-':'watch-')+t.item_id.toLowerCase()}>查看网站</a>}</p>}
 <details><summary>决定与处理记录</summary>{t.history.map((h:Obj,i:number)=><p key={i}>{h.created_at} · {h.action}<br/>{h.payload}</p>)}</details></article>;
}

function SelectionReview({batch}:{batch:string}){
 const [offset,setOffset]=useState(0),[focus,setFocus]=useState<Obj|null>(null),[outcome,setOutcome]=useState('investigate'),[reason,setReason]=useState(''),[sources,setSources]=useState(''),[error,setError]=useState(''),[busy,setBusy]=useState(false);
 const data=useRemote<Obj>(api+'/batches/'+batch+'/selection?offset='+offset,true);
 return <details className="management-manual"><summary>日报选题检查{data.data?' · '+data.data.unreviewed+' 项重要线索未记录':''}</summary><p>检查已选、热门待核验、反复出现与积压线索。这里只记录编辑判断，不代替用户决定，也不创建草稿。</p><p>{data.data?.scope}</p>{(error||data.error)&&<p role="alert">{error||data.error}</p>}{data.data&&<p role="status">共 {data.data.total} 项线索，待后续处理的积压 {data.data.backlog} 项；{data.data.required} 项须说明处理结果；{data.data.ready?'重要线索检查已齐，仍需实际交付日报。':'先补齐以下线索的处理理由。'}</p>}
 {data.data?.items.map((c:Obj)=><article className="management-candidate" key={c.ref}><h4>{c.title}</h4><p>{c.reasons.join('；')||'近期线索，供本地主动选题检查'}</p><p>{c.review?'已记录：'+c.review.reason:c.review_stale?'证据变化，请重新核对':c.required?'未记录处理结果':'可继续调查'}</p><a href={c.url} target="_blank" rel="noreferrer">核对来源 ↗</a><button className="button" onClick={()=>{setFocus(c);setReason(c.review?.reason||'');setSources(c.review?.sources?.join('\n')||'');setOutcome(c.review?.outcome||'investigate');}}>记录选题结果</button></article>)}
 <div className="platform-actions"><button className="button" disabled={offset===0} onClick={()=>setOffset(Math.max(0,offset-30))}>上一页线索</button><button className="button" disabled={data.data?.next_offset==null} onClick={()=>setOffset(data.data?.next_offset??offset)}>下一页线索</button></div>
 {focus&&<fieldset><legend>{focus.title}</legend><label>编辑判断<select value={outcome} onChange={e=>setOutcome(e.target.value)}><option value="investigate">继续核验，并在日报说明缺口</option><option value="recommend">推荐给用户确认</option><option value="not_recommended">暂不推荐，说明理由</option><option value="already_covered">已报道或重复，说明对应内容</option></select></label><label>具体理由或尚缺材料<textarea value={reason} onChange={e=>setReason(e.target.value)}/></label><label>实际核对的来源链接，每行一个<textarea value={sources} onChange={e=>setSources(e.target.value)}/></label><button className="button" disabled={busy||!reason.trim()} onClick={async()=>{setBusy(true);setError('');try{await send(api+'/batches/'+batch+'/selection-review',{ref:focus.ref,evidence_fingerprint:focus.evidence_fingerprint,outcome,reason,sources:sources.split('\n').map(s=>s.trim()).filter(Boolean)});setFocus(null);data.reload();}catch(e){setError((e as Error).message);}finally{setBusy(false);}}}>保存选题记录</button></fieldset>}
 </details>
}
