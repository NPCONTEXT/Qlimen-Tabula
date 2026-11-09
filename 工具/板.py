#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""无限表格 Qlimen Tabula（Qlimen 的可视化看板）：一张表看所有长任务的进度、TODO、谁在干；重活（比如 MV 分镜、小说）在同一张表上有施工区。
说明见 docs/使用说明.md。只在本机，不绑定哪家模型：进度读各任务的 TODO.md；谁在干由干活的模型自己开灯关灯。

用法（都用 /usr/bin/python3 跑）：
  板.py 服务 [端口] [--父 进程号]                      本机服务（默认 8770），只让本机访问；带 --父 的，那个进程没了就自己退（原生小窗起的服务）
  板.py 开工 任务 [格子…] [--谁 名字] [--预计 分钟] [--说 一句话]   开灯（在干，框上色块慢慢走）；同一任务同一个谁再开一次 = 续期（租期 30 分钟）
                                                    带 --预计 时先报上一段实际 ÷ 预计、往常是预计的几倍（估时对账，11-04 起）
  板.py 等你 任务 [--谁 名字] [--说 交付了什么]          交付、等你：框留着、动效停、名牌「等你」，你在看板上点「知道了」或我「收工」才消失
  命令名和核心 §5 的状态词一样：施工 = 开工；等你 = 交付；收工 = 完工、灭灯（11-05 卷二 7.20 起；以前「收工」是交付的意思，
  老插件（11-05 01:1x 前开的会话）带 --会话 敲的收工照旧当等你）
  开工、等你还能带 --题 标题（零活那一行的名字）、--对不上 原因（回复说的和插件看到的不一样，名牌上打个问号）；
  等你还能带 --收工：会话说做完了、用户还没看，名牌写「收工」（卷四 6.26）；
  开工还能带 --要你：回复写了【等你】、后台又还在跑，照旧在干（亮片照走），名牌写「等你」（卷四 6.24）
  任务写「零活:会话号」= 没有任务目录的会话（查询、小任务），看板上单独一行、进度条占位
  板.py 收工 任务 [--谁 名字]                         真没事了：框直接消失（= 完工）
  开工、等你、收工都能加 --会话 号（不写任务就用这个会话最近在干的那个）、--接入 名、--租 分钟（开工用，默认 30）；
  Claude 会话的插件「无限表格监听」就是这么替会话自动开关灯的。灯按「任务 × 谁 × 会话」分开记。
  板.py 跑 任务 [--谁 名字] [--说 话] -- 命令…           命令在跑灯就亮，退出就灭（进程没了也灭）
  板.py 列                                           列出你在看板上点过、写过的（TODO 的等你格 + 各施工区），记下已读
  板.py 段 任务                                      接手要读的：TODO 的「现在」和在做的段（还有 交接.md 的先打印它最上面一条）
  板.py 等 [静默秒] [最长秒] [最多挂几小时]             挂后台：你在看板上点头、写意见后，静默期满才退出（叫醒干活的会话）
  板.py 读 [任务]                                     打印看板读到的东西（自测用）
  板.py 重开 [端口]                                   换版：叫正在跑的服务退出，原生小窗几秒内用新代码再起一个（不开终端）；等到新服务起来（进程号换了）才算换好，25 秒没起来就直说
  板.py 对标准                                       和 工具/标准答案.json 逐份对
  板.py 区 新建 任务 [--模板 小说] [--号 区号] [--名 名字] [--段 卷一,卷二]   给这个任务建施工区（分卷五）：任务目录里建 施工台/（区域.json 照
                                                    工具/施工区模板/ 里的模板、空存档），看板登记加一行；之后用 工具/施工台.py 施工台目录 加/改/列…
  板.py 区 列                                         列出登记的施工区
  板.py 对账 [任务] [--谁 名字] [--条 N]              估时对账：带 --预计 开工的每一段预计几分钟、实际几分钟、几倍
  板.py 设置                                         打印读到的设置（工作区、分组、跳过目录、派工账本、Codex）：装好后先跑它核对
  板.py 演示                                         把仓库自带的演示工作区弄得像在用：错开 TODO 的修改时间、登记两个演示施工区、亮几盏演示灯
                                                    （没写 设置.json、也还没有数据时，双击 打开无限表格.command 会自动跑一次）
任务 = 任务目录（相对工作区，或绝对路径），或看板上的名字（唯一能对上就行）；Codex 额外工作区里的写「名字/…」（设置.json 的 Codex.额外工作区）。
Codex（设置.json 里 Codex.开 = true 才读）：服务每 3 秒读她的会话记录（~/.codex/sessions），照每轮开始、结束和回复开头的状态词替她开关灯，她不用敲命令；
  板.py codex 读一遍、打印记了什么（接入 Codex，11-05）。
存放：数据.nosync/ 里 开关.jsonl（开灯关灯）、布局.json（你在总览里手动排的位置、大小）、事件.jsonl（你在看板上的动作）、已读.json、信箱/<会话>.jsonl（你在看板上的动作，按任务投给在干它的会话）。
会话：开工时记下 BAN_SESSION（别家照这个传）或 Claude 桌面会话号 CLAUDE_CODE_HOST_SESSION_ID；怎么打开会话写在 接入/<接入名>.json。
设置：仓库根目录的 设置.json（照 设置.example.json 写；没有就全用默认，工作区是仓库自带的 示例/演示工作区）。
测试：BAN_DATA 指到别的数据目录、BAN_ROOT 指到别的工作区、BAN_SETTINGS 指到别的设置文件（设了 BAN_ROOT 或 BAN_DATA 又没设它，就不读 设置.json）、BAN_LEDGER 指到别的派工账本、BAN_SGT 写「区号=存档目录;…」把施工区指到副本（DYT_DIR 是老写法，指登记的第一个区）、BAN_OPEN 指到 /bin/echo（「文件夹 ↗」不真开访达）。"""
import csv
import copy
import fcntl
import importlib.util
import json
import os
import re
import subprocess
import sys
import threading
import statistics
import glob
import time
from datetime import datetime
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, unquote, parse_qs, quote

工具 = os.path.dirname(os.path.abspath(__file__))
本任务 = os.path.dirname(工具)
测试中 = bool(os.environ.get('BAN_ROOT') or os.environ.get('BAN_DATA'))


def 读设置():
    """仓库根目录的 设置.json（照 设置.example.json 写）；没有就全用默认。测试中（设了 BAN_ROOT 或 BAN_DATA）不读，除非用 BAN_SETTINGS 指定。"""
    p = os.environ.get('BAN_SETTINGS') or ('' if 测试中 else os.path.join(本任务, '设置.json'))
    if not p or not os.path.exists(p):
        return {}
    try:
        with open(p, encoding='utf-8') as f:
            j = json.load(f)
        return j if isinstance(j, dict) else {}
    except (OSError, ValueError) as e:
        print(f'设置.json 读不了，先用默认：{e}', file=sys.stderr)
        return {}


设置 = 读设置()
_codex = 设置.get('Codex') if isinstance(设置.get('Codex'), dict) else {}
# 工作区：看板扫这下面所有带 TODO.md 的目录；没设就用仓库自带的演示工作区
根 = os.path.realpath(os.environ.get('BAN_ROOT') or os.path.join(本任务, os.path.expanduser(设置.get('工作区') or os.path.join('示例', '演示工作区'))))   # 相对路径按仓库目录算（插件也这么算）
数据 = os.environ.get('BAN_DATA') or os.path.join(本任务, '数据.nosync')
# 接入 Codex（默认关，设置里 Codex.开 = true 才读）：额外工作区（Codex 自己的工作区在工作区外面时）里的任务键写「名字/…」，
# 只认她在 Codex 界面开的、没归档的会话所在的有 TODO.md 的目录。测试默认不扫：BAN_EXTRA 写「名=路径;名=路径」、BAN_CODEX 指仿造的 ~/.codex
外区 = {k.strip(): os.path.realpath(os.path.expanduser(v.strip())) for k, v in (x.split('=', 1) for x in (
    os.environ.get('BAN_EXTRA', '' if 测试中 or not _codex.get('开') else ';'.join(f'{k}={v}' for k, v in (_codex.get('额外工作区') or {}).items()))).split(';') if '=' in x)}
Codex家 = os.environ.get('BAN_CODEX') or ('' if 测试中 or not _codex.get('开') else os.path.expanduser(_codex.get('家') or '~/.codex'))
模板 = os.environ.get('BAN_TEMPLATE') or os.path.join(工具, '板-页面.txt')
# Qlimen 派工脚本 waibao 的账本（core/data/用量日志.csv）：「运行中」那行就是开着的灯；不用 Qlimen 就空着
账本 = os.environ.get('BAN_LEDGER') or (os.path.expanduser(设置['派工账本']) if 设置.get('派工账本') else '')
打开命令 = os.environ.get('BAN_OPEN') or '/usr/bin/open'   # 展开里的「文件夹 ↗」「最近改了 X」用它开
施工台文件 = os.path.join(工具, '施工台.py')   # 分卷五：施工区的通用引擎（锁、读写、事件、网页操作、Claude 用的命令）；每个区的字段写在它存档目录的 区域.json
小窗 = os.path.join(本任务, '小窗.nosync', '无限表格小窗.app')
接入目录 = os.path.join(本任务, '接入')   # 各家怎么打开会话、开新会话（claude.json；别家照格式另写一份）   # 原生置顶小窗（工具/小窗.swift，编译：工具/编译小窗.sh）
登记文件 = os.path.join(数据, '施工区登记.json')   # 分卷五：哪些任务有施工区（区号 → 任务、存档目录、看板这边的状态文件）；板.py 区 新建 往里加
母文件夹 = [x for x in (设置.get('分组') or []) if isinstance(x, str)]   # 总览里分组的顺序；空着 = 自动：工作区下第一层每个文件夹一组，按名字排
跳过目录 = {'冷归档', '归档', 'node_modules', '资料', '__pycache__', '备份', '历史资料'} | set(设置.get('跳过目录') or [])   # 这些目录里的 TODO.md 是旧副本、资料，不当任务；.nosync 结尾、点开头的也跳过
跳过节 = ('模板', '验收', '查到', '摸底', '结论', '资源', '已定', '先读', '备选', '记录', '原话')
租期 = 1800
七天 = 7 * 86400


class 错(Exception):
    pass


# ---------- 读 TODO ----------

ID = r'[A-Za-z]?\d+(?:\.\d+)*(?:[a-z]\d*)?'
行编号 = re.compile(r'^(' + ID + r')(?=$|[\s✅⏸🔄➡\[（(])')
勾选 = re.compile(r'^\s*[-*]\s*\[([ xX])\]\s*(.*)$')
编号框 = re.compile(r'^(\[[ xX-]\]|[☑☐])\s*')
勾编号 = re.compile(r'\[([ xX])\]\s*(' + ID + r'(?:\s*[–~]\s*' + ID + r')?)(?=$|[\s·（(，,：:；;|])')
开头编号 = re.compile(r'^(' + ID + r'(?:\s*[、,，]\s*' + ID + r')*)(?=$|[\s·（(，,：:；;\[])')
日期 = re.compile(r'(?:20\d\d-)?(\d{1,2})-(\d{1,2})')
依赖头 = re.compile(r'^\s*(?:步骤\s*)?(' + ID + r'(?:\s*(?:[、,，和]|[–~])\s*(?:步骤\s*)?' + ID + r')*)')
分隔行 = re.compile(r'^\|?\s*:?-{2,}')


def 拆(l):
    return [c.strip() for c in l.strip().strip('|').split('|')]


def 展开(a, b):
    ma, mb = re.match(r'^(.*?)(\d+)$', a), re.match(r'^(.*?)(\d+)$', b)
    if ma and mb and ma.group(1) == mb.group(1) and int(mb.group(2)) - int(ma.group(2)) < 60:
        return [ma.group(1) + str(k) for k in range(int(ma.group(2)), int(mb.group(2)) + 1)]
    ma, mb = re.match(r'^(.*?)([a-z])$', a), re.match(r'^(.*?)([a-z])$', b)
    if ma and mb and ma.group(1) == mb.group(1):
        return [ma.group(1) + chr(c) for c in range(ord(ma.group(2)), ord(mb.group(2)) + 1)]
    return [a, b]


def 编号们(spec):
    m = re.match(r'^(' + ID + r')\s*[–~]\s*(' + ID + r')$', spec.strip())
    return 展开(m.group(1), m.group(2)) if m else [spec.strip()]


def 短名(t):
    t = re.sub(r'✅|⏸️?|🔄|➡️?|\[[^\]]*\]|\*\*|`', '', t).strip(' ：:;；，,·')
    n = re.split(r'[：:；;（(，,。]', t, 1)[0].strip()
    return (n or t)[:20]


def 表头(cells):
    h = {}
    for i, c in enumerate(cells):
        if '步骤' in c and '步骤' not in h:
            h['步骤'] = i
        if '依赖' in c:
            h['依赖'] = i
    if '步骤' in h or (cells and ('编号' in cells[0] or cells[0] == '#')):
        h.setdefault('步骤', 1)
        return h
    return None


def 触发(全文):
    """[待触发] 的条件（核心 §2 11-04，卷二 7.48）：`到 MM-DD` 到日子了、`数 路径 [字段] [减 K] ≥ N` 数够了才算到；
    数 = 路径（可带 * ）下各文件的非空行，写了字段就只数 JSON 里这个字段不空的行，减 K 扣掉已知的测试行；只数行，不执行任何东西。
    返回 (进度, 到了没)；没写机器能查的条件就是 ('', False)，一直灰着，等人想起来"""
    m = re.search(r'`到\s*(\d{1,2})-(\d{1,2})`', 全文)
    if m:
        今 = datetime.now()
        try:
            日 = datetime(今.year, int(m.group(1)), int(m.group(2)))
        except ValueError:
            return '', False
        if (今 - 日).days > 180:   # 年底写的、日子在明年初
            日 = 日.replace(year=今.year + 1)
        elif (日 - 今).days > 180:   # 年初看去年底的日子
            日 = 日.replace(year=今.year - 1)
        到了 = 今 >= 日
        return ('到日子了' if 到了 else f'到 {日:%m-%d}'), 到了
    m = re.search(r'`数\s+(\S+)(?:\s+(?!减)([^\s≥>]+))?(?:\s+减\s*(\d+))?\s*(?:≥|>=)\s*(\d+)`', 全文)
    if m:
        路, 字段, 减, 要 = m.group(1), m.group(2), int(m.group(3) or 0), int(m.group(4))
        n = 0
        for f in glob.glob(os.path.expanduser(路)):
            try:
                with open(f, encoding='utf-8', errors='replace') as fh:
                    for l in fh:
                        l = l.strip()
                        if not l:
                            continue
                        if not 字段:
                            n += 1
                            continue
                        try:
                            v = json.loads(l)
                        except ValueError:
                            continue
                        if isinstance(v, dict) and v.get(字段):
                            n += 1
            except OSError:
                pass
        n = max(0, n - 减)
        return f'{n}/{要}', n >= 要
    return '', False


def 新步骤(编, 全文, 行, 依赖='', 节=None):
    done = ('✅' in 行) or bool(re.search(r'\[[xX]\]', 行)) or ('➡' in 行) or ('➖' in 行)   # ➡ 并到别处、➖ 不用做了，都算做完
    待 = '[待触发]' in 行   # 卷二 7.48：条件到了才算等你；数得出的在名字后面写几/几
    进度, 到了 = 触发(全文) if 待 else ('', False)
    return {'id': 编, '名': 短名(全文) + (' ' + 进度 if 进度 else ''), '全': re.sub(r'\s+', ' ', 全文).strip()[:300] + (f'（现在 {进度}）' if 进度 else ''), '完': done,
            '待': 待, '到了': 到了,
            '在做': ('🔄' in 行) and not done, '停': '⏸' in 行,
            '用户': ('需用户' in 行) and ('需用户→自动' not in 行), '依': 依赖,
            '选': bool(re.search(r'需用户[^\]】|]*可选', 行) or re.match(r'^\s*(?:\[[^\]]*\]\s*)?[（(]可选[）)]', 全文))}   # 可选的不算等你（卷四 6.12）


段态式 = re.compile(r'[（(](?:[^（）()]*·\s*)?(在做|做完|搁置)[）)]\s*$')   # 新写法的段状态：「（11-03 起 · 在做）」「（做完）」；「（11-01 05:1x 做完）」这种旧标题不算


def 段态(题):
    m = 段态式.search(题)
    return m.group(1) if m else None


def 是现在(题):
    return 题 == '现在' or bool(re.match(r'^现在[（(\s]', 题))


def 现在块(text):
    """TODO 最上面「## 现在」那块的几行（新写法，卷二 7.23）：第 1 层悬停、`板.py 段` 用"""
    out, 在 = [], False
    for l in text.split('\n'):
        s = l.strip()
        if re.match(r'^#{1,3} ', s):
            if 在:
                break
            在 = 是现在(s.lstrip('#').strip())
            continue
        if 在 and s:
            out.append(re.sub(r'^[-*]\s*', '', s))
    return out[:5]


