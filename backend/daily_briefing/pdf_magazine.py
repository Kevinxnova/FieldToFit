"""Portable magazine layout for quality editions; legacy PDFs use their renderer."""
from io import BytesIO
import hashlib
from html import escape as esc
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import BaseDocTemplate, PageTemplate, Frame, Paragraph, Spacer, PageBreak, Table, TableStyle, HRFlowable, KeepTogether, Image
from pypdf import PdfReader
from .schema import digest, LABELS
from .service import _public_copy
from .watchlist import GROUPS as GROUP_ROWS, GROUP_TICKERS
INK='#263c31'; GREEN='#40624b'; MUTED='#6d796c'; LINE='#d8ded2'; SOFT='#eef1e7'; PAPER='#fcfbf7'
W,H=A4;M=40;CW=W-M*2
GROUPS={k:(zh,en) for k,zh,en in GROUP_ROWS}
def tr(v,lang):return v[lang] if isinstance(v,dict) else v
def num(q):return '—' if q['price'] is None else f"{q['price']:,.0f}" if q['currency']=='KRW' else f"{q['price']:,.2f}"
def pct(q):return f"{q['change']:+.2f}%" if q['change'] is not None else '—'
def adapt(raw):
    return dict(raw,editorial=raw['takeaway'],sources={s['id']:s for s in raw['sources']},
        highlights=[{'story':s['id'],'title':s['highlight_title'],'text':s['highlight_summary']} for s in raw['stories'] if s['highlight']],
        stories=[dict(s,body=s['summary'],angle=s['analysis']) for s in raw['stories']],
        products=[{'name':p['name'],'version':p['version'],'date':p['release_date'],'channel':{'zh':('本期更新' if p['is_new'] else '近期版本')+' · '+p['release_channel'],'en':('New this issue' if p['is_new'] else 'Recent version')+' · '+p['release_channel']},'detail':p['changes'],'refs':p['source_ids']} for p in raw['products']],
        quotes=[dict(r,change=r['change_pct'],currency=m['currency'],market=m['id'].upper(),date=m['trade_date']) for group in GROUP_TICKERS.values() for ticker in group for m in raw['markets'] for r in m['rows'] if r['ticker']==ticker],
        market_intro=raw['market_overview']['title'],market_body=raw['market_overview']['summary'],market_note=raw['market_overview']['note'])
