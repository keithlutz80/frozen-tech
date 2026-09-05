# Frozen — projection template pack

Companion files to the Arendelle Projection Plot. Everything here is generated
from one set of venue numbers by `generate.py`, so once you have surveyed the
real room you edit that file and re-run rather than re-drawing anything by hand.

Loaded with the surveyed **Corner Canyon High School Performing Arts** numbers:
proscenium opening 50′ × 21.5′ in a 62′ × 29.5′ surround (8′ head, 6′ side
bands), 29.6′ of usable stage depth with the 50′ × 30′ cyc on line set 30, legs
on line sets 6 and 12 (5.92′ and 11.84′ upstage), **Epson + ELPLX02 on line set
14** at 24.92′ trim, two TITANs in the tech booth 75′ out with a **DP 109-236
lens at 1.21:1** and a lens height of only 6.5′ above the deck.

**Rasters are calibrated to what the projectors actually make.** The FOH raster
maps 62.0 × 34.88 ft to 3840 × 2160 (61.9 px/ft). The Epson's fixed 0.35:1 lens
at a 15.79′ throw makes exactly 45.10 × 25.37 ft, so the cyc raster maps that —
which leaves 2.45′ of cyc unlit at each side and 4.6′ vertically. See the design
document, Section 07.

---

## Regenerating after your site survey

```bash
pip install pillow
python3 generate.py
```

Open `generate.py`, edit the `VENUE` dictionary at the top with your surveyed
M-numbers, and re-run. Every grid, mask and template rebuilds in place, and the
script prints the leg corner coordinates in the FOH raster for you to type into
QLab's region warps.

---

## `grids/` — project these, don't play them in the show

| File | Use |
|---|---|
| `align-grid-cyc-3840x2160.png` | Warping and focusing the Epson on the cyc. 1′ minor / 5′ major grid, feet labelled down the left, pixel positions along the bottom, focus targets at centre and all four corners. The circle is a true circle — if it reads as an oval your aspect ratio is wrong before you touch anything else. |
| `align-grid-portal-3840x2160.png` | Same, for the TITAN stack on the surround. |
| `align-grid-leg-512x2560.png` | Same, for a single leg stage. 6″ minor grid. |
| `blend-field-50grey-3840x2160.png` | Flat 50% grey. **This is the file you tune blends on**, not a grid. Play it across the whole stage, then adjust blend width until the seam vanishes and blend gamma until the overlap band stops reading brighter or darker than the wings. |
| `blend-field-50grey-512x2560.png` | Same, leg-sized. |
| `foh-placement-guide-3840x2160.png` | Project this **while you are still hanging and lensing P3/P4**, before any warping. It shows where the frame band and all four legs fall in the FOH raster, so you can position and shift the units until the real surfaces land near their targets optically. Blue = surround, violet = legs. |

### About the leg quads on the placement guide

They are perspective-correct from the FOH lens position, not simple rectangles.
The upstage legs are deliberately narrower and shorter — a leg 11.84′ upstage is
86.84′ from the lens versus 80.92′ for one at 5.92′, so it subtends less raster, and
the tops and bottoms foreshorten toward lens height. That is what the projector
actually sees, and it is why each leg needs its own region warp.

The legs are **staggered** in traditional masking order: `LEG-*1` downstage and
furthest offstage, `LEG-*2` upstage of it and stepped onstage.

**Two checks run on every rebuild**, because staggering legs in the wings breaks
in two ways that are easy to miss:

- **Leg-on-leg shadow.** The beam to the upstage leg has to clear the downstage
  one. `clear_by_ft` on the upstage leg sets the margin, measured at the
  downstage leg's own plane. `0.0` is exactly tangent — no shadow, but zero
  tolerance, and two inches of drift in a hung canvas either opens a bare slot
  or drops a hard shadow line down the upstage panel. `2.0` is comfortable.
- **Full coverage.** A panel reaching further off centre than the FOH unit can
  see through the opening has a strip no front projector can ever light — the
  surround is in the way. From house centre the proscenium hides it and nobody
  notices; from the opposite side of the house it is a dark stripe down the
  panel edge. Keep every leg inside its limit: 26.97′ at 5.92′ upstage, 28.95′ at 11.84′.

