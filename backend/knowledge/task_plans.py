"""Evidence-gated task plans. Design proposals are never promoted to source facts."""
import json
import re

from backend.knowledge import store

SPEC_FIELDS = {'inputs', 'outputs', 'success_criteria', 'input_kind'}
INPUT_KINDS = {'unknown', 'searchable_pdf', 'scanned_pdf', 'page_text'}
RECIPE_VERSION = '1'
PDF_VERSION = '6.17.0'
PDF_SOURCE = 'https://github.com/py-pdf/pypdf'
GUIDE = 'https://github.com/Kevinxnova/metis/blob/codex/metis-knowledge-workspace/examples/task_packets/pdf_amount.md'
CODE = 'https://github.com/Kevinxnova/metis/blob/codex/metis-knowledge-workspace/examples/task_packets/pdf_amount.py'


def brief(goal, background, spec=None):
    if spec is None:
        spec = {}
    if not isinstance(spec, dict) or set(spec) - SPEC_FIELDS:
        raise ValueError('Unsupported task specification')
    if any(not isinstance(v, str) or len(v) > 2000 for v in spec.values()):
        raise ValueError('Task specification fields must be text of at most 2000 characters')
    if spec.get('input_kind', 'unknown') not in INPUT_KINDS:
        raise ValueError('Unsupported input kind')
    text = '\n'.join((goal, background, spec.get('inputs', '')))
    # Narrow, visible hints; user can correct these with the explicit input kind.
    kind = spec.get('input_kind', 'unknown')
    if kind == 'unknown':
        if re.search(r'扫描|图片型|\bscanned?\b', text, re.I) and not re.search(r'非扫描|不是扫描|not scanned', text, re.I):
            kind = 'scanned_pdf'
        elif re.search(r'文本层|可搜索|searchable|text.layer', text, re.I):
            kind = 'searchable_pdf'
    novice = bool(re.search(r'零基础|初学|刚学|不会\s*Python|\bbeginner\b', background, re.I))
    missing = [key for key in ('inputs', 'outputs', 'success_criteria') if not spec.get(key, '').strip()]
    applied = []
    if background.strip():
        applied.append({'reason': '已有基础和环境参与条件识别；未能识别的自由文本保留待人工核对。', 'source': 'user_background'})
    if kind == 'scanned_pdf':
        applied.append({'reason': '输入为扫描件：先验证 OCR，不把纯文本提取案例当作完整解决方案。', 'source': 'input_kind'})
    if novice:
        applied.append({'reason': '已有基础为初学：优先从可运行样本起步，再替换为自己的文件。', 'source': 'user_background'})
    return {'goal': goal, 'inputs': spec.get('inputs', '').strip(), 'outputs': spec.get('outputs', '').strip(),
            'success_criteria': spec.get('success_criteria', '').strip(), 'input_kind': kind,
            'background': background, 'novice': novice, 'missing_fields': missing, 'applied_context': applied,
            'origin': 'User requirements and visible rule-based hints; not verified resource facts'}


def supported_fact(record, key):
    fact = record['facts'].get(key, {})
    return bool(fact.get('source_url') and fact.get('value') is not None and not fact.get('conflict')
                and fact.get('status') in {'documented', 'official_claim'}
                and record['version'] and fact.get('version') == record['version'])


def reference(record, key):
    fact = record['facts'][key]
    return {'record_id': record['id'], 'field': key, 'value': fact['value'], 'source_url': fact['source_url'],
            'version': fact['version'], 'status': fact['status'], 'evidence_id': fact.get('evidence_id')}


