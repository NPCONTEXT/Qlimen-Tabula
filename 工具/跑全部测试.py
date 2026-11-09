#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""一条命令跑全部测试：读 TODO 的标准答案、11 个 python 测试、4 个页面测试、Claude 插件测试。都不花钱、不联网、不碰你的数据。
跑法：/usr/bin/python3 工具/跑全部测试.py [--不跑页面] [--不跑插件]
- 页面测试要装 node 和 Google Chrome，测试服务开在 8771（被占着就跳过）。
- 插件测试要 Claude Code 自带的 claude 命令：在 Claude Code 会话里跑会用环境变量 CLAUDE_CODE_EXECPATH；终端里有 claude 命令也行；都没有就跳过。"""
import os
import shutil
import subprocess
import sys

这 = os.path.dirname(os.path.abspath(__file__))
库 = os.path.dirname(这)
板 = os.path.join(这, '板.py')
python测试 = ['测读法', '测对账', '测零活', '测收工核对', '测多名牌', '测命令名', '测待续', '测Codex', '测叫醒摘要', '测小说区', '测设置']
结果 = []


def 记(名, 过, 话=''):
    结果.append((名, 过, 话))
    print(('✅ ' if 过 else ('⏭ ' if 过 is None else '❌ ')) + 名 + (f'：{话}' if 话 else ''), flush=True)


env = {k: v for k, v in os.environ.items() if not k.startswith('BAN_')}
r = subprocess.run(['/usr/bin/python3', 板, '对标准'], capture_output=True, text=True, env=dict(env, BAN_DATA='/tmp/ban-对标准'))
记('读 TODO 的标准答案（演示工作区 8 份）', r.returncode == 0, r.stdout.strip().splitlines()[-1] if r.stdout.strip() else r.stderr[-200:])
shutil.rmtree('/tmp/ban-对标准', ignore_errors=True)
for t in python测试:
    r = subprocess.run(['/usr/bin/python3', os.path.join(这, t + '.py'), 板], capture_output=True, text=True, env=env, timeout=600)
    行 = r.stdout.strip().splitlines()
    记(t, r.returncode == 0, f'✅ {r.stdout.count("✅")} 条' + ('' if r.returncode == 0 else '；' + (行[-1] if 行 else r.stderr[-200:])))
if '--不跑页面' in sys.argv:
    记('页面测试', None, '照参数跳过')
elif not shutil.which('node') or not os.path.exists('/Applications/Google Chrome.app'):
    记('页面测试', None, '没装 node 或 Google Chrome，跳过')
else:
    r = subprocess.run(['/usr/bin/python3', os.path.join(这, '跑页面测试.py')], capture_output=True, text=True, env=env, timeout=1200)
    行 = r.stdout.strip().splitlines()
    记('页面测试（4 个）', r.returncode == 0, '；'.join(行[-5:-1]) if 行 else r.stderr[-200:])
if '--不跑插件' in sys.argv:
    记('Claude 插件测试', None, '照参数跳过')
else:
    claude = os.environ.get('CLAUDE_CODE_EXECPATH') or shutil.which('claude')
    if not claude:
        记('Claude 插件测试', None, '找不到 claude 命令，跳过')
    else:
        r = subprocess.run([claude, 'plugin', 'test', os.path.join(库, '插件', 'ban-listen')], capture_output=True, text=True, timeout=600, cwd='/tmp')
        尾 = [x.strip() for x in (r.stdout + r.stderr).splitlines() if x.strip().endswith(('pass', 'fail'))]
        记('Claude 插件测试', r.returncode == 0, ' · '.join(尾[-2:]))
坏 = [x for x in 结果 if x[1] is False]
跳 = [x for x in 结果 if x[1] is None]
print(f'\n{len(结果) - len(坏) - len(跳)} 组过、{len(坏)} 组没过、{len(跳)} 组跳过')
sys.exit(1 if 坏 else 0)
