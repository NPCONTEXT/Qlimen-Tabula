// 卷二 7.7 手动调格子：在测试端口的页面里用合成的指针事件测（测页面.mjs 的脚本体）。
// 跑法：工具/跑页面测试.py 会搭好环境；手动跑：测试服务开在 8771（BAN_DATA 指到数据副本、布局.json 先清空），BAN_NATIVE=1 node 工具/测页面.mjs http://127.0.0.1:8771/ 工具/测拖.js "" 680x1700
const 结果 = [], 记 = (名, 过, 细 = '') => 结果.push((过 ? '✅ ' : '❌ ') + 名 + (过 ? '' : '  ' + 细));
去层(2, 1); await wait(1500);
const 可 = () => DATA.任务.filter(可见).slice().sort((a, b) => (b.灯.length ? 1 : 0) - (a.灯.length ? 1 : 0));
// ①（作者本机还拿改前页面里原来的排法逐块比过；改前那份页面没放进仓库，开源版不跑这一条）
const 块 = k => cv.querySelector('.r[data-t="' + CSS.escape(k) + '"]');
const 中 = el => { const r = el.getBoundingClientRect(); return [r.left + r.width / 2, r.top + r.height / 2]; };
const 发 = (目, 型, x, y) => 目.dispatchEvent(new PointerEvent(型, { bubbles: true, cancelable: true, clientX: x, clientY: y, pointerId: 1, button: 0, isPrimary: true }));
const 点 = (目, x, y) => 目.dispatchEvent(new MouseEvent('click', { bubbles: true, cancelable: true, clientX: x, clientY: y, button: 0 }));
async function 拖(起el, 到x, 到y, 点它 = true) { const [x, y] = 起el === window ? [0, 0] : 中(起el); 发(起el, 'pointerdown', x, y);
  for (let i = 1; i <= 6; i++) 发(window, 'pointermove', x + (到x - x) * i / 6, y + (到y - y) * i / 6);
  发(window, 'pointerup', 到x, 到y); if (点它) 点(起el, 到x, 到y); await wait(900); }
const 不亮 = 可().filter(t => !t.灯.length && !t.施工区);
const [A, B, C, D, E] = 不亮.map(t => t.键);
const L0 = 排过[0].pos, a0 = { ...L0[A] }, b0 = { ...L0[B] };
// ② 拖 A 到 B 上：换位，所有看得见的都钉住，那一下不算单击
await 拖(块(A), ...中(块(B)));
let 布局 = DATA.布局;
记('拖到别的块上：两块换位', 布局[A] && 布局[A].x == b0.gx && 布局[A].y == b0.gy && 布局[B] && 布局[B].x == a0.gx && 布局[B].y == a0.gy, JSON.stringify([布局[A], 布局[B], a0.gx, a0.gy, b0.gx, b0.gy]));
记('第一次拖就把看得见的都钉住', Object.keys(排过[0].pos).every(k => 布局[k] && 布局[k].x != null), Object.keys(布局).length + '/' + Object.keys(排过[0].pos).length);
记('拖过的那一下不算单击（没展开）', !MAIN.open.has(A));
记('块真挪过去了', 排过[0].pos[A].gx == b0.gx && 排过[0].pos[A].gy == b0.gy);
// ③ 小于半格的移动 = 单击，照旧展开
{ const el = 块(C), [x, y] = 中(el); 发(el, 'pointerdown', x, y); 发(window, 'pointermove', x + 6, y + 4); 发(window, 'pointerup', x + 6, y + 4); 点(el, x + 6, y + 4); await wait(300);
  记('挪不到半格就是单击：照旧展开', MAIN.open.has(C)); MAIN.open.delete(C); renderOverview(cv, MAIN); await wait(600); }
