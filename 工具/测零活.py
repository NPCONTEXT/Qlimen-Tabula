# 卷二 7.10 板.py 离线测：零活、--题、--对不上、施工 / 等你 命令名（临时数据目录）
import json, os, subprocess, sys, tempfile
板 = sys.argv[1]; 错 = []
def 查(名, 过, 细=''):
    print(('✅ ' if 过 else '❌ ') + 名 + ('' if 过 else '  ' + 细)); 过 or 错.append(名)
with tempfile.TemporaryDirectory() as d:
    env = dict(os.environ, BAN_DATA=d, BAN_LEDGER=d + '/账本.csv')
    跑 = lambda *a: subprocess.run(['/usr/bin/python3', 板, *a], capture_output=True, text=True, env=env, timeout=60).stdout
    会 = ['--会话', 'local_t1', '--接入', 'claude']
    o = 跑('等你', '零活:local_t1', '--题', '「steam 走哪条线？」', '--说', '「steam 走哪条线？」', *会)
    读 = 跑('读', '零活')
    查('等你 = 收工：零活一行挂等你', "零活:local_t1：零活 0/0" in 读 and "Claude:等" in 读, 读 + o)
    跑('施工', '零活:local_t1', '--说', '「不用了」', *会)
    读 = 跑('读', '零活')
    查('施工 = 开工：零活一行在干', "Claude:干" in 读, 读)
    跑('等你', '零活:local_t1', '--对不上', '说施工，什么都没在跑', *会)
    末 = [json.loads(l) for l in open(d + '/开关.jsonl', encoding='utf-8')][-1]
    查('收工没写 --题 就沿用上一条的；--对不上 记进这一条', 末.get('题') == '「steam 走哪条线？」' and 末.get('对不上') == '说施工，什么都没在跑', json.dumps(末, ensure_ascii=False))
    跑('施工', '零活:local_t1', '--说', '「再问」', *会)
    末 = [json.loads(l) for l in open(d + '/开关.jsonl', encoding='utf-8')][-1]
    查('对不上不会带到下一条', '对不上' not in 末, json.dumps(末, ensure_ascii=False))
    跑('完工', '零活:local_t1', *会)
    查('完工：零活那一行消失', '零活:' not in 跑('读', '零活'))
    # 6.29：零活那一行也能点「知道了」（看板上的动作，走 板操作）
    跑('等你', '零活:local_t1', '--题', '「问一句」', '--说', '「问一句」', *会)
    os.environ.update(BAN_DATA=d, BAN_LEDGER=d + '/账本.csv')
    import importlib.util; sp = importlib.util.spec_from_file_location('板模块', 板); 模 = importlib.util.module_from_spec(sp); sp.loader.exec_module(模)
    try:
        模.板操作({'op': '知道了', '任务': '零活:local_t1', '谁': 'Claude'}); 认 = '零活:' not in 跑('读', '零活')
    except Exception as x:
        认 = False; o = repr(x)
    查('零活那一行点「知道了」：消失', 认)
    跑('等你', '零活:local_t1', '--题', '「再问一句」', '--说', '「再问一句」', *会)
    查('点过知道了，下一次照样挂等你', 'Claude:等' in 跑('读', '零活'))
    o = 跑('开工', '对不上的任务名xyz', *会) + subprocess.run(['/usr/bin/python3', 板, '开工', '对不上的任务名xyz', *会], capture_output=True, text=True, env=env).stderr
    查('不是零活、也对不上任务的名字照旧报错', '对不上任务' in o, o)
print('全过' if not 错 else f'{len(错)} 条没过'); sys.exit(1 if 错 else 0)
