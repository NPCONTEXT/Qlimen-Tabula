import { expect, mock, test } from 'claude-code/testing'

const 家 = '/Users/t'
const 会 = 'local_abc-123'
const 板 = 家 + '/Documents/工作区/Qlimen/无限表格'
const 窗 = 板 + '/小窗.nosync/无限表格小窗.app'
const 箱 = `${板}/数据.nosync/信箱/${会}.jsonl`
const 位置 = 家 + '/.claude/skills/ban-listen/看板位置.txt'   // 装插件时写的看板位置
const 设置 = 板 + '/设置.json'                                // 看板的设置：工作区
const T = 1_800_000_000_000   // 测试里的「现在」，毫秒

const 信行 = (号: number, 秒: number, 摘要: string) => JSON.stringify({ 号, 秒, 名: '无限表格', 摘要 })
const 根 = 家 + '/Documents/工作区/'
const 任务们 = ['Qlimen/无限表格', '创作/示例小说', '冷归档/旧任务', '视频/示例MV', '视频/示例MV/MV', 'Qlimen/无限表格/历史资料/整理前']   // 历史资料里那个是旧副本（6.40）   // 这几个目录里有 TODO.md（MV 在示例MV 里面）

// 垫好插件下面的世界：环境变量、时钟、存储、文件、跑命令、发话；信箱的内容由 文() 给（null = 没有信箱文件）
const 准备 = (on: any, 文: () => string | null, 变量: Record<string, string> = { HOME: 家, CLAUDE_CODE_HOST_SESSION_ID: 会 }, 小窗在跑 = false, 定位 = true) => {
  mock.env(on, 变量)
  const clock = mock.clock(on, { now: T })
  mock.store(on, {})
  const 跑过: string[][] = []
  const 发过: string[] = []
  const 化 = (p: string) => { const 段: string[] = []; for (const x of p.split('/')) { if (x === '..') 段.pop(); else if (x && x !== '.') 段.push(x) } return '/' + 段.join('/') }   // 跟真文件系统一样认 ..（6.40）
  on('fs.exists', (_: unknown, e: { path: string }) => ({
    value: 化(e.path) === 窗 || (化(e.path) === 箱 && 文() !== null) || 任务们.some(t => 化(e.path) === 根 + t + '/TODO.md') || (定位 && (化(e.path) === 位置 || 化(e.path) === 设置)),
  }))
  on('fs.read', (_: unknown, e: { path: string }) => ({
    value: e.path === 箱 ? (文() ?? '') : 定位 && e.path === 位置 ? 板 + '\n' : 定位 && e.path === 设置 ? JSON.stringify({ 工作区: '~' + 根.slice(家.length) }) : '',
  }))
  on('process.run', (_: unknown, e: { argv: string[] }) => {
    跑过.push([...e.argv])
    const 查小窗 = e.argv[0] === '/usr/bin/pgrep'
    return { value: { exitCode: 查小窗 && !小窗在跑 ? 1 : 0, stdout: '', stderr: '' } }
  })
  on('prompt.submit', (_: unknown, e: { text: string }) => {
    发过.push(e.text)
    return { text: e.text }
  })
  on('session.start', (_: unknown, e: { cwd: string }) => ({ cwd: e.cwd }))
  on('tool.call', () => ({ result: {} }))
  on('turn.start', (_: unknown, e: { turnId: string }) => ({ turnId: e.turnId }))
  on('turn.complete', (_: unknown, e: { answer: string }) => ({ text: e.answer }))
  on('classic.Stop', () => ({}))
  on('classic.PermissionRequest', () => ({}))
  // 跑过的 板.py：只留参数，去掉每条都带的会话号
  const 板过 = () =>
    跑过.filter(a => a[1]?.endsWith('/工具/板.py')).map(a => a.slice(2).join(' ').replace(` --会话 ${会} --接入 claude`, ''))
  return { clock, 跑过, 发过, 板过 }
}

const 开会话 = ($: any) => $.session.start({ cwd: '/', surface: 'desktop', isInteractive: true })

const 查 = ['/usr/bin/pgrep', '-x', 'BanWindow']

test('会话一开始，小窗没在运行就在后台拉起它', async ($, on) => {
  const { 跑过, clock } = 准备(on, () => null)
  await 开会话($)
  await clock.settle()
  expect(跑过).toEqual([查, ['/usr/bin/open', '-g', 窗]])
})

test('小窗已经在运行（可能收在菜单栏）就不去碰它', async ($, on) => {
  const { 跑过, clock } = 准备(on, () => null, undefined, true)
  await 开会话($)
  await clock.settle()
  expect(跑过).toEqual([查])
})

test('你停手 20 秒后发一次，之后不重发', async ($, on) => {
  const 早 = T / 1000 - 30
  const { 发过, clock } = 准备(on, () => [信行(1, 早, '无限表格·2.11：点了「做完了」'), 信行(2, 早, 'MV·V1：意见「再暗一点」')].join('\n') + '\n')
  await 开会话($)
  await clock.advance(3_000)
  expect(发过.length).toBe(1)
  expect(发过[0]).toContain('【无限表格】我在看板上：')
  expect(发过[0]).toContain('- 无限表格·2.11：点了「做完了」')
  expect(发过[0]).toContain('- MV·V1：意见「再暗一点」')
  await clock.advance(30_000)
  expect(发过.length).toBe(1)
})

test('刚点的先不发，停手满 20 秒才发', async ($, on) => {
  const { 发过, clock } = 准备(on, () => 信行(1, T / 1000, '无限表格·2.11：点了「还没」') + '\n')
  await 开会话($)
  await clock.advance(15_000)
  expect(发过.length).toBe(0)
  await clock.advance(6_000)
  expect(发过.length).toBe(1)
})

test('一直有新动作，最多攒 2 分钟也发', async ($, on) => {
  let 号 = 0
  const 行们: string[] = []
  const { 发过, clock } = 准备(on, () => 行们.join('\n'))
  await 开会话($)
  for (let k = 0; k < 45; k++) {   // 每 3 秒点一下，一直不停手
    行们.push(信行(++号, (T + k * 3_000) / 1000, `点了第 ${号} 下`))
    await clock.advance(3_000)
  }
  expect(发过.length).toBe(1)
  expect(发过[0]).toContain('- 点了第 1 下')
})

test('没有会话号就只拉起小窗、不听信箱', async ($, on) => {
  let 读过 = 0
  const { 跑过, 发过, clock } = 准备(on, () => {
    读过++
    return 信行(1, T / 1000 - 60, '不该发') + '\n'
  }, { HOME: 家 })
  await 开会话($)
  await clock.advance(30_000)
  expect(跑过).toEqual([查, ['/usr/bin/open', '-g', 窗]])
  expect(发过.length).toBe(0)
  expect(读过).toBe(0)
})

test('没有信箱文件也不出错', async ($, on) => {
  const { 发过, clock } = 准备(on, () => null)
  await 开会话($)
  await clock.advance(30_000)
  expect(发过.length).toBe(0)
})

// ---------- 替会话开关灯 ----------

