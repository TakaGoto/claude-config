#!/usr/bin/env python3
"""Self-test for slop_scan.py: every rule must fire on the sloppy fixture, none on the clean one."""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import slop_scan  # noqa: E402

# Rules that cannot be exercised by a single small fixture (need a whole repo's worth of signal).
NOT_IN_FIXTURE = {"generator-fingerprint", "no-focus-states", "one-radius", "terracotta-accent",
                  "cream-serif", "overused-typeface"}

sloppy = slop_scan.scan(os.path.join(HERE, "fixtures", "sloppy"), include_tests=True)
defaults = slop_scan.scan(os.path.join(HERE, "fixtures", "sloppy-defaults"), include_tests=True)
clean = slop_scan.scan(os.path.join(HERE, "fixtures", "clean"), include_tests=True)

fired = {f["id"] for f in sloppy["findings"]} | {f["id"] for f in defaults["findings"]}
expected = {r["id"] for r in slop_scan.RULES} | {
    "emoji-icons", "default-typeface", "stock-icon-set", "stock-landing-order",
    "shadcn-default-theme", "claude-warm-house-style", "violet-hex", "dark-acid-house-style"}
missing = sorted(expected - NOT_IN_FIXTURE - fired)
false_pos = sorted(f["id"] for f in clean["findings"])

ok = True
if missing:
    ok = False
    print("FAIL: rules that did not fire on the sloppy fixture:", ", ".join(missing))
if false_pos:
    ok = False
    print("FAIL: rules that fired on the clean fixture:", ", ".join(false_pos))
if sloppy["tier"] != "obvious":
    ok = False
    print("FAIL: sloppy fixture tier is %s, expected obvious" % sloppy["tier"])
if clean["tier"] != "clean":
    ok = False
    print("FAIL: clean fixture tier is %s, expected clean" % clean["tier"])
classmap = slop_scan.scan(os.path.join(HERE, "fixtures", "class-map"), include_tests=True)
cm = {f["id"]: f for f in classmap["findings"]}
if "eyebrow-caps" not in cm or cm["eyebrow-caps"]["count"] < 4:
    ok = False
    print("FAIL: CSS-class eyebrow (.kicker) uses not counted: %s" % cm.get("eyebrow-caps", {}).get("count"))
if "hover-lift" not in cm:
    ok = False
    print("FAIL: CSS-class hover lift (.lift:hover) not detected")
if any(".label" in loc[2] for f in classmap["findings"] for loc in f["locations"]):
    ok = False
    print("FAIL: plain uppercase without tracking (.label) was flagged as an eyebrow")
if "space grotesk" not in classmap["fonts"]:
    ok = False
    print("FAIL: next/font/local family not detected: %s" % classmap["fonts"])
dark = slop_scan.scan(os.path.join(HERE, "fixtures", "dark-coral"), include_tests=True)
dk = {f["id"] for f in dark["findings"]}
for need in ("eyebrow-caps", "slogan-headings", "default-typeface", "dark-warm-house-style"):
    if need not in dk:
        ok = False
        print("FAIL: dark-coral fixture (CSS-in-TS page) missed %s; got %s" % (need, sorted(dk)))
print("sloppy: %d findings, tier %s | clean: %d findings, tier %s" % (
    len(sloppy["findings"]), sloppy["tier"], len(clean["findings"]), clean["tier"]))
print("PASS" if ok else "FAILED")
sys.exit(0 if ok else 1)
