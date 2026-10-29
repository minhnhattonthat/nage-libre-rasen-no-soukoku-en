"""Graphics text (docs/re/graphics.md): redraw the Japanese drawn as TIM images in English.

    python -X utf8 tools/gfx.py [--only NAME] [--png work/qa/gfx/out]   preview: original | English per element

Each element names one TIM (file + offset of its first copy) and a list of ops on its pixels: `clear` a rect (each
row filled from the pixel left of the rect, which keeps a horizontal-gradient bar; or one colour) and `text` into a
rect. Colours are RGB, mapped to the nearest index of the TIM's CLUT 0 (8bpp) or written direct (16bpp). Fonts:
`game` = the game's own half-width ASCII (tools/font.py, the dialogue font), `tiny` = Tiny5 (fonts/, OFL) for labels
too small for it. build_gfx() writes the edited TIM over every byte-identical copy in the disc tree (shared textures
sit in up to 46 files).
"""
import argparse
import os
import struct
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import decomp  # noqa: E402
import extract  # noqa: E402
import font  # noqa: E402
import tim  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
TTF = {"tiny": (ROOT / "fonts/Tiny5.ttf", 8)}
SKIP = ("3MIN.BIN", ".STR", ".XA", "MAPDAT.BIN", "NAGE.EXE", "SYSDATA.BIN")

WHITE, BLACK, NAVY = (248, 248, 248), (0, 0, 0), (0, 0, 64)
BAR = dict(font="game", ink=WHITE, shadow=(16, 16, 96), bold=True)  # white on the blue header bars, dark drop shadow
KEEP = {"gold": lambda c: c[0] - c[2] > 40 and c[1] - c[2] > 20,  # the statue on the MAP86 poster
        "red": lambda c: c[0] > 150,  # its pink seal (clears only the blue signature ink)
        "dark": lambda c: sum(c) < 500}  # portraits beside the white vertical 参上 labels


# ---- masks -------------------------------------------------------------------------------------------------
_glyphs = None


def game_mask(line, track=0):
    """1-bit rows (13 high) of one line in the dialogue font; track = extra px after each glyph (bold text)."""
    global _glyphs
    if _glyphs is None:
        _glyphs = font.glyphs((extract.TREE / "NAGE.EXE").read_bytes())
    cols = []
    for ch in line:
        rows, adv = _glyphs[font.SPACE if ch == " " else font.ascii_index(ch)]
        w = len(rows[0])
        cols += [[r[c] if c < w else 0 for r in rows] for c in range(adv + track)]
    return [[col[y] for col in cols] for y in range(font.ROWS)]


def ttf_mask(line, name):
    path, size = TTF[name]
    f = ImageFont.truetype(str(path), size)
    w = int(f.getlength(line)) + 2
    im = Image.new("1", (w, size * 2), 0)
    d = ImageDraw.Draw(im)
    d.fontmode = "1"
    d.text((0, 0), line, font=f, fill=1)
    asc, desc = f.getmetrics()
    bb = im.getbbox() or (0, 0, 1, 1)
    im = im.crop((0, 0, bb[2], asc + desc))
    return [[im.getpixel((x, y)) for x in range(im.width)] for y in range(im.height)]


def mask(line, name, track=0):
    m = game_mask(line, track) if name == "game" else ttf_mask(line, name)
    while m and m[0] and not any(r[-1] for r in m):  # trailing gap after the last glyph
        m = [r[:-1] for r in m]
    return m


def line_height(name):
    return 13 if name == "game" else TTF[name][1]


