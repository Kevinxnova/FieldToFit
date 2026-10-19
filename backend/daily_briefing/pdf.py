"""Portable A4 magazine renderer; flowables paginate instead of clipping copy."""
from io import BytesIO
from pathlib import Path
from html import escape
import hashlib
import threading
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import BaseDocTemplate, PageTemplate, Frame, Paragraph, Spacer, PageBreak, NextPageTemplate, Table, TableStyle, Image, HRFlowable, KeepTogether
from pypdf import PdfReader
from .schema import project, news_sections, edition_sections, LABELS

_LOCK=threading.Lock()
INK='#253E32';GREEN='#315E49';MUTED='#647568';PAPER='#FAF8F2';SOFT='#EDF1E7';LINE='#CED8CA'
W,H=A4;M=40;CW=W-2*M

def render(raw, lang='zh', image=None, revision=1):
    from .service import _public_copy
    from .schema import digest
    content_hash=digest(_public_copy(raw))
    with _LOCK:
        if 'DailyNoto' not in pdfmetrics.getRegisteredFontNames():
            pdfmetrics.registerFont(TTFont('DailyNoto',str(Path(__file__).with_name('fonts')/'NotoSansSC.ttf')))
            pdfmetrics.registerFontFamily('DailyNoto',normal='DailyNoto',bold='DailyNoto',italic='DailyNoto',boldItalic='DailyNoto')
    if raw.get('layout_version')==3:
        from .pdf_magazine import render as magazine_render
        return magazine_render(raw,lang,image,revision)
    d=project(raw,lang);modern=raw.get('layout_version')==2;pick=lambda zh,en:zh if lang=='zh' else en
    styles={}
    for name,size,leading,color in [('body',9.4,15.5,INK),('small',7.7,12,MUTED),('source',7.6,11.8,GREEN),('h1',30,41,INK),('h2',23,32,INK),('h3',14,21,INK),('kicker',8.2,13,GREEN),('metric',31,41,GREEN)]:
        styles[name]=ParagraphStyle(name,fontName='DailyNoto',fontSize=size,leading=leading,textColor=colors.HexColor(color),wordWrap='CJK' if lang=='zh' else None,spaceAfter=7,keepWithNext=name in ('h2','h3','kicker'),splitLongWords=True)
    if lang=='en':
        for name,size,leading in [('body',9,14),('small',7.5,11.5),('source',7.1,10.5),('h3',13,18.5)]:
            styles[name].fontSize=size;styles[name].leading=leading;styles[name].spaceAfter=6
    def p(s,style='body',markup=False):return Paragraph(s if markup else escape(s).replace('\n','<br/>'),styles[style])
    sources={s['id']:s for s in d['sources']}
    def refs(ids):return [p('<link href="'+escape(sources[i]['url'],quote=True)+'"><u>'+escape(sources[i]['title'])+'</u></link>','source',True) for i in ids]
    def rule(keep=False):
        r=HRFlowable(width='100%',thickness=.5,color=colors.HexColor(LINE),spaceBefore=9,spaceAfter=14);r.keepWithNext=keep;return r
    def section(n,title,key=None):
        title_p=p(('<a name="daily-'+key+'"/>'+escape(title)) if key else title,'h2',bool(key))
        return [p(n+' / FIELDTOFIT DAILY','kicker'),title_p,rule(True)]
    def story(s):
        out=[p(s['event_date'],'kicker'),p(s['title'],'h3'),p(s['summary']),p(pick('本站解读：','FieldToFit: ')+s['analysis'],'small')]
        if s.get('metric'):out += [p(s['metric']['value'],'metric'),p(s['metric']['label'],'small'),p(s['metric']['note'],'small')]
        return out+refs(s['source_ids'])+[rule()]
    buffer=BytesIO()
    doc=BaseDocTemplate(buffer,pagesize=A4,leftMargin=M,rightMargin=M,topMargin=64,bottomMargin=53,title=pick('FieldToFit AI 日报','FieldToFit AI Daily')+' | '+d['date'],author='FieldToFit',subject='Revision '+str(revision)+'; content_sha256='+content_hash,allowSplitting=True)
    def page(canvas,doc):
        canvas.saveState();canvas.setFillColor(colors.HexColor(PAPER if doc.page==1 else '#FFFFFF'));canvas.rect(0,0,W,H,fill=1,stroke=0)
        canvas.setFillColor(colors.HexColor(INK));canvas.rect(0,H-5,W,5,fill=1,stroke=0);canvas.setFont('DailyNoto',11);canvas.drawString(M,H-34,'FieldToFit');canvas.setFont('DailyNoto',7.5);canvas.drawRightString(W-M,H-32,d['date']+'  /  DAILY')
        canvas.setStrokeColor(colors.HexColor(LINE));canvas.line(M,H-46,W-M,H-46);canvas.line(M,38,W-M,38)
        canvas.setFont('DailyNoto',7);canvas.setFillColor(colors.HexColor(MUTED));canvas.drawString(M,23,pick('读懂重点，保留依据。','Read the essentials. Keep the sources.'));canvas.drawCentredString(W/2+25,23,'r'+str(revision)+' / '+content_hash[:12]);canvas.drawRightString(W-M,23,str(doc.page).zfill(2));canvas.restoreState()
    full=Frame(M,53,CW,H-117,id='full',leftPadding=0,rightPadding=0,topPadding=0,bottomPadding=0)
    col=(CW-25)/2
    columns=[Frame(M+i*(col+25),53,col,H-117,id='col'+str(i),leftPadding=0,rightPadding=0,topPadding=0,bottomPadding=0) for i in range(2)]
    doc.addPageTemplates([PageTemplate(id='full',frames=[full],onPage=page),PageTemplate(id='columns',frames=columns,onPage=page)])
    content=[p(('<a name="daily-highlights"/>' if modern else '')+'FOR YOU  /  '+pick('AI 日报','AI DAILY'),'kicker',True),p(pick('AI 日报.','AI Daily.'),'h1'),p(d['date']+' · '+pick('取材截止 ','Cutoff ')+d['cutoff_at']+' · '+pick('北京时间','Asia/Shanghai'),'small')]
    if d['kind']=='review_sample':content += [p(pick('版式审阅样刊 · 保留实际取材时间','Layout review sample · Original cutoff retained') if modern else pick('晚间审阅样刊 · 保留实际取材时间','Evening review sample · Original cutoff retained'),'small')]
    if image:
        from PIL import Image as PILImage
        im=PILImage.open(BytesIO(image));im.verify()
        im=PILImage.open(BytesIO(image));width,height=im.size
        if width*height>30_000_000:raise ValueError('Cover image is too large')
        # Encode the printed figure at a bounded resolution; never ship a multi-
        # megabyte PNG in every immutable database revision. Preserve proportions.
        im.thumbnail((1600,1600));optimized=BytesIO()
        if im.mode in ('RGBA','LA'):
            background=PILImage.new('RGB',im.size,'white');background.paste(im,mask=im.getchannel('A'));im=background
        im.convert('RGB').save(optimized,format='JPEG',quality=90,optimize=True)
        content += [Image(BytesIO(optimized.getvalue()),width=CW,height=CW*height/width,kind='proportional'),Spacer(1,6),p('<link href="'+escape(sources[d['image']['source_id']]['url'],quote=True)+'">'+escape(d['image']['caption']+' · '+d['image']['credit'])+'</link>','source',True)]
    content += [Spacer(1,12),p(pick('今日重点 / 主编导读','HIGHLIGHTS / EDITOR’S LETTER'),'kicker'),p(d['headline'].replace('\n','' if lang=='zh' else ' '),'h2'),p(d['intro']),p(d['takeaway'],'small'),rule()]
    highlights=[s for s in d['stories'] if s['highlight']]
    if highlights:
        cells=[[p(str(i).zfill(2),'kicker'),p(s['title'],'body')] for i,s in enumerate(highlights,1)]
        brief=Table([cells],colWidths=[CW/len(cells)]*len(cells))
        brief.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),7),('RIGHTPADDING',(0,0),(-1,-1),12)]))
        content.append(brief)
    def table(rows,widths):
        t=Table(rows,colWidths=widths,repeatRows=1,hAlign='LEFT')
        t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor(SOFT)),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#F6F7F2')]),('VALIGN',(0,0),(-1,-1),'TOP'),('TOPPADDING',(0,0),(-1,-1),9),('BOTTOMPADDING',(0,0),(-1,-1),9),('LEFTPADDING',(0,0),(-1,-1),8),('RIGHTPADDING',(0,0),(-1,-1),8),('LINEBELOW',(0,0),(-1,-1),.4,colors.HexColor(LINE))]))
        return t
    def product_block():
        out=[]
        for is_new in (True,False):
            products=[v for v in d['products'] if v['is_new']==is_new]
            if not products:continue
            out += [p(pick('本期变化','New this issue') if is_new else (pick('近期已核实版本','Recently verified versions') if modern else pick('近期基线','Recent baseline')),'h3')]
            rows=[[p(v,'small') for v in [pick('产品 / 开发方','Product / Developer'),pick('版本 / 发布日期','Version / Release'),pick('关键特性与来源','Changes and sources')]]]
            for v in products:rows.append([p(v['name']+'\n'+v['organization'],'small'),p(v['version']+'\n'+v['release_date'],'small'),[p(v['changes'],'small'),*refs(v['source_ids']),*([p(pick('核对于 ','Checked ')+v['checked_at'],'small')] if modern else [])]])
            out += [table(rows,[110,128,CW-238]),Spacer(1,16)]
        if not d['products']:out += [p(pick('本期无产品版本更新。','No product version updates in this issue.'))]
        return out
    def news_block(keys,offset):
        out=[]
        for i,key in enumerate(keys,offset):
            heading=section(str(i).zfill(2),LABELS[key][0 if lang=='zh' else 1],key if modern else None)
            stories=[s for s in d['stories'] if s['section']==key]
            if not stories:out += [KeepTogether(heading+[p(d['section_notes'][key])])]
            else:
                out += [KeepTogether(heading+story(stories[0]))]
                for item in stories[1:]:out += [KeepTogether(story(item))]
        return out
    if modern:
        contents=' · '.join('<link href="#daily-'+key+'">'+escape(cn if lang=='zh' else en)+'</link>' for key,cn,en in edition_sections(raw))
        content += [Spacer(1,18),p(contents,'source',True)]
        # The short company opening uses the full page width; longer industry
        # sections flow through ordinary frames without shrinking text to fit.
        content += [NextPageTemplate('full'),PageBreak(),*news_block(('companies',),1)]
        content += [NextPageTemplate('full'),PageBreak(),*section('02',pick('热点 AI 产品追踪','AI product tracker'),'products'),*product_block()]
        content += [NextPageTemplate('columns'),PageBreak(),*news_block(news_sections(raw)[1:],3)]
        content += [NextPageTemplate('full'),PageBreak(),*section('08',pick('AI 股市','AI markets'),'markets')]
    else:
        content += [NextPageTemplate('columns'),PageBreak(),*news_block(news_sections(raw),1)]
        content += [NextPageTemplate('full'),PageBreak(),*section('06',pick('热点 AI 产品追踪','AI product tracker')),*product_block()]
        content += [PageBreak(),*section('07',pick('AI 股市','AI markets'))]
    content += [p(pick('统一采用各市场最近完整交易日收盘。','Each market uses its latest complete trading-session close.'),'small')]
    names={'us':pick('美股','United States'),'cn':pick('A 股','Mainland China'),'hk':pick('港股','Hong Kong')}
    for m in d['markets']:
        content += [p(names[m['id']]+' / '+m['currency'],'h3'),p((m['trade_date'] or pick('未取得交易日','Trading date unavailable'))+' · '+m['note'],'small')]
        rows=[[p(t,'small') for t in [pick('公司 / 代码','Company / Ticker'),pick('收盘','Close'),pick('日涨跌','Change'),pick('来源','Sources')]]]
        for r in m['rows']:
            rows.append([p(r['name']+'\n'+r['ticker'],'small'),p(f"{r['price']:,.2f}" if r['price'] is not None else pick('缺值','Missing'),'small'),p(f"{r['change_pct']:+.2f}%" if r['change_pct'] is not None else '—','small'),refs(r['source_ids']) or p(pick('未核实','Unverified'),'small')])
        content += [table(rows,[144,83,78,CW-305]),Spacer(1,20)]
    content += [rule(),p(pick('写在最后','EDITOR’S NOTE'),'kicker'),p(d['closing'])]
    doc.build(content);data=buffer.getvalue();pages=len(PdfReader(BytesIO(data)).pages)
    return {'bytes':data,'pages':pages,'sha256':hashlib.sha256(data).hexdigest()}
