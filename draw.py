#!/usr/bin/env python3
"""Draw the front page for Tuesday 24 November 2026 — v4 rebuild.

Fadli rejected v3 with three specific notes, all fixed here:
  1. IMAGE NOT HD — everything is rendered with 4x supersampling:
     all art and text are drawn on a 4096x4096 canvas, then downscaled
     to 1024x1024 with LANCZOS, so edges are smooth, not jagged.
  2. MAP WAS BAD — the blobby world map is REMOVED. Its slot becomes
     "WHERE IT HAPPENED": a structured region/place/story table.
  3. TEXT NOT STRUCTURED — strict type hierarchy (one size per role,
     same everywhere), a fixed grid, consistent gutters and spacing,
     clear section rules, nothing hugging an edge or colliding.

Style follows Koran 23 v2 (warm newsprint, giant serif date, three
detailed hero scenes, 6-number strip, navy region bar, 10 small cards
with mini art, numbered ALSO, DATE CHECK). Pure Pillow, no network,
no clock, no randomness: the same code always produces identical bytes.
"""
import math
import os
from PIL import Image, ImageDraw, ImageFont

S = 4                      # supersampling factor
W, H = 1024, 1024          # final size (canvas is W*S x H*S)

# ---- palette (same family as Koran 23 v2) --------------------------------
PAPER   = (246, 241, 231)
INK     = (26, 26, 26)
RED     = (179, 38, 30)
DARKRED = (140, 28, 22)
NAVY    = (24, 38, 64)
GOLD    = (201, 162, 39)
LGREY   = (232, 226, 212)
MGREY   = (210, 203, 188)
WHITE   = (255, 255, 255)
SKY     = (178, 214, 235)
GREEN   = (74, 124, 74)
ORANGE  = (224, 122, 26)
YELLOW  = (240, 196, 66)
TEAL    = (40, 110, 130)
TAN     = (198, 164, 110)
BROWN   = (122, 84, 52)
GREY_T  = (110, 108, 100)   # secondary text

FONT_DIR = "/usr/share/fonts/truetype/noto"
SERIF_B  = os.path.join(FONT_DIR, "NotoSerif-Bold.ttf")
SERIF_R  = os.path.join(FONT_DIR, "NotoSerif-Regular.ttf")
SANS_B   = os.path.join(FONT_DIR, "NotoSans-Bold.ttf")
SANS_R   = os.path.join(FONT_DIR, "NotoSans-Regular.ttf")


def sc(v):
    """Scale a 1024-space coordinate to canvas space."""
    return int(round(v * S))


def font(path, size):
    return ImageFont.truetype(path, sc(size))


def lerp(c1, c2, t):
    return tuple(int(round(a + (b - a) * t)) for a, b in zip(c1, c2))


def wrap(draw, text, fnt, max_w):
    words = text.split()
    lines, cur = [], ""
    for w in words:
        trial = (cur + " " + w).strip()
        if draw.textlength(trial, font=fnt) <= sc(max_w):
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def text_block(draw, xy, lines, fnt, fill=INK, leading=None):
    x, y = xy
    if leading is None:
        leading = int(fnt.size * 1.22)
    for ln in lines:
        draw.text((sc(x), sc(y)), ln, font=fnt, fill=fill)
        y += leading / S
    return y


def center_block(draw, cx, y, lines, fnt, fill=INK, leading=None):
    if leading is None:
        leading = int(fnt.size * 1.22)
    for ln in lines:
        w = draw.textlength(ln, font=fnt) / S
        draw.text((sc(cx - w / 2), sc(y)), ln, font=fnt, fill=fill)
        y += leading / S
    return y


def hline(draw, x0, x1, y, fill=INK, width=1):
    draw.line([(sc(x0), sc(y)), (sc(x1), sc(y))], fill=fill, width=sc(width))


def vline(draw, x, y0, y1, fill=INK, width=1):
    draw.line([(sc(x), sc(y0)), (sc(x), sc(y1))], fill=fill, width=sc(width))


def rect(draw, box, fill=None, outline=None, width=1):
    x0, y0, x1, y1 = box
    draw.rectangle([sc(x0), sc(y0), sc(x1), sc(y1)], fill=fill,
                   outline=outline, width=sc(width))


def ell(draw, box, fill=None, outline=None, width=1):
    x0, y0, x1, y1 = box
    draw.ellipse([sc(x0), sc(y0), sc(x1), sc(y1)], fill=fill,
                 outline=outline, width=sc(width))


def poly(draw, pts, fill=None, outline=None):
    draw.polygon([(sc(x), sc(y)) for x, y in pts], fill=fill, outline=outline)


def line(draw, pts, fill=INK, width=1):
    draw.line([(sc(x), sc(y)) for x, y in pts], fill=fill, width=sc(width),
              joint="curve")


def vgrad(draw, box, top, bottom):
    """Smooth vertical gradient over box (1024-space), via a 256-row strip."""
    x0, y0, x1, y1 = box
    w, h = max(1, sc(x1 - x0)), max(1, sc(y1 - y0))
    strip = Image.new("RGB", (1, 256))
    px = strip.load()
    for i in range(256):
        px[0, i] = lerp(top, bottom, i / 255.0)
    g = strip.resize((w, h), Image.BICUBIC)
    draw._image.paste(g, (sc(x0), sc(y0)))


def hgrad(draw, box, left, right):
    x0, y0, x1, y1 = box
    w, h = max(1, sc(x1 - x0)), max(1, sc(y1 - y0))
    strip = Image.new("RGB", (256, 1))
    px = strip.load()
    for i in range(256):
        px[i, 0] = lerp(left, right, i / 255.0)
    g = strip.resize((w, h), Image.BICUBIC)
    draw._image.paste(g, (sc(x0), sc(y0)))


def glow_disc(draw, cx, cy, r, inner, outer, steps=7):
    """Soft glow: nested discs lerping inner -> outer (no alpha needed)."""
    for i in range(steps, 0, -1):
        t = 1.0 - i / steps
        rr = r * i / steps
        ell(draw, (cx - rr, cy - rr, cx + rr, cy + rr),
            fill=lerp(inner, outer, t))


