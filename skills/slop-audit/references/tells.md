# Tells catalogue

Each tell: what it is · severity (P0 layperson notices, P1 designer notices, P2 craft) · detection (S static scan, R rendered screenshot, J judgement/copy read) · what a designer does instead. Scanner rule ids are in `code font`.

Why these exist: with no direction a model samples the centre of its training data ("distributional convergence", Anthropic, 2025). Told to avoid that centre, it moves to the next cluster rather than making a choice. So the catalogue has two layers: the original SaaS defaults and the second-order "tasteful" defaults.

## 1. Second-order defaults (Claude's own clusters)

These come from Anthropic's current frontend-design skill, which lists them as what generated design clusters around now. They look designed, which is why they get past people who only know the purple-gradient tell.

| Tell | Sev | Detect | Instead |
|---|---|---|---|
| Warm cream ground (~#F4F1EA) + serif display + terracotta/clay accent (~#D97757, Anthropic's own accent) `claude-warm-house-style` `terracotta-accent` `cream-serif` | P1 | S R | Take the ground and accent from the subject's world (its materials, its signage, its photos). Cream is fine when the subject is paper; say so. |
| Near-black (#0B0B0B, #111) + one acid-green or vermilion accent `dark-acid-house-style` | P1 | S R | If dark is right, build a dark palette on a hue (forest, oxblood, navy) with more than one tone. |
| Broadsheet cosplay: hairline rules, zero radius, dense newspaper columns on a non-news product | P2 | R J | Use editorial structure only for editorial content. |
| Template chrome: tracked ALL-CAPS eyebrow above every heading `eyebrow-caps`; meta joined with middle dots `middle-dot-meta`; "WORD — fragment" labels; mono for small labels `mono-labels`; `→` stapled to links `arrow-cta` | P1 | S | Delete eyebrows that carry no information; sentence case; plain labels; mono only for code and IDs. |
| One word of the headline accented (italic serif, colour, gradient) `headline-word-accent` | P1 | S R | One voice for the headline; let size and face carry it. |
| 01 / 02 / 03 markers on content that is not a sequence `numbered-markers` | P2 | S J | Number only real steps. |
| Fake window chrome (traffic-light dots) around mock screenshots `fake-window-chrome` | P2 | S R | A real screenshot, honestly cropped, or the live product. |
| Emerald as the "not purple" accent | P2 | R | Accent from the subject. |
| Crimson, oxblood or burgundy standing in for terracotta on a cream ground `claude-warm-house-style` | P1 | S R | Same as the cream + terracotta row: it is the same cluster one hue step over. |
| The quiet "tasteful B2B" page: off-white/grey ground, one grotesk, one deep warm accent, hairline tables, big numerals in a left column beside heading + body | P2 | R J | Fine when the content is genuinely tabular; otherwise it is the next default. Push one axis (colour, layout or type) from the subject's world. |
| Section headings written as slogans ending in a period ("Ten games, one wall.", "Come sit down.") `slogan-headings` | P1 | S J | Plain labels built from the product's nouns and numbers. |

## 2. Colour

| Tell | Sev | Detect | Instead |
|---|---|---|---|
| Purple/indigo-to-blue (or pink) gradient in hero, CTA or glow `purple-blue-gradient` | P0 | S R | One brand hue, solid. A gradient only if the brand owns one. |
| Gradient text on headlines or metrics `gradient-text` | P0 | S R | Solid ink; emphasis through size/weight. |
| Indigo/violet as the accent by default `violet-accent` `violet-hex` | P1 | S | Accent derived from the domain, defined once as a token. |
| Dark mode nobody asked for, zinc-950 + white/10 borders `default-dark-saas` | P1 | S R J | Choose light or dark for the product and its context of use. |
| Coloured glow shadows / neon halos `glow-shadow` | P1 | S R | Neutral, low-alpha elevation; borders first. |
| Gradient washes and radial halos everywhere `gradient-washes` | P2 | S R | Flat surfaces; one intentional moment at most. |
| Timid evenly distributed palette (five colours at equal weight) | P1 | R | Dominant ground, one supporting tone, one sharp accent (roughly 60/30/10). |
| Grey body text below AA contrast | P1 | R | 4.5:1 for body, 3:1 for large text. |

## 3. Typography

| Tell | Sev | Detect | Instead |
|---|---|---|---|
| Inter / Geist / system stack as the only face `default-typeface` | P0 | S | A family chosen for this subject; roles named in tokens. Native iOS SF Pro for UI text is fine; it is the platform. |
| The "tasteful free font" cluster: Space Grotesk, Instrument Serif, Fraunces, Plus Jakarta Sans, Syne, DM Sans, Satoshi, JetBrains Mono `overused-typeface` | P2 | S | Fine if chosen; otherwise pick outside the list (human-design's deck). |
| Flat hierarchy: steps under 1.25x, one weight | P2 | R | A real scale with contrast; at least two weights doing different jobs. |
| Giant bold tight-tracked hero headline `hero-display-size` | P2 | S R | Size from the scale for this face and line length. |
| Oversized italic serif as the hero | P1 | R | Only when the subject is literary or editorial. |

## 4. Layout and structure

| Tell | Sev | Detect | Instead |
|---|---|---|---|
| Centered hero: pill badge, centered H1, subhead, two CTAs | P0 | R | Open with the most characteristic thing in the subject's world: the product working, a real number, a real photo. |
| Three (or six) identical icon-topped feature cards `three-card-grid` `icon-tile` | P0 | S R | Structure from content: a list, a comparison table, one large worked example plus small notes. |
| The section waterfall: hero, logos, features, how-it-works, testimonials, stats, pricing, FAQ, CTA band, 4-column footer `stock-landing-order` | P1 | S R | Order sections by the decision the reader is making; cut the ones that exist out of habit. |
| Pricing as three tiers with a highlighted "Most Popular" middle `most-popular-tier` | P1 | S R | Price the way the product is bought. |
| Pill badge above the hero headline `pill-badge-hero` | P2 | S R | Remove, or make it a plain sentence if it carries news. |
| Every section in the same container and padding `same-container` `same-section-padding` | P2 | S R | Vary measure by content; tight groups, breaks where the story turns. |
| Dashboard = four KPI cards + chart `kpi-four-up` | P1 | S R | Lead with the number the user acts on; context and comparison beside it. |
| Cards inside cards; everything wrapped in a card | P2 | R | Spacing and type separate content; cards only for movable/selectable objects. |
| Missing states: empty, loading, error, focus `no-focus-states` | P1 | S R | Design each state; an empty state says the next step. |
| Design-system drift between pages | P0 | R | One token set; audit every page against it. |

## 5. Shape, effects, motion

| Tell | Sev | Detect | Instead |
|---|---|---|---|
| rounded-2xl + shadow-lg on everything `rounded-everything` `soft-shadow-stack` `one-radius` | P1 | S R | Radius and elevation by role. |
| Thick coloured left/top border on rounded cards `side-border-accent` | P1 | S R | Remove; signal category with a label or position. |
| Glassmorphism by reflex `glassmorphism` | P1 | S R | Opaque surface + border; glass only where the platform uses it. |
| Blurred colour blobs behind the hero `blur-blobs` | P0 | S R | Delete. |
| Gradient border wrappers `gradient-border` | P2 | S | Solid 1px border. |
| Decorative grid / dot-matrix backgrounds `grid-dot-background` | P2 | S R | Only when the grid means something. |
| Stock effect components (Magic UI / Aceternity: number ticker, marquee, beams, meteors, spotlight) `effect-library` | P1 | S R | Cut; design one moment specific to the product. |
| Fade-and-slide-up on every section `fade-up-everything`; hover-scale on every card `hover-lift` | P1 | S R | One orchestrated moment; hover feedback only on things that act. |
| transition-all everywhere `transition-all`; bounce/elastic easing `bounce-easing`; pulsing "live" dots `decorative-pulse` | P2 | S | Animate specific properties with exponential ease-out; animate status only when real. |

## 6. Icons and imagery

| Tell | Sev | Detect | Instead |
|---|---|---|---|
| Emoji as icons or bullets (🚀 ✨ 🎯) `emoji-icons` | P0 | S | One icon set at one weight, or none. |
| Sparkles/wand icon for "AI" or "new" `sparkles-icon` | P1 | S | Name and show the capability. |
| The stock Lucide feature glyphs (Zap, Rocket, Shield, BarChart3, CheckCircle2) `stock-icon-set` | P2 | S | Icons only where they aid recognition. |
| Placeholder avatars and photos (pravatar, DiceBear, picsum) `placeholder-imagery` | P0 | S | Real photos with consent, initials, or nothing. |
| Glossy 3D blobs, AI headshots, SVG scenes assembled from primitive shapes | P0 | R | Real screenshots or photography of the subject; or commission one illustration style. |
| `aspect-video bg-muted` box standing in for a product shot | P1 | R | Show the product. |

## 7. Copy

| Tell | Sev | Detect | Instead |
|---|---|---|---|
| Filler: seamless, elevate, unlock, empower, streamline, supercharge, cutting-edge, world-class, "the future of", "whether you're" `marketing-filler` | P1 | S J | Say what it does: a number, a domain noun, an example. Test: could a competitor use this headline unchanged? |
| Invented proof: "Trusted by 10,000+ teams", 99.9%, 4.9/5, logo walls, testimonials from "Sarah Chen, CEO at Acme" `fake-social-proof` | P0 | S J | Real, verifiable claims with names, or cut the section. |
| Cadence tics: "No X. Just Y.", "Faster. Smarter. Simpler.", "Not X. It's Y.", calling things "theater" `aphoristic-cadence` | P1 | S J | Plain declarative sentences. |
| Em-dash saturation `em-dash-copy` | P1 | S J | Periods and commas. |
| Title Case stock CTAs: Get Started, Learn More, Start Free Trial `title-case-cta` | P2 | S | Verb + this product's object, sentence case; same verb in the confirmation. |
| Leftovers: lorem ipsum, `href="#"` `dead-links`, template name in the footer, default meta/OG image, "SAMPLE"-watermarked product images, unformatted phone numbers, facts that contradict each other between pages | P1 | S R | Finish it or remove it. |

## 8. Code-level tells (visible to developers and reviewers)

| Tell | Sev | Detect | Instead |
|---|---|---|---|
| Untouched shadcn/ui theme, default `--radius` `shadcn-default-theme` | P0 | S | The project's own tokens; theme the primitives. |
| Narrating comments `{/* Hero Section */}` `section-comments` | P2 | S | Components named after their content. |
| Generator fingerprints (lovable-tagger, gpt-engineer, v0 meta) `generator-fingerprint` | info | S | Not a design flaw; tells you which defaults to look for. |
| Magic numbers off the scale (`text-[17px]`, `p-[13px]`), class strings over 200 characters | P2 | S | Tokens and a spacing scale. |

## Severity calibration notes

- Commenters most often name overall sameness ("they all look the same") ahead of any single feature. Among features, shadcn/Tailwind defaults, purple and gradients lead; bento grids, glassmorphism and aurora backgrounds are over-blamed (JCarterJohnson/vibecoded-design-tells, from 3.2M Reddit posts).
- On 1,590 Show HN sites, 22% hit 4+ patterns and 46% hit 0–1, with a 5–10% false-positive rate for the detector (Krebs, 2026). Expect false positives; confirm by looking.
- Spacing is the softest signal; never lead an audit with it.
- A default is not proof. Bootstrap and Material sites looked alike too. Frame findings as unchosen defaults.

## Sources

- Anthropic frontend-design skill (installed plugin, v1.1.1) and blog "Improving frontend design through Skills", 2025-11-12.
- pbakaus/impeccable: `antipatterns.json` (62 rules) and `npx impeccable detect`.
- funboy322/avoid-ai-design: `references/ai-tells-catalog.md` (P0/P1/P2 + detection mode).
- Adrian Krebs, "Scoring Show HN submissions for AI design patterns", 2026-04-20.
- JCarterJohnson/vibecoded-design-tells (Reddit-mined ranking).
- pixelslop `ai-slop-patterns.md` (scoring bands); Sailop "AI Slop in 2026" (section waterfall, silhouette test, copy as critical).
- VectorLab anti-slop checklist and UXKIN no-ui-slop (installed skills).
