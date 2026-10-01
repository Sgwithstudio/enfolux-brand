"""Build all ENFOLUX identity files (SVG masters + PNG/ICO exports).

Usage:  pip install fonttools cairosvg pillow
        python3 source/build.py

All text is converted to outlines (Montserrat, SIL OFL), so every SVG is
self-contained and renders identically everywhere.
"""
import io
import math
import os

import cairosvg
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.recordingPen import DecomposingRecordingPen
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONT_DIR = os.path.join(ROOT, "source", "fonts")

# ---------------------------------------------------------------- palette
FOREST = "#1F4D3A"
FOREST_900 = "#14302A"
NAVY = "#1C3557"
COPPER = "#A85F22"
CINNAMON = "#C8782E"
WHITE = "#FFFFFF"
CREAM = "#FAF6F0"
CREAM_DK = "#F3ECE1"
INK = "#1B1F1D"

# ---------------------------------------------------------------- fonts
_fonts = {}


def _font(subset, weight):
    key = (subset, weight)
    if key not in _fonts:
        f = TTFont(os.path.join(FONT_DIR, f"{subset}-{weight}.ttf"))
        _fonts[key] = (f.getGlyphSet(), f.getBestCmap())
    return _fonts[key]


def _glyph(ch, weight):
    for subset in ("latin", "vietnamese", "latin-ext"):
        gs, cmap = _font(subset, weight)
        if ord(ch) in cmap:
            return gs, cmap[ord(ch)]
    raise KeyError(f"glyph missing: {ch!r}")


def glyph_info(ch, weight):
    gs, name = _glyph(ch, weight)
    bp = BoundsPen(gs)
    rec = DecomposingRecordingPen(gs)
    gs[name].draw(rec)
    rec.replay(bp)
    return gs[name].width, bp.bounds


def text_path(text, weight, size, x=0.0, y=0.0, tracking=0.0, skip=()):
    """Return (svg path d, advance) for text with baseline at y.

    size is in output units per em, tracking in em. Indices in `skip`
    are laid out but not drawn (so a custom shape can replace them).
    """
    s = size / 1000.0
    pen = SVGPathPen(None)
    cx = x
    positions = []
    for i, ch in enumerate(text):
        gs, name = _glyph(ch, weight)
        g = gs[name]
        positions.append(cx)
        if i not in skip and ch != " ":
            rec = DecomposingRecordingPen(gs)
            g.draw(rec)
            rec.replay(TransformPen(pen, (s, 0, 0, -s, cx, y)))
        cx += g.width * s + (tracking * size if i < len(text) - 1 else 0)
    return pen.getCommands(), cx - x, positions


def text_ink(text, weight, size, tracking=0.0):
    """Ink extents (left, right) relative to origin, for centering."""
    d, adv, pos = text_path(text, weight, size, tracking=tracking)
    s = size / 1000.0
    w0, b0 = glyph_info(text[0], weight)
    wl, bl = glyph_info(text[-1], weight)
    left = b0[0] * s
    right = pos[-1] + bl[2] * s
    return left, right


# ---------------------------------------------------------------- shapes
def circle(cx, cy, r, fill):
    return f'<circle cx="{cx:.2f}" cy="{cy:.2f}" r="{r:.2f}" fill="{fill}"/>'


def drop(cx, cy, r, apex, fill):
    """Teardrop: circle (cx,cy,r) with a point `apex` above the centre."""
    a = math.acos(r / apex)
    tx, ty = r * math.sin(a), -r * math.cos(a)
    return (
        f'<path fill="{fill}" d="M{cx:.2f} {cy - apex:.2f}'
        f"L{cx + tx:.2f} {cy + ty:.2f}"
        f"A{r:.2f} {r:.2f} 0 1 1 {cx - tx:.2f} {cy + ty:.2f}Z\"/>"
    )


