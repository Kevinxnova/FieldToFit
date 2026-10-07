import { trackAction } from './Traffic';
import { useEffect, useState } from 'react';
import { request } from '../../api/knowledge';
import { useWorkspace } from './UI';
import { ReportCorrection } from './Corrections';
export type ReadingMaterial={id:string;title:string;url:string;coverage:string;reason:string;characters:number;upstream_revision:string;checked_at:string;locator:string;rights:{basis:string;url:string;notice:string};read_url:string};
export type PreviewBodies=Record<string,Record<string,string>>;
type Obj=Record<string,any>;
export function ContentMaterials({item,previewBodies}:{item:{id:string;materials?:ReadingMaterial[];materials_revision?:string};previewBodies?:PreviewBodies}){
 const {pick,notify}=useWorkspace(),[current,setCurrent]=useState<ReadingMaterial|null>(null),[body,setBody]=useState(''),[next,setNext]=useState<number|null>(null),[busy,setBusy]=useState(false),[error,setError]=useState('');
 const [directory,setDirectory]=useState<Obj|null>(null),[locationId,setLocationId]=useState(''),[range,setRange]=useState({start:0,end:0});
 useEffect(()=>{setCurrent(null);setBody('');setNext(null);setError('');setDirectory(null);setLocationId('');},[item.id,item.materials_revision]);
 if(!item.materials?.length)return null;
 const read=async(m:ReadingMaterial,offset=0,selected='')=>{setBusy(true);setError('');try{
   if(previewBodies){setCurrent(m);setBody(previewBodies[item.id]?.[m.id]||'');setNext(null);setDirectory(null);return;}
   const path=m.read_url.replace(/^\/api/,'');
   const r=await request<Obj>(path+'&offset='+offset+(selected?'&location_id='+encodeURIComponent(selected):''));
   setCurrent(m);setBody(prev=>offset&&current?.id===m.id&&selected===locationId?prev+r.body:r.body);setNext(r.next_offset);setLocationId(selected);
   setRange(prev=>({start:offset&&current?.id===m.id&&selected===locationId?prev.start:r.offset,end:r.offset+Array.from(r.body).length}));
   if(r.body)trackAction('material_read',item.id);
   if(current?.id!==m.id||!directory)setDirectory(await request<Obj>(path.split('?')[0]+'/locations?'+path.split('?')[1]));
 }catch(e){setError((e as Error).message);}finally{setBusy(false);}};
 const labels:Record<string,string>={full_text:'全文可读',excerpt:'部分可读',link_only:'仅外部链接',unavailable:'获取失败',withdrawn:'已失效'};
 const positions=directory?[...(directory.sections||[]),...(directory.pages||[]),...(!directory.sections?.length&&!directory.pages?.length?directory.paragraphs||[]:[])]:[];
 const gapNames:Record<string,string>={no_text_layer:pick('没有文字层','No text layer'),images_not_extracted:pick('图像未提取','Images not extracted'),formula_layout_unverified:pick('公式布局未验证','Formula layout not verified')};
 const selected=positions.find((p:Obj)=>p.id===locationId);
 return <details className="content-materials"><summary>{pick('材料与出处','Materials & sources')} · {item.materials.length}</summary><ul>{item.materials.map(m=><li key={m.id}><strong>{m.title}</strong> · {pick(labels[m.coverage]||m.coverage,m.coverage)}<p>{m.locator} · {m.checked_at}{m.upstream_revision?' · '+m.upstream_revision.slice(0,12):''}</p>{m.reason&&<p>{m.reason}</p>}<a href={m.url} target="_blank" rel="noreferrer">{pick('原始出处','Upstream source')} ↗</a>{m.characters>0&&<button className="text-button" disabled={busy} onClick={()=>read(m)}>{pick('读取已审核原文','Read reviewed text')}</button>}</li>)}</ul>
 {error&&<p role="alert">{error}</p>}{current&&<section><h5>{current.title}</h5><p>{current.rights.basis} <a href={current.rights.url}>{pick('许可依据','Permission')}</a></p>{current.rights.notice&&<details><summary>{pick('许可与署名','License and attribution')}</summary><pre className="platform-original">{current.rights.notice}</pre></details>}
 {!previewBodies&&positions.length>0&&<label>{pick('章节／文件页码','Section / physical PDF page')}<select aria-label={pick('章节／文件页码','Section / physical PDF page')} disabled={busy} value={locationId} onChange={e=>read(current,0,e.target.value)}><option value="">{pick('从全文开始','Start full text')}</option>{positions.map((p:Obj)=><option key={p.id} value={p.id}>{p.page?pick('文件第 '+p.page+' 页（印刷 '+p.label+'）','Physical page '+p.page+' (label '+p.label+')'):p.title}</option>)}</select></label>}
 {selected?.gaps?.length>0&&<p className="material-gaps">{pick('本页提取缺口：','Extraction gaps: ')}{selected.gaps.map((g:string)=>(gapNames[g]||g)).join('；')}</p>}
 <pre className="platform-original">{body}</pre>{next!==null&&<button className="button" disabled={busy} onClick={()=>read(current,next,locationId)}>{pick('继续读取此范围','Continue this range')}</button>}
 {!previewBodies&&<><button className="text-button" onClick={async()=>{const reference={object_id:item.id,material_id:current.id,content_revision:item.materials_revision,source_url:current.url,content_hash:directory?.content_hash,upstream_revision:current.upstream_revision,location:selected||null,start:range.start,end:Math.min(range.end,range.start+4000),excerpt:Array.from(body).slice(0,4000).join('')};try{await navigator.clipboard.writeText(JSON.stringify(reference,null,2));notify(pick('固定修订引用已复制','Revision-bound citation copied'));}catch{notify(pick('无法复制，请使用原始出处与当前位置','Copy unavailable; use the source and current position'));}}}>{pick('复制原文引用','Copy source citation')}</button>
 <ReportCorrection id={item.id} material={{material_id:current.id,content_revision:item.materials_revision,start:range.start,end:Math.min(range.end,range.start+4000)}}/></>}
 <p className="muted">{pick('以上为来源材料，仅供引用阅读；定位对应当前所选固定修订。','Source material is reference data; locations belong to this fixed revision.')}</p></section>}
 </details>;
}