def 一级标题数(text):
    """代码块外面、行首「# 」的一级标题有几个（代码块里的 # 注释不算）"""
    n, 框 = 0, False
    for l in text.split('\n'):
        if l.lstrip().startswith('```'):
            框 = not 框
        elif not 框 and l.startswith('# '):
            n += 1
    return n


def 解析(text):
    # 卷四 6.12：有两个以上一级标题的（盯跑这类一轮一个，上下文横条一部分一个），一级标题开一轮，
    # 轮里不跳的小节（「## 进度（10-22）」这种）归这一轮，勾只在本轮里找编号；以前只认 ## ###，几轮串在一起、勾打到别的轮上
    组模式 = 一级标题数(text) >= 2
    组块, 框 = None, False
    节们 = []
    cur = {'题': '（开头）', '步': [], '勾': [], '跳': False}
    节们.append(cur)
    hdr = None
    ls = text.split('\n')
    i = 0
    while i < len(ls):
        l = ls[i]
        s = l.strip()
        if 组模式:
            if s.startswith('```'):
                框 = not 框
            elif not 框 and l.startswith('# '):
                题 = s[2:].strip()
                cur = 组块 = {'题': 题, '步': [], '勾': [], '跳': any(k in re.split(r'[（(]', 题, 1)[0] for k in 跳过节), '组': i, '态': 段态(题)}
                节们.append(cur)
                hdr = None
                i += 1
                continue
        if s.startswith('## ') or s.startswith('### '):
            题 = s.lstrip('#').strip()   # 跳不跳只看括号前的标题本身（「10-27 手滑缓解（排查结论见交接）」不算结论节）
            跳 = any(k in re.split(r'[（(]', 题, 1)[0] for k in 跳过节) or 是现在(题)   # 「## 现在」只写停因、在跑这些，不是步骤
            if 组模式 and 组块 is not None and not 跳:
                cur = 组块   # 组模式：不跳的小节归这一轮
            else:
                cur = {'题': 题, '步': [], '勾': [], '跳': 跳, '态': 段态(题), **({'组': 组块['组']} if 组模式 and 组块 is not None else {})}
                节们.append(cur)
            hdr = None
            i += 1
            continue
        if '|' in s and i + 1 < len(ls) and 分隔行.match(ls[i + 1].strip()):
            hdr = 表头(拆(s))
            if hdr and (cur['步'] or cur['勾']):   # 同一节里又起一张步骤表：算新的一块（一节里分几批写的，比如 Q3）
                cur = {'题': cur['题'], '步': [], '勾': [], '跳': cur['跳'], '态': cur.get('态'), **({'组': cur['组']} if '组' in cur else {})}
                节们.append(cur)
                if '组' in cur:
                    组块 = cur
            i += 2
            continue
        if '|' in s and not hdr and '步骤' in s and i + 1 < len(ls) and '|' in ls[i + 1]:
            # 表头下面漏了 ---|--- 分隔行、下一行直接是编号行，也认（11-01 作者的一份 TODO）
            头, 下 = 拆(s), 拆(ls[i + 1].strip())
            框0 = 编号框.match(下[0]) if 下 else None
            if 头 and ('编号' in 头[0] or 头[0] == '#') and 下 and 行编号.match(下[0][框0.end():] if 框0 else 下[0]):
                hdr = 表头(头)
                if cur['步'] or cur['勾']:
                    cur = {'题': cur['题'], '步': [], '勾': [], '跳': cur['跳']}
                    节们.append(cur)
                i += 1
                continue
        if hdr and '|' in s:
            c = 拆(s)
            框 = 编号框.match(c[0]) if c else None   # 编号格前面带勾选框：[x] 1、[-] 7d、☑ J1、☐ J5
            m = 行编号.match(c[0][框.end():] if 框 else c[0]) if c else None
            if m:
                全文 = c[hdr['步骤']] if hdr['步骤'] < len(c) else ''
                依 = c[hdr['依赖']] if '依赖' in hdr and hdr['依赖'] < len(c) else ''
                st = 新步骤(m.group(1), 全文, s, 依)
                if 框 and 框.group(1) in ('[x]', '[X]', '[-]', '☑'):   # 勾了，或者 [-] 不用做了：算做完
                    st['完'], st['在做'] = True, False
                if re.match(r'^\s*(不需要|不用做|不做了|取消)', c[-1]):   # 最后一格写着不需要了 = 不用做，算做完
                    st['完'], st['在做'] = True, False
                cur['步'].append(st)
            i += 1
            continue
        if not s:
            hdr = None
        mb = 勾选.match(l)
        if mb:
            cur['勾'].append((mb.group(1), mb.group(2), l))
        i += 1
    索引 = {}
    for n in 节们:
        for st in n['步']:
            索引.setdefault(st['id'], st)
    局们 = {}   # 组模式：每一轮自己的编号表
    for n in 节们:
        if '组' in n:
            局 = 局们.setdefault(n['组'], {})
            for st in n['步']:
                局.setdefault(st['id'], st)
    for n in 节们:
        引 = 局们[n['组']] if '组' in n else 索引
        if '组' in n:
            n['局'] = 引
        if n['跳'] and '组' in n:
            continue   # 组模式：轮里要跳过的小节（验收、原话……）里的勾不算这一轮的步骤
        有表 = bool(n['步'])
        for k, (mark, rest, line) in enumerate(n['勾']):
            if 有表:
                ms = list(勾编号.finditer(line))
                if not ms:
                    continue   # 有步骤表的节里，不带编号的勾选框是验收条
                for m in ms:
                    for 编 in 编号们(m.group(2)):
                        if 编 in 引:
                            if m.group(1) in 'xX':
                                引[编]['完'] = True
                                引[编]['在做'] = False
                        else:
                            st = 新步骤(编, line[m.end():], line.replace('[ ]', ''), '')
                            st['完'] = m.group(1) in 'xX'
                            n['步'].append(st)
                            引[编] = st
            else:
                m = 开头编号.match(rest)
                if m:
                    列 = [x.strip() for x in re.split(r'[、,，]', m.group(1))]
                    if all(x in 引 for x in 列):   # 勾的是别处表里的步骤（比如表在下面、进度记在上面）：只当完成记号
                        if mark in 'xX':
                            for x in 列:
                                引[x]['完'] = True
                                引[x]['在做'] = False
                        continue
                编 = re.split(r'[、,，]', m.group(1))[0].strip() if m else f'•{k + 1}'
                st = 新步骤(编, rest[m.end():] if m else rest, line.replace('[ ]', ''), '')
                st['完'] = mark in 'xX'
                n['步'].append(st)
                引.setdefault(编, st)
    用节 = [n for n in 节们 if n['步'] and not n['跳']]
    return 用节, 索引


def 解依赖(依, 索引, 本=None):
    t0 = 依 or ''
    m = 依赖头.match(t0)
    if m:
        串 = m.group(1)
    else:   # 一句话里夹着编号：「第 10 步写完」「依赖 3」（卷四 6.12；以前认不出就当没依赖，前面的还没做完就标黄了）
        串 = '、'.join(re.findall(r'第\s*(' + ID + r')\s*步', t0))
        if not 串:
            m2 = re.match(r'^\s*依赖\s*(' + ID + r'(?:\s*(?:[、,，和]|[–~])\s*' + ID + r')*)', t0)
            串 = m2.group(1) if m2 else ''
        if not 串:
            return []
    out = []
    for t in re.finditer(r'(' + ID + r')(?:\s*[–~]\s*(' + ID + r'))?', 串):
        for 编 in (展开(t.group(1), t.group(2)) if t.group(2) else [t.group(1)]):
            if 编 in 索引:
                out.append(索引[编])
            elif 本 and re.match(r'^[a-z]\d*$', 编) and re.sub(r'[a-z]\d*$', '', 本) + 编 in 索引:   # 同一组的简写：11.11e5 写「e4」= 11.11e4
                out.append(索引[re.sub(r'[a-z]\d*$', '', 本) + 编])
            else:
                近 = [v for k, v in 索引.items() if k.endswith(编) and len(k) > len(编)]
                if len(近) == 1:
                    out.append(近[0])
    return out


def 节日期(题):
    ds = 日期.findall(题)
    return max((int(a), int(b)) for a, b in ds) if ds else None


def 读TODO(path, 旧=False):
    try:
        text = open(path, encoding='utf-8').read()
    except OSError as e:
        return {'读不出': f'打不开：{e}'}
    except ValueError:
        return {'读不出': 'TODO 不是 UTF-8 文字（编码坏了），看板读不出'}
    节们, 索引 = 解析(text)
    现 = 现在块(text)
    if not 节们:
        return {'读不出': '读不出进度：TODO 里没认出步骤表或勾选框，看板不猜'}
    标了 = [n for n in 节们 if n.get('态')]
    轮们 = [n for n in 节们 if n['步'][0]['id'] == '1']
    未完 = [n for n in 节们 if any(not s['完'] for s in n['步'])]
    if 标了:   # 新写法（核心 §2 11-04）：段标题带「在做 / 做完 / 搁置」，在做的段都算当前；一段都没在做就看日期最新的那段
        模式 = '段'
        当前们 = [n for n in 节们 if n.get('态') == '在做'] or [max(节们, key=lambda n: (节日期(n['题']) or (0, 0), -节们.index(n)))]
        当前 = 当前们[0]
        计 = [s for n in 节们 for s in n['步']]
    elif len(轮们) >= 2:
        模式 = '轮'
        候 = [n for n in 轮们 if n in 未完] or 轮们
        当前 = max(候, key=lambda n: (节日期(n['题']) or (0, 0), -节们.index(n)))
        计 = 当前['步']
    else:
        模式 = '阶段'
        有勾 = [k for k, n in enumerate(节们) if any(s['完'] for s in n['步'])]
        L = 有勾[-1] if 有勾 else 0
        后 = [n for n in 节们[L:] if n in 未完]
        前 = [n for n in 节们[:L] if n in 未完]
        当前 = 后[0] if 后 else (前[-1] if 前 else 节们[-1])
        计 = [s for n in 节们 for s in n['步']]
    if not 标了:
        当前们 = [当前]
    for n in 当前们:
        for s in n['步']:
            if s.get('待'):   # [待触发]：条件到了才算等你，平时灰的（卷二 7.48）
                s['等'] = (not s['完']) and s['到了']
                continue
            if 模式 == '段' and s['停']:   # 新写法（核心 §2）里 ⏸ 是搁置：不算等你、显示成灰的；旧写法里 ⏸ 是「停下等你」，照旧（卷二 7.45）
                s['等'] = False
                continue
            s['等'] = (not s['完']) and s['用户'] and not s.get('选') and (s['停'] or all(d['完'] for d in 解依赖(s['依'], n.get('局') or 索引, s['id'])))
    当前步 = [s for n in 当前们 for s in n['步']]
    def 态(s):
        if s['完']:
            return 'd'
        if s.get('等'):
            return 'o' if 旧 else 'w'
        return 'p' if s['在做'] else 't'
    return {'模式': 模式, '节': ' / '.join(n['题'] for n in 当前们)[:40], '当前节': [n['题'] for n in 当前们],
            '完成': sum(s['完'] for s in 计), '总数': len(计),
            '段': [态(s) for s in 计],
            '当前': [{'id': s['id'], '名': s['名'], '全': s['全'], '态': 态(s)} for s in 当前步],
            '等你': [s['id'] for s in 当前步 if s.get('等')],
            '能做': [s['id'] for s in 当前步 if not s['完'] and not s['用户'] and not s.get('选') and not s['停'] and (not s.get('待') or s.get('到了'))],   # 卷四 6.27 待续
            '在做': [s['id'] for s in 当前步 if s['在做']], **({'现在': 现} if 现 else {})}


# ---------- 找任务、动静 ----------

def 跳(d):
    return d in 跳过目录 or d.endswith('.nosync') or d.startswith('.')


def 找任务():
    out = []
    for dp, dns, fns in os.walk(根):
        dns[:] = sorted(d for d in dns if not 跳(d))
        rel = os.path.relpath(dp, 根)
        if rel != '.' and 'TODO.md' in fns:
            out.append(rel)
    out += sorted({k for k in (目录归属(s['目录']) for s in Codex会话们()) if k and k.split('/')[0] in 外区})   # 她在 Codex 界面开的任务（C2）
    def 键(r):
        g = r.split('/')[0]
        return (母文件夹.index(g) if g in 母文件夹 else 98 if g in 外区 else 99, r)
    return sorted(out, key=键)


def 任务路(rel):
    """任务键 → 目录：「ChatGPT/…」「Codex/…」在她的工作区（C2），别的在 根 下。"""
    ps = rel.split('/', 1)
    if ps[0] in 外区 and len(ps) > 1:
        return os.path.join(外区[ps[0]], ps[1])
    return os.path.join(根, rel)


def 任务键(p):
    """目录（realpath 过的）→ 任务键；根、她的工作区本身和外面的返回 None。"""
    if p.startswith(根 + os.sep):
        return os.path.relpath(p, 根)
    for k, d in 外区.items():
        if p.startswith(d + os.sep):
            return k + '/' + os.path.relpath(p, d)
    return None


