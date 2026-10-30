def svg(commits, prs, issues, repo_count, langs, generated):
    """Cyberpunk netrunner HUD. Uses only real aggregated stats and local SVG shapes."""
    import html as _html

    def text(x, y, value, size=14, color='#c4d6dc', weight=400, anchor=None, spacing=None):
        a = f' text-anchor="{anchor}"' if anchor else ''
        s = f' letter-spacing="{spacing}"' if spacing is not None else ''
        return (f'<text x="{x}" y="{y}" fill="{color}" font-size="{size}" '
                f'font-weight="{weight}"{a}{s}>{_html.escape(str(value))}</text>')

    PINK, CYAN, WHITE, DIM = '#ff245b', '#40e4ee', '#f1eff2', '#7d9aa7'
    W, H = 900, 470
    p = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="GitHub netrunner activity dashboard">',
        '<defs>',
        '<pattern id="scanlines" width="4" height="4" patternUnits="userSpaceOnUse"><path d="M0 3.5H4" stroke="#fff" stroke-opacity=".025"/></pattern>',
        '<pattern id="microgrid" width="32" height="32" patternUnits="userSpaceOnUse"><path d="M32 0H0V32" fill="none" stroke="#4d3350" stroke-opacity=".22" stroke-width=".7"/></pattern>',
        '<linearGradient id="panel" x1="0" y1="0" x2="0" y2="1"><stop stop-color="#11101d"/><stop offset="1" stop-color="#060a12"/></linearGradient>',
        '<clipPath id="barclip"><rect x="36" y="320" width="828" height="23" rx="1"/></clipPath>',
        '</defs>',
        '<rect width="900" height="470" fill="#06060b"/>',
        '<rect x="1" y="1" width="898" height="468" fill="url(#microgrid)" stroke="#92203f" stroke-width="1.4"/>',
        '<rect x="1" y="1" width="898" height="468" fill="url(#scanlines)"/>',
        '<path d="M10 56H465l17 -16H736l14 16H890" fill="none" stroke="#ff245b" stroke-width="1.5"/>',
        '<path d="M12 12H70L55 27H12Z" fill="#ff245b"/>',
        '<path d="M24 15l-7 10m18-10-7 10" stroke="#070a10" stroke-width="4"/>',
        text(84, 36, 'NETRUNNER ACTIVITY // TRACE ROUTE', 21, PINK, 800, spacing='1.2'),
        text(878, 36, 'LAST 12 MONTHS', 12, CYAN, 700, 'end', '.9'),
        '<g fill="#ff245b">' + ''.join(f'<rect x="{585+i*13}" y="20" width="9" height="5" opacity="{.4+i*.11:.2f}"/>' for i in range(5)) + '</g>',
    ]
    cards = [
        ('DATA PACKETS', commits, 'COMMITS.TRANSMITTED'),
        ('ACCESS REQUESTS', prs, 'PULL.REQUESTS'),
        ('SYSTEM FLAGS', issues, 'ISSUES.REPORTED'),
        ('NETWORK NODES', repo_count, 'REPOSITORIES.COUNT'),
    ]
    for i, (label, value, sub) in enumerate(cards):
        x, y, w, h = 18 + i * 221, 76, 209, 150
        path = (f'M{x+10} {y}H{x+w}V{y+h-11}L{x+w-11} {y+h}'
                f'H{x}V{y+10}Z')
        p += [f'<path d="{path}" fill="url(#panel)" stroke="#a71942" stroke-width="1.3"/>',
              f'<path d="M{x} {y+25}V{y+10}L{x+10} {y}H{x+67}" stroke="{PINK}" stroke-width="2" fill="none"/>',
              f'<path d="M{x+w-52} {y+4}H{x+w-14}" stroke="{PINK}" stroke-width="2"/>',
              text(x+18, y+30, label, 13, PINK, 700, spacing='.5'),
              text(x+w-14, y+30, f'[N-0{i+1}]', 9, '#d34672', 600, 'end'),
              text(x+18, y+88, value, 41, WHITE, 800),
              f'<path d="M{x+16} {y+102}H{x+w-16}" stroke="#632440" stroke-width="1"/>',
              # Deterministic technical trace, explicitly decoration rather than fabricated history.
              f'<path d="M{x+16} {y+117}h17l5 -7 7 11 6 -9 9 3 7 -8 8 12 9 -6 8 3 8 -12 8 9 8 -4 9 6 7 -8 9 5 10 -5 7 5" stroke="{CYAN if i%2 else PINK}" fill="none" stroke-width="1.15" opacity=".75"/>',
              text(x+17, y+138, '// '+sub, 9, '#67a5b5', 500),
              f'<rect x="{x+w-38}" y="{y+130}" width="7" height="4" fill="{CYAN}"/>',
              f'<rect x="{x+w-28}" y="{y+130}" width="7" height="4" fill="{CYAN}" opacity=".55"/>',
              f'<rect x="{x+w-18}" y="{y+130}" width="7" height="4" fill="none" stroke="#55808d"/>']
    p += [
        '<path d="M18 247H882V430H18Z" fill="url(#panel)" stroke="#9f1e43" stroke-width="1.3"/>',
        '<rect x="34" y="264" width="5" height="26" fill="#ff245b"/>',
        text(52, 286, 'PROTOCOL DISTRIBUTION', 20, PINK, 800, spacing='.9'),
        text(866, 281, 'LANGUAGE.SCAN.RESULTS', 10, '#6db9c9', 600, 'end'),
        '<path d="M52 297H866" stroke="#542138"/>',
        '<rect x="35" y="318" width="830" height="27" fill="#1a2330" stroke="#9e2450" stroke-width=".8"/>',
        '<g clip-path="url(#barclip)">',
    ]
    palette = ['#9e7cff', '#4cbaf3', '#45d7bc', '#ffb85c', '#f75a80', '#8799b5']
    total = sum(amount for _, amount in langs)
    if total:
        pos = 36.0
        # Group any languages beyond slot six into "Other", preserving 100% of the total.
        visible = list(langs[:5])
        if len(langs) > 5:
            visible.append(('Other', sum(n for _, n in langs[5:])))
        for i, (_, amount) in enumerate(visible):
            width = 828 * amount / total
            p.append(f'<rect x="{pos:.3f}" y="320" width="{width:.3f}" height="23" fill="{palette[i]}"/>')
            pos += width
        p.append('</g>')
        for i, (name, amount) in enumerate(visible):
            x, y = 40 + (i % 3) * 278, 377 + (i // 3) * 30
            pct = 100 * amount / total
            p += [f'<circle cx="{x}" cy="{y-5}" r="5.4" fill="{palette[i]}"/>',
                  text(x+13, y, f'{name} {pct:.1f}%', 13, '#ccdae4', 500)]
    else:
        p += ['</g>', text(42, 382, 'No language data available', 13, DIM)]
    p += [
        '<path d="M12 444H888" stroke="#ba204c" stroke-width="1.2"/>',
        text(25, 460, '>> TRACE COMPLETE // AGGREGATED GITHUB DATA', 10, CYAN, 600),
        text(877, 460, f'UPDATED {generated} UTC // PRIVATE NODES HIDDEN', 9, DIM, 600, 'end'),
        '</svg>',
    ]
    return '\n'.join(p) + '\n'