class Overlay:
    """Translucent drawing layer clipped to one box (1024-space)."""

    def __init__(self, box):
        self.box = box
        x0, y0, x1, y1 = box
        self.img = Image.new("RGBA", (sc(x1 - x0), sc(y1 - y0)), (0, 0, 0, 0))
        self.d = ImageDraw.Draw(self.img)

    def ell(self, box, fill):
        x0, y0, x1, y1 = box
        bx, by = self.box[0], self.box[1]
        self.d.ellipse([sc(x0 - bx), sc(y0 - by), sc(x1 - bx), sc(y1 - by)],
                       fill=fill)

    def poly(self, pts, fill):
        bx, by = self.box[0], self.box[1]
        self.d.polygon([(sc(x - bx), sc(y - by)) for x, y in pts], fill=fill)

    def paste(self, base):
        bx, by = self.box[0], self.box[1]
        base.alpha_composite(self.img, (sc(bx), sc(by)))


def lcg(seed):
    """Deterministic pseudo-random stream (fixed seed -> same every run)."""
    x = seed & 0x7FFFFFFF
    while True:
        x = (1103515245 * x + 12345) & 0x7FFFFFFF
        yield x / 0x7FFFFFFF


def flame_poly(cx, base_y, w, h, lean=0.0):
    """Smooth flame outline: rounded base, wavy sides, tip leaning a bit.

    Returns polygon points (1024-space). Never a plain triangle.
    """
    pts = []
    n = 14
    for i in range(n + 1):
        t = i / n                       # 0 at base, 1 at tip
        # wide flat base, gentle mid bulge, taper to a sharp tip
        half = (w / 2.0) * (1 - t ** 1.6) * (1 + 0.15 * math.sin(math.pi * t))
        wob = 0.14 * w * math.sin(2.6 * math.pi * t) * (1 - t)
        x = cx + half + lean * t * w + wob
        pts.append((x, base_y - t * h))
    for i in range(n, -1, -1):
        t = i / n
        half = (w / 2.0) * (1 - t ** 1.6) * (1 + 0.15 * math.sin(math.pi * t))
        wob = 0.14 * w * math.sin(2.6 * math.pi * t + 1.3) * (1 - t)
        x = cx - half + lean * t * w + wob
        pts.append((x, base_y - t * h))
    return pts


def draw_flame(draw, cx, base_y, w, h, lean=0.0):
    """Layered flame: red outer, orange mid, yellow inner, pale core."""
    poly(draw, flame_poly(cx, base_y, w, h, lean), fill=(198, 38, 18))
    poly(draw, flame_poly(cx, base_y - 1, w * 0.64, h * 0.72, lean),
         fill=(238, 118, 20))
    poly(draw, flame_poly(cx, base_y - 1, w * 0.38, h * 0.48, lean),
         fill=(250, 198, 60))
    poly(draw, flame_poly(cx, base_y - 1, w * 0.18, h * 0.28, lean),
         fill=(255, 244, 190))


def smoke_wisps(ov, x, y_top, y_bot, drift=0.0, color=(150, 148, 142)):
    """Thin rising smoke: flat translucent ellipses, never round balls."""
    n = 6
    for i in range(n):
        t = i / (n - 1)
        yy = y_bot - t * (y_bot - y_top)
        ww = 16 + 26 * t
        hh = 5 + 4 * t
        xx = x + drift * t * 30 + 5 * math.sin(i * 1.7)
        a = int(95 - 55 * t)
        ov.ell((xx - ww / 2, yy - hh / 2, xx + ww / 2, yy + hh / 2),
               fill=color + (a,))


def windows(draw, x, y, cols, rows, cw, ch, gx, gy, lit, lit_color,
            dark_color, rng):
    """Window grid; lit pattern from deterministic stream."""
    for r in range(rows):
        for c in range(cols):
            wx = x + c * (cw + gx)
            wy = y + r * (ch + gy)
            col = lit_color if next(rng) < lit else dark_color
            rect(draw, (wx, wy, wx + cw, wy + ch), fill=col)


# ---- hero art ------------------------------------------------------------
# Each art function draws into a box (x, y, w, h) in 1024-space on the
# 4x canvas. All coordinates below are 1024-space; helpers scale them.


