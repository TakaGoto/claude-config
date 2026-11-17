---
name: human-design
description: Design and build app or web UI (landing pages, full apps, UI flows, design systems, redesigns, iOS/SwiftUI screens) that reads as the work of a human designer with a point of view instead of AI-generated. Use whenever the user asks to design, redesign, restyle or build a new interface and cares how it looks, says "make it not look AI", "less generic", "more distinctive", "avoid the Claude look", wants several design directions, or brings a Claude Design handoff bundle to implement. Grounds the design in the subject's real world, deals divergent directions from a curated deck so the model cannot fall back on its defaults, writes tokens before components, and gates the result with the slop-audit scanner and a screenshot critique. To judge an existing design, use slop-audit.
---

# Human design

Models converge. With no direction they produce the centre of their training data (purple gradient, centered hero, three icon cards, Inter). Told to avoid that, they move to the next centre: cream paper, serif display, terracotta accent, tracked ALL-CAPS eyebrows, `→` on every link. Claude Design has the same pull. Adjectives like "distinctive" or "bold" only move the design from one default to another.

What works is replacing taste-by-adjective with **decisions made outside the model's habits**: evidence from the subject's real world, choices dealt from a curated deck, tokens written down before any component, and a gate that measures the result. This skill is that process.

## 0. Start from what exists

- If the product already has a design system (DESIGN.md, tokens, a component library, brand guide), work inside it. Only run the direction steps (3–5) when the user asks for a new direction or slop-audit recommended one.
- **Claude Design bundle**: if the user designed in Claude Design and exported a handoff bundle, treat it as the source of truth for layout and tokens, but still run step 4 (default check) on it, since Claude Design converges on the same clusters. Claude Design can also extract a design system from an existing repo, Figma file or live URL; suggest that when the user has a brand elsewhere.
- **Brand kits**: DESIGN.md files from real products (VoltAgent/awesome-design-md, getdesign.md, or UXKIN `find_ui_materials` if connected) are valid starting points when the user picks one. Use them as a base to diverge from, never as the final look, and never copy a brand's logo, name or illustrations.

## 1. Brief

Write a short brief before any visual decision. If facts are missing, ask once; otherwise propose them and say they are assumptions.

- **Subject**: what the product is, in the user's world's own words (not "a platform").
- **Audience** and the **one primary job** they come to do.
- **Context of use**: device, place, time, mood (a judge's tablet at a noisy card shop on Friday night is a design brief by itself).
- **Real content inventory**: the actual names, numbers, screens, prices and photos available. Design with these. No lorem ipsum, invented stats, fake testimonials or placeholder avatars. Note which assets really exist (photos, an illustrator, real product screens, physical artefacts to scan, a named person who would sign a letter); step 3 needs this.
- **Constraints**: platform, accessibility, brand assets, what must not change.
- **Pre-launch products**: sample data is fine when it is labelled as sample, but anything a mock screen implies (a sort order, a report, an integration) is a feature claim. List every such claim as an assumption for the user to confirm.

Save it in the project as PRODUCT.md (or the top of DESIGN.md).

## 2. Evidence board

Collect 4–6 references and write one line each: the one concrete thing you will borrow, and what you will not. Draw from, in this order:

1. **The subject's physical world**: its objects, materials, signage, printed matter, uniforms, tools (for a TCG app: card frames, pairings sheets taped to a wall, binder pages, playmats, shop chalkboards). This is where specific, non-generic choices come from.
2. **Real products in the category**: UXKIN `find_ui_references` / `find_ui_materials`, Mobbin or Refero MCP when connected and signed in (all need an account), or screenshots the user supplies (Dribbble, Awwwards, Pinterest). Without those, search the web for 2–3 real products in the category and screenshot their live sites with `python3 ~/.claude/skills/slop-audit/scripts/shoot.py <url> --out <dir>`, so the evidence is real rather than remembered. Borrow rhythm, density and attitude; never copy layouts or branding. Label any reference you could not look at as "from memory, unverified".
3. **Out-of-category inspiration** that shares the subject's attitude (a sports scoreboard for a competitive app, a field guide for a collector's app).

Never use AI-generated design galleries as references; they are the distribution you are trying to leave.

## 3. Deal directions

Deal three divergent seeds:

```bash
python3 ~/.claude/skills/human-design/scripts/deal.py --brief "<subject, audience and tone in plain words>" --count 3 \
    --have <photos,illustrator,signer,screens,artefacts: only what really exists>
# also: --mode light|dark  --lock axis=id (keep)  --exclude axis=id (reject)  --seed N  --json  --history
```

