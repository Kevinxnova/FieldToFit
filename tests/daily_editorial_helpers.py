"""Synthetic evidence for isolated tests, never a publishable research record."""
from backend.daily_briefing.editorial import TOPICS
from backend.daily_briefing.schema import instant, stamp


def modernize(data):
    data['layout_version']=2
    data['section_notes']['business']={'zh':'隔离测试：本期无商业事件。','en':'Isolated test: no business event selected.'}
    return data


def evidence_fields(data):
    at=data['cutoff_at']; refs=[s['id'] for s in data['sources'][:3]]
    rows=[]
    for section,topics in TOPICS.items():
        for i,topic in enumerate(topics):
            for region in ('cn','global'):
                rows.append({'section':section,'topic':topic,'region':region,'method':'search','query':'Synthetic test query '+topic,'source_ids':refs,'status':'checked','checked_at':at,'note':'Synthetic successful search record for isolated testing.'})
            for method in ('official','media'):
                rows.append({'section':section,'topic':topic,'region':'global','method':method,'query':'Synthetic source check '+topic,'source_ids':refs,'status':'checked','checked_at':at,'note':'Synthetic successful source record for isolated testing.'})
    return {'research_checks':rows,
            'event_checks':[{'story_id':s['id'],'event_time':s['event_date'],'timing_basis':'Synthetic date-only source with a manually checked test window.','event_status':'announced','attribution':'official','source_ids':s['source_ids'],'independent_publishers':[],'verified_claim':'Synthetic event claim for isolated integration testing only.'} for s in data['stories']],
            'product_checks':[{'product_id':p['id'],'release_time':p['release_date'],'release_status':'stable','source_ids':p['source_ids'],'verified_claim':'Synthetic product claim for isolated integration testing only.'} for p in data['products']]}


def layout_sample():
    """Explicitly labelled local layout fixture, not a current news edition."""
    import json
    from pathlib import Path
    data=modernize(json.loads((Path(__file__).parent/'fixtures/daily-2026-10-13.json').read_text()))
    data.pop('image',None)
    data['headline']={'zh':'九栏目版式验收样刊','en':'Nine-section layout sample'}
    data['intro']={'zh':'本页使用10月13日历史样刊内容验证新版排版；商业动态为明确标注的测试文字，不作为今日新闻发布。','en':'This page uses the October 13 historical sample to validate the new layout. Business copy is explicitly marked as test content and is not current news.'}
    data['sources'].append({'id':'business-test-source','title':{'zh':'隔离测试来源','en':'Isolated test source'},'url':'https://example.org/isolated-business-fixture','published_at':'2026-10-13','checked_at':data['cutoff_at']})
    data['stories'].append({'id':'business-layout-test','event_key':'business-layout-test','section':'business','dimensions':['business'],'event_date':'2026-10-13',
        'title':{'zh':'商业动态排版测试：签约与交割分别呈现','en':'Business layout test: distinguish signing from closing'},
        'summary':{'zh':'这是一条版式验收文字，用于检查商业动态位于监管政策之后、AI股市之前。正式稿件须逐项核对币种、交易金额、参与方和实际交易状态。','en':'This is layout test copy used to verify that business follows policy and precedes AI markets. Actual editions must verify the currency, transaction value, parties and current transaction stage.'},
        'analysis':{'zh':'标题、正文、日期与来源链接保持同一阅读层级，不把收购协议写成已经完成交割。','en':'Keep the title, copy, date and source at the same reading level. A signed acquisition agreement does not establish that the transaction has closed.'},'source_ids':['business-test-source'],'highlight':False})
    return data
