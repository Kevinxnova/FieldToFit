"""Local, deliberately narrow PDF-to-amount workflow. See pdf_amount.md."""
import argparse
from decimal import Decimal
import hashlib
import io
import json
from pathlib import Path
import re
from importlib.metadata import version

from pypdf import PdfReader


def page_materials(data):
    """Project-owned adapter around the documented PdfReader/pages API."""
    reader = PdfReader(io.BytesIO(data))
    if reader.is_encrypted:
        raise ValueError('Encrypted PDFs are outside this example')
    return [{'page': index + 1, 'text': page.extract_text() or ''}
            for index, page in enumerate(reader.pages)]


def extract_amount(pages):
    """Business rule, independently usable with already extracted page text."""
    hits = []
    # Match an entire line; do not silently turn negative/foreign/malformed amounts positive.
    pattern = r'^\s*发票金额[：:]\s*([0-9]+\.[0-9]{2})\s*元\s*$'
    for page in pages:
        for line in page['text'].splitlines():
            match = re.fullmatch(pattern, line)
            if match:
                hits.append({'amount': format(Decimal(match[1]), '.2f'), 'currency': 'CNY',
                             'source_page': page['page'], 'quote': line.strip()})
    if len(hits) == 1:
        return {'status': 'extracted', 'field': hits[0], 'matches': hits}
    status = 'ambiguous' if hits else ('needs_ocr_or_text_review' if not any(p['text'].strip() for p in pages) else 'not_found')
    return {'status': status, 'field': None, 'matches': hits}


def process_pdf(data):
    pages = page_materials(data)
    return {'input_sha256': hashlib.sha256(data).hexdigest(), 'page_count': len(pages),
            'pypdf_version': version('pypdf'), 'pages': pages, **extract_amount(pages)}


def demo(folder):
    """Create synthetic fixtures, run actual files and check positive/negative outcomes."""
    from reportlab.pdfgen.canvas import Canvas
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.cidfonts import UnicodeCIDFont
    folder.mkdir(parents=True, exist_ok=True)
    pdfmetrics.registerFont(UnicodeCIDFont('STSong-Light'))
    fixtures = {
        'searchable': [['项目：中文文档处理', '发票金额：128.50 元'], ['第二页：处理完成']],
        'missing': [['项目：没有金额字段']],
        'ambiguous': [['发票金额：128.50 元'], ['发票金额：256.00 元']],
        'no_text': [[]],
        'negative': [['发票金额：-128.50 元']],
    }
    results = {}
    for name, pages in fixtures.items():
        source = folder / (name + '.pdf')
        canvas = Canvas(str(source), invariant=1)
        for lines in pages:
            canvas.setFont('STSong-Light', 14)
            for index, line in enumerate(lines):
                canvas.drawString(50, 780 - index * 30, line)
            canvas.showPage()
        canvas.save()
        results[name] = process_pdf(source.read_bytes())
        (folder / (name + '.json')).write_text(json.dumps(results[name], ensure_ascii=False, indent=2) + '\n')
    checks = {
        'amount_currency_page_quote': results['searchable']['field'] == {
            'amount': '128.50', 'currency': 'CNY', 'source_page': 1, 'quote': '发票金额：128.50 元'},
        'page_adapter': results['searchable']['page_count'] == 2 and '第二页' in results['searchable']['pages'][1]['text'],
        'missing_is_not_zero': results['missing']['status'] == 'not_found' and results['missing']['field'] is None,
        'multiple_is_not_first': results['ambiguous']['status'] == 'ambiguous' and results['ambiguous']['field'] is None,
        'empty_text_requires_review': results['no_text']['status'] == 'needs_ocr_or_text_review',
        'negative_is_not_positive': results['negative']['status'] == 'not_found',
        'custom_rule_without_pdf_library': extract_amount([{'page': 3, 'text': '发票金额：42.00 元'}])['field']['source_page'] == 3,
    }
    assert all(checks.values()), checks
    return {'case': 'engineer-pdf-amount', 'recipe_version': '1', 'pypdf_version': version('pypdf'),
            'reportlab_version': version('reportlab'), 'checks': checks, 'artifacts': results,
            'scope': 'Five synthetic PDFs; blank page models unavailable text, not an OCR test. Fixed CNY line format only.'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--input', type=Path)
    group.add_argument('--demo-dir', type=Path)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    result = demo(args.demo_dir) if args.demo_dir else process_pdf(args.input.read_bytes())
    text = json.dumps(result, ensure_ascii=False, indent=2) + '\n'
    if args.output:
        args.output.write_text(text)
    else:
        print(text, end='')
