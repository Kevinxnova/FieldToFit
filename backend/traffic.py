"""First-party aggregate traffic reports. No raw IP, UA, query or referrer storage."""
import csv
import hashlib
import io
import os
import re
import time
from datetime import datetime, timedelta, timezone, date
from urllib.parse import urlsplit
from zoneinfo import ZoneInfo
from flask import Blueprint, request, jsonify, Response
from backend.db import get_db
from backend import analytics as a
from backend.knowledge.api import admin_required

bp = Blueprint('traffic', __name__)
TZ = ZoneInfo('Asia/Shanghai')
KINDS = {'page_view','content_view','material_export','material_read','handoff_copy','mcp_address_copy','mcp_service_check'}
CONTENT = re.compile(r'^(D-\d{2,}|CW-[MATSH]\d{2,})$')
DAYS = 90 * 86400


def config():
    return {'enabled': a.enabled() and os.getenv('FIELDTOFIT_ANALYTICS_DETAILS','1') == '1',
            'origin': a.site_origin(), 'consent_required': os.getenv('FIELDTOFIT_ANALYTICS_REQUIRE_CONSENT','0') == '1',
            'retention_days':90, 'timezone':'Asia/Shanghai', 'metric_version':1}


def day(ts): return datetime.fromtimestamp(ts, TZ).date().isoformat()
def digest(v): return hashlib.sha256(v.encode()).hexdigest() if v else None


def classify(referrer, campaign):
    allowed = {v for v in os.getenv('FIELDTOFIT_ANALYTICS_CAMPAIGNS','').split(',') if re.fullmatch(r'[a-zA-Z0-9_-]{1,40}',v)}
    if campaign in allowed: return 'campaign:'+campaign
    try:
        host = (urlsplit(referrer).hostname or '').lower()
        own = urlsplit(a.site_origin()).hostname
    except ValueError: return 'direct_unknown'
    if not host or host == own: return 'direct_unknown'
    for engine, roots in [('google',('google.com','google.cn','google.co.uk','google.com.hk')),('bing',('bing.com',)),('baidu',('baidu.com',))]:
        if any(host==root or host.endswith('.'+root) for root in roots):return 'search:'+engine
    return 'external'  # no arbitrary external text persisted


