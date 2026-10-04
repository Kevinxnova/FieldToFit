import { Link } from 'react-router-dom';
import { contentPath } from '../../search';
import { useWorkspace } from './UI';
import type { NewsItem } from './NewsReading';

/** Summarize only published, explicitly related records; review dates do not imply a new release. */
export function ProfileNewsOverview({news,ids,limit=2}:{news:NewsItem[];ids:string[];limit?:number}) {
  const {pick}=useWorkspace();
  const today=new Intl.DateTimeFormat('en-CA',{timeZone:'Asia/Shanghai',year:'numeric',month:'2-digit',day:'2-digit'}).format(new Date());
  const start=new Date(Date.parse(today+'T00:00:00Z')-6*86400000).toISOString().slice(0,10);
  const related=news.filter(n=>{const date=n.event_date||n.source_published_at;return date&&date>=start&&date<=today&&n.related.some(r=>ids.includes(r.id));}).sort((a,b)=>(b.event_date||b.source_published_at||'').localeCompare(a.event_date||a.source_published_at||'')).slice(0,limit);
  if(!related.length)return null;
  return <p className="overview-coverage">{pick('近7日关联动态：','Related developments in the last 7 days: ')}{related.map((n,i)=><span key={n.id}>{i>0?' · ':''}<Link to={contentPath(n.id)}>{n.title}</Link></span>)}</p>;
}
