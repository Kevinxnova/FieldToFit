"""Maintain explicitly selected repositories, preserving commit-specific source material."""
import base64
import os
import re
from urllib.parse import quote

from backend.knowledge import store
from backend.knowledge.skills import discovery_tags, safe_path


def collect(source):
    from backend.knowledge.sources import fetch_json, PartialSourceError
    projects = source['config'].get('projects', [])
    if not isinstance(projects, list) or not 1 <= len(projects) <= 30:
        raise ValueError('Select 1–30 repositories')
    headers = {'Accept': 'application/vnd.github+json'}
    if os.getenv('GITHUB_TOKEN'):
        headers['Authorization'] = 'Bearer ' + os.environ['GITHUB_TOKEN']
    found = changed = 0; errors = []
    for project in projects:
        repo = project.get('repo', '') if isinstance(project, dict) else ''
        typ = project.get('type', '') if isinstance(project, dict) else ''
        if not re.fullmatch(r'[\w.-]+/[\w.-]+', repo) or typ not in {'agent', 'model', 'tool', 'library', 'application', 'project'}:
            raise ValueError('Each project needs a repository and a supported resource type')
        try:
            info = fetch_json(f'https://api.github.com/repos/{repo}', headers)
            commit = fetch_json(f'https://api.github.com/repos/{repo}/commits/{quote(info["default_branch"], safe="")}', headers)['sha']
            if not re.fullmatch(r'[a-f0-9]{40}', commit):
                raise ValueError('Missing immutable repository version')
            readme = fetch_json(f'https://api.github.com/repos/{repo}/readme?ref={commit}', headers)
            if not safe_path(readme.get('path')):
                raise ValueError('Invalid README path')
            if readme.get('encoding') != 'base64':
                raise ValueError('README content is unavailable')
            content = base64.b64decode(readme['content']).decode('utf-8')
            if not 40 <= len(content) <= 200000:
                raise ValueError('README must contain 40–200000 characters')
            description = info.get('description') or ''
            permalink = f'https://github.com/{repo}/blob/{commit}/{quote(readme["path"], safe="/")}'
            facts = {}
            if description:
                facts['capabilities'] = {'value': description, 'status': 'official_claim', 'source_url': f'https://github.com/{repo}',
                                         'version': commit, 'checked_at': store.now()}
            rid, did_change = store.save_discovery({'kind': 'resource', 'canonical_url': f'https://github.com/{repo}',
                'title': repo, 'summary': description, 'object_type': typ, 'version': commit,
                'source_id': source['id'], 'checked_at': store.now(), 'facts': facts,
                'topics': ['agents', 'engineering'] if typ == 'agent' else store.classify_topics(repo + ' ' + description),
                'metadata': {'repository': repo, 'resource_type_basis': 'maintainer_source_selection',
                             'document_url': f'https://raw.githubusercontent.com/{repo}/{commit}/{quote(readme["path"], safe="/")}',
                             'capability_tags': discovery_tags(description),
                             'capability_tag_basis': 'description_keywords_not_verification',
                             'source_version_url': f'https://github.com/{repo}/commit/{commit}',
                             'repository_archived': bool(info.get('archived')), 'repository_updated_at': info.get('pushed_at')}})
            store.add_evidence(rid, permalink, repo + ' / README', content, readme['path'], commit, 'documented', 'full_text')
            found += 1; changed += did_change
        except Exception as exc:
            errors.append(f'{repo}: {type(exc).__name__}: {str(exc)[:160]}')
    if errors:
        raise PartialSourceError(found, changed, '; '.join(errors)[:1000])
    return found, changed
