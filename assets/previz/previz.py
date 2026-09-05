#!/usr/bin/env python3
"""
Arendelle previz — composite the three projection surfaces into an audience view
using the real staging geometry from the projection plot.

Surfaces are all parallel to the portal plane, so each maps to a scaled
rectangle in the audience's view; no perspective warp is needed, only the
foreshortening factor for its depth.
"""
import numpy as np, math, os
from PIL import Image, ImageDraw, ImageFilter

T      = 75.0     # audience / FOH distance to plaster line
EYE    = 5.0      # audience eye height above the stage deck
PX     = 30       # pixels per foot in the render
X0, X1 = -33.0, 33.0
Y0, Y1 = -2.0, 32.0
W, H   = int((X1 - X0) * PX), int((Y1 - Y0) * PX)

def sx(x): return (x - X0) * PX
def sy(y): return (Y1 - y) * PX

def app(x, y, z):
    s = T / (T + z)
    return x * s, EYE + (y - EYE) * s

# The Epson's 0.35:1 lens on line set 14 throws 15.79 ft and makes a 45.10 x 25.37 ft
# image, so the LIT area of the 50 x 30 ft cyc is smaller than the cloth. Only the lit
# part is drawn; the unlit margin stays dark, which is exactly what the audience sees.
SURFACES = {
    "cyc":  dict(z=29.6, x=(-22.55, 22.55), y=(0.81, 26.19)),
    "sr1":  dict(z= 5.92, x=(-26.00, -21.00), y=(0.0, 25.0)),
    "sr2":  dict(z=11.84, x=(-20.39, -15.39), y=(0.0, 25.0)),
    "sl2":  dict(z=11.84, x=( 15.39,  20.39), y=(0.0, 25.0)),
    "sl1":  dict(z= 5.92, x=( 21.00,  26.00), y=(0.0, 25.0)),
}
CYC_CLOTH = dict(z=29.6, x=(-25.0, 25.0), y=(0.0, 30.0))
PORTAL_X, PORTAL_Y = (-31.0, 31.0), (0.0, 29.5)
OPEN_X,  OPEN_Y    = (-25.0, 25.0), (0.0, 21.5)

# foot-lamberts from the plot, used for the "as projected" pass
FL = dict(portal=14.2, sr1=12.2, sr2=10.6, cyc_top=19.7, cyc_mid=9.7, cyc_bot=3.0)
FL_REF = 19.7


# ---------------------------------------------------------------- helpers
def grad(h, w, stops):
    """Vertical gradient. stops = [(pos 0-1 from top, (r,g,b)), ...]"""
    ys = np.linspace(0, 1, h)
    out = np.zeros((h, w, 3), np.float64)
    ps = [p for p, _ in stops]
    cs = np.array([c for _, c in stops], np.float64)
    for ch in range(3):
        out[:, :, ch] = np.interp(ys, ps, cs[:, ch])[:, None]
    return out


def fbm(h, w, octaves=5, seed=0, aspect=1.0):
    rng = np.random.default_rng(seed)
    acc = np.zeros((h, w), np.float64)
    amp, tot = 1.0, 0.0
    for o in range(octaves):
        gh = max(2, int(3 * 2 ** o))
        gw = max(2, int(3 * 2 ** o * aspect))
        g = rng.random((gh, gw))
        layer = np.array(Image.fromarray((g * 255).astype(np.uint8)).resize((w, h), Image.BICUBIC), np.float64) / 255
        acc += layer * amp
        tot += amp
        amp *= 0.5
    return acc / tot


def stars(img, n, seed, size=1, colour=(255, 255, 255), top=0.7):
    rng = np.random.default_rng(seed)
    h, w = img.shape[:2]
    for _ in range(n):
        x = rng.integers(0, w); y = rng.integers(0, int(h * top))
        b = rng.random() ** 2
        for dx in range(-size, size + 1):
            for dy in range(-size, size + 1):
                xx, yy = x + dx, y + dy
                if 0 <= xx < w and 0 <= yy < h:
                    f = b * max(0.0, 1 - (dx * dx + dy * dy) / (size * size + 1))
                    img[yy, xx] = img[yy, xx] * (1 - f) + np.array(colour) * f
    return img


