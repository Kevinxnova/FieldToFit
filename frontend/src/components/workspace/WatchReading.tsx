import { useEffect, useRef, useState } from 'react';
import { Link, useLocation } from '@fieldtofit/locale/router';
import { contentPath } from '../../search';
import type { NewsItem } from './NewsReading';
import { WatchText, type WatchItem } from './ContinuousWatch';
import { useWorkspace } from './UI';
import './watchReading.css';

export type WatchEvent = {date:string|null;date_kind:'release'|'source'|'commit'|'review';title:string;url?:string;news_id?:string;profile_id?:string;basis:string};
export type WatchOverviewData = {developer:string;category:string;purpose:string;recent_event:WatchEvent};
export type WatchMilestone = {id:string;news_id:string;date:string;date_kind:string;kind:'model'|'product';name:string;price:string|null;price_condition:string;summary:string;points:NewsItem['interpretation'];sources:NewsItem['sources']};

function DateLabel({kind}:{kind:string}) {
  const {pick}=useWorkspace();
  return <>{kind==='review'?pick('资料核验','Profile review'):kind==='commit'?pick('提交日期','Commit date'):kind==='source'?pick('来源日期','Source date'):pick('事件日期','Event date')}</>;
}

export function WatchOverview({items,name}:{items:WatchItem[];name:string}) {
  const {pick}=useWorkspace();
  return <div className="watch-overview">
    <table>
      <caption><span>{name} · {pick('总览','Overview')}</span><span>{items.length} {pick('项','profiles')}</span></caption>
      <thead><tr>{[pick('项目 / 开发方','Project / Developer'),pick('定位类别','Category'),pick('核心用途','Purpose'),pick('最近事件','Recent event')].map(s=><th scope="col" key={s}>{s}</th>)}</tr></thead>
      <tbody>{items.map(item=>{const o=item.overview,e=o?.recent_event;return <tr key={item.id}>
        <th scope="row"><Link to={contentPath(item.id)}>{item.name}<span aria-hidden="true"> ↗</span></Link><small>{o?.developer||'-'}</small></th>
        <td data-label={pick('定位类别','Category')}><span className="watch-category">{o?.category||'-'}</span></td>
        <td data-label={pick('核心用途','Purpose')}>{o?.purpose||'-'}</td>
        <td className="watch-recent" data-label={pick('最近事件','Recent event')}>{e?<>
          <small><DateLabel kind={e.date_kind}/> · {e.date?<time dateTime={e.date}>{e.date}</time>:pick('日期待核','Date unconfirmed')}</small>
          {e.news_id?<Link to={contentPath(e.news_id)}>{e.title}</Link>:<a href={e.url} target="_blank" rel="noopener noreferrer">{e.title} ↗</a>}
          {e.date_kind==='review'&&<small>{pick('档案记录，非新发布','Dossier record, not a new release')}</small>}
        </>:<Link to={contentPath(item.id)}>{pick('查看已审资料记录','Read reviewed profile record')}</Link>}</td>
      </tr>;})}</tbody>
    </table>
    <p className="watch-overview-note">{pick('最近事件优先展示近期编辑重点；没有热度排名数据。较早记录保留真实日期，资料核验不等于发布。','Recent events prioritize editorial highlights; no popularity ranking is available. Older records retain their dates; review dates are not release dates.')}</p>
  </div>;
}