def art_huang(d, x, y, w, h):
    """Nvidia stage: dark hall, big chart screen, podium + CEO, audience."""
    # hall background: deep navy gradient, lighter toward the stage
    vgrad(d, (x, y, x + w, y + h), (22, 34, 58), (10, 16, 30))
    # spotlight cone from top centre
    ov = Overlay((x, y, x + w, y + h))
    ov.poly([(x + w * 0.42, y), (x + w * 0.58, y),
             (x + w * 0.72, y + h), (x + w * 0.28, y + h)],
            fill=(255, 244, 200, 26))
    ov.paste(d._image)
    # big screen, left two-thirds
    sx, sy, sw, sh = x + 12, y + 10, w * 0.64, h * 0.62
    rect(d, (sx, sy, sx + sw, sy + sh), fill=(8, 32, 24),
         outline=(120, 160, 130), width=1)
    # screen grid
    for i in range(1, 5):
        gy = sy + sh * i / 5
        line(d, [(sx + 3, gy), (sx + sw - 3, gy)], fill=(38, 74, 56),
             width=0.5)
    for i in range(1, 6):
        gx = sx + sw * i / 6
        line(d, [(gx, sy + 3), (gx, sy + sh - 3)], fill=(38, 74, 56),
             width=0.5)
    # rising area chart
    pts = [(sx + 8, sy + sh - 14), (sx + sw * 0.18, sy + sh * 0.62),
           (sx + sw * 0.34, sy + sh * 0.48), (sx + sw * 0.50, sy + sh * 0.66),
           (sx + sw * 0.64, sy + sh * 0.34), (sx + sw * 0.80, sy + sh * 0.42),
           (sx + sw - 8, sy + sh * 0.16)]
    area = pts + [(sx + sw - 8, sy + sh - 4), (sx + 8, sy + sh - 4)]
    ov2 = Overlay((x, y, x + w, y + h))
    ov2.poly(area, fill=(60, 220, 130, 70))
    ov2.paste(d._image)
    line(d, pts, fill=(110, 240, 160), width=2)
    for px, py in pts:
        ell(d, (px - 2.5, py - 2.5, px + 2.5, py + 2.5), fill=(220, 255, 230))
    # candlesticks, bottom of screen
    rng = lcg(7)
    for i in range(7):
        cx = sx + 14 + i * (sw - 28) / 7
        up = next(rng) > 0.45
        bh = 4 + next(rng) * 7
        by = sy + sh - 8 - bh
        col = (110, 240, 160) if up else (240, 90, 70)
        rect(d, (cx - 2, by, cx + 2, by + bh), fill=col)
    # NVDA chip + +31% label on screen
    f_lab = font(SANS_B, 11)
    d.text((sc(sx + 8), sc(sy + 5)), "NVDA", font=f_lab, fill=(180, 255, 200))
    f_pct = font(SANS_B, 13)
    pct = "+31%"
    d.text((sc(sx + sw - 8 - d.textlength(pct, font=f_pct) / S), sc(sy + 4)),
           pct, font=f_pct, fill=(140, 255, 170))
    # stage floor
    rect(d, (x, y + h * 0.78, x + w, y + h), fill=(16, 20, 34))
    hline(d, x, x + w, y + h * 0.78, fill=(70, 80, 110), width=1)
    # podium + CEO, right of screen (large, clearly readable)
    px = x + w * 0.80
    py = y + h * 0.80
    # warm glow behind the speaker
    glow_disc(d, px, py - 26, 30, (90, 80, 60), (22, 34, 58), steps=5)
    rect(d, (px - 24, py - 2, px + 24, y + h), fill=(52, 40, 30))
    rect(d, (px - 24, py - 2, px + 24, py + 3), fill=(96, 74, 52))
    # CEO: head, hair, suit, green tie, mic
    ell(d, (px - 10, py - 50, px + 10, py - 30), fill=(232, 196, 160))
    poly(d, [(px - 10, py - 44), (px - 9, py - 53), (px + 9, py - 53),
             (px + 10, py - 44), (px + 6, py - 48), (px - 6, py - 48)],
         fill=(40, 32, 26))
    poly(d, [(px - 19, py - 30), (px + 19, py - 30), (px + 22, py - 2),
             (px - 22, py - 2)], fill=(30, 32, 40))
    poly(d, [(px - 4, py - 30), (px + 4, py - 30), (px + 2, py - 8),
             (px - 2, py - 8)], fill=(60, 160, 90))
    line(d, [(px + 24, py - 12), (px + 34, py - 30)], fill=(180, 180, 180),
         width=1.5)
    ell(d, (px + 34, py - 33, px + 39, py - 28), fill=(60, 60, 60))
    # audience silhouettes along the bottom
    rng2 = lcg(21)
    for i in range(9):
        ax = x + 10 + i * (w - 20) / 9 + next(rng2) * 4
        ay = y + h - 2
        ah = 8 + next(rng2) * 5
        ell(d, (ax - 5, ay - ah - 5, ax + 5, ay - ah + 5), fill=(8, 10, 18))
        poly(d, [(ax - 9, ay), (ax + 9, ay), (ax + 6, ay - ah),
                 (ax - 6, ay - ah)], fill=(8, 10, 18))
    # confetti dots over the hall
    rng3 = lcg(99)
    for i in range(26):
        cx = x + 6 + next(rng3) * (w - 12)
        cy = y + 4 + next(rng3) * (h * 0.5)
        col = [(240, 196, 66), (110, 240, 160), (240, 120, 90),
               (150, 200, 255)][i % 4]
        ell(d, (cx - 1, cy - 1, cx + 1, cy + 1), fill=col)


