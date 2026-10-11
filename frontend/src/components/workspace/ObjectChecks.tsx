import { useEffect, useState } from 'react';
import { send, useRemote } from '../../api/knowledge';
type Obj = Record<string, any>;
const api = '/v1/admin/workspace/object-checks';
const today = () => new Date().toLocaleDateString('sv-SE', {timeZone:'Asia/Shanghai'});
const labels: Record<string,string> = {changed:'有变化',unchanged:'未发现变化',failed:'失败',incomplete:'未完成'};
const handlingLabels: Record<string,string> = {pending:'恢复待处理',declined:'不采纳',evidence_withdrawn:'证据已撤回'};
export function ObjectChecks() {
  const [day,setDay]=useState(today()), [filter,setFilter]=useState(''), [error,setError]=useState(''), [busy,setBusy]=useState('');
  const data=useRemote<Obj>(api+'?day='+day,true);
  const [snapshot,setSnapshot]=useState<Obj|null>(null);
  useEffect(()=>{if(data.data)setSnapshot(data.data);},[data.data]);
  const board=snapshot?.day===day?snapshot:null;
  const act=async(action:()=>Promise<unknown>,key:string) => {
    setBusy(key);setError('');
    try {await action();data.reload();} catch(e) {setError((e as Error).message);} finally {setBusy('');}
  };
  return <section className="platform-panel object-checks"><h2>对象每日核对</h2>
    <p>按全部已发布档案核对官方资料。未处理差异跨日保留；已处置的相同证据不重复进入待办，新证据核对后重新进入。检查与差异处置均不发布内容。</p>
    <div className="platform-actions"><label>核对日期<input type="date" value={day} max={today()} onChange={e=>setDay(e.target.value)}/></label>
      <button className="button" disabled={!!busy||data.loading||!!data.error||day!==today()} onClick={()=>act(()=>send(api,{day},'POST',true),'start')}>建立今日全对象清单</button>
      <button className="button" onClick={data.reload}>刷新台账</button></div>
    {(error||data.error)&&<p role="alert">{error||data.error}</p>}
    {board&&<><div className="review-summary">{[['expected','应检查'],['completed','已完成'],...Object.entries(labels)].map(([key,label])=><div key={key}><span>{label}</span><strong>{board!.totals[key]}</strong></div>)}</div>
      {!board.created_at&&<p>当天尚未建立清单，不能将空记录判为无变化。</p>}
      <label>检查结果<select value={filter} onChange={e=>setFilter(e.target.value)}><option value="">全部结果</option>{Object.entries(labels).map(([key,label])=><option key={key} value={key}>{label}</option>)}</select></label>
      {board.handling_available===false&&<p role="alert">差异处置记录尚未初始化，请先初始化维护记录并重试；原核对记录保留。</p>}
      {board.items.filter((r:Obj)=>!filter||r.status===filter).map((row:Obj)=><CheckRow key={day+row.id} row={row} day={day} handlingEnabled={board.handling_available!==false} disabled={!!busy||data.loading||!!data.error||day!==today()} act={act}/>)}
    </>}
  </section>;
}
function CheckRow({row,day,disabled,handlingEnabled,act}:{row:Obj;day:string;disabled:boolean;handlingEnabled:boolean;act:(fn:()=>Promise<unknown>,key:string)=>Promise<void>}) {
  const [reason,setReason]=useState(''), [completed,setCompleted]=useState(false), [field,setField]=useState('introduction'), [after,setAfter]=useState(''), [quote,setQuote]=useState(''), [url,setUrl]=useState(row.entries[0]?.url||''), [notice,setNotice]=useState('');
  const [entries,setEntries]=useState(JSON.stringify(row.plan_entries_current,null,2));
  const [sourceDate,setSourceDate]=useState(''),[upstreamVersion,setUpstreamVersion]=useState('');
  useEffect(()=>{setReason('');setCompleted(false);setAfter('');setQuote('');},[row.attempt_id]);
  useEffect(()=>{setEntries(JSON.stringify(row.plan_entries_current,null,2));},[row.plan_version_current]);
  const findingState=JSON.stringify(row.latest.changes?.map((c:Obj)=>[c.difference_id,c.handling_version]));
  useEffect(()=>{setNotice('');},[findingState]);
  const baseline=row.latest.baseline;
  const allFetched=!!row.latest.observations?.length&&row.latest.observations.every((r:Obj)=>!r.required||r.fetched);
  const review=async()=>{
    let changes:Obj[]=[];
    if(after.trim()) {
      let before:any=baseline;
      for(const key of field.split('.'))before=before?.[key];
      if(before===undefined)throw new Error('字段不在当前档案中');
      changes=[{field,before,after:typeof before==='string'?after:JSON.parse(after),quote,source_url:url,source_date:sourceDate||null,upstream_version:upstreamVersion}];
    }
    await send(api+'/'+row.id+'/review',{day,attempt_id:row.attempt_id,reason,completed,changes},'POST',true);
  };
  return <details className="check-row"><summary>{row.name} · {labels[row.status]}{row.latest.changes?.length?' · '+row.latest.changes.length+'项待更新':''}</summary>
    <p>{row.id} · 最近尝试 {row.last_attempt||'未记录'}</p>{row.baseline_changed&&<p role="status">已审档案已经变化，请按当前版本重新获取并核对。</p>}
    <ul>{row.entries.map((e:Obj)=><li key={e.url}><a href={e.url} target="_blank" rel="noreferrer">{e.title}</a> · {e.required?'必要入口':'补充入口'} · {e.scope}</li>)}</ul>
    <button className="button" disabled={disabled} onClick={()=>act(()=>send(api+'/'+row.id+'/scan',{day},'POST',true),row.id)}>获取／重试官方入口</button>
    {row.latest.observations?.map((e:Obj)=><details key={e.url}><summary>{e.title} · {e.fetched?'已获取，待核对':'获取失败'}</summary><p>{e.error||e.checked_at}</p>{e.body&&<pre className="platform-original">{e.body}</pre>}</details>)}
    {baseline&&<details><summary>本次对照的已审档案</summary><pre className="platform-original">{JSON.stringify(baseline,null,2)}</pre></details>}
    {!!row.latest.changes?.length&&<details open><summary>仍待处理的差异证据</summary>{row.latest.changes.map((c:Obj)=><div className="check-difference" key={c.difference_id}>
      <DifferenceEvidence change={c}/>{c.new_evidence_after_handling&&<p role="status">此前相同建议已有处置；本项含新的定位证据，重新进入待办。</p>}
      <DifferenceHandling change={c} row={row} day={day} disabled={disabled||!handlingEnabled||row.baseline_changed||!baseline} act={act}/>
    </div>)}</details>}
    {!!row.handled_changes?.length&&<details className="handled-differences"><summary>已处置差异 · {row.handled_changes.length}</summary><p>原证据与处理记录仍然保留。处置不会改写当天检查结果或公开档案；复查条件供后续核对使用。</p>
      {row.handled_changes.map((e:Obj)=><div className="check-difference" key={e.difference_id}><strong>{handlingLabels[e.data.status]}</strong><DifferenceEvidence change={e.data.change}/>
        <p>处理时间：{e.created_at}</p><p>处理理由：{e.data.reason}</p><p>复查条件：{e.data.recheck_condition}</p>
        {e.reopen_notice&&<p>{e.reopen_notice}</p>}
        <DifferenceHandling change={{...e.data.change,difference_id:e.difference_id,handling_version:e.version}} row={row} day={day} reopen disabled={disabled||!handlingEnabled||row.baseline_changed||!baseline||!e.can_reopen} act={act}/>
      </div>)}</details>}
    {!!row.handling_history?.length&&<details className="difference-history"><summary>差异处置历史 · {row.handling_history.length}</summary>{[...row.handling_history].reverse().map((e:Obj)=><details key={e.id}><summary>{e.created_at} · {e.data.change.field} · {handlingLabels[e.data.status]}</summary>
      <DifferenceEvidence change={e.data.change}/><p>处理理由：{e.data.reason}</p><p>复查条件：{e.data.recheck_condition}</p><p>关联核对日：{e.data.day} · 处理版本：{e.version}</p>
    </details>)}</details>}
    {baseline&&<fieldset><legend>对照档案后的核对记录</legend><label>核对说明<textarea value={reason} onChange={e=>setReason(e.target.value)}/></label>
      <label className="check-control"><input type="checkbox" checked={completed} disabled={!allFetched} onChange={e=>setCompleted(e.target.checked)}/>已完成全部必要入口的档案核对</label>
      <details><summary>登记一项字段差异</summary><label>变化字段<input value={field} onChange={e=>setField(e.target.value)}/></label><label>建议新值<textarea value={after} onChange={e=>setAfter(e.target.value)}/></label>
        <label>依据入口<select value={url} onChange={e=>setUrl(e.target.value)}>{row.entries.map((e:Obj)=><option key={e.url} value={e.url}>{e.title}</option>)}</select></label><label>本次原文中的定位引文<textarea value={quote} onChange={e=>setQuote(e.target.value)}/></label>
        <label>来源发布日期（未知留空）<input type="date" max={today()} value={sourceDate} onChange={e=>setSourceDate(e.target.value)}/></label><label>来源版本（有依据才填）<input value={upstreamVersion} onChange={e=>setUpstreamVersion(e.target.value)}/></label>
      </details><button className="button" disabled={disabled||!reason.trim()} onClick={()=>act(review,row.id)}>保存核对记录</button>
    </fieldset>}
    {!!row.latest.changes?.length&&row.latest.reviewed_at&&<button className="button" disabled={disabled||row.baseline_changed} onClick={()=>act(async()=>{await send(api+'/'+row.id+'/proposal',{day},'POST',true);setNotice('已准备私密更新提案，内容确认后再创建草稿。');},row.id)}>准备档案更新提案</button>}
    {notice&&<p role="status">{notice}</p>}
    <details><summary>重试与核对历史 · {row.history.length}</summary>{row.history.map((h:Obj)=><p key={h.id}>{h.created_at} · {labels[h.data.status]} · {h.data.reason}</p>)}</details>
    <details><summary>调整下一批官方入口计划</summary><p>当前日清单保持冻结；这里保存的入口用于下一批。每入口填写url、title、required和scope。</p><label>入口计划<textarea rows={8} value={entries} onChange={e=>setEntries(e.target.value)}/></label><button className="button" disabled={disabled} onClick={()=>act(()=>send(api+'/'+row.id+'/plan',{entries:JSON.parse(entries),version:row.plan_version_current},'PATCH',true),row.id)}>保存下一批入口</button></details>
  </details>;
}

