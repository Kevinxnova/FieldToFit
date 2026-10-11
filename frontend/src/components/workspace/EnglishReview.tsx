import { useEffect, useState } from 'react';
import { send } from '../../api/knowledge';
import { useWorkspace } from './UI';
type Review={state:string;source_hash:string;fields:Record<string,string>;missing:string[]};
export function EnglishReview({kind,id,version,review,disabled,done,endpoint}:{kind:string;id:string;version:number;review:Review;disabled:boolean;done:(item:any)=>void;endpoint?:string}) {
  const {pick}=useWorkspace();const [fields,setFields]=useState(review.fields);const [confirmed,setConfirmed]=useState(false);const [reason,setReason]=useState('');const [error,setError]=useState('');const [busy,setBusy]=useState(false);
  useEffect(()=>{setFields(review.fields);setConfirmed(false);},[review.source_hash,version]);
  async function save(approve:boolean) {
    setBusy(true);setError('');
    try {done(await send(endpoint||`/v1/admin/workspace/content/${kind}/${id}/english-review`,{draft_version:version,source_hash:review.source_hash,fields,confirmed:approve,reason},'POST',true));}
    catch(error){setError((error as Error).message);}finally{setBusy(false);}
  }
  return <section className="management-english"><h3>{pick('英文正文审核','English content review')}</h3><p>{pick('英文与当前中文内容绑定。逐项核对事实、数字、单位、版本、日期、出处与适用边界；源文变化后须重新确认。原始材料与用户输入保留原语言。','English is bound to this source version. Check facts, numbers, units, versions, dates, citations and limitations. Confirm again after source changes. Original evidence and user input retain their source language.')}</p><p>{pick('审核状态','Review status')}: {({reviewed:pick('已审核','Reviewed'),draft:pick('待审核','Awaiting review'),stale:pick('源文已变化','Source changed')})[review.state]}</p>
    <details><summary>{pick('逐项核对中英正文','Review source and English text')} · {Object.keys(fields).length}</summary>{Object.entries(fields).map(([source,translation])=><label key={source} className="management-field"><span>{pick('中文原文','Chinese source')}</span><p lang="zh-CN" data-original-language="zh-CN">{source}</p><span>English</span><textarea rows={Math.max(2,Math.min(8,Math.ceil(translation.length/100)))} value={translation} disabled={disabled||busy} onChange={event=>{setFields({...fields,[source]:event.target.value});setConfirmed(false);}}/></label>)}</details>
    <label className="management-check"><input type="checkbox" checked={confirmed} disabled={disabled||busy} onChange={event=>setConfirmed(event.target.checked)}/>{pick('已逐项核对本版中英文，事实及限制条件一致','I checked this source and every English field; facts and limitations match.')}</label>
    <label className="management-field"><span>{pick('英文审核说明','English review note')}</span><textarea value={reason} onChange={event=>setReason(event.target.value)}/></label>
    {error&&<p role="alert">{error}</p>}<div className="platform-actions"><button className="button" disabled={disabled||busy} onClick={()=>save(false)}>{pick('保存英文草稿','Save English draft')}</button><button className="button primary" disabled={disabled||busy||!confirmed||!reason.trim()||Object.values(fields).some(value=>!value.trim())} onClick={()=>save(true)}>{pick('确认英文审核','Confirm English review')}</button></div>
  </section>;
}
