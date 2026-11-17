---
name: slop-audit
description: Audit an existing app, website, landing page, UI flow or design system for the signs that make people read it as AI-generated ("AI slop", "vibe-coded look", "looks like every v0/Lovable/Claude site"), grade how obvious it is with evidence, and plan the fixes a human designer would make. Use when the user asks whether a design looks AI-made or generic, wants a slop check, design critique for sameness, a "why does this look templated" review, or a plan to make an existing UI feel human and specific. Covers code (React/Tailwind/CSS/SwiftUI), rendered pages and copy. Plans fixes; applies them only when asked. To design something new, use human-design instead.
---

# Slop audit

People spot AI-made design from a handful of unchosen defaults: the purple-to-blue gradient, a centered hero over three icon cards, rounded-2xl everything, filler copy, and, since models were told to avoid those, a second wave of "tasteful" defaults (cream paper, serif display, terracotta accent, ALL-CAPS eyebrows, `→` on every link). No single default proves anything. Several together, with nothing specific to the product, is what people read as slop.

This skill finds those defaults, shows where they are, says how obvious the whole thing is to a human, and writes the plan to replace them with choices.

Ground rules:
- Never accuse anyone of using AI. Report "unchosen defaults" and how a viewer would read them.
- The brief wins. A pattern the product deliberately chose (documented in DESIGN.md, a brand guide, or by the user) is not a finding, even if it is on the list.
- Combinations, not single hits. One gradient is a choice; a gradient + centered hero + icon tiles + filler copy is a template.
- Copy weighs heaviest. Good copy rescues a generic layout; nothing rescues filler copy.
- Evidence or it didn't happen: every finding cites a file:line or a screenshot.

## 1. Scope

Establish what is being audited and where it lives:
- **Surface**: landing page, whole app, specific flows (onboarding, checkout, settings, empty states), or the design system itself. Default to the main entry page plus the primary task flow.
- **Source**: repo path, live URL, screenshots, or a Figma/Claude Design export. More than one is better.
- **Audit what is deployed**: find the production URL (README, CLAUDE.md, deploy config). Check how far the local checkout is from the deployed branch (`git fetch` then `git rev-list --count HEAD..origin/main`); if it is behind, read the deployed code read-only (`git show origin/main:<path>`, or `git archive origin/main src | tar -x -C <tmp>`) instead of the stale checkout. Never edit or install in the audited repo.
- **Intent**: read DESIGN.md, PRODUCT.md, brand guides, README and recent design discussion. A documented choice is exempt only when the document gives a reason rooted in the subject ("cut corners because the product is about cards"). A choice that is documented but default-shaped ("the handoff's signature italic word") stays in the report under its own label, "documented but default-shaped", for the owner to decide.
- **Live vs dead code**: map routes to the components they render. Code behind a disabled feature flag or unused fallback is reported separately as a risk ("would ship if the flag flips"), not as part of the live verdict.

## 2. Static scan

Run the bundled scanner on the frontend source:

```bash
python3 ~/.claude/skills/slop-audit/scripts/slop_scan.py <dir-or-file> [more paths]   # markdown report
python3 ~/.claude/skills/slop-audit/scripts/slop_scan.py <path> --exclude ClassicHome.tsx --exclude admin --json
```

It is stdlib-only Python and covers 50+ tells across colour, type, layout, shape, effects, icons, motion, copy, Claude's own second-order defaults, design-system defaults and generator fingerprints. It reads fonts from next/font (Google and local), @font-face, Google Fonts URLs and CSS, and maps custom CSS classes (a `.kicker` with uppercase + tracking) to the tells they implement, counting their uses in markup. It reports a tier per surface (route or package) and repo-wide, with file:line evidence for every finding.

Judge public pages by their own surface rows: internal tools legitimately use dense uppercase labels and mono, and dead code inflates the repo-wide number. Treat every hit as a lead to confirm: open the cited lines and check intent. A clean scan is not a pass: the scanner only knows named clusters, so the rendered review still decides.

Optional second opinion, if the user allows running it: `npx impeccable detect <path-or-url> --json` (pbakaus/impeccable, 62 rules; pointed at a URL it also catches render-only problems such as contrast and tiny text). It downloads and runs third-party code, so ask first.

## 3. Rendered review (the real evidence)

Most tells only exist on screen. Open the deployed URL (or run the app locally if it needs no production secrets) and capture screenshots at 390px and 1440px, plus 768px for flows. The quickest route needs no npm:

```bash
python3 ~/.claude/skills/slop-audit/scripts/shoot.py <url-or-html-file> --out <dir> --widths 390,768,1440 --full --theme both
```

It drives headless Chrome over the DevTools protocol at true device widths (it warns if the page reports a different `innerWidth`), scrolls first so lazy images load, and writes `<slug>-<width>-<theme>-view.png` (first viewport, for the glance test) and `-full.png` (silhouette test; sections sized in `vh` may stretch, so use `--segments` for viewport-by-viewport captures on long or lazy pages). Use `--theme both` whenever the site follows the OS colour scheme. For pages behind a login or needing clicks, use Playwright already in the repo, Claude in Chrome, or the built-in browser. If none is available, ask for screenshots; failing that, list every visual check as **Unproven**. Never pass a visual check from class names alone.