# ---- an editable TIM ---------------------------------------------------------------------------------------
class Img:
    def __init__(self, data, off):
        self.t = tim.parse(data, off)
        assert self.t, f"no TIM at {off:#x}"
        self.bpp, self.h = self.t["bpp"], self.t["h"]
        self.w = self.t["w"] * 2 if self.bpp == 8 else self.t["w"]
        self.pix = bytearray(self.t["pix"])
        self.pos = self.t["end"] - len(self.pix)
        if self.bpp == 8:
            cw, _, cd = self.t["clut"]
            self.pal = [tim.rgb(struct.unpack_from("<H", cd, i * 2)[0])[:3] for i in range(cw)]

    def get(self, x, y):
        if self.bpp == 8:
            return self.pix[y * self.w + x]
        return struct.unpack_from("<H", self.pix, (y * self.w + x) * 2)[0]

    def rgb(self, x, y):
        v = self.get(x, y)
        return self.pal[v] if self.bpp == 8 else tim.rgb(v)[:3]

    def put(self, x, y, v):
        if not (0 <= x < self.w and 0 <= y < self.h):
            return
        if self.bpp == 8:
            self.pix[y * self.w + x] = v
        else:
            struct.pack_into("<H", self.pix, (y * self.w + x) * 2, v)

    def colour(self, rgb):
        if self.bpp == 16:
            r, g, b = (c >> 3 for c in rgb)
            return r | g << 5 | b << 10 | 0x8000 * 0  # STP bit off, as the art around it
        # never index 0 (transparent black on PS1)
        return min(range(1, len(self.pal)), key=lambda i: sum((a - b) ** 2 for a, b in zip(self.pal[i], rgb)))

    def clear(self, x, y, w, h, fill=None, keep=None):
        """fill: None = copy each row's pixel left of the rect; "mode" = each row's commonest pixel inside the rect
        (a gradient plate under text); int = raw index (0 = transparent); else RGB. keep: a KEEP name; pixels of
        that colour class (art overlapping the text rect) stay."""
        for yy in range(y, y + h):
            if fill == "lerp":  # each row blends from the pixel left of the rect to the one right of it
                a, b = self.rgb(x - 1, yy), self.rgb(x + w, yy)
                for i, xx in enumerate(range(x, x + w)):
                    t = (i + 1) / (w + 1)
                    self.put(xx, yy, self.colour(tuple(round(p + (q - p) * t) for p, q in zip(a, b))))
                continue
            if fill == "mode":
                row = [self.get(xx, yy) for xx in range(x, x + w)]
                v = max(set(row), key=row.count)
            else:
                v = self.get(x - 1, yy) if fill is None else fill if isinstance(fill, int) else self.colour(fill)
            for xx in range(x, x + w):
                if not (keep and KEEP[keep](self.rgb(xx, yy))):
                    self.put(xx, yy, v)

    def text(self, x, y, w, h, s, font="game", ink=WHITE, shadow=None, outline=None, align="c", gap=0, bold=False,
             scale=1, rotate=False):
        """rotate: one line turned 90 degrees clockwise (reads top to bottom, for vertical Japanese labels), centred
        in the rect."""
        lines = s.split("\n")
        masks = [[[b for b in row for _ in range(scale)] for row in mask(ln, font, 1 if bold else 0)
                  for _ in range(scale)] for ln in lines]
        if rotate:
            m = masks[0]
            while m and not any(m[-1]):
                m = m[:-1]
            while m and not any(m[0]):
                m = m[1:]
            masks = [[[m[len(m) - 1 - c][r] for c in range(len(m))] for r in range(len(m[0]))]]
            assert len(masks[0]) <= h, f"{s!r} rotated is {len(masks[0])} px long, room {h}"
            lines, lh, gap = [s], len(masks[0]), 0
        else:
            lh = line_height(font) * scale + gap
        top = y + (h - (lh * len(lines) - gap)) // 2
        ink_v = self.colour(ink)
        for i, m in enumerate(masks):
            mw = len(m[0]) if m else 0
            assert mw <= w, f"{s!r}: line {lines[i]!r} is {mw} px, room {w}"
            lx = x + {"c": (w - mw) // 2, "l": 0, "r": w - mw}[align]
            ly = top + i * lh
            pts = [(lx + cx + b, ly + cy) for cy, row in enumerate(m) for cx, on in enumerate(row) if on
                   for b in ((0, 1) if bold else (0,))]
            if outline:
                v = self.colour(outline)
                for px, py in pts:
                    for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (1, 1), (-1, 1), (1, -1)):
                        self.put(px + dx, py + dy, v)
            if shadow:
                v = self.colour(shadow)
                for px, py in pts:
                    self.put(px + 1, py + 1, v)
            for px, py in pts:
                self.put(px, py, ink_v)

    def bytes(self, data):
        return data[:self.pos] + bytes(self.pix) + data[self.pos + len(self.pix):]

    def image(self):
        t = dict(self.t, pix=bytes(self.pix))
        return tim.to_image(t)


# ---- packed entries: re-encoded as the game's RLE behind tools/asm/rle.asm's marker ---------------------------
# Memory-area table at 0x80089794 ({addr, size} words): the only area at 0x80170000 big enough for OP_TMP2 (494,029
# bytes), OPTION2 and OPTION6 (~300 KB) is 0x86800 bytes (the others there are 0x41000, 0x3C000, 0x20000).
AREA = 0x86800
RLE_MARK = b"RR"  # second byte 'R': rle.asm sends the block to the RLE decoder (packed blocks have 00 there)