let 轮号 = 0
const 轮始 = ($: any, text: string, agentId?: string) => $.turn.start({ text, turnId: `t${++轮号}`, ...(agentId ? { agentId } : {}) })
const 轮终 = ($: any, answer = '好') => $.turn.complete({ answer, durationMs: 1, isAborted: false, turnId: `t${轮号}`, reason: 'answer' })
// Stop：停下时还在跑的后台任务、定好的定时叫醒（各几个）
const 停 = ($: any, 后台 = 0, 定时 = 0) =>
  $.classic.Stop({
    stop_hook_active: false,
    background_tasks: Array.from({ length: 后台 }, (_, i) => ({ id: `b${i}`, type: 'shell', status: 'running', description: 'watch.py' })),
    session_crons: Array.from({ length: 定时 }, (_, i) => ({ id: `c${i}`, schedule: '*/20 * * * *', recurring: false })),
  })
const 读 = ($: any, 相对: string) => $.tool.call({ tool: 'Read', file_path: 根 + 相对 })
const 改 = ($: any, 路: string) => $.tool.call({ tool: 'Edit', file_path: 路.startsWith('/') ? 路 : 根 + 路, old_string: 'a', new_string: 'b' })
const 跑 = ($: any, command: string, run_in_background = false) => $.tool.call({ tool: 'Bash', command, run_in_background })
const 亮着 = async ($: any) => {   // 读过交接、改了一个文件：亮在 无限表格
  await 轮始($, '做吧')
  await 读($, 'Qlimen/无限表格/交接.md')
  await 改($, 'Qlimen/无限表格/说明.md')
}

test('只读交接、TODO 不亮灯（多半是顺手查进度）', async ($, on) => {
  const { 板过, clock } = 准备(on, () => null)
  await 开会话($)
  await 轮始($, '无限表格进度怎么样')
  await 读($, 'Qlimen/无限表格/交接.md')
  await 读($, 'Qlimen/无限表格/TODO.md')
  await 轮终($)
  await clock.settle()
  expect(板过()).toEqual([])
})

test('没写看板位置、没有设置.json：看板当在 ~/Documents/Qlimen-Tabula，工作区是它自带的演示工作区', async ($, on) => {
  const { 跑过, clock } = 准备(on, () => null, undefined, false, false)
  await 开会话($)
  await 轮始($, '查一下')
  await 改($, 'Qlimen/无限表格/说明.md')   // 设置里没写工作区：这个目录不在演示工作区里，不亮任务
  await 轮终($, '【等你】查好了')
  await clock.settle()
  const 板们 = 跑过.filter(a => a[1]?.endsWith('/工具/板.py'))
  expect(板们.map(a => a.slice(1, 4))).toEqual([[家 + '/Documents/Qlimen-Tabula/工具/板.py', '等你', '零活:' + 会]])
})

test('第一次动笔才亮灯，之后每轮开始在干、结束等你', async ($, on) => {
  const { 板过, clock } = 准备(on, () => null)
  await 开会话($)
  await 亮着($)
  await 轮终($)
  await 轮始($, '继续，把第二步也做了')
  await 轮终($)
  await clock.settle()
  expect(板过()).toEqual([
    'Qlimen/无限表格 --说 「做吧」'.replace(/^/, '开工 '),
    '等你 Qlimen/无限表格',
    '开工 Qlimen/无限表格 --说 「继续，把第二步也做了」',
    '等你 Qlimen/无限表格',
  ])
})

test('这一轮起了后台任务：结束时还是在干，写「后台在跑」、租两小时', async ($, on) => {
  const { 板过, clock } = 准备(on, () => null)
  await 开会话($)
  await 亮着($)
  await 跑($, 'sleep 600', true)
  await 轮终($)
  await clock.settle()
  expect(板过().at(-1)).toBe('开工 Qlimen/无限表格 --说 后台在跑 --租 120')
})

test('它自己敲了完工、你没说收工：这一轮结束挂「收工」等你看，你回话就撤，下一轮也不亮（6.27）', async ($, on) => {
  const { 板过, clock } = 准备(on, () => null)
  await 开会话($)
  await 亮着($)
  await 跑($, '/usr/bin/python3 工具/板.py 完工 Qlimen/无限表格')
  await 轮终($)
  await 轮始($, '谢谢')
  await 轮终($)
  await clock.settle()
  expect(板过()).toEqual(['开工 Qlimen/无限表格 --说 「做吧」', '等你 Qlimen/无限表格 --收工', '完工 Qlimen/无限表格'])
})

// 11-04（卷四 6.9）以前是换任务、原来那个挂等你；用户：「其实不用硬修，完全可以标记跨区施工，等跨完把跨区的任务关掉就行」
test('改了另一个任务的 TODO：那边标「跨区施工」，这一轮结束关掉；本区不换', async ($, on) => {
  const { 板过, clock } = 准备(on, () => null)
  await 开会话($)
  await 亮着($)
  await 改($, '创作/示例小说/TODO.md')
  await 轮终($)
  await clock.settle()
  expect(板过()).toEqual(['开工 Qlimen/无限表格 --说 「做吧」', '开工 创作/示例小说 --说 跨区施工（从 无限表格 过来）', '完工 创作/示例小说', '等你 Qlimen/无限表格'])
})

test('改了别的任务的普通文件：也标跨区施工，本区不换', async ($, on) => {
  const { 板过, clock } = 准备(on, () => null)
  await 开会话($)
  await 亮着($)
  await 改($, '创作/示例小说/草稿.md')
  await 轮终($)
  await clock.settle()
  expect(板过()).toEqual(['开工 Qlimen/无限表格 --说 「做吧」', '开工 创作/示例小说 --说 跨区施工（从 无限表格 过来）', '完工 创作/示例小说', '等你 Qlimen/无限表格'])
})

test('跨区里改几次只标一次；下一轮只在本区动笔，就不再亮跨区', async ($, on) => {
  const { 板过, clock } = 准备(on, () => null)
  await 开会话($)
  await 亮着($)
  await 改($, '创作/示例小说/交接.md')
  await 跑($, `sed -i '' 's/甲/乙/' ${根}创作/示例小说/草稿.md`)
  await 轮终($)
  await 轮始($, '接着')
  await 改($, 'Qlimen/无限表格/说明.md')
  await 轮终($)
  await clock.settle()
  expect(板过()).toEqual(['开工 Qlimen/无限表格 --说 「做吧」', '开工 创作/示例小说 --说 跨区施工（从 无限表格 过来）', '完工 创作/示例小说', '等你 Qlimen/无限表格', '开工 Qlimen/无限表格 --说 「接着」', '等你 Qlimen/无限表格'])
})

test('按短名开的工（不知道本区在哪）：不标跨区，免得把本区当成别人', async ($, on) => {
  const { 板过, clock } = 准备(on, () => null)
  await 开会话($)
  await 轮始($, '做吧')
  await 跑($, '/usr/bin/python3 工具/板.py 开工 无限表格 --说 做')
  await 改($, 'Qlimen/无限表格/说明.md')
  await 改($, '创作/示例小说/TODO.md')
  await 轮终($)
  await clock.settle()
  expect(板过()).toEqual(['等你'])
})

