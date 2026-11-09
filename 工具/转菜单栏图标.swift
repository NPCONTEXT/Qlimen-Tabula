// 用法：swiftc -O -o /tmp/转图 工具/转菜单栏图标.swift -framework AppKit && /tmp/转图 某个.svg 工具/小窗/（出 menubar.png、menubar@2x.png；再跑 工具/编译小窗.sh）
// 把标志的等粗小尺寸版 SVG 转成菜单栏用的模板图：黑色、透明底、18 和 36 像素（@2x）
import AppKit
let 源 = URL(fileURLWithPath: CommandLine.arguments[1])
guard let 图 = NSImage(contentsOf: 源) else { print("读不了 SVG"); exit(1) }
print("读到 SVG：\(图.size)")
for (边, 名) in [(18, "menubar.png"), (36, "menubar@2x.png")] {
    let rep = NSBitmapImageRep(bitmapDataPlanes: nil, pixelsWide: 边, pixelsHigh: 边, bitsPerSample: 8, samplesPerPixel: 4,
                               hasAlpha: true, isPlanar: false, colorSpaceName: .deviceRGB, bytesPerRow: 0, bitsPerPixel: 0)!
    NSGraphicsContext.saveGraphicsState()
    NSGraphicsContext.current = NSGraphicsContext(bitmapImageRep: rep)
    NSColor.clear.set(); NSRect(x: 0, y: 0, width: 边, height: 边).fill()
    图.draw(in: NSRect(x: 0, y: 0, width: 边, height: 边))
    // 只留形状：所有不透明的地方涂成纯黑（模板图只看透明度）
    NSColor.black.set(); NSRect(x: 0, y: 0, width: 边, height: 边).fill(using: .sourceIn)
    NSGraphicsContext.restoreGraphicsState()
    let out = URL(fileURLWithPath: CommandLine.arguments[2]).appendingPathComponent(名)
    try! rep.representation(using: .png, properties: [:])!.write(to: out)
    var 不透明 = 0
    for y in 0..<边 { for x in 0..<边 { if (rep.colorAt(x: x, y: y)?.alphaComponent ?? 0) > 0.5 { 不透明 += 1 } } }
    print("\(名)：\(边)×\(边)，不透明像素 \(不透明)")
}
