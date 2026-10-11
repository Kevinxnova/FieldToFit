"""Protect exact URLs, versions and numbers for on-device translation drafts."""
import argparse
import json
import re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
parser=argparse.ArgumentParser();parser.add_argument('--folder',required=True);args=parser.parse_args()
folder=Path(args.folder).resolve()
glossary={
    '未独立复现实验':'FieldToFit has not independently reproduced the experiments',
    '事后评测':'post-hoc evaluation','成本口径':'cost accounting basis','评测口径':'evaluation basis','口径':'measurement basis',
    '原图':'original figure','重绘':'redrawing','示意':'illustration',
    '消融':'ablation','固定提交':'pinned commit','固定版本':'pinned version','仓库':'repository','量化':'quantization','署名':'attribution','分发许可':'distribution license','开放权重':'open weights','安装说明':'installation instructions','零样本质量':'zero-shot quality','共同成功题':'tasks successful under both conditions',
    '执行费用':'execution cost','官方原始材料':'official original materials',
    'MCP可读本站解读':'MCP provides FieldToFit interpretation',
    '官方材料仅链接':'Official material is link-only',
    '官网材料仅链接':'Official website material is link-only',
    '本站未安装或复现性能':'FieldToFit has not installed it or reproduced the reported performance',
    '本站未安装或独立验证':'FieldToFit has not installed or independently verified it',
    '独立复现':'independent reproduction','持续关注档案':'ongoing-watch profile',
    '持续关注':'ongoing watch','零样本':'zero-shot','置信区间':'confidence interval',
    '每百万':'per million','预填充':'prefill','封装':'encapsulation',
    '显存':'VRAM','幻觉':'hallucination','工具调用':'tool call','推理计算':'inference compute',
    '提示缓存':'prompt caching','命中率':'hit rate','吞吐':'throughput',
    '上游':'upstream','复测':'retest','复现':'reproduce','实测':'runtime test',
    '评测':'evaluation','榜单':'leaderboard','基线':'baseline','档案':'profile',
    '原文':'source text','本站':'FieldToFit','方案用量':'plan usage','套餐':'plan',
    '开源':'open source','只读':'read-only','副作用':'side effect',
    '模型权重':'model weights','权重':'weights','工具调用':'tool calls',
    '阿里巴巴':'Alibaba','字节跳动':'ByteDance','深度求索':'DeepSeek','智谱':'Zhipu AI','月之暗面':'Moonshot AI','腾讯':'Tencent',
}
entries=[]
for source in json.loads((folder/'local-input.json').read_text()):
    value=source
    value=re.sub(r'(\d{4})年(\d{1,2})月(\d{1,2})日',lambda m:f'{m[1]}-{int(m[2]):02d}-{int(m[3]):02d}',value)
    value=re.sub(r'(\d{4})年(\d{1,2})月',lambda m:f'{m[1]}-{int(m[2]):02d}',value)
    value=re.sub(r'(\d{1,2})月(\d{1,2})日',lambda m:f'{m[1]}/{m[2]}',value)
    value=re.sub(r'(\d+(?:\.\d+)?)\s*(万|亿)',lambda m:f'{float(m[1])*(10000 if m[2]=="万" else 100000000):,.0f}',value)
    for chinese,english in glossary.items():value=value.replace(chinese,' '+english+' ')
    tokens={}
    def protect(match):
        token='FtfToken'+str(len(tokens))+'End'
        tokens[token]=match[0];return ' '+token+' '
    # Natural English terminology stays visible. Protect URLs and literal numeric tokens.
    value=re.sub(r'https?://[^\s)\]<>，。；]+|\d{4}-\d{2}(?:-\d{2})?|\d{1,2}[:/]\d{1,2}|[A-Za-z][A-Za-z0-9._\-]*\d[A-Za-z0-9._\-]*|\d+(?:[.,]\d+)*(?:[%kKmMbB])?',protect,value)
    entries.append({'source':source,'prepared':value,'tokens':tokens})
(folder/'local-prepared.json').write_text(json.dumps(entries,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'prepared':len(entries)}))
