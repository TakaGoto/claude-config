#!/usr/bin/env python3
"""Forge Dashboard — live monitoring for forge workers.

Starts a local HTTP server that polls beads and displays worker status,
ticket progress, and queue health in a browser dashboard.

Usage:
    python forge-dashboard.py [--port PORT] [--repo PATH ...]
"""

import argparse
import json
import os
import re
import subprocess
import sys
from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime
from urllib.parse import urlparse, parse_qs

REPO_DIRS = []
# Track state changes for activity feed
activity_log = []
prev_statuses = {}


DASHBOARD_HTML = r"""<!DOCTYPE html>
<html lang="en" data-theme="dark">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Forge Dashboard</title>
<link id="favicon" rel="icon" type="image/svg+xml" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>&#x2692;</text></svg>">
<style>
  [data-theme="dark"] {
    --bg: #0a0a0a; --surface: #141414; --surface2: #1a1a1a; --border: #262626;
    --text: #e5e5e5; --muted: #737373; --accent: #8b5cf6;
    --green: #22c55e; --yellow: #eab308; --red: #ef4444; --blue: #3b82f6;
  }
  [data-theme="light"] {
    --bg: #f5f5f5; --surface: #ffffff; --surface2: #fafafa; --border: #e5e5e5;
    --text: #171717; --muted: #737373; --accent: #7c3aed;
    --green: #16a34a; --yellow: #ca8a04; --red: #dc2626; --blue: #2563eb;
  }
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body { font-family: 'SF Mono', 'Fira Code', 'Cascadia Code', monospace; background: var(--bg); color: var(--text); padding: 24px; transition: background 0.3s, color 0.3s; }
  h1 { font-size: 20px; font-weight: 600; margin-bottom: 4px; }
  .subtitle { color: var(--muted); font-size: 13px; }
  .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 16px; margin-bottom: 16px; }
  .card { background: var(--surface); border: 1px solid var(--border); border-radius: 8px; padding: 16px; transition: background 0.3s, border-color 0.3s; }
  .card-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
  .card-title { font-size: 12px; color: var(--muted); text-transform: uppercase; letter-spacing: 0.5px; }
  .stat-row { display: flex; justify-content: space-between; align-items: center; padding: 5px 0; }
  .stat-label { color: var(--muted); font-size: 13px; }
  .stat-value { font-size: 14px; font-weight: 600; transition: color 0.3s; }
  .stat-value.pulse { animation: pulse 0.6s ease; }
  @keyframes pulse { 0%{transform:scale(1)} 50%{transform:scale(1.2)} 100%{transform:scale(1)} }
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
  tr.clickable { cursor: pointer; }
  tr.clickable:hover { background: var(--surface2); }
  .app-tag { display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: 600; background: #8b5cf620; color: var(--accent); }
  .progress-bar { width: 100%; height: 6px; background: var(--border); border-radius: 3px; overflow: hidden; margin-top: 8px; }
  .progress-fill { height: 100%; border-radius: 3px; transition: width 0.8s ease; }
  .worker-card { border-left: 3px solid var(--accent); }
  .ticket-id { color: var(--accent); font-weight: 600; }
  .empty { color: var(--muted); font-style: italic; padding: 20px; text-align: center; }
  .header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 20px; }
  .header-right { display: flex; align-items: center; gap: 12px; }
  .last-update { color: var(--muted); font-size: 12px; }
  .error-banner { background: #ef444420; border: 1px solid var(--red); color: var(--red); padding: 12px 16px; border-radius: 8px; margin-bottom: 16px; display: none; }
  .elapsed { color: var(--yellow); font-size: 12px; font-weight: 600; }
  .eta-card { border-left: 3px solid var(--green); }
  /* Activity feed */
  .feed { max-height: 200px; overflow-y: auto; font-size: 12px; }
  .feed-item { padding: 6px 0; border-bottom: 1px solid var(--border); display: flex; gap: 8px; align-items: baseline; }
  .feed-item:last-child { border-bottom: none; }
  .feed-time { color: var(--muted); flex-shrink: 0; width: 65px; }
  .feed-msg { color: var(--text); }
  .feed-new { animation: fadeIn 0.5s ease; }
  @keyframes fadeIn { from{opacity:0;transform:translateY(-4px)} to{opacity:1;transform:translateY(0)} }
  /* Ticket detail */
  .detail-row { display: none; }
  .detail-row.open { display: table-row; }
  .detail-cell { padding: 12px 16px; background: var(--surface2); font-size: 12px; line-height: 1.6; white-space: pre-wrap; color: var(--muted); }
  /* Toolbar */
  .toolbar { display: flex; gap: 8px; align-items: center; }
  .btn { background: var(--surface); border: 1px solid var(--border); color: var(--text); padding: 4px 10px; border-radius: 4px; font-size: 11px; font-family: inherit; cursor: pointer; transition: all 0.2s; }
  .btn:hover { border-color: var(--accent); color: var(--accent); }
  .btn.active { background: var(--accent); color: white; border-color: var(--accent); }
  .refresh-bar { position: fixed; bottom: 0; left: 0; right: 0; height: 2px; background: var(--border); }
  .refresh-bar-fill { height: 100%; background: var(--accent); transition: width 0.1s linear; width: 0%; }
</style>
</head>
<body>

<div class="header">
  <div>
    <h1>Forge Dashboard</h1>
    <div class="subtitle" id="repoCount">Connecting...</div>
  </div>
  <div class="header-right">
    <div class="toolbar">
      <button class="btn" id="btnHideClosed" onclick="toggleClosed()">Hide Closed</button>
      <button class="btn" id="btnTheme" onclick="toggleTheme()">Light</button>
      <button class="btn" onclick="exportData('json')">JSON</button>
      <button class="btn" onclick="exportData('md')">Markdown</button>
    </div>
    <div class="last-update" id="lastUpdate">--:--:--</div>
  </div>
</div>

<div class="error-banner" id="errorBanner"></div>

<!-- Summary + ETA -->
<div class="grid" id="summaryGrid">
  <div class="card">
    <div class="card-title">Overall Progress</div>
    <div class="stat-row"><span class="stat-label">Total</span><span class="stat-value" id="stat-total">-</span></div>
    <div class="stat-row"><span class="stat-label">Closed</span><span class="stat-value" id="stat-closed" style="color:var(--green)">-</span></div>
    <div class="stat-row"><span class="stat-label">In progress</span><span class="stat-value" id="stat-inprogress" style="color:var(--yellow)">-</span></div>
    <div class="stat-row"><span class="stat-label">Open</span><span class="stat-value" id="stat-open" style="color:var(--blue)">-</span></div>
    <div class="progress-bar"><div class="progress-fill" id="progress-fill-main" style="width:0%;background:var(--green)"></div></div>
  </div>
  <div class="card eta-card">
    <div class="card-title">Estimated Completion</div>
    <div class="stat-row"><span class="stat-label">Avg time/ticket</span><span class="stat-value" id="eta-avg">-</span></div>
    <div class="stat-row"><span class="stat-label">Remaining</span><span class="stat-value" id="eta-remaining">-</span></div>
    <div class="stat-row"><span class="stat-label">ETA</span><span class="stat-value" id="eta-time" style="color:var(--green)">-</span></div>
    <div id="apps-list" style="margin-top:8px"></div>
  </div>
</div>

<!-- Active workers -->
<div class="card" style="margin-bottom: 16px;">
  <div class="card-title">Active Workers</div>
  <div id="workersContent" class="empty">No active workers</div>
</div>

<!-- Queue by app -->
<div class="card" style="margin-bottom: 16px;">
  <div class="card-title">Queue by App</div>
  <div id="queueContent"></div>
</div>

<!-- Activity feed -->
<div class="card" style="margin-bottom: 16px;">
  <div class="card-header">
    <div class="card-title">Activity Feed</div>
    <span style="color:var(--muted);font-size:11px" id="feedCount">0 events</span>
  </div>
  <div class="feed" id="feedContent">
    <div class="empty">No activity yet</div>
  </div>
</div>

<!-- All tickets -->
<div class="card">
  <div class="card-header">
    <div class="card-title">All Tickets</div>
    <span style="color:var(--muted);font-size:11px" id="ticketCount">-</span>
  </div>
  <div id="ticketsContent"></div>
</div>

<div class="refresh-bar"><div class="refresh-bar-fill" id="refreshBar"></div></div>

<script>
const POLL_INTERVAL = 15000;
let prevData = null;
let hideClosed = false;
let startTimes = {};   // id -> timestamp when first seen as in_progress
let closeTimes = [];   // array of durations (ms) for closed tickets
let latestData = null;
let notifPermission = 'default';
let refreshStart = 0;

// Request notification permission
if ('Notification' in window && Notification.permission === 'default') {
  Notification.requestPermission().then(p => notifPermission = p);
} else if ('Notification' in window) {
  notifPermission = Notification.permission;
}

function statusBadge(status) {
  const map = { 'open': ['Open', 'badge-blue'], 'in_progress': ['In Progress', 'badge-yellow'], 'closed': ['Closed', 'badge-green'], 'blocked': ['Blocked', 'badge-red'] };
  const [label, cls] = map[status] || [status, 'badge-muted'];
  return `<span class="badge ${cls}">${label}</span>`;
}

function priorityBadge(p) {
  const map = { 'P0': 'badge-red', 'P1': 'badge-red', 'P2': 'badge-yellow', 'P3': 'badge-blue', 'P4': 'badge-muted' };
  return `<span class="badge ${map[p] || 'badge-muted'}">${p}</span>`;
}

function setText(id, text) {
  const el = document.getElementById(id);
  if (!el || el.textContent === text) return;
  el.textContent = text;
}

function setHTML(id, html) {
  const el = document.getElementById(id);
  if (!el) return;
  if (el._lastHTML !== html) { el.innerHTML = html; el._lastHTML = html; }
}

function animateStat(id, newVal) {
  const el = document.getElementById(id);
  if (!el) return;
  const old = el.textContent;
  if (old !== String(newVal)) {
    el.textContent = newVal;
    el.classList.remove('pulse');
    void el.offsetWidth; // force reflow
    el.classList.add('pulse');
  }
}

function formatDuration(ms) {
  if (!ms || ms < 0) return '-';
  const s = Math.floor(ms / 1000);
  if (s < 60) return `${s}s`;
  const m = Math.floor(s / 60);
  if (m < 60) return `${m}m ${s % 60}s`;
  const h = Math.floor(m / 60);
  return `${h}h ${m % 60}m`;
}

function formatTime(date) {
  return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

// --- Favicon badge ---
function updateFavicon(count) {
  const canvas = document.createElement('canvas');
  canvas.width = 64; canvas.height = 64;
  const ctx = canvas.getContext('2d');
  ctx.font = '42px serif';
  ctx.textAlign = 'center';
  ctx.fillText('\u2692', 32, 44);
  if (count > 0) {
    ctx.fillStyle = '#8b5cf6';
    ctx.beginPath(); ctx.arc(50, 14, 14, 0, Math.PI * 2); ctx.fill();
    ctx.fillStyle = 'white'; ctx.font = 'bold 16px sans-serif';
    ctx.fillText(String(count), 50, 20);
  }
  document.getElementById('favicon').href = canvas.toDataURL();
}

// --- Activity feed ---
let feedItems = [];
function addFeedItem(msg) {
  const now = new Date();
  feedItems.unshift({ time: formatTime(now), msg, ts: now.getTime() });
  if (feedItems.length > 50) feedItems.pop();
  renderFeed();
}

function renderFeed() {
  const el = document.getElementById('feedContent');
  if (feedItems.length === 0) { el.innerHTML = '<div class="empty">No activity yet</div>'; return; }
  el.innerHTML = feedItems.map((f, i) =>
    `<div class="feed-item ${i === 0 ? 'feed-new' : ''}"><span class="feed-time">${f.time}</span><span class="feed-msg">${f.msg}</span></div>`
  ).join('');
  setText('feedCount', feedItems.length + ' events');
}

// --- Detect state changes ---
function detectChanges(data) {
  if (!prevData) return;
  const prevMap = {};
  prevData.tickets.forEach(t => prevMap[t.id] = t);
  const currMap = {};
  data.tickets.forEach(t => currMap[t.id] = t);

  for (const t of data.tickets) {
    const prev = prevMap[t.id];
    if (!prev) {
      addFeedItem(`<span class="ticket-id">${t.id}</span> <span class="app-tag">${t.app}</span> created as ${statusBadge(t.status)}`);
    } else if (prev.status !== t.status) {
      addFeedItem(`<span class="ticket-id">${t.id}</span> <span class="app-tag">${t.app}</span> ${statusBadge(prev.status)} &rarr; ${statusBadge(t.status)}`);
      if (t.status === 'closed' && startTimes[t.id]) {
        closeTimes.push(Date.now() - startTimes[t.id]);
        delete startTimes[t.id];
      }
      if (t.status === 'in_progress' && !startTimes[t.id]) {
        startTimes[t.id] = Date.now();
      }
    }
  }
  // Check for all-done
  const wasAllDone = prevData.tickets.length > 0 && prevData.tickets.every(t => t.status === 'closed');
  const isAllDone = data.tickets.length > 0 && data.tickets.every(t => t.status === 'closed');
  if (isAllDone && !wasAllDone) {
    addFeedItem('<strong style="color:var(--green)">All tickets completed!</strong>');
    notify('Forge Complete', 'All tickets have been closed.');
    playSound();
  }
}

// --- Notification + sound ---
function notify(title, body) {
  if (notifPermission === 'granted') {
    new Notification(title, { body, icon: 'data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><text y=".9em" font-size="90">&#x2692;</text></svg>' });
  }
}

function playSound() {
  try {
    const ctx = new (window.AudioContext || window.webkitAudioContext)();
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();
    osc.connect(gain); gain.connect(ctx.destination);
    osc.frequency.value = 800; gain.gain.value = 0.1;
    osc.start(); osc.stop(ctx.currentTime + 0.15);
    setTimeout(() => { const o2 = ctx.createOscillator(); o2.connect(gain); o2.frequency.value = 1200; o2.start(); o2.stop(ctx.currentTime + 0.15); }, 200);
  } catch(e) {}
}

// --- Theme ---
function toggleTheme() {
  const html = document.documentElement;
  const curr = html.getAttribute('data-theme');
  const next = curr === 'dark' ? 'light' : 'dark';
  html.setAttribute('data-theme', next);
  document.getElementById('btnTheme').textContent = next === 'dark' ? 'Light' : 'Dark';
  localStorage.setItem('forge-theme', next);
}
// Restore theme
(function() {
  const saved = localStorage.getItem('forge-theme');
  if (saved) {
    document.documentElement.setAttribute('data-theme', saved);
    const btn = document.getElementById('btnTheme');
    if (btn) btn.textContent = saved === 'dark' ? 'Light' : 'Dark';
  }
})();

// --- Hide closed ---
function toggleClosed() {
  hideClosed = !hideClosed;
  const btn = document.getElementById('btnHideClosed');
  btn.classList.toggle('active', hideClosed);
  btn.textContent = hideClosed ? 'Show Closed' : 'Hide Closed';
  if (latestData) renderTickets(latestData);
}

// --- Export ---
function exportData(fmt) {
  if (!latestData) return;
  let content, filename, mime;
  if (fmt === 'json') {
    content = JSON.stringify(latestData, null, 2);
    filename = `forge-status-${new Date().toISOString().slice(0,10)}.json`;
    mime = 'application/json';
  } else {
    const s = computeSummary(latestData);
    let md = `# Forge Status — ${new Date().toLocaleString()}\n\n`;
    md += `| Metric | Value |\n|--------|-------|\n`;
    md += `| Total | ${s.total} |\n| Closed | ${s.closed} |\n| In Progress | ${s.inProgress} |\n| Open | ${s.open} |\n\n`;
    md += `## Tickets\n\n| ID | App | Priority | Status | Title |\n|-----|-----|----------|--------|-------|\n`;
    latestData.tickets.forEach(t => { md += `| ${t.id} | ${t.app} | ${t.priority} | ${t.status} | ${t.title} |\n`; });
    if (feedItems.length) {
      md += `\n## Activity Log\n\n`;
      feedItems.forEach(f => { md += `- ${f.time}: ${f.msg.replace(/<[^>]*>/g, '')}\n`; });
    }
    content = md;
    filename = `forge-status-${new Date().toISOString().slice(0,10)}.md`;
    mime = 'text/markdown';
  }
  const blob = new Blob([content], { type: mime });
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob); a.download = filename; a.click();
}

// --- Expand ticket detail ---
async function toggleDetail(id) {
  const row = document.querySelector(`tr.detail-row[data-detail="${id}"]`);
  if (!row) return;
  if (row.classList.contains('open')) { row.classList.remove('open'); return; }
  // Close all others
  document.querySelectorAll('tr.detail-row.open').forEach(r => r.classList.remove('open'));
  const cell = row.querySelector('.detail-cell');
  cell.textContent = 'Loading...';
  row.classList.add('open');
  try {
    const res = await fetch(`/api/ticket?id=${encodeURIComponent(id)}`);
    const data = await res.json();
    cell.textContent = data.detail || 'No details available.';
  } catch(e) { cell.textContent = 'Failed to load: ' + e.message; }
}

// --- Render functions ---
function computeSummary(data) {
  const total = data.tickets.length;
  const closed = data.tickets.filter(t => t.status === 'closed').length;
  const inProgress = data.tickets.filter(t => t.status === 'in_progress').length;
  const open = data.tickets.filter(t => t.status === 'open').length;
  const pct = total > 0 ? Math.round((closed / total) * 100) : 0;
  return { total, closed, inProgress, open, pct };
}

function renderSummary(data) {
  const s = computeSummary(data);
  animateStat('stat-total', s.total);
  animateStat('stat-closed', s.closed);
  animateStat('stat-inprogress', s.inProgress);
  animateStat('stat-open', s.open);
  const fill = document.getElementById('progress-fill-main');
  if (fill) fill.style.width = s.pct + '%';

  // ETA calculation
  const remaining = s.inProgress + s.open;
  const avgMs = closeTimes.length > 0 ? closeTimes.reduce((a,b) => a+b, 0) / closeTimes.length : 0;
  setText('eta-avg', avgMs > 0 ? formatDuration(avgMs) : 'calculating...');
  setText('eta-remaining', String(remaining) + ' tickets');
  if (avgMs > 0 && remaining > 0) {
    const etaMs = avgMs * remaining;
    const etaDate = new Date(Date.now() + etaMs);
    setText('eta-time', formatTime(etaDate) + ` (${formatDuration(etaMs)})`);
  } else if (remaining === 0) {
    setText('eta-time', 'Done!');
  } else {
    setText('eta-time', '-');
  }

  const appsHTML = Object.entries(data.apps).map(([app, counts]) =>
    `<div class="stat-row"><span><span class="app-tag">${app}</span></span><span class="stat-value">${counts.closed}/${counts.total}</span></div>`
  ).join('');
  setHTML('apps-list', appsHTML);

  setText('repoCount', `Monitoring ${Object.keys(data.apps).length} app(s) across ${new Set(data.tickets.map(t=>t.repo)).size || '?'} repo(s)`);
}

function renderWorkers(data) {
  const workers = data.tickets.filter(t => t.status === 'in_progress');
  // Track start times
  workers.forEach(t => { if (!startTimes[t.id]) startTimes[t.id] = Date.now(); });

  if (workers.length === 0) {
    setHTML('workersContent', '<div class="empty">No active workers</div>');
    updateFavicon(0);
    return;
  }
  updateFavicon(workers.length);

  const html = `<div class="grid">${workers.map(t => {
    const elapsed = startTimes[t.id] ? Date.now() - startTimes[t.id] : 0;
    return `
      <div class="card worker-card" data-id="${t.id}">
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px">
          <span class="ticket-id">${t.id}</span>
          <span class="elapsed">${formatDuration(elapsed)}</span>
        </div>
        <div style="font-size:14px;margin-bottom:8px">${t.title}</div>
        <div class="stat-row"><span class="stat-label">App</span><span class="app-tag">${t.app}</span></div>
        <div class="stat-row"><span class="stat-label">Repo</span><span class="stat-value" style="font-size:12px">${t.repo || '-'}</span></div>
        <div class="stat-row"><span class="stat-label">Priority</span>${priorityBadge(t.priority)}</div>
        <div class="stat-row"><span class="stat-label">Type</span><span class="badge badge-muted">${t.type || '?'}</span></div>
      </div>`;
  }).join('')}</div>`;
  setHTML('workersContent', html);
}

function renderQueue(data) {
  if (Object.keys(data.apps).length === 0) {
    setHTML('queueContent', '<div class="empty">No tickets in queue</div>');
    return;
  }
  const html = Object.entries(data.apps).map(([app, counts]) => {
    const pct = counts.total > 0 ? Math.round((counts.closed / counts.total) * 100) : 0;
    return `
      <div style="margin-bottom:16px">
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px">
          <span class="app-tag">${app}</span>
          <span class="stat-value" style="font-size:13px">${counts.closed}/${counts.total} done (${pct}%)</span>
        </div>
        <div style="display:flex;gap:16px;font-size:12px;color:var(--muted);margin-bottom:6px">
          <span>Open: ${counts.open}</span><span>In Progress: ${counts.in_progress}</span><span>Closed: ${counts.closed}</span>
        </div>
        <div class="progress-bar"><div class="progress-fill" style="width:${pct}%;background:var(--accent)"></div></div>
      </div>`;
  }).join('');
  setHTML('queueContent', html);
}

function renderTickets(data) {
  let tickets = data.tickets;
  if (hideClosed) tickets = tickets.filter(t => t.status !== 'closed');

  if (tickets.length === 0) {
    setHTML('ticketsContent', '<div class="empty">No tickets</div>');
    setText('ticketCount', '0');
    return;
  }

  const order = { 'in_progress': 0, 'open': 1, 'blocked': 2, 'closed': 3 };
  const sorted = [...tickets].sort((a, b) => {
    const so = (order[a.status] ?? 9) - (order[b.status] ?? 9);
    if (so !== 0) return so;
    return (a.priority || 'P9').localeCompare(b.priority || 'P9');
  });

  const fingerprint = sorted.map(t => `${t.id}:${t.status}:${t.priority}`).join('|') + (hideClosed ? ':hc' : '');
  const container = document.getElementById('ticketsContent');
  if (container._fingerprint === fingerprint) return;
  container._fingerprint = fingerprint;

  setText('ticketCount', sorted.length + (hideClosed ? ' (closed hidden)' : ''));

  container.innerHTML = `
    <table>
      <thead><tr><th>ID</th><th>Repo</th><th>App</th><th>Priority</th><th>Status</th><th>Title</th></tr></thead>
      <tbody>
        ${sorted.map(t => `
          <tr class="clickable" style="${t.status === 'closed' ? 'opacity:0.4' : ''}" onclick="toggleDetail('${t.id}')">
            <td class="ticket-id">${t.id}</td>
            <td style="color:var(--muted);font-size:11px">${t.repo || '-'}</td>
            <td><span class="app-tag">${t.app}</span></td>
            <td>${priorityBadge(t.priority)}</td>
            <td>${statusBadge(t.status)}</td>
            <td>${t.title}</td>
          </tr>
          <tr class="detail-row" data-detail="${t.id}">
            <td colspan="6" class="detail-cell">Click to load details...</td>
          </tr>
        `).join('')}
      </tbody>
    </table>`;
}

// --- Refresh bar animation ---
function animateRefreshBar() {
  refreshStart = Date.now();
  function tick() {
    const elapsed = Date.now() - refreshStart;
    const pct = Math.min(100, (elapsed / POLL_INTERVAL) * 100);
    const bar = document.getElementById('refreshBar');
    if (bar) bar.style.width = pct + '%';
    if (pct < 100) requestAnimationFrame(tick);
  }
  tick();
}

// --- Elapsed time updater (runs every second) ---
setInterval(() => {
  document.querySelectorAll('.worker-card').forEach(card => {
    const id = card.getAttribute('data-id');
    if (startTimes[id]) {
      const el = card.querySelector('.elapsed');
      if (el) el.textContent = formatDuration(Date.now() - startTimes[id]);
    }
  });
}, 1000);

// --- Poll ---
async function poll() {
  try {
    const res = await fetch('/api/status');
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    latestData = data;

    document.getElementById('errorBanner').style.display = 'none';
    setText('lastUpdate', new Date().toLocaleTimeString());

    detectChanges(data);
    renderSummary(data);
    renderWorkers(data);
    renderQueue(data);
    renderTickets(data);
    prevData = data;
    animateRefreshBar();
  } catch (err) {
    const banner = document.getElementById('errorBanner');
    banner.textContent = 'Failed to fetch: ' + err.message;
    banner.style.display = 'block';
  }
}

poll();
setInterval(poll, POLL_INTERVAL);
</script>
</body>
</html>"""


