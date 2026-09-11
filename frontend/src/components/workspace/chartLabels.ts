/** Place names near their measured points; leaders connect displaced labels.
 * Coordinates are never jittered. Greedy rectangles also avoid other data dots.
 */
export type LabelPoint = { id:string; name:string; x:number; y:number };
export type PlacedLabel = LabelPoint & { lx:number; ly:number; width:number };
export function placeLabels(points:LabelPoint[], width:number, height:number):PlacedLabel[] {
  const placed:PlacedLabel[]=[];
  const canvas=document.createElement('canvas');const context=canvas.getContext('2d');
  if(context)context.font='500 14px Arial';
  const occupied=(x:number,y:number,w:number)=>placed.some(p=>x<p.lx+p.width+7&&x+w+7>p.lx&&y<p.ly+19&&y+19>p.ly);
  for(const p of [...points].sort((a,b)=>a.y-b.y||a.x-b.x||a.id.localeCompare(b.id))){
    const w=Math.ceil(context?.measureText(p.name).width??p.name.length*8)+4;
    let best={x:Math.min(width-w-16,p.x+10),y:Math.max(48,p.y-20)},bestCost=Infinity;
    // Closest free position wins; try both sides and progressively wider rings.
    for(let ring=0;ring<45;ring++){
      for(const dy of ring===0?[-20,5]:[-20-ring*20,5+ring*20])for(const dx of [10,-w-10,26,-w-26,80,-w-80]){
        const lx=Math.max(70,Math.min(width-w-16,p.x+dx)),ly=Math.max(48,Math.min(height-100,p.y+dy));
        if(occupied(lx,ly,w))continue;
        const coversDot=points.some(q=>q.x>=lx-5&&q.x<=lx+w+5&&q.y>=ly-5&&q.y<=ly+21);
        const cost=Math.hypot(lx+w/2-p.x,ly+8-p.y)+(coversDot?800:0);
        if(cost<bestCost){best={x:lx,y:ly};bestCost=cost;}
      }
      if(bestCost<ring*20+80)break;
    }
    placed.push({...p,lx:best.x,ly:best.y,width:w});
  }
  return placed;
}
