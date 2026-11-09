// 卷四 6.71–6.73 底下一行（状态摘要）：第 3 层放第 1 层的名牌条，各层和名牌同一套字。测页面.mjs 的脚本体。
// 跑法：测试服务开在 8771（BAN_DATA、DYT_DIR 指到副本，不设 BAN_CODEX，数据就不动），
//   BAN_NATIVE=1 node 工具/测页面.mjs http://127.0.0.1:8771/ 工具/测底行.js "" 1312x764
// 脚本自己往页面的 DATA 里塞两块测试名牌（一块「收工」、一盏同任务的「跨区」），不靠数据里碰巧有。
// 改坏验法：名牌条() 返回空串，① 要红；状态话() 把那句话挪到状态前面，③⑥ 要红；合计改回「处在干」，⑤ 要红。
const 过=[],败=[];const 验=(名,ok,细)=>(ok?过:败).push(名+(ok?'':'：'+JSON.stringify(细)));
window.webkit={messageHandlers:{ban:{postMessage:()=>{}}}};
for(let k=0;k<40&&!(window.DATA&&DATA.任务);k++)await wait(250);
const 字们=['施工','等你','收工','跨区','待续'];
// 塞测试名牌：找一个有灯的任务，加一盏别的会话的「收工」和一盏「跨区施工」（各一块名牌）
const 塞=()=>{const t=DATA.任务.find(x=>x.灯.length&&!x.施工区)||DATA.任务.find(x=>!x.施工区&&!x.占位);
  if(!t.灯.some(l=>l.会话=='local_测-收工'))t.灯.push({谁:'Claude',说:'测试：做完了',格子:[],开始:Date.now()/1000-120,态:'等',会话:'local_测-收工',接入:'claude',要你:false,收工:true,链:'claude://code/continue?session=local_测-收工'});
  if(!t.灯.some(l=>l.会话=='local_测-跨区'))t.灯.push({谁:'Claude',说:'跨区施工（从 测试 过来）',格子:[],开始:Date.now()/1000-60,态:'干',会话:'local_测-跨区',接入:'claude',要你:false,收工:false,链:'claude://code/continue?session=local_测-跨区'});
  return t;};
const t0=塞();
const 名=k=>(DATA.任务.find(t=>t.键==k)||{}).名||'';

// 第 3 层
去层(3,true);await wait(1500);塞();setLine();
const 组=[...document.querySelectorAll('#line .ltg')],一=一层们();
验('① 第 3 层底下一行：一个任务一组，组的顺序 = 第 1 层的顺序',组.length==一.length&&组.every((g,i)=>g.dataset.t==一[i].键),[组.map(g=>g.dataset.t),一.map(t=>t.键)]);
const 逐块=组.length==一.length&&一.every((t,i)=>{const 要=名牌们(t).filter(x=>!x.hit),有=[...组[i].querySelectorAll('.lt')];return 有.length==要.length&&有.every((a,j)=>a.textContent==要[j].字&&a.style.getPropertyValue('--c').includes(要[j].c));});
验('② 每组的名牌和第 1 层逐块一样（字、颜色）',逐块,一.map(t=>名牌们(t).map(x=>x.字).join('/')));
const 塞的=组.find(g=>g.dataset.t==t0.键),塞块=塞的?[...塞的.querySelectorAll('.lt')].map(a=>a.textContent):[];
验('② 塞的收工、跨区各出一块，收工不当等你',塞块.includes('收工')&&塞块.includes('跨区'),塞块);
const 链对=组.length==一.length&&一.every((t,i)=>{const 要=名牌们(t).filter(x=>!x.hit);return [...组[i].querySelectorAll('.lt')].every((a,j)=>{const 到=要[j].链||t.会话链接||'';return 到?a.tagName=='A'&&a.getAttribute('href')==到:a.tagName=='SPAN';});});
验('② 有会话的名牌是链接、点进那个会话',链对,[...document.querySelectorAll('#line .lt')].map(a=>a.getAttribute('href')));
const 块=[...document.querySelectorAll('#line .lt')].find(a=>a.textContent=='收工'&&a.dataset.t==t0.键);
块&&块.dispatchEvent(new MouseEvent('mouseover',{bubbles:true}));await wait(50);
const 写=(document.querySelector('#line .ltx')||{}).textContent||'';
验('③ 停在收工那块上：写「任务名 · Claude 收工 · 几分钟前」，说的是这块名牌那个会话',/^.+ · Claude 收工 · \d+ 分钟前/.test(写)&&写.startsWith(t0.名+' · Claude 收工 · '),写);
const 话收=t0.现在&&t0.现在.length?t0.现在[0]:'测试：做完了';
验('③ 状态写在那句话前面',写.indexOf(' · Claude 收工')>0&&写.indexOf(' · Claude 收工')<写.indexOf(话收),[写,话收]);
const 跨块=[...document.querySelectorAll('#line .lt')].find(a=>a.textContent=='跨区'&&a.dataset.t==t0.键);
跨块&&跨块.dispatchEvent(new MouseEvent('mouseover',{bubbles:true}));await wait(50);
const 写跨=(document.querySelector('#line .ltx')||{}).textContent||'';
验('③ 停在跨区那块上：写跨区那个会话（从哪来）',写跨.startsWith(t0.名+' · Claude 跨区 · ')&&写跨.includes('从 测试 过来'),写跨);
line.dispatchEvent(new MouseEvent('mouseleave'));await wait(50);
验('④ 移开：右边那截清空',((document.querySelector('#line .ltx')||{}).textContent||'')=='',document.querySelector('#line .ltx')&&document.querySelector('#line .ltx').textContent);
验('④ 第 3 层不再写「处在干」那套合计',!/处在干|处等你/.test(line.textContent),line.textContent);

// 第 1、2 层
for(const n of [2,1]){去层(n,true);await wait(900);塞();setLine();
  验('⑤ 第 '+n+' 层不出名牌条，合计用名牌那套字、收工单算',!document.querySelector('#line .lts')&&!/处在干|处等你/.test(line.textContent)&&/收工 \d/.test(line.textContent)&&/跨区 \d/.test(line.textContent),line.textContent);}
// 第 1 层停在某行上
const r=document.querySelector('.r.row1[data-t="'+CSS.escape(t0.键)+'"]');
悬停=null;r&&r.dispatchEvent(new MouseEvent('mouseover',{bubbles:true}));await wait(50);
const 行写=line.textContent,首=名牌们(t0).find(x=>!x.hit)||{};
验('⑥ 第 1 层停在行上：开头就是「任务名 · 谁 状态」，字和第一块名牌一样',!!r&&行写.startsWith(t0.名+' · '+首.谁+' '+首.字),[行写,首.谁,首.字]);
// 名牌层
去层(0,true);await wait(900);
const 字显=[...line.querySelectorAll(':scope>span')].filter(s=>getComputedStyle(s).display!='none').length;
验('⑦ 名牌层底下一行照旧只放圆点',字显==0&&!line.querySelector('.lts'),字显);
去层(1,true);
return {过:过.length,败,全过:!败.length,过的:过};