def aurora(h, w, seed, colours, strength=1.0):
    rng = np.random.default_rng(seed)
    out = np.zeros((h, w, 3), np.float64)
    xs = np.linspace(0, 1, w)
    for i, col in enumerate(colours):
        cy = rng.uniform(0.10, 0.45)
        amp = rng.uniform(0.03, 0.10)
        freq = rng.uniform(1.2, 3.0)
        thick = rng.uniform(0.05, 0.13)
        centre = cy + amp * np.sin(2 * np.pi * freq * xs + rng.uniform(0, 6))
        ys = np.linspace(0, 1, h)[:, None]
        band = np.exp(-((ys - centre[None, :]) ** 2) / (2 * thick ** 2))
        curtain = 0.55 + 0.45 * fbm(h, w, 4, seed + i * 7, aspect=3.0)
        band = band * curtain
        for ch in range(3):
            out[:, :, ch] += band * col[ch] * strength
    return out


def ice_palace(h, w, seed=3, colour=(150, 210, 255), glow=(90, 150, 230), base_frac=0.94):
    """Crystalline palace: explicit shadow / mid / lit facets so it reads as ice
    rather than as a flat silhouette tinted by whatever sky is behind it."""
    fill = Image.new("RGB", (w, h), (0, 0, 0))
    mask = Image.new("L", (w, h), 0)
    d, dm = ImageDraw.Draw(fill), ImageDraw.Draw(mask)
    rng = np.random.default_rng(seed)
    base = int(h * base_frac)
    cx = w // 2

    SHADOW = (26, 58, 100)
    MID    = (70, 138, 198)
    LIT    = (152, 216, 255)
    EDGE   = (222, 244, 255)

    def mix(c, k):
        return tuple(min(255, max(0, int(v * k))) for v in c)

    spires = [(-0.42, 0.26, 0.080, 0.62), (0.42, 0.27, 0.080, 0.62),
              (-0.31, 0.40, 0.092, 0.78), (0.31, 0.41, 0.092, 0.78),
              (-0.175, 0.58, 0.110, 0.92), (0.175, 0.59, 0.110, 0.92),
              (0.0, 0.80, 0.145, 1.00)]
    for off, ht, wd, k in spires:
        x = cx + off * w
        top = base - ht * h
        half = wd * w
        pts = [(x, top), (x + half, base), (x - half, base)]
        d.polygon(pts, fill=mix(SHADOW, k)); dm.polygon(pts, fill=255)
        d.polygon([(x, top), (x + half * 0.10, base), (x - half * 0.42, base)], fill=mix(MID, k))
        d.polygon([(x, top), (x - half * 0.42, base), (x - half * 0.78, base)], fill=mix(LIT, k))
        d.line([(x, top), (x - half, base)], fill=mix(EDGE, k), width=2)
        d.line([(x, top), (x + half, base)], fill=mix(MID, k * 1.1), width=2)

    wallt = base - 0.17 * h
    wl, wr = cx - 0.30 * w, cx + 0.30 * w
    d.rectangle([wl, wallt, wr, base], fill=SHADOW); dm.rectangle([wl, wallt, wr, base], fill=255)
    for i in range(15):
        x = wl + i * ((wr - wl) / 14)
        d.line([(x, wallt), (x, base)], fill=mix(MID, 0.9), width=max(1, int(w * 0.003)))
    d.line([(wl, wallt), (wr, wallt)], fill=EDGE, width=2)
    gw, gh = 0.090 * w, 0.145 * h
    d.polygon([(cx - gw, base), (cx - gw, base - gh * 0.55), (cx, base - gh),
               (cx + gw, base - gh * 0.55), (cx + gw, base)], fill=(236, 250, 255))

    m = np.array(mask, np.float64) / 255
    halo = np.array(mask.filter(ImageFilter.GaussianBlur(w * 0.020)), np.float64) / 255
    halo_rgb = halo[:, :, None] * np.array(glow, np.float64) * 0.85
    return np.array(fill, np.float64), halo_rgb, m


