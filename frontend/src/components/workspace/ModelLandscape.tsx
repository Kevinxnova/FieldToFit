import { useEffect, useRef, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { useRemote } from '../../api/knowledge';
import { SourceLink, useWorkspace } from './UI';

type Point = { name:string; organization:string; score:number; score_low?:number; score_high?:number; price:number; score_url:string; price_url:string; configuration:string; configuration_en:string };
type ChartSource = { id:string; name:string; source_url:string; source_updated_at:string|null; checked_at:string; score_label:string; price_label:string; price_label_en:string; note:string; note_en:string; points:Point[] };
type Landscape = { revision:string; interval_days:number; sources:ChartSource[] };
const choices = [{id:'artificial-analysis',name:'Artificial Analysis'},{id:'arena',name:'Arena'},{id:'epoch',name:'Epoch AI'}];
const colors:Record<string,string> = {Anthropic:'#b96745',OpenAI:'#268076',Google:'#4772b8',Meta:'#815db3','Z AI':'#9b6331',Alibaba:'#b35479',Kimi:'#5d7891',DeepSeek:'#4365b5'};

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
    <p className="platform-eyebrow">MODEL LANDSCAPE</p><h2 id="model-landscape" tabIndex={-1}>{pick('模型能力与价格','Model capability & pricing')}</h2>
    <p>{pick('切换评测视角，了解模型的能力表现与价格位置。先看坐标轴，再读模型配置与出处。','Switch evaluation perspectives to explore capability and pricing. Read the axes, then check model configurations and sources.')}</p>
    <div className="landscape-tabs" role="tablist" aria-label={pick('图表来源','Chart source')}>{choices.map((c,i)=><button key={c.id} ref={node=>{tabs.current[i]=node;}} id={'chart-tab-'+c.id} role="tab" aria-selected={current===c.id} aria-controls={'chart-panel-'+c.id} tabIndex={current===c.id?0:-1} onClick={()=>choose(i)} onKeyDown={e=>{let next:number|undefined;if(e.key==='ArrowRight')next=(i+1)%3;if(e.key==='ArrowLeft')next=(i+2)%3;if(e.key==='Home')next=0;if(e.key==='End')next=2;if(next!==undefined){e.preventDefault();choose(next,true);}}}>{c.name}</button>)}</div>
    <div role="tabpanel" id={'chart-panel-'+current} aria-labelledby={'chart-tab-'+current} tabIndex={0} className="landscape-panel">
      {result.loading&&<p role="status">{pick('正在读取已核验图表…','Loading reviewed charts…')}</p>}
      {result.error&&<div role="alert"><p>{pick('图表暂时无法读取，近期动态仍可继续阅读。','Charts are unavailable. You can still read the developments.')}</p><button className="button" onClick={result.reload}>{pick('重试','Retry')}</button></div>}
      {source&&<Scatter key={current} source={source}/>}
    </div>
    <details className="landscape-explanation"><summary>{pick('如何理解这三个来源？','How do these sources differ?')}</summary><ul>
      <li><strong>Artificial Analysis：</strong>{pick('标准化评测的综合能力指数。此图采用每项评测任务的加权成本，包括输入、缓存、推理和答案用量；不是每百万 token 单价，也不是你的任务报价。','A composite of standardized benchmarks. This chart uses weighted cost per benchmark task, including input, caching, reasoning and answers—not a token price or a quote for your task.')}</li>
      <li><strong>Arena：</strong>{pick('用户比较回答形成的偏好评分。关注模型回答是否受欢迎，分数会受任务分布和表达风格影响；不能直接等同于专业任务正确率。竖线表示来源展示的评分区间。','Preference scores from users comparing responses, influenced by tasks and presentation. They do not directly measure specialized-task accuracy. Vertical lines show the source’s score intervals.')}</li>
      <li><strong>Epoch AI：</strong>{pick('ECI 汇总多项基准，帮助观察综合能力。本图由 FieldToFit 将同一模型页面的 ECI 与输出价格配对绘制；ECI 采用跨设置最佳成绩，不能解释为以该价格实测获得的能力。','ECI combines multiple benchmarks. FieldToFit pairs ECI with the output price on the same model page. ECI aggregates best scores across settings; it is not capability measured at that exact cost.')}</li>
      <li>{pick('三家的分数不能直接比较。价格横轴使用对数刻度：相同距离表示相同倍数。图中只摘录部分已核对模型，不是完整排名；API 价格与订阅费用、实际任务花费也不同。','Scores are not comparable between sources. The price axis is logarithmic: equal distances represent equal ratios. These are selected verified examples, not complete rankings. API prices differ from subscriptions and actual task costs.')}</li>
    </ul><p>{pick('按 1 天周期检查来源可用性，数据经核对后随版本更新。检查成功不代表数值已更新；源数据日期未知时不使用本站检查日期代替。','Source availability is checked daily; reviewed data ships with a version update. A successful check does not mean scores changed. Unknown source dates are not replaced with our check date.')}</p></details>
  </section>;
}

