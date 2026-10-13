// Small, bounded flow field for pointer trails on the sphere.
export function createSphereFlow() {
  const w=128,h=64,N=w*h;
  const fluid={w,h,u:new Float32Array(N),v:new Float32Array(N),nextU:new Float32Array(N),nextV:new Float32Array(N),d:new Float32Array(N),nextD:new Float32Array(N),p:new Float32Array(N),nextP:new Float32Array(N),div:new Float32Array(N),curl:new Float32Array(N),pixels:new Uint8Array(N*4)};
  function sample(a: Float32Array,x: number,y: number){const w=fluid.w,h=fluid.h;x=((x%w)+w)%w;y=Math.max(0,Math.min(h-1.001,y));const x0=Math.floor(x),y0=Math.floor(y),dx=x-x0,dy=y-y0,x1=(x0+1)%w,y1=Math.min(y0+1,h-1);return (a[y0*w+x0]*(1.-dx)+a[y0*w+x1]*dx)*(1.-dy)+(a[y1*w+x0]*(1.-dx)+a[y1*w+x1]*dx)*dy;}
  function splat(u: number,v: number,dx: number,dy: number){const w=fluid.w,h=fluid.h;const cx=u*w,cy=v*h;for(let oy=-5;oy<=5;oy++)for(let ox=-5;ox<=5;ox++){const y=Math.round(cy)+oy;if(y<1||y>=h-1)continue;const x=((Math.round(cx)+ox)%w+w)%w,i=y*w+x,k=Math.exp(-(ox*ox+oy*oy)/9.);fluid.u[i]=Math.max(-55,Math.min(55,fluid.u[i]+dx*k));fluid.v[i]=Math.max(-55,Math.min(55,fluid.v[i]+dy*k));fluid.d[i]=Math.min(3.,fluid.d[i]+k*.48);}}
  function step(dt: number){const f=fluid,w=f.w,h=f.h;
    for(let y=1;y<h-1;y++)for(let x=0;x<w;x++){const i=y*w+x,L=y*w+(x+w-1)%w,R=y*w+(x+1)%w;f.curl[i]=(f.v[R]-f.v[L]-f.u[i+w]+f.u[i-w])*.5;}
    for(let y=1;y<h-1;y++)for(let x=0;x<w;x++){const i=y*w+x,L=y*w+(x+w-1)%w,R=y*w+(x+1)%w;let cx=(Math.abs(f.curl[R])-Math.abs(f.curl[L]))*.5,cy=(Math.abs(f.curl[i+w])-Math.abs(f.curl[i-w]))*.5;const len=Math.hypot(cx,cy)+.0001;cx/=len;cy/=len;f.u[i]+=cy*f.curl[i]*dt*8.;f.v[i]-=cx*f.curl[i]*dt*8.;}
    for(let y=0;y<h;y++)for(let x=0;x<w;x++){const i=y*w+x,px=x-f.u[i]*dt,py=y-f.v[i]*dt;f.nextU[i]=sample(f.u,px,py)*Math.exp(-dt*.55);f.nextV[i]=sample(f.v,px,py)*Math.exp(-dt*.55);}
    [f.u,f.nextU]=[f.nextU,f.u];[f.v,f.nextV]=[f.nextV,f.v];f.p.fill(0);
    for(let y=1;y<h-1;y++)for(let x=0;x<w;x++){const i=y*w+x,L=y*w+(x+w-1)%w,R=y*w+(x+1)%w;f.div[i]=.5*(f.u[R]-f.u[L]+f.v[i+w]-f.v[i-w]);}
    for(let a=0;a<7;a++){for(let y=1;y<h-1;y++)for(let x=0;x<w;x++){const i=y*w+x,L=y*w+(x+w-1)%w,R=y*w+(x+1)%w;f.nextP[i]=(f.p[L]+f.p[R]+f.p[i-w]+f.p[i+w]-f.div[i])*.25;}[f.p,f.nextP]=[f.nextP,f.p];}
    for(let y=1;y<h-1;y++)for(let x=0;x<w;x++){const i=y*w+x,L=y*w+(x+w-1)%w,R=y*w+(x+1)%w;f.u[i]-=(f.p[R]-f.p[L])*.5;f.v[i]-=(f.p[i+w]-f.p[i-w])*.5;}
    for(let y=0;y<h;y++)for(let x=0;x<w;x++){const i=y*w+x;f.nextD[i]=Math.max(0,sample(f.d,x-f.u[i]*dt,y-f.v[i]*dt)*Math.exp(-dt*.75));}
    [f.d,f.nextD]=[f.nextD,f.d];for(let i=0;i<N;i++){f.pixels[i*4]=Math.round(255*(f.d[i]/(1.+f.d[i])));f.pixels[i*4+3]=255;}

  }
  return {splat,step,pixels:fluid.pixels,width:fluid.w,height:fluid.h};
}
