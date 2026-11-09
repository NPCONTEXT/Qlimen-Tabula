#!/bin/bash
# 装 Claude 桌面应用的插件「无限表格监听」（ban-listen）：替 Claude 会话自动开关灯，把你在看板上点的、写的发进会话。
# 用法：bash 工具/装插件.sh          只预演：打印会做什么，不动任何文件
#       bash 工具/装插件.sh --装     真装：复制 插件/ban-listen 到 ~/.claude/skills/ban-listen，写上看板在哪（看板位置.txt）
# 已经装过的，先把旧的挪到 ~/.claude/skills/ban-listen.备份-时间 再装新的。装完要新开会话才加载。
# 卸载：删掉 ~/.claude/skills/ban-listen 这个文件夹，新开会话就没了。
set -e
REPO="$(cd "$(dirname "$0")/.." && pwd)"
SRC="${REPO}/插件/ban-listen"
DEST="${HOME}/.claude/skills/ban-listen"
case "${REPO}" in
  *" "*) echo "看板放在带空格的路径里（${REPO}），插件认不出命令里的路径：挪到不带空格的地方再装" >&2; exit 1 ;;
esac
[ -f "${SRC}/hooks/register.ts" ] || { echo "找不到插件源码：${SRC}" >&2; exit 1; }
BAK=""
[ -e "${DEST}" ] && BAK="${DEST}.备份-$(date +%Y%m%d-%H%M%S)"
if [ "$1" != "--装" ]; then
  echo "预演（没动任何文件）："
  [ -n "${BAK}" ] && echo "  - 已经装过：把 ${DEST} 挪到 ${BAK}"
  echo "  - 复制 ${SRC} → ${DEST}"
  echo "  - 写 ${DEST}/看板位置.txt，内容：${REPO}"
  echo "确认没问题就加 --装 再跑一次：bash \"${REPO}/工具/装插件.sh\" --装"
  exit 0
fi
mkdir -p "${HOME}/.claude/skills"
if [ -n "${BAK}" ]; then mv "${DEST}" "${BAK}"; echo "旧的挪到了 ${BAK}"; fi
cp -R "${SRC}" "${DEST}"
printf '%s\n' "${REPO}" > "${DEST}/看板位置.txt"
echo "装好了：${DEST}（看板在 ${REPO}）。新开一个 Claude Code 会话就会加载。"