**Dialling the stagger** is two numbers. `x0_ft` on the downstage pair sets how
far into the wings the walls sit — keep it inside 26.97′. `clear_by_ft` on the
upstage pair sets the shadow margin and therefore the visible slot between the
panels: 1.0 gives about 11 inches, 2.0 gives 22. At the current 2.0 the upstage
pair lands within 4 inches of the cyc's apparent edges, so that slot shows dark
wing space rather than cyc — which is what you want it to read as.

Current values, printed by the script on every run:

```
LEG-SR1   tl=(427,828)   tr=(715,828)   br=(715,2131)   bl=(427,2131)
LEG-SR2   tl=(829,828)   tr=(1097,828)  br=(1097,2105)  bl=(829,2105)
LEG-SL2   tl=(2743,828)  tr=(3011,828)  br=(3011,2105)  bl=(2743,2105)
LEG-SL1   tl=(3125,828)  tr=(3413,828)  br=(3413,2131)  bl=(3125,2131)
```

Note the tops all clamp to y=828, the bottom of the proscenium header. Your legs
are 25′ tall but the opening is only 21.5′, so the top 2.3′ of the downstage pair
and 1.1′ of the upstage pair is hidden behind the header from out front. Do not
put anything you need to see up there.

The bottoms stop at 2131 and 2105 rather than at the raster floor. The panels do
stand on the deck — but the FOH lens is only 6.5′ up, so the last few inches of
raster below those numbers pass *under* the panel and land on the stage floor.
Warp to the numbers above, not to the raster edge.

---

## `masks/` — greyscale, loaded onto QLab stages

Black hides, white shows, mid-grey dims proportionally. All are pre-feathered.

| File | Needed? | Use |
|---|---|---|
| `portal-frame-mask-3840x2160.png` | **Always** | White on the frame band, black across the opening. Without this, surround content sprays through the opening onto the legs and cyc. |
| `cyc-trim-mask-3840x2160.png` | **Always** | Feathered border that trims spill off the top, sides and bottom of the cyc onto the walls, grid and deck. |
| `cyc-gradient-mask-half-3840x2160.png` | **Probably** | Compensates the top-to-bottom brightness gradient the 0.35:1 ultra-short lens puts on the cyc. Halves a 6.0:1 gradient. Multiply this with the trim mask, or load whichever the tech-table eye prefers. |
| `cyc-gradient-mask-full-3840x2160.png` | Rarely | Same, flattened completely. Costs you the whole gradient in light — the cyc ends up at its dimmest reading everywhere. Use only if the gradient reads as an error rather than as sky. |
| `legs-slices-mask-3840x2160.png` | Only for the one-big-stage approach | Four white slices at the leg positions, everything else black. See the note below. |
| `leg-visible-LEG-*-512x2560.png` | **Always, for the part-masked legs** | One per leg. Blacks out the portion of that panel hidden behind the proscenium side band and the header, computed from the leg's real position. |
| `leg-edge-mask-512x2560.png` | Optional | Light feathered edge for an individual leg stage, so the panel edges glow off rather than cut hard. |

### Masks vs. region warps — pick one approach for the legs

There are two ways to get content onto four legs, and they need different files.

**Approach A — one stage per leg (recommended, and what the plot assumes).**
Each leg is its own `512×2560` stage with a single region, warped to that leg's
four corners in the projector's raster. The warp does all the shaping, so
`legs-slices-mask` is not needed at all — use only `leg-edge-mask` if you want a
soft panel edge. This is cleaner, keeps each leg independently adjustable, and
lets your designer build a leg as a true 1:5 portrait canvas.

**Approach B — one big FOH stage, masked into slices.**
One `3840×1920` stage carries the frame band and all four legs, cut apart by
`portal-frame-mask` and `legs-slices-mask`. Fewer stages to manage, but every
leg shares one warp, so you cannot correct an individual panel that gets bumped,
and content has to be authored into leg-shaped holes in a wide canvas.

