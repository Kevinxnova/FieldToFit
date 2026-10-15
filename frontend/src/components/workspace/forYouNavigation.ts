export const forYouSections = ['daily-preview','recent-news','hot-information-cards','technical-evolution-maps','news-codex-28-days','model-landscape','resource-dossiers'];
export function legacyReadingTargets(params:URLSearchParams){
  return [params.has('codex_date')?'codex':'', [...params.keys()].some(k=>k.startsWith('news_'))?'news':'', ['chart','company'].some(k=>params.has(k))?'models':'', ['q','type'].some(k=>params.has(k))?'watch':''].filter(Boolean);
}
export function legacyForYouTarget(search:string,hash:string):string|null {
  const params=new URLSearchParams(search);if(params.has('object'))return null;
  let id='';try{id=decodeURIComponent(hash.slice(1));}catch{return null;}
  const detail=/^(?:news|watch)-((?:d-\d+|cw-[matsh]\d+))$/i.exec(id);
  if(detail)return '/'+(detail[1].toUpperCase().startsWith('D-')?'news/':'watch/')+detail[1].toUpperCase();
  const targets=legacyReadingTargets(params);
  const anchored=id.startsWith('watch-group-')?'watch':id.startsWith('codex-day-')?'codex':['news-overview','news-releases'].includes(id)?'news':
    targets.length&&id==='resource-dossiers'?'watch':targets.length&&id==='model-landscape'?'models':targets.length&&id==='news-codex-28-days'?'codex':targets.length&&id==='recent-news'?'news':'';
  const target=anchored||(targets.length===1?targets[0]:'');
  return target?'/for-you/'+target+search+hash:null;
}
