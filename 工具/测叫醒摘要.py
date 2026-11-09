#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""施工区「叫醒 Claude」打包的摘要（卷四 6.74，11-06）：用户选了又取消，摘要要写「取消选了」，不能两次都写「选了」。
临时目录放分镜样本存档的副本（状态.json、区域.json 复制 测施工区-样本/导演台，事件.jsonl 自己造）和看板数据，不碰真数据、不真投信。
跑法：/usr/bin/python3 工具/测叫醒摘要.py [板.py 路径]
改坏验法：把 施工区摘要 里按「选」是不是 False 分开写的那句改回只写「选了」，第 1 条要红（11-07 分卷五起按登记认施工区）。"""
import importlib.util, json, os, shutil, sys, tempfile

板路 = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), '板.py')
真台 = os.path.join(os.path.dirname(os.path.abspath(__file__)), '测施工区-样本', '导演台')   # 合成的分镜样本
错 = []


def 查(名, 过, 细=''):
    print(('✅ ' if 过 else '❌ ') + 名 + ('' if 过 else '  ' + str(细)))
    if not 过:
        错.append(名)


with tempfile.TemporaryDirectory() as 数:
    台 = os.path.join(数, '导演台')
    os.makedirs(台)
    shutil.copyfile(os.path.join(真台, '状态.json'), os.path.join(台, '状态.json'))
    shutil.copyfile(os.path.join(真台, '区域.json'), os.path.join(台, '区域.json'))   # 分卷五：区的字段、行名从这里读
    事件 = [   # 照作者真点过的造：V3 样片选了又取消、开场通过又取消
        {'号': 1, '时间': '2026-11-06 03:26:34', '谁': '用户', '做': '选', '镜': 'V3', '产出': 'V3-5-1', '选': True},
        {'号': 2, '时间': '2026-11-06 03:26:55', '谁': '用户', '做': '选', '镜': 'V3', '产出': 'V3-5-1', '选': False},
        {'号': 3, '时间': '2026-11-06 21:17:47', '谁': '用户', '做': '通过', '镜': '开场'},
        {'号': 4, '时间': '2026-11-06 21:18:02', '谁': '用户', '做': '取消通过', '镜': '开场'},
    ]
    with open(os.path.join(台, '事件.jsonl'), 'w', encoding='utf-8') as f:
        for e in 事件:
            f.write(json.dumps(e, ensure_ascii=False) + '\n')
    with open(os.path.join(数, '施工区.json'), 'w', encoding='utf-8') as f:
        json.dump({'起点': 0, '已发': 0, '验收': {}}, f)
    with open(os.path.join(数, '施工区登记.json'), 'w', encoding='utf-8') as f:   # 分卷五：看板按登记认施工区
        json.dump({'区们': {'mv': {'任务': '视频/示例MV/MV', '台': 台, '态': '施工区.json'}}}, f, ensure_ascii=False)
    open(os.path.join(数, '账本.csv'), 'w').close()
    os.environ.update(BAN_DATA=数, BAN_LEDGER=os.path.join(数, '账本.csv'), DYT_DIR=台, BAN_OPEN='/bin/echo')
    sp = importlib.util.spec_from_file_location('板', 板路)
    板 = importlib.util.module_from_spec(sp)
    sp.loader.exec_module(板)
    区 = 板.施工区们().get('mv')
    查('只用临时目录：看板数据、MV 存档都指到副本', 板.数据 == 数 and getattr(区, '台', '') == 台, (板.数据, getattr(区, '台', '')))
    r = 板.施工区叫醒(区)
    箱 = os.path.join(数, '信箱', '待领.jsonl')
    摘要 = json.loads(open(箱, encoding='utf-8').read().strip().split('\n')[-1])['摘要'] if os.path.exists(箱) else ''
    行 = 摘要.split('\n')
    查('取消选写成「取消选了」', '· V3：取消选了 V3-5-1（样片）' in 行, 摘要)
    查('选上照旧写「选了」，只写一次', 行.count('· V3：选了 V3-5-1（样片）') == 1, 摘要)
    查('通过、取消通过照旧分开写', '· 开场：通过（镜号）' in 行 and '· 开场：取消通过（镜号）' in 行, 摘要)
    查('打包了 4 件、2 格', r.get('发了') == 4 and r.get('格') == 2, r)
print(f'\n{"全过" if not 错 else f"{len(错)} 条没过"}')
sys.exit(1 if 错 else 0)
