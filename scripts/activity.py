"""Render assets/activity.svg from the GitHub API: contribution heatmap, stats and language mix."""
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
langs = {}
for r in repos:
    for k, v in call(r["languages_url"]).items():
        langs[k] = langs.get(k, 0) + v
tot = sum(langs.values()) or 1
top = sorted(langs.items(), key=lambda kv: -kv[1])[:5]

W, CELL, GAP, X0, Y0 = 1200, 17, 4, 40, 96
mx = max((d["contributionCount"] for d in days), default=1) or 1
palette = ["#111111", "#2b2f36", "#4b5159", "#9da7b3", "#ffffff"]


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

bar_y, bar_w, x = 330, W - 80, 40
segs, legend = [], []
shades = ["#ffffff", "#c9d1d9", "#9da7b3", "#6e7681", "#484f58"]
for i, (k, v) in enumerate(top):
    w = bar_w * v / tot
    segs.append(f'<rect x="{x:.1f}" y="{bar_y}" width="{max(w - 3, 2):.1f}" height="14" rx="4" fill="{shades[i]}"/>')
    x += w
    legend.append(f'<g transform="translate({40 + i * 190},368)"><circle cx="6" cy="-4" r="6" fill="{shades[i]}"/><text x="20" y="0" font-size="14" fill="#c9d1d9">{k} {100 * v / tot:.1f}%</text></g>')

svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="400" viewBox="0 0 {W} 400" role="img" aria-label="GitHub activity: {total} contributions in the last year, {active} active days, longest streak {longest} days">
<style>text{{font-family:'SF Mono',Menlo,Consolas,'DejaVu Sans Mono',monospace}}</style>
<rect x="1" y="1" width="{W-2}" height="398" rx="18" fill="#000" stroke="#30363d" stroke-width="2"/>
<text x="40" y="52" font-size="26" font-weight="700" fill="#ffffff">{total}</text>
<text x="40" y="74" font-size="13" fill="#8b949e">contributions, last year</text>
<text x="330" y="52" font-size="26" font-weight="700" fill="#ffffff">{active}</text>
<text x="330" y="74" font-size="13" fill="#8b949e">active days</text>
<text x="560" y="52" font-size="26" font-weight="700" fill="#ffffff">{longest}</text>
<text x="560" y="74" font-size="13" fill="#8b949e">day longest streak</text>
<text x="800" y="52" font-size="26" font-weight="700" fill="#ffffff">{len(repos)}</text>
<text x="800" y="74" font-size="13" fill="#8b949e">own repositories</text>
{chr(10).join(cells)}
<text x="40" y="318" font-size="13" fill="#8b949e">languages across own repositories</text>
{chr(10).join(segs)}
{chr(10).join(legend)}
</svg>'''
open("assets/activity.svg", "w").write(svg)
print("ok", total, active, longest, top)