export function WatchMilestones({items,profile}:{items:WatchMilestone[];profile:string}) {
  const {pick}=useWorkspace();
  const [selected,setSelected]=useState<string|null>(null);
  const [edges,setEdges]=useState({start:true,end:true});
  const [mobile,setMobile]=useState(()=>window.matchMedia('(max-width:560px)').matches);
  const rail=useRef<HTMLDivElement>(null);
  const triggers=useRef(new Map<string,HTMLButtonElement>());
  const selectedItem=items.find(item=>item.id===selected);
  let column=1;
  const positions=new Map(items.map((item,index)=>{if(index)column+=items[index-1].kind===item.kind?2:1;return [item.id,column];}));
  const updateEdges=()=>{const el=rail.current;if(el)setEdges({start:el.scrollLeft<2,end:el.scrollLeft+el.clientWidth>=el.scrollWidth-2});};
  useEffect(()=>{
    const query=window.matchMedia('(max-width:560px)');const change=()=>setMobile(query.matches);
    query.addEventListener('change',change);return ()=>query.removeEventListener('change',change);
  },[]);
  useEffect(()=>{
    const el=rail.current;if(!el)return;
    el.scrollLeft=el.scrollWidth;updateEdges();
    const observer=new ResizeObserver(updateEdges);observer.observe(el);
    return ()=>observer.disconnect();
  },[items]);
  const close=()=>{const id=selected;setSelected(null);if(id)triggers.current.get(id)?.focus();};
  const move=(direction:number)=>{const el=rail.current;if(el)el.scrollBy({left:direction*304,behavior:window.matchMedia('(prefers-reduced-motion: reduce)').matches?'instant':'smooth'});};
  const panel=(item:WatchMilestone)=><div className="watch-milestone-detail" id={'milestone-detail-'+item.id} role="region" aria-label={item.name}>
    <div className="watch-reading-heading"><h4>{item.name}</h4><button onClick={close} className="text-button">{pick('收起','Close')} ↑</button></div>
    <p><WatchText text={item.summary}/></p>
    <ul>{item.points.map((p,i)=><li key={i}><strong>{p.title}</strong><p><WatchText text={p.text}/></p></li>)}</ul>
    <div className="watch-event-actions"><Link to={contentPath(item.news_id)}>{pick('完整记录','Full record')} ↗</Link>{item.sources.slice(0,2).map(s=><a key={s.url} href={s.url} target="_blank" rel="noopener noreferrer">{s.title} ↗</a>)}</div>
  </div>;
  return <section className="watch-milestones" aria-labelledby={'milestones-'+profile}>
    <div className="watch-reading-heading"><div><h3 id={'milestones-'+profile}>{pick('大事记','Milestones')}</h3><span>{items[0]?.date.slice(0,4)} — {pick('至今','present')}</span></div>
      <div className="watch-timeline-controls"><button aria-label={pick('查看较早节点','Earlier milestones')} disabled={edges.start} onClick={()=>move(-1)}>←</button><button aria-label={pick('查看较新节点','Later milestones')} disabled={edges.end} onClick={()=>move(1)}>→</button></div>
    </div>
    <p className="watch-price-note">{mobile?pick('最新在前。','Newest first. '):pick('模型在上，产品在下。','Models above, products below. ')}{pick('价格：发布时 API 标准输入 / 输出，美元 / 百万 tokens；“-”表示未核实。点击节点查看更新要点。','Price: launch API standard input / output, USD per million tokens; “-” means unverified. Select a milestone for details.')}</p>
    <div className="watch-timeline" ref={rail} onScroll={updateEdges} role="region" tabIndex={0} aria-label={mobile?pick('大事记，最新在前','Milestones, newest first'):pick('横向大事记，可左右滚动','Milestones, scroll horizontally')}>
      <ol>{(mobile?[...items].reverse():items).map(item=><li className={'watch-timeline-node '+item.kind+(selected===item.id?' selected':'')} style={{gridColumn:`${positions.get(item.id)} / span 2`,gridRow:1}} key={item.id}>
        <button ref={el=>{if(el)triggers.current.set(item.id,el);else triggers.current.delete(item.id);}} className="watch-node-card" aria-expanded={selected===item.id} aria-controls={'milestone-detail-'+item.id} onClick={()=>setSelected(selected===item.id?null:item.id)}>
          <span className="watch-node-date"><time dateTime={item.date}>{item.date}</time><span>{item.kind==='model'?pick('模型','Model'):pick('产品','Product')}</span>{item.date_kind==='source'&&<small>{pick('来源日期','Source date')}</small>}</span>
          <strong>{item.name}</strong>
          {item.kind==='model'&&<span className="watch-node-price">{pick('价格：','Price: ')}{item.price?item.price.split(' / ').map(p=>'$'+p).join(' / '):'-'}{item.price_condition&&<small>{item.price_condition}</small>}</span>}
          <span className="watch-node-toggle" aria-hidden="true">{selected===item.id?'−':'+'}</span>
        </button><span className="watch-timeline-dot" aria-hidden="true"/>
        {mobile&&selected===item.id&&<div className="watch-mobile-milestone">{panel(item)}</div>}
      </li>)}</ol>
    </div>
    {!items.length&&<p className="watch-price-note">{pick('暂无已核实日期的大事记。','No milestones with reviewed dates yet.')}</p>}
    {!mobile&&selectedItem&&<div className="watch-desktop-milestone">{panel(selectedItem)}</div>}
  </section>;
}

