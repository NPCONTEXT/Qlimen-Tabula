#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""跨区多名牌的离线测试（卷四 6.23，11-05）：一个任务几个会话同时干（一个本区、两个跨区），
每盏灯带自己的会话号和链接；绑定（接手、投信、没有会话号的名牌）只认本区会话，跨区会话来了、用户点「知道了」都不改；
跨区那盏关了只少它自己。临时目录造任务和开关记录，不碰真数据。
跑法：/usr/bin/python3 工具/测多名牌.py [板.py 路径]"""
import importlib.util, json, os, sys, tempfile, time
from urllib.parse import quote

板路 = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), '板.py')
错 = []


def 查(名, 过, 细=''):
    print(('✅ ' if 过 else '❌ ') + 名 + ('' if 过 else '  ' + str(细)))
    if not 过:
        错.append(名)


头 = '编号 | 步骤 | 产出物 | 预计耗时 | 依赖/阻塞\n---|---|---|---|---\n'
文 = lambda 名: f'# {名} · TODO\n\n## 卷一（11-05 · 在做）\n\n' + 头 + '1 | [自动] 做 | — | — | —\n'
本区, 跨一, 跨二, 挪 = 'local_aaaa-本区', 'local_bbbb-跨区一', 'local_cccc-跨区二', 'local_dddd-挪本区'
开链 = lambda 会: 'claude://code/continue?session=' + quote(会, safe='')
with tempfile.TemporaryDirectory() as 根, tempfile.TemporaryDirectory() as 数:
    now = time.time()
    for 任务 in ('组/示例小说', '组/只来过跨区', '组/挪本区', '组/一个会话'):
        os.makedirs(os.path.join(根, 任务))
        open(os.path.join(根, 任务, 'TODO.md'), 'w', encoding='utf-8').write(文(任务.split('/')[1]))
    记们 = [
        ('组/示例小说', 本区, {'开': True, '说': '第 54 章按推荐重写', '时间': now - 600}),
        ('组/示例小说', 跨一, {'开': True, '说': '跨区施工（从 无限表格 过来）', '时间': now - 60}),
        ('组/示例小说', 跨二, {'开': True, '说': '跨区施工（从 盯跑 过来）', '时间': now - 30}),
        ('组/只来过跨区', 跨一, {'开': True, '说': '跨区施工（从 无限表格 过来）', '时间': now - 500}),
        ('组/只来过跨区', 跨一, {'开': False, '等你': False, '时间': now - 400}),
        ('组/挪本区', 挪, {'开': True, '说': '跨区施工（从 别的 过来）', '时间': now - 100}),   # 一整轮只在这里动笔，一轮结束本区挪过来（卷四 6.10）
        ('组/挪本区', 挪, {'开': False, '等你': True, '说': '这一轮做完了', '时间': now - 50}),
        ('组/一个会话', 本区, {'开': True, '说': '照旧', '时间': now - 20}),
        ('零活:local_eeee-零活', 'local_eeee-零活', {'开': True, '说': '查个东西', '题': '查个东西', '时间': now - 10}),
    ]
    p = os.path.join(数, '开关.jsonl')
    with open(p, 'w', encoding='utf-8') as f:
        for 任务, 会, e in 记们:
            f.write(json.dumps(dict({'任务': 任务, '谁': 'Claude', '格子': [], '租': 1800, '会话': 会, '接入': 'claude'}, **e), ensure_ascii=False) + '\n')
    open(os.path.join(数, '账本.csv'), 'w').close()
    os.environ.update(BAN_ROOT=根, BAN_DATA=数, BAN_LEDGER=os.path.join(数, '账本.csv'), DYT_DIR=os.path.join(数, '导演台'), BAN_OPEN='/bin/echo')
    sp = importlib.util.spec_from_file_location('板', 板路)
    板 = importlib.util.module_from_spec(sp)
    sp.loader.exec_module(板)

    def 片们():
        return {t['键']: t for t in 板.看板数据(强制=True)['任务']}

    片 = 片们()
    t = 片['组/示例小说']
    会们 = [l.get('会话') or '' for l in t['灯']]
    查('一个任务三个会话：三盏灯各带自己的会话号', sorted(会们) == sorted([本区, 跨一, 跨二]), 会们)
    查('每盏灯的链接点进它自己的会话', all(l.get('链') == 开链(l.get('会话', '')) for l in t['灯']), [l.get('链') for l in t['灯']])
    查('绑定还是本区会话（跨区会话后来的，不抢）', t['会话'] == 本区, t['会话'])
    查('任务的会话链接（没有会话号的名牌、接手）点进本区会话', t['会话链接'] == 开链(本区), t['会话链接'])
    查('只来过跨区的任务：没有绑定，接手开新会话', 片['组/只来过跨区']['会话'] == '' and 片['组/只来过跨区']['会话链接'].startswith('claude://code/new'), (片['组/只来过跨区']['会话'], 片['组/只来过跨区']['会话链接'][:40]))
    查('一整轮只在那里动笔、本区挪过去的：绑定是它', 片['组/挪本区']['会话'] == 挪, 片['组/挪本区']['会话'])
    查('一个会话的任务照旧', 片['组/一个会话']['会话'] == 本区 and [l.get('链') for l in 片['组/一个会话']['灯']] == [开链(本区)], 片['组/一个会话'])
    零 = 片.get('零活:local_eeee-零活') or {}
    查('零活那一行的灯也带链接', [l.get('链') for l in 零.get('灯', [])] == [开链('local_eeee-零活')], 零.get('灯'))
    信 = 板.投信('组/示例小说', '测试：点了做完了')
    查('你在看板上的动作投给本区会话', 信.get('会话') == 本区, 信)

    # 跨区一那盏结束（插件一轮结束用「完工」关）；用户点了跨区二那盏的「知道了」（就算点错了也不改绑定）
    with open(p, 'a', encoding='utf-8') as f:
        f.write(json.dumps({'任务': '组/示例小说', '谁': 'Claude', '开': False, '等你': False, '时间': now, '会话': 跨一, '接入': 'claude'}, ensure_ascii=False) + '\n')
    片 = 片们()
    t = 片['组/示例小说']
    会们 = sorted(l.get('会话') or '' for l in t['灯'])
    查('跨区一那盏关了：只少它自己', 会们 == sorted([本区, 跨二]), 会们)
    查('本区那盏照旧在干', any(l.get('会话') == 本区 and l['态'] == '干' for l in t['灯']), t['灯'])
    with open(p, 'a', encoding='utf-8') as f:
        f.write(json.dumps({'任务': '组/示例小说', '谁': 'Claude', '开': False, '等你': False, '时间': now + 1, '会话': 跨二, '接入': 'claude', '由': '用户点知道了'}, ensure_ascii=False) + '\n')
    查('用户点「知道了」那条不改绑定', 片们()['组/示例小说']['会话'] == 本区, 片们()['组/示例小说']['会话'])
print(f'\n{"全过" if not 错 else f"{len(错)} 条没过"}')
sys.exit(1 if 错 else 0)
