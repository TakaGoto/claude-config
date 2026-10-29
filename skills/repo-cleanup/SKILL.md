---
name: repo-cleanup
description: Housekeeping for a repo that never touches source code - trim bloated CLAUDE.md/rules/skills/agents files, delete merged and stale branches and worktrees, and reclaim disk from build caches in old worktrees. Use this whenever the user says "clean up the repo", "cleanup", "prune branches/worktrees", "delete merged branches", "my CLAUDE.md is too big", "audit my skills/rules/agents", or asks why a repo or their disk feels bloated, even if they only name one of these tasks. For dead code, unused dependencies, or stale TODOs, use the separate dead-code-cleanup skill instead.
---

# Repo cleanup

Three phases, run in order. Each phase produces findings; nothing is deleted or edited until the user approves the combined report. Cleanup is easy to get wrong in ways that can't be undone (a branch holding the only copy of someone's work), so the shape is always: **measure, report, get one approval, act, re-verify.**

## Ground rules

- **Never modify source code.** This skill edits only Claude context files (CLAUDE.md, AGENTS.md, rules, skills, agents), git refs and worktrees, and regenerable build output. Dead code, unused dependencies, TODOs, and logging cleanup belong to `dead-code-cleanup`. If a finding points at source, mention it in the report as a pointer to that skill and leave it alone.
- **Report first.** The audit is read-only. Present one report, ask once, then execute only the approved items. Per the user's global rules, force-deleting branches needs a go-ahead in the same turn; approval of the report is that go-ahead for the items listed in it.
- **Verify state fresh.** Start with `pwd` and `git fetch --all --prune`. Do not trust worktree state or earlier-session memory about what is merged or pushed.
- **Respect git rules.** Never push to or commit on main. Context-file edits go on a feature branch and a PR. Under `~/work/`, keep everything local and do not commit or push without explicit permission.
- **Local only.** Do not delete remote branches unless the user asks for it explicitly.
- **Scope = the current repo.** Do not sweep other repos unless asked.
- **Never touch:** `main`/`master`, `staging`, the current branch, the current worktree, or any worktree another live session may be using (check `git worktree list` and running `claude` processes).

## Phase 1 - Context files audit

Why this matters: CLAUDE.md, rules, skill descriptions, and agent descriptions are loaded into context on every session. Each unnecessary line costs tokens on every turn and dilutes the instructions that matter.

Inventory: project and global `CLAUDE.md`, `AGENTS.md`, `.claude/rules/*`, `.claude/skills/*/SKILL.md`, `.claude/agents/*`, and `~/.claude/` equivalents. Measure with `wc -l`.

Flag, as defaults:
- `CLAUDE.md` / `AGENTS.md` over ~200 lines
- `SKILL.md` over ~500 lines, or a skill description over ~100 words
- agent files with long prompts that duplicate CLAUDE.md
- any rule loaded always that only applies to some paths (propose path-scoped rules or a skill instead)

Look for improvements:
- **Duplication** between global and project files, or between CLAUDE.md and rules
- **Derivable content**: things Claude can learn by reading the code (file trees, stack lists) rather than instructions
- **Drift**: every file path, script, command, and URL mentioned must still exist. Check each one read-only (`ls`, `grep` package.json scripts). Dead references are the most common rot.
- **Vague or contradictory** instructions; rules stated as ALL-CAPS commands with no reason
- **Content that should move**: long reference material belongs in a `references/` file or skill, not CLAUDE.md

Output: a table of file, lines, flag, proposed change. Propose edits as concrete diffs. Do not edit the global `~/.claude/CLAUDE.md` without asking, since it affects every project.

## Phase 2 - Branches and worktrees

Run `git fetch --all --prune`, then `git branch -vv`, `git worktree list`, and `git for-each-ref --format='%(refname:short) %(committerdate:unix) %(upstream:track)' refs/heads`.

Classify every local branch and worktree:

1. **Merged** - tip is an ancestor of the default branch (`git branch --merged <default>`), **or** its PR is merged (`gh pr list --state merged --head <branch>`). The second check is essential: squash merges leave the branch looking unmerged to git.
2. **Stale** - last commit older than 14 days and not merged.
3. **Active** - everything else. Leave alone.

