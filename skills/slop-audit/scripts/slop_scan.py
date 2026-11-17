#!/usr/bin/env python3
"""Static scan of a frontend codebase for design tells that read as AI-generated.

Usage:
  python3 slop_scan.py [PATH ...] [--exclude GLOB ...] [--json] [--max-locations N] [--include-tests]

PATH may be a directory or a single file. A triage signal, not a verdict: every rule here is
legitimate in some brief. Combinations matter more than any single hit, and the rendered review
decides. Severity: P0 a layperson notices, P1 a designer notices, P2 craft-level
(weight 3 / 2 / 1). Results are also given per surface (route or package) so dead code and
internal tools do not decide the verdict for the public pages.
"""
import argparse
import colorsys
import fnmatch
import json
import os
import re
import sys
from collections import Counter, defaultdict

SKIP_DIRS = {
    "node_modules", ".next", "dist", "build", "out", ".git", "coverage", ".turbo",
    ".expo", "ios", "android", "vendor", ".vercel", ".open-next", ".wrangler",
    "storybook-static", ".svelte-kit", ".nuxt", ".output", "Pods", "DerivedData",
    "__snapshots__", "target", "worktrees",
}
CODE_EXT = {".tsx", ".jsx", ".ts", ".js", ".mjs", ".vue", ".svelte", ".astro", ".swift"}
STYLE_EXT = {".css", ".scss", ".sass", ".less"}
TEXT_EXT = {".html", ".mdx"}
ALL_EXT = CODE_EXT | STYLE_EXT | TEXT_EXT
TEST_RE = re.compile(r"(\.test\.|\.spec\.|/__tests__/|/e2e/|/tests?/|\.stories\.|/fixtures?/|/mocks?/)")
LOG_RE = re.compile(r"console\.|logger\.|\blog\(|throw |Error\(|\.warn\(|\.error\(")

