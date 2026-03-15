# Bundle Info

Show all project identifiers and config for the current app.

## Steps

1. Find and read `app.json`, `app.config.js`, or `app.config.ts`
2. Find and read `.env`, `.env.local`, `.env.production` files
3. Find and read `eas.json`
4. Display a summary table:

```
App Name:           <name>
Bundle ID:          <ios.bundleIdentifier>
EAS Project ID:     <extra.eas.projectId>
Current Version:    <version>
Supabase URL:       <EXPO_PUBLIC_SUPABASE_URL>
RevenueCat Key:     <test key> (test) / <prod key> (prod)
EAS Profiles:       <list profiles from eas.json>
```

5. Flag any missing or placeholder values that need to be configured
