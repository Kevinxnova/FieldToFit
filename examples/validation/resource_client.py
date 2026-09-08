"""Read a collected Skill through the official MCP SDK over HTTP and stdio.

Requires examples/validation/requirements.txt and a running Metis with Skill data.
No source code is executed and no generation/admin endpoint is called.
"""
import asyncio
import json
import os
import sys
from importlib.metadata import version
from pathlib import Path

from mcp.client.session import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client
from mcp.client.streamable_http import streamable_http_client
from mcp.shared._httpx_utils import create_mcp_http_client


async def check(transport):
    async with transport as streams:
        async with ClientSession(*streams) as session:
            initialized = await session.initialize()
            found = await session.call_tool('search', {'object_type':'skill','limit':100})
            assert not found.is_error and found.structured_content['items'], 'Collect a Skill before running this check'
            selected = next(r for r in found.structured_content['items'] if r['metadata'].get('capability_tags'))
            capability = selected['metadata']['capability_tags'][0]
            narrowed = await session.call_tool('search', {'object_type':'skill','capability':capability})
            assert not narrowed.is_error and all(capability in r['metadata']['capability_tags'] for r in narrowed.structured_content['items'])
            dossier = await session.call_tool('get_record', {'id':selected['id']})
            record = dossier.structured_content
            material = next(e for e in record['evidence'] if e['version']==record['version'])
            body = await session.call_tool('read_evidence', {'id':material['id'],'limit':2000})
            assert not body.is_error
            args = {'goal':selected['title'],'object_type':'skill','capability':capability}
            result = await session.call_tool('task_context', args)
            assert not result.is_error
            packet = result.structured_content
            assert packet['filters']=={'object_type':'skill','capability':capability}
            assert selected['id'] in [r['id'] for r in packet['candidates']]
            assert material['url'] in packet['markdown']
            assert record['version'] in record['metadata']['skill']['entrypoint']
            return {'protocol':initialized.protocol_version,'skills_found':found.structured_content['total'],
                    'selected_id':selected['id'],'version':record['version'],'capability':capability,
                    'source_url':material['url'],'read_evidence':True,'same_task_filters':True,'cited_markdown':True,
                    'scope':'Official SDK protocol flow; no Skill execution or autonomous desktop-client outcome is asserted.'}


async def main():
    url = os.getenv('METIS_MCP_URL','http://127.0.0.1:8000/api/mcp')
    headers = {'Authorization':'Bearer '+os.environ['METIS_READ_TOKEN']} if os.getenv('METIS_READ_TOKEN') else None
    async with create_mcp_http_client(headers=headers) as http_client:
        http = await check(streamable_http_client(url, http_client=http_client))
    env = {'METIS_MCP_URL':url}
    if os.getenv('METIS_READ_TOKEN'): env['METIS_READ_TOKEN']=os.environ['METIS_READ_TOKEN']
    stdio = await check(stdio_client(StdioServerParameters(command=sys.executable,args=['-m','backend.mcp_stdio'],
        env=env,cwd=str(Path(__file__).resolve().parents[2]))))
    report = {'client':'Official Python MCP SDK','client_version':version('mcp'),'http':http,'stdio':stdio}
    if len(sys.argv)>1: Path(sys.argv[1]).write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(report,ensure_ascii=False))


if __name__=='__main__':
    asyncio.run(main())
