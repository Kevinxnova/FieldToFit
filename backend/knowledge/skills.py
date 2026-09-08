"""Index versioned Agent Skills as source material; never execute repository files."""
import base64
import os
from pathlib import PurePosixPath
import re
from urllib.parse import quote

import yaml

from backend.knowledge import store


def parse_skill(text):
    match = re.match(r'\A---\s*\n(.*?)\n---\s*(?:\n|\Z)', text, re.S)
    if not match or len(match[1]) > 16000:
        raise ValueError('SKILL.md requires bounded YAML frontmatter')
    try:
        metadata = yaml.safe_load(match[1])
    except yaml.YAMLError as exc:
        raise ValueError('Invalid skill frontmatter') from exc
    if not isinstance(metadata, dict):
        raise ValueError('Skill metadata must be an object')
    name, description = metadata.get('name'), metadata.get('description')
    if not isinstance(name, str) or not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', name) or len(name) > 64:
        raise ValueError('Invalid skill name')
    if not isinstance(description, str) or not 1 <= len(description.strip()) <= 1024:
        raise ValueError('Skill description must contain 1–1024 characters')
    result = {'name': name, 'description': description.strip()}
    for key in ('license', 'compatibility', 'allowed-tools'):
        value = metadata.get(key)
        if value is not None:
            if not isinstance(value, str) or len(value) > 4000:
                raise ValueError('Skill field must be bounded text: ' + key)
            result[key] = value.strip()
    return result


def safe_path(path):
    return (isinstance(path, str) and bool(path) and '\\' not in path
            and not PurePosixPath(path).is_absolute()
            and all(part not in ('..', '.') for part in path.split('/')))


def discovery_tags(description):
    patterns = {'document-processing': r'\b(pdf|document|docx|pptx|presentation)\b',
                'data-analysis': r'\b(data|spreadsheet|xlsx|csv|analytics)\b',
                'development': r'\b(code|coding|developer|testing|mcp|webapp)\b',
                'design': r'\b(design|visual|brand|art|canvas)\b',
                'writing': r'\b(writing|write|communication|author|content)\b'}
    return [name for name, pattern in patterns.items() if re.search(pattern, description, re.I)]


