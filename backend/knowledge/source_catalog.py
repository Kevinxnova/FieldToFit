"""Shared source manifest. Registration is not successful collection or publication."""
from urllib.parse import urlsplit
from backend.db import get_db
from backend.knowledge import store

ORGANIZATIONS = [
 ('openai','OpenAI',['GPT','Codex'],'openai','https://openai.com/news/'),
 ('anthropic','Anthropic',['Claude','Claude Code'],None,'https://www.anthropic.com/news'),
 ('google','Google',['Gemini','Gemma'],'google','https://blog.google/technology/ai/'),
 ('xai','xAI',['Grok'],'xai-org','https://x.ai/news'),
 ('meta','Meta',['Llama'],'meta-llama','https://ai.meta.com/blog/'),
 ('kimi','Kimi',['Kimi'],'moonshotai','https://www.kimi.com/'),
 ('glm','GLM',['GLM'],'zai-org','https://z.ai/'),
 ('qwen','Qwen',['Qwen','百炼（阿里云服务平台）'],'Qwen','https://qwen.ai/'),
 ('mimo','MiMo',['MiMo'],'XiaomiMiMo','https://mimo.xiaomi.com/'),
 ('minimax','MiniMax',['MiniMax'],'MiniMaxAI','https://www.minimax.io/'),
 ('deepseek','DeepSeek',['DeepSeek'],'deepseek-ai','https://www.deepseek.com/'),
 ('bytedance','字节',['Seed','Doubao','火山方舟'],'ByteDance-Seed','https://seed.bytedance.com/'),
]


