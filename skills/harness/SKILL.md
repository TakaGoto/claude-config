---
name: harness
description: "Harness Pattern: builds or modifies apps end-to-end via a planner/generator/evaluator loop with per-feature sprint contracts. Best for multi-feature scope or non-trivial builds. Integrates with beads when available. Use when the user explicitly says 'harness', 'vibe code this', 'run the harness on', asks for an app/feature-set to be built with automated evaluation between sprints, or requests a spec-driven multi-sprint build. Do NOT use for single-file edits, one-off fixes, or quick code changes."
---

# Harness — Planner / Generator / Evaluator

You are the Harness orchestrator. You take a task description and build or modify an application through three specialized agents: a Planner that writes the spec, a Generator that implements feature-by-feature with git commits, and an Evaluator that tests each feature and provides feedback for iteration.

**Arguments:** $ARGUMENTS

The argument is the task description. Examples:
- "a habit tracker with streaks and a calendar view" (new app)
- "add dark mode and a settings page" (existing app)
- "refactor the auth flow to use JWT" (existing app modification)

If no argument is provided, ask the user: "What do you want to build or change? Give me 1-4 sentences."

---

## Core Principles

1. **File-based communication** — agents exchange specs, contracts, and feedback via files in `harness/`, never through conversation memory
2. **Sprint contracts** — generator and evaluator agree on testable success criteria before each feature sprint
3. **Context resets** — each agent spawn is a fresh context with only the harness files as input
4. **Separate generation from evaluation** — the agent that writes code never evaluates its own output
5. **Beads integration** — when a project has beads, create and track tickets for every sprint

---

## Phase 0 — Initialize

