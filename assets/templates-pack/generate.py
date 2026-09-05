#!/usr/bin/env python3
"""
Frozen projection template generator
------------------------------------
Regenerates every alignment grid, mask and content template from one set of
venue numbers. Edit VENUE below with your surveyed M-numbers (Section 00 of the
projection plot) and re-run:

    pip install pillow
    python3 generate.py

Everything writes into grids/, masks/ and templates/ next to this file.
"""

from PIL import Image, ImageDraw, ImageFont
import os, json

# ---------------------------------------------------------------------------
# VENUE  -- edit these, then re-run
# ---------------------------------------------------------------------------

VENUE = {
    # ---- Corner Canyon High School Performing Arts, from the house plan ----
    # Proscenium surround: 6' side bands + a 50' opening = 62' wide; an 8' head
    # band on top of a 21.5' opening = 29.5' tall.
    "portal_w_ft": 62.0,
    "portal_h_ft": 29.5,
    "opening_w_ft": 50.0,
    "opening_h_ft": 21.5,

    # Cyclorama on line set 30, 30' tall, at the upstage limit of a 29.6' stage.
    "cyc_w_ft": 50.0,
    "cyc_h_ft": 30.0,
    "cyc_z_ft": 30.0,

    # FOH: tech booth 75' out, lens 10' above the HOUSE floor with the deck
    # 3'6" above it -> 6.5' above the stage. A low lens; see the design doc.
    "foh_throw_ft": 75.0,
    "foh_height_ft": 6.5,

    # Two TITANs stacked with a DP 109-236 HB zoom run at 1.21:1, covering the
    # full 62' surround from the tech booth.
    "foh_cover_w_ft": 62.0,

    # Epson + ELPLX02 0.35:1 fixed, on LINE SET 14 (13.81' US). Fixed lens, so
    # 29.6 - 13.81 = 15.79' of throw makes exactly a 45.10 x 25.37 ft image.
    # Centred at 13.5' so it covers the band the audience can actually see
    # through a 21.5' opening.
    "cyc_proj_z_ft": 14.0,
    "cyc_proj_trim_ft": 27.84,
    "cyc_lit_w_ft": 45.71,
    "cyc_lit_h_ft": 28.57,

    # Legs on real line sets. LEG-*2 goes as far upstage as it can while leaving
    # the Epson 2 ft of clearance -- set 12. LEG-*1 then sits exactly halfway
    # between the portal and LEG-*2, which lands on the house's LEG 1, set 6.
    "legs": [
        {"id": "LEG-SR1", "z_ft":  6.00, "x0_ft": -26.0, "x1_ft": -21.0},
        {"id": "LEG-SR2", "z_ft": 12.00, "x0_ft": None, "x1_ft": None,
         "aligns_with": "LEG-SR1", "clear_by_ft": 2.0},
        {"id": "LEG-SL2", "z_ft": 12.00, "x0_ft": None, "x1_ft": None,
         "aligns_with": "LEG-SL1", "clear_by_ft": 2.0},
        {"id": "LEG-SL1", "z_ft":  6.00, "x0_ft":  21.0, "x1_ft":  26.0},
    ],
    "leg_w_ft": 5.0,
    "leg_h_ft": 25.0,
}

def resolve_leg_alignment():
    """Fill in the dependent leg so its offstage edge visually abuts the
    anchor leg's onstage edge, from the FOH lens."""
    by_id = {l["id"]: l for l in VENUE["legs"]}
    thr = VENUE["foh_throw_ft"]
    w = VENUE["leg_w_ft"]
    for leg in VENUE["legs"]:
        if leg.get("x0_ft") is not None:
            continue
        ref = by_id[leg["aligns_with"]]
        s_ref = thr / (thr + ref["z_ft"])
        s_leg = thr / (thr + leg["z_ft"])
        # the reference leg's ONSTAGE edge is the one nearer centre
        onstage = ref["x1_ft"] if ref["x1_ft"] < 0 else ref["x0_ft"]
        margin = leg.get("clear_by_ft", 0.0)
        # step the crossing point onstage by the margin, then back-project to
        # the upstage leg's own plane
        target = onstage + margin if onstage < 0 else onstage - margin
        edge = target * (thr + leg["z_ft"]) / (thr + ref["z_ft"])
        if edge < 0:
            leg["x0_ft"], leg["x1_ft"] = edge, edge + w
        else:
            leg["x0_ft"], leg["x1_ft"] = edge - w, edge
    VENUE["legs"].sort(key=lambda l: l["x0_ft"])


