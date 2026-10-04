import { useEffect, useRef, useState } from 'react';
import { Link, useLocation, useSearchParams } from 'react-router-dom';
import { contentPath } from '../../search';
import { ContentExposure } from './Traffic';
import { SourceLink, useWorkspace } from './UI';
import type { NewsCollection, NewsItem } from './NewsReading';
import './reading-overview.css';

export type NewsMedia = {url:string;full_url:string;alt:string;caption:string;source_url:string;credit:string;reuse_basis:string;version:string;reviewed_at:string;fit:'contain'|'cover'};
export const newsCategories:Record<string,[string,string]> = {model:['模型','Model'],agent:['Agent','Agent'],tool:['工具','Tool'],skill:['Skill','Skill'],harness:['Harness','Harness'],research:['研究','Research'],industry:['行业动态','Industry'],other:['其他动态','Other']};
const dateOnly=(value?:string|null)=>value?.match(/^\d{4}-\d{2}-\d{2}/)?.[0]||'';
const chinaDay=(date:Date)=>new Intl.DateTimeFormat('en-CA',{timeZone:'Asia/Shanghai',year:'numeric',month:'2-digit',day:'2-digit'}).format(date);
const publicationDay=(value?:string|null)=>value?chinaDay(new Date(value)):'';
const eventDay=(item:NewsItem)=>dateOnly(item.event_date)||dateOnly(item.source_published_at);
// Legacy records retain their original content. An absent category stays explicitly unclassified.
const linkedTypes:Record<string,string>={M:'model',A:'agent',T:'tool',S:'skill',H:'harness'};
const category=(item:NewsItem)=>(item.category&&newsCategories[item.category]?item.category:undefined)||linkedTypes[item.related.find(r=>/^CW-[MATSH]\d+$/.test(r.id))?.id[3]||'']||'other';

export function ReviewedImage({media,lead=false,compact=false}:{media:NewsMedia;lead?:boolean;compact?:boolean}) {
  const {pick}=useWorkspace();const [broken,setBroken]=useState(false),[fullBroken,setFullBroken]=useState(false),[expanded,setExpanded]=useState(false);
  const dialog=useRef<HTMLDialogElement>(null),trigger=useRef<HTMLButtonElement>(null);
  useEffect(()=>{setBroken(false);setFullBroken(false);setExpanded(false);dialog.current?.close();},[media.url,media.full_url]);
  return <figure className={'reviewed-image'+(lead?' lead-image':'')}>
    {!broken&&<button ref={trigger} className="image-trigger" aria-label={pick('放大图片：','Enlarge image: ')+media.alt} onClick={()=>{setExpanded(true);dialog.current?.showModal();}}><img src={media.url} alt={media.alt} loading={lead?'eager':'lazy'} decoding="async" referrerPolicy="no-referrer" style={{objectFit:media.fit}} onError={()=>setBroken(true)}/></button>}
    <figcaption>{compact?pick('点图查看完整说明','Open image for full notes'):media.caption} · <SourceLink url={media.source_url}>{pick('图片出处','Image source')}</SourceLink>{broken&&<span> · {pick('图片暂不可用，正文仍可阅读','Image unavailable; text remains readable')}</span>}</figcaption>
    <dialog ref={dialog} className="reading-image-dialog" aria-label={media.alt} onClose={()=>{setExpanded(false);trigger.current?.focus();}}><button className="button" autoFocus onClick={()=>dialog.current?.close()}>{pick('关闭图片','Close image')}</button>{expanded&&(!fullBroken?<img src={media.full_url} alt={media.alt} referrerPolicy="no-referrer" onError={()=>setFullBroken(true)}/>:<p role="status">{pick('完整图片暂不可用，请查看出处。','Full image unavailable; visit the source.')}</p>)}<p>{media.caption}</p><p>{media.credit} · {media.version} · {pick('图片核对：','Image reviewed: ')}{media.reviewed_at}</p><SourceLink url={media.source_url}>{pick('图片原始出处','Original image source')}</SourceLink><p className="muted">{media.reuse_basis}</p></dialog>
  </figure>;
}