def rle(data):
    """Encode for NAGE.EXE 0x80031388: n < 0x80 = n literal bytes; n >= 0x80 = repeat the last byte (n & 0x7F) + 1
    times (the last literal; 0xFF before any); 0 ends."""
    out, prev, i, lit = bytearray(RLE_MARK), 0xFF, 0, bytearray()

    def flush():
        nonlocal lit
        for k in range(0, len(lit), 127):
            out.append(len(lit[k:k + 127]))
            out.extend(lit[k:k + 127])
        lit = bytearray()

    while i < len(data):
        b = data[i]
        n = 1
        while i + n < len(data) and data[i + n] == b and n < 128:
            n += 1
        if b == (lit[-1] if lit else prev) and n >= 2:  # repeat of the byte before
            flush()
            out.append(0x80 | (n - 1))
            prev = b
            i += n
        elif n >= 3:  # one literal, then repeats
            lit.append(b)
            flush()
            prev = b
            out.append(0x80 | (n - 2))
            i += n
        else:
            lit.append(b)
            i += 1
    flush()
    out.append(0)
    return bytes(out)


def entries(d):
    n = struct.unpack_from("<I", d, 0)[0] // 4
    offs = list(struct.unpack_from(f"<{n}I", d, 0)) + [len(d)]
    return [d[offs[i]:offs[i + 1]] for i in range(n)]


def join(blocks):
    """Offset-table container (docs/re/files.md) from its entries, each start kept 4-aligned."""
    head, body, offs = 4 * len(blocks), bytearray(), []
    for i, b in enumerate(blocks):
        offs.append(head + len(body))
        body += b + (bytes(-len(b) % 4) if i < len(blocks) - 1 else b"")  # the last keeps its stray tail byte
    return struct.pack(f"<{len(offs)}I", *offs) + bytes(body)


# ---- elements ----------------------------------------------------------------------------------------------
# (name, file, TIM offset, [ops]); ops: ("clear", x, y, w, h[, rgb]) / ("text", x, y, w, h, str, {style})
ELEMENTS = []


def element(name, rel, off, *ops):
    ELEMENTS.append((name, rel, off, list(ops)))


# 7 birthday entry headers
element("birthday", "OPTION1.BIN", 0x10298,
        ("clear", 24, 84, 208, 16), ("text", 24, 85, 208, 13, "Choose your birthday!", BAR),
        ("clear", 24, 108, 208, 16), ("text", 24, 109, 208, 13, "Is this OK?", BAR))
# 1 title screen subtitle 螺旋の相剋 on the red ribbon under the Latin logo (ribbon x 136..220, y 74..85)
element("subtitle", "OP_TMP2.BIN", 0x7034C,
        ("clear", 142, 69, 74, 5, "mode"), ("clear", 142, 74, 74, 12, "lerp"),
        ("text", 136, 74, 84, 13, "Spiral Conflict", dict(ink=(224, 232, 232), shadow=(72, 0, 0))))
# 15 ending picture (16bpp): おわり in yellow with a blue shadow over the sky
element("theend", "OPTION6.BIN", 0x329C8,
        ("clear", 150, 15, 95, 35, "lerp"),
        ("text", 150, 18, 95, 26, "The End", dict(ink=(248, 240, 72), shadow=(48, 120, 216), scale=2, bold=True)))
# 18, 19 boss intro labels (vertical, white; shared battle/map sheets in 34 BTLTIM and 46 MAPTIM files):
# 参上 "here!" beside the portrait, and the MAP01R boss's name レイプマン
element("sanjo_btl", "MAP01_06/MAP01R/BTLTIM.BIN", 0x18A78,
        ("clear", 177, 210, 15, 26, 0, "dark"),
        ("text", 178, 210, 12, 26, "Here!", dict(font="tiny", rotate=True)))
element("sanjo_map", "MAP01_06/MAP01R/MAPTIM.BIN", 0x33AE8,
        ("clear", 0, 110, 23, 46, 0, "dark"),
        ("text", 0, 110, 9, 40, "Rapeman", dict(font="tiny", rotate=True)),
        ("text", 10, 131, 12, 24, "Here!", dict(font="tiny", rotate=True)))
# 2-5 title screen, packed entries of OP_TMP2.BIN (written back as RLE, tools/asm/rle.asm)
element("pressstart", "OP_TMP2.BIN", ("entry", 11),
        ("clear", 40, 120, 176, 15, 0),
        ("text", 40, 121, 176, 13, "Press START to begin!", dict(outline=(32, 40, 176), bold=True)))
