# App Store Prep

Generate all App Store metadata for submission.

## Steps

1. Read the app's codebase to understand what it does, its features, and target audience
2. Generate ALL of the following:

### Required Output

**App Name** (30 chars max) — if the obvious name is taken, suggest 3 ASO-optimized alternatives

**Subtitle** (30 chars max) — keyword-rich, describes core value

**Promotional Text** (170 chars max) — can be updated without a new build, highlight current promotions or features

**Description** (4000 chars max) — structured as:
- Hook (first 3 lines visible before "more")
- Key features as bullet points
- Social proof / differentiator
- Call to action

**Keywords** (100 chars max, comma-separated) — no spaces after commas, no duplicates of words already in app name/subtitle, focus on search volume

**Category** — primary and secondary category recommendations

**Bundle ID** — look up from app.json/app.config

3. Also generate a **ChatGPT prompt for screenshots** that describes:
   - The app's key screens to showcase
   - Device frame style (iPhone 15 Pro)
   - Text overlay style and messaging for each screenshot
   - Correct App Store screenshot dimensions (1290 x 2796 for 6.7")

## Rules

- Optimize for ASO — every character counts
- Research competitor apps in the same category to differentiate
- Keywords should target low-competition, high-relevance terms
- Description should front-load the most important info (only first 3 lines show by default)
