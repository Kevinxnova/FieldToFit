import { Link } from 'react-router-dom';
import { contentPath } from '../../search';
import { useWorkspace } from './UI';
import { SourcePostCard } from './SourcePostCard';
import { overview } from './codexData';
import type { CodexRoundup as Roundup } from './codexData';
import type { NewsItem } from './NewsReading';

export function CodexRoundup({roundup,byId}:{roundup:Roundup;byId:Map<string,NewsItem>}){
 const {pick,zh}=useWorkspace();
 return <section className="codex-roundup" aria-label={pick(`官方 Day ${roundup.official_day} 小结`,`Official Day ${roundup.official_day} roundup`)}>
  <SourcePostCard post={roundup.source_post} label={pick('官方小结','Official roundup')}>
   <h5>{pick('官方','Official')} Day {roundup.official_day} · {pick('今日小结','Roundup')}</h5>
   <p className="codex-roundup-note">{pick('按原帖顺序整理，点击查看已审日志；小结不重复计数。','In the original post’s order. Open a reviewed log for details; the roundup adds no extra events.')}{roundup.steps.length<roundup.total_steps&&pick(` 当前范围展示 ${roundup.steps.length}/${roundup.total_steps} 项。`,` Showing ${roundup.steps.length}/${roundup.total_steps} items in this scope.`)}</p>
   <ol className="codex-roundup-steps">{roundup.steps.map(step=>{
    const item=byId.get(step.news_id);if(!item?.codex_28_days)return null;const event=item.codex_28_days;
    return <li key={step.number}><span className="codex-step-number">{roundup.official_day}.{step.number}</span><div><Link to={contentPath(item.id)}>{overview(item,zh)}</Link><small><span className={event.group==='other_openai'?'codex-group-other':''}>{event.group==='codex'?'Codex / Work':pick('其他 OpenAI','Other OpenAI')}</span> · {event.date_precision==='source_date'?pick('来源日期 ','Source date '):''}{event.date}{event.date!==roundup.date&&pick(' 已发布',' · previously announced')} · {item.id}</small></div></li>;
   })}</ol>
  </SourcePostCard>
 </section>;
}