def collect(source):
    from backend.knowledge.sources import fetch_json, PartialSourceError
    config = source['config']
    repos = config.get('repos', [])
    limit = int(config.get('limit', 30))
    if not isinstance(repos, list) or not 1 <= len(repos) <= 10 or not 1 <= limit <= 100:
        raise ValueError('Configure 1–10 skill repositories and a limit of 1–100')
    headers = {'Accept': 'application/vnd.github+json'}
    if os.getenv('GITHUB_TOKEN'):
        headers['Authorization'] = 'Bearer ' + os.environ['GITHUB_TOKEN']
    found = changed = 0
    errors = []
    for repo in repos:
        if not isinstance(repo, str) or not re.fullmatch(r'[\w.-]+/[\w.-]+', repo):
            raise ValueError('Invalid skill repository')
        try:
            with store.get_db() as db:
                row = db.execute('SELECT state FROM knowledge_source_progress WHERE source_id=?', (source['id'],)).fetchone()
            progress = store.decode(row['state'], {}) if row else {}
            state = progress.get(repo, {})
            info = fetch_json(f'https://api.github.com/repos/{repo}', headers)
            branch = info['default_branch']
            commit = fetch_json(f'https://api.github.com/repos/{repo}/commits/{quote(branch, safe="")}', headers)['sha']
            if state.get('remaining', 0) > 0:
                commit = state['commit']
            if not re.fullmatch(r'[a-f0-9]{40}', commit):
                raise ValueError('Missing immutable repository version')
            tree = fetch_json(f'https://api.github.com/repos/{repo}/git/trees/{commit}?recursive=1', headers)
            if tree.get('truncated'):
                raise ValueError('Repository tree truncated; select a smaller source')
            files = [entry for entry in tree.get('tree', []) if entry.get('type') == 'blob'
                     and entry.get('mode') in ('100644', '100755') and safe_path(entry.get('path'))]
            entries = sorted((e for e in files if PurePosixPath(e['path']).name == 'SKILL.md'), key=lambda e: e['path'])
            # Persist a page cursor so a large repository is not permanently limited to its first skills.
            start = int(state.get('offset', 0)) if state.get('commit') == commit else 0
            batch = entries[start:start + limit]
            next_offset = start
            for entry in batch:
                try:
                    if entry.get('size', 0) > 200000:
                        raise ValueError('Skill instructions exceed 200 KB')
                    blob = fetch_json(f'https://api.github.com/repos/{repo}/git/blobs/{entry["sha"]}', headers)
                    if blob.get('encoding') != 'base64':
                        raise ValueError('Unsupported skill content encoding')
                    raw = base64.b64decode(blob['content'])
                    if len(raw) > 200000:
                        raise ValueError('Skill instructions exceed 200 KB')
                    text = raw.decode('utf-8')
                    metadata = parse_skill(text)
                    path = entry['path']
                    directory = str(PurePosixPath(path).parent)
                    if directory != '.' and PurePosixPath(directory).name != metadata['name']:
                        raise ValueError('Skill name does not match its directory')
                    prefix = '' if directory == '.' else directory + '/'
                    permalink = f'https://github.com/{repo}/blob/{commit}/{quote(path, safe="/")}'
                    raw_url = f'https://raw.githubusercontent.com/{repo}/{commit}/{quote(path, safe="/")}'
                    # HEAD is the stable identity; the actual material URL always pins a commit.
                    identity = f'https://github.com/{repo}/tree/HEAD/' + quote(directory if directory != '.' else '', safe='/')
                    references = [{'path': e['path'][len(prefix):],
                                   'url': f'https://github.com/{repo}/blob/{commit}/{quote(e["path"], safe="/")}',
                                   'sha': e['sha']} for e in files if e['path'].startswith(prefix) and e['path'] != path]
                    facts = {'capabilities': {'value': metadata['description'], 'source_url': permalink,
                                              'status': 'official_claim', 'version': commit, 'checked_at': store.now()}}
                    for field in ('license', 'compatibility', 'allowed-tools'):
                        if metadata.get(field):
                            facts[field.replace('-', '_')] = {'value': metadata[field], 'source_url': permalink,
                                                             'status': 'documented', 'version': commit, 'checked_at': store.now()}
                    record = {'kind': 'resource', 'title': repo + ' / ' + metadata['name'], 'canonical_url': identity,
                              'summary': metadata['description'], 'object_type': 'skill', 'version': commit,
                              'source_id': source['id'], 'checked_at': store.now(), 'topics': ['agents', 'engineering'],
                              'facts': facts, 'metadata': {'repository': repo, 'document_url': raw_url,
                                  'skill': {**metadata, 'path': directory, 'entrypoint': permalink,
                                            'files': references[:100], 'files_total': len(references),
                                            'files_truncated': len(references) > 100, 'execution': 'not_run'},
                                  'capability_tags': discovery_tags(metadata['description']),
                                  'capability_tag_basis': 'description_keywords_not_verification',
                                  'source_version_url': f'https://github.com/{repo}/commit/{commit}'}}
                    rid, did_change = store.save_discovery(record)
                    store.add_evidence(rid, permalink, metadata['name'] + ' / SKILL.md', text,
                                       path, commit, 'documented', 'full_text')
                    found += 1
                    changed += did_change
                except (ValueError, KeyError, UnicodeError) as exc:
                    errors.append(f'{repo}/{entry["path"]}: {exc}')
                next_offset += 1
            progress[repo] = {'commit': commit, 'offset': next_offset if next_offset < len(entries) else 0,
                              'total': len(entries), 'remaining': max(0, len(entries) - next_offset)}
            if next_offset < len(entries):
                errors.append(f'{repo}: {len(entries) - next_offset} skills remain in the pinned snapshot')
            with store.get_db() as db:
                db.execute('INSERT INTO knowledge_source_progress(source_id,state,updated_at) VALUES(?,?,?) '
                           'ON CONFLICT(source_id) DO UPDATE SET state=excluded.state,updated_at=excluded.updated_at',
                           (source['id'], store.encode(progress), store.now()))
        except Exception as exc:
            errors.append(f'{repo}: {type(exc).__name__}: {str(exc)[:160]}')
    if errors:
        raise PartialSourceError(found, changed, '; '.join(errors)[:1000])
    return found, changed
