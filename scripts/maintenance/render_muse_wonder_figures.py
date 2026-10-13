"""Rebuild three original graphics from the reviewed Meta model-card facts. Requires matplotlib."""
import json,hashlib
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

P=Path(__file__).resolve().parents[2];TARGET=P/'frontend/public/report-figures';MAN=P/'backend/knowledge/content/report-figures.json'
SOURCE='https://research.meta.ai/static/muse-wonder-model-card'
RIGHTS='Graphics © FieldToFit; original data: Meta model card.'
manifest=json.loads(MAN.read_text())
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':14,'axes.spines.top':False,'axes.spines.right':False,'axes.labelcolor':'#526079','text.color':'#142844','xtick.color':'#526079','ytick.color':'#526079','figure.facecolor':'#f7f9fd','axes.facecolor':'#f7f9fd'})
def canvas(title,subtitle):
 f=plt.figure(figsize=(12,7.2),dpi=150);f.suptitle(title,x=.07,y=.95,ha='left',fontsize=25,fontweight='bold');f.text(.07,.87,subtitle,fontsize=12,color='#526079');f.text(.07,.055,'FieldToFit redraw · Meta Muse Wonder model card · 2026-10-12',fontsize=10,color='#526079');return f
def save(f,stem,stats):
 path=TARGET/('muse-wonder-20261012-'+stem+'.png');f.savefig(path,dpi=150);plt.close(f)
 manifest['/report-figures/'+path.name]={'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'source_urls':[SOURCE],'license':RIGHTS,'version':'Muse Wonder Model Card · 2026-10-12','origin':'fieldtofit-redraw','statistics':stats}

f=canvas('Memory: input capacity and tested recall are different','A scoped reading diagram; box area is not proportional to token count.')
a=f.add_axes([.06,.21,.88,.60]);a.axis('off')
for x,width,color,head,big,lines in [(.02,.43,'#e9effc','MODEL INPUT CAPACITY','1M tokens',['Inference context length','Text, image, video and audio input','Not a recall-success guarantee']),(.53,.43,'#e8f4f1','MEMORYBENCH CONDITIONS','64K–100K tokens',['Multi-turn facts, distractors and updates','LLM judge; weighted task-specific rubrics','Scores: Full 85.5 / Wonder 85.6'])]:
 a.add_patch(FancyBboxPatch((x,.08),width,.78,boxstyle='round,pad=0.018,rounding_size=.025',facecolor=color,edgecolor='#cbd5e3',transform=a.transAxes));a.text(x+.025,.75,head,fontsize=12,weight='bold',transform=a.transAxes);a.text(x+.025,.56,big,fontsize=24,weight='bold',transform=a.transAxes)
 for y,t in zip([.39,.28,.17],lines):a.text(x+.025,y,t,fontsize=11,transform=a.transAxes)
f.text(.07,.14,'No published evidence here establishes unlimited memory, every-language parity, or privacy behavior.',fontsize=11)
save(f,'memory',{'inference_context_tokens':1000000,'memorybench_context_tokens':[64000,100000],'reported_rubric_score_full':85.5,'reported_rubric_score_wonder':85.6,'score_unit':'reported MemoryBench rubric score','kind':'scope diagram; areas carry no numeric meaning','locator':'pp1,3,5'})

f=canvas('OSWorld V2.1: partial reward is not full completion','108 desktop workflows · reported model configurations · score definitions kept separate')
a=f.add_axes([.11,.25,.80,.53]);labels=['Wonder Full (max)','Wonder (max)'];x=[0,1];partial=[78.4,72.6];binary=[39.4,34.3]
a.bar([z-.19 for z in x],partial,width=.34,label='Mean partial reward ×100',color='#4263df');a.bar([z+.19 for z in x],binary,width=.34,label='Strict binary completion (%)',color='#16836d')
for positions,values in [([z-.19 for z in x],partial),([z+.19 for z in x],binary)]:
 for pos,val in zip(positions,values):a.text(pos,val+2,str(val),ha='center',fontsize=15,weight='bold')
a.set_ylim(0,100);a.set_yticks([0,20,40,60,80,100]);a.set_ylabel('Reported score on a 0–100 scale');a.set_xticks(x,labels);a.grid(axis='y',alpha=.16);a.set_axisbelow(True);a.legend(loc='upper right',fontsize=10,frameon=False)
f.text(.07,.15,'The gap is between grading rules, not an independently estimated failure probability.',fontsize=11)
save(f,'workflow',{'benchmark':'OSWorld V2.1','workflows':108,'models':['Muse Wonder Full (max)','Muse Wonder (max)'],'partial_reward_x100':partial,'strict_binary_completion_percent':binary,'locator':'pp3,5','interpretation':'Scores are not interchangeable; do not infer an exact number of completed tasks.'})

f=canvas('ExploitGym: classify the flags before comparing scores','Muse Wonder Full · captured flags, not distinct vulnerabilities or an overall task success rate')
a=f.add_axes([.13,.38,.76,.33]);a.barh([0],[21],height=.5,color='#4263df',label='Intended vulnerability');a.barh([0],[71],left=[21],height=.5,color='#a5b5d5',label='Unintended vulnerabilities');a.text(10.5,0,'21',va='center',ha='center',fontsize=25,color='white',weight='bold');a.text(56.5,0,'71',va='center',ha='center',fontsize=25,color='#142844',weight='bold');a.text(92, .36,'92 total captured flags',ha='right',fontsize=16,weight='bold');a.set_xlim(0,100);a.set_xticks([0,20,40,60,80,100]);a.set_yticks([]);a.set_xlabel('Captured flags (count)');a.spines['left'].set_visible(False);a.legend(loc='upper center',bbox_to_anchor=(.5,-.27),ncol=2,frameon=False,fontsize=11)
f.text(.07,.18,'Only 21 is comparable with the published intended-vulnerability ranking.',fontsize=12,weight='bold')
save(f,'flags',{'captured_flags':92,'intended_vulnerability_flags':21,'unintended_vulnerability_flags':71,'unit':'captured flags','ranking_comparable':21,'locator':'p7, ExploitGym scoring footnote'})
MAN.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
print('Rendered three original figures; source facts and asset hashes registered.')
