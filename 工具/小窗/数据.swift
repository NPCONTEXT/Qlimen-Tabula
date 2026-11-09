// 小窗自己读的看板数据：只用来守服务（连不上就起服务）、服务刚起来时去加载页面。
// 11-03 起（分卷三 5.4）：几处在干、几处等你由页面告诉小窗（{计:{干,等}}），小窗不再自己每 1.5 秒问版、每 6 秒读整份看板，
// 只每 10 秒问一次「版」看服务还在不在（页面和小窗以前各问一份，服务的开销翻倍）。
// 界面全在看板页面里（11-02 一层结构：三层是同一张格子表的三个镜头）；以前原生画的第一层（第一层.swift）11-02 起不用了，旧版在 归档/改前备份/第一层-1102-0340.swift。

import Foundation

struct 灯信息: Decodable {
    let 谁: String
    let 说: String?
    let 态: String?
    let 开始: Double?
    var 在干: Bool { 态 != "等" }
}

struct 任务信息: Decodable {
    let 键: String
    let 名: String
    let 灯: [灯信息]
    var 有在干的: Bool { 灯.contains { $0.在干 } }
}

struct 看板信息: Decodable {
    let 时间: String
    let 任务: [任务信息]
}

// ---------- 10 秒问一次 /api/版：只看服务在不在 ----------

final class 看板数据 {
    var 行们: [任务信息] = []   // 开着灯的任务：在干的在前，等你的在后
    var 连上了 = false
    var 状况 = "连看板服务……"
    var 连不上: (() -> Void)?
    var 连好了: (() -> Void)?   // 每次读到看板都叫一下（服务刚起来时，小窗靠它去加载页面）
    let 地址: URL
    private var 版 = ""
    private var 上次全读 = Date.distantPast
    private var 计时: Timer?

    init(地址: URL) {
        self.地址 = 地址
    }

    func 开始() {
        计时?.invalidate()
        计时 = Timer.scheduledTimer(withTimeInterval: 10, repeats: true) { [weak self] _ in self?.看一眼() }
        计时?.tolerance = 2
        看一眼()
    }

    func 看一眼() {
        取("api/版") { [weak self] 数 in
            guard let self else { return }
            guard let 数, let j = try? JSONSerialization.jsonObject(with: 数) as? [String: Any], let v = j["版"] as? String else {
                self.连上了 = false
                self.连不上?()
                return
            }
            self.版 = v
            self.连上了 = true
            self.状况 = ""
            self.连好了?()
        }
    }

    func 读看板() {
        取("api/看板") { [weak self] 数 in
            guard let self, let 数, let v = try? JSONDecoder().decode(看板信息.self, from: 数) else { return }
            self.上次全读 = Date()
            let 有灯 = v.任务.filter { !$0.灯.isEmpty }
            self.行们 = 有灯.filter { $0.有在干的 } + 有灯.filter { !$0.有在干的 }
            self.连上了 = true
            self.状况 = ""
            self.连好了?()
        }
    }

    private func 取(_ 路: String, _ 回: @escaping (Data?) -> Void) {
        var r = URLRequest(url: 地址.appendingPathComponent(路))
        r.timeoutInterval = 3
        r.cachePolicy = .reloadIgnoringLocalCacheData
        URLSession.shared.dataTask(with: r) { d, resp, _ in
            let ok = (resp as? HTTPURLResponse)?.statusCode == 200
            DispatchQueue.main.async { 回(ok ? d : nil) }
        }.resume()
    }
}
