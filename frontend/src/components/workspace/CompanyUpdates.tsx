import { useEffect, useState } from 'react';
import { Link, useSearchParams } from '@fieldtofit/locale/router';
import type { NewsCollection, NewsItem } from './NewsReading';
import { SourceLink, useWorkspace } from './UI';
import { contentPath } from '../../search';
import './company-updates.css';

export type Company = 'openai'|'anthropic';
const names = {openai:'OpenAI',anthropic:'Anthropic'};
const products:Record<string,[string,string]> = {'codex':['Codex','Codex'],'chatgpt-work':['ChatGPT / Work','ChatGPT / Work'],'claude-code':['Claude Code','Claude Code'],claude:['Claude','Claude'],'models-api':['模型与 API','Models & API'],other:['其他更新','Other updates']};

function UpdateList({items,company}:{items:NewsItem[];company:Company}){
  const {pick}=useWorkspace();
  return <ul className="company-update-list">{items.map(item=>{const event=item.company_update!;return <li key={item.id} id={company+'-'+item.id} tabIndex={-1}>
    <time dateTime={event.announced_at||event.date}>{event.display_time}</time><span className="company-date-kind"> {event.announced_at?pick('北京','Beijing'):event.date_precision==='source_date'?pick('来源日期','Source date'):''}</span>{' — '}
    <strong><Link to={contentPath(item.id)}>{item.title}</Link></strong><p>{item.summary}</p>
    <div className="company-update-links"><Link to={contentPath(item.id)}>{pick('完整记录','Full record')} ↗</Link>{item.sources[0]&&<SourceLink url={item.sources[0].url}>{pick('原始出处','Original source')}</SourceLink>}</div>
  </li>;})}</ul>;
}

export function CompanyUpdatesHome({company,items,ready}:{company:Company;items:NewsItem[];ready:boolean}){
  const {pick}=useWorkspace(),[params,setParams]=useSearchParams();
  const key=company+'_show',expanded=params.get(key)==='10';
  return <section className="home-section company-updates" aria-labelledby={company+'-updates'}>
    <header className="platform-section-heading"><h2 id={company+'-updates'} tabIndex={-1}>{names[company]} {pick('更新','updates')}</h2><Link to={'/for-you/'+company}>{pick('完整专题','Full topic')} ↗</Link></header>
    <UpdateList company={company} items={items.slice(0,expanded?10:3)}/>
    {ready&&!items.length&&<p className="muted">{pick('暂无已发布记录。','No published entries yet.')}</p>}
    {items.length>3&&<button className="text-button" aria-expanded={expanded} onClick={()=>setParams(p=>{if(expanded)p.delete(key);else p.set(key,'10');return p;},{preventScrollReset:true})}>{expanded?pick('收起，显示最新3条','Collapse to latest 3'):pick('展开更多（最多10条）','Show more (up to 10)')}</button>}
  </section>;
}

export function HistoricalTopics({total}:{total?:number}){
  const {pick}=useWorkspace();
  return <section className="home-section historical-topics" id="historical-topics" tabIndex={-1}><details><summary>{pick('历史专题','Historical topics')}</summary><div id="news-codex-28-days"><h3><Link to="/for-you/codex">{pick('Codex 28天进化日志','Codex: 28 Days of Progress')} ↗</Link></h3><p>{pick('已结束 · 2026年10月5日至11月1日','Closed · October 5–November 1, 2026')}{total!==undefined&&` · ${total} ${pick('条日志','entries')}`}</p><p className="muted">{pick('保留跨至11月2日的官方Day 28及已审核补录。','Includes official Day 28 on November 2 and reviewed historical additions.')}</p></div></details></section>;
}

export function CompanyUpdatesPage({company,data}:{company:Company;data:NewsCollection}){
  const {pick}=useWorkspace(),[params,setParams]=useSearchParams();
  const product=params.get('product')||'',month=params.get('month')||'',query=params.get('topic_q')||'';
  const [input,setInput]=useState(query);useEffect(()=>setInput(query),[query]);
  const topic=data.company_topics?.[company];
  const items=data.items.filter(i=>i.company_update?.company===company);
  const found=items.filter(i=>(!product||i.company_update!.products.includes(product))&&(!month||i.company_update!.date.startsWith(month))&&(!query||[i.title,i.summary,i.name].join(' ').toLowerCase().includes(query.toLowerCase())));
  const pages=Math.max(1,Math.ceil(found.length/20));const requested=Number(params.get('topic_page'))||1;const page=Math.max(1,Math.min(pages,Math.floor(requested)));
  const update=(key:string,value:string)=>setParams(p=>{value?p.set(key,value):p.delete(key);p.delete('topic_page');return p;});
  return <section className="company-updates company-topic" aria-label={names[company]+pick('完整更新日志',' full update log')}>
    <p className="muted">{pick('自2026年11月2日起，按事件日期阅读已审核发布的更新。','Reviewed updates from November 2, 2026, ordered by event date.')}</p>
    <form className="company-topic-filters" onSubmit={e=>{e.preventDefault();update('topic_q',input);}}>
      <label>{pick('产品','Product')}<select value={product} onChange={e=>update('product',e.target.value)}><option value="">{pick('全部产品','All products')}</option>{product&&!topic?.products.includes(product)&&<option value={product}>{product}</option>}{topic?.products.map(id=><option key={id} value={id}>{pick(...(products[id]||[id,id]))}</option>)}</select></label>
      <label>{pick('月份','Month')}<select value={month} onChange={e=>update('month',e.target.value)}><option value="">{pick('全部月份','All months')}</option>{month&&!topic?.months.includes(month)&&<option value={month}>{month}</option>}{topic?.months.map(m=><option key={m}>{m}</option>)}</select></label>
      <label>{pick('关键词','Keyword')}<input value={input} onChange={e=>setInput(e.target.value)} type="search"/></label><button className="button">{pick('查找更新','Find updates')}</button>
    </form>
    {(product||month||query)&&<button className="text-button" onClick={()=>setParams(p=>{['product','month','topic_q','topic_page'].forEach(k=>p.delete(k));return p;})}>{pick('清除筛选','Clear filters')}</button>}
    <p className="company-topic-count" role="status">{found.length} {pick('条记录','entries')}</p>
    <UpdateList company={company} items={found.slice((page-1)*20,page*20)}/>
    {!found.length&&<p>{pick('当前筛选没有匹配记录。','No entries match these filters.')}</p>}
    {pages>1&&<nav className="platform-actions" aria-label={pick('专题分页','Topic pages')}><button className="text-button" disabled={page===1} onClick={()=>setParams(p=>{p.set('topic_page',String(page-1));return p;})}>{pick('上一页','Previous')}</button><span>{page} / {pages}</span><button className="text-button" disabled={page===pages} onClick={()=>setParams(p=>{p.set('topic_page',String(page+1));return p;})}>{pick('下一页','Next')}</button></nav>}
  </section>;
}
