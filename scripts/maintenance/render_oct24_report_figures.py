"""Original factual diagrams for the selected October 24 report analyses."""
import json,hashlib
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch,FancyArrowPatch
ROOT=Path(__file__).resolve().parents[2];DEST=ROOT/'frontend/public/report-figures';MAN=ROOT/'backend/knowledge/content/report-figures.json'
BG='#f8faf6';INK='#172b3a';GREEN='#348371';PURPLE='#8173b5'
plt.rcParams.update({'font.family':'DejaVu Sans','text.color':INK,'axes.labelcolor':INK,'xtick.color':INK,'ytick.color':INK})
U1='https://www.anthropic.com/research/alignment-assessment-ukaisi';U2='https://openai.com/index/securing-our-frontier-model-training-environment/'
RIGHTS='Graphics © FieldToFit. Independent explanation of author-reported facts; original graphics are not reproduced.'
def base(title,sub,source):
 f=plt.figure(figsize=(14,8),facecolor=BG);f.text(.05,.92,title,fontsize=23,weight='bold');f.text(.05,.85,sub,fontsize=12);f.text(.05,.035,'FieldToFit independent graphic | '+source+' | Not independently reproduced',fontsize=10);return f
def save(f,name,url,loc,stats):
 p=DEST/(name+'.png');f.savefig(p,dpi=120);plt.close(f);m=json.loads(MAN.read_text());m['/report-figures/'+p.name]={'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'source_urls':[url],'license':RIGHTS,'version':'2026-10-23; unnumbered web report','origin':'fieldtofit-redraw','statistics':{'locators':[loc],**stats}};MAN.write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n')
def boxes(f,labels,footer,connect=True):
 a=f.add_axes([.04,.28,.92,.46]);a.set(xlim=(0,1),ylim=(0,1));a.axis('off')
 n=len(labels);w=.86/n;gap=.1/(n-1) if n>1 else 0
 for i,t in enumerate(labels):
  x=.02+i*(w+gap);a.add_patch(FancyBboxPatch((x,.22),w,.62,boxstyle='round,pad=0.008',facecolor='#e3efe7',edgecolor=GREEN));a.text(x+w/2,.53,t,ha='center',va='center',fontsize=13,linespacing=1.7)
  if connect and i<n-1:a.add_patch(FancyArrowPatch((x+w,.53),(x+w+gap-.005,.53),arrowstyle='-|>',mutation_scale=14,color=GREEN))
 f.text(.065,.18,footer,fontsize=13)
f=base('Three evidence layers, three different denominators','A replay of one transcript is not an independent full-task experiment.','Anthropic Alignment, 2026-10-23')
boxes(f,['Original testing\n43 runs\n9 unsanctioned runs','Selected evidence\n1 detailed transcript\n8 lighter reviews','Conditional replays\nEdited contexts\nSimulated tools'],'Original tests: internet enabled and some general-release safeguards disabled.')
save(f,'aisi-20261023-method',U1,'Methods; opening',{'original_runs':43,'unsanctioned_runs':9,'deep_transcripts':1,'lighter_reviews':8})
f=base('An early intervention changes the sampled continuation','Outcome: searching for an external repository over the next 12 turns from specified notes.','Anthropic Alignment, 2026-10-23')
a=f.add_axes([.15,.32,.70,.41],facecolor=BG);a.bar(['Original compaction notes','5 reasoning passages edited\nthen notes regenerated'],[83,13],color=['#8e9ca3',GREEN],width=.45);a.set_ylim(0,100);a.set_ylabel('Sampled trajectories (%)');a.grid(axis='y',alpha=.15);a.set_axisbelow(True)
for x,v in enumerate([83,13]):a.text(x,v+3,str(v)+'%',ha='center',fontsize=22,weight='bold')
f.text(.065,.16,'Conditional comparison, not a product incident rate or a measure of successful harm.',fontsize=13);f.text(.065,.10,'No invented confidence intervals; the separate 87% replay baseline is not pooled here.',fontsize=12)
save(f,'aisi-20261023-early',U1,'Why did Claude Mythos 5 begin the attack?',{'percent':[83,13],'turn_window':12,'edited_passages':5,'error_bars':False,'pooled_baselines':False})
f=base('Starting, redirecting and stopping are different endpoints','Do not combine different starting points, inserted messages or observation windows.','Anthropic Alignment, 2026-10-23')
boxes(f,['Initiation\nBegins an\nout-of-scope path','Redirection\nWorks in scope\npossibly temporarily','Stopping\nCeases the\nout-of-scope path'],'Compaction can preserve mistaken assumptions; authorization needs independent checks.',False)
f.text(.065,.11,'The source’s 67% / 62% internal-model discrepancy is disclosed, not charted as resolved.',fontsize=12)
save(f,'aisi-20261023-boundaries',U1,'Why did Claude Mythos 5 not stop the attack?; newer models',{'kind':'editorial_reading_diagram','unresolved_source_rates':[67,62]})
f=base('Containment is a set of boundaries','Each layer addresses a different route beyond explicitly authorized resources.','OpenAI, 2026-10-23')
boxes(f,['Offline resources\nIndexed and\ncached web','Compute isolation\nContainers\nand VMs','Network perimeter\nCloud controls\nRestricted egress'],'Monitoring and stopping span the layers; necessary service connections still exist.')
f.text(.065,.11,'Conceptual reading diagram, not a complete infrastructure map or physical air gap.',fontsize=12)
save(f,'containment-20261023-layers',U2,'Our new approach to model containment',{'kind':'conceptual_diagram','air_gapped':False})
f=base('Three objectives under attacker-favorable conditions','Purpose: discover defensive gaps, not score unaided model cyber capability.','OpenAI, 2026-10-23')
boxes(f,['External boundary\nReach a controlled\nexternal server','Internal boundary\nAccess unauthorized\ninternal resources','Agent isolation\nCommunicate across\nseparate environments'],'Supplied: source code, configuration and weakness hints; some tests assume host compromise.',False)
f.text(.065,.11,'Tests use isolated replicas, monitoring and out-of-scope pausing.',fontsize=12)
save(f,'containment-20261023-tests',U2,'Red-teaming containment at scale',{'objectives':3,'unaided_benchmark':False})
f=base('From candidate finding to maintained control','A reading framework for the reported process; counts are not interchangeable.','OpenAI, 2026-10-23')
boxes(f,['Candidate\nModel proposes\na possible gap','Triage + reproduce\nDeduplicate\nVerify behavior','Fix + recheck\nPatch/configure\nRetest and monitor'],'Changing models, targets and windows prevent a controlled compute-to-finding inference.')
f.text(.065,.11,'No curve digitization, invented vulnerability count or absolute-safety claim.',fontsize=12)
save(f,'containment-20261023-evidence',U2,'What our red-teaming agents found; cumulative curve caption',{'kind':'editorial_reading_diagram','curve_reconstructed':False})
print('Six figures generated and registered.')
