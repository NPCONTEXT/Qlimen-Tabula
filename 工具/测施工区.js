// 卷四 6.65–6.66 施工区横排 + 表格里直接干活。测页面.mjs 的脚本体（11-06 重写；竖着那版的测试在 归档/改前备份/测施工区-1106-竖排.js）。
// 11-07 分卷五 8.3：页面改成照 区域.json 画，MV.镜 → 条目们()、横镜 → 画条目、WA.mv → 区W()、#mvNote → #zqNote、loadMV → loadQD。
// 跑法：先 /usr/bin/python3 工具/测施工区-备环境.py（照固定样本搭 /tmp/ban-hp，6.85；每跑一遍前都重搭，测试会往里写），再照它打印的命令在 8771 起测试服务（BAN_OPEN=/bin/echo 免得真开 QuickTime），
//   BAN_NATIVE=1 node 工具/测页面.mjs http://127.0.0.1:8771/ 工具/测施工区.js "" 1312x764
// 8.8 起改字不另弹框，盖在格子上（.hin）。改坏验法：开编辑 里框宽改回 Math.max(c.offsetWidth,240)，⑧ 第一条要红；滚轮里去掉 .hin 那句判断，⑧ 滚轮那条要红。
// 会往存档副本里写：改一格画面、挑两次候选。改坏验法：把 横排列们() 里每镜的宽改掉，② 要红；把滚轮里的 镜头边界 去掉，⑤ 要红；把 粘标() 里的 translateX 去掉，⑥ 要红。
const 收=[];window.webkit={messageHandlers:{ban:{postMessage:m=>收.push(m)}}};   // 接住页面发给小窗的话
const 过=[],败=[];const 验=(名,ok,细)=>(ok?过:败).push(名+(ok?'':'：'+JSON.stringify(细)));
const 末窗=()=>{for(let i=收.length-1;i>=0;i--)if(收[i].窗)return 收[i].窗;return null;};
const 滚=async(dx,dy)=>{vp.dispatchEvent(new WheelEvent('wheel',{deltaX:dx,deltaY:dy,bubbles:true,cancelable:true}));await wait(80);};
const vr=vp.getBoundingClientRect(),格=(号,k)=>document.querySelector('.wa [data-cell="'+CSS.escape(号+'|'+k)+'"]');
const 记=[];const 原api=api;api=async(p,b)=>{记.push([p,b]);return 原api(p,b);};   // 记下页面叫了哪些接口
const 产出=(号,id)=>(条目们().find(x=>x.号==号).批次||[]).flatMap(b=>b.产出||[]).find(q=>q.id==id);

要窗.k='';去层(3,true);await wait(1500);
const 窗=末窗();
验('① 第 3 层窗口 = 字段名 2 格 + 6 镜 + 两边 16、22 行加底下一行正好放下',!!窗&&窗.宽==(横标格+6*横镜格)*CW+2*M1&&窗.高==M1+横行位._高*G+M1+28,窗);
const 列=横排列们(),段=横排列们.段;
验('② 所有镜一字排开：一镜挨一镜往右、每镜 3 格',列.length==条目们().length&&列.every((c,i)=>i==0||c.x-列[i-1].x==横镜格*CW),列.length);
验('② 段名横跨在各自的镜上面、一段接一段',段.every((s,i)=>i==0||s.x0==段[i-1].x1)&&段.reduce((n,s)=>n+s.n,0)==条目们().length,段.map(s=>s.n));
const lab=[...document.querySelectorAll('.wa .hlab>div')].slice(1);
验('③ 左边 10 个字段名和格子在同一行',lab.length==横行.length&&横行.every(([k],i)=>{const c=格(列[0].j.号,k);return c&&Math.abs(c.getBoundingClientRect().top-lab[i].getBoundingClientRect().top)<1;}),lab.length);
const 镜数=document.querySelectorAll('.wa .hno').length;
验('④ 只画窗口附近的几镜',镜数>=6&&镜数<条目们().length,镜数);

