#!/usr/bin/env python3
"""Audio design diagrams."""

BOX = ('fill="var(--surface)" stroke="var(--rule-strong)" stroke-width="1.4" rx="3"')


def flow_svg():
    p = []
    A = p.append
    A('<svg viewBox="0 0 720 372" role="img" aria-label="Signal flow from sources through DCAs '
      'and buses to the loudspeaker systems.">')
    A('<defs><marker id="ar" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" '
      'orient="auto"><path d="M0 0 L10 5 L0 10 z" fill="var(--ink-3)"/></marker></defs>')

    cols = [
        (14, 'CHANNELS', [
            ('Ch 1&ndash;14', 'principals'), ('Ch 15&ndash;19', 'ens. male'),
            ('Ch 20&ndash;24', 'ens. female'), ('Ch 25&ndash;26', 'orchestra'),
            ('FX 1&ndash;7', 'returns')]),
        (186, 'GROUP + bus comp', [
            ('Group 1', 'mono &middot; comp'), ('Group 2', 'stereo &middot; comp'),
            ('Group 3', 'stereo &middot; comp'), ('Group 4', 'stereo &middot; comp'),
            ('Group 5', 'stereo &middot; no comp')]),
        (358, 'DCA &mdash; fixed', [
            ('DCA 1', 'principals'), ('DCA 2', 'ensemble male'),
            ('DCA 3', 'ensemble female'), ('DCA 4', 'orchestra'), ('DCA 5', 'FX returns')]),
        (530, 'LR &rarr; OUT', [
            ('Matrix 1', 'flown arrays'), ('Matrix 2', 'front fill'),
            ('Matrix 3&ndash;4', 'backstage / DR'), ('Matrix 5&ndash;7', 'rec / stream / 2-trk'),
            ('Mix 1&ndash;10', 'monitors, surr, subs')]),
    ]
    W, H, GAP = 158, 42, 14
    for x, title, rows in cols:
        A(f'<text x="{x:.0f}" y="32" class="svg-label" style="font-weight:600;letter-spacing:.1em">{title}</text>')
        for i, (a_, b_) in enumerate(rows):
            if not a_:
                continue
            y = 46 + i * (H + GAP)
            A(f'<rect x="{x}" y="{y}" width="{W}" height="{H}" {BOX}/>')
            A(f'<text x="{x+11}" y="{y+18}" class="svg-label">{a_}</text>')
            A(f'<text x="{x+11}" y="{y+33}" class="svg-label sm">{b_}</text>')

    for x0 in (172, 344, 516):
        for i in range(5):
            y = 46 + i * (H + GAP) + H / 2
            A(f'<line x1="{x0}" y1="{y:.0f}" x2="{x0+26}" y2="{y:.0f}" stroke="var(--ink-3)" '
              'stroke-width="1.2" marker-end="url(#ar)"/>')
    A('</svg>')
    cap = ('Signal flow. Channels sum into five audio <strong>Groups</strong> &mdash; which is where the '
           'bus compressors live, because a Group is a bus the signal actually passes through &mdash; and '
           'each Group is driven by one <strong>DCA</strong>, which is a control link rather than an audio '
           'path. All five Groups feed LR, so LR is the sum of five faders. The scene&rsquo;s level map '
           'decides who is open, glided over one second; the operator only ever decides how loud.')
    return ('\n  <figure>\n    <div class="figbox">\n      ' + ''.join(p) +
            f'\n    </div>\n    <figcaption>{cap}</figcaption>\n  </figure>')


