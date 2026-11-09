// 卷四 6.43 名牌层、6.47 名牌圆角：测页面.mjs 的脚本体（11-06 写）。
// 跑法：测试服务开在 8771（BAN_DATA 指到数据副本，第 1 层至少要有一行在干、等你或待续），
//   BAN_NATIVE=1 node 工具/测页面.mjs http://127.0.0.1:8771/ 工具/测名牌层.js "" 416x400
// 改坏验法：把页面里第 0 层的宽（w:(LV==0?T:…)）、名牌提示那一句、.ctag 的 border-radius 改回原样（0 0 var(--R2) var(--R2)）再跑，③ ⑤ ⑥ ⑧ 要红；
// 6.77：画名牌那句的 LV==0?一块(t): 去掉、T 改回按名牌数、一块() 里跨区不改写施工、名牌提示不传 一块(t)[0]，⑪ 要红。
const 收=[];window.webkit={messageHandlers:{ban:{postMessage:m=>收.push(m)}}};   // 接住页面发给小窗的话
const 过=[],败=[];const 验=(名,ok,细)=>(ok?过:败).push(名+(ok?'':'：'+JSON.stringify(细)));
const 末窗=()=>{for(let i=收.length-1;i>=0;i--)if(收[i].窗)return 收[i].窗;return null;};
const 角=el=>{const c=getComputedStyle(el);return [c.borderTopLeftRadius,c.borderTopRightRadius,c.borderBottomRightRadius,c.borderBottomLeftRadius].join(' ');};
const 行们=()=>[...document.querySelectorAll('.r.row1')];
const 框=k=>document.querySelector('.claim.ovc[data-cl="'+CSS.escape(k)+'"]');
const 牌=k=>[...框(k).querySelectorAll('.ctag')];
const 任务=k=>DATA.任务.find(x=>x.键==k);

要窗.k='';去层(1,true);await wait(900);   // 页面一开就发过第 1 层的大小（那时还没接住）：清掉记的那句，逼它再发一次
const 一=末窗(),rows=行们().length,T=排过[1].T;
验('有第 1 层的行',rows>0,rows);
验('① 第 1 层大小',!!一&&一.层==1&&一.宽==32+(5+T)*64&&一.高==16+rows*32+8+28,一);
const 原题={},原链={};行们().forEach(r=>{const k=r.dataset.t;原题[k]=牌(k).map(a=>a.title);原链[k]=牌(k).map(a=>a.getAttribute('href')||'');});
验('⑥ 第 1 层名牌四角圆',行们().every(r=>牌(r.dataset.t).every(a=>角(a)=='6px 6px 6px 6px')),行们().map(r=>角(牌(r.dataset.t)[0])));

去层(0,true);await wait(900);
const 零=末窗();
验('② 名牌层发给小窗的是第 0 层',!!零&&零.层==0,零);
验('③ 名牌层大小 = 半格 + 1 格名牌 + 半格（6.77 起一个任务只挂一块）、半格 + 行数 + 半格 + 底下一行（6.67 起只放圆点）',!!零&&零.宽==32+64&&零.高==32+rows*32+28,零);
验('③ 每行框宽 1 格（6.77：第 1 层挂几块，名牌层都只一块）',行们().every(r=>Math.round(框(r.dataset.t).getBoundingClientRect().width)==64-6),行们().map(r=>框(r.dataset.t).getBoundingClientRect().width));
验('④ 名牌层底下一行只放圆点（卷四 6.67，用户：最小一层也恢复底部的圆点）',getComputedStyle(line).display!='none'&&[...line.children].every(e=>e.tagName=='I'||getComputedStyle(e).display=='none'),[...line.children].map(e=>e.tagName+':'+getComputedStyle(e).display));
验('④ 标题、进度条藏了',行们().every(r=>getComputedStyle(r.querySelector('.tn2')).opacity=='0'&&getComputedStyle(r.querySelector('.br2')).opacity=='0'),'');
const 有提示=()=>行们().every(r=>{const t=任务(r.dataset.t);return 牌(r.dataset.t).every(a=>a.title.startsWith(t.名+' · ')&&(a.tagName!='A'||a.title.endsWith('点一下打开那个会话')));});
验('⑤ 名牌悬停写任务名在干什么',有提示(),行们().map(r=>牌(r.dataset.t).map(a=>a.title)));
验('⑤ 每行只一块，链接是第 1 层那几块里的一个、或这个任务自己的会话（6.77）',行们().every(r=>{const k=r.dataset.t,ps=牌(k);if(ps.length!=1)return false;const h=ps[0].getAttribute('href')||'';return 原链[k].includes(h)||h==(任务(k).会话链接||'');}),行们().map(r=>[r.dataset.t,牌(r.dataset.t).map(a=>a.getAttribute('href')),原链[r.dataset.t]]));
验('⑥ 名牌层名牌四角圆',行们().every(r=>牌(r.dataset.t).every(a=>角(a)=='6px 6px 6px 6px')),'');
await wait(3500);   // 等一轮数据刷新，提示还在
验('⑤ 刷新后提示还在',有提示(),'');

