// 看板服务：小窗打开时没开，就在后台起一个（/usr/bin/python3 工具/板.py 服务 端口 --父 小窗的进程号），不弹终端；
// 小窗退出时关掉自己起的那个，小窗崩了服务也会在 5 秒内跟着退（板.py 的 --父）。双击 打开无限表格.command 起的那个照旧，小窗不碰它。
// 自己编的小窗每次重编都算新程序：它起的服务第一次读「文稿」会卡住等系统弹框，要点「好」（第一层底下一行会写）。

import Foundation

final class 看板服务 {
    let 地址: URL
    let 任务目录: URL
    private(set) var 起过 = false
    private(set) var 起于 = Date.distantPast
    private var 进程: Process?

    init(地址: URL, 任务目录: URL) {
        self.地址 = 地址
        self.任务目录 = 任务目录
    }

    /// 服务在不在：问一下 /api/版，1.5 秒没回就算不在
    func 在吗(_ 回: @escaping (Bool) -> Void) {
        var r = URLRequest(url: 地址.appendingPathComponent("api/版"))
        r.timeoutInterval = 1.5
        URLSession.shared.dataTask(with: r) { _, resp, _ in
            let ok = (resp as? HTTPURLResponse)?.statusCode == 200
            DispatchQueue.main.async { 回(ok) }
        }.resume()
    }

    func 起() {
        起过 = true
        起于 = Date()
        let 板 = 任务目录.appendingPathComponent("工具/板.py")
        let p = Process()
        p.executableURL = URL(fileURLWithPath: "/usr/bin/python3")
        p.arguments = [板.path, "服务", String(地址.port ?? 8770), "--父", String(ProcessInfo.processInfo.processIdentifier)]
        p.currentDirectoryURL = 任务目录
        // 日志放 ~/Library/Logs（不放文稿里：小窗自己碰文稿也可能弹框）
        let 日志 = FileManager.default.homeDirectoryForCurrentUser.appendingPathComponent("Library/Logs/无限表格小窗-服务.log")
        if !FileManager.default.fileExists(atPath: 日志.path) {
            FileManager.default.createFile(atPath: 日志.path, contents: nil)
        }
        if let h = try? FileHandle(forWritingTo: 日志) {
            h.seekToEndOfFile()
            p.standardOutput = h
            p.standardError = h
        }
        do {
            try p.run()
            进程 = p
        } catch {
            进程 = nil
        }
    }

    /// 自己起的那个还在不在（换版时被叫退了、崩了就是 false）
    var 在跑: Bool { 进程?.isRunning ?? false }
    /// 自己起的那个是不是被叫退的：退出码 0（「板.py 重开」、菜单「重开看板服务」、换版）；崩了、读不了文稿这类是非 0（卷二 7.41）
    var 好好退的: Bool {
        guard let p = 进程, !p.isRunning else { return false }
        return p.terminationStatus == 0
    }
    var 进程号: Int32 { 进程?.processIdentifier ?? 0 }

    /// 叫正在跑的服务退出（换版用；不管是不是自己起的）：退了以后 守服务 会用新代码再起一个
    func 请退(_ 完: @escaping () -> Void) {
        var r = URLRequest(url: 地址.appendingPathComponent("api/退出"))
        r.httpMethod = "POST"
        r.setValue("1", forHTTPHeaderField: "X-Ban")
        r.setValue("application/json", forHTTPHeaderField: "Content-Type")
        r.httpBody = Data("{}".utf8)
        r.timeoutInterval = 3
        URLSession.shared.dataTask(with: r) { _, _, _ in DispatchQueue.main.async { 完() } }.resume()
    }

    func 停() {
        if let p = 进程, p.isRunning {
            p.terminate()
        }
        进程 = nil
    }
}