def frost_lines(h, w, seed, n=180, colour=(210, 240, 255), from_edges=True):
    pil = Image.fromarray(np.zeros((h, w, 3), np.uint8))
    d = ImageDraw.Draw(pil)
    rng = np.random.default_rng(seed)
    for _ in range(n):
        if from_edges:
            x, y = (rng.choice([0, w]), rng.integers(0, h)) if rng.random() < .5 \
                   else (rng.integers(0, w), rng.choice([0, h]))
        else:
            x, y = rng.integers(0, w), rng.integers(0, h)
        ang = math.atan2(h / 2 - y, w / 2 - x) + rng.uniform(-0.9, 0.9)
        ln = rng.uniform(0.05, 0.30) * max(w, h)
        px, py = float(x), float(y)
        for seg in range(7):
            nx = px + math.cos(ang) * ln / 7
            ny = py + math.sin(ang) * ln / 7
            f = 1 - seg / 7
            d.line([(px, py), (nx, ny)], fill=tuple(int(c * f) for c in colour),
                   width=max(1, int(3 * f)))
            if rng.random() < 0.45:
                a2 = ang + rng.choice([-1, 1]) * rng.uniform(0.5, 1.0)
                d.line([(nx, ny), (nx + math.cos(a2) * ln / 9, ny + math.sin(a2) * ln / 9)],
                       fill=tuple(int(c * f * .7) for c in colour), width=1)
            px, py, ang = nx, ny, ang + rng.uniform(-0.2, 0.2)
    return np.array(pil.filter(ImageFilter.GaussianBlur(0.6)), np.float64)


def snow(h, w, seed, n=900, colour=(235, 245, 255)):
    img = np.zeros((h, w, 3), np.float64)
    rng = np.random.default_rng(seed)
    for _ in range(n):
        x, y = rng.integers(0, w), rng.integers(0, h)
        r = rng.choice([1, 1, 1, 2, 2, 3])
        b = rng.uniform(0.25, 1.0)
        for dx in range(-r, r + 1):
            for dy in range(-r, r + 1):
                if dx * dx + dy * dy <= r * r and 0 <= x + dx < w and 0 <= y + dy < h:
                    img[y + dy, x + dx] += np.array(colour) * b * 0.9
    return img


# ---------------------------------------------------------------- surface art
def make_cyc(scene, h, w):
    s = SCENES[scene]
    img = grad(h, w, s["cyc_grad"])
    if s.get("aurora"):
        img += aurora(h, w, 11, s["aurora"], s.get("aurora_strength", 1.0))
    if s.get("stars"):
        img = stars(img, s["stars"], 5, size=1)
    if s.get("palace"):
        fillp, halop, m = ice_palace(h, w, colour=s["palace"],
                                     glow=s.get("palace_glow", (90, 150, 230)),
                                     base_frac=s.get("palace_base", 0.94))
        soft = np.array(Image.fromarray((m * 255).astype(np.uint8))
                        .filter(ImageFilter.GaussianBlur(1.0)), np.float64)[:, :, None] / 255
        img = img * (1 - soft) + fillp * soft + halop
    if s.get("snow"):
        img += snow(h, w, 7, s["snow"])
    if s.get("whiteout"):
        n = fbm(h, w, 6, 21, aspect=1.6)
        img = img * (1 - s["whiteout"]) + (170 + 85 * n)[:, :, None] * s["whiteout"]
    return np.clip(img, 0, 255)


