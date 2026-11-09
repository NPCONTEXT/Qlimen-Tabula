# -*- coding: utf-8 -*-
# 页面测试照固定样本跑，不碰正在用的数据：样本在 工具/测施工区-样本/（导演台/ 是分镜施工区的合成存档：62 镜、长角色名 3 个、
# 等挑的样图 1 批、样片 3 批、V1 有意见；数据/ 里没有灯；工作区/ 只有那个分镜任务）。
# 搭 /tmp/ban-hp：数据、导演台（存档）、工作区（仓库自带的演示工作区 + 分镜任务）、板.py 的副本；先删掉旧的。
# 跑法：/usr/bin/python3 工具/测施工区-备环境.py，再照打印的命令起测试服务，再跑页面测试（写法在各测试开头；一条命令跑完用 工具/跑页面测试.py）
import os, shutil, time
这 = os.path.dirname(os.path.abspath(__file__))
样 = os.path.join(这, '测施工区-样本')
hp = '/tmp/ban-hp'
shutil.rmtree(hp, ignore_errors=True)
shutil.copytree(os.path.join(样, '数据'), os.path.join(hp, '数据'))
shutil.copytree(os.path.join(样, '导演台'), os.path.join(hp, '导演台'))
shutil.copytree(os.path.join(os.path.dirname(这), '示例', '演示工作区'), os.path.join(hp, '工作区'), ignore=shutil.ignore_patterns('施工台'))
shutil.copytree(os.path.join(样, '工作区'), os.path.join(hp, '工作区'), dirs_exist_ok=True)
# 复制出来的 TODO 修改时间都一样，看板会当成一次批量整理、全算休眠：照 板.py 演示 的办法错开（最近的 10 分钟前，往后每份早 5 小时）
现 = time.time()
for i, (dp, _, fs) in enumerate(sorted((d, n, f) for d, n, f in os.walk(os.path.join(hp, '工作区')) if 'TODO.md' in f)):
    os.utime(os.path.join(dp, 'TODO.md'), (现 - 600 - i * 5 * 3600,) * 2)
os.makedirs(os.path.join(hp, '工具'))
shutil.copyfile(os.path.join(这, '板.py'), os.path.join(hp, '工具', '板.py'))
open(os.path.join(hp, '账本.csv'), 'w').close()
print('搭好了 /tmp/ban-hp。起测试服务：')
print('BAN_ROOT=/tmp/ban-hp/工作区 BAN_DATA=/tmp/ban-hp/数据 DYT_DIR=/tmp/ban-hp/导演台 BAN_LEDGER=/tmp/ban-hp/账本.csv BAN_OPEN=/bin/echo /usr/bin/python3 ' + os.path.join(这, '板.py') + ' 服务 8771')
