"""Additional public source channels for the 09:00 magazine, not the 08:00 workflow.

Registration is not a successful scan. The existing bounded discovery adapters
retain original dates, unfinished pagination and source failures.
"""
import time
from concurrent.futures import ThreadPoolExecutor
from backend.db import get_db
from backend.knowledge.store import encode

CHANNELS=[
 ('nvidia','NVIDIA Newsroom','https://nvidianews.nvidia.com/','index','/news/'),
 ('amd','AMD announcements','https://ir.amd.com/news-events/press-releases?category=all','index','/news-events/press-releases/detail/'),
 ('intel','Intel Newsroom','https://newsroom.intel.com/news','index','/'),
 ('figure','Figure news','https://www.figure.ai/news','index','/news/'),
 ('unitree','Unitree news','https://www.unitree.com/news/','index','/news/'),
 ('cursor','Cursor changelog','https://cursor.com/en-US/changelog','document',''),
 ('copilot','GitHub Copilot changelog','https://github.blog/changelog/label/copilot/','index','/changelog/'),
 ('openclaw','OpenClaw releases','https://github.com/openclaw/openclaw/releases.atom','feed',''),
 ('langchain','LangChain releases','https://github.com/langchain-ai/langchain/releases.atom','feed',''),
 ('crewai','CrewAI releases','https://github.com/crewAIInc/crewAI/releases.atom','feed',''),
 ('autogen','AutoGen releases','https://github.com/microsoft/autogen/releases.atom','feed',''),
 ('azure','Microsoft official blog','https://blogs.microsoft.com/','index','/blog/'),
 ('aws','AWS AI announcements','https://aws.amazon.com/blogs/machine-learning/category/news/','index','/blogs/machine-learning/'),
 ('gcp','Google Cloud blog','https://cloud.google.com/blog?hl=en','index','/blog/products/'),
 ('eu-policy','European Commission AI policy','https://digital-strategy.ec.europa.eu/en/policies/artificial-intelligence','index','/en/news/'),
 ('cn-policy','MIIT information technology policy','https://www.miit.gov.cn/jgsj/xxjsfzs/index.html','index','/jgsj/'),
 ('us-policy','US Bureau of Industry and Security','https://www.bis.gov/','index','/press-release/'),
]

def seed():
    with get_db() as db:
        for key,name,url,mode,prefix in CHANNELS:
            cfg={'daily_enabled':False,'mode':mode,'company':'journal-'+key,'path_prefix':prefix,'limit':8,'pages_per_day':1,'history_days':3,'recheck_body':True,'scope':'Morning journal source; original-date checks and incomplete pagination remain explicit.'}
            db.execute('INSERT OR IGNORE INTO knowledge_sources(id,name,category,url,adapter,config) VALUES(?,?,?,?,?,?)',('journal-'+key,name,'official',url,'daily_discovery',encode(cfg)))

def refresh(mapping,budget_seconds=220):
    from backend.knowledge.sources import run_daily
    seed();started=time.monotonic();ids=sorted({i for v in mapping.values() for i in v})
    def one(ident):
        remaining=budget_seconds-(time.monotonic()-started)
        if remaining<1:return {'id':ident,'status':'deferred'}
        result=run_daily(ident,force=True,budget_seconds=min(25,remaining))
        return {'id':ident,'status':result['status'],'results':[{k:v for k,v in r.items() if k!='error'} for r in result['results']]}
    with ThreadPoolExecutor(max_workers=3) as pool:result=list(pool.map(one,ids))
    return {'sources':result,'complete':all(r['status']=='success' for r in result)}
