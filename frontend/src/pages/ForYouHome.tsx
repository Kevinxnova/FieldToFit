import { useState, type ReactNode } from 'react';
import { Link, Navigate, useLocation, useNavigate, useSearchParams } from '@fieldtofit/locale/router';
import { useHomeReading, type ChartPreview } from '../api/reading';
import { ForYouHero } from '../components/workspace/ForYouHero';
import { DailyPreview } from '../components/workspace/DailyPreview';
import { FollowUpdates } from '../components/workspace/FollowUpdates';
import { HotCardHighlights } from '../components/workspace/HotCards';
import { ModelChart } from '../components/workspace/ModelChart';
import { MapCards } from '../components/workspace/TechnicalMaps';
import { ReadingContents } from '../components/workspace/ReadingContents';
import { VisitReady } from '../components/workspace/SiteVisits';
import { AliasNotice } from '../components/workspace/PublicMaintenance';
import { ContentExposure } from '../components/workspace/Traffic';
import { SourceLink, useWorkspace } from '../components/workspace/UI';
import { legacyForYouTarget, legacyReadingTargets } from '../components/workspace/forYouNavigation';
import { contentPath } from '../search';
import type { NewsItem } from '../components/workspace/NewsReading';
import './for-you-preview.css';

export function PreviewHeading({id,title,to,action,children}:{id:string;title:string;to:string;action:string;children?:ReactNode}){
  return <><header className="platform-section-heading"><h2 id={id} tabIndex={-1}>{title}</h2><Link to={to}>{action} ↗</Link></header>{children&&<p className="home-section-intro">{children}</p>}</>;
}
export function ReadingLoadState({loading,error,reload}:{loading:boolean;error:string;reload:()=>void}){
  const {pick}=useWorkspace();
  return <>{loading&&<p role="status">{pick('正在读取已审内容…','Loading reviewed content…')}</p>}{error&&<div role="alert"><p>{pick('内容暂时无法读取。','Content is temporarily unavailable.')}</p><button className="button" onClick={reload}>{pick('重试','Retry')}</button></div>}</>;
}
export function ForYouHome(){
  const location=useLocation();const target=legacyForYouTarget(location.search,location.hash);
  return target?<Navigate to={target} replace state={location.state}/>:<Home/>;
}
function Home(){
  const {pick,zh}=useWorkspace(),navigate=useNavigate(),[params]=useSearchParams();
  const home=useHomeReading('','','home');const data=home.data;
  const [following,setFollowing]=useState(false),[query,setQuery]=useState('');
  const byId=new Map((data?.news.items||[]).map(i=>[i.id,i]));
  const selected=(ids?:string[])=>ids?.flatMap(id=>byId.has(id)?[byId.get(id)!]:[])||[];
  const highlights=selected(data?.home_preview?.highlights),logs=selected(data?.home_preview?.codex);
  const empty=<p className="muted">{pick('暂无已审内容，完成审核后会在这里展示。','Reviewed content will appear here when available.')}</p>;
  const targets=legacyReadingTargets(params);
  return <div className="platform-page for-you-home"><VisitReady ready={!!data&&!home.error}/><AliasNotice/>
    <ForYouHero onRead={()=>setFollowing(false)}/>
    {targets.length>1&&<nav className="platform-notice legacy-reading-options" aria-label={pick('原链接中的栏目筛选','Filters from this link')}><p>{pick('原链接包含多个栏目的筛选，请选择要继续阅读的栏目：','This link contains filters for several sections. Continue in a section:')}</p>{targets.map(target=><Link key={target} to={'/for-you/'+target+'?'+params}>{pick(...({news:['近期动态','Developments'],models:['模型能力与价格','Model charts'],watch:['持续关注','Ongoing watch'],codex:['Codex日志','Codex log']} as Record<string,[string,string]>)[target])} →</Link>)}</nav>}
    <form className="platform-search home-search" onSubmit={event=>{event.preventDefault();navigate('/for-you/watch?'+new URLSearchParams({q:query}));}}><input aria-label={pick('搜索持续关注','Search ongoing watch')} placeholder={pick('搜索完整档案中的名称、版本或关键词','Search all dossiers by name, version or keyword')} value={query} onChange={e=>setQuery(e.target.value)}/><button className="button">{pick('搜索','Search')}</button><Link to="/for-you/news#news-releases">{pick('查找动态','Find developments')} →</Link></form>
    <FollowUpdates active={following} onActive={setFollowing}/>
    <div hidden={following} className="reading-layout home-reading-layout"><ReadingContents home news={[]} resources={[]} newsTotal={data?.news.total??null} resourceTotal={data?.watch.total??null} loading={home.loading} filtered={false}/>
    <div className="reading-body">
      <DailyPreview data={data?.daily} loading={home.loading} error={home.error} retry={home.reload}/>
      <ReadingLoadState {...home}/>
      <section className="home-section home-developments"><PreviewHeading id="recent-news" title={pick('近期动态','Recent developments')} to="/for-you/news" action={pick('全部动态','All developments')}/><div className="home-glance-heading"><h3>{pick('近期热点速览','Recent highlights')}</h3><span>{pick('值得先读的几件事','A few things to read first')}</span></div>
        <div className="home-glance">{highlights.map((item,index)=><article key={item.id} className={index===0?'home-glance-lead':'home-glance-secondary'}>
          <HomeNewsArt item={item} lead={index===0}/>
          <p className="home-meta">{item.organization} · {item.event_date||item.source_published_at||pick('来源日期待核实','Source date unconfirmed')}</p><h4><Link to={contentPath(item.id)}>{item.title}</Link></h4><ContentExposure id={item.id}><p>{item.summary}</p></ContentExposure><Link to={contentPath(item.id)}>{pick('查看完整资料','Read full details')} ↗</Link>
        </article>)}</div>{data&&!highlights.length&&empty}
      </section>
      {data?<HotCardHighlights items={selected(data.home_preview?.hot_cards)}/>:<section className="home-section"><PreviewHeading id="hot-information-cards" title={pick('热点信息卡','Information cards')} to="/for-you/hot-cards" action={pick('全部热点','All information cards')}/></section>}
      {data?<MapCards items={selected(data.home_preview?.reports)} selection={data.news.report_selection} home/>:<section className="home-section"><PreviewHeading id="technical-evolution-maps" title={pick('技术报告精选&分析','Selected Technical Reports & Analysis')} to="/maps" action={pick('全部精选','All reports')}/></section>}
      <section className="home-section home-codex"><PreviewHeading id="news-codex-28-days" title={pick('Codex 28天进化日志','Codex: 28 Days of Progress')} to="/for-you/codex" action={pick('完整日志','Full log')}>{pick('把每一次真实更新，放回它发生的时间。','Place each update on its actual date.')}</PreviewHeading>
        <div className="home-codex-frame"><div className="home-codex-intro"><strong>Codex</strong><p>{pick('28天进化日志','28 Days of Progress')}</p><small>{pick('官方公告 · 已审记录','Official announcements · Reviewed records')}</small><Link className="button" to="/for-you/codex">{pick('按日期阅读','Read by date')} →</Link></div><div className="home-log-list">
          {logs.map(item=>{const event=item.codex_28_days!;return <article key={item.id}><Link className="home-log-date" to={'/for-you/codex?codex_date='+event.date+'#codex-day-'+event.date}><time dateTime={event.date}>{event.date.slice(5)}</time>{event.official_day&&<small>{pick('官方','Official')} Day {event.official_day}</small>}</Link><div><p className="home-meta">{event.group==='codex'?'Codex / Work':pick('其他 OpenAI','Other OpenAI')}</p><h3><Link to={contentPath(item.id)}>{(zh?event.overview_zh:event.overview_en)||item.title}</Link></h3><p>{item.summary}</p></div></article>;})}{data&&!logs.length&&empty}
        </div></div>
      </section>
      <section className="home-section home-models"><PreviewHeading id="model-landscape" title={pick('模型能力与价格','Model capability & pricing')} to="/for-you/models" action={pick('完整图表','Full charts')}>{pick('能力与成本一起看，配置与来源分开比较。','Read capability alongside cost, within each source and configuration.')}</PreviewHeading><div className="home-model-previews">{data?.chart_previews?.map(source=><ModelPreview key={source.id} source={source}/>)}</div>{data&&!data.chart_previews?.length&&empty}</section>
      <section className="home-section home-watch"><PreviewHeading id="resource-dossiers" title={pick('持续关注','Ongoing watch')} to="/for-you/watch" action={pick('全部档案','All dossiers')}>{pick('把一次发现，放回长期维护的对象档案。','Put each discovery in a maintained dossier.')}</PreviewHeading><nav className="home-watch-types" aria-label={pick('持续关注分类','Watch categories')}>{['model','tool','agent','skill','harness'].map(type=>{const group=data?.watch.groups.find(g=>g.id===type);return <Link key={type} to={'/for-you/watch?type='+type+'#watch-group-'+type}>{pick(...({model:['模型','Models'],tool:['工具','Tools'],agent:['Agent','Agents'],skill:['Skill','Skills'],harness:['Harness','Harnesses']} as Record<string,[string,string]>)[type])} <span>{group?.count??'—'}</span> ↗</Link>;})}</nav>
        <div className="home-watch-list">{data?.watch.items.map(item=>{const event=data.home_preview?.watch_events.find(e=>e.watch_id===item.id),news=event&&byId.get(event.news_id);return <article key={item.id}><div><h3><Link to={contentPath(item.id)}>{item.name}</Link></h3>{news&&<p><time dateTime={event!.date}>{event!.date}</time> · {news.title}</p>}</div><Link to={contentPath(item.id)}>{pick('阅读档案','Read dossier')} ↗</Link></article>;})}{data&&!data.watch.items.length&&<p className="muted">{pick('近30日暂无已审关联事件，可按分类浏览完整档案。','No reviewed related events in the last 30 days. Browse complete dossiers by category.')}</p>}</div>
      </section>
      <section className="home-community" aria-labelledby="developer-projects"><h2 id="developer-projects" tabIndex={-1}>{pick('还有值得被看见的项目？','Have a project to share?')}</h2><p>{pick('在社区分享你的工具、经验与问题。','Share tools, experiences and questions with the community.')}</p><Link to="/community#developer-projects">{pick('前往社区','Visit the community')} ↗</Link></section>
    </div></div>
  </div>;
}
function ModelPreview({source}:{source:ChartPreview}){
  const {pick}=useWorkspace();const to='/for-you/models?chart='+source.id;
  return <article>
    <div className="platform-section-heading"><h3><Link to={to}>{source.name}</Link></h3><span>{source.coverage.plotted} {pick('个配置','configurations')}</span></div>
    {!!source.plot_points?.length&&<Link to={to} className="home-chart-image landscape-plot" aria-label={source.name+pick('：查看完整图表与配置',' — open full chart and configurations')}><ModelChart source={{...source,points:source.plot_points}}/></Link>}
    <p className="home-meta">{pick('来源日期：','Source date: ')}{source.source_updated_at||pick('来源未标注','Not provided')} · {pick('核对：','Checked: ')}{source.checked_at}</p>
    <div className="platform-actions"><Link to={to}>{pick('查看完整图表与配置','Open full chart and configurations')} ↗</Link><SourceLink url={source.source_url}>{pick('原始来源','Original source')}</SourceLink></div>
  </article>;
}
function HomeNewsArt({item,lead}:{item:NewsItem;lead:boolean}){
  const {pick}=useWorkspace();const [broken,setBroken]=useState(false);
  if(!item.media&&!lead)return null;
  return item.media&&!broken?<Link className="home-news-image" to={contentPath(item.id)}><img src={item.media.url} alt={item.media.alt} loading="lazy" style={{objectFit:item.media.fit}} onError={()=>setBroken(true)}/></Link>:<Link className="home-news-cover" to={contentPath(item.id)} aria-label={item.title}><span>{item.organization}</span><strong>{item.name}</strong><small>{pick('近期精选','RECENT HIGHLIGHT')}</small></Link>;
}
