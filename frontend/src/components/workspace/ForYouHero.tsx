import { useEffect, useRef } from 'react';
import { Link } from '@fieldtofit/locale/router';
import { searchPages } from '../../search';
import { useWorkspace } from './UI';
import './ForYouHero.css';

/** Keep reading controls independent of the optional decorative renderer. */
export function ForYouHero({ onRead }: { onRead: () => void }) {
  const { pick } = useWorkspace();
  const art = useRef<HTMLDivElement>(null);
  const canvas = useRef<HTMLCanvasElement>(null);
  const globe = useRef<HTMLButtonElement>(null);
  useEffect(() => {
    let disposed = false;
    let destroy: (() => void) | undefined;
    void import('./forYouScene').then(({ mountForYouScene }) => {
      if (!disposed && art.current && canvas.current && globe.current) {
        destroy = mountForYouScene(art.current, canvas.current, globe.current);
      }
    }).catch(() => { /* The static scene and all reading links remain available. */ });
    return () => { disposed = true; destroy?.(); };
  }, []);
  const destinations = [
    ['model-landscape', pick('浏览模型图表', 'Explore model charts'), pick('比较能力与价格', 'Compare capability and cost')],
    ['recent-news', pick('阅读近期动态', 'Read developments'), pick('了解发布、变化与解读', 'Releases, changes and analysis')],
    ['resource-dossiers', pick('浏览持续关注', 'Explore ongoing watch'), pick('查看版本、原文与采用条件', 'Versions, sources and adoption')],
  ];
  return <header className="for-you-hero">
    <div className="for-you-hero-banner">
      <div ref={art} className="for-you-scene">
        <img className="for-you-scene-poster" src="/assets/for-you-scene/poster.webp" width="1100" height="525" alt="" fetchPriority="high" />
        <canvas ref={canvas} className="for-you-scene-canvas" aria-hidden="true" />
        <button ref={globe} className="for-you-scene-target" type="button" aria-label={pick('激发球体能量波', 'Send an energy wave through the sphere')} disabled />
      </div>
      <div className="for-you-hero-shade" />
      <div className="for-you-hero-intro">
        <p className="for-you-hero-eyebrow">FOR YOU · {pick('给你看', 'CURATED READING')}</p>
        <h1>{pick(...searchPages['/for-you'].heading).split('\n').map((line, index) => <span key={index}>{line}</span>)}</h1>
        <p className="for-you-hero-summary">{pick(searchPages['/for-you'].description[0].replace(/，/g, '，\n'), searchPages['/for-you'].description[1])}</p>
        <ul className="for-you-hero-types" aria-label={pick('持续关注范围', 'Ongoing watch categories')}>
          {[pick('模型', 'Models'), pick('工具', 'Tools'), 'Agent', 'Skill', 'Harness'].map(name => <li key={name}>{name}</li>)}
        </ul>
        <p className="for-you-hero-meta"><span>{pick('每日检查来源 · 内容经审核更新', 'Daily source checks · Reviewed updates')}</span><Link to="/about">{pick('为什么做 FieldToFit', 'Why FieldToFit')} ↗</Link></p>
      </div>
    </div>
    <nav className="for-you-hero-links" aria-label={pick('阅读入口', 'Reading sections')}>
      {destinations.map(([id, title, description], index) => <a key={id} href={'#' + id} onClick={onRead}>
        <span className="for-you-hero-number" aria-hidden="true">0{index + 1}</span><span><strong>{title}</strong><span>{description}</span></span><span className="for-you-hero-arrow" aria-hidden="true">↘</span>
      </a>)}
    </nav>
  </header>;
}
