"""Four task flows using the official Python MCP SDK 2.x (pip install mcp>=2,<3)."""
import asyncio,json,sys,os
from pathlib import Path
from importlib.metadata import version
from mcp.client.session import ClientSession
from mcp.client.streamable_http import streamable_http_client
from mcp.client.stdio import stdio_client,StdioServerParameters

async def check(transport):
 async with transport as streams:
  async with ClientSession(*streams) as session:
   init=await session.initialize(); tools=await session.list_tools()
   outcomes=[]
   for persona,goal in [('engineer','PDF'),('researcher','scikit-learn'),('graduate','scikit-learn'),('student','scikit-learn')]:
    called=await session.call_tool('task_context',{'goal':goal,'persona':persona})
    assert not called.is_error
    pack=called.structured_content
    assert pack['candidates'] and pack['deliverables']
    dossier=await session.call_tool('get_record',{'id':pack['candidates'][0]['id']})
    evidence=dossier.structured_content['evidence'][0]
    read=await session.call_tool('read_evidence',{'id':evidence['id'],'limit':1000})
    assert not read.is_error
    outcomes.append({'persona':persona,'goal':goal,'candidate_count':pack['total_candidates'],'record_id':pack['candidates'][0]['id'],'evidence_id':evidence['id'],'deliverables':pack['deliverables'],'conclusion':pack['conclusion']})
   reading=await session.call_tool('research_materials',{'goal':'scikit-learn','ids':['80bada030a39c91e2923059a']})
   assert not reading.is_error and '@misc' in reading.structured_content['bibtex']
   briefs=await session.call_tool('daily_briefs',{})
   assert not briefs.is_error
   return {'protocol':init.protocol_version,'tool_count':len(tools.tools),'tasks':outcomes,'research_export':True,'daily_briefs':True}
async def main():
 http=await check(streamable_http_client(os.getenv('METIS_MCP_URL','http://127.0.0.1:8000/api/mcp')))
 stdio=await check(stdio_client(StdioServerParameters(command=sys.executable,args=['-m','backend.mcp_stdio'],env={'METIS_MCP_URL':os.getenv('METIS_MCP_URL','http://127.0.0.1:8000/api/mcp')},cwd=str(Path(__file__).resolve().parents[2]))))
 report={'client':'Official Python MCP SDK','client_version':version('mcp'),'http':http,'stdio':stdio,'scope':'Protocol client acceptance; no end-user desktop client or autonomous agent outcome is asserted.'}
 if len(sys.argv)>1: Path(sys.argv[1]).write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps({'http':'passed','stdio':'passed','client_version':version('mcp')}))
asyncio.run(main())
