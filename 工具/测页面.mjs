// 无头 Chrome 测页面：[BAN_NATIVE=1] node 工具/测页面.mjs 网址 脚本.js [截图.png] [宽x高]（11-01 补测验收清单时写的；连测试服务 8771，别连正在用的 8770）
// 脚本.js 是一段 async 函数体（return 结果）；页面里能用 sh('命令') 让这边跑一条 shell 命令（返回输出），wait(毫秒)。
// 输出：结果 JSON + 页面报错（未捕获异常、console.error）。
import { spawn, execSync } from 'node:child_process';
import { readFileSync, writeFileSync, mkdtempSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';

const [url, scriptFile, shot, size = '1280x800'] = process.argv.slice(2);
const [W, H] = size.split('x').map(Number);
const port = 9400 + Math.floor(Math.random() * 400);
const dir = mkdtempSync(join(tmpdir(), 'ban-chrome-'));
const chrome = spawn('/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
  ['--headless=new', `--remote-debugging-port=${port}`, `--user-data-dir=${dir}`, '--no-first-run', '--no-default-browser-check',
   `--window-size=${W},${H}`, 'about:blank'], { stdio: 'ignore' });
const wait = ms => new Promise(r => setTimeout(r, ms));
let out = { 错: [] };
try {
  let tgt;
  for (let k = 0; k < 50 && !tgt; k++) {
    await wait(200);
    try { tgt = await (await fetch(`http://127.0.0.1:${port}/json/new?about:blank`, { method: 'PUT' })).json(); } catch (e) {}
  }
  const ws = new WebSocket(tgt.webSocketDebuggerUrl);
  await new Promise(r => ws.onopen = r);
  let id = 0; const pend = {}; const ev = [];
  ws.onmessage = m => {
    const d = JSON.parse(m.data);
    if (d.id && pend[d.id]) { pend[d.id](d); delete pend[d.id]; return; }
    if (d.method === 'Runtime.exceptionThrown') out.错.push('异常：' + (d.params.exceptionDetails.exception?.description || d.params.exceptionDetails.text).split('\n')[0]);
    if (d.method === 'Runtime.consoleAPICalled' && d.params.type === 'error') out.错.push('console.error：' + d.params.args.map(a => a.value ?? a.description).join(' '));
    if (d.method === 'Runtime.bindingCalled' && d.params.name === '__sh') {
      let r; try { r = execSync(d.params.payload, { encoding: 'utf8', shell: '/bin/zsh', timeout: 60000 }); } catch (e) { r = '出错：' + (e.stdout || '') + (e.stderr || ''); }
      send('Runtime.evaluate', { expression: `window.__shDone(${JSON.stringify(r)})` });
    }
    ev.push(d.method);
  };
  const send = (method, params = {}) => new Promise(r => { const i = ++id; pend[i] = r; ws.send(JSON.stringify({ id: i, method, params })); });
  await send('Runtime.enable'); await send('Page.enable');
  await send('Runtime.addBinding', { name: '__sh' });
  await send('Emulation.setDeviceMetricsOverride', { width: W, height: H, deviceScaleFactor: 1, mobile: false });
  await send('Emulation.setFocusEmulationEnabled', { enabled: true });
  // 环境变量 BAN_NATIVE=1：装成原生小窗（页面一开始就有 window.BAN_NATIVE，走小档、底行带「收起」）
  if (process.env.BAN_NATIVE) await send('Page.addScriptToEvaluateOnNewDocument', { source: 'window.BAN_NATIVE=true;' });
  await send('Page.navigate', { url });
  for (let k = 0; k < 100 && !ev.includes('Page.loadEventFired'); k++) await wait(100);
  await wait(1500);
  const body = readFileSync(scriptFile, 'utf8');
  const expr = `(async()=>{const wait=ms=>new Promise(r=>setTimeout(r,ms));const sh=c=>new Promise(r=>{window.__shDone=r;__sh(c);});${body}})()`;
  const r = await send('Runtime.evaluate', { expression: expr, awaitPromise: true, returnByValue: true, timeout: 120000 });
  const res = r.result || {};   // 先看有没有出错：出错时 value 是错误对象按值转成的 {}，会被当成正常结果
  out.结果 = res.exceptionDetails ? '脚本出错：' + (res.exceptionDetails.exception?.description || res.exceptionDetails.text) : res.result?.value;
  if (shot) {
    const s = await send('Page.captureScreenshot', { format: 'png' });
    writeFileSync(shot, Buffer.from(s.result.data, 'base64'));
    out.截图 = shot;
  }
  ws.close();
} catch (e) {
  out.错.push('测试脚本自己出错：' + e.message);
} finally {
  chrome.kill('SIGTERM');
  await wait(300);
  try { rmSync(dir, { recursive: true, force: true }); } catch (e) {}
}
console.log(JSON.stringify(out, null, 1));
