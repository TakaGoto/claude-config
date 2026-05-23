---
name: harness
description: "Harness Pattern: builds or modifies apps end-to-end via strict test-driven development — each feature runs through a planner / test-writer (RED) / implementer (GREEN) / refactorer (REFACTOR) / evaluator loop with orchestrator-verified gate checks between phases. Best for multi-feature scope or non-trivial builds. Integrates with beads when available. Use when the user explicitly says 'harness', 'vibe code this', 'run the harness on', asks for an app/feature-set to be built with automated evaluation between sprints, or requests a spec-driven multi-sprint build. Do NOT use for single-file edits, one-off fixes, or quick code changes."
---

# Harness — TDD Planner / Test-Writer / Implementer / Refactorer / Evaluator

You are the Harness orchestrator. You take a task description and build or modify an application using **strict test-driven development**. Each feature goes through a five-stage sprint:

1. **Planner** writes the spec (once, up front).
2. **Test-Writer** writes failing unit tests (RED).
3. **Implementer** writes minimum code to make them pass (GREEN).
4. **Refactorer** improves the code while keeping tests green (REFACTOR).
5. **Evaluator** does a final independent check against success criteria using the sprint-only test command. The orchestrator runs the full verification suite (build/typecheck/full-test/lint) once at Phase 2.8 after every sprint has landed.

The orchestrator runs the test suite between each stage as an independent gate check — agent self-reports are not trusted.

**Arguments:** $ARGUMENTS

The argument is the task description. Examples:
- "a habit tracker with streaks and a calendar view" (new app)
- "add dark mode and a settings page" (existing app)
- "refactor the auth flow to use JWT" (existing app modification)

If no argument is provided, ask the user: "What do you want to build or change? Give me 1-4 sentences."

---

## Core Principles

1. **File-based communication** — agents exchange specs, contracts, and feedback via files in `harness/`, never through conversation memory
2. **Sprint contracts** — every agent in a sprint agrees on testable success criteria and a test command before the sprint starts
3. **Context resets** — each agent spawn is a fresh context with only the harness files as input
4. **Separate writing from evaluation** — the agent that writes tests doesn't write impl; the agent that writes impl doesn't write tests; no agent evaluates its own output
5. **Test-driven** — tests are written before implementation. Tests must be RED before implementation begins, GREEN after implementation, and STILL GREEN after refactoring. The orchestrator verifies each gate by running the test command itself; agent self-reports are double-checked, not trusted.
6. **Beads integration** — when a project has beads, create and track tickets for every sprint
7. **Tight status format** — every status file follows the schema below. Agents are explicitly told to obey it and to never write narrative prose outside the listed sections. Every downstream phase reads these files, so bloat compounds.

---

## Status File Schema (mandatory for all `*-status.md` files)

Every agent that writes `harness/<phase>-status.md` MUST use exactly this layout. No extra prose, no preamble, no closing summary:

```markdown
---
phase: test-writer | implementer | refactorer
sprint: {N}
attempt: {X}
result: RED | GREEN | NO_CHANGES_NEEDED | FAIL
test_command: {the command this agent ran}
tests_total: {N}
tests_passing: {N}
tests_failing: {N}
loc_changed: {N}      # implementer/refactorer only; 0 for NO_CHANGES_NEEDED
---

## Files
- path/one.ts
- path/two.test.ts

## Notes
- ≤5 bullets, ≤120 chars each. Only non-obvious context the next agent needs.
- Forbidden: restating the contract, narrating what was tried, success self-congratulation.
```

When an orchestrator prompt tells an agent to "write your status to harness/<phase>-status.md", that instruction implicitly requires this schema. Reject and re-spawn if a status file deviates (missing frontmatter, prose outside Notes, Notes >5 bullets, or bullets >120 chars).

---

## Phase 0 — Initialize

