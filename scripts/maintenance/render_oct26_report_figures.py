"""Original FieldToFit redraws for the selected biological-reasoning analysis."""
import json,hashlib
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[2];DEST=ROOT/'frontend/public/report-figures';MAN=ROOT/'backend/knowledge/content/report-figures.json'
BG='#f8faf6';INK='#172b3a';GREEN='#348371';PURPLE='#8173b5'
plt.rcParams.update({'font.family':'DejaVu Sans','text.color':INK,'axes.labelcolor':INK,'xtick.color':INK,'ytick.color':INK})
URL='https://www.biorxiv.org/content/10.64898/2026.10.15.759436v1.full'
RIGHTS='Graphics © FieldToFit. Independent redraw of author-reported counts; original artwork is not reproduced.'
def base(t,s):
 f=plt.figure(figsize=(14,8),facecolor=BG);f.text(.05,.92,t,fontsize=23,weight='bold');f.text(.05,.85,s,fontsize=12);f.text(.05,.035,'FieldToFit independent redraw | Sun et al., bioRxiv v1, 2026-10-16 | Not independently replicated',fontsize=10);return f
def save(f,stem,loc):
 p=DEST/('bioagents-20261016-'+stem+'.png');f.savefig(p,dpi=120);plt.close(f);m=json.loads(MAN.read_text());m['/report-figures/'+p.name]={'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'source_urls':[URL],'license':RIGHTS,'attribution':'FieldToFit','source_version':'bioRxiv v1; 2026-10-16','locator':loc};MAN.write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n')
f=base('Recovery depends on the denominator','Claim-by-gene comparisons, not unique genes or experimentally verified new mechanisms.')
a=f.add_axes([.21,.32,.69,.41],facecolor=BG);vals=[[48,9,14],[48,4,3]];left=[0,0]
for j,(lab,col) in enumerate(zip(['Matched or refined','Partial','Uncovered'],[GREEN,PURPLE,'#b7bdc2'])):
 v=[r[j] for r in vals];a.barh([1,0],v,left=left,color=col,label=lab,height=.48)
 for y,n,l in zip([1,0],v,left):a.text(l+n/2,y,str(n),ha='center',va='center',fontsize=18,color='white' if j<2 else INK)
 left=[l+n for l,n in zip(left,v)]
a.set_yticks([1,0],['All comparisons\nn = 71','Directly testable\nn = 55']);a.set_xlim(0,75);a.set_xlabel('Number of comparisons');a.legend(loc='upper center',bbox_to_anchor=(.5,-.23),ncol=3,frameon=False)
f.text(.07,.13,'48 / 55 = 87.3% in the directly testable subset. All-comparison counts are 35 match + 13 refine.',fontsize=12);save(f,'recovery','Fig. 1C; Supplement pp. 12–13')
f=base('An unresolved one-case difference in the source','Held out: 100 responders + 172 nonresponders = 272 targets. Counts are kept separately.')
a=f.add_axes([.14,.28,.75,.46]);a.axis('off')
t=a.table(cellText=[['Main text / Fig. 3','59','41','142','30','0.708*'],['Supplement S9D','59','41','141','31','0.705'],['Single agent (S9D)','69','31','136','36','0.740']],colLabels=['Source / condition','TP','FN','TN','FP','Balanced acc.'],cellLoc='center',loc='center',colWidths=[.32,.12,.12,.12,.12,.2]);t.auto_set_font_size(False);t.set_fontsize(13);t.scale(1,3)
for (r,c),cell in t.get_celld().items():cell.set_edgecolor('#e3e7e2');cell.set_facecolor('#dcebe4' if r==0 else '#ffffff')
f.text(.07,.16,'* FieldToFit calculation: (59/100 + 142/172)/2. The paper text reports 0.705.',fontsize=12);f.text(.07,.11,'The source does not explain the discrepancy. This endpoint does not favor distributed over single.',fontsize=12);save(f,'prediction','Fig. 3B–C; Fig. S9D; Supplement pp. 20–24')
f=base('Expert preference is not mechanism validation','20 matched report pairs × 3 judgments = 60 judgments; distinct from 180 individual report ratings.')
a=f.add_axes([.14,.29,.75,.45],facecolor=BG);a.barh([2,1,0],[45,10,5],color=[GREEN,PURPLE,'#b7bdc2'],height=.55);a.set_yticks([2,1,0],['Distributed preferred','Single preferred','Tie']);a.set_xlim(0,60);a.set_xlabel('Number of judgments')
for y,v in zip([2,1,0],[45,10,5]):a.text(v+1,y,str(v),va='center',fontsize=20,weight='bold')
f.text(.07,.14,'45 / 60 = 75% of judgments. Not 75% of experts, discoveries or experimentally established mechanisms.',fontsize=12);save(f,'review','Fig. 4K; Supplement pp. 30–31')
print('Three figures generated and registered')
