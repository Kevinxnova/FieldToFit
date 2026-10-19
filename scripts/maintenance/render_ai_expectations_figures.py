"""Rebuild three independently designed figures from verified survey statistics.

Offline matplotlib dependency. No copied upstream graphic design, invented
confidence intervals, inferred denominators or external economic-model rerun.
"""
from pathlib import Path
import json,hashlib
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT=Path(__file__).resolve().parents[2]
DEST=ROOT/'frontend/public/report-figures'
MANIFEST=ROOT/'backend/knowledge/content/report-figures.json'
URL='https://www.anthropic.com/research/ai-expectations-gap'
RIGHTS='Graphics © FieldToFit; source facts: Sacher, Cotter, Jones, Korinek and McCrory, The Anthropic Institute, 2026-10-16. Original report graphics are not reproduced.'
VERSION='2026-10-16; unnumbered report; appendix dated October 2026'
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':14,'axes.spines.top':False,'axes.spines.right':False,'text.color':'#183b3c','axes.labelcolor':'#284c4c','axes.edgecolor':'#b7c7c1','xtick.color':'#42615c','ytick.color':'#284c4c'})
COLORS=['#7899ae','#25765f']
def base(title,subtitle):
    fig=plt.figure(figsize=(15,9),dpi=120,facecolor='#f7faf7')
    fig.text(.055,.93,title,fontsize=24,weight='bold')
    fig.text(.055,.873,subtitle,fontsize=13,color='#526b67')
    fig.text(.055,.037,'FieldToFit redraw | The Anthropic Institute, 2026-10-16 | Survey beliefs; not realized outcomes',fontsize=11,color='#526b67')
    return fig
def bars(fig,rect,title,labels,values,xlabel):
    ax=fig.add_axes(rect,facecolor='#f7faf7');ax.set_title(title,fontsize=15,loc='left',pad=20,weight='bold')
    ax.barh([1,0],values,color=COLORS,height=.40)
    for y,v in zip([1,0],values):ax.text(v+1.5,y,str(v)+'%',va='center',fontsize=20,weight='bold')
    ax.set_xlim(0,100);ax.set_ylim(-.65,1.65);ax.set_xticks([0,25,50,75,100]);ax.set_yticks([1,0],labels);ax.tick_params(axis='y',length=0,labelsize=12)
    ax.set_xlabel(xlabel,fontsize=12,labelpad=12);ax.grid(axis='x',alpha=.15);ax.set_axisbelow(True)
    return ax
def save(fig,stem,stats):
    DEST.mkdir(parents=True,exist_ok=True);path=DEST/('ai-expectations-20261016-'+stem+'.png');fig.savefig(path,dpi=120);plt.close(fig)
    data=json.loads(MANIFEST.read_text());data['/report-figures/'+path.name]={'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'source_urls':[URL],'license':RIGHTS,'version':VERSION,'origin':'fieldtofit-redraw','statistics':stats}
    MANIFEST.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')

fig=base('Two views of AI in 2030','Different questions and populations. Both panels describe beliefs about future capability.')
bars(fig,[.155,.34,.34,.40],'AI can make a Nobel-level discovery',['US adults','Anthropic staff'],[39,91],'Share answering capable by 2030 (%)')
bars(fig,[.65,.34,.30,.40],'AI can do my current work hours',['US workers\n(n=2,278)','Anthropic staff\n(n=1,147)'],[28,75],'Mean share of current work hours (%)')
fig.text(.065,.16,'Figures 1 and 5 | Public responses weighted; staff unweighted.\nPublic future questions split between 2027 and 2030; uncertain answers excluded question by question.\nOwn-work responses: public range midpoints, staff slider. Original Figure 5 has 95% intervals; not reconstructed here.',fontsize=12,color='#526b67',linespacing=1.7)
save(fig,'expectations',{'locators':['Figure 1 p.4','Figure 5 p.8'],'capability_belief_percent':[39,91],'own_work_hours_mean_percent':[28,75],'figure5_valid_n':[2278,1147],'scale':[0,100],'scope':'Beliefs, not measured capability or jobs lost; panels have different populations; original Figure 5 intervals omitted explicitly'})

fig=base('Adoption and time savings answer different questions','Keep the denominator and time horizon separate; these panels do not form a funnel.')
bars(fig,[.155,.34,.34,.40],'Expected adoption in 2030',['US adults','Anthropic staff'],[42,65],'Share of tasks AI could do (%)')
bars(fig,[.65,.34,.30,.40],'A suitable task takes 1/4 time or less',['US adults who\nuse AI at work','Anthropic staff'],[26,59],'Share of respondents reporting this (%)')
fig.text(.065,.16,'Adoption text and Figure 4 p.7 | Time includes checking and correcting the work.\nThe right panel concerns a task well suited to current AI, not all working hours or measured workplace output.\nValid subgroup counts are not inferred from percentages; do not multiply the two panels.',fontsize=12,color='#526b67',linespacing=1.7)
save(fig,'adoption-time',{'locators':['Adoption p.4','Figure 4 p.7'],'conditional_task_adoption_percent':[42,65],'respondents_quarter_time_or_less_percent':[26,59],'scale':[0,100],'scope':'Adoption conditional on AI-capable tasks; time self-reported including corrections, public group restricted to work users; no shared denominator or funnel'})

fig=base('Beliefs translated into conditional economic scenarios','Median model-implied annual GDP growth in 2030; not a direct survey forecast or realized growth.')
ax=fig.add_axes([.28,.31,.65,.46],facecolor='#f7faf7')
vals=[5.4,12.5,17.1];labels=['US adults\ncomplete responses: 3,259','Website visitors\ncomplete responses: 23,075','Anthropic staff\ncomplete responses: 1,093']
for y,v,c in zip([2,1,0],vals,['#7899ae','#b58f56','#25765f']):
    ax.plot([0,v],[y,y],color=c,alpha=.30,lw=4);ax.scatter([v],[y],color=c,s=170,zorder=3);ax.text(v+.6,y,f'{v}%',va='center',fontsize=21,weight='bold')
ax.set_yticks([2,1,0],labels);ax.tick_params(axis='y',length=0,labelsize=13);ax.set_xlim(0,30);ax.set_ylim(-.6,2.6);ax.set_xlabel('Annual GDP growth in 2030 (%)',labelpad=14);ax.set_xticks(range(0,31,5));ax.grid(axis='x',alpha=.15);ax.set_axisbelow(True)
fig.text(.065,.15,'Figure 7 p.12 | Public sample: 2030 half only. Visitors: first 48 hours after the 2026-09-09 launch.\nFive belief dimensions enter an existing model; other parameters held at the Substantial scenario.\nDistributions overlap. This redraw shows medians only and does not reconstruct percentile ranges.',fontsize=12,color='#526b67',linespacing=1.7)
save(fig,'scenarios',{'locator':'Figure 7 p.12; footnote 5 p.15','groups':['US adults','Website visitors','Anthropic staff'],'complete_response_n':[3259,23075,1093],'median_model_implied_annual_growth_percent':[5.4,12.5,17.1],'axis':[0,30],'scope':'Conditional model outputs, medians only; no reconstructed quantile intervals; public 2030 half, self-selected visitors; not realized GDP or forecast accuracy'})
print('Rendered three verified-fact survey redraws and registered their bytes.')
