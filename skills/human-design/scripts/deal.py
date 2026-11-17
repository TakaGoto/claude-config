#!/usr/bin/env python3
"""Deal divergent design-direction seeds so the model starts from choices it did not default to.

  python3 deal.py --brief "premium calm tournament software for tcg organizers" [--count 3]
                  [--mode light|dark] [--have photos,screens] [--lock type=plex-serif-sans]
                  [--exclude type=bungee-barlow] [--seed 7] [--json]
  python3 deal.py --record type=bricolage-literata,palette=signage,layout=index-list --project tablepop
  python3 deal.py --history

Brief words are mapped to deck tags (with synonyms), entries that clash with the brief or need
assets you do not have (--have photos,illustrator,signer,screens,artefacts) are left out, the
rest are sampled without replacement so the directions differ, and choices recorded for recent
projects (history.jsonl next to this skill) are avoided so projects stop sharing one house style.
"""
import argparse
import json
import os
import random
import re
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
DECK = os.path.join(HERE, "..", "data", "deck.json")
HISTORY = os.path.join(HERE, "..", "history.jsonl")
AXES = ["type", "palette", "hue", "layout", "shape", "density", "motion", "imagery"]
ASSETS = {"photos", "illustrator", "signer", "screens", "artefacts"}


def load_history():
    if not os.path.exists(HISTORY):
        return []
    with open(HISTORY) as f:
        return [json.loads(l) for l in f if l.strip()]


def brief_tags(text, deck):
    words = set(re.findall(r"[a-z]+", (text or "").lower()))
    tags, matched = set(), {}
    vocab = {t for axis in AXES for o in deck[axis] for t in o.get("tags", [])}
    for w in sorted(words):
        found = set(deck.get("synonyms", {}).get(w, []))
        if w in vocab:
            found.add(w)
        if found:
            matched[w] = sorted(found)
            tags |= found
    return tags, matched


def eligible(o, tags, have, excluded):
    if o["id"] in excluded:
        return False, "excluded"
    if o.get("requires") and o["requires"] not in have:
        return False, "needs " + o["requires"]
    if tags & set(o.get("clash", [])):
        return False, "clashes with brief"
    if o.get("only") and not (tags & set(o["only"])):
        return False, "only for " + "/".join(o["only"])
    return True, ""


def deal(deck, tags, count, mode, locks, excludes, have, rng, avoid_recent):
    history = load_history()[-avoid_recent:] if avoid_recent else []
    directions = [dict() for _ in range(count)]
    notes = []
    for axis in AXES:
        if axis in locks:
            match = [o for o in deck[axis] if o["id"] == locks[axis]]
            if not match:
                sys.exit("unknown %s id: %s (ids: %s)" % (axis, locks[axis], ", ".join(o["id"] for o in deck[axis])))
            for d in directions:
                d[axis] = match[0]
            continue
        opts, dropped = [], []
        for o in deck[axis]:
            ok, why = eligible(o, tags, have, excludes.get(axis, set()))
            (opts.append(o) if ok else dropped.append("%s (%s)" % (o["id"], why)))
        if axis == "palette" and mode in ("light", "dark"):
            opts = [o for o in opts if o.get("mode") in (mode, "either")] or opts
        recent = {h.get(axis) for h in history}
        opts = [o for o in opts if o["id"] not in recent] or opts
        if not opts:
            sys.exit("no %s options left after filters; loosen --exclude/--have" % axis)
        scores = {o["id"]: len(tags & set(o.get("tags", []))) for o in opts}
        if tags and len([o for o in opts if scores[o["id"]] > 0]) >= count:
            opts = [o for o in opts if scores[o["id"]] > 0]
        weights = [1 + 3 * scores[o["id"]] for o in opts]
        chosen = []
        while len(chosen) < count:
            avail = [(o, w) for o, w in zip(opts, weights) if o not in chosen] or list(zip(opts, weights))
            chosen.append(rng.choices([o for o, _ in avail], weights=[w for _, w in avail])[0])
        for d, c in zip(directions, chosen):
            d[axis] = c
        if dropped and axis != "hue":
            notes.append("%s left out: %s" % (axis, ", ".join(dropped)))
    return directions, notes


