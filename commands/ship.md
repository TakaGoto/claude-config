# Ship

Commit, push, and merge the current work in one shot.

## Steps

1. Run `git status` and `git diff --staged` to see what's changed
2. If there are unstaged changes, stage the relevant files (never stage .env, credentials, or secrets)
3. Create a concise commit message based on the changes
4. Commit the changes
5. Push to the remote branch (with `-u` if needed)
6. If a PR already exists for this branch, merge it using `gh pr merge --squash --delete-branch`
7. If no PR exists, create one with `gh pr create` and then merge it
8. After merge, switch back to main and pull latest
9. Report the final status

## Rules

- Never force push
- Never push directly to main
- If there are merge conflicts, stop and report them instead of resolving automatically
- If tests or lint fail on commit hooks, fix the issues and retry
- Skip if there are no changes to commit
