import {catalog,type Track,type Milestone,type EvolutionRoute} from './data';

export type Rect={x:number;y:number;width:number;height:number};
export type MapItem={node:Milestone;route:EvolutionRoute;rect:Rect};
export type MapPath={id:string;from:string;to:string;path:string;evidence:boolean;kind?:string};
// These are spatial packing priorities, not additional user-facing categories.
const packing:Record<string,number>={dense:1,encoder:0,text2text:0,moe:0,hybrid:0,data:1,preference:2,reasoning_rl:2,agent_rl:2,adaptation:3,representation:3,shared_kv:0,latent_kv:0,long_context:0,sparse_context:0,quantization:1,draft_verify:1,thinking:2,tools:2,sharding:0,model_parallel:0,expert_systems:0,kernels:1,kv_paging:2,batching:2,disaggregation:2,rl_systems:3};
const periods=[{label:'2017–2019',start:2017,end:2019,columns:1},{label:'2020–2021',start:2020,end:2021,columns:1},...Array.from({length:5},(_,i)=>({label:String(2022+i),start:2022+i,end:2022+i,columns:i===3?2:1}))];
export function connect(a:Rect,b:Rect){
  const start=a.x+a.width, end=b.x,ay=a.y+a.height/2,by=b.y+b.height/2;
  if(end>start+10){const bend=Math.max(20,(end-start)/2);return `M${start},${ay} C${start+bend},${ay} ${end-bend},${by} ${end},${by}`;}
  const gutter=Math.min(a.x,b.x)-18;return `M${a.x},${ay} C${gutter-12},${ay} ${gutter-12},${by} ${b.x},${by}`;
}
export function buildAtlas(track:Track){
  const routes=catalog.routes.filter(r=>r.track===track),nodeWidth=184,nodeHeight=260,columnStep=209,rowStep=288;
  let x=118;
  const bands=periods.map(b=>{const band={...b,x,width:b.columns*columnStep+12};x+=band.width;return band;});
  const items:MapItem[]=[];let y=103;
  for(let priority=0;priority<=3;priority++){
    let rows=0;
    for(const band of bands){
      const entries=routes.filter(r=>(packing[r.id]??3)===priority).flatMap(route=>route.nodes.map(node=>({node,route}))).filter(({node})=>+node.date.slice(0,4)>=band.start&&+node.date.slice(0,4)<=band.end).sort((a,b)=>a.node.date.localeCompare(b.node.date)||a.node.id.localeCompare(b.node.id));
      entries.forEach((entry,i)=>items.push({...entry,rect:{x:band.x+12+(i%band.columns)*columnStep,y:y+Math.floor(i/band.columns)*rowStep,width:nodeWidth,height:nodeHeight}}));
      rows=Math.max(rows,Math.ceil(entries.length/band.columns));
    }
    if(rows)y+=rows*rowStep+38;
  }
  const height=y+15,width=x+16,root={x:10,y:height/2-45,width:97,height:90};
  const byId=Object.fromEntries(items.map(item=>[item.node.id,item]));
  const paths:MapPath[]=[];
  for(const route of routes){
    const nodes=[...route.nodes].sort((a,b)=>a.date.localeCompare(b.date));
    nodes.forEach((node,i)=>{const previous=nodes[i-1];paths.push({id:'time-'+node.id,from:previous?.id||'',to:node.id,path:connect(previous?byId[previous.id].rect:root,byId[node.id].rect),evidence:false});});
  }
  for(const edge of catalog.relations){
    if(byId[edge.from_node]&&byId[edge.to_node])paths.push({id:edge.id,from:edge.from_node,to:edge.to_node,path:connect(byId[edge.from_node].rect,byId[edge.to_node].rect),evidence:true,kind:edge.kind});
  }
  return {track,width,height,root,bands,items:items.sort((a,b)=>a.node.date.localeCompare(b.node.date)||a.node.id.localeCompare(b.node.id)),byId,paths};
}
export const atlasLayouts=Object.fromEntries(catalog.tracks.map(t=>[t.id,buildAtlas(t.id)])) as Record<Track,ReturnType<typeof buildAtlas>>;
export type AtlasViewport={zoom:number;left:number;top:number;mode:'all'|'read'|'manual'};
export function boundedViewport(value:Partial<AtlasViewport>|undefined):AtlasViewport{
  return {zoom:Number.isFinite(value?.zoom)?Math.min(1.5,Math.max(.35,value!.zoom!)):.7,left:Number.isFinite(value?.left)?Math.max(0,value!.left!):0,top:Number.isFinite(value?.top)?Math.max(0,value!.top!):0,mode:value?.mode==='read'||value?.mode==='manual'?value.mode:'all'};
}