test('读过交接、整轮却只在别的任务动笔：先亮读过的那个、那边标跨区，一轮结束本区挪过去（6.10）', async ($, on) => {
  const { 板过, clock } = 准备(on, () => null)
  await 开会话($)
  await 轮始($, '做吧')
  await 读($, 'Qlimen/无限表格/交接.md')
  await 改($, '创作/示例小说/草稿.md')
  await 轮终($)
  await clock.settle()
  expect(板过()).toEqual(['开工 Qlimen/无限表格 --说 「做吧」', '开工 创作/示例小说 --说 跨区施工（从 无限表格 过来）', '完工 Qlimen/无限表格', '等你 创作/示例小说 --说 「做吧」'])
})

test('子代理的轮不算，主线程的才算', async ($, on) => {
  const { 板过, clock } = 准备(on, () => null)
  await 开会话($)
  await 亮着($)
  await 轮始($, '子代理的活', 'sub1')
  await clock.settle()
  expect(板过()).toEqual(['开工 Qlimen/无限表格 --说 「做吧」'])
})

test('冷归档里、工作区外的文件不认', async ($, on) => {
  const { 板过, clock } = 准备(on, () => null)
  await 开会话($)
  await 轮始($, '整理一下')
  await 改($, '冷归档/旧任务/笔记.md')
  await 改($, '/tmp/随便.txt')
  await 轮终($)
  await clock.settle()
  expect(板过()).toEqual([])
})

// 11-01 一个脚本合集挪进工作区：它的 core/、ui/ 不在任何任务目录里
test('读过交接、又改了工作区里不属于任何任务的文件：亮读过的那个任务', async ($, on) => {
  const { 板过, clock } = 准备(on, () => null)
  await 开会话($)
  await 轮始($, '修一下脚本合集')
  await 读($, '创作/示例小说/交接.md')
  await 改($, '工具集/脚本合集/core/x.py')
  await 轮终($)
  await clock.settle()
  expect(板过()).toEqual(['开工 创作/示例小说 --说 「修一下脚本合集」', '等你 创作/示例小说'])
})

test('没读过任何任务的交接、TODO，就改工作区里不属于任务的文件：不亮', async ($, on) => {
  const { 板过, clock } = 准备(on, () => null)
  await 开会话($)
  await 轮始($, '随便改改')
  await 改($, '工具集/脚本合集/core/x.py')
  await 轮终($)
  await clock.settle()
  expect(板过()).toEqual([])
})

test('读过交接、但改的是工作区外或冷归档里的文件：不亮', async ($, on) => {
  const { 板过, clock } = 准备(on, () => null)
  await 开会话($)
  await 轮始($, '查点东西')
  await 读($, 'Qlimen/无限表格/交接.md')
  await 改($, '/tmp/随便.txt')
  await 改($, '冷归档/旧任务/笔记.md')
  await 轮终($)
  await clock.settle()
  expect(板过()).toEqual([])
})

test('它自己按任务名开工也算亮了，之后照样替它收工', async ($, on) => {
  const { 板过, clock } = 准备(on, () => null)
  await 开会话($)
  await 轮始($, '接着写第 31 章')
  await 跑($, '/usr/bin/python3 ~/Documents/工作区/Qlimen/无限表格/工具/板.py 开工 "创作/示例小说" --说 第31章')
  await 轮终($)
  await clock.settle()
  expect(板过()).toEqual(['等你 创作/示例小说'])
})

test('看板上的动作发进来的那一轮，灯上写「处理你在看板上的动作」', async ($, on) => {
  const { 板过, clock } = 准备(on, () => null)
  await 开会话($)
  await 亮着($)
  await 轮终($)
  await 轮始($, '【无限表格】我在看板上：\n- 无限表格·2.19：点了「做完了」')
  await clock.settle()
  expect(板过().at(-1)).toBe('开工 Qlimen/无限表格 --说 处理你在看板上的动作')
})

// ---------- 11-03（3.9）：终端命令也认 ----------

test('终端命令写了任务里的文件：亮灯', async ($, on) => {
  const { 板过, clock } = 准备(on, () => null)
  await 开会话($)
  await 轮始($, '做吧')
  await 跑($, `cp /tmp/新页面.txt ${根}Qlimen/无限表格/工具/板-页面.txt`)
  await 轮终($)
  await clock.settle()
  expect(板过()).toEqual(['开工 Qlimen/无限表格 --说 「做吧」', '等你 Qlimen/无限表格'])
})

test('cd 进任务目录再用相对路径原地改：亮那个任务', async ($, on) => {
  const { 板过, clock } = 准备(on, () => null)
  await 开会话($)
  await 轮始($, '改一下')
  await 跑($, `cd ${根}创作/示例小说 && sed -i '' 's/甲/乙/' 草稿.md`)
  await 轮终($)
  await clock.settle()
  expect(板过()).toEqual(['开工 创作/示例小说 --说 「改一下」', '等你 创作/示例小说'])
})

// ---------- 7.10 状态词 ----------
test('回复开头写【收工】、你没说收工：挂「收工」等你看，不撤（6.27）', async ($, on) => {
  const { 板过, clock } = 准备(on, () => null)
  await 开会话($)
  await 亮着($)
  await 轮终($, '【收工】改好了，没有要你做的')
  await clock.settle()
  expect(板过()).toEqual(['开工 Qlimen/无限表格 --说 「做吧」', '等你 Qlimen/无限表格 --收工'])
})

test('你说了收工、回复写【等你】：照词挂等你（词比规则准）', async ($, on) => {
  const { 板过, clock } = 准备(on, () => null)
  await 开会话($)
  await 轮始($, '收工吧')
  await 读($, 'Qlimen/无限表格/交接.md')
  await 改($, 'Qlimen/无限表格/说明.md')
  await 轮终($, '【等你】收工前还要你在小窗里点一下那个按钮。')
  await clock.settle()
  expect(板过()).toEqual(['开工 Qlimen/无限表格 --说 「收工吧」', '等你 Qlimen/无限表格'])
})

test('写【施工】、Stop 说什么都没在跑：照看到的挂等你，记一笔对不上（Stop 先到、后到都认）', async ($, on) => {
  const { 板过, clock } = 准备(on, () => null)
  await 开会话($)
  await 亮着($)
  await 停($)
  await 轮终($, '【施工】接着跑')
  await 亮着($)
  await 轮终($, '【施工】接着跑')
  await 停($)
  await clock.settle()
  expect(板过()).toEqual(['开工 Qlimen/无限表格 --说 「做吧」', '等你 Qlimen/无限表格 --对不上 说施工，什么都没在跑',
    '开工 Qlimen/无限表格 --说 「做吧」', '等你 Qlimen/无限表格', '等你 Qlimen/无限表格 --对不上 说施工，什么都没在跑'])
})

test('写【收工】、Stop 说后台还在跑：照看到的在干，记一笔对不上', async ($, on) => {
  const { 板过, clock } = 准备(on, () => null)
  await 开会话($)
  await 亮着($)
  await 轮终($, '【收工】好了')
  await 停($, 1)
  await clock.settle()
  expect(板过()).toEqual(['开工 Qlimen/无限表格 --说 「做吧」', '等你 Qlimen/无限表格 --收工',
    `开工 Qlimen/无限表格 --说 后台在跑 --租 ${120} --对不上 说收工，后台还在跑`])
})

