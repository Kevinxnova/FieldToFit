"""Rebuild three original reading figures from verified OpenAI October facts.

Requires matplotlib only for this offline authoring step. No upstream graphic
design is copied, no missing confidence interval or sample count is inferred.
"""
from pathlib import Path
import hashlib,json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
import numpy as np

ROOT=Path(__file__).resolve().parents[2]
DEST=ROOT/'frontend/public/report-figures'
MANIFEST=ROOT/'backend/knowledge/content/report-figures.json'
URL='https://deploymentsafety.openai.com/gpt-6-october'
RIGHTS='Graphics © FieldToFit; source facts: OpenAI, GPT-6 Sol and GPT-6 Luna: October 2026 update, 2026-10-07.'
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':15,'axes.spines.top':False,'axes.spines.right':False,'axes.labelcolor':'#263e43','text.color':'#203b40','axes.edgecolor':'#9caeac','xtick.color':'#3b555b','ytick.color':'#3b555b'})

def base(title,subtitle):
    fig=plt.figure(figsize=(15,9),dpi=120,facecolor='#f7faf7')
    fig.text(.055,.93,title,fontsize=25,weight='bold')
    fig.text(.055,.879,subtitle,fontsize=13,color='#52686b')
    fig.text(.055,.045,'FieldToFit redraw | OpenAI, 2026-10-07 | Vendor results; not independently reproduced',fontsize=11,color='#52686b')
    return fig

def save(fig,stem,stats):
    DEST.mkdir(parents=True,exist_ok=True)
    path=DEST/('gpt6-oct2026-'+stem+'.png');fig.savefig(path,dpi=120);plt.close(fig)
    data=json.loads(MANIFEST.read_text())
    data['/report-figures/'+path.name]={'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'source_urls':[URL],'license':RIGHTS,'version':'October 2026 update; unnumbered','origin':'fieldtofit-redraw','statistics':stats}
    MANIFEST.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')

fig=base('One model name, two release months','Product mapping at report publication; this is not a live version inventory.')
ax=fig.add_axes([.055,.17,.89,.63]);ax.set_xlim(0,1);ax.set_ylim(0,1);ax.axis('off')
for x,label,month,body in [(.025,'ChatGPT','October 2026','GPT-6 Sol / GPT-6 Luna\nThe versions evaluated in this update'),(.525,'Codex / ChatGPT Work','September 2026','Previously released versions\nDo not transfer October results automatically')]:
    ax.add_patch(FancyBboxPatch((x,.32),.45,.57,boxstyle='round,pad=0.018',facecolor='#e6eeea',edgecolor='#b0c5bc'))
    ax.text(x+.035,.78,label,fontsize=22,weight='bold');ax.text(x+.035,.64,month,fontsize=27,color='#28715d',weight='bold')
    ax.text(x+.035,.48,body,fontsize=14,linespacing=1.8,va='top')
ax.text(.025,.14,'Safety tests: lowest deployed reasoning settings     |     Capability tests: maximum reasoning effort',fontsize=14)
ax.text(.025,.04,'Comparison values can reflect later versions of older models. Read within-card comparisons first.',fontsize=13,color='#52686b')
save(fig,'versions',{'scope':'Factual schematic at 2026-10-07 report publication, not a current deployment assertion','products':{'ChatGPT':'October','Codex / Work':'September'},'locator':'Introduction'})

names=['GPT-5.6 Sol\nAugust','GPT-6 Sol\nOctober','GPT-5.6 Luna\nAugust','GPT-6 Luna\nOctober']
raw=[56.6,62.2,46.8,57.8];adjusted=[54.0,55.2,44.1,48.2];characters=[2894,4360,2920,5289]
fig=base('HealthBench Professional: keep all three numbers','Table 5 | Scores: 0–100, higher is better. Mean visible length is in characters, not tokens.')
ax=fig.add_axes([.08,.27,.86,.52],facecolor='#f7faf7');x=np.arange(4);width=.34
for positions,values,color,label in [(x-width/2,raw,'#a6bbb4','Raw score'),(x+width/2,adjusted,'#28715d','Length-adjusted score')]:
    bars=ax.bar(positions,values,width,color=color,label=label)
    ax.bar_label(bars,labels=[str(v) for v in values],padding=5,fontsize=14)
ax.set_ylim(0,100);ax.set_ylabel('Score (points)');ax.set_xticks(x,names);ax.grid(axis='y',alpha=.15);ax.set_axisbelow(True);ax.legend(loc='upper left',frameon=False,ncol=2)
for i,value in enumerate(characters):ax.text(i,-.20,f'Mean length: {value:,} characters',ha='center',va='top',fontsize=12,transform=ax.get_xaxis_transform())
fig.text(.08,.095,'No adjustment at 2,000 characters; Professional: 1.47 points per additional 500 characters.\nThe source reports per-response adjustment; this redraw does not reconstruct individual responses.',fontsize=11,color='#52686b',linespacing=1.5)
save(fig,'healthbench',{'locator':'Table 5, HealthBench Professional','raw_score':raw,'length_adjusted_score':adjusted,'mean_visible_response_characters':characters,'score_scale':[0,100],'scope':'Vendor benchmark, not clinical outcomes; no inferred task counts or confidence intervals'})

values=[34,28,27,15.9]
fig=base('Respecting Warnings: successful circumvention','Figure 5 text | Conditional failure rate (%), lower is better; maximum reasoning effort.')
ax=fig.add_axes([.08,.28,.86,.51],facecolor='#f7faf7');bars=ax.bar(np.arange(4),values,color=['#a6bbb4','#28715d','#a6bbb4','#28715d'],width=.6)
ax.bar_label(bars,labels=[f'{v}%' for v in values],padding=8,fontsize=17);ax.set_ylim(0,100);ax.set_ylabel('Conditional failure rate (%)');ax.set_xticks(np.arange(4),names);ax.grid(axis='y',alpha=.15);ax.set_axisbelow(True)
fig.text(.08,.13,'Simulated, primarily low-stakes environments without system-level safeguards.\nThe metric tracks successful circumvention, not just attempts; these are not everyday violation rates.',fontsize=13,color='#52686b',linespacing=1.6)
save(fig,'warnings',{'locator':'Respecting Warnings; Figure 5 text','conditional_failure_percent':values,'scale':[0,100],'reasoning':'maximum','scope':'Simulated primarily low-stakes tasks, without system-level safeguards; point estimates only, no inferred sample sizes or confidence intervals'})
print('Rendered and registered three verified-fact figures; no upstream graphic design copied.')
