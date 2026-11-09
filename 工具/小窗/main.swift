// 无限表格 · 原生小窗（macOS）
// 一层结构（11-02 02:4x 用户定，方案第十五节）：一张格子表、一个窗口、三个镜头。三层都是看板页面画的，同一批格子原地变形：
//   第 1 层：在干、等你的任务一行一个；第 2 层：总览（同一批格子折成两行）；第 3 层：施工区。
//   第 0 层「名牌层」（卷四 6.42–6.44，11-06 用户要「只露出每个任务的状态按钮」）：第 1 层再按 − 收成只留名牌的一列，以左上角为准（用户选乙）；不写标题字（太窄放不下）。
// 窗口左上角 x − + 就是全部按钮：x 关窗口（收到菜单栏），− 缩一层，+ 放一层（双击标题栏也是放一层；系统设成双击最小化的话就是缩一层，⌘M 也是）。
// 窗口多大由页面算好告诉小窗（{窗:{层,宽,高}}），小窗以左上角为准原地动画改大小；你拖到哪，左上角就记在哪；
// 2、3 层你自己拉过大小的，以后照你拉的。第 1、2 层置顶，第 3 层是普通窗口（免得挡你开着的软件）。
// 用系统标题栏（11-02 04:4x 用户要回上下两条细边、应用的完整感）：按住标题栏拖，双击标题栏也是放一层。
// 置顶开关（11-02 21:3x 用户：「可以加一个置顶开关」）：菜单栏图标右键、窗口菜单里的「置顶」，关了第 1、2 层也是普通窗口；记在 UserDefaults「置顶」，自测时用 BAN_PIN=0/1 定、不记。
// 屏幕顶部菜单栏常驻一个图标：点一下收起 / 拿出来，右键有「置顶」「总览」「重开看板服务」「退出小窗」。收着的时候双击程序、看板上点「置顶小窗」也会拿出来。
// 看板服务没开就在后台起一个（服务.swift）；小窗自己 1.5 秒问一次服务（数据.swift），只用来守服务和图标提示。
// 编译：工具/编译小窗.sh → 小窗.nosync/无限表格小窗.app。看板右上角「置顶小窗」、Claude 插件「无限表格监听」都用 open 打开它。
// 自测：BAN_URL 指到测试服务；BAN_TEST 给一串步骤（JSON 数组）：{"等":秒} {"层":0|1|2|3} {"按":"缩|放|关"}（点窗口左上角的键） {"最小化":1} {"点行":序号}
//   {"js":函数体} {"拍":png（网页）} {"收起":1} {"拿出来":1} {"重开":1}（重开看板服务） {"报":1}；跑完自己退出，测试时不抢焦点、不记位置。

import AppKit
import WebKit

final class 浮窗: NSPanel {
    var 缩: (() -> Void)?   // 最小化（双击标题栏设成最小化、⌘M）都当「缩一层」，不进程序坞
    override var canBecomeKey: Bool { true }
    override var canBecomeMain: Bool { true }
    override func miniaturize(_ s: Any?) { if let 缩 { 缩() } else { super.miniaturize(s) } }
    override func performMiniaturize(_ s: Any?) { if let 缩 { 缩() } else { super.performMiniaturize(s) } }
}

final class 小窗控制: NSObject, NSApplicationDelegate, NSWindowDelegate, WKNavigationDelegate, WKUIDelegate, WKScriptMessageHandler, NSMenuItemValidation {
    var 窗: 浮窗!
    var 网: WKWebView!
    var 数据: 看板数据!
    var 服务: 看板服务!
    var 层 = 1
    var 页面好了 = false
    var 重试: Timer?
    let 地址: URL
    let 任务目录: URL
    let 测试步骤: [[String: Any]]?
    var 测过 = false
    let 存 = UserDefaults.standard
    var 状态栏: NSStatusItem!
    var 收起了 = false
    var 在动 = false        // 小窗自己在动画改大小：这时候的挪动、改大小不算你拖的
    var 锚: NSPoint!        // 窗口左上角（你拖到哪就是哪）；改大小都以它为准，碰到屏幕边只是这一次往回收
    var 当前右栏: CGFloat = 0   // 页面右栏开着时多要的宽（存你拉的大小时扣掉）
    var 页计: (干: Int, 等: Int)?   // 页面告诉的几处在干、几处等你（11-03 起小窗不再自己读整份看板）
    var 用户在拉 = false
    var 重起次数 = 0   // 自己起的服务退了再起：连着 3 次都没连上就不再起，等人看
    var 在测: Bool { 测试步骤 != nil }

