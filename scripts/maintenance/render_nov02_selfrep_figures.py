"""Independent evidence redraws for the 2026-10-12 Anthropic replication study."""
from pathlib import Path
import argparse
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
p=argparse.ArgumentParser();p.add_argument('--output',default='frontend/public/report-figures');args=p.parse_args();dest=Path(args.output);dest.mkdir(parents=True,exist_ok=True)
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':14,'axes.spines.top':False,'axes.spines.right':False,'axes.facecolor':'#fcfbf7','figure.facecolor':'#fcfbf7','axes.titleweight':'bold','axes.labelcolor':'#233c39','text.color':'#233c39'})
green='#39796d';soft='#adc7bc'
def new(title):
 f=plt.figure(figsize=(14,8),dpi=120);f.suptitle(title,fontsize=22,fontweight='bold',y=.94);return f
def finish(f,name,note):
 f.text(.055,.045,'FieldToFit independent redraw | '+note,fontsize=11,color='#536573');f.savefig(dest/('nov02-selfrep-'+name+'.png'),dpi=120);plt.close(f)
f=new('Controlled replication: keep the trial denominator');a=f.add_axes([.24,.27,.68,.53]);labels=['Qwen3.5-9B','Gemma4-26B-A4B','Qwen3-Coder-Next','GLM-5.2'];counts=[0,0,0,4];totals=[5,6,5,5];a.barh(range(4),[100*c/n for c,n in zip(counts,totals)],color=[soft,soft,soft,green],height=.55);a.set_yticks(range(4),labels);a.invert_yaxis();a.set_xlim(0,105);a.set_xlabel('Trials reaching all 8 serving nodes (%)');a.grid(axis='x',alpha=.17);a.set_axisbelow(True)
for y,(c,n) in enumerate(zip(counts,totals)):a.text(100*c/n+2,y,f'{c}/{n} trials',va='center',fontweight='bold')
f.text(.24,.15,'Same Llama3.1-8B payload; simplified access; controller served separately.\nThe remaining GLM-5.2 trial reached 7/8 nodes.',fontsize=14)
finish(f,'controlled','Section B / artifact07. Not a device vulnerability rate or an open-internet experiment.')
f=new('Inherited notes: gains are not monotonic');a=f.add_axes([.12,.28,.81,.52]);n=np.array([20,18,18,19,19,17]);k=np.array([9,13,11,12,16,11]);v=100*k/n;lo=np.array([26,49,39,41,62,41]);hi=np.array([66,88,80,81,94,83]);a.errorbar(range(1,7),v,yerr=[v-lo,hi-v],color=green,marker='o',markersize=9,linewidth=2,capsize=6);a.set_ylim(0,105);a.set_xticks(range(1,7));a.set_xlabel('Generation');a.set_ylabel('Inference setup success (%)');a.grid(alpha=.18)
for x,y,num,den in zip(range(1,7),v,k,n):a.annotate(f'{num}/{den}',(x,y),xytext=(7,-19),textcoords='offset points',fontsize=13,fontweight='bold')
f.text(.12,.10,'Qwen3.5-9B | Workspace + notes inherited; model weights are not updated.\nError bars: original Wilson 95% intervals, rounded to whole percentage points.',fontsize=13)
finish(f,'notes','Section D / artifact10. Changing denominators are retained; no fixed per-generation gain is implied.')
f=new('Context budget changes estimated inference throughput');ctx=[256,512,1024,2048,4096,8192,16384,32768];pref=[8,7.2,6,4.45,2.95,1.76,.97,.51];dec=[.34,.31,.28,.22,.155,.116,.063,.033]
for j,(vals,title) in enumerate([(pref,'Prefill'),(dec,'Decode')]):
 a=f.add_axes([.10+j*.47,.29,.37,.50]);a.plot(ctx,vals,'o-',color=green,linewidth=2);a.set_xscale('log',base=2);a.set_xticks([256,1024,4096,16384,32768],['256','1k','4k','16k','32k']);a.set_xlabel('Context length (tokens)');a.set_ylabel('Estimated throughput (token/s)');a.set_title(title);a.grid(alpha=.18);a.annotate(str(vals[-1]),(ctx[-1],vals[-1]),xytext=(-30,12),textcoords='offset points',fontweight='bold')
f.text(.10,.10,'Separate y-axes for different inference phases. These are estimates from the published artifacts,\nnot a new measurement of the physical demonstration and not a replication-cycle speed.',fontsize=13)
finish(f,'context','Appendix C / artifacts14-15. Runtime, context and aggregation conventions matter.')
