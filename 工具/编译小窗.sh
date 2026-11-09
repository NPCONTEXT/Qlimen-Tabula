#!/bin/bash
# 编译原生小窗：工具/小窗/*.swift → 小窗.nosync/无限表格小窗.app
# 先编到 小窗.nosync/新/、签好名再换上去：正开着的小窗不受影响（还用换下来的旧文件），关了重开就是新的。
# 放 .nosync：不进 iCloud（重编时不会冒出「名字 2」）。改了 Swift 跑这个就行，看板服务不用重开。
# 每次重编都算新程序：小窗起的服务第一次读「文稿」会等系统弹框，要点「好」。
set -e
cd "$(dirname "$0")/.."
rm -rf "小窗.nosync/新" "小窗.nosync/旧"
mkdir -p "小窗.nosync/新/无限表格小窗.app/Contents/MacOS"
swiftc -O -swift-version 5 -o "小窗.nosync/新/无限表格小窗.app/Contents/MacOS/BanWindow" 工具/小窗/*.swift -framework AppKit -framework WebKit -framework SwiftUI
# 程序图标：Qlimen 标志定稿的 qlimen.icns（11-01 换的；旧图标是 工具/画小窗图标.swift 画的）
mkdir -p "小窗.nosync/新/无限表格小窗.app/Contents/Resources"
cp 工具/小窗/AppIcon.icns "小窗.nosync/新/无限表格小窗.app/Contents/Resources/AppIcon.icns"
# 菜单栏图标：新标志的单色图形（11-01 定稿，18 和 36 像素两张，系统按屏幕挑）
cp 工具/小窗/menubar.png 工具/小窗/menubar@2x.png "小窗.nosync/新/无限表格小窗.app/Contents/Resources/"
cat > "小窗.nosync/新/无限表格小窗.app/Contents/Info.plist" <<'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>CFBundleIdentifier</key><string>local.qlimen.wuxianbiaoge</string>
  <key>CFBundleName</key><string>无限表格小窗</string>
  <key>CFBundleDisplayName</key><string>无限表格小窗</string>
  <key>CFBundleExecutable</key><string>BanWindow</string>
  <key>CFBundleIconFile</key><string>AppIcon</string>
  <key>CFBundlePackageType</key><string>APPL</string>
  <key>CFBundleShortVersionString</key><string>1.1</string>
  <key>CFBundleVersion</key><string>2</string>
  <key>CFBundleDevelopmentRegion</key><string>zh_CN</string>
  <key>LSMinimumSystemVersion</key><string>14.0</string>
  <key>NSHighResolutionCapable</key><true/>
  <key>NSAppTransportSecurity</key><dict><key>NSAllowsLocalNetworking</key><true/></dict>
</dict>
</plist>
EOF
# 文稿文件夹里的目录会被挂上 FinderInfo 等扩展属性，codesign 见了就拒签；清掉后有时马上又被挂回去，所以签不上就再来（最多三次）
SIGNED=""
for i in 1 2 3; do
  xattr -cr "小窗.nosync/新/无限表格小窗.app"
  if codesign --force --sign - "小窗.nosync/新/无限表格小窗.app" >/dev/null 2>&1; then SIGNED=1; break; fi
  sleep 1
done
[ -n "${SIGNED}" ] || echo "（签名没成功：本机自己编的照样能开）"
if [ -d "小窗.nosync/无限表格小窗.app" ]; then mv "小窗.nosync/无限表格小窗.app" "小窗.nosync/旧"; fi
mv "小窗.nosync/新/无限表格小窗.app" "小窗.nosync/无限表格小窗.app"
rm -rf "小窗.nosync/新" "小窗.nosync/旧"
# 让访达、程序坞认新图标（不登记的话访达可能一直显示旧的空白图标）
/System/Library/Frameworks/CoreServices.framework/Frameworks/LaunchServices.framework/Support/lsregister -f "小窗.nosync/无限表格小窗.app" >/dev/null 2>&1 || true
echo "编好了：$(pwd)/小窗.nosync/无限表格小窗.app"
