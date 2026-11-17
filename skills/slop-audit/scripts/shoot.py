#!/usr/bin/env python3
"""Screenshot a URL or local HTML file at true device widths with headless Chrome over the
DevTools protocol (no npm, no websockets: Chrome's --remote-debugging-pipe).

  python3 shoot.py <url-or-file> [--out DIR] [--name SLUG] [--widths 390,768,1440]
                   [--full] [--segments] [--theme light|dark|both] [--wait MS]

Per width it writes <slug>-<width>-view.png (first viewport, for the glance test) and, with
--full, <slug>-<width>-full.png (whole page after scrolling so lazy images load; sections sized
in vh can stretch in a full capture) or, with --segments, one PNG per viewport while scrolling.
It checks window.innerWidth matches the requested width and says so if it does not.
For pages behind a login or needing clicks, use Playwright or Claude in Chrome instead.
"""
import argparse
import base64
import fcntl
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time

CANDIDATES = [
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
    "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
    "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser",
]


def find_browser():
    for c in CANDIDATES:
        if os.path.exists(c):
            return c
    for name in ("google-chrome", "chromium", "chromium-browser", "chrome"):
        p = shutil.which(name)
        if p:
            return p
    return None


class CDP:
    def __init__(self, browser):
        self.profile = tempfile.mkdtemp(prefix="shoot-")
        cmd_r, self.cmd_w = os.pipe()
        self.res_r, res_w = os.pipe()

        def wire():
            a = fcntl.fcntl(cmd_r, fcntl.F_DUPFD, 100)
            b = fcntl.fcntl(res_w, fcntl.F_DUPFD, 100)
            os.dup2(a, 3)
            os.dup2(b, 4)

        self.proc = subprocess.Popen(
            [browser, "--headless=new", "--remote-debugging-pipe", "--no-first-run", "--no-default-browser-check",
             "--disable-gpu", "--hide-scrollbars", "--mute-audio", "--user-data-dir=" + self.profile, "about:blank"],
            preexec_fn=wire, close_fds=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        os.close(cmd_r)
        os.close(res_w)
        self.buf = b""
        self.next_id = 0
        self.events = []

    def _read_msg(self, timeout):
        deadline = time.time() + timeout
        while b"\0" not in self.buf:
            if time.time() > deadline:
                raise TimeoutError("no reply from Chrome")
            import select
            ready, _, _ = select.select([self.res_r], [], [], 0.5)
            if ready:
                chunk = os.read(self.res_r, 1 << 20)
                if not chunk:
                    raise RuntimeError("Chrome exited")
                self.buf += chunk
        msg, self.buf = self.buf.split(b"\0", 1)
        return json.loads(msg)

    def send(self, method, params=None, session=None, timeout=60):
        self.next_id += 1
        mid = self.next_id
        msg = {"id": mid, "method": method, "params": params or {}}
        if session:
            msg["sessionId"] = session
        os.write(self.cmd_w, json.dumps(msg).encode() + b"\0")
        while True:
            m = self._read_msg(timeout)
            if m.get("id") == mid:
                if "error" in m:
                    raise RuntimeError("%s: %s" % (method, m["error"].get("message")))
                return m.get("result", {})
            self.events.append(m)

    def wait_event(self, name, timeout):
        deadline = time.time() + timeout
        while time.time() < deadline:
            for i, e in enumerate(self.events):
                if e.get("method") == name:
                    self.events.pop(i)
                    return e
            try:
                self.events.append(self._read_msg(max(0.1, deadline - time.time())))
            except TimeoutError:
                break
        return None

    def close(self):
        try:
            self.send("Browser.close", timeout=5)
        except Exception:
            pass
        try:
            self.proc.wait(timeout=5)
        except Exception:
            self.proc.kill()
        shutil.rmtree(self.profile, ignore_errors=True)


SCROLL_JS = """(async () => {
  const h = () => document.documentElement.scrollHeight;
  for (let y = 0; y < h(); y += Math.max(200, innerHeight * 0.8)) {
    scrollTo(0, y); await new Promise(r => setTimeout(r, 200));
  }
  scrollTo(0, 0); await new Promise(r => setTimeout(r, 300));
  return h();
})()"""


def slug_for(target):
    s = re.sub(r"^https?://", "", target)
    s = re.sub(r"^file://", "", s)
    s = re.sub(r"[^A-Za-z0-9]+", "-", s).strip("-").lower()
    return s[-60:] or "page"


def shoot(cdp, url, width, theme, args, out, slug):
    height = 844 if width < 600 else 900
    target = cdp.send("Target.createTarget", {"url": "about:blank"})["targetId"]
    sess = cdp.send("Target.attachToTarget", {"targetId": target, "flatten": True})["sessionId"]
    cdp.send("Page.enable", session=sess)
    cdp.send("Emulation.setDeviceMetricsOverride", {"width": width, "height": height, "deviceScaleFactor": 1,
                                                     "mobile": width < 600}, session=sess)
    if theme:
        cdp.send("Emulation.setEmulatedMedia", {"features": [{"name": "prefers-color-scheme", "value": theme}]},
                 session=sess)
    cdp.send("Page.navigate", {"url": url}, session=sess)
    cdp.wait_event("Page.loadEventFired", 45)
    time.sleep(args.wait / 1000)
    inner = cdp.send("Runtime.evaluate", {"expression": "innerWidth", "returnByValue": True},
                     session=sess)["result"].get("value")
    suffix = "-" + theme if theme else ""
    paths = []

    def capture(name, clip=None, beyond=False):
        params = {"format": "png", "captureBeyondViewport": beyond}
        if clip:
            params["clip"] = dict(clip, scale=1)
        data = cdp.send("Page.captureScreenshot", params, session=sess, timeout=120)["data"]
        p = os.path.abspath(os.path.join(out, "%s-%d%s-%s.png" % (slug, width, suffix, name)))
        with open(p, "wb") as f:
            f.write(base64.b64decode(data))
        paths.append(p)

    capture("view")
    if args.full or args.segments:
        total = cdp.send("Runtime.evaluate", {"expression": SCROLL_JS, "awaitPromise": True, "returnByValue": True},
                         session=sess, timeout=180)["result"].get("value") or height
        time.sleep(0.5)
        if args.full:
            capture("full", {"x": 0, "y": 0, "width": width, "height": min(int(total), 16000)}, beyond=True)
        if args.segments:
            y, n = 0, 0
            while y < total and n < 30:
                cdp.send("Runtime.evaluate", {"expression": "scrollTo(0,%d)" % y}, session=sess)
                time.sleep(0.4)
                capture("seg%02d" % n)
                y += height
                n += 1
    cdp.send("Target.closeTarget", {"targetId": target})
    note = "" if inner == width else "  WARNING: page reports innerWidth=%s, not %d" % (inner, width)
    return paths, note


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("target")
    ap.add_argument("--out", default="./slop-shots")
    ap.add_argument("--name", help="filename slug (default: from the URL)")
    ap.add_argument("--widths", default="390,1440")
    ap.add_argument("--full", action="store_true", help="also capture the whole page")
    ap.add_argument("--segments", action="store_true", help="also capture one PNG per viewport while scrolling")
    ap.add_argument("--theme", choices=["light", "dark", "both"], help="force prefers-color-scheme")
    ap.add_argument("--wait", type=int, default=1500, help="ms to let the page settle after load")
    a = ap.parse_args()
    browser = find_browser()
    if not browser:
        sys.exit("No Chrome/Chromium found; use Playwright or Claude in Chrome for screenshots.")
    url = a.target
    if os.path.exists(url):
        url = "file://" + os.path.abspath(url)
    os.makedirs(a.out, exist_ok=True)
    slug = a.name or slug_for(a.target)
    themes = ["light", "dark"] if a.theme == "both" else [a.theme]
    cdp = CDP(browser)
    failed = False
    try:
        for theme in themes:
            for w in [int(x) for x in a.widths.split(",")]:
                try:
                    paths, note = shoot(cdp, url, w, theme, a, a.out, slug)
                    for p in paths:
                        print(p)
                    if note:
                        print(note)
                except Exception as e:
                    failed = True
                    print("FAILED at %dpx%s: %s" % (w, " (" + theme + ")" if theme else "", e))
    finally:
        cdp.close()
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
