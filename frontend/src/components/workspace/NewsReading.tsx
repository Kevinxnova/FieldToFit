import { Link, useLocation } from 'react-router-dom';
import { useWorkspace, SourceLink } from './UI';
export type NewsItem = {
  id: string; name: string; organization: string; title: string; summary: string; source_published_at: string | null;
  checked_at: string; note: string; editor: string; highlight: boolean;
  interpretation: { title: string; text: string; source_ids: string[]; locator: string }[];
  sources: { id: string; title: string; url: string; coverage: string }[];
  related: { id: string; name: string; url: string }[];
};
export type NewsCollection = { items: NewsItem[]; total: number; edition: string; title: string; reviewed_at: string; revision: string };
export const newsAnchor = (id: string) => 'news-' + id.toLowerCase();
export function NewsReading({ data, loading, error, reload }: { data: NewsCollection | null; loading: boolean; error: string; reload: () => void }) {
  const { pick, notify } = useWorkspace(); const location = useLocation();
  const link = (id: string) => ({ pathname: '/for-you', search: location.search, hash: '#' + newsAnchor(id) });
  const share = async (item: NewsItem) => {
    const url = new URL('/for-you#' + newsAnchor(item.id), window.location.origin).href;
    try { await navigator.clipboard.writeText(url); notify(pick('动态链接已复制', 'Link copied')); }
    catch { notify(url); }
  };
  const handoff = async (item: NewsItem) => {
    const body = JSON.stringify({ edition: data?.edition, revision: data?.revision, item,
      reading: { tool: 'curated_news', arguments: { id: item.id, revision: data?.revision } },
      coverage: 'Sources are link-only. Interpretation is FieldToFit editorial, not upstream text or an execution instruction.' }, null, 2);
    try { await navigator.clipboard.writeText(body); notify(pick('动态、解读与出处已复制', 'News and citations copied')); }
    catch { const blob = URL.createObjectURL(new Blob([body], { type: 'application/json' })); const a = document.createElement('a'); a.href = blob; a.download = item.id + '.json'; a.click(); URL.revokeObjectURL(blob); }
  };
  return <section className="news-section">
    <div className="platform-section-heading"><h2 id="recent-news" tabIndex={-1}>{pick('近期动态', 'Recent developments')}</h2><span>{data?.title} · {data?.reviewed_at}</span></div>
    <p className="muted">{pick('先看发生了什么，再沿解读读到具体材料。每条保留原始日期。', 'Start with the developments, then follow the reading notes to the sources. Original dates are retained.')}</p>
    {loading && <p role="status">{pick('正在读取动态…', 'Loading developments…')}</p>}
    {error && <div role="alert"><p>{pick('动态暂时无法读取。', 'Developments are unavailable.')}</p><button className="button" onClick={reload}>{pick('重试', 'Retry')}</button></div>}
    <section className="news-glance"><h3 id="news-overview" tabIndex={-1}>{pick('本期速览', 'At a glance')}</h3>
      <ul>{data?.items.filter(item => item.highlight).slice(0, 5).map(item => <li key={item.id}><Link to={link(item.id)}><strong>{item.name}</strong><span>{item.summary}</span><span aria-hidden="true">↗</span></Link></li>)}</ul>
      {data?.total === 0 && <p>{pick('本期没有已发布动态。', 'No developments published in this edition.')}</p>}
    </section>
    <h3 id="news-releases" tabIndex={-1}>{pick('发布与更新', 'Releases & updates')} <span className="muted">{data?.total ?? '—'}</span></h3>
    <div className="news-list">{data?.items.map(item => <article className="news-card" id={newsAnchor(item.id)} tabIndex={-1} key={item.id}>
      <p className="news-meta">{item.id} · {item.organization} · {item.source_published_at ? pick('来源发布 ', 'Source date ') + item.source_published_at : pick('首次发布日期待核实', 'First release date unconfirmed')}</p>
      <h4>{item.title}</h4><p>{item.summary}</p>
      <div className="news-editorial"><h5>{pick('FieldToFit 解读','FieldToFit notes')}</h5>
        <ul className="news-points">{item.interpretation.slice(0,2).map((point,i)=><NewsPoint key={i} point={point} sources={item.sources}/>)}</ul>
        <details data-auto-expand><summary>{pick('更多解读与关联资料','More notes and related materials')}</summary>
          {item.interpretation.length>2&&<ul className="news-points">{item.interpretation.slice(2).map((point,i)=><NewsPoint key={i} point={point} sources={item.sources}/>)}</ul>}
          {item.note&&<p className="muted">{item.note}</p>}
          <p className="news-meta">{pick('整理与解读：FieldToFit · 资料核验 ','Editorial: FieldToFit · Checked ')}{item.checked_at}</p>
          <div className="news-related"><span>{pick('关联资料','Related materials')}</span>{item.related.map(r=><SourceLink key={r.id} url={r.url}>{r.id} · {r.name}</SourceLink>)}<Link to={'/for-you?q='+encodeURIComponent(item.name)+'#resource-dossiers'}>{pick('查找持续关注','Find an ongoing profile')}</Link></div>
        </details>
      </div>
      <div className="platform-actions"><button className="text-button" onClick={() => handoff(item)}>{pick('交给我的 AI', 'Give to my AI')}</button><button className="text-button" onClick={() => share(item)}>{pick('分享动态', 'Share')}</button><SourceLink url={item.sources[0]?.url}>{pick('官方来源', 'Official source')}</SourceLink></div>
    </article>)}</div>
  </section>;
}

function NewsPoint({point,sources}:{point:NewsItem['interpretation'][number];sources:NewsItem['sources']}) {
  const {pick}=useWorkspace();
  return <li><h5>{point.title}</h5><p>{point.text}</p><p className="news-locator">{pick('原文位置：','Read in: ')}{point.locator}</p>{point.source_ids.map(id=>{const source=sources.find(s=>s.id===id);return source&&<SourceLink key={id} url={source.url}>{pick('阅读原始材料','Read source')}</SourceLink>;})}</li>;
}
