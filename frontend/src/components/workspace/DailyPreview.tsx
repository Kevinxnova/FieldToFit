import { useEffect, useState } from 'react';
import { Link } from '@fieldtofit/locale/router';
import { useReadingUpdates } from '../../api/reading';
import { useWorkspace } from './UI';
import './DailyPreview.css';

export type DailyPreviewData = {
  today:string; due:boolean; timezone:string; status:'published'|'scheduled'|'delayed';
  issue:null|{
    date:string; kind:string; headline:string; intro:string; path:string;
    highlights:{id:string;section:string;title:string;summary:string}[];
    publication:{revision:number;content_hash:string;published_at:string;first_published_at:string};
  };
};
const sectionNames:Record<string,[string,string]>={companies:['AI公司','AI companies'],chips:['AI芯片','AI chips'],robotics:['具身智能','Embodied AI'],infrastructure:['基础设施','Infrastructure'],policy:['监管政策','Policy'],markets:['AI股市','AI markets']};
const beijingDay=()=>new Intl.DateTimeFormat('sv-SE',{timeZone:'Asia/Shanghai',year:'numeric',month:'2-digit',day:'2-digit'}).format(new Date());
const publicationTime=(value:string,zh:boolean)=>new Date(value).toLocaleString(zh?'zh-CN':'en-GB',{timeZone:'Asia/Shanghai',year:'numeric',month:'2-digit',day:'2-digit',hour:'2-digit',minute:'2-digit',hour12:false});

export function DailyPreview({data,loading,error,retry}:{data?:DailyPreviewData;loading:boolean;error:string;retry:()=>void}){
  const {pick,zh}=useWorkspace();
  const updates=useReadingUpdates(false);
  const [today,setToday]=useState(beijingDay);
  useEffect(()=>{
    const check=()=>setToday(beijingDay());
    const timer=setInterval(check,60000);window.addEventListener('focus',check);document.addEventListener('visibilitychange',check);
    return()=>{clearInterval(timer);window.removeEventListener('focus',check);document.removeEventListener('visibilitychange',check);};
  },[]);
  const issue=error?null:data?.issue;
  // A reader may defer a normal content update across midnight. Never relabel an old issue as today.
  const current=issue?.kind==='daily'&&issue.date===today;
  const highlights=issue?.highlights.slice(0,3)||[];
  const edition=issue?issue.path+'?revision='+issue.publication.revision:'';
  return <section id="daily-preview" className="daily-preview" tabIndex={-1} aria-labelledby="daily-preview-title" data-state={error?'error':loading&&!data?'loading':issue?current?'today':'previous':'empty'}>
    <header className="dp-masthead"><div><p className="dp-brand">FieldToFit Daily</p><h2 id="daily-preview-title">{current?pick('今日 AI 日报','Today’s AI Daily'):issue?pick('最近一期 · AI 日报','Latest edition · AI Daily'):pick('AI 日报','AI Daily')}</h2></div>
      {issue&&<div className="dp-date"><time dateTime={issue.date}><strong>{issue.date.slice(-2)}</strong><span>{issue.date.slice(0,7).replace('-',' / ')}</span></time>{issue.kind==='review_sample'&&<small>{pick('晚间审阅样刊','Evening review sample')}</small>}</div>}
    </header>
    {error||!data&&!loading?<div className="dp-state" role="alert"><p>{pick('日报预览暂时无法读取。','The daily preview is temporarily unavailable.')}</p><button type="button" className="text-button" onClick={retry}>{pick('重试','Retry')}</button></div>:loading&&!data?<p className="dp-state" role="status">{pick('正在读取日报…','Loading the daily preview…')}</p>:<>
      {!current&&<p className="dp-status">{updates.pending?pick('内容有更新，当前保留上次读取的期次。','Updates are available. Showing the previously read edition.'):data?.today!==today||updates.notice==='offline'?<>{pick('尚未确认今日期次。','Today’s edition has not been checked yet.')} <button className="text-button" onClick={retry}>{pick('检查最新一期','Check latest edition')}</button></>:pick('今日日报尚未出刊。','Today’s issue has not been published yet.')} <span>{pick('每日北京时间 09:00 更新','Updated daily at 09:00 Beijing time')}</span></p>}
      {issue?<>
        <div className="dp-lead"><p className="dp-kicker">{pick('本期导读','IN THIS EDITION')}</p><h3><Link to={edition}>{issue.headline}</Link></h3><p className="dp-intro">{issue.intro}</p></div>
        {highlights.length>0&&<div className="dp-highlights" data-count={highlights.length}>{highlights.map((story,index)=><article className="dp-story" key={story.id}>
          <p className="dp-kicker">0{index+1} / {pick(...(sectionNames[story.section]||['今日重点','Highlights']))}</p>
          <h4><Link to={edition+'#daily-story-'+story.id}>{story.title}</Link></h4><p>{story.summary}</p>
        </article>)}</div>}
        <footer className="dp-footer"><div className="dp-publication"><span>{pick('实际出刊','Published')} <time dateTime={issue.publication.first_published_at}>{publicationTime(issue.publication.first_published_at,zh)}</time></span>{issue.publication.revision>1&&<span>{pick('修订于','Revised')} <time dateTime={issue.publication.published_at}>{publicationTime(issue.publication.published_at,zh)}</time> · r{issue.publication.revision}</span>}<small>{pick('北京时间','Beijing time')}</small></div><div className="dp-actions"><Link className="dp-archive" to="/for-you/daily/archive">{pick('往期日报','Past editions')} →</Link><Link className="dp-read" to={edition}>{pick('阅读完整日报','Read this edition')} <span aria-hidden="true">↗</span></Link></div></footer>
      </>:<div className="dp-empty"><p>{pick('完整期刊发布后，会在这里展示导读与重点。','The introduction and highlights will appear here when an edition is published.')}</p><Link to="/for-you/daily/archive">{pick('查看日报归档','View daily archive')} →</Link></div>}
    </>}
  </section>;
}
