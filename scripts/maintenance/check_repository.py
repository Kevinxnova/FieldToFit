"""Check repository versions, Markdown links and frontend imports without network access."""
import json
from pathlib import Path
import re
import sys
from urllib.parse import unquote

import release_metadata

ROOT = Path(__file__).resolve().parents[2]


def run():
    errors = []
    version = release_metadata.read_version(ROOT)
    errors.extend(release_metadata.check(ROOT))
    if (ROOT / 'backend/requirements.txt').read_text().splitlines()[-1] != '-r ../requirements.txt':
        errors.append('Backend compatibility requirements must reference the root requirements')

    documents = list(ROOT.glob('*.md')) + list((ROOT / 'docs').rglob('*.md'))
    documents += list((ROOT / 'examples').rglob('*.md')) + list((ROOT / 'scripts').rglob('*.md'))
    documents += list((ROOT / 'frontend/src').rglob('*.md')) + list((ROOT / 'tests').glob('*.md'))
    link_count = 0
    for path in documents:
        content = re.sub(r'```.*?```', '', path.read_text(), flags=re.S)
        for match in re.finditer(r'\]\(([^\s)]+)\)', content):
            url = match[1].strip('<>')
            if re.match(r'[a-zA-Z][a-zA-Z0-9+.-]*:', url):
                continue
            name, _, anchor = url.partition('#')
            target = (path.parent / unquote(name)).resolve() if name else path
            link_count += 1
            if not target.exists():
                errors.append(f'{path.relative_to(ROOT)}: missing {url}')
                continue
            if anchor and target.suffix == '.md':
                text = target.read_text()
                anchors = set(re.findall(r'\bid=["\']([^"\']+)["\']', text))
                for heading in re.findall(r'^#{1,6}\s+(.+)$', text, re.M):
                    slug = re.sub(r'[^\w\-\s]', '', heading.lower()).replace(' ', '-')
                    anchors.add(slug)
                if unquote(anchor) not in anchors:
                    errors.append(f'{path.relative_to(ROOT)}: missing anchor {url}')

    imports = 0
    for path in list((ROOT / 'frontend/src').rglob('*.tsx')) + list((ROOT / 'frontend/src').rglob('*.ts')):
        for match in re.finditer(r'(?:from\s*|import\s*|import\s*\()\s*[\'"](\.[^\'"]+)[\'"]', path.read_text()):
            base = path.parent / match[1]
            possibilities = [base, Path(str(base) + '.ts'), Path(str(base) + '.tsx'), base / 'index.ts', base / 'index.tsx']
            imports += 1
            if not any(p.is_file() for p in possibilities):
                errors.append(f'{path.relative_to(ROOT)}: unresolved import {match[1]}')
    index = (ROOT / 'FieldToFit-PM.md').read_text()
    reqs = re.findall(r'^## (REQ-\d+) ·', index, re.M)
    subreqs = re.findall(r'<a id="(req-\d+-\d+)"', index)
    legacy = re.findall(r'<a id="legacy-([a-z]+-\d{2})"', index)
    old_children = re.findall(r'<a id="(req-[a-z]+-\d{2}\.\d{2})"', index)
    declared = re.search(r'(\d+) 项主 REQ、(\d+) 项子 REQ', index)
    if not declared or (len(reqs), len(subreqs)) != tuple(map(int, declared.groups())):
        errors.append('PM declared counts do not match the actual requirements')
    if len(reqs) != len(set(reqs)) or len(subreqs) != len(set(subreqs)):
        errors.append('PM requirement IDs must be unique')
    for req in reqs:
        if f'](#{req.lower()})' not in index.split('更新：', 1)[0]:
            errors.append('PM overview missing requirement: ' + req)
        if not any(child.startswith(req.lower() + '-') for child in subreqs):
            errors.append('PM requirement has no child: ' + req)
    for child in subreqs:
        if child.rsplit('-', 1)[0].upper() not in reqs:
            errors.append('Orphan PM child: ' + child)
    expected_old = set()
    for prefix, count in [('f', 5), ('y', 5), ('ai', 4), ('ab', 1), ('c', 1), ('o', 5), ('x', 1)]:
        for number in range(1, count + 1):
            children = 6 if (prefix, number) == ('o', 5) else 5 if (prefix, number) == ('y', 5) else 4
            expected_old.update(f'req-{prefix}-{number:02}.{child:02}' for child in range(1, children + 1))
    if set(old_children) != expected_old or len(old_children) != len(expected_old):
        errors.append('All 91 old child IDs must retain one mapping')
    for old in old_children:
        row = next((line for line in index.splitlines() if f'id="{old}"' in line), '')
        target = re.search(r'\]\(#(req-\d+-\d+)\)', row)
        if not target or target[1] not in subreqs:
            errors.append('Invalid old-to-new child mapping: ' + old)
    if len(legacy) != 42 or len(set(legacy)) != 42:
        errors.append('Retain all 42 Metis compatibility anchors')
    for line in index.splitlines():
        if not line.startswith('|') or not re.search(r'(?:\[REQ-\d+|id="req-\d+-\d+")', line):
            continue
        website = line.strip('|').split('|')[-1]
        if re.search(r'基础|部分已上线|主体已上线|未上线/待验', website):
            errors.append('PM website state must name concrete shipped and unshipped behavior')
    for duplicate in ['ROADMAP.md', 'docs/product/requirements.md', 'docs/product/requirements',
                      'docs/product/goals.md', 'docs/product/acceptance.md']:
        if (ROOT / duplicate).exists():
            errors.append('Duplicate project-management file: ' + duplicate)
    for error in errors:
        print(error, file=sys.stderr)
    print(json.dumps({'version': version, 'documents': len(documents), 'local_links': link_count,
                      'relative_imports': imports, 'requirements': len(reqs), 'subrequirements': len(subreqs), 'legacy_anchors': len(legacy), 'old_child_mappings': len(old_children), 'errors': len(errors)}))
    return bool(errors)


if __name__ == '__main__':
    raise SystemExit(run())