def e_mark(cx, cy, R, fill, accent):
    """Direction B symbol: geometric open 'e' + extract drop in the opening.

    R = outer radius. Built on a 100-unit grid scaled to R/46.
    """
    k = R / 46.0
    t = 16 * k  # stroke
    ro, ri = R, R - t
    a_end = math.radians(52)  # arc terminal (below horizontal, y-down)
    # outer ring from crossbar (0deg) counter-clockwise over the top to a_end
    ox0, oy0 = cx + ro, cy
    ix0, iy0 = cx + ri, cy
    oxe, oye = cx + ro * math.cos(a_end), cy + ro * math.sin(a_end)
    ixe, iye = cx + ri * math.cos(a_end), cy + ri * math.sin(a_end)
    ring = (
        f"M{ox0:.2f} {oy0:.2f}"
        f"A{ro:.2f} {ro:.2f} 0 1 0 {oxe:.2f} {oye:.2f}"
        f"L{ixe:.2f} {iye:.2f}"
        f"A{ri:.2f} {ri:.2f} 0 1 1 {ix0:.2f} {iy0:.2f}Z"
    )
    # crossbar: from inner left edge to the outer right edge, top aligned to centre line
    to = math.asin((t / 2) / ro)
    bx = cx + ro * math.cos(to)
    bar = (
        f"M{cx - ri - 1:.2f} {cy - t / 2:.2f}H{bx:.2f}"
        f"A{ro:.2f} {ro:.2f} 0 0 1 {bx:.2f} {cy + t / 2:.2f}"
        f"H{cx - ri - 1:.2f}Z"
    )
    # ring path goes from (ro,0) so the crossbar must cover the joint
    path = f'<path fill="{fill}" d="{ring}"/><path fill="{fill}" d="{bar}"/>'
    # drop sitting in the opening
    ang = math.radians(29)
    rc = (ro + ri) / 2
    dcx, dcy = cx + rc * math.cos(ang) + 1.5 * k, cy + rc * math.sin(ang) + 2.5 * k
    dr = 7.2 * k
    return path + drop(dcx, dcy, dr, dr * 1.75, accent)


# ---------------------------------------------------------------- wordmark
WM_WEIGHT = 600
WM_SIZE = 1000
WM_TRACK = 0.012
ASC = 750  # ink top of f/l at 600 is ~749
DESC = 8


def wordmark(x, y, fill, accent, grain=False, scale=1.0):
    """'enfolux' with baseline at y. Returns (svg, ink_right)."""
    size = WM_SIZE * scale
    skip = ()
    d, adv, pos = text_path("enfolux", WM_WEIGHT, size, x, y, WM_TRACK)
    svg = f'<path fill="{fill}" d="{d}"/>'
    if grain:
        # copper grain inside the counter of the "o"
        s = size / 1000.0
        w, b = glyph_info("o", WM_WEIGHT)
        ocx = pos[3] + (b[0] + b[2]) / 2 * s
        ocy = y - (b[1] + b[3]) / 2 * s
        svg += circle(ocx, ocy, 92 * s, accent)
    _, right = text_ink("enfolux", WM_WEIGHT, size, WM_TRACK)
    return svg, x + right


def wm_left(scale=1.0):
    left, _ = text_ink("enfolux", WM_WEIGHT, WM_SIZE * scale, WM_TRACK)
    return left


# ---------------------------------------------------------------- monogram (C)
def monogram(x, y, size, bg, fg, accent, radius=0.16, knockout=False):
    """Rounded-square monogram: Montserrat 700 'e' + copper level line."""
    r = size * radius
    out = [f'<rect x="{x:.2f}" y="{y:.2f}" width="{size:.2f}" height="{size:.2f}" rx="{r:.2f}" fill="{bg}"/>']
    gsize = size * 0.80
    s = gsize / 1000.0
    w, b = glyph_info("e", 700)
    gw = (b[2] - b[0]) * s
    gh = (b[3] - b[1]) * s
    line_h = size * 0.075
    gap = size * 0.07
    block = gh + gap + line_h
    top = y + (size - block) / 2
    gx = x + (size - gw) / 2 - b[0] * s
    baseline = top + b[3] * s
    d, _, _ = text_path("e", 700, gsize, gx, baseline)
    out.append(f'<path fill="{fg}" d="{d}"/>')
    lw = gw * 0.62
    ly = top + gh + gap
    if knockout:
        lx = x + (size - lw) / 2
        sq = (f"M{x + r:.2f} {y:.2f}H{x + size - r:.2f}A{r:.2f} {r:.2f} 0 0 1 {x + size:.2f} {y + r:.2f}"
              f"V{y + size - r:.2f}A{r:.2f} {r:.2f} 0 0 1 {x + size - r:.2f} {y + size:.2f}"
              f"H{x + r:.2f}A{r:.2f} {r:.2f} 0 0 1 {x:.2f} {y + size - r:.2f}"
              f"V{y + r:.2f}A{r:.2f} {r:.2f} 0 0 1 {x + r:.2f} {y:.2f}Z")
        ln = f"M{lx:.2f} {ly:.2f}h{lw:.2f}v{line_h:.2f}h{-lw:.2f}Z"
        return f'<path fill="{bg}" fill-rule="evenodd" d="{sq}{d}{ln}"/>'
    out.append(
        f'<rect x="{x + (size - lw) / 2:.2f}" y="{ly:.2f}" width="{lw:.2f}" height="{line_h:.2f}" fill="{accent}"/>'
    )
    return "".join(out)


