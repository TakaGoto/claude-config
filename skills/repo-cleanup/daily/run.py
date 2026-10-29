"""Daily repo-cleanup runner. Run as: /usr/bin/python3 -I run.py

For each repo in repos.json: run the repo-cleanup skill headlessly (unattended mode), save the
raw `claude -p --output-format json` result, then build one HTML report (tokens, changes, merge
status per repo) at ~/.claude/repo-cleanup/report.html, to be published to one Artifact URL.

Env: REPO_CLEANUP_DRY_RUN=1 (change nothing), REPO_CLEANUP_ONLY=<repo name>, REPO_CLEANUP_BUDGET_USD (per repo, default 3),
     REPO_CLEANUP_PUBLISH=1 (try the headless Artifact step; currently unsupported, see main()).
"""
import datetime, html, json, os, pathlib, re, subprocess

HOME = pathlib.Path.home()
CLAUDE = str(HOME / ".local/bin/claude")
HERE = pathlib.Path(__file__).resolve().parent
BASE = HOME / ".claude/repo-cleanup"
STATE = BASE / "artifact_url"
DRY = os.environ.get("REPO_CLEANUP_DRY_RUN") == "1"
ONLY = os.environ.get("REPO_CLEANUP_ONLY")
BUDGET = os.environ.get("REPO_CLEANUP_BUDGET_USD", "3")
TODAY = datetime.date.today().isoformat()
OUT = BASE / (TODAY + ("-dry" if DRY else ""))

TOOLS = ["Skill", "Read", "Edit", "Write", "Glob", "Grep",
         "Bash(git:*)", "Bash(gh:*)", "Bash(du:*)", "Bash(wc:*)", "Bash(ls:*)", "Bash(find:*)",
         "Bash(ps:*)", "Bash(npm run:*)", "Bash(pnpm run:*)", "Bash(npm test:*)", "Bash(pnpm test:*)"]


def claude(prompt, cwd, tools, budget, timeout):
    cmd = [CLAUDE, "-p", prompt, "--output-format", "json", "--max-budget-usd", str(budget),
           "--permission-mode", "dontAsk", "--no-session-persistence", "--allowedTools", *tools]
    try:
        p = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, stdin=subprocess.DEVNULL, timeout=timeout)
        try:
            return json.loads(p.stdout)
        except ValueError:
            return {"is_error": True, "result": (p.stdout + p.stderr)[-2000:]}
    except subprocess.TimeoutExpired:
        return {"is_error": True, "result": f"timed out after {timeout}s"}


def run_repo(repo):
    path = os.path.expanduser(repo["path"])
    policy = dict(repo, path=path, dry_run=DRY)
    prompt = ("Run the repo-cleanup skill in unattended daily mode for the current repo. "
              f"Policy: {json.dumps(policy)}. Finish with the REPORT_JSON block the skill specifies.")
    res = claude(prompt, path, TOOLS, BUDGET, 2400)
    res["_repo"] = repo["name"]
    (OUT / f"{repo['name']}.json").write_text(json.dumps(res, indent=2))
    return res


def parse_report(text):
    for block in reversed(re.findall(r"```json\s*(\{.*?\})\s*```", text or "", re.S)):
        try:
            return json.loads(block)
        except ValueError:
            continue
    return None


def tokens(res):
    u = res.get("usage") or {}
    parts = {k: u.get(k, 0) for k in ("input_tokens", "cache_creation_input_tokens", "cache_read_input_tokens", "output_tokens")}
    return sum(parts.values()), parts["output_tokens"]


def load_day(d):
    rows = []
    for f in sorted(d.glob("*.json")):
        res = json.loads(f.read_text())
        rows.append((res, parse_report(res.get("result")) or {}))
    return rows


def esc(x):
    return html.escape(str(x))


def lst(items):
    return "<ul>" + "".join(f"<li>{esc(i if not isinstance(i, dict) else ' - '.join(map(str, i.values())))}</li>" for i in items) + "</ul>" if items else '<p class="muted">none</p>'


def pr_status(pr):
    pr = pr or {}
    if pr.get("merged"):
        return '<span class="pill ok">Merged</span>', pr
    if pr.get("url"):
        return '<span class="pill warn">Open, not merged</span>', pr
    return '<span class="pill">No PR</span>', pr


def repo_card(res, rep):
    total, out = tokens(res)
    pill, pr = pr_status(rep.get("pr"))
    link = f'<a href="{esc(pr["url"])}">{esc(pr["url"])}</a>' if str(pr.get("url", "")).startswith("https://") else ""
    err = '<p class="bad">Run failed: ' + esc((res.get("result") or "")[:400]) + "</p>" if res.get("is_error") or not rep else ""
    return f"""<section class="card"><h2>{esc(res['_repo'])} {pill}</h2>{err}
<p class="muted">{total:,} tokens ({out:,} output) · est. ${res.get('total_cost_usd', 0):.2f} ·{res.get('num_turns', '?')} turns</p>
<p>{link} {esc(pr.get('reason', ''))}</p>
<h3>Deleted branches ({len(rep.get('deleted_branches', []))})</h3>{lst(rep.get('deleted_branches', []))}
<h3>Removed worktrees ({len(rep.get('deleted_worktrees', []))})</h3>{lst(rep.get('deleted_worktrees', []))}
<h3>Context files updated</h3>{lst(rep.get('context_edits', []))}
<h3>Needs your call</h3>{lst(rep.get('needs_your_call', []))}
<h3>Flags</h3>{lst(rep.get('flags', []))}
<p class="muted">Disk reclaimed: {esc(rep.get('disk_reclaimed_mb', 0))} MB</p></section>"""


