"""Original FieldToFit diagrams/redraws of public facts in Anthropic's 2026-11-06 agent-memory article."""
from pathlib import Path
import argparse
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

def render(output):
    output=Path(output);output.mkdir(parents=True,exist_ok=True)
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':13,'text.color':'#203d36','axes.labelcolor':'#203d36','xtick.color':'#203d36','ytick.color':'#203d36'})
    paths=[]
    def finish(fig,name):
        p=output/('nov09-'+name+'.png');fig.savefig(p,dpi=160,facecolor='#fafbf7');plt.close(fig);paths.append(p)
    def head(fig,title,subtitle):
        fig.text(.065,.935,title,fontsize=20,weight='bold');fig.text(.065,.875,subtitle,fontsize=11)
    def footer(fig,text):
        fig.text(.065,.115,text,fontsize=11,linespacing=1.55);fig.text(.065,.025,'FieldToFit original redraw / diagram | Lance Martin / Anthropic, 2026-11-06',fontsize=10)
    fig=plt.figure(figsize=(10.5,7.2));head(fig,'Memory needs layers and a path back to evidence','Conceptual organization, not a fixed implementation or model-weight update.')
    layers=[('Always-loaded index','Small context prepared for a new session'),('Representations / wiki','Linked, organized views of the evidence'),('Memory notes','Selected facts, hypotheses and tested rules'),('Transcripts / event records','Searchable original records for correction')]
    ys=[.71,.555,.40,.245]
    for (title,text),y in zip(layers,ys):
        fig.add_artist(FancyBboxPatch((.08,y),.53,.105,boxstyle='round,pad=0.01',transform=fig.transFigure,facecolor='#e5eee5',edgecolor='#9db5a7'))
        fig.text(.105,y+.067,title,weight='bold',fontsize=14);fig.text(.105,y+.027,text,fontsize=11)
    for y in [.71,.555,.40]:fig.add_artist(FancyArrowPatch((.34,y-.045),(.34,y-.005),arrowstyle='-|>',mutation_scale=13,shrinkA=0,shrinkB=0,transform=fig.transFigure,color='#638571'))
    fig.add_artist(FancyBboxPatch((.69,.35),.235,.30,boxstyle='round,pad=0.015',transform=fig.transFigure,facecolor='#eee9f4',edgecolor='#aa9bb9'))
    fig.text(.713,.58,'Offline organization',weight='bold',fontsize=13);fig.text(.713,.535,'Review original records\nCorrect stale notes\nMerge or relink pages\nChoose what to preload',fontsize=11,va='top',linespacing=1.8)
    for y in [.765,.61,.455,.30]:fig.add_artist(FancyArrowPatch((.68,.49),(.62,y),arrowstyle='->',mutation_scale=11,transform=fig.transFigure,color='#aa9bb9',linestyle='--'))
    footer(fig,'Higher layers are fallible interpretations. Keep provenance and ways to correct them.\nArrows describe organization/access, not measured causal effects.');finish(fig,'memory-layers')
    fig,ax=plt.subplots(figsize=(10.5,7.2));fig.subplots_adjust(left=.22,right=.92,top=.77,bottom=.27)
    head(fig,'A memory directory helps models differently','CL-Bench 1.0 database task | fresh sessions | same-model paired conditions')
    names=['Opus 5.5','Sonnet 5.5','Opus 5','Opus 4.7','Sonnet 5','Sonnet 4.6'];a=[.655,.644,.564,.383,.306,.330];b=[.838,.833,.828,.700,.610,.364];ys=list(range(6))
    ax.barh([y-.17 for y in ys],a,height=.29,label='Stateless baseline',color='#a7b3b3');ax.barh([y+.17 for y in ys],b,height=.29,label='Memory directory',color='#357c63')
    for y,x1,x2 in zip(ys,a,b):ax.text(x1+.014,y-.17,f'{x1:.3f}',va='center',fontsize=10);ax.text(x2+.014,y+.17,f'{x2:.3f}',va='center',fontsize=10)
    ax.set(yticks=ys,yticklabels=names,xlim=(0,1),xlabel='Mean reward (0–1)');ax.invert_yaxis();ax.legend(loc='lower right',fontsize=10);ax.spines[['top','right']].set_visible(False);ax.grid(axis='x',alpha=.18)
    footer(fig,'Published figure 3 values; no uncertainty intervals supplied for this chart.\nNot the entire CL-Bench aggregate or a production task success rate.');finish(fig,'memory-rewards')
    fig,ax=plt.subplots(figsize=(10.5,7.2));fig.subplots_adjust(left=.14,right=.92,top=.76,bottom=.31)
    head(fig,'Wiki and search are complements, not free substitutes','Internal document corpus | 25 questions | final reported grading values')
    labels=['Search only','Wiki only','Wiki + search'];v=[53,48,61];bars=ax.bar(labels,v,color=['#9faeae','#a9a0ba','#357c63'],width=.55)
    for bar,x in zip(bars,v):ax.text(bar.get_x()+bar.get_width()/2,x+2,str(x)+'%',ha='center',weight='bold',fontsize=16)
    ax.set(ylim=(0,100),ylabel='Grading criteria met (%)');ax.spines[['top','right']].set_visible(False);ax.grid(axis='y',alpha=.18)
    footer(fig,'About 350,000 files / 420M corpus tokens; up to 128 construction sessions.\nBudget: 1M tokens/session, up to 128M; not measured spend.\nAbout 20,000 tokens saved/answer excludes full construction; no net-cost claim.');finish(fig,'memory-retrieval')
    return paths

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',required=True);args=p.parse_args()
    for path in render(args.output):print(path)