export function WatchEvents({events,profile}:{events:NewsItem[];profile:string}) {
  const {pick}=useWorkspace();const location=useLocation();
  const restore=typeof location.state?.readingRestore==='string'?location.state.readingRestore:'';
  const [limit,setLimit]=useState(()=>Math.max(10,Math.ceil((events.findIndex(e=>'watch-event-'+e.id===restore)+1)/10)*10));
  useEffect(()=>{if(!restore)return;const frame=requestAnimationFrame(()=>{const node=document.getElementById(restore);node?.scrollIntoView({block:'start'});node?.focus({preventScroll:true});});return()=>cancelAnimationFrame(frame);},[restore]);
  const returnState=(id:string)=>({readingReturn:{url:contentPath(profile),id:'watch-event-'+id}});
  const categories:Record<string,string>={model:pick('模型','Model'),agent:'Agent',tool:pick('工具','Tool'),skill:'Skill',harness:'Harness',research:pick('研究','Research'),industry:pick('行业','Industry'),other:pick('其他','Other')};
  return <section className="watch-events" aria-labelledby={'events-'+profile}>
    <div className="watch-reading-heading"><h3 id={'events-'+profile}>{pick('FieldToFit 事件记录','FieldToFit event record')}</h3><span>{events.length} {pick('条','events')}</span></div>
    <p className="watch-price-note">{pick('最新在前 · 保留全部已审关联事件','Newest first · All reviewed related events')}</p>
    <ol>{events.slice(0,limit).map(event=>{const day=event.event_date||event.source_published_at;return <li key={event.id} className="watch-event-row" id={'watch-event-'+event.id} tabIndex={-1}>
      <div className="watch-event-date">{day?<><time dateTime={day}>{day.slice(5)}</time><span>{day.slice(0,4)}</span></>:<span>{pick('日期待核','Date unconfirmed')}</span>}<small><DateLabel kind={event.event_date?'release':'source'}/></small></div>
      <article><div className="watch-event-meta"><span>{categories[event.category||'other']}</span><span>{event.id}</span></div>
        <h4><Link to={contentPath(event.id)} state={returnState(event.id)}>{event.title}</Link></h4><p><WatchText text={event.summary}/></p>
        <details><summary>{pick('展开本站解读','Read FieldToFit notes')}</summary><ul>{event.interpretation.map((p,i)=><li key={i}><strong>{p.title}</strong><p><WatchText text={p.text}/></p></li>)}</ul>{event.note&&<p className="muted">{event.note}</p>}<div className="watch-event-actions">{event.sources.map(s=><a key={s.id} href={s.url} target="_blank" rel="noopener noreferrer">{s.title} ↗</a>)}</div></details>
        <div className="watch-event-actions"><Link to={contentPath(event.id)} state={returnState(event.id)}>{pick('完整记录','Full record')} ↗</Link>{event.publication?.updated_at&&<span>{pick('本站更新 ','Updated ')}{event.publication.updated_at.slice(0,10)}</span>}</div>
      </article>
    </li>;})}</ol>
    {events.length>limit&&<button className="button watch-load-events" onClick={()=>setLimit(limit+10)}>{pick('继续读取较早事件','Load earlier events')} · {Math.min(10,events.length-limit)}</button>}
    {!events.length&&<p>{pick('暂无已审事件记录。','No reviewed events yet.')}</p>}
  </section>;
}