def record(data, now=None):
    now = int(time.time()) if now is None else now
    browser, eid = digest(data.get('browser_id')), digest(data['event_id'])
    kind, path, content = data['kind'], data['path'], data.get('content_id')
    source = classify(data.get('referrer',''),data.get('campaign',''))
    bucket, today = now//60, day(now)
    statements = [
        ('DELETE FROM fieldtofit_visit_limits WHERE bucket<?',(bucket-1,)),
        ("INSERT INTO fieldtofit_visit_limits VALUES('traffic-global',?,1) ON CONFLICT(scope,bucket) DO UPDATE SET hits=hits+1",(bucket,)),
        ('INSERT INTO fieldtofit_visit_limits VALUES(?,?,1) ON CONFLICT(scope,bucket) DO UPDATE SET hits=hits+1',('traffic:'+str(browser),bucket)),
        ('DROP TABLE IF EXISTS temp.traffic_guard',()),
        ('CREATE TEMP TABLE traffic_guard(fresh INTEGER, session_id TEXT, new_session INTEGER, is_returning INTEGER, limited INTEGER)',()),
        ('''INSERT INTO traffic_guard SELECT
          NOT EXISTS(SELECT 1 FROM fieldtofit_analytics_events WHERE event_id=?),
          COALESCE((SELECT session_id FROM fieldtofit_analytics_sessions WHERE browser_id=? AND last_seen>? ORDER BY last_seen DESC LIMIT 1),?),
          NOT EXISTS(SELECT 1 FROM fieldtofit_analytics_sessions WHERE browser_id=? AND last_seen>?),
          EXISTS(SELECT 1 FROM fieldtofit_analytics_visitors WHERE browser_id=? AND first_seen<?),
          EXISTS(SELECT 1 FROM fieldtofit_visit_limits WHERE bucket=? AND ((scope='traffic-global' AND hits>2400) OR (scope=? AND hits>180)))''',
         (eid,browser,now-1800,eid,browser,now-1800,browser,int(datetime.combine(date.fromisoformat(today),datetime.min.time(),TZ).timestamp()),bucket,'traffic:'+str(browser))),
        # Content/action events require an existing session and are never a page visit.
        ('''UPDATE traffic_guard SET fresh=0 WHERE ?!='page_view' AND (new_session OR ? IS NULL)''',(kind,browser)),
        ('''UPDATE traffic_guard SET fresh=0 WHERE ?='content_view' AND EXISTS(SELECT 1 FROM fieldtofit_analytics_events e WHERE e.kind='content_view' AND e.session_id=traffic_guard.session_id AND e.content_id=?)''',(kind,content)),
        ('''INSERT INTO fieldtofit_analytics_events SELECT ?,?,?,?,CASE WHEN ? IS NULL THEN NULL ELSE session_id END,?,?,?,?,is_returning FROM traffic_guard WHERE fresh AND NOT limited''',(eid,now,today,browser,browser,kind,path,content,source)),
        ('''INSERT INTO fieldtofit_analytics_visitors SELECT ?,?,? FROM traffic_guard WHERE fresh AND NOT limited AND ? IS NOT NULL ON CONFLICT(browser_id) DO UPDATE SET last_seen=excluded.last_seen''',(browser,now,now,browser)),
        ('''INSERT INTO fieldtofit_analytics_sessions SELECT session_id,?,?,?,?,? FROM traffic_guard WHERE fresh AND NOT limited AND ? IS NOT NULL ON CONFLICT(session_id) DO UPDATE SET last_seen=excluded.last_seen''',(browser,now,now,path,source,browser)),
        # Reuse the established counter's session clock so old/new collectors never double-count.
        ('''INSERT INTO fieldtofit_visit_total SELECT 1,1,?,? FROM traffic_guard WHERE fresh AND NOT limited AND ? IS NOT NULL AND ?='page_view' AND NOT EXISTS(SELECT 1 FROM fieldtofit_visit_sessions WHERE browser_id=? AND last_seen>?) ON CONFLICT(id) DO UPDATE SET visits=visits+1,updated_at=excluded.updated_at''',(now,now,browser,kind,browser,now-1800)),
        ('''INSERT INTO fieldtofit_visit_sessions SELECT ?,? FROM traffic_guard WHERE fresh AND NOT limited AND ? IS NOT NULL ON CONFLICT(browser_id) DO UPDATE SET last_seen=MAX(last_seen,excluded.last_seen)''',(browser,now,browser)),
        ('''INSERT INTO fieldtofit_analytics_daily(day,pv,uv,sessions,anonymous_pv,content_views,exports,material_reads)
           SELECT ?,CASE WHEN ?='page_view' THEN 1 ELSE 0 END,
           CASE WHEN ?='page_view' AND ? IS NOT NULL AND (SELECT COUNT(*) FROM fieldtofit_analytics_events WHERE day=? AND browser_id=? AND kind='page_view')=1 THEN 1 ELSE 0 END,
           CASE WHEN new_session AND ? IS NOT NULL THEN 1 ELSE 0 END,
           CASE WHEN ?='page_view' AND ? IS NULL THEN 1 ELSE 0 END,
           CASE WHEN ?='content_view' THEN 1 ELSE 0 END, CASE WHEN ?='material_export' THEN 1 ELSE 0 END, CASE WHEN ?='material_read' THEN 1 ELSE 0 END
           FROM traffic_guard WHERE fresh AND NOT limited
           ON CONFLICT(day) DO UPDATE SET pv=pv+excluded.pv,uv=uv+excluded.uv,sessions=sessions+excluded.sessions,anonymous_pv=anonymous_pv+excluded.anonymous_pv,content_views=content_views+excluded.content_views,exports=exports+excluded.exports,material_reads=material_reads+excluded.material_reads''',
         (today,kind,kind,browser,today,browser,browser,kind,browser,kind,kind,kind)),
        ('''INSERT INTO fieldtofit_analytics_state SELECT 1,?,? FROM traffic_guard WHERE fresh AND NOT limited ON CONFLICT(id) DO UPDATE SET updated_at=excluded.updated_at''',(now,now)),
        ('SELECT fresh,limited FROM traffic_guard',()),
        ('DROP TABLE temp.traffic_guard',())]
    with get_db() as db:
        result=a.atomic(db,statements)[-2].fetchone()
    return not bool(result['limited'])