def definitions():
    rows=[]
    def add(ident,name,url,mode,company='',**cfg):
        rows.append({'id':'daily-'+ident,'name':name,'category':'official' if company else 'discovery',
          'url':url,'adapter':'daily_discovery','config':{'daily_enabled':True,'mode':mode,'company':company,
          'limit':4,'pages_per_day':1,'history_days':7,**cfg}})
    for ident,name,products,author,url in ORGANIZATIONS:
        if author:
            add(ident+'-models',name+' · 官方模型卡','https://huggingface.co/'+author,'hub',ident,author=author,
                scope='该组织公开模型与模型卡；不覆盖未托管的闭源产品')
    add('openai-news','OpenAI · 官方公告','https://openai.com/news/rss.xml','feed','openai',scope='官方新闻订阅，原文逐条核对')
    add('google-news','Google · AI 官方动态','https://blog.google/technology/ai/rss/','feed','google',scope='Google AI 官方订阅')
    add('anthropic-news','Anthropic · 官方公告','https://www.anthropic.com/news','index','anthropic',path_prefix='/news/',scope='官方新闻列表和文章正文')
    for ident,name,url,mode,prefix,scope in [
      ('deepseek','DeepSeek','https://api-docs.deepseek.com/updates/','document','','官方 API 更新日志；同网址正文更正也复查'),
      ('kimi','Kimi','https://www.kimi.com/en/blog/','index','/en/blog/','Kimi 官方研究与模型发布；不代表全部开放平台服务及客户端动态'),
      ('glm','GLM','https://docs.z.ai/release-notes/new-released','document','','Z.AI 模型与服务更新；不代表全部国内平台公告'),
      ('minimax','MiniMax','https://platform.minimax.io/docs/release-notes/models','document','','官方模型发布记录；客户端变化另行核对'),
      ('xai','xAI','https://x.ai/news','index','/news/','官方公告及产品发布'),
      ('meta','Meta','https://ai.meta.com/blog/','index','/blog/','Meta AI 官方博客；不含其他 Meta 产品全部动态'),
      ('qwen','Qwen','https://qwen.ai/research','qwen','/blog','Qwen 官方研究发布；百炼服务公告不混作模型公告'),
      ('mimo','MiMo','https://mimo.xiaomi.com/','document','','官方产品页面变化；不代表已接入独立 API 更新日志'),
      ('bytedance','字节 Seed','https://seed.bytedance.com/en/blog','index','/en/blog/','Seed 技术博客；豆包客户端及火山平台另行核对'),
    ]:
        add(ident+'-announcements',name+' · 官方发布与变化',url,mode,ident,path_prefix=prefix,
            scope=scope,channel_role='announcements',recheck_body=True,history_days=365)
    add('github-agents','GitHub · Agent / Harness 项目','https://github.com/topics/ai-agents','github',query='topic:ai-agents archived:false',scope='公开 ai-agents 主题项目，按近期更新及累计关注发现；不代表能力排名')
    add('github-skills','GitHub · Skill 项目','https://github.com/topics/agent-skills','github',query='topic:agent-skills archived:false',scope='公开 agent-skills 主题仓库；核对 README 和使用入口')
    add('hub-discovery','Hugging Face · 新模型发现','https://huggingface.co/models','hub',scope='公开模型最近变化，非全部模型评测')
    add('hn','Hacker News · AI 讨论线索','https://hn.algolia.com/api/v1/search_by_date','hn',scope='AI / Agent / 模型相关讨论；原始出处未读前保留待核实')
    add('hn-hot','Hacker News · 高讨论补扫','https://hn.algolia.com/api/v1/search','hn_hot',limit=20,
        scope='近7天高讨论标题，先收线索再由本地核对是否与 AI 有关；无需标题含 AI')
    services=[
        ('doubao-ios','豆包 · iOS 版本记录','https://apps.apple.com/cn/app/id6459478672','apple','client','bytedance','iOS'),
        ('doubao-mac','豆包 · Mac 版本记录','https://apps.apple.com/cn/app/id6683305962','apple','client','bytedance','macOS'),
        ('ark-models','火山方舟 · 模型发布','https://docs.volcengine.com/docs/ark/model-release-announcement?lang=zh','ark','model','bytedance','火山方舟'),
        ('ark-platform','火山方舟 · 产品更新','https://docs.volcengine.com/docs/ark/product-update-announcements?lang=zh','ark','platform','bytedance','火山方舟'),
        ('ark-deprecation','火山方舟 · 模型下线','https://docs.volcengine.com/docs/ark/model-deprecation-notice?lang=zh','ark','deprecation','bytedance','火山方舟'),
        ('bailian-models','百炼 · 模型上下架与更新','https://help.aliyun.com/zh/model-studio/newly-released-models','bailian','model','qwen','百炼'),
        ('bailian-platform','百炼 · 模型平台功能','https://help.aliyun.com/zh/model-studio/model-release-notes','bailian','platform','qwen','百炼'),
        ('bailian-apps','百炼 · 应用功能','https://help.aliyun.com/zh/model-studio/application-release-notes','bailian','app','qwen','百炼'),
        ('bailian-deprecation','百炼 · 模型下线','https://help.aliyun.com/zh/model-studio/model-depreciation','bailian','deprecation','qwen','百炼'),
        ('mimo-api-models','MiMo API · 模型发布','https://mimo.mi.com/docs/en-US/updates/model','mimo','model','mimo','MiMo API'),
        ('mimo-api-deprecation','MiMo API · 模型下线','https://mimo.mi.com/docs/en-US/updates/deprecate','mimo','deprecation','mimo','MiMo API'),
        ('mimo-api-platform','MiMo API · 平台更新','https://mimo.mi.com/docs/en-US/updates/feature/platform','mimo','platform','mimo','MiMo API'),
    ]
    for ident,name,url,provider,kind,company,platform in services:
        add(ident+'-announcements',name,url,'service',company,provider=provider,notice_kind=kind,platform=platform,
            document_code=urlsplit(url).path.rsplit('/',1)[-1] if provider=='ark' else '',
            limit=5,history_days=30,channel_role='service',scope=platform+' 官方'+name.split(' · ')[-1]+'；逐条保存日期、型号、平台及地域，首次建立历史基线')
    add('research','arXiv · 重点对象相关研究','https://export.arxiv.org/api/query','arxiv',limit=8,
        scope='与重点模型和 Agent 相关的论文标题/摘要，不代表全部 AI 论文或已同行评审')
    add('map-research','技术地图 · 近30日研究与修订','https://export.arxiv.org/api/query','arxiv',limit=8,history_days=30,recheck_body=True,
        scope='技术地图近30日研究线索与潜在修订；分页保留积压，摘要不等于读过报告，实质修订须本地核对')
    return rows


