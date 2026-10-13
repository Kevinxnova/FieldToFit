// FieldToFit sphere rendering. Scene coordinates match the credited reference textures.
export const vertex = `#version 300 es
  in vec2 aPosition;void main(){gl_Position=vec4(aPosition,0.,1.);}`;

export const fragment = `#version 300 es
  precision highp float;
  uniform sampler2D bg;uniform sampler2D planet;uniform sampler2D geometry;uniform sampler2D dye;
  uniform vec2 resolution;uniform vec3 frame;uniform float seconds;uniform float pulses[3];uniform vec3 brushes[24];
  out vec4 result;
  const float PI=3.14159265;
  vec3 linear(vec3 c){return pow(max(c,vec3(0.)),vec3(2.2));}
  vec3 image(vec2 p){return linear(texture(bg,clamp(vec2(abs(p.x),p.y)/vec2(1672.,941.),vec2(0.),vec2(1.))).rgb);}
  float hash(vec2 p){return fract(sin(dot(p,vec2(127.1,311.7)))*43758.5453);}
  vec3 turn(vec3 n){float a=.41;vec3 k=vec3(n.x*cos(a)+n.y*sin(a),-n.x*sin(a)+n.y*cos(a),n.z);float b=seconds*.0314159;return vec3(k.x*cos(b)+k.z*sin(b),k.y,-k.x*sin(b)+k.z*cos(b));}
  void main(){
    vec2 px=vec2(gl_FragCoord.x,resolution.y-gl_FragCoord.y);vec2 p=(px-frame.yz)/frame.x;
    vec2 uv=p/vec2(1672.,941.);float sky=1.-smoothstep(290.,352.,p.y);
    vec3 col=image(p+vec2(sin(seconds*.07+uv.y*7.)*2.0*sky,0.));
    vec4 geo=texture(geometry,clamp(uv,0.,1.));
    float bright=dot(col,vec3(.2,.65,.15));
    float flicker=sin(seconds*(.4+hash(floor(p/5.)))+hash(floor(p/5.))*60.);
    col*=1.+.035*flicker*smoothstep(.25,.8,bright)*(1.-sky);
    float surge=0.;
    for(int i=0;i<3;i++){float a=pulses[i];if(a>=0.){surge+=exp(-a*3.8)*min(a*15.,1.);float d=length(vec2(p.x-829.,(p.y-772.)*3.3));float ring=exp(-pow((d-max(a-.2,0.)*500.)/19.,2.))*exp(-a*.9)*step(.2,a);col+=vec3(.60,.82,.86)*ring*.9*(.5+geo.a*.5);}}
    float heat=0.;for(int i=0;i<24;i++){vec3 b=brushes[i];if(b.z>0.){vec2 delta=(p-b.xy)/vec2(32.,24.);heat+=exp(-dot(delta,delta))*b.z;}}
    col+=vec3(.65,.22,.06)*heat*.25*(1.-sky);
    float beamY=clamp((772.-p.y)/143.,0.,1.), width=mix(21.,105.,beamY);
    float beamMask=(1.-smoothstep(768.,789.,p.y))*smoothstep(620.,653.,p.y);
    float shafts=.7+.3*sin((p.x-829.)*.2+seconds*.5+beamY*10.);
    float beam=exp(-pow((p.x-829.)/width,2.)*3.)*beamMask*(.21+.19*(1.-beamY))*shafts;
    col+=vec3(1.5,1.12,.75)*beam*(1.+surge*2.4);
    vec2 base=vec2((p.x-829.)/69.,(p.y-772.)/16.);float baseR=length(base);
    col+=vec3(1.,.83,.58)*(exp(-baseR*baseR*1.7)*.7+exp(-pow((baseR-.8)/.12,2.))*.32)*(1.+surge*2.);
    vec2 q=(p-vec2(830.7,449.3))/209.7;float r=length(q);float edge=fwidth(r)*1.4;
    vec3 rimColor=mix(vec3(.55,.72,.90),vec3(1.,.76,.47),(1.-smoothstep(-.7,.45,q.x)));
    col+=rimColor*exp(-max(r-1.,0.)*35.)*.07*step(1.,r);
    if(r<1.+edge){
      float cover=1.-smoothstep(1.-edge,1.+edge,r);vec3 ns=vec3(q.x,-q.y,sqrt(max(0.,1.-r*r)));
      vec2 refractOffset=q*(1.-ns.z)*10.;vec3 glass=image(p-refractOffset)*.78;
      glass.r=image(p-refractOffset*1.24).r*.78;glass.b=image(p-refractOffset*.8).b*.84;
      float core=.895;
      if(r<core){
        vec2 cq=q/core;vec3 n=vec3(cq.x,-cq.y,sqrt(max(0.,1.-dot(cq,cq))));vec3 local=turn(n);
        vec2 ll=vec2(atan(local.x,local.z)/(2.*PI)+.5,asin(clamp(local.y,-1.,1.))/PI+.5);
        vec2 grad=vec2(texture(dye,ll+vec2(.006,0.)).r-texture(dye,ll-vec2(.006,0.)).r,texture(dye,ll+vec2(0.,.01)).r-texture(dye,ll-vec2(0.,.01)).r);
        vec2 warped=ll+grad*.017;
        float row=floor(warped.y*108.);float latitude=((row+.5)/108.-.5)*PI;float columns=max(4.,floor(216.*cos(latitude)));
        vec2 cells=vec2(warped.x*columns,warped.y*108.);float d=length(fract(cells)-.5);float aa=min(.23,fwidth(cells.y)*.6+.02);float led=1.-smoothstep(.22-aa,.26+aa,d);
        float blendDots=smoothstep(.2,.7,fwidth(cells.y));led=mix(led,.19,blendDots);
        vec3 earth=texture(planet,vec2(warped.x,1.-warped.y)).rgb;
        vec3 sunDir=normalize(vec3(-.86,.16,.52));float lit=max(dot(n,sunDir),0.);
        vec3 lighting=mix(vec3(.006,.045,.052),vec3(1.02,.19,.025),smoothstep(.06,.73,lit));
        lighting+=vec3(1.6,.90,.32)*pow(lit,7.);
        lighting+=vec3(.08,.19,.105)*smoothstep(.1,.8,-n.y)*.42;
        vec3 land=mix(vec3(.60,.79,.81),vec3(1.08,1.01,.70),earth.r);
        vec3 luminous=lighting*land*(.34+led*2.4)+lighting*earth.g*.4;
        luminous+=vec3(1.,.54,.13)*earth.b*(1.-lit)*(.3+led*.8)*.25;
        float paint=texture(dye,ll).r;luminous+=vec3(.07,.95,.72)*paint*(.35+led*2.7);
        float highlight=pow(max(dot(reflect(vec3(0.,0.,-1.),n),sunDir),0.),22.);
        luminous+=vec3(1.4,1.13,.76)*highlight*(.35+led*.75);
        luminous=mix(luminous,rimColor*(.32+.4*led),pow(1.-n.z,3.)*.65);
        float clearBottom=smoothstep(.51,.9,-n.y)*.72;
        luminous=mix(luminous,image(p-refractOffset)*.7+lighting*led*.6,clearBottom);
        luminous*=1.+surge*.4;
        glass=mix(glass,luminous,1.-smoothstep(core-edge,core,r));
      }
      glass+=rimColor*pow(1.-ns.z,4.)*(.95+surge*.5);
      col=mix(col,glass,cover);
    }
    vec3 mapped=col/(1.+col*.16);result=vec4(pow(max(mapped,vec3(0.)),vec3(1./2.2)),1.);
  }`;