// ④ 右下角拉高两行：常驻展开
{ const p = 排过[0].pos[C], gp = 块(C).querySelector('[data-grip]'), 角0 = 块(C).getBoundingClientRect(), r = { left: 角0.right - 12, top: 角0.bottom - 12 };   // 把手平时藏着（鼠标停上去才出来），按块的右下角取坐标
  发(gp, 'pointerdown', r.left + 6, r.top + 6); for (let i = 1; i <= 4; i++) 发(window, 'pointermove', r.left + 6, r.top + 6 + 16 * i); 发(window, 'pointerup', r.left + 6, r.top + 70); 点(gp, r.left + 6, r.top + 70); await wait(900);
  const q = 排过[0].pos[C];
  { const sb = 块(C).querySelector('.steps').lastElementChild.getBoundingClientRect(), bb = 块(C).getBoundingClientRect(); 记('拉高的块最后一行没被切成半截', sb.bottom <= bb.bottom + 1, sb.bottom + ' > ' + bb.bottom); }
  记('拉高两行：存了 h、块变高、显示步骤（常驻展开）', DATA.布局[C].h == p.gh + 2 && q.gh == p.gh + 2 && !!块(C).querySelector('.steps') && !MAIN.open.has(C), JSON.stringify([DATA.布局[C], p.gh, q.gh]));
  // ⑤ 拉到 1 格：折起来；点一下复原
  const gp2 = 块(C).querySelector('[data-grip]'), 角 = 块(C).getBoundingClientRect(), r2 = { left: 角.right - 12, top: 角.bottom - 12 };
  发(gp2, 'pointerdown', r2.left + 6, r2.top + 6); for (let i = 1; i <= 4; i++) 发(window, 'pointermove', r2.left + 6 - (r2.left - 角.left) * i / 4, r2.top + 6 - (r2.top - 角.top) * i / 4); 发(window, 'pointerup', 角.left + 8, 角.top + 8); await wait(900);
  const f = 块(C);
  记('拉到 1 格：折起来（1 格宽、只剩进度条）', DATA.布局[C].折 && f.classList.contains('fold') && Math.abs(f.offsetWidth - (CW - 2 * I)) < 1 && !!f.querySelector('.fd'), JSON.stringify(DATA.布局[C]) + ' 宽 ' + f.offsetWidth);
  const [fx, fy] = 中(f); 点(f, fx, fy); await wait(900);
  记('点折起来的小块：放回原来大小', !DATA.布局[C].折 && !DATA.布局[C].h && !块(C).classList.contains('fold') && 排过[0].pos[C].gw == 块格0(DATA.任务.find(t => t.键 == C)), JSON.stringify(DATA.布局[C])); }
// ⑥ 拖进底行：收起；底行的小方块拖到上面：放回来
{ const sl = cv.querySelector('.sleep'), r = sl.getBoundingClientRect();
  await 拖(块(D), r.left + 200, r.top + 6);
  const dot = cv.querySelector('.sleep [data-k="' + CSS.escape(D) + '"]');
  记('拖进底行：收起，块不见了，底行多一个「收起」的方块', DATA.布局[D].档 && !块(D) && dot && dot.classList.contains('ar') && sl.textContent.includes('收起 1'), JSON.stringify(DATA.布局[D]) + ' ' + sl.textContent.slice(-20));
  const 空 = 排过[0].sleepY, cr = cv.getBoundingClientRect();
  await 拖(dot, cr.left + (G + 5 * CW + 40) * (cam.s || 1), cr.top + (空 - U * 1) * (cam.s || 1) + 10, false);
  记('底行的方块拖到上面：放回总览', !DATA.布局[D].档 && DATA.布局[D].显 && !!块(D), JSON.stringify(DATA.布局[D])); }
// ⑦ 取消一块的位置（像新任务进来）：别的块不动
{ const 前 = JSON.parse(JSON.stringify(排过[0].pos)); await 存布局({ [E]: null }); await wait(300);
  const 动了 = Object.keys(前).filter(k => k != E && (前[k].gx != 排过[0].pos[k].gx || 前[k].gy != 排过[0].pos[k].gy));
  记('有块没存位置（像新任务）：别的块不洗牌', !动了.length && !!排过[0].pos[E], JSON.stringify(动了.slice(0, 3))); }
// ⑧ 服务端存的和页面一致
await wait(1200);
const 服 = (await (await fetch('/api/看板', { cache: 'no-store' })).json()).布局;
const 页 = { ...DATA.布局 }; delete 页[E];
记('服务端存的和页面一样', JSON.stringify(Object.keys(页).sort().map(k => [k, 页[k]])) == JSON.stringify(Object.keys(服).sort().map(k => [k, 服[k]])), Object.keys(服).length + ' vs ' + Object.keys(页).length);
return 结果.join('\n') + '\n' + (结果.every(x => x.startsWith('✅')) ? '全过' : '有没过的');