def art_kyiv(d, x, y, w, h):
    """Dymer at dusk: gradient sky, low sun, skyline, cracked apartment."""
    vgrad(d, (x, y, x + w, y + h), (58, 44, 96), (232, 150, 88))
    vgrad(d, (x, y + h * 0.62, x + w, y + h), (214, 122, 74), (120, 62, 52))
    # low sun + glow
    sx, sy = x + w * 0.30, y + h * 0.42
    glow_disc(d, sx, sy, 34, (255, 214, 140), (232, 150, 88), steps=6)
    ell(d, (sx - 13, sy - 13, sx + 13, sy + 13), fill=(255, 226, 160))
    # far skyline silhouettes, left and right
    rng = lcg(31)
    for side in (0, 1):
        bx = x + 6 if side == 0 else x + w * 0.68
        bw = w * 0.30 if side == 0 else w * 0.30
        n = 4
        for i in range(n):
            bwid = bw / n
            bh = h * (0.22 + next(rng) * 0.20)
            bx0 = bx + i * bwid
            rect(d, (bx0, y + h * 0.72 - bh, bx0 + bwid - 2, y + h * 0.72),
                 fill=(52, 40, 66))
            for wy in range(2):
                for wx in range(2):
                    if next(rng) < 0.5:
                        rect(d, (bx0 + 3 + wx * 6, y + h * 0.72 - bh + 5 + wy * 8,
                                 bx0 + 6 + wx * 6, y + h * 0.72 - bh + 8 + wy * 8),
                             fill=(255, 214, 120))
    # central apartment block
    bx, by, bw, bh = x + w * 0.36, y + h * 0.24, w * 0.30, h * 0.50
    rect(d, (bx, by, bx + bw, by + bh), fill=(216, 200, 168),
         outline=(120, 100, 80), width=1)
    rect(d, (bx, by, bx + 5, by + bh), fill=(190, 172, 138))
    windows(d, bx + 9, by + 7, 4, 4, 12, 8, 6, 7, 0.45,
            (255, 214, 120), (70, 62, 52), lcg(41))
    # thin brown crack, roof to middle (zigzag, never spider-thick)
    crack = [(bx + bw * 0.55, by), (bx + bw * 0.48, by + bh * 0.22),
             (bx + bw * 0.58, by + bh * 0.40), (bx + bw * 0.46, by + bh * 0.58),
             (bx + bw * 0.52, by + bh * 0.72)]
    line(d, crack, fill=(96, 66, 44), width=1.5)
    # one shattered window: dark jagged patch
    wx0, wy0 = bx + bw * 0.62, by + bh * 0.30
    poly(d, [(wx0, wy0), (wx0 + 11, wy0 + 2), (wx0 + 9, wy0 + 9),
             (wx0 + 2, wy0 + 8)], fill=(52, 44, 40))
    line(d, [(wx0, wy0), (wx0 + 11, wy0 + 9)], fill=(200, 190, 170),
         width=0.5)
    # rubble at the base
    rng2 = lcg(53)
    for i in range(9):
        rx = bx - 8 + next(rng2) * (bw + 16)
        rw = 4 + next(rng2) * 7
        rh = 3 + next(rng2) * 5
        poly(d, [(rx, by + bh), (rx + rw, by + bh), (rx + rw / 2, by + bh - rh)],
             fill=(140, 122, 100) if i % 2 else (110, 96, 80))
    # ground band
    rect(d, (x, y + h * 0.72, x + w, y + h), fill=(74, 52, 52))
    hline(d, x, x + w, y + h * 0.72, fill=(40, 30, 40), width=1)
    # small drone silhouette in the sky
    dx, dy = x + w * 0.82, y + h * 0.16
    ell(d, (dx - 4, dy - 2, dx + 4, dy + 2), fill=(30, 28, 40))
    line(d, [(dx - 9, dy - 3), (dx + 9, dy - 3)], fill=(30, 28, 40), width=1)
    ell(d, (dx - 10, dy - 5, dx - 6, dy - 1), fill=(30, 28, 40))
    ell(d, (dx + 6, dy - 5, dx + 10, dy - 1), fill=(30, 28, 40))
    # thin smoke wisps from the roof
    ov = Overlay((x, y, x + w, y + h))
    smoke_wisps(ov, bx + bw * 0.7, y + 2, by + 4, drift=0.4,
                color=(140, 134, 128))
    ov.paste(d._image)


def art_fire(d, x, y, w, h):
    """Banten candy plant at night: glowing windows, layered flames,
    smoke wisps, fire truck with ladder."""
    vgrad(d, (x, y, x + w, y + h), (38, 14, 12), (96, 30, 16))
    # orange glow along the horizon
    ov0 = Overlay((x, y, x + w, y + h))
    ov0.poly([(x, y + h * 0.62), (x + w, y + h * 0.62),
              (x + w, y + h), (x, y + h)], fill=(224, 110, 30, 46))
    ov0.paste(d._image)
    # factory: long dark block with sawtooth roof
    fx, fy, fw, fh = x + 8, y + h * 0.48, w - 16, h * 0.30
    rect(d, (fx, fy, fx + fw, fy + fh), fill=(52, 34, 30),
         outline=(24, 16, 14), width=1)
    for i in range(5):
        tx0 = fx + i * fw / 5
        poly(d, [(tx0, fy), (tx0 + fw / 10, fy - 10), (tx0 + fw / 5, fy)],
             fill=(52, 34, 30))
    # glowing orange windows in a row
    rng = lcg(61)
    for i in range(8):
        wx = fx + 6 + i * (fw - 12) / 8
        flick = 200 + int(next(rng) * 40)
        rect(d, (wx, fy + 8, wx + 10, fy + 20), fill=(flick, 130, 30))
        rect(d, (wx, fy + 8, wx + 10, fy + 12), fill=(255, 200, 90))
    # door
    rect(d, (fx + fw / 2 - 7, fy + fh - 16, fx + fw / 2 + 7, fy + fh),
         fill=(30, 20, 18))
    # layered flames above the roof, three clusters (tall, not round)
    draw_flame(d, fx + fw * 0.22, fy - 2, 24, 44, lean=0.10)
    draw_flame(d, fx + fw * 0.52, fy - 2, 30, 54, lean=-0.06)
    draw_flame(d, fx + fw * 0.80, fy - 2, 20, 38, lean=0.14)
    # embers rising
    rng2 = lcg(77)
    for i in range(18):
        ex = fx + next(rng2) * fw
        ey = fy - 8 - next(rng2) * 34
        col = (255, 180, 60) if i % 3 else (255, 120, 40)
        ell(d, (ex - 1, ey - 1, ex + 1, ey + 1), fill=col)
    # smoke wisps drifting right
    ov = Overlay((x, y, x + w, y + h))
    smoke_wisps(ov, fx + fw * 0.52, y + 2, fy - 6, drift=0.8,
                color=(120, 112, 104))
    smoke_wisps(ov, fx + fw * 0.80, y + 8, fy - 4, drift=0.8,
                color=(120, 112, 104))
    ov.paste(d._image)
    # ground + orange reflection
    rect(d, (x, y + h * 0.78, x + w, y + h), fill=(30, 18, 16))
    hgrad(d, (x, y + h * 0.78, x + w, y + h * 0.86), (120, 50, 20),
          (40, 20, 16))
    # fire truck, bottom left, with ladder
    tx, ty = x + 12, y + h * 0.82
    rect(d, (tx, ty, tx + 46, ty + 12), fill=(178, 30, 22))
    rect(d, (tx + 34, ty - 8, tx + 46, ty), fill=(178, 30, 22))
    rect(d, (tx + 37, ty - 6, tx + 44, ty - 1), fill=(180, 220, 240))
    line(d, [(tx + 6, ty - 2), (tx + 44, ty - 22)], fill=(200, 200, 200),
         width=2)
    line(d, [(tx + 10, ty - 4), (tx + 40, ty - 20)], fill=(160, 160, 160),
         width=1)
    ell(d, (tx + 8, ty + 10, tx + 15, ty + 17), fill=(20, 20, 20))
    ell(d, (tx + 34, ty + 10, tx + 41, ty + 17), fill=(20, 20, 20))
    ell(d, (tx + 10, ty + 12, tx + 13, ty + 15), fill=(140, 140, 140))
    ell(d, (tx + 36, ty + 12, tx + 39, ty + 15), fill=(140, 140, 140))