test('零活：没碰过任务目录的会话，写【等你】就亮一行（标题是第一句话），下一轮在干，写【收工】灭', async ($, on) => {
  const { 板过, clock } = 准备(on, () => null)
  await 开会话($)
  await 轮始($, 'steam 下载走哪条线？')
  await 轮终($, '【等你】走线路一。要改成 A 吗？')
  await 轮始($, '不用了')
  await 轮终($, '【收工】好')
  await 轮始($, '再问一句')
  await 轮终($, '没写状态词的回复')
  await clock.settle()
  expect(板过()).toEqual([`等你 零活:${会} --题 「steam 下载走哪条线？」 --说 「steam 下载走哪条线？」`,
    `开工 零活:${会} --题 「steam 下载走哪条线？」 --说 「不用了」`, `完工 零活:${会}`])
})

test('零活的会话后来在任务里动笔：零活那行关掉，任务亮灯', async ($, on) => {
  const { 板过, clock } = 准备(on, () => null)
  await 开会话($)
  await 轮始($, '问一下')
  await 轮终($, '【等你】答好了')
  await 轮始($, '那改一下')
  await 改($, 'Qlimen/无限表格/说明.md')
  await 轮终($, '【等你】改好了，你看看')
  await clock.settle()
  expect(板过()).toEqual([`等你 零活:${会} --题 「问一下」 --说 「问一下」`, `开工 零活:${会} --题 「问一下」 --说 「那改一下」`,
    `完工 零活:${会}`, '开工 Qlimen/无限表格 --说 「那改一下」', '等你 Qlimen/无限表格'])
})

test('cd 进任务目录以后，下一条不写 cd、用相对路径改文件：照样亮那个任务（7.13）', async ($, on) => {
  const { 板过, clock } = 准备(on, () => null)
  await 开会话($)
  await 轮始($, '改一下')
  await 跑($, `cd ${根}创作/示例小说 && ls`)
  await 跑($, `cp 草稿.md 归档/草稿-备份.md`)
  await 轮终($)
  await clock.settle()
  expect(板过()).toEqual(['开工 创作/示例小说 --说 「改一下」', '等你 创作/示例小说'])
})

test('会话开始的目录就在任务里：没 cd 过，相对路径改文件也亮（7.13）', async ($, on) => {
  const { 板过, clock } = 准备(on, () => null)
  await $.session.start({ cwd: 根 + 'Qlimen/无限表格', surface: 'desktop', isInteractive: true })
  await 轮始($, '改')
  await 跑($, `sed -i '' 's/a/b/' 说明.md`)
  await 轮终($)
  await clock.settle()
  expect(板过()).toEqual(['开工 Qlimen/无限表格 --说 「改」', '等你 Qlimen/无限表格'])
})

test('只有 heredoc 正文里像文件名的字（s.replace、os.path）、或工作目录 cd 到了工作区外：不亮（7.13）', async ($, on) => {
  const { 板过, clock } = 准备(on, () => null)
  await 开会话($)
  await 轮始($, '看看')
  await 跑($, `cd ${根}创作/示例小说 && ls`)
  await 跑($, `python3 - <<'EOF'\nimport os.path\nprint(s.replace('a', 'b'))\nEOF`)
  await 跑($, `cd /tmp && ls`)
  await 跑($, `cp a.txt b.txt`)
  await 轮终($)
  await clock.settle()
  expect(板过()).toEqual([])
})

test('cd 到会话起始目录外面（/tmp）：工作目录会被拨回起始目录，之后的相对路径按起始目录算（7.13）', async ($, on) => {
  const { 板过, clock } = 准备(on, () => null)
  await $.session.start({ cwd: 根.replace(/\/$/, ''), surface: 'desktop', isInteractive: true })
  await 轮始($, '改')
  await 跑($, `cd /tmp/校准 && diff -u a b > 改法.diff`)
  await 跑($, `sed -i '' 's/a/b/' Qlimen/无限表格/说明.md`)
  await 轮终($)
  await clock.settle()
  expect(板过()).toEqual(['开工 Qlimen/无限表格 --说 「改」', '等你 Qlimen/无限表格'])
})

test('cd .. 回上级目录：相对路径按上级算（7.13）', async ($, on) => {
  const { 板过, clock } = 准备(on, () => null)
  await 开会话($)
  await 轮始($, '改脚本')
  await 跑($, `cd ${根}视频/示例MV/MV && ls`)
  await 跑($, `cd .. && cp 立绘.py 立绘-备份.py`)
  await 轮终($)
  await clock.settle()
  expect(板过()).toEqual(['开工 视频/示例MV --说 「改脚本」', '等你 视频/示例MV'])
})

test('终端命令只读交接、TODO：不亮，记下来；之后动笔亮的是读过的那个', async ($, on) => {
  const { 板过, clock } = 准备(on, () => null)
  await 开会话($)
  await 轮始($, '接着做')
  await 跑($, `head -c 3000 ${根}Qlimen/无限表格/交接.md; grep -n 现在 ${根}Qlimen/无限表格/TODO.md`)
  expect(板过()).toEqual([])
  await 跑($, `/usr/bin/python3 ${根}Qlimen/工具/某脚本.py`)   // 工作区里、不属于任务的脚本
  await 轮终($)
  await clock.settle()
  expect(板过()).toEqual(['开工 Qlimen/无限表格 --说 「接着做」', '等你 Qlimen/无限表格'])
})

test('只跑看板自己的命令（板.py 列）、往 /dev/null 重定向的只读命令：不亮', async ($, on) => {
  const { 板过, clock } = 准备(on, () => null)
  await 开会话($)
  await 轮始($, '看看')
  await 跑($, '/usr/bin/python3 ~/Documents/工作区/Qlimen/无限表格/工具/板.py 列')
  await 跑($, `ls ${根}创作/示例小说 >/dev/null 2>&1`)
  await 轮终($)
  await clock.settle()
  expect(板过()).toEqual([])
})

test('终端命令写了冷归档、工作区外的文件：不亮', async ($, on) => {
  const { 板过, clock } = 准备(on, () => null)
  await 开会话($)
  await 轮始($, '整理')
  await 跑($, `echo 1 > ${根}冷归档/旧任务/记录.md; cp a /tmp/b`)
  await 轮终($)
  await clock.settle()
  expect(板过()).toEqual([])
})

// ---------- 11-04（卷四 6.7，用户选 A）：你说了收工就灭灯，不挂等你 ----------

const 非开工 = (板过: () => string[]) => 板过().filter(x => !x.startsWith('开工'))

test('你说了收工、回复没在问你：一轮结束直接灭灯（完工），不挂等你', async ($, on) => {
  const { 板过, clock } = 准备(on, () => null)
  await 开会话($)
  await 亮着($)
  await 轮终($)
  await 轮始($, '名牌不用改，收工吧')
  await 改($, 'Qlimen/无限表格/交接.md')
  await 轮终($, '【已完成】已经收工，看板上的名牌是「等你」。下次从卷四接着做：先等你测完接手（6.1）。\n\n现在没有我起的进程在跑。')
  await clock.settle()
  expect(板过().slice(-2)).toEqual(['开工 Qlimen/无限表格 --说 「名牌不用改，收工吧」', '完工 Qlimen/无限表格'])
})

