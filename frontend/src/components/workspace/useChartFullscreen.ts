import { useEffect, useRef, useState } from 'react';

/** Only native fullscreen events determine whether the chart is fullscreen. */
export function useChartFullscreen() {
  const container = useRef<HTMLDivElement>(null);
  const button = useRef<HTMLButtonElement>(null);
  const active = useRef(false), busy = useRef(false);
  const position = useRef({x:0,y:0});
  const [fullscreen,setFullscreen] = useState(false);
  const [pending,setPending] = useState(false);
  const [error,setError] = useState<'unsupported'|'enter'|'exit'|null>(null);

  useEffect(()=>{
    let frame = 0;
    const changed = ()=>{
      const next = document.fullscreenElement === container.current;
      const wasActive = active.current;
      active.current = next;
      setFullscreen(next);
      setError(null);
      cancelAnimationFrame(frame);
      if(next) {
        container.current?.scrollTo(0,0);
        button.current?.focus({preventScroll:true});
      } else if(wasActive && !document.fullscreenElement) {
        // Wait for the normal chart layout to return before restoring the page.
        frame = requestAnimationFrame(()=>{
          container.current?.scrollTo(0,0);
          button.current?.focus({preventScroll:true});
          window.scrollTo({left:position.current.x,top:position.current.y,behavior:'instant'});
        });
      }
    };
    document.addEventListener('fullscreenchange',changed);
    return ()=>{
      document.removeEventListener('fullscreenchange',changed);
      cancelAnimationFrame(frame);
    };
  },[]);

  const toggle = async()=>{
    const element = container.current;
    if(!element || busy.current)return;
    setError(null);
    const exiting = document.fullscreenElement === element;
    if(!exiting && (!element.requestFullscreen || !document.fullscreenEnabled)) {
      setError('unsupported');
      return;
    }
    busy.current = true;
    setPending(true);
    try {
      if(exiting) await document.exitFullscreen();
      else {
        position.current = {x:window.scrollX,y:window.scrollY};
        // Keep the request in the click/keyboard activation, without an intervening await.
        await element.requestFullscreen({navigationUI:'hide'});
      }
    } catch {
      setError(exiting?'exit':'enter');
    } finally {
      busy.current = false;
      setPending(false);
    }
  };
  return {container,button,fullscreen,pending,error,toggle};
}
