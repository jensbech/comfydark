import Cocoa
import WebKit

let defaultURL = "http://127.0.0.1:1234/"
let appURL = ProcessInfo.processInfo.environment["COMFYDARK_URL"] ?? defaultURL

class AppDelegate: NSObject, NSApplicationDelegate, WKNavigationDelegate, WKUIDelegate {
    var window: NSWindow!
    var webView: WKWebView!

    func applicationDidFinishLaunching(_ notification: Notification) {
        setupMenu()

        let config = WKWebViewConfiguration()
        config.preferences.setValue(true, forKey: "developerExtrasEnabled")

        webView = WKWebView(frame: .zero, configuration: config)
        webView.navigationDelegate = self
        webView.uiDelegate = self
        webView.allowsBackForwardNavigationGestures = true
        webView.allowsMagnification = true
        webView.autoresizingMask = [.width, .height]
        webView.setValue(false, forKey: "drawsBackground")

        let frame = NSRect(x: 0, y: 0, width: 1200, height: 800)
        window = NSWindow(
            contentRect: frame,
            styleMask: [.titled, .closable, .miniaturizable, .resizable],
            backing: .buffered,
            defer: false
        )
        window.title = "Comfydark"
        window.contentView = webView
        webView.frame = window.contentView!.bounds
        window.setFrameAutosaveName("ComfydarkMainWindow")
        window.center()
        window.makeKeyAndOrderFront(nil)
        window.makeFirstResponder(webView)

        if let url = URL(string: appURL) {
            webView.load(URLRequest(url: url))
        }

        NSApp.setActivationPolicy(.regular)
        NSApp.activate(ignoringOtherApps: true)
    }

    func applicationShouldTerminateAfterLastWindowClosed(_ sender: NSApplication) -> Bool {
        return true
    }

    @objc func reloadPage(_ sender: Any?) {
        webView.reloadFromOrigin()
    }

    @objc func goBack(_ sender: Any?) {
        if webView.canGoBack { webView.goBack() }
    }

    @objc func goForward(_ sender: Any?) {
        if webView.canGoForward { webView.goForward() }
    }

    @objc func goHome(_ sender: Any?) {
        if let url = URL(string: appURL) {
            webView.load(URLRequest(url: url))
        }
    }

    @objc func openDevTools(_ sender: Any?) {
        webView.perform(NSSelectorFromString("_inspectorShow:"), with: nil)
    }

    func webView(_ webView: WKWebView, didFailProvisionalNavigation navigation: WKNavigation!, withError error: Error) {
        let nsErr = error as NSError
        guard nsErr.domain != "WebKitErrorDomain" || nsErr.code != 102 else { return }
        let html = """
        <!doctype html>
        <html><head><meta charset="utf-8"><title>Comfydark</title>
        <style>
          body { background:#161b22; color:#e6edf3; font:-apple-system-body, sans-serif;
                 display:flex; flex-direction:column; align-items:center; justify-content:center;
                 height:100vh; margin:0; gap:1rem; }
          h1 { font-weight:600; font-size:1.2rem; }
          p { color:#9aa6b2; max-width:42ch; text-align:center; }
          code { background:#0d1117; padding:.1em .35em; border-radius:4px; color:#9cdcfe; }
          button { background:#1f6feb; color:white; border:0; padding:.5rem 1rem;
                   border-radius:6px; font:inherit; cursor:pointer; }
        </style></head>
        <body>
          <h1>Can't reach \(appURL)</h1>
          <p>The opencode proxy isn't responding. Check that <code>opencode-proxy</code>
             and the upstream opencode server are running, then retry.</p>
          <button onclick="location.href='\(appURL)'">Retry</button>
        </body></html>
        """
        webView.loadHTMLString(html, baseURL: nil)
    }