export const overlayVertex = `#version 300 es
  precision highp float;in vec3 position;uniform vec2 resolution;uniform vec3 frame;uniform float seconds;out vec3 normal;out vec2 design;
  void main(){float angle=-seconds*.0242;vec3 a=vec3(position.x*cos(angle)+position.z*sin(angle),position.y,-position.x*sin(angle)+position.z*cos(angle));vec3 n=vec3(a.x*.917+a.y*.399,-a.x*.399+a.y*.917,a.z);normal=n;design=vec2(830.7+n.x*209.7,449.3-n.y*209.7);vec2 p=design*frame.x+frame.yz;gl_Position=vec4(p.x/resolution.x*2.-1.,1.-p.y/resolution.y*2.,0.,1.);gl_PointSize=max(1.,frame.x*1.4);}`;

export const overlayFragment = `#version 300 es
  precision highp float;in vec3 normal;in vec2 design;out vec4 result;void main(){if(normal.z<0.&&distance(design,vec2(830.7,449.3))<188.)discard;float alpha=(1.-smoothstep(.16,.5,length(gl_PointCoord-.5)))*mix(.2,.6,step(0.,normal.z));vec3 c=mix(vec3(.67,.87,1.),vec3(1.,.86,.67),(1.-smoothstep(-.6,.4,normal.x)));result=vec4(c,alpha);}`;

export const textVertex = `#version 300 es
  precision highp float;in vec2 ribbon;uniform vec2 resolution;uniform vec3 frame;out vec2 tex;out float depth;out vec2 design;
  void main(){float a=ribbon.x*6.2831853;vec3 n=vec3(sin(a)*235.,ribbon.y*43.,cos(a)*235.);float py=n.y*.985-n.z*.169;float z=n.y*.169+n.z*.985;float x=n.x*.929-py*.37;float y=n.x*.37+py*.929;float k=1./(1.-z/1750.);design=vec2(830.7+x*k,449.3-y*k);vec2 p=design*frame.x+frame.yz;gl_Position=vec4(p.x/resolution.x*2.-1.,1.-p.y/resolution.y*2.,0.,1.);tex=vec2(ribbon.x*2.,.5-ribbon.y*.5);depth=z;}`;

export const textFragment = `#version 300 es
  precision highp float;uniform sampler2D letters;uniform float seconds;in vec2 tex;in float depth;in vec2 design;out vec4 result;
  void main(){if(depth<0.&&distance(design,vec2(830.7,449.3))<210.)discard;float alpha=texture(letters,vec2(fract(tex.x-seconds/52.+.05),tex.y)).a;float face=depth<0.?.25:1.;float fade=smoothstep(0.,70.,abs(depth));result=vec4(.32,.94,.86,alpha*face*fade);}`;