# Stage raster sizes (Section 06 of the plot)
PORTAL_PX = (3840, 2160)          # matches the TITAN raster, 16:9
CYC_PX    = (1920, 1200)          # matches the Epson raster, WUXGA 16:10
LEG_PX    = (512, 2560)

FEATHER = 14          # px of Gaussian-equivalent softness on mask edges
OUT = os.path.dirname(os.path.abspath(__file__))
resolve_leg_alignment()

# ---------------------------------------------------------------------------

FONT_DIR = "/usr/share/fonts/truetype/dejavu"
def font(size, mono=True, bold=False):
    if mono:
        f = "DejaVuSansMono-Bold.ttf" if bold else "DejaVuSansMono.ttf"
    else:
        f = "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"
    try:
        return ImageFont.truetype(os.path.join(FONT_DIR, f), size)
    except OSError:
        return ImageFont.load_default()


# ---------------------------------------------------------------------------
# Perspective helpers -- where a real-world point lands in the FOH raster.
#
# The FOH raster is calibrated so the portal plane (z = 0), 60' x 30' standing
# on the deck, exactly fills 3840 x 1920. A point further upstage is projected
# back onto that plane along the ray from the lens.
# ---------------------------------------------------------------------------

def foh_cover():
    """What the FOH stack actually covers at the portal plane, in feet."""
    w = VENUE["foh_cover_w_ft"]
    return w, w * PORTAL_PX[1] / PORTAL_PX[0]


def foh_project(x_ft, y_ft, z_ft):
    """Real point -> (px, py) in the FOH raster."""
    W, H = PORTAL_PX
    cw, ch = foh_cover()
    ppf_x = W / cw
    ppf_y = H / ch
    throw = VENUE["foh_throw_ft"]
    lens_h = VENUE["foh_height_ft"]
    s = throw / (throw + z_ft)                       # foreshortening
    x_plane = x_ft * s
    y_plane = lens_h + (y_ft - lens_h) * s
    px = W / 2.0 + x_plane * ppf_x
    py = (ch - y_plane) * ppf_y            # raster bottom sits on the deck
    return px, py


def leg_quad(leg, clip_to_opening=True):
    """The four raster corners of a leg panel, as seen from the FOH lens.

    A 25' leg standing upstage of a 24' opening has its top foot hidden behind
    the proscenium header, so by default the quad is clipped to the opening.
    """
    z, h = leg["z_ft"], VENUE["leg_h_ft"]
    q = {
        "tl": foh_project(leg["x0_ft"], h,   z),
        "tr": foh_project(leg["x1_ft"], h,   z),
        "br": foh_project(leg["x1_ft"], 0.0, z),
        "bl": foh_project(leg["x0_ft"], 0.0, z),
    }
    if clip_to_opening:
        ox0, oy0, ox1, oy1 = opening_box()
        clamp = lambda p: (min(max(p[0], ox0), ox1), min(max(p[1], oy0), oy1))
        q = {k: clamp(v) for k, v in q.items()}
    return q


def opening_box():
    """Raster box of the proscenium opening (same plane as the surround)."""
    W, H = PORTAL_PX
    cw, ch = foh_cover()
    ppf_x, ppf_y = W / cw, H / ch
    ow, oh = VENUE["opening_w_ft"], VENUE["opening_h_ft"]
    x0 = W / 2.0 - (ow / 2.0) * ppf_x
    x1 = W / 2.0 + (ow / 2.0) * ppf_x
    y0 = (ch - oh) * ppf_y
    y1 = H
    return x0, y0, x1, y1


# ---------------------------------------------------------------------------
# Soft-edged mask builder
# ---------------------------------------------------------------------------

def feather(img, radius=FEATHER):
    from PIL import ImageFilter
    return img.filter(ImageFilter.GaussianBlur(radius))


