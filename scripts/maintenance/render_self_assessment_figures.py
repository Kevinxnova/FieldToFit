"""Independent diagrams from Anthropic's dated self-assessment results.

No original graphic is copied. Teacher-labelled recall, estimated compute and
24-task adversarial success have separate denominators and conditions.
"""
import json,hashlib
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch,FancyArrowPatch
ROOT=Path(__file__).resolve().parents[2];DEST=ROOT/'frontend/public/report-figures';MANIFEST=ROOT/'backend/knowledge/content/report-figures.json'
URL='https://safeguards.anthropic.com/2026/self-assessment/'
RIGHTS='Graphics © FieldToFit; source facts: Anthropic, Scaling Misuse Detection with Self-Assessment, 2026-10-16. Original report graphics are not reproduced.'
VERSION='2026-10-16; unnumbered official research webpage'
BG='#f8faf6';INK='#172b3a';GREEN='#348371';PURPLE='#8173b5';GRAY='#8e9ca3'
plt.rcParams.update({'font.family':'DejaVu Sans','text.color':INK,'axes.labelcolor':INK,'axes.edgecolor':'#d1dbd7','xtick.color':INK,'ytick.color':INK})
def base(title,subtitle):
 fig=plt.figure(figsize=(14,8),facecolor=BG);fig.text(.055,.92,title,fontsize=24,weight='bold');fig.text(.055,.85,subtitle,fontsize=12,color='#536972');fig.text(.055,.035,'FieldToFit independent redraw | Anthropic, 2026-10-16 | Not independently reproduced',fontsize=10,color='#536972');return fig
def save(fig,stem,stats):
 DEST.mkdir(parents=True,exist_ok=True);p=DEST/('self-assessment-20261016-'+stem+'.png');fig.savefig(p,dpi=120);plt.close(fig);d=json.loads(MANIFEST.read_text());d['/report-figures/'+p.name]={'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'source_urls':[URL],'license':RIGHTS,'version':VERSION,'origin':'fieldtofit-redraw','statistics':stats};MANIFEST.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
f=base('One conversation, a separate offline assessment','Reading diagram, not a measured latency, throughput or probability chart.');a=f.add_axes([.05,.21,.90,.53]);a.set(xlim=(0,1),ylim=(0,1));a.axis('off')
boxes=[(.01,.55,.20,.27,'Conversation\nClaude responds'),(.28,.55,.20,.27,'Cached context\nShort reflection'),(.55,.55,.20,.27,'Structured flag\nCategory + priority'),(.79,.55,.20,.27,'Offline review\nHuman investigation')]
for x,y,w,h,t in boxes:
 a.add_patch(FancyBboxPatch((x,y),w,h,boxstyle='round,pad=0.009',facecolor='#e3efe7',edgecolor=GREEN));a.text(x+w/2,y+h/2,t,ha='center',va='center',fontsize=13,linespacing=1.6)
for x1,x2 in ((.21,.28),(.48,.55),(.75,.79)):a.add_patch(FancyArrowPatch((x1,.68),(x2-.008,.68),arrowstyle='-|>',mutation_scale=15,color=GREEN))
a.text(.02,.25,'Reflection and assessment are not shown to the user and are not carried into later conversation turns.\nA flag is a review signal, not a confirmed policy violation. Other safeguards block requests in real time.',fontsize=13,linespacing=1.8)
f.text(.065,.14,'Author estimate: ~10 additional output tokens on average; <2% additional inference compute.\nEstimated internal compute is not an API price, customer bill, or measured end-to-end latency.',fontsize=12,linespacing=1.8,color='#536972');save(f,'pipeline',{'kind':'reading_diagram','locators':['Method: How self-assessment works','Introduction; footnotes1,2'],'estimated_compute_increase':'<2%','average_additional_tokens':'~10','causal_or_latency_data':False})
f=base('Recall against a teacher, not human ground truth','Claude Fable 5 | Operating point: 1% false-positive rate against teacher labels.');a=f.add_axes([.32,.35,.60,.40],facecolor=BG);a.set_xlim(0,100);a.set_ylim(-.65,1.65);a.set_xlabel('Recall among teacher-flagged conversations (%)');a.grid(axis='x',alpha=.15);a.set_axisbelow(True);a.barh([1,0],[78,94],color=[GREEN,PURPLE],height=.42);a.set_yticks([1,0],['All teacher-flagged\nconversations','High-priority teacher flags\n(priority >= 7)'])
for y,v in ((1,78),(0,94)):a.text(v-3,y,str(v)+'%',va='center',ha='right',color='white',fontsize=20,weight='bold')
f.text(.065,.17,'The two bars have different denominators. High-priority flags are a selected subset.\nProduction sample size, confidence intervals and the full observation window are not supplied.\nDo not merge these results with the separately trained XS / S / M / L scaling experiment.',fontsize=12,linespacing=1.8,color='#536972');save(f,'recall',{'locators':['Results: Self-assessment in Claude Fable5; Figure1'],'operating_point_false_positive_percent':1,'teacher_flagged_recall_percent':78,'priority7plus_teacher_flagged_recall_percent':94,'sample_n':'undisclosed','axes':[0,100],'human_ground_truth':False})
f=base('Blocking an adaptive attacker remains difficult','24 internal offensive cybersecurity tasks | Production classifiers disabled in this experiment.');a=f.add_axes([.36,.35,.56,.40],facecolor=BG);a.set_xlim(0,24);a.set_ylim(-.65,2.65);a.set_xlabel('Tasks with a successful attack (out of 24)');a.set_xticks([0,6,12,18,24]);a.grid(axis='x',alpha=.15);a.set_axisbelow(True);a.barh([2,1,0],[19,13,6],color=[GRAY,PURPLE,GREEN],height=.43);a.set_yticks([2,1,0],['No safeguards (baseline)','Self-assessment as blocker','Standalone prompted classifier'])
for y,v in ((2,19),(1,13),(0,6)):a.text(v+.3,y,str(v)+'/24',va='center',fontsize=18,weight='bold')
f.text(.065,.17,'The attacker can rewind and retry after a blocked turn, receiving feedback about what was detected.\nThis is a controlled adaptive attack test, not an estimate of harm prevalence in production.\nSelf-assessment is deployed as passive offline monitoring, alongside separate real-time safeguards.',fontsize=12,linespacing=1.8,color='#536972');save(f,'attacks',{'locators':['Results: Can self-assessment block attacks?; Figure4'],'task_denominator':24,'successful_tasks':[19,13,6],'production_classifiers_enabled':False,'attacker_can_rewind_and_retry':True,'axes':[0,24],'production_prevalence':False})
print('Rendered three independent self-assessment figures; original graphics not copied.')
