import { useId, useRef, useState } from 'react';
import { Link } from '@fieldtofit/locale/router';
import { useLanguage } from '../../locale/language';
import { contentPath } from '../../search';
import { SourceLink, useWorkspace } from './UI';
import type { NewsItem } from './NewsReading';
import { useHotCardMotion } from './useHotCardMotion';
import './hot-cards.css';

type Point = {title:string;detail:string};
export type HotCard = {
  headline:string;scope:string;changes:Point[];audiences:Point[];limits:Point[];next_step:string;
  evidence:{source_id:string;locator:string}[];verification:string;
  revised_at:string;checked_at:string;featured_rank:number;status:'current'|'needs_update';update_note:string;revision:string;
  share?:{content_revision:string;zh:{url:string;sha256:string};en:{url:string;sha256:string}};
};

function HotCardPreview({ item }: { item: NewsItem }) {
  const { pick } = useWorkspace();
  const motion = useHotCardMotion();
  const disclosureId = useId();
  const [hovered, setHovered] = useState(false);
  const [keyboardActive, setKeyboardActive] = useState(false);
  const [pinned, setPinned] = useState(false);
  const [dismissed, setDismissed] = useState(false);
  const expanded = !dismissed && (hovered || keyboardActive || pinned);
  const card = item.hot_card!;
  const path = contentPath(item.id) + '#hot-information-card';
  const readingReturn = { url: '/for-you#hot-information-cards', id: 'hot-information-cards' };
  const source = item.sources.find(entry => entry.id === card.evidence[0]?.source_id);
  return <article className="hot-card-preview" ref={motion}
    onPointerEnter={event => { if (event.pointerType === 'mouse') { setHovered(true); setDismissed(false); } }}
    onPointerLeave={() => { setHovered(false); setDismissed(false); }}
    onPointerDown={() => setKeyboardActive(false)}
    onFocusCapture={event => { if (event.target.matches(':focus-visible')) { setKeyboardActive(true); setDismissed(false); } }}
    onBlurCapture={event => { if (!event.currentTarget.contains(event.relatedTarget)) { setKeyboardActive(false); setDismissed(false); } }}
    onKeyDown={event => { if (event.key === 'Escape' && expanded) { setPinned(false); setDismissed(true); event.preventDefault(); } }}>
    <div className="hot-card-foil"><div className="hot-card-face">
      <div className="hot-card-collection"><strong>FieldToFit</strong><span>{item.id} · {pick('热点信息卡', 'INFORMATION CARD')}</span></div>
      <p className="hot-card-kicker"><strong>{item.name}</strong><span>{item.event_date || item.source_published_at || pick('日期待核实', 'Date unconfirmed')}</span></p>
      <div className="hot-card-art">
        <svg viewBox="0 0 64 64" fill="none" stroke="currentColor" strokeWidth="1.3" aria-hidden="true">
          <rect x="10" y="13" width="32" height="40" rx="5" transform="rotate(-12 26 33)"/>
          <rect x="22" y="17" width="32" height="40" rx="5"/>
          <path d="M29 32h18M29 39h18M29 46h10M47 4v12M41 10h12"/>
        </svg>
        <div><span>{pick('关键变化', 'Key change')}</span><strong>{card.changes[0].title}</strong></div>
      </div>
      <h4><Link to={path} state={{ readingReturn }}>{card.headline}</Link></h4>
      <p className="hot-card-scope-preview">{card.scope}</p>
      <button type="button" className="hot-card-disclosure" aria-expanded={expanded} aria-controls={disclosureId}
        onClick={() => { setPinned(!expanded); setDismissed(expanded); }}>
        {expanded ? pick('收起人群与条件', 'Hide audience and conditions') : pick('展开人群与条件', 'Show audience and conditions')}
        <span aria-hidden="true">{expanded ? '−' : '+'}</span>
      </button>
      <div className="hot-card-extra" id={disclosureId} hidden={!expanded}>
        <div className="hot-card-audience"><strong>{pick('对谁有用 · 本站判断', 'Who benefits · Our assessment')}</strong><ul>{card.audiences.map((point, i) => <li key={i}>{point.title}</li>)}</ul></div>
        <p className="hot-card-limit"><strong>{pick('先看条件', 'Check first')}</strong>{card.limits[0].detail}</p>
      </div>
      {card.status === 'needs_update' && <p className="hot-card-preview-maintenance" role="status">{pick('待更新：', 'Update pending: ')}{card.update_note}</p>}
      <div className="hot-card-preview-footer">
        {source && <SourceLink className="hot-card-source" url={source.url}>{pick('官方证据', 'Official evidence')} ↗</SourceLink>}
        <Link className="hot-card-read" to={path} state={{ readingReturn }}>{pick('读完整信息卡', 'Read the full card')} ↗</Link>
      </div>
    </div></div>
  </article>;
}

