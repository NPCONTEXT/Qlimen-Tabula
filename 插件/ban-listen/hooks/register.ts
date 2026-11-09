import type { EngineInterface, Register } from 'claude-code'

// 无限表格监听：Qlimen Tabula（无限表格）给 Claude 桌面应用的插件。装法见仓库 docs/使用说明.md。
// 1. 会话开始时，小窗没在运行就在后台拉起它（open -g：不抢焦点；小窗没开看板服务的话会自己起）。已经在运行的不碰——
//    用户可能把它收到了菜单栏，open 会发「重新打开」把它弹回来（11-01 17:1x 加了收起到菜单栏）。
// 2. 每 3 秒看一眼这个会话的信箱 无限表格/数据.nosync/信箱/<会话号>.jsonl——用户在看板上点的、写的，看板服务按任务
//    投给开工时记下的会话；用户停手 20 秒（最多攒 2 分钟）后，替用户把这一批发进会话。会话正忙就排队，空了再发
//    （$.prompt.submit 的规矩）。发到第几号记在 $.store，重开会话也不重发。
// 3. 替会话开关灯（11-01 20:1x 批，评估见方案第十三节）：会话不用自己记得敲 板.py 开工 / 等你。
//    11-03 起终端命令也认（3.9，用户：「插件先修」）：命令里出现工作区路径，像在写（重定向、cp/mv、sed -i、跑脚本……）就算动笔，只读到交接、TODO 就先记下。
//    认任务：读到哪个任务的 交接.md / TODO.md 先记下（不亮灯：只读不改的多半是顺手查进度，14 天里占 12%）；
//    第一次在工作区里改文件、或者它自己敲了 板.py 开工，就亮灯（这就是它的本区）；之后在别的任务里动笔（改文件、写交接）不换任务，
//    那个任务标「跨区施工（从 X 过来）」，这一轮结束就关掉（11-04 卷四 6.9，用户：「其实不用硬修，完全可以标记跨区施工，等跨完把跨区的任务关掉就行」）；
//    改本区上级任务目录里的文件也算本区（MV 的立绘脚本放在父目录 示例MV）；一整轮只在别的任务里动笔 → 一轮结束本区挪过去、原来的灭灯
//    （6.10，用户：「可以，加吧」）；真要换任务也可以敲 板.py 开工 新任务。
//    一轮开始（用户发话）→ 在干；一轮结束 → 等你；停下时还有后台任务在跑、或定好了定时叫醒 → 还是在干、写「后台在跑」、租两小时
//    （看 Stop 事件的 background_tasks、session_crons，哪一轮起的都算；6.11：盯跑的监听是前一轮起的，以前被挂成等你）；
//    11-04 起（卷四 6.7，用户选 A）：你这一轮说了收工、或回复末尾在道别（明天见、放心关、不需要你再做……）又没在问你 → 一轮结束直接灭灯；
//    只看「【已完成】、没写要你做事」会把四成在问你的判成做完（653 轮里抽 22 条错 9 条），所以只认这两种；
//    它自己敲了 板.py 完工 → 这一轮结束不再亮，直到它再动笔。子代理的轮不算，子代理改的文件算。
// 只管 Claude 这边：会话号是桌面应用的 CLAUDE_CODE_HOST_SESSION_ID；别家照信箱的格式、开工的 --会话 自己接。

// 看板（本仓库）装在哪：装插件时写进 看板位置.txt（工具/装插件.sh 会写）；没有就当它在 ~/Documents/Qlimen-Tabula
const 位置文件 = '/.claude/skills/ban-listen/看板位置.txt'   // 接在 HOME 后面
const 默认看板 = '/Documents/Qlimen-Tabula'                  // 接在 HOME 后面
let 板目录 = ''   // 看板仓库的绝对路径，会话开始时定
let 工作区 = ''   // 工作区的绝对路径，结尾带 /：看板 设置.json 里的「工作区」，没设就是 板目录/示例/演示工作区（和 板.py 一样）
const 每 = 3_000
const 静 = 20_000
const 最长 = 120_000
const 后台租分 = 120

type 信 = { 号: number; 秒?: number; 名?: string; 摘要?: string }
// 候选：读过交接、TODO 的任务；任务：已经亮了灯的任务（它自己按名字开工的话可能不知道，看板那边按会话号认）
type 灯态 = { 候选?: string; 任务?: string; 亮了: boolean; 零活?: boolean; 首句?: string; 收工没看?: boolean }   // 收工没看：挂着「收工」等用户看（6.27），用户一回话就撤   // 零活：没碰过任务目录、照状态词亮着的那一行；首句：会话第一句话，当零活的标题

