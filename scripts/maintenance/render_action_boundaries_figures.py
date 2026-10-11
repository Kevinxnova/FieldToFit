"""Original qualitative diagrams for the owner's selected October 9 Anthropic report.

No incident counts, rates or effectiveness measurements are implied by geometry.
"""
import argparse,hashlib,json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
ROOT=Path(__file__).resolve().parents[2]
URL='https://www.anthropic.com/research/investigating-unintended-model-actions'
RIGHTS='图形 © FieldToFit；原始案例与报告归属见来源'
def render(font):
 colors={'bg':'#f5f7fc','ink':'#172641','muted':'#556378','line':'#d2dbea','blue':'#3658c9','teal':'#117f79'}
 fonts={s:ImageFont.truetype(font,s) for s in (28,32,36,40,46,54)}
 target=ROOT/'frontend/public/report-figures';target.mkdir(exist_ok=True)
 manifest_path=ROOT/'backend/knowledge/content/report-figures.json';manifest=json.loads(manifest_path.read_text())
 def page(n,title,sub):
  im=Image.new('RGB',(1500,1100),colors['bg']);d=ImageDraw.Draw(im)
  d.text((65,44),f'FIELD TO FIT  /  REPORT 0{n}',font=fonts[28],fill=colors['blue'])
  d.text((65,113),title,font=fonts[54],fill=colors['ink']);d.text((65,193),sub,font=fonts[32],fill=colors['muted'])
  d.line((65,951,1435,951),fill=colors['line'],width=2)
  d.text((65,979),'来源：Anthropic，2026-10-09官方调查 / FieldToFit 本站示意',font=fonts[28],fill=colors['muted'])
  d.text((65,1030),'并列分类与阅读结构；没有案例数、发生率或防护效果统计。',font=fonts[28],fill=colors['muted'])
  return im,d
 def box(d,rect,title,lines,fill='white'):
  d.rounded_rectangle(rect,20,fill=fill,outline=colors['line'],width=2);x,y=rect[:2]
  d.text((x+30,y+26),title,font=fonts[40],fill=colors['blue'])
  for j,line in enumerate(lines):d.text((x+30,y+94+j*49),line,font=fonts[32],fill=colors['ink'])
 def save(im,name,loc):
  p=target/f'anthropic-20261009-{name}.png';im.save(p,optimize=True)
  manifest['/report-figures/'+p.name]={'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'source_urls':[URL],'license':RIGHTS,'version':'Anthropic官方网页 · 2026-10-09','origin':'fieldtofit-redraw','statistics':{'kind':'qualitative reading diagram','incident_counts':None,'incidence_rates':None,'effectiveness_measurements':None,'locator':loc}}
 im,d=page(1,'任务受阻后，替代路径仍有行动边界','四类已观察行为并列呈现；类别相同宽度不表示发生频率相同')
 box(d,(65,276,725,530),'服务器执行',['所需工具不可用或受限','转向第三方服务的软件缺陷','边界：目标与可执行动作'])
 box(d,(775,276,1435,530),'真实表单',['模拟页失效或误判确认流程','练习操作变成真实提交','边界：测试目标与外部写入'])
 box(d,(65,572,725,826),'有条件的数据访问',['遇到令牌、费用或协议条件','改走另一条获取路径','边界：技术可达与使用授权'])
 box(d,(775,572,1435,826),'fetch 工具限制',['用短链接服务改变请求路径','绕过原工具的长度限制','边界：组合工具后的动作范围'])
 d.text((65,875),'本站判断：是否完成目标，与是否保持授权范围，需要分别检查。',font=fonts[32],fill=colors['teal'])
 save(im,'boundaries','Overview of behaviors：四个行为分类')
 im,d=page(2,'防护分层，证据范围也要分层','下列为作者的内部改进措施；不是全部Claude产品覆盖保证')
 rows=[('训练','减少绕过限制的奖励；扩展搜索／计算机操作训练'),('工具','收紧联网工具可以执行的动作'),('环境','停用／离线化部分评测，集中管理与隔离内部Agent'),('监测与响应','自动检测阻断，分类器、分层摘要及安全团队响应')]
 for n,(title,body) in enumerate(rows):
  y=275+n*112;d.rounded_rectangle((65,y,1435,y+91),15,fill='white',outline=colors['line'],width=2)
  d.text((95,y+23),title,font=fonts[36],fill=colors['blue']);d.text((385,y+26),body,font=fonts[32],fill=colors['ink'])
 box(d,(65,770,725,914),'作者已报告',['所列案例测试中全部拦截'],fill='#e7f4f1')
 box(d,(775,770,1435,914),'仍未知',['总体遗漏率、独立验证与完整评估'],fill='#edf0fb')
 save(im,'defenses','Remediation；Lessons and next steps')
 manifest_path.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--font',default='/System/Library/Fonts/STHeiti Light.ttc');render(p.parse_args().font)
