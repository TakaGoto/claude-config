# Craft: what makes a design read as made by a person

Human-made design is recognisable by specificity and by decisions that cost something: a typeface that commits, a layout shaped by the content, copy only this product could say, details that only make sense for this subject. Each section below lists what to do, not what to avoid (defaults.md covers that).

## Conscious choices

Generic design is the sum of properties nobody decided. For the elements that matter most (the hero, the primary action, the main data display) decide every property explicitly: position, size, colour, weight, copy, state changes, motion. Give the less important elements high-level rules. The more conscious choices on the important parts, the less generic the result, even before taste comes into it.

## Type

- Pick the family for the subject and its context of use, then name the roles in tokens (display, text, data). One family with real weight contrast is often stronger than two.
- Set a scale with visible contrast (ratio 1.25–1.5; display sizes can jump further). Use at least two weights for different jobs, not decoration.
- Measure: 45–75 characters for reading text; serif body gets a little more line-height than sans.
- When the headline is a visual element, make the type treatment the design (width axis, weight, size against the grid), not a coloured word inside it.
- Tabular figures for numbers in tables and stats. Real quotes and apostrophes, real ellipsis.
- iOS: SF Pro for UI text is the platform and reads as native; express personality with a display face in headers and with layout, not by replacing system text.

## Colour

- Derive the palette from evidence (materials, signage, photos of the subject), name each colour after its source, then assign roles.
- Distribution: a dominant ground, a supporting tone, a sharp accent used sparingly (roughly 60/30/10). Status colours have fixed meanings.
- Build dark mode on a hue, with several tones, rather than neutral near-black plus one accent.
- Check contrast for every text/ground pair you actually use.

## Layout

- Let the content's real shape decide the structure: tabular content gets a table, sequences get steps, one strong example beats three thin cards.
- Open with the most characteristic thing in the subject's world: the product working, a real number, a real photo, the thing a user would recognise.
- Vary measure and rhythm on purpose: narrow for reading, wide for showing; tight spacing inside groups, generous breaks only where the story turns.
- Asymmetry when the content has a primary and a secondary part; symmetry when it is genuinely balanced. Alignment should be a decision (left-aligned reading text by default).
- Order sections by the decision the reader is making, and cut sections that exist out of habit.

## Shape and elevation

- Radius and elevation follow hierarchy: controls, cards and containers differ. Elevation only for things that actually float (menus, dialogs, dragged items).
- Borders and spacing separate content before shadows do. One depth mechanism per component.

## Motion

- One orchestrated moment at most (a first-load sequence, or one scroll-linked object). Everything else responds to the user's own actions and shows what changed.
- Time to information beats atmosphere, especially for B2B: no scroll-jacked intros, scroll-triggered videos or autoplaying animation that delays what the page says. Featured launch pages are the exception, not the template.
- Exponential ease-out, short durations, specific properties (transform, opacity). Honour reduced motion.

## Imagery and icons

- Real screenshots, real photos of the subject, diagrams of the product's actual mechanics, scans of physical artefacts, or none. One illustration style if any, never primitive-shape SVG scenes or stock 3D.
- Icons only where they speed recognition; one set, one weight. Labels beat icons for anything important.

## Copy

- Name things the way users name them. Say what the product does with a number, a domain noun or an example. Test: could a competitor use this sentence unchanged? Then rewrite it.
- CTAs are verb + object in sentence case ("Post round 3 pairings"), and the same verb appears in the confirmation ("Pairings posted").
- Errors say what happened and how to fix it, without apologising. Empty states say the next step.
- No invented proof. Real numbers with their source, named customers with permission, or nothing.
- Plain punctuation: periods and commas over em-dashes; no tricolon slogans.

## Details that signal a person was here

- Something only this subject would have: a pairing-table number styled like the shop's table tents, a set symbol, a real store's hours.
- Edge cases handled: long names, zero results, one result, 999+ items, slow networks.
- Focus states, hover states and pressed states designed in the same voice as the rest.
- Consistency across every page: the same tokens, the same voice, no screen that looks like it came from a different kit.