def clean(now=None):
    now=int(time.time()) if now is None else now
    with get_db() as db:
        a.atomic(db,[('DELETE FROM fieldtofit_analytics_events WHERE received_at<?',(now-DAYS,)),
          ('DELETE FROM fieldtofit_analytics_sessions WHERE last_seen<?',(now-DAYS,)),
          ('DELETE FROM fieldtofit_analytics_visitors WHERE last_seen<? OR first_seen<?',(now-DAYS,now-DAYS)),
          ('DELETE FROM fieldtofit_analytics_daily WHERE day<?',(day(now-396*86400),))])


def summary(start,end,now=None):
    now=int(time.time()) if now is None else now
    try:
        first,last=date.fromisoformat(start),date.fromisoformat(end)
        if last<first or (last-first).days>89 or first<datetime.fromtimestamp(now,TZ).date()-timedelta(days=89) or last>datetime.fromtimestamp(now,TZ).date():raise ValueError()
    except (ValueError,TypeError):raise ValueError('请选择最近 90 天内且不超过 90 天的区间')
    where="day>=? AND day<=?";params=(start,end)
    with get_db() as db:
        totals=dict(db.execute('''SELECT COUNT(CASE WHEN kind='page_view' THEN 1 END) pv,
          COUNT(DISTINCT CASE WHEN kind='page_view' THEN browser_id END) uv,
          COUNT(DISTINCT CASE WHEN kind='page_view' AND is_returning=1 THEN browser_id END) returning_uv,
          COUNT(CASE WHEN kind='page_view' AND browser_id IS NULL THEN 1 END) anonymous_pv,
          COUNT(CASE WHEN kind='content_view' THEN 1 END) content_views,
          COUNT(CASE WHEN kind='material_export' THEN 1 END) exports,
          COUNT(CASE WHEN kind='material_read' THEN 1 END) material_reads,
          COUNT(DISTINCT CASE WHEN kind='material_read' AND is_returning=1 THEN browser_id END) repeat_readers
          FROM fieldtofit_analytics_events WHERE '''+where,params).fetchone())
        t0=int(datetime.combine(first,datetime.min.time(),TZ).timestamp());t1=int(datetime.combine(last+timedelta(days=1),datetime.min.time(),TZ).timestamp())
        totals['sessions']=db.execute('SELECT COUNT(*) FROM fieldtofit_analytics_sessions WHERE started_at>=? AND started_at<?',(t0,t1)).fetchone()[0]
        totals['return_rate']=totals['returning_uv']/totals['uv'] if totals['uv'] else None
        trend=[dict(r) for r in db.execute('SELECT * FROM fieldtofit_analytics_daily WHERE '+where+' ORDER BY day',params).fetchall()]
        pages=[dict(r) for r in db.execute("SELECT path,COUNT(*) pv,COUNT(DISTINCT browser_id) uv FROM fieldtofit_analytics_events WHERE "+where+" AND kind='page_view' GROUP BY path ORDER BY pv DESC",params).fetchall()]
        contents=[dict(r) for r in db.execute("SELECT content_id,COUNT(*) views FROM fieldtofit_analytics_events WHERE "+where+" AND kind='content_view' GROUP BY content_id ORDER BY views DESC",params).fetchall()]
        sources=[dict(r) for r in db.execute('SELECT source,entry,COUNT(*) sessions FROM fieldtofit_analytics_sessions WHERE started_at>=? AND started_at<? GROUP BY source,entry ORDER BY sessions DESC',(t0,t1)).fetchall()]
        actions=[dict(r) for r in db.execute('SELECT kind,COUNT(*) count FROM fieldtofit_analytics_events WHERE '+where+' GROUP BY kind',params).fetchall()]
        state=db.execute('SELECT * FROM fieldtofit_analytics_state WHERE id=1').fetchone()
    return {'start':start,'end':end,'totals':totals,'trend':trend,'pages':pages,'contents':contents,'sources':sources,'actions':actions,
            'started_at':a.iso(state['started_at']) if state else None,'updated_at':a.iso(state['updated_at']) if state else None,
            'status':'not_started' if not state else 'active' if config()['enabled'] else 'paused','config':config(),
            'coverage':'仅含启用后成功接收的数据；缺失日期不表示零访问，停采及网络失败可能缺测。首日不完整。UV 按浏览器估算；复制接入地址不代表连接成功。再次取材为较早自然日已观测浏览器的成功原文读取，非任务成功率。MCP/AI 客户端不纳入浏览器访问或复访；连接成功尚无客户端回执。'}