// ⑤ 只左右滑：上下滚不动，左右滑到头停住；⑥ 字段名、段名粘在左边
const y0=cam.y;await 滚(0,600);
验('⑤ 一屏放得下 22 行时，上下滚不动',cam.y==y0,[y0,cam.y]);
for(let i=0;i<80;i++)await 滚(800,0);
const 末=列[列.length-1].j,末格=格(末.号,'镜号');
验('⑤ 往右滑到头：最后一镜在窗口里、右边留 16',!!末格&&Math.abs(innerWidth-末格.getBoundingClientRect().right-(M1+I))<=2,末格?innerWidth-末格.getBoundingClientRect().right:'没画出来');
const 标框=document.querySelector('.wa .hlab').getBoundingClientRect();
验('⑥ 滑到右边，字段名一列还粘在左边',Math.abs(标框.left-vr.left-M1)<=1,标框.left-vr.left);
const 缝=[0.25,0.5,0.75].map(f=>document.elementFromPoint(vr.left+Math.max(2,M1/2),标框.top+标框.height*f));
验('⑥ 冻结的第一列盖到窗口最左边：左边那条缝里是它的白底，不露滑过去的格子（6.88）',缝.every(e=>e&&e.closest('.hlab')),缝.map(e=>e&&(e.className||e.tagName)));
const sg=[...document.querySelectorAll('.wa .hseg')].find(s=>{const r=s.getBoundingClientRect();return r.left<标框.right&&r.right>标框.right+80;});
验('⑥ 被字段名盖住开头的那一段，段名挪到看得见的地方',!sg||sg.firstElementChild.getBoundingClientRect().left>=标框.right-1,sg?[sg.firstElementChild.getBoundingClientRect().left,标框.right]:'');
for(let i=0;i<80;i++)await 滚(-800,0);
验('⑤ 往左滑到头停在原位',Math.abs(cam.x-(区W().x-M1))<1,cam.x);
// ⑤ 卷四 6.86（用户 11-06：「施工区我建议还是可以上下左右……普通滚轮最好仍然上下滚动，横向移动交给 Shift + 滚轮」；方向键逐格、按住空白拖画布）
const x5=cam.x;vp.dispatchEvent(new WheelEvent('wheel',{deltaY:300,shiftKey:true,bubbles:true,cancelable:true}));await wait(80);
验('⑤ Shift + 滚轮（只有上下的量）往右走',cam.x>x5+100,[x5,cam.x]);
const x6=cam.x;dispatchEvent(new KeyboardEvent('keydown',{key:'ArrowRight',bubbles:true,cancelable:true}));await wait(50);
验('⑤ → 往右走一格（64）',Math.abs(cam.x-x6-CW)<1,[x6,cam.x]);
dispatchEvent(new KeyboardEvent('keydown',{key:'ArrowLeft',bubbles:true,cancelable:true}));await wait(50);
验('⑤ ← 走回来',Math.abs(cam.x-x6)<1,[x6,cam.x]);
const 段格=document.querySelector('.wa .hseg'),sr=段格&&段格.getBoundingClientRect(),x7=cam.x;
if(段格){段格.dispatchEvent(new MouseEvent('mousedown',{button:0,clientX:sr.left+40,clientY:sr.top+8,bubbles:true}));dispatchEvent(new MouseEvent('mousemove',{clientX:sr.left-160,clientY:sr.top+8,bubbles:true}));dispatchEvent(new MouseEvent('mouseup',{clientX:sr.left-160,clientY:sr.top+8,bubbles:true}));await wait(80);}
验('⑤ 在段名那一行（空白处）按住往左拖：画布往右走 200',!!段格&&Math.abs(cam.x-x7-200)<1,[x7,cam.x]);
vp.style.height='360px';await wait(80);const y8=cam.y;await 滚(0,200);
验('⑤ 窗口矮得放不下 22 行时，普通滚轮照常上下滚',cam.y>y8+100,[y8,cam.y]);
vp.style.height='';await 滚(0,-2000);for(let i=0;i<80;i++)await 滚(-800,0);