去层(1,true);await wait(900);
const 回=末窗();
验('⑦ 回第 1 层大小和收之前一样',!!回&&回.层==1&&回.宽==一.宽&&回.高==一.高,回);
验('⑦ 回第 1 层底下一行回来',getComputedStyle(line).display!='none','');
验('⑦ 回第 1 层名牌提示复原',行们().every(r=>JSON.stringify(牌(r.dataset.t).map(a=>a.title))==JSON.stringify(原题[r.dataset.t])),行们().map(r=>牌(r.dataset.t).map(a=>a.title)));

去层(2,true);await wait(900);
const 总=[...document.querySelectorAll('.claim.ovc .ctag')];
验('⑧ 总览的名牌也四角圆（6.48）',总.length>0&&总.every(a=>角(a)=='6px 6px 6px 6px'),总.slice(0,3).map(角));
// ⑩ 施工区的名牌：现在不一定有人在施工区干活，临时摆一块看样式（施工区的框圆角小一号，名牌跟着 4 像素）
const 假=document.createElement('div');假.className='wa';假.innerHTML='<div class="claim" style="--c:var(--claude)"><span class="ctags"><span class="ctag">施工</span></span></div>';cv.appendChild(假);
验('⑩ 施工区的名牌四角圆（4 像素）',角(假.querySelector('.ctag'))=='4px 4px 4px 4px',角(假.querySelector('.ctag')));假.remove();
去层(1,true);await wait(600);去层(0,true);await wait(900);
验('⑨ 总览 → 第 1 层 → 名牌层，大小照旧',(末窗()||{}).层==0&&末窗().宽==零.宽&&末窗().高==零.高,末窗());
// ⑪ 6.77（用户 11-06：「只要最上层的状态就行……不用告诉我到底是在派工、还是在跨区，最上面那个是在施工就行，其他的可以收起来」）：
// 一个任务挂两盏灯（本区等你 + 别家跨区施工），名牌层只挂一块、写施工、列 1 格；第 1 层照旧一个会话一块
const 测t=DATA.任务.find(x=>x.灯.length&&!x.施工区)||DATA.任务.find(x=>!x.施工区&&!x.占位);
const 测键=测t.键,现t=()=>DATA.任务.find(x=>x.键==测键)||测t;   // 页面隔一会儿会重取数据，按键找最新的那份再摆
const 摆=()=>{const now=Date.now()/1000;现t().灯=[{谁:'Claude',说:'交了',格子:[],开始:now-300,态:'等',会话:'local_测-本区',接入:'claude',要你:false,收工:false,链:'claude://code/continue?session=local_测-本区'},
  {谁:'Codex',说:'跨区施工（从 别处 过来）',格子:[],开始:now-100,态:'干',会话:'local_测-跨区',接入:'codex',要你:false,收工:false,链:'codex://threads/测-跨区'}];};
去层(0,true);await wait(900);摆();renderOverview(cv,MAIN);要窗.k='';要窗();await wait(400);
const 零牌=牌(测键);
验('⑪ 名牌层：挂两盏灯（本区等你 + 跨区施工）也只一块',零牌.length==1,零牌.map(a=>a.textContent));
验('⑪ 写最上层的状态：有人在干就写施工（跨区不单写），颜色是那盏灯的谁',!!零牌[0]&&零牌[0].textContent=='施工'&&零牌[0].style.getPropertyValue('--c').includes('codex'),零牌[0]&&[零牌[0].textContent,零牌[0].style.getPropertyValue('--c')]);
验('⑪ 跨区来的那块点进这个任务自己的会话',!!零牌[0]&&(零牌[0].getAttribute('href')||'')==(现t().会话链接||'codex://threads/测-跨区'),零牌[0]&&[零牌[0].getAttribute('href'),现t().会话链接]);
验('⑪ 名牌层只 1 格宽',(末窗()||{}).宽==M1+CW+M1,末窗());
验('⑪ 停上去写的是挂出来那块（Codex 施工），不是等你',!!零牌[0]&&/ · Codex 施工/.test(零牌[0].title),零牌[0]&&零牌[0].title);
去层(1,true);await wait(900);摆();renderOverview(cv,MAIN);
验('⑪ 第 1 层照旧一个会话一块',牌(测键).length==2,牌(测键).map(a=>a.textContent));
去层(1,true);await wait(600);
return {过:过.length,败};
