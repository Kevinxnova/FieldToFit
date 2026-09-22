import { useEffect, useRef, useState } from 'react';
import { useLocation } from 'react-router-dom';
import { BASE } from '../../api/knowledge';
import { useWorkspace } from './UI';
import './site-visits.css';

const SESSION_MS = 30 * 60 * 1000;
const ID_KEY = 'fieldtofit-visit-session';
const OPT_OUT = 'fieldtofit-visits-opt-out';
const ADMIN_OUT = 'fieldtofit-visits-admin';
const CHANGE = 'fieldtofit-visits-preference';
const UPDATED = 'fieldtofit-visits-updated';
type Total = { total: number; started_at: string | null; updated_at: string | null; status: 'active' | 'paused'; collection_enabled: boolean; collection_origin: string };

function privateBrowser() {
  try {
    return navigator.doNotTrack === '1' || (navigator as Navigator & { globalPrivacyControl?: boolean }).globalPrivacyControl === true
      || navigator.webdriver || !!sessionStorage.getItem('fieldtofit-admin-password')
      || localStorage.getItem(OPT_OUT) === '1' || localStorage.getItem(ADMIN_OUT) === '1';
  } catch { return true; }
}

export function excludeAdminVisits() {
  try { localStorage.setItem(ADMIN_OUT, '1'); localStorage.removeItem(ID_KEY); } catch { /* unavailable storage is already excluded */ }
  window.dispatchEvent(new Event(CHANGE));
}

async function timedFetch(url: string, options: RequestInit, signal: AbortSignal) {
  const child = new AbortController();
  const cancel = () => child.abort();
  signal.addEventListener('abort', cancel, { once: true });
  if (signal.aborted) child.abort();
  const timer = window.setTimeout(cancel, 8000);
  try { return await fetch(url, { ...options, signal: child.signal }); }
  finally { clearTimeout(timer); signal.removeEventListener('abort', cancel); }
}

async function readTotal(signal: AbortSignal): Promise<Total> {
  const response = await timedFetch(BASE + '/analytics/total', { credentials: 'same-origin', cache: 'no-store' }, signal);
  if (!response.ok) throw new Error('unavailable');
  const data = await response.json();
  if (!Number.isSafeInteger(data.total) || data.total < 0 || !['active', 'paused'].includes(data.status)) throw new Error('invalid total');
  return data;
}

async function browserSession(): Promise<string | null> {
  // Web Locks serializes first visits in simultaneous tabs. Without a shared lock
  // or usable storage, exclude collection rather than invent another visitor.
  if (!navigator.locks || !crypto.randomUUID) return null;
  return navigator.locks.request('fieldtofit-visit-session', () => {
    if (privateBrowser()) return null;
    try {
      const at = Date.now();
      const stored = JSON.parse(localStorage.getItem(ID_KEY) || 'null');
      const id = stored && typeof stored.id === 'string' && stored.expires > at ? stored.id : crypto.randomUUID();
      localStorage.setItem(ID_KEY, JSON.stringify({ id, expires: at + SESSION_MS }));
      return id;
    } catch { return null; }
  });
}

/** Mount only when a public page's main content has actually loaded. */
export function VisitReady({ ready = true }: { ready?: boolean }) {
  const location = useLocation();
  const last = useRef(0);
  useEffect(() => {
    if (!ready) return;
    const abort = new AbortController();
    let busy = false;
    let eventId = crypto.randomUUID?.();
    last.current = 0;
    const send = async () => {
      if (busy || document.visibilityState !== 'visible' || privateBrowser() || !eventId || abort.signal.aborted) return;
      if (last.current && Date.now() - last.current < SESSION_MS) return;
      busy = true;
      try {
        const config = await readTotal(abort.signal);
        if (!config.collection_enabled || config.collection_origin !== window.location.origin
            || new URL(BASE, window.location.origin).origin !== window.location.origin) return;
        const browserId = await browserSession();
        if (!browserId || abort.signal.aborted || privateBrowser()) return;
        if (last.current) eventId = crypto.randomUUID();
        const body = JSON.stringify({ browser_id: browserId, event_id: eventId, path: location.pathname });
        for (let attempt = 0; attempt < 3; attempt++) {
          if (abort.signal.aborted || privateBrowser() || document.visibilityState !== 'visible') return;
          try {
            const response = await timedFetch(BASE + '/analytics/visit', {
              method: 'POST', headers: { 'Content-Type': 'application/json' }, body,
              credentials: 'same-origin',
            }, abort.signal);
            if (response.ok) {
              last.current = Date.now();
              window.dispatchEvent(new Event(UPDATED));
              return;
            }
            if (response.status < 500) return;
          } catch { if (abort.signal.aborted) return; }
          if (attempt < 2) await new Promise<void>(resolve => {
            const done = () => { clearTimeout(timer); abort.signal.removeEventListener('abort', done); resolve(); };
            const timer = window.setTimeout(done, 500 * (attempt + 1));
            abort.signal.addEventListener('abort', done, { once: true });
          });
        }
      } catch { /* Collection must never prevent reading. */ }
      finally { busy = false; }
    };
    const preference = () => { if (privateBrowser()) abort.abort(); else void send(); };
    void send();
    document.addEventListener('visibilitychange', send);
    window.addEventListener('pageshow', send);
    window.addEventListener(CHANGE, preference);
    window.addEventListener('storage', preference);
    return () => {
      abort.abort();
      document.removeEventListener('visibilitychange', send);
      window.removeEventListener('pageshow', send);
      window.removeEventListener(CHANGE, preference);
      window.removeEventListener('storage', preference);
    };
  }, [ready, location.key, location.pathname]);
  return null;
}

