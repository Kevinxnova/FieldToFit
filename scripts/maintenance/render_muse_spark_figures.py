"""Original evidence diagrams; no upstream figure artwork or invented measurements."""
from pathlib import Path
import json,hashlib
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
P=Path(__file__).resolve().parents[2];dest=P/'frontend/public/report-figures';manifest_path=P/'backend/knowledge/content/report-figures.json';manifest=json.loads(manifest_path.read_text())
METHOD='https://research.meta.ai/static/muse-spark-open-evaluation-methodology';CARD='https://huggingface.co/meta-models/Muse-Spark-Open-816B-A42B';BLOG='https://research.meta.ai/blog/muse-spark-open'
RIGHTS='Graphics © FieldToFit; source facts: Meta Muse Spark Open model card, evaluation methodology and launch post.'
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':12,'figure.facecolor':'#f7faf8','axes.facecolor':'#f7faf8','text.color':'#19382e'})
def canvas(title,sub):
 f=plt.figure(figsize=(12,7.2),dpi=150);f.text(.055,.93,title,fontsize=22,weight='bold');f.text(.055,.875,sub,fontsize=10,color='#536b61');f.text(.055,.035,'FieldToFit original diagram · Meta October 2026 sources · author claims, not independently reproduced',fontsize=9,color='#536b61');return f
def panel(f,x,y,w,h,title,lines,color='#e6eee8'):
 f.add_artist(FancyBboxPatch((x,y),w,h,boxstyle='round,pad=0.015',transform=f.transFigure,facecolor=color,edgecolor='#b8cabc',linewidth=1));f.text(x+.018,y+h-.055,title,fontsize=17,weight='bold')
 for k,line in enumerate(lines):f.text(x+.018,y+h-.115-k*.054,line,fontsize=11,color='#314e43')
def save(f,stem,stats,urls):
 path=dest/('muse-spark-open-202610-'+stem+'.png');f.savefig(path,dpi=150);plt.close(f)
 manifest['/report-figures/'+path.name]={'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'source_urls':urls,'license':RIGHTS,'version':'Muse Spark Open · 2026-10 model card and methodology / 2026-10-15 announcement','origin':'fieldtofit-redraw','statistics':stats}
f=canvas('Two agent scores, two different rules','Read the task set, tool access and scoring rule before comparing the headline values.')
panel(f,.065,.29,.415,.49,'OSWorld-Verified',[
 '361-task subset; Google Drive excluded','GUI only; no direct shell access','200 steps maximum per episode','4 attempts per task; average reward','Model-card value: 80.4','Not a guarantee on your desktop tasks'])
panel(f,.52,.29,.415,.49,'MCP-Atlas',[
 'Benchmark: 1,000 tasks (500 + 500)','36 MCP servers; 220 tools','Claim grades: 0 / 0.5 / 1','Pass: mean claim coverage >= 0.75','Model-card pass rate: 89.2%','Exact reported split not specified here'])
f.text(.065,.16,'The 1,000-task benchmark size is not a verified denominator for the reported 89.2%.',fontsize=12,weight='bold');f.text(.065,.105,'Do not average 80.4 and 89.2: mean task reward and a thresholded pass rate measure different things.',fontsize=11)
save(f,'task-scope',{'osworld':{'tasks':361,'attempts':4,'step_cap':200,'score':80.4,'unit':'mean task reward × 100','excluded':'Google Drive-dependent tasks'},'mcp_atlas':{'benchmark_tasks':1000,'public':500,'private':500,'servers':36,'tools':220,'claim_grades':[0,0.5,1],'pass_threshold':0.75,'reported_pass_rate_percent':89.2,'reported_split':'Not explicitly specified in the source methodology'},'locator':'Methodology pp2-3; model card Benchmarks','scope':'Different evaluation protocols; not a common accuracy scale'},[METHOD,CARD])
f=canvas('A benchmark table is also a provenance table','The document combines internal runs, independent leaderboards and provider self-reports.')
rows=[['AA Intelligence Index','Artificial Analysis snapshot','2026-10-07; v4.3'],['MCP-Atlas','Scale AI; Beam self-report','Split / grader / threshold matter'],['OSWorld-Verified','Meta runs; Kimi self-report','361 tasks; native coordinates'],['DeepSWE v1.1','Preferred harness by model','Muse Code / Claude Code / others'],['Terminal-Bench 2.1','AA; Beam self-report','89 tasks; Terminus 2 for AA runs'],['Video-MME v2','Internal runs','800 videos / 3,200 questions; no audio']]
a=f.add_axes([.055,.20,.89,.59]);a.axis('off');t=a.table(cellText=rows,colLabels=['Evaluation','Where the number comes from','A condition to preserve'],cellLoc='left',colLoc='left',colWidths=[.24,.33,.43],bbox=[0,0,1,1]);t.auto_set_font_size(False);t.set_fontsize(10)
for (row,col),cell in t.get_celld().items():cell.set_edgecolor('#c5d3ca');cell.set_facecolor('#dce8df' if row==0 else '#f8faf8' if row%2 else '#edf3ef');cell.PAD=.08
f.text(.055,.11,'A missing value means unavailable evidence here, not zero capability or a failed evaluation.',fontsize=11)
save(f,'provenance',{'rows':rows,'locator':'Methodology pp1-7','scope':'Source and setup map; no new ranking, no zero-imputation for missing results'},[METHOD])
f=canvas('Kernel gain and application gain are separate claims','Two scopes from the launch post; this is an evidence diagram, not one benchmark curve.')
panel(f,.07,.33,.405,.40,'Custom Helion kernels', ['1.03–3.95× kernel-level speedup','NVIDIA and AMD GPU results','Specific optimized kernel paths'],color='#e1ece3')
panel(f,.525,.33,.405,.40,'Whole inference path',['+3% end-to-end speedup','AMD MI350 result','Includes work outside those kernels'],color='#e8edf3')
f.text(.07,.19,'Do not multiply these values or translate them into an API price reduction.',fontsize=13,weight='bold');f.text(.07,.12,'The post does not establish the same gain for every GPU, model configuration or user workflow.',fontsize=11)
save(f,'runtime-scope',{'kernel_speedup_range':[1.03,3.95],'kernel_unit':'×','kernel_hardware':'NVIDIA and AMD','end_to_end_speedup_percent':3,'end_to_end_hardware':'AMD MI350','locator':'Launch post, Available Now','scope':'Separate author-reported scopes; not scaled bars or combined resource/cost arithmetic'},[BLOG])
manifest_path.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n');print('Rendered 3 original Muse Spark diagrams and registered exact asset hashes.')
