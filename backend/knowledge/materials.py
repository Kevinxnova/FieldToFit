"""Versioned text extraction with explicit section/page coverage."""
import base64
import io
import re
from html.parser import HTMLParser
from urllib.parse import urljoin, urlsplit, quote

from backend.knowledge import store


class Sections(HTMLParser):
    def __init__(self):
        super().__init__(); self.sections = []; self.parts = []; self.heading = 'Document'; self.skip = 0; self.in_heading = False; self.links = []

    def flush(self):
        body = '\n'.join(x.strip() for x in ''.join(self.parts).splitlines() if x.strip())
        if body:
            self.sections.append((self.heading, body))
        self.parts = []

    def handle_starttag(self, tag, attrs):
        if tag in {'script','style','noscript','nav','footer'}:
            self.skip += 1
        if self.skip:
            return
        if tag in {'h1','h2','h3','h4'}:
            self.flush(); self.heading = ''; self.in_heading = True
        if tag in {'p','div','section','li','br','tr','pre'}:
            self.parts.append('\n')
        if tag == 'a':
            self.links.extend(v for k,v in attrs if k == 'href' and v)

    def handle_endtag(self, tag):
        if tag in {'script','style','noscript','nav','footer'}:
            self.skip = max(0, self.skip-1)
        if tag in {'h1','h2','h3','h4'}:
            self.in_heading = False

    def handle_data(self, data):
        if self.skip:
            return
        if self.in_heading:
            self.heading += data
        self.parts.append(data)


def extract(data, content_type, url):
    if 'pdf' in content_type or data.startswith(b'%PDF'):
        from pypdf import PdfReader
        reader = PdfReader(io.BytesIO(data))
        if reader.is_encrypted:
            raise ValueError('Encrypted PDF cannot be read')
        if len(reader.pages) > 300:
            raise ValueError('PDF exceeds the 300 page extraction limit')
        parts = [(f'Page {i+1}', p.extract_text() or '') for i,p in enumerate(reader.pages)]
        missing = [loc for loc, body in parts if len(body.strip()) < 20]
        return parts, [], {'format':'pdf', 'pages':len(parts), 'unreadable_pages':missing,
                           'limitations':'Text extraction only; scanned pages, formula and table structure require source review',
                           'coverage':'excerpt' if missing else 'full_text'}
    text = data.decode('utf-8', errors='replace')
    if 'html' in content_type or re.search(r'<(?:html|article|body)\b', text[:1000], re.I):
        parser = Sections(); parser.feed(text); parser.flush()
        return parser.sections, [urljoin(url, link) for link in parser.links], {'format':'html', 'coverage':'full_text', 'limitations':'Readable text; interactive content and page layout are not retained'}
    parts = []; heading = 'Document'; lines = []
    for line in text.splitlines():
        if re.match(r'^#{1,4}\s+', line):
            if lines:
                parts.append((heading, '\n'.join(lines)))
            heading = re.sub(r'^#+\s+', '', line); lines = []
        lines.append(line)
    if lines:
        parts.append((heading, '\n'.join(lines)))
    links = re.findall(r'https?://[^\s<>"\)\]]+', text)
    return parts, links, {'format':'text', 'coverage':'full_text', 'limitations':'Text and headings; no execution was performed'}


def retrieve(record_id):
    from backend.knowledge.sources import fetch, fetch_json
    record = store.get_record(record_id, include_withdrawn=True)
    if not record:
        raise ValueError('Record not found')
    url = record['metadata'].get('document_url') or record['canonical_url']
    p = urlsplit(record['canonical_url']); version = record['version']
    if p.hostname == 'github.com' and len(p.path.strip('/').split('/')) == 2 and not record['metadata'].get('document_url'):
        repo = p.path.strip('/')
        suffix = '?ref=' + quote(version, safe='') if version else ''
        info = fetch_json(f'https://api.github.com/repos/{repo}/readme' + suffix)
        data = base64.b64decode(info.get('content','')); url = info['html_url']; content_type = 'text/markdown'
        # A README blob SHA identifies the evidence, not a release/commit of the whole project.
        material_version = version or info.get('sha','')
    else:
        try:
            data, url, content_type = fetch(url, max_bytes=15_000_000)
        except Exception:
            if p.hostname in {'arxiv.org','export.arxiv.org'} and '/html/' in url:
                data, url, content_type = fetch(url.replace('/html/','/pdf/'), max_bytes=15_000_000)
            else:
                raise
        material_version = version
    sections, links, info = extract(data, content_type, url)
    if sum(len(body.strip()) for _,body in sections) < 40:
        raise ValueError('Source has insufficient readable text; scanned PDFs need OCR or a sourced manual extract')
    ids = []; total = 0
    for locator, body in sections:
        for offset in range(0,len(body),90000):
            chunk = body[offset:offset+90000]
            if not chunk.strip():
                continue
            loc = locator + (f' · characters {offset}–{offset+len(chunk)}' if len(body)>90000 else '')
            ids.append(store.add_evidence(record_id,url,record['title'],chunk,loc,material_version,'documented',info['coverage']))
            total += len(chunk)
    record['metadata']['material'] = {**info,'evidence_ids':ids,'url':url,'version':material_version,'characters':total}
    record['metadata']['document_evidence_id'] = ids[0]
    record['checked_at'] = store.now()
    store.save_record(record, 'Retrieved source sections with version and location', record_id)
    # Exact referenced URLs can establish a citation; official implementation requires explicit review.
    with store.get_db() as db:
        indexed = {r['canonical_url']:r['id'] for r in db.execute("SELECT id,canonical_url FROM knowledge_records WHERE status='published'").fetchall()}
    for link in set(links):
        try:
            target = indexed.get(store.canonical_url(link))
            if target and target != record_id:
                store.relate(record_id,target,'related',url,'Explicit link in source material; relationship type and authorship unconfirmed')
        except ValueError:
            continue
    return {'evidence_id':ids[0],'evidence_ids':ids,'characters':total,**info}
