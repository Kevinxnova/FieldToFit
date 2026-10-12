"""Original figures for the owner-selected MiMo-V2.6 report.

Numerical endpoints are reported in §§4.1 / 5.4, not digitized or interpolated.
Qualitative workflows have no quantitative scale. Upstream graphics are not copied.
"""
import hashlib,json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch,FancyArrowPatch
ROOT=Path(__file__).resolve().parents[2]
URL='https://arxiv.org/html/2610.11959v1'
RIGHTS='图形 © FieldToFit；公开数据与方法归属 Xiaomi LLM-Core，见原报告'
COLORS=['#91a9cf','#265ab9'];BG='#f5f7fb';INK='#162642';MUTED='#52637a'
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':15,'text.color':INK,'axes.labelcolor':INK,'xtick.color':MUTED,'ytick.color':MUTED,'axes.spines.top':False,'axes.spines.right':False,'axes.spines.left':False,'axes.spines.bottom':False})
def page(title,sub,size=(12,7)):
 fig=plt.figure(figsize=size,facecolor=BG)
 fig.text(.06,.93,title,size=22,weight='bold');fig.text(.06,.867,sub,size=13,color=MUTED)
 fig.text(.06,.042,'FieldToFit original redraw / schematic · Xiaomi LLM-Core · arXiv 2610.11959 v1',size=10,color=MUTED)
 return fig
manifest_path=ROOT/'backend/knowledge/content/report-figures.json';manifest=json.loads(manifest_path.read_text())
def save(fig,name,stats):
 target=ROOT/'frontend/public/report-figures'/('mimo-v26-'+name+'.png');fig.savefig(target,dpi=150,facecolor=BG);plt.close(fig)
 manifest['/report-figures/'+target.name]={'sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'source_urls':[URL],'license':RIGHTS,'version':'arXiv 2610.11959 v1','origin':'fieldtofit-redraw','statistics':stats}
fig=page('RL progress: reported training-curve endpoints','DeepSWE v1.1 · avg@3 · endpoints only; no interpolated learning curve')
ax=fig.add_axes([.10,.20,.84,.59],facecolor=BG);xs=[0,1];a=ax.bar([x-.17 for x in xs],[58.4,48.7],width=.32,color=COLORS[0],label='Start of reported RL curve');b=ax.bar([x+.17 for x in xs],[72.6,65.7],width=.32,color=COLORS[1],label='End of reported RL curve')
ax.set_ylim(0,100);ax.set_ylabel('Score (0–100)');ax.set_xticks(xs,['MiMo-V2.6-Pro','MiMo-V2.6-Flash']);ax.set_yticks([0,25,50,75,100]);ax.grid(axis='y',alpha=.15);ax.set_axisbelow(True);ax.bar_label(a,fmt='%.1f',padding=5);ax.bar_label(b,fmt='%.1f',padding=5);ax.legend(loc='upper left',frameon=False,fontsize=12)
fig.text(.1,.115,'Source: §4.1 / Figure 3. These are not the final checkpoints in Table 3.',size=12,color=MUTED)
save(fig,'training',{'kind':'reported score endpoints','metric':'DeepSWE v1.1 avg@3','unit':'score on 0–100 scale','pro':[58.4,72.6],'flash':[48.7,65.7],'locator':'§4.1; Figure 3','interpolation':False})
def box(ax,rect,title,body,color='#e7edf8'):
 x,y,w,h=rect;ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle='round,pad=0.008,rounding_size=0.02',facecolor=color,edgecolor='#c7d3e6'))
 ax.text(x+.025,y+h-.065,title,fontsize=15,weight='bold',va='top');ax.text(x+.025,y+h-.135,body,fontsize=12,va='top',linespacing=1.5)