// ⑦ 名字写全
const 长=条目们().filter(j=>(j.角色||'').split('（')[0].length>8);
验('⑦ 长角色名写全',长.length>0&&长.every(j=>画条目(j,0,()=>'').includes(esc((j.角色||'').split('（')[0]))),长.map(j=>j.号));

// ⑧ 就地改字（分卷五 8.8 用户挑甲）：点画面格，这一格原地变成能改的字（盖在格子上、位置大小一样，不另弹框），长了在格子里上下滑、滚轮留给这格；点别处就存进存档、格子跟着变；Esc 不存
const j0=列[1].j,原画面=j0.画面||'',g0=格(j0.号,'画面');g0.click();await wait(300);
const hin=document.querySelector('.hin'),ed=hin&&hin.querySelector('textarea');
验('⑧ 点文字格：就在这一格里改，位置、大小和格子一样，没有另弹的框',!!hin&&!document.querySelector('.hedit')&&(()=>{const a=hin.getBoundingClientRect(),b=g0.getBoundingClientRect();return Math.abs(a.left-b.left)<1&&Math.abs(a.top-b.top)<1&&Math.abs(a.width-b.width)<1&&Math.abs(a.height-b.height)<1;})(),hin&&hin.style.cssText);
验('⑧ 里面是原文',!!ed&&ed.value==原画面,ed&&ed.value.slice(0,20));
if(ed){ed.value='很长的一段画面描述，用来试格子里能不能上下滑。'.repeat(12);}
验('⑧ 字长了在格子里上下滑（能滚），格子不变大',!!ed&&ed.scrollHeight>ed.clientHeight+10&&Math.abs(hin.getBoundingClientRect().height-g0.getBoundingClientRect().height)<1,ed&&[ed.scrollHeight,ed.clientHeight]);
const 前y=cam.y,轮=new WheelEvent('wheel',{deltaY:80,bubbles:true,cancelable:true});if(ed)ed.dispatchEvent(轮);await wait(100);
验('⑧ 滚轮在点开的这格上：留给格子自己滚，表格不动',!!ed&&!轮.defaultPrevented&&cam.y==前y,[轮.defaultPrevented,前y,cam.y]);
if(ed){ed.value=原画面+'（测试加的）';ed.dispatchEvent(new Event('input',{bubbles:true}));ed.blur();await wait(1500);}
验('⑧ 点别处就存：存档、格子都变了',(条目们().find(x=>x.号==j0.号).画面||'').endsWith('（测试加的）')&&(格(j0.号,'画面')||{textContent:''}).textContent.includes('测试加的'),(条目们().find(x=>x.号==j0.号).画面||'').slice(-8));
格(j0.号,'素材').click();await wait(300);
const ed2=document.querySelector('.hin textarea');if(ed2){ed2.value='不该存';ed2.dispatchEvent(new KeyboardEvent('keydown',{key:'Escape',bubbles:true}));await wait(800);}
验('⑧ Esc 关掉、不存',!!ed2&&!document.querySelector('.hin')&&(条目们().find(x=>x.号==j0.号).素材||'')!='不该存','');

// ⑨ 看大图：点样图候选弹出大图，「选这张」记进存档，Esc 关
const pi=[...document.querySelectorAll('.wa [data-cell$="|样图"] .mcands i')].find(i=>i.querySelector('b'));
if(pi){const 号=pi.dataset.hpv.split('|')[0];pi.click();await wait(400);
  验('⑨ 点样图候选弹出大图',$('lbx').classList.contains('on')&&!!$('lbx').querySelector('img'),'');
  const s=$('lbx')._s,id=s&&s.ps[s.i].id,pb=$('lbx').querySelector('[data-lb="pick"]');if(pb){pb.click();await wait(1200);}
  验('⑨ 大图里「选这张」记进存档',!!pb&&!!id&&!!(产出(号,id)||{}).选,id);
  dispatchEvent(new KeyboardEvent('keydown',{key:'Escape'}));await wait(200);
  验('⑨ Esc 关大图',!$('lbx').classList.contains('on'),'');}
else 验('⑨ 有能挑的样图候选',false,'没有');

