#!/usr/bin/env python3
"""Build a review candidate from saved public HTML; never fetch or publish.

Usage: python scripts/maintenance/prepare_model_landscape.py --aa-html ...
       --arena-html ... --checked-at YYYY-MM-DD --output /tmp/candidate.json
Review the date ledger and candidate diff before replacing the published snapshot.
"""
import argparse
from datetime import date
import hashlib
from html.parser import HTMLParser
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
AA = 'https://artificialanalysis.ai/leaderboards/models'
ARENA = 'https://arena.ai/leaderboard/text'
COMPANIES = ['OpenAI', 'Anthropic', 'Google', 'xAI', 'Meta', 'Kimi', 'GLM', 'Qwen', 'MIMO', 'MiniMax', 'DeepSeek', '其他']


def company(name):
    return {'SpaceXAI':'xAI', 'xAI':'xAI', 'Z AI':'GLM', 'Z.ai':'GLM', 'Zhipu AI':'GLM', 'Alibaba':'Qwen', 'Xiaomi':'MIMO', 'Moonshot AI':'Kimi', 'Moonshot':'Kimi'}.get(name, name if name in COMPANIES else '其他')


class Scripts(HTMLParser):
    def __init__(self):
        super().__init__(); self.inside = False; self.body = ''; self.chunks = []
    def handle_starttag(self, tag, attrs):
        if tag == 'script': self.inside = True; self.body = ''
    def handle_data(self, data):
        if self.inside: self.body += data
    def handle_endtag(self, tag):
        if tag != 'script': return
        self.inside = False
        prefix = 'self.__next_f.push('
        if self.body.startswith(prefix):
            try:
                value = json.loads(self.body[len(prefix):].rstrip(';')[:-1])
                if len(value) > 1 and isinstance(value[1], str): self.chunks.append(value[1])
            except (ValueError, IndexError): pass


def objects(html):
    parser = Scripts(); parser.feed(html); roots = []
    for line in ''.join(parser.chunks).splitlines():
        try: roots.append(json.loads(line.partition(':')[2]))
        except ValueError: pass
    def walk(value):
        if isinstance(value, dict):
            yield value
            for child in value.values(): yield from walk(child)
        elif isinstance(value, list):
            for child in value: yield from walk(child)
    return list(walk(roots))


def number(value):
    return value if isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value) else None