def history():
    rows = []
    for d in sorted(p for p in BASE.iterdir() if p.is_dir())[-14:]:
        day = load_day(d)
        tok = sum(tokens(r)[0] for r, _ in day)
        cost = sum(r.get("total_cost_usd", 0) for r, _ in day)
        merged = sum(1 for _, rep in day if (rep.get("pr") or {}).get("merged"))
        dele = sum(len(rep.get("deleted_branches", [])) + len(rep.get("deleted_worktrees", [])) for _, rep in day)
        rows.append(f"<tr><td>{esc(d.name)}</td><td>{tok:,}</td><td>${cost:.2f}</td><td>{dele}</td><td>{merged}</td></tr>")
    return "".join(reversed(rows))


def build_html(day):
    total = sum(tokens(r)[0] for r, _ in day)
    cost = sum(r.get("total_cost_usd", 0) for r, _ in day)
    merged = sum(1 for _, rep in day if (rep.get("pr") or {}).get("merged"))
    dele = sum(len(rep.get("deleted_branches", [])) + len(rep.get("deleted_worktrees", [])) for _, rep in day)
    mode = " (dry run, nothing changed)" if DRY else ""
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Repo Cleanup Daily</title><style>
:root{{--bg:#fafaf9;--fg:#1c1917;--muted:#78716c;--card:#fff;--line:#e7e5e4;--ok:#15803d;--warn:#b45309;--bad:#b91c1c}}
@media (prefers-color-scheme:dark){{:root:not([data-theme="light"]){{--bg:#161412;--fg:#f5f5f4;--muted:#a8a29e;--card:#1f1c1a;--line:#33302d;--ok:#4ade80;--warn:#fbbf24;--bad:#f87171}}}}
:root[data-theme="dark"]{{--bg:#161412;--fg:#f5f5f4;--muted:#a8a29e;--card:#1f1c1a;--line:#33302d;--ok:#4ade80;--warn:#fbbf24;--bad:#f87171}}
body{{margin:0;background:var(--bg);color:var(--fg);font:15px/1.5 system-ui,sans-serif}}
main{{max-width:880px;margin:0 auto;padding:24px 16px}} h1{{margin:0 0 4px}} h2{{margin:0 0 4px;font-size:1.15rem}} h3{{margin:14px 0 2px;font-size:.9rem;color:var(--muted)}}
.tiles{{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px;margin:16px 0}}
.tile,.card{{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:12px 14px}} .card{{margin:12px 0}}
.tile b{{display:block;font-size:1.5rem}} .muted{{color:var(--muted)}} .bad{{color:var(--bad)}} a{{color:inherit;word-break:break-all}}
.pill{{font-size:.75rem;border:1px solid var(--line);border-radius:99px;padding:1px 8px;margin-left:6px;color:var(--muted)}} .ok{{color:var(--ok)}} .warn{{color:var(--warn)}}
ul{{margin:2px 0;padding-left:20px}} table{{width:100%;border-collapse:collapse}} td,th{{text-align:left;padding:4px 6px;border-bottom:1px solid var(--line)}}
</style></head><body><main>
<h1>Repo Cleanup Daily</h1><p class="muted">{esc(TODAY)}{mode} · generated {esc(datetime.datetime.now().strftime('%H:%M'))}</p>
<div class="tiles"><div class="tile"><b>{total:,}</b>tokens used</div><div class="tile"><b>${cost:.2f}</b>est. cost (not billed)</div>
<div class="tile"><b>{dele}</b>branches + worktrees removed</div><div class="tile"><b>{merged}</b>PRs merged</div></div>
{''.join(repo_card(r, rep) for r, rep in day)}
<h2>Last 14 days</h2><table><tr><th>Day</th><th>Tokens</th><th>Est. cost</th><th>Removed</th><th>Merged</th></tr>{history()}</table>
<p class="muted">Token counts are the cleanup runs only; they include cached input. Runs use the Claude subscription login, so dollar figures are API-equivalent estimates, not charges.</p>
</main></body></html>"""


def publish(report):
    known = STATE.read_text().strip() if STATE.exists() else ""
    how = (f"Publish it as an update to the existing artifact {known}." if known else
           f"Publish it as a new artifact (icon 'chart', description 'Daily repo cleanup: tokens, changes and merge status per repo'), then write the returned artifact URL to {STATE}.")
    res = claude(f"Use the Artifact tool to publish the file {report.name}. {how} Reply with the URL only.",
                 str(BASE), ["Artifact", "Read", "Write"], 1, 600)
    return res.get("result", "")


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    repos = [r for r in json.loads((HERE / "repos.json").read_text()) if not ONLY or r["name"] == ONLY]
    for repo in repos:
        run_repo(repo)
    report = BASE / "report.html"
    report.write_text(build_html(load_day(OUT)))
    print("report:", report)
    # Headless `claude -p` sessions have no Artifact tool (verified 2026-10-29), so publishing is opt-in
    # and only works if that changes. Otherwise publish report.html from an interactive session.
    if os.environ.get("REPO_CLEANUP_PUBLISH") == "1":
        print("artifact:", publish(report))


if __name__ == "__main__":
    main()