def save_L(img, path):
    img.convert("L").save(path, optimize=True)
    print("  wrote", os.path.relpath(path, OUT))


# ---------------------------------------------------------------------------
# 1. ALIGNMENT GRIDS
# ---------------------------------------------------------------------------

def alignment_grid(size, w_ft, h_ft, label, path, minor_ft=1.0, major_ft=5.0):
    W, H = size
    img = Image.new("RGB", size, (10, 14, 20))
    d = ImageDraw.Draw(img)
    ppf_x, ppf_y = W / w_ft, H / h_ft

    MINOR, MAJOR, EDGE = (34, 52, 70), (70, 108, 140), (120, 200, 255)

    n = 0
    while n * minor_ft <= w_ft + 1e-6:
        x = n * minor_ft * ppf_x
        d.line([(x, 0), (x, H)], fill=MINOR, width=1)
        n += 1
    n = 0
    while n * minor_ft <= h_ft + 1e-6:
        y = n * minor_ft * ppf_y
        d.line([(0, y), (W, y)], fill=MINOR, width=1)
        n += 1

    f_small = font(max(16, int(W / 150)))
    n = 0
    while n * major_ft <= w_ft + 1e-6:
        ft = n * major_ft
        x = ft * ppf_x
        d.line([(x, 0), (x, H)], fill=MAJOR, width=3)
        d.text((x + 8, 10), f"{ft:g}'", font=f_small, fill=MAJOR)
        d.text((x + 8, H - 34), f"{int(round(x))}px", font=f_small, fill=MAJOR)
        n += 1
    n = 0
    while n * major_ft <= h_ft + 1e-6:
        ft = n * major_ft
        y = ft * ppf_y
        d.line([(0, y), (W, y)], fill=MAJOR, width=3)
        d.text((10, y + 6), f"{h_ft - ft:g}'", font=f_small, fill=MAJOR)
        n += 1

    # centreline + centre crosshair
    cx, cy = W / 2, H / 2
    d.line([(cx, 0), (cx, H)], fill=EDGE, width=3)
    d.line([(0, cy), (W, cy)], fill=EDGE, width=3)
    r = min(W, H) * 0.16
    d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=EDGE, width=3)
    r2 = r * 0.5
    d.ellipse([cx - r2, cy - r2, cx + r2, cy + r2], outline=EDGE, width=2)

    # outer frame + corner brackets
    d.rectangle([0, 0, W - 1, H - 1], outline=EDGE, width=6)
    b = int(min(W, H) * 0.10)
    for (ox, oy, sx, sy) in [(0, 0, 1, 1), (W, 0, -1, 1), (0, H, 1, -1), (W, H, -1, -1)]:
        d.line([(ox, oy + sy * 4), (ox + sx * b, oy + sy * 4)], fill=EDGE, width=8)
        d.line([(ox + sx * 4, oy), (ox + sx * 4, oy + sy * b)], fill=EDGE, width=8)

    # focus targets: fine converging lines, centre + corners
    def focus_target(px, py, s):
        d.rectangle([px - s - 6, py - s - 6, px + s + 6, py + s + 6],
                    outline=(120, 200, 255), width=2)
        for i in range(0, s, 4):
            d.line([(px - s, py - s + i), (px + s, py - s + i)], fill=(210, 230, 250), width=1)
        for i in range(0, s * 2, 6):
            d.line([(px - s + i, py + 6), (px - s + i, py + s)], fill=(210, 230, 250), width=1)
        d.line([(px - s - 18, py), (px - s - 8, py)], fill=(120, 200, 255), width=2)
        d.line([(px + s + 8, py), (px + s + 18, py)], fill=(120, 200, 255), width=2)
    ts = int(min(W, H) * 0.045)
    for (px, py) in [(cx, cy), (b * 1.6, b * 1.6), (W - b * 1.6, b * 1.6),
                     (b * 1.6, H - b * 1.6), (W - b * 1.6, H - b * 1.6)]:
        focus_target(int(px), int(py), ts)

    # title block
    f_big = font(max(22, int(W / 60)), bold=True)
    f_med = font(max(16, int(W / 110)))
    tw = int(W * 0.46) if W > H else int(W * 0.9)
    th = int(min(W, H) * 0.085)
    tx, ty = int(cx - tw / 2), int(cy + min(W, H) * 0.20)
    d.rectangle([tx, ty, tx + tw, ty + th], fill=(10, 14, 20), outline=EDGE, width=3)
    d.text((tx + 16, ty + 10), label, font=f_big, fill=EDGE)
    d.text((tx + 16, ty + 10 + f_big.size + 6),
           f"{W} x {H} px   |   {w_ft:g}' x {h_ft:g}'   |   {ppf_x:.1f} px/ft",
           font=f_med, fill=(150, 175, 200))

    img.save(path, optimize=True)
    print("  wrote", os.path.relpath(path, OUT))