# where: cls = non-comment code line, text = user-facing copy only, any = any line,
# block = whole-file multi-line regex
RULES = [
    # ---------------- colour
    dict(id="purple-blue-gradient", cat="colour", w=3, min=1, where="cls",
         rx=r"from-(purple|violet|indigo|fuchsia)-\d{2,3}\b[^\"'`]*\bto-(blue|cyan|indigo|purple|violet|pink|fuchsia)-\d{2,3}"
            r"|from-(blue|pink)-\d{2,3}\b[^\"'`]*\bto-(purple|violet|indigo)-\d{2,3}"
            r"|linear-gradient\([^)]*(#6366f1|#8b5cf6|#7c3aed|#a855f7|#9333ea|#4f46e5)[^)]*(#3b82f6|#06b6d4|#ec4899|#8b5cf6|#6366f1|#a855f7)"
            r"|LinearGradient\([^)]*\.(purple|indigo)[^)]*\.(blue|pink|cyan)",
         tell="Purple/indigo-to-blue/pink gradient: the most recognised AI-SaaS colour move.",
         fix="One hue from the subject's world, used solid. A gradient only if the brand owns one."),
    dict(id="gradient-text", cat="colour", w=3, min=1, where="cls",
         rx=r"bg-clip-text[^\"'`]*text-transparent|text-transparent[^\"'`]*bg-clip-text|background-clip:\s*text|-webkit-text-fill-color:\s*transparent",
         tell="Gradient-filled headline or metric text.",
         fix="Solid ink; carry emphasis with size, weight or the typeface itself."),
    dict(id="violet-accent", cat="colour", w=2, min=6, where="cls",
         rx=r"\b(bg|text|border|ring|from|to|via|fill|stroke)-(indigo|violet|purple)-(400|500|600|700)\b",
         tell="Tailwind indigo/violet as the brand accent (the default 'AI purple').",
         fix="Accent from the product's domain, defined once as a token."),
    dict(id="gradient-washes", cat="colour", w=1, min=6, where="cls",
         rx=r"\bbg-(gradient|linear)-to-(r|l|t|b|br|bl|tr|tl)\b|\bbg-radial\b|radial-gradient\(",
         tell="Gradient washes and radial halos used as decoration on many surfaces.",
         fix="Flat surfaces; at most one intentional gradient moment."),
    dict(id="default-dark-saas", cat="colour", w=1, min=6, where="cls",
         rx=r"\bbg-(zinc|neutral|slate|gray)-950\b|\bborder-white/(5|10)\b",
         tell="Default dark SaaS kit (zinc-950 canvas, white/10 hairlines).",
         fix="Decide light or dark for this product; if dark, build its own dark palette."),
    # ---------------- effects
    dict(id="glow-shadow", cat="effects", w=2, min=1, where="cls",
         rx=r"shadow-(purple|indigo|violet|blue|cyan|pink|fuchsia|emerald|sky)-\d{2,3}(/\d+)?|box-shadow:\s*0(px)?\s+0(px)?\s+\d{2,}px\s+(rgba?\((?!0,\s*0,\s*0)|#)",
         tell="Coloured glow shadows (neon halo).",
         fix="Border-first elevation; neutral low-alpha shadow only where something floats."),
    dict(id="blur-blobs", cat="effects", w=3, min=1, where="cls",
         rx=r"(absolute[^\"'`]*rounded-full[^\"'`]*blur-(2xl|3xl|\[\d{2,}px\])|blur-(2xl|3xl|\[\d{2,}px\])[^\"'`]*rounded-full[^\"'`]*absolute)"
            r"|(?<![-\w])filter:\s*blur\(([4-9]\d|\d{3,})px\)",
         tell="Blurred colour blobs floating behind the hero.",
         fix="Delete; use a real image, the product itself, or nothing."),
    dict(id="glassmorphism", cat="effects", w=2, min=3, where="cls",
         rx=r"\bbackdrop-blur(-\w+)?\b|backdrop-filter:\s*blur",
         tell="Frosted-glass panels used by reflex.",
         fix="Opaque surface + 1px border; glass only where the platform itself uses it."),
    dict(id="gradient-border", cat="effects", w=2, min=1, where="cls",
         rx=r"\b(p-px|p-\[1px\]|p-\[2px\]|p-0\.5)\b[^\"'`]*bg-(gradient|linear)-to|bg-(gradient|linear)-to[^\"'`]*\b(p-px|p-\[1px\]|p-\[2px\]|p-0\.5)\b",
         tell="Gradient border wrapper (1px-padding gradient trick).",
         fix="1px solid border from the token set."),
    dict(id="grid-dot-background", cat="effects", w=1, min=1, where="cls",
         rx=r"bg-\[linear-gradient\(to_right|bg-\[radial-gradient\([^)]*1px|\b(DotPattern|GridPattern|RetroGrid|FlickeringGrid)\b",
         tell="Decorative hairline grid / dot-matrix background.",
         fix="Remove unless the grid means something (graph paper for a drafting tool, say)."),
    dict(id="effect-library", cat="effects", w=2, min=1, where="cls",
         rx=r"<(NumberTicker|Marquee|Meteors|BorderBeam|ShimmerButton|BackgroundBeams|AuroraBackground|TextGenerateEffect|TypewriterEffect|Spotlight|SparklesCore|BentoGrid|AnimatedBeam|Particles|WordRotate|BlurFade|MagicCard|ShineBorder)\b|components/(magicui|aceternity)",
         tell="Stock effect-library components (Magic UI / Aceternity: ticker, marquee, beams, meteors).",
         fix="Cut them; if motion is needed, design one moment specific to this product."),
    # ---------------- shape
    dict(id="rounded-everything", cat="shape", w=2, min=10, where="cls",
         rx=r"\brounded-(2xl|3xl|\[(1[6-9]|2\d|3\d)px\])\b|\.cornerRadius\((1[6-9]|2\d|3\d)\)|cornerRadius:\s*(1[6-9]|2\d|3\d)",
         tell="Large radius on everything (the rounded-2xl kit).",
         fix="A radius scale tied to hierarchy: controls, cards and containers differ."),
    dict(id="soft-shadow-stack", cat="shape", w=1, min=8, where="cls",
         rx=r"\b(hover:)?shadow-(lg|xl|2xl)\b|\.shadow\(radius:\s*\d{2}",
         tell="Soft drop shadow under every card.",
         fix="Elevation only where something truly floats; borders or spacing elsewhere."),
    dict(id="side-border-accent", cat="shape", w=2, min=2, where="cls",
         rx=r"\bborder-(l|t|s)-(4|\[3px\]|\[4px\]|\[5px\])\b[^\"'`]*\bborder-(l|t|s)?-?[a-z]+-\d{3}|\bborder-(l|t|s)-[a-z]+-\d{3}\b[^\"'`]*\bborder-(l|t|s)-(4|\[3px\]|\[4px\])\b|border-left:\s*[3-6]px solid",
         tell="Thick coloured left/top border on rounded cards.",
         fix="Remove; signal category with a label, a column or position."),
    dict(id="fake-window-chrome", cat="shape", w=2, min=1, where="block",
         rx=r"bg-(red|rose)-[345]00(?:(?!bg-(red|rose)-).){0,320}?bg-(yellow|amber)-[345]00.{0,320}?bg-(green|emerald)-[345]00"
            r"|#ff5f5[67].{0,200}?#(febc2e|ffbd2e).{0,200}?#(28c840|27c93f)",
         tell="Fake macOS traffic-light window chrome around a mock screenshot.",
         fix="Show a real screenshot cropped honestly, or the live product."),
    # ---------------- icons & imagery
    dict(id="icon-tile", cat="icons", w=2, min=2, where="cls",
         rx=r"^(?=.*\brounded-(lg|xl|2xl|full)\b)(?=.*\bbg-([a-z]+-(50|100|500/(10|15|20)|600/10)|primary/(5|10|15|20))(?![\w/-]))(?=.*(\bjustify-center\b|\b(h|w|size)-(8|9|10|11|12|14)\b))",
         tell="Icon in a pastel tinted tile above every card title.",
         fix="Drop the tiles: a domain image, a real screenshot, a number, or nothing."),
    dict(id="sparkles-icon", cat="icons", w=2, min=1, where="cls",
         rx=r"\bSparkles(Icon)?\b|systemName:\s*\"sparkles\"|\bWandSparkles\b",
         tell="Sparkles/magic-wand icon standing for 'AI' or 'new'.",
         fix="Name the actual capability and show it."),
    dict(id="placeholder-imagery", cat="icons", w=2, min=1, where="cls",
         rx=r"pravatar\.cc|dicebear|ui-avatars\.com|randomuser\.me|picsum\.photos|placehold\.co|via\.placeholder|placeholder\.com|unsplash\.it",
         tell="Placeholder avatars/photos (pravatar, DiceBear, picsum).",
         fix="Real photos with consent, initials, or no avatar."),
    # ---------------- motion
    dict(id="hover-lift", cat="motion", w=2, min=3, where="cls",
         rx=r"hover:(scale-1(0[2-9]|10)|-translate-y-(0\.5|1|2))\b",
         tell="Every card scales or lifts on hover.",
         fix="Hover feedback only on things that act; keep it to colour or underline."),
    dict(id="transition-all", cat="motion", w=1, min=5, where="cls",
         rx=r"\btransition-all\b|transition:\s*all\b",
         tell="transition-all sprinkled everywhere.",
         fix="Animate specific properties with motion tokens."),
    dict(id="fade-up-everything", cat="motion", w=2, min=3, where="cls",
         rx=r"initial=\{\{\s*opacity:\s*0,\s*y:\s*\d+|whileInView=|data-aos=|animate-(fade|slide)-(in|up)",
         tell="Fade-and-slide-up entrance on each section.",
         fix="One orchestrated moment at most; everything else simply appears."),
    dict(id="decorative-pulse", cat="motion", w=1, min=1, where="cls",
         rx=r"animate-ping|animate-pulse[^\"'`]*rounded-full[^\"'`]*\b(h|w|size)-(1\.5|2|2\.5|3)\b|rounded-full[^\"'`]*\b(h|w|size)-(1\.5|2|2\.5|3)\b[^\"'`]*animate-pulse|animate-bounce",
         tell="Pulsing 'live' dots or bouncing elements as decoration.",
         fix="Animate status only when it is real and changing."),
    dict(id="bounce-easing", cat="motion", w=1, min=1, where="cls",
         rx=r"cubic-bezier\(\s*[\d.]+\s*,\s*(-[\d.]+|1\.0*[1-9]\d*)\s*,|cubic-bezier\(\s*[\d.]+\s*,\s*-?[\d.]+\s*,\s*[\d.]+\s*,\s*(-[\d.]+|1\.0*[1-9]\d*)\s*\)"
            r"|bounce:\s*0\.[3-9]|ease-out-back|easeOutBack|\belastic\b",
         tell="Bounce/elastic easing.",
         fix="Exponential ease-out; things decelerate, they don't wobble."),
    # ---------------- layout
    dict(id="three-card-grid", cat="layout", w=2, min=2, where="cls",
         rx=r"\b(sm|md|lg):grid-cols-3\b",
         tell="Repeated 3-up grids (confirm on screen they are identical feature cards).",
         fix="Let content set structure: a list, a comparison, one big example, a table."),
    dict(id="kpi-four-up", cat="layout", w=1, min=2, where="cls",
         rx=r"\b(md|lg|xl):grid-cols-4\b",
         tell="Four-up grids (a KPI-card row is the tell; product grids are fine; confirm on screen).",
         fix="Lead with the number the user acts on; the rest in context."),
    dict(id="same-container", cat="layout", w=1, min=6, where="cls",
         rx=r"\bmax-w-7xl\b[^\"'`]*\bmx-auto\b|\bmx-auto\b[^\"'`]*\bmax-w-7xl\b",
         tell="Every section in the same max-w-7xl mx-auto container.",
         fix="Vary measure by content: narrow for reading, full-bleed for showing."),
    dict(id="same-section-padding", cat="layout", w=1, min=6, where="cls",
         rx=r"\bpy-(20|24|28|32)\b",
         tell="Identical large vertical padding on every section (no rhythm).",
         fix="Group related sections tightly; give breaks only where the story turns."),
    dict(id="pill-badge-hero", cat="layout", w=1, min=1, where="block",
         rx=r"class(Name)?=[\"'](?=[^\"']*\brounded-full\b)(?=[^\"']*\btext-(xs|sm)\b)(?=[^\"']*\b(border|bg-)\S*)[^\"']*[\"'][^\n]*\n(?:[^\n]*\n){0,8}?[^\n]*<h1\b",
         tell="Pill badge above the hero headline.",
         fix="Remove; if the line carries news, make it a plain sentence."),
    dict(id="headline-word-accent", cat="type", w=2, min=1, where="block",
         rx=r"<h[12][^>]*>(?:(?!</h[12]>).){0,400}?(<em\b|<(span|i|strong)\b[^>]*(class(Name)?=[\"'{][^\"'}]*(text-(?!sm\b|xs\b|base\b|lg\b|left|right|center|muted|gray|zinc|slate|neutral|stone|fg-muted|fg-subtle)[a-z]+-\d|text-primary|text-accent|italic|font-serif|bg-clip-text|gradient|underline)|style=\{\{[^}]*color))",
         tell="One word of the headline in a different colour/italic/gradient.",
         fix="One voice for the whole headline; let the typeface carry it."),
    dict(id="slogan-headings", cat="copy", w=2, min=3, where="block",
         rx=r"<h[23][^>]*>\s*[A-Z][a-z'’]*(?:[ ,]+[A-Za-z'’]+){0,6}\.\s*</h[23]>",
         tell="Section headings written as short slogans ending in a period ('Ten games, one wall.').",
         fix="Plain labels from the product's nouns and numbers ('Singles in stock (1,014)')."),
    dict(id="eyebrow-caps", cat="claude-defaults", w=2, min=3, where="cls",
         rx=r"\buppercase\b[^\"'`]*\btracking-(wide|wider|widest|\[0?\.\d+em\])|\btracking-(wider|widest|\[0?\.\d+em\])[^\"'`]*\buppercase\b"
            r"|textTransform:\s*[\"']uppercase[\"'][^}]*letterSpacing|letterSpacing[^}]*textTransform:\s*[\"']uppercase",
         tell="Tracked-out ALL-CAPS eyebrow/kicker labels above headings.",
         fix="Delete unless it carries real information; sentence case."),
    dict(id="hero-display-size", cat="type", w=1, min=1, where="cls",
         rx=r"\btext-(7xl|8xl|9xl)\b[^\"'`]*\b(font-bold|font-extrabold|tracking-tight)|\b(font-bold|font-extrabold|tracking-tight)[^\"'`]*\btext-(7xl|8xl|9xl)\b",
         tell="Giant bold tight-tracked hero headline (the default hero).",
         fix="Size from a real scale for this face and line length."),
    dict(id="mono-labels", cat="claude-defaults", w=1, min=6, where="cls",
         skip=r"<kbd|<code|<pre|\b\w*[iI]d\}|sku|hash|token|keys\}|tabular-nums",
         rx=r"\bfont-mono\b[^\"'`]*\btext-(xs|\[1[01]px\])|\btext-(xs|\[1[01]px\])[^\"'`]*\bfont-mono\b",
         tell="Monospace for small non-code labels.",
         fix="Mono only for code, IDs and tabular figures that need it."),
    # ---------------- copy
    dict(id="marketing-filler", cat="copy", w=2, min=2, where="text",
         rx=r"(?i)\b(seamless(ly)?|elevate|unlock|empower(s|ing)?|revolutioni[sz]e|supercharge|effortless(ly)?|game[- ]chang\w*|cutting[- ]edge|next[- ]level|next[- ]generation|world[- ]class|enterprise[- ]grade|harness the power|unleash|streamline|leverage|robust|delve|tapestry|in today'?s (fast[- ]paced|digital)|whether you'?re|all[- ]in[- ]one|at your fingertips|look no further|say goodbye to|the future of|reimagined|lightning[- ]fast|blazing[- ]fast|built for modern|designed to help you|transform(s)? (the way|your)|more than (just )?an?)\b",
         tell="Generic marketing filler.",
         fix="Say what the product does: a number, a noun from the domain, an example."),
    dict(id="fake-social-proof", cat="copy", w=3, min=1, where="text",
         rx=r"(?i)(trusted by (\d|over|thousands|teams|leading|the world)|join (thousands|over \d|\d[\d,]*\+)|\b\d{1,3}(,\d{3})+\+\s*(users|teams|customers|developers|creators|businesses)|\b\d+k\+\s*(users|teams|customers|developers)|\b99\.9+%|\b4\.9\s*/\s*5|★★★★★|sarah (chen|johnson|miller)|alex (rivera|johnson|chen)|michael chen|emily (rodriguez|chen)|\bacme( inc| corp)?\b|lorem ipsum)",
         tell="Placeholder social proof: invented counts, ratings, logos, testimonial names.",
         fix="Real numbers and named customers, or remove the section."),
    dict(id="most-popular-tier", cat="layout", w=2, min=1, where="text",
         rx=r"(?i)^(most popular|best value|recommended)$",
         tell="Three pricing tiers with a 'Most Popular' highlighted middle.",
         fix="Price the way this product is actually bought; often one plan and a contact."),
    dict(id="title-case-cta", cat="copy", w=1, min=2, where="text",
         rx=r"^(Get Started( Free| Today| Now)?|Start (Your )?Free Trial|Learn More|Sign Up Now|Book a Demo|Try It Free|Get Started for Free)$",
         tell="Stock title-case CTAs.",
         fix="Verb + this product's object, sentence case ('Import your first deck')."),
    dict(id="aphoristic-cadence", cat="copy", w=1, min=2, where="text",
         rx=r"\bNo [a-z]+( [a-z]+)?\. (Just|Only) |\bNot [a-z ]{2,20}\. (It'?s|It is) |^([A-Z][a-z]+\. ){2}[A-Z][a-z]+\.$|\btheat(er|re)\b|\bit'?s not (just )?an? [a-z ]{2,30}[,;—-]+ it'?s\b",
         tell="AI cadence: 'No X. Just Y.', 'Faster. Smarter. Simpler.', 'it's not just a X, it's a Y', 'theater'.",
         fix="Plain declarative sentences with specifics."),
    dict(id="em-dash-copy", cat="copy", w=2, min=6, density=0.02, where="text",
         skip=r"console\.|logger\.|\blog\(|throw |Error\(",
         rx=r"\u2014",
         tell="Em-dashes throughout UI copy.",
         fix="Periods and commas; UI copy rarely needs an em-dash."),
    dict(id="middle-dot-meta", cat="claude-defaults", w=1, min=3, density=0.02, where="text",
         skip=r"\btitle\b|<title|metadata",
         rx=r"\S \u00b7 \S",
         tell="Meta strings joined with middle dots ('A · B · C').",
         fix="Use layout (columns, labels) or plain commas."),
    dict(id="arrow-cta", cat="claude-defaults", w=2, min=3, where="cls", per_match=True,
         rx=r"[^\s>{\"'`]\s+(\u2192|&rarr;)\s*(<|[\"'`]|\}|$)|>\s*(\u2192|&rarr;)\s*<|\{[\"']\s*\u2192\s*[\"']\}",
         tell="'\u2192' stapled to link and button labels.",
         fix="Drop the arrow; the label says where it goes."),
    dict(id="numbered-markers", cat="claude-defaults", w=1, min=3, where="cls", per_match=True,
         rx=r">\s*0[1-9]\.?\s*<|[\"'`]0[1-9]\.?[\"'`]|\bn:\s*[\"']0[1-9][\"']",
         tell="01 / 02 / 03 markers on content that is not a sequence.",
         fix="Number only real steps."),
    # ---------------- code & provenance
    dict(id="section-comments", cat="code", w=1, min=3, where="any",
         rx=r"\{/\*\s*(Hero|Features?|Testimonials?|CTA|Pricing|FAQ|Footer|Stats|How It Works|Logo Cloud|Header|Navigation)( Section)?\s*\*/\}|//\s*(Hero|Features|Testimonials|CTA|Pricing) Section",
         tell="Narrating section comments ({/* Hero Section */}).",
         fix="Name components after the content; drop the narration."),
    dict(id="dead-links", cat="code", w=1, min=3, where="cls",
         rx=r"href=[\"']#[\"']",
         tell="href=\"#\" placeholder links.",
         fix="Real destinations or remove the link."),
    dict(id="generator-fingerprint", cat="provenance", w=3, min=1, where="any",
         rx=r"lovable-tagger|componentTagger\(|gpt-engineer|content=[\"']v0\.dev|bolt\.new|@stackblitz/",
         tell="Generator fingerprint in the code (Lovable/GPT-Engineer/v0/Bolt).",
         fix="Not a design flaw by itself; it tells you which defaults to look for."),
]

