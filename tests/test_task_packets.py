"""Task-level regressions: context changes decisions; evidence and outcomes stay scoped."""
import json
import runpy
from pathlib import Path

import pytest

from test_knowledge import client, seed
from backend.db import get_db
from backend.knowledge import tasks, store, verification

PDF = 'https://github.com/py-pdf/pypdf'
SPEC = {'inputs': '有文本层的中文 PDF', 'outputs': '金额与页码 JSON',
        'success_criteria': '128.50 CNY，第 1 页；歧义不猜测', 'input_kind': 'searchable_pdf'}


def pdf_record(**overrides):
    data = {'kind': 'resource', 'canonical_url': PDF, 'title': 'pypdf', 'summary': 'PDF text extraction',
            'version': '6.17.0', 'facts': {'usage': {'value': 'PdfReader(path); page.extract_text()',
                'source_url': 'https://pypdf.readthedocs.io/en/6.17.0/user/extract-text.html',
                'version': '6.17.0', 'status': 'documented'}}}
    data.update(overrides)
    return store.save_record(data)[0]


def test_background_changes_conditions_and_action_order(client):
    seed(version='v1', facts={'platform': {'value': 'linux', 'source_url': PDF,
         'status': 'documented', 'version': 'v1', 'exhaustive': True}})
    packet = tasks.pack('PDF 提取', background='Python 初学者，Windows，8GB 显存，已有扫描 PDF')
    assert packet['constraints']['platform'] == 'windows'
    assert packet['constraints']['hardware_vram_gb']['max'] == 8
    assert packet['candidates'][0]['fit']['unmet'] == 1
    assert packet['task_plan']['brief']['input_kind'] == 'scanned_pdf'
    assert 'OCR' in packet['next_steps'][0]
    assert '先运行' in packet['next_steps'][1]
    corrected = tasks.pack('PDF 提取', background='Windows，已有扫描 PDF', constraints={'platform': 'linux'}, task_spec=SPEC)
    assert corrected['constraints']['platform'] == 'linux'
    assert corrected['task_plan']['brief']['input_kind'] == 'searchable_pdf'


def test_evidence_conflicts_and_versions_do_not_become_adoption_instructions(client):
    rid = pdf_record()
    good = tasks.pack('PDF')
    assert good['paths'][0]['record_ids'] == [rid]
    for fact in ({'version': '6.16.0'}, {'conflict': True}):
        record = store.get_record(rid)
        record['facts']['usage'].update(fact)
        store.save_record(record, record_id=rid)
        packet = tasks.pack('PDF')
        assert not packet['paths'][0]['references']
        assert packet['paths'][0]['status'] == 'blocked'


def test_recipe_has_four_scoped_paths_and_does_not_claim_runtime_before_execution(client):
    pdf_record()
    packet = tasks.pack('本地 PDF 提取金额', task_spec=SPEC)
    recipe = packet['task_plan']['recipe']
    assert recipe['verification']['status'] == 'not_run'
    assert {p['path'] for p in packet['paths']} == {'use', 'extend', 'build', 'mixed'}
    assert '整个 PDF 解析器' in packet['paths'][2]['gaps'][0]
    assert packet['paths'][3]['status'] == 'example_design'
    assert any(c['condition'] == 'deployment' for c in packet['task_plan']['unresolved_conditions'])
    assert tasks.pack('PDF 合并文件')['task_plan']['recipe'] is None
    contextual = tasks.pack('提取金额', background='已有中文 PDF 文件', task_spec=SPEC)
    assert contextual['total_candidates'] == 1 and contextual['task_plan']['recipe']


def test_scanned_version_mismatch_and_hard_failures_block_recipe(client):
    rid = pdf_record()
    packet = tasks.pack('PDF 金额', background='扫描件')
    assert packet['task_plan']['recipe']['applicability'] == 'blocked'
    assert all(p['status'] == 'blocked' for p in packet['paths'])
    record = store.get_record(rid)
    record['facts']['deployment'] = {'value': 'local', 'version': '6.17.0', 'status': 'documented', 'source_url': PDF, 'exhaustive': True}
    store.save_record(record, record_id=rid)
    assert tasks.pack('PDF 金额', constraints={'deployment': 'cloud'})['task_plan']['recipe']['applicability'] == 'blocked'
    record['version'] = '6.18.0'
    store.save_record(record, record_id=rid)
    assert tasks.pack('PDF 金额')['task_plan']['recipe']['applicability'] == 'blocked'


def test_actual_recipe_files_and_independent_business_rule(tmp_path):
    workflow = runpy.run_path(str(Path(__file__).resolve().parents[1] / 'examples/task_packets/pdf_amount.py'))
    result = workflow['demo'](tmp_path)
    assert all(result['checks'].values())
    on_disk = json.loads((tmp_path / 'searchable.json').read_text())
    assert on_disk['field']['amount'] == '128.50' and on_disk['field']['source_page'] == 1
    assert len(on_disk['input_sha256']) == 64
    assert workflow['extract_amount']([{'page': 5, 'text': '发票金额：1,128.50 元'}])['field'] is None


def test_latest_observation_overrides_old_pass_and_export_carries_the_same_evidence(client, monkeypatch):
    rid = pdf_record()
    # Install-independent synthetic DB observations exercise recency/version handling; real script is tested separately.
    def observation(identifier, day, result, version='6.17.0', recipe_version='1'):
        with get_db() as db:
            db.execute('INSERT INTO knowledge_verifications VALUES(?,?,?,?,?,?,?,?,?,?,?,?)',
                (identifier, rid, 'PDF amount', 'Reviewed example execution', version, 'test fixture',
                 'Run pdf_amount_workflow.py engineer-pdf-amount; source '+PDF, 'expected amount', result,
                 json.dumps({'recipe_version': recipe_version}), 'synthetic test observation', day))
    observation('older', '2026-09-01T00:00:00Z', 'passed')
    observation('newer', '2026-09-02T00:00:00Z', 'failed')
    response = client.post('/api/v1/task', json={'goal': 'PDF 金额', 'task_spec': SPEC}).json
    assert response['task_plan']['recipe']['verification']['status'] == 'failed'
    assert 'expected amount' in response['markdown'] and 'synthetic test observation' in response['markdown']
    assert SPEC['outputs'] in response['markdown'] and 'source_page=1' in response['markdown']
    observation('stale', '2026-09-03T00:00:00Z', 'passed', recipe_version='0')
    assert tasks.pack('PDF 金额')['task_plan']['recipe']['verification']['status'] == 'stale'
    exported = client.post('/api/v1/task/export', json={'goal': 'PDF 金额', 'task_spec': SPEC}).text
    assert '状态：stale' in exported and '混合采用' in exported


def test_mcp_accepts_task_contract_and_invalid_spec_is_rejected(client):
    pdf_record()
    from backend.knowledge.mcp import invoke
    packet = invoke('task_context', {'goal': 'PDF 金额', 'task_spec': SPEC})
    assert packet['task_plan']['brief']['outputs'] == SPEC['outputs']
    for invalid in ({'input_kind': 'whatever'}, {'inputs': []}, {'unknown': 'x'}):
        response = client.post('/api/v1/task', json={'goal': 'PDF 金额', 'task_spec': invalid})
        assert response.status_code == 400