def pdf_recipe(task, records):
    text = '\n'.join((task['goal'], task['background'], task['inputs'], task['outputs']))
    if not re.search(r'pdf', text, re.I) or not re.search(r'金额|发票|invoice|amount', text, re.I):
        return None
    record = next((r for r in records if store.canonical_url(r['canonical_url']) == PDF_SOURCE), None)
    if not record:
        return None
    blockers = []
    if record['version'] != PDF_VERSION:
        blockers.append('案例要求 pypdf 6.17.0，当前资源版本不同，需重新核对和运行。')
    if task['input_kind'] == 'scanned_pdf':
        blockers.append('扫描件缺少文本层；此例不包含 OCR，不能完成当前输入任务。')
    if not supported_fact(record, 'usage'):
        blockers.append('当前版本的使用依据缺失或存在冲突，先补齐依据。')
    if any(m['state'] == 'unmet' for m in record.get('constraint_matches', [])):
        blockers.append('该资源有明确不满足的必需条件，不能作为当前任务的采用方案。')
    requirements = ['只接受有文本层、未加密的 PDF。', '金额行须为“发票金额：128.50 元”格式，仅 CNY；其他版式需另外验证。']
    checks = [v for v in record['verifications'] if v['method'] == 'Reviewed example execution'
              and v['steps'].startswith('Run pdf_amount_workflow.py engineer-pdf-amount;')]
    observation = max(checks, key=lambda v: v['checked_at']) if checks else None
    status = 'not_run'
    if observation:
        try:
            output = json.loads(observation['output'])
        except (ValueError, TypeError):
            output = {}
        if not isinstance(output, dict):
            output = {}
        if observation['result'] != 'passed':
            status = observation['result']
        elif observation['version'] != record['version'] or output.get('recipe_version') != RECIPE_VERSION:
            status = 'stale'
        else:
            status = observation['result']
    return {
        'id': 'pdf-amount', 'version': RECIPE_VERSION, 'title': '本地中文 PDF：提取金额并保留页码来源',
        'record_id': record['id'], 'resource_version': PDF_VERSION,
        'applicability': 'blocked' if blockers else 'review_input_format', 'blockers': blockers,
        'requirements': requirements, 'guide_url': GUIDE, 'code_url': CODE,
        'recommendation': '混合采用：复用 PDF 解析，自行实现页码包装和金额规则。' if not blockers else '先处理阻塞条件，再评估这个案例。',
        'success_criteria': [
            '两页样本输出 amount=128.50、currency=CNY、source_page=1，并附原文。',
            '缺失字段不填 0，多处金额不自动取第一项，无文本时要求 OCR 或检查。',
            '保留文件 SHA-256、逐页文本及 pypdf 版本，可回到输入核对。',
        ],
        'steps': [
            {'title': '准备独立环境', 'instruction': '使用 Python 3.12/3.13，安装固定版本依赖。', 'basis': 'example_design',
             'command': 'python3 -m venv /tmp/metis-pdf-env\n/tmp/metis-pdf-env/bin/pip install pypdf==6.17.0 reportlab==4.5.1', 'expected': '独立环境中依赖版本与案例一致。'},
            {'title': '先验证样本' if task['novice'] else '建立正例与边界基线', 'instruction': '在 Metis 仓库根目录执行随附代码，生成五组 PDF/JSON 文件。', 'basis': 'example_design',
             'command': '/tmp/metis-pdf-env/bin/python examples/task_packets/pdf_amount.py --demo-dir /tmp/metis-pdf-demo --output /tmp/metis-pdf-demo-result.json', 'expected': '七项 checks 为 true；正例金额和页码符合成功判据。'},
            {'title': '替换自己的输入', 'instruction': '先核对文本层与金额行格式，再将命令中的样本路径替换为自己的 PDF。', 'basis': 'example_design',
             'command': '/tmp/metis-pdf-env/bin/python examples/task_packets/pdf_amount.py --input /tmp/metis-pdf-demo/searchable.pdf --output /tmp/metis-pdf-amount.json', 'expected': '检查 status、原文、页码和金额；自己的输入结果需要单独验收。'},
        ],
        'facts': [reference(record, key) for key in ('usage', 'license', 'limitations') if supported_fact(record, key)],
        'verification': {'status': status, 'observation': observation,
                         'scope': '维护者运行的固定样本结果，不代表用户文件已运行，也不证明任意中文 PDF 或 OCR 支持。'},
    }