Look at the screenshots, then run these tests and write down what each one shows:

1. **Glance (3 seconds)**: what would a designer say first? Name the first impression honestly ("generic SaaS", "looks like a Claude artifact", "specific and owned").
2. **Swap**: put a competitor's name and logo on the page. If it still works, the page has no point of view. Note which elements would survive the swap.
3. **Silhouette**: zoom out until text is unreadable. Is the section rhythm the stock waterfall (hero, logos, three cards, how-it-works, testimonials, pricing with a highlighted middle tier, FAQ, CTA band, four-column footer), every section the same height and padding?
4. **Same-prompt**: imagine the default output for "a landing page for a <category>". Count how many visible decisions match it.
5. **Copy read**: read every headline, subhead and CTA aloud. Flag filler words, invented proof, cadence tics ("No X. Just Y.", tricolons, em-dash chains), title-case stock CTAs and anything a competitor could say verbatim.
6. **Second-order check**: does it land on one of Claude's own clusters (references/tells.md, section 1)?

## 4. Flows and states (when flows are in scope)

Walk the primary task end to end at phone width. Check the screens AI kits get wrong: first-run/empty states (illustration + "Get started" instead of a real next step), loading, errors (vague, apologetic), settings (generic card stacks), dashboards (four KPI cards and a chart with no decision attached), onboarding (carousel of benefit slides). Check that the visual system holds across screens: different fonts, colours or button styles per page is design-system drift, a strong tell.

## 5. Design-system review (when the system is in scope)

Check the tokens, not just the pages: are there real tokens (colour roles, a type scale, spacing, radius, elevation) or raw utility classes? Is the shadcn/Tailwind theme untouched (`--radius: 0.5rem`/`0.625rem`, default `--primary`, `baseColor: zinc|slate`)? Does the type scale have real contrast (steps of at least 1.25x, more than one weight in use)? Do radius and elevation vary by role, or is one value applied everywhere? Are components themed or stock?

## 6. Grade

For each confirmed tell record: what it is, severity, evidence, and whether it looks chosen or default.

- **P0**: a layperson notices (purple gradient hero, gradient text, fake testimonials, emoji icons, untouched default kit).
- **P1**: a designer notices (eyebrow labels, icon tiles, cream + terracotta, Inter-only, three identical cards, `→` CTAs).
- **P2**: craft-level (transition-all, uniform section padding, soft shadow on everything).

Verdict, judged on the combination of **distinct** tells (not instances): **clean** (0–1 signals), **mild** (2–3), **noticeable** (4–6), **obvious** (7+), where a P2 counts half and any two P0s make it at least noticeable.

- Give a verdict per surface (home, flows, about, admin...) and one overall. Visible design-system drift (two or more different visual systems a visitor moves between) makes the overall verdict at least noticeable, whatever the individual pages score.
- Specificity credit: real, specific content (real products, prices, names, rules, photos) can lower a surface's verdict by one band, because people forgive a generic frame around obviously real content. It never removes the frame findings from the fix plan.
- Partial matches (a pill badge over a centered H1 without the two buttons) are graded one severity lower than the full pattern.

State the verdict as how a person would read the design, plus the three tells doing the most damage.

## 7. Fix plan

Order fixes by leverage, highest first:

1. **Direction**. If the verdict is noticeable or obvious, patching tells one by one only moves the design to the next default (ban purple and you get cream + terracotta). Recommend a new direction first: run the human-design skill's brief and direction steps, then re-skin from the new tokens.
2. **System tokens**: type family and scale, palette and roles, radius and elevation by role. One token change kills many tells at once.
3. **Structure**: re-order or cut sections by the decision the reader is making; replace card grids with the structure the content has (list, table, comparison, one large example).
4. **Copy**: rewrite headlines and CTAs in the product's own nouns and numbers; remove invented proof.
5. **Details**: motion, icons, hover effects, comments, placeholder links.

For every item give: what a human designer would do instead (concrete, not "make it unique"), files or screens touched, effort (S/M/L) and which findings it resolves. Use references/tells.md for per-tell fixes.

Apply fixes only when the user asks. When applying, re-run the scanner and re-take the screenshots, and show before/after evidence. Do not claim a visual fix from code alone.

## 8. Report

Use references/report-template.md. Lead with the verdict and the three most damaging tells. Bugs found along the way (contrast failures, clipped text, contradictory facts, broken states) go in "Other issues seen": visitors read them the same way as tells. If the report is for someone else (a client, a teammate), publish it as a page and include the screenshots.

## Files

- `scripts/slop_scan.py`: static scanner. `scripts/selftest.py` proves every rule can fire (run it after editing rules).
- `scripts/shoot.py`: headless-Chrome screenshots at several widths, no npm needed.
- `references/tells.md`: the catalogue: each tell, why people notice it, how to detect it, what to do instead, with sources.
- `references/report-template.md`: report structure.
