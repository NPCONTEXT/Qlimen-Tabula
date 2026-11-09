# -*- coding: utf-8 -*-
# 分卷五 8.4（8.9 加了边界）：新建一个小说施工区，不装导演台、不改公共代码，看板认得出、画得出（竖排），网页里改格、批注，Claude 那边列、改，看板标验收，叫醒能投信。
# 用法：/usr/bin/python3 工具/测小说区.py [板.py] [页面] [截图放哪]
# 全在 /tmp/sgt-xs 里：假的工作区（只有 创作/小说样例 一个任务，没有 MV、没有导演台.py）、假的看板数据；测试服务开在 8771。
import hashlib
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
出 = sys.argv[3] if len(sys.argv) > 3 else '/tmp/ban小说区'
引擎 = os.path.join(os.path.dirname(板), '施工台.py')
临 = '/tmp/sgt-xs'
根 = os.path.join(临, 'root')
任务 = os.path.join(根, '创作', '小说样例')
台 = os.path.join(任务, '施工台')
数 = os.path.join(临, '数据')
端口 = 8771
过, 败 = [], []


def 验(名, ok, 细=''):
    (过 if ok else 败).append(名 + ('' if ok else '：' + str(细)[:300]))
    print(('✅ ' if ok else '❌ ') + 名 + ('' if ok else '：' + str(细)[:300]), flush=True)


def 指纹():
    d = os.path.dirname(板)
    return {f: hashlib.md5(open(os.path.join(d, f), 'rb').read()).hexdigest() for f in ('板.py', '施工台.py', os.path.basename(页)) if os.path.exists(os.path.join(d, f))} | \
        {'页面': hashlib.md5(open(页, 'rb').read()).hexdigest()}


env = dict(os.environ, BAN_ROOT=根, BAN_DATA=数, BAN_LEDGER=os.path.join(临, '账本.csv'), BAN_OPEN='/bin/echo', BAN_TEMPLATE=页)
for k in ('BAN_CODEX', 'BAN_EXTRA', 'BAN_SGT', 'DYT_DIR'):
    env.pop(k, None)


def 跑(*a):
    r = subprocess.run(['/usr/bin/python3', *a], env=env, capture_output=True, text=True, timeout=60)
    return r.returncode, r.stdout + r.stderr


shutil.rmtree(临, ignore_errors=True)
shutil.rmtree(出, ignore_errors=True)
os.makedirs(出)
os.makedirs(任务)
os.makedirs(数)
open(os.path.join(临, '账本.csv'), 'w').close()
open(os.path.join(任务, 'TODO.md'), 'w', encoding='utf-8').write('# 小说样例 · TODO\n\n## 第一轮（11-07 · 在做）\n\n编号 | 步骤 | 产出物 | 预计耗时 | 依赖/阻塞\n---|---|---|---|---\n1 | [自动] 写第一卷 | 正文 | 约 30 分钟 | —\n')
前 = 指纹()
验('工作区里没有导演台.py', not any('导演台' in f for d, _, fs in os.walk(根) for f in fs))

# ---- 新建、加章 ----
码, 话 = 跑(板, '区', '新建', '创作/小说样例', '--模板', '小说', '--号', 'xs', '--段', '第一卷,第二卷')
验('板.py 区 新建 成功', 码 == 0 and '建好了' in 话, 话)
验('任务目录里有 施工台/区域.json 和空存档', os.path.exists(os.path.join(台, '区域.json')) and os.path.exists(os.path.join(台, '状态.json')))
登 = json.load(open(os.path.join(数, '施工区登记.json'), encoding='utf-8'))
验('看板登记加了一行 xs', 登['区们'].get('xs', {}).get('任务') == '创作/小说样例', 登)
长 = '他推开门，雨从屋檐上斜着落下来。' * 30
for 号, 段, 字 in (('1', '第一卷', ['标题=重逢', '状态=定稿', '梗概=两人在雨夜的旧书店重逢，谁都没先开口。', '正文=' + 长, '字数=3200']),
                  ('2', '第一卷', ['标题=旧账', '状态=待改', '梗概=翻出十年前那张欠条，才知道当年是谁替他还的债。', '正文=（还没写）', '备注=节奏偏慢，第二场可以删']),
                  ('3', '第一卷', ['标题=夜车', '状态=草稿', '梗概=夜车上的对话，交代女主为什么离开。']),
                  ('4', '第二卷', ['标题=回城', '梗概=第二卷开头，三年后。'])):
    码, 话 = 跑(引擎, 台, '加', 号, 段, *字)
    验(f'施工台.py 加第 {号} 章', 码 == 0, 话)
