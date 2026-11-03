"""Independent explanatory diagrams from pinned official documentation; no benchmark data."""
import os
from pathlib import Path
os.environ.setdefault('MPLCONFIGDIR','/private/tmp/ftf-deepseek-superagent-20261102/mpl-cache')
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
OUT=Path(__file__).resolve().parents[2]/'frontend/public/report-figures'
BG='#f5f7fb';INK='#17283f';BLUE='#e3edfc';GREEN='#e0f0e9';AMBER='#fff0d5'
def canvas(title,sub):
 f,a=plt.subplots(figsize=(14,7.5),dpi=120);f.patch.set_facecolor(BG);a.set_facecolor(BG);a.set(xlim=(0,14),ylim=(0,7.5));a.axis('off');f.subplots_adjust(left=0,right=1,top=1,bottom=0)
 a.text(.55,6.95,title,color=INK,fontsize=23,weight='bold');a.text(.55,6.5,sub,color='#52647d',fontsize=12)
 a.text(.55,.3,'FieldToFit explanatory diagram · v0.1.0 / commit 6337fc8 · not an experimental chart',color='#52647d',fontsize=10)
 return f,a
def box(a,x,y,w,h,title,body='',color=BLUE):
 a.add_patch(FancyBboxPatch((x,y),w,h,boxstyle='round,pad=0.02,rounding_size=0.12',facecolor=color,edgecolor='#b6c6db',linewidth=1))
 a.text(x+w/2,y+h-.34,title,ha='center',va='center',fontsize=15,weight='bold',color=INK)
 if body:a.text(x+w/2,y+(h-.3)/2,body,ha='center',va='center',fontsize=12,color=INK,linespacing=1.5)
def arrow(a,p,q,label='',bend=0):
 a.annotate('',q,p,arrowprops={'arrowstyle':'->','color':'#466783','lw':1.8,'connectionstyle':f'arc3,rad={bend}'})
 if label:a.text((p[0]+q[0])/2,(p[1]+q[1])/2+.15,label,ha='center',fontsize=10,color='#466783',bbox={'facecolor':BG,'edgecolor':'none','pad':2})
def save(f,name):OUT.mkdir(parents=True,exist_ok=True);f.savefig(OUT/f'deepseek-superagent-{name}.png',dpi=120);plt.close(f)
def main():
 f,a=canvas('One task identity across conversations','Task state, execution sessions and delivery records are separate objects.')
 box(a,.6,4,2.25,1.6,'Sources','GitHub\nFeishu (optional)');box(a,3.55,4,2.25,1.6,'New-work Eval','Gate + assessment\nPolicy version');box(a,6.5,4,2.5,1.6,'Ticket + Mandate','Scope + authority\nPersistent identity',color=GREEN);box(a,9.75,4,3.55,1.6,'Executor','Own session + directory\nAssignment / report')
 for p,q in [((2.85,4.8),(3.55,4.8)),((5.8,4.8),(6.5,4.8)),((9,4.8),(9.75,4.8))]:arrow(a,p,q)
 box(a,3.55,1.25,3,1.5,'Subscribed Thread','Follow-up context\nNo new authority',color=AMBER);box(a,9,1.25,4.3,1.5,'Outbox + original channel','Pending / sent / dropped\nResult or one concrete question',color=GREEN)
 arrow(a,(1.7,4),(3.55,2.1),'follow-ups',.1);arrow(a,(6.55,2),(10.2,4),'direct to existing work',-.1);arrow(a,(11.5,4),(11.5,2.75))
 a.plot([9,8.7,.3,.3],[2,.8,.8,4.8],color='#466783',lw=1.8);arrow(a,(.3,4.8),(.6,4.8));a.text(4.5,.86,'human-facing delivery',ha='center',fontsize=10,color='#466783',bbox={'facecolor':BG,'edgecolor':'none','pad':2})
 save(f,'flow')
 f,a=canvas('Admission and continuation have different jobs','The right to start work is distinct from the context needed to continue it.')
 box(a,.65,4.3,3.1,1.45,'New event','Source / actor / scope');box(a,4.55,4.3,3.1,1.45,'Deterministic gate','Explicit or inferred?');box(a,8.45,4.3,4.8,1.45,'Explicit request','May proceed in all accept modes',color=GREEN);arrow(a,(3.75,5),(4.55,5));arrow(a,(7.65,5),(8.45,5))
 box(a,4.55,1.15,3.1,2.1,'Inferred candidate','off: not admitted\nobserve: record only\nauto: rule assessment',color=AMBER);box(a,8.45,1.15,4.8,2.1,'Existing task subscription','Context reaches Ticket directly\nMandate still limits the scope\nOut-of-scope requests handed back',color=GREEN);arrow(a,(6.1,4.3),(6.1,3.25),'inferred');a.text(.65,2.55,'DEFAULTS',fontsize=12,weight='bold',color=INK);a.text(.65,2.1,'Allowed + addressed:\nexplicit request\n\nUnlisted: ignored\nunless configured otherwise',fontsize=12,color=INK,va='top',linespacing=1.4)
 save(f,'authority')
 f,a=canvas('Durable recovery is more than restarting a chat','Local transactions and receipts support recovery; external delivery still has a boundary.')
 box(a,.65,4.05,3.25,1.7,'1 · Commit','Ticket state + effect\nReceipt: pending',color=GREEN);box(a,5.35,4.05,3.25,1.7,'2 · Execute effect','Call external Source\nRetry with backoff');box(a,10,4.05,3.25,1.7,'3 · Settle receipt','sent or dropped\nKeep record',color=GREEN);arrow(a,(3.9,4.9),(5.35,4.9));arrow(a,(8.6,4.9),(10,4.9))
 box(a,.65,1.25,5.4,1.7,'Recovery record','Sessions · directories · subscriptions\nPending inputs · stored effects');box(a,7.1,1.25,6.15,1.7,'Boundary to verify','Send succeeded + crash before settlement?\nDo not infer cross-system exactly-once.',color=AMBER);arrow(a,(9.3,4.55),(10.2,2.95),'crash window',-.1);arrow(a,(3.35,2.95),(2.3,4.05),'resume, then inspect')
 save(f,'recovery')
if __name__=='__main__':main()
