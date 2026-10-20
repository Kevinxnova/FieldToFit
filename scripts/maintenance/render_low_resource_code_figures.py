"""Redraw OpenAI's reported coding statistics offline, with distinct metrics.

No upstream graphics are copied. Does not run models or reconstruct undisclosed
sample sizes, uncertainty intervals, cost configurations or test subsets.
"""
from pathlib import Path
import json
import hashlib
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT=Path(__file__).resolve().parents[2]
DEST=ROOT/'frontend/public/report-figures'
MANIFEST=ROOT/'backend/knowledge/content/report-figures.json'
URL='https://openai.com/index/low-resource-programming-languages/'
RIGHTS='Graphics © FieldToFit; source facts: OpenAI, Advancing coding in low-resource programming languages, 2026-10-19. Original report graphics are not reproduced.'
VERSION='2026-10-19; unnumbered official web research'
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':14,'axes.spines.top':False,'axes.spines.right':False,'text.color':'#183b3c','axes.labelcolor':'#284c4c','axes.edgecolor':'#b7c7c1','xtick.color':'#42615c','ytick.color':'#284c4c'})
BG='#f7faf7';OLD='#7899ae';NEW='#25765f';MID='#b58f56'
def base(title,subtitle):
 fig=plt.figure(figsize=(15,9),dpi=120,facecolor=BG)
 fig.text(.055,.93,title,fontsize=24,weight='bold')
 fig.text(.055,.875,subtitle,fontsize=13,color='#526b67')
 fig.text(.055,.037,'FieldToFit redraw | OpenAI, 2026-10-19 | Author-reported results; not independently reproduced',fontsize=11,color='#526b67')
 return fig
def axis(fig,rect,title,xmax=100,xlabel='Test pass rate (%)'):
 ax=fig.add_axes(rect,facecolor=BG);ax.set_title(title,loc='left',fontsize=15,weight='bold',pad=18)
 ax.set_xlim(0,xmax);ax.set_xlabel(xlabel,labelpad=12);ax.grid(axis='x',alpha=.15);ax.set_axisbelow(True);ax.tick_params(axis='y',length=0)
 return ax
def save(fig,stem,stats):
 DEST.mkdir(exist_ok=True,parents=True);path=DEST/('low-resource-code-20261019-'+stem+'.png');fig.savefig(path,dpi=120);plt.close(fig)
 data=json.loads(MANIFEST.read_text());data['/report-figures/'+path.name]={'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'source_urls':[URL],'license':RIGHTS,'version':VERSION,'origin':'fieldtofit-redraw','statistics':stats};MANIFEST.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')

fig=base('Building SQLite across programming languages','Maximum reasoning effort | Test pass rates are partial functionality credit, not all-task success.')
ax=axis(fig,[.17,.38,.29,.39],'Mean across 20 languages')
vals=[26.8,40.3,87.4]
ax.barh([2,1,0],vals,color=[OLD,MID,NEW],height=.42)
ax.set_yticks([2,1,0],['GPT-5.6 Sol','GPT-6 Luna','GPT-6 Astra']);ax.set_ylim(-.6,2.6)
for y,v in zip([2,1,0],vals):ax.text(v+1,y,f'{v}%',va='center',fontsize=16,weight='bold')
ax=axis(fig,[.64,.38,.30,.39],'Selected language examples')
langs=['COBOL','OCaml','Fortran','Visual Basic'];old=[10.9,25.6,21.4,27.5];new=[72.1,85.8,83.5,89.4]
for y,a,b in zip([3,2,1,0],old,new):
 ax.barh(y+.16,a,height=.28,color=OLD);ax.barh(y-.16,b,height=.28,color=NEW)
 ax.text(a+1,y+.16,f'{a}',va='center',fontsize=11);ax.text(b+1,y-.16,f'{b}',va='center',fontsize=11)
ax.set_yticks([3,2,1,0],langs);ax.set_ylim(-.7,3.7)
fig.text(.065,.21,'Left: mean across all 20 languages. Right: four examples only; gray = GPT-5.6 Sol, green = GPT-6 Astra.\nAstra exceeds 83% in 19/20 languages; COBOL remains at 72.1%.\nNo confidence intervals or per-result test subsets are inferred.',fontsize=12,linespacing=1.8,color='#526b67')
save(fig,'languages',{'locator':'Section 1: mean and per-language test pass rates','metric':'test pass rate, percent','effort':'maximum','mean_20_languages':[26.8,40.3,87.4],'mean_models':['GPT-5.6 Sol','GPT-6 Luna','GPT-6 Astra'],'selected_languages':langs,'baseline':old,'GPT-6 Astra':new,'axis':[0,100],'scope':'Selected examples do not describe all languages; not migration success; no invented intervals'})