码, 话 = 跑(引擎, 台, '加', '9', '第一卷', '不存在的字段=x')
验('加不认识的字段会拦下', 码 != 0 and '不能改' in 话, 话)
验('建区、加章以后公共代码指纹没变', 指纹() == 前, (前, 指纹()))


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


def 页面(名, js, 尺寸='1312x764'):
    f = os.path.join(出, 名 + '.js')
    open(f, 'w', encoding='utf-8').write("window.webkit={messageHandlers:{ban:{postMessage:()=>{}}}};for(let k=0;k<40&&!(window.DATA&&DATA.任务);k++)await wait(250);" + js)
    r = subprocess.run(['node', os.path.join(这, '测页面.mjs'), f'http://127.0.0.1:{端口}/', f, os.path.join(出, 名 + '.png'), 尺寸],
                       env=dict(os.environ, BAN_NATIVE='1'), capture_output=True, text=True, timeout=120)
    try:
        return json.loads(r.stdout[r.stdout.index('{'):])
    except ValueError:
        return {'错': ['读不出：' + r.stdout[-200:] + r.stderr[-200:]]}


def 取(路):
    import urllib.request
    import urllib.parse
    with urllib.request.urlopen(f'http://127.0.0.1:{端口}' + urllib.parse.quote(路), timeout=10) as r:
        return json.loads(r.read())


def 存(路, 体):
    import urllib.request
    import urllib.parse
    q = urllib.request.Request(f'http://127.0.0.1:{端口}' + urllib.parse.quote(路), data=json.dumps(体, ensure_ascii=False).encode('utf-8'),
                               headers={'X-Ban': '1', 'Content-Type': 'application/json'})
    with urllib.request.urlopen(q, timeout=10) as r:
        return json.loads(r.read())