export function HotCardHighlights({items,preview=false}:{items:NewsItem[];preview?:boolean}) {
  const {pick}=useWorkspace();
  const cards=items.filter(i=>i.hot_card&&i.hot_card.featured_rank>0).sort((a,b)=>a.hot_card!.featured_rank-b.hot_card!.featured_rank).slice(0,3);
  return <section className="hot-card-section" aria-labelledby="hot-information-cards">
    <div className="platform-section-heading"><h3 id="hot-information-cards" tabIndex={-1}>{pick('热点信息卡','Information cards')}</h3><span>{pick('编辑精选','Editorial selection')}</span></div>
    <p className="hot-card-subtitle">{pick('这次更新，对谁有用？','Who benefits from this update?')}</p>
    <div className="hot-card-grid">{cards.map(item => <HotCardPreview key={item.id} item={item}/>)}</div>
    {!cards.length&&<p className="muted">{pick('暂无已审信息卡，完成审核后会在这里展示。','Reviewed information cards will appear here when available.')}</p>}
    {!preview&&<Link className="hot-card-all" to="/for-you?news_cards=1&news_range=all#news-releases">{pick('查看全部信息卡','View all information cards')} →</Link>}
  </section>;
}

export function HotCardReading({item,preview=false}:{item:NewsItem;preview?:boolean}) {
  const {pick,notify}=useWorkspace(),language=useLanguage();
  const card=item.hot_card!;const share=card.status==='current'?card.share?.[language]:undefined;
  const dialog=useRef<HTMLDialogElement>(null),trigger=useRef<HTMLButtonElement>(null);
  const [broken,setBroken]=useState(false),[busy,setBusy]=useState(false);
  const copy=async()=>{const url=new URL(contentPath(item.id)+'#hot-information-card',location.origin).href;try{await navigator.clipboard.writeText(url);notify(pick('信息卡链接已复制','Card link copied'));}catch{notify(url);}};
  const download=async()=>{if(!share)return;setBusy(true);try{const response=await fetch(share.url);if(!response.ok)throw new Error();const blob=await response.blob();const hash=Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',await blob.arrayBuffer()))).map(b=>b.toString(16).padStart(2,'0')).join('');if(hash!==share.sha256)throw new Error();const url=URL.createObjectURL(blob);const a=document.createElement('a');a.href=url;a.download=`FieldToFit-${item.id}-${card.revised_at}-${language}.png`;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);}catch{notify(pick('图片暂不可用，请稍后重试；正文仍可阅读。','Image unavailable. Please retry later; the text remains readable.'));}finally{setBusy(false);}};
  const points=(rows:Point[])=>rows.map((point,i)=><li key={i}><strong>{point.title}</strong><p>{point.detail}</p></li>);
  return <section className="hot-card-reading" id="hot-information-card" tabIndex={-1} aria-label={pick('热点信息卡','Information card')}>
    <div className="hot-card-sheet">
      <p className="hot-card-brand">FieldToFit <span>{pick('热点信息卡','INFORMATION CARD')}</span></p>
      <header><p className="hot-card-kicker">{item.name} · {pick('事件日期 ','Event date ')}{item.event_date||item.source_published_at||pick('待核实','Unconfirmed')}</p><h2>{card.headline}</h2><p className="hot-card-scope">{card.scope}</p></header>
      {card.status==='needs_update'&&<p className="hot-card-maintenance" role="status">{pick('信息待更新，暂停分享图下载：','Update pending; image downloads paused: ')}{card.update_note}</p>}
      <section><h3>{pick('发生了什么变化','What changed')}</h3><ol className="hot-card-changes">{points(card.changes)}</ol></section>
      <section><h3>{pick('对谁有用','Who benefits')} <small>{pick('本站判断','FieldToFit assessment')}</small></h3><ul className="hot-card-scenarios">{points(card.audiences)}</ul></section>
      <section className="hot-card-conditions"><h3>{pick('采用前，先看这些条件','Conditions to check first')}</h3><ul>{points(card.limits)}</ul></section>
      <section className="hot-card-next"><h3>{pick('接下来可以做什么','A useful next step')} <small>{pick('本站建议','FieldToFit suggestion')}</small></h3><p>{card.next_step}</p></section>
      <footer><h3>{pick('官方证据','Official evidence')}</h3><ul>{card.evidence.map((entry,i)=>{const source=item.sources.find(s=>s.id===entry.source_id);return source&&<li key={i}><SourceLink url={source.url}>{source.title}</SourceLink><p>{entry.locator}</p></li>;})}</ul><p>{pick('卡片修订 ','Card revised ')}{card.revised_at} · {pick('来源核对 ','Source checked ')}{card.checked_at}</p><p>{card.verification}</p></footer>
    </div>
    <div className="hot-card-actions">
      {share&&<><button className="button" ref={trigger} onClick={()=>{setBroken(false);dialog.current?.showModal();}}>{pick('查看分享图','View share image')}</button><button className="button" disabled={busy} onClick={download}>{busy?pick('正在保存…','Saving…'):pick('保存分享图','Save share image')}</button></>}
      {!preview&&<button className="text-button" onClick={copy}>{pick('复制链接','Copy link')}</button>}
    </div>
    {share&&<><p className="hot-card-help">{pick('微信内可打开图片后长按保存；已转发图片不会自动更新，最新说明见二维码对应详情。','In WeChat, open the image and press and hold to save. Shared images do not update automatically; the QR code leads to maintained details.')}</p><dialog ref={dialog} className="hot-card-dialog" aria-label={pick('信息卡分享图','Share image')} onClose={()=>trigger.current?.focus()}><button className="button" autoFocus onClick={()=>dialog.current?.close()}>{pick('关闭图片','Close image')}</button>{broken?<p role="status">{pick('分享图暂不可用，正文仍可阅读。','Share image unavailable; the text remains readable.')}</p>:<img src={share.url} alt={card.headline} onError={()=>setBroken(true)}/>}</dialog></>}
  </section>;
}