    override init() {
        // 地址：BAN_URL > 命令行 --端口 N（看板服务打开小窗时带上自己的端口）> 8770
        let env = ProcessInfo.processInfo.environment
        let a = CommandLine.arguments
        var 端口 = "8770"
        if let k = a.firstIndex(of: "--端口"), k + 1 < a.count { 端口 = a[k + 1] }
        地址 = URL(string: env["BAN_URL"] ?? "http://127.0.0.1:\(端口)/")!
        // 任务目录：…/无限表格/小窗.nosync/无限表格小窗.app → …/无限表格
        任务目录 = Bundle.main.bundleURL.deletingLastPathComponent().deletingLastPathComponent()
        if let s = env["BAN_TEST"], let d = s.data(using: .utf8),
           let j = try? JSONSerialization.jsonObject(with: d) as? [[String: Any]] {
            测试步骤 = j
        } else {
            测试步骤 = nil
        }
        super.init()
    }

    func applicationDidFinishLaunching(_ n: Notification) {
        菜单()
        服务 = 看板服务(地址: 地址, 任务目录: 任务目录)
        数据 = 看板数据(地址: 地址)
        数据.连不上 = { [weak self] in self?.守服务() }
        数据.连好了 = { [weak self] in
            guard let self else { return }
            // 连上了就清零：只有连着 3 次都起不来才停手（卷二 7.41：以前只在守服务里问到才清零，换三次版以后第四次就不再起，11-04 看板停了约 40 分钟）
            self.重起次数 = 0
            self.更新图标提示()
            if !self.页面好了, self.重试 == nil, !self.网.isLoading { self.打开页面() }
        }
        做窗()
        做菜单栏图标()
        数据.开始()
        窗.orderFrontRegardless()
        if 在测 {
            DispatchQueue.main.asyncAfter(deadline: .now() + 60) { print("测试超时，退出"); exit(3) }
        }
        守服务()
    }

    func applicationWillTerminate(_ n: Notification) {
        记锚()
        服务.停()
    }

    func applicationShouldTerminateAfterLastWindowClosed(_ s: NSApplication) -> Bool { false }

    /// 收着的时候双击小窗程序、看板上点「置顶小窗」（都会发「重新打开」）：拿出来
    func applicationShouldHandleReopen(_ s: NSApplication, hasVisibleWindows 有: Bool) -> Bool {
        if 收起了 || !有 { 拿出来() }
        return true
    }

    // ---------- 菜单栏图标：点一下收起 / 拿出来，右键出菜单 ----------

    func 做菜单栏图标() {
        状态栏 = NSStatusBar.system.statusItem(withLength: NSStatusItem.squareLength)
        guard let b = 状态栏.button else { return }
        // 新标志的单色图形（11-01 定稿，用笔画等粗的小尺寸版，编译时拷进程序的 Resources）；找不到就退回系统的表格图标
        let 图 = Bundle.main.image(forResource: "menubar") ?? NSImage(systemSymbolName: "tablecells", accessibilityDescription: "无限表格")
        图?.isTemplate = true
        图?.size = NSSize(width: 18, height: 18)
        b.image = 图
        b.target = self
        b.action = #selector(点图标(_:))
        b.sendAction(on: [.leftMouseUp, .rightMouseUp])
        b.toolTip = "无限表格"
    }

