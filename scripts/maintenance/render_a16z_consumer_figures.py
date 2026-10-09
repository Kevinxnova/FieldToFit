"""Render the owner-aligned October 5 report figures from public statistics.

Requires Pillow and a Chinese font, supplied with --font on other systems.
These are FieldToFit graphics, not captures of a16z artwork or raw-panel analysis.
"""
import argparse
import hashlib
import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[2]
SOURCE = 'https://a16z.com/100-gen-ai-apps-7/'
RIGHTS = '图形 © FieldToFit；原始数据归属见来源'


def render(font):
    bg, ink, muted, blue, teal = '#f7f8fc', '#172641', '#536178', '#375ad2', '#147c78'
    fonts = {s: ImageFont.truetype(font, s) for s in (23, 26, 29, 32, 36, 43, 56, 70)}
    target = ROOT/'frontend/public/report-figures'
    manifest_path = ROOT/'backend/knowledge/content/report-figures.json'
    manifest = json.loads(manifest_path.read_text())

    def page(number, title, subtitle, source_line=None):
        im = Image.new('RGB', (1500, 850), bg)
        d = ImageDraw.Draw(im)
        d.rounded_rectangle((60, 47, 230, 87), 12, fill=ink)
        d.text((78, 54), f'REPORT / 0{number}', font=fonts[23], fill='white')
        d.text((60, 117), title, font=fonts[43], fill=ink)
        d.text((60, 187), subtitle, font=fonts[26], fill=muted)
        d.line((60, 733, 1440, 733), fill='#d7ddea', width=2)
        d.text((60, 756), source_line or '来源：a16z 第7版（2026-10-05） / YipitData 美国面板', font=fonts[23], fill=muted)
        d.text((60, 794), 'FieldToFit 本站重绘 / a16z.com/100-gen-ai-apps-7/ / 非报告原图', font=fonts[23], fill=muted)
        return im, d

    def save(im, name, statistics):
        path = target/f'a16z-20261005-{name}.png'
        im.save(path, optimize=True)
        manifest['/report-figures/'+path.name] = {
            'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
            'source_urls': [SOURCE], 'license': RIGHTS,
            'version': 'a16z 第7版 · 2026-10-05',
            'origin': 'fieldtofit-redraw', 'statistics': statistics,
        }

    im, d = page(1, '个人付费订阅：覆盖上升，仍只是一小部分', '美国电子收据面板合格消费者；至少订阅 ChatGPT / Gemini / Claude 之一')
    left, right, bottom, top = 250, 1270, 620, 285
    for n in range(6):
        y = bottom-n/5*(bottom-top)
        d.line((left, y, right, y), fill='#dce2ed', width=2)
        d.text((175, y-17), f'{n}%', font=fonts[26], fill=muted)
    for x, val, label, color in [(475, 2.1, '2025年8月', '#a1b3e7'), (1035, 4.5, '2026年8月', blue)]:
        y = bottom-val/5*(bottom-top)
        d.rounded_rectangle((x-105, y, x+105, bottom), radius=9, fill=color)
        d.text((x, y-58), f'{val}%', font=fonts[43], fill=ink, anchor='mt')
        d.text((x, 643), label, font=fonts[29], fill=ink, anchor='mt')
    d.text((60, 695), '口径：三款产品的个人付费订阅覆盖；不是全部 AI 的使用率，也不含雇主代付。', font=fonts[23], fill=muted)
    save(im, 'personal-paid', {'2025-08': 2.1, '2026-08': 4.5, 'unit': '% eligible consumers', 'cohort': 'US e-receipt panel; personal ChatGPT/Gemini/Claude subscription'})

    im, d = page(2, '谁贡献了消费？两组用户，人数差距很大', '按付费者消费额排序；比较各组贡献的“已观测 AI 消费份额”')
    x0, x1 = 390, 1270
    for n in range(0, 26, 5):
        x = x0+n/25*(x1-x0)
        d.line((x, 290, x, 555), fill='#dce2ed', width=2)
        d.text((x, 576), f'{n}%', font=fonts[26], fill=muted, anchor='mt')
    for y, val, label, color in [(310, 19.5, '消费额最高的 1%', blue), (460, 16.6, '消费额最低的 50%', teal)]:
        d.text((60, y+27), label, font=fonts[29], fill=ink)
        end = x0+val/25*(x1-x0)
        d.rounded_rectangle((x0, y, end, y+85), radius=9, fill=color)
        d.text((end+20, y+17), f'{val}%', font=fonts[43], fill=ink)
    d.text((60, 652), '两条柱的横轴相同，代表消费贡献；不是两组人数相同，也不是人均支出。', font=fonts[26], fill=ink)
    d.text((60, 697), '边界：2026年8月美国面板观测；消费者卡支付可能用于工作；不是公司总营收。', font=fonts[23], fill=muted)
    save(im, 'spend-concentration', {'top_1_percent_payers_spend_share': 19.5, 'bottom_50_percent_payers_spend_share': 16.6, 'unit': '% observed consumer AI spend', 'period': '2026-08', 'cohort': 'US consumer panel'})

    im, d = page(3, '50 家付费榜头部，29 家不在两份流量榜上', '以报告的消费额 Top 50 为母集；下图每格代表 1 家供应商')
    for i in range(50):
        x, y = 85+(i%10)*135, 290+(i//10)*62
        d.rounded_rectangle((x, y, x+115, y+43), 8, fill=blue if i<29 else '#bdc8df')
    d.rounded_rectangle((80, 634, 112, 666), 6, fill=blue)
    d.text((135, 630), '29 家：两份流量榜均未入榜', font=fonts[29], fill=ink)
    d.rounded_rectangle((775, 634, 807, 666), 6, fill='#bdc8df')
    d.text((830, 630), '21 家：至少入一榜（50 − 29）', font=fonts[29], fill=ink)
    d.text((60, 696), '月访问量 ≠ 手机月活 ≠ 美国卡支付；不同样本和单位，不能直接换算。', font=fonts[23], fill=muted)
    save(im, 'ranking-gap', {'spend_top_50_absent_from_both_traffic_lists': 29, 'spend_top_50_in_at_least_one_traffic_list': 21, 'unit': 'vendors', 'derived': '21 = 50 - 29; cell positions carry no rank information'})

    im, d = page(4, '“买了什么”与“下一步可能怎样”分开读', '本站阅读示意；类别与例子不表示任务占比、频率或收益', '来源：a16z 第7版（2026-10-05）第2节观察 / 第5节作者判断')
    d.rounded_rectangle((60, 270, 735, 638), 20, fill='white', outline='#ccd6e8', width=2)
    d.rounded_rectangle((775, 270, 1440, 638), 20, fill='#ecf1ff', outline='#ccd6e8', width=2)
    d.text((95, 303), '报告观察 / 购买倾向', font=fonts[32], fill=teal)
    d.text((95, 377), '自动化与产品构建', font=fonts[32], fill=ink)
    d.text((95, 429), '例：n8n、fal', font=fonts[29], fill=muted)
    d.text((95, 493), '创意产出', font=fonts[32], fill=ink)
    d.text((95, 545), '例：Higgsfield、HeyGen', font=fonts[29], fill=muted)
    d.text((815, 303), '作者判断 / 待验证', font=fonts[32], fill=blue)
    d.text((815, 380), '更易使用的个人 Agent', font=fonts[32], fill=ink)
    d.text((815, 445), '广告 / 交易收入等收费方式', font=fonts[29], fill=ink)
    d.text((815, 534), '能否扩大日常使用？', font=fonts[36], fill=blue)
    d.text((60, 690), '购买记录不能证明生产力提升；未来产品和收费方式不能写成已实现的采用结果。', font=fonts[23], fill=muted)
    save(im, 'observation-and-hypothesis', {'kind': 'qualitative reading guide', 'numeric_task_shares': None, 'observations_and_author_hypotheses_separated': True})
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2)+'\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--font', default='/System/Library/Fonts/STHeiti Light.ttc')
    render(parser.parse_args().font)
