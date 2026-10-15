import { useEffect, useState } from 'react';
import { Link, useLocation, useSearchParams } from '@fieldtofit/locale/router';
import { useHomeReading } from '../api/reading';
import { ModelLandscape } from '../components/workspace/ModelLandscape';
import { NewsIndex } from '../components/workspace/NewsIndex';
import { CodexProgress } from '../components/workspace/CodexProgress';
import { ContinuousWatch } from '../components/workspace/ContinuousWatch';
import { ProfileNewsOverview } from '../components/workspace/ProfileNewsOverview';
import { VisitReady } from '../components/workspace/SiteVisits';
import { hasReadingPosition } from '../components/workspace/readingPosition';
import { useWorkspace } from '../components/workspace/UI';
import { ReadingLoadState } from './ForYouHome';
import './for-you-preview.css';

export type ForYouSectionName='news'|'hot-cards'|'codex'|'models'|'watch';
const sections:Record<ForYouSectionName,{title:[string,string];anchor:string}>={
  news:{title:['近期动态','Recent developments'],anchor:'recent-news'},
  'hot-cards':{title:['热点信息卡','Information cards'],anchor:'hot-information-cards'},
  codex:{title:['Codex 28天进化日志','Codex: 28 Days of Progress'],anchor:'news-codex-28-days'},
  models:{title:['模型能力与价格','Model capability & pricing'],anchor:'model-landscape'},
  watch:{title:['持续关注','Ongoing watch'],anchor:'resource-dossiers'},
};
export function ForYouSection({section}:{section:ForYouSectionName}){
  const {pick}=useWorkspace(),location=useLocation(),[params,setParams]=useSearchParams();
  const q=section==='watch'?params.get('q')||'':'',type=section==='watch'?params.get('type')||'':'';
  const result=useHomeReading(q,type,section),[query,setQuery]=useState(q),data=result.data;
  useEffect(()=>setQuery(q),[q]);
  useEffect(()=>{
    if(!data||!location.hash||(location.state?.restoreReading&&hasReadingPosition()))return;
    let id='';try{id=decodeURIComponent(location.hash.slice(1));}catch{return;}
    const frame=requestAnimationFrame(()=>{const node=document.getElementById(id);node?.focus({preventScroll:true});node?.scrollIntoView({block:'start'});});
    return()=>cancelAnimationFrame(frame);
  },[data,location.hash]);
  const current=sections[section];
  return <div className="platform-page for-you-section"><VisitReady ready={!!data&&!result.error}/><nav className="section-breadcrumb" aria-label={pick('阅读路径','Reading path')}><Link to={'/for-you#'+current.anchor} state={{restoreReading:!!location.state?.readingReturn}}>For you</Link><span>/</span><span>{pick(...current.title)}</span></nav><header className="platform-hero"><h1>{pick(...current.title)}</h1><Link className="section-return" to={'/for-you#'+current.anchor} state={{restoreReading:!!location.state?.readingReturn}}>← {pick('返回首页预览','Back to homepage preview')}</Link></header>
    <ReadingLoadState {...result}/>
    {data&&<>
      {section==='models'&&<ModelLandscape previewData={data.charts}/>}
      {(section==='news'||section==='hot-cards')&&<><NewsIndex data={data.news} loading={result.loading} error={result.error} reload={result.reload} topics={false} hotCards={section==='hot-cards'}/><nav className="section-links" aria-label={pick('相关专题','Related sections')}><Link to="/for-you/hot-cards">{pick('热点信息卡','Information cards')}</Link><Link to="/maps">{pick('技术报告精选&分析','Reports & analysis')}</Link><Link to="/for-you/codex">{pick('Codex 28天进化日志','Codex: 28 Days of Progress')}</Link></nav></>}
      {section==='codex'&&(data.news.codex_progress?.days.length?<CodexProgress data={data.news}/>:<p className="section-empty">{pick('暂无已审日志。','No reviewed log entries yet.')}</p>)}
      {section==='watch'&&<section aria-labelledby="resource-dossiers"><div className="platform-section-heading"><h2 id="resource-dossiers" tabIndex={-1}>{pick('完整档案','Complete dossiers')}</h2><span>{data.watch.total} / {data.watch.collection_total}</span></div><ProfileNewsOverview news={data.news.items} ids={data.watch.items.map(item=>item.id)}/><form className="platform-search" onSubmit={event=>{event.preventDefault();setParams(p=>{if(query)p.set('q',query);else p.delete('q');return p;});}}><input aria-label={pick('搜索持续关注','Search ongoing watch')} placeholder={pick('搜索名称、版本或关键词','Search names, versions or keywords')} value={query} onChange={e=>setQuery(e.target.value)}/><button className="button">{pick('搜索','Search')}</button><select aria-label={pick('持续关注类型','Watch type')} value={type} onChange={e=>setParams(p=>{if(e.target.value)p.set('type',e.target.value);else p.delete('type');return p;})}><option value="">{pick('全部五类','All five groups')}</option>{['model','tool','agent','skill','harness'].map(id=><option key={id} value={id}>{pick(...({model:['模型','Models'],tool:['工具','Tools'],agent:['Agent','Agents'],skill:['Skill','Skills'],harness:['Harness','Harnesses']} as Record<string,[string,string]>)[id])}</option>)}</select></form>{(q||type)&&<button className="text-button" onClick={()=>setParams(p=>{p.delete('q');p.delete('type');return p;})}>{pick('清除全部筛选','Clear filters')}</button>}<ContinuousWatch result={{...result,data:data.watch}}/></section>}
    </>}
  </div>;
}