# ---- mini art for the 10 small cards --------------------------------------
# Each draws into a square box (x, y, s) in 1024-space.


def mini_bg(d, x, y, s, tint):
    rect(d, (x, y, x + s, y + s), fill=tint, outline=MGREY, width=1)


def mini_ship(d, x, y, s):
    mini_bg(d, x, y, s, (214, 228, 240))
    rect(d, (x + 6, y + 18, x + s - 6, y + 26), fill=(120, 60, 50))
    rect(d, (x + 10, y + 12, x + 16, y + 18), fill=(200, 160, 60))
    rect(d, (x + 18, y + 10, x + 24, y + 18), fill=(60, 120, 90))
    rect(d, (x + 26, y + 13, x + 32, y + 18), fill=(90, 90, 140))
    line(d, [(x + 4, y + 30), (x + s - 4, y + 30)], fill=(40, 90, 140),
         width=1.5)
    line(d, [(x + 8, y + 34), (x + s - 8, y + 34)], fill=(40, 90, 140),
         width=1.5)


def mini_hazard(d, x, y, s):
    mini_bg(d, x, y, s, (250, 240, 200))
    poly(d, [(x + s / 2, y + 6), (x + s - 6, y + s - 8), (x + 6, y + s - 8)],
         fill=(240, 196, 66))
    poly(d, [(x + s / 2, y + 10), (x + s - 9, y + s - 11),
             (x + 9, y + s - 11)], fill=(250, 214, 90))
    f = font(SANS_B, 16)
    d.text((sc(x + s / 2 - 2), sc(y + 16)), "!", font=f, fill=INK)


def mini_parliament(d, x, y, s):
    mini_bg(d, x, y, s, (228, 226, 214))
    poly(d, [(x + 6, y + 12), (x + s - 6, y + 12), (x + s / 2, y + 5)],
         fill=(140, 120, 90))
    rect(d, (x + 6, y + 12, x + s - 6, y + 15), fill=(160, 140, 110))
    for i in range(4):
        cx = x + 10 + i * 8
        rect(d, (cx, y + 16, cx + 3, y + 30), fill=(120, 100, 80))
    rect(d, (x + 6, y + 30, x + s - 6, y + 33), fill=(160, 140, 110))
    rect(d, (x + 8, y + 33, x + s - 8, y + 36), fill=(140, 120, 90))


def mini_plane(d, x, y, s):
    mini_bg(d, x, y, s, (214, 228, 240))
    poly(d, [(x + 5, y + 20), (x + s - 8, y + 16), (x + s - 4, y + 20),
             (x + s - 8, y + 24)], fill=(220, 225, 230))
    poly(d, [(x + 18, y + 19), (x + 26, y + 8), (x + 30, y + 19)],
         fill=(180, 190, 200))
    poly(d, [(x + 20, y + 21), (x + 26, y + 32), (x + 30, y + 21)],
         fill=(180, 190, 200))
    poly(d, [(x + s - 12, y + 16), (x + s - 6, y + 8), (x + s - 4, y + 16)],
         fill=(200, 205, 210))
    for i in range(3):
        ell(d, (x + 12 + i * 5, y + 18, x + 14 + i * 5, y + 20),
            fill=(40, 90, 140))


def mini_racecar(d, x, y, s):
    mini_bg(d, x, y, s, (232, 226, 214))
    poly(d, [(x + 6, y + 24), (x + 12, y + 18), (x + 26, y + 17),
             (x + 34, y + 22), (x + 36, y + 26), (x + 6, y + 26)],
         fill=(30, 90, 160))
    rect(d, (x + 15, y + 19, x + 23, y + 23), fill=(180, 220, 240))
    rect(d, (x + 30, y + 12, x + 33, y + 18), fill=(30, 90, 160))
    line(d, [(x + 28, y + 13), (x + 36, y + 13)], fill=(30, 90, 160),
         width=1.5)
    ell(d, (x + 10, y + 25, x + 17, y + 32), fill=(20, 20, 20))
    ell(d, (x + 27, y + 25, x + 34, y + 32), fill=(20, 20, 20))
    ell(d, (x + 12, y + 27, x + 15, y + 30), fill=(160, 160, 160))
    ell(d, (x + 29, y + 27, x + 32, y + 30), fill=(160, 160, 160))


def mini_tennis(d, x, y, s):
    mini_bg(d, x, y, s, (214, 232, 200))
    rect(d, (x + 6, y + 8, x + s - 6, y + s - 8), fill=(120, 170, 90),
         outline=(255, 255, 255), width=1)
    line(d, [(x + s / 2, y + 8), (x + s / 2, y + s - 8)], fill=WHITE,
         width=1)
    line(d, [(x + 6, y + s / 2), (x + s - 6, y + s / 2)], fill=WHITE,
         width=1)
    ell(d, (x + s - 16, y + s - 16, x + s - 8, y + s - 8), fill=(200, 230, 80))
    line(d, [(x + s - 15, y + s - 12), (x + s - 9, y + s - 12)],
         fill=(255, 255, 255), width=1)


def mini_train(d, x, y, s):
    mini_bg(d, x, y, s, (222, 230, 238))
    rect(d, (x + 10, y + 8, x + s - 10, y + 30), fill=(40, 90, 160))
    rect(d, (x + 13, y + 11, x + s - 13, y + 18), fill=(180, 220, 240))
    vline(d, x + s / 2, y + 11, y + 18, fill=(40, 90, 160), width=1)
    ell(d, (x + 14, y + 22, x + 19, y + 27), fill=(255, 240, 160))
    ell(d, (x + s - 19, y + 22, x + s - 14, y + 27), fill=(255, 240, 160))
    line(d, [(x + 8, y + 34), (x + s - 8, y + 34)], fill=(90, 90, 90),
         width=1.5)
    line(d, [(x + 12, y + 30), (x + 10, y + 36)], fill=(90, 90, 90),
         width=1)
    line(d, [(x + s - 12, y + 30), (x + s - 10, y + 36)], fill=(90, 90, 90),
         width=1)


