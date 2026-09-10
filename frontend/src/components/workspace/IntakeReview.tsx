import { useState } from 'react';
import { request, send, useRemote } from '../../api/knowledge';
import { useWorkspace } from './UI';

type Intake = {schema_version:string;items:{id:string;name:string;observed_at:string;gaps:string[]}[]};
type Evidence = {quote:string;source_url:string};
type Preview = {object:{name:string;introduction:string;facts:Record<string,{value:unknown;quote?:string;status:string;source_url?:string}>;
  roles:{type:string;evidence:Evidence}[];attention:{explanation:string;evidence:Evidence}[];
  materials:{id:string;title:string;coverage:string;characters:number;note:string;source_url:string}[]};gate:{ready:boolean;errors:string[]}};

export default function IntakeReview() {
  const {pick} = useWorkspace();
  const jobs = useRemote<Intake>('/v1/admin/platform/intake?limit=100', true);
  const [drafts,setDrafts] = useState<Record<string,unknown>[]>([]);
  const [selected,setSelected] = useState(0);
  const [preview,setPreview] = useState<Preview|null>(null);
  const [error,setError] = useState('');
  const [busy,setBusy] = useState(false);
  const [notice,setNotice] = useState('');
  const labels:Record<string,string> = {capabilities:pick('公开能力','Capabilities'),limitations:pick('限制与未知','Limitations'),cost:pick('成本','Cost'),hardware:pick('硬件条件','Hardware'),license:pick('许可','License'),access:pick('访问方式','Access')};
  const download = async () => {
    setBusy(true);setError('');
    try {
      const data = await request<Intake>('/v1/admin/platform/intake?limit=100',{},true);
      const url = URL.createObjectURL(new Blob([JSON.stringify(data,null,2)],{type:'application/json'}));
      const a = document.createElement('a');a.href=url;a.download='fieldtofit-editorial-intake.json';a.click();
      setTimeout(()=>URL.revokeObjectURL(url),1000);
    } catch(e) {setError((e as Error).message);} finally {setBusy(false);}
  };
  const act = async (publish:boolean) => {
    setBusy(true);setError('');setNotice('');
    try {
      const result = await send<Preview>('/v1/admin/platform/intake/'+(publish?'publish':'review'),drafts[selected],'POST',true);
      setPreview(result);
      if(publish) {setNotice(pick('已发布，两个页面和 MCP 使用同一版本。','Published to both pages and MCP.'));setPreview(null);setDrafts(ds=>ds.filter((_,i)=>i!==selected));setSelected(0);jobs.reload();}
    } catch(e) {setError((e as Error).message);setPreview(null);} finally {setBusy(false);}
  };
  return <section className="ops-form"><h2>{pick('采集与本地 AI 整理','Collection and local AI organization')}</h2>
    <p>{pick('服务器保存原文。导出给本地 AI 整理后，导入稿件并核对内容；发布前，网站保留上次审核版本。','Export captured originals for local AI organization, import the draft and review it. The previous publication remains available until publication.')}</p>
    {(error||jobs.error) && <p role="alert" className="error-text">{error||jobs.error}</p>}{notice && <p role="status">{notice}</p>}
    <p>{pick('待整理','Pending organization')}：{jobs.data?.items.length ?? '—'}{jobs.data?.items.length===100 && pick('（本次最多展示 100 项）',' (up to 100 per export)')}</p>
    <div className="platform-actions"><button className="button" disabled={busy} onClick={download}>{pick('导出待整理原文','Export captured originals')}</button><button className="button subtle" onClick={jobs.reload}>{pick('刷新','Refresh')}</button></div>
    <label>{pick('导入本地 AI 整理稿（JSON）','Import a local AI draft (JSON)')}<input type="file" accept="application/json,.json" disabled={busy} onChange={async e=>{
      setError('');setPreview(null);setNotice('');
      const file=e.target.files?.[0];if(!file)return;
      try {if(file.size>2500000)throw Error(pick('稿件过大，请分批导入。','Draft too large; split the batch.'));
        const data=JSON.parse(await file.text());const entries=data.drafts||[data];
        if(!Array.isArray(entries)||!entries.length||entries.some((d:Record<string,unknown>)=>!d||d.schema_version!=='metis.editorial.v1'))throw Error(pick('稿件格式不正确。','Invalid editorial draft format.'));
        setDrafts(entries);setSelected(0);
      }catch(err){setError((err as Error).message);setDrafts([]);}
    }}/></label>
    {!!drafts.length && <><label>{pick('选择稿件','Choose draft')}<select value={selected} disabled={busy} onChange={e=>{setSelected(Number(e.target.value));setPreview(null);}}>{drafts.map((d,i)=><option key={i} value={i}>{String(d.introduction||d.id).slice(0,75)}</option>)}</select></label>
      <button className="button" disabled={busy} onClick={()=>act(false)}>{pick('核对引文并预览','Validate quotations and preview')}</button>
      {preview && <><h3>{preview.object.name}</h3><p>{preview.object.introduction}</p>
        {Object.entries(preview.object.facts).map(([key,f])=><div key={key}><strong>{labels[key]||key}</strong><p>{f.status==='unknown'?pick('未知','Unknown'):typeof f.value==='string'?f.value:JSON.stringify(f.value)}</p>{f.quote&&<blockquote>{f.quote}</blockquote>}{f.source_url&&<a href={f.source_url} target="_blank" rel="noreferrer">{pick('核对官方来源','Check official source')}</a>}</div>)}
        <h4>{pick('对象类型与依据','Object roles and evidence')}</h4>{preview.object.roles.map(r=><div key={r.type}><strong>{r.type}</strong><blockquote>{r.evidence.quote}</blockquote></div>)}
        <h4>{pick('关注依据','Reasons for inclusion')}</h4>{preview.object.attention.map((a,i)=><div key={i}><p>{a.explanation}</p><blockquote>{a.evidence.quote}</blockquote><a href={a.evidence.source_url} target="_blank" rel="noreferrer">{pick('核对来源','Check source')}</a></div>)}
        <h4>{pick('AI 能读取的材料','Materials available to AI')}</h4>{preview.object.materials.map(m=><div key={m.id}><a href={m.source_url} target="_blank" rel="noreferrer">{m.title}</a><p>{m.coverage==='full_text'?pick('文件全文','Full file text'):pick('摘录','Excerpt')} · {m.characters} {pick('字符','characters')} · {m.note}</p></div>)}
        <button className="button primary" disabled={busy||!preview.gate.ready} onClick={()=>act(true)}>{pick('核对完成，发布此稿','Reviewed — publish this draft')}</button></>}
    </>}
  </section>;
}
