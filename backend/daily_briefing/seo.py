"""Search-readable daily pages use the same permission-checked publication."""
from flask import render_template,request
from backend.knowledge.api import read_allowed
from backend.knowledge.platform import PlatformError
from backend.seo import document
from . import service
from .schema import edition_sections

def page(path,dist,english=False):
    lang='en' if english else 'zh';pick=lambda zh,en:en if english else zh
    if not read_allowed():return document(dist,'AI Daily · FieldToFit','','/for-you/daily',status=401,index=False)
    try:
        archive=service.archive(lang,30,int(request.args.get('offset','0')))
        is_archive=path=='/for-you/daily/archive';day=path.rsplit('/',1)[-1] if path!='/for-you/daily' and not is_archive else None
        issue=None if is_archive or (not day and not archive['latest']) else service.read(day,lang,int(request.args['revision']) if 'revision'in request.args else None)
        body=render_template('daily_journal.html',issue=issue,sections=edition_sections(issue) if issue else [],archive=archive,is_archive=is_archive,english=english,prefix='/en' if english else '',pick=pick)
        title=(issue['headline'] if issue else pick('AI日报','AI Daily'))+' · FieldToFit'
        return document(dist,title,issue['intro'] if issue else pick('每日重点与原始来源。','Daily essentials with original sources.'),path,body,index=bool(issue) or is_archive)
    except (PlatformError,ValueError) as e:
        status=getattr(e,'status',400)
        return document(dist,pick('日报暂不可用','Daily edition unavailable')+' · FieldToFit','',path,status=status,index=False)
    except Exception:
        return document(dist,'AI Daily · FieldToFit','',path,status=503,index=False)
