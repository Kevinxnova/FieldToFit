import { useLocation as useBrowserLocation } from 'react-router';
import { useEffect, useLayoutEffect, useRef } from 'react';
import { useLocation, useNavigationType } from '@fieldtofit/locale/router';
import { useReadingUpdates } from '../../api/reading';
import { hasReadingPosition, restoreReadingPosition, saveReadingPosition } from './readingPosition';
import { useWorkspace } from './UI';

export function ReadingSession(){
  const browserLocation=useBrowserLocation();
  const location=useLocation(),navigation=useNavigationType(),{pick}=useWorkspace();
  const relevant=/^\/(for-you$|news\/|watch\/|maps(?:\/|$))/.test(location.pathname);
  const updates=useReadingUpdates(relevant,location.pathname==='/for-you'), first=useRef(true), previousPath=useRef(location.pathname), pendingRestore=useRef(false);
  useEffect(()=>{const previous=window.history.scrollRestoration;window.history.scrollRestoration='manual';return()=>{window.history.scrollRestoration=previous;};},[]);
  useLayoutEffect(()=>{
    const returning=navigation==='POP'||location.state?.readingRestore||location.state?.restoreReading;
    const changed=previousPath.current!==location.pathname;
    pendingRestore.current=!!returning&&hasReadingPosition();
    if(pendingRestore.current)pendingRestore.current=!restoreReadingPosition();
    else if((first.current||changed)&&!location.hash)window.scrollTo(0,0);
    if(!first.current&&relevant&&changed)window.dispatchEvent(new Event('fieldtofit:check-reading'));
    first.current=false;previousPath.current=location.pathname;
  },[location.key]);
  useEffect(()=>{
    if(!relevant)return;
    let timer:ReturnType<typeof setTimeout>|undefined;
    const readingKey=browserLocation.pathname+browserLocation.search;
    const save=()=>saveReadingPosition(readingKey);const scroll=()=>{clearTimeout(timer);timer=setTimeout(save,100);};
    const restore=()=>{requestAnimationFrame(()=>restoreReadingPosition(true));};
    const ready=()=>{if(pendingRestore.current){pendingRestore.current=false;restoreReadingPosition(true);}};
    const cancel=()=>{pendingRestore.current=false;};
    window.addEventListener('fieldtofit:reading-ready',ready);window.addEventListener('pointerdown',cancel);window.addEventListener('wheel',cancel);window.addEventListener('keydown',cancel);
    window.addEventListener('scroll',scroll,{passive:true});document.addEventListener('toggle',scroll,true);window.addEventListener('pagehide',save);window.addEventListener('fieldtofit:save-reading',save);window.addEventListener('fieldtofit:restore-reading',restore);
    return()=>{clearTimeout(timer);window.removeEventListener('fieldtofit:reading-ready',ready);window.removeEventListener('pointerdown',cancel);window.removeEventListener('wheel',cancel);window.removeEventListener('keydown',cancel);window.removeEventListener('scroll',scroll);document.removeEventListener('toggle',scroll,true);window.removeEventListener('pagehide',save);window.removeEventListener('fieldtofit:save-reading',save);window.removeEventListener('fieldtofit:restore-reading',restore);};
  },[relevant,location.pathname,location.search]);
  if(!relevant||!updates.pending&&!updates.notice)return null;
  return <div className="platform-notice reading-update" role="status">
    {updates.notice==='offline'?<>{pick('暂未确认最新状态，正在显示上次读取的内容。','Latest status could not be checked. Showing the previously read content.')} <button className="text-button" onClick={()=>void updates.check()}>{pick('重试','Retry')}</button></>:updates.notice==='access'?<>{pick('读取权限已变化，请重新检查访问配置。','Read access changed. Check your access configuration.')} <button className="text-button" onClick={()=>void updates.check()}>{pick('重试','Retry')}</button></>:updates.notice==='withdrawn'?pick('内容可读状态已变化，相关旧资料已清除。','Content availability changed. Affected previous materials have been cleared.'):null}
    {updates.pending&&<><span>{pick('内容有更新','Content has updates')}</span> <button className="text-button" onClick={updates.apply}>{pick('更新并保持阅读位置','Update and keep reading position')}</button></>}
  </div>;
}
