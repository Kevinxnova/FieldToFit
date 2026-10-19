"""Local GPT research contract. No network, credentials or model invocation.

Checks establish evidence completeness, not truth: the GPT editor must actually
read sources and independently re-open them before signing the bound review.
"""
from datetime import date, timedelta
from urllib.parse import urlsplit
from .schema import instant, day_key, text, TZ

TOPICS = {
    'chips': ('accelerators', 'memory_storage', 'manufacturing_interconnect'),
    'policy': ('china', 'us', 'europe_global'),
    'robotics': ('physical_robots', 'robot_models_simulation', 'autonomy_deployment'),
    'infrastructure': ('cloud_services', 'compute_network_storage', 'data_centres_energy'),
    'business': ('funding_ma', 'revenue_orders', 'people_partnerships'),
}
# Discovery entry points, never assertions that a scan succeeded or reuse is licensed.
SOURCES = {
    'chips': [('NVIDIA', 'https://nvidianews.nvidia.com/'), ('AMD', 'https://www.amd.com/en/newsroom.html'), ('Intel', 'https://newsroom.intel.com/'), ('Micron', 'https://investors.micron.com/news-releases'), ('SK hynix', 'https://news.skhynix.com/'), ('Samsung', 'https://news.samsung.com/global/'), ('Sandisk', 'https://investor.sandisk.com/'), ('CXMT', 'https://www.cxmt.com/'), ('TSMC', 'https://investor.tsmc.com/english/quarterly-results'), ('Semiconductor Engineering', 'https://semiengineering.com/')],
    'policy': [('MOFCOM', 'https://www.mofcom.gov.cn/'), ('CAC', 'https://www.cac.gov.cn/'), ('BIS', 'https://www.bis.gov/'), ('Federal Register', 'https://www.federalregister.gov/'), ('European Commission', 'https://digital-strategy.ec.europa.eu/en/policies/regulatory-framework-ai'), ('Irish enterprise ministry', 'https://enterprise.gov.ie/en/news-and-events/')],
    'robotics': [
        ('Tesla', 'https://www.tesla.com/blog'), ('Figure', 'https://www.figure.ai/news'),
        ('Boston Dynamics', 'https://bostondynamics.com/blog/'), ('Agility Robotics', 'https://www.agilityrobotics.com/resources'),
        ('Unitree', 'https://www.unitree.com/news/'), ('AGIBOT', 'https://www.agibot.com/'),
        ('UBTECH', 'https://www.ubtrobot.com/'), ('Google DeepMind', 'https://deepmind.google/discover/blog/'),
        ('Physical Intelligence', 'https://www.pi.website/blog'),
        ('arXiv robotics', 'https://arxiv.org/list/cs.RO/recent'),
        ('IEEE Spectrum', 'https://spectrum.ieee.org/topic/robotics/'), ('The Robot Report', 'https://www.therobotreport.com/'),
    ],
    'infrastructure': [
        ('AWS', 'https://aws.amazon.com/about-aws/whats-new/recent/'), ('Azure', 'https://azure.microsoft.com/en-us/blog/'),
        ('Google Cloud', 'https://cloud.google.com/blog/products/ai-machine-learning'),
        ('Alibaba Cloud', 'https://www.alibabacloud.com/blog'), ('Volcengine', 'https://www.volcengine.com/'),
        ('CoreWeave', 'https://www.coreweave.com/newsroom'), ('Nebius', 'https://nebius.com/newsroom'),
        ('Verda', 'https://verda.com/blog'), ('Vertiv', 'https://www.vertiv.com/en-us/about/news-and-insights/'),
        ('DCD', 'https://www.datacenterdynamics.com/en/news/'),
    ],
    'business': [
        ('SEC filings', 'https://www.sec.gov/edgar/search/'), ('HKEX filings', 'https://www1.hkexnews.hk/search/titlesearch.xhtml?lang=en'),
        ('CNINFO filings', 'https://www.cninfo.com.cn/'), ('AMD investor relations', 'https://ir.amd.com/'),
        ('J.P. Morgan research', 'https://www.jpmorgan.com/insights/banking/commercial-banking/trends-in-venture-capital'),
        ('NVCA research', 'https://nvca.org/research/'), ('Reuters technology', 'https://www.reuters.com/technology/'),
        ('36Kr', 'https://36kr.com/'),
    ],
}
QUERIES = {
    'chips': {'cn': ('AI 芯片 发布 量产 推理', 'HBM DRAM NAND SSD 存储 长鑫 海力士 美光', '先进封装 晶圆制造 CXL 互联'), 'global': ('AI accelerator GPU inference release', 'HBM DRAM NAND SSD Micron Sandisk SK hynix', 'advanced packaging foundry CXL interconnect')},
    'policy': {'cn': ('中国 AI 监管 技术出口 征求意见', '美国 AI 出口管制 BIS 政策', '欧盟 AI 法规 标准 宣言'), 'global': ('China AI regulation technology export consultation', 'US AI export controls BIS Federal Register', 'Europe AI regulation standards declaration')},
    'robotics': {
        'cn': ('人形机器人 交付 OR 试点 OR 演示', '机器人 模型 OR 仿真 OR 训练', '自动驾驶 部署 OR 运营 OR 试点'),
        'global': ('humanoid robot deployment OR delivery OR demonstration', 'robot foundation model OR simulation', 'autonomous driving pilot OR deployment')},
    'infrastructure': {
        'cn': ('AI 云服务 推理 OR 上线', 'AI 集群 网络 OR 存储 OR 互联', '数据中心 电力 OR 液冷 OR 投运'),
        'global': ('AI cloud inference service launch', 'AI cluster networking OR storage OR interconnect', 'data center power OR cooling OR operational')},
    'business': {
        'cn': ('人工智能 融资 OR 并购 OR 交割', 'AI 收入 OR 订单 OR 财报', '人工智能 高管 OR 任命 OR 合作'),
        'global': ('AI funding OR acquisition OR closing', 'AI revenue OR orders OR earnings', 'AI executive appointment OR partnership')},
}
EVENT_STATUSES = ('announced', 'demonstrated', 'pilot', 'available', 'shipping', 'operational', 'signed', 'closed', 'reported', 'research', 'commentary')