let 首见: number | null = null   // 这一批第一条是什么时候看到的
let 忙 = false                    // 上一次还没看完，这一次就不看（免得同一批发两遍）
let 环境: { 家: string; 会: string } | null = null
let 态: 灯态 = { 亮了: false }
let 目录在: string | null = null   // Bash 的工作目录停在哪：会话开始时是会话的 cwd，之后跟着每条命令最后一个 cd 走（11-04 7.13）
let 起点: string | null = null     // 会话开始的 cwd：cd 到它外面（比如 /tmp），Claude Code 跑完命令会把工作目录拨回这里（11-04 实测「Shell cwd was reset」）
// 这一轮的账：跨区 = 去别的任务动过笔、标了「跨区施工」的，次 = 各跨区动了几笔，本区写 = 本区（含上级）动过笔没有；
// 在飞 = Stop 时还在跑的（undefined：Stop 还没到）；收了 = 一轮结束时做了什么（'收'：收工或灭灯，'后台'：在干、后台在跑）
const 新轮 = (文 = '') => ({ 文, 词: '', 后台: false, 完工: false, 跨区: [] as string[], 次: {} as Record<string, number>, 本区写: false, 在飞: undefined as string | undefined, 收了: '', 等批: false })   // 等批：权限弹框弹着（6.37）
let 本轮 = 新轮()
let 队: Promise<unknown> = Promise.resolve()   // 开关灯排着队一条条跑，不乱序

const 读信 = (文: string): 信[] =>
  文.split('\n').flatMap(l => {
    try {
      const e = JSON.parse(l)
      return typeof e?.号 === 'number' ? [e as 信] : []
    } catch {
      return []
    }
  })

export const 话 = (批: 信[]) =>
  [
    '【无限表格】我在看板上：',
    ...批.map(e => `- ${e.摘要 ?? ''}`),
    `先跑 /usr/bin/python3 ${板目录}/工具/板.py 列 看全（会顺带列出各施工区的），再照着处理。`,
  ].join('\n')

/** 灯上那句话：用户这一轮说的开头 */
export const 说法 = (文: string) => {
  const s = 文.trim()
  if (s.startsWith('【无限表格】')) return '处理你在看板上的动作'
  if (!s || s.startsWith('<')) return '接着干'   // 后台跑完的通知之类
  const 首 = s.split('\n')[0]
  return `「${首.length > 24 ? 首.slice(0, 24) + '…' : 首}」`
}

/** 你这一轮说了收工：「收工吧」「可以收工了」「先收工就行」「……，收工」；「没法正常收工」「先别收工」「收工前」「收工了吗」、后台通知不算 */
/** 回复开头的状态词（卷二 7.10、核心 §5）：【施工】【等你】【收工】。旧的【进行中】【已完成】和没写的返回 null，照旧按规则猜 */
export const 状态词 = (答: string): '施工' | '等你' | '收工' | null => {
  const m = /^\s*【(施工|等你|收工)】/.exec(答)
  return m ? (m[1] as '施工' | '等你' | '收工') : null
}
const 零活键 = () => '零活:' + (环境?.会 ?? '')
/** 这个会话第一次在任务里亮灯：先前亮着的零活那一行关掉 */
const 收零活 = ($: EngineInterface) => {
  if (!态.零活) return
  板($, ['完工', 零活键()])
  态.零活 = false
}

export const 说收工 = (文: string) => {
  const s = 文.trim()
  if (s.startsWith('<') || s.startsWith('【无限表格】')) return false
  const 去否定 = s.replace(/(?:没|不|别|未|无法|不能|没法)[^，,。.！!？?\n]{0,6}(?:收工|完工)/g, '')
  return /(?:收工|完工)(?:吧|啦|呗|就行|就好)|(?:收工|完工)了(?![吗么没？?])|(?:可以|先|就)(?:暂停)?(?:收工|完工)|(?:^|[，,。.！!\s])(?:收工|完工)[。.！!～~\s]*$/.test(去否定)
}

/** 这一轮结束不用挂「等你」：你说了收工、或回复末尾两段在道别，又没在问你（问号、在等你回复）；【进行中】的照旧等你 */
export const 不用等你 = (问: string, 答: string) => {
  if (答.trimStart().startsWith('【进行中】')) return false
  const 尾 = 答.trim().split(/\n\s*\n/).filter(p => p.trim()).slice(-2).join('\n')
  if (!(说收工(问) || /明天见|下次见|回见|好好休息|早点休息|放心关|不(?:需要|用)你(?:再)?做|没有要你做/.test(尾))) return false
  return !/[？?]|在等你回|等你回复|等你回话|等你拍板|等你决定/.test(尾)
}

/** 命令里真敲了 板.py 开工 / 施工 / 等你 / 收工 / 完工（python 跑的）；heredoc 正文里、写进文档的「`板.py 完工`」不算。施工 = 开工；收工 = 完工（11-05 7.20 起）
 *  （11-04 6.11：我往交接里写了这几个字，被当成敲了完工，那一轮结束没收工，灯一直停在施工） */
