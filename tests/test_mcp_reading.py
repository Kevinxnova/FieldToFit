"""Compatible bounded reading: exact reconstruction, changes and access boundaries."""
import copy
import base64
import hashlib
import json

import pytest
from test_knowledge import client, MCP
from backend.knowledge import locale, mcp, mcp_reading as reading


def call(client, name='curated_news', **args):
    return client.post('/api/mcp/curated', headers=MCP, json={'jsonrpc':'2.0','id':1,'method':'tools/call','params':{'name':name,'arguments':args}}).json['result']


@pytest.fixture
def payload(monkeypatch):
    data = {'revision':'r1','reviewed_at':'2026-10-19','items':[
        {'id':f'D-{i}','title':'标题😀'+str(i),'summary':'摘要'*400,'sources':[{'url':'https://example.org/'+str(i)}], 'body':'正文\n"😀\\'*2500}
        for i in range(13)]}
    monkeypatch.setattr(mcp, '_invoke', lambda name, args: copy.deepcopy(data))
    return data


def test_default_and_full_preserve_complete_result(client, payload):
    assert call(client)['structuredContent'] == payload
    assert call(client,response_mode='full')['structuredContent'] == payload


def test_summary_pages_are_bounded_and_complete(client, payload):
    args={'response_mode':'summary','page_size':10};seen=[]
    while True:
        result=call(client,**args)
        assert not result['isError']
        data=result['structuredContent'];seen += [i['id'] for i in data['items']]
        assert len(reading.encoded(data)) < 12000
        assert len(result['content'][0]['text'].encode('utf-8')) < 12000
        assert all(i['reading']['arguments']['response_mode']=='chunk' and i['summary_is_excerpt'] for i in data['items'])
        assert 'body' not in reading.encoded(data)
        if not data['has_more']:break
        args['response_cursor']=data['next_cursor']
    assert seen == [i['id'] for i in payload['items']]


def test_chunks_reconstruct_unicode_json_and_hash(client,payload):
    payload['items']=payload['items'][:1];args={'response_mode':'chunk','max_characters':6000};text=''
    while True:
        result=call(client,**args);assert not result['isError']
        data=result['structuredContent'];assert data['offset']==len(text)
        assert len(data['text'])<=6000
        assert len(result['content'][0]['text'].encode('utf-8')) < 12000
        text+=data['text']
        if not data['has_more']:break
        args['response_cursor']=data['next_cursor']
    assert json.loads(text)==payload
    assert hashlib.sha256(text.encode()).hexdigest()==data['content_hash']
    assert data['total_characters']==len(text) and data['next_cursor'] is None


@pytest.mark.parametrize('changed',[{'page_size':1},{'lang':'en'},{'q':'other'}])
def test_cursor_is_bound_to_original_request(client,payload,changed,monkeypatch):
    # Isolate cursor binding from translation availability of this synthetic fixture.
    monkeypatch.setattr(locale, 'project', lambda data, fields: data)
    args={'response_mode':'summary','page_size':2}
    cursor=call(client,**args)['structuredContent']['next_cursor']
    result=call(client,**{**args,**changed,'response_cursor':cursor})
    assert result['isError'] and result['structuredContent']['code']=='invalid_reading_cursor'


def test_changes_withdrawal_and_permissions_rechecked(client,payload,monkeypatch):
    args={'response_mode':'summary','page_size':2}
    cursor=call(client,**args)['structuredContent']['next_cursor']
    result=call(client,'curated_watch',**args,response_cursor=cursor)
    assert result['isError'] and result['structuredContent']['code']=='invalid_reading_cursor'
    payload['items'].pop(0)
    result=call(client,**args,response_cursor=cursor)
    assert result['isError'] and result['structuredContent']['code']=='reading_revision_changed'
    assert 'items' not in result['structuredContent']
    monkeypatch.setenv('FIELDTOFIT_READ_TOKEN','read-secret')
    assert client.post('/api/mcp/curated',headers=MCP,json={'jsonrpc':'2.0','id':1,'method':'tools/call','params':{'name':'curated_news','arguments':{**args,'response_cursor':cursor}}}).status_code==401


def test_changed_cursor_offset_is_rejected(client,payload):
    args={'response_mode':'summary','page_size':2}
    cursor=call(client,**args)['structuredContent']['next_cursor']
    changed=json.loads(base64.urlsafe_b64decode(cursor));changed['offset']+=1
    cursor=base64.urlsafe_b64encode(reading.encoded(changed).encode()).decode()
    result=call(client,**args,response_cursor=cursor)
    assert result['isError'] and result['structuredContent']['code']=='invalid_reading_cursor'


@pytest.mark.parametrize('args',[
 {'page_size':2},{'response_mode':'other'},{'response_mode':'summary','page_size':True},
 {'response_mode':'summary','page_size':11},{'response_mode':'chunk','max_characters':6001},
 {'response_mode':'chunk','page_size':1},{'response_mode':'summary','max_characters':500},
 {'response_mode':'summary','response_cursor':'not-a-cursor'},
 {'response_mode':'chunk','response_cursor':'a'*1025},
])
def test_invalid_controls_are_explicit_errors(client,payload,args):
    assert call(client,**args)['isError']


def test_empty_and_one_item_collection(client,payload):
    payload['items']=[]
    d=call(client,response_mode='summary')['structuredContent']
    assert d['total']==0 and d['items']==[] and not d['has_more'] and d['next_cursor'] is None
    assert call(client,'curated_bundle',response_mode='chunk')['isError']


@pytest.mark.parametrize('name',['curated_news','curated_watch','curated_maps'])
@pytest.mark.parametrize('lang',['zh','en'])
def test_real_public_views_keep_old_contract_and_precise_reading(client,name,lang):
    full=call(client,name,lang=lang);assert not full['isError']
    args={'lang':lang,'response_mode':'summary','page_size':1}
    summary=call(client,name,**args);assert not summary['isError']
    item=summary['structuredContent']['items'][0]
    ref=item['reading'];chunk=call(client,ref['tool'],**ref['arguments'])
    assert not chunk['isError']
    old_args={k:v for k,v in ref['arguments'].items() if k not in reading.CONTROLS}
    original=call(client,name,**old_args)['structuredContent']
    assert chunk['structuredContent']['content_hash']==hashlib.sha256(reading.encoded(original).encode()).hexdigest()
