#!/bin/bash
# 双击打开「无限表格」：在本机开一个小服务（只有这台电脑能访问），再用浏览器打开看板。
# 关掉这个终端窗口，看板就停了（终端问要不要终止进程，点「终止」）。说明见 说明.md。
cd "$(dirname "$0")" || exit 1
PORT=8770
URL="http://127.0.0.1:${PORT}/"
if /usr/sbin/lsof -nP -iTCP:${PORT} -sTCP:LISTEN >/dev/null 2>&1; then
  # 端口有人在听：问一下 /api/版，回答里有「进程」才是看板；别的程序占着就直说，不打开错的页面
  if /usr/bin/curl -s -m 2 "${URL}api/%E7%89%88" | grep -q '进程'; then
    echo "无限表格已经开着，在浏览器里打开：${URL}"
    [ -z "${BAN_NO_BROWSER}" ] && open "${URL}"
    echo "（这个窗口可以关掉，看板在原来那个窗口里跑着）"
    exit 0
  fi
  echo "${PORT} 端口被别的程序占着（不是无限表格）。先关掉那个程序再双击；或者在终端里换个端口开：/usr/bin/python3 \"$(pwd)/工具/板.py\" 服务 8780"
  exit 1
fi
echo "正在打开无限表格……"
# 第一次打开、又没写 设置.json：先把仓库自带的演示工作区准备好（错开修改时间、登记演示施工区、亮几盏演示灯）
if [ ! -f "设置.json" ] && [ ! -d "数据.nosync" ]; then
  /usr/bin/python3 "工具/板.py" 演示 || echo "演示没准备好，看板照样打开"
fi
( sleep 1.5; [ -z "${BAN_NO_BROWSER}" ] && open "${URL}" ) &
exec /usr/bin/python3 "工具/板.py" 服务 ${PORT}
