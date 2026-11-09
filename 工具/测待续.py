#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""第 1 层待续的离线测试（卷四 6.27，11-05 用户：熄灯只摘掉负责人的框，不把任务撤下第 1 层）：
没人亮灯、本区会话 7 天内动过、当前这一段还有我能接着做的 → 待续；只等用户做的、没到点的待触发、只被跨区碰过的、8 天前动的不算；
钉在第 1 层（常驻）的一直待续；用户点了放下，本区会话再动、TODO 再改才回来；会话说收工、用户还没看的灯带「收工」。临时目录，不碰真数据。
跑法：/usr/bin/python3 工具/测待续.py [板.py 路径]"""
import importlib.util, json, os, sys, tempfile, time

板路 = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), '板.py')
错 = []


def 查(名, 过, 细=''):
    print(('✅ ' if 过 else '❌ ') + 名 + ('' if 过 else '  ' + str(细)))
    if not 过:
        错.append(名)


头 = '编号 | 步骤 | 产出物 | 预计耗时 | 依赖/阻塞\n---|---|---|---|---\n'
段 = lambda 名, 行们: f'# {名} · TODO\n\n## 卷一（11-05 · 在做）\n\n' + 头 + ''.join(行们)
做完 = '1 | ✅ [自动] 做了 | — | — | —\n'
with tempfile.TemporaryDirectory() as 根, tempfile.TemporaryDirectory() as 数:
    now = time.time()
    天 = 86400
    # 任务：(TODO, TODO 改于, [(会话, 记录)])
    样 = {
        '组/甲': (段('甲', [做完, '2 | [自动] 接着写 | — | — | 1\n']), now - 7200, [('local_甲', {'开': False, '时间': now - 3600})]),
        '组/乙': (段('乙', [做完, '2 | [需用户] 看一眼 | — | — | 1\n']), now - 7200, [('local_乙', {'开': False, '时间': now - 3600})]),
        '组/丙': (段('丙', [做完, '2 | [自动] 接着写 | — | — | 1\n']), now - 9 * 天, [('local_丙', {'开': False, '时间': now - 8 * 天})]),
        '组/丁': (段('丁', [做完, '2 | [自动] 接着写 | — | — | 1\n']), now - 7200,
                [('local_丁', {'开': True, '说': '跨区施工（从 别的 过来）', '租': 1800, '时间': now - 3700}), ('local_丁', {'开': False, '时间': now - 3600})]),
        '组/戊': (段('戊', [做完, '2 | [待触发] 复查：`到 12-31` 再看 | — | — | —\n']), now - 7200, [('local_戊', {'开': False, '时间': now - 3600})]),
        '组/己': (段('己', [做完, '2 | [待触发] 复查：`到 11-01` 再看 | — | — | —\n']), now - 7200, [('local_己', {'开': False, '时间': now - 3600})]),
        '组/庚': (段('庚', [做完, '2 | [自动] 接着写 | — | — | 1\n']), now - 7200, [('local_庚', {'开': True, '说': '在写', '租': 1800, '时间': now - 60})]),
        '组/辛': (段('辛', [做完]), now - 7200, [('local_辛', {'开': False, '时间': now - 3600})]),
        '组/壬': (段('壬', [做完, '2 | [自动] 接着写 | — | — | 1\n']), now - 7200, [('local_壬', {'开': False, '时间': now - 3600})]),
        '组/癸': (段('癸', [做完, '2 | [自动] 接着写 | — | — | 1\n']), now - 7200, [('local_癸', {'开': False, '时间': now - 3600})]),
        '组/子': (段('子', [做完, '2 | [自动] 接着写 | — | — | 1\n']), now - 7200, [('local_子', {'开': False, '等你': True, '收工': True, '说': '做完了', '时间': now - 120})]),
    }
    with open(os.path.join(数, '开关.jsonl'), 'w', encoding='utf-8') as f:
        for 任务, (文, 改于, 记们) in 样.items():
            os.makedirs(os.path.join(根, 任务))
            p = os.path.join(根, 任务, 'TODO.md')
            open(p, 'w', encoding='utf-8').write(文)
            os.utime(p, (改于, 改于))
            for 会, e in 记们:
                f.write(json.dumps(dict({'任务': 任务, '谁': 'Claude', '格子': [], '会话': 会, '接入': 'claude'}, **e), ensure_ascii=False) + '\n')
    json.dump({'组/辛': {'常驻': True}, '组/壬': {'放下': now - 60}, '组/癸': {'放下': now - 5000}}, open(os.path.join(数, '布局.json'), 'w', encoding='utf-8'), ensure_ascii=False)
    open(os.path.join(数, '账本.csv'), 'w').close()
    os.environ.update(BAN_ROOT=根, BAN_DATA=数, BAN_LEDGER=os.path.join(数, '账本.csv'), DYT_DIR=os.path.join(数, '导演台'), BAN_OPEN='/bin/echo')
    sp = importlib.util.spec_from_file_location('板', 板路)
    板 = importlib.util.module_from_spec(sp)
    sp.loader.exec_module(板)
    片 = {t['键']: t for t in 板.看板数据(强制=True)['任务']}
    续 = lambda k: 片[k].get('待续')
    查('本区会话一小时前动过、还有能接着做的：待续，列出步骤', (续('组/甲') or {}).get('步') == ['2'], 续('组/甲'))
    查('待续那句话写了几步、怎么接着干', '还有 1 步能接着做：2' in (续('组/甲') or {}).get('说', '') and '继续' in (续('组/甲') or {}).get('说', ''), 续('组/甲'))
    查('只剩等用户做的需用户：不待续', not 续('组/乙'), 续('组/乙'))
    查('本区会话 8 天前动的：不待续', not 续('组/丙'), 续('组/丙'))
    查('只被别的会话跨区碰过：不待续', not 续('组/丁'), 续('组/丁'))
    查('只剩没到点的待触发：不待续', not 续('组/戊'), 续('组/戊'))
    查('待触发到点了：待续', (续('组/己') or {}).get('步') == ['2'], 续('组/己'))
    查('亮着灯的：不待续（第 1 层照灯画）', not 续('组/庚') and 片['组/庚']['灯'], 续('组/庚'))
    查('钉在第 1 层（常驻）、步骤都做完了：照样待续', (续('组/辛') or {}).get('常驻') is True and '钉在第 1 层' in 续('组/辛').get('说', ''), 续('组/辛'))
    查('用户点了放下、之后没新动静：不待续', not 续('组/壬'), 续('组/壬'))
    查('放下以后本区会话又动过：回来', bool(续('组/癸')), 续('组/癸'))
    灯 = 片['组/子']['灯']
    查('会话说收工、用户还没看：灯带「收工」、等你，不待续', len(灯) == 1 and 灯[0]['态'] == '等' and 灯[0].get('收工') is True and not 续('组/子'), 灯)
    v = 板.改布局({'组/甲': {'常驻': True, '放下': now}, '组/乙': {'x': 1, 'y': 2}})
    查('布局认常驻、放下，别的照旧', v.get('组/甲') == {'常驻': True, '放下': now} and v.get('组/乙') == {'x': 1, 'y': 2}, v)
    v = 板.改布局({'组/甲': {}})
    查('什么都不剩的条目删掉（不钉了以后不像排过）', '组/甲' not in v, v)
    try:
        板.改布局({'组/甲': {'放下': 'x'}})
        查('放下写坏了会报错', False)
    except Exception:
        查('放下写坏了会报错', True)
print(f'\n{"全过" if not 错 else f"{len(错)} 条没过"}')
sys.exit(1 if 错 else 0)