assert 等端口(False), '8771 被占着'
服 = subprocess.Popen(['/usr/bin/python3', 板, '服务', str(端口)], env=env, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
try:
    assert 等端口(True), '服务没起来'
    d = 取('/api/看板')
    t = next((x for x in d['任务'] if x['键'] == '创作/小说样例'), None)
    验('看板认出这个任务有施工区 xs', bool(t) and t.get('施工区') == 'xs', t and t.get('施工区'))
    验('看板数据带着 xs 的配置（竖排、条目叫章）', d.get('施工区们', {}).get('xs', {}).get('配', {}).get('排') == '竖', d.get('施工区们'))
    st = 取('/api/施工区/xs')
    验('施工区存档取得到：4 章、2 段', len(st.get('章', [])) == 4 and len(st.get('段', [])) == 2, (len(st.get('章', [])), st.get('段')))

    # 第 3 层：竖排画出来
    r = 页面('1-第3层竖排', "去层(3,true);await wait(1500);const 格们=[...document.querySelectorAll('.wa .hc')];const 头=document.querySelector('.wa .hlab.v');"
                      "return {区号,竖,格:格们.length,头:!!头,段:[...document.querySelectorAll('.wa .hseg.v')].map(x=>x.textContent),"
                      "章1:(document.querySelector('.wa [data-cell=\"1|章\"]')||{}).textContent||'',状态1:(document.querySelector('.wa [data-cell=\"1|状态\"]')||{}).className||'',"
                      "同列:(()=>{const a=document.querySelector('.wa [data-cell=\"1|梗概\"]'),b=document.querySelector('.wa [data-cell=\"2|梗概\"]');return a&&b?[a.offsetLeft==b.offsetLeft,b.offsetTop-a.offsetTop]:null;})()};")
    x = r.get('结果') or {}
    验('第 3 层画的是 xs、竖排', x.get('区号') == 'xs' and x.get('竖') is True, x)
    验('4 章 × 6 列 = 24 格，字段名那一行在顶上（.hlab.v）', x.get('格') == 24 and x.get('头'), x)
    验('段名竖着写在最左一列：第一卷 3 章、第二卷 1 章', x.get('段') == ['第一卷3 章', '第二卷1 章'], x.get('段'))
    验('第 1 章头一格写章号和标题', x.get('章1', '').startswith('1重逢'), x.get('章1'))
    验('状态「定稿」按配置标成完成色', ' d' in (' ' + x.get('状态1', '')), x.get('状态1'))
    验('同一字段一列：第 1、2 章的梗概上下对齐、差 3 格高（96 像素）', x.get('同列') == [True, 96], x.get('同列'))
    验('页面没报错', not r.get('错'), r.get('错'))

    # 网页里改格（就地改）、批注（详情页写意见）
    r = 页面('2-改格批注', "去层(3,true);await wait(1500);const c=document.querySelector('.wa [data-cell=\"3|梗概\"]');c.dispatchEvent(new MouseEvent('click',{bubbles:true}));await wait(300);"
                      "const ta=document.querySelector('.hin textarea');ta.value='夜车上的对话改了：她没说为什么离开。';ta.dispatchEvent(new Event('input',{bubbles:true}));await 关编辑(true);await wait(500);"
                      "document.querySelector('.wa [data-cell=\"2|章\"]').dispatchEvent(new MouseEvent('click',{bubbles:true}));await wait(500);"
                      "const n=document.getElementById('zqNote');n.value='第二场删掉，直接跳到欠条。';document.querySelector('[data-zqnote]').dispatchEvent(new MouseEvent('click',{bubbles:true}));await wait(800);"
                      "return {标题:(document.querySelector('#side h3')||{}).textContent,编号:(document.querySelector('#side .meta')||{}).textContent,底:(document.querySelector('#side .ft')||{}).textContent};")
    x = r.get('结果') or {}
    st = 取('/api/施工区/xs')
    章 = {j['号']: j for j in st['章']}
    验('就地改的梗概存进了存档', 章['3']['梗概'] == '夜车上的对话改了：她没说为什么离开。', 章['3']['梗概'])
    验('详情页写的意见存进了第 2 章', any(y['文'] == '第二场删掉，直接跳到欠条。' and y['谁'] == '用户' for y in 章['2']['意见']), 章['2']['意见'])
    验('详情页标题、编号按小说的叫法', x.get('标题', '').startswith('2 · 旧账') and '小说·2·大纲' in x.get('编号', ''), x)
    验('详情页底下一行列的是小说的字段', x.get('底', '').startswith('章、状态、字数、梗概、正文、备注'), x.get('底'))
    验('页面没报错（改格批注）', not r.get('错'), r.get('错'))

    # 叫醒：没发的改动打包投进这个任务的信箱
    d = 取('/api/看板')
    t = next(x for x in d['任务'] if x['键'] == '创作/小说样例')
    态 = t.get('施工区态') or {}
    验('看板算出 2 格改了、没发', 态.get('未发格') == 2 and 态.get('格', {}).get('3:梗概') == '改了', 态)
    r2 = 存('/api/施工区/xs/叫醒', {})
    箱 = os.path.join(数, '信箱', '待领.jsonl')
    摘要 = json.loads(open(箱, encoding='utf-8').read().strip().split('\n')[-1])['摘要'] if os.path.exists(箱) else ''
    验('叫醒投了信，摘要开头是「小说 施工区」', r2.get('发了') == 2 and 摘要.startswith('小说 施工区：用户改了 2 格'), (r2, 摘要[:80]))
    验('摘要里写了改的哪格、意见', '3·梗概：改了「梗概」' in 摘要 and '2：意见「第二场删掉' in 摘要, 摘要)

    # Claude 那边：列（读到了）、改（这格改好了）→ 看板标验收；用户点知道了 → 框消失
    码, 话 = 跑(引擎, 台, '列')
    验('施工台.py 列 列出用户的改动和意见', 码 == 0 and '意见' in 话 and '【2】' in 话, 话)
    码, 话 = 跑(引擎, 台, '改', '3', '梗概', '夜车上的对话：她只说了一句「票是你买的」。')
    验('施工台.py 改 成功', 码 == 0, 话)
    d = 取('/api/看板')
    t = next(x for x in d['任务'] if x['键'] == '创作/小说样例')
    验('Claude 改过的那格标成验收', (t.get('施工区态') or {}).get('格', {}).get('3:梗概') == '验收', t.get('施工区态'))
    r = 页面('3-验收', "去层(3,true);await wait(1500);const 牌=[...document.querySelectorAll('.wa .claim .ctag')].map(x=>x.textContent);return {牌};")
    验('第 3 层那格挂着「验收」名牌', '验收' in ((r.get('结果') or {}).get('牌') or []), r.get('结果'))
    存('/api/施工区/xs/验收', {'格': '3:梗概'})
    d = 取('/api/看板')
    t = next(x for x in d['任务'] if x['键'] == '创作/小说样例')
    验('用户点了知道了，那格的状态没了', '3:梗概' not in (t.get('施工区态') or {}).get('格', {}), t.get('施工区态'))

    # 8.9 边界（用户 11-07 定甲）：新建时照模板算好写进登记；区域.json 多加一行超了，看板只画到边界、顶上写出来，板.py 列 提醒会话
    登 = json.load(open(os.path.join(数, '施工区登记.json'), encoding='utf-8'))
    验('新建时照模板算好边界写进登记：18 格（段名 1 + 章 2 + 状态 1 + 字数 1 + 梗概 4 + 正文 6 + 备注 3）', 登['区们']['xs'].get('边界') == {'字段格': 18}, 登['区们']['xs'])
    配 = json.load(open(os.path.join(台, '区域.json'), encoding='utf-8'))
    配['行'].append({'名': '附记', '高': 2, '类': '文字', '字段': ['备注']})
    open(os.path.join(台, '区域.json'), 'w', encoding='utf-8').write(json.dumps(配, ensure_ascii=False, indent=1))
    r = 页面('4-超界', "去层(3,true);await wait(1500);return {格:document.querySelectorAll('.wa .hc').length,附记:!!document.querySelector('.wa [data-cell=\"1|附记\"]'),顶:(document.getElementById('qut')||{}).textContent||'',超:区超界,看得见:(()=>{const q=document.getElementById('qut');if(!q)return false;const r=q.getBoundingClientRect(),e=document.elementFromPoint(r.left+6,r.top+r.height/2);return !!e&&q.contains(e);})(),红:!!document.querySelector('#qut .cj')};")
    x = r.get('结果') or {}
    验('区域.json 多加一行超出边界：看板只画到边界（还是 24 格，没有「附记」）', x.get('格') == 24 and not x.get('附记'), x)
    验('顶上那行写「超出区域，没画：附记（要你批）」，标红，没被冻结的字段名那行盖住', '超出区域，没画：附记（要你批）' in x.get('顶', '') and x.get('红') and x.get('看得见'), x)
    码, 话 = 跑(板, '列')
    验('板.py 列 提醒会话：超出边界、要找用户批', '超出登记的边界 18 格：附记 没画' in 话, 话[-300:])
    码, 话 = 跑(板, '区', '列')
    验('板.py 区 列 写出边界和超界', 'xs：创作/小说样例' in 话 and '边界 18 格' in 话 and '附记 没画' in 话, 话)
finally:
    服.terminate()
    服.wait(timeout=10)
验('整个过程公共代码指纹没变', 指纹() == 前, (前, 指纹()))
print(f'\n过 {len(过)}，败 {len(败)}；截图在 {出}；测试目录 {临} 留着看，下次跑会重建')
sys.exit(1 if 败 else 0)
