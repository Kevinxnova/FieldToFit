"""Original factual diagrams, with no digitized or invented experimental curves."""
from pathlib import Path
import json,hashlib
from PIL import Image,ImageDraw,ImageFont
P=Path(__file__).resolve().parents[2]
DEST=P/'frontend/public/report-figures';MAN=P/'backend/knowledge/content/report-figures.json'
SOURCE='https://microsoft.ai/news/frontier-pre-training-at-microsoft-ai/'
RIGHTS='Graphics © FieldToFit; source facts: Microsoft AI, Frontier Pre-training at Microsoft AI, 2026-10-15.'
font='/System/Library/Fonts/Supplemental/Arial.ttf'
def ft(n):return ImageFont.truetype(font,n)
def canvas(title,sub):
 im=Image.new('RGB',(1800,1080),'#f5f8f5');d=ImageDraw.Draw(im);d.text((75,64),title,font=ft(46),fill='#173b30');d.text((75,135),sub,font=ft(26),fill='#536d63');d.text((75,1015),'FieldToFit original diagram | Microsoft AI 2026-10-15 | Author evidence; not reproduced',font=ft(23),fill='#536d63');return im,d
def panel(d,box,title,lines):
 x,y,w,h=box;d.rounded_rectangle((x,y,x+w,y+h),radius=24,fill='#e6eee8',outline='#b6cbbf',width=2);d.text((x+30,y+30),title,font=ft(32),fill='#173b30')
 for n,line in enumerate(lines):d.text((x+30,y+94+n*48),line,font=ft(27),fill='#314f43')
def save(im,stem,stats):
 path=DEST/('mai-base-2-202610-'+stem+'.png');im.save(path)
 data=json.loads(MAN.read_text());data['/report-figures/'+path.name]={'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'source_urls':[SOURCE,'https://microsoft.ai/pdf/Frontier-Pre-training-at-Microsoft-AI.pdf?v=2'],'license':RIGHTS,'version':'Lab Notes 2026-10-15; no numbered revision','origin':'fieldtofit-redraw','statistics':stats};MAN.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
im,d=canvas('Scale the data exposure, too','Source scaling preserves dataset repetitions across a ladder; example from the report.')
panel(d,(75,245,770,360),'Small-scale run: 5T tokens',['Use 1/10 of the unique source data','Repeat that restricted source 8 times','Hold tokens per active parameter fixed'])
panel(d,(955,245,770,360),'Full-scale run: 50T tokens',['Use the full unique source dataset','Repeat the same source 8 times','Compare within a fixed training recipe'])
d.line((865,415,935,415),fill='#32664f',width=5);d.polygon([(935,415),(916,403),(916,427)],fill='#32664f')
panel(d,(75,690,1650,235),'What transfers is an experimental condition',['Keep repetition and regularization comparable before extrapolating.','The 8-repeat example is illustrative, not the repetition count of every dataset.'])
save(im,'source-scaling',{'example_tokens_T':[5,50],'source_fraction':[0.1,1],'example_repetitions':8,'scope':'Report illustrative example; not measured curve points'})
im,d=canvas('Read the 4.2–12.3x claim at equal BPB','A fitted pre-training FLOPs comparison, not the bill for the final full-size training run.')
panel(d,(75,245,780,405),'Reference: DeepSeek-V4-Pro-Base',['Take its BPB on each held-out set','Use its reported training compute','Four independent BPB-versus-FLOPs fits','Code, QA, STEM and Math remain separate'])
panel(d,(945,245,780,405),'MAI ladder: matched quality',['Estimate FLOPs to reach the same BPB','Include the known MAI-Base-2 endpoint','The matching point lies inside the fit','Reported ratio spans 4.2–12.3x'])
panel(d,(75,735,1650,200),'Boundary',['Not an API price cut, not a 4.2–12.3x reduction in actual total training cost.'])
save(im,'efficiency-scope',{'efficiency_range':[4.2,12.3],'unit':'matched-BPB pretraining FLOPs ratio','baseline':'DeepSeek-V4-Pro-Base','scope':'Four independent fitted held-out tasks; not actual total cost'})
im,d=canvas('Fixed memory trades overflow for extra rounds','A qualitative reading diagram for multi-round dropless MoE, with separate system metrics.')
panel(d,(75,235,500,380),'Dispatch',['Fixed per-expert token capacity','Experts grouped on each rank','Group spare capacity can help'])
panel(d,(650,235,500,380),'Compute + collect',['Process fitting tokens now','Keep overflow for later rounds','Do not drop excess tokens'])
panel(d,(1225,235,500,380),'Overflow round',['More rounds mean more work','Steady state targets one round','Capacity trades memory for work'])
panel(d,(75,705,780,220),'Whole-run MFU: 21%',['Normalized to 2.5 PFLOPS per GB200','Excludes recomputation and optimizer FLOPs'])
panel(d,(945,705,780,220),'Whole-run goodput: 89%',['Fraction of time training made progress','Different denominator from MFU'])
save(im,'system-scope',{'whole_run_MFU_percent':21,'goodput_percent':89,'MFU_normalization_PFLOPS':2.5,'scope':'Qualitative MoE diagram; metrics are not directly comparable'})
print('Rendered and registered three original factual diagrams.')