element("pleasewait", "OP_TMP2.BIN", ("entry", 12),
        ("clear", 56, 121, 148, 16, 0),
        ("text", 56, 122, 148, 13, "Wait just a moment!", dict(outline=(16, 24, 128), bold=True)))
element("cardcheck", "OP_TMP2.BIN", ("entry", 13),
        ("clear", 2, 84, 124, 10, (40, 32, 248)),
        ("text", 1, 82, 126, 13, "Checking memory card", dict(shadow=(88, 88, 248))))
element("nocard", "OP_TMP2.BIN", ("entry", 14),
        ("clear", 74, 137, 124, 69, (40, 32, 248)),
        ("text", 74, 137, 124, 69, "No memory card is\ninserted. Saving needs\na memory card with at\nleast 2 free blocks.",
         dict(ink=(240, 232, 248))))
# 16 credits cast plates (OPTION6 #2-#11, 80x96 portrait + name rows 81..92 on transparent); Tiny5 since the
# longest full name in the game font (Makoto Matsunaga, 97 px) is wider than the 80-px plate
CAST = ("Ann Akagi", "Itsuki Morino", "Makoto Matsunaga", "Mio Tsukushi", "Shinobu Kazama", "Kaoru Kanzaki",
        "Jin Kiryu", "Dai Wajima", "Tsukasa Aida", "Ryo Kurosawa")
for _i, _s in enumerate(CAST):
    element(f"cast{_i}", "OPTION6.BIN", ("entry", 2 + _i),
            ("clear", 0, 80, 80, 16, 0), ("text", 0, 82, 80, 9, _s, dict(font="tiny", shadow=(64, 64, 64))))
# 8 birthstone plates: 12 gold plates of 16 rows at x 128..223, white text with a dark outline
STONES = ("Garnet", "Amethyst", "Aquamarine", "Diamond", "Emerald", "Moonstone", "Ruby", "Agate", "Sapphire", "Opal",
          "Topaz", "Lapis Lazuli")
element("birthstones", "OPTION1.BIN", 0x204B8,
        *[op for i, s in enumerate(STONES) for op in (
            ("clear", 129, 16 * i + 1, 94, 14, "mode"),
            ("text", 128, 16 * i + 2, 96, 13, s, dict(ink=WHITE, outline=(64, 48, 0))))])
# 6 loading chalkboard: "Now loading..." in chalk; the date's 月 becomes "/", 日 goes (smudged numbers are art)
CHALK = (216, 232, 216)
element("loading", "VARIE.BIN", 0x10228,
        ("clear", 44, 70, 158, 18), ("text", 44, 72, 158, 13, "Now loading...", dict(ink=CHALK, bold=True)),
        ("clear", 203, 60, 10, 11), ("text", 203, 59, 10, 13, "/", dict(ink=CHALK)),
        ("clear", 203, 86, 10, 12))
# 11 save-slot chapter titles: 16-row strips, white with a blue outline on transparent
TITLES = (
    "Nanju Street's Last Stand!!", "Lonely Plains! Ann Won't Cry!", "Empty Park! Owner, Come Out!",
    "A Desert House! Western?!", "Miracle Reunion! Search On!!", "Gasp! Who Wears That Here?!",
    "Love the Sea! But~ Sharks~", "Ancient Ruins!! Might as Well...", "Into the Cave!! Bored? Leave!!!",
    "Guilty! It's Trespassing! 1", "Guilty! It's Trespassing! 2", "That Bossy Guy? I Hate Him!",
    "Flung in the Desert, Alive!", "Lost in the Fog! Still Alive~!", "No Cave Behind the Falls!!",
    "Mystic Ruins! Nobody Cares!!", "Hey... Hot? Oh, Lava!", "Students! Tough Love Time!",
    "Mecha and Cute Girls! What Else?!", "Help!! I'm Scared of Heights!", "Back Alive!! Life Is Precious!",
    "Showdown!! Sneak In! Doomed?!", "Final Battle!! Keep the Vouchers!!", "The REAL Final Battle!!",
    "Ugh~ So Cold! Oh, Snow.", "Hot Springs! Cures Love? Pass.", "Open Up or We Smash It!!",
    "Why Tell US Something Big?", "Mountains Rock. Nice View.", "Lava Below! Fall and Die!!",
    "Falling Bridge!! Who Built This?!")
