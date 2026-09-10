import { useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { useRemote } from '../../api/knowledge';
import { dateText, SourceLink, useWorkspace } from './UI';

export type EditionEntry = { object_id: string; revision: number; status: string; name?: string; summary?: string; significance?: string; quote?: string; source_url?: string };
export type Edition = { id: string; revision: number; title: string; period_start: string; period_end: string; published_at: string; entries: EditionEntry[]; needs_review: boolean; unavailable?: boolean; is_latest_revision: boolean };
type Page = { next_cursor: string | null; total: number; has_more: boolean };

export function EditionOverview() {
  const { pick, zh } = useWorkspace();
  const [params, setParams] = useSearchParams();
  const [cursor, setCursor] = useState('');
  const archive = useRemote<Page & {items: Edition[]}>('/v1/platform/editions?limit=5' + (cursor ? '&cursor=' + encodeURIComponent(cursor) : ''));
  const id = params.get('edition');
  const revision = params.get('edition_revision');
  const selected = useRemote<Edition>(id ? `/v1/platform/editions/${encodeURIComponent(id)}` + (revision ? '?revision=' + encodeURIComponent(revision) : '') : null);
  // The current overview stays fixed while the archive is paged.
  const latest = useRemote<Page & {items: Edition[]}>('/v1/platform/editions?limit=1');
  const current = id ? selected : latest;
  const edition = id ? selected.data : latest.data?.items[0];
  const open = (entry?: Edition) => setParams(p => {
    if (entry) { p.set('edition', entry.id); p.set('edition_revision', String(entry.revision)); }
    else { p.delete('edition'); p.delete('edition_revision'); }
    return p;
  });
  return <section className="platform-overview" aria-label={pick('概览期次', 'Overview editions')}>
    <div className="platform-section-heading"><h2>{pick(id ? '概览详情' : '本期概览', id ? 'Edition details' : 'Latest edition')}</h2>{id && <button className="text-button" onClick={() => open()}>{pick('返回本期', 'Latest edition')}</button>}</div>
    <p className="muted">{pick('有经过复核的重点才发布新一期。每日检查不改变原期次日期。', 'A new edition needs reviewed highlights. Daily checks never change its publication date.')}</p>
    {current.loading && <p role="status">{pick('正在读取概览…', 'Loading edition…')}</p>}
    {current.error && <div role="alert"><p>{current.error}</p><button className="button" onClick={current.reload}>{pick('重试读取概览', 'Retry edition')}</button></div>}
    {!current.loading && !current.error && !edition && <p>{pick('尚未发布概览。可以先浏览下方已审核资料。', 'No edition published yet. Browse the reviewed materials below.')}</p>}
    {edition && (edition.unavailable ? <p>{pick('这期概览已撤回。', 'This edition has been withdrawn.')}</p> : <>
      <h3>{edition.title}</h3><p className="muted">{edition.period_start} — {edition.period_end} · {pick('发布于', 'Published')} {dateText(edition.published_at, zh)} · {pick('修订', 'Revision')} {edition.revision}</p>
      {(id || !edition.is_latest_revision) && <p>{pick('正在查看固定期次修订；下方资料流仍是当前精选。', 'Viewing a fixed edition revision; the feed below still shows current selections.')}</p>}
      {edition.needs_review && <p className="platform-notice">{pick('部分引用资料已有变化或不可用，已逐条标记。', 'Some referenced materials changed or became unavailable; see each entry.')}</p>}
      <ol>{edition.entries.map((entry, index) => <li key={entry.object_id}><span>0{index+1}</span><div>
        {entry.status === 'unavailable' ? <p>{pick('该条引用已不可用，内容停止展示。', 'This reference is no longer available; its content is hidden.')}</p> : <>
          <Link to={`/for-you?object=${entry.object_id}&revision=${entry.revision}`}>{entry.name}</Link><p>{entry.summary}</p><p className="muted">{entry.significance}</p>
          {entry.status !== 'current' && <p className="platform-notice">{pick('所引用版本已变化，待编辑复核。', 'The referenced selection changed and needs editorial review.')}</p>}
          <SourceLink url={entry.source_url}>{pick('查看原始依据', 'Original source')}</SourceLink><details><summary>{pick('查看引用原句', 'Source quotation')}</summary><blockquote>{entry.quote}</blockquote></details>
        </>}
      </div></li>)}</ol>
      <button className="text-button" onClick={() => open(edition)}>{pick('固定此期分享链接', 'Link to this revision')}</button>
    </>)}
    <details className="platform-archive"><summary>{pick('浏览往期概览', 'Browse edition archive')}</summary>
      {archive.loading && <p role="status">{pick('正在读取历史…', 'Loading archive…')}</p>}
      {archive.error && <p role="alert">{archive.error}</p>}
      <ul>{archive.data?.items.map(item => <li key={item.id}>{item.unavailable ? pick('已撤回期次', 'Withdrawn edition') : <button className="text-button" onClick={() => open(item)}>{item.period_start} — {item.period_end} · {item.title} · {pick('修订', 'Revision')} {item.revision}</button>}</li>)}</ul>
      {archive.data?.total === 0 && <p>{pick('没有已发布期次。', 'No published editions.')}</p>}
      <div className="platform-actions"><button className="button" disabled={!archive.data?.next_cursor || archive.loading} onClick={() => setCursor(archive.data!.next_cursor!)}>{pick('更早期次', 'Older editions')}</button><button className="text-button" onClick={() => {setCursor(''); archive.reload(); latest.reload();}}>{pick('重新查看最新期次', 'Reload latest editions')}</button></div>
    </details>
  </section>;
}

type ChangeEvent = { id: number; object_id: string; kind: string; name?: string; from_revision: number | null; to_revision: number | null; published_at: string; availability: string; changed_fields: string[] };
type ChangePage = Page & {items: ChangeEvent[]; resume_cursor: string; expires_at: string; until: number};

export function ChangeReader({ objectId }: { objectId: string }) {
  const { pick, zh, notify } = useWorkspace();
  const [cursor, setCursor] = useState('');
  const query = new URLSearchParams({limit:'5'});
  if (objectId) query.set('object_id', objectId);
  if (cursor) query.set('cursor', cursor);
  const result = useRemote<ChangePage>('/v1/platform/changes?' + query);
  const names: Record<string, string> = {added:pick('首次精选','Added'), updated:pick('资料修订','Updated'), needs_review:pick('资料变化，待复核','Needs review'), withdrawn:pick('撤回精选','Withdrawn')};
  const checkpoint = result.data ? JSON.stringify({tool:'curated_changes', arguments:{limit:5, object_ids:objectId ? [objectId] : [], cursor:result.data.resume_cursor}}, null, 2) : '';
  return <section className="platform-panel" aria-label={pick('精选变化读取', 'Selection updates')}>
    <h2>{pick('接着上次，读取变化', 'Continue reading updates')}</h2>
    <p>{pick(objectId ? '显示上方所选对象的发布、修订和撤回记录。' : '显示全部已精选对象的发布、修订和撤回记录。', objectId ? 'Changes for the object selected above.' : 'Publication, revision and withdrawal events for all selections.')}</p>
    {result.loading && <p role="status">{pick('正在读取变化…','Loading changes…')}</p>}
    {result.error && <div role="alert"><p>{result.error}</p><button className="button" onClick={() => {setCursor(''); result.reload();}}>{pick('重新读取全部变化','Restart from all changes')}</button></div>}
    {result.data && !result.data.items.length && <p>{pick('此范围没有新的精选变化。','No new selection changes in this window.')}</p>}
    <ol className="platform-change-list">{result.data?.items.map(event => <li key={event.id}><div className="platform-section-heading"><strong>{names[event.kind] || event.kind}</strong><span>{dateText(event.published_at,zh)}</span></div><p>{event.name || event.object_id}</p><p className="muted">{pick('事件','Event')} {event.id} · {event.from_revision ?? '—'} → {event.to_revision ?? '—'}</p>{event.availability !== 'readable' ? <p>{pick('原资料已不可用，仅保留变化通知。','Source unavailable; change notice retained.')}</p> : event.to_revision && <Link to={`/for-you?object=${event.object_id}&revision=${event.to_revision}`}>{pick('读取这次发布的资料','Read this publication')}</Link>}</li>)}</ol>
    {result.data && <><div className="platform-actions"><button className="button" disabled={!result.data.has_more || result.loading} onClick={() => setCursor(result.data!.next_cursor!)}>{pick('继续这一批','Continue this window')}</button><button className="button" disabled={result.data.has_more || result.loading} onClick={() => setCursor(result.data!.resume_cursor)}>{pick('检查后续变化','Check subsequent changes')}</button><button className="text-button" onClick={() => {setCursor(''); result.reload();}}>{pick('从头读取','Read from the start')}</button></div><details><summary>{pick('给 AI 的续读配置','Continuation for your AI')}</summary><p>{pick('读完这一批后保存此配置，下次继续。每次保持相同对象范围和每页条数；超过 7 天请从头读取并按事件 ID 去重。','Save this after finishing the window. Keep the same objects and page size. After 7 days, restart and deduplicate event IDs.')}</p><pre className="platform-original">{checkpoint}</pre><button className="button" onClick={() => navigator.clipboard.writeText(checkpoint).then(() => notify(pick('续读配置已复制','Continuation copied'))).catch(() => notify(pick('请手动复制上方配置','Copy the configuration manually')))}>{pick('复制续读配置','Copy continuation')}</button></details></>}
  </section>;
}
