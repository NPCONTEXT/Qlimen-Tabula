#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""设置.json 的读法：没有设置时工作区是仓库自带的演示工作区；工作区（相对路径按仓库目录算、~ 展开）、分组（空 = 自动按第一层文件夹）、
跳过目录、派工账本、Codex（默认关）都照设置读；测试中（设了 BAN_ROOT 或 BAN_DATA）不读 设置.json，除非用 BAN_SETTINGS 指定。
每条在子进程里跑 板.py 设置 / 读，临时目录造工作区和设置，不碰真数据。
跑法：/usr/bin/python3 工具/测设置.py [板.py 路径]
改坏验法：把 板.py 里 名字() 自动分组那句（if not 母文件夹 and len(ps) > 1）删掉，「没设分组」那条要红；把 读设置() 里的 os.path.exists(p) 判断改成 False，后面几条要红。"""
import json
import os
import subprocess
import sys
import tempfile

板 = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), '板.py')
库 = os.path.dirname(os.path.dirname(os.path.realpath(板)))   # 用真实路径算相对路径（/tmp 这类是软链接，.. 会走到别处）
错 = []


def 查(名, 过, 细=''):
    print(('✅ ' if 过 else '❌ ') + 名 + ('' if 过 else '  ' + str(细)[:300]))
    if not 过:
        错.append(名)


def 跑(*参数, env=None):
    e = {k: v for k, v in os.environ.items() if not k.startswith('BAN_')}
    e.update(env or {})
    r = subprocess.run(['/usr/bin/python3', 板, *参数], capture_output=True, text=True, env=e, timeout=60)
    return r.stdout + r.stderr


def 设置(env=None):
    out = 跑('设置', env=env)
    try:
        return json.loads(out[out.index('{'):])
    except ValueError:
        return {'读不出': out}


with tempfile.TemporaryDirectory() as d:
    d = os.path.realpath(d)
    区 = os.path.join(d, '我的任务')
    for k in ('甲组/任务一', '乙组/任务二', '旧的/任务三', '散任务'):
        os.makedirs(os.path.join(区, k))
        with open(os.path.join(区, k, 'TODO.md'), 'w', encoding='utf-8') as f:
            f.write(f'# {k.split("/")[-1]} · TODO\n\n编号 | 步骤 | 产出物 | 预计耗时 | 依赖/阻塞\n---|---|---|---|---\n1 | ✅ 第一步 | — | — | —\n2 | 第二步 | — | — | 1\n')
    数据 = os.path.join(d, '数据')

    s = 设置(env={'BAN_SETTINGS': os.path.join(d, '没有这个.json'), 'BAN_DATA': 数据})
    查('没有设置：工作区是仓库自带的演示工作区', s.get('工作区') == os.path.realpath(os.path.join(库, '示例', '演示工作区')), s)
    查('没有设置：分组自动、派工账本和 Codex 都不读', str(s.get('分组', '')).startswith('自动') and s.get('派工账本') == '不读' and (s.get('Codex') or {}).get('会话记录') == '不读', s)

    设 = os.path.join(d, '设置.json')
    with open(设, 'w', encoding='utf-8') as f:
        json.dump({'工作区': 区, '跳过目录': ['旧的'], '派工账本': '~/假账本.csv', 'Codex': {'开': False}}, f, ensure_ascii=False)
    s = 设置(env={'BAN_SETTINGS': 设, 'BAN_DATA': 数据})
    查('设置的工作区照写的读', s.get('工作区') == 区, s)
    查('跳过目录加在默认的后面', '旧的' in (s.get('跳过目录') or []) and '归档' in (s.get('跳过目录') or []), s)
    查('派工账本展开 ~', s.get('派工账本') == os.path.expanduser('~/假账本.csv'), s)
    查('Codex 没开：不读她的会话记录', (s.get('Codex') or {}).get('会话记录') == '不读', s)

    with open(设, 'w', encoding='utf-8') as f:
        json.dump({'工作区': os.path.relpath(区, 库)}, f, ensure_ascii=False)
    s = 设置(env={'BAN_SETTINGS': 设, 'BAN_DATA': 数据})
    查('相对路径的工作区按仓库目录算', s.get('工作区') == 区, (s.get('工作区'), 区))

    with open(设, 'w', encoding='utf-8') as f:
        json.dump({'工作区': 区, '跳过目录': ['旧的']}, f, ensure_ascii=False)
    out = 跑('读', env={'BAN_SETTINGS': 设, 'BAN_DATA': 数据})
    查('读到工作区里的任务、跳过目录里的不算', '甲组/任务一' in out and '乙组/任务二' in out and '散任务' in out and '任务三' not in out, out)

    sys.path.insert(0, os.path.dirname(板))
    import importlib.util
    def 载(env):
        old = dict(os.environ)
        os.environ.clear()
        os.environ.update({k: v for k, v in old.items() if not k.startswith('BAN_')}, **env)
        try:
            sp = importlib.util.spec_from_file_location('板测设置', 板)
            m = importlib.util.module_from_spec(sp)
            sp.loader.exec_module(m)
            return m
        finally:
            os.environ.clear()
            os.environ.update(old)
    m = 载({'BAN_SETTINGS': 设, 'BAN_DATA': 数据})
    查('没设分组：工作区下第一层每个文件夹一组，直接放在根下的归「其他」', m.名字('甲组/任务一') == ('甲组', '任务一') and m.名字('散任务') == ('其他', '散任务'), (m.名字('甲组/任务一'), m.名字('散任务')))
    with open(设, 'w', encoding='utf-8') as f:
        json.dump({'工作区': 区, '分组': ['乙组', '甲组']}, f, ensure_ascii=False)
    m = 载({'BAN_SETTINGS': 设, 'BAN_DATA': 数据})
    查('设了分组：照写的顺序排，不在里面的归「其他」', m.找任务()[:2] == ['乙组/任务二', '甲组/任务一'] and m.名字('旧的/任务三') == ('其他', '旧的·任务三'), (m.找任务(), m.名字('旧的/任务三')))

    m = 载({'BAN_DATA': 数据})
    查('测试中（设了 BAN_DATA）没给 BAN_SETTINGS：不读仓库里的 设置.json', m.设置 == {}, m.设置)

print('\n全过' if not 错 else f'\n{len(错)} 条没过')
sys.exit(1 if 错 else 0)