test('认你说的收工：这几天的原话都认得出；「没法收工」「收工前」「先别收工」「还不能收工吧」「收工了吗」、后台通知不算', async ($, on) => {
  const { 板过, clock } = 准备(on, () => null)
  await 开会话($)
  await 亮着($)
  await 轮终($)
  const 是 = ['收工吧', '好的，辛苦了，收工', '我这边已经关了，你先收工就行，明天再跑', '用了一天了，没问题，可以收工了，不用补', '不过今天该休息了，可以先暂停收工了', '好滴，辛苦，收工了可以']
  const 不是 = ['看无限表格任务卷二卷四，哪个可以先做，主要是目前还没法正常收工，还是有等你', '收工前把交接写了', '先别收工', '现在还不能收工吧', '今天没法收工了，明天接着', '你收工了吗？', '<task-notification>收工吧</task-notification>']
  for (const s of [...是, ...不是]) {
    await 轮始($, s)
    await 轮终($, '【已完成】好了。')
  }
  await clock.settle()
  expect(非开工(板过).slice(1)).toEqual([...是.map(() => '完工 Qlimen/无限表格'), ...不是.map(() => '等你 Qlimen/无限表格')])
})

test('回复在道别（明天见、不需要你再做）、你没说收工：挂「收工」等你看；还在问你、【进行中】、普通一轮照旧等你（6.27）', async ($, on) => {
  const { 板过, clock } = 准备(on, () => null)
  await 开会话($)
  await 亮着($)
  await 轮终($, '【已完成】今天的停点记好了。\n\n辛苦了，明天见。')
  await 轮始($, '额度那边看看')
  await 轮终($, '【已完成】Codex 本周用了 95%。\n\n现在没有在跑的东西，也不需要你再做什么。')
  await 轮始($, '收工吧')
  await 轮终($, '【已完成】交接写好了。\n\n收工前问一句：明天先做 A 还是 B？')
  await 轮始($, '好，收工')
  await 轮终($, '【进行中】还差一步，在等别的会话的结果。')
  await 轮始($, '看看哪个先做')
  await 轮终($, '【已完成】建议先修插件。\n\n现在在等你回复：选 A 还是 B。没有后台任务在跑。')
  await clock.settle()
  expect(非开工(板过)).toEqual(['等你 Qlimen/无限表格 --收工', '等你 Qlimen/无限表格 --收工', '等你 Qlimen/无限表格', '等你 Qlimen/无限表格', '等你 Qlimen/无限表格'])
})

test('你说了收工、但这一轮起了后台任务：还是在干，写「后台在跑」', async ($, on) => {
  const { 板过, clock } = 准备(on, () => null)
  await 开会话($)
  await 亮着($)
  await 轮终($)
  await 轮始($, '收工吧')
  await 跑($, 'sleep 600', true)
  await 轮终($, '【已完成】收工了，明天见。')
  await clock.settle()
  expect(板过().at(-1)).toBe('开工 Qlimen/无限表格 --说 后台在跑 --租 120')
})

// 11-03 22:5x 作者碰到的一盏：会话在别的任务的交接里记过一行，插件当成换任务；6.9 起只标跨区、这一轮结束关掉，本区不变
test('在别的任务交接里记了一行、你又说了收工：跨区那边关掉、本区灭灯，下一轮还亮本区', async ($, on) => {
  const { 板过, clock } = 准备(on, () => null)
  await 开会话($)
  await 亮着($)
  await 轮终($)
  await 轮始($, '用了一天了，没问题，可以收工了，不用补')
  await 改($, '创作/示例小说/交接.md')
  await 改($, 'Qlimen/无限表格/交接.md')   // 这一轮本区也动了笔，所以本区不挪
  await 轮终($, '【已完成】收工了。\n\n现在没有在跑的东西，也不需要你再做什么。')
  await 轮始($, '还有个事')
  await 轮终($)
  await clock.settle()
  expect(板过().slice(2)).toEqual([
    '开工 Qlimen/无限表格 --说 「用了一天了，没问题，可以收工了，不用补」',
    '开工 创作/示例小说 --说 跨区施工（从 无限表格 过来）',
    '完工 创作/示例小说',
    '完工 Qlimen/无限表格',
    '开工 Qlimen/无限表格 --说 「还有个事」',
    '等你 Qlimen/无限表格',
  ])
})

// ---------- 11-04（卷四 6.10）：一整轮只在别的任务动笔就挪本区；本区的上级任务目录算本区 ----------

test('一整轮只在别的任务里动笔：一轮结束本区挪过去，原来的灭灯，下一轮亮新的', async ($, on) => {
  const { 板过, clock } = 准备(on, () => null)
  await 开会话($)
  await 亮着($)
  await 轮终($)
  await 轮始($, '换去做示例小说')
  await 改($, '创作/示例小说/草稿.md')
  await 改($, '创作/示例小说/TODO.md')
  await 轮终($)
  await 轮始($, '继续')
  await 轮终($)
  await clock.settle()
  expect(板过().slice(2)).toEqual([
    '开工 Qlimen/无限表格 --说 「换去做示例小说」',
    '开工 创作/示例小说 --说 跨区施工（从 无限表格 过来）',
    '完工 Qlimen/无限表格',
    '等你 创作/示例小说 --说 「换去做示例小说」',
    '开工 创作/示例小说 --说 「继续」',
    '等你 创作/示例小说',
  ])
})

test('整轮在两个别的任务动笔：挪到动笔多的那个，另一个关掉', async ($, on) => {
  const { 板过, clock } = 准备(on, () => null)
  await 开会话($)
  await 亮着($)
  await 轮终($)
  await 轮始($, '做')
  await 改($, '创作/示例小说/交接.md')
  await 改($, '视频/示例MV/MV/分镜.md')
  await 改($, '视频/示例MV/MV/状态.json')
  await 轮终($)
  await clock.settle()
  expect(板过().slice(2)).toEqual([
    '开工 Qlimen/无限表格 --说 「做」',
    '开工 创作/示例小说 --说 跨区施工（从 无限表格 过来）',
    '开工 视频/示例MV/MV --说 跨区施工（从 无限表格 过来）',
    '完工 Qlimen/无限表格',
    '完工 创作/示例小说',
    '等你 视频/示例MV/MV --说 「做」',
  ])
})

test('改本区上级任务目录里的文件算本区：不标跨区、不挪（MV 的立绘脚本放在父目录）', async ($, on) => {
  const { 板过, clock } = 准备(on, () => null)
  await 开会话($)
  await 轮始($, '出立绘')
  await 读($, '视频/示例MV/MV/交接.md')
  await 改($, '视频/示例MV/MV/状态.json')
  await 轮终($)
  await 轮始($, '改脚本')
  await 改($, '视频/示例MV/跑MV立绘.py')
  await 轮终($)
  await clock.settle()
  expect(板过()).toEqual([
    '开工 视频/示例MV/MV --说 「出立绘」',
    '等你 视频/示例MV/MV',
    '开工 视频/示例MV/MV --说 「改脚本」',
    '等你 视频/示例MV/MV',
  ])
})

