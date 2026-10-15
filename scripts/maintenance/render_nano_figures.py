"""Original charts from Nano Banana 2.1 Model Card, physical page 5."""
from pathlib import Path
import json,hashlib
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
P=Path(__file__).resolve().parents[2];target=P/'frontend/public/report-figures';path=P/'backend/knowledge/content/report-figures.json'
source='https://storage.googleapis.com/deepmind-media/Model-Cards/Nano-Banana-2-1-Model-Card.pdf'
rights='Graphics © FieldToFit; original data: Google DeepMind Nano Banana 2.1 model card.'
manifest=json.loads(path.read_text());plt.rcParams.update({'font.family':'DejaVu Sans','font.size':12,'axes.spines.top':False,'axes.spines.right':False,'figure.facecolor':'#f8fafc','axes.facecolor':'#f8fafc','text.color':'#18324d','axes.labelcolor':'#18324d'})
models=['Nano Banana 2.1\nThinking','Nano Banana 2.1\nNo Thinking','Nano Banana 2\nThinking','Nano Banana Pro'];colors=['#3567ba','#38a092','#8197bd','#b58a5f']
def canvas(title,subtitle):
 f=plt.figure(figsize=(12,7.2),dpi=150);f.text(.06,.94,title,fontsize=23,weight='bold');f.text(.06,.885,subtitle,fontsize=10,color='#4e6378');f.text(.06,.035,'FieldToFit redraw · Nano Banana 2.1 model card · October 2026 · author data, not reproduced',fontsize=9,color='#4e6378');return f
def save(f,stem,stats):
 p=target/('nano-banana-21-202610-'+stem+'.png');f.savefig(p,dpi=150);plt.close(f)
 manifest['/report-figures/'+p.name]={'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'source_urls':[source],'license':rights,'version':'Nano Banana 2.1 Model Card · October 2026','origin':'fieldtofit-redraw','statistics':stats}
f=canvas('Preference scores are task-specific','Human side-by-side Elo · source ± ranges retained; confidence level not specified in the card')
values=[[1050,1015,990,935],[1048,1001,961,912]];errors=[[14,13,7,8],[17,17,12,12]]
for k,name in enumerate(['Overall preference','Infographic design']):
 a=f.add_axes([.23,.55-k*.32,.70,.23])
 for j in range(4):a.errorbar(values[k][j],j,xerr=errors[k][j],fmt='o',color=colors[j],capsize=4,markersize=7);a.text(values[k][j]+errors[k][j]+7,j,f'{values[k][j]} ± {errors[k][j]}',va='center',fontsize=10)
 a.set_yticks(range(4),models,fontsize=9);a.invert_yaxis();a.set_xlim(860,1130);a.set_title(name,loc='left',fontsize=13);a.set_xlabel('Elo (relative preference; not an accuracy percentage)');a.grid(axis='x',alpha=.15)
save(f,'preference',{'models':models,'rows':['overall preference','infographic design'],'elo':values,'source_plus_minus':errors,'locator':'physical p5','scope':'Separate preference evaluations, no cross-task total; source uncertainty interpretation unspecified.'})
f=canvas('Factuality uses a different evaluator','Infographic factuality · single-sided AutoRater · reported raw scores, not real-world accuracy rates')
a=f.add_axes([.24,.23,.68,.56]);scores=[.521,.328,.179,.265];a.barh(range(4),scores,color=colors,height=.55)
for y,v in enumerate(scores):a.text(v+.012,y,f'{v:.3f}',va='center',fontsize=14,weight='bold')
a.set_yticks(range(4),models);a.invert_yaxis();a.set_xlim(0,.65);a.set_xlabel('Reported AutoRater factuality score');a.grid(axis='x',alpha=.15);a.set_axisbelow(True)
f.text(.06,.13,'Do not merge AutoRater scores with Elo, or interpret 0.521 as a calibrated 52.1% business accuracy.',fontsize=10)
save(f,'factuality',{'models':models,'scores':scores,'metric':'Infographic factuality / single-sided AutoRater','locator':'physical p5','scope':'No published sample-size or calibration details sufficient for a business accuracy claim.'})
f=canvas('Editing consistency is not one overall score','Human side-by-side Elo · compare within each row · original ± ranges retained')
values=[[1028,1021,981,991],[1106,1068,978,1011],[1066,1041,988,989]];errors=[[14,14,10,9],[14,14,10,10],[22,20,13,12]]
a=f.add_axes([.24,.27,.69,.51])
for j,m in enumerate(models):
 y=[k+(j-1.5)*.16 for k in range(3)];v=[row[j] for row in values];er=[row[j] for row in errors]
 a.errorbar(v,y,xerr=er,fmt='o',color=colors[j],capsize=3,markersize=6,label=m.replace('\n',' / '))
a.set_yticks(range(3),['Single-character','Multi-character','Multi-reference']);a.invert_yaxis();a.set_xlim(930,1155);a.set_xlabel('Elo (independent evaluation rows)');a.grid(axis='x',alpha=.15);a.legend(loc='upper center',bbox_to_anchor=(.40,-.24),ncol=2,fontsize=9,frameon=False)
save(f,'editing',{'models':models,'rows':['single-character','multi-character','multi-reference'],'elo':values,'source_plus_minus':errors,'locator':'physical p5','scope':'No inference of universal or statistically significant gains from overlapping source ranges.'})
path.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
print('Rendered three original Nano Banana2.1 PNG charts with metric-specific facts and hashes.')
