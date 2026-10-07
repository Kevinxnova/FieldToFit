"""Revision-bound positions. Indexing never rewrites reviewed source characters."""
import hashlib
import io
import re
from html import unescape
from backend.knowledge.platform import PlatformError, integer, text


def validate(body, index):
    if not isinstance(index, dict) or index.get('format') != 'pdf':
        raise ValueError('Expected a PDF location index')
    pages = index.get('pages', [])
    if not isinstance(pages, list) or not 1 <= len(pages) <= 500:
        raise ValueError('Invalid PDF page count')
    result = []
    end = 0
    for n, page in enumerate(pages, 1):
        start = integer(page.get('start'), 'page start', end, len(body))
        stop = integer(page.get('end'), 'page end', start, len(body))
        if page.get('page') != n or body[end:start].strip('\n\f '):
            raise ValueError('PDF page ranges must cover the saved text in order')
        gaps = page.get('gaps', [])
        if not isinstance(gaps, list) or any(g not in {'no_text_layer', 'images_not_extracted', 'formula_layout_unverified'} for g in gaps):
            raise ValueError('Invalid PDF extraction gaps')
        result.append({'id': 'page-'+str(n), 'page': n, 'label': text(page.get('label', str(n)), 'printed page', 80, False),
                       'title': '文件第 '+str(n)+' 页', 'start': start, 'end': stop, 'gaps': sorted(set(gaps))})
        end = stop
    if body[end:].strip('\n\f '):
        raise ValueError('PDF index leaves source text outside its pages')
    file_hash = text(index.get('file_hash'), 'PDF file hash', 64)
    if not re.fullmatch('[0-9a-f]{64}', file_hash): raise ValueError('Invalid PDF file hash')
    return {'format': 'pdf', 'file_hash': file_hash, 'pages': result}


def extract_pdf(data):
    from pypdf import PdfReader
    from pypdf.errors import PdfReadError
    if not data or len(data) > 10*1024*1024: raise ValueError('PDF must be at most 10 MiB')
    try:
        reader = PdfReader(io.BytesIO(data))
    except (PdfReadError, ValueError) as exc:
        raise ValueError('PDF无法解析，请核对原始文件') from exc
    if reader.is_encrypted: raise ValueError('Encrypted PDF is not supported')
    if not 1 <= len(reader.pages) <= 500: raise ValueError('PDF must have 1–500 pages')
    body = ''; pages = []; labels = reader.page_labels
    for n, page in enumerate(reader.pages):
        if n: body += '\n\f\n'
        start = len(body); value = page.extract_text() or ''; body += value
        if len(body) > 300000: raise ValueError('Extracted PDF exceeds 300000 characters')
        gaps = ['formula_layout_unverified']
        if not value.strip(): gaps.append('no_text_layer')
        resources = page.get('/Resources')
        if resources and resources.get_object().get('/XObject'): gaps.append('images_not_extracted')
        pages.append({'page': n+1, 'label': labels[n], 'start': start, 'end': len(body), 'gaps': gaps})
    if not body.strip():
        body = ''
        for page in pages: page.update(start=0, end=0)
    return {'body': body, 'location_index': validate(body, {'format': 'pdf', 'file_hash': hashlib.sha256(data).hexdigest(), 'pages': pages}),
            'coverage': 'excerpt' if body.strip() else 'link_only',
            'reason': 'PDF文字层；图像、扫描内容与公式布局未完整提取或验证。' if body.strip() else 'PDF没有可读取文字层；请从原始文件核对扫描、图像与公式。'}


def index(body, supplied=None):
    if supplied:
        pdf = validate(body, supplied)
        return {'format': 'pdf', 'sections': [], 'pages': pdf['pages'], 'file_hash': pdf['file_hash']}
    headings = []; fenced = False; fence = ''; fence_length = 0; fence_start = 0; excluded = []; pos = 0
    for line in body.splitlines(keepends=True):
        marker = re.match(r'^\s{0,3}(`{3,}|~{3,})', line)
        if marker:
            if not fenced:
                fenced = True; fence = marker[1][0]; fence_length = len(marker[1]); fence_start = pos
            elif marker[1][0] == fence and len(marker[1]) >= fence_length and not line[marker.end():].strip():
                fenced = False; excluded.append((fence_start, pos+len(line)))
        elif not fenced:
            match = re.match(r'^\s{0,3}(#{1,6})\s+(.+?)\s*#*\s*$', line)
            if match: headings.append({'title': match[2], 'level': len(match[1]), 'start': pos})
        pos += len(line)
    if fenced: excluded.append((fence_start, len(body)))
    if not headings:
        for match in re.finditer(r'<h([1-6])\b[^>]*>(.*?)</h\1\s*>', body, re.I | re.S):
            if any(start <= match.start() < end for start, end in excluded): continue
            headings.append({'title': unescape(re.sub('<[^>]+>', '', match[2]))[:1000], 'level': int(match[1]), 'start': match.start()})
    sections = []
    for n, heading in enumerate(headings):
        stop = next((h['start'] for h in headings[n+1:] if h['level'] <= heading['level']), len(body))
        sections.append({**heading, 'id': 'section-'+str(n+1), 'end': stop})
    paragraphs = [{'id': 'paragraph-'+str(n+1), 'title': '段落 '+str(n+1), 'start': m.start(), 'end': m.end(), 'level': 0}
                  for n, m in enumerate(re.finditer(r'\S[^\n]*(?:\n(?!\s*\n)[^\n]*)*', body))]
    return {'format': 'text', 'sections': sections, 'paragraphs': paragraphs, 'pages': []}


def locate(material, revision, location_id='', offset=0, limit=12000):
    body = material['body']; directory = index(body, material.get('location_index'))
    locations = directory.get('sections', []) + directory.get('paragraphs', []) + directory['pages']
    location = next((p for p in locations if p['id'] == location_id), None)
    if not location: raise PlatformError('Location is not in this material revision', 'location_not_found', 404)
    offset = integer(offset, 'offset', location['start'], location['end'])
    end = min(offset + integer(limit, 'limit', 1, 50000), location['end'])
    citation = {'material_id': material['id'], 'content_revision': revision, 'content_hash': material['content_hash'],
                'source_url': material['url'], 'upstream_revision': material['upstream_revision'],
                'location': location, 'start': offset, 'end': end}
    return {'body': body[offset:end], 'offset': offset, 'next_offset': end if end < location['end'] else None,
            'has_more': end < location['end'], 'citation': citation, 'location': location}
