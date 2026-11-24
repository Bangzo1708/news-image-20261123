#!/usr/bin/env python3
"""Build the news-image-20261123 front page: one image summing up the
world news of Monday 23 November 2026.

Renders three layout variants (A: classic broadsheet, B: dark magazine,
C: six-card grid) from the same verified story set, all drawn with PIL
geometry only -- no photos, no downloads, fully deterministic.

Usage: python3 build_image.py [a|b|c|all]
"""
import sys
from PIL import Image, ImageDraw, ImageFont

W, H = 1024, 1024
PAPER = (247, 243, 234)      # newsprint cream
INK = (18, 18, 18)
RED = (178, 34, 34)
NAVY = (14, 26, 46)
GOLD = (201, 162, 39)
GREY = (90, 90, 90)
LIGHTGREY = (220, 216, 206)

SERIF = "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf"
SERIF_B = "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"
SANS = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
SANS_B = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


def font(path, size):
    return ImageFont.truetype(path, size)


def wrap(d, text, f, max_w):
    """Greedy word wrap returning a list of lines that fit max_w."""
    words = text.split()
    lines, cur = [], ""
    for w in words:
        trial = (cur + " " + w).strip()
        if d.textlength(trial, font=f) <= max_w:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def para(d, x, y, text, f, color, max_w, leading=None):
    """Draw wrapped paragraph, return y after last line."""
    lh = leading or int(f.size * 1.28)
    for line in wrap(d, text, f, max_w):
        d.text((x, y), line, font=f, fill=color)
        y += lh
    return y


def headline(d, x, y, text, f, color, max_w, leading=None):
    lh = leading or int(f.size * 1.12)
    for line in wrap(d, text, f, max_w):
        d.text((x, y), line, font=f, fill=color)
        y += lh
    return y


def rule(d, x0, y, x1, color=INK, w=2):
    d.line([(x0, y), (x1, y)], fill=color, width=w)


# ---------------------------------------------------------------- icons
def draw_globe(d, cx, cy, r, sea=(38, 90, 140), land=(46, 139, 87),
               outline=INK):
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=sea, outline=outline,
              width=3)
    # crude continents: a few blobs
    d.ellipse([cx - r * 0.75, cy - r * 0.55, cx - r * 0.15, cy - r * 0.05],
              fill=land)
    d.ellipse([cx - r * 0.1, cy + r * 0.05, cx + r * 0.55, cy + r * 0.6],
              fill=land)
    d.ellipse([cx + r * 0.15, cy - r * 0.7, cx + r * 0.7, cy - r * 0.25],
              fill=land)
    d.ellipse([cx - r * 0.45, cy + r * 0.35, cx - r * 0.05, cy + r * 0.75],
              fill=land)
    # latitude / longitude arcs
    d.arc([cx - r, cy - r, cx + r, cy + r], 200, 340, fill=(255, 255, 255),
          width=2)
    d.line([cx, cy - r, cx, cy + r], fill=(255, 255, 255), width=2)


def draw_flames(d, x, y, s):
    """Simple flame cluster anchored at (x, y) baseline, size s."""
    flames = ((-s * 0.5, s * 0.42, s * 0.8, (230, 126, 34)),
              (0.0, s * 0.5, s * 1.05, (231, 76, 60)),
              (s * 0.42, s * 0.4, s * 0.7, (243, 156, 18)))
    for dx, w, h, col in flames:
        d.polygon([(x + dx, y),
                   (x + dx + w * 0.5, y - h),
                   (x + dx + w, y)], fill=col)
    d.ellipse([x - s * 0.12, y - s * 0.45, x + s * 0.32, y - s * 0.05],
              fill=(247, 220, 111))