# CSS class definitions that implement a tell; uses of these classes in markup count as hits.
CSS_CLASS_TELLS = [
    ("eyebrow-caps", lambda sel, body: re.search(r"text-transform:\s*uppercase", body) and re.search(
        r"letter-spacing:\s*(0?\.(0[4-9]|[1-9])\d*em|[1-9][\d.]*px|0?\.\d+rem)", body)),
    ("hover-lift", lambda sel, body: ":hover" in sel and re.search(
        r"transform:[^;]*(translateY\(\s*-|scale\(\s*1\.(0[2-9]|1))", body)),
    ("glassmorphism", lambda sel, body: re.search(r"backdrop-filter:\s*blur", body)),
    ("gradient-text", lambda sel, body: re.search(r"background-clip:\s*text", body)),
]

EMOJI_RE = re.compile("[\U0001F300-\U0001FAFF\u2600-\u26FF\u2700-\u2712\u2718-\u27BF]")
STRING_RE = re.compile(r"\"([^\"\n]{3,})\"|'([^'\n]{3,})'|`([^`\n]{3,})`|>([^<>{}\n]{3,})<")
HEX_RE = re.compile(r"#([0-9a-fA-F]{6}|[0-9a-fA-F]{3})(?![0-9a-zA-Z])")
LUCIDE_RE = re.compile(r"import\s*\{([^}]+)\}\s*from\s*[\"']lucide-react[\"']")
CSS_BLOCK_RE = re.compile(r"([^{}]+)\{([^{}]*)\}")
OVERUSED_GLYPHS = {"Zap", "Rocket", "Shield", "ShieldCheck", "BarChart3", "BarChart", "CheckCircle2", "CheckCircle",
                   "TrendingUp", "Sparkles", "Star", "Users", "Globe", "Lock", "Layers", "Target", "Award", "Heart"}
