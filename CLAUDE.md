# Global Claude Code Instructions

## Security — API Keys & Secrets

- NEVER commit .env files, API keys, tokens, or credentials to git
- If the user pastes an API key in chat, add it to .env or .env.local — never hardcode it
- Always add .env* to .gitignore if not already present
- When configuring new services (Supabase, RevenueCat, etc.), always use environment variables

## Git Workflow

- Never push directly to main
- Create feature branches and PRs for all changes
- Use `/ship` to commit, push, and merge in one step
- Use worktrees for parallel Claude sessions (see per-project CLAUDE.md)

## Mobile App Stack (Expo/React Native)

- Package manager: pnpm (monorepo) or npm (standalone)
- Supabase for auth, database, edge functions
- RevenueCat for in-app purchases and subscriptions
- EAS Build for iOS builds
- TestFlight via `eas build --profile preview --auto-submit`
- Production builds: `eas build --profile production` (NO --auto-submit)

## Work Projects (~/work/)

- Do NOT commit or push without explicit permission
- Keep all changes local unless told otherwise

## Supabase Edge Functions

- Always deploy with `--no-verify-jwt` unless told otherwise:
  ```bash
  supabase functions deploy <function-name> --no-verify-jwt
  ```

## Shared Telemetry & App Registry

- See `registry.local.md` for Supabase URLs, EAS project IDs, bundle IDs, and app-specific infrastructure
- This file is gitignored — copy it manually when setting up a new machine
