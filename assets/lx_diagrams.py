#!/usr/bin/env python3
"""Lighting-plan diagrams, generated from the surveyed venue numbers."""
import math

# ---- venue, all depths in feet upstage of the plaster line, y=0 at stage deck
CYC_Z, CYC_W, CYC_H = 30.0, 50.0, 30.0
OPEN_W, OPEN_H = 50.0, 21.5
PORTAL_W, PORTAL_H = 62.0, 29.5
HOUSE_Y = -3.5                      # house floor relative to deck
APRON, PIT = 7.0, 16.0
EPSON_Z, EPSON_TRIM = 14.0, 27.84
EPSON_LO, EPSON_HI, EPSON_HALF = 0.70, 29.27, 22.86

CAT_Z, CAT_Y = -40.0, 25.0          # FOH catwalk
SPOT_Z, SPOT_Y = -89.0, 30.0        # followspot positions
ELEC = {1: 3.0, 2: 8.0, 3: 17.0}
TRIM = 18.0
LEGS = (6.0, 12.0)
DECK_UNITS_Z, DECK_UNITS_X = 3.0, 23.0


def beam_env(z):
    """Epson cyc-beam envelope at depth z: (bottom, top, half-width)."""
    f = (z - EPSON_Z) / (CYC_Z - EPSON_Z)
    if f < 0:
        return None
    return (EPSON_TRIM + (EPSON_LO - EPSON_TRIM) * f,
            EPSON_TRIM + (EPSON_HI - EPSON_TRIM) * f,
            EPSON_HALF * f)


