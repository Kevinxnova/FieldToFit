"""Small, reviewed examples of PDF extraction, extension and mixed implementation."""
import io
import json
import re
import sys
from importlib.metadata import version
from pypdf import PdfReader
from reportlab.pdfgen.canvas import Canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont

case=sys.argv[1]
buffer=io.BytesIO();pdfmetrics.registerFont(UnicodeCIDFont('STSong-Light'))
canvas=Canvas(buffer)
canvas.setFont('STSong-Light',14)
canvas.drawString(50,780,'项目：中文文档处理')
canvas.drawString(50,750,'发票金额：128.50 元')
canvas.showPage();canvas.setFont('STSong-Light',14);canvas.drawString(50,780,'第二页：处理完成');canvas.save()
reader=PdfReader(io.BytesIO(buffer.getvalue()))
text='\n'.join(page.extract_text() for page in reader.pages)
assert '中文文档处理' in text and '第二页' in text
artifact={'case':case,'pypdf_version':version('pypdf'),'input':'Generated two-page searchable Chinese PDF; not a scanned document','page_count':len(reader.pages)}
if case=='engineer-pdf':
    artifact['extracted_text']=text
elif case=='engineer-extension':
    # Project-owned extension around an existing library, without claiming an upstream code patch.
    def sections(pdf):
        return [{'page':index+1,'text':page.extract_text()} for index,page in enumerate(pdf.pages)]
    result=sections(reader)
    assert result[1]['page']==2 and '第二页' in result[1]['text']
    artifact['extension_output']=result
elif case=='engineer-mixed':
    # Reuse parsing; implement task-specific field extraction with an explicit narrow rule.
    match=re.search(r'发票金额[：:]\s*(\d+\.\d{2})',text)
    assert match and match.group(1)=='128.50'
    artifact['fields']={'amount':match.group(1),'currency':'CNY','source_page':1}
else:
    raise ValueError('Unknown reviewed case')
print(json.dumps(artifact,ensure_ascii=False,indent=2))
