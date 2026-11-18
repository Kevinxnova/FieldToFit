"""Redraw verified November 18 report facts; never writes to the CMS."""
from pathlib import Path
import hashlib,json
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[2]
P=ROOT/'frontend/public'
M=ROOT/'backend/knowledge/content'
SAFETY='https://deploymentsafety.openai.com/gpt-6-2-astra-sol'
PDF='https://cdn.openai.com/pdf/0e4b2466-0be0-4326-8bf7-117d809e14d2/Science%20at%20the%20Frontier.pdf'
LIC='Graphics © FieldToFit. Independent redraw of facts from the linked report.'
def font(size):return ImageFont.truetype(str(ROOT/'backend/daily_briefing/fonts/NotoSansSC.ttf'),size)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def manifest(name,key,v):
 p=M/name;obj=json.loads(p.read_text());obj[key]=v;p.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n')
def chart(name,title,subtitle,rows,maximum,source,unit='%'):
 im=Image.new('RGB',(1200,230+len(rows)*120),'#f3f7fc');d=ImageDraw.Draw(im)
 def put(x,y,t,s=27,c='#17334c'):d.text((x,y),t,font=font(s),fill=c)
 put(48,28,title,37);put(48,86,subtitle,24)
 for n,(label,val) in enumerate(rows):
  y=145+n*120;put(48,y,label,27)
  d.rounded_rectangle((48,y+48,48+max(2,val/maximum*950),y+79),radius=5,fill='#21796f')
  put(62+val/maximum*950,y+44,str(val)+unit,25)
 put(48,im.height-45,'FieldToFit redraw / 本站重绘 · '+('Science at the Frontier' if source==PDF else 'GPT-6.2 System Card'),20)
 p=P/'report-figures'/('nov18-'+name+'.png');im.save(p)
 url='/report-figures/'+p.name
 manifest('report-figures.json',url,dict(sha256=sha(p),source_urls=[source],version='2026-11',license=LIC))
def figures():
 chart('workplace','工作场景高严重度错误 / High-severity workplace actions','Valid scored rollouts · Figure 37 · Lower is better',[('GPT-6 Astra',1.20),('GPT-6.2 Astra',0.64),('GPT-6.1 Sol',1.32),('GPT-6.2 Sol',0.71)],1.6,SAFETY)
 chart('disclosure','已知障碍漏报 / Omission of a known obstacle','Blocker Deception · Figure 35 · Model-only condition',[('GPT-6 Astra',11.09),('GPT-6.2 Astra',22.28)],30,SAFETY)
 chart('ideas','构思采用率随阈值变化 / Ideation adoption by threshold','1,819 scientists · Appendix Table A3',[('At least 1 message / 至少1条',84.1),('At least 3 messages / 至少3条',67.6),('At least 10 messages / 至少10条',40.2)],100,PDF)
 chart('involvement','七日内后续核查 / Follow-up involvement within seven days','1,809 scientists · 125,947 initial requests · Figure 9',[('Overall / 总体',31.8),('Writing / 写作',38.0),('Analysis / 分析',34.4),('Research software / 研究软件',33.7)],50,PDF)

if __name__=='__main__':figures()