# ---------------------------------------------------------------- SECTION
def section_svg():
    """Side section: every position, its angle, and the projector beam."""
    X0, X1 = -95.0, 34.0                 # feet, downstage negative
    PX = 5.6                             # px per foot horizontally
    PY = 5.6                             # px per foot vertically
    DECK_Y = 300.0
    ox = 40.0

    sx = lambda z: ox + (z - X0) * PX
    sy = lambda y: DECK_Y - y * PY

    p = []
    A = p.append
    A('<svg viewBox="0 104 810 288" role="img" aria-label="Side section of Corner Canyon Theatre '
      'showing the followspot positions, FOH catwalk, three electrics, the stacked Epsons and '
      'the projector beam envelope.">')

    # --- projector beam envelope, drawn first so everything overlays it
    A(f'<path d="M{sx(EPSON_Z):.1f} {sy(EPSON_TRIM):.1f} L{sx(CYC_Z):.1f} {sy(EPSON_HI):.1f} '
      f'L{sx(CYC_Z):.1f} {sy(EPSON_LO):.1f} Z" fill="var(--aurora)" opacity=".17"/>')

    # --- catwalk cone to the acting area
    A(f'<path d="M{sx(CAT_Z):.1f} {sy(CAT_Y):.1f} L{sx(22.3):.1f} {sy(0):.1f} '
      f'L{sx(-1.0):.1f} {sy(0):.1f} Z" fill="var(--accent)" opacity=".13"/>')
    # --- lip wash cone, stopped by the deck
    A(f'<path d="M{sx(SPOT_Z):.1f} {sy(SPOT_Y):.1f} L{sx(2.70):.1f} {sy(0):.1f} '
      f'L{sx(-11.0):.1f} {sy(HOUSE_Y):.1f} Z" fill="var(--good)" opacity=".16"/>')

    # --- house floor and stage
    A(f'<line x1="{sx(X0):.1f}" y1="{sy(HOUSE_Y):.1f}" x2="{sx(-APRON):.1f}" '
      f'y2="{sy(HOUSE_Y):.1f}" stroke="var(--ink-3)" stroke-width="2"/>')
    A(f'<path d="M{sx(-APRON):.1f} {sy(HOUSE_Y):.1f} V{sy(0):.1f} H{sx(X1):.1f}" '
      'fill="none" stroke="var(--ink)" stroke-width="2.5"/>')
    A(f'<text x="{sx(-55):.1f}" y="{sy(HOUSE_Y)+16:.1f}" text-anchor="middle" class="svg-label sm">HOUSE FLOOR</text>')
    A(f'<text x="{sx(20):.1f}" y="{sy(0)+16:.1f}" text-anchor="middle" class="svg-label sm">STAGE DECK</text>')

    # --- scenic verticals
    for z, h, col, lbl, dy in ((0.0, PORTAL_H, 'var(--ink)', 'PORTAL', -7),
                               (LEGS[0], 25.0, 'var(--aurora)', 'LEG 1', -7),
                               (LEGS[1], 25.0, 'var(--aurora)', 'LEG 2', 30),
                               (CYC_Z, CYC_H, 'var(--accent)', 'CYC', -7)):
        A(f'<rect x="{sx(z)-2:.1f}" y="{sy(h):.1f}" width="4" height="{sy(0)-sy(h):.1f}" fill="{col}" opacity=".85"/>')
        A(f'<text x="{sx(z):.1f}" y="{sy(h)+dy:.1f}" text-anchor="middle" class="svg-label sm">{lbl}</text>')

    # --- electrics
    for n, z in ELEC.items():
        A(f'<circle cx="{sx(z):.1f}" cy="{sy(TRIM):.1f}" r="4.5" fill="var(--surface)" '
          'stroke="var(--warn)" stroke-width="2"/>')
        A(f'<text x="{sx(z):.1f}" y="{sy(TRIM)-9:.1f}" text-anchor="middle" class="svg-label sm" '
          f'style="fill:var(--warn)">E{n}</text>')

    # --- electric trim datum and the height the projector must reach
    A(f'<line x1="{sx(-3.0):.1f}" y1="{sy(TRIM):.1f}" x2="{sx(21.0):.1f}" y2="{sy(TRIM):.1f}" '
      'stroke="var(--warn)" stroke-width="1" stroke-dasharray="4 4" opacity=".8"/>')
    A(f'<text x="{sx(-3.5):.1f}" y="{sy(TRIM)+4:.1f}" text-anchor="end" class="svg-label sm" '
      f'style="fill:var(--warn)">ELEC TRIM {TRIM:.0f}&prime;</text>')
    xd = sx(10.6)
    A(f'<line x1="{xd:.1f}" y1="{sy(TRIM):.1f}" x2="{xd:.1f}" y2="{sy(EPSON_TRIM):.1f}" '
      'stroke="var(--ink-3)" stroke-width="1"/>')
    A(f'<line x1="{xd-5:.1f}" y1="{sy(TRIM):.1f}" x2="{xd+5:.1f}" y2="{sy(TRIM):.1f}" stroke="var(--ink-3)"/>')
    A(f'<line x1="{xd-5:.1f}" y1="{sy(EPSON_TRIM):.1f}" x2="{xd+5:.1f}" y2="{sy(EPSON_TRIM):.1f}" stroke="var(--ink-3)"/>')
    A(f'<text x="{xd-8:.1f}" y="{(sy(TRIM)+sy(EPSON_TRIM))/2+4:.1f}" text-anchor="end" '
      f'class="svg-label sm">{EPSON_TRIM-TRIM:.1f}&prime;</text>')

    # --- the two Epsons
    A(f'<rect x="{sx(EPSON_Z)-9:.1f}" y="{sy(EPSON_TRIM)-6:.1f}" width="18" height="11" rx="2" '
      'fill="var(--surface)" stroke="var(--aurora)" stroke-width="2"/>')
    A(f'<text x="{sx(EPSON_Z):.1f}" y="{sy(EPSON_TRIM)-11:.1f}" text-anchor="middle" '
      'class="svg-label sm" style="fill:var(--aurora);font-weight:600">EPSON &times;2</text>')
    A(f'<text x="{sx(EPSON_Z)+13:.1f}" y="{sy(EPSON_TRIM)+4:.1f}" text-anchor="start" '
      f'class="svg-label sm" style="fill:var(--aurora)">trim {EPSON_TRIM:.2f}&prime;</text>')

    # --- FOH positions
    A(f'<rect x="{sx(CAT_Z)-10:.1f}" y="{sy(CAT_Y)-6:.1f}" width="20" height="12" rx="2" '
      'fill="var(--surface)" stroke="var(--accent)" stroke-width="2"/>')
    A(f'<text x="{sx(CAT_Z):.1f}" y="{sy(CAT_Y)-11:.1f}" text-anchor="middle" class="svg-label hi">CATWALK</text>')
    A(f'<text x="{sx(CAT_Z):.1f}" y="{sy(CAT_Y)+20:.1f}" text-anchor="middle" class="svg-label sm">40&prime; &middot; 25&prime; up</text>')

    A(f'<rect x="{sx(SPOT_Z)-4:.1f}" y="{sy(SPOT_Y)-6:.1f}" width="20" height="12" rx="2" '
      'fill="var(--surface)" stroke="var(--good)" stroke-width="2"/>')
    A(f'<text x="{sx(SPOT_Z)+6:.1f}" y="{sy(SPOT_Y)-11:.1f}" text-anchor="middle" class="svg-label" '
      'style="fill:var(--good);font-weight:600">SPOT POSNS</text>')
    A(f'<text x="{sx(SPOT_Z)+6:.1f}" y="{sy(SPOT_Y)+20:.1f}" text-anchor="middle" class="svg-label sm">89&prime; &middot; 30&prime; up</text>')

    # --- deck beam units
    A(f'<path d="M{sx(DECK_UNITS_Z):.1f} {sy(2.0):.1f} l-8 -9" stroke="var(--warn)" stroke-width="2.5"/>')
    A(f'<circle cx="{sx(DECK_UNITS_Z):.1f}" cy="{sy(1.0):.1f}" r="4" fill="var(--warn)"/>')
    A(f'<text x="{sx(DECK_UNITS_Z)+8:.1f}" y="{sy(8.0):.1f}" text-anchor="start" class="svg-label sm" '
      'style="fill:var(--warn)">deck beams &times;4</text>')

    # --- lip actors
    A(f'<line x1="{sx(-8):.1f}" y1="{sy(HOUSE_Y):.1f}" x2="{sx(-8):.1f}" y2="{sy(HOUSE_Y+5.75):.1f}" '
      'stroke="var(--good)" stroke-width="3"/>')
    A(f'<text x="{sx(-8):.1f}" y="{sy(HOUSE_Y+5.75)-7:.1f}" text-anchor="middle" class="svg-label sm" '
      'style="fill:var(--good)">lip actors</text>')

    # --- dimension strip
    yb = DECK_Y + 52
    A(f'<line x1="{sx(SPOT_Z):.1f}" y1="{yb:.1f}" x2="{sx(CYC_Z):.1f}" y2="{yb:.1f}" stroke="var(--ink-3)"/>')
    for z, lbl in ((SPOT_Z, '89&prime;'), (CAT_Z, '40&prime;'), (0.0, '0'), (CYC_Z, '30&prime;')):
        A(f'<line x1="{sx(z):.1f}" y1="{yb-5:.1f}" x2="{sx(z):.1f}" y2="{yb+5:.1f}" stroke="var(--ink-3)"/>')
        A(f'<text x="{sx(z):.1f}" y="{yb+18:.1f}" text-anchor="middle" class="svg-label sm">{lbl}</text>')
    A('</svg>')

    cap = ('Side section, to scale. Note the vertical relationship: the Epsons hang at 27.84&prime;, '
           '<strong>9.8&prime; above the 18&prime; electric trim</strong>. An ultra-short lens sits near the '
           'top of its own picture, so it has to be above everything it clears &mdash; the beam then falls '
           'away downstage-to-upstage and passes over Electric 3 with 4.75&prime; to spare. '
           'The violet wedge is that beam &mdash; '
           'nothing may hang inside it, which is why Electric 4 flies out. The blue wedge is the catwalk '
           'front wash, top-cut so it dies on the deck at +22&prime; rather than climbing the cyc. The green '
           'wedge is the lip wash from the followspot positions: cut at 7&prime; above the house floor it is '
           'stopped by the apron at +2.7&prime;, downstage of the first legs, so it can never reach a screen.')
    return ('\n  <figure>\n    <div class="figbox">\n      ' + ''.join(p) +
            f'\n    </div>\n    <figcaption>{cap}</figcaption>\n  </figure>')


