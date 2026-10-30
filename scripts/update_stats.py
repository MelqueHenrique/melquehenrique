#!/usr/bin/env python3
"""Generate an aggregated GitHub profile SVG, including authorized private repositories.

Commit metric: unique commits authored by the account across *all branches* of
owned, non-archived, non-fork repositories during the last 365 days.
No repo names, commit identities, or tokens appear in the published SVG.
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
GRAPHQL = '''query($from: DateTime!, $to: DateTime!) {
  viewer {
    login
    contributionsCollection(from: $from, to: $to) {
      totalPullRequestContributions
      totalIssueContributions
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
    data = json.dumps(payload).encode() if payload is not None else None
    if data is not None:
        headers['Content-Type'] = 'application/json'
    req = urllib.request.Request(url, data=data, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            return json.load(response)
    except urllib.error.HTTPError as exc:
        # Never print auth headers, token, repository paths or private API bodies.
        raise RuntimeError(f'GitHub API returned HTTP {exc.code}') from None


def pages(url, params):
    """Fetch every REST page, erroring rather than silently truncating stats."""
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


def txt(x, y, text, size=14, color='#b7c3d7', weight=400, anchor=None):
    extra = f' text-anchor="{anchor}"' if anchor else ''
    return (f'<text x="{x}" y="{y}" fill="{color}" font-size="{size}" '
            f'font-weight="{weight}"{extra}>{esc(text)}</text>')


def svg(commits, prs, issues, repo_count, langs, generated):
    parts = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="860" height="348" '
        'viewBox="0 0 860 348" role="img" aria-label="GitHub activity dashboard">',
        '<rect x="1" y="1" width="858" height="346" rx="18" fill="#0d1321" '
        'stroke="#293246" stroke-width="2"/>',
        '<rect x="26" y="28" width="5" height="23" rx="2.5" fill="#9a79ff"/>',
        txt(44, 47, 'ACTIVITY OVERVIEW', 19, '#e9effb', 700),
        txt(833, 44, 'LAST 12 MONTHS', 11, '#8d9ab4', 600, 'end'),
    ]
    for i, (label, value) in enumerate([
        ('COMMITS', commits), ('PULL REQUESTS', prs),
        ('ISSUES', issues), ('REPOSITORIES', repo_count)
    ]):
        x = 26 + i * 207
        parts += [
            f'<rect x="{x}" y="72" width="190" height="92" rx="12" '
            'fill="#151e31" stroke="#28334b"/>',
            txt(x + 16, 97, label, 11, '#9eacc5', 600),
            txt(x + 16, 141, str(value), 30, '#ffffff', 700),
        ]
    parts.extend([
        txt(27, 206, 'LANGUAGE DISTRIBUTION', 13, '#dce5f6', 700),
        txt(833, 205, 'AUTHORIZED REPOSITORIES', 11, '#8d9ab4', 500, 'end'),
    ])
    palette = ['#a78bfa', '#56b8f7', '#52d6ae', '#ffbf69', '#fb7185', '#9aa8c0']
    total = sum(n for _, n in langs)
    if total:
        position = 27.0
        for i, (_, amount) in enumerate(langs[:6]):
            width = 806 * amount / total
            parts.append(f'<rect x="{position:.2f}" y="225" width="{width:.2f}" '
                         f'height="15" fill="{palette[i]}"/>')
            position += width
        for i, (name, amount) in enumerate(langs[:6]):
            x, y = 27 + (i % 3) * 268, 278 + (i // 3) * 27
            pct = round(amount * 100 / total, 1)
            parts.extend([
                f'<circle cx="{x + 6}" cy="{y - 5}" r="5" fill="{palette[i]}"/>',
                txt(x + 19, y, f'{name} {pct:g}%', 13, '#c6d2e7', 500),
            ])
    else:
        parts.extend([
            '<rect x="27" y="225" width="806" height="15" rx="6" fill="#293246"/>',
            txt(27, 277, 'No language data available.', 13),
        ])
    parts += [txt(833, 329, f'Updated {generated} UTC • private repositories stay private',
                  11, '#7c8ca6', 400, 'end'), '</svg>']
    return '\n'.join(parts) + '\n'


def get_stats():
    now = dt.datetime.now(dt.timezone.utc)
    since = now - dt.timedelta(days=365)
    data = request(f'{API}/graphql', {'query': GRAPHQL,
                    'variables': {'from': since.isoformat(), 'to': now.isoformat()}})
    if data.get('errors'):
        raise RuntimeError('GraphQL request failed; check token access')
    viewer = data['data']['viewer']
    if viewer['login'].lower() != USERNAME.lower():
        raise RuntimeError('Token belongs to a different GitHub account')
    contributions = viewer['contributionsCollection']

    repos = [repo for repo in pages(f'{API}/user/repos',
             {'affiliation': 'owner', 'visibility': 'all'})
             if not repo.get('fork') and not repo.get('archived')]
    seen_commits = set()  # (repository ID, SHA); avoid counting cross-branch duplicates.
    language_totals = {}
    for repo in repos:
        # GitHub language endpoint gives byte counts, including private repositories.
        for language, byte_count in request(repo['languages_url']).items():
            language_totals[language] = language_totals.get(language, 0) + byte_count

        # REST 'author' filters commit identity by GitHub username. Query each branch
        # because GraphQL's contribution calendar is default-branch-only.
        for branch in pages(repo['branches_url'].split('{')[0], {}):
            for commit in pages(repo['commits_url'].split('{')[0], {
                'sha': branch['name'], 'author': USERNAME,
                'since': since.isoformat(), 'until': now.isoformat(),
            }):
                seen_commits.add((repo['id'], commit['sha']))

    ranking = sorted(language_totals.items(), key=lambda pair: pair[1], reverse=True)
    languages = ranking[:5]
    remaining = sum(amount for _, amount in ranking[5:])
    if remaining:
        languages.append(('Other', remaining))
    # Use a stable date marker, not the exact second, to avoid unneeded commits.
    return (len(seen_commits), contributions['totalPullRequestContributions'],
            contributions['totalIssueContributions'], len(repos), languages,
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
    print(f'Complete: {count} repositories; {commits} unique author commits in last 365 days')


if __name__ == '__main__':
    main()
