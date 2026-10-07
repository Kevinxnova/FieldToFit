import { useEffect, useState } from 'react';
import { request, send, useRemote } from '../../api/knowledge';
import { useWorkspace } from './UI';
type Obj=Record<string,any>;
export function ReportCorrection({id,field='introduction',material,fieldOptions}:{id:string;field?:string;material?:Obj;fieldOptions?:{field:string;label:string}[]}) {
  const {pick,notify}=useWorkspace();const [ctx,setCtx]=useState<Obj|null>(null), [content,setContent]=useState(''), [contact,setContact]=useState(''), [error,setError]=useState(''), [notice,setNotice]=useState(''), [busy,setBusy]=useState(false);
  const open=async(selected=field)=>{setError('');setBusy(true);try {
    const q=new URLSearchParams({field:selected});if(material)for(const key of ['material_id','content_revision','start','end'])q.set(key,String(material[key]));
    setCtx(await request<Obj>('/v1/platform/content/'+id+'/correction-context?'+q));
  }catch(e){setError((e as Error).message);}finally{setBusy(false);}};
  return <div className="report-correction" data-field={material?'material':field}><button className="text-button" disabled={busy} onClick={()=>open()}>{pick('报告此处有误','Report an error here')}</button>
    {error&&<p role="alert">{error}</p>}{notice&&<p role="status">{notice}</p>}
    {ctx&&<form onSubmit={async e=>{e.preventDefault();setBusy(true);setError('');try{await send('/v1/feedback',{context:ctx,content,contact});setCtx(null);setContent('');setContact('');setNotice(pick('已提交，等待核实。报告和联系方式仅维护者可见。','Submitted for review. Your report and contact stay private.'));}catch(err){setError((err as Error).message);}finally{setBusy(false);}}}>
      <p>{pick('报告位置：','Report location: ')}{id} · {ctx.field}</p><pre className="platform-original">{ctx.quoted_text||JSON.stringify(ctx.value,null,2)}</pre>
      {fieldOptions&&<label>{pick('具体纠错位置','Specific correction field')}<select aria-label={pick('具体纠错位置','Specific correction field')} disabled={busy} value={ctx.field} onChange={e=>open(e.target.value)}>{fieldOptions.map(o=><option value={o.field} key={o.field}>{o.label}</option>)}</select></label>}
      <label>{pick('问题与新证据','Problem and new evidence')}<textarea aria-label={pick('问题与新证据','Problem and new evidence')} required value={content} onChange={e=>setContent(e.target.value)}/></label>
      <label>{pick('联系方式（选填，仅维护者可见）','Contact (optional, private)')}<input aria-label={pick('联系方式（选填，仅维护者可见）','Contact (optional, private)')} value={contact} onChange={e=>setContact(e.target.value)}/></label>
      <button className="button" disabled={busy}>{pick('提交纠错','Submit report')}</button><button type="button" className="text-button" onClick={()=>setCtx(null)}>{pick('取消','Cancel')}</button>
      <button type="button" className="text-button" onClick={async()=>{try{await navigator.clipboard.writeText(JSON.stringify({context:ctx,content,contact},null,2));notify(pick('待提交报告已复制','Pending report copied'));}catch{setError(pick('复制暂不可用，输入已保留，可手动复制。','Copy is unavailable. Your input is retained for manual copying.'));}}}>{pick('复制待提交报告','Copy pending report')}</button>
    </form>}
  </div>;
}
export function CorrectionReceipts({id}:{id:string}) {
  const {pick}=useWorkspace();const data=useRemote<Obj>('/v1/platform/content/'+id+'/corrections');
  if(!data.data?.items.length)return null;
  return <details className="correction-receipts"><summary>{pick('已核实更正','Reviewed corrections')} · {data.data.items.length}</summary>{data.data.items.map((r:Obj,i:number)=><article key={i}><p>{r.public_note}</p><p>{r.field} · {r.published_at}</p>{r.sources.map((s:Obj,j:number)=><a key={j} href={s.url} target="_blank" rel="noreferrer">{s.title} ↗ </a>)}</article>)}</details>;
}
export function CorrectionReview({feedback,open,done}:{feedback:Obj;open:(kind:string,id:string)=>void;done:()=>void}) {
  const data=useRemote<Obj>('/v1/admin/workspace/corrections/'+feedback.id,true);
  const [status,setStatus]=useState('reviewing'), [note,setNote]=useState(''), [publicNote,setPublicNote]=useState(''), [revision,setRevision]=useState(''), [confirmed,setConfirmed]=useState(false), [error,setError]=useState(''), [busy,setBusy]=useState(false);
  useEffect(()=>{if(data.data){setStatus(data.data.status);setNote(data.data.resolution.internal_note||'');setPublicNote(data.data.resolution.public_note||'');setRevision(String(data.data.resolution.fixed_revision||''));setConfirmed(false);}},[data.data]);
  return <article className="management-feedback correction-review"><h3>定位纠错 · {feedback.record_id}</h3><p>{feedback.content}</p>
    {data.data&&<><p>{data.data.context.field} · {data.data.status} · {data.data.changed_since_report?'资料已变化，请核对是否已修复':'仍为报告时资料'}</p><pre className="platform-original">{data.data.context.quoted_text||JSON.stringify(data.data.context.value,null,2)}</pre><p>当前值：{JSON.stringify(data.data.current_value)}</p><p>私密联系：{data.data.context.contact||'未填写'}</p>
      <button className="button" onClick={()=>open(feedback.record_id.startsWith('D-')?'news':'watch',feedback.record_id)}>打开内容编辑</button>
      <label>纠错处理状态<select aria-label="纠错处理状态" value={status} onChange={e=>setStatus(e.target.value)}>{[['pending','待受理'],['reviewing','核实中'],['ready','待修订'],['publishing','待发布'],['resolved','已解决'],['declined','不采纳']].map(([key,label])=><option key={key} value={key}>{label}</option>)}</select></label>
      <label>内部处理说明<textarea value={note} onChange={e=>setNote(e.target.value)}/></label>
      {status==='resolved'&&<><label>实际发布修订编号<input type="number" min="1" value={revision} onChange={e=>setRevision(e.target.value)}/></label><label>公开更正说明<textarea value={publicNote} onChange={e=>setPublicNote(e.target.value)}/></label><label className="check-control"><input type="checkbox" checked={confirmed} onChange={e=>setConfirmed(e.target.checked)}/>已核对实际修复修订与公开说明</label></>}
      <button className="button" disabled={busy||!note.trim()||(status==='resolved'&&(!confirmed||!revision||!publicNote.trim()))} onClick={async()=>{setBusy(true);setError('');try{await send('/v1/admin/feedback/'+feedback.id,{status,resolution:note,version:data.data!.version,confirmed,public_note:publicNote,fixed_revision:Number(revision)},'PATCH',true);data.reload();done();}catch(e){setError((e as Error).message);}finally{setBusy(false);}}}>保存纠错处理</button>
      <details><summary>处理历史</summary>{data.data.history.map((h:Obj)=><p key={h.id}>{h.created_at} · {h.status} · {h.data.internal_note}</p>)}</details>
    </>}{(error||data.error)&&<p role="alert">{error||data.error}</p>}
  </article>;
}