// ---------- 11-04（卷四 6.11）：两盏灯反了 ----------

test('写进文档里的「板.py 完工」不算敲了完工（heredoc 正文、echo 进说明的都不算）：这一轮照样收工', async ($, on) => {
  const { 板过, clock } = 准备(on, () => null)
  await 开会话($)
  await 亮着($)
  await 跑($, `/usr/bin/python3 -I - <<'EOF'\np = '${根}Qlimen/无限表格/交接.md'\ns = '一轮结束插件直接 \`板.py 完工\`；做完了敲 \`/usr/bin/python3 工具/板.py 完工 Qlimen/无限表格\`'\nEOF`)
  await 跑($, `echo '规矩：做完了敲 板.py 完工 任务' >> ${根}Qlimen/无限表格/说明.md`)
  await 轮终($)
  await clock.settle()
  expect(板过()).toEqual(['开工 Qlimen/无限表格 --说 「做吧」', '等你 Qlimen/无限表格'])
})

test('停下时还有前一轮起的后台在跑：还是在干、后台在跑（11-04 盯跑那盏）', async ($, on) => {
  const { 板过, clock } = 准备(on, () => null)
  await 开会话($)
  await 亮着($)
  await 跑($, 'python3 watch.py 6', true)
  await 停($, 1)
  await 轮终($)
  await 轮始($, '修吧，新BOSS明天再学')
  await 改($, 'Qlimen/无限表格/说明.md')
  await 停($, 1)
  await 轮终($, '【已完成】修好了，后台照常盯着。')
  await clock.settle()
  expect(板过().slice(-2)).toEqual(['开工 Qlimen/无限表格 --说 「修吧，新BOSS明天再学」', '开工 Qlimen/无限表格 --说 后台在跑 --租 120'])
})

test('Stop 比一轮结束晚到：已经收工了，Stop 说还有后台在跑，就补成在干', async ($, on) => {
  const { 板过, clock } = 准备(on, () => null)
  await 开会话($)
  await 亮着($)
  await 轮终($)
  await 停($, 1)
  await clock.settle()
  expect(板过()).toEqual(['开工 Qlimen/无限表格 --说 「做吧」', '等你 Qlimen/无限表格', '开工 Qlimen/无限表格 --说 后台在跑 --租 120'])
})

test('只剩定时叫醒：也算在干；Stop 说什么都没在跑：照旧等你（这一轮起过、已经跑完的后台不算）', async ($, on) => {
  const { 板过, clock } = 准备(on, () => null)
  await 开会话($)
  await 亮着($)
  await 停($, 0, 1)
  await 轮终($)
  await 轮始($, '再看看')
  await 跑($, 'sleep 1', true)
  await 停($, 0, 0)
  await 轮终($)
  await clock.settle()
  expect(板过()).toEqual([
    '开工 Qlimen/无限表格 --说 「做吧」',
    '开工 Qlimen/无限表格 --说 等定时叫醒 --租 120',
    '开工 Qlimen/无限表格 --说 「再看看」',
    '等你 Qlimen/无限表格',
  ])
})

// ---------- 11-05 卷四 6.24 乙（用户：回复写了等你、后台还在跑，名牌写「等你」、亮片照走）、卷二 7.20（收工 = 灭灯，交付敲「等你」）----------

test('6.24：写【等你】、这一轮起的后台还在跑：照旧在干（亮片照走），带 --要你', async ($, on) => {
  const { 板过, clock } = 准备(on, () => null)
  await 开会话($)
  await 亮着($)
  await 跑($, 'python3 watch.py 6', true)
  await 轮终($, '【等你】清单写好了，等你批；后台在盯着。')
  await clock.settle()
  expect(板过().at(-1)).toBe('开工 Qlimen/无限表格 --说 后台在跑 --租 120 --要你')
})

test('6.24：写【等你】、Stop 晚到说后台还在跑：先交付，再补成在干、带 --要你', async ($, on) => {
  const { 板过, clock } = 准备(on, () => null)
  await 开会话($)
  await 亮着($)
  await 轮终($, '【等你】要你批一下')
  await 停($, 1)
  await clock.settle()
  expect(板过()).toEqual(['开工 Qlimen/无限表格 --说 「做吧」', '等你 Qlimen/无限表格', '开工 Qlimen/无限表格 --说 后台在跑 --租 120 --要你'])
})

test('6.24：零活写【等你】、后台还在跑：那一行在干、带 --要你', async ($, on) => {
  const { 板过, clock } = 准备(on, () => null)
  await 开会话($)
  await 轮始($, '帮我盯一下下载')
  await 跑($, 'python3 watch.py', true)
  await 轮终($, '【等你】在盯着，要换线路吗？')
  await clock.settle()
  expect(板过()).toEqual([`开工 零活:${会} --题 「帮我盯一下下载」 --说 后台在跑 --租 120 --要你`])
})

test('6.24：写【施工】、后台还在跑：照旧在干，不带 --要你', async ($, on) => {
  const { 板过, clock } = 准备(on, () => null)
  await 开会话($)
  await 亮着($)
  await 跑($, 'python3 watch.py 6', true)
  await 轮终($, '【施工】后台在跑，跑完叫我。')
  await 停($, 1)
  await clock.settle()
  expect(板过().slice(1)).toEqual(['开工 Qlimen/无限表格 --说 后台在跑 --租 120'])
})

test('7.20：它自己敲了 板.py 收工 = 完工：不再亮；你没说收工，照样挂「收工」等你看（6.27）', async ($, on) => {
  const { 板过, clock } = 准备(on, () => null)
  await 开会话($)
  await 亮着($)
  await 跑($, '/usr/bin/python3 工具/板.py 收工 Qlimen/无限表格')
  await 轮终($, '【等你】还有一句话要问你')
  await 轮始($, '谢谢')
  await 轮终($)
  await clock.settle()
  expect(板过()).toEqual(['开工 Qlimen/无限表格 --说 「做吧」', '等你 Qlimen/无限表格 --收工', '完工 Qlimen/无限表格'])
})

test('7.20：它自己敲了 板.py 施工 = 开工：亮那个任务，之后照样替它交付（敲等你）', async ($, on) => {
  const { 板过, clock } = 准备(on, () => null)
  await 开会话($)
  await 轮始($, '接着写第 31 章')
  await 跑($, '/usr/bin/python3 ~/Documents/工作区/Qlimen/无限表格/工具/板.py 施工 "创作/示例小说" --说 第31章')
  await 轮终($)
  await clock.settle()
  expect(板过()).toEqual(['等你 创作/示例小说'])
})

// ---------- 11-05 卷四 6.27（用户：「我还没看的就不要撤走任务」；熄灯只摘掉负责人的框，不把任务撤下第 1 层）----------

test('6.27：写【收工】、你这一轮说了收工：看过了，直接灭灯（6.7 照旧）', async ($, on) => {
  const { 板过, clock } = 准备(on, () => null)
  await 开会话($)
  await 轮始($, '改一下说明，改完收工吧')
  await 读($, 'Qlimen/无限表格/交接.md')
  await 改($, 'Qlimen/无限表格/说明.md')
  await 轮终($, '【收工】改好了')
  await clock.settle()
  expect(板过()).toEqual(['开工 Qlimen/无限表格 --说 「改一下说明，改完收工吧」', '完工 Qlimen/无限表格'])
})