LANDING_SECTIONS = ["hero", "features", "howitworks", "testimonials", "pricing", "faq", "cta",
                    "stats", "logocloud", "trustedby", "logos", "integrations", "newsletter"]
DEFAULT_FONTS = {"inter", "geist", "geist sans", "geistsans", "system-ui", "ui-sans-serif", "roboto", "arial",
                 "helvetica", "sans-serif", "-apple-system", "blinkmacsystemfont", "segoe ui", "open sans", "lato"}
OVERUSED_FONTS = {"inter", "geist", "space grotesk", "dm sans", "plus jakarta sans", "manrope", "outfit",
                  "poppins", "instrument serif", "fraunces", "playfair display", "jetbrains mono", "syne",
                  "sora", "satoshi", "montserrat", "ibm plex mono", "geist mono", "newsreader", "recoleta",
                  "cormorant", "cormorant garamond"}
SERIF_DISPLAY = {"instrument serif", "fraunces", "playfair display", "newsreader", "eb garamond", "recoleta",
                 "cormorant", "cormorant garamond", "libre baskerville", "dm serif display", "lora"}
SHADCN_DEFAULT = [re.compile(r"--primary:\s*222\.2 47\.4% 11\.2%"), re.compile(r"--primary:\s*oklch\(0\.205 0 0\)"),
                  re.compile(r"--foreground:\s*222\.2 84% 4\.9%"), re.compile(r"--background:\s*oklch\(1 0 0\)"),
                  re.compile(r"--radius:\s*0\.(5|625)rem")]
