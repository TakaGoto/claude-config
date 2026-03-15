# Review PR

Review a pull request for correctness, quality, and security.

**Arguments:** $ARGUMENTS
Parse arguments:
- First positional arg: PR number or URL (required)
- `--focus <area>`: Focus review on a specific area: `security`, `types`, `tests`, `perf`, or `all` (default: `all`)

## Steps

### 1. Fetch PR Details

```bash
gh pr view {number} --json title,body,baseRefName,headRefName,files,additions,deletions
gh pr diff {number}
```

Read the PR title, description, and full diff.

### 2. Understand Context

- Read the PR description for intent — what problem does this solve?
- Check the base branch (main, staging, feature branch)
- Read any linked issues or beads references
- Skim the changed files list to understand scope

### 3. Review the Diff

For each changed file, read the surrounding code (not just the diff) to understand context. Check against:

**Correctness**
- Logic is correct — no off-by-one, wrong conditions, missed edge cases
- Async operations properly awaited, no floating promises
- Error paths handled by callers
- No race conditions in concurrent paths

**Type Safety**
- No `any` types without justification
- Null/undefined handled explicitly
- Casts (`as`) used only when necessary, not to silence errors

**Code Quality**
- Follows existing codebase patterns — no invented conventions
- No unnecessary duplication
- No over-engineering — complexity matches the problem
- No commented-out code or debug logs

**Security**
- No secrets, credentials, or tokens hardcoded
- User input validated before use (DB, shell, API)
- No injection vectors (SQL, XSS, command)
- Auth checks present on new endpoints

**Tests**
- New business logic has test coverage
- Tests verify behavior, not implementation details
- Edge cases covered (empty input, null, error paths)

**Performance** (if `--focus perf` or `all`)
- No N+1 query patterns
- No unnecessary re-renders (React)
- Large lists use virtualization
- No blocking operations in hot paths

### 4. Check PR Comments

```bash
gh api repos/{owner}/{repo}/pulls/{number}/comments
```

Read existing review comments to avoid duplicating feedback.

### 5. Output Review

```markdown
## PR Review: #{number} — {title}

### Summary
[1-2 sentence assessment]

### Issues

#### [HIGH] Issue Title
- **File:** path/to/file.ts:42
- **Problem:** What is wrong and why it matters
- **Suggestion:** How to fix it

#### [MEDIUM] Issue Title
...

#### [LOW] Issue Title
...

### Positive Notes
- [Things done well]

### Verdict: APPROVE / REQUEST CHANGES
[If REQUEST CHANGES, list only the HIGH items that must be fixed]
```

## Rules

- Always read surrounding code, not just the diff — context matters
- HIGH = must fix before merge (bugs, security, type errors)
- MEDIUM = should fix (code quality, missing error handling, missing tests)
- LOW = nice to have (naming, style, minor improvements)
- Only HIGH issues block merge
- If the PR looks good, say so concisely — don't pad the review
