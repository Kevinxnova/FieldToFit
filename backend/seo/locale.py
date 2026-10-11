"""Localize authored HTML text safely, preserving attributed original material."""
import html
from html.parser import HTMLParser
from backend.knowledge import locale

class EnglishHTML(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True);self.output=[];self.stack=[]
    def handle_starttag(self,tag,attrs):
        inherited=self.stack[-1][1] if self.stack else False
        original=inherited or tag in ('script','style') or any(k=='data-original-language' or k=='lang' and v and v.startswith('zh') for k,v in attrs)
        attributes=[]
        for key,value in attrs:
            if value is not None and not original and key in ('title','alt','aria-label','placeholder'):value=locale.text(value)
            if key=='href' and value and __import__('re').match(r'^/(for-you|for-your-ai|news|watch|maps|sources|about|community|feedback|collection)([/?#]|$)',value):value='/en'+value
            attributes.append(key if value is None else key+'="'+html.escape(value,quote=True)+'"')
        self.output.append('<'+tag+(' '+' '.join(attributes) if attributes else '')+'>')
        if tag not in ('area','base','br','col','embed','hr','img','input','link','meta','param','source','track','wbr'):self.stack.append((tag,original))
    def handle_endtag(self,tag):
        self.output.append('</'+tag+'>')
        if self.stack and self.stack[-1][0]==tag:self.stack.pop()
    def handle_data(self,data):
        if self.stack and self.stack[-1][0] in ('script','style'):self.output.append(data)
        else:self.output.append(html.escape(data if self.stack and self.stack[-1][1] else locale.text(data),quote=False))
    def handle_entityref(self,name):self.output.append('&'+name+';')
    def handle_charref(self,name):self.output.append('&#'+name+';')
    def handle_comment(self,data):self.output.append('<!--'+data+'-->')

def english_html(body):
    parser=EnglishHTML();parser.feed(body);return ''.join(parser.output)
