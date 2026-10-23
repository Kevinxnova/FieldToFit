import {useEffect,useRef} from 'react';
import {Link,useSearchParams} from '@fieldtofit/locale/router';
import {useWorkspace} from '../../components/workspace/UI';
import {catalog,nodeById,ROOT,type Copy,type Track} from './data';
import {flagships,modelById,modelEdges,validModels,compareModels,modelNodeLabel,type Adoption} from './flagships';
import {TrackMap} from './TrackMap';
import './flagships.css';

export function AdoptionEvidence({edge,choose}:{edge:Adoption;choose?:(id:string,track:Track)=>void}){
  const {zh,pick}=useWorkspace(),t=(c:Copy)=>c[zh?0:1],source=catalog.sources[edge.source];
  return <article className="flagship-evidence" data-evidence={edge.id}>
    {choose?<button onClick={()=>choose(edge.node,edge.track)}>{modelNodeLabel(edge.node,zh)} ↗</button>:<strong>{modelNodeLabel(edge.node,zh)}</strong>}
    <p>{t(edge.statement)}</p><p className="flagship-boundary">{t(edge.boundary)}</p>
    <a href={source.url} target="_blank" rel="noreferrer">{source.title} ↗</a>
    <small>{t(edge.section)} · {pick('相关正文已核','Relevant text reviewed')} · {pick('资料日期','Source date')} {source.date||pick('未标','Not stated')} · {pick('核对','Checked')} {edge.checked_at}</small>
  </article>;
}
export function FlagshipExplorer({home=false}:{home?:boolean}){
  const {zh,pick}=useWorkspace(),t=(c:Copy)=>c[zh?0:1], [params,setParams]=useSearchParams();
  const models=validModels(params.get('evolution_models')),requested=params.get(home?'evolution_node':'node')||'',selected=Object.prototype.hasOwnProperty.call(nodeById,requested)?requested:'';
  const map=params.get('evolution_map')||nodeById[selected]?.route.track;
  const previousTrack=useRef('');
  const choose=(id:string,track:Track)=>setParams(old=>{const next=new URLSearchParams(old);next.set(home?'evolution_node':'node',id);next.set('evolution_map',track);if(!home)next.set('track',nodeById[id].route.track);return next;});
  const close=()=>setParams(old=>{const next=new URLSearchParams(old);next.delete(home?'evolution_node':'node');return next;},{replace:true});
  const setModels=(ids:string[])=>setParams(old=>{const next=new URLSearchParams(old),value=validModels(ids.join(','));value.length?next.set('evolution_models',value.join(',')):next.delete('evolution_models');return next;});
  function selectModel(id:string){setModels(models.includes(id)?models.filter(v=>v!==id):models.length<2?[...models,id]:[models[0],id]);}
  useEffect(()=>{
    const track=params.get('track')||'';if(home||selected||!catalog.tracks.some(v=>v.id===track)||previousTrack.current===track)return;
    previousTrack.current=track;const frame=requestAnimationFrame(()=>document.getElementById('track-'+track)?.scrollIntoView({block:'start'}));return()=>cancelAnimationFrame(frame);
  },[params.get('track'),selected,home]);
  const fullLink=ROOT+(models.length?'?evolution_models='+encodeURIComponent(models.join(',')):'');
  return <div className={'flagship-explorer'+(home?' home':'')}>
    <div className="flagship-toolbar">
      <div><strong>{pick('从技术看模型，从模型追溯技术','From methods to models, and back')}</strong><p>{pick('选择一个型号追溯三图，选择两个对照已公开的路线。','Choose one model to trace all three maps, or two to compare disclosed approaches.')}</p></div>
      <div className="flagship-selectors">{[0,1].map(i=><label key={i}>{pick(i?'对比型号':'查看型号',i?'Compare with':'Explore model')}<select aria-label={pick(i?'对比型号':'查看型号',i?'Compare with':'Explore model')} value={models[i]||''} onChange={e=>{const next=[...models];next[i]=e.target.value;setModels(next.filter(Boolean));}}><option value="">{pick(i?'选择第二个型号':'全部技术主线',i?'Choose a second model':'All technical paths')}</option>{flagships.models.filter(m=>!models.includes(m.id)||models[i]===m.id).map(m=><option key={m.id} value={m.id}>{catalog.companies[m.company]} · {m.name}</option>)}</select></label>)}<button disabled={!models.length} onClick={()=>setModels([])}>{pick('清除选择','Clear selection')}</button></div>
    </div>
    <p className="flagship-caption">{flagships.scope.length} {pick('家公司','companies')} · {flagships.models.length} {pick('个型号／待核条目','model / unresolved entries')} · {flagships.adoptions.length} {pick('条型号披露','model disclosures')} · {pick('核对','Checked')} {flagships.checked_at} · {pick('未连线不等于未采用，资料核对日不等于模型首发日。','No link does not imply non-use; the check date is not a model launch date.')}</p>
    {params.get('evolution_models')&&validModels(params.get('evolution_models')).join(',')!==params.get('evolution_models')&&<p role="status">{pick('部分型号参数无效或重复，已保留有效的最多两个型号。','Some model parameters are invalid or duplicated; up to two valid models are shown.')}</p>}
    <details className="flagship-directory"><summary>{pick('型号目录与资料状态','Model directory and evidence status')} · {flagships.models.length}</summary><div>{flagships.models.map(m=><article key={m.id}><button aria-pressed={models.includes(m.id)} onClick={()=>selectModel(m.id)}>{m.name}</button><small>{catalog.companies[m.company]} · {t(m.role)} · {t(m.status)}</small><p>{t(m.notes)}</p><a href={catalog.sources[m.source].url} target="_blank" rel="noreferrer">{pick('身份资料','Identity source')} ↗</a></article>)}</div></details>
    {models.length===2&&<section className="flagship-comparison" aria-label={pick('型号路线比较','Model route comparison')}><h3>{modelById[models[0]].name} <span>×</span> {modelById[models[1]].name}</h3><p>{pick('比较的是公开证据，不是能力排名；只有一侧披露，不表示另一侧没有采用。','This compares public evidence, not capability rankings. Disclosure on one side does not imply non-use on the other.')}</p><div className="flagship-compare-scroll"><table><thead><tr><th>{pick('总图','Map')}</th><th>{pick('共同披露的技术身份','Shared disclosed mechanisms')}</th><th>{modelById[models[0]].name} · {pick('另有披露','Additional disclosures')}</th><th>{modelById[models[1]].name} · {pick('另有披露','Additional disclosures')}</th></tr></thead><tbody>{catalog.tracks.map(track=>{const comparison=compareModels(models[0],models[1],track.id);return <tr key={track.id}><th>{t(track.label)}</th>{[comparison.common,comparison.left,comparison.right].map((ids,i)=><td key={i}>{ids.length?ids.map(id=><button key={id} onClick={()=>choose(id,track.id)}>{modelNodeLabel(id,zh)}</button>):pick('未有可确认项','No confirmed item')}</td>)}</tr>;})}</tbody></table></div></section>}
    {models.length>0&&<section className="flagship-selected" aria-label={pick('所选型号证据','Selected model evidence')}>{models.map((id,i)=>{const m=modelById[id];return <article key={id} className={'model-color-'+i}><header><h3><span className="flagship-dot"/>{m.name}</h3><span>{t(m.status)}</span></header><p>{t(m.notes)}</p><small>{t(m.date_kind)} · {m.date||pick('未标','Not stated')} · {t(m.role)}</small>{catalog.tracks.map(track=>{const edges=modelEdges(id,track.id);return <details key={track.id}><summary>{t(track.label)} · {edges.length?edges.length+' '+pick('条披露','disclosures'):pick('证据待补','Evidence gap')}</summary><p>{t(m.gaps[track.id])}</p>{edges.map(e=><AdoptionEvidence key={e.id} edge={e} choose={choose}/>)}</details>;})}<a href={catalog.sources[m.source].url} target="_blank" rel="noreferrer">{pick('型号原始资料','Original model source')} ↗</a></article>;})}</section>}
    {requested&&!selected&&<p role="status">{pick('节点未找到，完整图仍可浏览。','Milestone not found; all maps remain available.')}</p>}
    {catalog.tracks.map(track=><TrackMap key={track.id} track={track.id} selected={map===track.id?selected:''} models={models} selectModel={selectModel} compact={home} company={params.get('company')||''} choose={id=>choose(id,track.id)} close={close} recent={!home&&params.get('period')==='recent'&&(!params.get('track')||params.get('track')===track.id)}/>)}
    <details className="flagship-text-list"><summary>{pick('按时间阅读文字目录','Read the chronological text directory')}</summary>{catalog.tracks.map(track=><section key={track.id}><h3>{t(track.label)}</h3><ul>{catalog.routes.filter(r=>r.track===track.id).flatMap(r=>r.nodes).sort((a,b)=>a.date.localeCompare(b.date)).map(n=><li key={n.id}><button onClick={()=>choose(n.id,track.id)}>{n.date} · {t(n.summary.technology)} · {n.summary.representative}</button></li>)}</ul></section>)}</details>
    {home&&<Link className="flagship-full-link" to={fullLink}>{pick('进入完整技术图谱，保留型号选择','Open the complete maps with this model selection')} →</Link>}
  </div>;
}
