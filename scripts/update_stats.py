#!/usr/bin/env python3
"""Generate a public SVG summary from authenticated GitHub statistics.
No repository names, source code, or token contents are rendered.
"""
import datetime as dt
import html
import json
import os
from pathlib import Path
import urllib.parse
import urllib.request

API = 'https://api.github.com'
TOKEN = os.environ.get('GH_STATS_TOKEN', '')
USERNAME = os.environ.get('GITHUB_USERNAME', 'MelqueHenrique')
OUT = Path(__file__).resolve().parents[1] / 'assets' / 'activity.svg'
GRAPHQL = '''query($from: DateTime!, $to: DateTime!) {
  viewer {
    login
    contributionsCollection(from: $from, to: $to) {
      totalCommitContributions
      totalPullRequestContributions
      totalIssueContributions
      restrictedContributionsCount
    }
  }
}'''

def request(url, payload=None):
    headers = {
        'Authorization': f'Bearer {TOKEN}',
        'Accept': 'application/vnd.github+json',
        'User-Agent': 'personal-profile-stats',
        'X-GitHub-Api-Version': '2022-11-28',
    }
    data = json.dumps(payload).encode('utf-8') if payload is not None else None
    if data:
        headers['Content-Type'] = 'application/json'
    req = urllib.request.Request(url, data=data, headers=headers)
    with urllib.request.urlopen(req, timeout=30) as response:
        return json.load(response)

def esc(s):
    return html.escape(str(s), quote=True)

def t(x, y, text, size=14, color='#b7c3d7', weight=400, anchor=None):
    a = f' text-anchor="{anchor}"' if anchor else ''
    return f'<text x="{x}" y="{y}" fill="{color}" font-size="{size}" font-weight="{weight}"{a}>{esc(text)}</text>'

def svg(commits, prs, issues, repo_count, langs, generated):
    width, height = 860, 348
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-label="GitHub activity dashboard">',
        '<rect x="1" y="1" width="858" height="346" rx="18" fill="#0d1321" stroke="#293246" stroke-width="2"/>',
        '<rect x="26" y="28" width="5" height="23" rx="2.5" fill="#9a79ff"/>',
        t(44, 47, 'ACTIVITY OVERVIEW', 19, '#e9effb', 700),
        t(833, 44, 'LAST 12 MONTHS', 11, '#8d9ab4', 600, 'end')]
    values = [('COMMITS', commits), ('PULL REQUESTS', prs), ('ISSUES', issues), ('REPOSITORIES', repo_count)]
    for i, (label, value) in enumerate(values):
        x = 26 + i * 207
        parts += [f'<rect x="{x}" y="72" width="190" height="92" rx="12" fill="#151e31" stroke="#28334b"/>',
                  t(x+16, 97, label, 11, '#9eacc5', 600), t(x+16, 141, str(value), 30, '#ffffff', 700)]
    parts += [t(27, 206, 'LANGUAGE DISTRIBUTION', 13, '#dce5f6', 700),
              t(833, 205, 'AUTHORIZED REPOSITORIES', 11, '#8d9ab4', 500, 'end')]
    palette = ['#a78bfa', '#56b8f7', '#52d6ae', '#ffbf69', '#fb7185', '#9aa8c0']
    total = sum(n for _, n in langs)
    if total:
        xx = 27
        for i, (_, n) in enumerate(langs[:6]):
            w = (806 * n / total)
            parts.append(f'<rect x="{xx:.2f}" y="225" width="{max(0,w):.2f}" height="15" fill="{palette[i]}"/>')
            xx += w
        legend = langs[:6]
        for i, (name, n) in enumerate(legend):
            col = i % 3
            row = i // 3
            x, y = 27 + col * 268, 278 + row * 27
            pct = round(n * 100 / total, 1)
            parts += [f'<circle cx="{x+6}" cy="{y-5}" r="5" fill="{palette[i]}"/>', t(x+19, y, f'{name}  {pct:g}%', 13, '#c6d2e7', 500)]
    else:
        parts += ['<rect x="27" y="225" width="806" height="15" rx="6" fill="#293246"/>',
                  t(27, 277, 'Language data will appear after the first successful sync.', 13)]
    parts += [t(833, 329, f'Updated {generated} UTC  •  private repositories stay private', 11, '#7c8ca6', 400, 'end'), '</svg>']
    return '\n'.join(parts) + '\n'

def get_stats():
    now = dt.datetime.now(dt.timezone.utc)
    start = now - dt.timedelta(days=365)
    data = request(f'{API}/graphql', {'query': GRAPHQL, 'variables': {'from': start.isoformat(), 'to': now.isoformat()}})
    if data.get('errors'):
        raise RuntimeError(f'GraphQL returned errors: {data["errors"]}')
    viewer = data['data']['viewer']
    if viewer['login'].lower() != USERNAME.lower():
        raise RuntimeError('GH_STATS_TOKEN belongs to a different account than GITHUB_USERNAME')
    contrib = viewer['contributionsCollection']
    repos = []
    page = 1
    while True:
        query = urllib.parse.urlencode({'affiliation': 'owner', 'visibility': 'all', 'per_page': 100, 'page': page})
        batch = request(f'{API}/user/repos?{query}')
        repos.extend(r for r in batch if not r.get('fork') and not r.get('archived'))
        if len(batch) < 100:
            break
        page += 1
    totals = {}
    for repo in repos:
        # Only aggregated byte counts are retained; repo identities are never output.
        lang_data = request(repo['languages_url'])
        for lang, amount in lang_data.items():
            totals[lang] = totals.get(lang, 0) + amount
    ranking = sorted(totals.items(), key=lambda pair: pair[1], reverse=True)
    # Preserve a correct denominator when there are more than 6 languages.
    top = ranking[:5]
    remainder = sum(n for _, n in ranking[5:])
    if remainder:
        top.append(('Other', remainder))
    return contrib, len(repos), top, now.strftime('%Y-%m-%d')

def main():
    if not TOKEN:
        raise SystemExit('Missing GH_STATS_TOKEN environment variable. No files changed.')
    c, count, langs, date = get_stats()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    output = svg(c['totalCommitContributions'], c['totalPullRequestContributions'], c['totalIssueContributions'], count, langs, date)
    # Check equality, so scheduled Actions do not produce unnecessary commits.
    if not OUT.exists() or OUT.read_text(encoding='utf-8') != output:
        OUT.write_text(output, encoding='utf-8')
        print('Updated SVG')
    else:
        print('No SVG changes')

if __name__ == '__main__':
    main()
