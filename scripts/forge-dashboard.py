#!/usr/bin/env python3
"""Forge Dashboard — live monitoring for forge workers.

Starts a local HTTP server that polls beads and displays worker status,
ticket progress, and queue health in a browser dashboard.

Usage:
    python forge-dashboard.py [--port PORT]
"""

import argparse
import json
import os
import re
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
      <thead><tr><th>ID</th><th>Repo</th><th>App</th><th>Priority</th><th>Status</th><th>Title</th><th>Assignee</th></tr></thead>
      <tbody>
        ${sorted.map(t => `
          <tr style="${t.status === 'closed' ? 'opacity:0.4' : ''}">
            <td class="ticket-id">${t.id}</td>
            <td style="color:var(--muted);font-size:11px">${t.repo || '-'}</td>
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


REPO_DIRS = []  # Set by main() from --repo args


def get_beads_status():
    """Read beads state from all configured repos and return aggregated data."""
    all_tickets = []
    errors = []

    for repo_dir in REPO_DIRS:
        try:
            result = subprocess.run(
                ["bd", "list", "--limit", "0", "--json"],
                capture_output=True, text=True, timeout=10,
                cwd=repo_dir
            )
            if result.returncode != 0 or not result.stdout.strip():
                tickets = parse_text_output_for_repo(repo_dir)
                all_tickets.extend(tickets)
            else:
                raw = json.loads(result.stdout)
                tickets = format_beads_data_list(raw, repo_dir)
                all_tickets.extend(tickets)
        except (json.JSONDecodeError, FileNotFoundError):
            tickets = parse_text_output_for_repo(repo_dir)
            all_tickets.extend(tickets)
        except subprocess.TimeoutExpired:
            errors.append(f"bd timed out for {repo_dir}")

    resp = build_response(all_tickets)
    if errors:
        resp["errors"] = errors
    return resp


def parse_text_output_for_repo(repo_dir):
    """Parse bd list text output for a specific repo."""
    try:
        result = subprocess.run(
            ["bd", "list", "--limit", "0"],
            capture_output=True, text=True, timeout=10,
            cwd=repo_dir
        )
        tickets = []
        repo_name = os.path.basename(repo_dir)
        for line in result.stdout.strip().split("\n"):
            if not line.strip():
                continue
            ticket = parse_beads_line(line, repo_name)
            if ticket:
                tickets.append(ticket)
        return tickets
    except Exception:
        return []


def parse_beads_line(line, repo_name=""):
    """Parse a single beads list line into a ticket dict."""
    line = line.strip()
    if not line or line.startswith("---") or line.startswith("Total:"):
        return None

    # Determine status from icon
    status = "open"
    if line.startswith("\u25d0"):  # ◐
        status = "in_progress"
    elif line.startswith("\u2713"):  # ✓
        status = "closed"

    # Extract ID — match any word-with-hyphens that contains a short hash suffix
    # Formats: punk_records-abc, card-id-23t, bd-a1b2, myproject-xyz
    id_match = re.search(r'(\S+-[a-z0-9]{2,5})\b', line)
    ticket_id = id_match.group(1) if id_match else None

    if not ticket_id:
        return None

    # Extract priority
    priority = "P3"
    priority_match = re.search(r'\b(P[0-4])\b', line)
    if priority_match:
        priority = priority_match.group(1)

    # Extract tags from [brackets]
    type_tags = {"bug", "feature", "task", "chore"}
    tags = re.findall(r'\[([\w-]+)\]', line)

    # First non-type tag is the app name
    app = "unknown"
    for tag in tags:
        if tag.lower() not in type_tags:
            app = tag
            break

    # First type tag is the ticket type
    ticket_type = "task"
    for tag in tags:
        if tag.lower() in type_tags:
            ticket_type = tag.lower()
            break

    # Extract title (everything after the last ] tag)
    title_match = re.search(r'\]([^[\]]*?)$', line)
    title = title_match.group(1).strip() if title_match else line

    return {
        "id": ticket_id,
        "status": status,
        "priority": priority,
        "app": app,
        "type": ticket_type,
        "title": title,
        "assignee": None,
        "repo": repo_name,
    }


def format_beads_data_list(raw, repo_dir):
    """Format raw JSON beads data into a list of tickets."""
    tickets = []
    repo_name = os.path.basename(repo_dir)
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
                "repo": repo_name,
            })
    return tickets


def extract_app(title):
    """Extract app name from [app] title prefix."""
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


def discover_repos():
    """Find all git repos under ~/terror/ that have beads initialized."""
    terror_dir = os.path.expanduser("~/terror")
    repos = []
    if not os.path.isdir(terror_dir):
        return repos
    for entry in os.listdir(terror_dir):
        path = os.path.join(terror_dir, entry)
        if os.path.isdir(path) and os.path.isdir(os.path.join(path, ".git")):
            # Check if beads is initialized (has .beads/ dir)
            if os.path.isdir(os.path.join(path, ".beads")):
                repos.append(path)
    return sorted(repos)


def main():
    global REPO_DIRS

    parser = argparse.ArgumentParser(description="Forge Dashboard")
    parser.add_argument("--port", type=int, default=3141, help="Port to serve on")
    parser.add_argument("--repo", type=str, action="append", default=None,
                        help="Path to git repo (can specify multiple). Auto-discovers all repos under ~/terror/ if omitted.")
    args = parser.parse_args()

    if args.repo:
        REPO_DIRS = [os.path.expanduser(r) for r in args.repo]
    else:
        REPO_DIRS = discover_repos()

    if not REPO_DIRS:
        print("No repos found. Use --repo <path> to specify manually.")
        sys.exit(1)

    print(f"Monitoring {len(REPO_DIRS)} repos:")
    for r in REPO_DIRS:
        print(f"  - {r}")

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
