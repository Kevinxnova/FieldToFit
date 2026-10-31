"""Independent redraws of the expert-judgment study; no source artwork reused."""
import json,hashlib
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[2];DEST=ROOT/'frontend/public/report-figures';MAN=ROOT/'backend/knowledge/content/report-figures.json';URL='https://www-cdn.anthropic.com/519c17a5d23a794e8b6d50a854048d0b61e0d73a.pdf';RIGHTS='Graphics © FieldToFit. Independent redraw of reported facts; original artwork is not reproduced.'
BG='#f8faf6';INK='#172b3a';GREEN='#348371';PURPLE='#8173b5'
plt.rcParams.update({'font.family':'DejaVu Sans','text.color':INK,'axes.labelcolor':INK,'xtick.color':INK,'ytick.color':INK})
def base(t,s):
 f=plt.figure(figsize=(14,8),facecolor=BG);f.text(.05,.93,t,fontsize=21,weight='bold');f.text(.05,.865,s,fontsize=12);return f
def save(f,stem,loc):
 f.text(.05,.035,'FieldToFit independent redraw | Herdagdelen, Joren & Tamkin (2026) | '+loc+' | Not replicated',fontsize=10);p=DEST/('oct31-judgment-'+stem+'.png');f.savefig(p,dpi=120);plt.close(f);m=json.loads(MAN.read_text());m['/report-figures/'+p.name]={'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'source_urls':[URL],'license':RIGHTS,'attribution':'FieldToFit','source_version':'Official paper linked 2026-10-27; unnumbered','locator':loc};MAN.write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n')
f=base('Registered estimates: similar-looking effects, different evidence','Percentage points with two-sided 95% confidence intervals | Read primary and conditional results separately')
a=f.add_axes([.36,.27,.57,.47]);v=[72,17,23,53];lo=[60,-6,-4,24];hi=[83,40,50,82];labels=['H1 Analytical choices\nPRIMARY','H2 Policy recommendation\nAdjusted; p = 0.069 (one-sided)','H3 Departing from own estimate\nDESCRIPTIVE only','H4 Switching an earlier choice\nConditional on selected trials'];a.errorbar(v,range(4),xerr=[[x-y for x,y in zip(v,lo)],[y-x for x,y in zip(v,hi)]],fmt='o',color=GREEN,capsize=5,markersize=8);a.set_yticks(range(4),labels);a.invert_yaxis();a.axvline(0,color='#888',linestyle='--');a.set_xlim(-15,100);a.set_xlabel('Effect (percentage points)');a.grid(axis='x',alpha=.18)
for j,x in enumerate(v):a.text(hi[j]+2,j,f'{x} [{lo[j]}, {hi[j]}]',va='center',fontsize=11)
f.text(.06,.13,'H3 failed its falsification check. H4 selects post-treatment behavior; causal interpretation is conditional.',fontsize=12);save(f,'effects','Figure 1; Table 2')
f=base('Alignment, argument reuse and attribution are different outcomes','Percent as reported | Different denominators | These bars are not a conversion funnel')
a=f.add_axes([.12,.28,.77,.47]);vals=[86,77,15];bars=a.bar(range(3),vals,color=[GREEN,PURPLE,PURPLE],width=.5);a.set_ylim(0,108);a.set_ylabel('Percent');a.set_xticks(range(3),['Analytical choices\nmatch assigned lean','Respondents reuse\nan agent argument','Respondents mention\nthe agent anywhere']);a.grid(axis='y',alpha=.15)
for j,v in enumerate(vals):a.text(j,v+3,str(v)+'%',ha='center',fontsize=18,weight='bold')
f.text(.06,.13,'Choice alignment: analytical decisions. Reuse and attribution: 48 survey respondents.',fontsize=13);f.text(.06,.085,'52% rated the final recommendation as more their own; this does not establish independent judgment.',fontsize=12);save(f,'awareness','Main text; section 4.2')
f=base('Errors and time: useful comparisons, but not randomized AI effects','Participants chose whether to use the agent | Different experience profiles | No causal productivity claim')
a=f.add_axes([.09,.28,.35,.46]);a.bar([0,1],[6,55],color=[GREEN,PURPLE],width=.5);a.set_xticks([0,1],['AI users\nn = 50','No-AI users\nn = 11']);a.set_ylim(0,70);a.set_ylabel('Serious error (%)');a.text(0,8,'3/50 = 6%',ha='center');a.text(1,57,'6/11 = 55%',ha='center')
a=f.add_axes([.61,.28,.31,.46]);a.bar([0,1],[65,90],color=[GREEN,PURPLE],width=.5);a.set_xticks([0,1],['AI users','No-AI users']);a.set_ylim(0,110);a.set_ylabel('Median task time (minutes)');a.text(0,68,'65',ha='center');a.text(1,93,'90',ha='center');f.text(.06,.13,'An author blindly adjudicated serious errors flagged by two models; unflagged sessions were not all human-reviewed.',fontsize=11);save(f,'utility','Section 4.2.3; Appendix A.9')
print('Three judgment-study figures registered')