def coverage_svg():
    """Section: array, fill and surround coverage with delay callouts."""
    PY = 5.4
    FLOOR = 258.0
    X0 = -95.0
    sx = lambda z: 22.0 + (z - X0) * 6.0
    sy = lambda y: FLOOR - y * PY

    p = []
    A = p.append
    A('<svg viewBox="0 40 720 258" role="img" aria-label="Section showing the flown array, front '
      'fill and surround coverage with delay times.">')

    # rake / floor
    A(f'<line x1="{sx(-95):.1f}" y1="{sy(0):.1f}" x2="{sx(-7):.1f}" y2="{sy(0):.1f}" '
      'stroke="var(--ink-3)" stroke-width="2"/>')
    A(f'<path d="M{sx(-7):.1f} {sy(0):.1f} V{sy(3.5):.1f} H{sx(12):.1f}" fill="none" '
      'stroke="var(--ink)" stroke-width="2.5"/>')
    A(f'<text x="{sx(11):.1f}" y="{sy(3.5)+16:.1f}" text-anchor="end" class="svg-label sm">STAGE</text>')

    # coverage wedges
    A(f'<path d="M{sx(2):.1f} {sy(25.5):.1f} L{sx(-88):.1f} {sy(0):.1f} L{sx(-30):.1f} {sy(0):.1f} Z" '
      'fill="var(--accent)" opacity=".13"/>')
    A(f'<path d="M{sx(-7):.1f} {sy(4.5):.1f} L{sx(-34):.1f} {sy(0):.1f} L{sx(-9):.1f} {sy(0):.1f} Z" '
      'fill="var(--good)" opacity=".22"/>')
    A(f'<path d="M{sx(-89):.1f} {sy(33.5):.1f} L{sx(-40):.1f} {sy(0):.1f} L{sx(-78):.1f} {sy(0):.1f} Z" '
      'fill="var(--warn)" opacity=".16"/>')

    # boxes
    for z, y, col, lbl, sub in ((2.0, 25.5, 'var(--accent)', 'FLOWN ARRAY', 'L / R'),
                                (-7.0, 4.5, 'var(--good)', 'FRONT FILL', '4 cabinets, one bus'),
                                (-89.0, 33.5, 'var(--warn)', 'SURROUND', 'spot booth')):
        A(f'<rect x="{sx(z)-11:.1f}" y="{sy(y)-7:.1f}" width="22" height="14" rx="2" '
          f'fill="var(--surface)" stroke="{col}" stroke-width="2"/>')
        A(f'<text x="{sx(z):.1f}" y="{sy(y)-12:.1f}" text-anchor="middle" class="svg-label" '
          f'style="fill:{col};font-weight:600">{lbl}</text>')
        A(f'<text x="{sx(z):.1f}" y="{sy(y)+26:.1f}" text-anchor="middle" class="svg-label sm">{sub}</text>')

    # sub position
    A(f'<rect x="{sx(4)-9:.1f}" y="{sy(3.5)-13:.1f}" width="18" height="12" rx="2" '
      'fill="var(--surface)" stroke="var(--accent)" stroke-width="1.6"/>')
    A(f'<text x="{sx(6.5):.1f}" y="{sy(3.5)-18:.1f}" text-anchor="start" class="svg-label sm">SUBS &middot; 7.75 ms</text>')

    # delay callouts
    for z, txt, col in ((-26.0, '12.35 ms', 'var(--good)'), (-58.0, '22 ms', 'var(--warn)')):
        A(f'<text x="{sx(z):.1f}" y="{sy(0)+18:.1f}" text-anchor="middle" class="svg-label sm" '
          f'style="fill:{col};font-weight:600">{txt}</text>')

    # row markers
    for z, lbl in ((-23, 'row 1'), (-53, 'row 12'), (-83, 'back')):
        A(f'<line x1="{sx(z):.1f}" y1="{sy(0):.1f}" x2="{sx(z):.1f}" y2="{sy(0)+6:.1f}" stroke="var(--ink-3)"/>')
        A(f'<text x="{sx(z):.1f}" y="{sy(0)+32:.1f}" text-anchor="middle" class="svg-label sm">{lbl}</text>')
    A('</svg>')

    cap = ('Coverage and time alignment, one value per system. The front fill runs 12.35&nbsp;ms so the '
           'image stays on the actor rather than at the lip; the subs 7.75&nbsp;ms to sit with the arrays. '
           'The surround is a different problem &mdash; sitting behind the audience, no single value is '
           'right everywhere &mdash; so it is tuned to 22&nbsp;ms for the middle of the house, kept low, '
           'and never carries dialogue.')
    return ('\n  <figure>\n    <div class="figbox">\n      ' + ''.join(p) +
            f'\n    </div>\n    <figcaption>{cap}</figcaption>\n  </figure>')