@bp.after_request
def no_store(response):response.headers['Cache-Control']='private, no-store';return response

@bp.get('/api/analytics/config')
def public_config():return jsonify(config())

@bp.post('/api/analytics/events')
def events():
    if not config()['enabled']:return '',204
    if request.headers.get('Origin')!=a.site_origin() or request.host_url.rstrip('/')!=a.site_origin() or request.headers.get('Sec-Fetch-Site') not in (None,'same-origin'):return jsonify(detail='Origin not allowed'),403
    ua=request.headers.get('User-Agent','')
    if not ua or a.BOT.search(ua) or request.headers.get('DNT')=='1' or request.headers.get('Sec-GPC')=='1' or request.headers.get('X-Admin-Password'):return '',204
    if not request.is_json or (request.content_length or 0)>4096:return jsonify(detail='Invalid event'),400
    data=request.get_json(silent=True)
    allowed={'browser_id','event_id','kind','path','content_id','referrer','campaign','consent','opt_out'}
    if not isinstance(data,dict) or set(data)-allowed:return jsonify(detail='Invalid event'),400
    if data.get('opt_out') is True:return '',204
    if config()['consent_required'] and data.get('consent') is not True:return '',204
    if not isinstance(data.get('event_id'),str) or not a.UUID.fullmatch(data['event_id']) or (data.get('browser_id') is not None and (not isinstance(data['browser_id'],str) or not a.UUID.fullmatch(data['browser_id']))):return jsonify(detail='Invalid identifier'),400
    if data.get('kind') not in KINDS:return jsonify(detail='Invalid kind'),400
    path=data.get('path');ident=data.get('content_id')
    if not isinstance(path,str) or (path not in a.PUBLIC_PATHS and not re.fullmatch(r'/(news/D-\d{2,}|watch/CW-[MATSH]\d{2,})',path)):return jsonify(detail='Invalid page'),400
    if ident is not None and (not isinstance(ident,str) or not CONTENT.fullmatch(ident)):return jsonify(detail='Invalid content'),400
    if data['kind']=='content_view' and not ident:return jsonify(detail='Content required'),400
    if any(not isinstance(data.get(k,''),str) or len(data.get(k,''))>1000 for k in ('referrer','campaign')):return jsonify(detail='Invalid source'),400
    try:
        from backend.knowledge.stewardship import public_status
        for cid in {ident,path.rsplit('/',1)[-1] if path.startswith(('/news/','/watch/')) else None}-{None}:
            if public_status(cid)['availability']=='unavailable':return jsonify(detail='Content unavailable'),400
        if not record(data):return jsonify(detail='Rate limited'),429
        return '',204
    except Exception:return jsonify(status='unavailable'),503

@bp.get('/api/admin/analytics/summary')
@admin_required
def report():
    today=day(time.time());start=request.args.get('start',today);end=request.args.get('end',today)
    try:return jsonify(summary(start,end))
    except ValueError as e:return jsonify(detail=str(e)),400
    except Exception:return jsonify(status='unavailable'),503

@bp.get('/api/admin/analytics/export')
@admin_required
def export():
    try:data=summary(request.args.get('start',day(time.time())),request.args.get('end',day(time.time())))
    except ValueError as e:return jsonify(detail=str(e)),400
    except Exception:return jsonify(status='unavailable'),503
    out=io.StringIO();writer=csv.writer(out);writer.writerow(['section','dimension','metric','value'])
    for key,val in data['totals'].items():writer.writerow(['total',data['start']+' / '+data['end'],key,'' if val is None else val])
    for group,dimension in [('trend','day'),('pages','path'),('contents','content_id'),('sources','source'),('actions','kind')]:
        for row in data[group]:
            for key,val in row.items():
                if key!=dimension:writer.writerow([group,row[dimension],key,val])
    response=Response('\ufeff'+out.getvalue(),mimetype='text/csv');response.headers['Content-Disposition']='attachment; filename="fieldtofit-traffic.csv"';return response