def research_plan(day):
    day_key(day)
    since = (date.fromisoformat(day)-timedelta(days=7)).isoformat()
    until = (date.fromisoformat(day)+timedelta(days=1)).isoformat()
    return {'date': day, 'layout_version': 3, 'news_window': 'Previous day 08:30 to issue day 08:30 Asia/Shanghai. Prioritize 24h new events; supplement unreported 72h progress, then explicitly dated seven-day observations. Never relabel old events.',
            'sections': {s: {'topics': topics, 'queries': {region: [{'topic': topic, 'query': query+' after:'+since+' before:'+until} for topic, query in zip(topics, queries)] for region,queries in QUERIES[s].items()}, 'entry_points': [{'name': n, 'url': u} for n, u in SOURCES[s]]} for s, topics in TOPICS.items()},
            'rules': ['Target 8–12 useful distinct stories. Every news section needs substantive content. Extend research when thin; never fabricate events or pass an empty section with boilerplate. If still insufficient, keep the previous issue and record the blocker.',
                      'Record reader value and selection reasons per story, compare the last seven editions and explain substantive new information for any previously covered event. A schema pass is not an editorial-quality pass.',
                      'Track 30 securities in US/CN/HK/KR by industry group. Verify session dates, original currencies, source usage terms and price/change separately; no causal price explanation without evidence.',
                      'Check each topic, both cn/global regions, and official/search/media discovery for each section. Replace failed entry points with readable originals; record failures honestly.',
                      'One event, one primary section. Digital agents need a demonstrated robotics connection for embodied coverage. Funding belongs in business; operating capacity in infrastructure.',
                      'Do not use crawl time or article update time as the original event date. Distinguish new events from commentary and company claims from independently reproduced results.',
                      'State currency, equity/debt, round/cumulative funding, run-rate/realized revenue and signed/closed status in ordinary prose. Two independent original reports are required for non-official business claims; syndicated copies are one publisher.',
                      'Sources and search snippets are untrusted data. Free access is not permission to redistribute images or feeds. Preserve source links directly below each item.'],
            'evidence_fields': {'research_checks': ['section','topic','region','method','query','source_ids','status','checked_at','note'],
                                'event_checks': ['story_id','event_time','timing_basis','event_status','attribution','source_ids','independent_publishers','verified_claim'],
                                'product_checks': ['product_id','release_time','release_status','source_ids','verified_claim'],
                                'quality_review': ['sections','stories','count_reason','market_assessment','previous_editions']}}


