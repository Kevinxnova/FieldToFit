import { Link, useSearchParams } from 'react-router-dom';
import { contentPath } from '../../search';
import { SourceLink, useWorkspace } from './UI';
import { ContentExposure, trackAction } from './Traffic';
import type { NewsCollection, NewsItem } from './NewsReading';
import './codex-progress.css';

export type {CodexEvent,CodexTopic} from './codexData';
export {codexTypes} from './codexData';
import { codexTypes, dayItems } from './codexData';
import { CodexOverview } from './CodexOverview';
import { SourcePosts } from './SourcePostCard';
import { CodexShare } from './CodexShare';
import { CodexRoundup } from './CodexRoundup';

export function CodexProgress({data,preview=false}:{data:NewsCollection;preview?:boolean}) {
  const {pick,notify}=useWorkspace();const [params,setParams]=useSearchParams();
  const topic=data.codex_progress;
  if(!topic?.days.length)return null;
  const today=new Intl.DateTimeFormat('sv-SE',{timeZone:'Asia/Shanghai'}).format(new Date());
  const catchupEnd=new Date(Date.parse(topic.end_date+'T00:00:00Z')+86400000).toISOString().slice(0,10);
  const archived=today>catchupEnd;
  const selected=params.get('codex_date');
  const current=selected==='all'?'all':topic.days.some(d=>d.date===selected)?selected!:topic.days[0].date;
  const days=current==='all'?topic.days:topic.days.filter(d=>d.date===current);
  const byId=new Map([...(data.referenced_items||[]),...data.items].map(i=>[i.id,i]));
  const roundups=topic.roundups||[];
  const officialSteps=new Map(roundups.flatMap(r=>r.steps.map(s=>[s.news_id,`${r.official_day}.${s.number}`] as const)));
  const choose=(value:string)=>{const next=new URLSearchParams(params);next.set('codex_date',value);setParams(next,{replace:true,preventScrollReset:true});};
  const exportLogs=async()=>{
    const ids=days.flatMap(d=>dayItems(d,byId).map(i=>i.id));
    const summaries=roundups.filter(r=>days.some(d=>d.date===r.date));
    const references=[...new Set(summaries.flatMap(r=>r.steps.map(s=>s.news_id)))].filter(id=>!ids.includes(id));
    const value=JSON.stringify({schema_version:'fieldtofit.codex-progress.v1',revision:data.revision,topic:{...topic,days,roundups:summaries,total:ids.length},items:ids.map(id=>byId.get(id)),referenced_items:references.map(id=>byId.get(id)),reading:[...ids,...references].map(id=>({tool:'curated_news',arguments:{id,revision:data.revision}}))},null,2);
    try{await navigator.clipboard.writeText(value);ids.forEach(id=>trackAction('handoff_copy',id));notify(pick('所选日志、出处和AI读取方式已复制','Selected logs, sources and AI reading instructions copied'));}
    catch{const url=URL.createObjectURL(new Blob([value],{type:'application/json'}));const a=document.createElement('a');a.href=url;a.download='codex-28-days-'+current+'.json';a.click();URL.revokeObjectURL(url);}
  };
  return <section className="codex-progress" aria-labelledby="news-codex-28-days">
    <div className="codex-heading"><div><p className="codex-kicker">CODEX · 28 DAYS</p><h3 id="news-codex-28-days" tabIndex={-1}>{pick(topic.title,topic.title_en)}</h3><p className="codex-subtitle">{pick(topic.subtitle,topic.subtitle_en)}</p></div><span className="codex-period">{topic.start_date} — {topic.end_date}<small>{pick('北京时间 · 28个日历日','Beijing time · 28 calendar days')}</small></span></div>
    <p className="codex-intro">{pick('记录 Codex／ChatGPT Work 的每日变化，其他 OpenAI 发布单独呈现。选择一个日期，阅读具体更新和官方出处。','Daily changes to Codex / ChatGPT Work, with other OpenAI releases presented separately. Choose a date to read the updates and official sources.')}</p>
    <details className="codex-background"><summary>{pick('28天从哪里开始？','Where do the 28 days begin?')}</summary><p>{pick(topic.pledge.summary,topic.pledge.summary_en)}</p><p>{pick('承诺发布于北京时间10月5日04:33，作为本站日历 Day 1。官方改进的 Day 编号另行保留；两者可能跨日。只提供日期的公告按来源日期标注，不推算北京时刻。承诺背景不计为更新。','The pledge was posted on October 5 at 04:33 Beijing time, our calendar Day 1. Official improvement day numbers are preserved separately and may differ across time zones. Date-only announcements keep their source date. The pledge itself is background, not an update.')}</p><p className="muted">{pick('承诺与提速帖的时刻由原帖ID推导，并与官方社区原帖嵌入交叉核对。','The pledge and speed announcement times are derived from post IDs and cross-checked against original embeds on the official community.')}</p><SourceLink url={topic.pledge.url}>{pick('Tibo 原帖','Tibo’s original post')}</SourceLink> · <SourceLink url={topic.pledge.evidence_url}>{pick('官方社区原帖嵌入','Original embed on the official community')}</SourceLink></details>
    {!preview&&<CodexShare/>}
    <CodexOverview topic={topic} byId={byId} current={current} choose={choose} today={today} catchupEnd={catchupEnd} preview={preview}/>
    <div className="codex-timeline" aria-live="polite" aria-atomic="false">{days.map(d=>{
      const summaries=roundups.filter(r=>r.date===d.date);
      const event=(id:string,groupBadge=false)=>byId.get(id)&&<Event key={id} item={byId.get(id)!} officialStep={officialSteps.get(id)} groupBadge={groupBadge} roundupUrls={summaries.map(r=>r.source_post.url)}/>;
      return <section key={d.date} className="codex-day" aria-labelledby={'codex-day-'+d.date}><header><time dateTime={d.date}>{d.date}</time><h4 id={'codex-day-'+d.date}>{pick('日历','Calendar')} Day {d.calendar_day}</h4></header>{summaries.map(r=><CodexRoundup key={r.source_post.url} roundup={r} byId={byId}/>)}<div className="codex-day-body">{summaries.length?<div className="codex-ordered">{dayItems(d,byId).length>0&&<h5>{pick('当日更新详情 · 按官方顺序','Today’s update details · official order')}</h5>}{dayItems(d,byId).map(i=>event(i.id,true))}</div>:<>{d.codex_ids.length>0&&<div className="codex-main"><h5>Codex / ChatGPT Work</h5>{d.codex_ids.map(id=>event(id))}</div>}{d.other_openai_ids.length>0&&<div className="codex-other"><h5>{pick('其他 OpenAI 更新','Other OpenAI updates')}</h5>{d.other_openai_ids.map(id=>event(id))}</div>}</>}</div></section>;
    })}</div>
    {!preview&&<div className="codex-footer"><p>{archived?pick('专题日志已存档，可继续阅读已有更新。','The log is archived; published updates remain available.'):pick('每日22:00（北京时间）检查；晚到的证据补回原发布日。','Checked daily at 22:00 Beijing time; late evidence is added to its original publication date.')}</p><button className="text-button" onClick={exportLogs}>{pick('将所选日志交给我的 AI','Give selected logs to my AI')} ↗</button></div>}
  </section>;
}

