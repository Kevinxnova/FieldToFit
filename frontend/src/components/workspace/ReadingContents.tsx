import { useEffect, useRef, useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { useWorkspace } from './UI';

export type ReadingAnchor = { id: string; title: string };
export function ReadingContents({ news, newsTotal, resources, resourceTotal, loading, filtered, groups }: {
  groups?: {id:string;title:string;items:ReadingAnchor[]}[]; news: ReadingAnchor[]; newsTotal: number | null; resources: ReadingAnchor[]; resourceTotal: number | null; loading: boolean; filtered: boolean;
}) {
  const { pick } = useWorkspace();
  const location = useLocation();
  const [active, setActive] = useState('model-landscape');
  const [open, setOpen] = useState(false);
  const [allNews, setAllNews] = useState(false);
  const [allResources, setAllResources] = useState(false);
  const mobileButton = useRef<HTMLButtonElement>(null);
  const ids = ['model-landscape', 'recent-news', 'news-overview', 'news-releases', ...news.map(n => n.id), 'resource-dossiers', ...(groups||[]).map(g=>g.id), ...resources.map(r => r.id)];
  const signature = ids.join('|');
  useEffect(() => {
    let frame = 0;
    const update = () => {
      cancelAnimationFrame(frame);
      frame = requestAnimationFrame(() => {
        let current = 'model-landscape';
        for (const id of signature.split('|')) {
          const node = document.getElementById(id);
          if (node && node.getBoundingClientRect().top <= 155) current = id;
        }
        setActive(current);
      });
    };
    update(); window.addEventListener('scroll', update, { passive: true });
    return () => { cancelAnimationFrame(frame); window.removeEventListener('scroll', update); };
  }, [signature]);
  useEffect(() => {
    let id: string;
    try { id = decodeURIComponent(location.hash.slice(1)); } catch { return; }
    if (!id || !signature.split('|').includes(id)) return;
    const frame = requestAnimationFrame(() => {
      const node = document.getElementById(id);
      if (!node) return;
      // Details may hide a shared target; expand before measuring and focusing.
      node.querySelectorAll('details[data-auto-expand]').forEach(d => { (d as HTMLDetailsElement).open = true; });
      node.focus({ preventScroll: true });
      node.scrollIntoView({ block: 'start', behavior: 'auto' });
      setActive(id);
    });
    return () => cancelAnimationFrame(frame);
  }, [location.hash, signature]);
  const link = (item: ReadingAnchor, main = false) => <Link
    key={item.id} className={main ? 'reading-toc-section' : ''}
    to={{ pathname: location.pathname, search: location.search, hash: '#' + item.id }}
    aria-current={active === item.id ? 'location' : undefined}
    onClick={() => {
      setOpen(false);
      if (location.hash === '#' + item.id) {
        const target = document.getElementById(item.id);
        target?.querySelectorAll('details[data-auto-expand]').forEach(d => { (d as HTMLDetailsElement).open = true; });
        target?.focus({ preventScroll: true }); target?.scrollIntoView({ block: 'start' });
      }
    }}>{item.title}</Link>;
  return <aside className={'reading-toc' + (open ? ' is-open' : '')}>
    <button ref={mobileButton} type="button" className="reading-toc-toggle" aria-expanded={open} aria-controls="reading-toc-links" onClick={() => setOpen(v => !v)}>{pick('本页目录', 'On this page')} <span>{open ? '−' : '+'}</span></button>
    <nav id="reading-toc-links" aria-label={pick('本页目录', 'On this page')} onKeyDown={e => { if (e.key === 'Escape') { setOpen(false); mobileButton.current?.focus(); } }}>
      <p className="reading-toc-label">{pick('本页内容', 'ON THIS PAGE')}</p>
      {link({ id: 'model-landscape', title: pick('模型能力与价格', 'Model capability & pricing') }, true)}
      {link({ id: 'recent-news', title: pick('近期动态', 'Recent developments') }, true)}
      {link({ id: 'news-overview', title: pick('本期速览', 'At a glance') })}
      {link({ id: 'news-releases', title: pick('发布与更新', 'Releases & updates') + ` · ${newsTotal ?? '—'}` })}
      <div className="reading-toc-items">{(allNews ? news : news.slice(0, 4)).map(n => link(n))}</div>
      {news.length > 4 && <button type="button" className="text-button" aria-expanded={allNews} onClick={() => setAllNews(v => !v)}>{pick(allNews ? '收起动态目录' : '展开其他动态', allNews ? 'Fewer entries' : 'All developments')}</button>}
      {link({ id: 'resource-dossiers', title: pick('持续关注', 'Ongoing watch') + ` · ${loading ? '…' : resourceTotal ?? '—'}` }, true)}
      {groups ? <>{loading&&<p role="status">{pick('正在读取目录…','Loading…')}</p>}{filtered&&<p className="muted">{pick('当前筛选结果','Filtered results')}</p>}{groups.map(g=><div className="watch-toc-group" key={g.id}>{link(g)}<details><summary>{pick('查看对象','Show profiles')}</summary><div className="reading-toc-items">{g.items.map(i=>link(i))}</div></details></div>)}{!loading&&resourceTotal===0&&<p>{pick('没有匹配资料','No matching profiles')}</p>}</> : <><div className="reading-toc-items">{(allResources ? resources : resources.slice(0,6)).map(r=>link(r))}</div>{resources.length>6&&<button className="text-button" onClick={()=>setAllResources(v=>!v)}>{pick('展开 / 收起','Expand / collapse')}</button>}</>}

    </nav>
  </aside>;
}
