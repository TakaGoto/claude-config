# Taste profile template

A shared skill that thousands of people install becomes the next default. What makes the output yours is your own taste written down. Save a filled-in copy as `~/.claude/skills/human-design/taste.md`; the skill reads it before every design job. Keep it short and concrete: examples beat adjectives.

```markdown
# My taste

## Sites and apps I love (and the one thing I love about each)
- <url>: <e.g. "the way the price list is a plain table with no cards">

## Sites and apps I can't stand (and why)
- <url>: <e.g. "scroll-jacked intro, 30 seconds before I learn what it does">

## Type
- Families I keep coming back to: ...
- Families I never want again: ...

## Colour
- Palettes or colours that feel like me: ...
- Never: ...

## Layout and density
- <e.g. "dense and scannable over airy; left-aligned; no centered hero">

## Motion
- <e.g. "only in response to a tap; never on scroll">

## Copy voice
- <e.g. "short, plain, numbers over adjectives, no exclamation marks">

## My weights when choices conflict
- <e.g. "clarity beats novelty; speed of reading beats atmosphere; one bold thing per page">

## Things I always end up fixing by hand
- <e.g. "letter-spacing on headings", "button padding on mobile">
```

Deck additions that fit this taste (favourite font pairings, palette recipes, layouts) go in `data/deck.local.json` with the same shape as `data/deck.json`; deal.py merges them and gives them priority over the shared deck.