test('6.27：它自己敲了完工、你这一轮说了收工：不挂「收工」', async ($, on) => {
  const { 板过, clock } = 准备(on, () => null)
  await 开会话($)
  await 轮始($, '做完就收工吧')
  await 读($, 'Qlimen/无限表格/交接.md')
  await 改($, 'Qlimen/无限表格/说明.md')
  await 跑($, '/usr/bin/python3 工具/板.py 收工 Qlimen/无限表格')
  await 轮终($, '【收工】好了')
  await clock.settle()
  expect(板过()).toEqual(['开工 Qlimen/无限表格 --说 「做完就收工吧」'])
})

test('6.27：挂着「收工」、来的是后台通知：不算你回话，「收工」留着', async ($, on) => {
  const { 板过, clock } = 准备(on, () => null)
  await 开会话($)
  await 亮着($)
  await 跑($, '/usr/bin/python3 工具/板.py 完工 Qlimen/无限表格')
  await 轮终($, '【收工】做完了')
  await 轮始($, '<task-notification>后台任务结束了</task-notification>')
  await 轮终($, '好')
  await clock.settle()
  expect(板过()).toEqual(['开工 Qlimen/无限表格 --说 「做吧」', '等你 Qlimen/无限表格 --收工'])
})

test('6.27：写【收工】挂着「收工」，你回话：照常开工（同一盏灯换掉「收工」）', async ($, on) => {
  const { 板过, clock } = 准备(on, () => null)
  await 开会话($)
  await 亮着($)
  await 轮终($, '【收工】做完了')
  await 轮始($, '再加一条')
  await clock.settle()
  expect(板过()).toEqual(['开工 Qlimen/无限表格 --说 「做吧」', '等你 Qlimen/无限表格 --收工', '开工 Qlimen/无限表格 --说 「再加一条」'])
})

// ---------- 11-05 卷四 6.32（用户：「我只是让你查一下施工区，为啥任务就变成了MV了」）：只读的不算动笔 ----------

test('6.32：只读的 python heredoc（正文里是别的任务的路径）不算动笔：不标跨区，一整轮这样也不挪本区', async ($, on) => {
  const { 板过, clock } = 准备(on, () => null)
  await 开会话($)
  await 亮着($)
  await 轮终($)
  await 轮始($, '查一下施工区')
  await 跑($, `/usr/bin/python3 - <<'EOF'\nimport json, re\nd = json.loads(open('${根}视频/示例MV/MV/导演台/状态.json', encoding='utf-8').read())\nprint(len(d))\nEOF`)
  await 轮终($, '【等你】查完了')
  await clock.settle()
  expect(板过()).toEqual(['开工 Qlimen/无限表格 --说 「做吧」', '等你 Qlimen/无限表格', '开工 Qlimen/无限表格 --说 「查一下施工区」', '等你 Qlimen/无限表格'])
})

test('6.32：写文件的 python heredoc 照旧算动笔（别的任务标跨区）', async ($, on) => {
  const { 板过, clock } = 准备(on, () => null)
  await 开会话($)
  await 亮着($)
  await 跑($, `/usr/bin/python3 - <<'EOF'\np = '${根}创作/示例小说/TODO.md'\nopen(p, 'w', encoding='utf-8').write('x')\nEOF`)
  await 轮终($)
  await clock.settle()
  expect(板过()).toEqual(['开工 Qlimen/无限表格 --说 「做吧」', '开工 创作/示例小说 --说 跨区施工（从 无限表格 过来）', '完工 创作/示例小说', '等你 Qlimen/无限表格'])
})

test('6.32：python -c 只读不算动笔', async ($, on) => {
  const { 板过, clock } = 准备(on, () => null)
  await 开会话($)
  await 亮着($)
  await 跑($, `/usr/bin/python3 -c "import sys; print(open(sys.argv[1]).read()[:10])" ${根}创作/示例小说/TODO.md`)
  await 轮终($)
  await clock.settle()
  expect(板过()).toEqual(['开工 Qlimen/无限表格 --说 「做吧」', '等你 Qlimen/无限表格'])
})

test('6.32：cd 进任务目录跑看板的只读命令（板.py 列）不亮', async ($, on) => {
  const { 板过, clock } = 准备(on, () => null)
  await 开会话($)
  await 轮始($, '看看进度')
  await 跑($, `cd ${根}Qlimen/无限表格 && /usr/bin/python3 工具/板.py 列 2>&1 | head -80`)
  await 轮终($, '【等你】进度在这')
  await clock.settle()
  expect(板过().filter(x => !x.includes('零活'))).toEqual([])
})

test('6.32：跑脚本文件（看不到里面）照旧算在写', async ($, on) => {
  const { 板过, clock } = 准备(on, () => null)
  await 开会话($)
  await 轮始($, '改一下')
  await 跑($, `cd ${根}创作/示例小说 && /usr/bin/python3 脚本/改稿.py`)
  await 轮终($)
  await clock.settle()
  expect(板过()).toEqual(['开工 创作/示例小说 --说 「改一下」', '等你 创作/示例小说'])
})

// ---------- 11-05 卷四 6.33：一条命令里串了几个 板.py 命令，按先后全认 ----------

test('6.33：一条命令里「完工 A && 开工 B」：本区换到 B，轮结束照状态词给 B 挂等你', async ($, on) => {
  const { 板过, clock } = 准备(on, () => null)
  await 开会话($)
  await 轮始($, '换一下')
  await 跑($, '/usr/bin/python3 工具/板.py 完工 创作/示例小说 && /usr/bin/python3 工具/板.py 开工 Qlimen/无限表格 --说 接着')
  await 轮终($, '【等你】好了')
  await clock.settle()
  expect(板过()).toEqual(['等你 Qlimen/无限表格'])
})

test('6.33：一条命令里「开工 A && 完工 A」：算完工，你没说收工就挂「收工」等你看', async ($, on) => {
  const { 板过, clock } = 准备(on, () => null)
  await 开会话($)
  await 轮始($, '做完')
  await 跑($, '/usr/bin/python3 工具/板.py 开工 创作/示例小说 && /usr/bin/python3 工具/板.py 完工 创作/示例小说')
  await 轮终($, '【等你】做完了')
  await clock.settle()
  expect(板过()).toEqual(['等你 创作/示例小说 --收工'])
})

// ---------- 11-05 卷四 6.37：问答卡片、计划审批弹着就是等你 ----------
const 问 = ($: any, question: string) => $.tool.call({ tool: 'AskUserQuestion', questions: [{ question, header: '定一下', multiSelect: false, options: [{ label: '甲', description: '' }, { label: '乙', description: '' }] }] })

