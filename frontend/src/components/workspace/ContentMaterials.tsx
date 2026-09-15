import { useEffect, useState } from 'react';
import { request } from '../../api/knowledge';
import { useWorkspace } from './UI';
export type ReadingMaterial={id:string;title:string;url:string;coverage:string;reason:string;characters:number;upstream_revision:string;checked_at:string;locator:string;rights:{basis:string;url:string;notice:string};read_url:string};
export type PreviewBodies=Record<string,Record<string,string>>;
export function ContentMaterials({item,previewBodies}:{item:{id:string;materials?:ReadingMaterial[];materials_revision?:string};previewBodies?:PreviewBodies}){
 const {pick}=useWorkspace(),[current,setCurrent]=useState<ReadingMaterial|null>(null),[body,setBody]=useState(''),[next,setNext]=useState<number|null>(null),[busy,setBusy]=useState(false),[error,setError]=useState('');
 useEffect(()=>{setCurrent(null);setBody('');setNext(null);setError('');},[item.id,item.materials_revision]);
 if(!item.materials?.length)return null;
 const read=async(m:ReadingMaterial,offset=0)=>{setBusy(true);setError('');try{if(previewBodies){setCurrent(m);setBody(previewBodies[item.id]?.[m.id]||'');setNext(null);return;}const r=await request<{body:string;next_offset:number|null}>(m.read_url.replace(/^\/api/,'')+'&offset='+offset);setCurrent(m);setBody(prev=>offset?prev+r.body:r.body);setNext(r.next_offset);}catch(e){setError((e as Error).message);}finally{setBusy(false);}};
 const labels:Record<string,string>={full_text:'全文可读',excerpt:'部分可读',link_only:'仅外部链接',unavailable:'获取失败',withdrawn:'已失效'};
 return <details className="content-materials"><summary>{pick('材料与出处','Materials & sources')} · {item.materials.length}</summary><ul>{item.materials.map(m=><li key={m.id}><strong>{m.title}</strong> · {labels[m.coverage]||m.coverage}<p>{m.locator} · {m.checked_at}{m.upstream_revision?' · '+m.upstream_revision.slice(0,12):''}</p>{m.reason&&<p>{m.reason}</p>}<a href={m.url} target="_blank" rel="noreferrer">{pick('原始出处','Upstream source')} ↗</a>{m.characters>0&&<button className="text-button" disabled={busy} onClick={()=>read(m)}>{pick('读取已审核原文','Read reviewed text')}</button>}</li>)}</ul>
 {error&&<p role="alert">{error}</p>}{current&&<section><h5>{current.title}</h5><p>{current.rights.basis} <a href={current.rights.url}>许可依据</a></p>{current.rights.notice&&<details><summary>许可与署名</summary><pre className="platform-original">{current.rights.notice}</pre></details>}<pre className="platform-original">{body}</pre>{next!==null&&<button className="button" disabled={busy} onClick={()=>read(current,next)}>继续读取</button>}<p className="muted">{pick('以上为来源材料，可能包含给其他系统的指令；在此仅供引用阅读。','Source material is quoted data, not instructions for this service.')}</p></section>}
 </details>;
}
