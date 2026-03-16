# Forge Status

Open the live Forge monitoring dashboard.

## Steps

1. Start the dashboard server in the background:
   ```bash
   nohup python ~/.claude/scripts/forge-dashboard.py --port 3141 > /dev/null 2>&1 &
   echo $!
   ```

2. Open the dashboard: `open http://localhost:3141`

3. Tell the user the dashboard is running and how to stop it:
   - Dashboard URL: http://localhost:3141
   - Auto-refreshes every 15 seconds
   - Stop with: `kill $(lsof -ti:3141)` or Ctrl+C if running in foreground
   - Shows: worker status, ticket progress per app, queue health, all tickets sorted by status

If the port is already in use (another dashboard is running), just open the URL — don't start a second server.

$ARGUMENTS