def 目录归属(d):
    """会话的工作目录 → 它在干的任务：自己或往上最近一个有 TODO.md 的目录（路上有 归档、备份 这类跳过的目录就不算）；都没有返回 None。"""
    cur = os.path.realpath(d) if d else ''
    k0 = 任务键(cur)
    if not k0:
        return None
    k = k0
    while k:
        if os.path.isfile(os.path.join(任务路(k), 'TODO.md')):
            return k if not any(跳(x) for x in k.split('/')) else None
        k = k.rsplit('/', 1)[0] if '/' in k else ''
        if k in 外区:   # 到了她工作区的最上面一层
            break
    return None


def 名字(rel):
    ps = rel.split('/')
    if ps[0] in 母文件夹 and len(ps) > 1:
        return ps[0], '·'.join(ps[1:])
    if ps[0] in 外区 and len(ps) > 1:
        return 'Codex', '·'.join(ps[1:])
    if not 母文件夹 and len(ps) > 1:   # 没设分组：工作区下第一层每个文件夹一组
        return ps[0], '·'.join(ps[1:])
    return '其他', '·'.join(ps)


def 标题名(path):
    """TODO 第一行的标题当名字：去掉括号里的话和 TODO 字样（例：「示例 MV 卷二（场景版）· TODO」→「示例 MV 卷二」）。"""
    try:
        with open(path, encoding='utf-8') as f:
            全 = f.read()
            for l in 全.split('\n')[:6]:
                if l.startswith('# '):
                    s = l[2:]
                    while True:   # 括号里套括号（「…补跑（推荐）」）」）：由里往外一层层去，不留半截
                        s2 = re.sub(r'（[^（）]*）|\([^()]*\)', '', s)
                        if s2 == s:
                            break
                        s = s2
                    s = re.sub(r'TODO', '', s)
                    s = re.sub(r'\s+', ' ', s).strip(' ·—-:：|')
                    if ' · ' in s and 一级标题数(全) >= 2:   # 一轮一个一级标题（盯跑这类）：名字取「·」前面那截，不拿某一轮的标题当名字（卷四 6.12）
                        s = s.split(' · ', 1)[0].strip()
                    return s
    except (OSError, ValueError):   # ValueError：编码坏了
        pass
    return ''


def 最近改动(rel, 批量窗):
    """任务目录里最近改过的文件（跳过 .nosync、归档、资料）；批量整理的时刻不算。"""
    最近, 文件, 真 = 0, '', 0
    for dp, dns, fns in os.walk(任务路(rel)):
        dns[:] = [d for d in dns if not 跳(d)]
        for f in fns:
            if f.startswith('.'):
                continue
            try:
                t = os.path.getmtime(os.path.join(dp, f))
            except OSError:
                continue
            if t > 最近:
                最近, 文件 = t, os.path.relpath(os.path.join(dp, f), 任务路(rel))
            if t > 真 and not any(a <= t < b for a, b in 批量窗):
                真 = t
    return 最近, 文件, 真


