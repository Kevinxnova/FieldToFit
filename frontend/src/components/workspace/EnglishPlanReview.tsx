import { useWorkspace } from './UI';
type Obj=Record<string,any>;
export function EnglishPlanReview({reviews,value,onChange,intake=false}:{reviews:Obj;value:Obj;onChange:(value:Obj)=>void;intake?:boolean}) {
  const {pick}=useWorkspace();
  return <section><h4>{intake?pick('核对本次稿件的英文','Review English for this draft'):pick('核对归并后的英文','Review English after the merge')}</h4>{Object.entries(reviews).map(([id,review])=>{
    const current=value[id]||{source_hash:review.source_hash,fields:review.fields,confirmed:false,reason:''};
    const change=(next:Obj)=>onChange({...value,[id]:{...current,...next,source_hash:review.source_hash}});
    return <details key={id}><summary>{id} · {review.state==='reviewed'?pick('已核对','Reviewed'):pick('需要核对英文','English review required')}</summary>
      {Object.entries(review.fields as Record<string,string>).map(([source])=><label className="management-field" key={source}><p data-original-language="zh-CN" lang="zh-CN">{source}</p><textarea rows={3} value={current.fields[source]||''} onChange={e=>change({fields:{...current.fields,[source]:e.target.value},confirmed:false})}/></label>)}
      <label><input type="checkbox" checked={current.confirmed} onChange={e=>change({confirmed:e.target.checked})}/>{intake?pick('已核对本次稿件的中英文事实及限制','I checked source and English facts and limitations for this draft.'):pick('已核对本次归并后的中英文事实及限制','I checked source and English facts and limitations after this merge.')}</label>
      <label>{pick('英文审核说明','English review note')}<textarea value={current.reason} onChange={e=>change({reason:e.target.value})}/></label>
    </details>})}<p>{pick('完成英文核对后重新预览，再确认应用。','Preview again after the English review, then confirm the change.')}</p></section>;
}