# ---------------------------------------------------------------- marks (square, 1000 units)
def mark_a(fg, accent, size=1000):
    """Direction A symbol: the grain-in-o, as a ring + grain."""
    c = size / 2
    R = size * 0.44
    t = size * 0.155
    return (
        f'<path fill="{fg}" fill-rule="evenodd" d="M{c - R} {c}a{R} {R} 0 1 0 {2 * R} 0a{R} {R} 0 1 0 {-2 * R} 0Z'
        f'M{c - R + t} {c}a{R - t} {R - t} 0 1 0 {2 * (R - t)} 0a{R - t} {R - t} 0 1 0 {-2 * (R - t)} 0Z"/>'
        + circle(c, c, size * 0.135, accent)
    )


def mark_b(fg, accent, size=1000):
    return e_mark(size / 2 - size * 0.01, size / 2, size * 0.46, fg, accent)


def mark_c(bg, fg, accent, size=1000):
    return monogram(0, 0, size, bg, fg, accent)


# ---------------------------------------------------------------- horizontal lockups
PAD = 30  # units of transparent padding around lockups


def lockup(direction, theme):
    """Return (inner svg, width, height) in font units."""
    light = theme == "light"
    fg = FOREST if light else CREAM
    acc = COPPER if light else CINNAMON
    base = PAD + ASC  # baseline
    if direction == "a":
        x = PAD - wm_left()
        svg, right = wordmark(x, base, fg, acc, grain=True)
        w = right + PAD
        h = PAD * 2 + ASC + DESC
        return svg, w, h
    # B, C: mark taller than the text block
    mh = 1000
    h = PAD * 2 + mh
    text_mid = (ASC - DESC) / 2  # mid of ink block above baseline
    base = PAD + mh / 2 + text_mid
    if direction == "b":
        m = e_mark(PAD + mh / 2, PAD + mh / 2, mh / 2, fg, acc)
        gap = 250
    else:
        if light:
            m = monogram(PAD, PAD, mh, FOREST, CREAM, CINNAMON)
        else:
            m = monogram(PAD, PAD, mh, CREAM, FOREST_900, COPPER)
        gap = 270
    x = PAD + mh + gap - wm_left()
    svg, right = wordmark(x, base, fg, acc)
    return m + svg, right + PAD, h


def svg_doc(inner, w, h, bg=None, extra=""):
    bgr = f'<rect width="{w:.2f}" height="{h:.2f}" fill="{bg}"/>' if bg else ""
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w:.2f} {h:.2f}" '
        f'width="{w:.2f}" height="{h:.2f}">{extra}{bgr}{inner}</svg>\n'
    )


