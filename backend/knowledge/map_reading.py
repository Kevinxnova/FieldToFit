"""Optional reviewed report reading. Text only; never HTML or generated runtime prose."""
import re
import json
from pathlib import Path


def validate(value, node_ids, report_ids, sources, words, evidence):
    if not isinstance(value, dict): raise ValueError('报告阅读须为对象')
    findings = value.get('findings')
    if not isinstance(findings, list) or not 1 <= len(findings) <= 8:
        raise ValueError('报告须有1至8个核心结论')
    out = {'title': words(value, 'title', 300), 'findings': []}
    ids = set()
    for finding in findings:
        if not isinstance(finding, dict): raise ValueError('核心结论须为对象')
        ident = words(finding, 'id', 80)
        if not re.fullmatch(r'[a-z][a-z0-9-]*', ident) or ident in ids:
            raise ValueError('结论编号无效或重复')
        ids.add(ident)
        nodes = finding.get('node_ids')
        if not isinstance(nodes, list) or not nodes or any(n not in node_ids for n in nodes) or len(set(nodes)) != len(nodes):
            raise ValueError('核心结论须关联已有地图节点')
        points = evidence(finding)
        if not any(p['source_id'] in report_ids for p in points): raise ValueError('结论须有原始报告依据')
        blocks = finding.get('blocks')
        if not isinstance(blocks, list) or not 1 <= len(blocks) <= 20: raise ValueError('每个结论须有展开论述')
        entry = {'id': ident, 'title': words(finding, 'title', 300), 'summary': words(finding, 'summary'),
                 'node_ids': nodes, 'evidence': points, 'blocks': []}
        for block in blocks:
            if not isinstance(block, dict): raise ValueError('论述块须为对象')
            kind = block.get('kind'); result = {'kind': kind}
            if kind in ('paragraph', 'highlight'):
                result['text'] = words(block, 'text', 4000)
                if kind == 'highlight':
                    if block.get('label') not in ('claim', 'evidence', 'limit'): raise ValueError('高亮须区分作者结论、关键证据和适用边界')
                    result['label'] = block['label']
            elif kind == 'points':
                items = block.get('items')
                if not isinstance(items, list) or not 2 <= len(items) <= 10: raise ValueError('分点论述须有2至10项')
                result['items'] = [words({'text': s}, 'text', 3000) for s in items]
            elif kind == 'figure':
                # Static, reviewed assets travel with the release; no arbitrary fetches or SVG/HTML.
                url = words(block, 'image_url', 300)
                if not re.fullmatch(r'/report-figures/[a-z0-9-]+\.png', url): raise ValueError('原图须使用已核对的报告PNG资源')
                points = evidence(block)
                if any(p['source_id'] not in report_ids for p in points): raise ValueError('原图须引用已登记原始报告')
                manifest = json.loads((Path(__file__).parent/'content'/'report-figures.json').read_text())
                asset = manifest.get(url)
                if not asset or block.get('license') != asset['license'] or any(sources[p['source_id']]['url'].split('#')[0] not in asset['source_urls'] for p in points):
                    raise ValueError('原图资源、许可和来源须与已核对清单一致')
                result.update(image_url=url, evidence=points)
                for key in ('alt', 'caption', 'attribution', 'license'):
                    result[key] = words(block, key, 2000)
            else: raise ValueError('论述块类型不支持')
            entry['blocks'].append(result)
        out['findings'].append(entry)
    editorial = value.get('editorial', [])
    if not isinstance(editorial, list) or len(editorial) > 8: raise ValueError('编辑判断须为文本列表')
    out['editorial'] = [words({'text': s}, 'text', 3000) for s in editorial]
    return out