    func setupMenu() {
        let mainMenu = NSMenu()

        let appMenuItem = NSMenuItem()
        let appMenu = NSMenu()
        appMenu.addItem(withTitle: "About Comfydark",
                        action: #selector(NSApplication.orderFrontStandardAboutPanel(_:)),
                        keyEquivalent: "")
        appMenu.addItem(NSMenuItem.separator())
        appMenu.addItem(withTitle: "Hide Comfydark",
                        action: #selector(NSApplication.hide(_:)),
                        keyEquivalent: "h")
        let hideOthers = appMenu.addItem(withTitle: "Hide Others",
                                         action: #selector(NSApplication.hideOtherApplications(_:)),
                                         keyEquivalent: "h")
        hideOthers.keyEquivalentModifierMask = [.command, .option]
        appMenu.addItem(withTitle: "Show All",
                        action: #selector(NSApplication.unhideAllApplications(_:)),
                        keyEquivalent: "")
        appMenu.addItem(NSMenuItem.separator())
        appMenu.addItem(withTitle: "Quit Comfydark",
                        action: #selector(NSApplication.terminate(_:)),
                        keyEquivalent: "q")
        appMenuItem.submenu = appMenu

        let editMenuItem = NSMenuItem()
        let editMenu = NSMenu(title: "Edit")
        editMenu.addItem(withTitle: "Undo", action: Selector(("undo:")), keyEquivalent: "z")
        editMenu.addItem(withTitle: "Redo", action: Selector(("redo:")), keyEquivalent: "Z")
        editMenu.addItem(NSMenuItem.separator())
        editMenu.addItem(withTitle: "Cut", action: #selector(NSText.cut(_:)), keyEquivalent: "x")
        editMenu.addItem(withTitle: "Copy", action: #selector(NSText.copy(_:)), keyEquivalent: "c")
        editMenu.addItem(withTitle: "Paste", action: #selector(NSText.paste(_:)), keyEquivalent: "v")
        editMenu.addItem(withTitle: "Select All", action: #selector(NSText.selectAll(_:)), keyEquivalent: "a")
        editMenuItem.submenu = editMenu

        let viewMenuItem = NSMenuItem()
        let viewMenu = NSMenu(title: "View")
        viewMenu.addItem(withTitle: "Reload", action: #selector(reloadPage(_:)), keyEquivalent: "r")
        viewMenu.addItem(withTitle: "Home", action: #selector(goHome(_:)), keyEquivalent: "H")
        viewMenu.addItem(NSMenuItem.separator())
        let fs = viewMenu.addItem(withTitle: "Enter Full Screen",
                                  action: #selector(NSWindow.toggleFullScreen(_:)),
                                  keyEquivalent: "f")
        fs.keyEquivalentModifierMask = [.control, .command]
        let devTools = viewMenu.addItem(withTitle: "Toggle Developer Tools",
                                        action: #selector(openDevTools(_:)),
                                        keyEquivalent: "i")
        devTools.keyEquivalentModifierMask = [.command, .option]
        viewMenuItem.submenu = viewMenu

        let histMenuItem = NSMenuItem()
        let histMenu = NSMenu(title: "History")
        histMenu.addItem(withTitle: "Back", action: #selector(goBack(_:)), keyEquivalent: "[")
        histMenu.addItem(withTitle: "Forward", action: #selector(goForward(_:)), keyEquivalent: "]")
        histMenuItem.submenu = histMenu

        let winMenuItem = NSMenuItem()
        let winMenu = NSMenu(title: "Window")
        winMenu.addItem(withTitle: "Minimize",
                        action: #selector(NSWindow.performMiniaturize(_:)),
                        keyEquivalent: "m")
        winMenu.addItem(withTitle: "Zoom",
                        action: #selector(NSWindow.performZoom(_:)),
                        keyEquivalent: "")
        winMenuItem.submenu = winMenu
        NSApp.windowsMenu = winMenu

        mainMenu.addItem(appMenuItem)
        mainMenu.addItem(editMenuItem)
        mainMenu.addItem(viewMenuItem)
        mainMenu.addItem(histMenuItem)
        mainMenu.addItem(winMenuItem)
        NSApp.mainMenu = mainMenu
    }
}

let app = NSApplication.shared
let delegate = AppDelegate()
app.delegate = delegate
app.run()
