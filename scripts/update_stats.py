#!/usr/bin/env python3
"""Private-aware GitHub statistics rendered as a Netrunner-style SVG.

Counts unique authored commit SHAs across branches; PRs and issues opened
by account during last 365 days. SVG exposes only aggregate data.
"""
import datetime as dt
import html
import json
import os
from pathlib import Path
import urllib.error
import urllib.parse
import urllib.request

API = 'https://api.github.com'
TOKEN = os.environ.get('GH_STATS_TOKEN', '')
USERNAME = os.environ.get('GITHUB_USERNAME', 'MelqueHenrique')
OUT = Path(__file__).resolve().parents[1] / 'assets' / 'activity.svg'


def request(url, payload=None):
    headers = {
        'Authorization': f'Bearer {TOKEN}',
        'Accept': 'application/vnd.github+json',
        'User-Agent': 'personal-profile-stats',
        'X-GitHub-Api-Version': '2022-11-28',
    }
    data = json.dumps(payload).encode() if payload is not None else None
    if data is not None:
        headers['Content-Type'] = 'application/json'
    req = urllib.request.Request(url, data=data, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            return json.load(response)
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f'GitHub API returned HTTP {exc.code}') from None


def pages(url, params):
    page = 1
    while True:
        query = urllib.parse.urlencode({**params, 'per_page': 100, 'page': page})
        separator = '&' if '?' in url else '?'
        batch = request(url + separator + query)
        if not isinstance(batch, list):
            raise RuntimeError('Unexpected GitHub API response (expected list)')
        yield from batch
        if len(batch) < 100:
            break
        page += 1


def esc(value):
    return html.escape(str(value), quote=True)


def txt(x, y, value, size=14, color='#d1e7f2', weight=500, anchor=None, spacing=None):
    attrs = (f' text-anchor="{anchor}"' if anchor else '')
    attrs += (f' letter-spacing="{spacing}"' if spacing else '')
    return (f'<text x="{x}" y="{y}" fill="{color}" font-family="Arial, Helvetica, sans-serif" '
            f'font-size="{size}" font-weight="{weight}"{attrs}>{esc(value)}</text>')


def poly(points, fill='none', stroke='#ff1859', sw=1):
    return f'<polygon points="{points}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>'