    @objc func 点图标(_ s: Any?) {
        let e = NSApp.currentEvent
        if e?.type == .rightMouseUp || e?.modifierFlags.contains(.control) == true {
            let m = NSMenu()
            m.addItem(withTitle: 收起了 ? "拿出小窗" : "收起到菜单栏", action: #selector(切收起), keyEquivalent: "").target = self
            let 顶 = NSMenuItem(title: "置顶", action: #selector(切置顶), keyEquivalent: "")
            顶.target = self
            顶.state = 置顶 ? .on : .off
            m.addItem(顶)
            m.addItem(withTitle: "总览", action: #selector(去总览), keyEquivalent: "").target = self
            m.addItem(withTitle: "重开看板服务", action: #selector(重开服务), keyEquivalent: "").target = self
            m.addItem(.separator())
            m.addItem(withTitle: "退出小窗", action: #selector(NSApplication.terminate(_:)), keyEquivalent: "")
            if let b = 状态栏.button { m.popUp(positioning: nil, at: NSPoint(x: 0, y: b.bounds.height + 4), in: b) }
            return
        }
        切收起()
    }

    @objc func 切收起() { 收起了 ? 拿出来() : 收起() }

    /// 置顶开关：开着时第 1、2 层浮在别的软件上面（第 3 层本来就不浮）；关了就是普通窗口。自测时 BAN_PIN=0/1 定
    var 置顶: Bool {
        if let p = ProcessInfo.processInfo.environment["BAN_PIN"] { return p != "0" }
        return 存.object(forKey: "置顶") as? Bool ?? true
    }

    @objc func 切置顶() {
        存.set(!置顶, forKey: "置顶")
        摆层级()
    }

    func 摆层级() {
        let 浮 = 层 < 3 && 置顶
        窗.isFloatingPanel = 浮
        窗.level = 浮 ? .floating : .normal
    }

    func validateMenuItem(_ i: NSMenuItem) -> Bool {
        if i.action == #selector(切置顶) { i.state = 置顶 ? .on : .off }
        return true
    }

    /// 换版：叫看板服务退出，退了以后 守服务 用新代码再起一个；页面文件变了，页面自己会整页刷新
    @objc func 重开服务() {
        数据.状况 = "看板服务重开中……"
        重起次数 = 0
        服务.请退 { [weak self] in
            DispatchQueue.main.asyncAfter(deadline: .now() + 1) { self?.守服务() }
        }
    }

    @objc func 去总览() {
        拿出来()
        跑JS("typeof 去层=='function'&&去层(2);")
    }

    func 收起() {
        记锚()
        窗.orderOut(nil)
        收起了 = true
        更新图标提示()
    }

    func 拿出来() {
        收起了 = false
        窗.orderFrontRegardless()
        if 层 >= 2, !在测 { NSApp.activate() }
        更新图标提示()
    }

    /// 图标的悬停提示：几处在干、几处等你（收着的时候也看得到）
    func 更新图标提示() {
        guard let 计 = 页计 else { 状态栏?.button?.toolTip = "无限表格" + (收起了 ? "（小窗收在这里，点一下拿出来）" : "（点一下收起小窗）"); return }
        let 干 = 计.干, 等 = 计.等
        let 字 = [干 > 0 ? "\(干) 处在干" : "", 等 > 0 ? "\(等) 处等你" : ""].filter { !$0.isEmpty }.joined(separator: " · ")
        状态栏?.button?.toolTip = "无限表格：" + (字.isEmpty ? "没有谁在干" : 字) + (收起了 ? "（小窗收在这里，点一下拿出来）" : "（点一下收起小窗）")
    }

    // ---------- 服务：没开就起，起了等它好 ----------

    func 守服务() {
        服务.在吗 { [weak self] ok in
            guard let self else { return }
            if ok {
                self.重起次数 = 0
                if !self.页面好了 && self.重试 == nil { self.打开页面() }
                return
            }
            let 隔 = Date().timeIntervalSince(self.服务.起于)
            // 自己起的那个是被叫退的（换版），不算一次没起来：只有连着崩、读不了文稿才攒次数（卷二 7.41）
            if self.服务.起过, self.服务.好好退的 { self.重起次数 = 0 }
            // 没起过；或者自己起的那个退了（换版时「重开看板服务」、崩了）：再起一个（11-01 二期补三，换版不再开终端）
            if !self.服务.起过 || (!self.服务.在跑 && 隔 > 5 && self.重起次数 < 3) {
                if self.服务.起过 { self.重起次数 += 1 }
                self.服务.起()
                self.数据.状况 = "正在开看板服务……第一次会弹框问能不能读「文稿」，点「好」"
            } else if 隔 > 20 {
                self.数据.状况 = "看板服务没开起来：右键菜单栏图标「重开看板服务」，或看 ~/Library/Logs/无限表格小窗-服务.log"
            }
        }
    }

    // ---------- 窗口：一个，x − + 在标题栏里 ----------

    func 做窗() {
        let 内容 = WKUserContentController()
        内容.add(self, name: "ban")
        内容.addUserScript(WKUserScript(source: "window.BAN_NATIVE=true;", injectionTime: .atDocumentStart, forMainFrameOnly: true))
        let 配置 = WKWebViewConfiguration()
        配置.userContentController = 内容
        锚 = 记的锚() ?? 默认锚()
        窗 = 浮窗(contentRect: NSRect(x: 0, y: 0, width: 400, height: 140), styleMask: [.titled, .closable, .miniaturizable, .resizable], backing: .buffered, defer: false)   // 11-06 卷四 6.83：去掉 .utilityWindow——带它系统报浮动窗口（AXFloatingWindow），AltTab 不当窗口、把无限表格排在最后
        let 起 = 窗.frameRect(forContentRect: NSRect(x: 0, y: 0, width: 400, height: 140))   // 页面还没来：先这么大，放得下「正在开看板服务」的提示
        窗.setFrame(NSRect(x: 锚.x, y: 锚.y - 起.height, width: 起.width, height: 起.height), display: false)
        窗.title = "无限表格"
        摆层级()
        窗.hidesOnDeactivate = false
        窗.collectionBehavior = [.canJoinAllSpaces, .fullScreenAuxiliary]
        窗.isReleasedWhenClosed = false
        窗.contentMinSize = NSSize(width: 240, height: 48)
        窗.delegate = self
        let 底 = 窗.contentView!
        网 = WKWebView(frame: 底.bounds, configuration: 配置)
        网.autoresizingMask = [.width, .height]
        网.navigationDelegate = self
        网.uiDelegate = self
        底.addSubview(网)
        // − 缩一层、+ 放一层（x 是关窗口，走 windowShouldClose）
        if let b = 窗.standardWindowButton(.miniaturizeButton) { b.target = self; b.action = #selector(缩一层) }
        窗.缩 = { [weak self] in self?.缩一层() }
        if let b = 窗.standardWindowButton(.zoomButton) { b.target = self; b.action = #selector(放一层) }
        按钮状态()
    }

    @objc func 缩一层() { 跑JS("typeof 去层=='function'&&去层(LV-1);") }
    @objc func 放一层() { 跑JS("typeof 去层=='function'&&去层(LV+1);") }

    func 按钮状态() {
        窗.standardWindowButton(.miniaturizeButton)?.isEnabled = 层 > 0   // 第 1 层也能缩：到名牌层（卷四 6.44）
        窗.standardWindowButton(.zoomButton)?.isEnabled = 层 < 3
    }

    /// 页面说这一层的内容要多大（不算标题栏）：以左上角（锚）为准原地动画改大小；2、3 层你自己拉过大小的照你的；碰到屏幕边这一次往回收
    func 改窗(_ 新层: Int, _ 宽: CGFloat, _ 高: CGFloat, 右栏: CGFloat = 0) {
        层 = 新层
        当前右栏 = 右栏
        var 大小 = NSSize(width: 宽, height: 高)
        if 新层 >= 2, let s = 存的大小(新层) { 大小 = NSSize(width: s.width + 右栏, height: s.height) }   // 右栏开着时页面多要的那 360 照加
        let 屏 = (窗.screen ?? NSScreen.main ?? NSScreen.screens[0]).visibleFrame
        大小 = 窗.frameRect(forContentRect: NSRect(origin: .zero, size: 大小)).size   // 加上标题栏
        大小.width = min(大小.width, 屏.width - 20)
        大小.height = min(大小.height, 屏.height - 20)
        var f = NSRect(x: 锚.x, y: 锚.y - 大小.height, width: 大小.width, height: 大小.height)
        if f.maxX > 屏.maxX { f.origin.x = 屏.maxX - f.width }
        if f.minX < 屏.minX { f.origin.x = 屏.minX }
        if f.minY < 屏.minY { f.origin.y = 屏.minY }
        if f.maxY > 屏.maxY { f.origin.y = 屏.maxY - f.height }
        摆层级()   // 第 3 层不置顶，免得挡住你开着的别的软件；置顶开关关了第 1、2 层也不置顶
        按钮状态()
        // 名牌层（第 0 层）：最小宽跟着名牌那一列（系统原来卡在 240）；标题字先藏，放回第 1 层时等窗口长开了再显示，免得半截
        窗.contentMinSize = NSSize(width: min(宽, 240), height: 48)
        let 显标题 = 新层 > 0
        if !显标题 { 窗.titleVisibility = .hidden }
        if f == 窗.frame { if 显标题 { 窗.titleVisibility = .visible }; return }
        在动 = true
        NSAnimationContext.runAnimationGroup({ c in
            c.duration = 在测 ? 0.05 : 0.45
            c.timingFunction = CAMediaTimingFunction(controlPoints: 0.3, 0.7, 0.2, 1)
            c.allowsImplicitAnimation = true
            窗.animator().setFrame(f, display: true)
        }, completionHandler: { [weak self] in
            self?.在动 = false
            if 显标题, self?.层 ?? 0 > 0 { self?.窗.titleVisibility = .visible }
        })
        if 新层 >= 2, !在测, !收起了 { NSApp.activate(); 窗.makeKeyAndOrderFront(nil) }
    }

    func 记的锚() -> NSPoint? {
        guard !在测, let s = 存.string(forKey: "窗.锚") else { return nil }
        let p = NSPointFromString(s)
        guard NSScreen.screens.contains(where: { $0.visibleFrame.insetBy(dx: -1, dy: -1).contains(NSPoint(x: p.x + 20, y: p.y - 10)) }) else { return nil }
        return p
    }

    func 默认锚() -> NSPoint {   // 屏幕右上角
        let v = (NSScreen.main ?? NSScreen.screens[0]).visibleFrame
        return NSPoint(x: v.maxX - 500, y: v.maxY - 20)
    }

    func 记锚() {
        guard !在测, 窗 != nil else { return }
        存.set(NSStringFromPoint(锚), forKey: "窗.锚")
    }

    func 存的大小(_ 哪层: Int) -> NSSize? {
        guard !在测, let s = 存.string(forKey: "窗.大小.\(哪层)") else { return nil }
        let z = NSSizeFromString(s)
        return z.width >= 240 ? z : nil
    }

    func windowShouldClose(_ w: NSWindow) -> Bool {   // x：关窗口 = 收到菜单栏（点菜单栏图标、程序坞图标再拿出来）
        收起()
        return false
    }

    /// 双击标题栏（系统的放大）也当 + 用
    func windowShouldZoom(_ w: NSWindow, toFrame f: NSRect) -> Bool {
        放一层()
        return false
    }

    func windowDidMove(_ n: Notification) {
        // 只认你按住拖的（左键按着）；小窗自己改大小、碰到屏幕边往回收的那种挪动不算，不然缩回来就回不到原处
        guard !在动, NSEvent.pressedMouseButtons & 1 == 1 else { return }
        锚 = NSPoint(x: 窗.frame.minX, y: 窗.frame.maxY)
        记锚()
    }

    /// 动画改大小系统也当「拉窗口边」报上来：开始时左键按着才算你拉的
    func windowWillStartLiveResize(_ n: Notification) { 用户在拉 = !在动 && NSEvent.pressedMouseButtons & 1 == 1 }

    func windowDidEndLiveResize(_ n: Notification) {
        guard 用户在拉 else { return }
        用户在拉 = false
        锚 = NSPoint(x: 窗.frame.minX, y: 窗.frame.maxY)
        记锚()
        let 内 = 窗.contentRect(forFrameRect: 窗.frame).size   // 存内容的大小（不算标题栏）
        if 层 >= 2, !在测 { 存.set(NSStringFromSize(NSSize(width: 内.width - 当前右栏, height: 内.height)), forKey: "窗.大小.\(层)") }
    }

    // ---------- 页面 ----------

    func 打开页面() { 网.load(URLRequest(url: 地址)) }

    func userContentController(_ c: WKUserContentController, didReceive m: WKScriptMessage) {
        guard let d = m.body as? [String: Any] else { return }
        if let w = d["窗"] as? [String: Any], let n = w["层"] as? Int, let 宽 = w["宽"] as? Double, let 高 = w["高"] as? Double {
            改窗(n, CGFloat(宽), CGFloat(高), 右栏: CGFloat(w["右栏"] as? Double ?? 0))
        }
        if d["开服务"] != nil { 开服务() }
        if let c = d["计"] as? [String: Any] {
            页计 = ((c["干"] as? NSNumber)?.intValue ?? 0, (c["等"] as? NSNumber)?.intValue ?? 0)
            更新图标提示()
        }
    }

    func webView(_ w: WKWebView, didFinish n: WKNavigation!) {
        guard w.url?.absoluteString.hasPrefix(地址.absoluteString) == true else { return }
        页面好了 = true
        跑JS("typeof 去层=='function'&&去层(\(层),1);")   // 页面重新载入（换版自己刷新）后还在原来那一层
        if 在测, !测过 {
            测过 = true
            DispatchQueue.main.asyncAfter(deadline: .now() + 1.5) { self.走(self.测试步骤!, 0) }
        }
    }

    func webView(_ w: WKWebView, didFailProvisionalNavigation n: WKNavigation!, withError e: Error) { 没开(e) }
    func webView(_ w: WKWebView, didFail n: WKNavigation!, withError e: Error) { 没开(e) }
    func webViewWebContentProcessDidTerminate(_ w: WKWebView) { 打开页面() }

    func 没开(_ e: Error) {
        if (e as NSError).code == NSURLErrorCancelled { return }
        页面好了 = false
        if 在测 { print("没开：\(地址.absoluteString) \(e.localizedDescription)") }
        let 状 = 数据.状况.isEmpty ? "小窗会自己在后台开；第一次会弹框问能不能读「文稿」，点「好」。" : 数据.状况
        let html = """
        <!doctype html><meta charset="utf-8"><body style="font:12.5px/1.6 -apple-system,'PingFang SC',sans-serif;color:#626a75;padding:26px 16px 10px;margin:0">
        <b style="color:#1f2328;font-size:13px">看板服务没开</b>
        <p style="margin:4px 0">\(状) 还不行就点：<button style="font:inherit;padding:1px 8px" onclick="webkit.messageHandlers.ban.postMessage({开服务:1})">用终端开</button></p>
        <p style="color:#9aa1ab;font-size:11.5px;margin:0">（\(地址.absoluteString)：\(e.localizedDescription)）</p></body>
        """
        网.loadHTMLString(html, baseURL: nil)
        if 窗.frame.height < 140 || 窗.frame.width < 400 { 改窗(层, max(400, 窗.frame.width), 140) }
        重试?.invalidate()
        重试 = Timer.scheduledTimer(withTimeInterval: 3, repeats: true) { [weak self] _ in
            guard let self else { return }
            self.服务.在吗 { ok in
                if ok {
                    self.重试?.invalidate()
                    self.重试 = nil
                    self.打开页面()
                }
            }
        }
    }

    @objc func 开服务() {
        let cmd = 任务目录.appendingPathComponent("打开无限表格.command")
        if FileManager.default.fileExists(atPath: cmd.path) {
            NSWorkspace.shared.open(cmd)
        } else {
            提示("找不到 \(cmd.path)")
        }
    }

    // ↗ 看原图原视频（target=_blank）、点到别的网站、「会话 ↗」（claude://）：交给系统打开
    func webView(_ w: WKWebView, createWebViewWith c: WKWebViewConfiguration, for a: WKNavigationAction, windowFeatures f: WKWindowFeatures) -> WKWebView? {
        if let u = a.request.url { NSWorkspace.shared.open(u) }
        return nil
    }

    func webView(_ w: WKWebView, decidePolicyFor a: WKNavigationAction, decisionHandler d: @escaping (WKNavigationActionPolicy) -> Void) {
        if let u = a.request.url {
            let 外 = !["http", "https", "about", "data", "blob"].contains(u.scheme ?? "")
            let 别站 = a.navigationType == .linkActivated && (u.host != 地址.host || u.port != 地址.port)
            if 外 || 别站 {
                NSWorkspace.shared.open(u)
                d(.cancel)
                return
            }
        }
        d(.allow)
    }

    func webView(_ w: WKWebView, runJavaScriptAlertPanelWithMessage m: String, initiatedByFrame f: WKFrameInfo, completionHandler done: @escaping () -> Void) {
        提示(m)
        done()
    }

    func webView(_ w: WKWebView, runJavaScriptConfirmPanelWithMessage m: String, initiatedByFrame f: WKFrameInfo, completionHandler done: @escaping (Bool) -> Void) {
        let a = NSAlert()
        a.messageText = m
        a.addButton(withTitle: "好")
        a.addButton(withTitle: "取消")
        done(a.runModal() == .alertFirstButtonReturn)
    }

    func 提示(_ m: String) {
        if 在测 { print("提示：\(m)"); return }
        let a = NSAlert()
        a.messageText = m
        a.runModal()
    }

    func 跑JS(_ js: String) {
        网.evaluateJavaScript(js, completionHandler: nil)
    }

    // ---------- 菜单：拷贝粘贴、撤销要靠菜单的快捷键才灵（菜单栏不显示） ----------

    func 菜单() {
        let 主 = NSMenu()
        func 加(_ 题: String, _ 项们: [NSMenuItem]) {
            let i = NSMenuItem()
            i.submenu = NSMenu(title: 题)
            项们.forEach { i.submenu!.addItem($0) }
            主.addItem(i)
        }
        func 项(_ t: String, _ a: Selector, _ k: String, _ m: NSEvent.ModifierFlags = .command) -> NSMenuItem {
            let i = NSMenuItem(title: t, action: a, keyEquivalent: k)
            i.keyEquivalentModifierMask = m
            return i
        }
        加("无限表格小窗", [项("退出", #selector(NSApplication.terminate(_:)), "q")])
        加("编辑", [项("撤销", Selector(("undo:")), "z"), 项("重做", Selector(("redo:")), "z", [.command, .shift]), .separator(),
                  项("剪切", #selector(NSText.cut(_:)), "x"), 项("拷贝", #selector(NSText.copy(_:)), "c"),
                  项("粘贴", #selector(NSText.paste(_:)), "v"), 项("全选", #selector(NSText.selectAll(_:)), "a")])
        let 刷 = 项("刷新", #selector(reloadPage), "r")
        刷.target = self
        let 终 = 项("用终端开服务", #selector(开服务), "")
        终.target = self
        let 重 = 项("重开看板服务", #selector(重开服务), "")
        重.target = self
        let 顶 = 项("置顶", #selector(切置顶), "")
        顶.target = self
        加("窗口", [项("关闭", #selector(NSWindow.performClose(_:)), "w"), 顶, 刷, 重, 终])
        NSApp.mainMenu = 主
    }

    @objc func reloadPage() { 网.reload() }

    // ---------- 自测 ----------

    func 走(_ 步: [[String: Any]], _ k: Int) {
        guard k < 步.count else { NSApp.terminate(nil); return }
        let s = 步[k]
        let 下 = { self.走(步, k + 1) }
        if let js = s["js"] as? String {
            网.callAsyncJavaScript(js, arguments: [:], in: nil, in: .page) { r in
                switch r {
                case .success(let v): print("js[\(k)] → \(self.成文(v))")
                case .failure(let e): print("js[\(k)] 出错：\(e)")
                }
                下()
            }
        } else if let t = s["等"] as? Double {
            DispatchQueue.main.asyncAfter(deadline: .now() + t) { 下() }
        } else if let n = s["层"] as? Int {
            跑JS("去层(\(n),1);")
            DispatchQueue.main.asyncAfter(deadline: .now() + 0.5) { 下() }
        } else if let b = s["按"] as? String {
            let 键: NSWindow.ButtonType = b == "缩" ? .miniaturizeButton : b == "放" ? .zoomButton : .closeButton
            if let 钮 = 窗.standardWindowButton(键) { 钮.performClick(nil) } else { print("按[\(k)]：没有这个键") }
            DispatchQueue.main.asyncAfter(deadline: .now() + 0.6) { 下() }
        } else if s["最小化"] != nil {   // 当成双击标题栏（系统设成最小化时）、⌘M
            窗.performMiniaturize(nil)
            DispatchQueue.main.asyncAfter(deadline: .now() + 0.6) { 下() }
        } else if let v = s["置顶"] as? Int {   // 自测：拨置顶开关（BAN_PIN 没设时才管用）
            if (v != 0) != 置顶 { 切置顶() }
            下()
        } else if s["收起"] != nil {
            收起()
            下()
        } else if s["拿出来"] != nil {
            拿出来()
            下()
        } else if s["重开"] != nil {
            重开服务()
            下()
        } else if let i = s["点行"] as? Int {
            跑JS("(()=>{const r=[...document.querySelectorAll('.r.row1')][\(i)];if(r)r.click();})();")
            DispatchQueue.main.asyncAfter(deadline: .now() + 0.6) { 下() }
        } else if let p = s["拍"] as? String {
            网.takeSnapshot(with: nil) { img, e in
                if let img, let tiff = img.tiffRepresentation, let rep = NSBitmapImageRep(data: tiff),
                   let png = rep.representation(using: .png, properties: [:]) {
                    try? png.write(to: URL(fileURLWithPath: p))
                    print("拍[\(k)] → \(p)")
                } else {
                    print("拍[\(k)] 失败：\(String(describing: e))")
                }
                下()
            }
        } else if s["报"] != nil {
            let f = 窗.frame
            let 钮 = { (t: NSWindow.ButtonType) -> String in
                guard let b = self.窗.standardWindowButton(t) else { return "没有" }
                let r = b.convert(b.bounds, to: nil)
                return (b.isEnabled ? "能点" : "灰") + "@\(Int(r.minX)),\(Int(f.height - r.maxY))"
            }
            print("报[\(k)] 层=\(层) 收起了=\(收起了) 图标=\(状态栏?.button?.image != nil) 提示=\(状态栏?.button?.toolTip ?? "") 页计=\(页计.map { "干\($0.干) 等\($0.等)" } ?? "没有") 连上=\(数据.连上了) 服务=\(服务.在跑 ? "自己起的 \(服务.进程号)" : "不是自己起的") 菜单栏图=\(Bundle.main.image(forResource: "menubar") != nil ? "新标志" : "系统表格")")
            let 内 = 窗.contentRect(forFrameRect: f).size
            print("   窗 \(Int(f.minX)),\(Int(f.minY)) \(Int(f.width))×\(Int(f.height))（内容 \(Int(内.width))×\(Int(内.height))） 左上=\(Int(f.minX)),\(Int(f.maxY)) 锚=\(Int(锚.x)),\(Int(锚.y)) 置顶=\(窗.level == .floating) 看得见=\(窗.isVisible) 标题=\(窗.titleVisibility == .visible ? "显示" : "藏") x=\(钮(.closeButton)) −=\(钮(.miniaturizeButton)) +=\(钮(.zoomButton))")
            下()
        } else {
            下()
        }
    }

    func 成文(_ v: Any?) -> String {
        guard let v else { return "null" }
        if JSONSerialization.isValidJSONObject(v), let d = try? JSONSerialization.data(withJSONObject: v),
           let s = String(data: d, encoding: .utf8) { return s }
        return "\(v)"
    }
}

setvbuf(stdout, nil, _IOLBF, 0)
let 应用 = NSApplication.shared
// 普通程序：程序坞里有图标、能 ⌘Tab（11-01 19:5x 用户要的）；收起时点程序坞图标也能拿出来。自测时不进程序坞，免得图标闪来闪去
应用.setActivationPolicy(ProcessInfo.processInfo.environment["BAN_TEST"] == nil ? .regular : .accessory)
let 控制 = 小窗控制()
应用.delegate = 控制
应用.run()
