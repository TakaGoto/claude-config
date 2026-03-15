# Retro

Generate a retrospective for recently completed work. Reads git history, closed issues, and merged PRs to summarize what shipped and what was learned.

**Arguments:** $ARGUMENTS
Parse arguments:
- `--since <date>`: Look back from this date (default: 7 days ago). Accepts "2026-03-01", "2w", "1m".
- `--app <name>`: Filter to a specific app (e.g., `wicklog`, `loki`). Default: all.
- `--format <type>`: `summary` (default) or `detailed`

## Steps

### 1. Gather Data

Run these in parallel:

**Git history:**
```bash
git log --oneline --since="{since}" --no-merges
git log --oneline --since="{since}" --merges
git shortlog -sn --since="{since}"
```

**Closed beads issues:**
```bash
bd list --limit 0 --status closed
```
Filter to issues closed within the time window and optionally by app prefix.

**Merged PRs:**
```bash
gh pr list --state merged --search "merged:>{since_date}" --json number,title,mergedAt,author,additions,deletions,url
```

**Open issues remaining:**
```bash
bd list --limit 0
```

### 2. Analyze

- Group work by category: features, bug fixes, refactoring, tests, chores
- Calculate velocity: issues closed, PRs merged, lines changed
- Identify who did what (git shortlog, PR authors, beads assignees)
- Note any issues that were opened but not closed (carry-over)
- Check for patterns: repeated bug areas, slow-moving issues, blocked items

### 3. Generate Retro Report

```markdown
# Retro — {date_range}

## What Shipped
- {n} issues closed, {n} PRs merged, {n} lines changed
- By category: {n} features, {n} fixes, {n} refactors, {n} chores

### Highlights
- [Top 3-5 most impactful changes with PR links]

### Full Changelog
| PR | Title | Type | Lines |
|----|-------|------|-------|
| #123 | Description | feature | +200/-50 |

## What's Still Open
- {n} open issues ({n} in progress, {n} blocked)
- Oldest open issue: {title} (opened {date})

### Carry-Over Items
[Issues that were expected to close this period but didn't]

## Observations
- [Patterns noticed: e.g., "3 of 5 bugs were in the same module"]
- [Velocity trend: faster/slower than previous period]
- [Blocked items and why]

## Next Period Priorities
Based on what's open and what was learned:
1. [Suggested focus area]
2. [Suggested focus area]
3. [Suggested focus area]
```

### 4. If `--format detailed`

Also include:
- Per-file change frequency (which files were modified most — hotspots)
- Test coverage changes (if test files were added/removed)
- Dependency changes (packages added/removed)
- ADRs written during the period

## Rules

- Be factual — report what happened, don't editorialize
- Link to PRs and issues so the user can drill in
- If no work was done in the period, say so and suggest what to prioritize