def svg(commits, prs, issues, repo_count, langs, generated):
    """Static network-trace HUD: all quantities are real; traces are ornamental."""
    pink, cyan, bg, panel = '#ff175b', '#42d6e9', '#070a12', '#0a101b'
    palette = ['#a481ff', '#40b8f5', '#38d9bc', '#ffbd60', '#fc597e', '#91a2b9']
    out = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="1000" height="510" '
        'viewBox="0 0 1000 510" role="img" aria-label="GitHub activity netrunner dashboard">',
        '<rect width="1000" height="510" fill="#05070d"/>',
        '<defs><pattern id="grid" width="25" height="25" patternUnits="userSpaceOnUse">'
        '<path d="M25 0H0V25" fill="none" stroke="#1f2639" stroke-width=".5" opacity=".48"/>'
        '</pattern><pattern id="scan" width="4" height="4" patternUnits="userSpaceOnUse">'
        '<path d="M0 0H4" stroke="#1a2941" stroke-width=".5" opacity=".45"/></pattern></defs>',
        '<rect x="10" y="10" width="980" height="490" fill="url(#grid)" stroke="#a70b3d" stroke-width="1.5"/>',
        '<path d="M10 55H990" stroke="#ff175b" stroke-width="1.3"/>',
        poly('25,24 51,24 38,43 25,43', pink, pink),
        txt(62, 40, 'NETRUNNER ACTIVITY // TRACE ROUTE', 23, pink, 800, spacing='1.5'),
        txt(967, 39, 'LAST 12 MONTHS', 12, cyan, 700, anchor='end', spacing='1'),
        '<rect x="15" y="67" width="970" height="201" fill="none" stroke="#61203e"/>',
    ]
    cards = [('DATA PACKETS', commits, 'COMMITS.TRANSMITTED'),
             ('ACCESS REQUESTS', prs, 'PULL.REQUESTS'),
             ('SYSTEM FLAGS', issues, 'ISSUES.REPORTED'),
             ('ACTIVE NODES', repo_count, 'REPOSITORIES.TRACKED')]
    for i, (label, value, subtitle) in enumerate(cards):
        x = 24 + i * 243
        out.extend([
            f'<path d="M{x+12} 76H{x+220}L{x+231} 87V249L{x+218} 260H{x}V87Z" '
            f'fill="{panel}" stroke="{pink}" stroke-width="1.4"/>',
            f'<path d="M{x} 98V87L{x+12} 76H{x+48}" stroke="{pink}" stroke-width="3" fill="none"/>',
            txt(x+16, 106, label, 13, pink, 750, spacing='.7'),
            txt(x+210, 105, f'[N-{i+1:02d}]', 10, pink, 500, 'end'),
            txt(x+18, 172, value, 49, '#f9f6fa', 800),
            f'<line x1="{x+18}" y1="215" x2="{x+206}" y2="215" stroke="{cyan}" stroke-width="1" opacity=".4"/>',
            txt(x+17, 243, '// '+subtitle, 10, cyan, 600),
        ])
        # Deliberately decorative signal, not fake time-series data.
        coords = ' '.join(f'{x+18+j*8},{206-(j*13+i*7)%10}' for j in range(24))
        out.append(f'<polyline points="{coords}" fill="none" stroke="{cyan if i%2 else pink}" stroke-width="1" opacity=".85"/>')
    out.extend([
        '<path d="M18 280H982V457H18Z" fill="#090e17" stroke="#b50f45" stroke-width="1.2"/>',
        '<rect x="37" y="299" width="6" height="27" fill="#ff175b"/>',
        txt(58, 320, 'PROTOCOL DISTRIBUTION', 23, pink, 800, spacing='1.5'),
        txt(959, 318, 'LANGUAGE.SCAN.RESULTS', 11, cyan, 600, 'end'),
        '<rect x="39" y="342" width="920" height="35" fill="#151e2b" stroke="#8f1541"/>',
    ])
    total = sum(n for _, n in langs)
    if total:
        pos = 40.0
        for i, (_, amount) in enumerate(langs[:6]):
            w = 918 * amount / total
            out.append(f'<rect x="{pos:.2f}" y="343" width="{w:.2f}" height="33" fill="{palette[i]}"/>')
            pos += w
        for i, (name, amount) in enumerate(langs[:6]):
            x, y = 48 + (i % 3) * 310, 409 + (i // 3) * 31
            percentage = round(amount * 100 / total, 1)
            out.extend([
                f'<circle cx="{x}" cy="{y-5}" r="6" fill="{palette[i]}"/>',
                txt(x+17, y, f'{name} {percentage:g}%', 15, '#c9d6ec', 500)
            ])
    else:
        out.append(txt(50, 410, 'NO LANGUAGE DATA', 14, cyan))
    out.extend([
        '<path d="M10 474H990" stroke="#ff175b" stroke-width="1.2"/>',
        txt(30, 491, '>> TRACE COMPLETE  //  NETWORK TELEMETRY', 11, cyan, 600),
        txt(967, 491, 'AUTHORIZED REPOSITORIES // PRIVATE NODES HIDDEN', 10, cyan, 500, 'end'),
        '</svg>'
    ])
    return '\n'.join(out) + '\n'


def count_activity(repos, since):
    """Count user-created PRs and issues. Pulls listed in issues do not double count."""
    prs = 0
    issues = 0
    cutoff = since.strftime('%Y-%m-%dT%H:%M:%SZ')
    for repo in repos:
        pulls_url = repo['pulls_url'].split('{')[0]
        for pr in pages(pulls_url, {'state': 'all', 'sort': 'created', 'direction': 'desc'}):
            if pr['created_at'] < cutoff:
                break
            if pr['user']['login'].casefold() == USERNAME.casefold():
                prs += 1
        issues_url = repo['issues_url'].split('{')[0]
        for issue in pages(issues_url, {'state': 'all', 'sort': 'created', 'direction': 'desc'}):
            if issue['created_at'] < cutoff:
                break
            if 'pull_request' not in issue and issue['user']['login'].casefold() == USERNAME.casefold():
                issues += 1
    return prs, issues


def get_stats():
    now = dt.datetime.now(dt.timezone.utc)
    since = now - dt.timedelta(days=365)
    repos = [repo for repo in pages(f'{API}/user/repos',
             {'affiliation': 'owner', 'visibility': 'all'})
             if not repo.get('fork')]  # Include archived repositories.
    seen_commits = set()
    language_totals = {}
    for repo in repos:
        for language, byte_count in request(repo['languages_url']).items():
            language_totals[language] = language_totals.get(language, 0) + byte_count
        for branch in pages(repo['branches_url'].split('{')[0], {}):
            for commit in pages(repo['commits_url'].split('{')[0], {
                'sha': branch['name'], 'author': USERNAME,
                'since': since.isoformat(), 'until': now.isoformat(),
            }):
                seen_commits.add((repo['id'], commit['sha']))
    prs, issues = count_activity(repos, since)
    ranking = sorted(language_totals.items(), key=lambda pair: pair[1], reverse=True)
    languages = ranking[:5]
    remaining = sum(amount for _, amount in ranking[5:])
    if remaining:
        languages.append(('Other', remaining))
    return (len(seen_commits), prs, issues, len(repos), languages,
            now.strftime('%Y-%m-%d'))


def main():
    if not TOKEN:
        raise SystemExit('Missing GH_STATS_TOKEN environment variable')
    commits, prs, issues, count, languages, date = get_stats()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    output = svg(commits, prs, issues, count, languages, date)
    if not OUT.exists() or OUT.read_text(encoding='utf-8') != output:
        OUT.write_text(output, encoding='utf-8')
        print('Updated SVG')
    else:
        print('No SVG changes')
    print(f'Complete: {count} repositories; {commits} commits; {prs} PRs; {issues} issues (last 365 days)')


if __name__ == '__main__':
    main()
