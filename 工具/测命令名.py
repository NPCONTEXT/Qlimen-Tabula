#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""命令名和状态词一样的离线测试（卷二 7.20、卷四 6.24，11-05）：等你 = 交付；收工 = 完工、灭灯；施工 = 开工；
老插件带 --会话 敲的收工照旧当交付；开工带 --要你（回复写了等你、后台还在跑）记进灯里、照旧在干、不当成格子。
临时目录造任务，真跑 板.py 的命令，看写进开关记录的是什么，不碰真数据。
跑法：/usr/bin/python3 工具/测命令名.py [板.py 路径]"""
import importlib.util, json, os, subprocess, sys, tempfile

板路 = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), '板.py')
错 = []


def 查(名, 过, 细=''):
    print(('✅ ' if 过 else '❌ ') + 名 + ('' if 过 else '  ' + str(细)))
    if not 过:
        错.append(名)


头 = '编号 | 步骤 | 产出物 | 预计耗时 | 依赖/阻塞\n---|---|---|---|---\n'
with tempfile.TemporaryDirectory() as 根, tempfile.TemporaryDirectory() as 数:
    os.makedirs(os.path.join(根, '组', '甲'))
    open(os.path.join(根, '组', '甲', 'TODO.md'), 'w', encoding='utf-8').write('# 甲 · TODO\n\n## 卷一（11-05 · 在做）\n\n' + 头 + '1 | [自动] 做 | — | — | —\n')
    open(os.path.join(数, '账本.csv'), 'w').close()
    环境 = dict(os.environ, BAN_ROOT=根, BAN_DATA=数, BAN_LEDGER=os.path.join(数, '账本.csv'), DYT_DIR=os.path.join(数, '导演台'),
              BAN_OPEN='/bin/echo', BAN_SESSION='local_测试', BAN_HARNESS='claude')
    记录 = os.path.join(数, '开关.jsonl')

    def 敲(*参):
        r = subprocess.run(['/usr/bin/python3', 板路, *参], env=环境, capture_output=True, text=True)
        行们 = [json.loads(l) for l in open(记录, encoding='utf-8')] if os.path.exists(记录) else []
        return (行们[-1] if 行们 else {}), r

    e, _ = 敲('施工', '组/甲', '--说', '做')
    查('施工 = 开工：开灯', e.get('开') is True and e.get('说') == '做', e)
    e, _ = 敲('等你', '组/甲', '--说', '交付了')
    查('等你 = 交付：灭了动效、挂等你', e.get('开') is False and e.get('等你') is True and e.get('说') == '交付了', e)
    e, r = 敲('收工', '组/甲')
    查('收工 = 完工：灭灯（不挂等你）', e.get('开') is False and not e.get('等你'), (e, r.stdout[-80:]))
    敲('开工', '组/甲', '--说', '再做')
    e, _ = 敲('收工', '组/甲', '--会话', 'local_老会话', '--接入', 'claude')
    查('老插件带 --会话 敲的收工：照旧当交付', e.get('开') is False and e.get('等你') is True and e.get('会话') == 'local_老会话', e)
    e, _ = 敲('完工', '组/甲')
    查('完工照旧灭灯', e.get('开') is False and not e.get('等你'), e)
    e, _ = 敲('开工', '组/甲', '--说', '后台在跑', '--租', '120', '--要你')
    查('开工带 --要你：记进去，不当成格子', e.get('开') is True and e.get('要你') is True and e.get('格子') == [] and e.get('租') == 7200, e)
    e2, _ = 敲('开工', '组/甲', '--说', '接着干')
    查('不带 --要你的开工：没有这个标', not e2.get('要你'), e2)
    敲('开工', '组/甲', '--说', '后台在跑', '--租', '120', '--要你')
    os.environ.update({k: v for k, v in 环境.items() if k.startswith(('BAN_', 'DYT_'))})
    sp = importlib.util.spec_from_file_location('板', 板路)
    板 = importlib.util.module_from_spec(sp)
    sp.loader.exec_module(板)
    灯 = [l for l in 板.灯们().get('组/甲', []) if l.get('会话') == 'local_测试']   # 老会话那盏（上面兼容收工挂的等你）不看
    查('看板读到的灯：在干、带「要你」', len(灯) == 1 and 灯[0]['态'] == '干' and 灯[0].get('要你') is True, 灯)
print(f'\n{"全过" if not 错 else f"{len(错)} 条没过"}')
sys.exit(1 if 错 else 0)