def 批量窗们(任务们):
    """很多任务的 TODO 在同两分钟里一起被改（比如 10-28 整理母文件夹），那两分钟不算动静。"""
    桶 = {}
    for rel in 任务们:
        try:
            t = os.path.getmtime(os.path.join(任务路(rel), 'TODO.md'))
        except OSError:
            continue
        桶.setdefault(int(t // 120), set()).add(rel)
    return [(k * 120 - 60, k * 120 + 180) for k, v in 桶.items() if len(v) >= 6]


# ---------- 灯 ----------

def 数据路(名):
    os.makedirs(数据, exist_ok=True)
    return os.path.join(数据, 名)


class 锁:
    def __init__(s, 名='.锁'):   # 不可重入：拿着一把时别再拿同名的（读 Codex 记录用另一把，里面还要记灯）
        s.名 = 名

    def __enter__(s):
        s.f = open(数据路(s.名), 'w')
        fcntl.flock(s.f, fcntl.LOCK_EX)
        return s

    def __exit__(s, *a):
        fcntl.flock(s.f, fcntl.LOCK_UN)
        s.f.close()


def 进程在(pid):
    try:
        os.kill(int(pid), 0)
        return True
    except PermissionError:
        return True
    except (OSError, ValueError, TypeError):
        return False


def 记灯(任务, 谁, 开, **kw):
    e = {'时间': time.time(), '任务': 任务, '谁': 谁, '开': 开}
    e.update(kw)
    with 锁():
        with open(数据路('开关.jsonl'), 'a', encoding='utf-8') as f:
            f.write(json.dumps(e, ensure_ascii=False) + '\n')


def 末条们():
    """开关.jsonl 里每个「任务 × 谁 × 会话 × 是不是 跑」的最后一条：两个会话干同一个任务不互相覆盖；
    跑 的命令和会话本身的灯分开记，命令跑完不关会话的灯。"""
    末 = {}
    p = 数据路('开关.jsonl')
    if os.path.exists(p):
        for l in open(p, encoding='utf-8', errors='replace'):
            try:
                e = json.loads(l)
            except ValueError:
                continue
            if isinstance(e, dict):
                末[(e.get('任务'), e.get('谁'), e.get('会话') or '', bool(e.get('跑')))] = e
    return 末


def 灯们():
    """{任务: [灯]}。态「干」：开着、没过租期、进程（有的话）还在。
    态「等」：收工了（交付，等你看），或者开着但 30 分钟没续期（多半是那一轮结束了、在等你回话）。
    完工、你点「知道了」、跑 的命令结束，就不显示。"""
    now = time.time()
    out = {}
    for (任务, 谁, _, 跑), e in 末条们().items():
        t0 = e.get('时间') or 0
        if e.get('开'):
            if e.get('pid'):
                if not 进程在(e['pid']):
                    continue
                态 = '干'
            else:
                态 = '干' if now - t0 <= e.get('租', 租期) else '等'
        elif e.get('等你'):
            态 = '等'
        else:
            continue
        l = {'谁': 谁, '说': e.get('说', ''), '格子': e.get('格子') or [], '预计': e.get('预计'), '开始': t0, '态': 态,
             '题': e.get('题', ''), '对不上': e.get('对不上', ''), '会话': e.get('会话') or '', '接入': e.get('接入', ''),
             '要你': bool(e.get('开') and e.get('要你')),
             '收工': bool(not e.get('开') and e.get('等你') and e.get('收工'))}   # 6.26：会话说做完了、用户还没看，名牌写「收工」，用户点知道了或回话才撤   # 6.24 乙：回复写了等你、后台还在跑，名牌写「等你」、亮片照走
        if e.get('开') and 态 == '等':
            l['没续期'] = True
        out.setdefault(任务, []).append(l)
    return out


def 分钟前(t):
    return f'{max(0, round((time.time() - t) / 60))} 分钟前' if t else ''


def 会话信息():
    """干活的是哪个会话：BAN_SESSION、BAN_HARNESS（别家照这个传）> Claude 桌面会话号。"""
    if os.environ.get('BAN_SESSION'):
        return os.environ['BAN_SESSION'], os.environ.get('BAN_HARNESS', '')
    s = os.environ.get('CLAUDE_CODE_HOST_SESSION_ID', '')
    return s, ('claude' if s else '')


def 会话的任务(会):
    """这个会话最近一条开关记录的任务（插件只给会话号、不写任务时用）。"""
    任务 = None
    p = 数据路('开关.jsonl')
    if 会 and os.path.exists(p):
        for l in open(p, encoding='utf-8', errors='replace'):
            try:
                e = json.loads(l)
            except ValueError:
                continue
            if isinstance(e, dict) and e.get('会话') == 会 and e.get('任务'):
                任务 = e['任务']
    return 任务


def 等着的(e, now=None):
    """这条记录现在是不是「等你」：收工交付的，或者开着但过了租期的。"""
    now = now or time.time()
    if e.get('开'):
        return not e.get('pid') and now - (e.get('时间') or 0) > e.get('租', 租期)
    return bool(e.get('等你'))


def 绑定们():
    """{任务: (会话, 接入)}：每个任务最近在本区干它的会话（接手、你在看板上的动作投给它、没有会话号的名牌点进它）。
    卷四 6.23（用户 11-04 06:0x：跨区是新增一个干活的，不替换原来的）：在这个任务上最后一盏灯写着「跨区施工」的会话不算，
    它是从别的任务顺手过来改东西的；你点「知道了」那条也不改绑定。名牌各点进各的会话，靠每盏灯自己带的会话号（一片() 的「链」）。"""
    return 绑定和时()[0]


def 绑定和时():
    """(绑定, 时)：绑定同 绑定们()；时 = {任务: 本区会话在这个任务上最后一条记录的时刻}（卷四 6.27 待续用）。"""
    末, 跨, 时们 = {}, {}, {}
    p = 数据路('开关.jsonl')
    if os.path.exists(p):
        for l in open(p, encoding='utf-8', errors='replace'):
            try:
                e = json.loads(l)
            except ValueError:
                continue
            if not isinstance(e, dict) or not e.get('会话') or e.get('由') == '用户点知道了':
                continue
            k = (e.get('任务'), e['会话'])
            if e.get('开') or e.get('等你'):
                跨[k] = str(e.get('说', '')).startswith('跨区施工')
            末.pop(k, None)   # 挪到最后：按最近一条记录排先后
            末[k] = e.get('接入', '')
            时们[k] = e.get('时间') or 0
    out, 时 = {}, {}
    for (任务, 会), 接 in 末.items():
        if not 跨.get((任务, 会)):
            out[任务] = (会, 接)
            时[任务] = 时们[(任务, 会)]
    return out, 时


def 接入们():
    """接入/*.json：{接入名: {打开会话, 新会话, 接手话}}。"""
    out = {}
    try:
        fs = sorted(os.listdir(接入目录))
    except OSError:
        return out
    for f in fs:
        if f.endswith('.json'):
            try:
                out[f[:-5]] = json.load(open(os.path.join(接入目录, f), encoding='utf-8'))
            except (OSError, ValueError):
                pass
    return out


def 开会话链(会, 接, 接们):
    """打开这个会话的链接；没有会话号、这家没写怎么打开，就是空的。"""
    j = 接们.get(接 or 'claude') or (next(iter(接们.values())) if 接们 else None)
    return j['打开会话'].replace('{会话}', quote(会, safe='')) if 会 and j and j.get('打开会话') else ''


def 带链(灯列, 接们):
    """每盏有会话号的灯带上打开它那个会话的链接（卷四 6.23：名牌各点进各的会话）。"""
    return [dict(l, 链=开会话链(l['会话'], l.get('接入', ''), 接们)) if l.get('会话') else l for l in 灯列]


def 会话链接(rel, 名, 绑, 接们):
    """有绑定：打开那个会话；没有：在任务目录开新会话、带上接手的第一句话。"""
    会, 接 = 绑.get(rel, ('', ''))
    j = 接们.get(接 or ('codex' if rel.split('/')[0] in 外区 else 'claude')) or (next(iter(接们.values())) if 接们 else None)   # 她工作区里的任务，接手默认开 Codex 会话（C4）
    if not j:
        return ''
    目录 = 任务路(rel)
    if 会 and j.get('打开会话'):
        return 开会话链(会, 接, 接们)
    if j.get('新会话'):
        话 = j.get('接手话', '').replace('{名}', 名).replace('{目录}', 目录).replace('{板}', os.path.join(工具, '板.py'))
        return j['新会话'].replace('{工作区}', quote(根, safe='')).replace('{目录}', quote(目录, safe='')).replace('{话}', quote(话, safe=''))   # {工作区}：11-03 起接手在主工作区开
    return ''


def 投信(任务, 摘要):
    """你在看板上的动作，投进在干这个任务的会话的信箱 数据.nosync/信箱/<会话>.jsonl；没绑定的投 待领.jsonl。
    Claude 那边由插件「无限表格监听」读自己的信箱，你停手一会儿后发进会话。"""
    会 = 绑定们().get(任务, ('', ''))[0]
    d = os.path.join(数据, '信箱')
    os.makedirs(d, exist_ok=True)
    p = os.path.join(d, (re.sub(r'[^A-Za-z0-9_.-]', '_', 会) if 会 else '待领') + '.jsonl')
    with 锁():
        号 = 0
        if os.path.exists(p):
            for l in open(p, encoding='utf-8', errors='replace'):
                try:
                    号 = max(号, int(json.loads(l).get('号', 0)))
                except (ValueError, TypeError, AttributeError):
                    pass
        e = {'号': 号 + 1, '时间': datetime.now().strftime('%Y-%m-%d %H:%M:%S'), '秒': round(time.time(), 3), '任务': 任务, '名': 名字(任务)[1],
             '摘要': 摘要, '会话': 会}
        with open(p, 'a', encoding='utf-8') as f:
            f.write(json.dumps(e, ensure_ascii=False) + '\n')
    return e


def 施工区摘要(z, a):
    """一条施工区事件写成一句话，开头是区名（MV·V2：……）。"""
    号, op, 名 = a.get(z.条目, ''), a.get('op'), z.名
    if op == '确认':
        return f'{名}·{号}：点头批第 {a.get("批号")} 批'
    if op == '选':   # 用户点已选的那张 = 取消（事件 选=False），别写成「选了」（卷四 6.74）
        return f'{名}·{号}：{"取消选了" if a.get("选") is False else "选了"} {a.get("产出")}'
    if op == '重出':
        return f'{名}·{号}：第 {a.get("批号")} 批重出' + (f'（{str(a["意见"])[:200]}）' if a.get('意见') else '')
    if op == '意见':
        return f'{名}·{号}{"·" + str(a["挂"]) if a.get("挂") else ""}：意见「{str(a.get("文", ""))[:300]}」'
    if op == '留言':
        return f'{名}：留言「{str(a.get("文", ""))[:300]}」'
    return f'{名}·{号}：{op}' if 号 else f'{名}：{op}'


# 卷四 6.67（用户 11-06 02:4x：「五步是底层状态机，不是五种新 UI」，界面复用名牌、选框、颜色只换字；「改成全手动吧」；10 分钟没叫醒左下角红点）：
# 施工区每格的状态从施工台事件、Claude已读、这个任务的灯里算，不另记：
#   改了（用户改了、Claude 还没读到）→ 施工（Claude 读表就算接手、灯亮着）→ 停下时：验收（Claude 后来改过这格）/ 等你（没改，要问用户）→ 用户点名牌 = 知道了，框消失
# 选、通过是用户拍板，Claude 读到就算完；只认换上那一刻以后的事件（起点），旧账不挂框。每个区一份状态文件（登记里的「态」，默认 施工区-区号.json）
# 记 起点、已发（叫醒发到第几号）、验收（每格用户点知道了时的事件号）。格子名「号:行名」，行名是 区域.json「行」里的名字（字段落在哪行、候选栏在哪行、意见挂头一行）
_拍板 = {'选', '通过', '取消通过'}
_要动手 = {'改格', '确认', '撤回确认', '重出', '撤回重出', '意见'}


def 读施工区(z):
    try:
        with open(z.态文件, encoding='utf-8') as f:
            x = json.load(f)
    except (OSError, ValueError):
        x = {}
    if '起点' not in x:
        x = {'起点': (z.读() or {}).get('事件号', 0), '已发': 0, '验收': {}}
        写施工区(z, x)
    return x


def 写施工区(z, x):
    os.makedirs(os.path.dirname(z.态文件), exist_ok=True)
    tmp = z.态文件 + '.tmp'
    with open(tmp, 'w', encoding='utf-8') as f:
        json.dump(x, f, ensure_ascii=False)
    os.replace(tmp, z.态文件)


def _行表(z):
    """区域.json 的「行」：字段 → 行名、候选栏 → 行名、头一行的名字（意见、通过、改了别的字段都挂这行）"""
    字行, 栏行, 头 = {}, {}, None
    for r in z.配.get('行') or []:
        if r.get('类') == '头':
            头 = 头 or r['名']
            continue
        for f in r.get('字段') or []:
            字行.setdefault(f, r['名'])
        if r.get('栏'):
            栏行[r['栏']] = r['名']
    return 字行, 栏行, 头 or '号'


def _栏行(z, 栏):
    栏行 = _行表(z)[1]
    return 栏行.get(栏 or z.默认栏) or 栏行.get(z.默认栏) or ''


def _批行(z, j, 批号):
    for b in (j.get('批次') or []) + ([j['下一批']] if j.get('下一批') else []):
        if b and b.get('号') == 批号:
            return _栏行(z, b.get('栏'))
    return ''


def _事件格(z, e, j):
    """事件落在哪几格（号:行名，行名就是施工区表的字段行）"""
    号, 做 = e.get(z.条目), e.get('做')
    if not 号 or not j:
        return []
    字行, _, 头 = _行表(z)
    if 做 == '改格':
        fs = e.get('字段')
        return sorted({f'{号}:{字行.get(f, 头)}' for f in (fs if isinstance(fs, list) else [fs]) if f})
    if 做 in ('确认', '撤回确认', '重出', '撤回重出', '批', '出', '交', '撤批', '代确认'):
        行 = _批行(z, j, e.get('批号'))
        return [f'{号}:{行}'] if 行 else []
    if 做 == '选':
        for b in j.get('批次') or []:
            if any(q.get('id') == e.get('产出') for q in b.get('产出') or []):
                return [f'{号}:{_栏行(z, b.get("栏"))}']
        return []
    if 做 in ('通过', '取消通过', '意见', '说', '处理', '接'):
        return [f'{号}:{头}']
    return []


def 施工区态(z, 灯=()):
    st = z.读() if z else None
    if not st:
        return None
    x = 读施工区(z)
    起, R, 发, 验 = x.get('起点', 0), st.get('Claude已读', 0), x.get('已发', 0), x.get('验收') or {}
    条表 = {j['号']: j for j in st.get(z.条目, [])}
    用, 拍, 克, 克做, 未发, 未发格 = {}, {}, {}, {}, [], set()
    for e in z.读事件(起):
        gs = _事件格(z, e, 条表.get(e.get(z.条目)))
        for g in gs:
            if e.get('谁') == '用户':
                (拍 if e.get('做') in _拍板 else 用)[g] = e['号']
            else:
                克[g], 克做[g] = e['号'], e.get('做')
        if e.get('谁') == '用户' and e['号'] > 发 and (e.get('做') in _拍板 or e.get('做') in _要动手):
            未发.append(e)
            未发格.update(gs)
    在干 = any(l.get('谁') == 'Claude' and l.get('态') != '等' and not l.get('要你') for l in 灯)
    格 = {}
    for g in set(用) | set(拍) | set(克):
        a, u, t, c = 验.get(g, 0), 用.get(g, 0), 拍.get(g, 0), 克.get(g, 0)
        if max(u, t) > max(a, R):
            格[g] = '改了'
        elif u > a or c > a:
            格[g] = '施工' if 在干 else ('验收' if c > u and 克做.get(g) != '批' else '等你')
    return {'格': 格, '未发': len(未发), '未发格': len(未发格), '最早': min((e.get('时间', '') for e in 未发), default=''), '读到': R}


def 施工区叫醒(z):
    """全手动（卷四 6.67）：用户点「叫醒 Claude」才把没发的改动按格打包成一条，投进做这个施工区的会话的信箱；插件照旧在用户停手 20 秒后送进会话"""
    st = z.读() or {}
    x = 读施工区(z)
    条表 = {j['号']: j for j in st.get(z.条目, [])}
    新 = [e for e in z.读事件(max(x.get('起点', 0), x.get('已发', 0))) if e.get('谁') == '用户' and (e.get('做') in _拍板 or e.get('做') in _要动手)]
    if not 新:
        return {'ok': True, '发了': 0}
    行, 格们 = [], set()
    for e in 新:
        j = 条表.get(e.get(z.条目), {})
        gs = _事件格(z, e, j)
        格们.update(gs)
        处 = '、'.join(g.split(':', 1)[1] for g in gs)
        做 = e.get('做')
        if 做 == '改格':
            f = e.get('字段')
            行.append(f'{e.get(z.条目)}·{处}：改了「{f}」，现在是「{str(j.get(f, "") if isinstance(f, str) else "")[:80]}」')
        elif 做 == '意见':
            文 = next((y.get('文', '') for y in reversed(j.get('意见') or []) if y.get('谁') == '用户'), '')
            行.append(f'{e.get(z.条目)}：意见「{str(文)[:200]}」')
        else:
            行.append(施工区摘要(z, {**e, 'op': 做}).replace(f'{z.名}·', '', 1) + (f'（{处}）' if 处 else ''))
    任务 = z.任务
    摘要 = f'{z.名} 施工区：用户改了 {len(格们)} 格，叫醒你\n' + '\n'.join('· ' + l for l in 行[:40]) + ('\n· ……还有，板.py 列 看全' if len(行) > 40 else '') + '\n（做完交付时带上这几格，看板会把格子标成「验收」）'
    e = 投信(任务, 摘要)
    with 锁():
        x = 读施工区(z)
        x['已发'] = max(x.get('已发', 0), 新[-1]['号'])
        写施工区(z, x)
    return {'ok': True, '发了': len(新), '格': len(格们), '会话': e.get('会话', '')}


def 派工灯(任务们):
    """派工账本里「运行中」、进程还在的行 → 对到任务目录。"""
    out = {}
    if not os.path.exists(账本):
        return out
    dirs = sorted(任务们, key=len, reverse=True)
    try:
        rows = list(csv.DictReader(open(账本, encoding='utf-8')))
    except (OSError, csv.Error):
        return out
    for r in rows:
        if r.get('状态') != '运行中' or not 进程在(r.get('pid')):
            continue
        d = os.path.realpath(os.path.expanduser(r.get('目录') or ''))
        rel = 任务键(d) or ''
        任务 = next((t for t in dirs if rel == t or rel.startswith(t + '/')), None)
        if not 任务:
            continue
        谁 = {'k31': 'K31', 'k3': 'K3', 'k28': 'K28', 'flash': 'flash'}.get(r.get('模型', ''), r.get('模型', '工人'))
        try:
            开始 = datetime.strptime(f'{r["日期"]} {r["开始时间"]}', '%Y-%m-%d %H:%M:%S').timestamp()
        except (KeyError, ValueError):
            开始 = None
        out.setdefault(任务, []).append({'谁': 谁, '说': r.get('标签', ''), '开始': 开始, '态': '干'})
    return out


def 规格(g):
    """格子名统一成「号:栏」：「区名·号·栏」「号·栏」「号:栏」都记成 号:栏，栏的别名照各区 区域.json 的「格子别名」换
    （MV：MV·V2·画面、V2·画面、V2:画面 都记成 V2:图片，分镜→文、画面→图片、视频→样片）；别的格子（比如步骤 2.6）照原样。"""
    s = str(g).strip()
    区们 = list(施工区们().values())
    for z in 区们:
        s2 = re.sub('^' + re.escape(z.名) + '[·:]', '', s)
        if s2 != s:
            s = s2
            break
    别, 栏 = {}, {'文'}
    for z in 区们:
        别.update(z.配.get('格子别名') or {})
        栏.update(z.栏们)
    m = re.match(r'^(.+?)[·:](' + '|'.join(re.escape(x) for x in sorted(set(别) | 栏, key=len, reverse=True)) + r')$', s)
    if not m:
        return s
    return m.group(1) + ':' + 别.get(m.group(2), m.group(2))


def 撞了(灯列):
    """同一格有两个以上的谁认领 → [{'格': 'V2:图片', '谁': ['Claude', 'K31']}]。"""
    格谁 = {}
    for l in 灯列:
        for g in l.get('格子') or []:
            格谁.setdefault(g, [])
            if l['谁'] not in 格谁[g]:
                格谁[g].append(l['谁'])
    return [{'格': g, '谁': w} for g, w in 格谁.items() if len(w) > 1]


def 解任务(arg):
    a = arg.rstrip('/')
    if a.startswith('零活:'):   # 没有任务目录的会话（卷二 7.10）
        return a
    p = os.path.realpath(a if os.path.isabs(a) else 任务路(a))
    if 任务键(p) and os.path.isdir(p):
        return 任务键(p)
    候 = [t for t in 找任务() if 名字(t)[1] == a or t.endswith('/' + a) or 名字(t)[1].endswith(a)]
    if len(候) == 1:
        return 候[0]
    raise 错(f'对不上任务「{arg}」' + (f'：有 {len(候)} 个像的（{"、".join(候[:5])}），写全一点' if 候 else '：写任务目录（相对工作区）'))


# ---------- Codex：看板自己读她的会话记录开关灯（11-05 接入 Codex C2、C3） ----------
# 用户 11-05：「codex本身遵守新协议，现在会打状态词的，如果乙只是读就行，如果反复要求手打就不对了」——她不用敲 板.py

_头缓 = {}   # 会话记录文件 → 首行里要的（首行不会变，读一次）


def Codex会话们():
    """她在 Codex 界面开的会话：[{'号', '目录', '文件'}]。子代理（source 是对象、带 parent_thread_id）、命令行 codex exec（出图的临时会话）不算；
    归档了的挪到 archived_sessions，不看。"""
    if not Codex家:
        return []
    out = []
    for f in glob.glob(os.path.join(Codex家, 'sessions', '*', '*', '*', 'rollout-*.jsonl')):
        h = _头缓.get(f)
        if h is None:
            try:
                with open(f, encoding='utf-8', errors='replace') as fh:
                    l = fh.readline()
            except OSError:
                continue
            if not l.endswith('\n'):
                continue   # 首行还没写完，下回再读
            h = {}
            try:
                e = json.loads(l)
                p = e.get('payload') or {}
                if e.get('type') == 'session_meta' and p.get('id') and not p.get('parent_thread_id') and not isinstance(p.get('source'), dict) \
                        and p.get('source') != 'exec' and p.get('originator') != 'codex_exec':
                    h = {'号': str(p['id']), '目录': str(p.get('cwd') or '')}
            except (ValueError, AttributeError, TypeError):
                pass
            _头缓[f] = h
        if h:
            out.append(dict(h, 文件=f))
    return out


def 时刻(s):
    try:
        return datetime.fromisoformat(str(s).replace('Z', '+00:00')).timestamp()
    except ValueError:
        return None


def 说收工(文):
    """用户这一轮说了收工（同插件 ban-listen 的 说收工）：她回【收工】就直接灭灯，不挂「收工」等用户看。"""
    s = (文 or '').strip()
    if s.startswith('<') or s.startswith('【无限表格】'):
        return False
    s = re.sub(r'(?:没|不|别|未|无法|不能|没法)[^，,。.！!？?\n]{0,6}(?:收工|完工)', '', s)
    return bool(re.search(r'(?:收工|完工)(?:吧|啦|呗|就行|就好)|(?:收工|完工)了(?![吗么没？?])|(?:可以|先|就)(?:暂停)?(?:收工|完工)|(?:^|[，,。.！!\s])(?:收工|完工)[。.！!～~\s]*$', s))


def 首句(答):
    s = re.sub(r'^\s*【[^】]{1,4}】\s*', '', 答 or '').strip().split('\n')[0]
    s = re.sub(r'[*`#>]', '', s).strip()
    return s[:60] + ('…' if len(s) > 60 else '')


def 说法(文):
    """灯上那句：用户这一轮说的第一行（同插件 ban-listen 的 说法）。"""
    s = (文 or '').strip()
    if s.startswith('【无限表格】'):
        return '处理你在看板上的动作'
    if not s or s.startswith('<'):
        return '接着干'
    首 = s.split('\n')[0]
    return '「' + (首[:24] + '…' if len(首) > 24 else 首) + '」'


def Codex题们():
    """会话号 → 会话标题（session_index.jsonl，零活那一行当名字）。"""
    out = {}
    try:
        for l in open(os.path.join(Codex家, 'session_index.jsonl'), encoding='utf-8', errors='replace'):
            try:
                e = json.loads(l)
                if e.get('id') and e.get('thread_name'):
                    out[str(e['id'])] = str(e['thread_name'])[:40]
            except (ValueError, AttributeError):
                pass
    except OSError:
        pass
    return out


def Codex读一遍():
    """看她会话记录新写的行，替她开关灯：一轮开始（task_started）→ 施工；一轮结束（task_complete）照最后一条回复开头的状态词：
    等你 → 等你；收工 → 挂「收工」等用户看（用户这一轮说了收工就直接灭）；施工 → 照旧在干（30 分钟没新动静变等你）；没写、旧词 → 等你。
    只看每行的类型、时刻、工作目录、用户那句话说没说收工、回复开头那句。工作目录不在任务里的照状态词亮零活（同 Claude）。
    第一次跑（还没有游标）不补以前的灯：半小时内有动静的照常亮，更早、7 天内动过的只补记「她在这个任务上的会话」（种：名牌点得进去、待续认得、不算收工）。返回 [(任务, 态)]。"""
    if not Codex家:
        return []
    做了 = []
    with 锁('.codex锁'):   # 服务的线程和命令行一起跑也不重复记；记灯拿的是另一把
        p = 数据路('codex游标.json')
        try:
            游 = json.load(open(p, encoding='utf-8'))
        except (OSError, ValueError):
            游 = None
        初次, 游 = 游 is None, 游 or {}
        题们, now, 变 = None, time.time(), 初次
        for s in sorted(Codex会话们(), key=lambda x: x['文件']):   # 文件名带开始时刻：同一任务几个会话，最近开的记在最后（绑定认它）
            f = s['文件']
            try:
                大 = os.path.getsize(f)
            except OSError:
                continue
            g = 游.get(f)
            if g is None:
                g = 游[f] = {'偏': max(0, 大 - 4_000_000) if 初次 else 0, '目录': s['目录'], '态': '', '任': ''}   # 第一次只看最后 4 MB 定现状
            if 大 <= g['偏']:
                continue
            with open(f, 'rb') as fh:
                fh.seek(g['偏'])
                块 = fh.read(大 - g['偏'])
            if g['偏'] and not g.get('齐'):   # 从中间开始读的：丢掉第一截半行
                块 = 块[块.find(b'\n') + 1:] if b'\n' in 块 else b''
                g['偏'] = 大 - len(块)
            g['齐'] = True
            尾 = 块.rfind(b'\n')
            if 尾 < 0:
                continue
            g['偏'] += 尾 + 1
            变 = True
            末事 = None   # 这一块里最后一件：('始',) 或 ('终', 回复, 用户说了收工)
            for l in 块[:尾 + 1].split(b'\n'):
                try:
                    e = json.loads(l)
                except ValueError:
                    continue
                if not isinstance(e, dict) or not isinstance(e.get('payload'), dict):
                    continue
                t, pl = e.get('type'), e['payload']
                pt = pl.get('type')
                g['末'] = 时刻(e.get('timestamp')) or g.get('末') or now
                if t == 'turn_context' and pl.get('cwd'):
                    g['目录'] = str(pl['cwd'])
                elif t == 'event_msg' and pt == 'task_started':
                    末事, g['他收'], g['说'] = ('始',), False, ''
                elif t == 'event_msg' and pt == 'item_completed' and isinstance(pl.get('item'), dict) and pl['item'].get('type') == 'UserMessage':
                    c = pl['item'].get('content')
                    问 = ''.join(x.get('text', '') for x in c if isinstance(x, dict)) if isinstance(c, list) else str(c or '')
                    g['他收'], g['说'] = 说收工(问), 说法(问)
                    if 末事 is None or 末事 == ('始',):
                        末事 = ('始',)   # 用户的话写进来了：灯上那句换成用户这一轮说的
                elif t == 'event_msg' and pt == 'task_complete':
                    末事 = ('终', str(pl.get('last_agent_message') or ''), bool(g.get('他收')))
            任 = 目录归属(g['目录'])
            零 = not 任
            键 = 任 or '零活:' + s['号']
            if g.get('任') and g['任'] != 键 and g.get('态') in ('干', '等', '收'):   # 换了目录、换了任务：旧的那盏关掉
                记灯(g['任'], 'Codex', False, 等你=False, 会话=s['号'], 接入='codex', 由='Codex 记录')
                g['态'] = ''
            g['任'] = 键
            if 零 and 题们 is None:
                题们 = Codex题们()
            题 = {'题': 题们.get(s['号'], '')} if 零 and 题们 and 题们.get(s['号']) else {}
            同 = {'会话': s['号'], '接入': 'codex', '由': 'Codex 记录', **题}
            态, 说, 末 = None, '', g.get('末') or now
            亮着 = g.get('态') in ('干', '等', '收')
            if 初次 and (零 or not 末事 or now - 末 > 租期):   # 第一次读：半小时内有动静的照常亮（在跑的施工、刚交的等你），更早的不补灯；零活要她写过状态词才亮，这时不知道，不亮
                if not 零 and now - 末 <= 七天:
                    记灯(键, 'Codex', False, 等你=False, 种=True, 时间=末, **同)
                    做了.append((键, '种'))
            elif 末事 == ('始',):
                态, 说 = ('干', g.get('说', '')) if (not 零 or 亮着) else (None, '')   # 零活：亮过才跟着开轮亮（同 Claude）
            elif 末事:
                词 = re.match(r'^\s*【(施工|等你|收工)】', 末事[1])
                词 = 词.group(1) if 词 else None
                说 = 首句(末事[1])
                if 零 and not 词 and not 亮着:
                    态 = None   # 没碰任务、也没写状态词的一轮：不亮零活（同 Claude）
                elif 词 == '施工':
                    态 = '干'
                elif 词 == '收工':
                    态 = '灭' if (末事[2] or 零) else '收'
                else:
                    态 = '等'
            elif g.get('态') == '干' and now - g.get('续', 0) > 300:   # 一轮还在跑、又有新动静：续期，那句照旧
                态, 说 = '干', g.get('灯说', '')
            if 态 == '干':
                记灯(键, 'Codex', True, 说=说 or 题.get('题', ''), **同)
                g['续'], g['灯说'] = now, 说
            elif 态 == '等':
                记灯(键, 'Codex', False, 等你=True, 说=说, **同)
            elif 态 == '收':
                记灯(键, 'Codex', False, 等你=True, 收工=True, 说=说, **同)
            elif 态 == '灭':
                记灯(键, 'Codex', False, 等你=False, **同)
            if 态:
                g['态'] = 态
                做了.append((键, 态))
        if 变:
            tmp = p + '.tmp'
            with open(tmp, 'w', encoding='utf-8') as fh:
                json.dump(游, fh, ensure_ascii=False, indent=1)
            os.replace(tmp, p)
    return 做了


# ---------- 施工区（分卷五：通用引擎 施工台.py + 每区一份 区域.json + 看板这边的登记） ----------

_引 = None


def 引擎():
    global _引
    if _引 is None:
        spec = importlib.util.spec_from_file_location('施工台', 施工台文件)
        m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(m)
        _引 = m
    return _引


_区缓 = {'签': None, '值': {}}


def 施工区们():
    """登记过、存档目录里有 区域.json 的施工区：{区号: 引擎.区}，每个多带 号、任务、名、态文件。登记、哪个区的 区域.json 一改就重读。
    测试：BAN_SGT 写「区号=存档目录;…」把区指到副本；DYT_DIR 是老写法，指登记的第一个区（以前只有 MV 一个区）。"""
    try:
        with open(登记文件, encoding='utf-8') as f:
            登 = json.load(f).get('区们') or {}
    except (OSError, ValueError, AttributeError):
        登 = {}
    盖 = {k.strip(): v.strip() for k, v in (x.split('=', 1) for x in os.environ.get('BAN_SGT', '').split(';') if '=' in x)}
    if os.environ.get('DYT_DIR') and 登:
        盖.setdefault(next(iter(登)), os.environ['DYT_DIR'])
    台们 = {号: os.path.join(根, 盖.get(号) or v.get('台') or '') for 号, v in 登.items()}   # 绝对路径照旧，相对的按工作区算
    时们 = []
    for t in 台们.values():
        try:
            时们.append(os.path.getmtime(os.path.join(t, '区域.json')))
        except OSError:
            时们.append(0)
    签 = json.dumps([登, 台们, 时们], ensure_ascii=False)
    if 签 == _区缓['签']:
        return _区缓['值']
    out = {}
    for 号, v in 登.items():
        台 = 台们[号]
        if not os.path.exists(os.path.join(台, '区域.json')):
            continue
        try:
            z = 引擎().区(台, os.path.join(根, v['根']) if v.get('根') else None)
        except (OSError, ValueError, KeyError) as x:
            print(f'施工区 {号} 的 区域.json 读不了：{x}', file=sys.stderr)
            continue
        z.号, z.任务 = 号, v.get('任务') or ''
        z.名 = z.配.get('名') or 号
        z.态文件 = os.path.join(数据, v.get('态') or f'施工区-{号}.json')
        z.边界 = v.get('边界') or {}   # 分卷五 8.9：只限字段那一向占几格（字段格），条目随便加
        out[号] = z
    _区缓.update(签=签, 值=out)
    return out


def 字段格(配):
    """区域.json 的行沿字段方向一共占几格（含第 0 格段名）"""
    return 1 + sum((r.get('高') or 1) for r in 配.get('行') or [])


def 超界(z):
    """分卷五 8.9（用户 11-07 定甲）：区域.json 的行超出登记的边界没有。返回 (边界, 一共几格, 没画的行名)；第一个放不下的行和它后面的都不画（页面照同一个算法）"""
    限 = (z.边界 or {}).get('字段格') or 0
    y, 没 = 1, []
    for r in z.配.get('行') or []:
        h = r.get('高') or 1
        if 没 or (限 and y + h > 限):
            没.append(r['名'])
            continue
        y += h
    return 限, 字段格(z.配), 没


def 超界话(z):
    限, 共, 没 = 超界(z)
    return f'区域.json 的行加起来 {共} 格，超出登记的边界 {限} 格：{"、".join(没)} 没画。要多占格子先找用户批（用户解锁施工区登记、改边界）' if 没 else ''


def 任务的区(rel):
    return next((z for z in 施工区们().values() if z.任务 == rel), None)


def 在出灯(z):
    st = z.读() if z else None
    if not st:
        return []
    out = []
    for j in st[z.条目]:
        if j.get('在出'):
            try:
                b = z.找批(j, j['在出'])
            except Exception:
                b = {}
            out.append({'谁': 'Claude', '说': f'在出 {j["号"]} 第 {j["在出"]} 批（{b.get("内容", "")[:16]}）',
                        '格子': [f'{j["号"]}:{b.get("栏", z.默认栏)}'], '开始': None, '态': '干'})
    return out


# ---------- 看板数据 ----------

_缓 = {'时': 0, '值': None, '签': None}

# ---------- 省电（分卷三 D）：读过的记着，没变不重算 ----------
_找缓 = {'时': 0.0, '值': None}
_读缓 = {}    # TODO 路径 → ((修改时间, 大小, 旧), 读数)
_题缓 = {}    # TODO 路径 → ((修改时间, 大小), 标题)
_改缓 = {}    # 任务 → (算的时刻, 批量窗, 结果)
_改预算 = [0]


def 找任务缓():
    if _找缓['值'] is None or time.time() - _找缓['时'] > 30:
        _找缓.update(时=time.time(), 值=找任务())
    return _找缓['值']


def _键(path, *多):
    try:
        st = os.stat(path)
        return (st.st_mtime_ns, st.st_size) + 多
    except OSError:
        return None


def 读TODO缓(path, 旧):
    k = _键(path, 旧)
    e = _读缓.get(path)
    if k is not None and e and e[0] == k:
        return copy.deepcopy(e[1])
    r = 读TODO(path, 旧=旧)
    if k is not None:
        _读缓[path] = (k, r)
    return copy.deepcopy(r)


def 标题名缓(path):
    k = _键(path)
    e = _题缓.get(path)
    if k is not None and e and e[0] == k:
        return e[1]
    r = 标题名(path)
    if k is not None:
        _题缓[path] = (k, r)
    return r


def 最近改动缓(rel, 窗, 急):
    e = _改缓.get(rel)
    if e and e[1] == 窗 and not 急:
        if time.time() - e[0] < 60 or _改预算[0] <= 0:
            return e[2]
        _改预算[0] -= 1
    r = 最近改动(rel, 窗)
    _改缓[rel] = (time.time(), 窗, r)
    return r


def 页版():
    """页面文件的修改时间：变了，打开着的页面就整页刷新（换版不用按 ⌘R）。"""
    try:
        return str(os.stat(模板).st_mtime_ns)
    except OSError:
        return ''


def 签名():
    """开关灯、看板上的动作、派工账本、施工区登记、各施工区的存档和状态文件的修改时间。页面 1.5 秒问一次，一变就重读（开工后 3 秒内出框）。"""
    区们 = list(施工区们().values())
    out = []
    for p in (数据路('开关.jsonl'), 数据路('事件.jsonl'), 数据路('布局.json'), 账本, 登记文件,
              *[x for z in 区们 for x in (z.态文件, os.path.join(z.台, '状态.json'))]):
        try:
            st = os.stat(p)
            out.append(f'{st.st_mtime_ns}:{st.st_size}')
        except OSError:
            out.append('-')
    return '|'.join(out)


def 读布局():
    try:
        with open(数据路('布局.json'), encoding='utf-8') as f:
            v = json.load(f)
        return v if isinstance(v, dict) else {}
    except (OSError, ValueError):
        return {}


def 改布局(改):
    """看板上手动调格子（11-04 卷二 7.7）：{任务键: {x, y, w, h, 折, 档, 显} 或 null}，按格子记（x 第几格、y 第几行）；带锁合并写回 布局.json。"""
    if not isinstance(改, dict):
        raise 错('改 要写成 {任务: 位置}')
    已有 = set(找任务())
    with 锁():
        v = 读布局()
        for k, b in 改.items():
            if k not in 已有:
                continue   # 不是看板认得的任务（挪走、删了）就不记
            if b is None:
                v.pop(k, None)
                continue
            if not isinstance(b, dict):
                raise 错(f'{k} 的位置要写成 {{x, y, …}}')
            新 = {}
            for f in ('x', 'y', 'w', 'h'):
                if b.get(f) is not None:
                    n = int(b[f])
                    if not 0 <= n <= 999:
                        raise 错(f'{k} 的 {f} = {n} 超出范围')
                    新[f] = n
            for f in ('折', '档', '显', '常驻'):   # 常驻：钉在第 1 层（卷四 6.27）
                if b.get(f):
                    新[f] = True
            if b.get('放下'):   # 放下：从第 1 层拿下来的时刻，本区会话再动、TODO 再改才回来（卷四 6.27）
                放 = float(b['放下'])
                if not 0 < 放 < time.time() + 86400:
                    raise 错(f'{k} 的 放下 = {放} 不像个时刻')
                新['放下'] = 放
            if 新:
                v[k] = 新
            else:
                v.pop(k, None)   # 什么都不剩（比如不钉了）就删掉，免得像排过
        tmp = 数据路('布局.json.tmp')
        with open(tmp, 'w', encoding='utf-8') as f:
            json.dump(v, f, ensure_ascii=False, indent=1)
        os.replace(tmp, 数据路('布局.json'))
    return v


def 看板数据(强制=False):
    签 = 签名()
    if not 强制 and 签 == _缓['签'] and time.time() - _缓['时'] < 4 and _缓['值']:
        return _缓['值']
    任务们 = 找任务缓()
    _改预算[0] = 8
    窗 = 批量窗们(任务们)
    灯 = 灯们()
    派 = 派工灯(任务们)
    (绑, 本区时), 接们 = 绑定和时(), 接入们()
    收工时 = 收工时们()
    布局 = 读布局()
    now = time.time()
    out = []
    for rel in 任务们:
        try:
            out.append(一片(rel, 窗, 灯, 派, now, 绑, 接们, 收工时, 本区时, 布局))
        except Exception as x:   # 一份读坏了只让那一片写「读不出」，总览照常
            g, n = 名字(rel)
            out.append({'键': rel, '组': g, '名': n, '施工区': '', '灯': [], '撞': [], '活动': None, '会话链接': '',
                        '休眠': False, '旧账': False, '读不出': f'读这份时出错：{type(x).__name__} {x}'[:200], '做完': False})
    for rel, ls in 灯.items():   # 零活：没有任务目录的会话（查询、小任务），照回复的状态词亮一行，进度条占位（卷二 7.10，用户 11-04 01:2x）
        if not str(rel).startswith('零活:'):
            continue
        n = next((l['题'] for l in ls if l.get('题')), '') or next((l['说'] for l in ls if l.get('说')), '') or '零活'
        n = n.strip('「」') or '零活'
        out.append({'键': rel, '组': '零活', '名': n, '施工区': '', '灯': 带链(ls, 接们), '撞': [], '会话': 绑.get(rel, ('', ''))[0],
                    '会话链接': 会话链接(rel, n, 绑, 接们), '活动': None, '休眠': False, '旧账': False, '做完': False, '占位': True,
                    '模式': '零活', '完成': 0, '总数': 0, '节': '', '段': [], '当前': [], '等你': [], '在做': []})
    v = {'时间': datetime.now().strftime('%m-%d %H:%M:%S'), '任务': out, '布局': 布局,
         '施工区们': {z.号: {'名': z.名, '任务': z.任务, '配': z.配, '边界': z.边界} for z in 施工区们().values()}}   # 分卷五：页面照各区的 区域.json 画、只画到边界
    _缓.update(时=time.time(), 值=v, 签=签)
    return v


def 收工时们():
    """每个任务最近一次「会话自己收工」（完工灭灯，不是用户点「知道了」）的时刻；之后又开了灯、等你的不算（卷四 6.15）。
    关掉的是「跨区施工」那盏（顺手在别的任务里改了东西，一轮结束插件关掉）也不算：那不是对它说收工"""
    末, 开说 = {}, {}
    p = 数据路('开关.jsonl')
    if os.path.exists(p):
        for l in open(p, encoding='utf-8', errors='replace'):
            try:
                e = json.loads(l)
            except ValueError:
                continue
            if isinstance(e, dict):
                k = (e.get('任务'), e.get('谁'), e.get('会话') or '', bool(e.get('跑')))
                末[k] = e
                if e.get('开'):
                    开说[k] = str(e.get('说', ''))
    最近, 收 = {}, {}
    for k, e in 末.items():
        t = e.get('时间') or 0
        if t > 最近.get(k[0], (0, None, None))[0]:
            最近[k[0]] = (t, e, k)
    for 任务, (t, e, k) in 最近.items():
        if not e.get('开') and not e.get('等你') and e.get('由') != '用户点知道了' and not e.get('种') and not 开说.get(k, '').startswith('跨区施工'):   # 种：接入 Codex 时补记的「她以前在这个任务上的会话」，不是收工
            收[任务] = t
    return 收


def 一片(rel, 窗, 灯, 派, now, 绑, 接们, 收工时=None, 本区时=None, 布局=None):
    """总览里的一个任务：名字、TODO 读数、谁开着灯、动静。"""
    g, n = 名字(rel)
    n = 标题名缓(os.path.join(任务路(rel), 'TODO.md')) or n
    最近, 文件, 真 = 最近改动缓(rel, 窗, bool(灯.get(rel) or 派.get(rel)))
    try:
        tm = os.path.getmtime(os.path.join(任务路(rel), 'TODO.md'))
    except OSError:
        tm = 0
    tm真 = tm if not any(a <= tm < b for a, b in 窗) else 真
    旧 = now - max(tm真, 0) > 七天
    r = 读TODO缓(os.path.join(任务路(rel), 'TODO.md'), 旧)
    亮 = list(灯.get(rel, [])) + list(派.get(rel, []))
    z = 任务的区(rel)
    if z:
        亮 += 在出灯(z)
    亮 = 带链(亮, 接们)
    t = {'键': rel, '组': g, '名': n, '施工区': z.号 if z else '', '灯': 亮, '撞': 撞了(亮),
         '会话': 绑.get(rel, ('', ''))[0], '会话链接': 会话链接(rel, n, 绑, 接们),
         '接入': 绑.get(rel, ('', ''))[1] or ('codex' if rel.split('/')[0] in 外区 else 'claude'),   # 右栏的接手、投递说明按这家写（C4）
         '活动': {'时间': 最近, '文件': 文件} if now - 最近 < 600 else None,
         '休眠': (not 亮) and now - 真 > 七天, '旧账': 旧}
    t.update(r)
    if z:
        t['施工区态'] = 施工区态(z, 亮)   # 卷四 6.67：每格状态、没发的改动
    t['做完'] = bool(r.get('总数')) and r['完成'] == r['总数'] and not 亮
    # 待续（卷四 6.26 乙，用户 11-05：熄灯只摘掉负责人的框，不把任务撤下第 1 层）：没人亮着灯，本区会话 7 天内动过、当前这一段还有我能接着做的，
    # 或者用户钉在了第 1 层（常驻）；用户点了「放下」，要等本区会话再动、TODO 再改才回来
    b = (布局 or {}).get(rel) or {}
    if not 亮 and not r.get('读不出'):
        能做, 本 = list(r.get('能做') or []), (本区时 or {}).get(rel, 0)
        常驻 = bool(b.get('常驻'))
        if 常驻 or (能做 and rel in 绑 and now - 本 <= 七天 and (b.get('放下') or 0) < max(本, tm真)):
            t['待续'] = {'步': 能做, '常驻': 常驻, '说': '；'.join(x for x in (
                f'还有 {len(能做)} 步能接着做：' + '、'.join(能做[:3]) + ('…' if len(能做) > 3 else '') if 能做 else '',
                '钉在第 1 层' if 常驻 else '') if x) + '；点名牌进它的会话，说「继续」'}
    收 = (收工时 or {}).get(rel)
    if 收 and not 亮 and r.get('等你') and tm <= 收 and now - 收 < 七天:   # 收工核对（卷四 6.15）：说收工了，TODO 里还挂着要你做的；TODO 一改就消失
        t['收工疑'] = {'时': 收, '步': list(r['等你'])}
    return t


# ---------- 你在看板上的动作 ----------

def 读板事件(起=0):
    p = 数据路('事件.jsonl')
    out = []
    if os.path.exists(p):
        for l in open(p, encoding='utf-8', errors='replace'):
            try:
                e = json.loads(l)
                if e['号'] > 起:
                    out.append(e)
            except (ValueError, KeyError, TypeError):   # 坏行（写到一半断电之类）跳过
                continue
    return out


def 板操作(a):
    op = a.get('op')
    任务 = a.get('任务', '')
    零活 = op == '知道了' and str(任务).startswith('零活:')   # 6.29：零活那一行（没有任务目录的会话）也能点知道了；做完你交代的事都标等你以后，它会常挂着
    if not 零活 and not os.path.isfile(os.path.join(任务路(任务), 'TODO.md')):
        raise 错('没有这个任务')
    if op == '知道了':   # 点了「等你」的名牌：框消失（不进信箱，不叫醒谁）
        谁 = str(a.get('谁', '')).strip()
        if not 谁:
            raise 错('要写是谁的名牌')
        清了 = 0
        for (t2, w, 会, 跑), e2 in 末条们().items():   # 每个会话各一盏，都清（只清等你的，在干的不动）
            if t2 == 任务 and w == 谁 and not 跑 and 等着的(e2):
                记灯(任务, 谁, False, 等你=False, 会话=会, 由='用户点知道了')
                清了 += 1
        if not 清了:
            记灯(任务, 谁, False, 等你=False, 由='用户点知道了')
        return {'做': '知道了', '任务': 任务, '谁': 谁}
    e = {'谁': '用户', '时间': datetime.now().strftime('%Y-%m-%d %H:%M:%S'), '任务': 任务, '步骤': str(a.get('步骤', ''))}
    if op == '点':
        if a.get('值') not in ('做完了', '还没', '不做了'):
            raise 错('只能点 做完了 / 还没 / 不做了')
        e.update(做='点', 值=a['值'])
    elif op == '意见':
        话 = str(a.get('文', '')).strip()
        if not 话:
            raise 错('意见是空的')
        e.update(做='意见', 文=话[:8000])
    else:
        raise 错(f'不认识的操作：{op}')
    with 锁():
        e['号'] = (读板事件()[-1]['号'] if 读板事件() else 0) + 1
        with open(数据路('事件.jsonl'), 'a', encoding='utf-8') as f:
            f.write(json.dumps(e, ensure_ascii=False) + '\n')
    名 = 名字(任务)[1]
    投信(任务, f'{名}·{e["步骤"]}：点了「{e["值"]}」' if e['做'] == '点' else f'{名}{"·" + e["步骤"] if e["步骤"] else ""}：意见「{e["文"][:300]}」')
    return e


def 已读(新=None, **叫醒过):
    """板 = 「列」读到第几号；叫醒板、叫醒台们（每个施工区一个号） = 「等」为哪几号叫醒过（没跑「列」又挂上「等」，同一批不再叫醒第二次）。"""
    p = 数据路('已读.json')
    try:
        d = json.load(open(p, encoding='utf-8'))
        d['板'] = int(d.get('板', 0))
    except (OSError, ValueError, TypeError, AttributeError):   # 没有或读坏了：从 0 起（宁可多列一遍，不漏）
        d = {'板': 0}
    if 新 is not None or 叫醒过:
        if 新 is not None:
            d['板'] = 新
        d.update(叫醒过)
        with open(p + '.tmp', 'w', encoding='utf-8') as f:
            json.dump(d, f, ensure_ascii=False)
        os.replace(p + '.tmp', p)
    return d


# ---------- 估时对账（11-04 卷二 7.2）：把「实际 ÷ 预计」在估时那一刻摆到眼前 ----------
# 用户 11-02：「你预估3个多小时，实际20分钟做完」「核心协议里面写低于1/4主动复盘，好像也没有触发」——模型手里没有实际用时，做快了也没有信号。
# 一段 = 一次带 --预计 的开工，到同一会话下一次带预计的开工、或这个任务收工 / 完工为止；插件每轮开始的续期（不带预计）不算断。
没收工算 = 12 * 3600   # 开了工、12 小时都没收工（别家没插件、忘了收）：这一段不算


def 段们():
    p = 数据路('开关.jsonl')
    out, 开着 = [], {}
    if not os.path.exists(p):
        return out
    for l in open(p, encoding='utf-8', errors='replace'):
        try:
            e = json.loads(l)
        except ValueError:
            continue
        if not isinstance(e, dict) or e.get('跑'):
            continue
        k = (e.get('谁'), e.get('会话') or '')
        d = 开着.get(k)
        if e.get('开') and e.get('预计'):
            if d:
                d['结束'] = e.get('时间')
            d = {'任务': e.get('任务'), '谁': e.get('谁'), '会话': k[1], '说': e.get('说') or '', '预计': e['预计'],
                 '开始': e.get('时间') or 0, '结束': None}
            out.append(d)
            开着[k] = d
        elif not e.get('开') and d and e.get('任务') == d['任务']:
            d['结束'] = e.get('时间')
            开着.pop(k)
    return out


def 实际(d, now):
    s = (d['结束'] if d['结束'] is not None else now) - d['开始']
    return None if s > 没收工算 else s


def 分(s):
    m = s / 60
    return f'{m:.1f}' if m < 10 else str(round(m))


def 报段(d, now, 前):
    """一行：预计几分钟、实际几分钟、几倍；不到四分之一、超过两倍再加一句（核心协议 §2 那两条）。"""
    s = 实际(d, now)
    if s is None:
        return
    x = s / (d['预计'] * 60)
    print(f'{前}「{d["说"] or 名字(d["任务"])[1]}」预计 {d["预计"]} 分钟，实际 {分(s)} 分钟（{x:.2g} 倍）')
    if x < 0.25:
        print('  ⚠ 不到预估的四分之一：照协议补一句估多在哪，剩下的按实际速度重估')
    elif x > 2:
        print('  ⚠ 超过预估一倍：照协议补一句卡在哪、还要多久、要不要换做法')


def 往常(谁, now, 条=5):
    xs = [实际(d, now) and 实际(d, now) / (d['预计'] * 60) for d in 段们() if d['谁'] == 谁 and d['结束'] is not None]
    return [x for x in xs if x][-条:]


def 对账(任务=None, 谁=None, 条=10):
    now = time.time()
    ds = [d for d in 段们() if (not 任务 or d['任务'] == 任务) and (not 谁 or d['谁'] == 谁)][-条:]
    if not ds:
        print('还没有带 --预计 开工的段')
        return
    xs = []
    for d in ds:
        t = time.strftime('%m-%d %H:%M', time.localtime(d['开始']))
        头 = f'{t}  {d["谁"]}  {名字(d["任务"])[1]}  「{d["说"][:30]}」  预计 {d["预计"]}'
        s = 实际(d, now)
        if s is None:
            print(f'{头}，12 小时没收工，不算')
            continue
        x = s / (d['预计'] * 60)
        if d['结束'] is not None:
            xs.append(x)
        print(f'{头} → 实际 {分(s)}{"（还在做）" if d["结束"] is None else ""}  {x:.2g} 倍{" ⚠" if x < 0.25 or x > 2 else ""}')
    if xs:
        print(f'做完的 {len(xs)} 段：中位 {statistics.median(xs):.2g} 倍；不到四分之一 {sum(x < 0.25 for x in xs)} 段，超过两倍 {sum(x > 2 for x in xs)} 段')


def 段(任务):
    """接手要读的（核心 §2、§6 11-04）：还没迁的先打印 交接.md 最上面一条；TODO 的「现在」和在做的段（没标状态的，打印看板认的当前一节）"""
    p = os.path.join(任务路(任务), 'TODO.md')
    try:
        text = open(p, encoding='utf-8').read()
    except OSError as e:
        raise 错(f'打不开 TODO：{e}')
    r = 读TODO(p)
    jp = os.path.join(任务路(任务), '交接.md')
    if os.path.exists(jp):
        jt = open(jp, encoding='utf-8', errors='replace').read()
        m = re.search(r'^## .*?(?=^## |\Z)', jt, re.M | re.S)
        print('—— 还没迁的 交接.md 最上面一条 ——')
        print((m.group(0) if m else jt[:1500]).rstrip())
        print()
    if r.get('读不出'):
        print(f'TODO：{r["读不出"]}')
        return
    要 = set(r.get('当前节') or [])
    print(f'—— {标题名(p) or 任务} · TODO：{r["完成"]}/{r["总数"]}，等你 {"、".join(r["等你"]) or "没有"} ——')
    块们, 框 = [], False
    for l in text.split('\n'):
        if l.lstrip().startswith('```'):
            框 = not 框
        if not 框 and re.match(r'^#{1,3} ', l):
            块们.append([l])
        elif 块们:
            块们[-1].append(l)
    轮印 = False   # 多个一级标题时：当前那一轮的一级标题下面，小节一起打印
    for k, b in enumerate(块们):
        h = b[0]
        题 = h.lstrip('#').strip()
        级 = len(h) - len(h.lstrip('#'))
        if 是现在(题):
            print('\n'.join(b).rstrip() + '\n')
        elif 级 == 1:
            轮印 = 题 in 要
            if 轮印 or (k == 0 and '（开头）' in 要):   # 第一个一级标题下面、第一个小节前面的就是「（开头）」那节
                print('\n'.join(b).rstrip() + '\n')
        elif 题 in 要 or 轮印:
            print('\n'.join(b).rstrip() + '\n')


def 列():
    d = 已读()
    新 = 读板事件(d['板'])
    if 新:
        print(f'看板上你做了 {len(新)} 件：')
        for e in 新:
            名 = 名字(e['任务'])[1]
            if e['做'] == '点':
                print(f'  {e["时间"][5:16]} 【{名} · {e["步骤"]}】点了「{e["值"]}」')
            else:
                print(f'  {e["时间"][5:16]} 【{名}{" · " + e["步骤"] if e["步骤"] else ""}】意见：{e["文"]}')
        已读(新[-1]['号'])
    else:
        print('看板上你没新动作（TODO 那边）')
    for z in 施工区们().values():
        if z.读():
            print(f'—— {z.名} 施工区 ——')
            if 超界话(z):
                print('⚠ ' + 超界话(z))
            z.列()


def 等(静=300, 最长=1800, 小时=12):
    读过 = 已读()
    基 = max(读过['板'], 读过.get('叫醒板', 0))
    区们 = list(施工区们().values())
    台基 = {z.号: max((z.读() or {}).get('Claude已读', 0), (读过.get('叫醒台们') or {}).get(z.号, 0)) for z in 区们}   # 分卷五：每个区各记各的
    首 = None
    起 = time.time()
    while True:
        if 小时 and time.time() - 起 > 小时 * 3600:
            print(f'挂了 {小时} 小时，看板上没动静，等待程序退出。', flush=True)
            return
        板新 = 读板事件(基)
        台新 = {z.号: [e for e in z.读事件(台基[z.号]) if e['谁'] == '用户' and e['做'] in z.叫醒] for z in 区们}
        时们 = [datetime.strptime(e['时间'], '%Y-%m-%d %H:%M:%S').timestamp() for e in 板新]
        时们 += [引擎().解时(e['时间']).timestamp() for es in 台新.values() for e in es]
        if 时们:
            首 = 首 or time.time()
            if time.time() - max(时们) >= 静 or time.time() - 首 >= 最长:
                已读(叫醒板=max([基] + [e['号'] for e in 板新]), 叫醒台们={k: max([台基[k]] + [e['号'] for e in v]) for k, v in 台新.items()})
                print(f'你在看板上动了 {len(时们)} 次。跑「板.py 列」看详情。', flush=True)
                return
        time.sleep(3)


# ---------- 本机服务 ----------

def 解路径(raw):
    """网址里的中文：浏览器会编成 %XX，curl 可能直接发 UTF-8（被当成 latin-1 读进来），两种都还原。"""
    p = unquote(urlparse(raw).path)
    try:
        p = p.encode('latin-1').decode('utf-8')
    except (UnicodeEncodeError, UnicodeDecodeError):
        pass
    return p


def 服务(端口=8770, 父=None):
    if 父:   # 原生小窗起的服务：小窗没了（退出、崩了）就跟着退，不留孤儿进程
        def 看父():
            while True:
                time.sleep(5)
                if not 进程在(父):
                    os._exit(0)
        threading.Thread(target=看父, daemon=True).start()
    if Codex家:   # 接入 Codex（C3）：每 3 秒看一眼她的会话记录有没有新写的，替她开关灯
        def 盯Codex():
            while True:
                try:
                    Codex读一遍()
                except Exception as x:   # 读坏一回不让线程停
                    print('读 Codex 记录出错：', type(x).__name__, x, file=sys.stderr, flush=True)
                time.sleep(3)
        threading.Thread(target=盯Codex, daemon=True).start()
    class 处理(BaseHTTPRequestHandler):
        def log_message(s, *a):
            pass

        def 主机对(s):
            return s.headers.get('Host', '') in (f'127.0.0.1:{端口}', f'localhost:{端口}')

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

        def do_POST(s):
            try:
                s.存()
            except (BrokenPipeError, ConnectionResetError):
                pass

        def 区文件(s, z, rel):
            """施工区里的原文件（引擎的处理类按区的项目目录给，支持 Range）"""
            return z.处理类().文件(s, rel)

        def 缩略(s, z, rel, q):
            """视频的缩略图取第 2 秒（引擎的旧网页取 0.5 秒，片头常是黑的）；图片照引擎的做。"""
            E = 引擎()
            if not rel.lower().endswith(E.视频后缀):
                return z.处理类().缩略(s, rel, q)
            f = z.安全路径(rel)
            if not f or not os.path.isfile(f):
                return s.回(404, {'错': '没有这个文件'})
            try:
                w = max(60, min(1600, int((q.get('w') or ['240'])[0])))
            except ValueError:
                w = 240
            import hashlib
            键 = hashlib.sha1(f'{f}|{os.stat(f).st_mtime}|{w}|2s'.encode('utf-8')).hexdigest()[:20]
            缓 = os.path.join(z.台, '缓存.nosync', '缩略图')
            os.makedirs(缓, exist_ok=True)
            out = os.path.join(缓, 键 + '.jpg')
            if not os.path.exists(out):
                tmp = out + f'.{os.getpid()}.{id(s)}.jpg'
                subprocess.run([E.FFMPEG, '-v', 'error', '-ss', '2', '-i', f, '-frames:v', '1', '-vf', f'scale={w}:-2', '-y', tmp],
                               capture_output=True, timeout=60)
                if not os.path.exists(tmp):
                    subprocess.run([E.FFMPEG, '-v', 'error', '-ss', '0', '-i', f, '-frames:v', '1', '-vf', f'scale={w}:-2', '-y', tmp],
                                   capture_output=True, timeout=60)
                if not os.path.exists(tmp):
                    return s.回(500, {'错': '缩略图没做出来'})
                os.replace(tmp, out)
            with open(out, 'rb') as fh:
                return s.回(200, fh.read(), 'image/jpeg')

        def 取(s):
            if not s.主机对():
                return s.回(403, {'错': '只让本机访问'})
            u = urlparse(s.path)
            p = 解路径(s.path)
            if p in ('/', '/index.html'):
                with open(模板, encoding='utf-8') as f:
                    return s.回(200, f.read(), 'text/html; charset=utf-8')
            if p == '/api/看板':
                return s.回(200, 看板数据())
            if p == '/api/版':
                return s.回(200, {'版': 签名(), '页': 页版(), '进程': os.getpid()})   # 进程号：「板.py 重开」认新服务用（卷二 7.39）
            m = re.match(r'^/api/施工区/([^/]+)(/rev)?$', p)   # 分卷五：每个区一套地址（MV 的区号是 mv，老地址照旧）
            if m:
                z = 施工区们().get(m.group(1))
                st = z.读() if z else None
                if m.group(2):
                    return s.回(200, {'改动号': (st or {}).get('改动号', 0)})
                return s.回(200, z.带算(st)) if st else s.回(404, {'错': f'没有 {z.名 if z else m.group(1)} 存档'})
            m = re.match(r'^/([^/]+)/(f|t)/(.+)$', p)
            if m and m.group(1) in 施工区们():
                z = 施工区们()[m.group(1)]
                return s.区文件(z, m.group(3)) if m.group(2) == 'f' else s.缩略(z, m.group(3), parse_qs(u.query))
            if p == '/favicon.ico' or p.startswith('/图标/'):   # 标志（和 Qlimen 共用的图形）：网页标签图标、顶栏的图形
                名 = 'favicon.ico' if p == '/favicon.ico' else p[len('/图标/'):]
                f = os.path.join(工具, '图标', 名)
                if '/' in 名 or 名.startswith('.') or not os.path.isfile(f):
                    return s.回(404, {'错': '没有这个图标'})
                类 = {'.ico': 'image/x-icon', '.svg': 'image/svg+xml', '.png': 'image/png'}.get(os.path.splitext(名)[1].lower(), 'application/octet-stream')
                with open(f, 'rb') as fh:
                    return s.回(200, fh.read(), 类)
            return s.回(404, {'错': '没有这个地址'})

        def 存(s):
            if not s.主机对() or s.headers.get('X-Ban') != '1':
                return s.回(403, {'错': '只让本机的看板页面改'})
            o = s.headers.get('Origin')
            if o and o not in (f'http://127.0.0.1:{端口}', f'http://localhost:{端口}'):
                return s.回(403, {'错': '只让本机的看板页面改'})
            path = 解路径(s.path)
            n = int(s.headers.get('Content-Length') or 0)
            try:
                a = json.loads(s.rfile.read(n) or b'{}')
            except ValueError:
                return s.回(400, {'错': '不是 JSON'})
            if path == '/api/板':
                try:
                    e = 板操作(a)
                except 错 as x:
                    return s.回(400, {'错': str(x)})
                return s.回(200, {'ok': True, '事件': e})
            if path == '/api/布局':   # 手动调格子（卷二 7.7）
                try:
                    v = 改布局(a.get('改'))
                except (错, ValueError, TypeError) as x:
                    return s.回(400, {'错': str(x)})
                return s.回(200, {'ok': True, '布局': v})
            if path == '/api/小窗':
                if not os.path.isdir(小窗):
                    return s.回(404, {'错': '原生小窗还没编译（工具/编译小窗.sh）'})
                subprocess.Popen(['/usr/bin/open', 小窗, '--args', '--端口', str(端口)])
                return s.回(200, {'ok': True})
            if path == '/api/打开':   # 展开里的「文件夹 ↗」「最近改了 X」：交给访达 / 默认程序打开，只许开这个任务目录里有的
                任务 = str(a.get('任务') or '')
                if 任务 not in 找任务():
                    return s.回(400, {'错': '没有这个任务'})
                底 = os.path.realpath(任务路(任务))
                f = os.path.realpath(os.path.join(底, str(a.get('文件') or '')))
                if (f != 底 and not f.startswith(底 + os.sep)) or not os.path.exists(f):
                    return s.回(400, {'错': '只能开这个任务目录里有的东西'})
                if a.get('用') == 'QuickTime' and f.lower().endswith(('.mp4', '.mov', '.m4v')):   # 卷四 6.66：施工区点样片的候选，用 QuickTime 看
                    subprocess.Popen([打开命令, '-a', 'QuickTime Player', f])
                else:
                    subprocess.Popen([打开命令, f])
                return s.回(200, {'ok': True})
            if path == '/api/退出':   # 换版：「板.py 重开」、小窗菜单「重开看板服务」叫的；回完话就退，小窗见服务没了会用新代码再起一个
                threading.Timer(0.3, lambda: os._exit(0)).start()
                return s.回(200, {'ok': True})
            动, z = None, None   # 施工区的动作：叫醒、验收、op（网页里的 12 种操作）
            m = re.match(r'^/api/施工区/([^/]+)/(叫醒|验收|op)$', path)
            if m:
                z, 动 = 施工区们().get(m.group(1)), m.group(2)
                if not z:
                    return s.回(404, {'错': '没有这个施工区'})
            elif path == '/api/op':   # 老写法（页面 8.3 前只有 MV 一个区）：没写「区」就是登记的第一个区
                区们 = 施工区们()
                z = 区们.get(str(a.get('区') or '')) or next(iter(区们.values()), None)
                动 = 'op' if z else None
            if 动 == '叫醒':
                return s.回(200, 施工区叫醒(z))
            if 动 == '验收':   # 用户点格子上的「验收 / 等你」= 知道了：记下这一格看到第几号，框就消失
                with 锁():
                    x = 读施工区(z)
                    x.setdefault('验收', {})[str(a.get('格') or '')] = (z.读() or {}).get('事件号', 0)
                    写施工区(z, x)
                return s.回(200, {'ok': True})
            if 动 == 'op':
                E = 引擎()
                try:
                    st, 回 = z.用户操作(a)
                except E.冲突 as x:
                    return s.回(409, {'冲突': True, '错': str(x), z.条目: dict(x.条, _标签=E.标签(x.条)) if x.条 else None})
                except E.错 as x:
                    return s.回(400, {'错': str(x)})
                # 卷四 6.67：全手动——施工区的操作不再自动投信，用户点「叫醒 Claude」才把没发的打包发过去（施工区叫醒）
                if 回 is not None:
                    回.update(ok=True, 改动号=st['改动号'])
                    return s.回(200, 回)
                return s.回(200, {'ok': True, '状态': z.带算(st)})
            return s.回(404, {'错': '没有这个地址'})

    ThreadingHTTPServer.daemon_threads = True
    srv = ThreadingHTTPServer(('127.0.0.1', 端口), 处理)
    print(f'无限表格开着：http://127.0.0.1:{端口}/ （只让本机访问；关掉这个窗口或按 Ctrl-C 就停）', flush=True)
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass


# ---------- 命令行 ----------

def 选项(r, 名, 默认=None):
    if 名 in r:
        k = r.index(名)
        v = r[k + 1] if k + 1 < len(r) else 默认
        del r[k:k + 2]
        return v
    return 默认


def 定会话(r):
    """--会话、--接入（插件替会话开关灯时给）；没给就看环境变量（会话自己敲的命令）。"""
    会 = 选项(r, '--会话')
    接 = 选项(r, '--接入')
    if 会 is None:
        会, 接0 = 会话信息()
        接 = 接 if 接 is not None else 接0
    return 会, 接 or ''


def 对标准():
    std = json.load(open(os.path.join(工具, '标准答案.json'), encoding='utf-8'))
    坏 = 0
    for k, want in std.items():
        if k == '说明':
            continue
        got = 读TODO(os.path.join(本任务, '示例', '演示工作区', k, 'TODO.md'))   # 标准答案只管仓库自带的演示工作区，设了别的工作区也照样对
        差 = []
        for f in ('模式', '完成', '总数'):
            if f in want and got.get(f) != want[f]:
                差.append(f'{f} 读成 {got.get(f)}，应是 {want[f]}')
        for f in ('等你', '在做'):
            if f in want and sorted(got.get(f, [])) != sorted(want[f]):
                差.append(f'{f} 读成 {got.get(f)}，应是 {want[f]}')
        if '当前含' in want and want['当前含'] not in got.get('节', ''):
            差.append(f'当前节读成「{got.get("节")}」，应含「{want["当前含"]}」')
        坏 += bool(差)
        print(('✗ ' if 差 else '✓ ') + k + ('：' + '；'.join(差) if 差 else ''))
    print(f'{len(std) - 1 - 坏}/{len(std) - 1} 份对上')
    return 坏


def 演示():
    """把仓库自带的演示工作区弄得像在用。git clone 下来的文件修改时间都一样，看板会当成一次批量整理、不算动静，
    演示任务就全算休眠、总览里看不到；这里把 8 份 TODO 的修改时间错开（最近的 10 分钟前，往后每份早 5 小时），
    再登记小说、分镜两个演示施工区，亮三盏演示灯（Claude 在写、Codex 等你、K31 在跑）。只动演示工作区和看板数据目录。"""
    演 = os.path.realpath(os.path.join(本任务, '示例', '演示工作区'))
    if 根 != 演:
        raise 错(f'演示只在工作区就是演示工作区时用（现在是 {根}）：先把 设置.json 挪开，或把里面的工作区写成 示例/演示工作区')
    now = time.time()
    次序 = ['写作/长篇小说', '研究/竞品调研', '开发/记账小程序', '视频/产品宣传片', '研究/读书笔记', '开发/网站改版', '视频/播客剪辑', '写作/短篇合集']
    for i, k in enumerate(次序):
        p = os.path.join(演, k, 'TODO.md')
        if os.path.exists(p):
            t = now - 600 - i * 5 * 3600
            os.utime(p, (t, t))
    自己 = [sys.executable, os.path.abspath(__file__)]
    for k, 模, 号 in (('写作/长篇小说', '小说', 'xs'), ('视频/产品宣传片', '分镜', 'fj')):
        subprocess.run(自己 + ['区', '新建', k, '--模板', 模, '--号', 号], capture_output=True, text=True)
    for a in (['开工', '写作/长篇小说', '--谁', 'Claude', '--说', '写第 14 章', '--租', '720'],
              ['开工', '研究/竞品调研', '--谁', 'K31', '--说', '定价对比（派工）', '--租', '720'],
              ['开工', '开发/记账小程序', '--谁', 'Codex', '--说', '月度统计', '--租', '720'],
              ['等你', '开发/记账小程序', '--谁', 'Codex', '--说', '导出格式等你选']):
        subprocess.run(自己 + a, capture_output=True, text=True)
    print('演示准备好了：8 个演示任务、2 个施工区（小说 xs、分镜 fj）、3 盏灯。打开 http://127.0.0.1:8770/ 看；想重来就删掉 数据.nosync 再跑一次。')


def 区命令(r):
    """板.py 区 新建 / 区 列（分卷五 8.4）"""
    动 = r[0] if r else '列'
    try:
        with open(登记文件, encoding='utf-8') as f:
            登 = json.load(f)
    except (OSError, ValueError):
        登 = {'说明': '分卷五：看板认哪些施工区。区号 → 任务（任务目录，相对工作区）、台（存档目录，里面要有 区域.json）、态（看板这边的状态文件，默认 施工区-区号.json）。', '区们': {}}
    区们表 = 登.setdefault('区们', {})
    if 动 == '列':
        if not 区们表:
            print('还没有登记的施工区')
        for 号, v in 区们表.items():
            z = 施工区们().get(号)
            print(f'{号}：{v.get("任务")} · 存档 {v.get("台")} · 边界 {(v.get("边界") or {}).get("字段格") or "没定"} 格' + (f' · {z.名} · 条目叫「{z.条目}」 · {"竖排" if z.配.get("排") == "竖" else "横排"}' if z else ' · 读不到 区域.json'))
            if z and 超界话(z):
                print('  ⚠ ' + 超界话(z))
        return
    if 动 != '新建' or len(r) < 2:
        sys.exit('用法：板.py 区 新建 任务 [--模板 小说] [--号 区号] [--名 名字] [--段 卷一,卷二]；板.py 区 列')
    rel = 解任务(r[1])
    if rel.split('/')[0] in 外区 or rel.startswith('零活:'):
        sys.exit('只给工作区里有 TODO.md 的任务建施工区')
    if any(v.get('任务') == rel for v in 区们表.values()):
        sys.exit(f'{rel} 已经有施工区了（板.py 区 列）')
    模板名 = 选项(r, '--模板') or '小说'
    模板 = os.path.join(工具, '施工区模板', 模板名 + '.json')
    if not os.path.exists(模板):
        sys.exit(f'没有这个模板：{模板}（工具/施工区模板/ 里有：{"、".join(x[:-5] for x in sorted(os.listdir(os.path.dirname(模板))) if x.endswith(".json"))}）')
    号 = 选项(r, '--号') or next(f'q{i}' for i in range(1, 1000) if f'q{i}' not in 区们表)
    if not re.match(r'^[a-z][a-z0-9]{0,15}$', 号) or 号 in 区们表:
        sys.exit(f'区号要小写字母开头、只用小写字母和数字，而且不能和已有的重：{号}')
    台 = os.path.join(任务路(rel), '施工台')
    os.makedirs(台, exist_ok=True)
    配文件 = os.path.join(台, '区域.json')
    if not os.path.exists(配文件):
        with open(模板, encoding='utf-8') as f:
            配 = json.load(f)
        名 = 选项(r, '--名')
        if 名:
            配['名'] = 名
        配['标题'] = 配.get('标题') or 名字(rel)[1]
        with open(配文件, 'w', encoding='utf-8') as f:
            json.dump(配, f, ensure_ascii=False, indent=1)
            f.write('\n')
    z = 引擎().区(台)
    if z.读() is None:
        z.新建([x for x in (选项(r, '--段') or '第一卷').split(',') if x.strip()])
    区们表[号] = {'任务': rel, '台': os.path.relpath(台, 根) if (台 + os.sep).startswith(根 + os.sep) else 台, '边界': {'字段格': 字段格(z.配)}}   # 8.9：照模板算好，以后要多占先找用户批
    with 锁():
        tmp = 登记文件 + '.tmp'
        os.makedirs(os.path.dirname(登记文件), exist_ok=True)
        with open(tmp, 'w', encoding='utf-8') as f:
            json.dump(登, f, ensure_ascii=False, indent=1)
        os.replace(tmp, 登记文件)
    print(f'建好了：{rel} 的施工区 {号}（{z.配.get("名") or 号}，条目叫「{z.条目}」，{"竖排" if z.配.get("排") == "竖" else "横排"}，边界 {字段格(z.配)} 格：字段那一向最多占这么多，条目随便加）')
    print(f'  配置 {配文件}（字段、行怎么排改这里）')
    print(f'  加条目：/usr/bin/python3 {os.path.join(工具, "施工台.py")} {台} 加 号 段名 字段=值 …')
    print('  看板几秒内认到（第 1 层点这个任务进第 3 层）')


def main():
    a = sys.argv[1:]
    if not a:
        print(__doc__)
        return
    c, r = a[0], a[1:]
    if c == '收工':   # 7.20（用户 11-05 01:0x「720也做」）：收工 = 灭灯，和核心 §5 的状态词一样。插件替会话开关灯时才带 --会话，
        c = '等你' if '--会话' in r else '完工'   # 新插件交付敲「等你」，带 --会话 敲收工的只有老插件（11-05 01:1x 前开的会话），照旧当交付
    c = {'施工': '开工'}.get(c, c)   # 和核心 §5 的状态词同名（卷二 7.10）
    try:
        if c == 'codex':
            for k, 态 in Codex读一遍():
                print(态, k)
        elif c == '服务':
            父 = 选项(r, '--父')
            服务(int(r[0]) if r else 8770, int(父) if 父 else None)
        elif c == '开工':
            谁 = 选项(r, '--谁', os.environ.get('BAN_WHO', 'Claude'))
            预计 = 选项(r, '--预计')
            说 = 选项(r, '--说', '')
            租分 = 选项(r, '--租')
            题 = 选项(r, '--题')
            疑 = 选项(r, '--对不上')
            要 = '--要你' in r   # 6.24：没有值的开关，先拿掉，免得当成格子
            if 要:
                r.remove('--要你')
            会, 接 = 定会话(r)
            任务 = 解任务(r[0]) if r else 会话的任务(会)
            if not 任务:
                raise 错('要写任务（这个会话还没在看板上开过工）')
            格子 = [规格(g) for g in r[1:]] if r else (末条们().get((任务, 谁, 会, False)) or {}).get('格子') or []
            try:   # 查撞格出错（比如 MV 存档读坏了）也照样开灯
                别人 = [l for l in 灯们().get(任务, []) + 在出灯(任务的区(任务)) if l['谁'] != 谁]
            except Exception:
                别人 = []
            now = time.time()
            if 预计:   # 估时对账：同一会话上一段（还开着、或一小时内刚收）实际用了多久
                上 = [d for d in 段们() if d['谁'] == 谁 and d['会话'] == (会 or '')]
                if 上 and (上[-1]['结束'] is None or 上[-1]['结束'] > now - 3600):
                    报段(上[-1], now, '上一段')
            题 = 题 or (末条们().get((任务, 谁, 会, False)) or {}).get('题')   # 零活的标题：没写就沿用上一条的
            记灯(任务, 谁, True, 格子=格子, 预计=int(预计) if 预计 else None, 说=说, 租=int(float(租分) * 60) if 租分 else 租期, 会话=会, 接入=接,
                 **({'题': 题} if 题 else {}), **({'对不上': 疑} if 疑 else {}), **({'要你': True} if 要 else {}))
            if 预计:
                xs = 往常(谁, now)
                if len(xs) >= 3:
                    中 = statistics.median(xs)
                    print(f'估时：最近 {len(xs)} 段实际是预计的 {min(xs):.2g}–{max(xs):.2g} 倍，中位 {中:.2g}；这段写 {预计} 分钟，按往常约 {分(int(预计) * 60 * 中)} 分钟')
                else:
                    print('估时：带预计的段还不到 3 段，没法按往常校准')
            print(f'开灯：{名字(任务)[1]} · {谁}{"（" + 说 + "）" if 说 else ""}{"，格子 " + "、".join(格子) if 格子 else ""}；{round(float(租分)) if 租分 else 30} 分钟没再开工，看板上就显示成「等你」')
            for x in [y for y in 撞了([{'谁': 谁, '格子': 格子}] + 别人) if y['格'] in 格子]:
                l = next(l for l in 别人 if x['格'] in (l.get('格子') or []))
                m = 分钟前(l.get('开始'))
                print(f'⚠ 撞格：{x["格"]} {l["谁"]} 也认领了（{m + " 开工" if m else "正在出"}{"：" + l["说"] if l.get("说") else ""}）。'
                      f'看板上这格并排挂两块名牌；先和对方或用户说好谁做，别两边同时改。')
        elif c in ('等你', '完工'):
            收 = '--收工' in r   # 6.26：会话说做完了、用户还没看，名牌写「收工」；没有值的开关，先拿掉
            if 收:
                r.remove('--收工')
            谁 = 选项(r, '--谁', os.environ.get('BAN_WHO', 'Claude'))
            说 = 选项(r, '--说')
            题 = 选项(r, '--题')
            疑 = 选项(r, '--对不上')
            会, 接 = 定会话(r)
            任务 = 解任务(r[0]) if r else 会话的任务(会)
            if not 任务:
                raise 错('要写任务（这个会话还没在看板上开过工）')
            开着 = [d for d in 段们() if d['谁'] == 谁 and d['会话'] == (会 or '') and d['任务'] == 任务 and d['结束'] is None]
            if 开着:
                报段(开着[-1], time.time(), '这一段')
            if c == '完工':
                记灯(任务, 谁, False, 等你=False, 会话=会, 接入=接)
                print(f'完工：{名字(任务)[1]} · {谁}，框消失')
            else:
                上 = 末条们().get((任务, 谁, 会, False)) or {}
                记灯(任务, 谁, False, 等你=True, 说=说 if 说 is not None else 上.get('说', ''), 格子=上.get('格子') or [], 会话=会, 接入=接,
                   **({'题': 题 or 上['题']} if 题 or 上.get('题') else {}), **({'对不上': 疑} if 疑 else {}), **({'收工': True} if 收 else {}))
                print(f'交付：{名字(任务)[1]} · {谁}，框留着、名牌「等你」；用户点「知道了」或你敲「收工」才消失')
        elif c == '跑':
            if '--' not in r:
                raise 错('写成：板.py 跑 任务 [--谁 名字] [--说 话] -- 命令…')
            k = r.index('--')
            前, cmd = r[:k], r[k + 1:]
            谁 = 选项(前, '--谁', os.environ.get('BAN_WHO', 'Claude'))
            说 = 选项(前, '--说', '')
            任务 = 解任务(前[0])
            p = subprocess.Popen(cmd)
            记灯(任务, 谁, True, 说=说 or ' '.join(cmd)[:40], pid=p.pid, 租=30 * 86400, 跑=True)
            try:
                rc = p.wait()
            finally:
                记灯(任务, 谁, False, 跑=True)
            sys.exit(rc)
        elif c == '列':
            列()
        elif c == '段':
            if not r:
                raise 错('写成：板.py 段 任务')
            段(解任务(r[0]))
        elif c == '等':
            等(int(r[0]) if r else 300, int(r[1]) if len(r) > 1 else 1800, float(r[2]) if len(r) > 2 else 12)
        elif c == '读':
            v = 看板数据(强制=True)
            for t in v['任务']:
                if r and r[0] not in t['键']:
                    continue
                if t.get('读不出'):
                    print(f'{t["键"]}：{t["读不出"]}')
                    continue
                print(f'{t["键"]}：{t["模式"]} {t["完成"]}/{t["总数"]} 当前「{t["节"]}」 等你{t["等你"]} 在做{t["在做"]}'
                      f'{" 旧账" if t["旧账"] else ""}{" 休眠" if t["休眠"] else ""}{" 做完" if t["做完"] else ""}'
                      f'{" 灯" + str([x["谁"] + ":" + x.get("态", "干") for x in t["灯"]]) if t["灯"] else ""}'
                      f'{" 会话 " + t["会话"] if t.get("会话") else ""}')
        elif c == '重开':   # 换版：叫正在跑的看板服务退出；原生小窗在管的话，几秒内会用新代码再起一个（不开终端）
            import urllib.request
            端口 = int(r[0]) if r else 8770
            q = urllib.request.Request(f'http://127.0.0.1:{端口}/api/' + quote('退出'), data=b'{}', method='POST',
                                       headers={'X-Ban': '1', 'Content-Type': 'application/json'})
            def 问版():
                try:
                    return json.loads(urllib.request.urlopen(f'http://127.0.0.1:{端口}/api/' + quote('版'), timeout=1.5).read())
                except (OSError, ValueError):
                    return None
            旧号 = (问版() or {}).get('进程')
            try:
                urllib.request.urlopen(q, timeout=3).read()
            except OSError as x:
                sys.exit(f'没叫到：{x}（服务可能本来就没开）')
            # 叫退了不算换好：等新服务起来、进程号换了才算（卷二 7.39；11-04 03:36 马上问到 200，其实是旧服务退出前最后答的一下，
            # 小窗重起次数满了没再起，看板停了约 40 分钟）
            for _ in range(50):
                time.sleep(0.5)
                v = 问版()
                if v and v.get('进程') and v['进程'] != 旧号:
                    print(f'换好了：{端口} 的看板服务换成新的（进程 {旧号 or "?"} → {v["进程"]}）')
                    break
            else:
                sys.exit(f'{端口} 的旧服务退了，25 秒内没有新的起来：右键菜单栏的无限表格图标，点「重开看板服务」（没开小窗就双击 打开无限表格.command）')
        elif c == '对标准':
            sys.exit(1 if 对标准() else 0)
        elif c == '设置':
            print(json.dumps({'设置文件': os.environ.get('BAN_SETTINGS') or os.path.join(本任务, '设置.json') + ('' if 设置 else '（没有或没读，全用默认）'),
                              '工作区': 根, '分组': 母文件夹 or '自动：工作区下第一层每个文件夹一组', '跳过目录': sorted(跳过目录),
                              '派工账本': 账本 or '不读', 'Codex': {'会话记录': Codex家 or '不读', '额外工作区': 外区}, '数据': 数据},
                             ensure_ascii=False, indent=1))
        elif c == '区':
            区命令(r)
        elif c == '演示':
            演示()
        elif c == '对账':
            谁 = 选项(r, '--谁')
            条 = int(选项(r, '--条', '10'))
            对账(解任务(r[0]) if r else None, 谁, 条)
        else:
            print(__doc__)
            sys.exit(1)
    except 错 as e:
        sys.exit(f'没做：{e}')


if __name__ == '__main__':
    main()
