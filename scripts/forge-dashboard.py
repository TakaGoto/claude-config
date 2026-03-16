#!/usr/bin/env python3
"""Forge Dashboard — live monitoring for forge workers.

Starts a local HTTP server that polls beads and displays worker status,
ticket progress, and queue health in a browser dashboard.

Usage:
    python forge-dashboard.py [--port PORT]
"""

import argparse
import json
import subprocess
import sys
from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime


DASHBOARD_HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Forge Dashboard</title>
<style>
  :root {
    --bg: #0a0a0a; --surface: #141414; --border: #262626;
    --text: #e5e5e5; --muted: #737373; --accent: #8b5cf6;
    --green: #22c55e; --yellow: #eab308; --red: #ef4444; --blue: #3b82f6;
  }
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body { font-family: 'SF Mono', 'Fira Code', monospace; background: var(--bg); color: var(--text); padding: 24px; }
  h1 { font-size: 20px; font-weight: 600; margin-bottom: 4px; }
  .subtitle { color: var(--muted); font-size: 13px; margin-bottom: 24px; }
  .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(340px, 1fr)); gap: 16px; margin-bottom: 24px; }
  .card { background: var(--surface); border: 1px solid var(--border); border-radius: 8px; padding: 16px; }
  .card-title { font-size: 13px; color: var(--muted); text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 12px; }
  .stat-row { display: flex; justify-content: space-between; align-items: center; padding: 6px 0; }
  .stat-label { color: var(--muted); font-size: 13px; }
  .stat-value { font-size: 14px; font-weight: 600; }
  .badge { display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: 600; }
  .badge-green { background: #22c55e20; color: var(--green); }
  .badge-yellow { background: #eab30820; color: var(--yellow); }
  .badge-red { background: #ef444420; color: var(--red); }
  .badge-blue { background: #3b82f620; color: var(--blue); }
  .badge-muted { background: #73737320; color: var(--muted); }
  table { width: 100%; border-collapse: collapse; font-size: 13px; }
  th { text-align: left; color: var(--muted); font-weight: 500; padding: 8px 12px; border-bottom: 1px solid var(--border); font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px; }
  td { padding: 10px 12px; border-bottom: 1px solid var(--border); vertical-align: top; }
  tr:last-child td { border-bottom: none; }
  .app-tag { display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: 600; background: #8b5cf620; color: var(--accent); }
  .progress-bar { width: 100%; height: 6px; background: var(--border); border-radius: 3px; overflow: hidden; margin-top: 8px; }
  .progress-fill { height: 100%; border-radius: 3px; transition: width 0.5s ease; }
  .worker-card { border-left: 3px solid var(--accent); }
  .worker-card.idle { border-left-color: var(--muted); }
  .ticket-id { color: var(--accent); font-weight: 600; }
  .refresh-info { color: var(--muted); font-size: 11px; position: fixed; bottom: 12px; right: 16px; }
  .empty { color: var(--muted); font-style: italic; padding: 24px; text-align: center; }
  .header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 24px; }
  .header-right { text-align: right; }
  .last-update { color: var(--muted); font-size: 12px; }
  .error-banner { background: #ef444420; border: 1px solid var(--red); color: var(--red); padding: 12px 16px; border-radius: 8px; margin-bottom: 16px; display: none; }
</style>
</head>
<body>

<div class="header">
  <div>
    <h1>Forge Dashboard</h1>
    <div class="subtitle">Live worker monitoring</div>
  </div>
  <div class="header-right">
    <div class="last-update" id="lastUpdate">Connecting...</div>
  </div>
</div>

<div class="error-banner" id="errorBanner"></div>

<!-- Summary cards -->
<div class="grid" id="summaryGrid"></div>

<!-- Active workers -->
<div class="card" style="margin-bottom: 16px;" id="workersCard">
  <div class="card-title">Active Workers</div>
  <div id="workersContent" class="empty">No active workers</div>
</div>

<!-- Queue by app -->
<div class="card" style="margin-bottom: 16px;" id="queueCard">
  <div class="card-title">Queue by App</div>
  <div id="queueContent"></div>
</div>

<!-- All tickets -->
<div class="card" id="ticketsCard">
  <div class="card-title">All Tickets</div>
  <div id="ticketsContent"></div>
</div>

<div class="refresh-info">Auto-refreshes every 15s</div>

<script>
const POLL_INTERVAL = 15000;
let pollTimer = null;

function statusBadge(status) {
  const map = {
    'open': ['Open', 'badge-blue'],
    'in_progress': ['In Progress', 'badge-yellow'],
    'closed': ['Closed', 'badge-green'],
    'blocked': ['Blocked', 'badge-red'],
  };
  const [label, cls] = map[status] || [status, 'badge-muted'];
  return `<span class="badge ${cls}">${label}</span>`;
}

function priorityBadge(p) {
  const map = { 'P0': 'badge-red', 'P1': 'badge-red', 'P2': 'badge-yellow', 'P3': 'badge-blue', 'P4': 'badge-muted' };
  return `<span class="badge ${map[p] || 'badge-muted'}">${p}</span>`;
}

function renderSummary(data) {
  const grid = document.getElementById('summaryGrid');
  const total = data.tickets.length;
  const closed = data.tickets.filter(t => t.status === 'closed').length;
  const inProgress = data.tickets.filter(t => t.status === 'in_progress').length;
  const open = data.tickets.filter(t => t.status === 'open').length;
  const pct = total > 0 ? Math.round((closed / total) * 100) : 0;

  grid.innerHTML = `
    <div class="card">
      <div class="card-title">Overall Progress</div>
      <div class="stat-row"><span class="stat-label">Total tickets</span><span class="stat-value">${total}</span></div>
      <div class="stat-row"><span class="stat-label">Closed</span><span class="stat-value" style="color:var(--green)">${closed}</span></div>
      <div class="stat-row"><span class="stat-label">In progress</span><span class="stat-value" style="color:var(--yellow)">${inProgress}</span></div>
      <div class="stat-row"><span class="stat-label">Open</span><span class="stat-value" style="color:var(--blue)">${open}</span></div>
      <div class="progress-bar"><div class="progress-fill" style="width:${pct}%;background:var(--green)"></div></div>
    </div>
    <div class="card">
      <div class="card-title">Apps</div>
      ${Object.entries(data.apps).map(([app, counts]) => `
        <div class="stat-row">
          <span><span class="app-tag">${app}</span></span>
          <span class="stat-value">${counts.closed}/${counts.total}</span>
        </div>
      `).join('')}
    </div>
  `;
}

function renderWorkers(data) {
  const container = document.getElementById('workersContent');
  const workers = data.tickets.filter(t => t.status === 'in_progress' && t.assignee);

  if (workers.length === 0) {
    container.innerHTML = '<div class="empty">No active workers</div>';
    return;
  }

  container.innerHTML = `<div class="grid">${workers.map(t => `
    <div class="card worker-card">
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px">
        <span class="ticket-id">${t.id}</span>
        <span class="app-tag">${t.app}</span>
      </div>
      <div style="font-size:14px;margin-bottom:8px">${t.title}</div>
      <div class="stat-row"><span class="stat-label">Worker</span><span class="stat-value">${t.assignee || '?'}</span></div>
      <div class="stat-row"><span class="stat-label">Priority</span>${priorityBadge(t.priority)}</div>
      <div class="stat-row"><span class="stat-label">Type</span><span class="badge badge-muted">${t.type || '?'}</span></div>
    </div>
  `).join('')}</div>`;
}

function renderQueue(data) {
  const container = document.getElementById('queueContent');

  if (Object.keys(data.apps).length === 0) {
    container.innerHTML = '<div class="empty">No tickets in queue</div>';
    return;
  }

  container.innerHTML = Object.entries(data.apps).map(([app, counts]) => {
    const pct = counts.total > 0 ? Math.round((counts.closed / counts.total) * 100) : 0;
    return `
      <div style="margin-bottom:16px">
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px">
          <span class="app-tag">${app}</span>
          <span class="stat-value" style="font-size:13px">${counts.closed}/${counts.total} done (${pct}%)</span>
        </div>
        <div style="display:flex;gap:16px;font-size:12px;color:var(--muted);margin-bottom:6px">
          <span>Open: ${counts.open}</span>
          <span>In Progress: ${counts.in_progress}</span>
          <span>Closed: ${counts.closed}</span>
        </div>
        <div class="progress-bar"><div class="progress-fill" style="width:${pct}%;background:var(--accent)"></div></div>
      </div>
    `;
  }).join('');
}

function renderTickets(data) {
  const container = document.getElementById('ticketsContent');

  if (data.tickets.length === 0) {
    container.innerHTML = '<div class="empty">No tickets</div>';
    return;
  }

  // Sort: in_progress first, then open, then closed. Within each group, by priority.
  const order = { 'in_progress': 0, 'open': 1, 'blocked': 2, 'closed': 3 };
  const sorted = [...data.tickets].sort((a, b) => {
    const so = (order[a.status] ?? 9) - (order[b.status] ?? 9);
    if (so !== 0) return so;
    return (a.priority || 'P9').localeCompare(b.priority || 'P9');
  });

  container.innerHTML = `
    <table>
      <thead><tr><th>ID</th><th>App</th><th>Priority</th><th>Status</th><th>Title</th><th>Assignee</th></tr></thead>
      <tbody>
        ${sorted.map(t => `
          <tr style="${t.status === 'closed' ? 'opacity:0.4' : ''}">
            <td class="ticket-id">${t.id}</td>
            <td><span class="app-tag">${t.app}</span></td>
            <td>${priorityBadge(t.priority)}</td>
            <td>${statusBadge(t.status)}</td>
            <td>${t.title}</td>
            <td style="color:var(--muted)">${t.assignee || '-'}</td>
          </tr>
        `).join('')}
      </tbody>
    </table>
  `;
}

async function poll() {
  try {
    const res = await fetch('/api/status');
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();

    document.getElementById('errorBanner').style.display = 'none';
    document.getElementById('lastUpdate').textContent = `Updated: ${new Date().toLocaleTimeString()}`;

    renderSummary(data);
    renderWorkers(data);
    renderQueue(data);
    renderTickets(data);
  } catch (err) {
    const banner = document.getElementById('errorBanner');
    banner.textContent = `Failed to fetch status: ${err.message}`;
    banner.style.display = 'block';
  }
}

poll();
pollTimer = setInterval(poll, POLL_INTERVAL);
</script>
</body>
</html>"""


def get_beads_status():
    """Read beads state and return structured data."""
    try:
        result = subprocess.run(
            ["bd", "list", "--limit", "0", "--json"],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode != 0:
            # Fallback: parse text output
            return parse_text_output()
        raw = json.loads(result.stdout)
        return format_beads_data(raw)
    except (json.JSONDecodeError, FileNotFoundError):
        return parse_text_output()
    except subprocess.TimeoutExpired:
        return {"tickets": [], "apps": {}, "error": "bd command timed out"}


def parse_text_output():
    """Parse bd list text output when --json isn't available or fails."""
    try:
        result = subprocess.run(
            ["bd", "list", "--limit", "0"],
            capture_output=True, text=True, timeout=10
        )
        tickets = []
        for line in result.stdout.strip().split("\n"):
            if not line.strip():
                continue
            # Parse format: ○ punk_records-abc ● P2 [bug] [wicklog] Title here
            # or: ◐ punk_records-abc ● P2 [wicklog] Title here
            ticket = parse_beads_line(line)
            if ticket:
                tickets.append(ticket)

        return build_response(tickets)
    except Exception as e:
        return {"tickets": [], "apps": {}, "error": str(e)}


def parse_beads_line(line):
    """Parse a single beads list line into a ticket dict."""
    line = line.strip()
    if not line:
        return None

    # Determine status from icon
    status = "open"
    if line.startswith("◐") or "in_progress" in line.lower():
        status = "in_progress"
    elif line.startswith("✓") or line.startswith("●"):
        status = "closed"

    # Extract ID
    parts = line.split()
    ticket_id = None
    for p in parts:
        if p.startswith("punk_records-") or p.startswith("bd-"):
            ticket_id = p
            break

    if not ticket_id:
        return None

    # Extract priority
    priority = "P3"
    for p in parts:
        if p in ("P0", "P1", "P2", "P3", "P4"):
            priority = p
            break

    # Extract app name from [app] tag
    app = "unknown"
    import re
    app_match = re.search(r'\[(\w+)\]', line)
    # Skip type tags
    type_tags = {"bug", "feature", "task", "chore"}
    for m in re.finditer(r'\[(\w+)\]', line):
        if m.group(1).lower() not in type_tags:
            app = m.group(1)
            break

    # Extract type
    ticket_type = "task"
    for m in re.finditer(r'\[(\w+)\]', line):
        if m.group(1).lower() in type_tags:
            ticket_type = m.group(1).lower()
            break

    # Extract title (everything after the last ] tag)
    title_match = re.search(r'\]([^[]*?)$', line)
    title = title_match.group(1).strip() if title_match else line

    return {
        "id": ticket_id,
        "status": status,
        "priority": priority,
        "app": app,
        "type": ticket_type,
        "title": title,
        "assignee": None,
    }


def format_beads_data(raw):
    """Format raw JSON beads data."""
    tickets = []
    if isinstance(raw, list):
        for item in raw:
            tickets.append({
                "id": item.get("id", "?"),
                "status": item.get("status", "open"),
                "priority": item.get("priority", "P3"),
                "app": extract_app(item.get("title", "")),
                "type": item.get("type", "task"),
                "title": item.get("title", ""),
                "assignee": item.get("assignee"),
            })
    return build_response(tickets)


def extract_app(title):
    """Extract app name from [app] title prefix."""
    import re
    match = re.search(r'\[(\w+)\]', title)
    type_tags = {"bug", "feature", "task", "chore"}
    for m in re.finditer(r'\[(\w+)\]', title):
        if m.group(1).lower() not in type_tags:
            return m.group(1)
    return "unknown"


def build_response(tickets):
    """Build the API response with tickets and app summaries."""
    apps = {}
    for t in tickets:
        app = t["app"]
        if app not in apps:
            apps[app] = {"total": 0, "open": 0, "in_progress": 0, "closed": 0}
        apps[app]["total"] += 1
        status = t["status"]
        if status in apps[app]:
            apps[app][status] += 1

    return {"tickets": tickets, "apps": apps, "timestamp": datetime.now().isoformat()}


class DashboardHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/":
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(DASHBOARD_HTML.encode())
        elif self.path == "/api/status":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Cache-Control", "no-cache")
            self.end_headers()
            data = get_beads_status()
            self.wfile.write(json.dumps(data).encode())
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        pass  # Suppress request logs


def find_repo_root():
    """Find the nearest git repo root, preferring punk_records."""
    import os
    # Check common locations
    candidates = [
        os.path.expanduser("~/terror/punk_records"),
        os.getcwd(),
    ]
    for path in candidates:
        if os.path.isdir(os.path.join(path, ".git")):
            return path
    # Walk up from cwd
    path = os.getcwd()
    while path != "/":
        if os.path.isdir(os.path.join(path, ".git")):
            return path
        path = os.path.dirname(path)
    return os.getcwd()


def main():
    parser = argparse.ArgumentParser(description="Forge Dashboard")
    parser.add_argument("--port", type=int, default=3141, help="Port to serve on")
    parser.add_argument("--repo", type=str, default=None, help="Path to git repo (auto-detected if omitted)")
    args = parser.parse_args()

    repo = args.repo or find_repo_root()
    import os
    os.chdir(repo)
    print(f"Using repo: {repo}")

    server = HTTPServer(("127.0.0.1", args.port), DashboardHandler)
    url = f"http://localhost:{args.port}"
    print(f"Forge Dashboard running at {url}")
    print("Press Ctrl+C to stop")

    # Open browser
    import webbrowser
    webbrowser.open(url)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nDashboard stopped.")
        server.server_close()


if __name__ == "__main__":
    main()