export const 敲板 = (cmd: string) =>   // 一条命令里串了几个，按先后全认出来（11-05 卷四 6.33：以前只认第一个，「开工 A && 完工 A && 开工 B」插件以为还在 A，轮结束把 B 当跨区关了）
  [...cmd.replace(/<<-?\s*(['"]?)(\w+)\1[^\n]*\n[\s\S]*?\n\s*\2[ \t]*(?=\n|$)/g, '').matchAll(
    /(?:^|[\s;&|(])(?:\S*\/)?python3?(?:\s+-\w+)*\s+['"]?[^\s'"]*板\.py['"]?\s+(开工|施工|等你|收工|完工)(?:\s+([^\s-]\S*))?/g,
  )]

const 看信箱 = async ($: EngineInterface, 箱: string, 键: string) => {
  if (!(await $.fs.exists(箱))) return
  const 已 = Number((await $.store.get(键)) ?? 0)
  const 新 = 读信(await $.fs.read(箱)).filter(e => e.号 > 已)
  if (!新.length) {
    首见 = null
    return
  }
  const 现在 = await $.clock.now()
  首见 ??= 现在
  const 最后 = Math.max(...新.map(e => (e.秒 ?? 0) * 1000))
  if (现在 - 最后 < 静 && 现在 - 首见 < 最长) return
  await $.store.set(键, Math.max(...新.map(e => e.号)))
  首见 = null
  void $.prompt.submit({ text: 话(新), asUser: true })
}

const 拉起小窗 = async ($: EngineInterface, 窗: string) => {
  const { exitCode } = await $.process.run(['/usr/bin/pgrep', '-x', 'BanWindow'])
  if (exitCode !== 0) await $.process.run(['/usr/bin/open', '-g', 窗])
}

// ---------- 替会话开关灯 ----------

/** 排队跑一条 板.py（开工 / 等你 / 完工），带上会话号。11-05（7.20）起交付敲「等你」：板.py 的「收工」改成灭灯了，和核心 §5 的状态词一样 */
const 板 = ($: EngineInterface, 参数: string[]) => {
  if (!环境) return
  const argv = ['/usr/bin/python3', 板目录 + '/工具/板.py', ...参数, '--会话', 环境.会, '--接入', 'claude']
  队 = 队.then(() => $.process.run(argv)).catch(() => undefined)
}

/** 6.24 乙（用户 11-05 01:0x）：回复写了【等你】、后台又还在跑——照旧算在干（亮片照走），开工带 --要你，看板名牌写「等你」 */
const 要你 = (词: string | null | undefined) => (词 === '等你' ? ['--要你'] : [])

/** 问答卡片、计划审批（卷四 6.37，用户 11-05：「看板好像没法识别问答卡片？」）：卡片在一轮中途弹着等你选，这一轮没结束，
 *  以前灯一直是施工；现在弹之前切等你（名牌写卡片上的问题），你选完切回施工。不是卡片返回空串 */
export const 卡片说 = (a: Record<string, unknown>): string => {
  const 名 = String(a.tool ?? '')
  if (名 === 'ExitPlanMode') return '等你批计划'
  if (名 !== 'AskUserQuestion') return ''
  const qs = Array.isArray(a.questions) ? (a.questions as Array<Record<string, unknown>>) : []
  const 问 = String(qs[0]?.question ?? qs[0]?.header ?? '').trim()
  return '问你：' + (问 ? 说法(问) : '选一下')
}
const 等卡 = ($: EngineInterface, 说: string) => {
  if (态.亮了 && 态.任务) 板($, ['等你', 态.任务, '--说', 说])
  else if (!态.亮了) {   // 没碰过任务目录的会话：亮零活那一行（卷二 7.10）
    板($, ['等你', 零活键(), '--题', 态.首句 ?? 说法(本轮.文), '--说', 说])
    态.零活 = true
    void 存态($)
  }
}
const 卡完 = ($: EngineInterface) => {
  if (态.亮了 && 态.任务) 板($, ['开工', 态.任务, '--说', 说法(本轮.文)])
  else if (!态.亮了 && 态.零活) 板($, ['开工', 零活键(), '--题', 态.首句 ?? '', '--说', 说法(本轮.文)])
}

const 存态 = ($: EngineInterface) => (环境 ? $.store.set(`灯态:${环境.会}`, 态) : Promise.resolve())

/** 在不在工作区里（冷归档不算） */
const 在工作区 = (路: string) => {
  if (!环境 || !工作区) return false
  return 路.startsWith(工作区) && !跳过段.has(路.slice(工作区.length).split('/')[0])
}

/** 文件在哪个任务里：从它所在目录往上找第一个有 TODO.md 的目录（只在工作区里找，冷归档不算） */
/** 这些目录里的 TODO.md 是旧副本，不当任务（和 板.py 的 跳过目录 一样；6.40 加了历史资料：榜单「历史资料/…/三件套整理前」里有一份备份） */
const 跳过段 = new Set(['冷归档', '归档', 'node_modules', '资料', '__pycache__', '备份', '历史资料'])
const 任务目录 = async ($: EngineInterface, 路: string): Promise<string | null> => {
  if (!环境 || !在工作区(路)) return null
  const 根 = 工作区
  let d = 路.slice(0, 路.lastIndexOf('/'))
  while (d.length >= 根.length) {
    const 旧副本 = d.slice(根.length).split('/').some(x => 跳过段.has(x) || x.endsWith('.nosync'))
    if (!旧副本 && (await $.fs.exists(d + '/TODO.md'))) return d.slice(根.length)
    d = d.slice(0, d.lastIndexOf('/'))
  }
  return null
}

/** 规整成绝对路径：去引号、~ 换成家目录、相对的接在 基 后面，去掉 . 和 ..；相对路径又不知道 基 就是 null */
const 绝对 = (p: string, 家: string, 基: string | null): string | null => {
  p = p.replace(/^['"]|['"]$/g, '').replace(/^~(?=\/|$)/, 家)
  if (!p.startsWith('/')) {
    if (!基) return null
    p = 基 + '/' + p
  }
  const 段: string[] = []
  for (const x of p.split('/')) {
    if (x === '..') 段.pop()
    else if (x && x !== '.') 段.push(x)
  }
  return '/' + 段.join('/')
}

/** 终端命令里出现的工作区路径：绝对路径、~ 开头的，和相对路径（11-03 加，3.9）。
 *  相对路径按这条命令里第一个 cd 进的目录算；没写 cd 就按 起（上一条命令留下的工作目录，会话开始时是会话的 cwd）算——
 *  Bash 的工作目录会留到下一条，11-04 卷二会话 cd 进任务目录以后直接写 TODO.md，以前认不出、没亮（7.13）。
 *  按 起 算的时候不看 heredoc 正文（多半是代码，s.replace、os.path 这种会被当成文件）。停 = 命令跑完停在哪（最后一个 cd）。 */
export const 命令里的路 = (cmd: string, 家: string, 起: string | null = null): { 路们: string[]; 停: string | null } => {
  const 根 = 工作区 || '/没有工作区/'   // 会话开始前还没定位：什么都不算在工作区里
  const 规 = (p: string) => p.replace(/^['"]|['"]$/g, '').replace(/^~\//, 家 + '/').replace(/\/+$/, '')
  const 在区 = (p: string | null): p is string => !!p && (p + '/').startsWith(根)
  const cds = [...cmd.matchAll(/(?:^|&&|\|\||;|\n)\s*cd(?:\s+("[^"]+"|'[^']+'|[^\s;&|]+))?(?![^\s;&|])/g)]
  let 停 = 起
  let 基: string | null = cds.length ? null : 起
  cds.forEach((m, i) => {
    const 到 = m[1] === undefined ? 家 : m[1] === '-' ? null : 绝对(m[1], 家, 停)   // 光写 cd 是回家目录；cd - 不知道去了哪
    if (i === 0) 基 = 到
    停 = 到
  })
  if (!在区(基)) 基 = null
  const 路们: string[] = []
  const 无正文 = cmd.replace(/<<-?\s*(['"]?)(\w+)\1[^\n]*\n[\s\S]*?\n\s*\2[ \t]*(?=\n|$)/g, '')
  for (const m of cmd.matchAll(/"[^"\n]*"|'[^'\n]*'|[^\s"'|&;<>()=]+/g)) {
    const p = 规(m[0])
    if ((p + '/').startsWith(根)) 路们.push(p)
    else if (基 && cds.length && /^[^/~\-$][^\s]*\.[A-Za-z0-9]{1,6}$/.test(p)) 路们.push(基 + '/' + p)
  }
  if (基 && !cds.length)
    for (const m of 无正文.matchAll(/"[^"\n]*"|'[^'\n]*'|[^\s"'|&;<>()=]+/g)) {
      const p = 规(m[0])
      if (/^[^/~\-$][^\s]*\.[A-Za-z0-9]{1,6}$/.test(p)) 路们.push(绝对(p, 家, 基)!)
    }
  if (基 && cds.length) 路们.push(基 + '/.')   // cd 进去的那个目录本身
  // 看板自己的命令（板.py 列 / 读 / 对标准……）不算动了「无限表格」这个任务
  return { 路们: 路们.map(p => 绝对(p, 家, null) ?? p).filter(p => p !== 板目录 + '/工具/板.py'), 停 }   // 化简 . 和 ..（6.40）
}

const 正文式 = /<<-?\s*(['"]?)(\w+)\1[^\n]*\n([\s\S]*?)\n\s*\2[ \t]*(?=\n|$)/g   // heredoc（第 3 组是正文）
/** cp、rsync、ditto、scp：除了最后一个路径（复制到哪）都只是读，不算在那个任务里动笔（卷四 6.78，11-06 我把 MV 存档 rsync 到 /tmp 当测试副本，
 *  插件在 MV 上标了「跨区施工（从 无限表格 过来）」）。按段走，跟着段里的 cd 换相对路径的起点；heredoc 正文不看。
 *  返回 源（来源）、目标（复制到哪）、余（拿掉复制那几段的命令，用来判断别的部分在不在写） */
export const 复制们 = (cmd: string, 家: string, 起: string | null): { 源: Set<string>; 目标: string[]; 余: string } => {
  const 源 = new Set<string>(), 目标: string[] = []
  let 基 = 起, 余 = cmd
  for (const 段 of cmd.replace(正文式, '').split(/&&|\|\||;|\||\n/)) {
    const 词 = [...段.matchAll(/"[^"\n]*"|'[^'\n]*'|[^\s"']+/g)].map(m => m[0])
    let i = 0
    while (i < 词.length && /^\w+=/.test(词[i])) i++   // 前面的 FOO=bar
    if (词[i] === 'cd') { 基 = 词[i + 1] === undefined ? 家 : 绝对(词[i + 1], 家, 基); continue }
    if (!/^(?:\S*\/)?(cp|rsync|ditto|scp)$/.test(词[i] ?? '')) continue
    const 参 = 词.slice(i + 1).filter(w => !w.startsWith('-')).map(w => 绝对(w, 家, 基))
    参.slice(0, -1).forEach(q => q && 源.add(q))
    const 到 = 参[参.length - 1]
    if (到) 目标.push(到)
    余 = 余.replace(段.trim(), ' ')
  }
  return { 源, 目标, 余 }
}
const 写命令 = /(^|[\s;&|(])(cp|mv|rm|rsync|mkdir|touch|ln|tee|chmod|ditto|sed\s+-i|perl\s+-\w*i|swift|swiftc|ffmpeg|sips|osascript)(\s|$)/
const 重定向 = /(^|[^0-9&<>=-])>>?(?!\s*\/dev\/null)\s*['"]?[~/.\w]/   // 重定向写文件（2>&1、>/dev/null、=>、-> 不算）
/** 内联代码（heredoc 正文、python -c、node -e）里有没有写文件、跑子进程 */
const 码里写 = (码: string) =>
  写命令.test(码) || 重定向.test(码) ||
  /open\([^)]*?,\s*(?:mode\s*=\s*)?['"][rbt+]*[wxa]|\.write\(|write_text|write_bytes|json\.dump\(|shutil\.|os\.(?:replace|rename|remove|unlink|makedirs|mkdir|rmdir|utime|system|chmod)\b|\.unlink\(|\.mkdir\(|\.touch\(|subprocess|copyfile|writeFile|appendFile|renameSync|unlinkSync|mkdirSync|rmSync|copyFile|execSync|spawn|child_process/.test(码)

/** 终端命令像不像在写东西：重定向、复制挪删、原地改、跑脚本（脚本多半在改文件）。
 *  11-05（卷四 6.32，用户：「我只是让你查一下施工区，为啥任务就变成了MV了」）：python、node、shell 后面跟的是内联代码（heredoc、-c、-e），
 *  要代码里真有写文件才算，只读的查数脚本不算动笔；看板的只读命令（板.py 列、段、读、对标准、对账、等）也不算。跑脚本文件看不到里面，照旧当在写。 */
export const 像在写 = (cmd: string) => {
  const 去看板 = cmd.replace(/(?:\S*\/)?python3?(?:\s+-\w+)*\s+['"]?[^\s'"]*板\.py['"]?\s+(?:列|段|读|对标准|对账|等)(?=\s|$)/g, ' ')
  const 正文们 = [...去看板.matchAll(正文式)].map(m => m[3])
  const 外 = 去看板.replace(正文式, '')
  const 码们 = [...外.matchAll(/(?:^|\s)-[ce]\s+("(?:[^"\\]|\\.)*"|'[^']*')/g)].map(m => m[1])
  const 去码 = 码们.reduce((s, c) => s.replace(c, ' '), 外)
  if (写命令.test(去码) || 重定向.test(去码)) return true
  if (!/(^|[\s;&|(])(python3?|\/usr\/bin\/python3|node|bash|sh|zsh)(\s|$)/.test(去码)) return false
  const 内联 = [...正文们, ...码们]
  return !内联.length || 内联.some(码里写)
}

/** 认到一个工作区里的文件：读交接、TODO 先记下；动笔就亮灯（Edit/Write 和终端命令共用） */
const 看路 = async ($: EngineInterface, 路: string, 改: boolean) => {
  const 钥 = /\/(TODO|交接)\.md$/.test(路)
  if (!(改 || 钥)) return
  const t = await 任务目录($, 路)
  if (!t) {
    // 工作区里、但不在任何任务目录里的文件（比如某个脚本合集的 core/、ui/）：读过某个任务的交接、TODO，又在这里动笔，就亮那个任务（11-01 一个脚本合集挪进工作区后加）
    const 读过 = 态.任务 ?? 态.候选
    if (改 && !态.亮了 && 读过 && 在工作区(路)) {
      态 = { ...态, 任务: 读过, 亮了: true }
      await 存态($)
      板($, ['开工', 读过, '--说', 说法(本轮.文)])
    }
    return
  }
  if (!改) {   // 读交接、TODO：先记下，不亮灯
    if (!态.候选 && !态.任务) {
      态.候选 = t
      await 存态($)
    }
    return
  }
  if (!态.亮了) {   // 第一次动笔：亮灯（读过交接、TODO 的那个任务优先），这就是本区
    const 目标 = 态.任务 ?? 态.候选 ?? t
    收零活($)
    态 = { ...态, 任务: 目标, 亮了: true }
    await 存态($)
    板($, ['开工', 目标, '--说', 说法(本轮.文)])
  }
  // 在别的任务里动笔：不换本区，那边标「跨区施工」，这一轮结束关掉（11-04 6.9）。本区不知道（按短名开的工）就不标；本区的上级任务算本区（6.10）
  if (!态.任务) return
  if (t === 态.任务 || 态.任务.startsWith(t + '/')) {
    本轮.本区写 = true
    return
  }
  本轮.次[t] = (本轮.次[t] ?? 0) + 1
  if (!本轮.跨区.includes(t)) {
    本轮.跨区.push(t)
    板($, ['开工', t, '--说', `跨区施工（从 ${态.任务.split('/').pop()} 过来）`])
  }
}

const 看动作 = async ($: EngineInterface, a: Record<string, unknown>) => {
  if (!环境) return
  const 名 = String(a.tool ?? '')
  if ((名 === 'Bash' || 名 === 'Agent' || 名 === 'Task') && a.run_in_background) 本轮.后台 = true
  if (名 === 'Bash') {
    const 命令 = String(a.command ?? '')
    const 复 = 复制们(命令, 环境.家, 目录在)   // 6.78：复制的来源只算读，只有复制到哪算写
    const { 路们, 停 } = 命令里的路(命令, 环境.家, 目录在)
    目录在 = 停 && 起点 && !(停 + '/').startsWith(起点 + '/') ? 起点 : 停
    const ms = 敲板(命令)
    if (ms.length) {
      for (const m of ms) {
        if (m[1] === '开工' || m[1] === '施工') {   // 它自己开了灯：以后每轮照样替它开关；这一轮又开了工，轮结束照状态词收（6.33）
          收零活($)
          态.亮了 = true
          本轮.完工 = false
          const 名0 = (m[2] ?? '').replace(/^['"]|['"]$/g, '').replace(/^~(?=\/)/, 环境.家)
          const 名 = 工作区 && 名0.startsWith(工作区) ? 名0.slice(工作区.length) : 名0   // 带引号、写全路径的都规整成看板认的写法（相对工作区）
          if (名.includes('/') && !名.startsWith('~') && !名.startsWith('/')) 态.任务 = 名
        } else if (m[1] === '完工' || m[1] === '收工') {   // 收工 = 完工（7.20）
          本轮.完工 = true
          态.亮了 = false
        }
      }
      await 存态($)
      return
    }
    // 11-03（3.9）：全用终端命令读改文件的会话以前认不出、看板上不亮。命令里出现工作区路径：像在写就算动笔，只读到交接、TODO 就先记下
    if (!路们.length) return
    const 写 = 像在写(复.余), 原来亮着 = 态.亮了
    for (const 路 of 路们) {
      const 这写 = (写 && !复.源.has(路)) || 复.目标.some(d => 路 === d || 路.startsWith(d + '/'))   // 6.78：cp、rsync 的来源不算动笔，复制到哪算
      if (这写 && 本轮.完工) break   // 这一轮它自己敲了完工，就别再亮
      if (这写 || /\/(TODO|交接)\.md$/.test(路)) await 看路($, 路, 这写)
      if (!原来亮着 && 态.亮了) break   // 这条命令刚把灯点亮：后面的路径不再换来换去
    }
    return
  }
  const 路 = a.file_path ?? a.notebook_path
  if (typeof 路 !== 'string') return
  const 改 = ['Edit', 'Write', 'MultiEdit', 'NotebookEdit'].includes(名)
  if (!(改 || 名 === 'Read')) return
  await 看路($, 路, 改)
}

/** 会话开始时定看板在哪、工作区是哪：看板位置.txt（装插件时写的）> ~/Documents/Qlimen-Tabula；工作区读看板的 设置.json，
 *  相对路径按看板目录算，没设就是看板自带的演示工作区——和 板.py 的读法一样。跳过目录也照设置加上 */
const 定位 = async ($: EngineInterface, 家: string) => {
  板目录 = 家 + 默认看板
  if (await $.fs.exists(家 + 位置文件)) {
    const 位 = 绝对((await $.fs.read(家 + 位置文件)).trim(), 家, null)
    if (位) 板目录 = 位
  }
  工作区 = 板目录 + '/示例/演示工作区/'
  if (!(await $.fs.exists(板目录 + '/设置.json'))) return
  try {
    const 设 = JSON.parse(await $.fs.read(板目录 + '/设置.json')) as { 工作区?: unknown; 跳过目录?: unknown }
    const 区 = typeof 设.工作区 === 'string' && 设.工作区.trim() ? 绝对(设.工作区.trim(), 家, 板目录) : null
    if (区) 工作区 = 区 + '/'
    if (Array.isArray(设.跳过目录)) for (const x of 设.跳过目录) if (typeof x === 'string') 跳过段.add(x)
  } catch {
    // 设置.json 写坏了：照默认（板.py 会在终端里提示）
  }
}

export const register: Register = on => {
  on('session.start', async ($, e, next) => {
    const r = await next(e)
    目录在 = 起点 = typeof e.cwd === 'string' && e.cwd.startsWith('/') ? e.cwd.replace(/\/+$/, '') : null
    首见 = null
    忙 = false
    本轮 = 新轮()
    const 家 = await $.env.get('HOME')
    if (!家) return r
    await 定位($, 家)
    const 窗 = 板目录 + '/小窗.nosync/无限表格小窗.app'
    if (await $.fs.exists(窗)) void 拉起小窗($, 窗).catch(() => undefined)
    const 会 = await $.env.get('CLAUDE_CODE_HOST_SESSION_ID')
    if (会) {
      环境 = { 家, 会 }
      态 = ((await $.store.get(`灯态:${会}`)) as 灯态 | undefined) ?? { 亮了: false }
      const 箱 = `${板目录}/数据.nosync/信箱/${会.replace(/[^A-Za-z0-9_.-]/g, '_')}.jsonl`
      const 键 = `已发:${会}`
      $.clock.every(每, () => {
        if (忙) return
        忙 = true
        void 看信箱($, 箱, 键)
          .catch(() => undefined)
          .finally(() => {
            忙 = false
          })
      })
    }
    return r
  })

  on('tool.call', async ($, e, next) => {
    const a = e as unknown as Record<string, unknown>
    const 卡 = 卡片说(a)   // 问答卡片、计划审批：弹着就是在等你回话，先切等你（6.37）
    if (卡) 等卡($, 卡)
    const r = await next(e)
    if (卡 || 本轮.等批) {   // 卡片选完、权限批了或拒了，这个工具往下走完：切回施工
      本轮.等批 = false
      卡完($)
    }
    await 看动作($, a).catch(() => undefined)
    return r
  })

  on('turn.start', async ($, e, next) => {
    const r = await next(e)
    if (e.agentId === undefined) {   // 只看主线程的轮
      本轮 = 新轮(e.text ?? '')
      if (!态.首句 && 本轮.文.trim() && !本轮.文.startsWith('<')) {
        态.首句 = 说法(本轮.文)
        void 存态($)
      }
      if (态.收工没看 && 本轮.文.trim() && !本轮.文.startsWith('<')) {   // 6.27：用户回话了 = 看过了；亮着的会被下面的开工换掉，灭了的撤掉「收工」
        态.收工没看 = false
        void 存态($)
        if (!态.亮了 && 态.任务) 板($, ['完工', 态.任务])
      }
      if (态.亮了) 板($, ['开工', ...(态.任务 ? [态.任务] : []), '--说', 说法(本轮.文)])
      else if (态.零活) 板($, ['开工', 零活键(), '--题', 态.首句 ?? '', '--说', 说法(本轮.文)])
    }
    return r
  })

  on('turn.complete', async ($, e, next) => {
    const r = await next(e)
    if (e.agentId !== undefined) return r
    let 挪了 = false
    if (态.亮了 && !本轮.完工 && 态.任务 && !本轮.本区写 && 本轮.跨区.length) {   // 一整轮只在别的任务动笔：本区挪过去（动笔最多的那个），原来的灭灯（6.10）
      const 新 = 本轮.跨区.reduce((a, b) => ((本轮.次[b] ?? 0) > (本轮.次[a] ?? 0) ? b : a))
      板($, ['完工', 态.任务])
      态.任务 = 新
      await 存态($)
      挪了 = true
    }
    for (const t of 本轮.跨区) if (t !== 态.任务) 板($, ['完工', t])   // 跨区施工：这一轮结束就关掉
    // 7.10：回复开头写了状态词（【施工】【等你】【收工】）就照词开关灯，不再猜；说的和看到的对不上，照看到的亮、记一笔「对不上」；没写词的照旧按规则
    const 词 = 状态词(e.answer ?? '')
    本轮.词 = 词 ?? ''
    const 后台 = 本轮.在飞 ?? (本轮.后台 ? '后台在跑' : '')   // Stop 先到就听它的（哪一轮起的都算），没到就看这一轮起没起
    const 疑 = (...x: string[]) => (x[0] ? ['--对不上', x[0]] : [])
    if (态.亮了 && !本轮.完工) {
      const 任务 = 态.任务 ? [态.任务] : []
      if (后台) 板($, ['开工', ...任务, '--说', 后台, '--租', String(后台租分), ...要你(词), ...疑(词 === '收工' ? '说收工，后台还在跑' : '')])
      else if (词 === '收工' || (!词 && 不用等你(本轮.文, e.answer ?? ''))) {   // 写了【收工】，或你说了收工、我在道别
        if (说收工(本轮.文)) 板($, ['完工', ...任务])   // 用户这一轮说了收工：看过了，直接灭灯（6.7）
        else {   // 6.27（用户 11-05：「我还没看的就不要撤走任务」）：挂「收工」，框留着、亮片停，用户点知道了或回话才撤
          板($, ['等你', ...任务, '--收工'])
          态.收工没看 = true
          await 存态($)
        }
      }
      else 板($, ['等你', ...任务, ...(挪了 ? ['--说', 说法(本轮.文)] : []), ...疑(词 === '施工' && 本轮.在飞 !== undefined ? '说施工，什么都没在跑' : '')])
      本轮.收了 = 后台 ? '后台' : '收'
    } else if (本轮.完工 && 态.任务 && !态.零活 && !说收工(本轮.文)) {   // 6.27：它自己敲了收工（完工），用户这一轮没说收工：照样挂「收工」等用户看
      板($, ['等你', 态.任务, '--收工'])
      态.收工没看 = true
      await 存态($)
    } else if (!态.亮了 && !本轮.完工 && 词) {   // 零活：没碰过任务目录的会话（查询、小任务），照状态词亮一行，进度条占位（用户 11-04 01:2x）
      const 题 = ['--题', 态.首句 ?? 说法(本轮.文)]
      if (后台) {
        板($, ['开工', 零活键(), ...题, '--说', 后台, '--租', String(后台租分), ...要你(词), ...疑(词 === '收工' ? '说收工，后台还在跑' : '')])
        态.零活 = true
      } else if (词 === '收工') 收零活($)
      else {
        板($, ['等你', 零活键(), ...题, '--说', 说法(本轮.文), ...疑(词 === '施工' && 本轮.在飞 !== undefined ? '说施工，什么都没在跑' : '')])
        态.零活 = true
      }
      await 存态($)
      本轮.收了 = 后台 ? '后台' : '收'
    }
    return r
  })

  // Stop：停下时还在跑的后台任务、定好的定时叫醒（哪一轮起的都算，6.11）。一轮结束先到、已经收工或灭灯了，就补成在干
  // 6.37：权限弹框（要你批准一条命令、一个工具）也是在等你：弹的时候切等你，批了或拒了、那个工具往下走完切回施工（上面 tool.call 里）
  on('classic.PermissionRequest', async ($, e, next) => {
    const r = await next(e)
    const 名 = String((e as unknown as Record<string, unknown>).tool_name ?? '')
    if (环境 && 名 !== 'AskUserQuestion' && 名 !== 'ExitPlanMode') {   // 卡片自己会发一次权限请求，卡片那边已经切过等你（6.40）
      本轮.等批 = true
      等卡($, '等你批准：' + String((e as unknown as Record<string, unknown>).tool_name ?? '工具'))
    }
    return r
  })

  on('classic.Stop', async ($, e, next) => {
    const r = await next(e)
    本轮.在飞 = e.background_tasks?.length ? '后台在跑' : e.session_crons?.length ? '等定时叫醒' : ''
    const 键们 = 态.亮了 ? (态.任务 ? [态.任务] : []) : 态.零活 || 本轮.词 ? [零活键()] : null
    if (键们 && 本轮.在飞 && 本轮.收了 === '收') {
      板($, ['开工', ...键们, ...(态.亮了 ? [] : ['--题', 态.首句 ?? '']), '--说', 本轮.在飞, '--租', String(后台租分), ...要你(本轮.词), ...(本轮.词 === '收工' ? ['--对不上', '说收工，后台还在跑'] : [])])
      if (!态.亮了) 态.零活 = true
      本轮.收了 = '后台'
    } else if (键们 && 本轮.在飞 === '' && 本轮.收了 === '收' && 本轮.词 === '施工' && (态.亮了 || 态.零活)) {
      板($, ['等你', ...键们, '--对不上', '说施工，什么都没在跑'])
      本轮.收了 = '疑'
    }
    return r
  })
}
