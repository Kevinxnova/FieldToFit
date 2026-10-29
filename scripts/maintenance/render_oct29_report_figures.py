"""Independent FieldToFit redraws of Qwen-Image-PE v1 facts and method."""
import json,hashlib
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
ROOT=Path(__file__).resolve().parents[2];DEST=ROOT/'frontend/public/report-figures';MAN=ROOT/'backend/knowledge/content/report-figures.json'
BG='#f8faf6';INK='#172b3a';GREEN='#348371';PURPLE='#8173b5';RIGHTS='Graphics © FieldToFit. Independent redraw of reported facts and method schematic; original artwork is not reproduced.'
URL='https://arxiv.org/html/2610.33472v1';VERSION='arXiv:2610.33472v1'
plt.rcParams.update({'font.family':'DejaVu Sans','text.color':INK,'axes.labelcolor':INK,'xtick.color':INK,'ytick.color':INK})
def base(t,s,loc):
 f=plt.figure(figsize=(14,8),facecolor=BG);f.text(.05,.93,t,fontsize=22,weight='bold');f.text(.05,.865,s,fontsize=12);f.text(.05,.035,'FieldToFit independent redraw | Qwen-Image-PE v1, 2026-10-24 | '+loc+' | Not replicated',fontsize=10);return f
def save(f,stem,loc):
 p=DEST/('oct29-pe-'+stem+'.png');f.savefig(p,dpi=120);plt.close(f);m=json.loads(MAN.read_text());m['/report-figures/'+p.name]={'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'source_urls':[URL],'license':RIGHTS,'attribution':'FieldToFit','source_version':VERSION,'locator':loc};MAN.write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n')
f=base('Teach design, then compare candidate images','Prompt enhancer is trained; text-to-image generator remains frozen','Figure 2; §2')
a=f.add_axes([.05,.20,.9,.57]);a.set_xlim(0,1);a.set_ylim(0,1);a.axis('off')
def box(x,y,w,h,t,col):
 a.add_patch(FancyBboxPatch((x,y),w,h,boxstyle='round,pad=0.015',facecolor=col,edgecolor='#d1dcd5'));a.text(x+w/2,y+h/2,t,ha='center',va='center',fontsize=13,linespacing=1.6)
def arrow(x,y,xx,yy):a.annotate('',xy=(xx,yy),xytext=(x,y),arrowprops={'arrowstyle':'->','color':INK,'lw':1.7})
box(.02,.62,.24,.26,'CRD: good images\nDense captions +\nsynthetic rationales','#e4dff3');box(.38,.62,.24,.26,'SFT enhancer\nRequest -> design,\nprompt, aspect ratio','#d7ebe0');box(.74,.62,.24,.26,'Frozen generator\nRender images\nfrom prompts','#edf1e9');arrow(.27,.75,.36,.75);arrow(.63,.75,.72,.75)
box(.02,.11,.24,.26,'GRPO update\nAlignment reward\n+ KL to SFT','#d7ebe0');box(.38,.11,.24,.26,'GDR: score grids\nLighting / composition\nLayout / detail','#e4dff3');box(.74,.11,.24,.26,'Same request\nCandidate images\nShuffled grids','#edf1e9');arrow(.86,.60,.86,.40);arrow(.73,.24,.64,.24);arrow(.37,.24,.28,.24);arrow(.14,.39,.42,.60)
f.text(.06,.12,'Method schematic: training data flow, not a causal performance estimate.',fontsize=13);save(f,'route','Figure 2; §2')
f=base('Hold the image backbone fixed before comparing scores','Qwen-Image-2.1 | 2K generation | matched per-request seeds | Overall points, higher is better','Tables 1, 3')
for pos,names,vals,title in [([.11,.32,.34,.43],['Original','9B','397B internal'],[54.36,60.28,62.17],'Main comparison (Table 1)'),([.59,.32,.34,.43],['SFT','Pointwise RL','Groupwise RL'],[61.52,61.36,62.17],'397B ablation (Table 3)')]:
 a=f.add_axes(pos);a.bar(range(3),vals,color=[PURPLE,GREEN,GREEN]);a.set_xticks(range(3),names);a.set_ylim(0,70);a.set_title(title,fontsize=14);a.set_ylabel('Overall score (points)')
 for i,v in enumerate(vals):a.text(i,v+1,f'{v:.2f}',ha='center',fontsize=12)
f.text(.06,.17,'+7.81 points is not +7.81%. The two panels are separate comparisons, not one training curve.',fontsize=12);save(f,'scores','Tables 1, 3')
f=base('Low information density can make enhancement worse','Fixed Qwen3.5-9B enhancer and 50K SFT examples | density levels are not prompt word counts','Figure 7(c); §4')
a=f.add_axes([.12,.28,.78,.47]);vals=[44.65,51.36,55.39,57.31];a.bar(range(4),vals,color=[PURPLE,PURPLE,GREEN,GREEN]);a.axhline(54.36,color='#a85e36',ls='--',lw=2,label='Original request: 54.36');a.set_xticks(range(4),['L1','L2','L3','L4']);a.set_ylim(0,66);a.set_ylabel('Overall score (points), higher is better');a.legend(loc='upper left',frameon=False)
for i,v in enumerate(vals):a.text(i,v+1,f'{v:.2f}',ha='center',fontsize=13)
f.text(.06,.15,'GPG measures image-grounded likelihood gains using frozen Qwen3-VL-8B-Instruct.',fontsize=12);f.text(.06,.11,'The result applies to this ablation; it does not establish a universal prompt-length threshold.',fontsize=12);save(f,'density','Figure 7(c); §4')
print('Three factual redraws rendered and registered')
