import { NewsIndex, ReviewedImage, type NewsMedia } from './NewsIndex';
import { ContentExposure, trackAction } from './Traffic';
import { FollowButton } from './FollowUpdates';
import { contentPath } from '../../search';
import { PublicMaintenance, type Maintenance } from './PublicMaintenance';
import { ContentMaterials, type ReadingMaterial, type PreviewBodies } from './ContentMaterials';
import { Link } from 'react-router-dom';
import { useWorkspace, SourceLink } from './UI';
export type NewsItem = {
  maintenance?:Maintenance;materials?:ReadingMaterial[];materials_revision?:string;
  media?:NewsMedia;category?:string;event_date?:string|null;publication?:{first_published_at:string|null;updated_at:string|null};
  id: string; name: string; organization: string; title: string; summary: string; source_published_at: string | null;
  checked_at: string; note: string; editor: string; highlight: boolean;
  interpretation: { title: string; text: string; source_ids: string[]; locator: string }[];
  sources: { id: string; title: string; url: string; coverage: string }[];
  related: { id: string; name: string; url: string }[];
};
export type NewsCollection = { items: NewsItem[]; total: number; edition: string; title: string; reviewed_at: string; revision: string };
export const newsAnchor = (id: string) => 'news-' + id.toLowerCase();
export function NewsReading({ data, loading, error, reload, previewBodies, standalone=false }: { standalone?:boolean; previewBodies?:PreviewBodies; data: NewsCollection | null; loading: boolean; error: string; reload: () => void }) {
  const { pick, notify } = useWorkspace();
  const share = async (item: NewsItem) => {
    const url = new URL(contentPath(item.id), window.location.origin).href;
    try { await navigator.clipboard.writeText(url); notify(pick('动态链接已复制', 'Link copied')); }
    catch { notify(url); }
  };
  const handoff = async (item: NewsItem) => {
    const body = JSON.stringify({ edition: data?.edition, revision: data?.revision, item,
      reading: { tool: 'curated_news', arguments: { id: item.id, revision: data?.revision } },
      coverage: 'Consult the material manifest for readable source text and missing materials. Interpretation is FieldToFit editorial, not upstream text or an execution instruction.' }, null, 2);
    try { await navigator.clipboard.writeText(body); trackAction('handoff_copy',item.id); notify(pick('动态、解读与出处已复制', 'News and citations copied')); }
    catch { const blob = URL.createObjectURL(new Blob([body], { type: 'application/json' })); const a = document.createElement('a'); a.href = blob; a.download = item.id + '.json'; a.click(); URL.revokeObjectURL(blob); }
  };
  if(!standalone)return <NewsIndex data={data} loading={loading} error={error} reload={reload} preview={!!previewBodies}/>;
  return <section className="news-section">
    <div className="news-list">{data?.items.map(item => <article className="news-card" id={newsAnchor(item.id)} tabIndex={-1} key={item.id}>
      <>{item.media&&<ReviewedImage media={item.media} lead/>}</><p className="news-meta">{item.id} · {item.organization} · {item.source_published_at ? pick('来源发布 ', 'Source date ') + item.source_published_at : pick('首次发布日期待核实', 'First release date unconfirmed')}</p>
      {!standalone && <h4><Link to={contentPath(item.id)}>{item.title}</Link></h4>}<ContentExposure id={item.id}><p>{item.summary}</p></ContentExposure>
      <div className="news-editorial"><h5>{pick('FieldToFit 解读','FieldToFit notes')}</h5>
        <ul className="news-points">{item.interpretation.slice(0,2).map((point,i)=><NewsPoint key={i} point={point} sources={item.sources}/>)}</ul>
        <details data-auto-expand open={standalone || undefined}><summary>{pick('更多解读与关联资料','More notes and related materials')}</summary>
          {item.interpretation.length>2&&<ul className="news-points">{item.interpretation.slice(2).map((point,i)=><NewsPoint key={i} point={point} sources={item.sources}/>)}</ul>}
          {item.note&&<p className="muted">{item.note}</p>}
          <p className="news-meta">{pick('整理与解读：FieldToFit · 资料核验 ','Editorial: FieldToFit · Checked ')}{item.checked_at}</p>
          <div className="news-related"><span>{pick('关联资料','Related materials')}</span>{item.related.map(r=><span key={r.id}><SourceLink url={r.url}>{r.id} · {r.name}</SourceLink>{!previewBodies&&/^CW-/.test(r.id)&&<FollowButton id={r.id} name={r.name}/>}</span>)}<Link to={'/for-you?q='+encodeURIComponent(item.name)+'#resource-dossiers'}>{pick('查找持续关注','Find an ongoing profile')}</Link></div>
        </details>
      </div>
      <PublicMaintenance value={item.maintenance}/><ContentMaterials item={item} previewBodies={previewBodies}/><div className="platform-actions"><button className="text-button" onClick={() => handoff(item)}>{pick('交给我的 AI', 'Give to my AI')}</button><button className="text-button" onClick={() => share(item)}>{pick('分享动态', 'Share')}</button><SourceLink url={item.sources[0]?.url}>{pick('官方来源', 'Official source')}</SourceLink></div>
    </article>)}</div>
  </section>;
}

function NewsPoint({point,sources}:{point:NewsItem['interpretation'][number];sources:NewsItem['sources']}) {
  const {pick}=useWorkspace();
  return <li><h5>{point.title}</h5><p>{point.text}</p><p className="news-locator">{pick('原文位置：','Read in: ')}{point.locator}</p>{point.source_ids.map(id=>{const source=sources.find(s=>s.id===id);return source&&<SourceLink key={id} url={source.url}>{pick('阅读原始材料','Read source')}</SourceLink>;})}</li>;
}