Use A unless you have a reason not to. The slices mask ships either way because
it is also a useful reference image for checking where the legs land.

### The per-leg visibility masks

At the current positions no panel is masked horizontally — every leg is fully
lit, which is the point of moving them onstage. The masks still matter for the
**header**: legs are 25′ tall against a 21.5′ opening, so the top of each is
behind the proscenium wherever it sits sideways.

If you ever push a leg back out into the wings, the mask earns its keep again.
Warp each region to the leg's **full** physical quad so the texture maps
correctly onto the real panel, then let the mask hide what falls outside the
opening. Never squeeze the warp into the visible sliver — that distorts the
content.

---

## `templates/` — hand these to whoever makes content

Transparent PNG guide overlays at exact stage size. Drop one on a top layer in
Photoshop or After Effects, build underneath it, **delete the guide layer before
export**.

| File | Canvas | Zones |
|---|---|---|
| `cyc-template-3840x2160.png` | 3840×2160, 16:9, 85.1 px/ft | Shadow/bounce zone 0–8′ (no critical detail), horizon band 8–14′, prime 14–25.4′ for sky, aurora, ice palace and all pale imagery |
| `portal-template-3840x2160.png` | 3840×2160, 16:9, 61.9 px/ft | Head band 21.5–29.5′ visible; everything below 21.5′ is masked, everything above 29.5′ overspills the scenery |
| `leg-template-512x2560.png` | 512×2560, 1:5, 102 px/ft | Base trim 0–3′, prime 3–22′, top trim 22–25′ (the top foot is behind the header) |

### Delivery reminders

- **HAP or HAP Q in a `.mov`**, not H.264. Three surfaces playing at once will
  drop frames on H.264 at these pixel counts.
- **Every background must loop seamlessly.** Nearly every cue in this show is an
  ambient hold of unknown length.
- **Ship a matching still frame with every moving cue.** If playback fails
  mid-show a still is a recoverable night; black is not.
- **Grade on the actual surfaces at show brightness**, not on a laptop. Content
  that looks rich on a monitor goes flat at 8 fL, and you will end up pushing
  contrast and saturation well past what looks correct in the edit suite.

---

## The cyc gradient

The Epson's 0.35:1 ultra-short lens sits 15.79 ft from the cyc and 24.92 ft up.
Illuminance falls as cos(incidence) / distance², and over the 25.4 ft tall lit
band at that angle the top ends up roughly **6.5× brighter than the bottom** —
about 19.7 fL at the top, 9.7 in the middle, 3.0 at the foot of the lit area.

This is geometry, not a fault, and it is not entirely unwelcome: your cyc content
is sky and aurora at the top and dark ground at the bottom, so a top-bright
gradient broadly matches what the images want to do anyway.

`generate.py` computes the real profile from your venue numbers and writes two
correction masks. Change `strength` in the `cyc_gradient_mask` calls to taste —
0.5 halves the gradient, 1.0 flattens it, 0.0 does nothing. Measure the actual
falloff with a meter at five heights at tech before deciding; the model is good
but the cyc's own surface has a say.

---

## Beam-clearance check

Every run ends with a check nobody thinks to do by hand: does any leg stick into
the cyc projector's beam on its way upstage? A leg that intrudes casts a shadow
band across the outer cyc. The script prints the beam half-width at each leg's
depth, the clearance or intrusion, and where the resulting shadow lands, so you
can fix it on paper rather than discovering it at tech.

If you move legs upstage, re-run and read that block before anything else.

With the Epson on line set 14 (+13.81′) both leg pairs sit **downstage of
the cyc projector**, so they cannot block its beam at all — the check reports
them clear by construction. This is the cleanest possible arrangement and it
survives moving the legs anywhere downstage of 13.81′. The upstage pair on set 12
leaves 1.97′ of clearance to the Epson; set 13 would leave 0.99′.

---

## `venue.json`

The numbers the current file set was generated from, dumped for reference. If a
mask ever looks wrong, check this first — it is almost always a venue number
that never got updated after the survey.