ROUTE_DIRS = {"app", "pages", "routes", "components", "views", "screens", "features"}


def hex_to_hsl(h):
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    r, g, b = (int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))
    hh, l, s = colorsys.rgb_to_hls(r, g, b)
    return hh * 360, s, l


def classify_hex(h):
    hue, s, l = hex_to_hsl(h)
    if 0.90 <= l <= 0.975 and 28 <= hue <= 52 and 0.18 <= s <= 0.65:
        return "cream"
    if 8 <= hue <= 24 and 0.42 <= s <= 0.82 and 0.42 <= l <= 0.66:
        return "terracotta"
    if (hue >= 340 or hue < 8) and 0.45 <= s <= 0.85 and 0.22 <= l <= 0.5:
        return "warm-red"
    if 68 <= hue <= 100 and s >= 0.7 and 0.42 <= l <= 0.64:
        return "acid"
    if l <= 0.075 and s <= 0.25:
        return "near-black"
    if 235 <= hue <= 285 and s >= 0.6 and 0.45 <= l <= 0.72:
        return "ai-violet"
    return None


FONT_NOISE = {"variable", "vf", "var", "regular", "medium", "bold", "semibold", "light", "black", "italic", "thin",
              "extrabold", "extralight", "ultralight", "heavy", "book", "roman", "latin", "ext", "cyrillic", "greek",
              "vietnamese", "subset", "normal", "wght", "opsz", "ital", "wdth", "web", "webfont", "font", "fonts",
              "woff", "woff2", "ttf", "otf", "full", "standard", "oblique", "slnt"}


def font_name_from_file(path):
    base = os.path.splitext(os.path.basename(path))[0]
    tokens = []
    for part in re.split(r"[-_.\[\],+ ]+", base):
        tokens += re.findall(r"[A-Z]{2,}(?=[A-Z][a-z])|[A-Z]?[a-z]+|[A-Z]+(?![a-z])|\d+", part)
    words = [t.lower() for t in tokens if t.lower() not in FONT_NOISE and not t.isdigit()]
    return " ".join(words).strip()


def surface_of(rel):
    parts = rel.replace("\\", "/").split("/")
    if parts[0] == "src" and len(parts) > 1:
        parts = parts[1:]
    if len(parts) == 1:
        return "(root)"
    if parts[0] in ROUTE_DIRS:
        rest = [p for p in parts[1:-1] if not (p.startswith("(") and p.endswith(")"))]
        return parts[0] + "/" + (rest[0] if rest else "(top)")
    return parts[0]