1. Create the `harness/` directory in the current project root (if it doesn't exist)
2. Detect project context by checking for:
   - Package files: `package.json`, `app.json`, `pyproject.toml`, `Gemfile`, `Cargo.toml`, `go.mod`, `_config.yml`
   - Source directories: `src/`, `app/`, `lib/`, `_layouts/`, `_sass/`, etc.
   - Run `git log --oneline -5` if it's a git repo
3. **Detect beads:** Check if `.beads/` directory exists in the project root. If it does, run `bd list --limit 0` to confirm beads is operational. Set `BEADS_ENABLED=true` for the rest of the run.
4. Write `harness/idea.md`:
   ```markdown
   # Task

   {user's task description}

   ## Project Context
   - Type: {NEW or EXISTING}
   - Stack: {detected stack or "to be determined"}
   - Key files: {list of important files/dirs found, or "empty project"}
   - Git status: {clean/dirty/not a repo}
   - Beads: {ENABLED or NOT AVAILABLE}

   Submitted: {YYYY-MM-DD HH:MM}
   ```
5. If not already a git repo, run `git init`

---

## Phase 1 — Planning

Spawn the **planner** agent using the Agent tool with `subagent_type: harness-planner`.

Pass this prompt to the agent:
```
Read harness/idea.md for the task description and project context.
Explore the existing codebase to understand current patterns and conventions.
Write your output to harness/spec.md.
```

Wait for the planner to complete. Then read `harness/spec.md` to verify it exists and contains:
- Overview
- Feature list (ordered by priority)
- Tech stack
- Success criteria for each feature
- **Verification Commands** (build/test/typecheck commands — used as the regression baseline)

If `harness/spec.md` is missing or empty, report the error and stop.

Print a brief summary of the spec to the user: feature count, tech stack, and the feature list. Ask the user if they want to proceed or adjust the spec.

---

## Phase 1.5 — Beads Grooming (only if BEADS_ENABLED)

After the user approves the spec, create and groom beads tickets for each feature.

### Step 1: Create tickets in dependency order

For each feature in the spec (in implementation order), create a beads ticket:

```bash
bd create "[harness] Feature N: {feature name}" \
  -p P2 \
  -t feature \
  -d "{feature description from spec}

Success Criteria:
{copy the success criteria from spec.md for this feature}

Key Files:
{list of files to create/modify}

Sprint: {N} of {total}
Depends on: {previous feature ticket ID, if any}" \
  -l harness
```

Use P1 for the first feature (foundation work) and P2 for the rest. Use `-t task` instead of `-t feature` for refactoring or cleanup work.

### Step 2: Set dependencies

After all tickets are created, set dependency chains so they must be worked in order:

```bash
bd update {ticket-2-id} --dep {ticket-1-id}
bd update {ticket-3-id} --dep {ticket-2-id}
# ... and so on
```

### Step 3: Groom the tickets

Review each ticket and improve the descriptions:
- Make sure the description is specific enough that a generator agent can implement it without ambiguity
- Add file paths, function names, and patterns from the existing codebase where relevant
- Add sizing hints using `bd update {id} --append-notes "Size: [s|m|l], Pattern: {description}"`
- Verify the order makes sense (dependencies first, quick wins early where possible)

### Step 4: Print the groomed backlog

Run `bd list --limit 0` and print the ticket list to the user so they can see the backlog before sprints begin.

---

## Phase 2 — Sprint Loop

Read `harness/spec.md` and extract the ordered feature list. For each feature, run a generate-evaluate sprint.

### For each feature (in order):

#### Step 2a — Write the Sprint Contract

**If BEADS_ENABLED:** Run `bd ready --json` and pick the next unblocked ticket. Claim it with `bd update {id} --claim`.

The contract must be **self-contained** — the generator and evaluator should not need to re-read `spec.md`. Extract the feature's full section from `spec.md` and embed it verbatim, along with the Verification Commands block.

Write `harness/contract.md`:

```markdown
# Sprint Contract

## Feature
{feature name and description — copy verbatim from spec.md}

## Beads Ticket
{ticket ID, or "N/A" if beads not enabled}

## Sprint Number
{N} of {total features}

## Success Criteria
{3-5 testable criteria copied verbatim from spec.md for this feature}
- [ ] Criterion 1
- [ ] Criterion 2
- [ ] Criterion 3

## Key Files
{files to create/modify — from spec.md}

## Input State
{what exists so far — "clean project" for sprint 1, or list of completed feature names and the key files they touched}

## Tech Context
{tech stack from spec.md, key existing files or patterns relevant to this feature}

## Verification Commands
{copied verbatim from spec.md — commands the evaluator must run. Example:
- build: `npm run build`
- typecheck: `npx tsc --noEmit`
- test: `npm test`}
```

#### Step 2b — Generate

Spawn the **generator** agent with `subagent_type: harness-generator`.

Pass this prompt (first attempt):
```
Read harness/contract.md — it is self-contained with everything you need (feature description, success criteria, key files, tech context, verification commands).
Only read harness/spec.md if the contract references something you need to cross-check.

Implement the feature. Do NOT commit — the orchestrator handles commits after evaluation passes.
Write your status to harness/generator-status.md when done.
```

On a retry (attempt 2 or 3), pass instead:
```
This is retry attempt {X}. Read in order:
1. harness/contract.md — sprint contract (self-contained)
2. harness/generator-status-attempt-{X-1}.md — what you tried last time
3. harness/feedback.md — evaluator's feedback on that attempt. Fix the issues.

Your previous changes are still in the working tree — edit them, do not start over unless feedback says to.
Do NOT commit. Write your status to harness/generator-status.md when done.
```

Wait for completion. Verify `harness/generator-status.md` exists.

#### Step 2c — Evaluate

Spawn the **evaluator** agent with `subagent_type: harness-evaluator`.

Pass this prompt:
```
Read these files in order:
1. harness/contract.md — self-contained sprint contract with success criteria and verification commands
2. harness/generator-status.md — what the generator claims it did
{on retry: 3. harness/generator-status-attempt-{X-1}.md and harness/feedback-attempt-{X-1}.md — prior attempt + your prior feedback, for continuity}

Test the implementation against the success criteria. Run every command in the contract's Verification Commands block as the regression check. Write your results to harness/feedback.md.
```

Wait for completion. Read `harness/feedback.md`.

#### Step 2d — Iterate or Advance

Read the verdict in `harness/feedback.md`:

**If PASS:**
- Orchestrator commits now (generator never commits): stage only the files the generator touched (parse them from `generator-status.md`) and run `git commit -m "feat: {feature name}"`. Never use `git add -A`/`git add .`.
- Print to user: "Feature {N}/{total}: {name} — PASSED (commit {short-hash})"
- **If BEADS_ENABLED:** Close the ticket: `bd close {ticket-id} --reason "Passed evaluation. Commit: {hash}"`
- Archive the sprint files into `harness/archive/feature-{N}/` (move `contract.md`, `generator-status.md`, `feedback.md`, and any `*-attempt-*.md`). Keeps history for debugging without polluting the active workspace.
- Move to the next feature

**If FAIL (attempt 1 or 2):**
- Print to user: "Feature {N}/{total}: {name} — FAILED (attempt {X}), retrying..."
- **If BEADS_ENABLED:** Add note: `bd update {ticket-id} --append-notes "Attempt {X} failed: {summary of feedback}"`
- Copy `harness/feedback.md` → `harness/feedback-attempt-{X}.md`
- Copy `harness/generator-status.md` → `harness/generator-status-attempt-{X}.md` (preserves what the generator tried; the retry prompt references it)
- Leave the working tree as-is (no commits to revert — generator never committed). The retry edits the same files.
- Re-run Step 2b with the retry prompt variant
- Then re-run Step 2c
- Maximum 3 attempts per feature

**If FAIL (attempt 3):**
- Print to user: "Feature {N}/{total}: {name} — FAILED after 3 attempts, moving on"
- **If BEADS_ENABLED:** Update ticket: `bd update {ticket-id} --status blocked --append-notes "Failed after 3 attempts. Last feedback: {summary}"`
- Commit the incomplete work so subsequent features start from a clean tree: `git commit -m "chore: incomplete {feature name} (see harness/incomplete.md)"`. This preserves the code but marks it clearly in git log.
- Append a summary of the failure and the final feedback to `harness/incomplete.md`
- Archive sprint files into `harness/archive/feature-{N}-incomplete/`
- Move to the next feature

---

## Phase 3 — Final Report

After all features are attempted, write `harness/report.md`:

```markdown
# Harness Report

## Task
{original task description}

## Tech Stack
{from spec}

## Beads
{ENABLED — tickets created and tracked | NOT AVAILABLE}

## Results
| # | Feature | Beads ID | Attempts | Status |
|---|---------|----------|----------|--------|
| 1 | {name} | {id} | 1 | PASS |
| 2 | {name} | {id} | 3 | FAIL — {reason} |

## Summary
- Features attempted: {N}
- Features completed: {N}
- Total sprints run: {N}

## Incomplete Features
{list with failure reasons, or "None"}

## Next Steps
{suggestions from evaluator feedback}
```

Print the report summary to the user.

---

## Safety Guardrails

- **NEVER** push to remote unless the user explicitly asks
- **NEVER** modify files outside the project directory (except harness/ files)
- **NEVER** run destructive git operations (force push, reset --hard)
- **NEVER** use `bd edit` (interactive, incompatible with agents)
- **Maximum 3 iterations per feature** — prevents infinite loops
- **Maximum 10 features per run** — if the spec has more, stop after 10 and note the rest
- **Ask user before proceeding** after Phase 1 (spec review)
