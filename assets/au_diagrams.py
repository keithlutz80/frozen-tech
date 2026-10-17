#!/usr/bin/env python3
"""Audio design diagrams."""

import math

BOX = ('fill="var(--surface)" stroke="var(--rule-strong)" stroke-width="1.4" rx="3"')

# Front fill: Meyer M1D, five cabinets on the curved apron (feet; x from centre, z upstage of plaster).
# Geometry is read off the seating plan, scaled from the 50 ft opening: the apron is a 50 ft chord, 15.2 ft deep,
# so the apron edge is 8.2 ft from row 1. Each cabinet lies on the apron deck and is aimed along its radius from
# the arc centre.
APRON_R = 28.2          # apron arc radius
APRON_CZ = 13.0         # apron arc centre, upstage of plaster
SEAT_CZ = 20.7          # centre of the seat fan (where the aisle lines meet)
FILL_X = (-21.0, -12.0, 0.0, 12.0, 21.0)
ROW1, ROW_PITCH = 23.4, 3.18   # row 1 distance from plaster, row spacing
M1D_W, M1D_H, M1D_D = 23.04 / 12, 7.12 / 12, 8.50 / 12   # feet, from the datasheet
DECK = 3.5              # apron deck height above house floor


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
            ('LR', 'flown arrays'), ('Matrix 1&ndash;2', 'front fill, 2 zones'),
            ('Matrix 3&ndash;4', 'dressing / backstage'), ('St Matrix 1&ndash;2', 'video rec / stream'),
            ('Aux, St Aux', 'monitors, subs, surr')]),
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


def _fill_cabs():
    """(x, z, aim) per cabinet: z in feet upstage of plaster (negative = downstage), aim in degrees out."""
    out = []
    for x in FILL_X:
        out.append((x, APRON_CZ - math.sqrt(APRON_R ** 2 - x ** 2), math.degrees(math.asin(x / APRON_R))))
    return out


def _fill_level(x, z, cabs):
    """Relative level (dB) of the five fills at a seat: -6 dB at +-50 deg off axis, inverse distance."""
    p = 0.0
    for cx, cz, aim in cabs:
        dx, dz = x - cx, cz - z
        th = math.degrees(math.atan2(dx, dz)) - aim
        off = -6 * (th / 50.0) ** 2 if abs(th) <= 90 else -40
        r = max(math.hypot(dx, dz), 3)
        p += 10 ** ((off - 20 * math.log10(r / 16)) / 10)
    return 10 * math.log10(p)


def _seats(rows=range(1, 6)):
    """Seat grid for the first five rows: a fan about SEAT_CZ, aisles at 17-22 deg."""
    out = []
    r1 = SEAT_CZ + ROW1
    for n in rows:
        r = r1 + (n - 1) * ROW_PITCH
        for deg in range(-50, 51):
            if 17 < abs(deg) < 22:
                continue
            a = math.radians(deg)
            out.append((n, deg, r * math.sin(a), SEAT_CZ - r * math.cos(a)))
    return out