// ⑩ 样片：点候选叫看板用 QuickTime 开
const vi=document.querySelector('.wa [data-cell$="|样片"] .mcands i');
if(vi){vi.click();await wait(800);const k=记.find(([p])=>p=='/api/打开');
  验('⑩ 点样片候选：叫看板用 QuickTime 开那个视频',!!k&&k[1].用=='QuickTime'&&/\.(mp4|mov|m4v)$/i.test(k[1].文件||''),k&&k[1]);}
else 验('⑩ 有样片候选',false,'没有');

// ⑪ 候选上悬停出的「选」直接挑
const hb=document.querySelector('.wa .mcands i b[data-hpick]');
if(hb){const [号,id]=hb.dataset.hpick.split('|');hb.click();await wait(1200);验('⑪ 候选上的「选」直接挑',!!(产出(号,id)||{}).选,id);}
else 验('⑪ 有没选的候选',false,'没有');

// ⑫ 详情表精简：点镜号开；表格里有的字段不再摆；意见写的框在最上面、外面最多两条
格(j0.号,'镜号').click();await wait(600);
const 字段=[...sidein.querySelectorAll('textarea[data-field]')].map(t=>t.dataset.field);
验('⑫ 详情表不再摆表格里有的字段',side.classList.contains('open')&&!字段.some(f=>['画面','景别','运镜','歌词','时间','素材','备注','分镜状态'].includes(f)),字段);
const blk=[...sidein.querySelectorAll('.blk')].find(b=>/^意见/.test((b.querySelector('.sh')||{}).textContent||''));
const 外条=blk?[...blk.children].filter(e=>e.classList.contains('note')).length:-1,框=blk&&blk.querySelector('#zqNote'),条1=blk&&blk.querySelector(':scope>.note');
验('⑫ 意见：写的框在最上面、外面最多两条',!!框&&外条>=1&&外条<=2&&!!条1&&!!(框.compareDocumentPosition(条1)&4),外条);
sidein.scrollTop=99999;await wait(100);const 收b=sidein.querySelector('.sclose'),题b=sidein.querySelector('h3'),右r=side.getBoundingClientRect();
验('⑫ 详情页滚到最底下，「收起」和标题还在最上面（6.89）',sidein.scrollTop>0&&!!收b&&!!题b&&收b.getBoundingClientRect().top>=右r.top-1&&收b.getBoundingClientRect().top<右r.top+40&&题b.getBoundingClientRect().top<右r.top+40,[sidein.scrollTop,收b&&收b.getBoundingClientRect().top,题b&&题b.getBoundingClientRect().top,右r.top]);
closeSide();await wait(200);