def arrow(ax,a,b):ax.add_patch(FancyArrowPatch(a,b,arrowstyle='-|>',mutation_scale=15,color='#6482b4',lw=1.8))
fig=page('Passing tests can still leave quality differences','GRS and GAR apply to different code-task subsets · qualitative workflow',size=(12,8));ax=fig.add_axes([.05,.16,.9,.65]);ax.set_xlim(-.012,1.012);ax.set_ylim(0,1);ax.axis('off')
box(ax,(.0,.57,.3,.33),'GRS · offline','Compare task trajectories\nBuild solution + behavior rubrics')
box(ax,(.35,.57,.3,.33),'Per-rollout assessment','Inspect implementation\nand execution evidence')
box(ax,(.70,.57,.28,.33),'Synthesized reward','Test reward ×\nsolution × behavior scores')
arrow(ax,(.305,.73),(.345,.73));arrow(ax,(.655,.73),(.695,.73))
box(ax,(.0,.10,.3,.33),'GAR · online','Compare successful and\nfailed attempts in one group',color='#e5f2ef')
box(ax,(.35,.10,.3,.33),'Inspect and correct','Repository + targeted tests\nConfirmed hacks → reward zero',color='#e5f2ef')
box(ax,(.70,.10,.28,.33),'Redistribute advantage','Rank passing solutions\nShift positive advantage',color='#e5f2ef')
arrow(ax,(.305,.27),(.345,.27));arrow(ax,(.655,.27),(.695,.27))
fig.text(.06,.105,'Source: §4.3 / Figure 7. Box size does not represent cost, frequency or performance.',size=11,color=MUTED)
save(fig,'grading',{'kind':'qualitative method diagram','locator':'§4.3.1–4.3.2; Figure 7','numerical_effect_sizes':None})
fig=page('Router drift: three separate expert-load measures','Trainable router · Pro layer 9 · 384 experts · first 20 RL steps',size=(12,7))
for n,(title,unit,values,limit) in enumerate([('Load CV','Coefficient of variation',[.78,2.0],2.5),('Peak / mean','Load ratio',[6,16],20),('Cold experts','Percent below 0.1 × mean',[.5,22],30)]):
 ax=fig.add_axes([.085+n*.31,.22,.24,.53],facecolor=BG);bars=ax.bar([0,1],values,width=.57,color=COLORS);ax.set_ylim(0,limit);ax.set_title(title,fontsize=17,pad=22);ax.set_ylabel(unit,fontsize=11);ax.set_xticks([0,1],['Initial','Step 20'],fontsize=12);ax.grid(axis='y',alpha=.15);ax.set_axisbelow(True)
 for bar,val in zip(bars,values):ax.text(bar.get_x()+bar.get_width()/2,val+limit*.035,str(val)+'%' if n==2 else str(val),ha='center',fontsize=14)
fig.text(.07,.11,'Source: §5.4 / Figure 11. Separate units; do not multiply these measures.',size=12,color=MUTED)
save(fig,'router',{'kind':'reported load endpoints','layer':9,'experts':384,'steps':20,'CV':[.78,2.0],'peak_mean_ratio':[6,16],'cold_percent':[.5,22],'cold_definition':'load below 0.1 times mean','locator':'§5.4; Figure 11'})
fig=page('MOPD2: students generate; teachers supervise','Mixed RL precedes distillation · qualitative workflow; no effect-size scale',size=(12,8));ax=fig.add_axes([.05,.16,.9,.65]);ax.set_xlim(-.012,1.012);ax.set_ylim(0,1);ax.axis('off')
for y,title,body in [(.70,'Standard MOPD','Student interaction history'),(.39,'Teacher-Prefix OPD','History from a teacher trajectory'),(.08,'SFT-Prefix OPD','Fixed demonstration history')]:
 box(ax,(.0,y,.34,.23),title,body,color='#e7edf8');box(ax,(.40,y,.24,.23),'Student generation',('Autonomous rollout' if title=='Standard MOPD' else 'Next turn / continuation'),color='#e5f2ef');box(ax,(.70,y,.28,.23),'Domain teacher','Same history +\ngenerated student tokens')
 arrow(ax,(.345,y+.11),(.395,y+.11));arrow(ax,(.645,y+.11),(.695,y+.11))
fig.text(.06,.102,'Source: §5.6 / Figure 13. Prefixes supply history, not a fixed target response.',size=12,color=MUTED)
save(fig,'mopd2',{'kind':'qualitative distillation diagram','locator':'§5.6; Figure 13','numerical_effect_sizes':None})
manifest_path.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
print('Four original static PNGs registered with hashes and source definitions')
