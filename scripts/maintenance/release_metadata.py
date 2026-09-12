"""Synchronize release metadata from the backend version and bilingual changelog."""
import argparse
import ast
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[2]
SECTIONS = ['overview', 'release', 'ai', 'community', 'local', 'docs']


def read_version(root=ROOT):
    tree = ast.parse((root / 'backend/__init__.py').read_text())
    value = next(ast.literal_eval(n.value) for n in tree.body if isinstance(n, ast.Assign)
                 and any(isinstance(t, ast.Name) and t.id == '__version__' for t in n.targets))
    if not re.fullmatch(r'\d+\.\d+\.\d+', value):
        raise ValueError('Application version must use x.y.z')
    return value


def block(text, name):
    start, end = f'<!-- {name}:start -->', f'<!-- {name}:end -->'
    if text.count(start) != 1 or text.count(end) != 1:
        raise ValueError(f'Expected one {name} block')
    before, tail = text.split(start)
    if end not in tail:
        raise ValueError(f'Invalid {name} block order')
    body, after = tail.split(end)
    return before + start, body.strip(), end + after


def replace_block(text, name, value):
    before, _, after = block(text, name)
    return before + '\n' + value + '\n' + after


def latest_entry(root=ROOT):
    version = read_version(root)
    text = (root / 'CHANGELOG.md').read_text()
    parts = re.split(r'(?=^## v\d+\.\d+\.\d+ ·)', text, flags=re.M)
    if len(parts) < 2 or not parts[1].startswith(f'## v{version} ·'):
        raise ValueError('Latest CHANGELOG entry must match the application version')
    # A following anchor can remain at the end of the section; summaries are bounded.
    return parts[1]


def expected_updates(root=ROOT):
    version, entry = read_version(root), latest_entry(root)
    updates = {}
    for filename in ['frontend/package.json', 'frontend/package-lock.json']:
        path = root / filename
        data = json.loads(path.read_text())
        data['version'] = version
        if 'packages' in data:
            data['packages']['']['version'] = version
        updates[path] = json.dumps(data, indent=2, ensure_ascii=False) + '\n'
    for locale, filename in [('zh', 'README.md'), ('en', 'README.en.md')]:
        path = root / filename
        text = path.read_text()
        sections = re.findall(r'<!-- section:([a-z]+) -->', text)
        if sections != SECTIONS:
            raise ValueError(f'{filename}: bilingual README sections differ from the agreed structure')
        if len(re.findall(r'<!-- section:[a-z]+ -->\s*## [^\n]+', text)) != len(SECTIONS):
            raise ValueError(f'{filename}: each section marker must introduce its heading')
        if len(re.findall(r'^## ', text, flags=re.M)) != len(SECTIONS):
            raise ValueError(f'{filename}: every main section must have a section marker')
        summary = block(entry, f'release-summary:{locale}')[1]
        if not 3 <= len(re.findall(r'^- ', summary, flags=re.M)) <= 5:
            raise ValueError(f'Latest {locale} summary must contain 3–5 highlights')
        label = '当前源码版本' if locale == 'zh' else 'Current source version'
        tag = f'https://github.com/Kevinxnova/FieldToFit/tree/fieldtofit-v{version}'
        current = f'**{label}：[v{version}](CHANGELOG.md#v{version})** · [fieldtofit-v{version}]({tag})' if locale == 'zh' else f'**{label}: [v{version}](CHANGELOG.md#v{version})** · [fieldtofit-v{version}]({tag})'
        text = replace_block(text, 'current-version', current)
        text = replace_block(text, 'latest-summary', summary)
        updates[path] = text
    return updates


def check(root=ROOT):
    try:
        return [f'Release metadata out of sync: {p.relative_to(root)}'
                for p, expected in expected_updates(root).items() if p.read_text() != expected]
    except (ValueError, OSError, KeyError, StopIteration) as error:
        return [f'Release metadata: {error}']


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write', action='store_true', help='Update generated metadata; otherwise only check')
    args = parser.parse_args()
    if args.write:
        # Validate every source first, so a missing translation cannot cause partial writes.
        updates = expected_updates()
        for path, expected in updates.items():
            if path.read_text() != expected:
                path.write_text(expected)
                print('Updated', path.relative_to(ROOT))
    errors = check()
    for error in errors:
        print(error)
    if not errors:
        print('Release metadata consistent:', read_version())
    return bool(errors)


if __name__ == '__main__':
    raise SystemExit(main())