def write(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    mode = "wb" if isinstance(data, bytes) else "w"
    with open(path, mode) as f:
        f.write(data)


def png(svg, out_w=None, out_h=None):
    return cairosvg.svg2png(bytestring=svg.encode(), output_width=out_w, output_height=out_h)


# ---------------------------------------------------------------- favicon / icons
def icon_svg(direction, size=512, safe=0.12):
    inner_size = size * (1 - 2 * safe)
    off = size * safe
    if direction == "a":
        m = mark_a(CREAM, CINNAMON, 1000)
    elif direction == "b":
        m = mark_b(CREAM, CINNAMON, 1000)
    else:
        # the monogram already is a forest square: draw the 'e' at full icon size
        m = monogram(0, 0, 1000, FOREST, CREAM, CINNAMON, radius=0)
        return svg_doc(f'<g transform="scale({size / 1000})">{m}</g>', size, size)
    k = inner_size / 1000
    return svg_doc(
        f'<g transform="translate({off} {off}) scale({k})">{m}</g>', size, size, bg=FOREST
    )


# ---------------------------------------------------------------- OG image
OG_W, OG_H = 1200, 630
TAGLINE = "Nguyên liệu thực phẩm chuyên nghiệp"


def og_svg(direction, theme):
    light = theme == "light"
    bg = CREAM if light else FOREST_900
    acc = COPPER if light else CINNAMON
    sub = INK if light else CREAM
    inner, w, h = lockup(direction, theme)
    # fit the logo into the centre square safe zone (630 square minus 60 px margins)
    max_w = 500
    k = max_w / w
    lw, lh = w * k, h * k
    tag_size = 25
    tl, tr = text_ink(TAGLINE, 500, tag_size, 0.0)
    url_size = 17
    ul, ur = text_ink("enfolux.com", 600, url_size, 0.18)
    rule_gap = 34
    block_h = lh + rule_gap + 3 + rule_gap + tag_size * 0.72
    top = (OG_H - block_h) / 2 - 18
    lx = (OG_W - lw) / 2
    parts = [f'<g transform="translate({lx:.2f} {top:.2f}) scale({k:.5f})">{inner}</g>']
    ry = top + lh + rule_gap
    parts.append(f'<rect x="{OG_W / 2 - 24}" y="{ry:.2f}" width="48" height="3" fill="{acc}"/>')
    tb = ry + 3 + rule_gap + tag_size * 0.72
    tx = (OG_W - (tr - tl)) / 2 - tl
    d, _, _ = text_path(TAGLINE, 500, tag_size, tx, tb)
    parts.append(f'<path fill="{sub}" d="{d}"/>')
    ux = (OG_W - (ur - ul)) / 2 - ul
    d, _, _ = text_path("enfolux.com", 600, url_size, ux, OG_H - 72, 0.18)
    parts.append(f'<path fill="{acc}" d="{d}"/>')
    # thin geometric decoration: concentric arcs (grain / drop ripples) bleeding off the edges
    deco = []
    for r in (150, 190, 230):
        deco.append(f'<circle cx="60" cy="560" r="{r}" fill="none" stroke="{acc}" stroke-width="2" opacity="0.55"/>')
        deco.append(f'<circle cx="1140" cy="70" r="{r}" fill="none" stroke="{acc}" stroke-width="2" opacity="0.55"/>')
    deco.append(circle(1140, 70, 10, acc))
    deco.append(circle(60, 560, 10, acc))
    return svg_doc("".join(deco) + "".join(parts), OG_W, OG_H, bg=bg)


# ---------------------------------------------------------------- build
DIRS = {"a": "huong-a-wordmark", "b": "huong-b-bieu-tuong", "c": "huong-c-monogram"}


def build():
    previews = {}
    for key, folder in DIRS.items():
        out = os.path.join(ROOT, folder)
        for theme, suffix in (("light", ""), ("dark", "-dark")):
            inner, w, h = lockup(key, theme)
            svg = svg_doc(inner, w, h)
            write(f"{out}/logo-horizontal{suffix}.svg", svg)
            write(f"{out}/logo-horizontal{suffix}.png", png(svg, out_h=256))
            write(f"{out}/logo-horizontal{suffix}@2x.png", png(svg, out_h=512))
            previews[(key, theme)] = svg
            print(folder, theme, f"ratio {w / h:.2f}:1")
        # single-colour (one ink) versions
        inner, w, h = lockup(key, "light")
        mono = inner.replace(COPPER, FOREST).replace(CINNAMON, FOREST).replace(CREAM, "#FFFFFF")
        if key == "c":
            # knock the 'e' and line out of the square so it stays one colour
            mono = monogram_mono(inner, w, h)
        write(f"{out}/logo-horizontal-1mau.svg", svg_doc(mono, w, h))
        write(f"{out}/logo-horizontal-1mau.png", png(svg_doc(mono, w, h), out_h=256))
        # mark
        if key == "a":
            mark = mark_a(FOREST, COPPER)
        elif key == "b":
            mark = mark_b(FOREST, COPPER)
        else:
            mark = mark_c(FOREST, CREAM, CINNAMON)
        write(f"{out}/logo-mark.svg", svg_doc(mark, 1000, 1000))
        write(f"{out}/logo-mark.png", png(svg_doc(mark, 1000, 1000), 512, 512))
        # icons
        isvg = icon_svg(key)
        write(f"{out}/favicon.svg", isvg)
        fav = png(isvg, 512, 512)
        write(f"{out}/favicon.png", fav)
        write(f"{out}/apple-touch-icon.png", png(isvg, 180, 180))
        img = Image.open(io.BytesIO(fav)).convert("RGBA")
        ico_frames = [Image.open(io.BytesIO(png(isvg, s, s))).convert("RGBA") for s in (16, 32, 48)]
        ico_frames[2].save(f"{out}/favicon.ico", sizes=[(16, 16), (32, 32), (48, 48)],
                           append_images=ico_frames[:2])
        for s in (16, 32, 48):
            write(f"{out}/_kiem-tra/favicon-{s}.png", png(isvg, s, s))
        # OG
        for theme, suffix in (("light", ""), ("dark", "-dark")):
            o = og_svg(key, theme)
            write(f"{out}/og-image{suffix}.svg", o)
            write(f"{out}/og-image{suffix}.png", png(o, OG_W, OG_H))
    return previews


def monogram_mono(inner, w, h):
    """One-colour C: forest square with the 'e' and level line knocked out."""
    wm = inner[inner.rfind("<path"):]
    return monogram(PAD, PAD, 1000, FOREST, None, None, knockout=True) + wm


if __name__ == "__main__":
    build()