def grey_field(size, path, level=128):
    Image.new("RGB", size, (level, level, level)).save(path, optimize=True)
    print("  wrote", os.path.relpath(path, OUT))


# ---------------------------------------------------------------------------
# 2. MASKS
# ---------------------------------------------------------------------------

def portal_frame_mask(path):
    W, H = PORTAL_PX
    m = Image.new("L", (W, H), 255)          # white = show
    d = ImageDraw.Draw(m)
    x0, y0, x1, y1 = opening_box()
    d.rectangle([x0, y0, x1, y1 + 10], fill=0)   # black = hide the opening
    m = feather(m, FEATHER)
    # keep the outer edge clean-ish but slightly soft
    save_L(m, path)


def legs_mask(path):
    W, H = PORTAL_PX
    m = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(m)
    for leg in VENUE["legs"]:
        q = leg_quad(leg)
        d.polygon([q["tl"], q["tr"], q["br"], q["bl"]], fill=255)
    m = feather(m, FEATHER)
    save_L(m, path)


def cyc_gradient_mask(path, strength=0.5):
    """Compensate the brightness gradient an ultra-short-throw lens puts on the cyc.

    A 0.35:1 lens sits close and high, so the top of the cyc is far brighter than
    the bottom: illuminance goes as cos(incidence) / distance^2, which for this
    geometry is roughly 5:1 top to bottom. This mask dims the bright end back
    toward the dim end.

    strength = 1.0 flattens completely (and costs you the whole gradient in
    light); 0.0 does nothing; 0.5 halves the gradient, which is usually the
    right trade for a cyc whose content is bright at the top anyway.
    """
    import math
    W, H = CYC_PX
    throw = VENUE["cyc_z_ft"] - VENUE["cyc_proj_z_ft"]
    trim = VENUE["cyc_proj_trim_ft"]
    cyc_h = VENUE["cyc_lit_h_ft"]

    def illum(y_ft):
        dy = trim - y_ft
        d = math.hypot(dy, throw)
        return (throw / d) / (d * d)          # cos(incidence) / distance^2

    prof = [illum(cyc_h * (1 - r / (H - 1))) for r in range(H)]
    lo = min(prof)
    m = Image.new("L", (W, H))
    px = m.load()
    for r in range(H):
        v = int(round(255 * ((lo / prof[r]) ** strength)))
        v = max(0, min(255, v))
        for c in range(W):
            px[c, r] = v
    save_L(m, path)
    print(f"      gradient {max(prof)/lo:.1f}:1 over {cyc_h:g} ft, "
          f"strength {strength} -> top of mask at {int(255*((lo/max(prof))**strength))}/255")


def cyc_trim_mask(path, inset=18, bottom_extra=10):
    W, H = CYC_PX
    m = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(m)
    d.rectangle([inset, inset, W - inset, H - inset - bottom_extra], fill=255)
    m = feather(m, 22)
    save_L(m, path)


