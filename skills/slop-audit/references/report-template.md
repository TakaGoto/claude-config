# Report template

```markdown
# Slop audit: <product> (<surfaces>)

**Verdict: <clean | mild | noticeable | obvious>.** <One sentence on how a person would read it, e.g. "Reads as a stock AI SaaS template within three seconds; nothing on the page is specific to card shops.">

Most damaging tells:
1. <tell>: <evidence, file:line or screenshot>
2. ...
3. ...

| Surface | Verdict | Main tells |
|---|---|---|
| Home | ... | ... |
| <flow> | ... | ... |

## What was checked
- Code audited: <repo> at <commit> (<deployed branch>; local checkout <n> commits behind/ahead)
- Static scan: <overall tier>; per-surface rows above (`slop_scan.py <path>`, excludes: <...>)
- Screenshots: <paths at 390 / 768 / 1440, themes>
- Flows walked: <list>, or "not in scope"
- Intent sources read: <DESIGN.md, brand guide, ...>
- Exempt (documented with a subject-rooted reason): <list>
- Documented but default-shaped (owner to decide): <list>

## Unproven
<Everything that could not be checked on screen and why: behind a login, no browser, theme not captured, ...>

## Human tests
| Test | Result |
|---|---|
| Glance | ... |
| Swap | ... (what survives a competitor's logo; what does not) |
| Silhouette | ... |
| Same-prompt | n of m visible decisions match the default |
| Copy read | ... |
| Second-order clusters | none / which |

## Findings
| Sev | Tell | Evidence | Chosen, default, or documented-but-default |
|---|---|---|---|
| P0 | ... | file:line / screenshot | default |

## Other issues seen
<Contrast failures, clipped text, contradictory facts, broken states, leftovers.>

## Fix plan
| # | Change (what a designer would do) | Touches | Effort | Resolves |
|---|---|---|---|---|
| 1 | Direction: ... | ... | L | ... |
| 2 | Tokens: ... | ... | M | ... |

Decisions this plan leaves to you: ...
Dead or flagged-off code that would ship these tells if enabled: ...
```

Keep the verdict, the top three tells and the surface table above the fold; the rest is for whoever implements the fixes.
