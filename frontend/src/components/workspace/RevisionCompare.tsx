import { useEffect, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { request, useRemote } from '../../api/knowledge';
import { useWorkspace } from './UI';
type Obj=Record<string,any>;
const names:Record<string,string>={name:'名称',type:'类型',introduction:'介绍',blocks:'版本与事实资料',interpretation:'编辑解读',sources:'出处',aliases:'别名',attention:'关注依据',materials:'原文材料',submission:'投稿信息'};
export function RevisionCompare({id}:{id:string}) {
  const {pick,notify}=useWorkspace(),[params,setParams]=useSearchParams();
  const history=useRemote<Obj>('/v1/platform/content/'+id+'/revisions?limit=100');
  const [older,setOlder]=useState(''),[newer,setNewer]=useState(''),[unchanged,setUnchanged]=useState(false),[rows,setRows]=useState<Obj[]>([]),[next,setNext]=useState<number|null>(null),[error,setError]=useState('');
  useEffect(()=>{if(history.data){setRows(history.data.items);setNext(history.data.next_offset);setOlder(params.get('compare_from')||String(history.data.items[1]?.revision||''));setNewer(params.get('compare_to')||String(history.data.items[0]?.revision||''));}},[history.data,params]);
  const comparison=useRemote<Obj>(older&&newer?'/v1/platform/content/'+id+'/compare?'+new URLSearchParams({from_revision:older,to_revision:newer,include_unchanged:String(unchanged)}):null);
  const choose=(a:string,b:string)=>{const nextParams=new URLSearchParams(params);nextParams.set('compare_from',a);nextParams.set('compare_to',b);setParams(nextParams,{replace:true});};
  return <details className="revision-compare" id={'revisions-'+id.toLowerCase()} open={params.has('compare_from')}><summary>{pick('资料修订对照','Compare dossier revisions')}</summary>
    <p>{pick('对照本站已审资料；修订编号与上游软件版本分开。迁移基线时间不是原发布日期。','Compare reviewed FieldToFit dossiers. Revision IDs are separate from upstream versions; migration baselines are not original publication dates.')}</p>
    {history.loading&&<p role="status">{pick('正在读取历史…','Loading history…')}</p>}
    {history.data&&rows.length<2&&<p>{pick('尚未保存两次可公开修订，暂不能对照。','Two readable public revisions have not yet been recorded.')}</p>}
    {rows.length>=2&&<><div className="compare-controls">{[['较早修订','Earlier revision',older,true],['较新修订','Later revision',newer,false]].map(([zh,en,value,isOlder])=><label key={String(zh)}>{pick(String(zh),String(en))}<select aria-label={pick(String(zh),String(en))} value={String(value)} onChange={e=>choose(isOlder?e.target.value:older,isOlder?newer:e.target.value)}>{rows.map(r=><option value={r.revision} key={r.revision}>r{r.revision} · {r.date_basis==='migration_baseline'?pick('迁移基线','Migration baseline'):new Date(r.recorded_at).toLocaleString(pick('zh-CN','en-GB'),{timeZone:'Asia/Shanghai'})}</option>)}</select></label>)}</div>
      <label className="check-control"><input type="checkbox" checked={unchanged} onChange={e=>setUnchanged(e.target.checked)}/>{pick('同时显示未变化字段','Include unchanged fields')}</label>
      {comparison.loading&&<p role="status">{pick('正在对照…','Comparing…')}</p>}
      {comparison.data&&<><p>r{comparison.data.from.revision} → r{comparison.data.to.revision}</p>
        {comparison.data.fields.length===0&&<p>{pick('此范围没有公开字段差异。','No public field differences in this range.')}</p>}
        {comparison.data.fields.map((f:Obj)=><section className="revision-field" key={f.field}><h4>{pick(names[f.field]||f.field,f.field)} · {f.kind==='unchanged'?pick('未变化','Unchanged'):f.kind==='added'?pick('新增','Added'):f.kind==='removed'?pick('移除','Removed'):pick('修改','Modified')}</h4>{f.kind!=='unchanged'&&<p className="muted">{f.classification==='editorial'?pick('介绍／解读文字变化，事实影响请核对出处','Editorial text changed; verify factual implications at the source'):pick('资料字段变化，实际产品变化请核对出处','Source data change; check citations for actual product changes')}</p>}<div className="revision-values"><div><h5>{pick('较早内容','Before')}</h5><DisplayValue field={f.field} value={f.before}/><Sources items={f.before_sources}/></div><div><h5>{pick('较新内容','After')}</h5><DisplayValue field={f.field} value={f.after}/><Sources items={f.after_sources}/></div></div></section>)}
        <div className="platform-actions"><button className="button" onClick={async()=>{const url=new URL(comparison.data!.share_path,location.origin).href;try{await navigator.clipboard.writeText(url);notify(pick('对照链接已复制','Comparison link copied'));}catch{notify(url);}}}>{pick('复制对照链接','Copy comparison link')}</button><button className="button" onClick={()=>{const url=URL.createObjectURL(new Blob([JSON.stringify(comparison.data,null,2)],{type:'application/json'}));const a=document.createElement('a');a.href=url;a.download=id+'-revision-comparison.json';a.click();URL.revokeObjectURL(url);}}>{pick('下载对照资料','Download comparison')}</button></div>
      </>}
    </>}
    {next!==null&&<button className="button" onClick={async()=>{try{const result=await request<Obj>('/v1/platform/content/'+id+'/revisions?limit=100&offset='+next);setRows(prev=>[...prev,...result.items]);setNext(result.next_offset);}catch(e){setError((e as Error).message);}}}>{pick('读取更早历史','Read earlier history')}</button>}
    {(error||history.error||comparison.error)&&<div role="alert"><p>{error||history.error||comparison.error}</p><button className="button" onClick={()=>{setError('');history.reload();comparison.reload();}}>{pick('重试','Retry')}</button></div>}
  </details>;
}
function Sources({items}:{items:Obj[]}) {return <ul>{items.map((s,i)=><li key={i}><a href={s.url} target="_blank" rel="noreferrer">{s.title} ↗</a></li>)}</ul>;}

function DisplayValue({field,value}:{field:string;value:any}) {
  const {pick}=useWorkspace();
  if(value===null||value===undefined)return <p>—</p>;
  if(typeof value==='string')return <p className="revision-prose">{value}</p>;
  if(field==='aliases')return <p>{value.join('、')||'—'}</p>;
  if(field==='blocks')return <>{value.map((block:Obj,i:number)=>block.kind==='paragraph'?<p className="revision-prose" key={i}>{block.text}</p>:<div className="watch-table-scroll" key={i} tabIndex={0} role="region" aria-label={pick('对照资料表','Compared data table')}><table className="watch-table"><thead><tr>{block.columns.map((column:string,j:number)=><th key={j} scope="col">{column}</th>)}</tr></thead><tbody>{block.rows.map((row:string[],r:number)=><tr key={r}>{row.map((cell,c)=><td key={c}>{cell}</td>)}</tr>)}</tbody></table></div>)}</>;
  if(field==='interpretation')return <>{value.map((point:Obj,i:number)=><div key={i}><strong>{point.title}</strong><p className="revision-prose">{point.text}</p>{point.locator&&<p>{point.locator}</p>}</div>)}</>;
  if(field==='sources')return <Sources items={value}/>;
  if(field==='materials')return <ul>{value.map((m:Obj,i:number)=><li key={i}>{m.coverage==='withdrawn'?pick('材料读取权限已撤回','Material reading permission withdrawn'):<><strong>{m.title}</strong> · {m.coverage==='full_text'?pick('全文可读','Full text'):m.coverage==='excerpt'?pick('部分可读','Excerpt'):pick('仅链接／不可读','Link only / unreadable')}<p>{m.locator} · {m.checked_at}</p><a href={m.url} target="_blank" rel="noreferrer">{pick('原始出处','Original source')} ↗</a>{m.reason&&<p>{m.reason}</p>}</>}</li>)}</ul>;
  return <pre className="platform-original">{JSON.stringify(value,null,2)}</pre>;
}
