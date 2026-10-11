import { useSyncExternalStore, createContext, useContext } from 'react';
import entries from './en.json';

export type Language = 'zh' | 'en';
const listeners = new Set<() => void>();
let languageScroll: {language: Language; position: [number,number]; hash: string} | null = null;
export const canonicalPath = (path: string) => path.replace(/^\/en(?=\/|$)/, '') || '/';
export function currentLanguage(): Language { return /^\/en(?:\/|$)/.test(window.location.pathname) ? 'en' : 'zh'; }
export const LanguageContext = createContext<Language|null>(null);
export function useLanguage() { const override=useContext(LanguageContext);const language=useSyncExternalStore(subscribe, currentLanguage, () => 'zh' as Language);return override || language; }
function subscribe(listener: () => void) { listeners.add(listener); return () => { listeners.delete(listener); }; }
export function languagePath(path: string, language = currentLanguage()) {
  if (!path.startsWith('/') || path.startsWith('//') || path.startsWith('/api/') || path.startsWith('/assets/')) return path;
  const clean = canonicalPath(path);
  return language === 'en' ? '/en' + (clean === '/' ? '/for-you' : clean) : clean;
}
export function changeLanguage(language: Language) {
  const scroll: [number,number] = [window.scrollX, window.scrollY];
  languageScroll = {language, position: scroll, hash: location.hash};
  const path = languagePath(location.pathname, language) + location.search + location.hash;
  window.history.replaceState(window.history.state, '', path);
  window.dispatchEvent(new PopStateEvent('popstate', {state:window.history.state}));
  listeners.forEach(listener => listener());
  requestAnimationFrame(() => window.scrollTo(scroll[0], scroll[1]));
}
export function restoreLanguageScroll(language: string) {
  const saved=languageScroll;
  if (!saved || saved.language!==language) return;
  // Wait for React to render the newly read content before restoring its position.
  requestAnimationFrame(() => requestAnimationFrame(() => {
    if (languageScroll!==saved || currentLanguage()!==language) return;
    let target: HTMLElement | null = null;
    try { target=saved.hash ? document.getElementById(decodeURIComponent(saved.hash.slice(1))) : null; } catch { /* Malformed fragment: retain the numeric position. */ }
    if (target) target.scrollIntoView({block:'start'});
    else window.scrollTo(...saved.position);
  }));
}
// A reader's next action takes precedence over a pending language reload.
for (const event of ['pointerdown','wheel','touchstart','keydown']) window.addEventListener(event, () => {languageScroll=null;}, {passive:true});
window.addEventListener('popstate', () => listeners.forEach(listener => listener()));
const catalog = entries as Record<string,string>;
const fragments = Object.keys(catalog).filter(s => /[\u3400-\u9fff]/.test(s)).sort((a,b) => b.length-a.length);
const escape = (s:string) => s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
const pattern = new RegExp(fragments.map(escape).join('|'), 'g');
export function english(value:string) {
  if (!/[\u3400-\u9fff]/.test(value)) return value;
  if (catalog[value]) return catalog[value];
  const trimmed = value.trim();
  if (catalog[trimmed]) return value.replace(trimmed,catalog[trimmed]);
  return value.replace(pattern, match => catalog[match]);
}
const confirm = window.confirm.bind(window);
window.confirm = message => confirm(currentLanguage()==='en' ? english(String(message)) : message);
