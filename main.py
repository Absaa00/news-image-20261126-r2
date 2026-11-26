#!/usr/bin/env python3
"""THE WORLD TODAY -- front page of world news, Thursday 26 November 2026.

A program that writes one image summing up the day's world news to
/output/entry.png (or $MAKEFUN_OUTPUT_DIR/entry.png when that is set).

Stdlib-only: no Pillow, no network, no pip install. The PNG is encoded by
hand (zlib + struct, IHDR/IDAT/IEND chunks) and all text is drawn with a
built-in 5x7 bitmap font defined in this file. Deterministic: two runs
write byte-identical files.
"""

import os
import struct
import sys
import zlib

W = 1024
H = 1024

PAPER = (251, 247, 238)
PANEL = (255, 255, 255)
INK = (17, 17, 17)
GREY = (74, 74, 74)
RED = (163, 22, 33)
NAVY = (29, 53, 87)
PURPLE = (109, 40, 217)
GREEN = (22, 101, 52)
ORANGE = (194, 65, 12)
TEAL = (15, 118, 110)
GOLD = (180, 130, 29)

# ---------------------------------------------------------------- font 5x7
# Each glyph is 7 rows of 5 cells; "#" is ink, "." is empty.
FONT = {
    "A": [".###.", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"],
    "B": ["####.", "#...#", "#...#", "####.", "#...#", "#...#", "####."],
    "C": [".####", "#....", "#....", "#....", "#....", "#....", ".####"],
    "D": ["####.", "#...#", "#...#", "#...#", "#...#", "#...#", "####."],
    "E": ["#####", "#....", "#....", "####.", "#....", "#....", "#####"],
    "F": ["#####", "#....", "#....", "####.", "#....", "#....", "#...."],
    "G": [".####", "#....", "#....", "#.###", "#...#", "#...#", ".###."],
    "H": ["#...#", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"],
    "I": ["#####", "..#..", "..#..", "..#..", "..#..", "..#..", "#####"],
    "J": ["..###", "...#.", "...#.", "...#.", "...#.", "#..#.", ".##.."],
    "K": ["#...#", "#..#.", "#.#..", "##...", "#.#..", "#..#.", "#...#"],
    "L": ["#....", "#....", "#....", "#....", "#....", "#....", "#####"],
    "M": ["#...#", "##.##", "#.#.#", "#.#.#", "#...#", "#...#", "#...#"],
    "N": ["#...#", "##..#", "#.#.#", "#..##", "#...#", "#...#", "#...#"],
    "O": [".###.", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."],
    "P": ["####.", "#...#", "#...#", "####.", "#....", "#....", "#...."],
    "Q": [".###.", "#...#", "#...#", "#...#", "#.#.#", "#..#.", ".##.#"],
    "R": ["####.", "#...#", "#...#", "####.", "#.#..", "#..#.", "#...#"],
    "S": [".####", "#....", "#....", ".###.", "....#", "....#", "####."],
    "T": ["#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."],
    "U": ["#...#", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."],
    "V": ["#...#", "#...#", "#...#", "#...#", "#...#", ".#.#.", "..#.."],
    "W": ["#...#", "#...#", "#...#", "#.#.#", "#.#.#", "##.##", "#...#"],
    "X": ["#...#", "#...#", ".#.#.", "..#..", ".#.#.", "#...#", "#...#"],
    "Y": ["#...#", "#...#", ".#.#.", "..#..", "..#..", "..#..", "..#.."],
    "Z": ["#####", "....#", "...#.", "..#..", ".#...", "#....", "#####"],
    "0": [".###.", "#...#", "#..##", "#.#.#", "##..#", "#...#", ".###."],
    "1": ["..#..", ".##..", "..#..", "..#..", "..#..", "..#..", ".###."],
    "2": [".###.", "#...#", "....#", "...#.", "..#..", ".#...", "#####"],
    "3": ["####.", "....#", "....#", ".###.", "....#", "....#", "####."],
    "4": ["...#.", "..##.", ".#.#.", "#..#.", "#####", "...#.", "...#."],
    "5": ["#####", "#....", "####.", "....#", "....#", "#...#", ".###."],
    "6": [".###.", "#....", "#....", "####.", "#...#", "#...#", ".###."],
    "7": ["#####", "....#", "...#.", "..#..", "..#..", "..#..", "..#.."],
    "8": [".###.", "#...#", "#...#", ".###.", "#...#", "#...#", ".###."],
    "9": [".###.", "#...#", "#...#", ".####", "....#", "....#", ".###."],
    ".": [".....", ".....", ".....", ".....", ".....", ".....", "..#.."],
    ",": [".....", ".....", ".....", ".....", ".....", "..#..", ".#..."],
    ":": [".....", "..#..", ".....", ".....", ".....", "..#..", "....."],
    ";": [".....", "..#..", ".....", ".....", ".....", "..#..", ".#..."],
    "'": ["..#..", "..#..", ".#...", ".....", ".....", ".....", "....."],
    '"': [".#.#.", ".#.#.", ".....", ".....", ".....", ".....", "....."],
    "!": ["..#..", "..#..", "..#..", "..#..", "..#..", ".....", "..#.."],
    "?": [".###.", "#...#", "....#", "...#.", "..#..", ".....", "..#.."],
    "-": [".....", ".....", ".....", ".###.", ".....", ".....", "....."],
    "(": ["...#.", "..#..", ".#...", ".#...", ".#...", "..#..", "...#."],
    ")": [".#...", "..#..", "...#.", "...#.", "...#.", "..#..", ".#..."],
    "%": ["#...#", "#..#.", "...#.", "..#..", ".#...", "#..#.", "#...#"],
    "/": ["....#", "....#", "...#.", "..#..", ".#...", "#....", "#...."],
    "&": [".##..", "#..#.", "#.#..", ".#...", "#.#.#", "#..#.", ".##.#"],
    "+": [".....", "..#..", "..#..", ".###.", "..#..", "..#..", "....."],
    "=": [".....", ".....", ".###.", ".....", ".###.", ".....", "....."],
    " ": [".....", ".....", ".....", ".....", ".....", ".....", "....."],
}

# ---------------------------------------------------------------- canvas
buf = bytearray(W * H * 3)


def px(x, y, c):
    if 0 <= x < W and 0 <= y < H:
        i = (y * W + x) * 3
        buf[i] = c[0]
        buf[i + 1] = c[1]
        buf[i + 2] = c[2]


def fill(x, y, w, h, c):
    x0 = max(0, x)
    y0 = max(0, y)
    x1 = min(W, x + w)
    y1 = min(H, y + h)
    for yy in range(y0, y1):
        base = (yy * W + x0) * 3
        for xx in range(x0, x1):
            i = base + (xx - x0) * 3
            buf[i] = c[0]
            buf[i + 1] = c[1]
            buf[i + 2] = c[2]


def hline(x, y, w, c, t=1):
    fill(x, y, w, t, c)


def vline(x, y, h, c, t=1):
    fill(x, y, t, h, c)


def rect(x, y, w, h, c, t=3):
    hline(x, y, w, c, t)
    hline(x, y + h - t, w, c, t)
    vline(x, y, h, c, t)
    vline(x + w - t, y, h, c, t)


def line(x0, y0, x1, y1, c, t=1):
    dx = abs(x1 - x0)
    sx = 1 if x0 < x1 else -1
    dy = -abs(y1 - y0)
    sy = 1 if y0 < y1 else -1
    err = dx + dy
    while True:
        fill(x0 - t // 2, y0 - t // 2, t, t, c)
        if x0 == x1 and y0 == y1:
            break
        e2 = 2 * err
        if e2 >= dy:
            err += dy
            x0 += sx
        if e2 <= dx:
            err += dx
            y0 += sy


def disc(cx, cy, r, c):
    for yy in range(cy - r, cy + r + 1):
        for xx in range(cx - r, cx + r + 1):
            if (xx - cx) * (xx - cx) + (yy - cy) * (yy - cy) <= r * r:
                px(xx, yy, c)


def tri(x0, y0, x1, y1, x2, y2, c):
    def sign(ax, ay, bx, by, cx, cy):
        return (ax - cx) * (by - cy) - (bx - cx) * (ay - cy)

    d = sign(x0, y0, x1, y1, x2, y2)
    if d == 0:
        return
    for yy in range(min(y0, y1, y2), max(y0, y1, y2) + 1):
        for xx in range(min(x0, x1, x2), max(x0, x1, x2) + 1):
            s1 = sign(xx, yy, x0, y0, x1, y1)
            s2 = sign(xx, yy, x1, y1, x2, y2)
            s3 = sign(xx, yy, x2, y2, x0, y0)
            if (d > 0 and s1 >= 0 and s2 >= 0 and s3 >= 0) or \
               (d < 0 and s1 <= 0 and s2 <= 0 and s3 <= 0):
                px(xx, yy, c)


# ---------------------------------------------------------------- text
def text_width(s, scale):
    return len(s) * 6 * scale - scale


def draw_text(x, y, s, scale, color):
    cx = x
    for ch in s:
        g = FONT.get(ch, FONT[" "])
        for row in range(7):
            bits = g[row]
            for col in range(5):
                if bits[col] == "#":
                    fill(cx + col * scale, y + row * scale, scale, scale, color)
        cx += 6 * scale
    return cx


def draw_centered(y, s, scale, color):
    draw_text((W - text_width(s, scale)) // 2, y, s, scale, color)


def wrap(s, scale, max_w):
    lines = []
    for para in s.split("\n"):
        words = para.split(" ")
        cur = ""
        for wd in words:
            trial = (cur + " " + wd) if cur else wd
            if text_width(trial, scale) <= max_w or not cur:
                cur = trial
            else:
                lines.append(cur)
                cur = wd
        if cur:
            lines.append(cur)
    return lines


# ---------------------------------------------------------------- panels
def panel(x, y, w, h, kicker, kcolor, headline, body, hscale, art, art_h):
    fill(x, y, w, h, PANEL)
    rect(x, y, w, h, INK, 3)
    pad = 16
    cy = y + pad
    draw_text(x + pad, cy, kicker, 2, kcolor)
    cy += 7 * 2 + 8
    for ln in wrap(headline, hscale, w - 2 * pad):
        draw_text(x + pad, cy, ln, hscale, INK)
        cy += 7 * hscale + 4
    cy += 4
    limit = y + h - art_h - 8
    for ln in wrap(body, 2, w - 2 * pad):
        if cy + 7 * 2 > limit:
            break
        draw_text(x + pad, cy, ln, 2, GREY)
        cy += 7 * 2 + 3
    art(x, y, w, h, art_h)


# ---------------------------------------------------------------- art
def art_refinery(bx, by, bw, bh, ah):
    # box at right side of the lead panel
    x0 = bx + 660
    y0 = by + 34
    w = 300
    h = bh - 68
    disc(x0 + 250, y0 + 26, 18, GOLD)
    fill(x0, y0 + h - 10, w, 4, INK)
    # three towers
    for i, th in enumerate((120, 150, 100)):
        tx = x0 + 20 + i * 62
        fill(tx, y0 + h - 10 - th, 34, th, NAVY if i != 1 else RED)
        for k in range(3):
            hline(tx - 4, y0 + h - 30 - k * 36, 42, PANEL, 3)
    # flame above the middle tower
    tri(x0 + 96, y0 + h - 10 - 150, x0 + 82, y0 + h - 10 - 182,
        x0 + 110, y0 + h - 10 - 182, ORANGE)
    tri(x0 + 96, y0 + h - 10 - 158, x0 + 88, y0 + h - 10 - 176,
        x0 + 104, y0 + h - 10 - 176, GOLD)
    # smoke
    disc(x0 + 40, y0 + 12, 9, GREY)
    disc(x0 + 62, y0 + 4, 7, GREY)


def art_tanker(bx, by, bw, bh, ah):
    yb = by + bh - ah + 12
    # containers
    fill(bx + 30, yb, 46, 18, RED)
    fill(bx + 80, yb, 46, 18, NAVY)
    fill(bx + 130, yb, 46, 18, GOLD)
    fill(bx + 55, yb - 18, 46, 18, TEAL)
    fill(bx + 105, yb - 18, 46, 18, ORANGE)
    # hull
    fill(bx + 20, yb + 18, 220, 16, INK)
    tri(bx + 240, yb + 18, bx + 272, yb + 18, bx + 240, yb + 34, INK)
    # bridge
    fill(bx + 196, yb - 16, 26, 34, GREY)
    # waves
    for k in range(3):
        yy = yb + 40 + k * 8
        for sx in range(0, bw - 32, 24):
            hline(bx + 16 + sx, yy, 14, NAVY, 3)


def art_rocket(bx, by, bw, bh, ah):
    yb = by + bh - ah + 6
    # stars
    for sx, sy in ((30, 8), (70, 22), (250, 6), (285, 26), (150, 4)):
        fill(bx + sx, yb + sy, 3, 3, GOLD)
    # planet
    disc(bx + 255, yb + 34, 16, PURPLE)
    line(bx + 232, yb + 26, bx + 278, yb + 42, INK, 2)
    # rocket body
    cx = bx + 130
    fill(cx - 12, yb + 6, 24, 34, RED)
    tri(cx - 12, yb + 6, cx + 12, yb + 6, cx, yb - 14, RED)
    tri(cx - 12, yb + 40, cx - 26, yb + 52, cx - 12, yb + 28, NAVY)
    tri(cx + 12, yb + 40, cx + 26, yb + 52, cx + 12, yb + 28, NAVY)
    tri(cx - 8, yb + 40, cx + 8, yb + 40, cx, yb + 58, ORANGE)
    fill(cx - 4, yb + 14, 8, 8, PANEL)


def art_factory(bx, by, bw, bh, ah):
    yb = by + bh - ah + 10
    disc(bx + 262, yb + 10, 14, GOLD)
    # chimney
    fill(bx + 34, yb - 26, 16, 34, RED)
    # factory body with sawtooth roof
    fill(bx + 56, yb - 6, 170, 34, NAVY)
    tri(bx + 56, yb - 6, bx + 98, yb - 6, bx + 98, yb - 26, NAVY)
    tri(bx + 98, yb - 6, bx + 140, yb - 6, bx + 140, yb - 26, NAVY)
    tri(bx + 140, yb - 6, bx + 182, yb - 6, bx + 182, yb - 26, NAVY)
    tri(bx + 182, yb - 6, bx + 226, yb - 6, bx + 226, yb - 26, NAVY)
    # windows
    for wx in range(66, 216, 26):
        fill(bx + wx, yb + 6, 14, 12, PANEL)
    # spool of thread
    fill(bx + 246, yb + 8, 8, 20, TEAL)
    disc(bx + 250, yb + 8, 7, TEAL)


def art_bars(bx, by, bw, bh, ah):
    yb = by + bh - 14
    base = yb - 8
    hline(bx + 30, base, bw - 60, INK, 3)
    vline(bx + 30, base - 64, 64, INK, 3)
    bars = ((70, 22, RED), (150, 38, ORANGE), (230, 56, NAVY))
    for off, bhgt, col in bars:
        fill(bx + off, base - bhgt, 44, bhgt, col)
    draw_text(bx + 300, base - 46, "500,000", 3, RED)


def art_cricket(bx, by, bw, bh, ah):
    yb = by + bh - 16
    base = yb - 6
    # stumps
    for sx in (70, 86, 102):
        fill(bx + sx, base - 52, 8, 52, GOLD)
    fill(bx + 70, base - 58, 14, 5, INK)
    fill(bx + 88, base - 58, 14, 5, INK)
    # ball
    disc(bx + 150, base - 18, 12, RED)
    line(bx + 128, base - 40, bx + 172, base - 2, GREY, 2)
    # bat
    line(bx + 220, base - 58, bx + 268, base - 6, INK, 7)
    line(bx + 220, base - 58, bx + 206, base - 72, INK, 5)
    draw_text(bx + 320, base - 40, "204", 4, TEAL)


# ---------------------------------------------------------------- png
def _chunk(typ, data):
    return (struct.pack(">I", len(data)) + typ + data +
            struct.pack(">I", zlib.crc32(typ + data) & 0xFFFFFFFF))


def write_png(path, w, h, rgb):
    raw = bytearray()
    stride = w * 3
    for y in range(h):
        raw.append(0)
        raw += rgb[y * stride:(y + 1) * stride]
    ihdr = struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)
    png = (b"\x89PNG\r\n\x1a\n" + _chunk(b"IHDR", ihdr) +
           _chunk(b"IDAT", zlib.compress(bytes(raw), 9)) + _chunk(b"IEND", b""))
    with open(path, "wb") as f:
        f.write(png)
    return len(png)


# ---------------------------------------------------------------- page
def build():
    fill(0, 0, W, H, PAPER)

    # masthead
    draw_centered(30, "THE WORLD TODAY", 8, INK)
    hline(24, 100, 976, INK, 3)
    draw_centered(112, "THURSDAY 26 NOVEMBER 2026", 3, GREY)
    draw_centered(140, "ONE IMAGE, SIX STORIES FROM AROUND THE GLOBE", 2, RED)

    # lead story
    x, y, w, h = 24, 172, 976, 240
    fill(x, y, w, h, PANEL)
    rect(x, y, w, h, INK, 3)
    draw_text(x + 16, y + 16, "LEAD STORY", 2, RED)
    cy = y + 16 + 14 + 8
    for ln in wrap("HOUTHIS STRIKE RAS TANURA REFINERY", 5, 620):
        draw_text(x + 16, cy, ln, 5, INK)
        cy += 7 * 5 + 4
    cy += 4
    for ln in wrap("YEMEN'S HOUTHIS HIT SAUDI ARABIA'S RAS TANURA "
                   "REFINERY IN A DRONE AND MISSILE ATTACK.", 3, 620):
        draw_text(x + 16, cy, ln, 3, GREY)
        cy += 7 * 3 + 3
    art_refinery(x, y, w, h, 0)

    # row of three
    rw, rh, ry = 316, 250, 426
    panel(24, ry, rw, rh, "GULF", NAVY,
          "TWO TANKERS HIT BY MINES IN STRAIT OF HORMUZ",
          "TWO OIL TANKERS WERE DAMAGED BY SEA MINES IN THE "
          "STRAIT OF HORMUZ.", 3, art_tanker, 64)
    panel(354, ry, rw, rh, "SPACE", PURPLE,
          "FIRST PAKISTANI ASTRONAUT HEADS TO TIANGONG",
          "PAKISTAN'S FIRST ASTRONAUT WILL FLY TO CHINA'S "
          "TIANGONG STATION ON SHENZHOU-24.", 3, art_rocket, 64)
    panel(684, ry, rw, rh, "LABOUR", GREEN,
          "BANGLADESH GARMENT WORKERS WIN 36% PAY RISE",
          "GARMENT WORKERS IN BANGLADESH SECURED A 36% WAGE "
          "INCREASE AFTER TALKS.", 3, art_factory, 64)

    # row of two
    rw2, rh2, ry2 = 481, 310, 690
    panel(24, ry2, rw2, rh2, "WAR", RED,
          "RUSSIA'S OWN DATA: ABOUT 500,000 KILLED IN UKRAINE WAR",
          "RUSSIAN FIGURES POINT TO ABOUT 500,000 DEATHS IN THE "
          "WAR IN UKRAINE.", 4, art_bars, 84)
    panel(519, ry2, rw2, rh2, "SPORT", TEAL,
          "SOORYAVANSHI, 15, SMASHES WORLD RECORD 204 OFF 53 BALLS",
          "FIFTEEN-YEAR-OLD VAIBHAV SOORYAVANSHI HIT 204 FROM "
          "JUST 53 BALLS.", 4, art_cricket, 84)

    # footer credit line in the bottom margin
    draw_centered(1006, "DRAWN FROM THE DAY'S REPORTS - 26 NOVEMBER 2026",
                  2, GREY)


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR") or "/output"
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "entry.png")
    build()
    n = write_png(out_path, W, H, buf)
    print("wrote %s 1024x1024 %d bytes" % (out_path, n))
    return 0


if __name__ == "__main__":
    sys.exit(main())
