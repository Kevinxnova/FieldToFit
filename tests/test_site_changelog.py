"""Release history must follow deployed artifacts without leaking draft prose."""
import json
from pathlib import Path
from scripts.maintenance import release_metadata as metadata
from test_knowledge import client
from test_release_metadata import release_tree


def test_projection_uses_only_explicit_copy_and_keeps_truthful_status(release_tree):
    path = release_tree / 'CHANGELOG.md'
    source = path.read_text()
    source = source.replace('<!-- public-details:zh:start -->', '<!-- private-scratch:DO-NOT-PUBLISH -->\n<!-- public-details:zh:start -->', 1)
    source += '\n## v99.0.0 · Future draft · 2099-01-01\n<!-- release-summary:zh:start -->\n- FUTURE\n<!-- release-summary:zh:end -->\n'
    path.write_text(source)
    data = json.loads(metadata.public_changelog(release_tree))
    assert 'DO-NOT-PUBLISH' not in json.dumps(data)
    assert all(item['version'] != '99.0.0' for item in data['items'])
    assert all(item['version'] != '1.8.24' for item in data['items'])
    assert data['items'][0]['version'] == metadata.read_version(release_tree)
    assert next(item for item in data['items'] if item['version'] == '1.8.30')['deployed_on'] == '2026-10-12'
    assert len({item['version'] for item in data['items']}) == len(data['items'])


def test_missing_translation_never_returns_chinese_summary(release_tree):
    path = release_tree / 'CHANGELOG.md'
    source = path.read_text().replace('public-summary:en:', 'unused-summary:en:', 2).replace('release-summary:en:', 'unused-release:en:', 2)
    path.write_text(source)
    copy = json.loads(metadata.public_changelog(release_tree))['items'][0]['copy']['en']
    assert copy['highlights'] == [] and not copy['translation_available']


def test_public_endpoint_version_locale_and_failure_boundaries(client, tmp_path, monkeypatch):
    from backend import site_changelog as history
    zh = client.get('/api/changelog')
    en = client.get('/api/changelog?lang=en')
    assert zh.status_code == en.status_code == 200
    assert zh.headers['Cache-Control'] == 'no-store'
    assert zh.json['version'] == client.get('/api/health').json['version'].removeprefix('v')
    assert zh.json['revision'] == en.json['revision']
    assert zh.json['items'][0]['status'] == 'current'
    assert en.json['items'][0]['title'] != zh.json['items'][0]['title']
    assert client.get('/api/changelog?metadata=1').json == {key: zh.json[key] for key in ('version', 'revision', 'language')}
    assert client.get('/api/changelog?lang=xx').status_code == 400
    bad = tmp_path / 'bad.json'
    data = json.loads(history.DATA.read_text()); data['version'] = '0.0.0'
    bad.write_text(json.dumps(data)); monkeypatch.setattr(history, 'DATA', bad)
    response = client.get('/api/changelog?lang=en')
    assert response.status_code == 503 and response.json == {'detail': 'Changelog temporarily unavailable'}
    bad.unlink()
    assert client.get('/api/changelog').status_code == 503


def test_bilingual_direct_pages_render_without_javascript(client, tmp_path, monkeypatch):
    import backend.api.main as main
    dist = tmp_path / 'dist'; dist.mkdir()
    (dist / 'index.html').write_text(Path('frontend/index.html').read_text())
    monkeypatch.setattr(main, 'CLIENT_DIST', dist)
    for language, path in [('zh', '/changelog'), ('en', '/en/changelog')]:
        data = client.get('/api/changelog?lang=' + language).json
        response = client.get(path, base_url='https://fieldtofit.top')
        assert response.status_code == 200
        assert 'id="v' + data['version'] + '"' in response.text
        assert data['items'][0]['title'] in response.text
        assert response.text.count('rel="canonical"') == 1
        assert 'https://fieldtofit.top' + path in response.text
        assert response.headers['Cache-Control'] == 'no-store'
    assert client.get('/en/changelog/', base_url='https://fieldtofit.top').status_code == 308
