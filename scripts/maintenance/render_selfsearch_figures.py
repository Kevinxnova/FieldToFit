"""FieldToFit diagrams from SelfSearch v2 facts, not reproductions of its artwork.

Uses the already-supported Pillow renderer; --font allows another Chinese font.
The paper's arXiv non-exclusive license is not a reuse license for its figures.
"""
import argparse
import hashlib
import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[2]
SOURCE = 'https://arxiv.org/html/2609.37968v2'
RIGHTS = '图形 © FieldToFit；原始数据与方法归属见来源'


def render(font):
    bg, ink, muted, blue, teal = '#f7f8fc', '#172641', '#536178', '#375ad2', '#147c78'
    fonts = {s: ImageFont.truetype(font, s) for s in (23, 26, 29, 32, 36, 43, 54)}
    target = ROOT/'frontend/public/report-figures'
    manifest_path = ROOT/'backend/knowledge/content/report-figures.json'
    manifest = json.loads(manifest_path.read_text())

    def page(number, title, subtitle, locator):
        im = Image.new('RGB', (1500, 900), bg); d = ImageDraw.Draw(im)
        d.rounded_rectangle((60, 47, 230, 87), 12, fill=ink)
        d.text((78, 54), f'REPORT / 0{number}', font=fonts[23], fill='white')
        d.text((60, 117), title, font=fonts[43], fill=ink)
        d.text((60, 187), subtitle, font=fonts[26], fill=muted)
        d.line((60, 783, 1440, 783), fill='#d7ddea', width=2)
        d.text((60, 806), '来源：SelfSearch v2（2026-09-30） / '+locator, font=fonts[23], fill=muted)
        d.text((60, 848), 'FieldToFit 本站重绘／示意 / arxiv.org/html/2609.37968v2 / 非报告原图', font=fonts[23], fill=muted)
        return im, d

    def save(im, name, statistics):
        path = target/f'selfsearch-v2-{name}.png'; im.save(path, optimize=True)
        manifest['/report-figures/'+path.name] = {
            'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
            'source_urls': [SOURCE], 'license': RIGHTS,
            'version': 'arXiv 2609.37968v2 · 2026-09-30',
            'origin': 'fieldtofit-redraw', 'statistics': statistics,
        }

    im, d = page(1, '模型保持不变，改进发生在工具与流程', '一轮改进如何交给下一代；流程示意，不表示训练模型或在运行中替换自己', '第2节／附录A')
    boxes = [(60, '读取前代记录', ['推理、调用与结果', '代码变化与本地检查']),
             (540, '编辑并验证副本', ['指令、工具、执行逻辑', '本轮运行者保持不变']),
             (1020, '下一代接棒', ['新实现成为下一轮运行者', '本轮记录交给下一代'])]
    for x, title, lines in boxes:
        d.rounded_rectangle((x, 280, x+420, 485), 18, fill='white', outline='#ccd6e8', width=2)
        d.text((x+25, 308), title, font=fonts[32], fill=blue)
        for i, line in enumerate(lines): d.text((x+25, 377+46*i), line, font=fonts[26], fill=ink)
    for x in (490, 970):
        d.line((x, 380, x+35, 380), fill=blue, width=4)
        d.polygon([(x+35, 380), (x+24, 371), (x+24, 389)], fill=blue)
    d.rounded_rectangle((60, 525, 1440, 630), 16, fill='#eaf0ff')
    d.text((90, 545), '两条路线 × 10代：各自保留实现，共享上一代两份记录', font=fonts[32], fill=ink)
    d.text((90, 594), '能力路线：补齐工具／程序    ·    适应路线：遇到失败或矛盾证据时调整做法', font=fonts[26], fill=muted)
    d.text((60, 668), '固定边界：模型权重、外部运行时、推理设置、输出上限、资源预算、日志', font=fonts[26], fill=ink)
    d.text((60, 719), '搜索阶段无下游题目／分数；仍有工具反馈和本地检查，冻结后另做下游评测。', font=fonts[26], fill=muted)
    save(im, 'mechanism', {'kind': 'procedure diagram', 'generations': 10, 'lineages': 2,
                          'model_weights_fixed': True, 'downstream_feedback_during_search': False})

    im, d = page(2, '经验记录与改进者接棒，都有实验支持', 'DeepSeek配置 · SWE-bench Verified 120题 · 两条路线的平均成功率', '第4.1节／表4')
    x0, x1 = 405, 1280
    for value in (0, 20, 40, 60, 80, 100):
        x = x0+value/100*(x1-x0);d.line((x, 280, x, 633), fill='#dce2ed', width=2)
        d.text((x, 650), f'{value}%', font=fonts[26], fill=muted, anchor='mt')
    rows = [('初始Agent', 81.7, '#b6c2dd'), ('不提供前代记录', 83.8, '#889bcc'),
            ('始终由初始Agent改进', 83.8, '#889bcc'), ('完整 SelfSearch', 86.7, teal)]
    for i, (label, value, color) in enumerate(rows):
        y = 290+i*88;d.text((60, y+12), label, font=fonts[29], fill=ink)
        end = x0+value/100*(x1-x0);d.rounded_rectangle((x0, y, end, y+56), 7, fill=color)
        d.text((end+15, y+8), f'{value}%', font=fonts[32], fill=ink)
    d.text((60, 709), '完整方法比两种消融各高2.9个百分点；本图不是单条路线，也不证明无限持续进步。', font=fonts[26], fill=muted)
    save(im, 'records', {'unit': '% success, mean of two lineages', 'benchmark': 'SWE-bench Verified 120 tasks',
                        'configuration': 'DeepSeek V4 Pro search / V4 Flash execution; generation 10',
                        'initial': 81.7, 'no_records': 83.8, 'fixed_improver': 83.8, 'full': 86.7})

    im, d = page(3, '成功率与费用：先分清样本和分母', 'DeepSeek配置 · SWE-bench Multilingual抽样60题、8种语言 · 表1', '第3.1–3.2节／表1／表10')
    d.rounded_rectangle((60, 270, 1440, 565), 18, fill='white', outline='#ccd6e8', width=2)
    columns = [(100, '指标'), (650, '初始'), (925, '能力路线'), (1210, '适应路线')]
    for x, label in columns: d.text((x, 298), label, font=fonts[29], fill=muted)
    d.line((100, 352, 1390, 352), fill='#dce2ed', width=2)
    for y, label, values in [(382, '成功率（%）', ['68.3', '66.7', '73.3']),
                             (471, '平均执行费用（美元／尝试）', ['0.0521', '0.0321', '0.0332'])]:
        d.text((100, y), label, font=fonts[29], fill=ink)
        for (x, _), val in zip(columns[1:], values): d.text((x, y), val, font=fonts[36], fill=teal if x==1210 else ink)
    d.rounded_rectangle((60, 600, 1440, 715), 16, fill='#eaf0ff')
    d.text((90, 619), '38.5%：适应路线在“双方都解对的题”上，执行费用的降幅', font=fonts[32], fill=blue)
    d.text((90, 670), '这是表10的独立口径，不能由上面的平均费用计算；搜索与事后评测费用另计。', font=fonts[26], fill=muted)
    d.text((60, 740), '同一配置也会有退步：能力路线成功率68.3% → 66.7%；不是每条路线都更好。', font=fonts[23], fill=muted)
    save(im, 'results', {'benchmark': 'SWE-bench Multilingual 60 sampled tasks / eight languages',
                        'success_unit': '%', 'success': [68.3, 66.7, 73.3],
                        'average_execution_cost_unit': 'USD per attempt, including failures; excludes search',
                        'average_execution_cost': [0.0521, 0.0321, 0.0332],
                        'shared_success_execution_cost_reduction_percent': 38.5,
                        'shared_success_scope': 'Initial and DeepSeek adaptive jointly solved tasks, separate denominator'})

    im, d = page(4, '工具能跨模型复用，但证据仍有边界', 'SWE-bench Verified 120题 · 固定工具实现后换执行模型 · 成功率（%）', '第3.4节／表3／第6节')
    xs = [100, 590, 870, 1160]
    # Baselines belong to execution models, so keep them in their own row.
    labels = ['工具实现来源', '路线', 'GPT执行', 'DeepSeek执行']
    d.rounded_rectangle((60, 270, 1440, 665), 18, fill='white', outline='#ccd6e8', width=2)
    for x, label in zip(xs, labels): d.text((x, 292), label, font=fonts[29], fill=muted)
    rows = [('初始Agent', '基线', '75.0', '81.7'),
            ('GPT搜索得到', '能力 / 适应', '77.5 / 75.0', '83.3 / 85.0'),
            ('DeepSeek搜索得到', '能力 / 适应', '79.2 / 76.7', '86.7 / 86.7')]
    for i, row in enumerate(rows):
        y = 375+i*92
        for x, val in zip(xs, row): d.text((x, y), val, font=fonts[29], fill=ink)
        if i<2:d.line((100, y+65, 1390, y+65), fill='#dce2ed', width=2)
    d.text((60, 700), '配置：搜索 GPT-5.6 Sol / DeepSeek V4 Pro；执行 GPT-5.6 Luna / DeepSeek V4 Flash', font=fonts[23], fill=muted)
    d.text((60, 744), '这是有限任务集的迁移实验；独立重复搜索的稳定性、更多模型与真实业务仍待验证。', font=fonts[23], fill=muted)
    save(im, 'transfer', {'unit': '% success', 'benchmark': 'SWE-bench Verified 120 tasks',
                         'execution_columns': ['GPT-5.6 Luna', 'DeepSeek V4 Flash'],
                         'initial': [75.0, 81.7], 'gpt_search_capability': [77.5, 83.3],
                         'gpt_search_adaptive': [75.0, 85.0], 'deepseek_search_capability': [79.2, 86.7],
                         'deepseek_search_adaptive': [76.7, 86.7]})
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2)+'\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--font', default='/System/Library/Fonts/STHeiti Light.ttc')
    render(parser.parse_args().font)
