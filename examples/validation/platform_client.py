"""Read a real curated publication through HTTP and stdio with the official MCP SDK."""
import asyncio
import hashlib
import json
import os
import sys
from importlib.metadata import version
from pathlib import Path

from mcp.client.session import ClientSession
from mcp.client.streamable_http import streamable_http_client
from mcp.client.stdio import stdio_client, StdioServerParameters


async def check(transport):
    async with transport as streams:
        async with ClientSession(*streams) as session:
            await session.initialize()
            tools = await session.list_tools()
            async def call(name, args):
                result = await session.call_tool(name, args)
                if result.is_error:
                    raise ValueError(str(result.content))
                return result.structured_content
            result = await call('curated_search', {'q':'deepagents','object_type':'harness'})
            assert result['total'] == 1
            row = result['items'][0]
            obj = await call('curated_object', {'id':row['object']['id'],'revision':row['revision']})
            assert obj['object'] == row['object']
            source_state = await call('curated_sources', {})
            check = obj['source_check']
            assert any(x['id'] == check['id'] for x in source_state['items'])
            from datetime import datetime, timezone
            day = datetime.fromisoformat(obj['published_at'].replace('Z', '+00:00')).astimezone(timezone.utc).date().isoformat()
            filtered = await call('curated_search', {'source':check['id'], 'since':day, 'until':day})
            assert any(x['revision'] == obj['revision'] for x in filtered['items'])
            history = await call('curated_history', {'id':obj['object']['id'], 'revision':obj['revision'], 'limit':1})
            history_ids = []
            while True:
                history_ids.extend(event['id'] for event in history['items'])
                if not history['has_more']:
                    break
                continuation = history['continuation']
                history = await call(continuation['tool'], continuation['arguments'])
            assert history_ids == sorted(set(history_ids), reverse=True)
            assert max(history_ids) == obj['revision']
            report = []
            for material in obj['object']['materials']:
                position, chunks = 0, []
                while True:
                    part = await call('curated_material',{'id':obj['object']['id'],'revision':obj['revision'],
                        'material_id':material['id'],'offset':position,'limit':777})
                    chunks.append(part['body'])
                    if not part['has_more']:
                        break
                    position = part['next_offset']
                body = ''.join(chunks)
                assert len(body) == material['characters']
                assert hashlib.sha256(body.encode()).hexdigest() == material['content_hash']
                report.append({'material_id':material['id'],'source_url':material['source_url'],
                    'coverage':material['coverage'],'characters':len(body),'chunks':len(chunks),'hash_matches':True})
            exported = await call('curated_export',{'id':obj['object']['id'],'revision':obj['revision']})
            assert exported['object'] == obj['object'] and exported['requires_service_for_full_text']
            bundle = await call('curated_bundle', {'objects':[{'id':obj['object']['id'], 'revision':obj['revision']}]})
            assert [event['id'] for event in bundle['objects'][0]['history']['items']] == history_ids[:20]
            assert bundle['coverage']['all_stored_text_included']
            assert bundle['coverage']['included_characters'] == sum(m['characters'] for m in obj['object']['materials'])
            for material in bundle['objects'][0]['materials']:
                assert hashlib.sha256(material['body'].encode()).hexdigest() == material['content_hash']
            limited = await call('curated_bundle', {'objects':[{'id':obj['object']['id'], 'revision':obj['revision']}], 'max_characters':33})
            assert not limited['coverage']['all_stored_text_included']
            assert limited['coverage']['included_characters'] == 33
            continued = []
            for material in limited['objects'][0]['materials']:
                body = material['body']
                continuation = material['continuation']
                while continuation:
                    part = await call(continuation['tool'], continuation['arguments'])
                    body += part['body']
                    continuation = {'tool':'curated_material', 'arguments':{**continuation['arguments'], 'offset':part['next_offset']}} if part['has_more'] else None
                assert hashlib.sha256(body.encode()).hexdigest() == material['content_hash']
                continued.append(material['id'])
            markdown = await call('curated_bundle', {'objects':[{'id':obj['object']['id'], 'revision':obj['revision']}], 'format':'markdown'})
            assert markdown['coverage'] == bundle['coverage']
            assert all(m['body'] in markdown['markdown'] for m in bundle['objects'][0]['materials'])
            change_page = await call('curated_changes', {'object_ids':[obj['object']['id']], 'limit':1})
            window = change_page['snapshot']
            event_ids = []
            while True:
                assert change_page['snapshot'] == window
                event_ids.extend(event['id'] for event in change_page['items'])
                if not change_page['has_more']:
                    break
                change_page = await call('curated_changes', {'object_ids':[obj['object']['id']], 'limit':1, 'cursor':change_page['next_cursor']})
            assert len(event_ids) == len(set(event_ids))
            following = await call('curated_changes', {'object_ids':[obj['object']['id']], 'limit':1, 'cursor':change_page['resume_cursor']})
            assert not following['items']
            overview = await call('curated_editions', {'limit':5})
            editions = []
            for item in overview['items']:
                if item.get('unavailable'):
                    continue
                read = await call('curated_edition', {'id':item['id'], 'revision':item['revision']})
                assert read == item
                editions.append({'id':item['id'], 'revision':item['revision'], 'entries':len(item['entries'])})
            return {'public_history_event_ids':history_ids, 'bundle_history_matches':True, 'source_check':check, 'source_and_date_filter_matches':True, 'source_package':{'coverage':bundle['coverage'], 'all_body_hashes_match':True, 'limited_package_restored':continued, 'markdown_has_source_text':True}, 'change_window_event_ids':event_ids,'checkpoint_caught_up':True,'editions':editions,
                'tool_count':len(tools.tools),'object_id':obj['object']['id'],'revision':obj['revision'],
                'upstream_version':obj['object']['upstream_version'],'materials':report,'same_object_and_export':True,
                'no_task_plan_generated':True}


async def main():
    url=os.getenv('FIELDTOFIT_MCP_URL','http://127.0.0.1:18000/api/mcp')
    http=await check(streamable_http_client(url))
    stdio=await check(stdio_client(StdioServerParameters(command=sys.executable,args=['-m','backend.mcp_stdio'],
        env={'FIELDTOFIT_MCP_URL':url,'PYTHON_DOTENV_DISABLED':'1'},cwd=str(Path(__file__).resolve().parents[2]))))
    report={'client':'Official Python MCP SDK','client_version':version('mcp'),'http':http,'stdio':stdio,
        'scope':'Source reading and protocol acceptance only; not a desktop agent outcome or product showcase.'}
    if len(sys.argv)>1:
        Path(sys.argv[1]).write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'http':'passed','stdio':'passed','tool_count':http['tool_count'],'materials':len(http['materials'])}))


if __name__=='__main__':
    asyncio.run(main())