def draw_ship(d, x, y, w, h):
    """Tanker silhouette: hull + containers + smoke, baseline y."""
    d.polygon([(x, y - h * 0.45), (x + w, y - h * 0.45),
               (x + w * 0.88, y), (x + w * 0.12, y)], fill=(52, 73, 94))
    d.rectangle([x + w * 0.14, y - h * 0.85, x + w * 0.42, y - h * 0.45],
                fill=(178, 34, 34))
    d.rectangle([x + w * 0.46, y - h * 0.8, x + w * 0.68, y - h * 0.45],
                fill=(201, 162, 39))
    d.rectangle([x + w * 0.74, y - h, x + w * 0.82, y - h * 0.45],
                fill=(44, 62, 80))
    # waves
    for i in range(4):
        wx = x - 6 + i * (w // 3)
        d.arc([wx, y + 2, wx + 34, y + 16], 0, 180, fill=(38, 90, 140),
              width=3)


def draw_factory(d, x, y, w, h):
    """Factory with two chimneys and smoke puffs, baseline y."""
    d.rectangle([x, y - h * 0.55, x + w * 0.62, y], fill=(120, 120, 120))
    d.polygon([(x, y - h * 0.55), (x + w * 0.31, y - h * 0.85),
               (x + w * 0.62, y - h * 0.55)], fill=(90, 90, 90))
    d.rectangle([x + w * 0.68, y - h, x + w * 0.8, y], fill=(100, 100, 100))
    d.rectangle([x + w * 0.86, y - h * 0.85, x + w * 0.97, y],
                fill=(110, 110, 110))
    for sx, sy, r in ((x + w * 0.74, y - h - 14, 9),
                      (x + w * 0.78, y - h - 30, 12),
                      (x + w * 0.72, y - h - 48, 15),
                      (x + w * 0.9, y - h - 26, 10)):
        d.ellipse([sx - r, sy - r, sx + r, sy + r], fill=(200, 200, 200))


def draw_flags(d, x, y, w, h):
    """Two small flags side by side: Nepal crimson pennant + India tricolour."""
    # Nepal pennant (stylised triangle pair)
    d.polygon([(x, y), (x + w * 0.42, y + h * 0.28),
               (x, y + h * 0.55)], fill=(220, 20, 60))
    d.polygon([(x, y + h * 0.55), (x + w * 0.42, y + h * 0.82),
               (x, y + h)], fill=(220, 20, 60))
    # India tricolour
    fx = x + w * 0.52
    fw, fh = w * 0.48, h * 0.32
    d.rectangle([fx, y, fx + fw, y + fh], fill=(255, 153, 51))
    d.rectangle([fx, y + fh, fx + fw, y + 2 * fh], fill=(255, 255, 255),
                outline=INK)
    d.rectangle([fx, y + 2 * fh, fx + fw, y + 3 * fh], fill=(19, 136, 8))
    d.ellipse([fx + fw / 2 - 8, y + fh - 8, fx + fw / 2 + 8, y + fh + 8],
              outline=(0, 0, 128), width=2)


def draw_grad_cap(d, x, y, w, h):
    """Graduation cap with a red X mark (resignation)."""
    cx, cy = x + w / 2, y + h * 0.42
    d.polygon([(cx - w * 0.5, cy), (cx, cy - h * 0.28),
               (cx + w * 0.5, cy), (cx, cy + h * 0.28)], fill=(30, 30, 30))
    d.rectangle([cx - w * 0.22, cy + h * 0.05, cx + w * 0.22,
                 cy + h * 0.42], fill=(30, 30, 30))
    d.line([cx + w * 0.5, cy, cx + w * 0.5, cy + h * 0.45],
           fill=(201, 162, 39), width=3)
    d.ellipse([cx + w * 0.42, cy + h * 0.42, cx + w * 0.58, cy + h * 0.58],
              fill=(201, 162, 39))
    # red X
    s = w * 0.2
    d.line([cx + s, cy - h * 0.55, cx + s * 2, cy - h * 0.1],
           fill=RED, width=5)
    d.line([cx + s * 2, cy - h * 0.55, cx + s, cy - h * 0.1],
           fill=RED, width=5)


def draw_building_smoke(d, x, y, w, h):
    """Apartment block with smoke and a small drone above."""
    d.rectangle([x, y - h * 0.8, x + w * 0.55, y], fill=(93, 109, 126))
    d.rectangle([x + w * 0.6, y - h * 0.55, x + w, y], fill=(120, 130, 145))
    for r in range(3):
        for c in range(2):
            wx = x + 10 + c * (w * 0.26)
            wy = y - h * 0.72 + r * (h * 0.22)
            d.rectangle([wx, wy, wx + w * 0.14, wy + h * 0.12],
                        fill=(247, 220, 111))
    # smoke
    for sx, sy, r in ((x + w * 0.3, y - h * 0.92, 10),
                      (x + w * 0.36, y - h - 12, 13),
                      (x + w * 0.28, y - h - 30, 16)):
        d.ellipse([sx - r, sy - r, sx + r, sy + r], fill=(170, 170, 170))
    # drone
    dx, dy = x + w * 0.8, y - h - 34
    d.rectangle([dx - 12, dy - 4, dx + 12, dy + 4], fill=INK)
    d.ellipse([dx - 24, dy - 8, dx - 8, dy], fill=(120, 120, 120))
    d.ellipse([dx + 8, dy - 8, dx + 24, dy], fill=(120, 120, 120))


# ---------------------------------------------------------------- stories
STORIES = [
    dict(tag="CLIMATE  •  ANTALYA, TURKEY",
         head="CLIMATE TALKS COLLAPSE",
         body=("After two weeks, the longest COP in history ends with no deal. "
               "The EU rejected the Antalya Pact because the draft never even "
               "named fossil fuels."),
         icon="globe"),
    dict(tag="WAR IN THE GULF  •  BAHRAIN",
         head="IRAN HITS US BASE; BAHRAIN DEMANDS UN ACTION",
         body=("Iran struck a US radar base in Bahrain and tankers came under "
               "fire in the Strait of Hormuz, the world's oil lifeline."),
         icon="ship"),
    dict(tag="UKRAINE  •  KYIV REGION",
         head="DRONE HITS FLATS; 14 MISSING",
         body=("A Russian drone struck a residential building; at least 14 "
               "people are missing, President Zelenskyy says. A Russian cargo "
               "ship burns off Finland."),
         icon="building"),
    dict(tag="ASIA  •  NEW DELHI",
         head="NEPAL PM MEETS MODI",
         body=("Nepal's PM Balendra Shah holds bilateral talks with India's "
               "PM Narendra Modi on his state visit to New Delhi."),
         icon="flags"),
    dict(tag="SOUTH KOREA  •  SEOUL",
         head="MINISTER QUITS OVER AI CHEATING",
         body=("South Korea's education minister resigns amid an AI-driven "
               "exam-cheating scandal."),
         icon="cap"),
    dict(tag="INDONESIA",
         head="FACTORY FIRE: DOZENS MISSING",
         body=("A fire at a candy factory leaves 3 dead and dozens of "
               "workers unaccounted for."),
         icon="factory"),
]

TICKER = ("INDIA 720/9d IN WELLINGTON   •   DEMOCRATS TAKE 258 HOUSE "
          "SEATS   •   UN KEEPS AI-WEAPONS TALKS GOING   •   LISBON MARCH "
          "OVER LIVING COSTS")

def icon_tile(kind, w, h):
    """Render one story icon onto its own tile; drawing outside the tile
    is clipped by PIL, so smoke/flames can never spill into the text."""
    tile = Image.new("RGB", (w, h), (232, 228, 216))
    td = ImageDraw.Draw(tile)
    ICON_DRAW[kind](td, 0, 0, w, h)
    return tile


def fit_ticker(d, text, max_w, size=15):
    """Largest bold size (<= size) at which the ticker fits max_w."""
    while size > 10:
        f = font(SANS_B, size)
        if d.textlength(text, font=f) <= max_w:
            return f
        size -= 1
    return font(SANS_B, 10)


ICON_DRAW = {"globe": lambda d, x, y, w, h: draw_globe(
                 d, x + w / 2, y + h / 2, min(w, h) * 0.42),
             "ship": lambda d, x, y, w, h: draw_ship(d, x + 6, y + h - 22,
                                                      w - 12, h * 0.6),
             "building": lambda d, x, y, w, h: draw_building_smoke(
                 d, x + 8, y + h - 8, w - 16, h * 0.62),
             "flags": lambda d, x, y, w, h: draw_flags(d, x + 8, y + 12,
                                                        w - 16, h - 24),
             "cap": lambda d, x, y, w, h: draw_grad_cap(d, x + 8, y + 10,
                                                         w - 16, h - 20),
             "factory": lambda d, x, y, w, h: draw_factory(d, x + 8, y + h - 8,
                                                            w - 16, h * 0.6)}


def masthead_a(d):
    """Classic newspaper masthead for variants A and C."""
    d.text((512, 26), "THE WORLD TODAY", font=font(SERIF_B, 74),
           fill=INK, anchor="ma")
    rule(d, 36, 118, 988, INK, 4)
    rule(d, 36, 124, 988, INK, 1)
    d.rectangle([36, 132, 988, 178], fill=INK)
    d.text((512, 138), "MONDAY  •  23 NOVEMBER 2026  •  ONE DAY, ONE IMAGE",
           font=font(SANS_B, 26), fill=(255, 255, 255), anchor="ma")


# ---------------------------------------------------------------- variant A
def variant_a():
    img = Image.new("RGB", (W, H), PAPER)
    d = ImageDraw.Draw(img)
    masthead_a(d)

    # --- lead story: COP31, full width with globe illustration
    s = STORIES[0]
    d.text((36, 196), s["tag"], font=font(SANS_B, 19), fill=RED)
    y = headline(d, 36, 222, s["head"], font(SERIF_B, 62), INK, 620, 66)
    y = para(d, 36, y + 8, s["body"], font(SERIF, 23), INK, 600, 30)
    # illustration panel right
    d.rectangle([690, 196, 988, 420], outline=INK, width=3, fill=(232, 228, 216))
    draw_globe(d, 839, 292, 74)
    draw_flames(d, 800, 388, 34)
    d.text((839, 392), "ANTALYA: NO DEAL",
           font=font(SANS_B, 16), fill=INK, anchor="ma")
    rule(d, 36, 440, 988, INK, 2)

    # --- 2 x 2 grid of the next four stories
    cells = [(36, 462, 460, 240), (528, 462, 460, 240),
             (36, 722, 460, 240), (528, 722, 460, 240)]
    for st, (cx, cy, cw, ch) in zip(STORIES[1:5], cells):
        d.text((cx, cy), st["tag"], font=font(SANS_B, 15), fill=RED)
        yy = headline(d, cx, cy + 26, st["head"], font(SERIF_B, 27), INK,
                      cw, 31)
        yy = para(d, cx, yy + 6, st["body"], font(SERIF, 18), INK, cw, 23)
        # small icon at bottom-right of the cell
        ICON_DRAW[st["icon"]](d, cx + cw - 108, cy + ch - 96, 104, 92)
    rule(d, 36, 712, 988, LIGHTGREY, 1)
    d.line([(512, 462), (512, 962)], fill=LIGHTGREY, width=1)

    # footer ticker (auto-fit so it never runs off the right edge)
    d.rectangle([0, 968, 1024, 1024], fill=INK)
    tf = fit_ticker(d, TICKER, 1000)
    d.text((512, 978), TICKER, font=tf,
           fill=(255, 255, 255), anchor="ma")
    return img


# ---------------------------------------------------------------- variant B
def variant_b():
    img = Image.new("RGB", (W, H), NAVY)
    d = ImageDraw.Draw(img)
    # gold frame
    d.rectangle([18, 18, 1006, 1006], outline=GOLD, width=3)
    d.text((512, 44), "THE WORLD IN ONE IMAGE", font=font(SANS_B, 24),
           fill=GOLD, anchor="ma")
    d.text((512, 76), "23 NOVEMBER 2026", font=font(SERIF_B, 96),
           fill=(255, 255, 255), anchor="ma")
    d.text((512, 176), "MONDAY", font=font(SANS_B, 30),
           fill=(255, 255, 255), anchor="ma")
    rule(d, 312, 224, 712, GOLD, 2)

    # central illustration: globe over a burning sea
    draw_globe(d, 512, 330, 92, sea=(30, 70, 120), land=(60, 130, 80))
    draw_flames(d, 452, 452, 44)
    draw_ship(d, 392, 470, 240, 60)
    d.text((512, 500), "A WORLD ON EDGE: WAR IN THE GULF, CLIMATE TALKS FAIL",
           font=font(SANS_B, 17), fill=GOLD, anchor="ma")

    # numbered story rows
    y = 548
    for i, st in enumerate(STORIES, 1):
        d.text((52, y), f"{i}", font=font(SERIF_B, 40), fill=GOLD)
        d.text((108, y + 2), st["tag"], font=font(SANS_B, 14),
               fill=(170, 190, 220))
        yy = headline(d, 108, y + 22, st["head"], font(SANS_B, 24),
                      (255, 255, 255), 860, 27)
        para(d, 108, yy + 2, st["body"], font(SANS, 17), (200, 210, 225),
             860, 21)
        y += 74 if i < 6 else 0
        if i < 6:
            d.line([(52, y - 6), (972, y - 6)], fill=(40, 60, 90), width=1)
    # footer ticker
    d.text((512, 984), "INDIA 720/9d IN WELLINGTON  •  DEMOCRATS 258 HOUSE "
           "SEATS  •  UN KEEPS AI-WEAPONS TALKS GOING",
           font=font(SANS_B, 14), fill=(170, 190, 220), anchor="ma")
    return img


# ---------------------------------------------------------------- variant C
def variant_c():
    img = Image.new("RGB", (W, H), PAPER)
    d = ImageDraw.Draw(img)
    masthead_a(d)

    # 2 x 3 grid of story cards
    cards = [(36, 196, 466, 240), (522, 196, 466, 240),
             (36, 452, 466, 240), (522, 452, 466, 240),
             (36, 708, 466, 240), (522, 708, 466, 240)]
    for st, (cx, cy, cw, ch) in zip(STORIES, cards):
        d.rectangle([cx, cy, cx + cw, cy + ch], outline=INK, width=2,
                    fill=(255, 255, 255))
        d.rectangle([cx, cy, cx + cw, cy + 30], fill=RED)
        d.text((cx + 10, cy + 4), st["tag"], font=font(SANS_B, 14),
               fill=(255, 255, 255))
        # icon tile left (clipped, can never spill into the text)
        tile = icon_tile(st["icon"], 108, 108)
        img.paste(tile, (cx + 10, cy + 42))
        d.rectangle([cx + 10, cy + 42, cx + 118, cy + 150],
                    outline=LIGHTGREY)
        tx = cx + 130
        yy = headline(d, tx, cy + 42, st["head"], font(SERIF_B, 25), INK,
                      cw - 142, 29)
        para(d, tx, yy + 6, st["body"], font(SERIF, 17), INK, cw - 142, 22)
    # footer ticker (auto-fit so it never runs off the right edge)
    d.rectangle([0, 968, 1024, 1024], fill=INK)
    tf = fit_ticker(d, TICKER, 1000)
    d.text((512, 978), TICKER, font=tf,
           fill=(255, 255, 255), anchor="ma")
    return img


def main():
    which = sys.argv[1] if len(sys.argv) > 1 else "all"
    builders = {"a": variant_a, "b": variant_b, "c": variant_c}
    for key in (builders if which == "all" else [which]):
        img = builders[key]()
        out = f"variants/variant_{key}.png"
        img.save(out, optimize=True)
        print(key, out, img.size, img.mode)


if __name__ == "__main__":
    main()