function Scatter({source}:{source:ChartSource}) {
  const {pick,zh}=useWorkspace();
  const [selected,setSelected]=useState(0);
  const [compact,setCompact]=useState(()=>window.matchMedia('(max-width:600px)').matches);
  useEffect(()=>{const media=window.matchMedia('(max-width:600px)');const update=()=>setCompact(media.matches);media.addEventListener('change',update);return()=>media.removeEventListener('change',update);},[]);
  const [large,setLarge]=useState(false);
  const dialog=useRef<HTMLDialogElement>(null);
  const zoom=useRef<HTMLButtonElement>(null);
  const points=source.points;
  const point=points[selected];
  const low=Math.floor(Math.min(...points.map(p=>p.score_low??p.score))/5)*5-5;
  const high=Math.ceil(Math.max(...points.map(p=>p.score_high??p.score))/5)*5+5;
  const priceMin=Math.pow(10,Math.floor(Math.log10(Math.min(...points.map(p=>p.price)))));
  const priceMax=Math.pow(10,Math.ceil(Math.log10(Math.max(...points.map(p=>p.price)))));
  const left=compact?48:64,right=compact?396:680,top=72,bottom=370;
  const x=(n:number)=>left+(Math.log10(n)-Math.log10(priceMin))/(Math.log10(priceMax)-Math.log10(priceMin))*(right-left);
  const y=(n:number)=>bottom-(n-low)/(high-low)*(bottom-top);
  const ticks:number[]=[];
  for(let decade=priceMin;decade<=priceMax;decade*=10)for(const m of [1,3])if(decade*m<=priceMax)ticks.push(decade*m);
  const date=source.source_updated_at||pick('来源未标注','Not provided by source');
  const plot=(interactive:boolean)=><svg viewBox={compact?"0 0 420 490":"0 0 720 490"} role={interactive?'group':'img'} aria-label={source.name+pick(' 能力与价格散点图',' capability and price scatterplot')}>
    <title>{source.name} · {source.score_label}</title><desc>{pick('横轴是对数价格，纵轴是评分。编号与下方模型列表对应；每个点可点击或用键盘选择。','Price is logarithmic; scores are on the vertical axis. Point numbers match the model list. Select a point by click or keyboard.')}</desc>
    <text x={left} y={24} className="chart-axis-title">{source.score_label} ↑</text>
    {Array.from({length:5},(_,i)=>low+(high-low)*i/4).map(v=><g key={v}><line className="chart-grid" x1={left} x2={right} y1={y(v)} y2={y(v)}/><text className="chart-tick" x={left-12} y={y(v)+4} textAnchor="end">{Number(v.toFixed(1))}</text></g>)}
    {ticks.map(v=><g key={v}><line className="chart-grid" x1={x(v)} x2={x(v)} y1={top} y2={bottom}/><text className="chart-tick" x={x(v)} y={bottom+24} textAnchor="middle">${v.toPrecision(2).replace(/\.0$/,'')}</text></g>)}
    {points.map((p,i)=>({p,i})).sort((a,b)=>Number(a.i===selected)-Number(b.i===selected)).map(({p,i})=><g key={p.name} className={'chart-point'+(selected===i?' selected':'')} role={interactive?'button':undefined} tabIndex={interactive?0:undefined} aria-label={`${p.name}; ${source.score_label}: ${p.score}; ${source.price_label_en}: ${p.price}`} onClick={()=>setSelected(i)} onKeyDown={e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();setSelected(i);}}}>
      <title>{p.name}: {p.score} · ${p.price}</title>
      {p.score_low!==undefined&&p.score_high!==undefined&&<line x1={x(p.price)} x2={x(p.price)} y1={y(p.score_low)} y2={y(p.score_high)} stroke={colors[p.organization]||'#54756a'} strokeWidth={2}/>}
      <circle cx={x(p.price)} cy={y(p.score)} r={selected===i?15:12} fill={colors[p.organization]||'#54756a'}/><text x={x(p.price)} y={y(p.score)+4} textAnchor="middle" className="chart-point-number">{i+1}</text>
    </g>)}
    <text className="chart-axis-title" x={(left+right)/2} y={425} textAnchor="middle">{zh?source.price_label:source.price_label_en} · {pick('对数刻度','log scale')} →</text>
    <text className="chart-credit" x={left} y={452}>Source: {source.name}</text><text className="chart-credit" x={left} y={474}>{pick('本站核验','Checked')} {source.checked_at} · FieldToFit</text>
  </svg>;
  return <>
    <div className="landscape-chart-heading"><h3>{source.name}</h3><button ref={zoom} className="text-button" onClick={()=>{setLarge(true);dialog.current?.showModal();}}>{pick('放大查看','Enlarge chart')}</button></div>
    <p className="landscape-scope">{zh?source.note:source.note_en}</p>
    <div className="landscape-plot">{plot(true)}</div>
    <div className="landscape-models" aria-label={pick('选择图中模型','Select a plotted model')}>{points.map((p,i)=><button key={p.name} aria-pressed={selected===i} onClick={()=>setSelected(i)}><span style={{background:colors[p.organization]||'#54756a'}}>{i+1}</span>{p.name}</button>)}</div>
    <div className="landscape-point-detail" aria-live="polite"><strong>{point.name}</strong><p>{source.score_label}: <b>{point.score}</b> · {zh?source.price_label:source.price_label_en}: <b>${point.price}</b></p><p>{zh?point.configuration:point.configuration_en}</p><SourceLink url={point.score_url}>{pick('核对评分','Verify score')}</SourceLink> · <SourceLink url={point.price_url}>{pick('核对价格','Verify price')}</SourceLink></div>
    <div className="landscape-attribution"><p>{pick('引用来源：','Source: ')}<SourceLink url={source.source_url}>{source.name}</SourceLink> · {pick('FieldToFit 根据公开数据绘制，非来源官方原图。','Drawn by FieldToFit from public data; not an official source chart.')}</p><p>{pick('源数据更新：','Source updated: ')}<span data-source-date>{date}</span> · {pick('本站核验 / 同步：','Reviewed / synced: ')}{source.checked_at}</p>{!source.source_updated_at&&<p>{pick('来源未标明本组数据的整体更新时间；模型发布日期不作为数据更新日期。','No overall update date is given for this selection; model release dates are not data update dates.')}</p>}</div>
    <details className="landscape-data"><summary>{pick('查看图中数值与出处','View plotted values and sources')}</summary><div className="watch-table-scroll" tabIndex={0}><table className="watch-table"><caption>{source.name} · {pick('已核对模型摘录','Selected verified models')}</caption><thead><tr><th scope="col">{pick('模型 / 配置','Model / configuration')}</th><th scope="col">{source.score_label}</th><th scope="col">{zh?source.price_label:source.price_label_en}</th><th scope="col">{pick('出处','Source')}</th></tr></thead><tbody>{points.map(p=><tr key={p.name}><th scope="row">{p.name}</th><td>{p.score}{p.score_low!==undefined?` (${p.score_low}–${p.score_high})`:''}</td><td>${p.price}</td><td><SourceLink url={p.score_url}>{pick('评分','Score')}</SourceLink> · <SourceLink url={p.price_url}>{pick('价格','Price')}</SourceLink></td></tr>)}</tbody></table></div></details>
    <dialog ref={dialog} className="landscape-dialog" onClose={()=>{setLarge(false);zoom.current?.focus();}}><div className="landscape-chart-heading"><h3>{source.name}</h3><button className="button" autoFocus onClick={()=>dialog.current?.close()}>{pick('关闭','Close')}</button></div>{large&&plot(false)}<p>{pick('源数据更新：','Source updated: ')}{date} · {pick('本站核验：','Checked: ')}{source.checked_at}</p></dialog>
  </>;
}