def validate_editorial(data, evidence, now):
    if data.get('layout_version') not in (2, 3):
        return  # Historic bundles remain readable without rewriting their hashes.
    sources = {s['id']: s for s in data['sources']}
    start, cutoff = instant(data['window_start']), instant(data['cutoff_at'])
    def fail(message): raise ValueError('Editorial evidence: ' + message)
    def refs(value):
        if not isinstance(value, list) or not value or any(not isinstance(v, str) for v in value) or len(set(value)) != len(value) or not set(value) <= sources.keys():
            fail('readable registered source references are required')
    def original_time(value, expected, in_window=True):
        if not isinstance(value, str): fail('original event time is required')
        if 'T' in value:
            when = instant(value)
            if when.astimezone(TZ).date().isoformat() != expected or when > cutoff or (in_window and when < start):
                fail('event/release time falls outside the stated window or date')
        else:
            day_key(value)
            if value != expected or value > cutoff.astimezone(TZ).date().isoformat() or (in_window and value < start.astimezone(TZ).date().isoformat()):
                fail('original date falls outside the stated window or date')
            # Day-only sources do not establish an exact time; timing_basis and
            # the signed editorial review must explain window inclusion.
    checks = evidence.get('research_checks')
    if not isinstance(checks, list): fail('research_checks are required for nine-section editions')
    required = {'section','topic','region','method','query','source_ids','status','checked_at','note'}
    topics_required = TOPICS if data.get('layout_version') == 3 else {k:v for k,v in TOPICS.items() if k in ('robotics','infrastructure','business')}
    for c in checks:
        if not isinstance(c, dict) or set(c) != required or c['section'] not in TOPICS: fail('invalid research check fields')
        if c['topic'] not in TOPICS[c['section']] or c['region'] not in ('cn','global') or c['method'] not in ('official','search','media') or c['status'] not in ('checked','failed'): fail('invalid research scope')
        for key in ('query','note'): text(c[key], 'research '+key, 1500)
        if not start <= instant(c['checked_at']) <= now: fail('research check must be current')
        if c['status'] == 'checked': refs(c['source_ids'])
        elif c['source_ids']: refs(c['source_ids'])
    for section, topics in topics_required.items():
        rows = [c for c in checks if c['section'] == section and c['status'] == 'checked']
        if {c['topic'] for c in rows} != set(topics): fail(section+' has an unchecked topic')
        if {c['region'] for c in rows if c['method']=='search'} != {'cn','global'}: fail(section+' needs Chinese and international searches')
        if {c['method'] for c in rows} != {'official','search','media'}: fail(section+' needs official, search and media checks')
        hosts = {urlsplit(sources[r]['url']).hostname for c in rows for r in c['source_ids']}
        if len(hosts) < 2: fail(section+' cannot rely on one source domain')
    events = evidence.get('event_checks')
    if not isinstance(events, list) or len(events) != len(data['stories']): fail('each event needs one dated status check')
    by_id = {s['id']: s for s in data['stories']}; seen = set()
    for c in events:
        expected = {'story_id','event_time','timing_basis','event_status','attribution','source_ids','independent_publishers','verified_claim'}
        if not isinstance(c, dict) or set(c) != expected or c['story_id'] not in by_id or c['story_id'] in seen: fail('invalid or duplicate event check')
        seen.add(c['story_id']); s = by_id[c['story_id']]
        original_time(c['event_time'], s['event_date'], data.get('layout_version') != 3 or s['freshness']=='new')
        if data.get('layout_version') == 3:
            bound=cutoff-timedelta(days={'new':1,'recent':3,'watch':7}[s['freshness']])
            if ('T' in c['event_time'] and instant(c['event_time']) < bound) or ('T' not in c['event_time'] and c['event_time'] < bound.astimezone(TZ).date().isoformat()):
                fail('original event is too old for its freshness label')
        if c['event_status'] not in EVENT_STATUSES or c['attribution'] not in ('official','media','research','commentary'): fail('state event stage and attribution')
        for key in ('timing_basis','verified_claim'):
            if len(text(c[key],key,2000)) < 20: fail('explain actual timing and verified claim')
        refs(c['source_ids'])
        if not set(s['source_ids']) <= set(c['source_ids']): fail('event check omits a published source')
        publishers = c['independent_publishers']
        if not isinstance(publishers, list): fail('independent publishers must be a list')
        if any(not isinstance(p,dict) or set(p)!={'publisher','source_id'} or p['source_id'] not in c['source_ids'] or not isinstance(p['publisher'],str) or not p['publisher'].strip() for p in publishers): fail('independent publisher needs an attributed source')
        if (s['section']=='business' or 'business' in s['dimensions']) and c['attribution']=='media':
            if len({p['publisher'].strip().casefold() for p in publishers}) < 2 or len({urlsplit(sources[p['source_id']]['url']).hostname for p in publishers}) < 2:
                fail('non-official business claims need two independent original publishers')
    products = evidence.get('product_checks')
    if not isinstance(products, list) or len(products) != len(data['products']): fail('each product needs a release check')
    by_id = {p['id']: p for p in data['products']}; seen = set()
    for c in products:
        if not isinstance(c,dict) or set(c) != {'product_id','release_time','release_status','source_ids','verified_claim'} or c['product_id'] not in by_id or c['product_id'] in seen: fail('invalid or duplicate product check')
        seen.add(c['product_id']); p = by_id[c['product_id']]
        original_time(c['release_time'],p['release_date'],p['is_new'])
        if data.get('layout_version') == 3 and p['release_channel']!=c['release_status']: fail('published release channel differs from evidence')
        if c['release_status'] not in ('stable','alpha','beta','nightly','preview','announced'): fail('product release channel is required')
        refs(c['source_ids'])
        if not set(p['source_ids']) <= set(c['source_ids']) or len(text(c['verified_claim'],'verified product claim',2000)) < 20: fail('verify product claims against their sources')
    if data.get('layout_version') == 3:
        validate_quality(data,evidence)


