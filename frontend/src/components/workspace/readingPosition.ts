type Position={anchor:string;offset:number;y:number;open:string[];focus:string};
const storageKey='fieldtofit.reading.positions';
let restoring=false,restoration=0;
const urlKey=()=>location.pathname+location.search;
function positions():Record<string,Position>{try{return JSON.parse(sessionStorage.getItem(storageKey)||'{}');}catch{return {};}}
function detailKey(node:HTMLDetailsElement){const parent=node.parentElement?.closest('[id]');if(!parent)return '';return parent.id+'::'+Array.from(parent.querySelectorAll('details')).indexOf(node);}
export function hasReadingPosition(){return !!positions()[urlKey()];}
export function saveReadingPosition(expectedKey=urlKey(),navigation=false){
  // A debounced scroll from the old route must not overwrite the new route.
  if(expectedKey!==urlKey())return;
  if(navigation){restoration++;restoring=false;}
  if(restoring)return;
  const content=document.getElementById('main-content');if(!content)return;
  const anchors=Array.from(content.querySelectorAll<HTMLElement>('[id]')).filter(n=>n.getClientRects().length&&n.getBoundingClientRect().top<=160);
  const anchor=anchors.sort((a,b)=>b.getBoundingClientRect().top-a.getBoundingClientRect().top)[0];
  const all=positions();delete all[urlKey()];all[urlKey()]={anchor:anchor?.id||'',offset:anchor?.getBoundingClientRect().top||0,y:window.scrollY,open:Array.from(content.querySelectorAll<HTMLDetailsElement>('details[open]')).map(detailKey).filter(Boolean),focus:(document.activeElement as HTMLElement)?.id||''};
  try{sessionStorage.setItem(storageKey,JSON.stringify(Object.fromEntries(Object.entries(all).slice(-30))));}catch{/* Reading works without storage. */}
}
export function restoreReadingPosition(fallback=false){
  const saved=positions()[urlKey()];if(!saved)return false;
  if(saved.anchor&&!document.getElementById(saved.anchor)&&!fallback)return false;
  const expectedKey=urlKey();
  const token=++restoration;restoring=true;
  const content=document.getElementById('main-content');
  content?.querySelectorAll<HTMLDetailsElement>('details').forEach(d=>{d.open=saved.open.includes(detailKey(d));});
  let cancelled=false;
  const cancel=()=>{if(token!==restoration)return;cancelled=true;restoration++;restoring=false;};
  window.addEventListener('pointerdown',cancel,{once:true});window.addEventListener('wheel',cancel,{once:true});window.addEventListener('keydown',cancel,{once:true});
  const apply=()=>{if(!cancelled&&token===restoration&&expectedKey===urlKey()){const node=document.getElementById(saved.anchor);window.scrollTo(0,node?window.scrollY+node.getBoundingClientRect().top-saved.offset:saved.y);document.getElementById(saved.focus)?.focus({preventScroll:true});}};
  // Cached markup is already committed; restore now, then settle reopened details.
  apply();
  requestAnimationFrame(()=>requestAnimationFrame(()=>{
    apply();
    if(token===restoration)restoring=false;window.removeEventListener('pointerdown',cancel);window.removeEventListener('wheel',cancel);window.removeEventListener('keydown',cancel);
  }));return true;
}