def iter_files(roots, include_tests, excludes):
    for root in roots:
        if os.path.isfile(root):
            ext = os.path.splitext(root)[1].lower()
            if ext in ALL_EXT:
                yield root, os.path.basename(root), ext
            continue
        for dirpath, dirnames, filenames in os.walk(root):
            dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS and not d.startswith(".")]
            for fn in filenames:
                ext = os.path.splitext(fn)[1].lower()
                if ext not in ALL_EXT or ".min." in fn or fn.endswith(".d.ts") \
                        or (fn.endswith(".config.ts") and "tailwind" not in fn):
                    continue
                path = os.path.join(dirpath, fn)
                rel = os.path.relpath(path, root)
                if not include_tests and TEST_RE.search("/" + rel):
                    continue
                if any(fnmatch.fnmatch(rel, pat) or fnmatch.fnmatch("/" + rel, pat) or pat.strip("/") in rel.split("/")
                       for pat in excludes):
                    continue
                yield path, rel, ext


CLASSLIKE = re.compile(r"^[\w\-:/\[\]\.#%@,()=&?+*!$<>|~ ]*$")


def extract_text(line, ext):
    """User-facing strings on a line (JSX text and string literals that read like prose)."""
    if ext in TEXT_EXT:
        t = re.sub(r"<[^>]+>", " ", line).strip()
        return [t] if t else []
    out = []
    for m in STRING_RE.finditer(line):
        s = next(g for g in m.groups() if g is not None).strip()
        if not s or s.startswith(("http", "/", "./", "../", "@", "#")):
            continue
        if re.search(r"\b(bg|text|flex|grid|px|py|mx|my|rounded|border|font|gap|w|h|items|justify)-[\w\[]", s):
            continue
        if CLASSLIKE.match(s) and not re.search(r"[A-Za-z]{2,} [a-z]{2,}", s) and len(s.split()) < 2:
            continue
        if re.fullmatch(r"[\w.$]+(\([^)]*\))?", s):
            continue
        out.append(s)
    return out


RULE_BY_ID = {r["id"]: r for r in RULES}


def rule_findings(hits, text_total, max_loc):
    out = []
    for rid, locs in hits.items():
        r = RULE_BY_ID[rid]
        if "density" in r and len(locs) < r["density"] * max(text_total, 1):
            continue
        if len(locs) >= r["min"]:
            out.append(dict(id=rid, cat=r["cat"], weight=r["w"], count=len(locs),
                            tell=r["tell"], fix=r["fix"], locations=locs[:max_loc]))
    return out


def tier_of(findings):
    design = [f for f in findings if f["cat"] != "provenance"]
    signals = sum(1 for f in design if f["weight"] >= 2) + 0.5 * sum(1 for f in design if f["weight"] == 1)
    strong = sum(1 for f in design if f["weight"] == 3)
    tier = "clean" if signals < 2 else "mild" if signals < 4 else "noticeable" if signals < 7 else "obvious"
    if strong >= 2 and tier in ("clean", "mild"):
        tier = "noticeable"
    return tier, signals, strong


