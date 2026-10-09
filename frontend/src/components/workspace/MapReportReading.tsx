import {useEffect,useRef,useState} from 'react';
import type {MapEvidence,TechnicalMap} from './TechnicalMaps';
import type {NewsItem} from './NewsReading';
import {SourceLink,useWorkspace} from './UI';

export type ReadingBlock={kind:'paragraph'|'points'|'highlight'|'figure';text?:string;items?:string[];label?:'claim'|'evidence'|'limit';image_url?:string;alt?:string;caption?:string;attribution?:string;license?:string;evidence?:MapEvidence[]};
export type MapFinding={id:string;title:string;summary:string;node_ids:string[];evidence:MapEvidence[];blocks:ReadingBlock[]};
export type MapReading={title:string;findings:MapFinding[];editorial:string[]};
export const argumentId=(id:string)=>'argument-'+id;
export function ReadingEvidence({points,sources}:{points:MapEvidence[];sources:NewsItem['sources']}){return <ul className="map-evidence">{points.map((e,i)=>{const s=sources.find(x=>x.id===e.source_id);return s&&<li key={i}><SourceLink url={s.url.split('#')[0]+(e.fragment?'#'+e.fragment:'')}>{s.title} · {e.locator}</SourceLink></li>;})}</ul>;}
function Figure({block,sources}:{block:ReadingBlock;sources:NewsItem['sources']}){
 const {pick}=useWorkspace();const [open,setOpen]=useState(false);const dialog=useRef<HTMLDialogElement>(null);
 useEffect(()=>{if(open&&!dialog.current?.open)dialog.current?.showModal();},[open]);
 return <figure className="map-report-figure"><button className="map-figure-button" type="button" onClick={()=>setOpen(true)} aria-label={pick('放大图表：','Enlarge figure: ')+block.alt}><img src={block.image_url} alt={block.alt} loading="lazy"/></button><figcaption><strong>{block.caption}</strong><span>{block.attribution} · {block.license}</span><ReadingEvidence points={block.evidence||[]} sources={sources}/><button type="button" className="text-button" onClick={()=>setOpen(true)}>{pick('放大图表','Enlarge figure')}</button> · <a href={block.image_url} target="_blank" rel="noopener noreferrer">{pick('打开完整图片','Open full image')}</a></figcaption>
 {open&&<dialog ref={dialog} className="map-figure-dialog" aria-label={pick('报告图表放大','Enlarged report figure')} onClose={()=>setOpen(false)} onClick={e=>{if(e.target===dialog.current)dialog.current?.close();}}><button type="button" autoFocus onClick={()=>dialog.current?.close()}>{pick('关闭图片','Close image')}</button><p>{block.caption}</p><div className="map-figure-zoom"><img src={block.image_url} alt={block.alt}/></div><p>{block.attribution} · {block.license}</p><ReadingEvidence points={block.evidence||[]} sources={sources}/></dialog>}
 </figure>;
}
export function MapReportReading({map,sources,highlightNode,prefix='',onRoute}:{map:TechnicalMap;sources:NewsItem['sources'];highlightNode?:string;prefix?:string;onRoute?:(id:string)=>void}){
 const {pick}=useWorkspace();const reading=map.reading;if(!reading)return null;
 return <section className="map-report-reading" aria-label={pick('技术报告阅读','Technical report reading')}><header><p className="platform-eyebrow">{pick('先读结论，再看依据','FINDINGS, THEN EVIDENCE')}</p><h2 id={prefix+'report-findings'} tabIndex={-1}>{reading.title}</h2><p>{pick('以下为作者报告的中文整理；FieldToFit的判断单独列在末尾。','A curated reading of the author report. FieldToFit interpretation follows separately.')}</p></header>
 <ol className="map-core-findings">{reading.findings.map(f=><li id={prefix+'finding-'+f.id} key={f.id}><a href={'#'+prefix+argumentId(f.id)}><strong><mark>{f.title}</mark></strong></a><p>{f.summary}</p><a className="map-reading-link" href={'#'+prefix+argumentId(f.id)}>{pick('阅读对应论述','Read the argument')} →</a></li>)}</ol>
 {reading.findings.map((f,i)=><section className={'map-report-argument'+(highlightNode&&f.node_ids.includes(highlightNode)?' route-selected':'')} key={f.id} id={prefix+argumentId(f.id)} tabIndex={-1}><p className="platform-eyebrow">{pick('核心观点','FINDING')} {i+1}</p><h3>{i+1}. {f.title}</h3>{f.blocks.map((b,j)=>b.kind==='figure'?<Figure key={j} block={b} sources={sources}/>:b.kind==='points'?<ol key={j} className="map-report-points">{b.items?.map((s,k)=><li key={k}>{s}</li>)}</ol>:b.kind==='highlight'?<p key={j} className={'map-report-highlight '+b.label}><small>{pick(({claim:'作者结论',evidence:'关键证据',limit:'适用边界'})[b.label||'claim'],({claim:'Author finding',evidence:'Key evidence',limit:'Scope'})[b.label||'claim'])}</small><mark>{b.text}</mark></p>:<p key={j}>{b.text}</p>)}<ReadingEvidence points={f.evidence} sources={sources}/><nav className="map-report-navigation"><a href={'#'+prefix+'finding-'+f.id}>{pick('回到这条结论','Back to this finding')} ↑</a><a href={'#'+prefix+'map-overview'} onClick={()=>onRoute?.(f.node_ids.find(id=>map.nodes.some(n=>n.id===id&&n.kind==='method'))||f.node_ids[0])}>{pick('回到路线全貌','Back to overview')} ↑</a><a href={'#'+prefix+argumentId(f.id)}>{pick('本段链接','Link to this section')}</a></nav></section>)}
 {!!reading.editorial.length&&<aside className="map-editorial"><h2>{pick('FieldToFit 的判断','FieldToFit interpretation')}</h2>{reading.editorial.length>1?<ol>{reading.editorial.map((s,i)=><li key={i}>{s}</li>)}</ol>:<p>{reading.editorial[0]}</p>}</aside>}
 </section>;
}
export function mapThumbnail(map:TechnicalMap){return map.reading?.findings.flatMap(f=>f.blocks).find(b=>b.kind==='figure');}
