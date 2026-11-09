#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""无限表格的施工台引擎（分卷五 8.1，11-07 从 MV 的导演台.py 抽出来，逻辑一行没改，只把写死的 MV 字段换成从配置读）。

一个施工区 = 一个存档目录（台）：状态.json（唯一的真相，加锁）、事件.jsonl、备份/、缓存.nosync/，加一份 区域.json：
条目叫什么（存档里条目列表的键也是它，MV 是「镜」）、能改的文字字段、改了要作废下一批的依据字段、候选的栏、话里怎么称呼。
引擎不认识任何一个区的字段；网页里的操作（改格、选、通过、意见、确认、重出……）和 Claude 用的命令（列、看、改、说、处理、批、出、交……）都在这里。
MV 的导演台.py 只剩一层壳（加上分镜表导入导出、它自己的旧网页服务），新建的施工区（比如小说）不用装它。

命令行（新区用；MV 照旧用 导演台.py，命令和输出都一样）：
  /usr/bin/python3 工具/施工台.py 存档目录 命令 …
  命令：新建 [段名…]、加 号 段名 [字段=值…]、列、看 号、改 号 字段 值、改多 文件.json、批 号 内容 模型 件数 额度:预计 提示词文件 [栏]、撤批 号 [强制]、接 号、出 号、
        交 号 [批N] 文件[@标签[@组]]…、花 额度 数 [号] [说明]、参考 号 文件 说明、说 号|留言 话 [挂的产出id]、处理 号|留言 号…、
        卡 号 原因、解卡 号、等 [静默秒] [最长秒] [最多挂几小时]、花费
  存档目录的上一层是这个区的项目目录（交、参考的文件要在里面）。"""
import fcntl
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import time
from datetime import datetime, timedelta
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, unquote, parse_qs

FFMPEG = shutil.which('ffmpeg') or '/opt/homebrew/bin/ffmpeg'   # 视频候选截缩略图用；没装 ffmpeg 就不截
叫醒 = {'交给', '确认', '选', '重出', '通过', '意见', '留言'}   # 11-01 起写意见、留言也叫醒（用户 10-31 碰到过只写意见叫不醒）
我的标签 = ('等我出', '在出', '等我改下一批', '等我接着做', '有新意见', '卡住')
类型表 = {'.png': 'image/png', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.webp': 'image/webp', '.gif': 'image/gif',
         '.mp4': 'video/mp4', '.mov': 'video/quicktime', '.webm': 'video/webm', '.md': 'text/plain; charset=utf-8',
         '.txt': 'text/plain; charset=utf-8', '.json': 'application/json; charset=utf-8', '.wav': 'audio/wav', '.mp3': 'audio/mpeg'}
视频后缀 = ('.mp4', '.mov', '.webm')


class 错(Exception):
    pass


class 冲突(Exception):
    def __init__(s, 话, 条=None):
        super().__init__(话)
        s.条 = 条


def 现在(秒=False):
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S' if 秒 else '%Y-%m-%d %H:%M')


def 解时(s):
    for f in ('%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M'):
        try:
            return datetime.strptime(s, f)
        except ValueError:
            pass
    raise ValueError(f'时间格式不对：{s}')


def 本期(规则, 此刻=None):
    此刻 = 此刻 or datetime.now()
    if 规则['类'] == '周':
        锚 = 解时(规则['锚'])
        止 = 锚 + ((此刻 - 锚) // timedelta(days=7) + 1) * timedelta(days=7)
        return 止 - timedelta(days=7), 止
    h, m = map(int, 规则['时'].split(':'))

    def 某月(y, mo):
        return datetime(y, mo, 规则['日'], h, m)
    c = 某月(此刻.year, 此刻.month)
    if 此刻 >= c:
        return c, 某月(此刻.year + (此刻.month == 12), 1 if 此刻.month == 12 else 此刻.month + 1)
    return 某月(此刻.year - (此刻.month == 1), 12 if 此刻.month == 1 else 此刻.month - 1), c


def 花费表(st):
    out = {}
    for 名, q in (st.get('期') or {}).items():
        起, 止 = 本期(q['规则'])
        已 = sum(x['数'] for x in st.get('花费', []) if x['额度'] == 名 and 起 <= 解时(x['时间']) < 止)
        out[名] = {'单位': q['单位'], '上限': q['上限'], '已花': round(已, 3),
                  '起': 起.strftime('%m-%d %H:%M'), '止': 止.strftime('%m-%d %H:%M')}
    return out


def 新号(列表):
    return max([x['号'] for x in 列表] + [0]) + 1


def 标签(j):
    if j.get('通过'):
        return ['通过']
    t = []
    if j.get('卡住'):
        t.append('卡住')
    nb = j.get('下一批')
    if nb:
        免 = (nb.get('预计') or {}).get('额度') == '无'   # 不花钱的批不用用户点头（11-01 用户批的改法）
        t.append('等我改下一批' if nb.get('依据改了') else '等我出' if (nb.get('确认') or 免) else '等你确认')
    if j.get('在出'):
        t.append('在出')
    if any(b.get('产出') and not b.get('结论') for b in j.get('批次', [])):
        t.append('等你验收')
    if any(b.get('结论') and not b.get('已接') for b in j.get('批次', [])):
        t.append('等我接着做')
    if any(y['谁'] == '用户' and y.get('处理') != '已处理' for y in j.get('意见', [])):
        t.append('有新意见')
    return t or ['草稿']


def 读配置(台):
    with open(os.path.join(台, '区域.json'), encoding='utf-8') as f:
        return json.load(f)


class _锁:
    def __init__(s, 台):
        s.台 = 台

    def __enter__(s):
        os.makedirs(s.台, exist_ok=True)
        s.f = open(os.path.join(s.台, '.锁'), 'w')
        fcntl.flock(s.f, fcntl.LOCK_EX)
        return s

    def __exit__(s, *a):
        fcntl.flock(s.f, fcntl.LOCK_UN)
        s.f.close()


class 区:
    """一个施工区。台 = 存档目录；根 = 项目目录（交、参考的文件要在里面，网页只给看它里面的文件）；配置默认读 台/区域.json。"""

    def __init__(s, 台, 根=None, 配置=None):
        s.台 = 台
        s.根 = os.path.realpath(根 or os.path.dirname(os.path.abspath(台)))
        s.配 = 配置 if 配置 is not None else 读配置(台)
        s.条目 = s.配['条目']                        # 条目叫什么，也是存档里条目列表的键（MV：镜）
        s.依据名 = s.配.get('依据名', '依据')          # 依据字段合起来叫什么（MV：分镜）
        s.台名 = s.配.get('台名', '施工台')            # 话里这个区的网页叫什么（MV：导演台）
        s.命令 = s.配.get('命令', '施工台.py')         # 话里叫 Claude 跑的命令（MV：导演台.py）
        s.根名 = s.配.get('根名', os.path.basename(s.根))
        s.文字段 = list(s.配['文字段'])
        s.依据段 = set(s.配.get('依据段', []))          # 改了这些，没出的下一批就要重写、确认作废
        s.栏们 = tuple(s.配.get('栏', []))              # 候选的栏（MV：图片、样片、成片），第一个是默认
        s.默认栏 = s.栏们[0] if s.栏们 else ''
        s.叫醒 = 叫醒
        s.我的标签 = 我的标签

    # ---------- 底子：锁、读写、备份、事件 ----------

    def 路(s, 名):
        return os.path.join(s.台, 名)

    def 锁(s):
        return _锁(s.台)

    def 读(s):
        p = s.路('状态.json')
        if not os.path.exists(p):
            return None
        with open(p, encoding='utf-8') as f:
            return json.load(f)

    def 备份(s):
        """每小时最多一份，留最新 48 份。在覆盖前调用，备的是上一版。"""
        p = s.路('状态.json')
        if not os.path.exists(p):
            return
        d = s.路('备份')
        os.makedirs(d, exist_ok=True)
        旧 = sorted(x for x in os.listdir(d) if x.startswith('状态-') and x.endswith('.json'))
        if 旧 and time.time() - os.path.getmtime(os.path.join(d, 旧[-1])) < 3600:
            return
        shutil.copyfile(p, os.path.join(d, f'状态-{datetime.now():%m%d-%H%M}.json'))
        旧 = sorted(x for x in os.listdir(d) if x.startswith('状态-') and x.endswith('.json'))
        for x in 旧[:-48]:
            os.remove(os.path.join(d, x))

    def 写(s, st):
        s.备份()
        st['改动号'] = st.get('改动号', 0) + 1
        缓 = s.路('缓存.nosync')
        os.makedirs(缓, exist_ok=True)
        tmp = os.path.join(缓, f'状态-{os.getpid()}.tmp')
        with open(tmp, 'w', encoding='utf-8') as f:
            json.dump(st, f, ensure_ascii=False, indent=1)
        os.replace(tmp, s.路('状态.json'))

    def 记事件(s, st, 谁, 做, **kw):
        st['事件号'] = st.get('事件号', 0) + 1
        e = {'号': st['事件号'], '时间': 现在(True), '谁': 谁, '做': 做}
        e.update(kw)
        with open(s.路('事件.jsonl'), 'a', encoding='utf-8') as f:
            f.write(json.dumps(e, ensure_ascii=False) + '\n')

    def 读事件(s, 起号=0):
        p = s.路('事件.jsonl')
        if not os.path.exists(p):
            return []
        out = []
        with open(p, encoding='utf-8') as f:
            for l in f:
                if l.strip():
                    e = json.loads(l)
                    if e['号'] > 起号:
                        out.append(e)
        return out

    # ---------- 条目、批次 ----------

    def 找条目(s, st, 号):
        for j in st[s.条目]:
            if j['号'] == 号:
                return j
        raise 错(f'没有{s.条目}号 {号}')

    @staticmethod
    def 找批(j, 号):
        for b in j.get('批次', []):
            if b['号'] == 号:
                return b
        raise 错(f'{j["号"]} 没有第 {号} 批')

    def 空条目(s, 号, 段):
        j = {'号': 号, '段': 段, '版': 1, '下一批': None, '批次': [], '参考': [], '意见': [],
             '在出': None, '卡住': None, '通过': None}
        for k in s.文字段:
            j[k] = ''
        return j

    def 带算(s, st):
        for j in st[s.条目]:
            j['_标签'] = 标签(j)
        st['_花费'] = 花费表(st)
        st['_现在'] = 现在()
        return st

    def 依据作废(s, j, 谁):
        """依据（这个区的依据字段）改了：没出的下一批要重写，确认过的作废。"""
        nb = j.get('下一批')
        if not nb:
            return
        if nb.get('确认'):
            nb['作废的确认'] = dict(nb['确认'], 作废于=现在(), 因为=f'{谁}改了{s.依据名}')
            nb['确认'] = None
        nb['依据改了'] = True

    def 安全路径(s, rel):
        full = os.path.realpath(os.path.join(s.根, rel))
        if not full.startswith(s.根 + os.sep):
            return None
        return full

    def 相对(s, 文件):
        full = os.path.realpath(文件 if os.path.isabs(文件) else os.path.join(os.getcwd(), 文件))
        if not os.path.exists(full):
            full2 = os.path.realpath(os.path.join(s.根, 文件))
            if os.path.exists(full2):
                full = full2
            else:
                raise 错(f'文件不存在：{文件}')
        if not full.startswith(s.根 + os.sep):
            raise 错(f'文件要在 {s.根名} 目录里：{文件}')
        return os.path.relpath(full, s.根)

    def _冲突(s, 话, 条):
        e = 冲突(话, 条)
        setattr(e, s.条目, 条)   # 老代码按条目名取（MV 的 x.镜）
        return e

    # ---------- 用户在网页里的操作 ----------

    def 用户操作(s, a):
        op = a.get('op')
        with s.锁():
            st = s.读()
            回 = None
            if op == '改格':
                j = s.找条目(st, a.get(s.条目))
                字 = a.get('字段')
                if 字 not in s.文字段:
                    raise 错(f'不能改「{字}」')
                if a.get('版') != j['版']:
                    raise s._冲突('这一行刚被改过', j)
                值 = str(a.get('值', ''))[:8000]
                if j.get(字, '') != 值:
                    j[字] = 值
                    j['版'] += 1
                    if 字 in s.依据段:
                        s.依据作废(j, '你')
                    s.记事件(st, '用户', '改格', **{s.条目: j['号']}, 字段=字)
                回 = {'版': j['版'], '标签': 标签(j), '下一批': j.get('下一批')}
            elif op == '确认':
                j = s.找条目(st, a.get(s.条目))
                nb = j.get('下一批')
                if not nb:
                    raise 错(f'这一{s.条目}没有等你确认的批')
                if nb.get('依据改了'):
                    raise 错(f'你改了{s.依据名}，等 Claude 按新的改好这一批再确认')
                if nb['号'] != a.get('批号') or nb['写于'] != a.get('写于'):
                    raise s._冲突('这一批 Claude 刚改过，看一眼再确认', j)
                if not nb.get('确认'):
                    快照 = {k: nb.get(k) for k in ('内容', '模型', '件数', '预计', '提示词', '栏')}
                    快照['依据'] = {k: j.get(k, '') for k in sorted(s.依据段)}
                    nb['确认'] = {'时间': 现在(), '快照': 快照}
                    j['版'] += 1
                    s.记事件(st, '用户', '确认', **{s.条目: j['号']}, 批号=nb['号'])
            elif op == '撤回确认':
                j = s.找条目(st, a.get(s.条目))
                nb = j.get('下一批')
                if nb and nb.get('确认'):
                    nb['确认'] = None
                    j['版'] += 1
                    s.记事件(st, '用户', '撤回确认', **{s.条目: j['号']}, 批号=nb['号'])
            elif op == '选':
                j = s.找条目(st, a.get(s.条目))
                目标 = None
                for b in j.get('批次', []):
                    for p in b.get('产出', []):
                        if p['id'] == a.get('产出'):
                            目标 = (b, p)
                if not 目标:
                    raise 错('没找到这张')
                b, p = 目标
                if p.get('选'):
                    p['选'] = False
                else:
                    for q in b['产出']:
                        if q.get('组', '') == p.get('组', ''):
                            q['选'] = False
                    p['选'] = True
                组们 = {q.get('组', '') for q in b['产出']}
                已选 = {q.get('组', '') for q in b['产出'] if q.get('选')}
                新结论 = '选好了' if 组们 <= 已选 else (None if b.get('结论') == '选好了' else b.get('结论'))
                if 新结论 != b.get('结论'):
                    b['结论'] = 新结论
                    b['已接'] = False
                j['版'] += 1
                s.记事件(st, '用户', '选', **{s.条目: j['号']}, 产出=p['id'], 选=p['选'])
            elif op == '重出':
                j = s.找条目(st, a.get(s.条目))
                b = s.找批(j, a.get('批号'))
                话 = str(a.get('意见', '')).strip()
                b['结论'] = '重出'
                b['重出意见'] = 话
                b['已接'] = False
                j['意见'].append({'号': 新号(j['意见']), '谁': '用户', '时间': 现在(), '文': f'第 {b["号"]} 批重出：{话 or "（没写怎么改）"}',
                                 '挂': f'批{b["号"]}', '处理': '待处理'})
                j['版'] += 1
                s.记事件(st, '用户', '重出', **{s.条目: j['号']}, 批号=b['号'])
            elif op == '撤回重出':
                j = s.找条目(st, a.get(s.条目))
                b = s.找批(j, a.get('批号'))
                if b.get('结论') == '重出':
                    b['结论'] = None
                    b['已接'] = False
                    j['版'] += 1
                    s.记事件(st, '用户', '撤回重出', **{s.条目: j['号']}, 批号=b['号'])
            elif op in ('通过', '取消通过'):
                j = s.找条目(st, a.get(s.条目))
                j['通过'] = 现在() if op == '通过' else None
                j['版'] += 1
                s.记事件(st, '用户', op, **{s.条目: j['号']})
            elif op == '意见':
                j = s.找条目(st, a.get(s.条目))
                话 = str(a.get('文', '')).strip()
                if not 话:
                    raise 错('意见是空的')
                j['意见'].append({'号': 新号(j['意见']), '谁': '用户', '时间': 现在(), '文': 话[:8000], '挂': a.get('挂') or '', '处理': '待处理'})
                j['版'] += 1
                s.记事件(st, '用户', '意见', **{s.条目: j['号']})
            elif op == '留言':
                话 = str(a.get('文', '')).strip()
                if not 话:
                    raise 错('留言是空的')
                st.setdefault('留言', []).append({'号': 新号(st['留言']), '谁': '用户', '时间': 现在(), '文': 话[:8000], '处理': '待处理'})
                s.记事件(st, '用户', '留言')
            elif op == '交给':
                st['交给'] = 现在()
                s.记事件(st, '用户', '交给')
            elif op == '改上限':
                q = (st.get('期') or {}).get(a.get('额度'))
                if not q:
                    raise 错('没有这个额度')
                try:
                    v = float(a.get('上限'))
                except (TypeError, ValueError):
                    raise 错('上限要是数字')
                if v < 0:
                    raise 错('上限不能是负数')
                q['上限'] = int(v) if v == int(v) else v
                s.记事件(st, '用户', '改上限', 额度=a.get('额度'), 上限=q['上限'])
            elif op == '加' + s.条目:
                后 = s.找条目(st, a.get('后'))
                号 = str(a.get('号', '')).strip()
                if not 号 or any(x['号'] == 号 for x in st[s.条目]):
                    raise 错(f'新{s.条目}号是空的，或者和已有的重了')
                st[s.条目].insert(st[s.条目].index(后) + 1, s.空条目(号, 后['段']))
                s.记事件(st, '用户', '加' + s.条目, **{s.条目: 号}, 后=后['号'])
            else:
                raise 错(f'不认识的操作：{op}')
            s.写(st)
            return st, 回

    # ---------- Claude 用的命令 ----------

    def 新建(s, 段们=('第一卷',)):
        """新区（分卷五 8.4）：建一份空存档，已有就不动。MV 的存档是导演台.py 从分镜表导入的，不走这里。"""
        if s.读() is not None:
            raise 错('存档已经有了，不重复新建')
        st = {'版本': 1, '改动号': 0, '事件号': 0, 'Claude已读': 0, 'Claude看表': None, '交给': None, '期': {}, '花费': [],
              '段': [{'名': x} for x in 段们], s.条目: [], '留言': [], '头': [], '附录': []}
        with s.锁():
            s.记事件(st, 'Claude', '新建', 段数=len(段们))
            s.写(st)
        print(f'建好了空存档：{len(段们)} 段，还没有{s.条目}（用「加」加）')

    def 加条(s, 号, 段, 字段们=None):
        """Claude 加一个条目，放在这一段的最后（段没有就新开一段）；网页里用户加的是插在某一条后面（加 + 条目名）。"""
        字段们 = 字段们 or {}
        for k in 字段们:
            if k not in s.文字段:
                raise 错(f'不能改「{k}」')
        with s.锁():
            st = s.读()
            if st is None:
                raise 错('还没有存档，先「新建」')
            if not 号 or any(x['号'] == 号 for x in st[s.条目]):
                raise 错(f'{s.条目}号是空的，或者和已有的重了：{号}')
            if not any(x['名'] == 段 for x in st['段']):
                st['段'].append({'名': 段})
            j = s.空条目(号, 段)
            j.update(字段们)
            同段 = [i for i, x in enumerate(st[s.条目]) if x['段'] == 段]
            st[s.条目].insert(同段[-1] + 1 if 同段 else len(st[s.条目]), j)
            s.记事件(st, 'Claude', '加' + s.条目, **{s.条目: 号})
            s.写(st)
        print(f'加了{s.条目} {号}（{段}）')

    def 改格们(s, 改表, 谁='Claude'):
        with s.锁():
            st = s.读()
            for 号, 字典 in 改表.items():
                j = s.找条目(st, 号)
                动 = False
                for 字, 值 in 字典.items():
                    if 字 not in s.文字段:
                        raise 错(f'不能改「{字}」')
                    if j.get(字, '') != 值:
                        j[字] = 值
                        动 = True
                        if 字 in s.依据段:
                            s.依据作废(j, 'Claude')
                if 动:
                    j['版'] += 1
                    s.记事件(st, 谁, '改格', **{s.条目: 号}, 字段=list(字典))
            s.写(st)

    def 列(s):
        with s.锁():
            st = s.读()
            新 = [e for e in s.读事件(st.get('Claude已读', 0)) if e['谁'] == '用户']
            if 新:
                计 = {}
                for e in 新:
                    计[e['做']] = 计.get(e['做'], 0) + 1
                print('上次看表以后用户做了：' + '、'.join(f'{k} {v} 次' for k, v in 计.items()))
            else:
                print('上次看表以后用户没动过')
            for j in st[s.条目]:
                t = 标签(j)
                要 = [x for x in t if x in s.我的标签]
                if not 要:
                    continue
                细 = []
                nb = j.get('下一批')
                if '等我出' in t:
                    细.append(f'确认了第 {nb["号"]} 批「{nb["内容"]}」（{nb["确认"]["时间"]}）')
                if '等我改下一批' in t:
                    细.append(f'第 {nb["号"]} 批的依据改了（{"确认已作废" if nb.get("作废的确认") else "还没确认"}）')
                for b in j.get('批次', []):
                    if b.get('结论') and not b.get('已接'):
                        if b['结论'] == '重出':
                            细.append(f'第 {b["号"]} 批要重出：{b.get("重出意见") or "（没写）"}')
                        else:
                            选 = [p.get('标') or p['id'] for p in b['产出'] if p.get('选')]
                            细.append(f'第 {b["号"]} 批选好了：{"、".join(选)}')
                for y in j.get('意见', []):
                    if y['谁'] == '用户' and y.get('处理') != '已处理':
                        细.append(f'意见 {y["号"]}（{y["时间"][5:]}{"，挂 " + y["挂"] if y.get("挂") else ""}）：{y["文"]}')
                if j.get('卡住'):
                    细.append(f'卡住：{j["卡住"]}')
                if j.get('在出'):
                    细.append(f'第 {j["在出"]} 批在出')
                print(f'【{j["号"]}】{"、".join(要)}')
                for x in 细:
                    print('   ', x)
            for m in st.get('留言', []):
                if m['谁'] == '用户' and m.get('处理') != '已处理':
                    print(f'【留言 {m["号"]}】{m["时间"][5:]}：{m["文"]}')
            for 名, v in 花费表(st).items():
                print(f'{名} 本期（{v["起"]}–{v["止"]}）已花 {v["已花"]} / 上限 {v["上限"]} {v["单位"]}')
            st['Claude已读'] = st.get('事件号', 0)
            st['Claude看表'] = 现在()
            s.写(st)

    def 批(s, 号, 内容, 模型, 件数, 预计, 提示词文件, 栏=None):
        栏 = s.默认栏 if 栏 is None else 栏
        if 栏 not in s.栏们:
            raise 错(f'栏只能是 {"、".join(s.栏们)}')
        额度, 数 = 预计.split(':')
        提示词 = open(提示词文件, encoding='utf-8').read().strip()
        with s.锁():
            st = s.读()
            if 额度 not in (st.get('期') or {}) and 额度 != '无':   # 无 = 本机代码这类不花额度的活
                raise 错(f'没有这个额度：{额度}')
            j = s.找条目(st, 号)
            nb = j.get('下一批')
            if nb and nb.get('确认'):
                raise 错(f'下一批用户已经确认了；真要改，先「撤批 {s.条目}号 强制」')
            批号 = nb['号'] if nb else max([b['号'] for b in j['批次']] + [0]) + 1
            j['下一批'] = {'号': 批号, '内容': 内容, '模型': 模型, '件数': int(件数), '预计': {'额度': 额度, '数': float(数)},
                         '提示词': 提示词, '栏': 栏, '写于': 现在(True), '确认': None, '依据改了': False}
            for b in j['批次']:
                if b.get('结论'):
                    b['已接'] = True
            j['版'] += 1
            s.记事件(st, 'Claude', '批', **{s.条目: 号}, 批号=批号)
            s.写(st)
        print(f'{号} 第 {批号} 批写好了，' + ('不花钱，直接「出」就行' if 额度 == '无' else '等用户确认'))

    def 撤批(s, 号, 强制=False):
        with s.锁():
            st = s.读()
            j = s.找条目(st, 号)
            nb = j.get('下一批')
            if not nb:
                raise 错('没有下一批')
            if nb.get('确认') and not 强制:
                raise 错('用户已经确认了，要撤写「强制」')
            j['下一批'] = None
            j['版'] += 1
            s.记事件(st, 'Claude', '撤批', **{s.条目: 号}, 批号=nb['号'])
            s.写(st)

    def 接(s, 号):
        with s.锁():
            st = s.读()
            j = s.找条目(st, 号)
            for b in j['批次']:
                if b.get('结论'):
                    b['已接'] = True
            j['版'] += 1
            s.记事件(st, 'Claude', '接', **{s.条目: 号})
            s.写(st)

    def 出(s, 号):
        with s.锁():
            st = s.读()
            j = s.找条目(st, 号)
            nb = j.get('下一批')
            if nb and not nb.get('确认') and not nb.get('依据改了') and (nb.get('预计') or {}).get('额度') == '无':
                快照 = {k: nb.get(k) for k in ('内容', '模型', '件数', '预计', '提示词', '栏')}
                快照['依据'] = {k: j.get(k, '') for k in sorted(s.依据段)}
                nb['确认'] = {'时间': 现在(), '快照': 快照, '免': '不花钱，不用点头'}
            if not nb or not nb.get('确认'):
                raise 错(f'{号} 没有用户确认了的批（不花钱的批额度写「无」就不用确认）')
            if nb.get('依据改了'):
                raise 错(f'{号} 的依据改过，确认已作废')
            额度, 数 = nb['预计']['额度'], nb['预计']['数']
            表 = 花费表(st).get(额度)
            if 表 and 表['已花'] + 数 > 表['上限']:
                j['卡住'] = f'超上限：{额度} 本期已花 {表["已花"]} + 这批预计 {数} > 上限 {表["上限"]} {表["单位"]}，等你调上限'
                j['版'] += 1
                s.记事件(st, 'Claude', '卡', **{s.条目: 号}, 因='超上限')
                s.写(st)
                print(j['卡住'])
                sys.exit(2)
            b = dict(nb)
            b.update(出于=现在(), 产出=[], 结论=None, 已接=False)
            b.pop('依据改了', None)
            for 旧 in j['批次']:   # 同一栏里用户还没表态的旧批，算被新批换掉了（用户 10-30：看过的旧图别再挂着，免得影响判断）
                if 旧.get('栏', s.默认栏) == b.get('栏', s.默认栏) and not 旧.get('结论'):
                    旧['结论'] = '换新批'
                    旧['已接'] = True
            j['批次'].append(b)
            j['下一批'] = None
            j['在出'] = b['号']
            if (j.get('卡住') or '').startswith('超上限'):
                j['卡住'] = None
            j['版'] += 1
            s.记事件(st, 'Claude', '出', **{s.条目: 号}, 批号=b['号'])
            s.写(st)
        print(f'{号} 第 {b["号"]} 批开始出：{b["内容"]}（预计 {额度} {数}）')

    def 交(s, 号, 项们):
        with s.锁():
            st = s.读()
            j = s.找条目(st, 号)
            if not j['批次']:
                raise 错(f'{号} 还没有批次')
            if 项们 and re.match(r'^批\d+$', 项们[0]):   # 11-01 起能指定挂到哪一批：交 号 批3 文件…
                b = s.找批(j, int(项们[0][1:]))
                项们 = 项们[1:]
            else:
                b = s.找批(j, j['在出']) if j.get('在出') else j['批次'][-1]
            for 项 in 项们:
                部 = 项.split('@')
                rel = s.相对(部[0])
                b['产出'].append({'id': f'{号}-{b["号"]}-{len(b["产出"]) + 1}', '文件': rel, '栏': b.get('栏', s.默认栏),
                                 '标': 部[1] if len(部) > 1 else '', '组': 部[2] if len(部) > 2 else '', '选': False, '时间': 现在()})
            if j.get('在出') == b['号']:
                j['在出'] = None
            b['结论'] = None
            b['已接'] = False
            j['版'] += 1
            s.记事件(st, 'Claude', '交', **{s.条目: 号}, 批号=b['号'], 件数=len(项们))
            s.写(st)
        print(f'{号} 第 {b["号"]} 批挂了 {len(项们)} 件，等用户验收')

    def 花(s, 额度, 数, 号='', 说明='', 时间=None):
        with s.锁():
            st = s.读()
            if 额度 not in (st.get('期') or {}):
                raise 错(f'没有这个额度：{额度}')
            st['花费'].append({'时间': 时间 or 现在(), '额度': 额度, '数': float(数), s.条目: 号, '说明': 说明})
            s.记事件(st, 'Claude', '花', 额度=额度, 数=float(数), **{s.条目: 号})
            s.写(st)
            v = 花费表(st)[额度]
        print(f'{额度} 本期已花 {v["已花"]} / 上限 {v["上限"]} {v["单位"]}')

    def 参考(s, 号, 文件, 说明):
        with s.锁():
            st = s.读()
            j = s.找条目(st, 号)
            j['参考'].append({'文件': s.相对(文件), '说明': 说明})
            j['版'] += 1
            s.记事件(st, 'Claude', '参考', **{s.条目: 号})
            s.写(st)

    def 说(s, 号, 话, 挂=''):
        with s.锁():
            st = s.读()
            if 号 == '留言':
                st['留言'].append({'号': 新号(st['留言']), '谁': 'Claude', '时间': 现在(), '文': 话})
            else:
                j = s.找条目(st, 号)
                j['意见'].append({'号': 新号(j['意见']), '谁': 'Claude', '时间': 现在(), '文': 话, '挂': 挂})
                j['版'] += 1
            s.记事件(st, 'Claude', '说', **{s.条目: 号})
            s.写(st)

    def 标处理(s, 号, 意见号们):
        with s.锁():
            st = s.读()
            表 = st['留言'] if 号 == '留言' else s.找条目(st, 号)['意见']
            for y in 表:
                if y['号'] in 意见号们 and y['谁'] == '用户':
                    y['处理'] = '已处理'
            if 号 != '留言':
                s.找条目(st, 号)['版'] += 1
            s.记事件(st, 'Claude', '处理', **{s.条目: 号}, 号们=意见号们)
            s.写(st)

    def 卡(s, 号, 原因=None):
        with s.锁():
            st = s.读()
            j = s.找条目(st, 号)
            j['卡住'] = 原因
            j['版'] += 1
            s.记事件(st, 'Claude', '卡' if 原因 else '解卡', **{s.条目: 号})
            s.写(st)

    def 等(s, 静=300, 最长=1800, 小时=12):
        """挂后台。用户点了「交给 Claude」或确认、选、重出、通过以后，先不急着叫醒我：
        用户最后一次动作后静默 静 秒才退出（攒成一批）；从第一次该叫醒算起最多攒 最长 秒。"""
        基 = (s.读() or {}).get('Claude已读', 0)
        首 = None
        起 = time.time()
        while True:
            if 小时 and time.time() - 起 > 小时 * 3600:
                print(f'挂了 {小时} 小时，用户没在{s.台名}里动过，等待程序退出。', flush=True)
                return
            evs = [e for e in s.读事件(基) if e['谁'] == '用户']
            if any(e['做'] in s.叫醒 for e in evs):
                首 = 首 or time.time()
                末 = max(解时(e['时间']) for e in evs).timestamp()
                if time.time() - 末 >= 静 or time.time() - 首 >= 最长:
                    计 = {}
                    for e in evs:
                        计[e['做']] = 计.get(e['做'], 0) + 1
                    print(f'用户在{s.台名}里动了：' + '、'.join(f'{k} {v} 次' for k, v in 计.items()) + f'。跑「{s.命令} 列」看详情。', flush=True)
                    return
            time.sleep(3)

    def 命令行(s, a):
        """通用命令。认得、做了返回 True；不认得返回 False（壳自己处理或打印用法）。错 照旧往外抛。"""
        c, r = a[0], a[1:]
        if c == '新建':
            s.新建(r or ('第一卷',))
        elif c == '加':
            s.加条(r[0], r[1], dict(x.split('=', 1) for x in r[2:] if '=' in x))
        elif c == '列':
            s.列()
        elif c == '看':
            print(json.dumps(dict(s.找条目(s.读(), r[0]), _标签=标签(s.找条目(s.读(), r[0]))), ensure_ascii=False, indent=1))
        elif c == '改':
            s.改格们({r[0]: {r[1]: r[2]}})
        elif c == '改多':
            s.改格们(json.load(open(r[0], encoding='utf-8')))
        elif c == '批':
            s.批(*r[:6], *(r[6:7] or [s.默认栏]))
        elif c == '撤批':
            s.撤批(r[0], 强制=len(r) > 1 and r[1] == '强制')
        elif c == '接':
            s.接(r[0])
        elif c == '出':
            s.出(r[0])
        elif c == '交':
            s.交(r[0], r[1:])
        elif c == '花':
            s.花(r[0], r[1], r[2] if len(r) > 2 else '', r[3] if len(r) > 3 else '', r[4] if len(r) > 4 else None)
        elif c == '参考':
            s.参考(r[0], r[1], r[2] if len(r) > 2 else '')
        elif c == '说':
            s.说(r[0], r[1], r[2] if len(r) > 2 else '')
        elif c == '处理':
            s.标处理(r[0], [int(x) for x in r[1:]])
        elif c == '卡':
            s.卡(r[0], r[1])
        elif c == '解卡':
            s.卡(r[0], None)
        elif c == '等':
            s.等(int(r[0]) if r else 300, int(r[1]) if len(r) > 1 else 1800, float(r[2]) if len(r) > 2 else 12)
        elif c == '花费':
            for 名, v in 花费表(s.读()).items():
                print(f'{名} 本期（{v["起"]}–{v["止"]}）已花 {v["已花"]} / 上限 {v["上限"]} {v["单位"]}')
        else:
            return False
        return True

    # ---------- 本机网页服务（这个区自己的旧网页用；看板有自己的服务，只借文件和缩略图） ----------

    def 处理类(s, 模板=None):
        """给这个区做一个网页处理类：/ 给 模板 页面，/api/state、/api/rev、/api/todo，/f/ 原文件，/t/ 缩略图，POST /api/op 网页操作。"""
        区_ = s

        class 处理(BaseHTTPRequestHandler):
            台区 = 区_

            def log_message(s, *a):
                pass

            def 主机对(s):
                h = s.headers.get('Host', '')
                port = s.server.server_port
                return h in (f'127.0.0.1:{port}', f'localhost:{port}')

            def 回(s, code, body, ctype='application/json; charset=utf-8'):
                if isinstance(body, (dict, list)):
                    body = json.dumps(body, ensure_ascii=False).encode('utf-8')
                elif isinstance(body, str):
                    body = body.encode('utf-8')
                s.send_response(code)
                s.send_header('Content-Type', ctype)
                s.send_header('Content-Length', str(len(body)))
                s.send_header('Cache-Control', 'no-store')
                s.end_headers()
                s.wfile.write(body)

            def do_GET(s):
                try:
                    s.取()
                except (BrokenPipeError, ConnectionResetError):
                    pass

            def 取(s):
                if not s.主机对():
                    return s.回(403, {'错': '只让本机访问'})
                u = urlparse(s.path)
                p = unquote(u.path)
                if p in ('/', '/index.html'):
                    with open(模板, encoding='utf-8') as f:
                        return s.回(200, f.read(), 'text/html; charset=utf-8')
                if p == '/api/state':
                    st = 区_.读()
                    return s.回(200, 区_.带算(st)) if st else s.回(404, {'错': '还没有存档'})
                if p == '/api/rev':
                    st = 区_.读() or {}
                    return s.回(200, {'改动号': st.get('改动号', 0)})
                if p == '/api/todo':
                    with open(os.path.join(区_.根, 'TODO.md'), encoding='utf-8') as f:
                        return s.回(200, {'文': f.read()})
                if p.startswith('/f/'):
                    return s.文件(p[3:])
                if p.startswith('/t/'):
                    return s.缩略(p[3:], parse_qs(u.query))
                return s.回(404, {'错': '没有这个地址'})

            def 文件(s, rel):
                f = 区_.安全路径(rel)
                if not f or not os.path.isfile(f):
                    return s.回(404, {'错': '没有这个文件'})
                size = os.path.getsize(f)
                ctype = 类型表.get(os.path.splitext(f)[1].lower(), 'application/octet-stream')
                起, 止, code = 0, size - 1, 200
                rng = s.headers.get('Range')
                if rng:
                    m = re.match(r'bytes=(\d*)-(\d*)$', rng.strip())
                    if m and (m.group(1) or m.group(2)):
                        if m.group(1) == '':
                            起 = max(0, size - int(m.group(2)))
                        else:
                            起 = int(m.group(1))
                            if m.group(2):
                                止 = min(int(m.group(2)), size - 1)
                        if 起 > 止 or 起 >= size:
                            s.send_response(416)
                            s.send_header('Content-Range', f'bytes */{size}')
                            s.send_header('Content-Length', '0')
                            s.end_headers()
                            return
                        code = 206
                s.send_response(code)
                s.send_header('Content-Type', ctype)
                s.send_header('Accept-Ranges', 'bytes')
                s.send_header('Content-Length', str(止 - 起 + 1))
                s.send_header('Cache-Control', 'no-cache')
                if code == 206:
                    s.send_header('Content-Range', f'bytes {起}-{止}/{size}')
                s.end_headers()
                with open(f, 'rb') as fh:
                    fh.seek(起)
                    剩 = 止 - 起 + 1
                    while 剩 > 0:
                        块 = fh.read(min(1 << 20, 剩))
                        if not 块:
                            break
                        s.wfile.write(块)
                        剩 -= len(块)

            def 缩略(s, rel, q):
                f = 区_.安全路径(rel)
                if not f or not os.path.isfile(f):
                    return s.回(404, {'错': '没有这个文件'})
                try:
                    w = max(60, min(1600, int((q.get('w') or ['240'])[0])))
                except ValueError:
                    w = 240
                stt = os.stat(f)
                键 = hashlib.sha1(f'{f}|{stt.st_mtime}|{w}'.encode('utf-8')).hexdigest()[:20]
                缓 = os.path.join(区_.台, '缓存.nosync', '缩略图')
                os.makedirs(缓, exist_ok=True)
                out = os.path.join(缓, 键 + '.jpg')
                if not os.path.exists(out):
                    tmp = out + f'.{os.getpid()}.{id(s)}.jpg'
                    if f.lower().endswith(视频后缀):
                        subprocess.run([FFMPEG, '-v', 'error', '-ss', '0.5', '-i', f, '-frames:v', '1', '-vf', f'scale={w}:-2', '-y', tmp],
                                       capture_output=True, timeout=60)
                    else:
                        from PIL import Image
                        im = Image.open(f).convert('RGB')
                        im.thumbnail((w, w * 4), Image.LANCZOS)
                        im.save(tmp, 'JPEG', quality=84)
                    if not os.path.exists(tmp):
                        return s.回(500, {'错': '缩略图没做出来'})
                    os.replace(tmp, out)
                with open(out, 'rb') as fh:
                    return s.回(200, fh.read(), 'image/jpeg')

            def do_POST(s):
                try:
                    s.存()
                except (BrokenPipeError, ConnectionResetError):
                    pass

            def 存(s):
                port = s.server.server_port
                if not s.主机对() or s.headers.get('X-Daoyantai') != '1':
                    return s.回(403, {'错': f'只让本机的{区_.台名}页面改'})
                o = s.headers.get('Origin')
                if o and o not in (f'http://127.0.0.1:{port}', f'http://localhost:{port}'):
                    return s.回(403, {'错': f'只让本机的{区_.台名}页面改'})
                if urlparse(s.path).path != '/api/op':
                    return s.回(404, {'错': '没有这个地址'})
                n = int(s.headers.get('Content-Length') or 0)
                try:
                    a = json.loads(s.rfile.read(n) or b'{}')
                except ValueError:
                    return s.回(400, {'错': '不是 JSON'})
                try:
                    st, 回 = 区_.用户操作(a)
                except 冲突 as e:
                    return s.回(409, {'冲突': True, '错': str(e), 区_.条目: dict(e.条, _标签=标签(e.条)) if e.条 else None})
                except 错 as e:
                    return s.回(400, {'错': str(e)})
                if 回 is not None:
                    回.update(ok=True, 改动号=st['改动号'])
                    return s.回(200, 回)
                return s.回(200, {'ok': True, '状态': 区_.带算(st)})

        return 处理


def main():
    a = sys.argv[1:]
    if len(a) < 2:
        print(__doc__)
        return
    try:
        台 = os.path.abspath(a[0])
        if not os.path.exists(os.path.join(台, '区域.json')):
            sys.exit(f'没做：{台} 里没有 区域.json，不是施工区的存档目录')
        if not 区(台).命令行(a[1:]):
            print(__doc__)
            sys.exit(1)
    except 错 as e:
        sys.exit(f'没做：{e}')


if __name__ == '__main__':
    main()
