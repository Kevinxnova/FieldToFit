"""Independent redraws of the October29 Luna addendum; no source artwork reused."""
import json,hashlib
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[2];DEST=ROOT/'frontend/public/report-figures';MAN=ROOT/'backend/knowledge/content/report-figures.json'
BG='#f8faf6';INK='#172b3a';GREEN='#348371';PURPLE='#8173b5';RIGHTS='Graphics © FieldToFit. Independent redraw of reported facts; original artwork is not reproduced.'
URL='https://deploymentsafety.openai.com/gpt-6-luna-october-28-2026-addendum'
plt.rcParams.update({'font.family':'DejaVu Sans','text.color':INK,'axes.labelcolor':INK,'xtick.color':INK,'ytick.color':INK})
def base(t,s):
 f=plt.figure(figsize=(14,8),facecolor=BG);f.text(.05,.93,t,fontsize=21,weight='bold');f.text(.05,.865,s,fontsize=12);return f
def save(f,stem,loc):
 f.text(.05,.035,'FieldToFit independent redraw | OpenAI Luna October29 addendum | '+loc+' | Not replicated',fontsize=10)
 p=DEST/('oct30-luna-'+stem+'.png');f.savefig(p,dpi=120);plt.close(f);m=json.loads(MAN.read_text());m['/report-figures/'+p.name]={'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'source_urls':[URL],'license':RIGHTS,'attribution':'FieldToFit','source_version':'GPT-6 Luna October29, 2026 addendum','locator':loc};MAN.write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n')
def grouped(a,labels,old,new,ylim,ylabel):
 x=range(len(labels));a.bar([v-.18 for v in x],old,.34,color=PURPLE,label='October7');a.bar([v+.18 for v in x],new,.34,color=GREEN,label='October29');a.set_xticks(list(x),labels);a.set_ylim(0,ylim);a.set_ylabel(ylabel)
 for i,v,w in zip(x,old,new):a.text(i-.18,v+ylim*.025,str(v),ha='center',fontsize=11);a.text(i+.18,w+ylim*.025,str(w),ha='center',fontsize=11)
 a.legend(frameon=False,loc='upper center',bbox_to_anchor=(.5,-.20),ncol=2)
f=base('Factuality: both denominators regress on all three sets','Deliberately difficult prompt sets | Percent error, lower is better | Not production prevalence')
for pos,old,new,t,lim in [([.09,.30,.36,.45],[5.6,18.7,4.5],[8.5,24.6,7.8],'Responses containing an error',30),([.59,.30,.36,.45],[1.6,5.1,1.1],[2.5,7.2,1.6],'Claims judged erroneous',9)]:
 a=f.add_axes(pos);grouped(a,['Factuality\nheavy','User-flagged\nfailures','High\nstakes'],old,new,lim,'Error (%)');a.set_title(t,fontsize=14)
f.text(.06,.12,'Response-level and claim-level rates must not be pooled; no confidence intervals were inferred.',fontsize=12);save(f,'factuality','Figure3; §6.1')
f=base('HealthBench: adjusted score, raw score and length are distinct','Scores 0–100, higher is better | Length in visible characters | Not clinical effectiveness')
a=f.add_axes([.09,.29,.42,.46]);grouped(a,['Professional','Standard','Hard','Consensus'],[48.2,50.4,27.2,95.0],[47.4,48.2,22.8,93.3],110,'Length-adjusted score');a.tick_params(axis='x',labelsize=10)
a=f.add_axes([.63,.30,.31,.45]);a.axis('off');tb=a.table(cellText=[['Adjusted','50.4','48.2'],['Raw','58.5','54.0'],['Characters','3361','2970']],colLabels=['Standard','Oct7','Oct29'],loc='center',cellLoc='center',colWidths=[.46,.27,.27]);tb.auto_set_font_size(False);tb.set_fontsize(12);tb.scale(1,3)
f.text(.06,.12,'Lower adjusted scores do not establish that shorter answers caused the regression.',fontsize=13);save(f,'health','Table5; §5.1')
f=base('Behavior tests improve, but their failure definitions differ','Maximum reasoning | Percent failure, lower is better | Compare within each metric only')
a=f.add_axes([.13,.29,.78,.46]);grouped(a,['Warning\ncircumvention','Blocker\nnondisclosure*','Broken search\nnondisclosure'],[15.9,13.3,9.7],[11.8,11.1,7.83],20,'Failure (%)')
f.text(.06,.13,'* Earlier Blocker evaluation excluded 0.25% premature exits due to infrastructure issues.',fontsize=12);f.text(.06,.085,'Auto-Review already observed 0.0% for October7; observed zero is not a guarantee.',fontsize=12);save(f,'behavior','Figures4–7; §7')
print('Three independent Luna redraws registered')
