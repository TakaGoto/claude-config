# Deploy

Deploy the current project to its target platform. Auto-detects the deployment method from the project config.

**Arguments:** $ARGUMENTS
Parse arguments:
- `--platform <name>`: Override platform detection (e.g., `ios`, `web`, `worker`)
- `--profile <name>`: Build profile (e.g., `preview`, `production`). Default: `preview`
- `--dry-run`: Show what would be deployed without actually deploying

## Steps

### 1. Detect Deployment Target

Read the project config to determine the deployment method:

| Config File | Platform | Deploy Command |
|------------|----------|----------------|
| `eas.json` | Expo/iOS | `eas build --platform ios --profile {profile}` |
| `wrangler.toml` | Cloudflare Workers | `wrangler deploy` |
| `vercel.json` or `next.config.*` | Vercel | `vercel deploy` (or `vercel --prod` for production) |
| `fly.toml` | Fly.io | `fly deploy` |
| `Dockerfile` | Docker | `docker build && docker push` |
| `netlify.toml` | Netlify | `netlify deploy` (or `--prod`) |

If multiple config files exist, ask the user which target to deploy.

### 2. Pre-Deploy Checks

Before deploying:
- Run quality gates (type-check, lint, build) if available in `package.json` scripts
- Check for uncommitted changes — warn if working tree is dirty
- Check that the current branch is appropriate for the profile (e.g., don't deploy `main` as `preview`)
- Verify environment variables are set (check `.env`, `.env.local`, or platform secrets)

### 3. Platform-Specific Deploy

**Expo/iOS (EAS):**
- `preview` profile: `eas build --platform ios --profile preview --auto-submit` (goes to TestFlight)
- `production` profile: `eas build --platform ios --profile production` (NO `--auto-submit`)
- After production build: remind user to run `eas submit --platform ios --id <build-id>` when ready
- Report the build URL for monitoring

**Cloudflare Workers:**
- Run `wrangler deploy`
- Report the deployed URL

**Vercel:**
- Preview: `vercel deploy`
- Production: `vercel deploy --prod`
- Report the deployment URL

**Other platforms:**
- Run the detected deploy command
- Report the result

### 4. Post-Deploy

- Report the deployment URL or build status
- If deploying to a preview/staging environment, remind user to test before promoting to production
- If `--dry-run`, just print what would have been executed

## Rules

- Never deploy production without confirming with the user first
- Never use `--auto-submit` for production EAS builds
- Always run quality gates before deploying
- If any quality gate fails, stop and report the error — do not deploy broken code
