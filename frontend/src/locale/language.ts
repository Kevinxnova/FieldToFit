import { useSyncExternalStore, createContext, useContext } from 'react';
import entries from './en.json';

export type Language = 'zh' | 'en';
const listeners = new Set<() => void>();
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
  const scroll = [window.scrollX, window.scrollY];
  const path = languagePath(location.pathname, language) + location.search + location.hash;
  window.history.replaceState(window.history.state, '', path);
  window.dispatchEvent(new PopStateEvent('popstate', {state:window.history.state}));
  listeners.forEach(listener => listener());
  requestAnimationFrame(() => window.scrollTo(scroll[0], scroll[1]));
}
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
