"""Bind reviewed Chinese launch notes to an actual exported intake snapshot."""
import argparse
import json
from pathlib import Path


def prepare(intake, notes):
    mapping = {o['name']: o for o in notes['objects']}
    drafts, missing = [], []
    for job in intake['items']:
        note = mapping.get(job['name'])
        if not note:
            missing.append(job['name'])
            continue
        readme = next(m for m in job['materials'] if m['key'] == 'readme')
        for key in ('quote', 'limitation_quote'):
            if note.get(key) and note[key] not in readme['body']:
                raise ValueError(job['name'] + ': quotation no longer matches: ' + key)
        facts = {'capabilities': {'value': note['introduction'].split('。')[0] + '。',
                                 'material': 'readme', 'quote': note['quote']},
                 'limitations': {'status': 'unknown', 'value': None},
                 'cost': {'status': 'unknown', 'value': None}, 'hardware': {'status': 'unknown', 'value': None}}
        if note.get('limitation_quote'):
            facts['limitations'] = {'value': note['limitation'], 'material': 'readme', 'quote': note['limitation_quote']}
        drafts.append({'schema_version': intake['schema_version'], 'id': job['id'], 'fingerprint': job['fingerprint'],
            'base_token': job['base_token'], 'editor': 'FieldToFit · local Codex editorial review',
            'reason': '根据本次取得的官方原文整理，逐项核对引文；无来源的事实保持未知。',
            'introduction': note['introduction'], 'roles': [{'type': note.get('type', job['object_type']),
                'material': 'readme', 'quote': note['quote']}],
            'attention': [{'kind': 'editorial', 'explanation': note['reason'], 'observed_at': job['observed_at'],
                           'material': 'readme', 'quote': note['quote']}], 'facts': facts})
    return {'drafts': drafts, 'without_editorial_notes': missing}


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--intake', required=True)
    p.add_argument('--notes', required=True)
    p.add_argument('--output', required=True)
    a = p.parse_args()
    result = prepare(json.loads(Path(a.intake).read_text()), json.loads(Path(a.notes).read_text()))
    Path(a.output).write_text(json.dumps(result, ensure_ascii=False, indent=2))
    print(json.dumps({'drafts': len(result['drafts']), 'pending': result['without_editorial_notes']}, ensure_ascii=False))
