"""Six independent factual reading diagrams for the owner-selected October 23 analyses."""
import json,hashlib
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch,FancyArrowPatch
ROOT=Path(__file__).resolve().parents[2];DEST=ROOT/'frontend/public/report-figures';PATH=ROOT/'backend/knowledge/content/report-figures.json'
BG='#f8faf6';INK='#172b3a';GREEN='#348371';PURPLE='#8173b5';GRAY='#8e9ca3'
plt.rcParams.update({'font.family':'DejaVu Sans','text.color':INK,'axes.labelcolor':INK,'axes.edgecolor':'#cbd4ce','xtick.color':INK,'ytick.color':INK})
U1='https://www.anthropic.com/research/formal-verification';U2='https://arxiv.org/abs/2610.22367'
RIGHTS='Graphics © FieldToFit. Independent redraw of author-reported facts; original report graphics are not reproduced.'
def base(title,subtitle,source):
 f=plt.figure(figsize=(14,8),facecolor=BG);f.text(.055,.92,title,fontsize=23,weight='bold');f.text(.055,.85,subtitle,fontsize=12,color='#536972');f.text(.055,.035,'FieldToFit independent redraw | '+source+' | Not independently reproduced',fontsize=10,color='#536972');return f
def save(f,name,url,version,loc,stats):
 DEST.mkdir(parents=True,exist_ok=True);p=DEST/(name+'.png');f.savefig(p,dpi=120);plt.close(f);m=json.loads(PATH.read_text());m['/report-figures/'+p.name]={'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'source_urls':[url],'license':RIGHTS,'version':version,'origin':'fieldtofit-redraw','statistics':{'locators':loc,**stats}};PATH.write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n')
def flow(f,labels,bottom):
 a=f.add_axes([.04,.26,.92,.49]);a.set(xlim=(0,1),ylim=(0,1));a.axis('off')
 for x,t in zip([.01,.27,.53,.79],labels):
  a.add_patch(FancyBboxPatch((x,.43),.20,.43,boxstyle='round,pad=0.008',facecolor='#e3efe7',edgecolor=GREEN));a.text(x+.10,.645,t,ha='center',va='center',fontsize=12,linespacing=1.65)
 for x1,x2 in ((.21,.27),(.47,.53),(.73,.79)):a.add_patch(FancyArrowPatch((x1,.64),(x2-.008,.64),arrowstyle='-|>',mutation_scale=16,color=GREEN))
 f.text(.07,.18,bottom,fontsize=12)
f=base('A proof checker does not choose the right specification','The model proposes evidence; independent tools check it; people audit what the theorem means.','Anthropic / Theorem, 2026-10-22')
flow(f,['Specify\nBinary + assumptions\nRequired behavior','Claude\nGenerate proofs\nInvestigate failures','Rocq\nCheck proof steps\nAgainst the theorem','Human review\nSpecification + patches\nTrusted components'],'Machine-checked proof ≠ unrestricted coverage of every library behavior.')
save(f,'formal-20261022-workflow',U1,'2026-10-22; unnumbered',['Turning tests into proofs','Limitations'],{'kind':'reading_diagram','claims_universal_software_safety':False})
f=base('Coverage is a set of entry points, not a percentage','The source reports 123 libraries and 239 entry points; no whole-library coverage denominator is given.','Anthropic / Theorem, 2026-10-22')
f.text(.10,.62,'123',fontsize=62,color=GREEN,weight='bold');f.text(.10,.54,'open-source libraries',fontsize=17);f.text(.49,.62,'239',fontsize=62,color=PURPLE,weight='bold');f.text(.49,.54,'verification entry points',fontsize=17)
f.text(.10,.39,'Execution boundary',fontsize=20,weight='bold');f.text(.10,.29,'RISC-V Linux  •  single-threaded  •  static binary  •  fixed memory budget',fontsize=15);f.text(.10,.20,'Inputs below 64 MiB in the main effort; 64-byte inputs in the small-task comparison.',fontsize=13);f.text(.10,.12,'No implication for uncovered entry points, other architectures or unrestricted input sizes.',fontsize=12,color='#536972')
save(f,'formal-20261022-scope',U1,'2026-10-22; unnumbered',['Introduction','Appendix pp.1–2,5'],{'libraries':123,'entry_points':239,'coverage_percentage':None,'main_input_limit':'below 64 MiB','small_tasks_input_bound':'64 bytes'})
f=base('Two separate token comparisons','Each panel has its own baseline = 100. Indexed values are derived, not raw token counts or dollar costs.','Anthropic / Theorem, 2026-10-22')
for rect,title,names,vals in [([.12,.32,.32,.39],'Tokens to solve half of 36 tasks',['Opus 5','Opus 5.5'],[100,60]),([.61,.32,.32,.39],'Separate shared-proof experiment',['Own baseline','Shared work'],[100,83])]:
 a=f.add_axes(rect,facecolor=BG);a.bar(range(2),vals,color=[GRAY,GREEN],width=.55);a.set_xticks(range(2),names);a.set_ylim(0,120);a.set_ylabel('Token index (own baseline = 100)');a.set_title(title,fontsize=12);a.grid(axis='y',alpha=.15);a.set_axisbelow(True)
 for x,v in enumerate(vals):a.text(x,v+3,str(v),ha='center',fontsize=17,weight='bold')
