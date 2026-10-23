import {useEffect,useLayoutEffect,useRef,useState,type CSSProperties} from 'react';
import {Link} from '@fieldtofit/locale/router';
import {useWorkspace} from '../../components/workspace/UI';
import {catalog,ROOT,nodeById,nodeDestination,relationCopy,type Copy} from './data';
import {NodeDetail} from './AtlasMap';
import {homeLayout,homeDefinitions} from './homeLayout';
import './home.css';

export function HomeAtlas(){
  const {zh,pick}=useWorkspace(),t=(c:Copy)=>c[zh?0:1];
  const [selected,setSelected]=useState('');
  const [boardWidth,setBoardWidth]=useState(840);
  const scroll=useRef<HTMLDivElement>(null);
  const dialog=useRef<HTMLDialogElement>(null),trigger=useRef<HTMLButtonElement|null>(null);
  const target=nodeById[selected];
  useEffect(()=>{
    const element=scroll.current;if(!element)return;
    const update=()=>setBoardWidth(window.innerWidth>=900?Math.max(600,Math.min(840,element.clientWidth-132)):840);
    const observer=new ResizeObserver(update);observer.observe(element);update();
    return()=>observer.disconnect();
  },[]);
  useLayoutEffect(()=>{
    if(!target)return;
    const element=dialog.current,previous=document.body.style.overflow;
    element?.showModal();document.body.style.overflow='hidden';
    return()=>{element?.close();document.body.style.overflow=previous;if(trigger.current?.isConnected)trigger.current.focus({preventScroll:true});};
  },[selected]);
  useEffect(()=>()=>{trigger.current=null;},[]);
  return <>
    <header className="platform-section-heading evolution-home-heading"><div><p className="evolution-home-eyebrow">2017—2026</p><h2 id="llm-evolution" tabIndex={-1}>{pick('大模型技术演进','LLM technical evolution')}</h2></div><Link to={ROOT}>{pick('探索完整图谱','Explore full maps')} ↗</Link></header>
    <p className="evolution-home-intro">{pick('能力如何形成、如何使用，又如何高效运行。','How capabilities are learned, used and run efficiently.')}</p>
    <div className="evolution-home-meta"><span>{pick('三张总图','Three complete maps')} · {Object.keys(nodeById).length} {pick('个节点','milestones')}</span><span>{pick('论文 / 技术报告 / 官方资料','Papers / technical reports / official sources')}</span><span>{pick('专题更新','Catalog updated')} <time>{catalog.updated_at}</time></span></div>
    <p className="evolution-home-pan">{pick('左右滑动查看时间演进 · 三图同步浏览','Scroll horizontally through time · all three maps move together')}</p>
    <div ref={scroll} className="evolution-home-scroll" role="region" aria-label={pick('三张横向技术演进预览图','Three horizontal evolution previews')} tabIndex={0} style={{'--home-board':boardWidth+'px','--home-column':boardWidth/6+'px'} as CSSProperties}>
      <div className="evolution-home-grid">
        <div className="evolution-home-axis"><span>{pick('关键节点预览','Selected milestones')}</span><div><span>2017—2021</span><span>2022—2023</span><span>2024</span><span>2025 · {pick('路线扩展','Expanding approaches')}</span><span>2026</span></div></div>
        {catalog.tracks.map(track=>{const layout=homeLayout(track.id,zh,boardWidth);return <section key={track.id} className={'evolution-home-track evo-'+track.id} aria-label={t(track.label)}>
          <header><h3>{track.id==='systems'?pick('系统','Systems'):t(track.label)}</h3><span>{track.id==='systems'?pick('Systems · 推训','Training & serving'):track.name}</span><p>{t(homeDefinitions[track.id])}</p><Link to={ROOT+'?track='+track.id}>{pick('完整图谱','Full map')} ↗</Link></header>
          <div className="evolution-home-board" style={{height:layout.height}}>
            <svg className="evolution-home-lines" width={layout.width} height={layout.height} aria-hidden="true"><defs><marker id={'home-arrow-'+track.id} markerWidth="5" markerHeight="5" refX="4" refY="2.5" orient="auto"><path d="M0 0L4 2.5L0 5"/></marker></defs>{layout.paths.map(({relation,d})=><path key={relation.id} data-relation={relation.id} className={relation.kind} d={d} markerEnd={'url(#home-arrow-'+track.id+')'}><title>{t(relationCopy[relation.kind])} · {t(relation.reason)}</title></path>)}</svg>
            {layout.items.map(({node,x,y,width,height})=><button key={node.id} type="button" data-home-node={node.id} className="evolution-home-node" style={{left:x,top:y,width,height} as CSSProperties} onClick={e=>{trigger.current=e.currentTarget;setSelected(node.id);}} aria-haspopup="dialog" aria-expanded={selected===node.id} aria-controls="evolution-home-detail"><time>{node.date.slice(0,4)}</time><strong>{t(node.summary.technology)}</strong><span>{node.summary.representative}</span></button>)}
          </div>
        </section>})}
      </div>
    </div>
    <div className="evolution-home-legend"><span><i/>{pick('采用 / 改进 / 组合','Adoption / improvement / combination')}</span><span><i className="alternative"/>{pick('替代路线','Alternative approach')}</span><span>{pick('时间间距不等比；时间先后不表示继承。','Time spacing is not proportional; chronology does not imply inheritance.')}</span><span>{pick('点击节点查看证据','Select a milestone for evidence')}</span></div>
    {target&&<dialog ref={dialog} id="evolution-home-detail" className={'evolution-home-detail evo-'+target.route.track} aria-labelledby={'detail-heading-'+selected} onCancel={()=>setSelected('')} onClose={()=>setSelected('')} onClick={e=>{if(e.target===e.currentTarget){const r=e.currentTarget.getBoundingClientRect();if(e.clientX<r.left||e.clientX>r.right||e.clientY<r.top||e.clientY>r.bottom)setSelected('');}}}>
      <div className="atlas-inspector"><NodeDetail node={target.node} route={target.route} close={()=>setSelected('')}/><Link className="evolution-home-locate" to={nodeDestination(selected)}>{pick('在完整图谱中定位','Locate in the full map')} →</Link></div>
    </dialog>}
  </>;
}
