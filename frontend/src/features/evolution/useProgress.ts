import {useSyncExternalStore} from 'react';
import {decodeProgress,PROGRESS_KEY,type Records} from './progress';
let snapshot:{records:Records;warning:boolean}={records:{},warning:false};
let initialized=false;
const listeners=new Set<()=>void>();
function refresh(){
  try {snapshot={records:decodeProgress(localStorage.getItem(PROGRESS_KEY)),warning:false};}
  catch {snapshot={...snapshot,warning:true};}
}
function emit(){listeners.forEach(fn=>fn());}
function storage(event:StorageEvent){if(event.key===PROGRESS_KEY||event.key===null){refresh();emit();}}
function subscribe(listener:()=>void){
  listeners.add(listener);
  if(listeners.size===1){window.addEventListener('storage',storage);refresh();emit();}
  return ()=>{listeners.delete(listener);if(!listeners.size)window.removeEventListener('storage',storage);};
}
function getSnapshot(){if(!initialized){initialized=true;refresh();}return snapshot;}
export function markRead(id:string,revision:number,read:boolean){
  let records=snapshot.records,warning=false;
  try{records={...records,...decodeProgress(localStorage.getItem(PROGRESS_KEY))};}catch{warning=true;}
  records={...records,[id]:{read,revision,at:new Date().toISOString()}};
  try{localStorage.setItem(PROGRESS_KEY,JSON.stringify({version:1,records}));}catch{warning=true;}
  snapshot={records,warning};emit();
}
export function useProgress(){return useSyncExternalStore(subscribe,getSnapshot);}
