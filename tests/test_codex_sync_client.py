"""A client must commit cache + cursor only after completing the whole read."""
import importlib.util
import json
from pathlib import Path
import httpx
import pytest

spec=importlib.util.spec_from_file_location('codex_sync',Path('scripts/maintenance/sync_codex_updates.py'))
sync_client=importlib.util.module_from_spec(spec);spec.loader.exec_module(sync_client)


def transport(pages):
    def handler(request):
        msg=json.loads(request.content)
        if msg['method']=='initialize':return httpx.Response(200,json={'result':{'protocolVersion':'2025-11-25'}})
        if msg['method']=='notifications/initialized':return httpx.Response(202)
        result=pages.pop(0)
        if isinstance(result,int):return httpx.Response(result)
        if 'isError' not in result:result={'isError':False,'structuredContent':result}
        return httpx.Response(200,json={'result':result})
    return httpx.Client(transport=httpx.MockTransport(handler))


def page(items, cursor='saved', more=False, mode='full'):
    return {'mode':mode,'items':items,'revision':'r1','topic_changed':False,'has_more':more,
            'next_cursor':cursor if more else None,'resume_cursor':None if more else cursor}


def added(ident):return {'object_id':ident,'kind':'added','item':{'id':ident,'title':'Public'}}


def test_client_full_empty_delta_and_expiry_removal(tmp_path):
    state=tmp_path/'state.json';url='https://example.org/api/mcp/codex'
    result=sync_client.sync(url,state,client=transport([page([added('D-78')],'next',True),page([added('D-79')])]))
    assert result['pages']==2 and len(result['changes'])==2
    assert json.loads(state.read_text())['cursor']=='saved'
    result=sync_client.sync(url,state,client=transport([page([],mode='delta')]))
    assert result['changes']==[] and result['cached']==2
    result=sync_client.sync(url,state,client=transport([{'isError':True,'structuredContent':{'code':'snapshot_expired'}},page([added('D-79')])]))
    assert result['cached']==1 and result['changes']==[{'object_id':'D-78','kind':'removed'}]
    assert state.stat().st_mode & 0o777 == 0o600


def test_client_midpage_failure_never_advances_or_replaces_cache(tmp_path):
    state=tmp_path/'state.json';url='https://example.org/api/mcp/codex'
    sync_client.sync(url,state,client=transport([page([added('D-78')])]))
    before=state.read_bytes()
    with pytest.raises(httpx.HTTPStatusError):
        sync_client.sync(url,state,client=transport([page([added('D-79')],'p2',True,'delta'),503]))
    assert state.read_bytes()==before
