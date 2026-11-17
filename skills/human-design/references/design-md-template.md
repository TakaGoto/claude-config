# DESIGN.md template

Based on Google's DESIGN.md format (google-labs-code/design.md): YAML front matter for tokens, prose for the reasons. Drop any token group the design does not use (a direction with no motion has no motion block). `npx @google/design.md lint DESIGN.md` checks references and contrast, but it downloads third-party code, so run it only if the user allows.

```markdown
---
name: <Product>
direction: <direction name from step 5>
colors:
  ground: "#......"   # source: <what in the subject's world this came from>
  ink: "#......"
  muted: "#......"
  accent: "#......"   # used only for: <the one job>
  danger: "#......"
  success: "#......"
typography:
  display: { family: "<family>", weights: [<n>, <n>], source: "<google|fontshare|self-hosted>" }
  text: { family: "<family>", weights: [<n>, <n>] }
  data: { family: "<family>", features: ["tnum"] }
  scale: [12, 14, 16, 20, 25, 32, 48, 72]   # px, ratio ~1.25 + display jumps
rounded: { control: <px>, card: <px>, container: <px> }
spacing: [4, 8, 12, 16, 24, 32, 48, 64, 96]
elevation: { raised: "<shadow or none>", overlay: "<shadow>" }
motion: { duration: { fast: 120, base: 200 }, easing: "cubic-bezier(0.16, 1, 0.3, 1)" }
---

## Point of view
<Two or three sentences: who it is for, what the design should feel like, and why, tied to the evidence board.>

## The one bold thing
<The single memorable element. Everything else stays quiet.>

## Rules
- <Rule an agent can follow, e.g. "Accent only on the primary action and live round status.">
- <...>

## Do / Don't
| Do | Don't |
|---|---|
| ... | ... |

## Evidence board
- <reference>: borrowed <x>; not <y>.

## Deliberate exceptions
<Anything the slop scanner flags that is chosen on purpose, with the reason.>
```
