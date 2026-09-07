"""Check repository versions, Markdown links and frontend imports without network access."""
import ast
import json
from pathlib import Path
import re
import sys
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[2]


def run():
    errors = []
    tree = ast.parse((ROOT / 'backend/__init__.py').read_text())
    version = next(ast.literal_eval(n.value) for n in tree.body if isinstance(n, ast.Assign)
                   and any(isinstance(t, ast.Name) and t.id == '__version__' for t in n.targets))
    manifest = json.loads((ROOT / 'frontend/package.json').read_text())
    lock = json.loads((ROOT / 'frontend/package-lock.json').read_text())
    if {version, manifest['version'], lock['version'], lock['packages']['']['version']} != {version}:
        errors.append('Backend and frontend versions differ')
    for file in ['CHANGELOG.md', 'README.md', 'README.en.md', f'docs/releases/v{version}.md']:
        path = ROOT / file
        if not path.exists() or version not in path.read_text():
            errors.append('Version missing in ' + file)
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
    reqs = re.findall(r'<a id="([a-z]+-\d{2})"', (ROOT / 'docs/product/requirements.md').read_text())
    if len(reqs) != 42 or len(set(reqs)) != 42:
        errors.append('Current requirements must retain exactly 42 distinct REQ IDs')
    for error in errors:
        print(error, file=sys.stderr)
    print(json.dumps({'version': version, 'documents': len(documents), 'local_links': link_count,
                      'relative_imports': imports, 'requirements': len(reqs), 'errors': len(errors)}))
    return bool(errors)


if __name__ == '__main__':
    raise SystemExit(run())
