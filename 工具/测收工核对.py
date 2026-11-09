#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""收工核对的离线测试（卷四 6.15，11-04）：会话自己收工以后 TODO 没再改、还有等你的，总览「几/几」后面打「?」；
TODO 一改、用户点了「知道了」、灯还亮着、没有等你、收工超过一周，都不打。临时目录造任务和开关记录，不碰真数据。
跑法：/usr/bin/python3 工具/测收工核对.py [板.py 路径]"""
import importlib.util, json, os, sys, tempfile, time

板路 = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), '板.py')
错 = []


def 查(名, 过, 细=''):
    print(('✅ ' if 过 else '❌ ') + 名 + ('' if 过 else '  ' + str(细)))
    if not 过:
        错.append(名)


头 = '编号 | 步骤 | 产出物 | 预计耗时 | 依赖/阻塞\n---|---|---|---|---\n'
等你的 = '# 甲 · TODO\n\n## 卷一（11-04 · 在做）\n\n' + 头 + '1 | [需用户] 看一眼 | — | — | —\n2 | ✅ [自动] 做了 | — | — | —\n'
没等的 = '# 戊 · TODO\n\n## 卷一（11-04 · 在做）\n\n' + 头 + '1 | ✅ [自动] 做了 | — | — | —\n'
with tempfile.TemporaryDirectory() as 根, tempfile.TemporaryDirectory() as 数:
    now = time.time()
    天 = 86400
    # 任务：(TODO 内容, TODO 改于, [开关记录])
    样 = {
        '组/甲': (等你的, now - 60, [{'开': False, '时间': now}]),                              # 收工后没改 TODO、还有等你 → 打「?」
        '组/乙': (等你的, now, [{'开': False, '时间': now - 120}]),                             # 收工后又改过 TODO → 不打
        '组/丙': (等你的, now - 60, [{'开': False, '等你': False, '由': '用户点知道了', '时间': now}]),   # 用户点了知道了 → 不打
        '组/丁': (等你的, now - 60, [{'开': False, '时间': now - 30}, {'开': True, '租': 1800, '时间': now}]),   # 收工后又开了灯 → 不打
        '组/戊': (没等的, now - 60, [{'开': False, '时间': now}]),                              # 没有等你的 → 不打
        '组/己': (等你的, now - 9 * 天, [{'开': False, '时间': now - 8 * 天}]),                   # 收工超过一周 → 不打
        '组/庚': (等你的, now - 60, [{'开': True, '说': '跨区施工（从 别的 过来）', '租': 1800, '时间': now - 30}, {'开': False, '等你': False, '时间': now}]),   # 关的是跨区施工那盏 → 不打
    }
    with open(os.path.join(数, '开关.jsonl'), 'w', encoding='utf-8') as f:
        for 任务, (文, 改于, 记们) in 样.items():
            d = os.path.join(根, 任务)
            os.makedirs(d)
            p = os.path.join(d, 'TODO.md')
            open(p, 'w', encoding='utf-8').write(文)
            os.utime(p, (改于, 改于))
            for e in 记们:
                f.write(json.dumps(dict({'任务': 任务, '谁': 'Claude', '格子': [], '会话': 'local_测试', '接入': 'claude'}, **e), ensure_ascii=False) + '\n')
    open(os.path.join(数, '账本.csv'), 'w').close()
    os.environ.update(BAN_ROOT=根, BAN_DATA=数, BAN_LEDGER=os.path.join(数, '账本.csv'), DYT_DIR=os.path.join(数, '导演台'), BAN_OPEN='/bin/echo')
    sp = importlib.util.spec_from_file_location('板', 板路)
    板 = importlib.util.module_from_spec(sp)
    sp.loader.exec_module(板)
    片 = {t['键']: t for t in 板.看板数据(强制=True)['任务']}
    查('收工后 TODO 没改、还有等你：打「?」，写出是哪几步', (片['组/甲'].get('收工疑') or {}).get('步') == ['1'], 片['组/甲'].get('收工疑'))
    for k, 说 in (('组/乙', '收工后又改过 TODO'), ('组/丙', '用户点了「知道了」'), ('组/丁', '收工后又开了灯'), ('组/戊', '没有等你的步骤'), ('组/己', '收工超过一周'), ('组/庚', '关的是跨区施工那盏灯')):
        查(说 + '：不打「?」', '收工疑' not in 片[k], 片[k].get('收工疑'))
print(f'\n{"全过" if not 错 else f"{len(错)} 条没过"}')
sys.exit(1 if 错 else 0)
