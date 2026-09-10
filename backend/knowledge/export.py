"""Portable dossiers retain evidence, dates and uncertainty."""
import re


def markdown(record):
    lines = [f"# {record.get('title_zh') or record['title']}", "", record.get('summary_zh') or record['summary'], "",
             f"- Stable ID: {record['id']}", f"- Type: {record['kind']} / {record['object_type']}",
             f"- Version: {record['version'] or 'Unknown'}", f"- Published: {record['published_at'] or 'Unknown'}",
             f"- Last checked: {record['checked_at'] or 'Not checked'}", f"- Source: {record['canonical_url']}",
             f"- Material completeness: {record['completeness']}", "", "## Facts and conditions", ""]
    for key, fact in record['facts'].items():
        lines += [f"### {key}", str(fact.get('value', 'Unknown')), "",
                  f"Evidence: {fact.get('status', 'unknown')} · {fact.get('source_url', '')}", ""]
    if not record['facts']:
        lines += ["Detailed capabilities and conditions have not been verified.", ""]
    editorial=record.get('metadata',{}).get('editorial',{})
    if editorial:
        lines += ['## AI-organized reading',f"Generator: {editorial.get('model','Unknown')}; generated: {editorial.get('generated_at','Unknown')}",'']
        for key,value in editorial.get('human',{}).get('zh',{}).items():
            lines += ['### '+key,str(value),'']
        for key,value in editorial.get('research',{}).items():
            if isinstance(value,str) and value: lines += ['### '+key,value,'']
        for citation in editorial.get('citations',[]):
            lines += [f"- Evidence: {citation['source_url']} · {citation.get('locator','')} · version {citation.get('version') or 'Unknown'}"]
    for conflict in record.get('conflicts',[]):
        lines += ['', 'Conflicting evidence: '+conflict['field']]
        for alternative in conflict['alternatives']:
            lines += [f"- {alternative.get('value')} · {alternative.get('source_url')}"]
    lines += ["## Source materials", ""]
    for e in record.get('evidence', []):
        lines += [f"- {e['title']} — {e['url']}", f"  Coverage: {e['coverage']}; version: {e['version'] or 'unknown'}; location: {e['locator']}"]
    lines += ["", "## Verification records", ""]
    for v in record.get('verifications', []):
        lines += [f"- {v['title']}: {v['result']} ({v['checked_at']})", f"  Environment: {v['environment']}", f"  Limitations: {v['limitations']}"]
    if not record.get('verifications'):
        lines += ["No FieldToFit runtime verification has been recorded."]
    return '\n'.join(lines) + '\n'


def bibtex(record):
    def clean(value):
        return str(value).replace('\\', '').replace('{', '').replace('}', '').replace('\n', ' ')
    authors = record.get('facts', {}).get('authors', {}).get('value') or record.get('metadata', {}).get('authors', [])
    fields = {'title': record['title'], 'url': record['canonical_url']}
    if authors:
        fields['author'] = ' and '.join(authors) if isinstance(authors, list) else authors
    if record.get('published_at'):
        fields['year'] = record['published_at'][:4]
    elif record.get('metadata',{}).get('publication_year'):
        fields['year'] = record['metadata']['publication_year']
    doi = record.get('facts', {}).get('doi', {}).get('value')
    if doi:
        fields['doi'] = doi
    fields['note'] = 'FieldToFit source record; publication and review status must be checked in the source'
    key = re.sub(r'[^a-zA-Z0-9]', '', record['id'])
    return '@misc{fieldtofit' + key + ',\n' + ',\n'.join(f'  {k} = {{{clean(v)}}}' for k, v in fields.items()) + '\n}\n'