def leg_visibility(leg):
    """How much of a leg the audience actually sees through the opening.

    Returns (u0, v0) in leg-stage pixels: everything left of u0 is hidden
    behind the proscenium side band, everything above v0 behind the header.
    """
    thr = VENUE["foh_throw_ft"]; lens = VENUE["foh_height_ft"]
    z = leg["z_ft"]; s = thr / (thr + z)
    x0, x1 = leg["x0_ft"], leg["x1_ft"]
    w, h = VENUE["leg_w_ft"], VENUE["leg_h_ft"]
    LW, LH = LEG_PX

    x_limit = (VENUE["opening_w_ft"] / 2.0) / s          # |X| beyond this is hidden
    y_limit = lens + (VENUE["opening_h_ft"] - lens) / s  # Y above this is hidden

    # leg-stage u runs 0 -> LW across x0 -> x1; the hidden end is the offstage one
    if x0 < 0:                                   # stage right: offstage is x0
        frac = (max(x0, -x_limit) - x0) / w
        u0 = frac * LW
        u1 = LW
    else:                                        # stage left: offstage is x1
        frac = (x1 - min(x1, x_limit)) / w
        u0 = 0.0
        u1 = LW - frac * LW
    v0 = max(0.0, (h - y_limit) / h) * LH        # v runs 0 (top, y=h) -> LH (deck)
    return u0, u1, v0


def leg_visibility_mask(leg, path):
    LW, LH = LEG_PX
    u0, u1, v0 = leg_visibility(leg)
    m = Image.new("L", LEG_PX, 0)
    d = ImageDraw.Draw(m)
    d.rectangle([u0, v0, u1, LH], fill=255)
    m = feather(m, 8)
    save_L(m, path)


def leg_mask(path):
    W, H = LEG_PX
    m = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(m)
    d.rectangle([8, 8, W - 8, H - 8], fill=255)
    m = feather(m, 8)
    save_L(m, path)


# ---------------------------------------------------------------------------
# 3. PLACEMENT GUIDE  (colour, for projecting during hang -- not a mask)
# ---------------------------------------------------------------------------

def placement_guide(path):
    W, H = PORTAL_PX
    img = Image.new("RGB", (W, H), (8, 10, 14))
    d = ImageDraw.Draw(img)
    f = font(30, bold=True)
    f_s = font(22)

    x0, y0, x1, y1 = opening_box()
    # frame band = where surround content actually lands
    d.rectangle([0, 0, W - 1, H - 1], fill=(16, 40, 62))
    d.rectangle([x0, y0, x1, y1], fill=(8, 10, 14))
    d.rectangle([x0, y0, x1, y1], outline=(120, 200, 255), width=5)
    d.rectangle([2, 2, W - 3, H - 3], outline=(120, 200, 255), width=5)
    d.text((W / 2 - 130, y0 / 2 - 20), "PORTAL-HEAD", font=f, fill=(150, 215, 255))
    d.text((x0 / 2 - 60, H / 2), "PORTAL-SR", font=f, fill=(150, 215, 255))
    d.text((x1 + (W - x1) / 2 - 60, H / 2), "PORTAL-SL", font=f, fill=(150, 215, 255))

    for leg in VENUE["legs"]:
        q = leg_quad(leg)
        pts = [q["tl"], q["tr"], q["br"], q["bl"]]
        d.polygon(pts, fill=(52, 40, 92), outline=(175, 150, 240))
        d.line(pts + [pts[0]], fill=(175, 150, 240), width=4)
        cxp = sum(p[0] for p in pts) / 4
        cyp = sum(p[1] for p in pts) / 4
        d.text((cxp - 62, cyp - 30), leg["id"], font=f_s, fill=(215, 200, 255))
        d.text((cxp - 40, cyp + 2), f'{leg["z_ft"]:g}\' US', font=f_s, fill=(160, 145, 200))

    # deck line
    d.line([(0, H - 3), (W, H - 3)], fill=(255, 190, 110), width=6)
    d.text((20, H - 44), "DECK", font=f_s, fill=(255, 190, 110))
    d.text((20, 16), "FOH RASTER PLACEMENT GUIDE  |  project this while positioning P3 / P4",
           font=f_s, fill=(150, 215, 255))
    d.text((20, 46),
           "Leg quads are perspective-correct from the FOH lens and clipped to the opening. "
           "Foreshortened tops/bottoms are correct, not an error.",
           font=f_s, fill=(110, 140, 170))
    img.save(path, optimize=True)
    print("  wrote", os.path.relpath(path, OUT))


# ---------------------------------------------------------------------------
# 4. CONTENT TEMPLATES
# ---------------------------------------------------------------------------