for _i, (_off, _n) in enumerate(((0x308EC, 15), (0x38B0C, 15), (0x4052C, 1))):
    _ts = TITLES[_i * 15:_i * 15 + _n]
    element(f"titles{_i}", "OPTION3.BIN", _off,
            *[op for j, s in enumerate(_ts) for op in (
                ("clear", 0, 16 * j, 128, 16, 0),
                ("text", 1, 16 * j + 2, 126, 13, s, dict(font="tiny", ink=WHITE, outline=(0, 0, 248))))])
# 20 news ticker (MAP01R intro): 6 strips of 16 rows, yellow on an 11-row grey band; caps on rows 0-10
NEWS = ("* Strange disturbances seen in Nanju Town.",
        "* Disturbances are links to another world.",
        "* New creatures from it do more damage.",
        "* Anger at 309-yen tax for new town hall.",
        "* Nage Libre feedback to VARIE Corp.",
        "* Lost candy behind hotel. Help! -Kimutake")
element("news", "MAP01_06/MAP01R/MAPTIM.BIN", 0x10244,
        *[op for i, s in enumerate(NEWS) for op in (
            ("clear", 4, 16 * i, 252, 11, "mode"),
            ("text", 6, 16 * i - 1, 248, 13, s, dict(ink=(224, 200, 80))))])
# 28 recruitment poster (MAP86 intro, full screen): red heading, black body left of the statue, blue signature
INK = (16, 16, 16)
POSTER = (("The Nage Statue has been\nstolen from Nanju Shrine!\nMonsters freed from their\nseal plague our shops.", 62),
          ("Let's get the Statue back\nfor Nanju Town's peace!", 115),
          ("Volunteers, meet in the\ncouncil room after school.", 144),
          ("Shops will reward you with\ngift certificates!!", 173))
element("poster", "MAP01_06/MAP86/MAPFIRST.BIN", 0xF8,
        ("clear", 140, 50, 36, 14, (240, 240, 240), "gold"),  # the "これ" note pointing at the statue
        ("clear", 30, 21, 198, 38, (240, 240, 240)),
        ("text", 30, 22, 198, 13, "Nage Statue Search Team", dict(ink=(240, 8, 0), bold=True)),
        ("text", 30, 34, 198, 26, "MEMBERS WANTED!", dict(ink=(240, 8, 0), scale=2)),
        ("clear", 24, 60, 150, 140, (240, 240, 240), "gold"),
        ("clear", 174, 180, 14, 18, (240, 240, 240), "gold"),
        *[("text", 28, y, 142, 12 * s.count("\n") + 12, s, dict(ink=INK, align="l", gap=-1)) for s, y in POSTER],
        ("clear", 100, 198, 112, 14, (240, 240, 240)), ("clear", 212, 198, 10, 14, (240, 240, 240), "red"),
        ("text", 40, 199, 164, 13, "Nanju High Student Council", dict(ink=(16, 0, 208), align="r")))
# 26 MAP81 classroom blackboard: "This month's goal / Aim for town peace!" (x 88 = board edge, 87 = frame)
element("blackboard", "MAP01_06/MAP81/MAPFIRST.BIN", 0x10298,
        ("clear", 94, 54, 38, 10), ("text", 92, 53, 50, 9, "Monthly goal:", dict(font="tiny", ink=CHALK)),
        ("clear", 89, 64, 79, 12), ("text", 88, 63, 76, 13, "Town peace!", dict(ink=CHALK)))
# 27 MAP82 shrine notice board header 南寿神社のゆらい (the body is drawn as grey lines, not text)
element("shrineboard", "MAP01_06/MAP82/MAPFIRST.BIN", 0xC8,
        ("clear", 107, 14, 43, 8, "mode"), ("text", 107, 13, 43, 9, "Shrine Lore", dict(font="tiny", ink=(40, 40, 40))))
# 9, 10 load / save headers
element("load", "OPTION3.BIN", 0x10298,
        ("clear", 24, 24, 208, 16), ("text", 24, 25, 208, 13, "Which file do you want to play?", BAR))
element("save", "OPTION3.BIN", 0x206CC,
        ("clear", 24, 24, 208, 16), ("text", 24, 25, 208, 13, "Where do you want to save?", BAR))
# 12 between-stage menu
element("menu", "OPTION4.BIN", 0x10298,
        ("clear", 24, 24, 208, 16), ("text", 24, 25, 208, 13, "What do you want to do now?", BAR),
        *[op for i, s in enumerate(("Club Select", "Dress-Up", "Save", "Start"))
          for op in (("clear", 40, 96 + 16 * i, 176, 16), ("text", 40, 97 + 16 * i, 176, 13, s, BAR))])