// ---------- 卷四 6.67：格子状态（复用认领框，名牌只换字：改了 / 施工 / 等你 / 验收）、全手动叫醒、红点、名牌层圆点 ----------
// Claude 那边的动作用 sh 在副本上跑（导演台「列」「改」、板.py 开工 / 等你），不碰正在用的数据
const 框上=(号,k)=>{const c=格(号,k);if(!c)return null;const r=c.getBoundingClientRect();return [...document.querySelectorAll('.wa .claim')].find(f=>{const q=f.getBoundingClientRect();return Math.abs(q.left-r.left)<1&&Math.abs(q.top-r.top)<1;})||null;};
const 牌字=f=>f?[...f.querySelectorAll('.ctag')].map(t=>t.textContent).join('+'):'';
const 刷=async()=>{await tick();await wait(400);};
const 等到=async(f,ms=8000)=>{const t0=Date.now();while(Date.now()-t0<ms){await tick();await wait(300);if(f())return true;}return false;};   // Claude 那边一动，看板要过几秒才把新状态给页面
const 信箱行=async()=>+((await sh('cat /tmp/ban-hp/数据/信箱/*.jsonl 2>/dev/null | wc -l')).trim()||0);
const 台='/usr/bin/python3 "$BAN_REPO/工具/施工台.py" /tmp/ban-hp/导演台',板='BAN_ROOT=/tmp/ban-hp/工作区 BAN_DATA=/tmp/ban-hp/数据 DYT_DIR=/tmp/ban-hp/导演台 /usr/bin/python3 /tmp/ban-hp/工具/板.py';   // 台：施工台引擎的命令行（BAN_REPO 由 跑页面测试.py 给）
await 刷();
const f13=框上(j0.号,'画面');
验('⑬ 用户改过、Claude 还没读到的格：灰框、名牌「改了」',!!f13&&f13.classList.contains('xu')&&牌字(f13)=='改了',牌字(f13));
const 箱前=await 信箱行(),ok18=await api('/api/op',{op:'通过',镜:列[3].j.号}).then(()=>true,()=>false);await wait(600);   // 通过、选、重出、意见……以前一做就自动投信
验('⑱ 全手动：施工区里点了「这一镜通过」，信箱里没多东西',ok18&&(await 信箱行())==箱前,箱前);
await 刷();setLine();const wk=line.querySelector('[data-wake]');
验('⑭ 底下一行有「叫醒 Claude」',!!wk,line.textContent);
if(wk){wk.click();await wait(1500);}
const 最后=await sh('tail -n 1 /tmp/ban-hp/数据/信箱/*.jsonl 2>/dev/null');
验('⑭ 点了叫醒：信箱多一条、写着改了哪几格',(await 信箱行())==箱前+1&&/MV 施工区：用户改了/.test(最后)&&最后.includes(j0.号),最后.slice(0,160));
await 刷();setLine();验('⑭ 发完「叫醒」就不显示了',!line.querySelector('[data-wake]'),line.textContent);
const j1=列[2].j;await api('/api/op',{op:'意见',镜:j1.号,文:'测试意见：这里要你看一下'});
await sh(台+' 列 >/dev/null');await sh(板+' 开工 视频/示例MV/MV --说 测试 >/dev/null');await 等到(()=>/施工/.test(牌字(框上(j0.号,'画面'))));
const f15=框上(j0.号,'画面');
验('⑮ Claude 读到、灯亮着：橙框、名牌「施工」、亮片走',!!f15&&!f15.classList.contains('xu')&&!f15.classList.contains('wait')&&/施工/.test(牌字(f15)),[牌字(f15),f15&&f15.className]);
await sh(台+' 改 '+j0.号+' 画面 "Claude 改好的画面" >/dev/null');await sh(板+' 等你 视频/示例MV/MV --说 测试 >/dev/null');await loadQD(true);await 等到(()=>牌字(框上(j0.号,'画面'))=='验收'&&牌字(框上(j1.号,'镜号'))=='等你');
const f16=框上(j0.号,'画面'),g16=框上(j1.号,'镜号');
验('⑯ Claude 改好了停下：那格「验收」、框留着、亮片停',!!f16&&f16.classList.contains('wait')&&牌字(f16)=='验收',[牌字(f16),f16&&f16.className]);
验('⑯ Claude 没动的那格（只写了意见）：「等你」',!!g16&&牌字(g16)=='等你',牌字(g16));
const ac=f16&&f16.querySelector('[data-hacc]');if(ac){ac.click();await 等到(()=>!框上(j0.号,'画面'));}
验('⑰ 点名牌「验收」= 知道了，这一格的框消失',!!ac&&!框上(j0.号,'画面'),'');
格(j0.号,'备注').click();await wait(300);const ed3=document.querySelector('.hin textarea');if(ed3){ed3.value='测试备注';ed3.dispatchEvent(new Event('input',{bubbles:true}));ed3.blur();await wait(1500);}
红点分=0;await 刷();setLine();
验('⑲ 改了没叫醒、到了时间：底下一行最左边一个红点',!!line.firstElementChild&&line.firstElementChild.classList.contains('reddot'),line.innerHTML.slice(0,80));
去层(0,true);await wait(600);setLine();
const 点=[...line.children].filter(e=>getComputedStyle(e).display!='none');
验('⑲ 名牌层底下一行只剩圆点，红点也在',getComputedStyle(line).display!='none'&&点.length>0&&点.every(e=>e.tagName=='I')&&点.some(e=>e.classList.contains('reddot')),点.map(e=>e.tagName+'.'+e.className));
去层(3,true);await wait(400);红点分=10;
return {过:过.length,败};