fig=base('COBOL migration: every hidden test must pass','Observable outputs must match byte for byte. Effort conditions are separated.')
ax=axis(fig,[.20,.38,.32,.38],'Same low reasoning effort',xlabel='Successful migrations (%)')
ax.barh([1,0],[5.4,86.6],color=[OLD,NEW],height=.4);ax.set_yticks([1,0],['GPT-5.6 Sol','GPT-6.1 Sol']);ax.set_ylim(-.6,1.6)
for y,v in zip([1,0],[5.4,86.6]):ax.text(v+1.3,y,f'{v}%',va='center',fontsize=20,weight='bold')
ax=axis(fig,[.70,.38,.24,.38],'Higher effort (different setting)',xlabel='Successful migrations (%)')
ax.barh([0],[97.9],color=MID,height=.4);ax.set_yticks([0],['GPT-6.1 Sol']);ax.set_ylim(-1,1);ax.text(97.9-2,0,'97.9%',ha='right',va='center',color='white',fontsize=20,weight='bold')
fig.text(.065,.21,'Targets: C++, Java, Kotlin, Python and Rust. All hidden tests must pass for one migration to succeed.\nThe exact higher-effort level and full hidden-test sample size are not stated in the read research text.\nThese scores are not the partial test-pass metric in MultiLangBench or a production safety guarantee.',fontsize=12,linespacing=1.8,color='#526b67')
save(fig,'migration',{'locator':'Section 2: accuracy at low and higher effort','metric':'all-tests migration success, percent','low_effort_models':['GPT-5.6 Sol','GPT-6.1 Sol'],'low_effort':[5.4,86.6],'higher_effort_model':'GPT-6.1 Sol','higher_effort':97.9,'exact_higher_effort':'not specified','axis':[0,100],'scope':'Different effort conditions shown in separate panels; full hidden-test denominator undisclosed'})

fig=base('Evaluation spending: keep task units separate','Estimated API spending, not token list prices or universal migration budgets.')
ax=axis(fig,[.20,.38,.30,.38],'MultiLangBench',xmax=4.2,xlabel='Estimated API cost (USD / sample)')
ax.barh([1,0],[3.48,.77],color=[OLD,NEW],height=.4);ax.set_yticks([1,0],['GPT-5.6 Sol','GPT-6 Luna']);ax.set_ylim(-.6,1.6)
for y,v in zip([1,0],[3.48,.77]):ax.text(v+.07,y,f'${v:.2f}',va='center',fontsize=19,weight='bold')
ax=axis(fig,[.70,.38,.24,.38],'COBOL migration: low effort',xmax=120,xlabel='Relative cost (older Sol = 100)')
ax.barh([1,0],[100,61],color=[OLD,NEW],height=.4);ax.set_yticks([1,0],['GPT-5.6 Sol','GPT-6.1 Sol']);ax.set_ylim(-.6,1.6)
for y,v in zip([1,0],[100,61]):ax.text(v+2,y,str(v),va='center',fontsize=19,weight='bold')
fig.text(.065,.21,'Left: about 78% lower per-sample spending. Right: 61% of the baseline, or about 39% lower.\nPanels use different units and must not be multiplied. Absolute migration dollars are not supplied.\nPricing dates, full retry configurations and production validation costs remain incomplete.',fontsize=12,linespacing=1.8,color='#526b67')
save(fig,'cost',{'locators':['Section 1: estimated API cost','Section 2: 61% of baseline API cost'],'database_usd_per_sample':{'GPT-5.6 Sol':3.48,'GPT-6 Luna':.77},'migration_low_effort_relative_cost':{'GPT-5.6 Sol':100,'GPT-6.1 Sol':61},'axes':[[0,4.2],[0,120]],'scope':'Different task units; not token prices; no invented absolute migration dollars'})
print('Rendered three independent coding-evaluation redraws and registered their bytes.')
