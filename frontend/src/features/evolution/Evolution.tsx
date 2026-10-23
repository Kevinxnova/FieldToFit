import {useEffect,useState} from 'react';
import {Link,useLocation,useParams,useSearchParams} from '@fieldtofit/locale/router';
import {useWorkspace} from '../../components/workspace/UI';
import {PageMetadata} from '../../search';
import {catalog,ROOT,QUESTIONS,questionById,kvMiB,type Copy,type Question} from './data';
import {chooseQuestion,statusFor,type ReadStatus} from './progress';
import {markRead,useProgress} from './useProgress';
import './evolution.css';
import {AtlasMap} from './AtlasMap';
import {HomeAtlas} from './HomeAtlas';
function useCopy(){const {zh,pick}=useWorkspace();return {t:(c:Copy)=>c[zh?0:1],pick,zh};}
const statusCopy:Record<ReadStatus,Copy>={unread:['未读','Unread'],read:['已读','Read'],updated:['有更新','Updated']};
function Sources({ids}:{ids:string[]}){
  const {pick}=useCopy();return <ul className="evo-sources">{[...new Set(ids)].map(id=>{const s=catalog.sources[id];return <li key={id}><a href={s.url} target="_blank" rel="noreferrer">{s.title} ↗</a><small>{s.date||pick('来源未标日期','Source date not stated')} · {pick('核对','Checked')} {s.checked_at}</small></li>;})}</ul>;
}
function ProgressNotice(){const {warning}=useProgress();const {pick}=useCopy();return <p className={warning?'evo-warning':'evo-note'} role={warning?'status':undefined}>{warning?pick('浏览器存储不可用或记录损坏；当前操作会尽量保存，请勿依赖跨刷新恢复。','Browser storage is unavailable or damaged. Changes are kept where possible; refresh recovery is not guaranteed.'):pick('手动勾选，保存在当前浏览器；不跨设备同步。修订后保留已读记录并提示有更新。','Mark manually; saved in this browser without cross-device sync. Revised articles retain your record and show an update.')}</p>;}
function ReadButton({question}:{question:Question}){
  const {records}=useProgress(),{pick,t}=useCopy();const status=statusFor(records,question.id,question.revision);
  return <div className="evo-read-action"><label><input type="checkbox" checked={status!=='unread'} onChange={e=>markRead(question.id,question.revision,e.target.checked)}/>{pick('已读','Read')} · {question.id}</label>{status==='updated'&&<button onClick={()=>markRead(question.id,question.revision,true)}>{pick('已读新版','Mark new version read')}</button>}<span className={'evo-status '+status}>{t(statusCopy[status])}</span></div>;
}
export function Figure({question}:{question:Question}){
  const {t,pick}=useCopy();return <figure className={'evo-figure '+question.figure.kind}><div className="evo-figure-nodes">{question.figure.labels.map((label,i)=><div key={i}><small>{String(i+1).padStart(2,'0')}</small><strong>{t(label)}</strong></div>)}</div><figcaption>{pick('本站重绘 · ','FieldToFit redraw · ')}{t(question.figure.caption)}</figcaption></figure>;
}
function KVMeter(){
  const {pick}=useCopy();const [values,setValues]=useState(['1','32','4096','8','128','2']);
  const labels=[pick('请求数 B','Requests B'),pick('层数 L','Layers L'),pick('每请求 token T','Tokens/request T'),pick('KV 头 H','KV heads H'),pick('头维度 d','Head dimension d'),pick('字节／元素 s','Bytes/element s')];
  const valid=values.every((v,i)=>Number(v)>0&&Number.isFinite(Number(v))&&(i===5||Number.isInteger(Number(v))));
  const result=valid?kvMiB(...values.map(Number) as [number,number,number,number,number,number]):null;
  return <section className="evo-calculator"><h3>{pick('算一算理想 KV 载荷','Calculate ideal KV payload')}</h3><div>{values.map((value,i)=><label key={i}>{labels[i]}<input type="number" min={i===5?0.125:1} step={i===5?0.125:1} value={value} onChange={e=>setValues(v=>v.map((old,j)=>j===i?e.target.value:old))}/></label>)}</div><output aria-live="polite">{result===null?pick('请输入有效正数；维度必须为整数。','Enter positive values; dimensions must be integers.'):`${result.toLocaleString(undefined,{maximumFractionDigits:2})} MiB`}</output><p>{pick('等长请求，标准 MHA／GQA／MQA。排除权重、工作区、分配浪费、量化元数据和副本；不直接适用于 MLA。','Equal-length requests, standard MHA/GQA/MQA. Excludes weights, workspace, allocation waste, quantization metadata and replicas; not a direct MLA estimate.')}</p></section>;
}
function TopicNav(){const {pick}=useCopy();return <nav className="evo-nav" aria-label={pick('专题导航','Topic navigation')}><Link to="/for-you#llm-evolution">← For you</Link><Link to={ROOT}>{pick('演进图','Evolution maps')}</Link><Link to={QUESTIONS}>{pick('重要问题目录','Question directory')}</Link></nav>;}
function QuestionIllustration({question}:{question:Question}){
  const {pick}=useCopy();
  if(question.id!=='S03')return <Figure question={question}/>;
  return <figure className="evolution-home-io"><figcaption>{pick('同样的注意力计算，更少的显存往返','The same attention computation, fewer memory transfers')}</figcaption><div><span>{pick('HBM · 高带宽显存','HBM · high-bandwidth memory')}</span><span>Q / K / V</span></div><p>{pick('↓ 分块载入　↑ 写回结果','↓ Load tiles　↑ Write results')}</p><div><span>{pick('SRAM · 片上存储','SRAM · on-chip memory')}<small>{pick('分块计算 · 算子融合','Tiled computation · fused operations')}</small></span><span className="evolution-home-tiles" aria-hidden="true">{Array.from({length:12},(_,i)=><i key={i}/>)}</span></div><small>{pick('本站机制重绘：省去完整注意力中间矩阵的显存读写，非容量或性能实测。','Mechanism redraw: avoid HBM reads/writes of the full intermediate attention matrix; not measured capacity or performance.')}</small></figure>;
}
export function QuestionPreview({home=false}:{home?:boolean}){
  const {records}=useProgress(),{t,pick}=useCopy();
  const [directory,setDirectory]=useState(false);
  const [id,setId]=useState(()=>{try{const stored=sessionStorage.getItem('fieldtofit:evolution:current');if(stored&&questionById[stored])return stored;}catch{}return chooseQuestion(catalog.questions,records)?.id||'T01';});
  const q=questionById[id];const read=catalog.questions.filter(q=>statusFor(records,q.id,q.revision)==='read').length;
  const returnTo=home?'/for-you#llm-evolution':ROOT;
  useEffect(()=>{try{sessionStorage.setItem('fieldtofit:evolution:current',id);}catch{}},[id]);
  return <section className="evo-question-preview evolution-question-card" aria-labelledby="evo-question-title">
    <header><div><h2 id="evo-question-title">{pick('重要问题 · 图文解析','Important questions · explained')}</h2><div className="evolution-question-progress"><span aria-live="polite">{read} / {catalog.questions.length} {pick('篇已读当前版','current versions read')}</span><progress max={catalog.questions.length} value={read} aria-label={pick('当前版阅读进度','Current-version reading progress')}/></div></div><button aria-expanded={directory} aria-controls="evolution-home-directory" onClick={()=>setDirectory(v=>!v)}>{directory?pick('收起目录','Hide directory'):pick('全部18题','All 18 questions')} {directory?'↑':'→'}</button></header>
    <div className="evo-featured-question"><div className="evolution-question-copy"><span className="evo-question-number">{q.id} · {t(catalog.tracks.find(v=>v.id===q.track)!.label)} · {t(statusCopy[statusFor(records,q.id,q.revision)])}</span><h3><Link to={QUESTIONS+'/'+q.id} state={{evolutionReturn:returnTo}}>{t(q.title)}</Link></h3><p>{t(q.goal)}</p><div className="evo-actions"><Link className="button primary" to={QUESTIONS+'/'+q.id} state={{evolutionReturn:returnTo}}>{pick('阅读解析','Read explanation')} →</Link><button onClick={()=>setId(chooseQuestion(catalog.questions,records,id)!.id)}>{pick('换一题','Another question')} ↻</button></div></div><div className="evolution-question-art"><QuestionIllustration question={q}/></div><footer><ReadButton question={q}/><span>{pick('手动记录 · 优先未读／有更新','Mark manually · prioritize unread / updated')}</span></footer></div>
    {directory&&<div id="evolution-home-directory" className="evolution-inline-directory"><div><p>{pick('任选一题开始，也可进入完整目录筛选。','Start with any question, or filter in the full directory.')}</p><Link to={QUESTIONS}>{pick('打开完整目录','Open full directory')} →</Link></div>{catalog.tracks.map(track=><section key={track.id}><h3>{t(track.label)} <small>{track.id==='systems'?'Systems':track.name}</small></h3>{catalog.questions.filter(item=>item.track===track.id).map(item=><article key={item.id}><Link to={QUESTIONS+'/'+item.id} state={{evolutionReturn:returnTo}}>{item.id} · {t(item.title)}</Link><ReadButton question={item}/></article>)}</section>)}</div>}
    <ProgressNotice/>
  </section>;
}