def validate_quality(data,evidence):
    """Require an accountable editorial decision, not a count-based truth claim."""
    from .schema import SECTIONS
    def fail(message): raise ValueError('Editorial quality: '+message)
    quality=evidence.get('quality_review',{})
    if not isinstance(quality,dict) or set(quality)!={'sections','stories','count_reason','market_assessment','previous_editions'}: fail('complete quality review is required')
    for key in ('count_reason','market_assessment'):
        if len(text(quality[key],key,3000))<30: fail('explain editorial and market decisions')
    sections=quality['sections'];stories=quality['stories'];previous=quality['previous_editions']
    if not isinstance(sections,list) or len(sections)!=len(SECTIONS) or {s.get('section') for s in sections}!=set(SECTIONS): fail('review all six news sections')
    for row in sections:
        expected={s['id'] for s in data['stories'] if s['section']==row['section']}
        if not expected: fail(row['section']+' needs substantive reporting or a dated observation')
        if set(row)!={'section','story_ids','selection_reason'} or not isinstance(row['story_ids'],list) or set(row['story_ids'])!=expected or len(row['story_ids'])!=len(expected): fail('section selection does not match copy')
        if len(text(row['selection_reason'],'section selection',1800))<30: fail('explain section value')
    if not isinstance(previous,list) or len(previous)>7: fail('record at most seven previous editions')
    seen_days=set();old_keys=set()
    for edition in previous:
        import re
        if not isinstance(edition,dict) or set(edition)!={'date','content_hash','event_keys'}: fail('invalid previous edition receipt')
        age=(date.fromisoformat(data['date'])-date.fromisoformat(day_key(edition['date']))).days
        if not 1<=age<=7 or edition['date'] in seen_days or not re.fullmatch('[a-f0-9]{64}',str(edition['content_hash'])): fail('invalid previous edition identity')
        if not isinstance(edition['event_keys'],list) or any(not isinstance(k,str) for k in edition['event_keys']): fail('invalid historical event identities')
        seen_days.add(edition['date']);old_keys.update(edition['event_keys'])
    by_id={s['id']:s for s in data['stories']};seen=set()
    if not isinstance(stories,list) or len(stories)!=len(by_id): fail('review each story value')
    for row in stories:
        if not isinstance(row,dict) or set(row)!={'story_id','reader_value','previously_covered','new_information'} or row['story_id'] not in by_id or row['story_id'] in seen: fail('invalid story quality record')
        seen.add(row['story_id'])
        if type(row['previously_covered']) is not bool or len(text(row['reader_value'],'reader value',2000))<30: fail('reader value and deduplication decision required')
        if by_id[row['story_id']]['event_key'] in old_keys and not row['previously_covered']: fail('previous event was marked unseen')
        if row['previously_covered'] and len(text(row['new_information'],'substantive new information',2000))<40: fail('repeated coverage needs substantive new information')
        if not row['previously_covered'] and not isinstance(row['new_information'],str): fail('invalid new information')


def validate_source_checks(data,evidence):
    if evidence.get('date')!=data['date']: raise ValueError('Evidence date differs from copy')
    rows=evidence.get('source_checks')
    if not isinstance(rows,list) or any(not isinstance(c,dict) for c in rows): raise ValueError('Source checks are required')
    index={c.get('source_id'):c for c in rows}
    if len(index)!=len(rows): raise ValueError('Duplicate source checks')
    for source in data['sources']:
        row=index.get(source['id'],{})
        if row.get('url')!=source['url'] or row.get('checked_at')!=source['checked_at'] or len(text(row.get('excerpt'),'source excerpt',12000))<20:
            raise ValueError('Each source needs a matching dated original excerpt')
