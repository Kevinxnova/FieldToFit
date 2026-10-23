import preview from '../../../../backend/llm_evolution/home_preview.json';
import {catalog,nodeById,type Track,type Copy} from './data';

// Presentation-only selection. Facts and relations always come from the shared catalog.
export const homePreview = preview;
export const homeDefinitions:Record<Track,Copy> = {
  train:['通过数据、目标与优化，形成和改变模型能力。','Learn and change model capabilities through data, objectives and optimization.'],
  inference:['组织生成、搜索与工具调用，使用已有模型能力。','Use model capabilities through generation, search and tools.'],
  systems:['组织计算、存储与通信，让训练和推理高效运行。','Organize compute, memory and communication for efficient training and serving.'],
};
export function homeLayout(track:Track,zh:boolean,boardWidth=840) {
  const columnWidth=boardWidth/6,nodeWidth=columnWidth-14;
  const nodeHeight=nodeWidth<118?(zh?102:136):(zh?84:108),width=boardWidth,height=nodeHeight*2+30;
  const items=preview[track].map(item=>({
    ...nodeById[item.id],id:item.id,x:6+item.column*columnWidth,
    y:item.row==='top'?8:item.row==='bottom'?nodeHeight+22:nodeHeight/2+15,
    width:nodeWidth,height:nodeHeight,
  }));
  const positions=Object.fromEntries(items.map(item=>[item.id,item]));
  const paths=catalog.relations.filter(e=>positions[e.from_node]&&positions[e.to_node]).map(relation=>{
    const a=positions[relation.from_node],b=positions[relation.to_node];
    const x1=a.x+a.width,y1=a.y+a.height/2,x2=b.x,y2=b.y+b.height/2;
    return {relation,d:`M${x1},${y1} C${x1+14},${y1} ${x2-14},${y2} ${x2},${y2}`};
  });
  return {items,paths,width,height};
}