test('6.37：弹问答卡片：先切等你（名牌写问题），你选完切回施工，一轮结束照状态词', async ($, on) => {
  const { 板过, clock } = 准备(on, () => null)
  await 开会话($)
  await 亮着($)
  await 问($, '这轮榜单刷新做到哪一步？')
  await 轮终($, '【等你】照你选的做完了')
  await clock.settle()
  expect(板过()).toEqual(['开工 Qlimen/无限表格 --说 「做吧」', '等你 Qlimen/无限表格 --说 问你：「这轮榜单刷新做到哪一步？」', '开工 Qlimen/无限表格 --说 「做吧」', '等你 Qlimen/无限表格'])
})

test('6.37：计划审批也一样：先等你批，批了切回施工', async ($, on) => {
  const { 板过, clock } = 准备(on, () => null)
  await 开会话($)
  await 亮着($)
  await $.tool.call({ tool: 'ExitPlanMode', plan: '先改插件，再加测试' })
  await clock.settle()
  expect(板过()).toEqual(['开工 Qlimen/无限表格 --说 「做吧」', '等你 Qlimen/无限表格 --说 等你批计划', '开工 Qlimen/无限表格 --说 「做吧」'])
})

test('6.37：没亮灯的会话弹问答卡片：亮零活那一行写等你，选完切回在干', async ($, on) => {
  const { 板过, clock } = 准备(on, () => null)
  await 开会话($)
  await 轮始($, '榜单先做哪个？')
  await 问($, '先做哪个？')
  await clock.settle()
  expect(板过()).toEqual([`等你 零活:${会} --题 「榜单先做哪个？」 --说 问你：「先做哪个？」`, `开工 零活:${会} --题 「榜单先做哪个？」 --说 「榜单先做哪个？」`])
})

test('6.37：别的工具（读文件、跑命令）不切灯', async ($, on) => {
  const { 板过, clock } = 准备(on, () => null)
  await 开会话($)
  await 亮着($)
  await 读($, 'Qlimen/无限表格/TODO.md')
  await 跑($, 'ls')
  await clock.settle()
  expect(板过()).toEqual(['开工 Qlimen/无限表格 --说 「做吧」'])
})

test('6.37：权限弹框（要你批准命令）：切等你、写批准什么，批了那个工具走完切回施工', async ($, on) => {
  const { 板过, clock } = 准备(on, () => null)
  await 开会话($)
  await 亮着($)
  await $.classic.PermissionRequest({ hook_event_name: 'PermissionRequest', session_id: 's', transcript_path: '', cwd: '/', tool_name: 'Bash', tool_input: { command: 'rm -rf /tmp/x' } })
  await 跑($, 'rm -rf /tmp/x')
  await clock.settle()
  expect(板过()).toEqual(['开工 Qlimen/无限表格 --说 「做吧」', '等你 Qlimen/无限表格 --说 等你批准：Bash', '开工 Qlimen/无限表格 --说 「做吧」'])
})

// ---------- 11-05 卷四 6.40（用户：「大模型网站明明是自己派工，却显示跨区」；某平台问答卡片的问题被「等你批准」盖掉）----------

test('6.40：cd 进子目录再写 ../ 的文件：还是本区，不在自己身上标跨区', async ($, on) => {
  const { 板过, clock } = 准备(on, () => null)
  await 开会话($)
  await 亮着($)
  await 跑($, `cd ${根}Qlimen/无限表格/工具 && /usr/bin/python3 排队.py >> ../数据/排队输出.log 2>&1`)
  await 轮终($)
  await clock.settle()
  expect(板过()).toEqual(['开工 Qlimen/无限表格 --说 「做吧」', '等你 Qlimen/无限表格'])
})

test('6.40 复核（11-05 19:1x 用户截图：榜单又标了「跨区施工（从 模型榜单 过来）」，是 03:44 开的会话还在用改前的插件）：榜单 17:31、18:39 原样的两种命令都算本区', async ($, on) => {
  const { 板过, clock } = 准备(on, () => null)
  await 开会话($)
  await 亮着($)
  await 跑($, `cd ${根}Qlimen/无限表格/工具 && /usr/bin/python3 排队.py >> ../历史资料/整理前/排队输出.log 2>&1`)
  await 跑($, `cd ${根}Qlimen/无限表格 && /usr/bin/python3 工具/准备.py`)
  await 跑($, 'date +%H:%M:%S; tail -5 历史资料/整理前/排队输出.log | cut -c1-160; cd 工具 && for g in 甲 乙; do /usr/bin/python3 抽.py ../历史资料/整理前/日志/榜单-$g.log 复核-$g 2>&1 | tail -1 | cut -c1-200; done')
  await 轮终($)
  await clock.settle()
  expect(板过()).toEqual(['开工 Qlimen/无限表格 --说 「做吧」', '等你 Qlimen/无限表格'])
})

test('6.40：历史资料里的旧副本（也有 TODO.md）不当任务：在里面写东西算本区', async ($, on) => {
  const { 板过, clock } = 准备(on, () => null)
  await 开会话($)
  await 亮着($)
  await 改($, 'Qlimen/无限表格/历史资料/整理前/方案.md')
  await 轮终($)
  await clock.settle()
  expect(板过()).toEqual(['开工 Qlimen/无限表格 --说 「做吧」', '等你 Qlimen/无限表格'])
})

test('6.40：问答卡片顺带发的权限请求不再记「等你批准」（卡片那边已经切过等你）', async ($, on) => {
  const { 板过, clock } = 准备(on, () => null)
  await 开会话($)
  await 亮着($)
  await $.classic.PermissionRequest({ hook_event_name: 'PermissionRequest', session_id: 's', transcript_path: '', cwd: '/', tool_name: 'AskUserQuestion', tool_input: {} })
  await clock.settle()
  expect(板过()).toEqual(['开工 Qlimen/无限表格 --说 「做吧」'])
})

// ---------- 11-06 卷四 6.78（用户：「都修一下」；我把 MV 存档 rsync 到 /tmp 当测试副本，插件在 MV 上标了跨区）----------

test('6.78：rsync、cp 只是从别的任务复制出来：不算在那边动笔、不标跨区', async ($, on) => {
  const { 板过, clock } = 准备(on, () => null)
  await 开会话($)
  await 亮着($)
  await 跑($, `rsync -rlpt ${根}视频/示例MV/MV/导演台/ /tmp/ban底行/导演台/ && : > /tmp/ban底行/账本.csv`)
  await 跑($, `cp ${根}创作/示例小说/人设.md /tmp/人设.md`)
  await 跑($, `cd ${根}视频/示例MV/MV && rsync -a 导演台/ /tmp/y/`)
  await 轮终($)
  await clock.settle()
  expect(板过()).toEqual(['开工 Qlimen/无限表格 --说 「做吧」', '等你 Qlimen/无限表格'])
})

test('6.78：复制到别的任务里（目标在那边）照旧算动笔、标跨区', async ($, on) => {
  const { 板过, clock } = 准备(on, () => null)
  await 开会话($)
  await 亮着($)
  await 跑($, `cp /tmp/人设.md ${根}创作/示例小说/人设.md`)
  await 轮终($)
  await clock.settle()
  expect(板过()).toEqual(['开工 Qlimen/无限表格 --说 「做吧」', '开工 创作/示例小说 --说 跨区施工（从 无限表格 过来）', '完工 创作/示例小说', '等你 Qlimen/无限表格'])
})
