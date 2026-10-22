"""Versioned editorial catalog shared by React, search HTML and read-only HTTP."""
import hashlib
import json
from pathlib import Path
from flask import Blueprint, jsonify, request, render_template

ROOT = '/for-you/evolution'
QUESTIONS = ROOT + '/questions'
CATALOG = json.loads(Path(__file__).with_name('catalog.json').read_text())
QUESTION_BY_ID = {q['id']: q for q in CATALOG['questions']}
REVISION = hashlib.sha256(json.dumps(CATALOG, sort_keys=True).encode()).hexdigest()[:20]
bp = Blueprint('llm_evolution', __name__, template_folder='templates')


@bp.get('/api/v1/platform/evolution')
@bp.get('/api/v1/platform/evolution/questions/<ident>')
def catalog_api(ident=None):
    from backend.knowledge.api import read_allowed
    if not read_allowed():
        return jsonify(error='Read access required'), 401
    if ident is not None and ident not in QUESTION_BY_ID:
        return jsonify(error='Question not found'), 404
    data = CATALOG if ident is None else {
        'schema_version': CATALOG['schema_version'], 'revision': CATALOG['revision'],
        'question': QUESTION_BY_ID[ident],
        'sources': {key: CATALOG['sources'][key] for key in QUESTION_BY_ID[ident]['sources']}}
    response = jsonify(data)
    response.set_etag(REVISION + ('-' + ident if ident else ''))
    response.headers['Cache-Control'] = 'no-cache'
    return response.make_conditional(request)


def sitemap_entries():
    return [(path, CATALOG['updated_at']) for path in [ROOT, QUESTIONS] +
            [QUESTIONS + '/' + q['id'] for q in CATALOG['questions']]]


def page(path, dist, english):
    from backend.seo import document
    from backend.knowledge.api import read_allowed
    from flask import redirect
    if path.endswith('/'):
        return redirect(('/en' if english else '') + path.rstrip('/'), 308)
    ident = path.removeprefix(QUESTIONS + '/') if path.startswith(QUESTIONS + '/') else None
    question = QUESTION_BY_ID.get(ident)
    if path not in (ROOT, QUESTIONS) and question is None:
        return document(dist, 'Question not found' if english else '题目未找到', '', path,
                        '<h1>' + ('Question not found' if english else '题目未找到') + '</h1>', status=404, index=False)
    if not read_allowed():
        return document(dist, 'Read access required' if english else '需要读取权限', '', path, status=401, index=False)
    index = int(english)
    title = question['title'][index] if question else ('Important questions' if english else '重要问题目录') if path == QUESTIONS else ('LLM technical evolution' if english else '大模型技术演进')
    description = question['goal'][index] if question else ('2017–2026: training, inference and systems. Bottlenecks, breakthroughs and new constraints.' if english else '2017—2026：训练、推理、系统。沿着瓶颈理解创新与新约束。')
    body = render_template('evolution.html', catalog=CATALOG, question=question,
                           title=title, description=description, index=index, english=english,
                           root=ROOT, questions=QUESTIONS, directory=path == QUESTIONS,
                           question_by_id=QUESTION_BY_ID,
                           node_by_id={n["id"]: n for r in CATALOG["routes"] for n in r["nodes"]})
    return document(dist, title + ' · FieldToFit', description, path, body)
