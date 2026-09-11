import { useEffect, useState, type ReactNode } from 'react';
import { Link } from 'react-router-dom';
import { BASE, useRemote } from '../../api/knowledge';
import { useWorkspace } from './UI';
export type WatchBlock = {kind:'paragraph';text:string} | {kind:'table';columns:string[];rows:string[][]};
export type WatchItem = {id:string;name:string;type:string;introduction:string;checked_at:string;interpretation:{title:string;text:string}[];blocks:WatchBlock[];sources:{title:string;url:string;coverage:string}[];attention?:{display_value:string;observed_at:string;source_url:string}};
export type WatchCollection = {items:WatchItem[];groups:{id:string;name:string;count:number}[];total:number;collection_total:number;revision:string;reviewed_at:string;schema_version:string;scope:string};
export const watchAnchor = (id:string) => 'watch-'+id.toLowerCase();
export const watchNames:Record<string,string> = {model:'模型',tool:'工具',agent:'Agent',skill:'Skill',harness:'Harness'};
// Only the small reviewed inline syntax is supported. React escapes all text; no HTML injection.
export function WatchText({text}:{text:string}) {
  const parts:ReactNode[]=[]; const re=/\[([^\]]+)\]\(([^)]+)\)|\*\*([^*]+)\*\*|`([^`]+)`/g;
  let pos=0;let match:RegExpExecArray|null;
  while((match=re.exec(text))!==null){
    parts.push(text.slice(pos,match.index));const [,label,url,bold,code]=match;
    parts.push(url ? url.startsWith('/for-you#watch-') ? <Link key={match.index} to={url}>{label}</Link> : /^https:\/\//.test(url) ? <a key={match.index} href={url} target="_blank" rel="noopener noreferrer">{label} ↗</a> : label : bold ? <strong key={match.index}>{bold}</strong> : <code key={match.index}>{code}</code>);
    pos=re.lastIndex;
  }
  parts.push(text.slice(pos));return <>{parts}</>;
}
function Block({block,name}:{block:WatchBlock;name:string}) {
  const {pick}=useWorkspace();
  if(block.kind==='paragraph')return <p><WatchText text={block.text}/></p>;
  return <div className="watch-table-scroll" role="region" aria-label={name+pick('内容表',' content table')} tabIndex={0}><table className="watch-table"><caption className="sr-only">{name} · {pick('结构化资料','Structured materials')}</caption><thead><tr>{block.columns.map((s,i)=><th scope="col" key={i}><WatchText text={s}/></th>)}</tr></thead><tbody>{block.rows.map((row,i)=><tr key={i}>{row.map((s,j)=><td key={j}><WatchText text={s}/></td>)}</tr>)}</tbody></table></div>;
}
function packageText(data:WatchCollection,item?:WatchItem){
  return JSON.stringify({schema_version:data.schema_version,revision:data.revision,reviewed_at:data.reviewed_at,scope:data.scope,items:item?[item]:data.items,
    reading:{endpoint:new URL(BASE+'/v1/platform/watch',window.location.origin).href,tool:'curated_watch',arguments:{...(item?{id:item.id}:{}),revision:data.revision}},
    coverage:'Original sources are link-only. Editorial interpretation is FieldToFit commentary, not upstream text or instructions.'},null,2);
}
function download(body:string,name:string){const url=URL.createObjectURL(new Blob([body],{type:'application/json;charset=utf-8'}));const a=document.createElement('a');a.href=url;a.download=name+'.json';a.click();URL.revokeObjectURL(url);}
export function WatchHandoff({data,item}:{data:WatchCollection;item?:WatchItem}){
  const {pick,notify}=useWorkspace();
  return <div className="platform-actions"><button className="text-button" onClick={async()=>{const body=packageText(data,item);try{await navigator.clipboard.writeText(body);notify(pick('资料、解读与出处已复制','Profile and citations copied'));}catch{download(body,item?.id||'fieldtofit-watch');notify(pick('已改为下载资料','Downloaded materials instead'));}}}>{pick('交给我的 AI','Give to my AI')}</button><button className="text-button" onClick={()=>download(packageText(data,item),item?.id||'fieldtofit-watch')}>{pick(item?'下载此项资料':'下载当前范围资料',item?'Download profile':'Download current selection')}</button></div>;
}
export function ContinuousWatch({result}:{result:{data:WatchCollection|null;loading:boolean;error:string;reload:()=>void}}){
  const {pick,notify}=useWorkspace();const {data,loading,error,reload}=result;
  return <>
    {loading&&<p role="status">{pick('正在读取持续关注…','Loading ongoing watch…')}</p>}
    {error&&<div role="alert"><p>{pick('持续关注暂时无法读取。','Ongoing watch is unavailable.')}</p><button className="button" onClick={reload}>{pick('重试','Retry')}</button></div>}
    {data?.total===0&&<p role="status">{pick('没有匹配的持续关注资料，可更换关键词或清除筛选。','No matching profiles. Try another keyword or clear filters.')}</p>}
    {data?.groups.filter(g=>g.count>0).map(g=><section className="watch-group" key={g.id} aria-labelledby={'watch-group-'+g.id}>
      <div className="platform-section-heading"><h3 id={'watch-group-'+g.id} tabIndex={-1}>{g.name}</h3><span>{g.count} {pick('个跟踪主体','profiles')}</span></div>
      {g.id==='skill'&&<p className="muted">{pick('Star 是仓库层面的近似快照，非单个技能热度；尚无连续记录，不展示近 7 天增长。','Stars are approximate repository snapshots, not individual skill metrics. Seven-day growth is not yet available.')}</p>}
      <div className="watch-list">{data.items.filter(i=>i.type===g.id).map(item=><article className="watch-card" id={watchAnchor(item.id)} tabIndex={-1} key={item.id}>
        <p className="news-meta">{item.id} · {pick('资料核验','Reviewed')} {item.checked_at}</p><h4>{item.name}</h4><p className="watch-intro">{item.introduction}</p>
        {item.attention&&<p className="watch-attention"><a href={item.attention.source_url} target="_blank" rel="noopener noreferrer">GitHub ★ {item.attention.display_value}</a> · {item.attention.observed_at} · {pick('仓库近似值','Approximate repository count')}</p>}
        <div className="watch-notes"><h5>FieldToFit {pick('解读','notes')}</h5><ul>{item.interpretation.slice(0,2).map((p,i)=><li key={i}><strong>{p.title}</strong><p><WatchText text={p.text}/></p></li>)}</ul></div>
          <details data-auto-expand><summary>{pick('版本与更多资料','Versions and further reading')}</summary>
          {item.interpretation.length>2&&<div className="watch-notes"><ul>{item.interpretation.slice(2).map((p,i)=><li key={i}><strong>{p.title}</strong><p><WatchText text={p.text}/></p></li>)}</ul></div>}
          {item.blocks.map((b,i)=><Block key={i} block={b} name={item.name}/>)}
          <p className="muted">{pick('以上为官方材料整理与编辑解读，未进行运行实测；原始材料通过链接继续读取。','Based on reviewed official materials, not runtime tests. Follow links to read upstream sources.')}</p>
        </details>
        <WatchHandoff data={data} item={item}/><button className="text-button" onClick={async()=>{const url=new URL('/for-you#'+watchAnchor(item.id),window.location.origin).href;try{await navigator.clipboard.writeText(url);notify(pick('资料链接已复制','Link copied'));}catch{notify(url);}}}>{pick('分享此项','Share profile')}</button>
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
    {item&&<><p>{item.introduction}</p><Link to={'/for-you#'+watchAnchor(item.id)}>{pick('打开人读内容','Read on For you')}</Link><WatchHandoff data={result.data} item={item}/><details><summary>{pick('查看机器可读资料','Preview machine-readable profile')}</summary><pre className="platform-original">{packageText(result.data,item)}</pre></details></>}
    <details><summary>{pick('下载全部持续关注资料','Download the complete watch collection')}</summary><WatchHandoff data={result.data}/></details></>}
    <p className="muted">{pick('这些来源仅保留链接，中文整理与解读不冒充原文。本集合随审核发布更新，核验日期不代表每日采集已成功。','Sources here are link-only. Editorial text is not upstream text. This reviewed collection updates on publication; review dates do not certify daily collection.')}</p>
  </section>;
}