def scan(roots, include_tests=False, max_loc=5, excludes=()):
    if isinstance(roots, str):
        roots = [roots]
    files = []
    for path, rel, ext in iter_files(roots, include_tests, list(excludes)):
        try:
            with open(path, encoding="utf-8", errors="ignore") as f:
                files.append((rel, ext, f.read()))
        except OSError:
            pass

    # pass 1: CSS classes that implement a tell
    class_tells = defaultdict(set)
    class_defs = defaultdict(list)
    for rel, ext, src in files:
        if ext not in STYLE_EXT and "<style" not in src:
            continue
        for m in CSS_BLOCK_RE.finditer(src):
            sel, body = m.group(1), m.group(2)
            for rid, test in CSS_CLASS_TELLS:
                if test(sel, body):
                    ln = src.count("\n", 0, m.start(2)) + 1
                    for cls in re.findall(r"\.([A-Za-z_][\w-]*)", sel):
                        if not re.match(r"(hover|focus|active|dark|group|peer|md|lg|sm|xl)$", cls):
                            class_tells[cls].add(rid)
                            class_defs[rid].append((rel, ln, sel.strip()[:80] + " { ... }"))

    hits = defaultdict(list)
    surf_hits = defaultdict(lambda: defaultdict(list))
    surf_text = Counter()
    fonts = Counter()
    colours = Counter()
    colour_locs = defaultdict(list)
    sections = set()
    shadcn_default = []
    lucide = Counter()
    rounded_values = Counter()
    emoji_hits = []
    interactive = focus_visible = text_total = 0

    def hit(rid, rel, ln, snip):
        hits[rid].append((rel, ln, snip))
        surf_hits[surface_of(rel)][rid].append((rel, ln, snip))

    for rid, defs in class_defs.items():
        for d in defs[:2]:
            hits[rid].append(d)

    for rel, ext, src in files:
        lines = src.splitlines()
        base = os.path.splitext(os.path.basename(rel))[0].lower().replace("-", "").replace("_", "")
        for name in LANDING_SECTIONS:
            if base in (name, name + "section") or re.search(r"<%s(Section)?\b" % re.escape(name), src, re.I) \
                    or re.search(r'id=["\']%s["\']' % name, src, re.I):
                sections.add(name)
        for m in re.finditer(r"import\s*\{([^}]+)\}\s*from\s*[\"']next/font/google[\"']", src):
            for n in m.group(1).split(","):
                n = n.strip().split(" as ")[0].replace("_", " ").strip()
                if n:
                    fonts[n.lower()] += 1
        if re.search(r"from\s*[\"']geist/font", src):
            fonts["geist"] += 1
        if re.search(r"next/font/local|@font-face", src):
            for m in re.finditer(r"[\"'`]([^\"'`\s]+\.(woff2?|ttf|otf))[\"'`]", src):
                n = font_name_from_file(m.group(1))
                if n:
                    fonts[n] += 1
        for m in re.finditer(r"fonts\.googleapis\.com/css2?\?family=([A-Za-z+]+)", src):
            fonts[m.group(1).replace("+", " ").lower()] += 1
        for m in re.finditer(r"font-family:\s*([^;}{]+)", src):
            first = m.group(1).split(",")[0].strip().strip("'\"")
            if first and not first.startswith(("var(", "inherit", "initial")):
                fonts[first.lower()] += 1
        for m in re.finditer(r"@fontsource(?:-variable)?/([a-z0-9-]+)", src):
            fonts[m.group(1).replace("-", " ")] += 1
        for m in re.finditer(r"\.custom\(\"([^\"]+)\"", src):
            fonts[m.group(1).lower()] += 1
        for m in re.finditer(r"fontFamily:\s*[\"']([A-Za-z][\w -]+?)[\"']", src):
            fonts[m.group(1).lower().replace("_", " ")] += 1
        for m in LUCIDE_RE.finditer(src):
            for n in m.group(1).split(","):
                n = n.strip().split(" as ")[0].strip()
                if n:
                    lucide[n] += 1
        if sum(1 for rx in SHADCN_DEFAULT if rx.search(src)) >= 2:
            shadcn_default.append(rel)
        for m in HEX_RE.finditer(src):
            c = classify_hex(m.group(1))
            if c:
                colours[c] += 1
                if len(colour_locs[c]) < max_loc:
                    ln = src.count("\n", 0, m.start()) + 1
                    colour_locs[c].append((rel, ln, lines[ln - 1].strip()[:140]))
        for m in re.finditer(r"\brounded(-(none|sm|md|lg|xl|2xl|3xl|full|\[[^\]]+\]))?(?=[\s\"'`])", src):
            rounded_values[m.group(0)] += 1
        if ext in CODE_EXT:
            interactive += len(re.findall(r"<button\b|<Button\b|onClick=|<a\s", src))
            focus_visible += len(re.findall(r"focus-visible|:focus-visible|focusRing|focus:ring", src))
        for rule in RULES:
            if rule["where"] != "block":
                continue
            for m in re.finditer(rule["rx"], src, re.S):
                ln = src.count("\n", 0, m.start()) + 1
                hit(rule["id"], rel, ln, lines[ln - 1].strip()[:140])
        for i, line in enumerate(lines, 1):
            if len(line) > 600:
                continue
            stripped = line.strip()
            is_comment = stripped.startswith(("//", "*", "/*", "#")) and not stripped.startswith("{/*")
            texts = [] if is_comment or stripped.startswith(("import ", "export {")) else extract_text(line, ext)
            text_total += len(texts)
            surf_text[surface_of(rel)] += len(texts)
            snip = stripped[:140]
            for rule in RULES:
                w = rule["where"]
                if w == "block" or ("skip" in rule and re.search(rule["skip"], line)):
                    continue
                if w == "text":
                    if any(re.search(rule["rx"], t) for t in texts):
                        hit(rule["id"], rel, i, snip)
                elif w == "cls":
                    if not is_comment:
                        n = len(re.findall(rule["rx"], line)) if rule.get("per_match") else int(bool(re.search(rule["rx"], line)))
                        for _ in range(n):
                            hit(rule["id"], rel, i, snip)
                elif re.search(rule["rx"], line):
                    hit(rule["id"], rel, i, snip)
            if class_tells and ext not in STYLE_EXT and not is_comment and re.search(r"class(Name)?\s*[=:]|cn\(|clsx\(", line):
                done = set()
                for tok in re.findall(r"[A-Za-z_][\w-]*", line):
                    for rid in class_tells.get(tok, ()):
                        if rid not in done:
                            done.add(rid)
                            hit(rid, rel, i, snip)
            if any(EMOJI_RE.search(t) for t in texts):
                emoji_hits.append((rel, i, snip))

    findings = rule_findings(hits, text_total, max_loc)

    def add(fid, cat, weight, count, tell, fix, locs=None):
        findings.append(dict(id=fid, cat=cat, weight=weight, count=count, tell=tell, fix=fix,
                             locations=(locs or [])[:max_loc]))

    if len(emoji_hits) >= 2:
        add("emoji-icons", "icons", 2, len(emoji_hits), "Emoji used as icons, bullets or decoration in UI copy.",
            "One real icon set at one weight, or no icon.", emoji_hits)
    font_names = {f for f in fonts if f}
    if font_names and font_names <= DEFAULT_FONTS:
        add("default-typeface", "type", 3, len(font_names),
            "Only default UI faces (%s): no typographic voice." % ", ".join(sorted(font_names)),
            "Choose a family for this subject and set a real scale (human-design/references/craft.md).")
    overused = sorted((font_names & OVERUSED_FONTS) - (DEFAULT_FONTS - {"inter", "geist"}))
    if overused and not (font_names <= DEFAULT_FONTS):
        add("overused-typeface", "type", 1, len(overused),
            "Faces that dominate AI output right now: %s." % ", ".join(overused),
            "Fine if chosen on purpose; otherwise pick outside the overused list.")
    glyphs = sorted(set(lucide) & OVERUSED_GLYPHS)
    if len(glyphs) >= 4:
        add("stock-icon-set", "icons", 1, len(glyphs), "The stock Lucide feature glyphs: %s." % ", ".join(glyphs),
            "Icons only where they aid recognition; consider a set with more character.")
    if len(sections) >= 5:
        add("stock-landing-order", "layout", 2, len(sections),
            "Stock landing-page sections present: %s." % ", ".join(sorted(sections)),
            "Order by the decision the reader is making; cut sections that exist out of habit.")
    if shadcn_default:
        add("shadcn-default-theme", "design-system", 3, len(shadcn_default),
            "Unmodified shadcn/ui default theme tokens (colour and/or --radius).",
            "Write the project's own tokens: colour, radius, type.",
            [(p, 1, "default shadcn tokens") for p in shadcn_default])
    total_rounded = sum(rounded_values.values())
    if total_rounded >= 20:
        top, n = rounded_values.most_common(1)[0]
        if n / total_rounded >= 0.7:
            add("one-radius", "shape", 1, n,
                "One radius (%s) on %d%% of rounded elements regardless of hierarchy." % (top, round(100 * n / total_rounded)),
                "Radius follows hierarchy: controls, cards and containers differ.")
    if interactive >= 15 and focus_visible == 0:
        add("no-focus-states", "quality", 1, interactive, "Many interactive elements, no focus-visible styling anywhere.",
            "Design the focus state; it is part of the look.")
    has_serif = bool(font_names & SERIF_DISPLAY)
    warm = colours["terracotta"] + colours["warm-red"]
    if colours["cream"] and warm:
        add("claude-warm-house-style", "claude-defaults", 2, colours["cream"] + warm,
            "Warm cream ground + terracotta/clay/crimson accent%s: Claude's own interface look and its close variants." % (
                " + serif display" if has_serif else ""),
            "Unless the brief asks for it, take palette and type from the product's subject.",
            colour_locs["cream"][:2] + colour_locs["terracotta"][:2] + colour_locs["warm-red"][:2])
    elif colours["terracotta"] >= 2:
        add("terracotta-accent", "claude-defaults", 2, colours["terracotta"],
            "Terracotta/clay accent (near #D97757).", "Accent from the subject's world.", colour_locs["terracotta"])
    elif colours["cream"] >= 2 and has_serif:
        add("cream-serif", "claude-defaults", 2, colours["cream"],
            "Cream ground with a serif display face (the 'tasteful' default).", "Ground from the subject's world.",
            colour_locs["cream"])
    if colours["near-black"] and colours["acid"]:
        add("dark-acid-house-style", "claude-defaults", 2, colours["acid"],
            "Near-black canvas with a single acid-green/lime accent.", "Only if the brand truly lives there.",
            colour_locs["near-black"][:2] + colour_locs["acid"][:3])
    if colours["ai-violet"] >= 3:
        add("violet-hex", "colour", 2, colours["ai-violet"], "Indigo/violet hex values (#6366f1 family) in the palette.",
            "Accent from the subject's world.", colour_locs["ai-violet"])

    tier, signals, strong = tier_of(findings)
    by_cat = defaultdict(int)
    for f in findings:
        if f["cat"] != "provenance":
            by_cat[f["cat"]] += f["weight"]
    surfaces = []
    for s, sh in surf_hits.items():
        sf = rule_findings(sh, surf_text[s], 0)
        st, ss, sstrong = tier_of(sf)
        if sf:
            surfaces.append(dict(surface=s, tier=st, signals=ss, strong=sstrong,
                                 tells=sorted(f["id"] for f in sf)))
    surfaces.sort(key=lambda d: -d["signals"])
    findings.sort(key=lambda f: (f["cat"] == "provenance", -f["weight"], -f["count"]))
    return dict(root=", ".join(os.path.abspath(r) for r in roots), files_scanned=len(files), signals=signals,
                strong=strong, tier=tier, points=sum(by_cat.values()),
                by_category=dict(sorted(by_cat.items(), key=lambda kv: -kv[1])), findings=findings,
                surfaces=surfaces, fonts=dict(fonts.most_common(12)), colour_classes=dict(colours),
                landing_sections=sorted(sections))