def content_template(size, w_ft, h_ft, label, zones, path):
    """zones: list of (y0_ft, y1_ft, rgba, text)"""
    W, H = size
    img = Image.new("RGBA", size, (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    ppf_y = H / h_ft
    f = font(max(18, int(W / 90)), bold=True)
    f_s = font(max(15, int(W / 130)))

    title_h = f.size + f_s.size + 34

    for (a, b, rgba, text) in zones:
        y0, y1 = (h_ft - b) * ppf_y, (h_ft - a) * ppf_y
        d.rectangle([0, y0, W, y1], fill=rgba)
        d.line([(0, y0), (W, y0)], fill=(255, 255, 255, 160), width=2)
        ty = y0 + 12
        if ty < title_h + 12:          # don't collide with the title block
            ty = min(y1 - f_s.size - 12, title_h + 12)
        d.text((24, ty), text, font=f_s, fill=(255, 255, 255, 235))

    d.rectangle([0, 0, W - 1, H - 1], outline=(255, 255, 255, 130), width=4)
    d.line([(W / 2, 0), (W / 2, H)], fill=(255, 255, 255, 80), width=2)

    tw = int(W * 0.62) if W > H else W - 24
    d.rectangle([12, 12, 12 + tw, title_h], fill=(8, 12, 18, 225),
                outline=(255, 255, 255, 150), width=2)
    d.text((26, 22), label, font=f, fill=(255, 255, 255, 245))
    d.text((26, 22 + f.size + 6),
           f"{W} x {H} px  |  {w_ft:g}' x {h_ft:g}'  |  {W/w_ft:.1f} px/ft  -- guide layer, delete before export",
           font=f_s, fill=(180, 205, 225, 235))
    img.save(path)
    print("  wrote", os.path.relpath(path, OUT))


# ---------------------------------------------------------------------------

def main():
    g = lambda *p: os.path.join(OUT, "grids", *p)
    m = lambda *p: os.path.join(OUT, "masks", *p)
    t = lambda *p: os.path.join(OUT, "templates", *p)

    print("Alignment grids:")
    alignment_grid(CYC_PX, VENUE["cyc_lit_w_ft"], VENUE["cyc_lit_h_ft"],
                   "STG_CYC", g("align-grid-cyc-1920x1200.png"))
    cw, ch = foh_cover()
    alignment_grid(PORTAL_PX, cw, ch, "STG_PORTAL", g("align-grid-portal-3840x2160.png"))
    alignment_grid(LEG_PX, 5.0, VENUE["leg_h_ft"],
                   "STG_LEG", g("align-grid-leg-512x2560.png"), minor_ft=0.5, major_ft=5.0)
    grey_field(PORTAL_PX, g("blend-field-50grey-3840x2160.png"))
    grey_field(LEG_PX, g("blend-field-50grey-512x2560.png"))
    placement_guide(g("foh-placement-guide-3840x2160.png"))

    print("Masks:")
    portal_frame_mask(m("portal-frame-mask-3840x2160.png"))
    legs_mask(m("legs-slices-mask-3840x2160.png"))
    cyc_trim_mask(m("cyc-trim-mask-1920x1200.png"))
    cyc_gradient_mask(m("cyc-gradient-mask-half-1920x1200.png"), strength=0.5)
    cyc_gradient_mask(m("cyc-gradient-mask-full-1920x1200.png"), strength=1.0)
    leg_mask(m("leg-edge-mask-512x2560.png"))
    for leg in VENUE["legs"]:
        leg_visibility_mask(leg, m(f"leg-visible-{leg['id']}-512x2560.png"))

    print("Content templates:")
    lit_h = VENUE["cyc_lit_h_ft"]
    content_template(
        CYC_PX, VENUE["cyc_lit_w_ft"], lit_h, "CYC CONTENT TEMPLATE",
        [(0, 8, (200, 90, 40, 62), "SHADOW / BOUNCE ZONE 0-8'  -- no critical detail here"),
         (8, 14, (60, 130, 190, 42), "HORIZON BAND 8-14'  -- keep the horizon in here"),
         (14, lit_h, (40, 170, 130, 32), "PRIME 14-25.4'  -- sky, aurora, ice palace, all pale imagery")],
        t("cyc-template-1920x1200.png"))
    content_template(
        PORTAL_PX, cw, ch, "PORTAL CONTENT TEMPLATE",
        [(VENUE["portal_h_ft"], ch, (120, 120, 120, 45), "OVERSPILL -- above the surround, masks off"),
         (VENUE["opening_h_ft"], VENUE["portal_h_ft"], (60, 130, 190, 45), "HEAD BAND 21.5-29.5'  -- visible"),
         (0, VENUE["opening_h_ft"], (140, 40, 40, 70), "OPENING 0-21.5'  -- MASKED, nothing here is seen on the surround")],
        t("portal-template-3840x2160.png"))
    content_template(
        LEG_PX, 5.0, VENUE["leg_h_ft"], "LEG TEMPLATE",
        [(0, 3, (200, 90, 40, 62), "BASE TRIM 0-3'"),
         (3, 22, (40, 170, 130, 32), "PRIME 3-22'  -- vertical texture only"),
         (22, 25, (200, 90, 40, 62), "TOP TRIM 22-25'")],
        t("leg-template-512x2560.png"))

    with open(os.path.join(OUT, "venue.json"), "w") as fh:
        json.dump(VENUE, fh, indent=2)
    print("  wrote venue.json")

    print("\nLeg quads in the FOH raster (paste into QLab region warps):")
    for leg in VENUE["legs"]:
        q = leg_quad(leg)
        pts = " ".join(f"{k}=({v[0]:.0f},{v[1]:.0f})" for k, v in q.items())
        print(f"  {leg['id']:<9} {pts}")

    print("\nPer-leg light and focus (FOH unit, f/2.0, 0.67\" DMD):")
    thr = VENUE["foh_throw_ft"]
    w_panel = 0.67 * 0.848
    print(f"  {'leg':<9}{'z':>4}{'x0':>7}{'x1':>7}{'apparent span':>18}"
          f"{'visible':>9}{'rel.light':>11}{'blur px':>9}")
    for leg in VENUE["legs"]:
        z = leg["z_ft"]
        sc = thr / (thr + z)
        W_in = VENUE["portal_w_ft"] * 12
        blur_in = (z * 12) / (2.0 * (1 + W_in / w_panel))
        u0, u1, v0 = leg_visibility(leg)
        vis = (u1 - u0) / LEG_PX[0]
        print(f"  {leg['id']:<9}{z:>4.0f}{leg['x0_ft']:>7.2f}{leg['x1_ft']:>7.2f}"
              f"{leg['x0_ft']*sc:>9.2f} to{leg['x1_ft']*sc:>7.2f}"
              f"{vis*100:>8.0f}%{sc*sc:>10.3f}x{blur_in/(W_in/1920):>9.2f}")
    print("\n  Stagger check -- apparent edges should abut:")
    ls = sorted(VENUE["legs"], key=lambda l: l["x0_ft"])
    for a, b in [(ls[0], ls[1]), (ls[2], ls[3])]:
        sa = thr / (thr + a["z_ft"]); sb = thr / (thr + b["z_ft"])
        gap = b["x0_ft"] * sb - a["x1_ft"] * sa
        print(f"    {a['id']} onstage edge {a['x1_ft']*sa:+7.2f}'  ->  "
              f"{b['id']} offstage edge {b['x0_ft']*sb:+7.2f}'   gap {gap*12:+5.1f} in")

    leg_conflicts()
    cyc_beam_clearance()


def leg_conflicts():
    """Two things that bite when legs are staggered in the wings:
    one leg shadowing another, and a leg reaching outside what the FOH unit
    can see through the opening."""
    thr = VENUE["foh_throw_ft"]
    half = VENUE["opening_w_ft"] / 2.0
    print("\nLeg-on-leg shadow check:")
    for tgt in VENUE["legs"]:
        worst = None
        for occ in VENUE["legs"]:
            if occ is tgt or occ["z_ft"] >= tgt["z_ft"]:
                continue
            if (occ["x0_ft"] < 0) != (tgt["x0_ft"] < 0):
                continue                                   # other side of stage
            k = (tgt["z_ft"] + thr) / (occ["z_ft"] + thr)
            lo, hi = sorted((occ["x0_ft"] * k, occ["x1_ft"] * k))
            ov0, ov1 = max(lo, tgt["x0_ft"]), min(hi, tgt["x1_ft"])
            gap = ov1 - ov0
            worst = gap if worst is None else max(worst, gap)
        if worst is None:
            print(f"  {tgt['id']:<9} nothing downstage of it on that side")
        elif worst > 0.02:
            print(f"  {tgt['id']:<9} ** SHADOWED over {worst:.2f} ft "
                  f"({worst/VENUE['leg_w_ft']*100:.0f}% of the panel) **")
        elif worst > -0.05:
            print(f"  {tgt['id']:<9} TANGENT -- no shadow, but zero tolerance")
        else:
            print(f"  {tgt['id']:<9} clear by {-worst:.2f} ft")

    print("\nFull-coverage check (can the FOH unit light the whole panel?):")
    for leg in VENUE["legs"]:
        limit = half / (thr / (thr + leg["z_ft"]))
        reach = max(abs(leg["x0_ft"]), abs(leg["x1_ft"]))
        if reach <= limit + 1e-6:
            print(f"  {leg['id']:<9} reaches {reach:5.2f} ft, lit out to {limit:5.2f} ft"
                  f"  -> fully lit, {(limit-reach)*12:4.1f} in to spare")
        else:
            print(f"  {leg['id']:<9} reaches {reach:5.2f} ft, lit out to {limit:5.2f} ft"
                  f"  -> ** {(reach-limit)*12:.0f} in BEHIND THE PROSCENIUM, unlightable **")


def cyc_beam_clearance():
    """Does any leg stick into the cyc projector's beam?

    The cyc unit throws from cyc_proj_z_ft to the cyc at cyc_z_ft, spreading to
    half the cyc width. At any intermediate depth the beam's half-width is a
    simple linear interpolation -- a leg whose inner edge falls inside that
    half-width intercepts the beam and casts a shadow onto the cyc.
    """
    zp = VENUE["cyc_proj_z_ft"]
    zc = VENUE["cyc_z_ft"]
    half = VENUE["cyc_w_ft"] / 2.0
    print("\nCyc-beam clearance check:")
    print(f"  cyc unit at z={zp:g}', cyc at z={zc:g}', beam reaches +/-{half:g}' at the cyc")
    worst = None
    for leg in VENUE["legs"]:
        z = leg["z_ft"]
        if z <= zp:
            print(f"  {leg['id']:<9} z={z:>4.0f}'  DOWNSTAGE of the cyc unit at z={zp:g}' "
                  f"-> cannot block it. CLEAR.")
            continue
        hw = half * (z - zp) / (zc - zp)
        inner = min(abs(leg["x0_ft"]), abs(leg["x1_ft"]))
        clear = inner - hw
        if clear >= 0:
            print(f"  {leg['id']:<9} z={z:>4.0f}'  beam half-width {hw:5.2f}'  "
                  f"inner edge {inner:5.1f}'  CLEAR by {clear:4.2f}'")
        else:
            # where the shadow lands on the cyc
            s_in = inner * (zc - zp) / (z - zp)
            s_out = min(hw, max(abs(leg['x0_ft']), abs(leg['x1_ft']))) * (zc - zp) / (z - zp)
            print(f"  {leg['id']:<9} z={z:>4.0f}'  beam half-width {hw:5.2f}'  "
                  f"inner edge {inner:5.1f}'  ** INTRUDES {-clear:4.2f}' **")
            print(f"            -> shadow band on the cyc from {s_in:.1f}' to "
                  f"{min(s_out, half):.1f}' off centre")
            worst = max(worst or 0, -clear)
    if worst:
        need = max(half * (l["z_ft"] - zp) / (zc - zp) for l in VENUE["legs"])
        print(f"\n  FIX: move the inboard legs out so their inner edge is at least "
              f"{need:.1f}' off centre,")
        print( "       or accept a dark band at the outer edges of the cyc.")


if __name__ == "__main__":
    main()