def render(raw, lang='zh', image=None, revision=1):
 D=adapt(raw)
 content_hash=digest(_public_copy(raw))
 pick=lambda z,e:z if lang=='zh' else e
 styles={}
 for name,size,leading,color in [('body',9.5,15.5,INK),('angle',8.8,14,MUTED),('small',7.3,11,MUTED),('source',7.1,10.5,GREEN),('h1',30,40,INK),('h2',20,29,INK),('h3',13.7,20,INK),('date',7.1,11,GREEN),('table',8,12,INK)]:
  styles[name]=ParagraphStyle(name,fontName='DailyNoto',fontSize=size,leading=leading,textColor=colors.HexColor(color),wordWrap='CJK' if lang=='zh' else None,spaceAfter=6,keepWithNext=name in ('h2','h3','date'),splitLongWords=True)
 if lang=='en':
  for k in ['h1','h2','h3']:styles[k].fontName='Times-Roman'
  for k in ['body','angle']:styles[k].fontSize-=.25;styles[k].leading-=.5
 def p(t,style='body',markup=False):return Paragraph(t if markup else esc(t).replace('\n','<br/>'),styles[style])
 def refs(ids):return [p('<link href="'+esc(D['sources'][i]['url'],quote=True)+'"><u>'+esc(tr(D['sources'][i]['title'],lang))+'</u></link>','source',True) for i in ids]
 def rule():
  r=HRFlowable(width='100%',thickness=.5,color=colors.HexColor(LINE),spaceBefore=6,spaceAfter=12);r.keepWithNext=True;return r
 def heading(n,key):return [Spacer(1,7),p(str(n).zfill(2)+' / '+LABELS[key][0 if lang=='zh' else 1],'h2'),rule()]
 def st(s):return [p(tr(s['date_label'],lang),'date'),p(tr(s['title'],lang),'h3'),p(tr(s['body'],lang)),p(tr(s['angle'],lang),'angle'),*refs(s['source_ids']),Spacer(1,12)]
 def spread(items):
  if not items:return p(pick('暂无合格内容。','No qualifying content.'))
  if len(items)>3:return KeepTogether([spread(items[i:i+2]) for i in range(0,len(items),2)])
  count=len(items);gap=18;cw=(CW-gap*(count-1))/count;cells=[];widths=[]
  for i,it in enumerate(items):
   if i:cells.append('');widths.append(gap)
   cells.append(it);widths.append(cw)
  t=Table([cells],colWidths=widths,hAlign='LEFT');t.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),0),('RIGHTPADDING',(0,0),(-1,-1),0),('TOPPADDING',(0,0),(-1,-1),0),('BOTTOMPADDING',(0,0),(-1,-1),0)]));
  if t.wrap(CW,H)[1]>H-108:return KeepTogether([flow for cell in items for flow in cell])
  return t
 def table(rows,widths):
  t=Table(rows,colWidths=widths,repeatRows=1,hAlign='LEFT');t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor(SOFT)),('VALIGN',(0,0),(-1,-1),'TOP'),('LINEBELOW',(0,0),(-1,-1),.4,colors.HexColor(LINE)),('LEFTPADDING',(0,0),(-1,-1),8),('RIGHTPADDING',(0,0),(-1,-1),8),('TOPPADDING',(0,0),(-1,-1),9),('BOTTOMPADDING',(0,0),(-1,-1),8)]));return t
 buffer=BytesIO()
 doc=BaseDocTemplate(buffer,pagesize=A4,leftMargin=M,rightMargin=M,topMargin=60,bottomMargin=48,title='FieldToFit AI Daily | '+raw['date'],author='FieldToFit',subject='Revision '+str(revision)+'; content_sha256='+content_hash,allowSplitting=True)
 def page(c,d):
  c.saveState();c.setFillColor(colors.HexColor(PAPER));c.rect(0,0,W,H,fill=1,stroke=0);c.setFillColor(colors.HexColor(INK));c.rect(0,H-5,W,5,fill=1,stroke=0);c.setFont('Times-Roman',14);c.drawString(M,H-32,'FieldToFit.');c.setFont('DailyNoto',7);c.drawRightString(W-M,H-31,raw['date']+' / r'+str(revision));c.setStrokeColor(colors.HexColor(LINE));c.line(M,H-43,W-M,H-43);c.line(M,33,W-M,33);c.setFillColor(colors.HexColor(MUTED));c.setFont('DailyNoto',7);c.drawString(M,20,pick('读懂重点，保留依据。','Read the essentials. Keep the sources.'));c.drawCentredString(W/2,20,content_hash[:12]);c.drawRightString(W-M,20,str(d.page).zfill(2));c.restoreState()
 full=Frame(M,48,CW,H-108,leftPadding=0,rightPadding=0,topPadding=0,bottomPadding=0,id='full')
 col=(CW-26)/2
 cols=[Frame(M+i*(col+26),48,col,H-108,leftPadding=0,rightPadding=0,topPadding=0,bottomPadding=0,id='col'+str(i)) for i in range(2)]
 doc.addPageTemplates([PageTemplate(id='full',frames=[full],onPage=page),PageTemplate(id='columns',frames=cols,onPage=page)])
 content=[p('FOR YOU / '+pick('今日重点 · 主编导读','HIGHLIGHTS · EDITOR’S LETTER'),'date'),p(tr(D['headline'],lang),'h1'),p(tr(D['intro'],lang)),p(tr(D['editorial'],lang),'small'),rule()]
 if image:
  from PIL import Image as PILImage
  im=PILImage.open(BytesIO(image));im.verify();im=PILImage.open(BytesIO(image))
  if im.width*im.height>30_000_000:raise ValueError('Cover image is too large')
  im.thumbnail((1400,1000));im=im.convert('RGB');out=BytesIO();im.save(out,format='JPEG',quality=85,optimize=True)
  height=min(180,CW*im.height/im.width);width=height*im.width/im.height
  content += [Image(BytesIO(out.getvalue()),width=width,height=height),p(tr(raw['image']['caption'],lang)+' · '+raw['image']['credit'],'small'),*refs([raw['image']['source_id']])]
 high=[]
 for h in D['highlights']:
  high.append([p(tr(h['title'],lang),'h3'),p(tr(h['text'],lang),'angle'),*refs(next(s for s in D['stories'] if s['id']==h['story'])['source_ids'])])
 content += [spread(high),Spacer(1,14)]
 content += heading(1,'companies')
 content += [spread([st(s) for s in D['stories'] if s['section']=='companies'])]
 # Product rows are kept intact; the rest follows content length naturally.
 content += [PageBreak(),*heading(2,'products')]
 rows=[[p(v,'small') for v in pick(['产品','版本 / 日期','变化与来源'],['Product','Version / date','Changes and sources'])]]
 for q in D['products']:rows.append([p(esc(tr(q['name'],lang)).replace('Physical Intelligence','Physical<br/>Intelligence'),'table',True),[p(tr(q['version'],lang),'table'),p(q['date']+'\n'+tr(q['channel'],lang),'small')],[p(tr(q['detail'],lang),'table'),*refs(q['refs'])]])
 content += [table(rows,[88,131,CW-219]),Spacer(1,10),*heading(3,'chips')]
 for s in [s for s in D['stories'] if s['section']=='chips']:content += st(s)
 content += [PageBreak()]
 for n,key in [(4,'robotics'),(5,'infrastructure')]:
  content += heading(n,key)+[spread([st(s) for s in D['stories'] if s['section']==key])]
 content += [PageBreak()]
 for n,key in [(6,'policy'),(7,'business')]:
  content += heading(n,key)+[spread([st(s) for s in D['stories'] if s['section']==key])]
 content += [PageBreak(),*heading(8,'markets'),p(tr(D['market_intro'],lang),'h3'),p(tr(D['market_body'],lang)),p(tr(D['market_note'],lang),'small')]
 for group,labels in GROUPS.items():
  content += [Spacer(1,10),p(labels[0 if lang=='zh' else 1],'h3')]
  rows=[[p(v,'small') for v in pick(['公司 / 代码','市场 / 币种','收盘','日涨跌','交易日 / 来源'],['Company / ticker','Market / FX','Close','Change','Session / source'])]]
  for q in [q for q in D['quotes'] if q['group']==group]:
   clr='#358277' if q['change'] is not None and q['change']<0 else '#a55940'
   rows.append([p(tr(q['name'],lang)+' / '+q['ticker'],'table'),p(q['market']+' / '+q['currency'],'table'),p(num(q),'table'),p('<font color="'+clr+'">'+pct(q)+'</font>','table',True),p(esc(q['date'] or '—')+'<br/>'+' · '.join('<link href="'+esc(D['sources'][i]['url'],quote=True)+'"><u>'+esc(tr(D['sources'][i]['title'],lang))+'</u></link>' for i in q['source_ids']),'source',True)])
  t=table(rows,[153,75,93,62,CW-383]);t.setStyle(TableStyle([('TOPPADDING',(0,0),(-1,-1),3),('BOTTOMPADDING',(0,0),(-1,-1),2)]));content += [t]
 content += [Spacer(1,8),p(tr(D['closing'],lang),'angle')]
 doc.build(content)
 data=buffer.getvalue()
 return {'bytes':data,'pages':len(PdfReader(BytesIO(data)).pages),'sha256':hashlib.sha256(data).hexdigest()}
