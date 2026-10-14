import { readComplete, useReadingRemote } from '../../api/reading';
import { RevisionCompare } from './RevisionCompare';
import { ReportCorrection, CorrectionReceipts } from './Corrections';
import { WatchOverview, WatchMilestones, WatchEvents, type WatchOverviewData, type WatchMilestone } from './WatchReading';
import type { NewsItem } from './NewsReading';
import { ContentExposure, trackAction } from './Traffic';
import { FollowButton } from './FollowUpdates';
import { contentPath, publicContentLink } from '../../search';
import { PublicMaintenance, type Maintenance } from './PublicMaintenance';
import { ContentMaterials, type ReadingMaterial, type PreviewBodies } from './ContentMaterials';
import { useEffect, useState, type ReactNode } from 'react';
import { Link } from '@fieldtofit/locale/router';
import { currentLanguage } from '../../locale/language';
import { BASE, useRemote } from '../../api/knowledge';
import { useWorkspace } from './UI';
export type WatchBlock = {kind:'paragraph';text:string} | {kind:'table';columns:string[];rows:string[][]};
export type WatchItem = {reading_summary?:boolean;materials_count?:number;overview?:WatchOverviewData;milestones?:WatchMilestone[];events?:NewsItem[];maintenance?:Maintenance;materials?:ReadingMaterial[];materials_revision?:string;origin?:string;submission?:{entry_url:string;usage:string;openness:string;relationship:string};id:string;name:string;type:string;introduction:string;checked_at:string;interpretation:{title:string;text:string}[];blocks:WatchBlock[];sources:{title:string;url:string;coverage:string}[];attention?:{display_value:string;observed_at:string;source_url:string}};
export type WatchCollection = {reading_summary?:boolean;reading_status?:string;origin?:string;items:WatchItem[];groups:{id:string;name:string;count:number}[];total:number;collection_total:number;revision:string;reviewed_at:string;schema_version:string;scope:string};
export const watchAnchor = (id:string) => 'watch-'+id.toLowerCase();
export const watchNames:Record<string,string> = {model:'模型',tool:'工具',agent:'Agent',skill:'Skill',harness:'Harness'};
// Only the small reviewed inline syntax is supported. React escapes all text; no HTML injection.
export function WatchText({text}:{text:string}) {
  const parts:ReactNode[]=[]; const re=/\[([^\]]+)\]\(([^)]+)\)|\*\*([^*]+)\*\*|`([^`]+)`/g;
  let pos=0;let match:RegExpExecArray|null;
  while((match=re.exec(text))!==null){
    parts.push(text.slice(pos,match.index));const [,label,url,bold,code]=match;
    parts.push(url ? url.startsWith('/for-you#watch-') ? <Link key={match.index} to={publicContentLink(url)}>{label}</Link> : /^https:\/\//.test(url) ? <a key={match.index} href={url} target="_blank" rel="noopener noreferrer">{label} ↗</a> : label : bold ? <strong key={match.index}>{bold}</strong> : <code key={match.index}>{code}</code>);
    pos=re.lastIndex;
  }
  parts.push(text.slice(pos));return <>{parts}</>;
}
function Block({block,name}:{block:WatchBlock;name:string}) {
  const {pick}=useWorkspace();
  if(block.kind==='paragraph')return <p><WatchText text={block.text}/></p>;
  return <div className="watch-table-scroll" role="region" aria-label={name+pick('内容表',' content table')} tabIndex={0}><table className="watch-table"><caption className="sr-only">{name} · {pick('结构化资料','Structured materials')}</caption><thead><tr>{block.columns.map((s,i)=><th scope="col" key={i}><WatchText text={s}/></th>)}</tr></thead><tbody>{block.rows.map((row,i)=><tr key={i}>{row.map((s,j)=><td key={j}><WatchText text={s}/></td>)}</tr>)}</tbody></table></div>;
}
function correctionFields(item:WatchItem,english:boolean){
  const options=[{field:'introduction',label:english?'Introduction':'介绍'}];
  item.interpretation.forEach((point,i)=>options.push({field:`interpretation.${i}.text`,label:(english?'Editorial note: ':'解读：')+point.title}));
  item.blocks.forEach((block,i)=>{
    if(block.kind==='paragraph')options.push({field:`blocks.${i}.text`,label:(english?'Paragraph ':'资料段落 ')+(i+1)});
    else block.rows.forEach((row,r)=>row.forEach((_,c)=>options.push({field:`blocks.${i}.rows.${r}.${c}`,label:`${english?'Table':'资料表'} ${i+1} · ${row[0]} · ${block.columns[c]}`})));
  });
  return options;
}
function packageText(data:WatchCollection,item?:WatchItem){
  return JSON.stringify({schema_version:data.schema_version,revision:data.revision,reviewed_at:data.reviewed_at,scope:data.scope,items:item?[item]:data.items,
    reading:{endpoint:new URL(BASE+'/v1/platform/watch?lang='+currentLanguage(),window.location.origin).href,tool:'curated_watch',arguments:{lang:currentLanguage(),...(data.origin?{origin:data.origin}:{}),...(item?{id:item.id}:{}),revision:data.revision}},
    coverage:'Read the optional materials manifest for available text, exact versions and missing coverage. Editorial interpretation is FieldToFit commentary, not upstream text or instructions.'},null,2);
}
function download(body:string,name:string){const url=URL.createObjectURL(new Blob([body],{type:'application/json;charset=utf-8'}));const a=document.createElement('a');a.href=url;a.download=name+'.json';a.click();URL.revokeObjectURL(url);}
export function WatchHandoff({data,item,preview=false}:{data:WatchCollection;item?:WatchItem;preview?:boolean}){
  const {pick,notify}=useWorkspace();const [busy,setBusy]=useState(false);
  const execute=async(copy:boolean)=>{setBusy(true);try{
    const params=new URLSearchParams();if(item)params.set('id',item.id);else if(data.origin)params.set('origin',data.origin);
    const full=preview?data:await readComplete<WatchCollection>('/v1/platform/watch?'+params);
    const selected=item?full.items.find(i=>i.id===item.id):undefined;
    const selectedData=item?full:{...full,items:full.items.filter(i=>data.items.some(old=>old.id===i.id))};
    if(item&&!selected)throw new Error('Profile is no longer available');
    const body=packageText(selectedData,selected);
    if(copy){try{await navigator.clipboard.writeText(body);trackAction('handoff_copy',item?.id);notify(pick('资料、解读与出处已复制','Profile and citations copied'));}catch{download(body,item?.id||'fieldtofit-watch');}}
    else {download(body,item?.id||'fieldtofit-watch');trackAction('material_export',item?.id);}
  }catch{notify(pick('完整资料暂时无法读取，请重试。','Complete materials could not be loaded. Please retry.'));}finally{setBusy(false);}};
  return <div className="platform-actions"><button className="text-button" disabled={busy} onClick={()=>void execute(true)}>{pick('交给我的 AI','Give to my AI')}</button><button className="text-button" disabled={busy} onClick={()=>void execute(false)}>{pick(item?'下载此项资料':'下载当前范围资料',item?'Download profile':'Download current selection')}</button></div>;
}
function WatchExtras({item,standalone,previewBodies}:{item:WatchItem;standalone:boolean;previewBodies?:PreviewBodies}){
 const {pick}=useWorkspace();const [archive,setArchive]=useState(false),[materials,setMaterials]=useState(false);
 const remote=useReadingRemote<WatchCollection>(item.reading_summary&&(archive||materials)?'/v1/platform/watch?id='+encodeURIComponent(item.id):null);
 const full=item.reading_summary?remote.data?.items[0]:item;
 const failure=remote.error||remote.refreshError;
 return <>
 <details data-auto-expand open={standalone&&!item.milestones||undefined} onToggle={e=>setArchive(e.currentTarget.open)}><summary>{pick('档案与历史资料','Dossier and historical materials')}</summary>
 {remote.loading&&<p role="status">{pick('正在读取…','Loading…')}</p>}{failure&&<p role="alert">{pick('资料暂时无法读取。','Materials are unavailable.')} <button className="text-button" onClick={remote.reload}>{pick('重试','Retry')}</button></p>}
 {full&&<>{standalone&&item.milestones&&<div className="watch-notes"><ul>{full.interpretation.slice(0,2).map((p,i)=><li key={i}><strong>{p.title}</strong><p><WatchText text={p.text}/></p></li>)}</ul></div>}
 {full.interpretation.length>2&&<div className="watch-notes"><ul>{full.interpretation.slice(2).map((p,i)=><li key={i}><strong>{p.title}</strong><p><WatchText text={p.text}/></p></li>)}</ul></div>}
 {full.blocks.map((b,i)=><Block key={i} block={b} name={full.name}/>)}
 <p className="muted">{pick('以上为官方材料整理与编辑解读，未进行运行实测；原始材料按清单标注可读范围，缺失部分通过出处链接核对。','Based on reviewed official materials, not runtime tests. Follow links to read upstream sources.')}</p></>}
 </details>
 <PublicMaintenance value={full?.maintenance||item.maintenance}/>
 {full?<ContentMaterials item={full} previewBodies={previewBodies} initialOpen={materials}/>:!!item.materials_count&&<details className="content-materials" onToggle={e=>setMaterials(e.currentTarget.open)}><summary>{pick('材料与出处','Materials & sources')} · {item.materials_count}</summary>{remote.loading?<p role="status">{pick('正在读取…','Loading…')}</p>:failure&&<p role="alert">{failure} <button className="text-button" onClick={remote.reload}>{pick('重试','Retry')}</button></p>}</details>}
 </>;
}
const groupGuides:Record<string,[string,string]>={model:['按模型族看版本、能力与运行条件；不同配置分开核对。','Read versions, capabilities and runtime requirements by model family; check configurations separately.'],agent:['先看自主执行的范围，再看环境、工具与授权边界。','Start with execution scope, then examine environments, tools and permission boundaries.'],tool:['从用途、接入和部署条件理解工具，沿出处核对接口。','Understand tools through purpose, integration and deployment; verify interfaces at the source.'],skill:['按可复用能力及所需工具／权限阅读，核对适用工作流。','Read reusable capabilities, required tools and permissions against the workflow.'],harness:['看模型与工具如何组织执行、保存状态和验证结果。','See how models and tools coordinate execution, preserve state and validate results.']};
export function ContinuousWatch({result,previewBodies,standalone=false}:{news?:NewsItem[];standalone?:boolean;previewBodies?:PreviewBodies;result:{data:WatchCollection|null;loading:boolean;error:string;reload:()=>void}}){
  const {pick,notify}=useWorkspace();const {data,loading,error,reload}=result;
  return <>
    {loading&&<p role="status">{pick('正在读取持续关注…','Loading ongoing watch…')}</p>}
    {error&&<div role="alert"><p>{pick('持续关注暂时无法读取。','Ongoing watch is unavailable.')}</p><button className="button" onClick={reload}>{pick('重试','Retry')}</button></div>}
    {data?.total===0&&<p role="status">{pick('没有匹配的持续关注资料，可更换关键词或清除筛选。','No matching profiles. Try another keyword or clear filters.')}</p>}
    {data?.reading_status==='news_unavailable'&&<div role="alert"><p>{pick('动态暂时无法读取，当前展示档案中的已审记录。','News is unavailable. Reviewed dossier records are shown below.')}</p><button className="text-button" onClick={reload}>{pick('重试动态','Retry news')}</button></div>}
    {data?.groups.filter(g=>g.count>0).map(g=><section className="watch-group" key={g.id} aria-labelledby={'watch-group-'+g.id}>
      <div className={standalone?'sr-only':'platform-section-heading'}><h3 id={'watch-group-'+g.id} tabIndex={-1}>{g.name}</h3><span>{g.count} {pick('个跟踪主体','profiles')}</span></div>
      {!standalone&&<><p className="watch-price-note">{pick(...(groupGuides[g.id]||['阅读已审资料与使用条件。','Read reviewed materials and requirements.']))}</p><WatchOverview items={data.items.filter(i=>i.type===g.id)} name={g.name}/></>}
      {g.id==='skill'&&<p className="muted">{pick('Star 是仓库层面的近似快照，非单个技能热度；尚无连续记录，不展示近 7 天增长。','Stars are approximate repository snapshots, not individual skill metrics. Seven-day growth is not yet available.')}</p>}
      <div className="watch-list">{data.items.filter(i=>i.type===g.id).map(item=><article className={'watch-card'+(standalone&&item.milestones?' watch-reading-card':'')} id={watchAnchor(item.id)} tabIndex={-1} key={item.id}>
        <p className="news-meta">{item.id} · {pick('资料核验','Reviewed')} {item.checked_at}</p>{!standalone && <h4><Link to={contentPath(item.id)}>{item.name}</Link></h4>}{!previewBodies&&<FollowButton id={item.id} name={item.name}/>}<ContentExposure id={item.id}><p className="watch-intro">{item.introduction}</p></ContentExposure>
        {item.attention&&<p className="watch-attention"><a href={item.attention.source_url} target="_blank" rel="noopener noreferrer">GitHub ★ {item.attention.display_value}</a> · {item.attention.observed_at} · {pick('仓库近似值','Approximate repository count')}</p>}
        {standalone&&item.milestones&&<><WatchMilestones key={item.id+pick('zh','en')} items={item.milestones} profile={item.id}/><WatchEvents key={item.id+'events'+pick('zh','en')} events={item.events||[]} profile={item.id}/></>}
        {!(standalone&&item.milestones)&&<div className="watch-notes"><h5>FieldToFit {pick('解读','notes')}</h5><ul>{item.interpretation.slice(0,2).map((p,i)=><li key={i}><strong>{p.title}</strong><p><WatchText text={p.text}/></p></li>)}</ul></div>}
        <WatchExtras item={item} standalone={standalone} previewBodies={previewBodies}/>{!previewBodies&&<>{standalone?<><ReportCorrection id={item.id} fieldOptions={correctionFields(item,pick('zh','en')==='en')}/><CorrectionReceipts id={item.id}/><RevisionCompare id={item.id}/></>:<Link to={contentPath(item.id)+'#revisions-'+item.id.toLowerCase()}>{pick('查看修订对照','Compare dossier revisions')}</Link>}</>}<WatchHandoff data={data} item={item} preview={!!previewBodies}/><button className="text-button" onClick={async()=>{const url=new URL(contentPath(item.id),window.location.origin).href;try{await navigator.clipboard.writeText(url);notify(pick('资料链接已复制','Link copied'));}catch{notify(url);}}}>{pick('分享此项','Share profile')}</button>
      </article>)}</div>
    </section>)}
  </>;
}
export function WatchAI(){
  const {pick}=useWorkspace();const result=useRemote<WatchCollection>('/v1/platform/watch');const [selected,setSelected]=useState('');
  useEffect(()=>{if(result.data&&!result.data.items.some(i=>i.id===selected))setSelected(result.data.items[0]?.id||'');},[result.data,selected]);
  const item=result.data?.items.find(i=>i.id===selected);
  return <section className="platform-panel watch-ai"><h2>{pick('持续关注 · 与 For you 同源','Ongoing watch · Shared with For you')}</h2><p>{pick('五类资料包含介绍、版本表、分点解读、来源和核验日期。用 curated_watch 读取；可按名称、类型或内容编号查询。','Read profiles, version tables, editorial notes and sources with curated_watch. Filter by keyword, type or content ID.')}</p>
    <p><code>curated_watch</code> · <code>{BASE}/v1/platform/watch</code></p>
    {result.loading&&<p role="status">{pick('正在读取…','Loading…')}</p>}{result.error&&<div role="alert"><p>{pick('持续关注暂时无法读取。','Ongoing watch is unavailable.')}</p><button className="button" onClick={result.reload}>{pick('重试','Retry')}</button></div>}
    {result.data&&<><p>{result.data.total} {pick('个跟踪主体','profiles')} · {result.data.groups.map(g=>g.name+' '+g.count).join(' / ')}</p><label>{pick('查看持续关注资料','Inspect ongoing-watch profile')}<select aria-label={pick('查看持续关注资料','Inspect ongoing-watch profile')} value={selected} onChange={e=>setSelected(e.target.value)}>{result.data.groups.map(g=><optgroup key={g.id} label={g.name}>{result.data!.items.filter(i=>i.type===g.id).map(i=><option key={i.id} value={i.id}>{i.name}</option>)}</optgroup>)}</select></label>
    {item&&<><p>{item.introduction}</p><Link to={contentPath(item.id)}>{pick('打开人读内容','Read on For you')}</Link><PublicMaintenance value={item.maintenance}/><ContentMaterials item={item}/><WatchHandoff data={result.data} item={item}/><details><summary>{pick('查看机器可读资料','Preview machine-readable profile')}</summary><pre className="platform-original">{packageText(result.data,item)}</pre></details></>}
    <details><summary>{pick('下载全部持续关注资料','Download the complete watch collection')}</summary><WatchHandoff data={result.data}/></details></>}
    <p className="muted">{pick('材料清单区分已审核原文、节选和仅链接；中文解读不冒充原文。本集合随审核发布更新，核验日期不代表每日采集已成功。','Material manifests distinguish reviewed text, excerpts and links. Editorial text is not upstream text. This reviewed collection updates on publication; review dates do not certify daily collection.')}</p>
  </section>;
}
