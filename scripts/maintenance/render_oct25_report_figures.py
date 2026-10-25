"""Independent explanatory figures for the owner-selected October 25 reports."""
import json,hashlib
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
ROOT=Path(__file__).resolve().parents[2];DEST=ROOT/'frontend/public/report-figures';MAN=ROOT/'backend/knowledge/content/report-figures.json'
BG='#f8faf6';INK='#172b3a';GREEN='#348371';PURPLE='#8173b5'
plt.rcParams.update({'font.family':'DejaVu Sans','text.color':INK,'axes.labelcolor':INK,'xtick.color':INK,'ytick.color':INK})
U1='https://alignment.openai.com/beyond-gmean-squared/';U2='https://www.anthropic.com/research/employment-at-anthropic'
RIGHTS='Graphics © FieldToFit. Independent explanation of author-reported facts; original graphics are not reproduced.'
def base(title,sub,source):
 f=plt.figure(figsize=(14,8),facecolor=BG);f.text(.05,.92,title,fontsize=23,weight='bold');f.text(.05,.85,sub,fontsize=12);f.text(.05,.035,'FieldToFit independent graphic | '+source+' | Not independently replicated',fontsize=10);return f
def save(f,name,url,loc):
 p=DEST/(name+'.png');f.savefig(p,dpi=120);plt.close(f);m=json.loads(MAN.read_text());m['/report-figures/'+p.name]={'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'source_urls':[url],'license':RIGHTS,'attribution':'FieldToFit','source_version':'2026-10-20' if url==U1 else '2026-10-16','locator':loc};MAN.write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n')
def boxes(f,labels,foot):
 a=f.add_axes([.055,.27,.89,.48]);a.set_axis_off()
 for i,text in enumerate(labels):
  x=.008+i*.333;a.add_patch(FancyBboxPatch((x,.10),.305,.80,boxstyle='round,pad=0.008',facecolor=['#e1ede6','#e7e5f1','#e7edf1'][i],edgecolor='none'));a.text(x+.152,.5,text,ha='center',va='center',fontsize=18,linespacing=1.6)
 f.text(.065,.15,foot,fontsize=12)
f=base('Match the samples before comparing the monitors','Outcome evaluations match positive and negative instances separately.','OpenAI, 2026-10-20')
boxes(f,['Shared positives\nEstimate TPR\nSame task support','Shared negatives\nEstimate TNR\nSeparate support','Matched score\nTPR × TNR\nPair-specific estimate'],'Shared tasks can still contain different behavior classes and detection difficulty.')
save(f,'monitorability-20261020-matching',U1,'Metric 1; Figure 1')
f=base('A low per-request risk can hide sparse delivery','Two Honeypot slices at K = 4; reported ranges, not invented point estimates.','OpenAI, 2026-10-20')
boxes(f,['B(4) < 3%\nBad output\nper request','A(4) < 7%\nAny output\nper request','B(4) / A(4)\n41–45% bad\namong deliveries'],'Read all three together. Target positives are not necessarily harmful in every environment.')
save(f,'monitorability-20261020-denominators',U1,'Risk must be read beside deployment; Figure 6')
f=base('Observed flags do not identify causal labels','Appendix illustration: 10 positives, 6 flagged, at least 8 intervention-caused.','OpenAI, 2026-10-20')
boxes(f,['Pessimistic\n4 causal caught / 8\n50% recall','Same observations\nWhich positives are\ncausal is unknown','Optimistic\n6 causal caught / 8\n75% recall'],'Identification bounds, not an empirical confidence interval or deployment success rate.')
save(f,'monitorability-20261020-bounds',U1,'Appendix; Figure A1')
f=base('Junior technical shares fall while the company expands','Reported early-to-later values since early 2025; distinct denominators.','Anthropic Institute, 2026-10-16')
a=f.add_axes([.12,.29,.76,.46],facecolor=BG);x=[0,1];a.bar([-.17,.83],[21,27],.32,color='#8e9ca3',label='Earlier');a.bar([.17,1.17],[14,9],.32,color=GREEN,label='Later');a.set_xticks(x,['Junior technical employees\n/ technical employees','Junior technical hires\n/ technical hires']);a.set_ylim(0,35);a.set_ylabel('Share (%)');a.legend(frameon=False);a.grid(axis='y',alpha=.15);a.set_axisbelow(True)
for xx,v in zip([-.17,.17,.83,1.17],[21,14,27,9]):a.text(xx,v+.8,str(v)+'%',ha='center',fontsize=18,weight='bold')
f.text(.065,.14,'These are composition shares, not layoff rates or counts. Figure-specific dates remain in the source.',fontsize=12)
save(f,'employment-20261016-shares',U2,'Labor demand at the frontier; Figure 1')
f=base('An adoption study, not a randomized trial','Engineering comparison in Figure 4; adoption starts at 5+ agentic sessions in a month.','Anthropic Institute, 2026-10-16')
boxes(f,['192 adopters\n74 non-adopters\nFollow people over time','Two-way fixed effects\nPerson + month\n95% clustered CIs','Remaining uncertainty\nSelf-selection\nCode is not value'],'Autonomous-agent adopters already had upward pre-trends. No effect size is invented here.')
save(f,'employment-20261016-design',U2,'Is AI driving productivity increases at Anthropic?; Figure 4')
f=base('Meta-work grows as a share of interactive sessions','Automated classification of 2,000 one-line summaries; not a time-use survey.','Anthropic Institute, 2026-10-16')
a=f.add_axes([.15,.29,.70,.46],facecolor=BG);a.bar(['Fall 2025','Spring 2026'],[10,22],color=['#8e9ca3',PURPLE],width=.45);a.set_ylim(0,30);a.set_ylabel('Interactive sessions classified as meta-work (%)');a.grid(axis='y',alpha=.15);a.set_axisbelow(True)
for x,v in enumerate([10,22]):a.text(x,v+1,str(v)+'%',ha='center',fontsize=23,weight='bold')
f.text(.065,.14,'Includes skills, plans, agent reviews and pipeline monitors. This is not the share of working hours.',fontsize=12)
save(f,'employment-20261016-metawork',U2,'Becoming managers of Claudes; Figure 7')
print('Six figures generated and registered')
