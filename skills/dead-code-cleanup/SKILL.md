---
name: dead-code-cleanup
description: Find and remove dead code, unused dependencies, commented-out code, stray debug logs, and stale TODOs in a codebase. This skill edits source code, so it is separate from repo-cleanup (which never does). Use this whenever the user says "find dead code", "unused exports/imports/deps", "remove unused packages", "clean up TODOs", "strip console.logs", "tidy the source", or wants to shrink a codebase's source footprint.
---

# Dead code cleanup

This skill changes source code, which is why it is kept apart from `repo-cleanup`. The shape is: **detect, verify each candidate, report, get approval, remove on a branch, run the gate.**

## Ground rules

- **Branch + PR only.** Work on a feature branch (use a worktree if other sessions are active). Never commit to or push main. Under `~/work/`, keep changes local and do not commit or push without explicit permission.
- **Candidates, not verdicts.** Tool output is a starting list. Nothing is removed until it has been checked by hand.
- **One kind of change per commit** (deps, dead exports, debug logs) so any one can be reverted alone.
- **Confirm `pwd`** is the target package before touching `package.json` or running installs, and use the repo's package manager only, from within the app directory.

## Phase 1 - Dead code and unused dependencies

Use the repo's own tooling when present; otherwise suggest one (`knip` for JS/TS, `depcheck`, `ts-prune`; `vulture` for Python).

Before listing anything as removable, grep for it, including dynamic imports, string references, and config files. Common false positives: framework file-based routing (Next/Expo Router), Worker entry points in `wrangler.toml`, scripts referenced only from `package.json` or CI, peer dependencies, type-only packages, and side-effect imports.

Report each candidate with its evidence.

## Phase 2 - Stale TODOs, commented-out code, stray logs

Search for `TODO|FIXME|HACK|XXX`, large commented-out blocks, and `console.log`/`print` debugging. Use `git blame` to date TODOs and surface the oldest. Skip logging that is intentional (CLIs, scripts, Workers observability). Suggest turning long-lived TODOs into issues rather than deleting them. This phase is the most subjective, so only touch the items the user selects.

## Report, then act

Present candidates grouped by kind, with evidence, and ask once. After approved removals, run the repo's full gate (typecheck, lint, unit, and e2e unless the repo's CLAUDE.md says otherwise) and report actual counts, not "tests pass". If the gate fails, revert that removal and say so. Finish with the branch and PR holding the changes.