# 14 world-map area cards: 25 TIMs 0x1620 apart, box at the top (y 0) or under the party sprites (y 24)
AREAS = [("Jungle", 24), ("Southern Sea", 24), ("Island of Ruins", 24), ("Underground Cave", 0),
         ("Fortress Interior", 0), ("Fortress Headquarters", 0), ("Forked Cape", 0),
         ("Battleship Dunes", 0),  # wider was clipped at the screen edge (wm13)
         ("Fog-Shrouded Forest", 0), ("Cascade Falls", 0),
         ("Ancient Ruins", 0), ("Lava Cave", 24), ("Autumn Leaf Valley", 24), ("In the Flying Battleship", 24),
         ("Flying Battleship Dock", 0), ("Oka High Control Tower", 0), ("Altar of Nage", 0),
         ("Control Tower Roof", 24), ("Frozen Mountain", 0), ("Hot Spring Village", 24), ("Castle Walls", 0),
         ("Forest of Giant Trees", 0), ("Mt. Issun", 0), ("Volcano Cave", 24), ("Connecting Bridge", 0)]
for _n, (_s, _y) in enumerate(AREAS):
    element(f"area{_n:02d}", "OPTION7.BIN", 0x3D6A0 + _n * 0x1620, ("card", _y, _s))


def card(y, text):
    """World-map area card (64x40 TIM, OPTION7): a navy 16-row box at y 0 or 24 centred on x 64, sized to the text."""
    w = min(128, len(mask(text, "game")[0]) + 8)
    return [("clear", 0, y, 128, 16, 0), ("clear", 64 - w // 2, y, w, 16, (0, 0, 128)),
            ("text", 1, y + 2, 126, 13, text, dict(ink=(224, 224, 224), shadow=(64, 64, 64)))]


def apply(img, ops):
    for op in ops:
        if op[0] == "clear":
            img.clear(*op[1:])
        elif op[0] == "card":
            apply(img, card(*op[1:]))
        else:
            x, y, w, h, s = op[1:6]
            img.text(x, y, w, h, s, **(op[6] if len(op) > 6 else {}))


def tree_files(tree):
    for p in sorted(Path(tree).rglob("*")):
        rel = p.relative_to(tree).as_posix()
        if p.is_file() and not any(k in rel for k in SKIP):
            yield rel, p


def build_gfx(tree, only=None):
    """{disc path: bytes} for every file holding a copy of an edited TIM; [(name, original, English)] previews."""
    tree = Path(tree)
    data = {rel: p.read_bytes() for rel, p in tree_files(tree)}
    out, previews = {}, []
    for name, rel, off, ops in ELEMENTS:
        if only and name != only:
            continue
        if isinstance(off, tuple):  # ("entry", n): packed TIM in an offset-table file, written back as RLE
            blocks = entries(out.get(rel, data[rel]))
            t = decomp.decompress(blocks[off[1]])
            img = Img(t, 0)
            before = img.image()
            apply(img, ops)
            blocks[off[1]] = rle(img.bytes(t))
            out[rel] = join(blocks)
            assert len(out[rel]) <= AREA, f"{rel}: {len(out[rel])} bytes, its RAM area holds {AREA}"
            previews.append((name, before, img.image()))
            continue
        src = data[rel]
        img = Img(src, off)
        before = img.image()
        old = src[off:img.t["end"]]
        apply(img, ops)
        new = img.bytes(src)[off:img.t["end"]]
        hits = 0
        for r, d in data.items():
            if old in d:
                cur = out.get(r, d)
                hits += cur.count(old)
                out[r] = cur.replace(old, new)
        assert hits, f"{name}: TIM not found"
        previews.append((name, before, img.image()))
    return out, previews


def preview(previews, outdir):
    os.makedirs(outdir, exist_ok=True)
    for name, a, b in previews:
        im = Image.new("RGBA", (a.width * 2 + 4, a.height), (255, 0, 255, 255))
        im.paste(a, (0, 0))
        im.paste(b, (a.width + 4, 0))
        im.save(os.path.join(outdir, f"{name}.png"))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--only")
    ap.add_argument("--png", default=str(ROOT / "work/qa/gfx/out"))
    a = ap.parse_args()
    files, pv = build_gfx(extract.TREE, a.only)
    preview(pv, a.png)
    print(f"{len(pv)} elements, {len(files)} files")