def build(aa_html, arena_html, ledger, checked_at):
    checked = date.fromisoformat(checked_at)
    aa_objects = objects(aa_html); arena_objects = objects(arena_html)
    dates = {o['slug']:o for o in aa_objects if 'releaseDate' in o and 'slug' in o}
    models = {o['slug']:o for o in aa_objects if 'intelligenceIndex' in o and 'shortName' in o}
    boards = [o for o in arena_objects if o.get('leaderboardSlug') == 'overall' and o.get('params', {}).get('styleControl') is True and 'entries' in o]
    assert len(boards) == 1 and len(models) > 200, 'Source structure changed; review required'
    board = boards[0]
    aa = dict(id='artificial-analysis', name='Artificial Analysis', source_url=AA, source_updated_at=None, checked_at=checked_at,
              score_label='Intelligence Index v4.3', price_label='每项评测任务成本（美元）', price_label_en='USD per benchmark task', price_unit='usd_per_task',
              note='2026 年发布的模型配置；综合能力指数 × 每项评测任务加权成本。名称、配置与数值沿用来源，空心点为来源估计分。',
              note_en='Model configurations released in 2026: intelligence index × weighted cost per benchmark task. Original source names and values; hollow dots indicate estimated scores.')
    arena = dict(id='arena', name='Arena', source_url=ARENA, source_updated_at=board['voteCutoffISOString'][:10], checked_at=checked_at,
                 score_label='Text Arena · Overall · Style Control', price_label='输出价格（美元 / 百万 token）', price_label_en='USD per million output tokens', price_unit='usd_per_million_output_tokens',
                 note='2026 年模型 / 版本；用户偏好评分 × 输出 token 单价。竖线为来源评分区间，发布日期另行核对；评分不与 AA 换算。',
                 note_en='2026 models / versions: preference score × output token price. Vertical lines are source score intervals. Release dates are checked separately; scores are not converted to AA scores.')
    for source, raw in [(aa, models), (arena, board['entries'])]:
        source.update(points=[], not_plotted=[], undated=[], coverage={'source_models':len(raw), 'released_2026':0, 'outside_year':0})
    def add(source, p):
        day = p.get('release_date')
        if day is None:
            source['undated'].append(p); return
        assert date.fromisoformat(day) <= checked, 'Future release requires review'
        if not day.startswith('2026-'):
            source['coverage']['outside_year'] += 1; return
        source['coverage']['released_2026'] += 1
        reasons = []
        if p['score'] is None: reasons.append('missing_score')
        if p['price'] is None: reasons.append('missing_price')
        elif p['price'] <= 0: reasons.append('nonpositive_price')
        if reasons:
            p['missing'] = reasons; source['not_plotted'].append(p)
        else: source['points'].append(p)
    for slug, r in models.items():
        d = dates[slug]; cost = r.get('intelligenceIndexCostPerTask')
        price = number(cost.get('cost', {}).get('total')) if isinstance(cost, dict) else None
        estimated = r.get('intelligenceIndexIsEstimated') is True
        add(aa, dict(id=slug, name=r['shortName'], organization=company(r['modelCreatorName']), source_organization=r['modelCreatorName'],
                     score=number(r['intelligenceIndex']), price=price, score_url=AA, price_url=AA,
                     release_date=d['releaseDate'], date_basis='source_release_date', date_url='https://artificialanalysis.ai/models/'+slug,
                     configuration=d['name'] + (' · 来源估计分' if estimated else ''), configuration_en=d['name'] + (' · Source estimate' if estimated else ''),
                     estimated=estimated, deprecated=r.get('deprecated') is True))
    for r in board['entries']:
        evidence = ledger.get(r['modelKey'], {})
        add(arena, dict(id=r['modelKey'], name=r['modelDisplayName'], organization=company(r['modelOrganization']), source_organization=r['modelOrganization'],
                        score=number(r['rating']), score_low=number(r['ratingLower']), score_high=number(r['ratingUpper']),
                        price=number(r.get('outputPricePerMillion')), score_url=ARENA, price_url=ARENA,
                        release_date=evidence.get('release_date'), date_basis=evidence.get('date_basis'), date_url=evidence.get('date_url'),
                        model_url=r.get('modelUrl'), configuration='Text Overall · Style Control；'+str(r['votes'])+' 票；评分区间不代表名次差异显著。',
                        configuration_en='Text Overall · Style Control; '+str(r['votes'])+' votes; score intervals do not imply statistically distinct ranks.', votes=r['votes']))
    for source, html in [(aa, aa_html), (arena, arena_html)]:
        source['source_sha256'] = hashlib.sha256(html.encode()).hexdigest()
        source['points'].sort(key=lambda p:(-p['score'], p['name']))
        source['coverage'].update(plotted=len(source['points']), missing_coordinates=len(source['not_plotted']), unconfirmed_date=len(source['undated']))
        assert sum(source['coverage'][k] for k in ['released_2026', 'outside_year', 'unconfirmed_date']) == source['coverage']['source_models']
    return dict(schema_version='fieldtofit.model-landscape.v1', revision=checked_at+'.2', year=2026, interval_days=1, companies=COMPANIES, sources=[aa, arena])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--aa-html', type=Path, required=True); parser.add_argument('--arena-html', type=Path, required=True)
    parser.add_argument('--checked-at', required=True); parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    canonical = ROOT/'backend/knowledge/content/model-landscape.json'
    if args.output.resolve() == canonical.resolve(): parser.error('Write a candidate outside the published snapshot; review before publishing')
    ledger = json.loads((canonical.parent/'model-landscape-arena-dates.json').read_text())
    candidate = build(args.aa_html.read_text(), args.arena_html.read_text(), ledger, args.checked_at)
    args.output.write_text(json.dumps(candidate, ensure_ascii=False, indent=2, allow_nan=False)+'\n')
    print(json.dumps({s['id']:s['coverage'] for s in candidate['sources']}))


if __name__ == '__main__': main()
