"""Render assets/activity-blue.svg from the GitHub API: contribution heatmap and stats."""
import json, os, urllib.request
from datetime import date

USER = "sarveshsuhaskute"
TOKEN = os.environ["GH_TOKEN"]


def call(url, body=None):
    req = urllib.request.Request(url, data=json.dumps(body).encode() if body else None,
                                 headers={"Authorization": f"bearer {TOKEN}", "Accept": "application/vnd.github+json"})
    with urllib.request.urlopen(req) as r:
        return json.load(r)


cal = call("https://api.github.com/graphql", {"query": """query($u:String!){user(login:$u){
  contributionsCollection{contributionCalendar{totalContributions weeks{contributionDays{date contributionCount}}}}}}""",
  "variables": {"u": USER}})["data"]["user"]["contributionsCollection"]["contributionCalendar"]
weeks = cal["weeks"]
days = [d for w in weeks for d in w["contributionDays"]]
total = cal["totalContributions"]
best = cur = longest = 0
for d in days:
    cur = cur + 1 if d["contributionCount"] else 0
    longest = max(longest, cur)
active = sum(1 for d in days if d["contributionCount"])

repos = [r for r in call(f"https://api.github.com/users/{USER}/repos?per_page=100&type=owner") if not r["fork"]]

W, CELL, GAP, X0, Y0 = 1200, 17, 4, 40, 96
mx = max((d["contributionCount"] for d in days), default=1) or 1
palette = ["#111111", "#1e3a8a", "#2563eb", "#60a5fa", "#bfdbfe"]


def level(n):
    if n == 0:
        return 0
    r = n / mx
    return 4 if r > 0.75 else 3 if r > 0.5 else 2 if r > 0.25 else 1


cells = []
for wi, w in enumerate(weeks):
    for d in w["contributionDays"]:
        wd = date.fromisoformat(d["date"]).isoweekday() % 7
        x, y = X0 + wi * (CELL + GAP), Y0 + wd * (CELL + GAP)
        n = d["contributionCount"]
        cells.append(f'<rect x="{x}" y="{y}" width="{CELL}" height="{CELL}" rx="4" fill="{palette[level(n)]}"><title>{d["date"]}: {n}</title></rect>')


svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="272" viewBox="0 0 {W} 272" role="img" aria-label="GitHub activity: {total} contributions in the last year, {active} active days, longest streak {longest} days">
<style>text{{font-family:'SF Mono',Menlo,Consolas,'DejaVu Sans Mono',monospace}}</style>
<rect x="1" y="1" width="{W-2}" height="270" rx="18" fill="#000" stroke="#30363d" stroke-width="2"/>
<text x="40" y="52" font-size="26" font-weight="700" fill="#ffffff">{total}</text>
<text x="40" y="74" font-size="13" fill="#8b949e">contributions, last year</text>
<text x="330" y="52" font-size="26" font-weight="700" fill="#ffffff">{active}</text>
<text x="330" y="74" font-size="13" fill="#8b949e">active days</text>
<text x="560" y="52" font-size="26" font-weight="700" fill="#ffffff">{longest}</text>
<text x="560" y="74" font-size="13" fill="#8b949e">day longest streak</text>
<text x="800" y="52" font-size="26" font-weight="700" fill="#ffffff">{len(repos)}</text>
<text x="800" y="74" font-size="13" fill="#8b949e">own repositories</text>
{chr(10).join(cells)}
</svg>'''
open("assets/activity-blue.svg", "w").write(svg)
print("ok", total, active, longest)