export function SiteVisits() {
  const { pick, zh } = useWorkspace();
  const location = useLocation();
  const [data, setData] = useState<Total | null>(null);
  const [failed, setFailed] = useState(false);
  const [excluded, setExcluded] = useState(privateBrowser);
  const [preferenceFailed, setPreferenceFailed] = useState(false);
  const hidden = /^\/(admin|account|tasks|compare|collection|feedback|legacy)(\/|$)/.test(location.pathname);
  useEffect(() => {
    if (hidden) return;
    const abort = new AbortController();
    let requestNumber = 0;
    const load = async () => {
      const number = ++requestNumber;
      try {
        const next = await readTotal(abort.signal);
        if (number === requestNumber) { setData(next); setFailed(false); }
      } catch { if (!abort.signal.aborted && number === requestNumber) setFailed(true); }
    };
    const changed = () => setExcluded(privateBrowser());
    const visible = () => { if (document.visibilityState === 'visible') void load(); };
    void load();
    const timer = window.setInterval(visible, 60_000);
    window.addEventListener(UPDATED, load);
    window.addEventListener(CHANGE, changed);
    window.addEventListener('storage', changed);
    document.addEventListener('visibilitychange', visible);
    return () => { abort.abort(); clearInterval(timer); window.removeEventListener(UPDATED, load); window.removeEventListener(CHANGE, changed); window.removeEventListener('storage', changed); document.removeEventListener('visibilitychange', visible); };
  }, [hidden, location.pathname]);
  if (hidden) return null;
  const toggle = () => {
    try {
      localStorage.removeItem(ID_KEY);
      if (excluded) { localStorage.removeItem(OPT_OUT); localStorage.removeItem(ADMIN_OUT); }
      else localStorage.setItem(OPT_OUT, '1');
      setPreferenceFailed(false);
      window.dispatchEvent(new Event(CHANGE));
    } catch { setPreferenceFailed(true); }
  };
  const since = data?.started_at ? new Intl.DateTimeFormat('en-CA', { timeZone: 'Asia/Shanghai', year: 'numeric', month: '2-digit', day: '2-digit' }).format(new Date(data.started_at)) : null;
  return <div className="site-visits">
    <p className="site-visits-count" aria-live="polite">{failed ? pick('访问统计暂不可用', 'Visit statistics temporarily unavailable') : pick('全站累计访问：', 'Total site visits: ') + (data ? data.total.toLocaleString(zh ? 'zh-CN' : 'en-US') : '—') + pick(' 次', '')}</p>
    {!failed && data && <small>{since ? pick(`自 ${since} 起统计`, `Counted since ${since}`) : pick('尚未开始统计', 'Counting has not started')}{data.status === 'paused' && since ? pick(' · 统计已暂停', ' · Collection paused') : ''}</small>}
    <details className="site-visits-details"><summary>{pick('统计说明与设置', 'About this count & preferences')}</summary>
      <p>{pick('按浏览器访问会话估算；30 分钟内刷新、换页和多标签页不重复计数。仅记录正式站公开页面，排除已知机器人、管理和测试访问；未参与统计的访问及无法识别的机器人会造成误差。数字可能稍有延迟，不代表独立人数。', 'Estimated browser visits: refreshes, navigation and tabs within 30 minutes share one visit. Counts public pages on the main site, excluding known bots, administration and tests. Opt-outs and unidentified bots affect accuracy. Updates may be delayed; this is not a unique-person count.')}</p>
      <p>{pick('仅使用短期随机标识去重，不保存浏览历史或完整 IP。服务器标识满 24 小时后在下次访问或每日维护时清理；累计次数长期保留。退出后清除本地标识并停止发送；已计入的匿名总数不回撤。尊重浏览器隐私信号，存储不可用时不计数。', 'Short-lived random identifiers deduplicate visits; no browsing history or full IP is stored. Server identifiers expire after 24 hours and are removed on the next visit or daily maintenance; the anonymous total is retained. Opting out clears the local identifier and stops collection, without subtracting prior visits. Browser privacy signals and unavailable storage exclude collection.')}</p>
      <p>{excluded ? pick('此浏览器当前不参与统计。', 'This browser is currently excluded.') : pick('此浏览器可参与访问统计。', 'This browser can participate in visit counting.')}</p>
      <button type="button" className="text-button" onClick={toggle}>{excluded ? pick('允许此浏览器参与', 'Allow this browser') : pick('此浏览器不参与统计', 'Exclude this browser')}</button>
      {preferenceFailed && <p role="status">{pick('浏览器无法保存设置；当前不参与统计。', 'Preferences cannot be saved; this browser is excluded.')}</p>}
      {excluded && <small>{pick('浏览器隐私信号或管理身份仍会优先排除；允许后下次打开页面生效。', 'Privacy signals and admin status still take priority; allowing applies on the next page visit.')}</small>}
    </details>
  </div>;
}