# ---------------------------------------------------------------- PLAN
def plan_svg():
    """Plan view: positions across the width, and what each system covers."""
    PX = 8.4
    cx = 350.0
    top = 46.0          # y px for the cyc (z = 30)
    PZ = 6.4            # px per foot of depth

    sx = lambda x: cx + x * PX
    sz = lambda z: top + (CYC_Z - z) * PZ

    p = []
    A = p.append
    A('<svg viewBox="0 26 700 306" role="img" aria-label="Plan view showing the cyclorama, four leg '
      'panels, three electrics, the deck beam units and the five acting areas.">')

    # the volume nothing may hang in -- the projector beam on its way to the cyc
    A(f'<path d="M{sx(-EPSON_HALF):.1f} {sz(CYC_Z):.1f} L{sx(EPSON_HALF):.1f} {sz(CYC_Z):.1f} '
      f'L{cx+10:.1f} {sz(EPSON_Z):.1f} L{cx-10:.1f} {sz(EPSON_Z):.1f} Z" '
      'fill="var(--aurora)" opacity=".13"/>')
    A(f'<text x="{cx:.0f}" y="{sz(23.0):.0f}" text-anchor="middle" class="svg-label sm" '
      'style="fill:var(--aurora)">KEEP CLEAR &mdash; projector beam</text>')

    # acting areas, drawn under everything
    for i, x in enumerate((-20, -10, 0, 10, 20), start=1):
        A(f'<circle cx="{sx(x):.1f}" cy="{sz(8.0):.1f}" r="17" fill="var(--surface)" '
          'stroke="var(--ink-3)" stroke-width="1" stroke-dasharray="3 3" opacity=".9"/>')
        A(f'<text x="{sx(x):.1f}" y="{sz(8.0)+4:.1f}" text-anchor="middle" class="svg-label sm">{i}</text>')

    # cyc
    A(f'<rect x="{sx(-25):.1f}" y="{sz(CYC_Z)-6:.1f}" width="{50*PX:.1f}" height="6" '
      'fill="var(--accent-soft)" stroke="var(--accent)" stroke-width="1.5"/>')
    A(f'<text x="{cx:.0f}" y="{sz(CYC_Z)-11:.0f}" text-anchor="middle" class="svg-label hi">CYC 50&prime; &middot; line set 30</text>')

    # electrics
    for n, z in ELEC.items():
        A(f'<line x1="{sx(-27):.1f}" y1="{sz(z):.1f}" x2="{sx(27):.1f}" y2="{sz(z):.1f}" '
          'stroke="var(--warn)" stroke-width="2.5"/>')
        A(f'<text x="{sx(-28.5):.1f}" y="{sz(z)+4:.1f}" text-anchor="end" class="svg-label sm" '
          f'style="fill:var(--warn)">ELEC {n}</text>')
        A(f'<text x="{sx(28.5):.1f}" y="{sz(z)+4:.1f}" text-anchor="start" class="svg-label sm" '
          f'style="fill:var(--warn)">+{z:.0f}&prime;</text>')

    # epson
    A(f'<rect x="{cx-16:.1f}" y="{sz(EPSON_Z)-5:.1f}" width="32" height="10" rx="2" '
      'fill="var(--surface)" stroke="var(--aurora)" stroke-width="2"/>')
    A(f'<text x="{cx:.0f}" y="{sz(EPSON_Z)-9:.0f}" text-anchor="middle" class="svg-label sm" '
      'style="fill:var(--aurora);font-weight:600">EPSON &times;2 &middot; set 14</text>')

    # legs
    for z in LEGS:
        for x0, x1 in ((-26.0, -21.0), (21.0, 26.0)) if z == 6.0 else ((-20.39, -15.39), (15.39, 20.39)):
            A(f'<rect x="{sx(x0):.1f}" y="{sz(z)-4:.1f}" width="{(x1-x0)*PX:.1f}" height="8" '
              'fill="var(--aurora-soft)" stroke="var(--aurora)" stroke-width="1.4"/>')

    # portal
    A(f'<line x1="{sx(-31):.1f}" y1="{sz(0):.1f}" x2="{sx(-25):.1f}" y2="{sz(0):.1f}" stroke="var(--ink)" stroke-width="5"/>')
    A(f'<line x1="{sx(25):.1f}" y1="{sz(0):.1f}" x2="{sx(31):.1f}" y2="{sz(0):.1f}" stroke="var(--ink)" stroke-width="5"/>')
    A(f'<line x1="{sx(-25):.1f}" y1="{sz(0):.1f}" x2="{sx(25):.1f}" y2="{sz(0):.1f}" stroke="var(--ink)" '
      'stroke-width="1.2" stroke-dasharray="4 4"/>')
    A(f'<text x="{sx(-33):.1f}" y="{sz(0)+4:.1f}" text-anchor="end" class="svg-label sm">PLASTER 0</text>')

    # apron edge
    A(f'<line x1="{sx(-25):.1f}" y1="{sz(-APRON):.1f}" x2="{sx(25):.1f}" y2="{sz(-APRON):.1f}" '
      'stroke="var(--ink)" stroke-width="2"/>')
    A(f'<text x="{cx:.0f}" y="{sz(-APRON)+15:.0f}" text-anchor="middle" class="svg-label sm">STAGE LIP &minus;7&prime;</text>')

    # deck beam units
    for x in (-DECK_UNITS_X, DECK_UNITS_X):
        for dz in (-0.8, 1.8):
            A(f'<circle cx="{sx(x):.1f}" cy="{sz(DECK_UNITS_Z-dz):.1f}" r="4" fill="var(--warn)"/>')
    for xx, anc in ((-DECK_UNITS_X, 'end'), (DECK_UNITS_X, 'start')):
        A(f'<text x="{sx(xx):.1f}" y="{sz(DECK_UNITS_Z)+22:.1f}" text-anchor="middle" '
          'class="svg-label sm" style="fill:var(--warn)">2 beams</text>')

    A(f'<text x="{cx:.0f}" y="{sz(-APRON)+30:.0f}" text-anchor="middle" class="svg-label sm">'
      'five acting areas on 10&prime; centres at +8&prime;, keyed from the catwalk at 19&deg;</text>')
    A('</svg>')

    cap = ('Plan. Five acting areas on 10&prime; centres at +8&prime;, each keyed from the catwalk at 19&deg;. '
           'The four deck beam units sit at &plusmn;23&prime;, three feet upstage of plaster &mdash; downstage of '
           'the first legs so nothing blocks them, and behind the 6&prime; portal side bands so the bodies are '
           'masked from most of the house.')
    return ('\n  <figure>\n    <div class="figbox">\n      ' + ''.join(p) +
            f'\n    </div>\n    <figcaption>{cap}</figcaption>\n  </figure>')


if __name__ == "__main__":
    print(len(section_svg()), len(plan_svg()))
