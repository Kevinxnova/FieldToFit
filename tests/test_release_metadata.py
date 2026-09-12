"""Release checks must reject stale or incomplete bilingual metadata."""
import shutil
import pytest
from scripts.maintenance import release_metadata as metadata


@pytest.fixture
def release_tree(tmp_path):
    for name in ['backend/__init__.py', 'frontend/package.json', 'frontend/package-lock.json',
                 'CHANGELOG.md', 'README.md', 'README.en.md']:
        target = tmp_path / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(metadata.ROOT / name, target)
    return tmp_path


def test_current_metadata_is_synchronized(release_tree):
    assert metadata.check(release_tree) == []


@pytest.mark.parametrize('filename,old,new', [
    ('README.en.md', 'Current source version:', 'Old source version:'),
    ('README.md', metadata.block(metadata.latest_entry(), 'release-summary:zh')[1], '- 旧版摘要'),
    ('frontend/package-lock.json', f'"version": "{metadata.read_version()}"', '"version": "0.0.0"'),
])
def test_stale_generated_content_is_rejected(release_tree, filename, old, new):
    path = release_tree / filename
    original = path.read_text()
    assert old in original
    path.write_text(original.replace(old, new, 1))
    assert any(filename in error for error in metadata.check(release_tree))
    for target, content in metadata.expected_updates(release_tree).items():
        target.write_text(content)
    assert metadata.check(release_tree) == []


def test_old_version_mention_cannot_satisfy_latest_check(release_tree):
    path = release_tree / 'CHANGELOG.md'
    path.write_text(path.read_text().replace(f'## v{metadata.read_version()} ·', '## v0.0.0 ·', 1))
    assert 'Latest CHANGELOG entry' in metadata.check(release_tree)[0]


def test_missing_english_summary_rejected_before_sync(release_tree):
    path = release_tree / 'CHANGELOG.md'
    path.write_text(path.read_text().replace('release-summary:en:start', 'translation-missing', 1))
    with pytest.raises(ValueError, match='release-summary:en'):
        metadata.expected_updates(release_tree)


def test_bilingual_section_drift_rejected(release_tree):
    path = release_tree / 'README.en.md'
    path.write_text(path.read_text().replace('<!-- section:community -->', '', 1))
    assert 'bilingual README sections' in metadata.check(release_tree)[0]