function Event({item,officialStep,groupBadge=false,roundupUrls=[]}:{item:NewsItem;officialStep?:string;groupBadge?:boolean;roundupUrls?:string[]}) {
  const {pick}=useWorkspace();const event=item.codex_28_days!;const type=codexTypes[event.type];
  const time=event.announced_at?new Date(event.announced_at).toLocaleTimeString('en-GB',{timeZone:'Asia/Shanghai',hour:'2-digit',minute:'2-digit'}):null;
  return <article className={'codex-event'+(event.group==='other_openai'?' codex-event-other':'')}><p className="codex-event-meta"><span>{pick(type[0],type[1])}</span>{(officialStep||event.official_day)&&<strong>{pick('官方','Official')} {officialStep||`Day ${event.official_day}`}</strong>}{groupBadge&&<span className={event.group==='other_openai'?'codex-group-other':''}>{event.group==='codex'?'Codex / Work':pick('其他 OpenAI','Other OpenAI')}</span>}<span>{time?time+pick(' 北京时间',' Beijing time'):pick('来源日期 · 未提供时刻','Source date · time not supplied')}</span></p><h6><Link to={contentPath(item.id)}>{item.title}</Link></h6><ContentExposure id={item.id}><p>{item.summary}</p></ContentExposure>{event.reset&&<p>{event.reset.plans} · {event.reset.scope} · {pick('生效：','Effective: ')}{new Date(event.reset.effective_at).toLocaleString('sv-SE',{timeZone:'Asia/Shanghai'})}</p>}<SourcePosts posts={event.source_posts?.filter(p=>!roundupUrls.includes(p.url))}/><div className="codex-sources">{item.sources.slice(0,2).map(s=><SourceLink key={s.id} url={s.url}>{s.title}</SourceLink>)}</div><details><summary>{pick('影响、使用条件与依据','Impact, conditions and evidence')}</summary>{item.interpretation.map((p,i)=><div key={i}><strong>{p.title}</strong><p>{p.text}</p><p className="muted">{p.locator}</p></div>)}{item.note&&<p className="muted">{item.note}</p>}<Link to={contentPath(item.id)}>{pick('完整资料与出处','Full record and sources')} · {item.id} ↗</Link></details></article>;
}
