import { useEffect } from 'react';
import pages from '../../backend/seo/pages.json';

type PageCopy = { title: [string, string]; heading: [string, string]; description: [string, string] };
export const searchPages = pages as unknown as Record<string, PageCopy>;
export const contentPath = (id: string) => (id.startsWith('D-') ? '/news/' : '/watch/') + id;
export function publicContentLink(url: string) {
  const match = /^\/for-you#(?:news|watch)-((?:d-\d+|cw-[matsh]\d+))$/i.exec(url);
  return match ? contentPath(match[1].toUpperCase()) : url;
}

export function PageMetadata({ title, description = '', path, index = true }: {title:string; description?:string; path:string; index?:boolean}) {
  useEffect(() => {
    document.title = title;
    const url = 'https://fieldtofit.top' + path;
    const meta = (attribute: 'name'|'property', name: string, content: string) => {
      const nodes = [...document.head.querySelectorAll<HTMLMetaElement>(`meta[${attribute}="${name}"]`)];
      const node = nodes.shift() || document.createElement('meta');
      nodes.forEach(n => n.remove()); node.setAttribute(attribute, name); node.content = content;
      document.head.appendChild(node);
    };
    meta('name', 'description', description);
    meta('property', 'og:title', title); meta('property', 'og:description', description); meta('property', 'og:url', url);
    meta('name', 'robots', index && location.hostname === 'fieldtofit.top' ? 'index, follow' : 'noindex');
    const links = [...document.head.querySelectorAll<HTMLLinkElement>('link[rel="canonical"]')];
    const link = links.shift() || document.createElement('link'); links.forEach(n => n.remove());
    link.rel = 'canonical'; link.href = url; document.head.appendChild(link);
  }, [title, description, path, index]);
  return null;
}