export function NewsIndex({data,loading,error,reload,preview=false}:{data:NewsCollection|null;loading:boolean;error:string;reload:()=>void;preview?:boolean}) {
  const {pick}=useWorkspace();const [params,setParams]=useSearchParams(),location=useLocation();
  const range=['7','30','all'].includes(params.get('news_range')||'')?params.get('news_range')!:'7';
  const basis=params.get('news_sort')==='updated'?'updated':'event';
  const type=params.get('news_type')||'all',query=params.get('news_q')||'';
  const [input,setInput]=useState(query);useEffect(()=>setInput(query),[query]);
  const [today,setToday]=useState(()=>chinaDay(new Date()));
  useEffect(()=>{const refresh=()=>setToday(chinaDay(new Date()));const timer=setInterval(refresh,60000);window.addEventListener('focus',refresh);return()=>{clearInterval(timer);window.removeEventListener('focus',refresh);};},[]);
  const start=range==='all'?'':new Date(Date.parse(today+'T00:00:00Z')-(Number(range)-1)*86400000).toISOString().slice(0,10);
  const items=!loading&&!error?data?.items||[]:[];
  const day=(item:NewsItem)=>basis==='event'?eventDay(item):publicationDay(item.publication?.updated_at);
  const matching=items.filter(item=>preview||((type==='all'||category(item)===type)&&(!query||[item.name,item.organization,item.title,item.summary,...item.related.map(r=>r.name)].join(' ').toLocaleLowerCase().includes(query.toLocaleLowerCase()))&&(!start||!!day(item)&&day(item)>=start&&day(item)<=today)))
    .sort((a,b)=>day(b).localeCompare(day(a))||a.id.localeCompare(b.id,undefined,{numeric:true}));
  const pages=Math.max(1,Math.ceil(matching.length/10));
  const rawPage=Number(params.get('news_page'));const page=Math.min(pages,Number.isSafeInteger(rawPage)&&rawPage>0?rawPage:1);
  const visible=preview?matching:matching.slice((page-1)*10,page*10);
  const highlights=items.filter(item=>item.highlight).slice(0,5);
  const change=(values:Record<string,string>)=>setParams(p=>{p.delete('news_page');for(const [key,value]of Object.entries(values)){if(value)p.set(key,value);else p.delete(key);}return p;},{preventScrollReset:true});
  const reset=()=>change({news_range:'all',news_type:'',news_q:'',news_sort:''});
  const remember=(id:string)=>{if(preview)return;try{sessionStorage.setItem('fieldtofit.reading.return',JSON.stringify({search:location.search,id}));}catch{/* Links and URL filters work without session storage. */}};
  const returnTo='/for-you'+location.search;
  const linkState=(id:string)=>({readingReturn:{url:returnTo,id}});
  const signature=visible.map(i=>i.id).join('|');
  const restored=useRef(false);
  useEffect(()=>{
    if(loading||error||!data||preview||restored.current)return;
    let id='';
    if(location.state?.readingRestore)id=location.state.readingRestore;
    else if(!location.hash){try{const saved=JSON.parse(sessionStorage.getItem('fieldtofit.reading.return')||'null');if(saved?.search===location.search)id=saved.id;sessionStorage.removeItem('fieldtofit.reading.return');}catch{/* Optional restoration only. */}}
    restored.current=true;if(!id)return;
    const frame=requestAnimationFrame(()=>{const node=document.getElementById('news-'+id.toLowerCase())||document.getElementById('news-overview');node?.focus({preventScroll:true});node?.scrollIntoView({block:'start'});});return()=>cancelAnimationFrame(frame);
  },[data,loading,error,signature,preview,location.search,location.state,location.hash]);
  const hashId=/^#news-(d-\d+)$/i.exec(location.hash)?.[1].toUpperCase();
  const excluded=hashId&&!visible.some(i=>i.id===hashId)?items.find(i=>i.id===hashId):undefined;
  return <section className="news-section">
    <div className="platform-section-heading"><h2 id="recent-news" tabIndex={-1}>{pick('近期动态','Recent developments')}</h2><span>{data?.reviewed_at}</span></div>
    <div className="section-overview"><strong>{data?.title||pick('从变化读到采用条件','From changes to adoption conditions')}</strong><p>{pick('本期速览提炼已审内容；发布记录保留事件日期、解读和原始出处。','The briefing highlights reviewed material; the archive retains event dates, notes and sources.')}</p></div>
    {loading&&<p role="status">{pick('正在读取动态…','Loading developments…')}</p>}{error&&<div role="alert"><p>{pick('动态暂时无法读取。','Developments are unavailable.')}</p><button className="button" onClick={reload}>{pick('重试','Retry')}</button></div>}
    {!!data&&!loading&&!error&&<>
    <section className="news-glance glance-b"><div className="platform-section-heading"><h3 id="news-overview" tabIndex={-1}>{pick('本期速览','At a glance')}</h3><span>{pick('整理日期：','Edited: ')}{data.reviewed_at}</span></div>
      <div className="glance-layout">{highlights.map((item,i)=><article key={item.id} className={(i===0?'glance-lead':'glance-secondary')+(item.media?' has-media':'')}><div className="glance-copy"><h4><Link to={contentPath(item.id)} state={linkState(item.id)} onClick={()=>remember(item.id)}>{item.name}</Link></h4><ContentExposure id={item.id}><p>{item.summary}</p></ContentExposure>{i===0&&item.interpretation[0]&&<p className="glance-note muted">{item.interpretation[0].text}</p>}<Link to={contentPath(item.id)} state={linkState(item.id)} onClick={()=>remember(item.id)}>{pick('查看完整资料','Read full details')} ↗</Link></div>{item.media&&<ReviewedImage media={item.media} lead={i===0} compact={i!==0}/>}</article>)}</div>
      {!highlights.length&&<p>{pick('本期暂无已审精选。可继续浏览发布记录。','No reviewed highlights in this edition. Browse the archive below.')}</p>}
    </section>
    <div className="platform-section-heading"><h3 id="news-releases" tabIndex={-1}>{pick('发布与更新','Releases & updates')}</h3><span>{pick('累计收录 ','Collected ')}{data.total}{pick(' 条',' records')}</span></div>
    {!preview&&<form className="release-filters" onSubmit={e=>{e.preventDefault();change({news_q:input.trim()});}}>
      <label>{pick('时间范围','Time range')}<select aria-label={pick('时间范围','Time range')} value={range} onChange={e=>change({news_range:e.target.value})}><option value="7">{pick('近7日','Last 7 days')}</option><option value="30">{pick('近30日','Last 30 days')}</option><option value="all">{pick('全部时间','All time')}</option></select></label>
      <label>{pick('日期口径','Date basis')}<select aria-label={pick('日期口径','Date basis')} value={basis} onChange={e=>change({news_sort:e.target.value})}><option value="event">{pick('事件／来源发布','Event / source release')}</option><option value="updated">{pick('最近收录／更新','Recently added / revised')}</option></select></label>
      <label>{pick('内容类型','Content type')}<select aria-label={pick('内容类型','Content type')} value={type} onChange={e=>change({news_type:e.target.value})}><option value="all">{pick('全部类型','All types')}</option>{Object.entries(newsCategories).map(([key,label])=><option key={key} value={key}>{pick(...label)}</option>)}</select></label>
      <label>{pick('对象／关键词','Object / keyword')}<input type="search" aria-label={pick('对象／关键词','Object / keyword')} value={input} onChange={e=>setInput(e.target.value)} maxLength={200}/></label><button className="button">{pick('查找动态','Find developments')}</button>
    </form>}
    <p className="release-status" role="status">{preview?pick('私密预览 · 当前条目','Private preview · current record'):pick(`${range==='all'?'全部时间':start+' — '+today} · ${basis==='event'?'事件／来源日期':'本站实际收录／修订日期'} · 匹配 ${matching.length} 条 · 日期未明确 ${items.filter(i=>!day(i)).length} 条（全部时间可查）`,`${range==='all'?'All time':start+' — '+today} · ${basis==='event'?'Event / source dates':'Actual publication / revision dates'} · ${matching.length} matches · ${items.filter(i=>!day(i)).length} undated (available under All time)`)}</p>
    {excluded&&<p className="platform-notice" id={'news-'+excluded.id.toLowerCase()} tabIndex={-1}>{pick('链接指向的条目在当前筛选或页码之外：','This linked item is outside this filter or page: ')}<Link to={contentPath(excluded.id)} state={linkState(excluded.id)}>{excluded.title}</Link></p>}
    <div className="release-list">{visible.map((item,i)=><div key={item.id}>{(i===0||day(item)!==day(visible[i-1]))&&<h4 className="release-date">{day(item)||pick('日期未明确','Date unconfirmed')}</h4>}<article className="release-row" id={'news-'+item.id.toLowerCase()} tabIndex={-1}>
      <h4><Link to={contentPath(item.id)} state={linkState(item.id)} onClick={()=>remember(item.id)}>{item.title}</Link></h4><ContentExposure id={item.id}><p>{item.summary}</p></ContentExposure>
      <p className="news-meta">{pick(...newsCategories[category(item)])}{!item.category&&category(item)!=='other'?pick('相关',' related'):''} · {item.name} · {item.source_published_at?pick('官方发布 ','Source released ')+item.source_published_at:pick('来源发布日期未明确','Source date unconfirmed')}{item.event_date&&item.event_date!==item.source_published_at?' · '+pick('事件日期 ','Event date ')+item.event_date:''} · {pick('核对 ','Checked ')}{item.checked_at}</p>
      <details><summary>{pick('展开要点与来源','Key changes and sources')}</summary><ul>{item.interpretation.slice(0,3).map((point,j)=><li key={j}><strong>{point.title}</strong><p>{point.text}</p>{point.source_ids.map(id=>{const source=item.sources.find(s=>s.id===id);return source&&<SourceLink key={id} url={source.url}>{source.title}</SourceLink>;})}</li>)}</ul>{item.publication&&<p className="muted">{pick('本站首次发布：','First published here: ')}{item.publication.first_published_at||pick('历史日期未留存','Historical date not retained')} · {pick('最近修订：','Last revised: ')}{item.publication.updated_at}</p>}<Link to={contentPath(item.id)} state={linkState(item.id)} onClick={()=>remember(item.id)}>{pick('查看完整资料','Read full details')} ↗</Link></details>
    </article></div>)}</div>
    {!matching.length&&<div className="release-empty"><p>{pick('当前筛选没有匹配条目。','No records match these filters.')}</p><button className="button" onClick={reset}>{pick('清除筛选，查看全部','Clear filters and view all')}</button></div>}
    {!preview&&matching.length>0&&<nav className="release-pagination" aria-label={pick('动态分页','News pagination')}><span>{pick(`第 ${page} / ${pages} 页 · 每页10条`,`Page ${page} / ${pages} · 10 per page`)}</span>{[-1,1].map(step=><button key={step} className="button" disabled={step<0?page===1:page===pages} onClick={()=>{change({news_page:String(page+step)});requestAnimationFrame(()=>{document.getElementById('news-releases')?.focus({preventScroll:true});document.getElementById('news-releases')?.scrollIntoView({block:'start'});});}}>{step<0?pick('上一页动态','Previous developments'):pick('下一页动态','Next developments')}</button>)}</nav>}
    </>}
  </section>;
}
