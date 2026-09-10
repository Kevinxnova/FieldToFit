import { useState } from 'react';
import { Link } from 'react-router-dom';
import { request, send, useRemote } from '../../api/knowledge';
import { SourceLink, useWorkspace } from './UI';

type Entry = { object_id: string; revision: number; summary: string; significance: string; material_id: string; quote: string };
type Draft = { title: string; period_start: string; period_end: string; entries: Entry[] };
type Preview = { id: string; revision: number; draft: Draft; published_revision: number | null; review_token: string; gate: {ready: boolean; errors: string[]} };
type Selection = { revision: number; unavailable?: boolean; object: { id: string; name: string; introduction: string; attention: {explanation: string; evidence: {material_id: string; quote: string; source_url: string}}[]; materials: {id: string; title: string; source_url: string}[] } };
function blank(): Draft {
  const today = new Intl.DateTimeFormat('sv-SE', {timeZone:'Asia/Shanghai'}).format(new Date());
  return {title:'',period_start:today,period_end:today,entries:[]};
}

export default function EditionReview() {
  const { pick } = useWorkspace();
  const list = useRemote<{items: {id:string;title:string;revision:number;published_revision:number|null}[]}>('/v1/admin/platform/editions',true);
  const selections = useRemote<{items:Selection[];total:number}>('/v1/admin/platform/selections?limit=100',true);
  const [preview, setPreview] = useState<Preview | null>(null);
  const [draft, setDraft] = useState<Draft>(blank);
  const [selected, setSelected] = useState('');
  const [dirty, setDirty] = useState(false);
  const [reason, setReason] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const accept = (value:Preview) => {setPreview(value);setDraft(value.draft);setDirty(false);};
  const load = async (id:string) => {
    setBusy(true);setError('');
    try {accept(await request<Preview>('/v1/admin/platform/editions/'+id,{},true));setReason('');}
    catch(e){setError((e as Error).message);}finally{setBusy(false);}
  };
  const act = async (action:'save'|'published'|'withdrawn') => {
    setBusy(true);setError('');
    try {
      const path = '/v1/admin/platform/editions'+(preview ? '/'+preview.id : '');
      const value = action === 'save' ? await send<Preview>(path,{draft,expected_revision:preview?.revision ?? 0},preview ? 'PATCH':'POST',true)
        : await send<Preview>(path+'/transition',{state:action,review_token:preview!.review_token,reason},'POST',true);
      accept(value);list.reload();
    }catch(e){setError((e as Error).message);}finally{setBusy(false);}
  };
  const update = (next:Draft) => {setDraft(next);setDirty(true);};
  const editEntry = (index:number, patch:Partial<Entry>) => update({...draft,entries:draft.entries.map((e,i)=>i===index ? {...e,...patch}:e)});
  const add = () => {
    const pub = selections.data?.items.find(p=>p.object.id===selected);
    if (!pub || pub.unavailable || draft.entries.some(e=>e.object_id===selected)) return;
    const attention = pub.object.attention[0];
    update({...draft,entries:[...draft.entries,{object_id:selected,revision:pub.revision,summary:pub.object.introduction,significance:attention?.explanation || '',material_id:attention?.evidence.material_id || '',quote:attention?.evidence.quote || ''}]});setSelected('');
  };
  return <section className="edition-review" aria-label={pick('概览发布管理','Edition publishing')}>
    <h2>{pick('把重点整理成一期','Publish a reviewed overview')}</h2><p>{pick('只引用已审核的精选版本，按实际材料编写重点和关注理由。没有新内容时保留原期次，不自动修改日期。','Use reviewed publication revisions and source-backed highlights. Keep the previous edition when there is nothing new.')}</p>
    {list.error && <p role="alert">{list.error}</p>}
    <div className="platform-actions"><button className="button" disabled={busy} onClick={()=>{setPreview(null);setDraft(blank());setDirty(false);setError('');setReason('');}}>{pick('新建一期','New edition')}</button><button className="text-button" disabled={busy} onClick={()=>{list.reload();selections.reload();}}>{pick('刷新期次和精选','Refresh editions and selections')}</button></div>
    <ul className="edition-draft-list">{list.data?.items.map(item=><li key={item.id}><button className="text-button" disabled={busy} onClick={()=>load(item.id)}>{item.title || pick('未命名草稿','Untitled draft')} · {pick('草稿','Draft')} {item.revision} · {item.published_revision ? pick('有发布记录','Has publication history'):pick('未发布','Unpublished')}</button></li>)}</ul>
    {error && <p className="platform-notice" role="alert">{error}</p>}
    <fieldset className="ops-form" disabled={busy} style={{minWidth:0}}>
      <label>{pick('本期标题','Edition title')}<input value={draft.title} maxLength={160} onChange={e=>update({...draft,title:e.target.value})}/></label>
      <div className="platform-facts"><label>{pick('涵盖起日','Period starts')}<input type="date" value={draft.period_start} onChange={e=>update({...draft,period_start:e.target.value})}/></label><label>{pick('涵盖止日','Period ends')}<input type="date" value={draft.period_end} onChange={e=>update({...draft,period_end:e.target.value})}/></label></div>
      {selections.error && <p role="alert">{selections.error}</p>}
      <label>{pick('加入已审核对象','Add reviewed object')}<select value={selected} onChange={e=>setSelected(e.target.value)}><option value="">{pick('选择一个对象','Choose an object')}</option>{selections.data?.items.filter(p=>!p.unavailable && !draft.entries.some(e=>e.object_id===p.object.id)).map(p=><option key={p.object.id} value={p.object.id}>{p.object.name} · {pick('修订','Revision')} {p.revision}</option>)}</select></label>
      {(selections.data?.total || 0)>100 && <p>{pick('此处列最近 100 项，请先在资料审核中确认维护范围。','Showing the latest 100 selections. Confirm your maintained scope in record review.')}</p>}
      <button className="button" disabled={!selected || draft.entries.length>=5} onClick={add}>{pick('加入本期重点','Add highlight')}</button>
      {draft.entries.map((entry,index)=>{
        const pub=selections.data?.items.find(p=>p.object.id===entry.object_id);
        const material=pub?.object.materials.find(m=>m.id===entry.material_id);
        return <article className="platform-material" key={entry.object_id}>
          <h3>{index+1}. {pub?.object.name || entry.object_id} · {pick('固定修订','Fixed revision')} {entry.revision}</h3>
          <p><Link to={`/for-you?object=${entry.object_id}&revision=${entry.revision}`}>{pick('核对引用版本','Check referenced revision')}</Link></p>
          {pub && pub.revision!==entry.revision && <div className="platform-notice"><p>{pick('该对象有新的审核版本。更新引用后重新核对文案和引文。','A newer reviewed revision exists. Update the reference and recheck every claim.')}</p><button className="button" onClick={()=>editEntry(index,{revision:pub.revision,material_id:pub.object.attention[0]?.evidence.material_id || '',quote:pub.object.attention[0]?.evidence.quote || ''})}>{pick('更新引用到当前修订','Use current revision')}</button></div>}
          <label>{pick('本条重点','Highlight')}<textarea value={entry.summary} maxLength={800} onChange={e=>editEntry(index,{summary:e.target.value})}/></label>
          <label>{pick('为什么值得关注','Reason for attention')}<textarea value={entry.significance} maxLength={800} onChange={e=>editEntry(index,{significance:e.target.value})}/></label>
          <label>{pick('引用材料 ID','Quoted material ID')}<input value={entry.material_id} onChange={e=>editEntry(index,{material_id:e.target.value})}/></label>
          {material && <SourceLink url={material.source_url}>{material.title}</SourceLink>}
          <label>{pick('支撑重点的原句','Supporting source quotation')}<textarea value={entry.quote} maxLength={2000} onChange={e=>editEntry(index,{quote:e.target.value})}/></label>
          <div className="platform-actions"><button className="text-button" disabled={index===0} onClick={()=>{const entries=[...draft.entries];[entries[index-1],entries[index]]=[entries[index],entries[index-1]];update({...draft,entries});}}>{pick('上移','Move up')}</button><button className="text-button" onClick={()=>update({...draft,entries:draft.entries.filter((_,i)=>i!==index)})}>{pick('移出本期','Remove highlight')}</button></div>
        </article>;
      })}
      <label>{pick('本次概览审核依据','Edition review reason')}<textarea value={reason} onChange={e=>setReason(e.target.value)}/></label>
      <p>{pick('审核依据只进入后台记录，不公开为概览正文。','Review reasons are private audit notes, never public edition prose.')}</p>
    </fieldset>
    {preview && <div className="platform-panel" aria-live="polite"><h3>{pick('已保存草稿的发布检查','Saved draft publication checks')}</h3>{dirty && <p>{pick('存在未保存修改，请先保存再审核。','Save your changes before review.')}</p>}<p>{pick('草稿版本','Draft revision')} {preview.revision}</p>{preview.gate.ready ? <p>{pick('基础门槛通过，请核对重点、引文和时间范围后发布。','Basic checks passed. Verify highlights, quotations and dates before publishing.')}</p>:<ul>{preview.gate.errors.map((error,i)=><li key={i}>{error}</li>)}</ul>}
      {preview.published_revision && <Link to={`/for-you?edition=${preview.id}&edition_revision=${preview.published_revision}`}>{pick('检查公开期次或撤回状态','Check public edition or withdrawal status')}</Link>}
    </div>}
    <div className="platform-actions"><button className="button" disabled={busy || (!dirty && !!preview)} onClick={()=>act('save')}>{pick('保存概览草稿','Save edition draft')}</button><button className="button primary" disabled={busy || dirty || !preview?.gate.ready || !reason.trim()} onClick={()=>act('published')}>{pick('审核并发布本期','Review and publish edition')}</button><button className="button" disabled={busy || dirty || !preview?.published_revision || !reason.trim()} onClick={()=>act('withdrawn')}>{pick('撤回本期','Withdraw edition')}</button>{preview && <button className="text-button" disabled={busy} onClick={()=>load(preview.id)}>{pick('重新加载已保存概览','Reload saved edition')}</button>}</div>
  </section>;
}
