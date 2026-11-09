import {useState} from 'react';
import {SourceLink,useWorkspace} from './UI';
import './source-reading.css';
export type SourceBlock={id:string;kind:'quote'|'figure';source_id:string;locator:string;author:string;checked_at:string;quote:string;translation_zh:string;original_language?:'en'|'zh';reuse_basis?:string;original_url?:string;display?:'link'|'embedded';image_url?:string;rights_url?:string;alt?:string};
export type OriginalReading={schema_version:'fieldtofit.source-reading.v1';blocks:SourceBlock[]};
type Source={id:string;title:string;url:string};
function OriginalFigure({block}:{block:SourceBlock}){
 const {pick}=useWorkspace();const [failed,setFailed]=useState(false);
 return <figure className="source-original-figure">{block.display==='embedded'&&!failed&&<a href={block.image_url} target="_blank" rel="noopener noreferrer"><img src={block.image_url} alt={block.alt} loading="lazy" onError={()=>setFailed(true)}/></a>}<figcaption><p>{pick(block.translation_zh,block.quote)}</p>{block.display==='embedded'&&<p>{block.author} · {block.reuse_basis} {block.rights_url&&<SourceLink url={block.rights_url}>{pick('复用依据','Reuse basis')}</SourceLink>}</p>}<SourceLink url={block.original_url}>{pick('查看来源原图','View original figure')}</SourceLink>{failed&&<p role="status">{pick('图片暂时无法显示，可打开来源原图。','The image could not load. Open the original figure.')}</p>}<details><summary>{pick('原始图注','Original caption')}</summary><p>{block.quote}</p></details></figcaption></figure>;
}
export function SourceReading({value,sources}:{value:OriginalReading;sources:Source[]}){
 const {pick}=useWorkspace();
 return <section className="source-reading" aria-label={pick('原文摘录','Source excerpts')}><h2>{pick('原文摘录','Source excerpts')}</h2>{value.blocks.map(b=>{const source=sources.find(s=>s.id===b.source_id);const translated=b.kind==='quote'&&b.original_language==='en';return <section key={b.id} className="source-reading-block" data-source-block={b.id}><p className="source-byline">{b.author} · {b.locator}</p>{b.kind==='figure'?<OriginalFigure block={b}/>:<><p className="source-label">{translated?pick('中文译文 · 原文摘录','Original excerpt · English'):pick('原文摘录 · 中文','Original excerpt · Chinese')}</p><blockquote>{translated?pick(b.translation_zh,b.quote):b.quote}</blockquote>{translated&&<details><summary>{pick('查看英文原文','Chinese translation')}</summary><blockquote lang={pick('en','zh')}>{pick(b.quote,b.translation_zh)}</blockquote></details>}</>}<p className="source-citation">{source&&<SourceLink url={source.url}>{pick('阅读原文','Read source')} · {source.title}</SourceLink>}<span>{pick('核对：','Checked: ')}{b.checked_at}</span></p></section>;})}</section>;
}