def render(rep):
    out = ["# Slop scan: %s" % rep["root"], "",
           "Files scanned: %d. Static tier: **%s** (%.1f weighted signals, %d strong, %d points)." % (
               rep["files_scanned"], rep["tier"], rep["signals"], rep["strong"], rep["points"]),
           "Triage only: combinations matter more than single hits, and the rendered review decides.",
           "Repo-wide numbers include internal tools and dead code; judge public surfaces by their own row.", ""]
    if rep["surfaces"]:
        out += ["| Surface | Tier | Signals | Tells |", "|---|---|---|---|"]
        out += ["| %s | %s | %.1f | %s |" % (s["surface"], s["tier"], s["signals"], ", ".join(s["tells"]))
                for s in rep["surfaces"][:25]]
        out.append("")
    if rep["by_category"]:
        out += ["| Category | Points |", "|---|---|"] + ["| %s | %d |" % kv for kv in rep["by_category"].items()] + [""]
    out.append("Fonts seen: %s" % (", ".join("%s (%d)" % kv for kv in rep["fonts"].items()) or "none declared"))
    out.append("Colour clusters: %s" % (", ".join("%s (%d)" % kv for kv in rep["colour_classes"].items()) or "none flagged"))
    out.append("Landing sections: %s" % (", ".join(rep["landing_sections"]) or "none"))
    out.append("")
    for f in rep["findings"]:
        sev = {3: "P0", 2: "P1", 1: "P2"}[f["weight"]] if f["cat"] != "provenance" else "info"
        out.append("## [%s] %s (%s, %d hits)" % (sev, f["id"], f["cat"], f["count"]))
        out.append("Tell: %s" % f["tell"])
        out.append("Fix: %s" % f["fix"])
        for p, ln, snip in f["locations"]:
            out.append("  - %s:%d  %s" % (p, ln, snip))
        out.append("")
    if not rep["findings"]:
        out.append("No static tells fired. That is not a pass: the scanner only knows named clusters. "
                   "Do the rendered review.")
    return "\n".join(out)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("paths", nargs="*", default=["."])
    ap.add_argument("--exclude", action="append", default=[], help="glob or directory name to skip, repeatable")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--max-locations", type=int, default=5)
    ap.add_argument("--include-tests", action="store_true")
    a = ap.parse_args()
    for p in a.paths:
        if not os.path.exists(p):
            sys.exit("no such path: %s" % p)
    rep = scan(a.paths, a.include_tests, a.max_locations, a.exclude)
    print(json.dumps(rep, indent=2) if a.json else render(rep))


if __name__ == "__main__":
    main()
