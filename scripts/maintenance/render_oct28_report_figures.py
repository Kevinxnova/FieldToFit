"""Original FieldToFit redraws of reported Qwen-Audio-3.1-ASR v1 facts."""
import json,hashlib
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[2];DEST=ROOT/'frontend/public/report-figures';MAN=ROOT/'backend/knowledge/content/report-figures.json'
BG='#f8faf6';INK='#172b3a';GREEN='#348371';PURPLE='#8173b5';RIGHTS='Graphics © FieldToFit. Independent redraw of reported facts and method schematic; original artwork is not reproduced.'
URL='https://arxiv.org/html/2610.28711v1';VERSION='arXiv:2610.28711v1'
plt.rcParams.update({'font.family':'DejaVu Sans','text.color':INK,'axes.labelcolor':INK,'xtick.color':INK,'ytick.color':INK})
def base(t,s,loc):
 f=plt.figure(figsize=(14,8),facecolor=BG);f.text(.05,.93,t,fontsize=22,weight='bold');f.text(.05,.865,s,fontsize=12);f.text(.05,.035,'FieldToFit independent redraw | Qwen-Audio-3.1-ASR v1, 2026-10-20 | '+loc+' | Not replicated',fontsize=10);return f
def save(f,stem,loc):
 p=DEST/('oct28-asr-'+stem+'.png');f.savefig(p,dpi=120);plt.close(f);m=json.loads(MAN.read_text());m['/report-figures/'+p.name]={'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'source_urls':[URL],'license':RIGHTS,'attribution':'FieldToFit','source_version':VERSION,'locator':loc};MAN.write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n')
f=base('Choose the deployment profile before the feature','SD: recording-local speaker labels + time | AU: general audio understanding','Table 1')
a=f.add_axes([.05,.24,.90,.53]);a.axis('off');data=[['Flash-Filetrans','Yes','—','—','Yes','Yes','—'],['Flash-Streaming','Yes','—','—','Yes','Yes','—'],['Flash-Message','Yes','—','—','Yes','Yes','Yes'],['Flash (non-streaming)','Yes','Yes','—','Yes','Yes','Yes'],['Next (non-streaming)','Yes','Yes','Yes','Yes','Yes','Yes']];tb=a.table(cellText=data,colLabels=['Profile','ASR','SD','AU','Context','Hotwords','Polishing'],colWidths=[.30]+[.116]*6,cellLoc='center',loc='center');tb.auto_set_font_size(False);tb.set_fontsize(12);tb.scale(1,3.3)
for (r,c),cell in tb.get_celld().items():cell.set_edgecolor('#dce3dc');cell.set_facecolor('#cde5d8' if r==0 else '#eef4ee' if c==0 else 'white')
f.text(.06,.13,'Capability support does not establish account access, price or real-world identity recognition.',fontsize=13);save(f,'profiles','Table 1; §4')
f=base('Speaker-attributed transcription: Next does not win every set','Approximately 4-minute chunks | cpWER (%) | lower is better','Table 7')
a=f.add_axes([.10,.25,.84,.51]);names=['AISHELL-4','AliMeeting-test','MLC-SLM','MagicData-RAMC'];basevals=[15.02,15.78,12.35,13.32];nxt=[13.51,12.04,12.60,13.58];x=list(range(4));a.bar([z-.18 for z in x],basevals,width=.34,color=PURPLE,label='Qwen-Audio-3.1-ASR');a.bar([z+.18 for z in x],nxt,width=.34,color=GREEN,label='Next');a.set_xticks(x,names);a.set_ylim(0,19);a.set_ylabel('cpWER (%)');a.legend(loc='upper center',bbox_to_anchor=(.5,-.13),ncol=2,frameon=False)
for z,v,w in zip(x,basevals,nxt):a.text(z-.18,v+.25,f'{v:.2f}',ha='center');a.text(z+.18,w+.25,f'{w:.2f}',ha='center')
f.text(.06,.13,'DER and WER are separate metrics. Chunked results do not validate hour-long speaker consistency.',fontsize=12);save(f,'diarization','§5.8 Table 7')
f=base('Latency results depend on the deployment conditions','10 concurrent streams | Qwen: self-hosted H100 | Doubao: API | comparable network latency assumed','Table 6')
a=f.add_axes([.20,.29,.72,.47]);labels=['Text emission','First character','Last character'];q=[220,100,103];d=[530,570,307];y=list(range(3));a.barh([z-.18 for z in y],q,height=.32,color=GREEN,label='Qwen Flash-Message');a.barh([z+.18 for z in y],d,height=.32,color=PURPLE,label='Doubao Streaming ASR 2.0');a.set_yticks(y,labels);a.invert_yaxis();a.set_xlim(0,660);a.set_xlabel('Latency (ms), lower is better');a.legend(loc='upper center',bbox_to_anchor=(.5,-.19),ncol=2,frameon=False)
for yy,v,w in zip(y,q,d):a.text(v+7,yy-.18,str(v),va='center');a.text(w+7,yy+.18,str(w),va='center')
f.text(.06,.14,'Different infrastructure: not a matched-hardware production throughput or cost comparison.',fontsize=13);save(f,'latency','§5.7 Table 6')
print('Three factual redraws rendered and registered')
