"""Daily journal endpoints, separate from the compatible legacy daily-news API."""
from flask import Blueprint, request, jsonify, Response
from werkzeug.exceptions import BadRequest
from backend.knowledge.api import read_allowed, admin_required
from backend.knowledge.platform import PlatformError
from backend.security import allowed_origins
from . import service
from .schema import fail

bp=Blueprint('daily_briefing',__name__,url_prefix='/api/v1')

@bp.before_request
def protect():
    if request.method=='OPTIONS':return '',204
    if request.args.get('lang','zh') not in ('zh','en'):fail('Unsupported language')
    if not request.path.startswith('/api/v1/admin/') and not read_allowed():return jsonify(detail='Read access token required'),401
    if request.method in ('POST','PUT','DELETE'):
        if request.headers.get('Origin') and request.headers['Origin'] not in allowed_origins():return jsonify(detail='Origin not allowed'),403
        if not request.is_json:return jsonify(detail='Use application/json'),415
        if request.content_length and request.content_length>2_000_000:return jsonify(detail='Daily input exceeds size limit'),413

@bp.after_request
def headers(response):
    response.headers['Cache-Control']='private, no-store' if '/admin/' in request.path else 'no-store'
    response.headers['Content-Language']=request.args.get('lang','zh')
    response.headers['X-Content-Type-Options']='nosniff'
    return response

@bp.errorhandler(PlatformError)
def domain_error(e):return jsonify(detail=str(e),code=e.code),e.status
@bp.errorhandler(BadRequest)
@bp.errorhandler(ValueError)
@bp.errorhandler(TypeError)
@bp.errorhandler(KeyError)
def bad_input(e):return jsonify(detail='Invalid daily edition input',code='daily_invalid'),400

def body():
    b=request.get_json()
    if not isinstance(b,dict):fail('JSON object required')
    return b

def revision():return int(request.args['revision']) if 'revision' in request.args else None

@bp.get('/daily')
def index():return jsonify(service.archive(request.args.get('lang','zh'),int(request.args.get('limit',30)),int(request.args.get('offset',0))))
@bp.get('/daily/latest')
def latest():return jsonify(service.read(lang=request.args.get('lang','zh')))
@bp.get('/daily/<day>')
def issue(day):return jsonify(service.read(day,request.args.get('lang','zh'),revision()))
@bp.get('/daily/<day>/pdf')
def pdf(day):
    lang=request.args.get('lang','zh');data,sha,rev=service.pdf_bytes(day,lang,revision())
    name=f'FieldToFit-Daily-{day}-'+('zh-CN' if lang=='zh' else 'en')+f'-r{rev}.pdf'
    return Response(data,content_type='application/pdf',headers={'Content-Disposition':f'attachment; filename="{name}"','ETag':'"'+sha+'"','X-Daily-Revision':str(rev)})
@bp.get('/admin/daily')
@admin_required
def admin_index():return jsonify(service.administrative_index())
@bp.get('/admin/daily/<day>')
@admin_required
def admin_read(day):return jsonify(service.draft(day))
@bp.get('/admin/daily/<day>/pdf')
@admin_required
def admin_pdf(day):
    lang=request.args.get('lang','zh');data,sha=service.prepared_pdf_bytes(day,lang)
    return Response(data,content_type='application/pdf',headers={'ETag':'"'+sha+'"','Content-Disposition':f'attachment; filename="FieldToFit-proof-{day}-{lang}.pdf"'})
@bp.post('/admin/daily')
@admin_required
def admin_save():
    b=body();return jsonify(service.save(b['issue'],b.get('draft_version',0)))
@bp.post('/admin/daily/<day>/review')
@admin_required
def admin_review(day):
    b=body()
    if 'review_report' in b:
        report=b['review_report']
        if not isinstance(report,dict) or report.get('method')!='local_gpt':fail('Expected a local GPT editorial review')
        return jsonify(service.approve(day,b['draft_version'],report))
    if b.get('facts_and_languages_checked') is not True:fail('Confirm source facts and both languages before review')
    return jsonify(service.approve(day,b['draft_version'],{'approved':True,'method':'owner'}))
@bp.post('/admin/daily/<day>/publish')
@admin_required
def admin_publish(day):
    b=body();automatic=b.get('automatic',False)
    if type(automatic) is not bool:fail('Automatic publication must be a boolean')
    return jsonify(service.publish(day,b['draft_version'],b['reason'],automatic=automatic,proof_hashes=b.get('proof_hashes')))
@bp.post('/admin/daily/<day>/withdraw')
@admin_required
def admin_withdraw(day):
    b=body();return jsonify(service.withdraw(day,b['draft_version'],b['reason']))
@bp.post('/admin/daily/run')
@admin_required
def admin_run():
    from .pipeline import run
    return jsonify(run(body().get('phase','prepare'),manual=True))