def make_portal(scene, h, w):
    """The surround reads only as a frame, so the structure lives at the edges:
    crystalline fronds growing inward from the two sides and down from the top."""
    s = SCENES[scene]
    img = grad(h, w, s["portal_grad"])
    n = fbm(h, w, 5, 31, aspect=2.0)
    img *= (0.78 + 0.42 * n)[:, :, None]

    pil = Image.new("RGB", (w, h), (0, 0, 0)); d = ImageDraw.Draw(pil)
    rng = np.random.default_rng(9)
    F = np.array(s["frost_col"], float)

    def frond(ox, oy, ang, length, k):
        """A tapered ice frond with side spines."""
        px, py = ox, oy
        segs = 9
        for i in range(segs):
            f = 1 - i / segs
            nx = px + math.cos(ang) * length / segs
            ny = py + math.sin(ang) * length / segs
            d.line([(px, py), (nx, ny)],
                   fill=tuple(min(255, int(v * k * (0.45 + 0.55 * f))) for v in F),
                   width=max(1, int(9 * f * k)))
            for sgn in (-1, 1):
                a2 = ang + sgn * rng.uniform(0.55, 1.15)
                sl = length * rng.uniform(0.10, 0.30) * f
                d.line([(nx, ny), (nx + math.cos(a2) * sl, ny + math.sin(a2) * sl)],
                       fill=tuple(min(255, int(v * k * f * 0.85)) for v in F),
                       width=max(1, int(5 * f * k)))
            px, py = nx, ny
            ang += rng.uniform(-0.10, 0.10)

    band = int(w * 0.13)                      # side band width in art space
    for i in range(16):                       # left side band
        frond(rng.uniform(0, band * 0.5), rng.uniform(0.05, 1.0) * h,
              rng.uniform(-0.6, 0.6), rng.uniform(0.30, 0.75) * band * 2.4,
              rng.uniform(0.55, 1.0))
    for i in range(16):                       # right side band
        frond(w - rng.uniform(0, band * 0.5), rng.uniform(0.05, 1.0) * h,
              math.pi + rng.uniform(-0.6, 0.6), rng.uniform(0.30, 0.75) * band * 2.4,
              rng.uniform(0.55, 1.0))
    for i in range(26):                       # head band, growing downward
        frond(rng.uniform(0, w), rng.uniform(0, h * 0.06),
              math.pi / 2 + rng.uniform(-0.85, 0.85), rng.uniform(0.10, 0.26) * h,
              rng.uniform(0.55, 1.0))
    img += np.array(pil.filter(ImageFilter.GaussianBlur(1.0)), np.float64) * 0.95
    img += frost_lines(h, w, 41, n=max(30, s.get("frost", 200) // 4),
                       colour=s["frost_col"]) * 0.30
    return np.clip(img, 0, 255)


def make_leg(scene, h, w, seed):
    """A 1:5 portrait panel: one frost-laden conifer, dark ground, bright crown."""
    s = SCENES[scene]
    img = grad(h, w, s["leg_grad"])
    img *= (0.70 + 0.50 * fbm(h, w, 5, seed, aspect=0.20))[:, :, None]

    pil = Image.new("RGB", (w, h), (0, 0, 0)); d = ImageDraw.Draw(pil)
    rng = np.random.default_rng(seed + 3)
    F = np.array(s["leg_frost"], float)
    cx = w * rng.uniform(0.42, 0.58)

    # trunk
    for j in range(h):
        t = j / h
        tw = w * (0.030 + 0.055 * t)
        k = 0.30 + 0.55 * (1 - t)
        d.line([(cx - tw / 2, j), (cx + tw / 2, j)],
               fill=tuple(int(v * k * 0.5) for v in F), width=1)

    # boughs: denser and wider toward the base, drooping
    n = 42
    for i in range(n):
        t = (i / n) ** 0.85
        y = h * (0.045 + 0.94 * t)
        reach = w * (0.10 + 0.42 * t) * rng.uniform(0.8, 1.15)
        droop = h * 0.016 * rng.uniform(0.5, 1.6)
        k = (0.42 + 0.58 * (1 - t)) * rng.uniform(0.75, 1.1)
        for sgn in (-1, 1):
            ex, ey = cx + sgn * reach, y + droop
            d.line([(cx, y), (ex, ey)],
                   fill=tuple(min(255, int(v * k)) for v in F),
                   width=max(1, int(w * 0.020 * (0.5 + t))))
            for _ in range(3):            # needle sprays
                f = rng.uniform(0.35, 0.95)
                bx, by = cx + sgn * reach * f, y + droop * f
                a = rng.uniform(0.25, 1.15) * sgn
                sl = reach * rng.uniform(0.14, 0.34)
                d.line([(bx, by), (bx + math.cos(a) * sl, by + abs(math.sin(a)) * sl * 0.8)],
                       fill=tuple(min(255, int(v * k * 0.75)) for v in F),
                       width=max(1, int(w * 0.008)))
    img += np.array(pil.filter(ImageFilter.GaussianBlur(w * 0.006)), np.float64) * 0.95

    # rim of light down one edge, and a dark vignette on the other
    xs = np.linspace(0, 1, w)[None, :, None]
    img *= (0.78 + 0.30 * np.exp(-((xs - 0.34) ** 2) / 0.22))
    if s.get("leg_snow"):
        img += snow(h, w, seed + 9, s["leg_snow"])
    return np.clip(img, 0, 255)


# ---------------------------------------------------------------- scenes
SCENES = {
    "let-it-go": dict(
        title="Let It Go", act="Act I finale — the ice palace builds",
        cyc_grad=[(0.0, (8, 16, 46)), (0.30, (16, 44, 96)), (0.62, (34, 96, 158)),
                  (0.85, (14, 40, 78)), (1.0, (5, 12, 28))],
        aurora=[(30, 140, 120), (60, 90, 175), (40, 130, 150)], aurora_strength=0.75,
        stars=520, palace=(168, 224, 255), palace_glow=(80, 150, 235), snow=700,
        portal_grad=[(0.0, (16, 46, 104)), (0.5, (26, 84, 152)), (1.0, (10, 28, 66))],
        frost_col=(190, 232, 255), frost=230,
        leg_grad=[(0.0, (150, 205, 240)), (0.35, (52, 104, 160)), (1.0, (12, 30, 62))],
        leg_frost=(200, 235, 255), leg_snow=260,
    ),
    "let-it-go-hi": dict(
        title="Let It Go, recomposed", act="the same cue, built for the gradient",
        cyc_grad=[(0.0, (10, 22, 58)), (0.28, (20, 56, 116)), (0.55, (40, 112, 176)),
                  (0.70, (12, 34, 70)), (1.0, (3, 7, 16))],
        aurora=[(30, 140, 120), (60, 90, 175), (40, 130, 150)], aurora_strength=0.55,
        stars=520, palace=(168, 224, 255), palace_glow=(80, 150, 235),
        palace_base=0.60, snow=700,
        portal_grad=[(0.0, (16, 46, 104)), (0.5, (26, 84, 152)), (1.0, (10, 28, 66))],
        frost_col=(190, 232, 255), frost=230,
        leg_grad=[(0.0, (150, 205, 240)), (0.35, (52, 104, 160)), (1.0, (12, 30, 62))],
        leg_frost=(200, 235, 255), leg_snow=260,
    ),
    "colder": dict(
        title="Colder by the Minute", act="Act II — the whiteout",
        cyc_grad=[(0.0, (108, 126, 150)), (0.45, (150, 168, 190)), (1.0, (72, 86, 106))],
        stars=0, snow=2200, whiteout=0.55,
        portal_grad=[(0.0, (78, 100, 132)), (0.5, (118, 146, 178)), (1.0, (52, 68, 94))],
        frost_col=(232, 244, 255), frost=320,
        leg_grad=[(0.0, (196, 214, 236)), (0.4, (118, 142, 172)), (1.0, (44, 58, 82))],
        leg_frost=(236, 246, 255), leg_snow=520,
    ),
    "finale": dict(
        title="Finale", act="Arendelle in summer",
        cyc_grad=[(0.0, (36, 92, 172)), (0.34, (108, 172, 228)), (0.66, (206, 216, 214)),
                  (0.86, (96, 128, 96)), (1.0, (34, 52, 40))],
        aurora=[(150, 130, 70)], aurora_strength=0.35, stars=0,
        portal_grad=[(0.0, (108, 66, 30)), (0.5, (168, 118, 56)), (1.0, (68, 40, 20))],
        frost_col=(246, 214, 150), frost=140,
        leg_grad=[(0.0, (140, 178, 92)), (0.4, (74, 118, 56)), (1.0, (26, 42, 24))],
        leg_frost=(196, 220, 130), leg_snow=0,
    ),
}


# ---------------------------------------------------------------- composite
def paste(base, art, x_ft, y_ft, z, clip=None, dim=1.0, profile=None):
    (ax0, ay0) = app(x_ft[0], y_ft[1], z)
    (ax1, ay1) = app(x_ft[1], y_ft[0], z)
    px0, py0, px1, py1 = sx(ax0), sy(ay0), sx(ax1), sy(ay1)
    w, h = max(1, int(round(px1 - px0))), max(1, int(round(py1 - py0)))
    im = Image.fromarray(art.astype(np.uint8)).resize((w, h), Image.LANCZOS)
    a = np.array(im, np.float64)
    if profile is not None:
        a *= np.interp(np.linspace(0, 1, h), [0, .5, 1], profile)[:, None, None]
    a *= dim
    reg = np.array(im.resize((w, h)))  # placeholder shape
    xs, ys = int(round(px0)), int(round(py0))
    for j in range(h):
        Y = ys + j
        if not (0 <= Y < base.shape[0]):
            continue
        for_x0, for_x1 = xs, xs + w
        cx0, cx1 = max(0, for_x0), min(base.shape[1], for_x1)
        if cx1 <= cx0:
            continue
        seg = a[j, cx0 - for_x0:cx1 - for_x0]
        if clip is not None:
            ox0, oy0, ox1, oy1 = clip
            if not (oy0 <= Y <= oy1):
                continue
            k0, k1 = max(cx0, ox0), min(cx1, ox1)
            if k1 <= k0:
                continue
            base[Y, k0:k1] = seg[k0 - cx0:k1 - cx0]
        else:
            base[Y, cx0:cx1] = seg
    return base


def render(scene, projected=True):
    base = np.zeros((H, W, 3), np.float64)
    # house / walls beyond the surround
    base[:, :] = np.array([9, 10, 13], np.float64)

    clip = (int(sx(OPEN_X[0])), int(sy(OPEN_Y[1])), int(sx(OPEN_X[1])), int(sy(0.0)))

    d = (lambda k: FL[k] / FL_REF) if projected else (lambda k: 1.0)
    prof = ([FL["cyc_top"] / FL_REF, FL["cyc_mid"] / FL_REF, FL["cyc_bot"] / FL_REF]
            if projected else None)

    s = SURFACES["cyc"]
    base = paste(base, make_cyc(scene, 900, 1800), s["x"], s["y"], s["z"], clip, 1.0, prof)

    # borders / teaser masking above the cyc: the header hides the top of the
    # 30 ft cloth, but not down to the top of the Epson's image -- about 1.3 ft
    # of bare cloth shows in between, and a black border has to take it
    cyc_top_y = int(sy(app(0, 26.19, 29.6)[1]))
    base[clip[1]:cyc_top_y, clip[0]:clip[2]] = np.array([6, 7, 10], np.float64)

    # deck
    deck_top = int(sy(app(0, 0, 29.6)[1]))
    dk = np.linspace(0.62, 0.16, max(1, int(sy(0.0)) - deck_top))[:, None, None]
    base[deck_top:int(sy(0.0)), clip[0]:clip[2]] *= dk

    for key, seed, fl in (("sr2", 101, "sr2"), ("sl2", 202, "sr2"),
                          ("sr1", 303, "sr1"), ("sl1", 404, "sr1")):
        s = SURFACES[key]
        base = paste(base, make_leg(scene, 1400, 280, seed), s["x"], s["y"], s["z"],
                     clip, d(fl))

    # portal surround, drawn last with the opening punched out
    art = make_portal(scene, 900, 1800) * d("portal")
    im = np.array(Image.fromarray(art.astype(np.uint8)).resize(
        (int(sx(PORTAL_X[1]) - sx(PORTAL_X[0])), int(sy(PORTAL_Y[0]) - sy(PORTAL_Y[1]))),
        Image.LANCZOS), np.float64)
    ox, oy = int(sx(PORTAL_X[0])), int(sy(PORTAL_Y[1]))
    for j in range(im.shape[0]):
        Y = oy + j
        if not (0 <= Y < H):
            continue
        for i in range(im.shape[1]):
            X = ox + i
            if not (0 <= X < W):
                continue
            if clip[0] <= X <= clip[2] and clip[1] <= Y <= clip[3]:
                continue
            base[Y, X] = im[j, i]

    if projected:
        base = 255 * (np.clip(base, 0, 255) / 255) ** 0.85     # gentle perceptual lift
    return Image.fromarray(np.clip(base, 0, 255).astype(np.uint8))


if __name__ == "__main__":
    out = "/root/work/previz"
    os.makedirs(out, exist_ok=True)
    for k in SCENES:
        render(k, True).save(f"{out}/{k}-projected.png")
        print("wrote", k)
    render("let-it-go", False).save(f"{out}/let-it-go-flat.png")
    print("wrote flat comparison")
