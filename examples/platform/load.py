"""Load the captured official-source dossier into an explicitly chosen local preview.

No model/network calls and no environment-file loading. Creates a draft by default.
--publish performs the explicit reviewed publication used in acceptance checks.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path


def run(data_dir, publish=False):
    # This loader is intentionally unable to select a production database from .env.
    os.environ.update(PYTHON_DOTENV_DISABLED='1', TURSO_DATABASE_URL='', TURSO_AUTH_TOKEN='', METIS_DATA_DIR=str(Path(data_dir).resolve()))
    from backend.db import init_db
    from backend.knowledge import store, platform
    init_db()
    root = Path(__file__).parent
    capture = json.loads((root / 'capture.json').read_text())
    content = (root / 'deepagents-readme.txt').read_text()
    license = (root / 'deepagents-license.txt').read_text()
    if hashlib.sha256(content.encode()).hexdigest() != capture['sha256'] or hashlib.sha256(license.encode()).hexdigest() != capture['license_sha256']:
        raise ValueError('Captured source hash mismatch')
    rid = store.stable_id('resource', capture['repository'])
    if store.get_record(rid, include_withdrawn=True):
        return {'id':rid, 'status':'already_exists', 'note':'Existing corrections and publication preserved'}
    role_quote = 'Deep Agents is an open source agent harness'
    capabilities_quote = '**Skills** — reusable behaviors the agent can load on demand'
    limitation_quote = 'The agent can do anything its tools allow.'
    rid, _ = store.save_record({'canonical_url':capture['repository'], 'kind':'resource','title':'Deep Agents',
        'summary':'An open source agent harness.', 'summary_zh':'提供文件系统、子 Agent、上下文管理与 Skill 支持的开源 Agent Harness。',
        'object_type':'harness', 'topics':[], 'version':'', 'source_id':'manual', 'checked_at':capture['captured_at'],
        'metadata':{'source_capture':capture, 'editorial_override':True},
        'facts':{
            'capabilities':{'value':'作者说明包含文件系统、子 Agent、上下文管理和可按需加载的 Skills。','status':'official_claim',
                'source_url':capture['readme_url'],'quote':capabilities_quote},
            'limitations':{'value':'作者说明权限边界由工具和沙箱约束；不能依赖模型自行限制权限。','status':'official_claim',
                'source_url':capture['readme_url'],'quote':limitation_quote},
            'hardware':{'value':None,'status':'unknown'},
            'cost':{'value':None,'status':'unknown'},
        }},'Official README snapshot for platform material acceptance')
    eid = store.add_evidence(rid,capture['readme_url'],'Deep Agents · official README',content,'README.md',evidence_type='documented',coverage='full_text')
    lid = store.add_evidence(rid,capture['license_url'],'Deep Agents · MIT License',license,'LICENSE',evidence_type='documented',coverage='full_text')
    docs = store.add_evidence(rid,'https://docs.langchain.com/oss/python/deepagents/overview','Deep Agents documentation',coverage='link_only')
    profile = {'introduction':'Deep Agents 是 LangChain 提供的开源 Agent Harness。官方 README 介绍了文件系统、子 Agent、上下文管理和 Skill 等组成部分；模型和工具权限边界需要按作者文档进一步核对。',
        'aliases':['deepagents'], 'roles':[{'type':'harness','evidence_id':eid,'quote':role_quote}],
        'attention':[{'kind':'editorial','explanation':'编辑选择：作者提供了明确的 Harness 定义、组成能力和权限限制，适合持续维护完整资料。这不是热度排名或实测结论。',
            'evidence_id':eid,'quote':role_quote,'observed_at':capture['captured_at']}],
        'materials':[
            {'evidence_id':eid,'kind':'readme','primary':True,'note':'只保存此 README 文本；外链文档、图片和完整代码未全部采集。提交版本未取得，按内容哈希追溯。'},
            {'evidence_id':lid,'kind':'license','primary':False,'note':'单独获取的许可证文本；保留上游署名。'},
            {'evidence_id':docs,'kind':'documentation','primary':False,'note':'仅保存官方入口，未获取文档正文。'},
        ]}
    draft = platform.save_profile(rid,profile,0,'Source-linked editorial draft; upstream version explicitly unknown')
    if publish:
        draft = platform.transition(rid,'review',draft['review_token'],'Review original quotes and coverage')
        draft = platform.transition(rid,'published',draft['review_token'],'Captured official README and license checked; unknowns and link-only docs disclosed')
    return {'id':rid,'selection':draft['selection'],'gate':draft['gate'],'material_ids':[eid,lid,docs],'source_capture':capture}


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data-dir',required=True,help='Explicit local preview data directory')
    parser.add_argument('--publish',action='store_true',help='Publish this reviewed fixture in the selected preview')
    args=parser.parse_args()
    print(json.dumps(run(args.data_dir,args.publish),ensure_ascii=False,indent=2))
