# Deploy to TestFlight

Bump version, build with EAS, and deploy to TestFlight.

## Steps

1. Check the current version in `app.json` or `app.config.ts`
2. Ask the user: "Bump patch, minor, or major?" (default: patch)
3. Update the version number in the config file
4. Run lint/type-check if available to catch issues before building
5. Commit the version bump: `git add app.json && git commit -m "chore: bump version to X.Y.Z"`
6. Push the commit
7. Run the EAS build:
   ```bash
   eas build --platform ios --profile preview --auto-submit
   ```
8. Report the build URL so the user can monitor progress

## Rules

- Always use `preview` profile for TestFlight (never `production`)
- `--auto-submit` sends the build to TestFlight automatically
- Build numbers auto-increment via EAS remote — do NOT manually set them
- If the build command fails, report the error and suggest fixes