export function EvolutionHome(){
  return <section className="home-section evo-home" aria-labelledby="llm-evolution"><HomeAtlas/><QuestionPreview home/></section>;
}

function Directory(){
  const {t,pick}=useCopy(),{records}=useProgress(),[params,setParams]=useSearchParams(),location=useLocation();
  const query=params.get('q')||'',track=params.get('track')||'',read=params.get('read')||'';
  const update=(key:string,value:string)=>setParams(old=>{const next=new URLSearchParams(old);value?next.set(key,value):next.delete(key);return next;},{replace:true});
  const found=catalog.questions.filter(q=>(!track||q.track===track)&&(!read||statusFor(records,q.id,q.revision)===read)&&`${q.id} ${q.title.join(' ')} ${q.goal.join(' ')}`.toLowerCase().includes(query.toLowerCase().trim()));
  return <div className="evo-page"><PageMetadata title={pick('重要问题目录 · FieldToFit','Question directory · FieldToFit')} path={QUESTIONS}/><TopicNav/><header className="evo-hero"><p className="evo-eyebrow">A READING PATH · 18 QUESTIONS</p><h1>{pick('把关键问题，一个个读懂','Understand the questions that matter')}</h1><p>{pick('训练、推理、系统各六题。从基础机制走向工程取舍；无需按顺序读，完成一题后手动勾选。','Six questions each on training, inference and systems. Move from mechanisms to engineering tradeoffs, or read in any order and mark completion manually.')}</p><progress max={catalog.questions.length} value={catalog.questions.filter(q=>statusFor(records,q.id,q.revision)==='read').length} aria-label={pick('当前版阅读进度','Current-version reading progress')}/><span> {catalog.questions.filter(q=>statusFor(records,q.id,q.revision)==='read').length} / 18</span></header>
    <div className="evo-toolbar"><label>{pick('关键词','Keyword')}<input type="search" value={query} placeholder={pick('标题、编号或机制','Title, ID or mechanism')} onChange={e=>update('q',e.target.value)}/></label><label>{pick('分类','Category')}<select value={track} onChange={e=>update('track',e.target.value)}><option value="">{pick('全部','All')}</option>{catalog.tracks.map(v=><option key={v.id} value={v.id}>{v.name}</option>)}</select></label><label>{pick('阅读状态','Reading status')}<select value={read} onChange={e=>update('read',e.target.value)}><option value="">{pick('全部','All')}</option>{Object.entries(statusCopy).map(([id,label])=><option key={id} value={id}>{t(label)}</option>)}</select></label><button onClick={()=>setParams({},{replace:true})}>{pick('清除筛选','Clear filters')}</button></div><ProgressNotice/><p role="status">{found.length} {pick('题匹配','matching questions')}</p>
    {catalog.tracks.map(v=>{const items=found.filter(q=>q.track===v.id);return items.length?<section className="evo-directory-group" key={v.id}><h2>{v.name} <small>{t(v.label)}</small></h2><div>{items.map(q=><article key={q.id}><div><span>{q.id}</span><h3><Link to={QUESTIONS+'/'+q.id} state={{evolutionReturn:QUESTIONS+location.search}}>{t(q.title)}</Link></h3><p>{t(q.goal)}</p></div><ReadButton question={q}/></article>)}</div></section>:null;})}{!found.length&&<p>{pick('没有匹配题目，可清除筛选查看全部目录。','No questions match. Clear filters to see the full directory.')}</p>}
  </div>;
}
function QuestionPage(){
  const {id}=useParams(),location=useLocation(),{t,pick}=useCopy();const q=questionById[id||''];
  useEffect(()=>{if(q)try{sessionStorage.setItem('fieldtofit:evolution:current',q.id);}catch{/* Reading remains available without storage. */}},[q?.id]);
  const requestedBack=location.state?.evolutionReturn;
  const back=typeof requestedBack==='string'&&(requestedBack===ROOT||requestedBack==='/for-you#llm-evolution'||requestedBack===QUESTIONS||requestedBack.startsWith(QUESTIONS+'?'))?requestedBack:QUESTIONS;
  const backLabel=back==='/for-you#llm-evolution'?pick('返回首页预览','Back to homepage preview'):back===ROOT?pick('返回完整图谱','Back to full maps'):pick('返回问题目录','Back to questions');
  if(!q)return <div className="evo-page"><PageMetadata title={pick('题目未找到','Question not found')} path={location.pathname} index={false}/><h1>{pick('题目未找到','Question not found')}</h1><Link to={QUESTIONS}>{pick('返回目录','Return to directory')}</Link></div>;
  const sections:[[string,string],Copy][]=[[['问题从哪里来','The bottleneck'],q.problem],[['关键机制','The mechanism'],q.mechanism],[['算例与证据','Examples and evidence'],q.example],[['收益之外的新约束','The new constraints'],q.limit]];
  return <article className="evo-page evo-article"><PageMetadata title={t(q.title)+' · FieldToFit'} description={t(q.goal)} path={QUESTIONS+'/'+q.id}/><TopicNav/><Link to={back}>← {backLabel}</Link><header className="evo-hero"><p className="evo-eyebrow">{q.id} · {catalog.tracks.find(v=>v.id===q.track)!.name.toUpperCase()}</p><h1>{t(q.title)}</h1><p>{t(q.goal)}</p><small>{pick('修订','Revision')} {q.revision} · {q.updated_at} · {t(q.change_reason)}</small></header><Figure question={q}/>
    {sections.map(([heading,copy],i)=><section className="evo-prose" key={i}><h2><span>0{i+1}</span>{t(heading)}</h2><p>{t(copy)}</p>{i===1&&<pre className="evo-formula"><code>{q.formula}</code></pre>}{i===2&&q.id==='I01'&&<KVMeter/>}</section>)}
    <section className="evo-prose"><h2>{pick('原始来源','Primary sources')}</h2><Sources ids={q.sources}/></section><aside className="evo-reading-end"><ReadButton question={q}/><ProgressNotice/><Link to={ROOT+'?view=all&track='+q.track+'&node='+catalog.routes.find(r=>r.id===q.route)!.nodes.find(n=>n.question===q.id)!.id}>{pick('回到相关技术节点','View the related milestone')} →</Link><h3>{pick('继续追问','Keep exploring')}</h3>{q.related.map(id=><Link key={id} to={QUESTIONS+'/'+id} state={{evolutionReturn:back}}>{id} · {t(questionById[id].title)} →</Link>)}<Link to={back}>← {backLabel}</Link></aside>
  </article>;
}
export default function Evolution(){const location=useLocation();useEffect(()=>{window.dispatchEvent(new Event('fieldtofit:reading-ready'));},[location.pathname]);return location.pathname===QUESTIONS?<Directory/>:location.pathname===ROOT?<AtlasMap navigation={<TopicNav/>} footer={<QuestionPreview/>}/>:<QuestionPage key={location.pathname}/>;}