Each seed fixes eight axes: type pairing, palette strategy, starting hue, layout archetype, shape language, density, motion and imagery. The deck (data/deck.json) leaves out the overused faces and the default clusters. It maps the brief's words to tags through a synonym list and prints which words matched; if few matched, add plain subject and tone words. It drops entries that clash with the brief's tone (no arcade fonts for "premium, calm") or need assets you did not list in `--have`, and it avoids anything recorded for recent projects (history.jsonl), so separate projects stop sharing one house style.

Turn each seed into a direction for this brief:
- a name and a one-sentence idea tied to the evidence board;
- palette: 4–6 named hex values with roles (ground, ink, muted, accent, plus status colours if needed), derived from the evidence and the seed's strategy and hue;
- type: families and roles, plus a scale with real contrast (steps ≥1.25x, at least two weights doing different jobs);
- an ASCII wireframe of the key screen;
- the **one bold thing** (spend boldness in exactly one place).

If an axis still fights the brief, redeal just that axis: `--count 1`, `--lock` the axes you keep and `--exclude axis=<id>` the one you reject. Don't silently swap in your own default. Directions must differ on at least three axes.

## 4. Default check

Before showing anything, test each direction against references/defaults.md:
- does any part match a first-order default (SaaS kit) or a second-order default (Claude's clusters)?
- **same-prompt test**: imagine the default answer to "design a <category> app". Does this direction land anywhere near it?
- **swap test**: would the direction still work with a competitor's name on it? If yes, it lacks a point of view; pull more from the evidence board.

Revise what fails and note what you changed and why. The brief's own words win: if the user asks for a cream editorial look, build it well rather than avoiding it.

Avoiding the listed tells because you just read the list is suppression, not a direction; with nothing else pushing, the design settles into the nearest unlisted default (an off-white page, one grotesk, one deep warm accent, hairline tables). For each direction, name at least one decision that came from the evidence board and could not have come from the defaults list.

## 5. Choose

If the user is around, show the three directions side by side (token swatches, type specimens and the ASCII wireframes, or a quick static HTML mock of the key screen for each). Parallel variants beat sequential edits of one design. If the user is away, pick the one that best fits the brief and evidence, and say why in one sentence. Record the choice:

```bash
python3 ~/.claude/skills/human-design/scripts/deal.py --record type=<id>,palette=<id>,layout=<id>,shape=<id> --project <name>
```

The record goes to `~/.claude/skills/human-design/history.jsonl` (shared by every project on this machine). Skip it for throwaway experiments.

## 6. Tokens before components

Write DESIGN.md (template: references/design-md-template.md, Google's DESIGN.md format) with the tokens, the rules, the do's and don'ts and the one bold thing. Then implement the tokens in code before building any component: CSS custom properties or the Tailwind theme, or a SwiftUI theme for iOS. Replace framework defaults (the shadcn theme, `--radius`, default Tailwind colours). Verify every font exists: `python3 ~/.claude/skills/human-design/scripts/check_fonts.py "Family Name"` (add `--fontshare` for Fontshare families).

## 7. Build

Follow references/craft.md: type, colour, layout, shape, motion, imagery, copy and states. Write real copy in the product's nouns. Design every state (empty, loading, error, long content, small screens). Build to an accessibility floor without fuss: 4.5:1 text contrast, visible focus, reduced motion respected, 44px touch targets.

## 8. Gate

1. Static: `python3 ~/.claude/skills/slop-audit/scripts/slop_scan.py <src>`. Target: tier clean or mild, no P0 finding. Every remaining finding is either fixed or explicitly chosen (note it in DESIGN.md). A clean scan is necessary, not sufficient: the scanner only knows named clusters.
2. Rendered: screenshot the key screens at 390px and 1440px (plus 768px for flows): `python3 ~/.claude/skills/slop-audit/scripts/shoot.py <url-or-html-file> --out <dir> --full`, or Playwright / Claude in Chrome for flows that need clicks. Look at every image. Critique problems first, praise never: run slop-audit's glance, swap, silhouette and copy-read tests on your own screenshots.
3. At most two fix rounds, then report. Say what was checked in a browser and what is unproven.

A final polish pass (spacing rhythm, motion timing, micro-copy) is fine, but it comes after the gate passes, not instead of it.

## Files

- `scripts/deal.py`: deals direction seeds; `--record` and `--history` keep the cross-project memory.
- `scripts/check_fonts.py`: confirms deck families (or the ones you name) exist on Google Fonts or Fontshare.
- `data/deck.json`: the curated deck (44 type pairings, 12 palette strategies, 14 layout archetypes, plus shape, density, motion, imagery and hue), with tags, tone clashes, asset requirements and the brief-word synonym list. Add entries when you find good ones; run check_fonts.py after.
- `references/defaults.md`: what convergence looks like and what to do instead.
- `references/craft.md`: the practices that make a design read as made by a person.
- `references/design-md-template.md`: DESIGN.md skeleton.