def fill_plan_svg():
    """Plan of the apron, the five M1Ds and the first five rows, seats coloured by predicted level."""
    S, X0 = 7.3, 360
    px = lambda x: X0 + x * S
    pz = lambda z: 40 + (4.0 - z) * S
    cabs = _fill_cabs()
    seats = _seats()
    lv = [_fill_level(x, z, cabs) for _, _, x, z in seats]
    med = sorted(lv)[len(lv) // 2]
    H = pz(-38) + 16
    p = []
    A = p.append
    A(f'<svg viewBox="0 0 720 {H:.0f}" role="img" aria-label="Plan of the curved apron with five M1D '
      'front fill cabinets aimed along its radii and the first five rows coloured by predicted level.">')
    A(f'<rect x="{px(-31):.1f}" y="{pz(0)-70:.1f}" width="{62*S:.1f}" height="70" fill="var(--surface-2)" '
      'stroke="var(--rule-strong)"/>')
    a0 = math.asin(25 / APRON_R)
    pts = [(APRON_R * math.sin(-a0 + 2 * a0 * i / 60), APRON_CZ - APRON_R * math.cos(-a0 + 2 * a0 * i / 60))
           for i in range(61)]
    d = 'M' + ' L'.join(f'{px(x):.1f} {pz(z):.1f}' for x, z in pts)
    A(f'<path d="{d} L{px(25):.1f} {pz(0):.1f} L{px(-25):.1f} {pz(0):.1f} Z" fill="var(--surface-2)" '
      'stroke="var(--ink)" stroke-width="2"/>')
    A(f'<text x="{px(0):.1f}" y="{pz(-4.2):.1f}" text-anchor="middle" class="svg-label sm">APRON</text>')
    A(f'<text x="{px(0):.1f}" y="{pz(1.2):.1f}" text-anchor="middle" class="svg-label sm">'
      'plaster line &middot; 50&prime; opening</text>')
    for x, z, aim in cabs:
        t0 = math.radians(aim)
        edge = [(x + 24 * math.sin(t0 + math.radians(o)), z - 24 * math.cos(t0 + math.radians(o))) for o in (-50, 50)]
        A(f'<path d="M{px(x):.1f} {pz(z):.1f} L{px(edge[0][0]):.1f} {pz(edge[0][1]):.1f} '
          f'L{px(edge[1][0]):.1f} {pz(edge[1][1]):.1f} Z" fill="var(--accent)" opacity=".07" '
          'stroke="var(--accent)" stroke-width=".8" stroke-dasharray="4 3"/>')
        tip = (x + 24 * math.sin(t0), z - 24 * math.cos(t0))
        A(f'<line x1="{px(x):.1f}" y1="{pz(z):.1f}" x2="{px(tip[0]):.1f}" y2="{pz(tip[1]):.1f}" '
          'stroke="var(--accent)" stroke-width="1.1"/>')
    for (n, deg, x, z), v in zip(seats, lv):
        dv = v - med
        col = 'var(--warn)' if dv > 3 else ('var(--aurora)' if dv < -3 else 'var(--good)')
        A(f'<circle cx="{px(x):.1f}" cy="{pz(z):.1f}" r="1.7" fill="{col}"/>')
    for n in (1, 3, 5):
        r = SEAT_CZ + ROW1 + (n - 1) * ROW_PITCH
        A(f'<text x="{px(0):.1f}" y="{pz(SEAT_CZ - r)+12:.1f}" text-anchor="middle" class="svg-label sm">row {n}</text>')
    for i, (x, z, aim) in enumerate(cabs):
        A(f'<g transform="translate({px(x):.1f} {pz(z):.1f}) rotate({-aim:.1f})"><rect x="{-M1D_W*S/2:.1f}" '
          f'y="{-M1D_D*S:.1f}" width="{M1D_W*S:.1f}" height="{M1D_D*S:.1f}" rx="1.5" fill="var(--surface)" '
          'stroke="var(--accent)" stroke-width="2"/></g>')
        A(f'<text x="{px(x):.1f}" y="{pz(z)-10:.1f}" text-anchor="middle" class="svg-label hi">FF-{i+1}</text>')
    A('</svg>')
    cap = ('Front fill plan. Five M1Ds lie on the apron deck and follow its arc, each aimed along its radius '
           'from the arc centre. Dashed wedges are the 100&deg; horizontal coverage at its &minus;6&nbsp;dB '
           'edges. Seats in rows 1 to 5 are <span style="color:var(--good)">green</span> within 3&nbsp;dB of the '
           'median, <span style="color:var(--warn)">orange</span> more than 3&nbsp;dB hot and '
           '<span style="color:var(--aurora)">violet</span> more than 3&nbsp;dB low. The model sums the five '
           'cabinets as power and ignores the vertical pattern, so treat it as a layout check and run the '
           'final aim in MAPP.')
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
    A(f'<line x1="{sx(-95):.1f}" y1="{sy(0):.1f}" x2="{sx(-(APRON_R - APRON_CZ)):.1f}" y2="{sy(0):.1f}" '
      'stroke="var(--ink-3)" stroke-width="2"/>')
    A(f'<path d="M{sx(-(APRON_R - APRON_CZ)):.1f} {sy(0):.1f} V{sy(DECK):.1f} H{sx(12):.1f}" fill="none" '
      'stroke="var(--ink)" stroke-width="2.5"/>')
    A(f'<text x="{sx(11):.1f}" y="{sy(3.5)+16:.1f}" text-anchor="end" class="svg-label sm">STAGE</text>')

    # coverage wedges
    A(f'<path d="M{sx(2):.1f} {sy(25.5):.1f} L{sx(-88):.1f} {sy(0):.1f} L{sx(-30):.1f} {sy(0):.1f} Z" '
      'fill="var(--accent)" opacity=".13"/>')
    zf = _fill_cabs()[2][1]                      # centre cabinet FF-3, centre-line section
    yf = DECK + M1D_H / 2
    z5 = -(ROW1 + 4 * ROW_PITCH)
    dy = abs(z5 - zf) * math.tan(math.radians(5))   # 10 deg vertical minimum, single cabinet
    A(f'<path d="M{sx(zf):.1f} {sy(yf):.1f} L{sx(z5):.1f} {sy(DECK+dy):.1f} L{sx(z5):.1f} {sy(DECK-dy):.1f} Z" '
      'fill="var(--good)" opacity=".22"/>')
    A(f'<path d="M{sx(-89):.1f} {sy(33.5):.1f} L{sx(-40):.1f} {sy(0):.1f} L{sx(-78):.1f} {sy(0):.1f} Z" '
      'fill="var(--warn)" opacity=".16"/>')

    # boxes
    for z, y, col, lbl, sub in ((2.0, 25.5, 'var(--accent)', 'FLOWN ARRAY', 'L / R'),
                                (_fill_cabs()[2][1], DECK + M1D_H / 2, 'var(--good)', 'FRONT FILL', '5 &times; M1D, two delays'),
                                (-89.0, 33.5, 'var(--warn)', 'SURROUND', 'spot booth')):
        A(f'<rect x="{sx(z)-11:.1f}" y="{sy(y)-7:.1f}" width="22" height="14" rx="2" '
          f'fill="var(--surface)" stroke="{col}" stroke-width="2"/>')
        A(f'<text x="{sx(z):.1f}" y="{sy(y)-12:.1f}" text-anchor="middle" class="svg-label" '
          f'style="fill:{col};font-weight:600">{lbl}</text>')
        A(f'<text x="{sx(z):.1f}" y="{sy(y)+(-24 if lbl == "FRONT FILL" else 26):.1f}" text-anchor="middle" '
          f'class="svg-label sm">{sub}</text>')

    # sub position
    A(f'<rect x="{sx(4)-9:.1f}" y="{sy(3.5)-13:.1f}" width="18" height="12" rx="2" '
      'fill="var(--surface)" stroke="var(--accent)" stroke-width="1.6"/>')
    A(f'<text x="{sx(6.5):.1f}" y="{sy(3.5)-18:.1f}" text-anchor="start" class="svg-label sm">SUBS &middot; 7.75 ms</text>')

    # delay callouts
    for z, txt, col in ((-26.0, '20 / 15 ms', 'var(--good)'), (-62.0, '22 ms', 'var(--warn)')):
        A(f'<text x="{sx(z):.1f}" y="{sy(0)+18:.1f}" text-anchor="middle" class="svg-label sm" '
          f'style="fill:{col};font-weight:600">{txt}</text>')

    # row markers
    for z, lbl in ((-ROW1, 'row 1'), (-(ROW1 + 11 * ROW_PITCH), 'row 12'), (-83, 'back')):
        A(f'<line x1="{sx(z):.1f}" y1="{sy(0):.1f}" x2="{sx(z):.1f}" y2="{sy(0)+6:.1f}" stroke="var(--ink-3)"/>')
        A(f'<text x="{sx(z):.1f}" y="{sy(0)+32:.1f}" text-anchor="middle" class="svg-label sm">{lbl}</text>')
    A('</svg>')

    cap = ('Coverage and time alignment, one value per system and two for the front fill. The centre three front fills run 20&nbsp;ms and the '
           'outer two about 15&nbsp;ms, so the image stays on the actor rather than at the lip; the subs 7.75&nbsp;ms to sit with the arrays. '
           'The surround is a different problem &mdash; sitting behind the audience, no single value is '
           'right everywhere &mdash; so it is tuned to 22&nbsp;ms for the middle of the house, kept low, '
           'and never carries dialogue.')
    return ('\n  <figure>\n    <div class="figbox">\n      ' + ''.join(p) +
            f'\n    </div>\n    <figcaption>{cap}</figcaption>\n  </figure>')


# ---------------------------------------------------------------------------------------------
# Front fill: level map, section and projector-clearance figures
# ---------------------------------------------------------------------------------------------

EAR = 3.5               # seated ear height above the house floor
FOH_LENS_Z, FOH_LENS_Y = -75.0, DECK + 6.5   # FOH projector lens: 75 ft out, 6.5 ft above the deck


def _fill_levels():
    """Per-seat level relative to the median seat, for the first five rows."""
    cabs = _fill_cabs()
    seats = _seats()
    lv = [_fill_level(x, z, cabs) for _, _, x, z in seats]
    med = sorted(lv)[len(lv) // 2]
    return seats, [v - med for v in lv]


def fill_stats():
    """Share of centre-block and side-block seats within 3 dB of the median, worst and hottest seat."""
    seats, d = _fill_levels()
    pick = lambda sel: [v for (n, deg, x, z), v in zip(seats, d) if sel(abs(deg))]
    share = lambda vs: 100 * sum(abs(v) <= 3 for v in vs) / len(vs)
    return dict(centre=share(pick(lambda a: a <= 17)), side=share(pick(lambda a: a >= 22)),
                worst=min(d), hot=max(d))


def _foh_ray(z_at, z_target):
    """Height above the house floor, at z_at, of the FOH ray that lands on the deck at z_target."""
    return FOH_LENS_Y + (DECK - FOH_LENS_Y) * ((z_at - FOH_LENS_Z) / (z_target - FOH_LENS_Z))


def _fig(svg_parts, cap):
    return ('\n  <figure>\n    <div class="figbox">\n      ' + ''.join(svg_parts) +
            f'\n    </div>\n    <figcaption>{cap}</figcaption>\n  </figure>')


def fill_level_svg():
    """Predicted level along rows 1, 3 and 5 by seat angle."""
    seats, d = _fill_levels()
    W, H, L, R, T, B = 720, 250, 54, 24, 18, 44
    cx = lambda a: L + (a + 50) / 100 * (W - L - R)
    cy = lambda db: T + (8 - db) / 18 * (H - T - B)
    p = []
    A = p.append
    A(f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="Predicted level relative to the median seat along '
      'rows 1, 3 and 5 by seat angle from the centre line.">')
    for db in range(8, -11, -3):
        A(f'<line x1="{L}" y1="{cy(db):.1f}" x2="{W-R}" y2="{cy(db):.1f}" '
          f'stroke="{"var(--rule-strong)" if db == 0 else "var(--rule)"}"/>')
        A(f'<text x="{L-8}" y="{cy(db)+4:.1f}" text-anchor="end" class="svg-label sm">'
          f'{"median" if db == 0 else f"{db:+d} dB"}</text>')
    for a0, a1 in ((17, 22), (-22, -17)):
        A(f'<rect x="{cx(a0):.1f}" y="{T}" width="{cx(a1)-cx(a0):.1f}" height="{H-T-B}" fill="var(--rule)" opacity=".6"/>'
          f'<text x="{(cx(a0)+cx(a1))/2:.1f}" y="{T+11}" text-anchor="middle" class="svg-label sm">aisle</text>')
    for a in range(-50, 51, 10):
        A(f'<line x1="{cx(a):.1f}" y1="{H-B}" x2="{cx(a):.1f}" y2="{H-B+5}" stroke="var(--ink-3)"/>'
          f'<text x="{cx(a):.1f}" y="{H-B+18}" text-anchor="middle" class="svg-label sm">{a:+d}&deg;</text>'
          if a else
          f'<line x1="{cx(0):.1f}" y1="{H-B}" x2="{cx(0):.1f}" y2="{H-B+5}" stroke="var(--ink-3)"/>'
          f'<text x="{cx(0):.1f}" y="{H-B+18}" text-anchor="middle" class="svg-label sm">0&deg;</text>')
    A(f'<text x="{(L+W-R)/2:.0f}" y="{H-6}" text-anchor="middle" class="svg-label sm">'
      'seat angle from the centre line, seen from the middle of the seat fan</text>')
    for n, col in ((1, 'var(--accent)'), (3, 'var(--good)'), (5, 'var(--aurora)')):
        row = sorted((deg, v) for (nn, deg, x, z), v in zip(seats, d) if nn == n)
        for part in ([t for t in row if t[0] <= -22], [t for t in row if -17 <= t[0] <= 0],
                     [t for t in row if 0 <= t[0] <= 17], [t for t in row if t[0] >= 22]):
            if len(part) > 1:
                A('<polyline points="' + ' '.join(f'{cx(a):.1f},{cy(v):.1f}' for a, v in part) +
                  f'" fill="none" stroke="{col}" stroke-width="2" stroke-linejoin="round"/>')
    A('</svg>')
    cap = ('Predicted level along row 1 (<span style="color:var(--accent)">blue</span>), row 3 '
           '(<span style="color:var(--good)">green</span>) and row 5 (<span style="color:var(--aurora)">violet</span>), '
           'relative to the median seat. The model sums the five cabinets as power and ignores the vertical pattern '
           'and comb filtering. The percentages carry about &plusmn;5 points of noise, so run the final aim in MAPP.')
    return _fig(p, cap)


def fill_section_svg():
    """Centre-line section through FF-3: vertical wedge over rows 1 to 5 and the lowest FOH rays."""
    zi = _fill_cabs()[2][1]
    sz, z_left, ys = 14.0, -42, 20.0
    sx = lambda z: 20 + (z - z_left) * sz
    sy = lambda y: 232 - y * ys
    row_z = lambda n: -(ROW1 + ROW_PITCH * (n - 1))
    p = []
    A = p.append
    A('<svg viewBox="0 0 720 262" role="img" aria-label="Centre-line section: FF-3 lying on the apron deck, its '
      'vertical coverage over rows 1 to 5, and the lowest projector rays.">')
    A(f'<line x1="{sx(-42):.1f}" y1="{sy(0):.1f}" x2="{sx(zi):.1f}" y2="{sy(0):.1f}" stroke="var(--ink-3)" stroke-width="2"/>')
    A(f'<path d="M{sx(zi):.1f} {sy(0):.1f} V{sy(DECK):.1f} H{sx(6):.1f}" fill="none" stroke="var(--ink)" stroke-width="2.5"/>')
    A(f'<text x="{sx(5.6):.1f}" y="{sy(DECK)+16:.1f}" text-anchor="end" class="svg-label sm">APRON DECK +3.5&prime;</text>')
    y0 = DECK + M1D_H / 2
    for n in range(1, 6):
        A(f'<line x1="{sx(row_z(n)):.1f}" y1="{sy(0):.1f}" x2="{sx(row_z(n)):.1f}" y2="{sy(0)+6:.1f}" stroke="var(--ink-3)"/>'
          f'<text x="{sx(row_z(n)):.1f}" y="{sy(0)+19:.1f}" text-anchor="middle" class="svg-label sm">r{n}</text>')
    z5 = row_z(5)
    dy = abs(z5 - zi) * math.tan(math.radians(5))
    A(f'<path d="M{sx(zi):.1f} {sy(y0):.1f} L{sx(z5):.1f} {sy(y0+dy):.1f} L{sx(z5):.1f} {sy(y0-dy):.1f} Z" '
      'fill="var(--accent)" opacity=".16"/>')
    A(f'<line x1="{sx(zi):.1f}" y1="{sy(y0):.1f}" x2="{sx(z5):.1f}" y2="{sy(EAR):.1f}" stroke="var(--accent)" stroke-width="1.2"/>')
    A(f'<line x1="{sx(row_z(1)):.1f}" y1="{sy(EAR):.1f}" x2="{sx(z5):.1f}" y2="{sy(EAR):.1f}" '
      'stroke="var(--ink-2)" stroke-width="1" stroke-dasharray="2 3"/>')
    A(f'<text x="{sx(row_z(3)):.1f}" y="{sy(EAR)+15:.1f}" text-anchor="middle" class="svg-label sm">seated ear 3.5&prime;</text>')
    for zt, col in ((0, 'var(--warn)'), (6, 'var(--aurora)')):
        za = -38
        A(f'<line x1="{sx(za):.1f}" y1="{sy(_foh_ray(za, zt)):.1f}" x2="{sx(zt):.1f}" y2="{sy(DECK):.1f}" '
          f'stroke="{col}" stroke-width="1.4"/>')
    A(f'<rect x="{sx(zi)-M1D_D*sz/2:.1f}" y="{sy(DECK+M1D_H):.1f}" width="{M1D_D*sz:.1f}" height="{M1D_H*ys:.1f}" '
      'fill="var(--surface)" stroke="var(--accent)" stroke-width="2"/>')
    A(f'<text x="{sx(zi)+14:.1f}" y="{sy(DECK+M1D_H)-26:.1f}" class="svg-label hi">FF-3 on the deck</text>'
      f'<text x="{sx(zi)+14:.1f}" y="{sy(DECK+M1D_H)-14:.1f}" class="svg-label sm">apron apex, {abs(zi):.1f}&prime; downstage</text>')
    A('</svg>')
    cap = ('Centre-line section through FF-3. The blue wedge is the 10&deg; vertical minimum for one cabinet, aimed '
           'at seated ears; it covers rows 1 to 5 on a flat floor. Orange and violet are the lowest rays from the '
           'FOH projectors, 75&prime; out. Vertical scale is exaggerated about 1.5&times;.')
    return _fig(p, cap)


def fill_clearance_svg():
    """Detail at the outer cabinets: top edge against the lowest FOH rays, on the deck and raised."""
    zo = _fill_cabs()[0][1]
    zs, ys, zl, zr, yb = 161.0, 125.0, zo - 2.0, zo + 2.0, 3.3
    ix = lambda z: 56 + (z - zl) * zs
    iy = lambda y: 215 - (y - yb) * ys
    rl = _foh_ray(zo, 6) - DECK
    rb = _foh_ray(zo, 0) - DECK
    p = []
    A = p.append
    A('<svg viewBox="0 0 720 250" role="img" aria-label="Magnified view at the outer cabinets: the M1D top edge '
      'against the lowest projector rays, on the deck and raised.">')
    A(f'<rect x="{ix(zl):.1f}" y="{iy(DECK):.1f}" width="{(zr-zl)*zs:.1f}" height="{iy(yb)-iy(DECK):.1f}" fill="var(--surface-2)"/>')
    A(f'<line x1="{ix(zl):.1f}" y1="{iy(DECK):.1f}" x2="{ix(zr):.1f}" y2="{iy(DECK):.1f}" stroke="var(--ink)" stroke-width="2.5"/>')
    for yy in (DECK + 0.5, DECK + 1.0, DECK + 1.5):
        A(f'<line x1="{ix(zl):.1f}" y1="{iy(yy):.1f}" x2="{ix(zr):.1f}" y2="{iy(yy):.1f}" stroke="var(--rule)"/>'
          f'<text x="{ix(zl)-6:.1f}" y="{iy(yy)+4:.1f}" text-anchor="end" class="svg-label sm">+{yy-DECK:.1f}&prime;</text>')
    for zt, col in ((0, 'var(--warn)'), (6, 'var(--aurora)')):
        A(f'<line x1="{ix(zl):.1f}" y1="{iy(_foh_ray(zl, zt)):.1f}" x2="{ix(zr):.1f}" y2="{iy(_foh_ray(zr, zt)):.1f}" '
          f'stroke="{col}" stroke-width="1.6"/>')
    A(f'<text x="{ix(zl)+6:.1f}" y="{iy(_foh_ray(zl, 6))-8:.1f}" class="svg-label sm" style="fill:var(--aurora)">'
      f'ray to LEG-*1, {rl:.2f}&prime; at FF-1 / FF-5</text>')
    A(f'<text x="{ix(zl)+6:.1f}" y="{iy(_foh_ray(zl, 0))-8:.1f}" class="svg-label sm" style="fill:var(--warn)">'
      f'ray to portal side band, {rb:.2f}&prime;</text>')
    c1, c2 = zo - 0.9, zo + 0.9
    A(f'<rect x="{ix(c1-M1D_D/2):.1f}" y="{iy(DECK+M1D_H):.1f}" width="{M1D_D*zs:.1f}" height="{M1D_H*ys:.1f}" '
      'fill="var(--surface)" fill-opacity=".92" stroke="var(--good)" stroke-width="2"/>')
    A(f'<rect x="{ix(c2-M1D_D/2):.1f}" y="{iy(DECK+0.7+M1D_H):.1f}" width="{M1D_D*zs:.1f}" height="{M1D_H*ys:.1f}" '
      'fill="var(--surface)" fill-opacity=".92" stroke="var(--warn)" stroke-width="2" stroke-dasharray="4 3"/>')
    A(f'<text x="{ix(c1):.1f}" y="{iy(DECK)+18:.1f}" text-anchor="middle" class="svg-label sm" '
      'style="fill:var(--good);font-weight:600">on the deck</text>'
      f'<text x="{ix(c1):.1f}" y="{iy(DECK)+31:.1f}" text-anchor="middle" class="svg-label sm">'
      f'top +{M1D_H:.2f}&prime; &mdash; clears by {rl-M1D_H:.2f}&prime;</text>')
    A(f'<text x="{ix(c2):.1f}" y="{iy(DECK)+18:.1f}" text-anchor="middle" class="svg-label sm" '
      'style="fill:var(--warn);font-weight:600">raised to a 4.5&prime; centre</text>'
      f'<text x="{ix(c2):.1f}" y="{iy(DECK)+31:.1f}" text-anchor="middle" class="svg-label sm">'
      f'top +{0.7+M1D_H:.2f}&prime; &mdash; cuts the ray by {0.7+M1D_H-rl:.2f}&prime;</text>')
    A('</svg>')
    cap = (f'Detail at FF-1 and FF-5, four feet across and vertically exaggerated. On the deck the cabinet top clears '
           f'the ray to LEG-*1 by {rl-M1D_H:.2f}&prime;. Raised to the 4.5&prime; centre an earlier plot showed, it would '
           f'cut {0.7+M1D_H-rl:.2f}&prime; into the beam and shadow the foot of the panel. The three inner cabinets are '
           'clear of every projected surface.')
    return _fig(p, cap)
