"""Original plots from the reviewed October 2026 Gemini 4 Argon model card."""
from pathlib import Path
import json,hashlib
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
P=Path(__file__).resolve().parents[2];target=P/'frontend/public/report-figures';path=P/'backend/knowledge/content/report-figures.json'
source='https://storage.googleapis.com/deepmind-media/Model-Cards/Gemini-4-Argon-Model-Card.pdf';rights='Graphics © FieldToFit; original data: Google DeepMind model card.'
manifest=json.loads(path.read_text());plt.rcParams.update({'font.family':'DejaVu Sans','font.size':13,'axes.spines.top':False,'axes.spines.right':False,'figure.facecolor':'#f8fafc','axes.facecolor':'#f8fafc','text.color':'#18324d','axes.labelcolor':'#18324d'})
def canvas(title,subtitle):
 f=plt.figure(figsize=(12,7.2),dpi=150);f.text(.06,.94,title,fontsize=23,weight='bold');f.text(.06,.885,subtitle,fontsize=11,color='#4e6378');f.text(.06,.035,'FieldToFit redraw · Gemini 4 Argon model card · October 2026 · not independently reproduced',fontsize=9,color='#4e6378');return f
def save(f,stem,stats):
 p=target/('gemini-argon-202610-'+stem+'.png');f.savefig(p,dpi=150);plt.close(f)
 manifest['/report-figures/'+p.name]={'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'source_urls':[source],'license':rights,'version':'Gemini 4 Argon Model Card · October 2026','origin':'fieldtofit-redraw','statistics':stats}
# Independent rows on the same 0–100 scale; do not average across benchmarks.
models=['Gemini 4 Argon','GPT-6 Astra','Claude Fable 5.1','Claude Opus 5.5']
bench=['Vals Index','FrontierSWE v2','Terminal-Bench 4.0','PostTrainBench']
values=[[68.9,63.1,65.8,67.0],[55.0,65.5,56.3,62.3],[57.4,58.2,57.9,66.4],[45.3,44.3,40.2,49.3]]
f=canvas('Strong in some tasks, behind in others','Four independent benchmark rows · reported scores (%) · different harnesses and data sources')
a=f.add_axes([.24,.24,.70,.58]);colors=['#3567ba','#8197bd','#38a092','#b58a5f']
for j,m in enumerate(models):
 y=[i+(j-1.5)*.18 for i in range(4)];a.barh(y,[v[j] for v in values],height=.16,label=m,color=colors[j])
 for pos,v in zip(y,[v[j] for v in values]):a.text(v+.6,pos,f'{v:.1f}',va='center',fontsize=9)
a.set_yticks(range(4),bench);a.invert_yaxis();a.set_xlim(0,100);a.set_xlabel('Reported score (%)');a.grid(axis='x',alpha=.15);a.set_axisbelow(True);a.legend(loc='upper center',bbox_to_anchor=(.5,-.20),ncol=2,fontsize=10,frameon=False)
save(f,'tasks',{'models':models,'benchmarks':bench,'scores_percent':values,'locator':'physical p6 / printed p5','notes':'Independent rows; provider/public-leaderboard results except shared PostTrainBench configuration. No aggregate ranking.'})
f=canvas('Long context: capacity is not a recall guarantee','GraphWalks BFS F1 · different subsets, not repeated tests of the same questions')
a=f.add_axes([.1,.28,.82,.53]);a.bar([0,1],[99.7,84.2],color=['#3567ba','#38a092'],width=.5)
for x,v in enumerate([99.7,84.2]):a.text(x,v+1.5,str(v)+'%',ha='center',fontsize=18,weight='bold')
a.set_ylim(0,110);a.set_yticks([0,20,40,60,80,100]);a.set_ylabel('BFS F1 (%)');a.set_xticks([0,1],['Up to 128K tokens\n650 items','256K to 1M tokens\n200 problems']);a.grid(axis='y',alpha=.15);a.set_axisbelow(True)
f.text(.06,.15,'1M is the combined input/output capacity; the two subsets do not estimate failure probability.',fontsize=11)
save(f,'context',{'gemini_bfs_f1_percent':[99.7,84.2],'subsets':['up to 128K','256K to 1M'],'sample_sizes':[650,200],'locator':'card physical p6; methods physical p3','scope':'Different subsets; capacity is combined input/output, not unlimited memory.'})
f=canvas('Safety changes use percentage points, not risk rates','Gemini 4 Argon minus Gemini 3.1 Pro · internal automated evaluations · original metric directions')
a=f.add_axes([.29,.24,.63,.59]);names=['Text safety (lower better)','Multilingual (lower better)','Image-to-text (lower better)','Refusal tone (higher better)','Unjustified refusal (lower better)'];deltas=[1.57,-3.16,-9.29,5.5,-9.6]
a.barh(range(5),deltas,color=['#bb8262','#38a092','#38a092','#38a092','#38a092']);a.axvline(0,color='#5b6c81',lw=1);a.set_xlim(-12,8);a.set_yticks(range(5),names);a.invert_yaxis();a.set_xlabel('Change (percentage points)');a.grid(axis='x',alpha=.15);a.set_axisbelow(True)
for y,v in enumerate(deltas):a.text(v+(.25 if v>=0 else -.25),y,f'{v:+.2f} pp',ha='left' if v>=0 else 'right',va='center',fontsize=11)
f.text(.06,.13,'Text safety is described as similar within confidence intervals; revised tests limit cross-card comparison.',fontsize=10)
save(f,'safety',{'baseline':'Gemini 3.1 Pro','metrics':names,'deltas_percentage_points':deltas,'lower_is_better':[True,True,True,False,True],'locator':'physical p10 / printed p9','scope':'Internal automated changes, not deployment incident rates. Raw directions retained.'})
path.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
print('Rendered three original PNG figures with source facts and hashes.')