function DifferenceEvidence({change}:{change:Obj}) {
  return <div className="difference-evidence"><strong>{change.field}</strong><p>{JSON.stringify(change.before)} → {JSON.stringify(change.after)}</p><blockquote>{change.quote}</blockquote>
    <a href={change.source_url} target="_blank" rel="noreferrer">官方依据</a><p>来源日期：{change.source_date||'未知'} · 来源版本：{change.upstream_version||'未知'}</p>
    <details><summary>原证据定位</summary><p>引文起点：{change.offset??'未知'}</p><p>原文指纹：{change.content_hash||'未知'}</p></details>
  </div>;
}

function DifferenceHandling({change,row,day,reopen=false,disabled,act}:{change:Obj;row:Obj;day:string;reopen?:boolean;disabled:boolean;act:(fn:()=>Promise<unknown>,key:string)=>Promise<void>}) {
  const [status,setStatus]=useState('declined'),[reason,setReason]=useState(''),[condition,setCondition]=useState('');
  useEffect(()=>{setReason('');setCondition('');},[change.difference_id,change.handling_version]);
  return <fieldset className="difference-handling" disabled={disabled}><legend>{reopen?'恢复这条差异':'处理这条差异'}</legend>
    {!reopen&&<label>处理决定<select value={status} onChange={e=>setStatus(e.target.value)}><option value="declined">不采纳</option><option value="evidence_withdrawn">证据已撤回</option></select><span className="muted">“证据已撤回”须核实来源撤回或更正；访问失败仍按来源失败记录。</span></label>}
    <label>{reopen?'恢复理由':'处理理由'}<textarea value={reason} onChange={e=>setReason(e.target.value)} maxLength={2000}/></label>
    {!reopen&&<label>复查条件<textarea value={condition} onChange={e=>setCondition(e.target.value)} maxLength={2000}/><span className="muted">例如官方发布新版本或更正原文；新证据需实际核对，也可手动恢复。</span></label>}
    <button className="button" disabled={disabled||!reason.trim()||(!reopen&&!condition.trim())} onClick={()=>act(()=>send(api+'/'+row.id+'/handle',{
      day,attempt_id:row.attempt_id,difference_id:change.difference_id,version:change.handling_version,
      status:reopen?'pending':status,reason,recheck_condition:condition
    },'POST',true),row.id)}>{reopen?'恢复待处理':'保存差异处置'}</button>
  </fieldset>;
}
