import {useEffect,useRef,useState,type ReactNode} from 'react';
import {Link,useLocation,useSearchParams} from '@fieldtofit/locale/router';
import {useWorkspace} from '../../components/workspace/UI';
import {PageMetadata} from '../../search';
import {catalog,QUESTIONS,nodeById,nodeDestination,nodeCases,visibleNodes,timeBand,relationCopy,nodeKindCopy,questionById,type Copy,type EvolutionRoute,type Milestone,type Period,type Track} from './data';

function useCopy(){const {zh,pick}=useWorkspace();return {t:(copy:Copy)=>copy[zh?0:1],pick};}
const sourceKinds:Record<string,Copy>={paper:['论文','Paper'],'technical-report':['技术报告','Technical report'],'official-note':['官方说明','Official note'],'model-card':['型号资料','Model card'],engineering:['工程文档','Engineering docs']};
function Evidence({node}:{node:Milestone}) {
  const {t,pick}=useCopy();
  return <ul className="evo-sources">{node.references.map(ref=>{const source=catalog.sources[ref.source];return <li key={ref.source}>
    <a href={source.url} target="_blank" rel="noreferrer">{source.title} ↗</a>
    <small>{t(sourceKinds[source.kind]||sourceKinds['official-note'])} · {source.date||pick('未标发布日期','Publication date not stated')}{source.revised_at&&<> · {pick('修订','Revised')} {source.revised_at}</>}</small>
    <p>{t(ref.section)}</p><small>{pick('核对','Checked')} {source.checked_at}</small>
  </li>;})}</ul>;
}
function MilestoneCard({route,node,expanded,toggle,company,selected,relationKind}:{route:EvolutionRoute;node:Milestone;expanded:boolean;toggle:()=>void;company:string;selected:boolean;relationKind:string}) {
  const {t,pick}=useCopy(),cases=nodeCases(route,node.id);
  const relations=catalog.relations.filter(edge=>(edge.from_node===node.id||edge.to_node===node.id)&&(!relationKind||edge.kind===relationKind));
  return <article id={'node-'+node.id} tabIndex={-1} className={'evo-node atlas-node '+(company&&cases.some(c=>c.company===company)?'matched ':'')+(selected?'selected':'')}>
    <button className="evo-node-toggle" aria-expanded={expanded} aria-controls={'body-'+node.id} onClick={toggle}>
      <span className="atlas-node-meta"><time>{node.date}</time><span>{t(nodeKindCopy[node.kind])}</span></span>
      <strong>{node.title}</strong><span className="atlas-summary">{t(node.mechanism)}</span>
      <small>{expanded?pick('收起详情 −','Collapse details −'):pick('机制、证据与关系 ＋','Mechanism, evidence & relations ＋')}</small>
    </button>
    {cases.length>0&&<div className="atlas-company-tags">{[...new Set(cases.map(c=>c.company))].map(id=><span key={id}>{catalog.companies[id]}</span>)}</div>}
    {expanded&&<div id={'body-'+node.id} className="evo-node-body">
      <p className="atlas-date-note">{node.date_kind==='model-adoption'?pick('日期为型号采用；方法首发见相关节点。','Date records model adoption; see related nodes for method origins.'):node.date_kind==='engineering-release'?pick('日期为工程公开年份，未推断具体日。','Date is the engineering release year; no exact day is inferred.'):pick('日期为这份原始资料首次公开；报告修订另列。','Date records this source’s initial publication; revisions are listed separately.')}</p>
      {([[pick('当时的瓶颈','Bottleneck'),node.problem],[pick('关键机制','Mechanism'),node.mechanism],[pick('证据与条件','Evidence & conditions'),node.evidence],[pick('新约束','New constraints'),node.limit]] as [string,Copy][]).map(([heading,copy])=><section key={heading}><h4>{heading}</h4><p>{t(copy)}</p></section>)}
      {node.formula&&<pre className="evo-formula"><code>{node.formula}</code></pre>}
      {cases.map(c=><section key={c.id}><h4>{catalog.companies[c.company]} · {c.model}</h4><p>{t(c.evidence)}</p><a href={catalog.sources[c.source].url} target="_blank" rel="noreferrer">{pick('采用依据','Adoption evidence')} ↗</a></section>)}
      <h4>{pick('关系','Relations')} · {relations.length}</h4>
      {relations.length? <ul className="atlas-relations">{relations.map(edge=>{const outgoing=edge.from_node===node.id,target=nodeById[outgoing?edge.to_node:edge.from_node];return <li key={edge.id}>
        <span className={'atlas-relation-type '+edge.kind}>{t(relationCopy[edge.kind])}</span>
        <Link to={nodeDestination(target.node.id)}>{outgoing?'→':'←'} {target.node.title} <small>{catalog.tracks.find(track=>track.id===target.route.track)!.name} · {target.node.date}</small></Link>
        <p>{t(edge.reason)}</p><span className="atlas-edge-sources">{edge.sources.map(id=><a key={id} href={catalog.sources[id].url} target="_blank" rel="noreferrer">{catalog.sources[id].title} ↗</a>)}</span>
      </li>;})}</ul>:<p>{relationKind?pick('此类关系暂无收录；切换“全部关系”查看其他关系。','No relation of this type is recorded; select all relations for other types.'):pick('暂无独立关系条目；同路线相邻节点只表示时间顺序。','No separate relation is recorded; adjacent nodes indicate chronology only.')}</p>}
      <h4>{pick('原始资料与对应内容','Primary sources & supported content')}</h4><Evidence node={node}/>
      <Link to={QUESTIONS+'/'+node.question}>{pick('相关基础问题','Related foundation')} · {node.question} · {t(questionById[node.question].title)} →</Link>
    </div>}
  </article>;
}
const bands=['2017–2019','2020–2022','2023–2024','2025 H1','2025 H2','2026 H1','2026 H2'];
function Chart({track,all,period,company,expanded,setExpanded,collapsed,onCollapse,selected,relationKind}:{track:Track;all:boolean;period:Period;company:string;expanded:string[];setExpanded:(ids:string[])=>void;collapsed:boolean;onCollapse:()=>void;selected:string;relationKind:string}) {
  const {t,pick}=useCopy(),info=catalog.tracks.find(v=>v.id===track)!;
  const routes=catalog.routes.filter(route=>route.track===track&&visibleNodes(route,all,period).length);
  const shownBands=bands.filter(band=>period==='all'||band.startsWith('2025')||band.startsWith('2026'));
  for(const year of ['2025','2026'])if(routes.some(r=>visibleNodes(r,all,period).some(n=>n.date===year)))shownBands.splice(shownBands.indexOf(year+' H1'),0,year);
  const groups=[...new Set(routes.map(route=>route.group))];
  return <section className={'evo-chart atlas-chart evo-'+track} aria-labelledby={'track-'+track}>
    <header><div><p>{info.name.toUpperCase()} · {routes.reduce((sum,r)=>sum+visibleNodes(r,all,period).length,0)} {pick('个可见节点','visible milestones')}</p><h2 id={'track-'+track}>{t(info.label)}</h2><span>{t(info.description)}</span></div><button aria-expanded={!collapsed} aria-controls={'chart-'+track} onClick={onCollapse}>{collapsed?pick('展开主线 ＋','Expand track ＋'):pick('收起主线 −','Collapse track −')}</button></header>
    {!collapsed&&<div id={'chart-'+track} className="atlas-chart-body">
      <p className="atlas-pan-hint">{pick('横向滑动查看时间 → 同期节点纵向排列；每个时间段等宽，不表示经过时长。','Scroll horizontally through time → Contemporary nodes stack vertically; equal-width bands do not represent elapsed duration.')}</p>
      {groups.map(group=><section className="atlas-group" key={group}><h3>{t(catalog.groups[group])}<small>{pick('分支可并存','Branches can coexist')}</small></h3><div className="atlas-branches">{routes.filter(route=>route.group===group).map(route=>{
        const nodes=visibleNodes(route,all,period),unbound=route.cases.filter(c=>!c.nodes.length);
        return <section className="atlas-branch" key={route.id}>
          <header className="atlas-route-label"><strong>{t(route.title)}</strong><span>{t(route.method)}</span><small>{nodes.length} {pick('个节点','milestones')}</small></header>
          <div className="atlas-lane" tabIndex={0} role="region" aria-label={t(route.title)+pick(' 横向时间图',' horizontal timeline')}>
            <div className="atlas-time-grid" style={{gridTemplateColumns:`repeat(${shownBands.length}, minmax(270px, 1fr))`}}>{shownBands.map(band=>{
              const items=nodes.filter(n=>timeBand(n.date)===band);
              return <div className="atlas-band" key={band}><div className="atlas-band-label">{band.replace('H1',pick('上半年','H1')).replace('H2',pick('下半年','H2'))}{band.length===4&&pick(' · 仅确认年份',' · year only')}</div><div className="atlas-band-nodes">{items.length?items.map(node=><MilestoneCard key={node.id} node={node} route={route} expanded={expanded.includes(node.id)} toggle={()=>setExpanded(expanded.includes(node.id)?expanded.filter(id=>id!==node.id):[...expanded,node.id])} company={company} selected={selected===node.id} relationKind={relationKind}/>):<span className="atlas-gap" aria-label={pick('此时间段未收录节点','No milestone recorded in this band')}>·</span>}</div></div>;
            })}</div>
          </div>
          {unbound.length>0&&<details className="atlas-route-evidence"><summary>{pick('路线层面的型号证据','Route-level model evidence')} · {unbound.length}</summary><p>{pick('这些资料支持路线采用，未据此高亮每个研究节点。','These sources support route adoption; they do not mark every research node as adopted.')}</p>{unbound.map(c=><p key={c.id}><strong>{catalog.companies[c.company]||pick('研究项目','Research')} · {c.model} · {c.year}</strong> — {t(c.evidence)} <a href={catalog.sources[c.source].url} target="_blank" rel="noreferrer">{pick('来源','Source')} ↗</a></p>)}</details>}
        </section>;
      })}</div></section>)}
      {!routes.length&&<p className="evo-note">{pick('当前时间和重点筛选没有节点。可切换全部节点或完整历史。','No milestones match this period and highlight filter. Try all milestones or full history.')}</p>}
    </div>}
  </section>;
}
const VIEW_KEY='fieldtofit:evolution:map-view:v1';
function readView():{expanded:string[];collapsed:string[]}{try{const v=JSON.parse(sessionStorage.getItem(VIEW_KEY)||'{}');return {expanded:Array.isArray(v.expanded)?v.expanded.filter((x:unknown)=>typeof x==='string'&&!!nodeById[x]):[],collapsed:Array.isArray(v.collapsed)?v.collapsed.filter((x:unknown)=>typeof x==='string'):[]};}catch{return {expanded:[],collapsed:[]};}}
export function AtlasMap({navigation,footer}:{navigation:ReactNode;footer:ReactNode}) {
  const {t,pick}=useCopy(),[params,setParams]=useSearchParams(),location=useLocation();
  const [view,setView]=useState(readView),[large,setLarge]=useState(false),dialog=useRef<HTMLDialogElement>(null),largeButton=useRef<HTMLButtonElement>(null);
  const all=params.get('view')==='all',period:Period=params.get('period')==='all'?'all':'recent',company=params.get('company')||'',track=params.get('track')||'',selected=params.get('node')||'',relationKind=params.get('relation')||'';
  const expanded=view.expanded,setExpanded=(ids:string[])=>setView(v=>({...v,expanded:ids}));
  const tracks=catalog.tracks.filter(v=>!catalog.tracks.some(t=>t.id===track)||v.id===track);
  const visible=catalog.routes.filter(r=>tracks.some(t=>t.id===r.track)&&!view.collapsed.includes(r.track)).flatMap(r=>visibleNodes(r,all,period).map(n=>n.id));
  const update=(key:string,value:string)=>setParams(old=>{const next=new URLSearchParams(old);value?next.set(key,value):next.delete(key);next.delete('node');return next;},{replace:true});
  useEffect(()=>{try{sessionStorage.setItem(VIEW_KEY,JSON.stringify(view));}catch{/* Viewing remains usable without storage. */}},[view]);
  // The locale router creates a new setter each render; depend on URL values, not its identity.
  // A legacy direct link must reveal its target, even with contradictory saved filters.
  useEffect(()=>{
    const target=nodeById[selected];if(!target)return;
    if(!all||track!==target.route.track||(period==='recent'&&target.node.date<'2025')){
      setParams(old=>{const next=new URLSearchParams(old);next.set('view','all');next.set('track',target.route.track);if(target.node.date<'2025')next.set('period','all');return next;},{replace:true});return;
    }
    setView(v=>v.expanded.includes(selected)&&!v.collapsed.includes(target.route.track)?v:{expanded:[...new Set([...v.expanded,selected])],collapsed:v.collapsed.filter(t=>t!==target.route.track)});
    const timer=setTimeout(()=>{const element=document.getElementById('node-'+selected);element?.scrollIntoView({block:'start',inline:'center',behavior:'instant'});element?.focus({preventScroll:true});},100);
    return()=>clearTimeout(timer);
  },[selected,all,period,track]);
  useEffect(()=>{if(large){dialog.current?.showModal();const previous=document.body.style.overflow;document.body.style.overflow='hidden';return()=>{document.body.style.overflow=previous;};}dialog.current?.close();},[large]);
  const controls=<div className="evo-toolbar atlas-toolbar">
    <label>{pick('时间范围','Time range')}<select value={period} onChange={e=>update('period',e.target.value)}><option value="all">2017—2026 · {pick('完整历史','Full history')}</option><option value="recent">2025—2026 · {pick('近期放大','Recent focus')}</option></select></label>
    <label>{pick('展示','Show')}<select value={all?'all':'key'} onChange={e=>update('view',e.target.value)}><option value="key">{pick('重点节点','Highlights')}</option><option value="all">{pick('全部节点','All milestones')}</option></select></label>
    <label>{pick('主线','Track')}<select value={tracks.length===1?track:''} onChange={e=>update('track',e.target.value)}><option value="">{pick('全部三条','All three')}</option>{catalog.tracks.map(v=><option key={v.id} value={v.id}>{v.name}</option>)}</select></label>
    <label>{pick('公司高亮','Highlight company')}<select value={catalog.companies[company]?company:''} onChange={e=>update('company',e.target.value)}><option value="">{pick('全部公司','All companies')}</option>{Object.entries(catalog.companies).map(([id,name])=><option key={id} value={id}>{name}</option>)}</select></label>
    <label>{pick('详情中的关系','Relations in details')}<select value={relationKind in relationCopy?relationKind:''} onChange={e=>update('relation',e.target.value)}><option value="">{pick('全部关系','All relations')}</option>{Object.entries(relationCopy).map(([kind,label])=><option key={kind} value={kind}>{t(label)}</option>)}</select></label>
    <div className="atlas-expand-actions"><button onClick={()=>setExpanded([...new Set([...expanded,...visible])])}>{pick('展开可见详情','Expand visible details')} ({visible.length})</button><button onClick={()=>setExpanded([])}>{pick('收起全部详情','Collapse all details')}</button></div>
  </div>;
  const charts=<>{controls}<div className="atlas-legend"><span>{pick('时间横排 · 分支并存','Chronology · coexisting branches')}</span>{Object.entries(relationCopy).map(([kind,label])=><span key={kind} className={'atlas-relation-type '+kind}>{t(label)}</span>)}</div><p className="evo-note">{pick('时间线只表示先后。展开节点查看有依据的关系与报告章节；跨主线支撑是机制对照，不代表某家公司采用了对应系统。只标具体型号，未标注不等于未采用。','The timeline shows chronology only. Expand a node for evidenced relations and report sections. Cross-track support compares mechanisms, not undisclosed company deployment. Labels apply to specific models; absence is not non-use.')}</p>{company&&<p className="evo-filter-hint">{pick('仅高亮已绑定节点的型号证据；切换全部节点可查看更多实践。','Only node-linked model evidence is highlighted; all milestones reveal more practices.')}</p>}{tracks.map(v=><Chart key={v.id} track={v.id} all={all} period={period} company={company} expanded={expanded} setExpanded={setExpanded} collapsed={view.collapsed.includes(v.id)} onCollapse={()=>setView(old=>({...old,collapsed:old.collapsed.includes(v.id)?old.collapsed.filter(id=>id!==v.id):[...old.collapsed,v.id]}))} selected={selected} relationKind={relationKind in relationCopy?relationKind:''}/>)}</>;
  return <div className="evo-page"><PageMetadata title={pick('大模型技术演进 · FieldToFit','LLM technical evolution · FieldToFit')} description={pick('2017—2026训练、推理、系统三图：原始资料、技术分支、型号实践与18题解析。','2017–2026 training, inference and systems: primary sources, technical branches, model practice and 18 explanations.')} path={location.pathname}/>{navigation}
    <header className="evo-hero atlas-hero"><p className="evo-eyebrow">2017—2026 · LIVING ATLAS</p><h1>{pick('大模型技术演进','How large models evolved')}</h1><p>{pick('沿着瓶颈，理解创新如何改变计算、学习与服务。方法首次提出、型号采用和工程实现分别记录，每一次突破也带来新的约束。','Follow how bottlenecks reshape computation, learning and serving. Method origins, model adoption and engineering practice are distinct; each breakthrough brings new constraints.')}</p><div className="evo-hero-meta"><span>{catalog.routes.length} {pick('条路线','routes')} · {Object.keys(nodeById).length} {pick('个节点','milestones')} · {catalog.relations.length} {pick('条关系','relations')}</span><span>{pick('修订','Revision')} {catalog.revision} · {catalog.updated_at}</span><button ref={largeButton} onClick={()=>setLarge(true)}>{pick('全屏阅读大图 ↗','Open full-screen map ↗')}</button></div><button className="atlas-focus-link" onClick={()=>{setParams({period:'recent',view:'key'});}}>{pick('聚焦2025—2026：推理训练、混合架构与系统协同','Focus on 2025–2026: reasoning training, hybrid architectures and systems')} →</button></header>
    {!large&&charts}<dialog className="evo-fullscreen" ref={dialog} aria-label={pick('全屏技术路线图','Full-screen technical maps')} onCancel={()=>setLarge(false)} onClose={()=>{setLarge(false);largeButton.current?.focus();}}>{large&&<><header className="evo-fullscreen-heading"><strong>{pick('大模型技术演进 · 全屏图','LLM evolution · Full-screen maps')}</strong><button onClick={()=>setLarge(false)}>{pick('退出全屏 · Esc','Exit full screen · Esc')}</button></header>{charts}</>}</dialog>{footer}
  </div>;
}
