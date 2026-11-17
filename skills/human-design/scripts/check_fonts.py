#!/usr/bin/env python3
"""Check that font families resolve on their foundry (Google Fonts or Fontshare).

  python3 check_fonts.py                         # every family in data/deck.json
  python3 check_fonts.py "Host Grotesk" "Literata"   # specific Google Fonts families
  python3 check_fonts.py "Zodiak" --fontshare        # specific Fontshare families
"""
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
deck = json.load(open(os.path.join(HERE, "..", "data", "deck.json")))
UA = {"User-Agent": "Mozilla/5.0 (Macintosh) font-check"}


def family(name):
    return re.sub(r"\s*\(.*\)$", "", name).strip()


def exists(name, src):
    if src == "google":
        url = "https://fonts.googleapis.com/css2?family=" + urllib.parse.quote(name).replace("%20", "+")
    else:
        url = "https://api.fontshare.com/v2/css?f[]=" + urllib.parse.quote(name.lower().replace(" ", "-")) + "@400"
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=15) as r:
            body = r.read().decode("utf-8", "ignore")
            return r.status == 200 and "@font-face" in body
    except urllib.error.HTTPError:
        return False


def main():
    """No arguments: check the whole deck. Otherwise: check_fonts.py "Family Name" [--fontshare]."""
    bad = []
    names = set()
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if args:
        src = "fontshare" if "--fontshare" in sys.argv else "google"
        names = {(family(a), src) for a in args}
    else:
        for t in deck["type"]:
            for k in ("display", "text", "mono"):
                if t.get(k):
                    names.add((family(t[k]), t["src"]))
    for name, src in sorted(names):
        ok = exists(name, src)
        print(("ok   " if ok else "MISS ") + "%-26s %s" % (name, src))
        if not ok:
            bad.append(name)
    print("\n%d families checked, %d missing" % (len(names), len(bad)))
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