Deletion rules:
- **Merged:** delete if the working tree is clean. Use `git branch -d` where git agrees it is merged; use `-D` only for PR-merged squash cases, and list them as such in the report.
- **Stale:** delete only if (a) no uncommitted changes in its worktree and (b) no unpushed commits: `git rev-list -n1 <branch> --not --remotes --tags` is empty. Age alone is not proof the work is disposable; stale-looking worktrees have held the only copy of WIP before.
- **Stale with uncommitted or unpushed work:** do not delete. List under "Needs your call" with a one-line summary of what is at risk (`git status -s`, commit count).
- Remove worktrees with `git worktree remove <path>` (no `--force`; its refusal on dirty trees is a useful backstop), then delete the branch, then `git worktree prune`.

## Phase 3 - Disk bloat

Find regenerable build output, especially inside stale worktrees: `node_modules`, `.next`, `.turbo`, `.wrangler`, `.expo`, `dist`, `build`, `.cache`. Use `du -sh` and rank by size, per worktree.

- In worktrees already approved for removal, this is covered by the removal.
- In worktrees being kept, only delete caches the user approves, and say what regenerates them.
- Never delete lockfiles, `.env*`, or anything tracked by git.

## Unattended daily mode

`daily/run.py` runs this skill headlessly with a policy object for one repo, e.g. `{"name","path","base","merge"}`. Nobody is there to approve a report, so the user pre-approved a narrow set of actions; everything else goes in the report instead of being done.

Pre-approved (local only):
- delete merged branches and worktrees with a clean tree
- delete stale (14+ days) branches and worktrees with no uncommitted changes and no unpushed commits
- never the "Never touch" list above, and never remote branches

Not pre-approved, report only: stale branches with at-risk work, build-cache deletion in kept worktrees, and any rewrite of a context file.

Context-file edits are limited to mechanical fixes: a reference to a path/command verified missing, or an exact duplicate line. Make them in a temporary worktree off `base` on branch `chore/repo-cleanup-<YYYY-MM-DD>` and open a PR to `base`. No edits means no PR. Never edit the global `~/.claude/CLAUDE.md` unattended.

Merging follows `policy.merge`:
- `"main"` or `"staging"`: merge the PR into that branch only if the repo's documented gate passes on the exact head, with `gh pr merge --merge` (never squash, never a direct push). If the gate cannot be run or fails, leave the PR open and say why. For `"staging"`, also open (never merge) a PR from `staging` to `main` if none is open.
- `"none"`: leave the PR open.
- Never promote, deploy, apply migrations, or publish OTAs, and never merge a PR other than the one this run opened.

Tool permissions are an allow-list that matches simple commands only. Issue exactly one plain command per Bash call (`git`, `gh`, `du`, `wc`, `ls`, `find`): no pipes, `;`, `&&`, loops, `$(...)`, or redirects, and use a `-C <path>` or an absolute path instead of `cd`. Compound commands are denied silently, which would leave checks (like whether a PR was merged) undone. If a check still cannot run, put it in `flags` and do not delete anything that depended on it.

If the policy says dry run, change nothing (no deletes, edits, pushes, or PRs) and report what would be done.

End the final message with one fenced `json` block named by the line `REPORT_JSON`:

```json
{"repo": "", "deleted_branches": [], "deleted_worktrees": [], "needs_your_call": [{"item": "", "risk": ""}],
 "disk_reclaimed_mb": 0, "context_edits": [""], "pr": {"url": "", "merged": false, "reason": ""}, "flags": [""]}
```

## Report format

```
## Cleanup report - <repo> @ <date>
1. Context files       - N files, M flagged; proposed edits (table)
2. Branches/worktrees  - delete: [merged: ...] [stale+clean: ...]; needs your call: [...]
3. Disk                - X GB reclaimable; top items
Source-code findings   - pointer to dead-code-cleanup, if any noticed
Approve all / pick items?
```

## Execute and verify

After approval, do the deletions and edits, then re-read state rather than assuming it worked: `git worktree list`, `git branch`, `du -sh` on what was cleared, and `wc -l` on trimmed files. End with what was removed, what was kept and why, and the branch/PR holding any context-file changes.
