#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""接入 Codex 的离线测试（11-05 C2–C5；用户：「codex本身遵守新协议，现在会打状态词的……如果反复要求手打就不对了」）：
看板也认她工作区里的任务（只认她在界面开的、没归档的会话所在的有 TODO 的目录；命令行出图、子代理、没人开过会话的旧副本不算），
看板自己读她的会话记录开关灯：开轮施工；结束照回复开头的状态词（等你、收工、施工、没写）；用户说了收工她回收工就灭；
没碰任务目录的照状态词亮零活；第一次读不补以前的灯，只补记会话（名牌点得进去、待续认得、不算收工）；换目录关旧灯；同一任务两个会话各一盏；
续期；半行不读。临时目录，不碰真数据、不碰 ~/.codex。
跑法：/usr/bin/python3 工具/测Codex.py [板.py 路径]"""
import importlib.util, json, os, subprocess, sys, tempfile, time
from datetime import datetime, timezone

板路 = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), '板.py')
错 = []


def 查(名, 过, 细=''):
    print(('✅ ' if 过 else '❌ ') + 名 + ('' if 过 else '  ' + str(细)))
    if not 过:
        错.append(名)


def ts(t):
    return datetime.fromtimestamp(t, timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.000Z')


def 行(t, 类, **pl):
    return json.dumps({'timestamp': ts(t), 'type': 类, 'payload': pl}, ensure_ascii=False) + '\n'


元 = lambda t, 号, cwd, **k: 行(t, 'session_meta', id=号, cwd=cwd, **dict({'originator': 'Codex Desktop', 'source': 'vscode'}, **k))
始 = lambda t: 行(t, 'event_msg', type='task_started', turn_id='x', started_at=int(t))
境 = lambda t, cwd: 行(t, 'turn_context', cwd=cwd, turn_id='x')
问 = lambda t, 文: 行(t, 'event_msg', type='item_completed', item={'type': 'UserMessage', 'content': [{'type': 'text', 'text': 文}]})
终 = lambda t, 答: 行(t, 'event_msg', type='task_complete', last_agent_message=答, completed_at=int(t))
杂 = lambda t: 行(t, 'event_msg', type='token_count')
头 = '编号 | 步骤 | 产出物 | 预计耗时 | 依赖/阻塞\n---|---|---|---|---\n'
段 = lambda 名, 行们: f'# {名} · TODO\n\n## 卷一（11-05 · 在做）\n\n' + 头 + ''.join(行们)

with tempfile.TemporaryDirectory() as 临:
    now = time.time()
    根, 数, 家 = os.path.join(临, 'Claude'), os.path.join(临, '数据'), os.path.join(临, 'codex家')
    外G, 外C = os.path.join(临, 'ChatGPT'), os.path.join(临, 'Codex')
    def 写(p, 文=''):
        os.makedirs(os.path.dirname(p), exist_ok=True)
        open(p, 'w', encoding='utf-8').write(文)
    写(os.path.join(根, 'Qlimen', '甲', 'TODO.md'), 段('甲', ['1 | [自动] 写 | — | — | —\n']))
    写(os.path.join(外G, '重制', 'TODO.md'), 段('示例重制', ['1 | ✅ [自动] 第一版 | — | — | —\n', '2 | [自动] 第二版 | — | — | 1\n', '3 | [需用户] 看第一版 | — | — | 1\n']))
    os.makedirs(os.path.join(外G, '重制', '子目录'))
    写(os.path.join(外C, '2026-10-18', '旧项目', 'work', 'batch9', 'TODO.md'), 段('旧副本', ['1 | [自动] 旧 | — | — | —\n']))
    写(os.path.join(外C, '2026-11-05', '出图', 'TODO.md'), 段('出图', ['1 | [自动] 出 | — | — | —\n']))
    写(os.path.join(外C, '2026-11-05', '子代理目录', 'TODO.md'), 段('子代理', ['1 | [自动] 子 | — | — | —\n']))
    写(os.path.join(外C, '2026-11-05', '归档', '旧任务', 'TODO.md'), 段('归档里的', ['1 | [自动] 旧 | — | — | —\n']))
    for d in ('小事', '另一件'):
        os.makedirs(os.path.join(外C, '2026-11-05', d))
    会们 = os.path.join(家, 'sessions', '2026', '11', '05')
    文A = os.path.join(会们, 'rollout-2026-11-05T10-00-00-aaaa.jsonl')
    写(文A, 元(now - 7300, 'aaaa', os.path.join(外G, '重制')) + 始(now - 7200) + 境(now - 7200, os.path.join(外G, '重制')) + 问(now - 7200, '做一下')
       + 终(now - 7100, '【等你】交了初稿，你看一下'))
    写(os.path.join(会们, 'rollout-2026-11-05T10-01-00-cccc.jsonl'), 元(now - 7000, 'cccc', os.path.join(外C, '2026-11-05', '出图'), originator='codex_exec', source='exec')
       + 始(now - 60))
    写(os.path.join(会们, 'rollout-2026-11-05T10-02-00-dddd.jsonl'), 元(now - 7000, 'dddd', os.path.join(外C, '2026-11-05', '子代理目录'), source={'subagent': {'other': 'guardian'}}, parent_thread_id='aaaa')
       + 始(now - 60))
    写(os.path.join(会们, 'rollout-2026-11-05T10-03-00-hhhh.jsonl'), 元(now - 7000, 'hhhh', os.path.join(外C, '2026-11-05', '归档', '旧任务')) + 始(now - 60))
    文B = os.path.join(会们, 'rollout-2026-11-05T10-04-00-bbbb.jsonl')
    写(文B, 元(now - 6000, 'bbbb', os.path.join(外C, '2026-11-05', '小事')))
    文E = os.path.join(会们, 'rollout-2026-11-05T10-05-00-eeee.jsonl')
    写(文E, 元(now - 600, 'eeee', os.path.join(外G, '重制', '子目录')) + 始(now - 300) + 问(now - 300, '在子目录里干'))
    写(os.path.join(家, 'session_index.jsonl'), json.dumps({'id': 'bbbb', 'thread_name': '问个小事'}, ensure_ascii=False) + '\n')
    写(os.path.join(外G, '旧活', 'TODO.md'), 段('旧活', ['1 | [自动] 接着做 | — | — | —\n', '2 | [需用户] 看一眼 | — | — | —\n']))
    os.utime(os.path.join(外G, '旧活', 'TODO.md'), (now - 9000, now - 9000))
    写(os.path.join(会们, 'rollout-2026-11-05T09-00-00-kkkk.jsonl'), 元(now - 7300, 'kkkk', os.path.join(外G, '旧活')) + 始(now - 7200) + 终(now - 7000, '【等你】交了'))
    写(os.path.join(外G, '刚交', 'TODO.md'), 段('刚交', ['1 | [自动] 接着做 | — | — | —\n']))
    写(os.path.join(会们, 'rollout-2026-11-05T09-30-00-jjjj.jsonl'), 元(now - 900, 'jjjj', os.path.join(外G, '刚交')) + 始(now - 800) + 问(now - 800, '做') + 终(now - 600, '【等你】刚交的'))
    写(os.path.join(外G, '老任务', 'TODO.md'), 段('老任务', ['1 | [自动] 接着做 | — | — | —\n']))
    写(os.path.join(会们, 'rollout-2026-10-28T09-00-00-oooo.jsonl'), 元(now - 8 * 86400, 'oooo', os.path.join(外G, '老任务')) + 始(now - 8 * 86400) + 终(now - 8 * 86400 + 60, '【等你】交了'))
    open(os.path.join(临, '账本.csv'), 'w').close()

    # 测试模式默认不扫她那边
    r = subprocess.run(['/usr/bin/python3', '-c', f'import importlib.util as u; s=u.spec_from_file_location("板", {板路!r}); m=u.module_from_spec(s); s.loader.exec_module(m); print(m.外区, repr(m.Codex家))'],
                       env=dict(os.environ, BAN_ROOT=根, BAN_DATA=数), capture_output=True, text=True)
    查('设了 BAN_ROOT 没给 BAN_EXTRA、BAN_CODEX：不扫她的工作区、不读真的 ~/.codex', r.stdout.strip() == "{} ''", r.stdout + r.stderr)

    os.environ.update(BAN_ROOT=根, BAN_DATA=数, BAN_LEDGER=os.path.join(临, '账本.csv'), DYT_DIR=os.path.join(临, '导演台'), BAN_OPEN='/bin/echo',
                      BAN_EXTRA=f'ChatGPT={外G};Codex={外C}', BAN_CODEX=家)
    sp = importlib.util.spec_from_file_location('板', 板路)
    板 = importlib.util.module_from_spec(sp)
    sp.loader.exec_module(板)
    读 = 板.Codex读一遍
    def 追加(f, 文):
        with open(f, 'a', encoding='utf-8') as fh:
            fh.write(文)
    def 灯(k, 会):
        return next((l for l in 板.灯们().get(k, []) if l['会话'] == 会), None)
    def 片():
        return {t['键']: t for t in 板.看板数据(强制=True)['任务']}

    任 = 板.找任务()
    查('她界面开的会话所在、有 TODO 的目录是任务，键写 ChatGPT/…', 'ChatGPT/重制' in 任 and 'Qlimen/甲' in 任, 任)
    查('没人开过会话的旧副本、命令行出图、子代理、归档目录里的都不算', not any(k.startswith('Codex/') for k in 任), 任)
    查('任务路、任务键来回对得上', 板.任务路('ChatGPT/重制') == os.path.join(os.path.realpath(外G), '重制') and 板.任务键(os.path.realpath(os.path.join(外G, '重制'))) == 'ChatGPT/重制')
    查('板.py 认 ChatGPT/… 和绝对路径', 板.解任务('ChatGPT/重制') == 'ChatGPT/重制' and 板.解任务(os.path.join(外G, '重制')) == 'ChatGPT/重制')
    查('子目录里的会话归到上面的任务', 板.目录归属(os.path.join(外G, '重制', '子目录')) == 'ChatGPT/重制')

    做 = 读()
    查('第一次读：两小时前收的那轮不补灯，只补记会话（种）', ('ChatGPT/重制', '种') in 做 and not 灯('ChatGPT/重制', 'aaaa'), 做)
    查('第一次读：五分钟前开轮、还在跑的亮上', 灯('ChatGPT/重制', 'eeee') and 灯('ChatGPT/重制', 'eeee')['态'] == '干', 做)
    l = 灯('ChatGPT/刚交', 'jjjj')
    查('第一次读：十分钟前刚交【等你】的照常亮等你', l and l['态'] == '等' and l['说'] == '刚交的', l)
    查('第一次读：零活、出图、子代理都不亮', not any(k.startswith('零活:') for k in 板.灯们()) and not any('cccc' == l['会话'] or 'dddd' == l['会话'] for ls in 板.灯们().values() for l in ls), 板.灯们())
    t = 片()['ChatGPT/重制']
    查('总览：归 Codex 组、名字取 TODO 标题', t['组'] == 'Codex' and t['名'] == '示例重制', (t['组'], t['名']))
    查('右栏按 Codex 写说明（接入）', t.get('接入') == 'codex', t.get('接入'))
    查('补记的会话不算收工：不出收工核对', not t.get('收工疑'), t.get('收工疑'))
    旧 = 片()['ChatGPT/旧活']
    查('只补记过会话、TODO 还挂着要用户做的：不出收工核对，待续照常', not 旧.get('收工疑') and (旧.get('待续') or {}).get('步') == ['1'], (旧.get('收工疑'), 旧.get('待续')))
    老 = 片()['ChatGPT/老任务']
    查('8 天前的会话不补记；没会话的接手开 Codex 新会话（任务目录、带接手话）', 老['会话链接'].startswith('codex://threads/new?path=') and 'prompt=' in 老['会话链接'] and '%E8%80%81%E4%BB%BB%E5%8A%A1' in 老['会话链接'] and not 老.get('会话'), 老['会话链接'][:120])
    追加(文E, 终(now - 200, '【等你】子目录的活交了'))
    读()
    t = 片()['ChatGPT/重制']
    查('都等你时：名牌点进最近开的那个会话（codex://threads/<号>）', t['会话链接'] == 'codex://threads/eeee', t['会话链接'])
    查('灯带链接，各点进各的会话', any(l.get('链') == 'codex://threads/eeee' for l in t['灯']), t['灯'])
    板.板操作({'op': '知道了', '任务': 'ChatGPT/重制', '谁': 'Codex'})
    t = 片()['ChatGPT/重制']
    查('用户点了知道了、没人亮灯：待续（灰框），列出能接着做的', (t.get('待续') or {}).get('步') == ['2'], t.get('待续'))

    追加(文A, 始(now - 50) + 问(now - 50, '接着改第二版'))
    读()
    l = 灯('ChatGPT/重制', 'aaaa')
    查('开轮：施工，那句是用户这一轮说的', l and l['态'] == '干' and l['说'] == '「接着改第二版」' and l['接入'] == 'codex', l)
    追加(文A, 杂(now - 40) + 终(now - 30, '【等你】第二版好了，在 out/ 里\n\n细节……'))
    读()
    l = 灯('ChatGPT/重制', 'aaaa')
    查('回复写【等你】：等你，那句是回复第一句', l and l['态'] == '等' and l['说'] == '第二版好了，在 out/ 里' and not l['收工'], l)
    追加(文A, 始(now - 29) + 问(now - 29, '再改一处') + 终(now - 28, '【施工】还在跑渲染，跑完我接着看'))
    读()
    l = 灯('ChatGPT/重制', 'aaaa')
    查('回复写【施工】：照旧在干', l and l['态'] == '干' and l['说'] == '还在跑渲染，跑完我接着看', l)
    追加(文A, 始(now - 27) + 问(now - 27, '好，收工') + 终(now - 26, '【收工】今天到这'))
    读()
    查('用户说了收工、她回【收工】：直接灭', not 灯('ChatGPT/重制', 'aaaa'), 灯('ChatGPT/重制', 'aaaa'))
    追加(文A, 始(now - 25) + 问(now - 25, '还有一件') + 终(now - 24, '【收工】都做完了'))
    读()
    l = 灯('ChatGPT/重制', 'aaaa')
    查('用户没说收工、她回【收工】：挂「收工」等用户看', l and l['态'] == '等' and l['收工'], l)
    追加(文A, 始(now - 23) + 问(now - 23, '问一下') + 终(now - 22, '好的，我看了'))
    读()
    l = 灯('ChatGPT/重制', 'aaaa')
    查('回复没写状态词：等你', l and l['态'] == '等' and not l['收工'], l)

    追加(文B, 始(now - 21) + 问(now - 21, '问个事') + 终(now - 20, '【等你】答案是这样'))
    读()
    l = 灯('零活:bbbb', 'bbbb')
    查('没碰任务目录、写了状态词：亮零活，名字取会话标题', l and l['态'] == '等' and l.get('题') == '问个小事', l)
    z = 片().get('零活:bbbb') or {}
    查('零活那一行点进她的会话', z.get('会话链接') == 'codex://threads/bbbb', z.get('会话链接'))
    追加(文B, 始(now - 19) + 问(now - 19, '再问') + 终(now - 18, '【收工】好了'))
    读()
    查('零活回【收工】：灭', not 灯('零活:bbbb', 'bbbb'))
    文F = os.path.join(会们, 'rollout-2026-11-05T11-00-00-ffff.jsonl')
    写(文F, 元(now - 17, 'ffff', os.path.join(外C, '2026-11-05', '另一件')) + 始(now - 17) + 问(now - 17, '随便聊') + 终(now - 16, '好的'))
    读()
    追加(文F, 始(now - 15) + 问(now - 15, '再聊'))
    读()
    查('后来新开的会话、没碰任务也没写状态词：不亮零活，开轮也不亮', not 灯('零活:ffff', 'ffff'))

    文G = os.path.join(会们, 'rollout-2026-11-05T11-01-00-gggg.jsonl')
    写(文G, 元(now - 14, 'gggg', os.path.join(外G, '重制')) + 始(now - 14) + 问(now - 14, '另开一个'))
    读()
    查('同一任务第二个会话：各一盏', 灯('ChatGPT/重制', 'gggg') and 灯('ChatGPT/重制', 'aaaa'), 板.灯们().get('ChatGPT/重制'))
    游 = json.load(open(os.path.join(数, 'codex游标.json'), encoding='utf-8'))
    游[文G]['续'] = 0
    json.dump(游, open(os.path.join(数, 'codex游标.json'), 'w', encoding='utf-8'))
    追加(文G, 杂(now - 13))
    查('一轮还在跑、过了 5 分钟又有新动静：续期，那句照旧', 读() == [('ChatGPT/重制', '干')] and 灯('ChatGPT/重制', 'gggg')['说'] == '「另开一个」', 灯('ChatGPT/重制', 'gggg'))
    追加(文G, 杂(now - 12))
    查('没到 5 分钟：不续期', 读() == [])
    半 = 终(now - 11, '【等你】半行')
    追加(文G, 半[:20])
    查('写到一半的行不读', 读() == [] and 灯('ChatGPT/重制', 'gggg')['态'] == '干')
    追加(文G, 半[20:])
    查('写完了再读', 读() == [('ChatGPT/重制', '等')])
    追加(文A, 境(now - 10, os.path.join(外C, '2026-11-05', '小事')) + 始(now - 10) + 问(now - 10, '换个地方'))
    读()
    查('会话换到别的目录：旧任务上那盏关掉', not 灯('ChatGPT/重制', 'aaaa'), 灯('ChatGPT/重制', 'aaaa'))
    查('板.py codex 命令能跑', subprocess.run(['/usr/bin/python3', 板路, 'codex'], env=os.environ, capture_output=True, text=True).returncode == 0)

print(f'\n{"全过" if not 错 else f"{len(错)} 条没过"}')
sys.exit(1 if 错 else 0)
