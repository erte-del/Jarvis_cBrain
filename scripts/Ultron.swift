// Ultron.app: Ultron in the menu bar. Opening it starts Ultron and opens the page;
// the orb's menu opens the page again or quits (which stops Ultron).
// Built by scripts/make_app.sh, which writes the project folder into Info.plist (UltronRoot).
import AppKit

final class App: NSObject, NSApplicationDelegate {
    let root = Bundle.main.object(forInfoDictionaryKey: "UltronRoot") as! String
    let page = URL(string: "http://127.0.0.1:8000")!
    var item: NSStatusItem!

    func applicationDidFinishLaunching(_ note: Notification) {
        item = NSStatusBar.system.statusItem(withLength: NSStatusItem.squareLength)
        item.button?.image = orb()
        item.button?.toolTip = "Ultron"
        let menu = NSMenu()
        menu.addItem(withTitle: "Open Ultron", action: #selector(openPage), keyEquivalent: "o").target = self
        menu.addItem(.separator())
        menu.addItem(withTitle: "Quit Ultron", action: #selector(NSApplication.terminate(_:)), keyEquivalent: "q")
        item.menu = menu

        DispatchQueue.global().async {  // start_ultron.sh can take up to 30 seconds
            let (ok, message) = self.run("start_ultron.sh")
            guard !ok else { return }
            DispatchQueue.main.async {
                NSApp.activate(ignoringOtherApps: true)
                let alert = NSAlert()
                alert.messageText = "Ultron couldn't start"
                alert.informativeText = message
                alert.alertStyle = .warning
                alert.runModal()
                NSApp.terminate(nil)
            }
        }
    }

    // Opening Ultron.app again while it runs just opens the page again.
    func applicationShouldHandleReopen(_ sender: NSApplication, hasVisibleWindows: Bool) -> Bool {
        openPage()
        return false
    }

    func applicationWillTerminate(_ note: Notification) {
        run("stop_ultron.sh")
    }

    @objc func openPage() {
        NSWorkspace.shared.open(page)
    }

    /// Runs one of our scripts and returns whether it worked, and what it said on stderr.
    @discardableResult
    func run(_ script: String) -> (Bool, String) {
        let p = Process()
        p.executableURL = URL(fileURLWithPath: "\(root)/scripts/\(script)")
        let err = Pipe()
        p.standardError = err
        p.standardOutput = FileHandle.nullDevice
        do { try p.run() } catch { return (false, error.localizedDescription) }
        let data = err.fileHandleForReading.readDataToEndOfFile()
        p.waitUntilExit()
        return (p.terminationStatus == 0, String(decoding: data, as: UTF8.self))
    }

    /// The orb from the page header as a menu bar symbol: a ring around a dot. A template
    /// image, so macOS draws it white or black to match the menu bar.
    func orb() -> NSImage {
        let img = NSImage(size: NSSize(width: 18, height: 18), flipped: false) { r in
            NSColor.black.set()
            let ring = NSBezierPath(ovalIn: r.insetBy(dx: 1.5, dy: 1.5))
            ring.lineWidth = 1.5
            ring.stroke()
            NSBezierPath(ovalIn: r.insetBy(dx: 5, dy: 5)).fill()
            return true
        }
        img.isTemplate = true
        return img
    }
}

let app = NSApplication.shared
let delegate = App()
app.delegate = delegate
app.run()