def render(directions, notes, brief, matched):
    out = ["# Direction seeds", "", "Brief: %s" % (brief or "(none given)"),
           "Matched words: %s" % (", ".join("%s -> %s" % (w, "/".join(t)) for w, t in matched.items())
                                  or "none (dealt from the full deck; add subject/tone words, see deck.json synonyms)"), ""]
    for i, d in enumerate(directions, 1):
        t = d["type"]
        out.append("## Seed %s" % "ABCDEF"[i - 1])
        out.append("- Type: %s for display, %s for text%s (%s) [%s]" % (
            t["display"], t["text"], ", %s for code/data" % t["mono"] if t.get("mono") else "", t["src"], t["id"]))
        out.append("- Palette: %s [%s]" % (d["palette"]["recipe"], d["palette"]["id"]))
        out.append("- Hue to start the accent search: %s (%s deg)" % (d["hue"]["id"], d["hue"]["range"]))
        for axis in ("layout", "shape", "density", "motion", "imagery"):
            out.append("- %s: %s [%s]" % (axis.capitalize(), d[axis]["recipe"], d[axis]["id"]))
        out.append("")
    if notes:
        out += ["Filtered by the brief and --have:"] + ["- " + n for n in notes] + [""]
    out.append("Seeds are starting points. To change one axis of one seed: --count 1 with --lock on the axes "
               "you keep and --exclude axis=<id> on the one you reject. Record the final choice with --record.")
    return "\n".join(out)


def parse_pairs(items):
    out = {}
    for it in items:
        for kv in it.split(","):
            if "=" in kv:
                k, v = kv.split("=", 1)
                out.setdefault(k.strip(), set()).add(v.strip())
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--brief", default="")
    ap.add_argument("--count", type=int, default=3)
    ap.add_argument("--mode", choices=["light", "dark", "any"], default="any")
    ap.add_argument("--have", default="", help="assets you really have: " + ",".join(sorted(ASSETS)))
    ap.add_argument("--lock", action="append", default=[], help="axis=id, repeatable")
    ap.add_argument("--exclude", action="append", default=[], help="axis=id, repeatable")
    ap.add_argument("--seed", type=int)
    ap.add_argument("--avoid-recent", type=int, default=8)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--record", help="axis=id,axis=id of the direction you chose")
    ap.add_argument("--project", default="")
    ap.add_argument("--history", action="store_true")
    a = ap.parse_args()

    if a.history:
        for h in load_history():
            print(json.dumps(h))
        return
    if a.record:
        entry = {k: sorted(v)[0] for k, v in parse_pairs([a.record]).items()}
        entry.update(project=a.project, at=time.strftime("%Y-%m-%d"))
        with open(HISTORY, "a") as f:
            f.write(json.dumps(entry) + "\n")
        print("recorded to %s: %s" % (os.path.abspath(HISTORY), json.dumps(entry)))
        return
    deck = json.load(open(DECK))
    tags, matched = brief_tags(a.brief, deck)
    have = {x.strip() for x in a.have.split(",") if x.strip()}
    unknown = have - ASSETS
    if unknown:
        sys.exit("unknown --have values: %s (use %s)" % (", ".join(sorted(unknown)), ", ".join(sorted(ASSETS))))
    locks = {k: sorted(v)[0] for k, v in parse_pairs(a.lock).items()}
    rng = random.Random(a.seed if a.seed is not None else time.time_ns())
    directions, notes = deal(deck, tags, max(1, min(a.count, 6)), a.mode, locks, parse_pairs(a.exclude),
                             have, rng, a.avoid_recent)
    if a.json:
        print(json.dumps(dict(brief=a.brief, matched=matched, directions=directions, notes=notes), indent=2))
    else:
        print(render(directions, notes, a.brief, matched))


if __name__ == "__main__":
    main()