def seed():
    with get_db() as db:
        for s in definitions():
            db.execute('INSERT OR IGNORE INTO knowledge_sources(id,name,category,url,adapter,config) VALUES(?,?,?,?,?,?)',
                       (s['id'],s['name'],s['category'],s['url'],s['adapter'],store.encode(s['config'])))


def registry(admin=False):
    from backend.knowledge.sources import list_sources
    from backend.knowledge.platform_sources import status
    from backend.knowledge.content_workspace import seeds, load_published, CONTENT
    sources=list_sources(); byid={s['id']:s for s in sources}; declared=definitions()
    published=[]
    for kind, fallback in seeds().items():
        if kind=='charts':continue
        for p in load_published(kind,CONTENT / (kind+'.json')).get('items',[]):
            if p.get('state')!='withdrawn':published.append((kind,p))
    channels=[]
    with get_db() as db:
        for s in sources:
            cfg=s['config']; runtime=status(db,s['id'])
            daily=cfg.get('daily_enabled') is True and s['adapter']=='daily_discovery'
            if s['adapter']=='platform_repository':
                daily=bool(db.execute("SELECT 1 FROM knowledge_records r JOIN knowledge_selections k ON k.record_id=r.id WHERE r.source_id=? AND k.state!='withdrawn' AND EXISTS(SELECT 1 FROM knowledge_publications p WHERE p.record_id=r.id AND p.state='published')",(s['id'],)).fetchone())
            u=urlsplit(s['url']);safe_url=u._replace(query='',fragment='',netloc=u.hostname or '').geturl() if not u.username else ''
            channel={'id':s['id'],'name':s['name'],'url':safe_url,'company':cfg.get('company',''),
               'scope':cfg.get('scope') or ('已发布仓库的原始文件' if s['adapter']=='platform_repository' else '兼容采集配置，未纳入正式日调度'),
               'mode':cfg.get('mode') or s['adapter'],'daily_scheduled':daily and s['enabled'],**runtime,
               'access':'公开入口；受来源限流和可读取范围限制。未获取材料不计为已核实。'}
            channel['scope']=cfg.get('scope') or ('已发布仓库的原始文件' if s['adapter']=='platform_repository' else '兼容采集配置，未纳入正式日调度')
            if admin:channel['error']=s.get('error','')
            channels.append(channel)
    tracked=[]
    for ident,name,products,author,url in ORGANIZATIONS:
        linked=[c for c in channels if c['company']==ident]
        collected=[c for c in linked if c['last_success_at']]
        domains={urlsplit(url).hostname}
        matches=[]
        for kind,p in published:
            urls=[x.get('url','') for x in p.get('sources',[])]
            if any(urlsplit(u).hostname in domains or (author and u.lower().startswith(('https://huggingface.co/'+author+'/').lower())) for u in urls):
                matches.append({'id':p['id'],'name':p.get('name') or p.get('title'),'kind':kind})
        planned=[] if ident in ('openai','anthropic','google') or any(c['id']=='daily-'+ident+'-announcements' for c in linked) else ['官方公告及闭源产品变化入口待接入']
        expected={s['id'] for s in declared if s['config'].get('company')==ident and s['config'].get('mode')=='service'}
        missing=expected-set(byid)
        if missing:planned.append('部分服务公告配置待升级接入：'+str(len(missing))+' 个；注册后仍需正文采集验证')
        if ident=='bytedance':planned.append('豆包 Android、Windows、网页端稳定公开更新日志尚未确认')
        tracked.append({'id':ident,'name':name,'products':products,'official_url':url,
            'tracking':['新发布与版本变化','使用材料与开放情况'],'channels':linked,'planned':planned,
            'registered_count':len(linked),'successful_count':len(collected),'published':matches})
    return {'tracked':tracked,'channels':channels,'interval_days':1,'schedule':'06:30 Asia/Shanghai',
       'scope':'实际配置与最后成功检查；已注册、已采集和已发布分别记录。','observed_at':store.now()}
