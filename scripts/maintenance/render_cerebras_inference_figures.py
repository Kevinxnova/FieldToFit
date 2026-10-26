import sys
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
from pathlib import Path
import argparse
p=argparse.ArgumentParser(description='Render independently calculated Cerebras teaching figures');p.add_argument('--output',type=Path,default=Path(__file__).resolve().parents[2]/'frontend/public/report-figures');args=p.parse_args();P=args.output;P.mkdir(parents=True,exist_ok=True);
BG='#f5f6f1';INK='#213438';G='#398776';B='#718bb5'
plt.rcParams.update({'font.family':'DejaVu Sans','text.color':INK,'axes.labelcolor':INK,'xtick.color':INK,'ytick.color':INK})
def base(t,s):
 f=plt.figure(figsize=(14,8),facecolor=BG);f.text(.05,.92,t,fontsize=24,weight='bold');f.text(.05,.85,s,fontsize=13);return f
def save(f,n,foot):
 f.text(.05,.055,foot,fontsize=11);f.savefig(P/('cerebras-20261022-'+n),dpi=140);plt.close(f)
f=base('59 wafers: a placement illustration','Assumed ~3T parameters, all weights at 4 bits, 93 average-sized layers, 44 GB per wafer.')
a=f.add_axes([.18,.3,.72,.42],facecolor=BG);a.barh([1,0],[35,24],color=[G,B],height=.5);a.set_yticks([1,0],['69 KDA layers\n2 per wafer','24 full-attention layers\n1 per wafer']);a.set_xlim(0,42);a.set_xlabel('Wafers in the illustration')
for y,v in [(1,35),(0,24)]:a.text(v+1,y,str(v),va='center',fontsize=24,weight='bold')
f.text(.14,.17,'ceil(69 / 2) + 24 = 59     |     3e12 × 4 / 8 / 93 ≈ 16.13 GB per layer',fontsize=17)
save(f,'wafer.png','FieldToFit redraw | Cerebras, 2026-10-22 | Not a measured deployment or complete memory allocation')
f=base('Longer contexts reduce the KV-only concurrency budget','FieldToFit conditional calculation: N = 28e9 / (576 × context length). Decimal bytes; no overhead.')
a=f.add_axes([.12,.24,.81,.52],facecolor=BG);xs=[128000,256000,512000,1000000];ys=[28e9/(576*x) for x in xs];a.plot(xs,ys,'o-',color=G,lw=3,ms=10);a.set_xticks(xs,['128k','256k','512k','1M']);a.set_ylabel('Theoretical request-equivalent capacity');a.set_xlabel('Context length (tokens)');a.set_ylim(0,440);a.grid(alpha=.2)
for x,y in zip(xs,ys):a.annotate(f'{y:.1f}',(x,y),xytext=(0,15),textcoords='offset points',ha='center',fontsize=17)
save(f,'cache.png','No throughput prediction. Integer capacity and production reserves are lower; 576 bytes is the blog assumption.')
f=base('A pipeline overlaps requests, not one request’s dependencies','Teaching example: three equal-time stages and four requests. Not the actual 59-wafer mapping.')
a=f.add_axes([.12,.27,.81,.46],facecolor=BG);colors=[G,B,'#9a80b2','#c3a06b']
for stage in range(3):
 for req in range(4):
  a.barh(2-stage,.92,left=stage+req,color=colors[req],height=.62);a.text(stage+req+.46,2-stage,chr(65+req),ha='center',va='center',fontsize=22,color='white')
a.set_yticks([2,1,0],['Stage 1','Stage 2','Stage 3']);a.set_xticks([i+.46 for i in range(6)],[str(i+1) for i in range(6)]);a.set_xlabel('Illustrative time step');a.set_xlim(-.1,6)
f.text(.12,.16,'Latency follows the path; steady-state throughput depends on the bottleneck stage and scheduling.',fontsize=14)
save(f,'pipeline.png','FieldToFit original schematic | Multiple requests in flight still require separate state and available capacity.')
print('Three Cerebras explanatory figures generated')
