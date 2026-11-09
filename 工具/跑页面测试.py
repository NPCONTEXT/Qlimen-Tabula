# -*- coding: utf-8 -*-
# 四个页面测试（测施工区、测底行、测名牌层、测拖）一条命令跑完，换 板.py、页面前后都跑。要装 node 和 Google Chrome（无头模式）。
# 用法：/usr/bin/python3 工具/跑页面测试.py [板.py] [页面模板] [只跑哪几个，逗号分开]
#   默认用本目录的 板.py 和 板-页面.txt。测试服务开在 8771，都用固定样本：每个测试前 测施工区-备环境.py 重搭 /tmp/ban-hp
#   （演示工作区 + 分镜样本 + 空数据；测拖先清空 布局.json）；跑完停服务、删副本。不碰正在用的 8770 和你的数据。
import json
import os
import shutil
import socket
import subprocess
import sys
import time

这 = os.path.dirname(os.path.abspath(__file__))
板 = sys.argv[1] if len(sys.argv) > 1 and sys.argv[1] else os.path.join(这, '板.py')
页 = sys.argv[2] if len(sys.argv) > 2 and sys.argv[2] else os.path.join(这, '板-页面.txt')
只 = set(sys.argv[3].split(',')) if len(sys.argv) > 3 and sys.argv[3] else None
库 = os.path.dirname(这)
端口 = 8771


def 等端口(开):
    for _ in range(100):
        try:
            socket.create_connection(('127.0.0.1', 端口), timeout=0.2).close()
            if 开:
                return True
        except OSError:
            if not 开:
                return True
        time.sleep(0.1)
    return False


def 跑(名, 数据, 台, 脚本, 尺寸):
    账 = os.path.join(os.path.dirname(数据), '账本.csv')
    open(账, 'a').close()
    env = dict(os.environ, BAN_DATA=数据, DYT_DIR=台, BAN_LEDGER=账, BAN_OPEN='/bin/echo', BAN_TEMPLATE=页, BAN_ROOT='/tmp/ban-hp/工作区')
    for k in ('BAN_CODEX', 'BAN_EXTRA', 'BAN_SGT', 'BAN_SETTINGS'):
        env.pop(k, None)
    if not 等端口(False):
        return 名, None, ['8771 被占着']
    服 = subprocess.Popen(['/usr/bin/python3', 板, '服务', str(端口)], env=env, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
    try:
        if not 等端口(True):
            return 名, None, ['服务没起来：' + (服.stderr.read() if 服.poll() is not None else '')[-300:]]
        r = subprocess.run(['node', os.path.join(这, '测页面.mjs'), f'http://127.0.0.1:{端口}/', os.path.join(这, 脚本), '', 尺寸],
                           env=dict(os.environ, BAN_NATIVE='1', BAN_REPO=库), capture_output=True, text=True, timeout=240)
        try:
            d = json.loads(r.stdout[r.stdout.index('{'):])
        except ValueError:
            return 名, None, ['读不出结果：' + r.stdout[-300:] + r.stderr[-300:]]
        res = d.get('结果') or {}
        if isinstance(res, str):   # 测拖 返回一段字：一行一条 ✅ / ❌，最后一行「全过」或「有没过的」
            行 = [x for x in res.split('\n') if x.strip()]
            条 = [x for x in 行 if x.startswith(('✅', '❌'))]
            败 = [x for x in 条 if x.startswith('❌')] + ([] if 行 and 行[-1] == '全过' else ['最后一行不是「全过」'])
            return 名, len(条) - len([x for x in 条 if x.startswith('❌')]), 败 + [f'页面报错：{e}' for e in d.get('错') or []]
        return 名, res.get('过'), list(res.get('败') or []) + [f'页面报错：{e}' for e in d.get('错') or []]
    finally:
        服.terminate()
        服.wait(timeout=10)
        等端口(False)


结果 = []
for 名, 尺寸 in (('测施工区', '1312x764'), ('测底行', '1312x764'), ('测名牌层', '416x400'), ('测拖', '680x1700')):
    if 只 and 名 not in 只:
        continue
    subprocess.run(['/usr/bin/python3', os.path.join(这, '测施工区-备环境.py')], check=True, capture_output=True)
    if 名 == '测拖':
        open('/tmp/ban-hp/数据/布局.json', 'w').write('{}')
    if 名 == '测名牌层':   # 第 1 层要有在干、等你的行：亮三盏（一盏跨区）
        灯env = dict(os.environ, BAN_ROOT='/tmp/ban-hp/工作区', BAN_DATA='/tmp/ban-hp/数据', DYT_DIR='/tmp/ban-hp/导演台', BAN_LEDGER='/tmp/ban-hp/账本.csv')
        for a in (['开工', '写作/长篇小说', '--谁', 'Claude', '--说', '测试：写第 14 章', '--会话', 'local_t1', '--接入', 'claude'],
                  ['开工', '开发/记账小程序', '--谁', 'Codex', '--说', '测试', '--会话', 't2', '--接入', 'codex'],
                  ['等你', '开发/记账小程序', '--谁', 'Codex', '--说', '测试：等你选', '--会话', 't2', '--接入', 'codex'],
                  ['开工', '研究/竞品调研', '--谁', 'Claude', '--说', '跨区施工（从 长篇小说 过来）', '--会话', 'local_t1', '--接入', 'claude']):
            subprocess.run(['/usr/bin/python3', 板, *a], env=灯env, capture_output=True, text=True)
    结果.append(跑(名, '/tmp/ban-hp/数据', '/tmp/ban-hp/导演台', 名 + '.js', 尺寸))
shutil.rmtree('/tmp/ban-hp', ignore_errors=True)
全过 = True
for 名, 过, 败 in 结果:
    print(f'{名}：过 {过}，败 {len(败)}' + ('' if not 败 else '：' + ' ｜ '.join(str(x)[:120] for x in 败[:6])))
    全过 = 全过 and 过 is not None and not 败
print('四个页面测试全过' if 全过 else '有没过的', f'（板.py：{板}；页面：{页}）')
sys.exit(0 if 全过 else 1)
