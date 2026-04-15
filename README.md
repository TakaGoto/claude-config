# claude-config

Claude Code skills, agents, commands, and config — version controlled so a new machine can be productive in one step.

## What's in here

```
skills/     # multi-step workflows (harness, fix, architect, forge, scout)
agents/     # specialized subagents spawned by skills
commands/   # slash commands (/ship, /retro, /brainstorm, etc.)
scripts/    # helper scripts (forge-dashboard)
CLAUDE.md   # global instructions loaded into every session
settings.json  # permissions, env, and plugin config
```

## Quick start on a new machine

```bash
git clone git@github.com:TakaGoto/claude-config.git ~/code/claude-config
cd ~/code/claude-config
./bootstrap.sh
```

The bootstrap script symlinks everything into `~/.claude/`. No files are clobbered — anything that already exists as a real file is skipped and reported. Changes pulled into the repo later are picked up automatically (since everything is a symlink).

To overwrite existing local files with the repo versions (backups are created first):

```bash
./bootstrap.sh --force
```

To install into a different location:

```bash
CLAUDE_DIR=/path/to/claude ./bootstrap.sh
```

## Updating

```bash
cd ~/code/claude-config
git pull
```

Symlinks mean no re-run of `bootstrap.sh` needed for edits to existing files. Re-run it only when new files are added to the repo.

## Machine-local files (not tracked)

After bootstrap, copy these from your previous machine (or create them):

- `~/.claude/settings.local.json` — machine-specific permissions (hostnames, paths)
- `~/.claude/registry.local.md` — Supabase URLs, EAS project IDs, bundle IDs

Both are gitignored for a reason — they contain machine- or account-specific state.

## Featured skills

### `/harness`
Builds or modifies apps end-to-end via a planner/generator/evaluator loop. The planner writes a spec, the generator implements feature-by-feature, and the evaluator tests each feature against success criteria before advancing. Orchestrator-managed commits, per-feature archives, beads integration.

### `/fix`
Debug-and-fix loop: an investigator reproduces the bug and diagnoses root cause, a fixer writes the regression test first and then the fix, and a verifier proves the test actually catches the bug by stash-reverting the fix and confirming the test fails. No fix lands without a test that catches it.

### `/architect`, `/forge`, `/scout`
See individual skill files.

## Contributing to your own config

Edit files in this repo, commit, push. The symlinks on all your machines pick up the change on next `git pull`.