def plan(task, records, candidates):
    by_id = {r['id']: r for r in candidates}
    for record in records:
        record['constraint_matches'] = by_id[record['id']]['constraint_matches']
    usable = [r for r in records if not by_id[r['id']]['fit']['unmet'] and supported_fact(r, 'usage')]
    extendable = [r for r in usable if supported_fact(r, 'extension')]
    refs = [reference(r, 'usage') for r in usable]
    unresolved = [{'record_id': r['id'], **m} for r in candidates for m in r['constraint_matches'] if m['state'] != 'satisfied']
    target = task['outputs'] or task['goal']
    criterion = task['success_criteria'] or '先填写可检查的成功判据，再判断结果是否完成目标。'
    inputs = task['inputs'] or '待明确的输入材料'
    recipe = pdf_recipe(task, records)
    blocked_input = task['input_kind'] == 'scanned_pdf'
    paths = [
        {'path': 'use', 'title': '直接使用', 'record_ids': [r['id'] for r in usable], 'status': 'documented' if usable else 'blocked',
         'instruction': f'按下列版本对应的使用材料，把“{inputs}”交给现有工具，检查能否直接得到“{target}”。',
         'references': refs, 'check': criterion,
         'gaps': ['库的使用材料不代表完整目标已经完成；逐项核对未知条件。'] + ([] if usable else ['缺少符合已知条件、版本一致的使用材料。'])},
        {'path': 'extend', 'title': '基于开源扩展', 'record_ids': [r['id'] for r in extendable], 'status': 'documented' if extendable else 'needs_evidence',
         'instruction': f'从有依据的扩展入口修改最小一处，使现有结果满足“{target}”；保留原行为的检查。',
         'references': [reference(r, 'extension') for r in extendable], 'check': criterion,
         'gaps': [] if extendable else ['缺少上游扩展入口依据，不能指定内部文件或假设可以修改。']},
        {'path': 'build', 'title': '自行实现', 'record_ids': [], 'status': 'design_proposal',
         'instruction': f'把“{inputs}”到“{target}”定义为输入输出契约，先准备正例、缺失输入和歧义样本，再实现最小转换。',
         'references': [], 'check': criterion,
         'gaps': ['此路径是设计建议，尚无完整自研实现和运行结果。', *['任务定义缺少：' + k for k in task['missing_fields']]]},
        {'path': 'mixed', 'title': '混合采用', 'record_ids': [r['id'] for r in usable], 'status': 'design_proposal' if usable else 'blocked',
         'instruction': f'让有依据的现有组件处理它已支持的部分，自行实现到“{target}”所需的接口转换或业务规则，分别检查组件输出和最终结果。',
         'references': refs, 'check': criterion,
         'gaps': ['需明确每个组件的输入输出边界，并验证最终产物。'] + ([] if usable else ['尚无可复用组件的使用依据。'])},
    ]
    if recipe:
        for path in paths:
            path['example_url'] = CODE
            path['example_verification'] = recipe['verification']['status']
        paths[0]['instruction'] = '使用 PdfReader 和 page.extract_text() 获得逐页文本；金额识别仍需业务规则。'
        paths[0]['gaps'].append('单独使用 PDF 文本提取不能完成金额字段目标。')
        paths[1].update(instruction='在项目自己的 page_materials 包装层增加页码与文本接口；不修改上游内部源码。',
                        record_ids=[recipe['record_id']], references=recipe['facts'][:1], status='example_design',
                        gaps=['这是基于公开接口的项目扩展；未验证修改 pypdf 内部源码的路径。'])
        paths[2].update(instruction='自行编写 extract_amount：接受逐页文本，严格匹配金额行，缺失或歧义时返回明确状态。',
                        status='example_design', gaps=['仅实现业务字段规则；自行实现整个 PDF 解析器尚无可运行材料。'])
        paths[3].update(instruction=recipe['recommendation'], status='example_design', check='；'.join(recipe['success_criteria']),
                        gaps=recipe['requirements'] + ['还需在自己的文件上复验，并核实所有必需条件。'])
        if recipe['blockers']:
            for path in paths:
                path['status'] = 'blocked'
                path['gaps'] += recipe['blockers']
    return {'brief': task, 'paths': paths, 'recipe': recipe, 'unresolved_conditions': unresolved,
            'scope': 'Paths describe this candidate page. Source facts, design proposals and observed example results remain separate.',
            'next_steps': (['先确认 OCR 或文本来源；当前纯文本案例不适用于扫描输入。'] if blocked_input else [])
            + (['有可运行样本时，先运行样本，再替换自己的输入。'] if task['novice'] else [])
            + ['补齐输入、输出和成功判据中的空缺。', '核对采用路径引用的版本与未满足条件。',
               '对照成功判据检查产物，记录自己的环境、输入和实际结果。']}
