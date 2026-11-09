# -*- coding: utf-8 -*-
# 分卷五 8.3：页面改成照配置画以后，MV 施工区改前改后逐像素一样。同一份固定样本、同一个 板.py，先用改前的页面截一组、再用改后的截一组，逐张比。
# 用法：/usr/bin/python3 工具/测施工区截图对照.py 改前页面 改后页面 [板.py] [截图放哪]
# 场景：第 3 层刚进来、往右滑到主歌、点镜号开详情、点样图格开详情、点画面就地改、点候选看大图、第 1 层、第 2 层（总览）。
# 底下一行有「更新于 几点几分」，比的时候盖掉最下面 30 像素；右栏开着的场景再盖掉右栏标题那一行（粘在顶上的标题、「收起」字的抗锯齿本来就不稳：
# 11-07 改前的页面自己连截三轮，两轮这一行有几百个像素不同，改后的页面也一样，和这次改动无关）。改坏验法：把 MV 区域.json 里「对应内容」的 括 删掉，或把某一行的 高 改了，要红。
import os
import shutil
import socket
import subprocess
import sys
import time

from PIL import Image, ImageChops

这 = os.path.dirname(os.path.abspath(__file__))
前, 后 = sys.argv[1], sys.argv[2]
板 = sys.argv[3] if len(sys.argv) > 3 and sys.argv[3] else os.path.join(这, '板.py')
出 = sys.argv[4] if len(sys.argv) > 4 else '/tmp/ban截图对照'
端口 = 8771
头 = "window.webkit={messageHandlers:{ban:{postMessage:()=>{}}}};for(let k=0;k<40&&!(window.DATA&&DATA.任务);k++)await wait(250);"
进三 = "去层(3,true);await wait(1500);"
格 = "const 格=s=>document.querySelector('.wa [data-cell=\"'+s+'\"]');"
场景 = {
    '1-进第3层': 进三,
    '2-滑到主歌': 进三 + "cam.x+=6*横镜格*CW;applyCam();await wait(800);",
    '3-镜号详情': 进三 + 格 + "格('V3|镜号').dispatchEvent(new MouseEvent('click',{bubbles:true}));await wait(800);",
    '4-样图详情': 进三 + 格 + "格('V2|样图').dispatchEvent(new MouseEvent('click',{bubbles:true}));await wait(800);",
    '5-就地改': 进三 + 格 + "格('V3|画面').dispatchEvent(new MouseEvent('click',{bubbles:true}));await wait(500);",
    '6-看大图': 进三 + "const h=document.querySelector('.wa [data-hpv]');h&&h.dispatchEvent(new MouseEvent('click',{bubbles:true}));await wait(800);",
    '7-第1层': "去层(1,true);await wait(1200);",
    '8-总览': "去层(2,true);await wait(1200);",
}


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


def 截一组(页, 名):
    subprocess.run(['/usr/bin/python3', os.path.join(这, '测施工区-备环境.py')], check=True, capture_output=True)
    env = dict(os.environ, BAN_DATA='/tmp/ban-hp/数据', DYT_DIR='/tmp/ban-hp/导演台', BAN_LEDGER='/tmp/ban-hp/账本.csv', BAN_OPEN='/bin/echo', BAN_TEMPLATE=页)
    for k in ('BAN_CODEX', 'BAN_EXTRA', 'BAN_ROOT', 'BAN_SGT'):
        env.pop(k, None)
    assert 等端口(False), '8771 被占着'
    服 = subprocess.Popen(['/usr/bin/python3', 板, '服务', str(端口)], env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    错 = []
    try:
        assert 等端口(True), '服务没起来'
        for k, js in 场景.items():
            f = os.path.join(出, f'{名}-{k}.js')
            open(f, 'w', encoding='utf-8').write(头 + js + "return {ok:1};")
            r = subprocess.run(['node', os.path.join(这, '测页面.mjs'), f'http://127.0.0.1:{端口}/', f, os.path.join(出, f'{名}-{k}.png'), '1312x764'],
                               env=dict(os.environ, BAN_NATIVE='1'), capture_output=True, text=True, timeout=120)
            if '"错": []' not in r.stdout:
                错.append(f'{k}：' + r.stdout[-300:].replace('\n', ' '))
    finally:
        服.terminate()
        服.wait(timeout=10)
        等端口(False)
    return 错


shutil.rmtree(出, ignore_errors=True)
os.makedirs(出)
报错 = 截一组(前, '前') + 截一组(后, '后')
不同 = []
for k in 场景:
    a = Image.open(os.path.join(出, f'前-{k}.png')).convert('RGB')
    b = Image.open(os.path.join(出, f'后-{k}.png')).convert('RGB')
    if a.size != b.size:
        不同.append(f'{k}：尺寸不同 {a.size} {b.size}')
        continue
    w, h = a.size
    差 = ImageChops.difference(a.crop((0, 0, w, h - 30)), b.crop((0, 0, w, h - 30)))
    if '详情' in k:
        差.paste((0, 0, 0), (w - 360, 18, w, 50))   # 右栏标题那一行
    框 = 差.getbbox()
    if 框:
        不同.append(f'{k}：有像素不同，范围 {框}')
print('页面报错：', 报错 or '没有')
print('\n'.join(不同) if 不同 else f'{len(场景)} 个场景逐像素一样（最下面 30 像素的「更新于」不比）', f'；截图在 {出}')
sys.exit(1 if 不同 or 报错 else 0)