def mini_probe(d, x, y, s):
    mini_bg(d, x, y, s, (24, 32, 52))
    ell(d, (x + 8, y + 8, x + 22, y + 22), fill=(200, 170, 130))
    ell(d, (x + 11, y + 11, x + 17, y + 17), fill=(170, 140, 105))
    ell(d, (x + 13, y + 13, x + 15, y + 15), fill=(140, 110, 85))
    rect(d, (x + 26, y + 12, x + s - 8, y + 18), fill=(120, 140, 170))
    rect(d, (x + 24, y + 20, x + 30, y + 26), fill=(160, 170, 190))
    line(d, [(x + 22, y + 16), (x + 26, y + 16)], fill=(160, 170, 190),
         width=1.5)
    for i in range(4):
        ell(d, (x + 6 + i * 8, y + s - 8, x + 8 + i * 8, y + s - 6),
            fill=(255, 255, 255))


def mini_chart_down(d, x, y, s):
    mini_bg(d, x, y, s, (242, 228, 222))
    line(d, [(x + 8, y + 32), (x + 8, y + 10)], fill=INK, width=1.5)
    line(d, [(x + 8, y + 32), (x + s - 6, y + 32)], fill=INK, width=1.5)
    line(d, [(x + 10, y + 14), (x + 18, y + 20), (x + 26, y + 18),
             (x + 34, y + 28)], fill=(179, 38, 30), width=2)
    poly(d, [(x + 34, y + 28), (x + 28, y + 27), (x + 33, y + 33)],
         fill=(179, 38, 30))


def mini_ferrari(d, x, y, s):
    mini_bg(d, x, y, s, (242, 228, 222))
    poly(d, [(x + 5, y + 26), (x + 10, y + 20), (x + 18, y + 18),
             (x + 26, y + 19), (x + 33, y + 23), (x + 36, y + 26),
             (x + 5, y + 26)], fill=(200, 30, 30))
    poly(d, [(x + 13, y + 20), (x + 16, y + 16), (x + 22, y + 16),
             (x + 25, y + 20)], fill=(200, 30, 30))
    rect(d, (x + 16, y + 17, x + 22, y + 20), fill=(180, 220, 240))
    ell(d, (x + 9, y + 25, x + 16, y + 32), fill=(20, 20, 20))
    ell(d, (x + 26, y + 25, x + 33, y + 32), fill=(20, 20, 20))
    ell(d, (x + 11, y + 27, x + 14, y + 30), fill=(160, 160, 160))
    ell(d, (x + 28, y + 27, x + 31, y + 30), fill=(160, 160, 160))


# ---- content (facts identical to v1/v2/v3, verified against Reuters) ------

HEROES = [
    {
        "kicker": "TECH  ·  MARKETS  —  NVIDIA",
        "headline": "HUANG IS BACK",
        "body": ("Nvidia reinstates Jensen Huang as CEO 12 days after he "
                 "quit; shares soar 31% — best day since 2003, adding "
                 "$952bn. Nasdaq +6.5%."),
        "source": "REUTERS · CNN",
        "art": art_huang,
    },
    {
        "kicker": "UKRAINE  ·  DYMER, KYIV REGION",
        "headline": "KYIV UNDER FIRE",
        "body": ("Drone strike collapses a Dymer apartment block: 11 dead, "
                 "2 missing. Zelensky warns of new strikes before Abu "
                 "Dhabi talks."),
        "source": "REUTERS · AL JAZEERA",
        "art": art_kyiv,
    },
    {
        "kicker": "INDONESIA  ·  CIKANDE, BANTEN",
        "headline": "24 DEAD IN FACTORY FIRE",
        "body": ("Indonesia confirms 24 killed in the Banten candy-plant "
                 "blaze; about 30 still missing."),
        "source": "REUTERS · AP",
        "art": art_fire,
    },
]

NUMBERS = [
    ("+31%", "NVIDIA SHARES, MONDAY"),
    ("$952bn", "NVIDIA VALUE GAINED IN A DAY"),
    ("24", "DEAD IN BANTEN FACTORY FIRE"),
    ("11", "DEAD IN DYMER FLAT STRIKE"),
    ("99%", "OF GAZA SHOWS CONTAMINATION"),
    ("1,448", "DOW POINTS GAINED MONDAY"),
]

REGIONS = [("Europe", 11), ("Asia", 16), ("Middle East", 1),
           ("Americas", 6), ("Global", 1)]

SMALL = [
    ("SPARTA II LIMPS HOME",
     "Russian cargo ship hit by drones in the Baltic reaches port under tow.",
     mini_ship),
    ("GAZA 'TOXIC WASTELAND'",
     "Oxfam/CEOBS: 99% of Gaza shows toxic contamination.",
     mini_hazard),
    ("LISBON MARCHES AGAIN",
     "Unions rally outside parliament as MPs vote on the budget today.",
     mini_parliament),
    ("O'HARE GROUND STOP",
     "FAA halts arrivals over staffing as the Thanksgiving rush begins.",
     mini_plane),
    ("VERSTAPPEN WINS VEGAS",
     "Third Las Vegas GP win in four years; Norris 2nd, Piastri 3rd.",
     mini_racecar),
    ("ALCARAZ TAKES ATP FINALS",
     "Beats Zverev 6–2, 7–6 in Turin for his first ATP Finals title.",
     mini_tennis),
    ("NEW INDIA–NEPAL TRAIN",
     "Modi and Nepal's PM flag off the Saryu–Kamala Express.",
     mini_train),
    ("PROBE REACHES MERCURY",
     "ESA/JAXA BepiColombo enters Mercury orbit, only the second ever.",
     mini_probe),
    ("SENSEX SINKS",
     "Sensex falls 1,484 points to 82,435; Nifty down 451.",
     mini_chart_down),
    ("FERRARI'S NEW 296s",
     "Two new 296 Challenge models unveiled at Finali Mondiali.",
     mini_ferrari),
]

