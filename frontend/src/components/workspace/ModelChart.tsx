import { useMemo } from 'react';
import { useWorkspace } from './UI';
import { placeLabels } from './chartLabels';

export type ChartPoint = {id:string;name:string;organization:string;score:number;price:number;score_low?:number;score_high?:number;estimated?:boolean};
export type PlotSource = {name:string;score_label:string;price_label:string;price_label_en:string;source_updated_at:string|null;checked_at:string;points:ChartPoint[]};
export const companyColors:Record<string,string> = {OpenAI:'#242b35',Anthropic:'#a4542a',Google:'#238340',xAI:'#8051ad',Meta:'#157ab9',Kimi:'#168f9d',GLM:'#9b445f',Qwen:'#bd6714',MIMO:'#907900',MiniMax:'#d33981',DeepSeek:'#3456d1','其他':'#69757a'};
const fmt=(n:number)=>n.toLocaleString('en-US',{maximumFractionDigits:4});

// One original plot for the homepage and the interactive full chart. Filters keep the source domain.
export function ModelChart({source,points=source.points,width=1400,height=1200,expanded=false,scale=1,selected=null,onSelect}:{source:PlotSource;points?:ChartPoint[];width?:number;height?:number;expanded?:boolean;scale?:number;selected?:string|null;onSelect?:(id:string)=>void}) {
  const {pick,zh}=useWorkspace();
  const left=78,right=width-90,top=86,bottom=height-120;
  // Keep domains fixed when filtering so a model never appears to gain capability or lose cost.
  const low=Math.floor(Math.min(...source.points.map(p=>p.score_low??p.score))/5)*5-5;
  const high=Math.ceil(Math.max(...source.points.map(p=>p.score_high??p.score))/5)*5+5;
  const priceMin=10**Math.floor(Math.log10(Math.min(...source.points.map(p=>p.price))));
  const priceMax=10**Math.ceil(Math.log10(Math.max(...source.points.map(p=>p.price))));
  const x=(n:number)=>left+(Math.log10(n)-Math.log10(priceMin))/(Math.log10(priceMax)-Math.log10(priceMin))*(right-left);
  const y=(n:number)=>bottom-(n-low)/(high-low)*(bottom-top);
  const labels=useMemo(()=>placeLabels(points.map(p=>({id:p.id,name:p.name,x:x(p.price),y:y(p.score)})),width,height-40),[points,source.points,width,height]);
  const byId=new Map(labels.map(p=>[p.id,p]));
  const ticks:number[]=[];for(let decade=priceMin;decade<=priceMax*1.001;decade*=10)for(const m of [1,2,5])if(decade*m<=priceMax*1.001)ticks.push(decade*m);
  const date=source.source_updated_at||pick('来源未标注','Not provided by source');
  return <svg viewBox={`0 0 ${width} ${height}`} style={{width:expanded?`${scale*100}%`:'100%',height:expanded?`${scale*100}%`:undefined}} role={onSelect?"group":"img"} aria-label={source.name+pick(' 能力与价格散点图',' capability and price scatterplot')}>
    <title>{source.name} · 2026 · {source.score_label}</title><desc>{pick('横轴是对数价格，纵轴是评分。保留全部来源模型名称，同公司同色；完整栏目可筛选并查看依据。','Logarithmic price on x, score on y. All original model names are retained and colored by company; the complete section provides filters and evidence.')}</desc>
    <text x={left} y={34} className="chart-axis-title">{source.score_label} ↑</text>
    {Array.from({length:9},(_,i)=>low+(high-low)*i/8).map(v=><g key={v}><line className="chart-grid" x1={left} x2={right} y1={y(v)} y2={y(v)}/><text className="chart-tick" x={left-12} y={y(v)+5} textAnchor="end">{Number(v.toFixed(1))}</text></g>)}
    {ticks.map(v=><g key={v}><line className="chart-grid" x1={x(v)} x2={x(v)} y1={top} y2={bottom}/><text className="chart-tick" x={x(v)} y={bottom+28} textAnchor="middle">${fmt(v)}</text></g>)}
    {points.map(p=>{const l=byId.get(p.id)!;return <line key={p.id} className="chart-leader" x1={l.x} y1={l.y} x2={Math.max(l.lx,Math.min(l.lx+l.width,l.x))} y2={l.ly+8} stroke={companyColors[p.organization]}/>;})}
    {points.map(p=>{const l=byId.get(p.id)!;const color=companyColors[p.organization];return <g key={p.id} data-model-id={p.id} data-company={p.organization} className={'chart-point'+(selected===p.id?' selected':'')} role={onSelect?'button':undefined} tabIndex={onSelect?0:undefined} aria-label={`${p.name}; ${source.score_label}: ${fmt(p.score)}; ${source.price_label_en}: ${fmt(p.price)}`} onClick={onSelect?()=>onSelect(p.id):undefined} onKeyDown={onSelect?e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();onSelect(p.id);}}:undefined}>
      <title>{p.name}: {fmt(p.score)} · ${fmt(p.price)}</title>
      {p.score_low!==undefined&&p.score_high!==undefined&&<line className="chart-interval" x1={l.x} x2={l.x} y1={y(p.score_low)} y2={y(p.score_high)} stroke={color}/>}
      <circle cx={l.x} cy={l.y} r={selected===p.id?8:6} fill={p.estimated?'white':color} stroke={color}/><text x={l.lx} y={l.ly+13} className="chart-model-name" fill={color}>{p.name}</text>
    </g>;})}
    <text className="chart-axis-title" x={(left+right)/2} y={height-60} textAnchor="middle">{zh?source.price_label:source.price_label_en} · {pick('对数刻度','log scale')} →</text>
    <text className="chart-credit" x={left} y={height-20}>Source: {source.name} · {pick('源日期','Source date')}: {date} · FieldToFit {source.checked_at}</text>
  </svg>;
}
