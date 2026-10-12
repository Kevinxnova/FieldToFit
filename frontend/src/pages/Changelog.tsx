import { useEffect, useRef, useState } from 'react';
import { useLocation } from '@fieldtofit/locale/router';
import { request } from '../api/knowledge';
import { useLanguage, restoreLanguageScroll } from '../locale/language';
import { useWorkspace } from '../components/workspace/UI';
import './changelog.css';

type Entry = { version: string; date: string; deployed_on: string; title: string; highlights: string[]; details: string; translation_available: boolean; status: 'current'|'deployed'|'unverified'; source_url: string };
type History = { version: string; revision: string; language: string; items: Entry[]; archive_url: string };
const PAGE_SIZE = 10;

export default function Changelog() {
  const { pick } = useWorkspace();
  const language = useLanguage();
  const location = useLocation();
  const [data, setData] = useState<History | null>(null);
  const [pending, setPending] = useState<History | null>(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [attempt, setAttempt] = useState(0);
  const [count, setCount] = useState(PAGE_SIZE);
  const [expanded, setExpanded] = useState<Set<string>>(new Set());
  const current = useRef<History | null>(null);
  const shown = data?.language === language ? data : null;
  const update = pending?.language === language ? pending : null;

  useEffect(() => {
    let cancelled = false, busy = false;
    const controller = new AbortController();
    setError(''); setPending(null); setLoading(true);
    const read = async (initial = false) => {
      if (busy || (!initial && document.visibilityState === 'hidden')) return;
      busy = true;
      // A stalled network request must not prevent retries forever.
      const requestController = new AbortController();
      const abort = () => requestController.abort();
      controller.signal.addEventListener('abort', abort, { once: true });
      const timer = window.setTimeout(abort, 15000);
      try {
        const options = { signal: requestController.signal, cache: 'no-store' as const };
        const existing = current.current?.language === language ? current.current : null;
        if (!initial && existing) {
          const meta = await request<Pick<History, 'revision'|'version'>>(`/changelog?metadata=1&lang=${language}`, options);
          if (meta.revision === existing.revision) { if (!cancelled) setError(''); return; }
        }
        const result = await request<History>(`/changelog?lang=${language}`, options);
        if (cancelled) return;
        if (result.language !== language) throw new Error('Language mismatch');
        setError('');
        if (initial || !existing) {
          current.current = result; setData(result); setPending(null);
          restoreLanguageScroll(language);
        } else {
          setPending(result);
        }
      } catch {
        if (!cancelled) setError(language === 'en' ? 'Unable to check the latest changelog. Please retry.' : '暂时无法读取最新更新日志，请重试。');
      } finally {
        window.clearTimeout(timer); controller.signal.removeEventListener('abort', abort);
        busy = false; if (!cancelled) setLoading(false);
      }
    };
    void read(true);
    const check = () => { void read(); };
    const interval = window.setInterval(check, 60000);
    window.addEventListener('focus', check);
    document.addEventListener('visibilitychange', check);
    return () => { cancelled = true; controller.abort(); window.clearInterval(interval); window.removeEventListener('focus', check); document.removeEventListener('visibilitychange', check); };
  }, [language, attempt]);

  useEffect(() => {
    if (!shown || !/^#v\d+\.\d+\.\d+$/.test(location.hash)) return;
    const index = shown.items.findIndex(item => '#v' + item.version === location.hash);
    if (index < 0) return;
    if (index >= count) { setCount(index + 1); return; }
    const frame = requestAnimationFrame(() => document.getElementById(location.hash.slice(1))?.scrollIntoView({ block: 'start' }));
    return () => cancelAnimationFrame(frame);
  }, [shown, location.hash, count]);

  const applyUpdate = () => {
    if (!update) return;
    const anchor = [...document.querySelectorAll<HTMLElement>('.changelog-entry')].find(item => item.getBoundingClientRect().bottom > 90);
    const before = anchor?.getBoundingClientRect().top;
    const id = anchor?.id;
    current.current = update; setData(update); setPending(null);
    setCount(previous => previous + Math.max(0, update.items.length - (shown?.items.length || 0)));
    requestAnimationFrame(() => {
      const after = id ? document.getElementById(id)?.getBoundingClientRect().top : undefined;
      if (before !== undefined && after !== undefined) window.scrollBy(0, after - before);
    });
  };
  return <div className="platform-page changelog-page">
    <header className="platform-hero"><p className="platform-eyebrow">FIELDTOFIT · CHANGELOG</p><h1>{pick('FieldToFit 更新日志', 'FieldToFit changelog')}</h1><p className="platform-lead">{pick('记录每一次改进。', 'Every improvement, recorded.')}</p>
      <p className="changelog-running">{pick('当前运行版本：', 'Running version: ')}<strong>{shown ? 'v' + shown.version : '—'}</strong></p>
    </header>
    {update && <div className="changelog-update" role="status"><span>{pick('有新版本记录', 'New release notes are available')}</span><button className="button" onClick={applyUpdate}>{pick('更新列表', 'Update list')}</button></div>}
    {error && <div className="platform-notice" role="alert">{error} {shown && pick('已保留当前阅读记录。', 'Your current reading is preserved.')} <button className="button" disabled={loading} onClick={() => setAttempt(value => value + 1)}>{pick('重试', 'Retry')}</button></div>}
    {(!shown && !error) && <p role="status">{pick('正在读取更新日志…', 'Loading changelog…')}</p>}
    {shown && <>
      <div className="changelog-timeline">{shown.items.slice(0, count).map(entry => <article className="changelog-entry" id={'v' + entry.version} key={entry.version}>
        <div className="changelog-meta"><a href={'#v' + entry.version} aria-label={pick('链接到版本 ', 'Link to version ') + entry.version}>v{entry.version}</a><time dateTime={entry.date || undefined}>{entry.date || pick('日期未记录', 'Date not recorded')}</time><span>{entry.status === 'current' ? pick('当前版本', 'Current version') : entry.status === 'deployed' ? pick('已上线', 'Deployed') : pick('上线状态未核实', 'Deployment unverified')}</span></div>
        <h2>{entry.title}</h2>
        {!entry.translation_available ? <p className="muted">{pick('此版本摘要暂未提供。', 'The English summary for this version is not available.')}</p> : <ul>{entry.highlights.slice(0, 3).map((line, index) => <li key={index}>{line}</li>)}</ul>}
        <details open={expanded.has(entry.version)} onToggle={event => { const open = event.currentTarget.open; setExpanded(previous => { if (previous.has(entry.version) === open) return previous; const next = new Set(previous); if (open) next.add(entry.version); else next.delete(entry.version); return next; }); }}>
          <summary>{pick('完整说明', 'Full notes')}</summary>
          {entry.highlights.length > 3 && <ul>{entry.highlights.slice(3).map((line, index) => <li key={index}>{line}</li>)}</ul>}
          {entry.details && entry.details.split(/\n\s*\n/).map((paragraph, index) => <p key={index}>{paragraph}</p>)}
          {entry.deployed_on && <p className="muted">{pick('已核对上线日期：', 'Verified deployment date: ')}{entry.deployed_on}</p>}
          <a className="changelog-source" href={entry.source_url} target="_blank" rel="noopener noreferrer">{pick('查看 GitHub 原记录', 'View the original GitHub record')} ↗</a>
        </details>
      </article>)}</div>
      {count < shown.items.length && <button className="button" onClick={() => setCount(value => value + PAGE_SIZE)}>{pick('加载更多历史', 'Load earlier releases')}</button>}
      {!shown.items.length && <p>{pick('暂无更新记录。', 'No release notes yet.')}</p>}
      <p className="changelog-archive"><a href={shown.archive_url} target="_blank" rel="noopener noreferrer">{pick('查看 Metis 历史归档', 'View the Metis archive')} ↗</a></p>
    </>}
  </div>;
}
