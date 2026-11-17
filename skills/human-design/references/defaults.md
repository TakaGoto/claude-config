# Defaults to recognise

These are not banned. They are what appears when nobody chose. If a direction lands on one, either the brief asked for it (fine, build it well) or it slipped in (replace it with a decision from the evidence board).

## First-order: the generated-SaaS kit

- Purple/indigo-to-blue gradients; gradient text; violet accent; glow shadows; blurred blobs behind the hero.
- Inter, Geist or the system stack as the only face; giant bold tight-tracked hero headline.
- Centered hero (pill badge, H1, subhead, two buttons) followed by three icon-topped feature cards.
- The section waterfall: logos, features, how-it-works, testimonials, stats, three-tier pricing with a "Most Popular" middle, FAQ, CTA band, four-column footer.
- rounded-2xl and shadow-lg on everything; glassmorphism; gradient borders; dot/grid backgrounds.
- Lucide glyphs in tinted rounded squares; emoji bullets; sparkles for "AI".
- Fade-up-on-scroll on every section; hover-scale on every card; number tickers; marquees.
- Copy: seamless, elevate, unlock, empower, "the future of", invented user counts, testimonials from people who do not exist.
- Dashboards: four KPI cards and a line chart, unrelated to any decision.

## Second-order: where models go when told "not that"

From Anthropic's own frontend-design skill (it lists these as what generated design clusters around now):

1. Warm cream ground (~#F4F1EA), high-contrast serif display, terracotta/clay accent (~#D97757, Anthropic's own accent colour).
2. Near-black (#0B0B0B/#111 standing in for black) with one acid-green or vermilion accent.
3. Broadsheet layout: hairline rules, zero radius, dense newspaper columns.
4. The card kit: content chopped into identical rounded cards, one radius regardless of hierarchy, the same soft grey shadow, gradient washes.
5. Template chrome: tracked ALL-CAPS eyebrow above every heading; meta strings joined with middle dots; "WORD — fragment" labels; monospace for small labels; `→` appended to links and buttons.

Also: one word of the headline in italic serif or a different colour; 01/02/03 markers on content that is not a sequence; emerald as the "escape" accent; the "tasteful free font" cluster (Space Grotesk, Instrument Serif, Fraunces, Plus Jakarta Sans, Syne, DM Sans, Satoshi).

## Third-order: watch for your own drift

Already seen when a model is steered away from both lists above:
- crimson, oxblood or burgundy on a cream ground: the cream + terracotta cluster one hue step over;
- the quiet "tasteful B2B" page: off-white or warm-grey ground, a single grotesk, one deep warm accent, hairline-ruled tables, large numerals in a left column beside a heading and body. Each part is reasonable; together, with nothing from the subject, it is the next default.

The deck and history file exist because the next cluster forms wherever many outputs are steered the same way. If several recent projects share a family, a palette strategy or a layout, that is drift even if each looked fine alone. Check `deal.py --history` before choosing.

## Escape moves that actually work

- Pull a choice from the subject's physical world and name it after the source ("felt green from the playmat", "pairings-sheet grid").
- Let content dictate structure: a table when the content is tabular, a list when it is a list, one big example instead of three small cards.
- Spend boldness once: one memorable element, everything around it quiet.
- Use real material: screenshots, photos, data, names. Placeholders are the strongest tell of all.
- Write copy a competitor could not reuse unchanged.
