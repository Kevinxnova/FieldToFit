import { useMemo, useRef, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { useRemote } from '../../api/knowledge';
import { SourceLink, useWorkspace } from './UI';
import { placeLabels } from './chartLabels';

type Model = { id:string; name:string; organization:string; source_organization:string; score:number|null; score_low?:number; score_high?:number; price:number|null; score_url:string; price_url:string; configuration:string; configuration_en:string; release_date:string|null; date_url:string|null; date_basis:string|null; missing?:string[]; estimated?:boolean; deprecated?:boolean };
type Point = Model & {score:number;price:number};
type ChartSource = { id:string; name:string; source_url:string; source_updated_at:string|null; checked_at:string; score_label:string; price_label:string; price_label_en:string; note:string; note_en:string; flagship:{reviewed_at:string;policy:string;policy_en:string;models:{company:string;family:string;id:string|null;evidence_url:string;status:string}[]}; points:Point[]; not_plotted:Model[]; undated:Model[]; coverage:{source_models:number;released_2026:number;outside_year:number;plotted:number;missing_coordinates:number;unconfirmed_date:number} };
type Landscape = { revision:string; interval_days:number; sources:ChartSource[] };
const choices = [{id:'artificial-analysis',name:'Artificial Analysis'},{id:'arena',name:'Arena'}];
export const companyColors:Record<string,string> = {OpenAI:'#242b35',Anthropic:'#a4542a',Google:'#238340',xAI:'#8051ad',Meta:'#157ab9',Kimi:'#168f9d',GLM:'#9b445f',Qwen:'#bd6714',MIMO:'#907900',MiniMax:'#d33981',DeepSeek:'#3456d1','其他':'#69757a'};
const fmt=(n:number)=>n.toLocaleString('en-US',{maximumFractionDigits:4});

export function ModelLandscape() {
  const {pick}=useWorkspace();
  const result=useRemote<Landscape>('/v1/platform/model-landscape');
  const [params,setParams]=useSearchParams();
  const selected=params.get('chart');
  const current=choices.some(c=>c.id===selected)?selected!:'artificial-analysis';
  const tabs=useRef<(HTMLButtonElement|null)[]>([]);
  const source=result.data?.sources.find(s=>s.id===current);
  const choose=(index:number,focus=false)=>{
    setParams(p=>{p.set('chart',choices[index].id);return p;},{replace:true,preventScrollReset:true});
    if(focus)tabs.current[index]?.focus();
  };
  return <section className="model-landscape" aria-labelledby="model-landscape">
    <p className="platform-eyebrow">2026 · MODEL LANDSCAPE</p><h2 id="model-landscape" tabIndex={-1}>{pick('模型能力与价格','Model capability & pricing')}</h2>
    <p>{pick('看今年发布的模型落在哪里：越靠左，成本越低；越靠上，该项评分越高。同一公司使用同一颜色，名称沿用来源。可筛选公司、搜索模型，或放大看完整分布。','Explore this year’s models: left means lower cost; higher means a higher score on that metric. Companies share colors across charts; names follow the sources. Filter, search or enlarge to read the distribution.')}</p>
    <div className="landscape-tabs" role="tablist" aria-label={pick('图表来源','Chart source')}>{choices.map((c,i)=><button key={c.id} ref={node=>{tabs.current[i]=node;}} id={'chart-tab-'+c.id} role="tab" aria-selected={current===c.id} aria-controls={'chart-panel-'+c.id} tabIndex={current===c.id?0:-1} onClick={()=>choose(i)} onKeyDown={e=>{let next:number|undefined;if(e.key==='ArrowRight'||e.key==='ArrowLeft')next=(i+1)%choices.length;if(e.key==='Home')next=0;if(e.key==='End')next=choices.length-1;if(next!==undefined){e.preventDefault();choose(next,true);}}}>{c.name}</button>)}</div>
    <div role="tabpanel" id={'chart-panel-'+current} aria-labelledby={'chart-tab-'+current} tabIndex={0} className="landscape-panel">
      {result.loading&&<p role="status">{pick('正在读取已核验图表…','Loading reviewed charts…')}</p>}
      {result.error&&<div role="alert"><p>{pick('图表暂时无法读取，近期动态仍可继续阅读。','Charts are unavailable. You can still read the developments.')}</p><button className="button" onClick={result.reload}>{pick('重试','Retry')}</button></div>}
      {source&&<Scatter key={current} source={source}/>}
    </div>
    <details className="landscape-explanation"><summary>{pick('如何理解这两个来源？','How do these sources differ?')}</summary><ul>
      <li><strong>Artificial Analysis：</strong>{pick('标准化评测的 Intelligence Index v4.3。横轴为每项评测任务的加权成本，包含输入、缓存、推理和答案用量；不是每百万 token 单价，也不是你的任务报价。','Intelligence Index v4.3 from standardized benchmarks. The x-axis is weighted cost per benchmark task, including input, caching, reasoning and answers—not a token price or a quote for your task.')}</li>
      <li><strong>Arena：</strong>{pick('Text Overall 开启 Style Control 的用户偏好评分。横轴为每百万输出 token 单价，不包含输入成本或回答长度。竖线保留来源评分区间；受欢迎不等于专业任务正确。','Text Overall preference scores with Style Control enabled. The x-axis is price per million output tokens, excluding input cost and answer length. Vertical lines retain source score intervals; preference is not specialized-task accuracy.')}</li>
      <li>{pick('两家的分数和价格口径不能直接比较。横轴为对数刻度，相同距离表示相同倍数。同一模型不同配置保留为不同点；连线仅指向名称，不表示趋势。','Neither scores nor cost definitions are interchangeable. Logarithmic x-axes show equal ratios at equal distances. Configurations remain separate points; leaders connect labels, not trends.')}</li>
      <li>{pick('范围是这两个来源收录且日期依据落在 2026 年的模型 / 版本。AA 使用来源发布日期；Arena 另核对对应模型发布记录或明确带年份的版本日期。缺价格、评分或日期的条目在覆盖清单中保留，不补造坐标。','Coverage is source-listed models / versions with date evidence in 2026. AA provides release dates; Arena dates use matched release records or explicitly dated versions. Missing prices, scores or dates remain in the coverage list without invented coordinates.')}</li>
    </ul><p>{pick('每 1 天检查来源可用性，数值经核对后随版本更新。检查成功不代表数值已更新；来源日期未知时不以本站检查日期代替。','Sources are checked daily; reviewed values ship with a version update. Successful checks do not refresh values or replace unknown source dates.')}</p></details>
  </section>;
}

function Scatter({source}:{source:ChartSource}) {
  const {pick,zh}=useWorkspace();
  const [filterParams,setFilterParams]=useSearchParams();
  const requested=filterParams.get('company');
  const company=requested==='flagship'||(requested&&Object.prototype.hasOwnProperty.call(companyColors,requested))?requested:'all';
  const setCompany=(value:string)=>setFilterParams(p=>{if(value==='all')p.delete('company');else p.set('company',value);return p;},{replace:true,preventScrollReset:true});
  const flagshipIds=new Set(source.flagship.models.map(m=>m.id));
  const [query,setQuery]=useState(''),[selected,setSelected]=useState<string|null>(null),[scale,setScale]=useState(1);
  const dialog=useRef<HTMLDialogElement>(null),zoom=useRef<HTMLButtonElement>(null);
  const matches=(p:Model)=>(company==='all'||(company==='flagship'?flagshipIds.has(p.id):p.organization===company))&&p.name.toLowerCase().includes(query.trim().toLowerCase());
  const points=source.points.filter(matches),missing=source.not_plotted.filter(matches),undated=source.undated.filter(matches);
  const point=points.find(p=>p.id===selected);
  const width=1400,height=1200,left=78,right=1310,top=86,bottom=1080;
  // Keep domains fixed when filtering so a model never appears to gain capability or lose cost.
  const low=Math.floor(Math.min(...source.points.map(p=>p.score_low??p.score))/5)*5-5;
  const high=Math.ceil(Math.max(...source.points.map(p=>p.score_high??p.score))/5)*5+5;
  const priceMin=10**Math.floor(Math.log10(Math.min(...source.points.map(p=>p.price))));
  const priceMax=10**Math.ceil(Math.log10(Math.max(...source.points.map(p=>p.price))));
  const x=(n:number)=>left+(Math.log10(n)-Math.log10(priceMin))/(Math.log10(priceMax)-Math.log10(priceMin))*(right-left);
  const y=(n:number)=>bottom-(n-low)/(high-low)*(bottom-top);
  const labels=useMemo(()=>placeLabels(points.map(p=>({id:p.id,name:p.name,x:x(p.price),y:y(p.score)})),width,height),[source,company,query]);
  const byId=new Map(labels.map(p=>[p.id,p]));
  const ticks:number[]=[];for(let decade=priceMin;decade<=priceMax*1.001;decade*=10)for(const m of [1,2,5])if(decade*m<=priceMax*1.001)ticks.push(decade*m);
  const date=source.source_updated_at||pick('来源未标注','Not provided by source');
  const plot=(expanded=false)=><svg viewBox={`0 0 ${width} ${height}`} style={{width:expanded?`${scale*100}%`:'100%',minWidth:expanded?'1000px':undefined}} role="group" aria-label={source.name+pick(' 能力与价格散点图',' capability and price scatterplot')}>
    <title>{source.name} · 2026 · {source.score_label}</title><desc>{pick('横轴是对数价格，纵轴是评分。点旁直接标注来源模型名，同公司同色。点击模型或用键盘选择查看依据。','Logarithmic price on x, score on y. Original model names label dots, colored by company. Select a model by click or keyboard to inspect evidence.')}</desc>
    <text x={left} y={34} className="chart-axis-title">{source.score_label} ↑</text>
    {Array.from({length:9},(_,i)=>low+(high-low)*i/8).map(v=><g key={v}><line className="chart-grid" x1={left} x2={right} y1={y(v)} y2={y(v)}/><text className="chart-tick" x={left-12} y={y(v)+5} textAnchor="end">{Number(v.toFixed(1))}</text></g>)}
    {ticks.map(v=><g key={v}><line className="chart-grid" x1={x(v)} x2={x(v)} y1={top} y2={bottom}/><text className="chart-tick" x={x(v)} y={bottom+28} textAnchor="middle">${fmt(v)}</text></g>)}
    {points.map(p=>{const l=byId.get(p.id)!;return <line key={p.id} className="chart-leader" x1={l.x} y1={l.y} x2={Math.max(l.lx,Math.min(l.lx+l.width,l.x))} y2={l.ly+8} stroke={companyColors[p.organization]}/>;})}
    {points.map(p=>{const l=byId.get(p.id)!;const color=companyColors[p.organization];return <g key={p.id} data-model-id={p.id} data-company={p.organization} className={'chart-point'+(selected===p.id?' selected':'')} role="button" tabIndex={0} aria-label={`${p.name}; ${source.score_label}: ${fmt(p.score)}; ${source.price_label_en}: ${fmt(p.price)}`} onClick={()=>setSelected(p.id)} onKeyDown={e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();setSelected(p.id);}}}>
      <title>{p.name}: {fmt(p.score)} · ${fmt(p.price)}</title>
      {p.score_low!==undefined&&p.score_high!==undefined&&<line className="chart-interval" x1={l.x} x2={l.x} y1={y(p.score_low)} y2={y(p.score_high)} stroke={color}/>}
      <circle cx={l.x} cy={l.y} r={selected===p.id?8:6} fill={p.estimated?'white':color} stroke={color}/><text x={l.lx} y={l.ly+13} className="chart-model-name" fill={color}>{p.name}</text>
    </g>;})}
    <text className="chart-axis-title" x={(left+right)/2} y={1140} textAnchor="middle">{zh?source.price_label:source.price_label_en} · {pick('对数刻度','log scale')} →</text>
    <text className="chart-credit" x={left} y={1180}>Source: {source.name} · {pick('源日期','Source date')}: {date} · FieldToFit {source.checked_at}</text>
  </svg>;
  const details=point?<div className="landscape-point-detail" aria-live="polite"><strong>{point.name}</strong><p>{point.source_organization||point.organization} · {source.score_label}: <b>{fmt(point.score)}</b> · {zh?source.price_label:source.price_label_en}: <b>${fmt(point.price)}</b></p><p>{zh?point.configuration:point.configuration_en}</p><p>{dateDescription(point)} {point.release_date}{point.date_url&&<> · <SourceLink url={point.date_url}>{pick('日期依据','Date evidence')}</SourceLink></>}{point.deprecated&&pick(' · 来源已标为旧版本',' · Deprecated by source')}</p><SourceLink url={point.score_url}>{pick('核对评分与价格','Verify score and price')}</SourceLink></div>:<p className="landscape-hint">{pick('点击图中的模型名称或圆点，查看数值与依据。','Select a model name or dot to inspect values and evidence.')}</p>;
  function dateDescription(p:Model){return p.date_basis==='source_version_date'?pick('来源版本日期：','Source version date: '):p.date_basis==='matched_model_release'?pick('对应模型发布记录：','Matched model release: '):pick('发布日期：','Release date: ');}
  const table=(models:Model[],caption:string)=><div className="watch-table-scroll" tabIndex={0}><table className="watch-table"><caption>{caption}</caption><thead><tr><th>{pick('来源模型名 / 公司','Source model / company')}</th><th>{pick('日期依据','Date evidence')}</th><th>{source.score_label}</th><th>{zh?source.price_label:source.price_label_en}</th><th>{pick('依据 / 缺项','Evidence / gaps')}</th></tr></thead><tbody>{models.map(p=><tr key={p.id}><th scope="row">{p.name}<small className="chart-table-org">{p.source_organization||p.organization}</small></th><td>{p.release_date?<>{dateDescription(p)}<br/>{p.release_date}<br/>{p.date_url&&<SourceLink url={p.date_url}>{pick('日期出处','Date source')}</SourceLink>}</>:pick('尚未确认；未计入 2026','Unconfirmed; not counted as 2026')}</td><td>{p.score===null?'—':fmt(p.score)}{p.estimated&&pick('（估计）',' (estimated)')}{p.score_low!==undefined&&<small className="chart-table-org">{fmt(p.score_low)}–{fmt(p.score_high!)}</small>}</td><td>{p.price===null?'—':'$'+fmt(p.price)}</td><td><SourceLink url={p.score_url}>{pick('来源','Source')}</SourceLink>{p.missing?.map(reason=><div key={reason}>{reason==='missing_score'?pick('缺评分','Missing score'):reason==='missing_price'?pick('缺价格','Missing price'):pick('非正价格不进入对数图','Non-positive price cannot be plotted on log scale')}</div>)}{p.deprecated&&<div>{pick('来源已标为旧版本','Deprecated by source')}</div>}</td></tr>)}</tbody></table></div>;
  return <>
    <div className="landscape-chart-heading"><h3>{source.name} <span>2026</span></h3><button ref={zoom} className="text-button" onClick={()=>{setScale(1);dialog.current?.showModal();}}>{pick('放大查看','Enlarge chart')}</button></div>
    <p className="landscape-scope">{zh?source.note:source.note_en}</p>
    <div className="chart-company-legend" aria-label={pick('按公司筛选','Filter by company')}><button aria-pressed={company==='all'} onClick={()=>setCompany('all')}>{pick('全部公司','All companies')}</button><button aria-pressed={company==='flagship'} onClick={()=>{setCompany('flagship');setQuery('');setSelected(null);}}>{pick('各家旗舰模型','Company flagships')}<small>{source.flagship.models.filter(m=>m.status==='plotted').length}</small></button>{Object.entries(companyColors).map(([name,color])=><button key={name} aria-pressed={company===name} onClick={()=>setCompany(company===name?'all':name)}><i style={{background:color}}/>{name==='其他'?pick('其他','Other'):name}<small>{source.points.filter(p=>p.organization===name).length}</small></button>)}</div>
    {company==='flagship'&&<div className="chart-flagship-note"><p>{pick('本期旗舰系列，每家一个代表配置；名单由 FieldToFit 维护。','One representative configuration per company’s selected flagship series; curated by FieldToFit.')} {pick('名单核验：','Selection reviewed: ')}{source.flagship.reviewed_at}</p><details><summary>{pick('查看旗舰名单与缺项','View flagship selection and gaps')}</summary><p>{zh?source.flagship.policy:source.flagship.policy_en}</p><ul>{source.flagship.models.map(m=><li key={m.company}><strong>{m.company}</strong> · <SourceLink url={m.evidence_url}>{m.family}</SourceLink> · {m.status==='plotted'?pick('已绘制','Plotted'):m.status==='missing_coordinates'?pick('来源缺少坐标数据，暂未绘制','Missing coordinates; not plotted'):m.status==='unconfirmed_date'?pick('来源日期待确认，暂未绘制','Date unconfirmed; not plotted'):pick('当前来源快照未收录，暂未绘制','Not listed in this source snapshot')}</li>)}</ul></details></div>}
    <div className="chart-search"><label>{pick('查找模型','Find a model')}<input type="search" value={query} onChange={e=>setQuery(e.target.value)} placeholder={pick('输入来源中的模型名称','Search original model names')}/></label><button className="text-button" onClick={()=>{setCompany('all');setQuery('');setSelected(null);}}>{pick('重置筛选','Reset filters')}</button></div>
    <p className="chart-coverage" role="status">{pick(`图中 ${points.length} / ${source.points.length} 个模型配置 · 已核对 ${source.coverage.released_2026} 个 2026 年条目 · ${source.not_plotted.length} 个缺少可用坐标`,`${points.length} / ${source.points.length} configurations plotted · ${source.coverage.released_2026} dated to 2026 · ${source.not_plotted.length} without usable coordinates`)}</p>
    {points.length?<div className="landscape-plot">{plot()}</div>:<p className="landscape-empty">{pick('当前筛选没有可绘制的模型。可查看下方缺项清单，或重置筛选。','No plottable models match. Check the coverage list below or reset filters.')}</p>}
    {details}
    <div className="landscape-attribution"><p>{pick('引用来源：','Source: ')}<SourceLink url={source.source_url}>{source.name}</SourceLink> · {pick('FieldToFit 根据公开数值绘制。','Drawn by FieldToFit from public values.')}</p><p>{pick('源数据更新：','Source updated: ')}<span data-source-date>{date}</span> · {pick('本站核验 / 同步：','Reviewed / synced: ')}{source.checked_at}</p>{!source.source_updated_at&&<p>{pick('来源未标明本组数据的整体更新时间；模型发布日期不作为数据更新日期。','No overall update date is given; model release dates are not data update dates.')}</p>}</div>
    <details className="landscape-data"><summary>{pick(`数值与出处（当前筛选 ${points.length}）`,`Values and sources (${points.length} matching)`)}</summary>{table(points,source.name+' · 2026')}</details>
    <details className="landscape-data landscape-coverage"><summary>{pick(`覆盖与缺项：${missing.length} 个缺少坐标，${undated.length} 个日期待确认`,`Coverage: ${missing.length} missing coordinates, ${undated.length} unconfirmed dates`)}</summary><p>{pick(`已读取来源 ${source.coverage.source_models} 个条目：${source.coverage.released_2026} 个归入 2026 年，${source.coverage.outside_year} 个日期在其他年份，${source.undated.length} 个日期尚未确认。下表随筛选变化；日期待确认不意味着属于今年。`,`Reviewed ${source.coverage.source_models} source entries: ${source.coverage.released_2026} dated to 2026, ${source.coverage.outside_year} to other years, ${source.undated.length} unconfirmed. Tables follow filters; undated entries are not assumed to be from 2026.`)}</p>{missing.length>0&&table(missing,pick('2026 年 · 缺少坐标','2026 · Missing coordinates'))}{undated.length>0&&table(undated,pick('来源条目 · 日期待确认','Source entries · Unconfirmed dates'))}</details>
    <dialog ref={dialog} className="landscape-dialog" onClose={()=>zoom.current?.focus()}><div className="landscape-chart-heading"><h3>{source.name} · 2026</h3><label>{pick('缩放','Zoom')} <select value={scale} onChange={e=>setScale(Number(e.target.value))}><option value={1}>100%</option><option value={1.5}>150%</option><option value={2}>200%</option></select></label><button className="button" autoFocus onClick={()=>dialog.current?.close()}>{pick('关闭','Close')}</button></div><p className="landscape-hint">{pick('可横向、纵向滚动；与主图使用同一公司筛选，点击模型查看依据。','Scroll in both directions. Filters match the main chart; select a model for evidence.')}</p><div className="landscape-zoom-scroll" tabIndex={0}>{plot(true)}</div>{details}<p>{pick('源数据更新：','Source updated: ')}{date} · {pick('本站核验：','Checked: ')}{source.checked_at}</p></dialog>
  </>;
}
