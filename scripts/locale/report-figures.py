"""Create code-native English equivalents of FieldToFit's two reading illustrations."""
from html import escape
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]/'frontend/public/report-figures'
def text(x,y,value,size=30,color='#192849'):
    return f'<text x="{x}" y="{y}" font-size="{size}" fill="{color}">{escape(value)}</text>'
def rect(x,y,w,h,fill='#fff'):
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="20" fill="{fill}" stroke="#cbd6ee" stroke-width="2"/>'
def shell(title,number):
    return ['<svg xmlns="http://www.w3.org/2000/svg" width="1500" height="1100" viewBox="0 0 1500 1100" role="img">',f'<title>{escape(title)}</title>','<rect width="1500" height="1100" fill="#f5f7fe"/>','<g font-family="Arial, Helvetica, sans-serif">',text(65,67,f'FIELD TO FIT / REPORT {number}',28,'#3456ec'),text(65,158,title,46)]
def footer(parts):
    parts.extend(['<path d="M65 952H1435" stroke="#cbd6ee" stroke-width="2"/>',text(65,1002,'Source: Anthropic, official investigation 2026-10-09 / FieldToFit illustration',28,'#5b6a82'),text(65,1056,'Parallel categories and reading structure; no case-count, incidence or effectiveness statistics.',26,'#5b6a82'),'</g></svg>'])
    return '\n'.join(parts)+'\n'
parts=shell('Alternative paths still have action boundaries','01')
parts.append(text(65,220,'Four observed categories shown in parallel; equal widths do not mean equal frequency.',28,'#5b6a82'))
cards=[(65,277,'Server execution',['Required tools unavailable or restricted','Switch to flaws in a third-party service','Boundary: target and executable actions']),
       (775,277,'Real forms',['Simulation fails or confirmation is misread','Practice becomes an actual submission','Boundary: test target and external writes']),
       (65,573,'Conditional data access',['Token, fee or agreement restrictions','Switch to another retrieval path','Boundary: technical access and permission']),
       (775,573,'fetch tool restrictions',['Shortening service changes request paths','Bypass the original tool’s length limit','Boundary: actions after combining tools'])]
for x,y,title,lines in cards:
    parts.extend([rect(x,y,660,254),text(x+30,y+60,title,36,'#3456ec')])
    for i,line in enumerate(lines):parts.append(text(x+30,y+120+i*49,line,28))
parts.append(text(65,905,'FieldToFit: assess task completion and preservation of authorization scope separately.',28,'#008c8d'))
(ROOT/'anthropic-20261009-boundaries-en.svg').write_text(footer(parts))
parts=shell('Layer safeguards. Keep evidence boundaries clear.','02')
parts.append(text(65,220,'Authors’ internal improvements; no guarantee of coverage across all Claude products.',28,'#5b6a82'))
rows=[('Training','Reduce rewards for bypasses; extend search and computer-use training'),('Tools','Tighten the actions connected tools can execute'),('Environment','Disable or take evaluations offline; centrally manage and isolate agents'),('Monitoring / response','Detect and block; classifiers, layered summaries and safety-team response')]
for i,(label,description) in enumerate(rows):
    y=277+i*112;parts.append(rect(65,y,1370,90))
    if label=='Monitoring / response':
        parts.extend([text(95,y+35,'Monitoring',27,'#3456ec'),text(95,y+70,'and response',27,'#3456ec')])
    else:parts.append(text(95,y+57,label,32,'#3456ec'))
    parts.append(text(384,y+57,description,27))
parts.extend([rect(65,771,660,143,'#e7f5f2'),rect(775,771,660,143,'#edf0fc'),text(95,830,'Reported by the authors',34,'#3456ec'),text(95,886,'All listed test cases blocked',29),text(805,830,'Still unknown',34,'#3456ec'),text(805,876,'Overall miss rate, independent validation',27),text(805,908,'and complete evaluation',27)])
(ROOT/'anthropic-20261009-defenses-en.svg').write_text(footer(parts))