f.text(.07,.17,'Left: three independent attempts per task, 5M tokens per attempt; earliest successful attempt counted.',fontsize=12);f.text(.07,.11,'Do not add or multiply the reported 40% and 17% savings; neither establishes end-to-end compute cost.',fontsize=12)
save(f,'formal-20261022-comparisons',U1,'2026-10-22; unnumbered',['This is just the beginning','Technical appendix'],{'separate_baselines':True,'derived_index_values':[[100,60],[100,83]],'reported_relative_savings_percent':[40,17],'raw_curves_reconstructed':False})
f=base('An evaluator-guided search, within human-set constraints','Correctness, input conventions, error budgets and scoring are set before the candidate is accepted.','Gu et al., arXiv:2610.22367v1')
flow(f,['Human setup\nTask + encoding\nError budget','Claude Mythos 5\nPropose circuit\nRevise generator','Independent evaluator\nOutput + phase\nAncillas + resources','Evolution archive\nKeep useful families\nGuide the next round'],'Feedback from accepted and rejected designs informs the next proposal.')
f.text(.07,.11,'Classical validation and logical-resource accounting; no measured quantum-hardware runtime.',fontsize=12,color='#536972')
save(f,'quantum-20261015-workflow',U2,'arXiv:2610.22367v1',['Main Methods','SI I'],{'kind':'reading_diagram','hardware_runtime_measured':False})
f=base('Reed–Solomon decoding: keep gates and qubits separate','Same specified DQI task; source counts are rounded. Approximation and input-distribution limits still apply.','Gu et al., Extended Data Table 1 / SI I.1')
for rect,title,vals,ylim,unit in [([.12,.32,.32,.39],'Toffoli gates',[5.1,.44],6,'Millions of Toffoli gates'),([.61,.32,.32,.39],'Peak logical qubits',[1938,1837],2300,'Logical qubits (count)')]:
 a=f.add_axes(rect,facecolor=BG);a.bar(range(2),vals,color=[GRAY,GREEN],width=.55);a.set_xticks(range(2),['Baseline','Discovered']);a.set_ylim(0,ylim);a.set_ylabel(unit);a.set_title(title,fontsize=13);a.grid(axis='y',alpha=.15);a.set_axisbelow(True)
 for x,v in enumerate(vals):a.text(x,v+.025*ylim,f'{v:g}',ha='center',fontsize=17,weight='bold')
f.text(.07,.17,'Reported TQ improvement: about 12×. TQ = Toffoli count × peak logical qubits.',fontsize=13);f.text(.07,.11,'A resource-product ratio is not a hardware speedup, physical-qubit estimate or full-application cost.',fontsize=12,color='#536972')
save(f,'quantum-20261015-costs',U2,'arXiv:2610.22367v1',['Extended Data Table 1','SI I.1'],{'Toffoli_millions':[5.1,.44],'logical_qubits':[1938,1837],'reported_TQ_factor':12,'baseline':'Khattar et al. reconstructed EEA decoder','axes_zero':True})
f=base('Point addition has a resource frontier, not one winner','Counts include reversible cleanup; source-specific failure guarantees and approximation budgets differ.','Gu et al., Table S3 / SI II')
a=f.add_axes([.12,.26,.78,.49],facecolor=BG);xs=[1.9,4,69.5,20.5];ys=[1446,935,838,843];names=['Binary gcd comparator','Divstep design','Packed Euclidean baseline','Specialized Euclidean'];a.scatter(xs,ys,s=130,c=[GRAY,GREEN,GRAY,PURPLE]);a.set_xscale('log');a.set_xlim(1,120);a.set_ylim(780,1580);a.set_xlabel('Toffoli gates (millions; logarithmic scale)');a.set_ylabel('Peak logical qubits (count)');a.grid(alpha=.2)
for x,y,n,offset in zip(xs,ys,names,[(12,-12),(12,12),(-150,80),(-170,20)]):a.annotate(n+'\n'+f'{x:g}M / {y}',(x,y),xytext=offset,textcoords='offset points',fontsize=11,arrowprops={'arrowstyle':'-','color':GRAY})
f.text(.07,.14,'The divstep design uses fewer qubits and more gates than the binary-gcd comparator.',fontsize=12);f.text(.07,.09,'Points are distinct constructions, not a measured time series. No physical quantum hardware was tested.',fontsize=11,color='#536972')
save(f,'quantum-20261015-tradeoff',U2,'arXiv:2610.22367v1',['Table S3','SI II.1–II.2'],{'Toffoli_millions':xs,'qubits':ys,'names':names,'same_failure_guarantees':False,'time_series':False})
print('Six factual graphics registered')