def get_beads_status():
    """Read beads state from all configured repos and return aggregated data."""
    global prev_statuses, activity_log
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


def get_ticket_detail(ticket_id):
    """Fetch full detail for a single ticket."""
    for repo_dir in REPO_DIRS:
        try:
            result = subprocess.run(
                ["bd", "show", ticket_id],
                capture_output=True, text=True, timeout=10,
                cwd=repo_dir
            )
            if result.returncode == 0 and result.stdout.strip():
                return result.stdout.strip()
        except Exception:
            continue
    return "Ticket not found in any repo."


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

    status = "open"
    if line.startswith("\u25d0"):
        status = "in_progress"
    elif line.startswith("\u2713"):
        status = "closed"

    id_match = re.search(r'(\S+-[a-z0-9]{2,5})\b', line)
    ticket_id = id_match.group(1) if id_match else None
    if not ticket_id:
        return None

    priority = "P3"
    priority_match = re.search(r'\b(P[0-4])\b', line)
    if priority_match:
        priority = priority_match.group(1)

    type_tags = {"bug", "feature", "task", "chore"}
    tags = re.findall(r'\[([\w-]+)\]', line)

    app = "unknown"
    for tag in tags:
        if tag.lower() not in type_tags:
            app = tag
            break

    ticket_type = "task"
    for tag in tags:
        if tag.lower() in type_tags:
            ticket_type = tag.lower()
            break

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
        parsed = urlparse(self.path)
        if parsed.path == "/":
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(DASHBOARD_HTML.encode())
        elif parsed.path == "/api/status":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Cache-Control", "no-cache")
            self.end_headers()
            data = get_beads_status()
            self.wfile.write(json.dumps(data).encode())
        elif parsed.path == "/api/ticket":
            params = parse_qs(parsed.query)
            ticket_id = params.get("id", [""])[0]
            detail = get_ticket_detail(ticket_id) if ticket_id else "No ID provided"
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"id": ticket_id, "detail": detail}).encode())
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        pass


def discover_repos():
    """Find all git repos under ~/terror/ that have beads initialized."""
    terror_dir = os.path.expanduser("~/terror")
    repos = []
    if not os.path.isdir(terror_dir):
        return repos
    for entry in os.listdir(terror_dir):
        path = os.path.join(terror_dir, entry)
        if os.path.isdir(path) and os.path.isdir(os.path.join(path, ".git")):
            if os.path.isdir(os.path.join(path, ".beads")):
                repos.append(path)
    return sorted(repos)


def main():
    global REPO_DIRS

    parser = argparse.ArgumentParser(description="Forge Dashboard")
    parser.add_argument("--port", type=int, default=3141, help="Port to serve on")
    parser.add_argument("--repo", type=str, action="append", default=None,
                        help="Path to git repo (can specify multiple). Auto-discovers if omitted.")
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

    import webbrowser
    webbrowser.open(url)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nDashboard stopped.")
        server.server_close()


if __name__ == "__main__":
    main()