ALSO = [
    "India–China generals hold border talks in Arunachal",
    "Modi opens AI centre at IIT Patna, Rs 400cr research park",
    "SpiceJet crisis deepens; pilots urge government action",
    "India's oil import bill jumped about 60% in October",
    "Pant hits 128 as India–NZ Wellington Test ends in draw",
    "Gukesh begins chess title defence vs Sindarov in Geneva",
    "Seoul: new foreign minister and spy chief nominated",
    "China sets 2030 targets for elderly care and childcare",
    "Dhaka vows to arrest Hasina if she returns from India",
    "Armenia drafts new constitution to advance peace with Azerbaijan",
    "Myanmar junta attacks ASEAN decision as unfair",
    "Taliban erase women's names in Balkh, replace with 'Bibi'",
    "Lahore tops world pollution list as AQI passes 500",
    "Magnitude 4.0 quake strikes near Pakistan–Afghan border",
    "About 450 German schools hit by emailed bomb threats",
    "Chinese official sentenced to death for leaking secrets",
    "King Charles reaches out to Meghan after her father's arrest",
    "Trump attacks Newsom in DOJ speech over 548 commuted sentences",
    "Mossad 'saved Taylor Swift's Vienna shows from ISIS plot'",
    "Ex-Jackson mayor jailed 37 months in bribery case",
    "Dutch activist, 28, dies by euthanasia after long struggle",
    "Minnesota fraud probe: $41m, child centres raided",
]

# Structured replacement for the bad world map: region / place / story.
WHERE = [
    ("EUROPE", "Dymer, Ukraine",
     "Drone strike collapses a flat block; 11 dead, 2 missing"),
    ("EUROPE", "Lisbon, Portugal",
     "Unions march as MPs vote on the budget"),
    ("EUROPE", "Turin, Italy",
     "Alcaraz beats Zverev for first ATP Finals title"),
    ("ASIA", "Banten, Indonesia",
     "Candy-plant fire kills 24; about 30 still missing"),
    ("ASIA", "Mumbai, India",
     "Sensex falls 1,484 points to 82,435"),
    ("MIDDLE EAST", "Gaza",
     "99% shows toxic contamination, Oxfam/CEOBS say"),
    ("AMERICAS", "Las Vegas, USA",
     "Verstappen wins third Las Vegas GP in four years"),
    ("AMERICAS", "Chicago, USA",
     "FAA halts O'Hare arrivals over staffing"),
    ("GLOBAL", "Orbit",
     "BepiColombo enters Mercury orbit, only the second ever"),
]

# ---- type scale: ONE size per role, used identically everywhere -----------
F_TOP    = ("sans_b", 12)     # masthead lines
F_DATE   = ("serif_b", 56)    # giant date headline
F_TAG    = ("sans_r", 13)     # tagline under the date
F_KICK   = ("sans_b", 10.5)   # hero kicker (red caps)
F_HEAD   = ("serif_b", 24)    # hero headline
F_BODY   = ("sans_r", 12)     # hero body
F_SRC    = ("sans_r", 9)      # hero source line
F_NUM    = ("serif_b", 30)    # big-number value
F_NUMLAB = ("sans_b", 8.5)    # big-number label
F_BAR    = ("sans_b", 11.5)   # navy region bar
F_SEC    = ("sans_b", 13)     # section headers
F_CTITLE = ("sans_b", 11.5)   # small-card title
F_CBOD   = ("sans_r", 10)     # small-card body
F_WTAG   = ("sans_b", 9)      # where-it-happened region tag
F_WSTORY = ("sans_r", 10.5)   # where-it-happened story
F_ALSO   = ("sans_r", 10)     # also items
F_DC_T   = ("sans_b", 11)     # date-check title
F_DC_B   = ("sans_r", 11)     # date-check body
F_FOOT   = ("sans_r", 9)      # footer


def _font(spec):
    kind, size = spec
    path = {"serif_b": SERIF_B, "serif_r": SERIF_R,
            "sans_b": SANS_B, "sans_r": SANS_R}[kind]
    return font(path, size)


# ---- main layout -----------------------------------------------------------
# Fixed grid: margin 24, content width 976 (x 24..1000), gutters 16/12.

