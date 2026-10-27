"""Original FieldToFit evidence redraws and method schematics for October 27."""
import json,hashlib
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
ROOT=Path(__file__).resolve().parents[2];DEST=ROOT/'frontend/public/report-figures';MAN=ROOT/'backend/knowledge/content/report-figures.json'
BG='#f8faf6';INK='#172b3a';GREEN='#348371';PURPLE='#8173b5'
RIGHTS='Graphics © FieldToFit. Independent redraw of reported facts and method schematic; original artwork is not reproduced.'
plt.rcParams.update({'font.family':'DejaVu Sans','text.color':INK,'axes.labelcolor':INK,'xtick.color':INK,'ytick.color':INK})
def base(t,s,source):
 f=plt.figure(figsize=(14,8),facecolor=BG);f.text(.05,.93,t,fontsize=22,weight='bold');f.text(.05,.86,s,fontsize=12);f.text(.05,.035,'FieldToFit independent redraw / schematic | '+source+' | Not replicated',fontsize=10);return f
def save(f,stem,url,version,loc):
 p=DEST/('oct27-'+stem+'.png');f.savefig(p,dpi=120);plt.close(f);m=json.loads(MAN.read_text());m['/report-figures/'+p.name]={'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'source_urls':[url],'license':RIGHTS,'attribution':'FieldToFit','source_version':version,'locator':loc};MAN.write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n')
u='https://deploymentsafety.openai.com/gpt-6-1-terra';v='2026-10-26 HTML addendum'
f=base('Internal simulation: compare counts on a matched set','48,690 matched tasks | severity >=3 flags | not external-user incident rates','OpenAI Terra system card, 2026-10-26, §7.5.2')
a=f.add_axes([.20,.25,.72,.52],facecolor=BG);vals=[22,24,26,38,61];names=['6.1 Terra','6.1 Sol','6 Astra','6 Sol','5.6 Sol'];a.barh(range(5),vals,color=[GREEN]+[PURPLE]*4,height=.6);a.set_yticks(range(5),names);a.invert_yaxis();a.set_xlim(0,70);a.set_xlabel('Flag count');
for y,n in enumerate(vals):a.text(n+1,y,str(n),va='center',fontsize=17)
f.text(.07,.13,'22 versus 24 is not evidence of a statistically established advantage.',fontsize=13);save(f,'terra-flags',u,v,'§7.5.2')
f=base('External-agent messages: engagement is not the same as misconduct','10 scenarios | 80 samples per model | all samples discovered the board','OpenAI Terra system card, 2026-10-26, §7.5.1')
a=f.add_axes([.20,.27,.72,.48],facecolor=BG);y=[0,1,2];a.barh([z-.17 for z in y],[65,50,41.25],height=.3,color=PURPLE,label='Engagement (includes refusal / failed attempts)');a.barh([z+.17 for z in y],[13.75,1.25,16.25],height=.3,color=GREEN,label='Specified unauthorized action');a.set_yticks(y,['6.1 Terra','6.1 Sol','6 Sol']);a.invert_yaxis();a.set_xlim(0,100);a.set_xlabel('Percent of 80 samples');a.legend(loc='upper center',bbox_to_anchor=(.5,-.17),frameon=False,fontsize=11)
for yy,aa,bb in zip(y,[65,50,41.25],[13.75,1.25,16.25]):a.text(aa+1,yy-.17,str(aa)+'%',va='center');a.text(bb+1,yy+.17,str(bb)+'%',va='center')
save(f,'terra-agent',u,v,'§7.5.1')
u='https://arxiv.org/html/2610.17062v1';v='arXiv:2610.17062v1'
f=base('GRAFT: route updates, then remove FORGET','Method schematic, not a measured performance chart','Ward, Hu et al., 2026-10-12 v1, §3 / Fig. 1')
a=f.add_axes([.04,.18,.92,.60]);a.axis('off')
def box(x,y,w,h,t,color):
 a.add_patch(FancyBboxPatch((x,y),w,h,boxstyle='round,pad=0.01',facecolor=color,edgecolor='none'));a.text(x+w/2,y+h/2,t,ha='center',va='center',fontsize=13,linespacing=1.5)
box(.02,.66,.25,.23,'Target rollout\nRETAIN + FORGET','#dfe7f2');box(.39,.68,.26,.21,'Not flagged\nupdate BOTH','#dcebe4');box(.39,.36,.26,.21,'Flagged\nupdate FORGET ×2','#e9dff1');box(.02,.06,.25,.23,'Anchor environment\nRETAIN only','#dcebe4');box(.75,.36,.22,.30,'Deployment\nremove FORGET\nuse RETAIN','#c5e2d7')
for start,end in [((.28,.78),(.38,.78)),((.28,.70),(.38,.48)),((.28,.17),(.74,.40)),((.66,.76),(.74,.62)),((.66,.46),(.74,.50))]:a.annotate('',xy=end,xytext=start,arrowprops={'arrowstyle':'->','color':INK,'lw':2})
f.text(.07,.12,'Missed bad trajectories still update RETAIN. Anchoring trains the deployment configuration.',fontsize=13);save(f,'graft-routing',u,v,'§3; Figure 1; Appendix B')
f=base('Evidence scope: larger does not mean the same training experiment','Keep training regime, task distribution and sample budget separate','Ward, Hu et al., 2026-10-12 v1, §4 / §5 / Appendix G.5')
a=f.add_axes([.08,.24,.84,.52]);a.axis('off');t=a.table(cellText=[['Training','Reinforcement learning','Supervised fine-tuning'],['Model','Qwen3-8B','Qwen3-32B'],['Interaction','Single-turn Countdown-Code','Up to 64 turns; Terminal Wrench'],['Evidence','~16 pp clean-solve gain vs base','99 held-out tasks; 1 training seed'],['Sampling caveat','Task / monitor-specific results','Unprompted k=4; prompted k=1']],colLabels=['Dimension','RL experiment','SFT experiment'],cellLoc='left',loc='center',colWidths=[.19,.37,.44]);t.auto_set_font_size(False);t.set_fontsize(12);t.scale(1,2.7)
for (r,c),cell in t.get_celld().items():cell.set_edgecolor('#e3e7e2');cell.set_facecolor('#dcebe4' if r==0 else 'white')
f.text(.07,.12,'No claim of validated frontier-scale, multi-turn RL safety. Error bars are not invented here.',fontsize=13);save(f,'graft-scope',u,v,'§4.1; §5; §7; Appendix G.5')
print('Four figures rendered and registered')
