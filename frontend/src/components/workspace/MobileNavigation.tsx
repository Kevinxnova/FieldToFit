import { useEffect, useRef, useState } from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import { Icon, useWorkspace } from './UI';

const destinations = [
  ['/about', 'info', '关于 FieldToFit', 'About FieldToFit', '了解项目的立意与使用方式', 'Understand the project and how to use it'],
  ['/community', 'source', 'FieldToFit 社区', 'FieldToFit Community', '投稿项目、推荐资源、参与共建', 'Submit projects, recommend resources, and contribute'],
  ['/sources', 'source', '数据来源', 'Sources', '查看关注对象、采集渠道与检查情况', 'View tracked subjects, collection channels, and check status'],
  ['/admin', 'settings', '内容管理', 'Content management', '每日审阅、资料管理与需求反馈', 'Daily review, content management, and feedback'],
];

export function MobileNavigation() {
  const { pick } = useWorkspace();
  const location = useLocation();
  const [open, setOpen] = useState(false);
  const dialog = useRef<HTMLDialogElement>(null);
  const trigger = useRef<HTMLButtonElement>(null);
  const navigating = useRef(false);
  const active = destinations.some(([path]) => location.pathname === path || location.pathname.startsWith(path + '/'));
  const close = () => { dialog.current?.close(); setOpen(false); };
  const navigate = () => {
    navigating.current = true;
    close();
    requestAnimationFrame(() => document.getElementById('main-content')?.focus({ preventScroll: true }));
  };
  useEffect(() => { if (dialog.current?.open) navigate(); }, [location.key]);
  useEffect(() => {
    const media = window.matchMedia('(max-width: 700px)');
    const resize = () => { if (!media.matches) close(); };
    const anotherPanel = () => { navigating.current = true; close(); };
    media.addEventListener('change', resize);
    window.addEventListener('fieldtofit:open-contents', anotherPanel);
    return () => {
      media.removeEventListener('change', resize);
      window.removeEventListener('fieldtofit:open-contents', anotherPanel);
    };
  }, []);
  const show = () => {
    window.dispatchEvent(new Event('fieldtofit:open-more'));
    navigating.current = false;
    dialog.current?.showModal();
    setOpen(true);
  };
  const bar = (inside = false) => <nav className="mobile-bottom-nav" aria-label={pick('手机导航', 'Mobile navigation')}>
    <NavLink to="/for-you" onClick={inside ? navigate : undefined}><Icon name="news" size={20} /><span>For you</span></NavLink>
    <NavLink to="/for-your-ai" onClick={inside ? navigate : undefined}><Icon name="code" size={20} /><span>For your AI</span></NavLink>
    <button ref={inside ? undefined : trigger} type="button" className={active ? 'active' : ''} aria-current={active ? 'location' : undefined} aria-haspopup="dialog" aria-expanded={open} aria-controls="mobile-more-dialog" onClick={inside ? close : show}>
      <Icon name="more" size={20} /><span>{pick('更多', 'More')}</span>
    </button>
  </nav>;
  return <div className="mobile-navigation">
    {bar()}
    <dialog ref={dialog} id="mobile-more-dialog" className="mobile-more-dialog" aria-labelledby="mobile-more-title" onClick={event => { if (event.target === event.currentTarget) close(); }} onClose={() => {
      setOpen(false);
      if (!navigating.current && window.matchMedia('(max-width: 700px)').matches) trigger.current?.focus({ preventScroll: true });
      navigating.current = false;
    }}>
      <section className="mobile-more-panel">
        <header><h2 id="mobile-more-title">{pick('更多', 'More')}</h2><button type="button" className="icon-button" aria-label={pick('关闭更多导航', 'Close more navigation')} onClick={close}><Icon name="close" /></button></header>
        <nav aria-label={pick('更多页面', 'More pages')}>
          {destinations.map(([path, icon, zh, en, descriptionZh, descriptionEn]) => <NavLink key={path} to={path} onClick={navigate}>
            <Icon name={icon} /><span><strong>{pick(zh, en)}</strong><small>{pick(descriptionZh, descriptionEn)}</small></span><Icon name="chevron" size={16} />
          </NavLink>)}
        </nav>
      </section>
      {bar(true)}
    </dialog>
  </div>;
}