def build():
    canvas = Image.new("RGBA", (W * S, H * S), PAPER + (255,))
    d = ImageDraw.Draw(canvas)
    f = {k: _font(v) for k, v in
         [("top", F_TOP), ("date", F_DATE), ("tag", F_TAG),
          ("kick", F_KICK), ("head", F_HEAD), ("body", F_BODY),
          ("src", F_SRC), ("num", F_NUM), ("numlab", F_NUMLAB),
          ("bar", F_BAR), ("sec", F_SEC), ("ctitle", F_CTITLE),
          ("cbod", F_CBOD), ("wtag", F_WTAG), ("wstory", F_WSTORY),
          ("also", F_ALSO), ("dc_t", F_DC_T), ("dc_b", F_DC_B),
          ("foot", F_FOOT)]}

    # ---- masthead --------------------------------------------------------
    d.text((sc(24), sc(11)), "THE WORLD IN ONE PAGE", font=f["top"],
           fill=INK)
    right = "TUESDAY  ·  24 NOVEMBER 2026"
    d.text((sc(1000 - d.textlength(right, font=f["top"]) / S), sc(11)),
           right, font=f["top"], fill=INK)
    hline(d, 24, 1000, 32, fill=INK, width=2)

    # ---- giant date headline --------------------------------------------
    # Measured ink boxes (1024-space): date descenders reach y=113.5 when
    # drawn at y=40, tagline ink spans y+3.75..y+17.25. The old layout
    # (date y=40, tagline y=103, rule y=131) overlapped the "y" descender
    # of "Tuesday" with the tagline by ~7 units, so the descender tail
    # struck through the "O" of "One". Fix: date up 6, tagline down 9,
    # rule down 2 — ink gaps are now 8.2 / 3.8 / 4.0, nothing touches.
    center_block(d, W // 2, 34, ["Tuesday 24 November 2026"], f["date"],
                 leading=sc(58))
    center_block(d, W // 2, 112,
                 ["One day. Every story that mattered.  35 stories, all verified."],
                 f["tag"], leading=sc(15))
    hline(d, 24, 1000, 133, fill=INK, width=2)

    # ---- hero row ----------------------------------------------------------
    hy, hh = 138, 248
    for i, hero in enumerate(HEROES):
        hx = 24 + i * 331
        hw = 314
        rect(d, (hx, hy, hx + hw, hy + hh), fill=WHITE, outline=INK,
             width=1)
        hero["art"](d, hx + 1, hy + 1, hw - 2, 110)
        hline(d, hx + 1, hx + hw - 1, hy + 111, fill=INK, width=1)
        d.text((sc(hx + 10), sc(hy + 119)), hero["kicker"], font=f["kick"],
               fill=RED)
        hlines = wrap(d, hero["headline"], f["head"], hw - 20)[:2]
        y = text_block(d, (hx + 10, hy + 134), hlines, f["head"],
                       leading=sc(27))
        blines = wrap(d, hero["body"], f["body"], hw - 20)[:3]
        text_block(d, (hx + 10, y + 4), blines, f["body"],
                   leading=sc(14.5))
        d.text((sc(hx + 10), sc(hy + hh - 16)), hero["source"],
               font=f["src"], fill=GREY_T)

    # ---- 6-number strip ----------------------------------------------------
    ny, nh = 396, 60
    rect(d, (24, ny, 1000, ny + nh), fill=(240, 234, 220), outline=INK,
         width=1)
    for i, (val, lab) in enumerate(NUMBERS):
        cx = 24 + (i + 0.5) * 976 / 6
        center_block(d, cx, ny + 6, [val], f["num"], fill=RED,
                     leading=sc(32))
        ll = wrap(d, lab, f["numlab"], 150)
        center_block(d, cx, ny + 40, ll, f["numlab"], leading=sc(10))
        if i:
            vline(d, 24 + i * 976 / 6, ny + 8, ny + nh - 8, fill=MGREY,
                  width=1)

    # ---- navy region bar ----------------------------------------------------
    by, bh = 464, 28
    rect(d, (24, by, 1000, by + bh), fill=NAVY)
    bar = "WHERE THE NEWS WAS   ·   " + "   ·   ".join(
        f"{name} {n}" for name, n in REGIONS)
    center_block(d, W // 2, by + 7, [bar], f["bar"], fill=WHITE,
                 leading=sc(13))

    # ---- 10 small cards, 2 rows of 5 ---------------------------------------
    cw, ch, gap = 185, 76, 12
    cx0 = 24 + (976 - (5 * cw + 4 * gap)) // 2
    for idx, (title, body, art) in enumerate(SMALL):
        r, c = divmod(idx, 5)
        x = cx0 + c * (cw + gap)
        y = 500 + r * (ch + 8)
        rect(d, (x, y, x + cw, y + ch), fill=WHITE, outline=INK, width=1)
        art(d, x + 8, y + 8, 40)
        tlines = wrap(d, title, f["ctitle"], cw - 62)[:2]
        text_block(d, (x + 54, y + 8), tlines, f["ctitle"],
                   leading=sc(13))
        blines = wrap(d, body, f["cbod"], cw - 16)[:2]
        text_block(d, (x + 8, y + 50), blines, f["cbod"],
                   leading=sc(11))

    # ---- bottom section headers --------------------------------------------
    d.text((sc(24), sc(670)), "WHERE IT HAPPENED", font=f["sec"], fill=INK)
    d.text((sc(370), sc(670)), "ALSO ON TUESDAY…", font=f["sec"], fill=INK)
    hline(d, 24, 354, 690, fill=INK, width=1.5)
    hline(d, 370, 1000, 690, fill=INK, width=1.5)

    # ---- WHERE IT HAPPENED (structured table, replaces the bad map) --------
    wy = 698
    for region, place, story in WHERE:
        d.text((sc(24), sc(wy)), f"{region} · {place.upper()}",
               font=f["wtag"], fill=RED)
        d.text((sc(24), sc(wy + 12)), story, font=f["wstory"], fill=INK)
        wy += 29

    # ---- ALSO ON TUESDAY, two even columns ---------------------------------
    for col in range(2):
        ax = 370 + col * 325
        ay = 698
        for n in range(col * 11 + 1, col * 11 + 12):
            item = ALSO[n - 1]
            d.text((sc(ax), sc(ay)), f"{n}.", font=f["also"], fill=RED)
            lines = wrap(d, item, f["also"], 287)
            ay = text_block(d, (ax + 20, ay), lines, f["also"],
                            leading=sc(15))
            ay += 1.5

    # ---- DATE CHECK ----------------------------------------------------------
    dy = 912
    rect(d, (370, dy, 1000, dy + 56), fill=(255, 248, 240),
         outline=RED, width=1.5)
    d.text((sc(382), sc(dy + 7)), "DATE CHECK", font=f["dc_t"], fill=RED)
    dc = ("NOT IN TODAY'S PAPER: COP31 collapsed in Antalya on Monday "
          "23 Nov — that was yesterday's front page. Today's paper only "
          "covers news first reported on Tuesday 24 November.")
    dcl = wrap(d, dc, f["dc_b"], 606)
    text_block(d, (382, dy + 22), dcl, f["dc_b"], leading=sc(13.5))

    # ---- footer --------------------------------------------------------------
    foot = ("Every story here happened, or was first reported, on Tuesday "
            "24 November 2026. All drawings are original. Sources: Reuters "
            "· AP · CNN · Al Jazeera · Oxfam/CEOBS · FAA · ESA · "
            "The Indian Express")
    center_block(d, W // 2, 980, [foot], f["foot"], fill=GREY_T,
                 leading=sc(11))

    return canvas.convert("RGB").resize((W, H), Image.LANCZOS)