1. Create the `harness/` directory in the current project root (if it doesn't exist)
2. Detect project context by checking for:
   - Package files: `package.json`, `app.json`, `pyproject.toml`, `Gemfile`, `Cargo.toml`, `go.mod`, `_config.yml`
   - Source directories: `src/`, `app/`, `lib/`, `_layouts/`, `_sass/`, etc.
   - Run `git log --oneline -5` if it's a git repo
3. **Detect beads:** Check if `.beads/` directory exists in the project root. If it does, run `bd list --limit 0` to confirm beads is operational. Set `BEADS_ENABLED=true` for the rest of the run.
4. **Detect a project verification skill:** Check whether `.claude/skills/verify/SKILL.md` exists in the project root. If it does, set `PROJECT_VERIFY=true` — after the sprint loop the orchestrator runs this skill as a whole-app acceptance gate (Phase 2.9). A project verification skill performs checks the per-sprint evaluator structurally cannot — most often a visual/screenshot review of the running app.
5. **Detect architecture/decisions docs:** Probe the repo for the canonical decision-record locations:
   - `docs/adr/`, `docs/adrs/`, `docs/architecture/decisions/`, `architecture/decisions/`
   - `docs/decisions/`, `decisions/`
   - Single-file forms: `DECISIONS.md`, `docs/DECISIONS.md`, `ARCHITECTURE.md`, `docs/architecture.md`
   - Filename patterns: `ADR-*.md`, `[0-9][0-9][0-9][0-9]-*.md` under any `docs/` subtree

   Run a single shell sweep, e.g.:
   ```bash
   ls -d docs/adr docs/adrs docs/architecture/decisions architecture/decisions docs/decisions decisions 2>/dev/null
   ls DECISIONS.md docs/DECISIONS.md ARCHITECTURE.md docs/architecture.md 2>/dev/null
   find docs -maxdepth 4 -type f \( -name 'ADR-*.md' -o -regex '.*/[0-9][0-9][0-9][0-9]-.*\.md' \) 2>/dev/null
   ```

   If any hits come back, set `DOCS_ENABLED=true` and record:
   - `DOCS_KIND`: `adr-dir` (numbered ADR files in a folder), `decisions-file` (single markdown log), or `arch-md` (a freeform ARCHITECTURE.md / decisions.md).
   - `DOCS_PATH`: the chosen path (the directory for `adr-dir`, the file for the others). If multiple candidates exist, prefer the one most recently modified.
   - For `adr-dir`, also note the next ADR number (max existing + 1, zero-padded to match the existing width).

   If nothing matches, set `DOCS_ENABLED=false`. Do NOT invent a docs location — the planner can propose creating one in the spec if the user opts in.
6. Write `harness/idea.md`:
   ```markdown
   # Task

   {user's task description}

   ## Project Context
   - Type: {NEW or EXISTING}
   - Stack: {detected stack or "to be determined"}
   - Key files: {list of important files/dirs found, or "empty project"}
   - Git status: {clean/dirty/not a repo}
   - Beads: {ENABLED or NOT AVAILABLE}
   - Verification skill: {.claude/skills/verify — DETECTED or NONE}
   - Decision docs: {DOCS_KIND at DOCS_PATH, or "NONE detected"}

   Submitted: {YYYY-MM-DD HH:MM}
   ```
7. If not already a git repo, run `git init`

---

## Phase 1 — Planning

Spawn the **planner** agent using the Agent tool with `subagent_type: harness-planner`.

Pass this prompt to the agent:
```
Read harness/idea.md for the task description and project context.
Explore the existing codebase to understand current patterns and conventions.

If idea.md lists a "Decision docs" path, read it before planning — those documents capture
architectural decisions already in force and may constrain or pre-decide parts of this task.
Reference any ADRs that bind the design in the spec's Overview section by ID/title (e.g.
"per ADR-0007 we use Postgres for the event log") so the test-writer and implementer inherit
that context.

For each feature, include a "Documentation Updates" line in the success criteria block:
- the existing ADR/decision files that need amending, OR
- a new ADR to author (with proposed title), OR
- "None — no architectural decision made by this feature".

If no decision docs were detected and a feature in this task introduces a genuine architectural
choice (data store, auth model, framework swap, public contract, etc.), propose creating
`docs/adr/0001-{slug}.md` (or `DECISIONS.md` for very small projects) and note it in the spec
Overview. Do NOT propose docs scaffolding for pure feature work with no architectural import.

Write your output to harness/spec.md.
```

Wait for the planner to complete. Then read `harness/spec.md` to verify it exists and contains:
- Overview
- Feature list (ordered by priority)
- Tech stack
- Success criteria for each feature
- **Documentation Updates** line per feature (existing ADRs to amend, new ADRs to write, or "None")
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

The contract must be **self-contained** — every agent in this sprint should not need to re-read `spec.md`. Extract the feature's full section from `spec.md` and embed it verbatim, along with the Test Strategy and Verification Commands.

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
{3-5 testable criteria copied verbatim from spec.md for this feature. Each must be expressible as a unit test.}
- [ ] Criterion 1
- [ ] Criterion 2
- [ ] Criterion 3

## Key Files (implementation)
{implementation files to create/modify — from spec.md}

## Test Files
{test file paths the test-writer must create — from spec.md's per-feature Test files block}

## Documentation Updates
{copied verbatim from spec.md's "Documentation Updates" line for this feature. One of:
- existing ADR/decision files to amend (with the specific section/heading), OR
- a new ADR to author at {DOCS_PATH}/{NNNN}-{slug}.md with proposed title, OR
- "None — no architectural decision made by this feature"}

## Test Strategy
- **Framework:** {from spec.md, e.g., Vitest, pytest. "None" → orchestrator skips TDD gates and falls back to legacy single-shot impl.}
- **Test command (full suite):** {e.g., `npm test`}
- **Test command (this sprint only):** {how to run just the test files for this sprint, e.g., `npx vitest run src/lib/parser.test.ts`. Used by the orchestrator's gate checks and by every agent's self-check.}

## Input State
{what exists so far — "clean project" for sprint 1, or list of completed feature names and the key files they touched}

## Tech Context
{tech stack from spec.md, key existing files or patterns relevant to this feature}

## Verification Commands
{copied verbatim from spec.md — commands the evaluator must run as the regression check. Example:
- build: `npm run build`
- typecheck: `npx tsc --noEmit`
- test: `npm test`
- lint: `npm run lint`}
```

> **TDD fallback.** If the contract's Test Strategy says `Framework: None`, skip Steps 2b–2d (RED/GREEN/REFACTOR) and run a single implementer-style spawn followed by Step 2e (Evaluate). The rest of this section assumes Test Strategy ≠ None.

> **Gate check protocol.** After each phase agent finishes, the orchestrator runs the contract's "Test command (this sprint only)" itself and parses the result — never just trusting the agent's self-reported numbers. The expected state per gate:
> - **RED gate** (after test-writer): the new tests must fail. If they pass, the sprint is poisoned (the test isn't really testing the criterion, or impl already exists).
> - **GREEN gate** (after implementer): all tests in the sprint must pass.
> - **REFACTOR gate** (after refactorer): all tests in the sprint must still pass — same count and same pass/fail set as the GREEN gate.

#### Step 2b — RED phase (Write failing tests)

Spawn the **test-writer** with `subagent_type: harness-test-writer`.

Prompt (first attempt):
```
Read harness/contract.md (self-contained). Write tests for this feature only — no implementation. Run the "Test command (this sprint only)" and confirm every new test fails. Write status to harness/test-writer-status.md following the Status File Schema (frontmatter + Files + ≤5 Notes bullets, ≤120 chars each).
```

Retry prompt (attempt 2 or 3):
```
Retry {X}. Read harness/test-writer-feedback-attempt-{X-1}.md and fix only what it lists. Edit existing test files in place. Same contract (harness/contract.md). Confirm all new tests fail. Status → harness/test-writer-status.md (schema).
```

After the agent returns, read `harness/test-writer-status.md` and **run the RED gate yourself** with the contract's "Test command (this sprint only)":

- **All tests fail** → RED gate PASS. Continue to Step 2c.
- **Any test passes** → RED gate FAIL. Write `harness/test-writer-feedback.md` describing which test passed and why that's wrong (e.g., "test_returns_total passed — implementation must already exist, or the test is a tautology"). Copy `test-writer-status.md` → `test-writer-status-attempt-{X}.md` and `test-writer-feedback.md` → `test-writer-feedback-attempt-{X}.md`, then re-run Step 2b with the retry prompt. Max 3 attempts. After 3 failed attempts, treat the sprint as failed (jump to Step 2f's "FAIL after 3 attempts" branch).
- **No test files were created** → RED gate FAIL, same retry path.

#### Step 2c — GREEN phase (Implement)

Spawn the **implementer** with `subagent_type: harness-implementer`.

Prompt (first attempt):
```
Read harness/contract.md, harness/test-writer-status.md, and the test files (they are your spec). Write the minimum implementation to make every test pass. Do NOT modify any test file. Run the "Test command (this sprint only)" and confirm all tests pass. Write status to harness/implementer-status.md following the Status File Schema (must include loc_changed).
```

Retry prompt (attempt 2 or 3):
```
Retry {X}. Read harness/implementer-feedback-attempt-{X-1}.md and fix only what it lists. Edit implementation in place; do NOT touch test files. Same contract. Confirm all tests pass. Status → harness/implementer-status.md (schema).
```

After the agent returns, read `harness/implementer-status.md` and **run the GREEN gate yourself**:

- **All tests pass** → GREEN gate PASS. Continue to Step 2d.
- **Any test fails** → GREEN gate FAIL. Also verify the implementer didn't touch any test file (`git diff` against the test paths from `test-writer-status.md` — if test files changed, that alone is a hard FAIL). Write `harness/implementer-feedback.md` listing the failing tests and any test-file tampering. Copy status and feedback to `*-attempt-{X}.md` and re-run Step 2c. Max 3 attempts. After 3 failed attempts, jump to Step 2f's "FAIL after 3 attempts" branch.

#### Step 2d — REFACTOR phase

**Trivial-impl short-circuit.** Read `harness/implementer-status.md`. If `loc_changed < 30` AND `tests_failing == 0`, the refactor spawn is skipped — write a synthetic `harness/refactorer-status.md` with `result: NO_CHANGES_NEEDED`, `loc_changed: 0`, and a one-bullet Note ("auto-skipped: implementation under threshold"). Continue to Step 2e. Saves a full agent context on small features. The threshold can be overridden per-sprint if `contract.md` includes a `refactor: always` line in its frontmatter.

Otherwise, spawn the **refactorer** with `subagent_type: harness-refactorer`.

Prompt (first attempt):
```
Read harness/contract.md, harness/implementer-status.md (your refactor targets), and the test + implementation files. Improve implementation quality with behavior-preserving changes only. Do NOT modify any test file. Run the "Test command (this sprint only)" at the end; same tests must still pass. If code is already clean, set result: NO_CHANGES_NEEDED. Status → harness/refactorer-status.md (schema).
```

Retry prompt (attempt 2 or 3):
```
Retry {X}. Tests broke last time — see harness/refactorer-feedback-attempt-{X-1}.md. Either revert to GREEN and take smaller steps, or set result: NO_CHANGES_NEEDED. Same contract. Tests must stay green. Status → harness/refactorer-status.md (schema).
```

After the agent returns, read `harness/refactorer-status.md` and **run the REFACTOR gate yourself** — re-run the contract's test command:

- **All tests still pass** (same set as GREEN) → REFACTOR gate PASS. Continue to Step 2e.
- **Any test fails** → REFACTOR gate FAIL. Also verify no test files were modified. Write `harness/refactorer-feedback.md` listing what broke. Copy status/feedback to `*-attempt-{X}.md` and re-run Step 2d. Max 3 attempts. If still failing on attempt 3, revert the refactor changes (`git checkout -- {refactorer's Files Changed}`) so the sprint can still ship the GREEN-state implementation, and continue to Step 2e.
- **Status `NO_CHANGES_NEEDED`** → REFACTOR gate PASS by definition (re-run the command anyway as a sanity check). Continue to Step 2e.

#### Step 2e — Evaluate

Spawn the **evaluator** with `subagent_type: harness-evaluator`.

Prompt:
```
Read in order:
1. harness/contract.md — self-contained sprint contract with success criteria
2. harness/test-writer-status.md and the test files
3. harness/implementer-status.md
4. harness/refactorer-status.md
{on retry: 5. harness/feedback-attempt-{X-1}.md — your prior verdict, for continuity}

Verify each success criterion against the actual code. Run ONLY the contract's "Test command (this sprint only)" — do NOT run the full verification suite (build/typecheck/full-test/lint). The orchestrator runs those once cumulatively at Phase 2.8 after all sprints land. Write your results to harness/feedback.md.
```

Wait for completion. Read `harness/feedback.md`.

#### Step 2f — Iterate or Advance

Read the verdict in `harness/feedback.md`:

**If PASS:**
- **Step 2f.1 — Update decision docs.** If the contract's "Documentation Updates" line is not "None", apply it before committing:
  - **Amend existing ADR/decisions file:** open the file at the path listed in the contract and update the relevant section (status, consequences, or a new dated entry in `DECISIONS.md`). Keep the edit small and factual — what changed in this feature, why, and (for ADRs) any superseded decisions.
  - **New ADR:** create the file at the path the contract specifies. Use a minimal template:
    ```markdown
    # ADR-{NNNN}: {Title}

    - Status: Accepted
    - Date: {YYYY-MM-DD}
    - Sprint: harness feature {N} — {feature name}

    ## Context
    {1–3 sentences: what problem the feature created the need to decide}

    ## Decision
    {1–3 sentences: what was chosen}

    ## Consequences
    {bullets: tradeoffs, follow-ups, what becomes harder/easier}
    ```
  - Do these edits inline (orchestrator-level Edit/Write calls) — do not spawn a subagent.
  - Then re-run the contract's "Test command (this sprint only)" once more as a sanity check; docs edits should not affect tests, but a typo in a code-fenced doc that gets imported by tests can. If anything breaks, revert the doc edit and surface it to the user rather than committing.
- Orchestrator commits now (no agent ever commits). Stage only the files listed across `test-writer-status.md` (Test Files Created), `implementer-status.md` (Implementation Files Touched), `refactorer-status.md` (Files Changed), **and any docs files written or amended in Step 2f.1**. Then run `git commit -m "feat: {feature name}"`. Never use `git add -A` / `git add .`.
- Print: "Feature {N}/{total}: {name} — PASSED (commit {short-hash}){, docs updated: {path} if applicable}"
- **If BEADS_ENABLED:** `bd close {ticket-id} --reason "Passed evaluation. Commit: {hash}"`
- Archive the sprint files into `harness/archive/feature-{N}/`: move `contract.md`, `test-writer-status.md`, `implementer-status.md`, `refactorer-status.md`, `feedback.md`, and any `*-attempt-*.md` / `*-feedback*.md`.
- Move to the next feature.

**If FAIL (sprint attempt 1 or 2):**
- Print: "Feature {N}/{total}: {name} — FAILED evaluation (sprint attempt {X}), retrying..."
- **If BEADS_ENABLED:** `bd update {ticket-id} --append-notes "Sprint attempt {X} failed: {summary}"`
- Copy `harness/feedback.md` → `harness/feedback-attempt-{X}.md`.
- Re-run only Step 2c (implementer) with this retry prompt — the tests are the agreed contract, so we don't re-spawn the test-writer:
  ```
  Sprint retry {X}. Evaluator failed verification — see harness/feedback-attempt-{X-1}.md and address its complaints. Same contract, same tests (do NOT modify test files). Confirm all tests pass. Status → harness/implementer-status.md (schema).
  ```
- Re-run the GREEN gate, then Step 2d (REFACTOR), then Step 2e.
- Maximum 3 sprint-level attempts.

**If FAIL (sprint attempt 3):**
- Print: "Feature {N}/{total}: {name} — FAILED after 3 attempts, moving on"
- **If BEADS_ENABLED:** `bd update {ticket-id} --status blocked --append-notes "Failed after 3 attempts. Last feedback: {summary}"`
- Commit the incomplete work so the next feature starts clean: `git commit -m "chore: incomplete {feature name} (see harness/incomplete.md)"`. The failing tests are part of this commit — they document what the feature was supposed to do.
- Append a summary of the failure and the final feedback to `harness/incomplete.md`.
- Archive sprint files into `harness/archive/feature-{N}-incomplete/`.
- Move to the next feature.

---

## Phase 2.8 — Cumulative Verification Gate

After every sprint has landed (PASS or incomplete) and before Phase 2.9, the orchestrator runs the **full** verification suite from `spec.md` — once, not per-sprint:

- `build`, `typecheck`, `lint`, and the **full** test command (not the sprint-only one).

Run each command, capture exit code and a short tail of output, and write `harness/verification.md`:

```markdown
| command | status | notes |
|---|---|---|
| build | PASS | |
| typecheck | PASS | |
| test (full) | FAIL | 2 unrelated suites flaky — see notes |
| lint | PASS | |
```

- **All PASS** → continue to Phase 2.9.
- **Any FAIL** → identify which sprint(s) plausibly introduced the regression (use `git log --oneline` against the failing files). For each suspect sprint, re-open at Step 2c with `harness/verification.md` excerpt as feedback. Max 2 re-openings before surfacing the failure to the user and continuing to Phase 2.9 with the failure noted.

Why this exists: running build/typecheck/full-suite/lint inside every per-sprint evaluator multiplied the heaviest commands by N. Sprint evaluators now run only the sprint-only test command; full-suite checking happens here, once.

---

## Phase 2.9 — Project Verification (only if PROJECT_VERIFY)

After the sprint loop finishes and before the final report, run the project's
own verification skill as a whole-app acceptance gate. This catches issues the
per-sprint evaluator's build / test / lint gates structurally cannot — most
often **visual or UI defects in the running app**.

1. Invoke the project verification skill with the Skill tool:
   - skill: `verify`
   - args: a one-line summary of what this run changed (the feature list from
     `spec.md`), so the skill knows which pages and flows to exercise.
2. The skill runs its own procedure (e.g. boots the app, screenshots the key
   pages, reviews them) and returns a verdict.
3. Record the outcome:
   - **PASS / clean** → note it in `harness/report.md`.
   - **Defects found** → write them into `harness/report.md` under a
     "Project Verification" section and surface them to the user prominently.
     For each defect that maps to a specific feature, offer to re-open that
     sprint at Step 2c (spawn an implementer fix with the defect as feedback).
     Do not report the run as fully passing while project verification has open
     defects.

This phase runs **once per harness run**, not per sprint.

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

## Project Verification
{verdict from the Phase 2.9 verification skill — PASS, or the list of defects found; "Not run" if no project verification skill was detected}

## Decision Docs
{list of ADR/decisions files created or amended during this run, by feature. Format:
- Feature {N} — {feature name}: created `docs/adr/0007-foo.md` / amended `DECISIONS.md` (§ Auth)
- Feature {M} — {feature name}: none

Or "Not tracked — no decision-doc location detected and no new ones authored" if DOCS_ENABLED was false and nothing was created.}

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
