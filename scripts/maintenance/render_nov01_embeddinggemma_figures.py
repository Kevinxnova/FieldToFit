"""Independent redraws of reported EmbeddingGemma 2 facts; no original artwork copied."""
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'frontend/public/report-figures';OUT.mkdir(parents=True,exist_ok=True)
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':13,'axes.spines.top':False,'axes.spines.right':False,'figure.facecolor':'#fcfbf7','axes.facecolor':'#fcfbf7'})
def save(fig,name,title,note):
 fig.suptitle(title,fontsize=20,fontweight='bold',x=.06,ha='left',y=.97);fig.text(.06,.035,note,fontsize=11,color='#475569',va='bottom');fig.subplots_adjust(left=.12,right=.96,top=.82,bottom=.24,wspace=.32);fig.savefig(OUT/('nov01-embeddinggemma-'+name+'.png'),dpi=120);plt.close(fig)
fig,ax=plt.subplots(figsize=(14,8));labels=['All modalities','Text + audio','Text + vision','Text only'];vals=[744,577,439,271];ax.barh(labels,vals,color=['#304c68','#5d8b83','#8db1a1','#c2d4b2']);ax.set_xlim(0,850);ax.set_xlabel('Reported parameters used (millions)')
for y,v in enumerate(vals):ax.text(v+12,y,str(v)+'M',va='center',fontweight='bold')
save(fig,'modules','Load only the modality encoders the task needs','FieldToFit independent redraw | Paper v1, Figure 1 and Section 1\nReported configurations; do not sum rounded component values. Parameters are not embedding dimensions.')
fig,axes=plt.subplots(1,2,figsize=(14,8));tasks=['Multilingual text','English text','Code'];a=[61.15,69.67,68.76];b=[61.36,68.46,78.68]
import numpy as np
y=np.arange(3);axes[0].barh(y-.18,a,.32,label='EmbeddingGemma 1',color='#bec8c6');axes[0].barh(y+.18,b,.32,label='EmbeddingGemma 2',color='#477e75');axes[0].set_yticks(y,tasks);axes[0].set_xlim(0,100);axes[0].set_xlabel('MTEB Mean(Task)');axes[0].legend(loc='lower center',bbox_to_anchor=(.5,1.02),fontsize=10,ncol=2)
for j,(v,w) in enumerate(zip(a,b)):axes[0].text(v+1,j-.18,str(v),va='center',fontsize=10);axes[0].text(w+1,j+.18,str(w),va='center',fontsize=10)
axes[1].barh(['EG1 ASR\n308M','EG2 ASR\n271M','EG2 native audio\n577M'],[50.95,57.59,69.54],color=['#bec8c6','#8db1a1','#477e75']);axes[1].set_xlim(0,100);axes[1].set_xlabel('MSEB Retrieval MRR@10')
for j,v in enumerate([50.95,57.59,69.54]):axes[1].text(v+1,j,str(v),va='center',fontsize=11)
save(fig,'tradeoffs','Gains are task-specific; English text regresses','FieldToFit independent redraw | Tables 6 and 11 | Each panel keeps its own metric.\nAudio paths differ in modality and active parameters; these are not equal-cost comparisons or one aggregate gain.')
fig,axes=plt.subplots(1,2,figsize=(14,8));x=[70,140,280,560]
for ax,v,label,col in zip(axes,[[46.33,47.99,48.51,46.52],[51.61,63.60,63.38,67.62]],['Video Hit@1','Visual document NDCG@5'],['#b16f58','#477e75']):
 ax.plot(x,v,marker='o',color=col,lw=3);ax.set_xticks(x);ax.set_xlabel('Evaluation vision token budget');ax.set_ylabel(label);ax.set_ylim(40,75)
 for a,b in zip(x,v):ax.annotate(str(b),(a,b),xytext=(0,10),textcoords='offset points',ha='center',fontsize=11)
save(fig,'budget','More vision tokens help documents, but not every video task','FieldToFit independent redraw | Table 5, top half | One intermediate recipe, trained at 280/image and 140/frame.\nPanels use different metrics. These ablations are not final-model production settings or measured latency.')
print('Three independent report figures rendered')
