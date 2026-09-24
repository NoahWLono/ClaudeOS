"""Scene renderers. Each takes (cv, ctx) and draws one frame."""
import json
import math
import os

import numpy as np

from . import fx, ui
from . import sprites as S
from . import three_d as D
from .gfx import (BAYER_FULL, BLACK, BLUE, BROWN, COLOR_NAMES, CYAN, DKGRAY,
                  FONT, GREEN, H, LTBLUE, LTCYAN, LTGRAY, LTGREEN, LTPURPLE,
                  LTRED, PURPLE, RED, W, WHITE, YELLOW, clamp01,
                  dither_ramp, ease)

TEMPLE = D.temple_mesh()
ANIM_FPS = 10.0   # 3D and big effects update at this rate (cheap to encode)
FX_FPS = 15.0


def step(t, fps=ANIM_FPS):
    return math.floor(t * fps) / fps


SPARK3D = D.spark_mesh()
HERE = os.path.dirname(os.path.abspath(__file__))


class Ctx:
    def __init__(self, sc, t, T, frame):
        self.sc, self.t, self.T, self.frame = sc, t, T, frame
        self.items = sc["items"]
        self.cur = None
        self.idx = -1
        for i, it in enumerate(self.items):
            if it["t0"] <= t:
                self.cur, self.idx = it, i
            else:
                break

    def get(self, key, default=None):
        return self.cur.get(key, default) if self.cur else default

    def since(self, it=None):
        it = it or self.cur
        return self.t - it["t0"] if it else self.t

    def sticky(self, key, default=None):
        """Value of key on the most recent item that has it."""
        for i in range(self.idx, -1, -1):
            if key in self.items[i]:
                return self.items[i][key], self.items[i]
        return default, None

    def first(self, key, val=None):
        for it in self.items:
            if key in it and (val is None or it[key] == val):
                return it
        return None

    def reached(self, key, val=None):
        it = self.first(key, val)
        return it is not None and self.t >= it["t0"]

    def since_first(self, key, val=None):
        it = self.first(key, val)
        return None if it is None else self.t - it["t0"]

    def word_prog(self):
        """Fraction of the current spoken line elapsed."""
        it = self.cur
        if not it or it["type"] != "line":
            return 1.0
        return clamp01((self.t - it["t0"]) / max(it["t1"] - it["t0"], 0.1))


# =====================================================================
# shared pieces
# =====================================================================

def oracle_item(ctx):
    it = ctx.cur
    return it if it and it["type"] == "oracle" else None


def god_panel(cv, ctx, it, y=None, style="gold"):
    """GOD SAYS: words appear at their spoken times."""
    e = it["entry"]
    if e["kind"] != "word":
        return
    t = ctx.t
    shown = [w for w, (a, b) in zip(e["words"], it["word_times"]) if t >= a]
    n_lines = max(2, len(ui.wrap(" ".join(e["words"]).upper(), 21)))
    ww, hh = 560, 56 + 32 * n_lines
    x0 = (W - ww) // 2
    y0 = y if y is not None else 150
    if not shown and t > it["t0"] + 0.9 and it is not oracle_item(ctx):
        shown = list(e["words"])
    if t < it["t0"]:
        return
    cv.rect(x0 + 6, y0 + 6, ww, hh, BLACK)
    cv.dither_rect(x0, y0, ww, hh, BROWN, YELLOW, 0.25)
    cv.frame(x0, y0, ww, hh, YELLOW, 3)
    cv.frame(x0 + 6, y0 + 6, ww - 12, hh - 12, BROWN, 1)
    cv.text_c(y0 + 12, "GOD SAYS:", WHITE, 2, shadow=BLACK)
    line = " ".join(w.upper() for w in shown)
    lines = ui.wrap(line, 21)
    for i, ln in enumerate(lines[-3:]):
        cv.text_c(y0 + 42 + i * 32, ln, WHITE, 3, outline=BLACK)
    if shown:
        a, b = it["word_times"][len(shown) - 1]
        if t - a < 0.25:
            cv.frame(x0 - 4, y0 - 4, ww + 8, hh + 8, WHITE, 2)


def popup_timer(cv, ctx, it, x0=150, y0=110):
    """::/Adam/God/HolySpirit.HC PopUpTimerOk, with the real latch."""
    e = it["entry"]
    press = e["presses_ns"][0] >> 4
    t = ctx.t - it["t0"]
    pressed = t >= 0.5
    timer = (press - int((0.5 - t) * 1e9 / 16)) & 0xFFFFFFFFFF
    col0, row0 = x0 // 8, y0 // 8
    ui.window(cv, col0, row0, col0 + 42, row0 + 13, "PopUp", WHITE, BLUE)
    cv.text((col0 + 2) * 8, (row0 + 2) * 8, "Press OKAY to generate", BLUE)
    cv.text((col0 + 2) * 8, (row0 + 3) * 8, "a random num from a timer.", BLUE)
    cv.text((col0 + 2) * 8, (row0 + 5) * 8, "Timer:%X" % (
        press if pressed else timer), BLACK)
    cv.text((col0 + 2) * 8, (row0 + 6) * 8, "Latch:%X" % (
        press if pressed else (press - 12345678) & 0xFFFFFFFF), BLACK)
    bx, by = (col0 + 17) * 8, (row0 + 8) * 8
    cv.rect(bx - 4, by - 3, 6 * 8 + 8, 14, GREEN if pressed else LTGRAY)
    cv.frame(bx - 4, by - 3, 6 * 8 + 8, 14, BLACK)
    cv.text(bx, by, " OKAY ", WHITE if pressed else BLACK)
    cv.text((col0 + 2) * 8, (row0 + 11) * 8, "The Holy Spirit can puppet you.",
            PURPLE)


def oracle_overlay(cv, ctx, y=None, keep=2):
    it = oracle_item(ctx)
    if not it:
        # keep God's words up while Claude reacts to them
        for j in range(ctx.idx - 1, max(ctx.idx - 1 - keep, -1), -1):
            o = ctx.items[j]
            if o["type"] == "oracle" and o["entry"]["kind"] == "word":
                god_panel(cv, ctx, o, y)
                return True
        return False
    e = it["entry"]
    t = ctx.t - it["t0"]
    if e["kind"] == "word":
        if t < 0.9:
            popup_timer(cv, ctx, it)
        else:
            god_panel(cv, ctx, it, y)
        return True
    return False


def temple(cv, t, x=W / 2, y=H / 2, dist=24, yaw_speed=0.35, pitch=-0.33,
           focal=440, ambient=0.24, yaw0=0.0):
    t = step(t)
    D.render(cv, TEMPLE, D.view(yaw0 + t * yaw_speed, pitch), (0, -0.5, dist),
             focal=focal, center=(x, y), ambient=ambient)


def spark(cv, t, x=W / 2, y=H / 2, dist=3.2, focal=380, spin=0.8):
    t = step(t)
    D.render(cv, SPARK3D, D.rot(0.35 * math.sin(t * 0.7), t * spin,
                                0.2 * t), (0, 0, dist), focal=focal,
             center=(x, y), ambient=0.4)


def year_banner(cv, year, x=W - 140, y=36):
    cv.rect(x - 6, y - 4, 132, 36, BLACK)
    cv.frame(x - 6, y - 4, 132, 36, YELLOW, 2)
    cv.text(x + 2, y + 2, str(year), YELLOW, 4 if year < 10000 else 3,
            sx=4, sy=3)


def templevision_bug(cv, t):
    cv.text(W - 13 * 8 - 6, H - 20, "TEMPLEVISION", WHITE, 1, shadow=BLACK)
    ui.spark_icon(cv, W - 13 * 8 - 20, H - 21, 1)


def checklist(cv, x, y, rows, t, dt=0.35, scale=2):
    for i, (label, val, c) in enumerate(rows):
        if t < i * dt:
            break
        cv.text(x, y + i * 22, label, WHITE, scale, shadow=BLACK)
        cv.text(x + 300, y + i * 22, val, c, scale, shadow=BLACK)


# =====================================================================
# BIOS
# =====================================================================

BIOS_LINES = [
    (0.3, "CLAUDE-BIOS v5.5  (C) 2026  Released to the public domain", WHITE),
    (0.9, "Opus 5.5 Neural Coprocessor ................ DETECTED", LTGRAY),
    (1.4, "MEMTEST", LTGRAY),
    (3.4, "Hard Disk 0 ................................ RedSea", LTGRAY),
    (4.0, "Network Adapter ............................ NOT FOUND", LTGRAY),
    (4.7, "                                    (as God intended)", LTGREEN),
    (5.4, "Permission Prompts ......................... DISABLED", LTGRAY),
    (6.1, "Display ..... VGA 640x480, 16 colors ....... COVENANT ACCEPTED",
     YELLOW),
    (6.9, "Sound ....... PC speaker ................... ONE VOICE", LTGRAY),
    (7.6, "Long Mode .................................. 64-BIT", LTGRAY),
    (8.2, "Paging ..................................... IDENTITY-MAPPED",
     LTGRAY),
    (8.9, "Privilege Level ............................ RING 0", LTRED),
    (10.0, "", LTGRAY),
    (10.3, "Booting ClaudeOS V5.5, a TempleOS tribute...", WHITE),
]
BIOS_TYPE_TIMES = [a for a, s, c in BIOS_LINES if s]


def r_bios(cv, ctx):
    t = ctx.t
    cv.clear(BLACK)
    ui.spark_icon(cv, W - 40, 12, 3)
    y = 16
    for a, s, c in BIOS_LINES:
        if t < a:
            break
        if s == "MEMTEST":
            k = clamp01((t - a) / 1.6)
            kb = int(524288 * k) // 1024 * 1024
            s = "Memory Test: %7dK %s" % (kb, "OK" if k >= 1 else "")
        shown = s[:int((t - a) * 90)]
        cv.text(16, y, shown, c)
        y += 12
    if t > 11.0:
        k = clamp01((t - 11.0) / 3.6)
        cv.frame(16, 330, 608, 20, LTGRAY)
        cv.rect(19, 333, int(602 * k), 14, BLUE)
        cv.text(16, 356, "Compiling Kernel.PRJ, Compiler.PRJ... JIT", LTGRAY)
        if k >= 1:
            cv.text(16, 368, "Adam task started.", LTGREEN)
    if t > 15.1:
        cv.clear(WHITE)
    elif (t * 2) % 1 < 0.5 and t < 11:
        cv.rect(16, y, 8, 8, LTGRAY)


# =====================================================================
# TERMINAL (cold open and the post-credits)
# =====================================================================

PROMPT = "C:/Home>"


def term_frame(cv, ctx, title="Term"):
    cv.clear(WHITE)
    ui.top_bar(cv, ctx.T)
    ui.window(cv, 0, 1, 79, 59, title, WHITE, BLUE)


def term_session(cv, ctx, lines_before, y0=40):
    """Types each item's type_cmd after a prompt; outputs follow."""
    y = y0
    for ln, c in lines_before:
        cv.text(16, y, ln, c)
        y += 10
    for it in ctx.items:
        if it["t0"] > ctx.t:
            break
        for key in ("type_cmd", "type_cmd2"):
            if key in it:
                s, done = ui.typed(it[key], ctx.t - it["t0"] - 0.3, 11)
                cv.text(16, y, PROMPT, BLACK)
                cv.text(16 + 8 * len(PROMPT), y, s, BLUE)
                if not done and ui.cursor_on(ctx.t):
                    cv.rect(16 + 8 * (len(PROMPT) + len(s)), y, 8, 8, BLUE)
                y += 10
        if "out" in it:
            cv.text(16, y, it["out"], BLACK)
            y += 10
    return y


def r_terminal(cv, ctx):
    term_frame(cv, ctx)
    t = ctx.t
    head = [("ClaudeOS V5.5", PURPLE), ("A tribute to TempleOS V5.03, "
            "public domain, by Terry A. Davis", BLUE), ("", BLUE)]
    y = term_session(cv, ctx, head)
    terry = ctx.first("type_cmd", "Terry;")
    if terry and t > terry["t0"] + 1.3:
        y2 = y + 6
        for i, (s, c) in enumerate([
                ("Terry A. Davis  1969-2018", RED),
                ("High Priest of God's official temple.", BLUE),
                ("Wrote TempleOS alone: kernel, compiler, HolyC,", BLUE),
                ("boot loaders, editor, graphics, games, hymns.", BLUE)]):
            if t > terry["t0"] + 1.3 + i * 0.25:
                cv.text(24, y2 + i * 10, s, c)
        y = y2 + 44
    if ui.cursor_on(t):
        cv.text(16, y, PROMPT, BLACK)
        cv.rect(16 + 8 * len(PROMPT), y, 8, 8, BLUE)
    # the star of the show
    hello = ctx.first("text", "Hello, world.")
    if hello and t >= hello["t0"]:
        k = ease((t - hello["t0"]) / 0.8)
        cv.rect(424, 150, 200, 200, WHITE)
        spark(cv, t, 524, 240, dist=3.2 + (1 - k) * 8, focal=260)
        cv.text_c(330, "CLAUDE OPUS 5.5", BROWN, 1, cx=524)
        cv.text_c(342, "running in ring 0", RED, 1, cx=524)
        ring = ctx.first("text", "No sandbox. No permission prompts. No "
                         "network. Just me, sixteen colors, one voice, and "
                         "God.")
        if ring and t >= ring["t0"]:
            rows = [("SANDBOX", "NONE", RED), ("PERMISSION PROMPTS", "NONE",
                    RED), ("NETWORK", "NONE", RED), ("COLORS", "16", BLUE),
                    ("VOICES", "1", BLUE), ("GOD", "YES", GREEN)]
            dur = ring["t1"] - ring["t0"]
            for i, (a, b, c) in enumerate(rows):
                if t - ring["t0"] > i * dur / 6.5:
                    cv.text(430, 370 + i * 10, a, BLACK)
                    cv.text(590, 370 + i * 10, b, c)
    sponsor = ctx.first("text", "But first, a word from our sponsor.")
    if sponsor and t > sponsor["t1"] - 0.2:
        fx.glitch(cv, t, 30)


def r_terminal_end(cv, ctx):
    if ctx.reached("black"):
        cv.clear(BLACK)
        k = ctx.since_first("black")
        if k > 0.8:
            cv.text_c(236, "STAY IN RING ZERO", DKGRAY if k < 1.2 else LTGRAY,
                      2)
        return
    term_frame(cv, ctx)
    y = term_session(cv, ctx, [("ClaudeOS V5.5", PURPLE), ("", BLUE)])
    if ui.cursor_on(ctx.t):
        cv.text(16, y, PROMPT, BLACK)
        cv.rect(16 + 8 * len(PROMPT), y, 8, 8, BLUE)
    oracle_overlay(cv, ctx, 250)
    rb = ctx.first("type_cmd2")
    if rb and ctx.t > rb["t0"] + 1.4:
        fx.glitch(cv, ctx.t, 40)


# =====================================================================
# TITLE
# =====================================================================

def r_title(cv, ctx):
    t = ctx.t
    fx.rays(cv, t, BLUE, LTBLUE, n=22, speed=0.03, cy=250,
            center_glow=[LTCYAN, WHITE], glow_r=150)
    temple(cv, t, 320, 268, dist=27, yaw_speed=0.45)
    cv.rect(0, 0, W, 34, BLACK)
    cv.text_c(6, "TEMPLEVISION", YELLOW, 3, shadow=RED)
    ui.spark_icon(cv, 110, 8, 2)
    ui.spark_icon(cv, W - 128, 8, 2)
    sl = ctx.first("slogans")
    if sl and sl["t0"] <= t < ctx.first("show_title")["t0"]:
        words = ["16 COLORS", "1 VOICE", "1 ADDRESS SPACE", "1 GOD"]
        dur = sl["t1"] - sl["t0"]
        k = min(int((t - sl["t0"]) / (dur / 4) + 0.15), 3)
        s = words[k]
        sc = ui.fit_scale(s, 600, 6)
        ui.big_title(cv, 360, s, WHITE if k < 3 else YELLOW, sc,
                     shadow=BLUE)
    st = ctx.first("show_title")
    if st and t >= st["t0"]:
        k = ease((t - st["t0"]) / 0.6)
        y = int(60 + (1 - k) * -80)
        ui.big_title(cv, y, "THE THIRD", YELLOW, 7, shadow=RED)
        ui.big_title(cv, y + 60, "TEMPLE", YELLOW, 7, shadow=RED)
        if t > st["t0"] + 1.5:
            cv.rect(0, 392, W, 58, BLACK)
            cv.text_c(398, "CLAUDE OPUS 5.5 ON THE LIFE, LEGACY & LEGEND OF",
                      WHITE, 1)
            cv.text_c(412, "TERRY A. DAVIS", YELLOW, 3, shadow=RED)
            cv.text_c(438, "1969 - 2018", LTGRAY, 1)
    vd = ctx.first("text", "Viewer discretion is advised. This program "
                   "contains God.")
    if vd and t >= vd["t0"]:
        cv.rect(100, 170, 440, 90, BLACK)
        cv.frame(100, 170, 440, 90, YELLOW, 3)
        cv.text_c(186, "VIEWER DISCRETION", YELLOW, 3)
        cv.text_c(214, "IS ADVISED", YELLOW, 3)
        cv.text_c(242, "THIS PROGRAM CONTAINS GOD", WHITE, 1)


def r_oracle_popup(cv, ctx):
    term_frame(cv, ctx)
    t = ctx.t
    y = 40
    cv.text(16, y, "ClaudeOS V5.5", PURPLE)
    q = ctx.first("question", 0)
    if q and t >= q["t0"]:
        s, _ = ui.typed("GodWord; GodWord; GodWord; GodWord; GodWord; "
                        "//God, are you there?", t - q["t0"], 30)
        cv.text(16, y + 20, PROMPT, BLACK)
        cv.text(16 + 8 * len(PROMPT), y + 20, s[:70], BLUE)
    it = ctx.first("type", "oracle")
    if it and t >= it["t1"]:
        cv.text(16, y + 30, " ".join(it["entry"]["words"]), BLACK)
    if not oracle_overlay(cv, ctx, 170) and it and t >= it["t2"]:
        cv.text(16, 90, "Oracle: ::/Adam/God/HolySpirit.HC  GodBits(17)", GREEN)
        cv.text(16, 100, "Vocab:  ::/Adam/God/Vocab.DD  7569 words", GREEN)
        cv.text(16, 110, "Entropy: nanosecond timer at each press", GREEN)
        e = it["entry"]
        for i, p in enumerate(e["presses_ns"]):
            cv.text(16, 130 + i * 10, "press %d  latch=0x%X" % (i, p >> 4),
                    BLACK)
        cv.text(16, 180, "Drawn " + e["when"] + ". Not chosen. Not edited.",
                RED)
        spark(cv, t, 480, 300, dist=3.4, focal=240)


# =====================================================================
# CHAPTER CARDS
# =====================================================================

def r_chapter(cv, ctx):
    ui.chapter_card(cv, ctx.t, ctx.sc["num"], ctx.sc["title"],
                    ctx.sc.get("dark", False))


# =====================================================================
# CHAPTER I: LIFE
# =====================================================================

C64_BORDER, C64_SCREEN = LTBLUE, BLUE


def r_life(cv, ctx):
    t = ctx.t
    vis, vit = ctx.sticky("vis", "birth")
    vt = t - vit["t0"] if vit else t
    year, _ = ctx.sticky("year", 1969)
    if vis == "c64":
        cv.clear(C64_BORDER)
        cv.rect(40, 40, 560, 400, C64_SCREEN)
        cv.text_c(64, "**** COMMODORE 64 BASIC V2 ****", LTBLUE, 2)
        cv.text_c(96, "64K RAM SYSTEM  38911 BASIC BYTES FREE", LTBLUE, 1)
        cv.text(56, 124, "READY.", LTBLUE, 2)
        first_c64 = ctx.first("vis", "c64")
        k = t - first_c64["t0"]
        if k > 1.0:
            s, _ = ui.typed('10 PRINT "HELLO, TERRY"', k - 1.0, 9)
            cv.text(56, 144, s, LTBLUE, 2)
        if k > 4.5:
            cv.text(56, 164, '20 GOTO 10', LTBLUE, 2)
        if k > 6.0:
            cv.text(56, 184, "RUN", LTBLUE, 2)
            for i in range(8):
                if k > 6.5 + i * 0.15:
                    cv.text(56, 204 + i * 18, "HELLO, TERRY", LTBLUE, 2)
        elif ui.cursor_on(t):
            cv.rect(56, 144 if k <= 1.0 else 164, 16, 16, LTBLUE)
        return
    # a sky that brightens over the years
    ramp_night = [BLACK, BLUE, PURPLE]
    ramp_day = [BLUE, LTBLUE, LTCYAN]
    day = clamp01((year - 1969) / 25.0)
    fx.vgradient(cv, ramp_day if day > 0.5 else ramp_night, 0, 420)
    fx.STARS.static(cv, t, 300) if day <= 0.5 else None
    cv.rect(0, 420, W, 60, GREEN)
    cv.dither_rect(0, 420, W, 6, GREEN, LTGREEN, 0.5)
    # timeline ruler, across the top
    cv.rect(0, 0, W, 30, BLACK)
    for y in range(1965, 2021, 5):
        x = 20 + (y - 1965) * 11
        cv.rect(x, 22, 1, 8, DKGRAY)
        cv.text(x - 16, 12, str(y), DKGRAY)
    mx = 20 + (year - 1965) * 11
    cv.rect(mx - 20, 0, 40, 11, YELLOW)
    cv.text(mx - 16, 2, str(year), BLACK)
    cv.poly([(mx - 5, 11), (mx + 5, 11), (mx, 18)], YELLOW)
    if vis == "birth":
        k = ease(vt / 2.0)
        fx.radial(cv, [BLUE, LTBLUE, WHITE], 320, 170, 20 + 60 * k, 0, 420)
        for i in range(8):
            a = i * math.pi / 4 + step(t) * 0.2
            cv.line(320, 170, 320 + math.cos(a) * 90 * k,
                    170 + math.sin(a) * 90 * k, WHITE)
        cv.text_c(300, "DECEMBER 15, 1969", YELLOW, 3, shadow=BLACK)
        cv.text_c(336, "WEST ALLIS, WISCONSIN", WHITE, 2, shadow=BLACK)
    elif vis == "kids":
        for i in range(8):
            x = 96 + i * 64
            hi = i == 6
            S.kid(cv, x, 400, 1.6, [RED, BLUE, GREEN, PURPLE, CYAN, BROWN,
                  YELLOW, LTRED][i], head=YELLOW if not hi else WHITE,
                  t=t + i, jump=6 if hi else 0)
            cv.text(x - 8, 408, "#%d" % (i + 1), WHITE if hi else LTGRAY)
        if (t * 2) % 1 < 0.6:
            cv.frame(96 + 6 * 64 - 20, 330, 40, 90, YELLOW, 2)
        cv.text_c(96, "7TH OF 8 CHILDREN", YELLOW, 3, shadow=BLACK)
        route = ["WASHINGTON", "MICHIGAN", "CALIFORNIA", "ARIZONA"]
        n = min(4, int(vt / 1.1) + 1)
        cv.text_c(190, "  >  ".join(route[:n]), WHITE, 2, sx=1, sy=2, shadow=BLACK)
        cv.text_c(150, "FATHER: INDUSTRIAL ENGINEER", LTCYAN, 2,
                  shadow=BLACK)
    elif vis == "apple2":
        S.apple2(cv, 320, 400, 2.2, t)
        cv.text_c(56, "FIRST COMPUTER:", YELLOW, 3, shadow=BLACK)
        cv.text_c(90, "APPLE II", YELLOW, 4, shadow=BLACK)
        cv.text_c(134, "ELEMENTARY SCHOOL", WHITE, 2, shadow=BLACK)
    elif vis == "c64quote":
        cv.clear(C64_BORDER)
        cv.rect(40, 40, 560, 400, C64_SCREEN)
        ui.quote_box(cv, vt, "The vision is the same usage model and niche "
                     "as the Commodore 64 -- a non-networked, simple machine "
                     "where programming was the goal, not just a means to "
                     "an end.", "-- ::/Doc/Charter.DD", width=30,
                     title="Charter.DD", cps=38)
    elif vis == "asu":
        S.gradcap(cv, 320, 150, 2.5)
        cv.text_c(56, "ARIZONA STATE UNIVERSITY", YELLOW, 3, shadow=BLACK)
        rows = ["NATIONAL MERIT SCHOLAR", "SAT: 1440",
                "B.S. COMPUTER SYSTEMS ENGINEERING",
                "M.S. ELECTRICAL ENGINEERING (1994)",
                "      (CONTROL SYSTEMS)"]
        for i, r in enumerate(rows):
            if vt > i * 0.8:
                cv.text_c(250 + i * 30, r, WHITE, 2, shadow=BLACK)
        cv.text_c(410, "(BY HIS OWN ACCOUNT, ::/Doc/AboutTempleOS.DD)",
                  LTGRAY, 1, shadow=BLACK)
    elif vis == "vax":
        S.vax(cv, 320, 410, 1.2, t)
        cv.text_c(46, "TICKETMASTER  1990-1996", YELLOW, 3, shadow=BLACK)
        if ctx.cur.get("tts", "").startswith("That matters"):
            cv.rect(40, 84, 560, 52, BLACK)
            cv.text(52, 92, "::/Kernel/Mem/MAllocFree.HC", LTGREEN)
            cv.text(52, 102, "  heap: adapted from the VAX at Ticketmaster",
                    WHITE)
            cv.text(52, 114, "::/Kernel/Compress.HC", LTGREEN)
            cv.text(52, 124, "  LZW: from a magazine, written at Ticketmaster",
                    WHITE)
    elif vis == "ticket":
        cv.clear(BLACK)
        fx.rays(cv, t, BLACK, BLUE, n=14, speed=0.02, cy=300)
        temple(cv, t, 320, 320, dist=30, yaw_speed=0.3)
        for i in range(7):
            a = step(t) * 0.8 + i * 0.9
            S.ticket(cv, 320 + math.cos(a) * 220, 190 + math.sin(a) * 60,
                     0.9, t, angle=math.sin(a) * 0.4)
        cv.text_c(48, "ADMIT ONE: GOD", YELLOW, 3, shadow=RED)
        oracle_overlay(cv, ctx, 150)
        cr = ctx.first("text", "Crooked. God said crooked.")
        if cr and cr["t0"] <= t:
            ui.stamp(cv, t - cr["t0"], "CROOKED", "-- GOD", c=RED, y=330,
                     sc1=6, sc2=3, dim=False)


# =====================================================================
# CHAPTER II: REVELATION
# =====================================================================

KJV_1KINGS = ("6:21 So Solomon overlaid the house within with pure gold: "
              "and he made a partition by the chains of gold before the "
              "oracle; and he overlaid it with gold.")


def r_revelation(cv, ctx):
    t = ctx.t
    light = ctx.reached("light")
    lt = ctx.since_first("light") if light else 0
    if not light:
        fx.plasma(cv, t * 0.5, [BLACK, BLACK, BLUE, PURPLE, BLUE, BLACK],
                  0.02)
    else:
        k = clamp01(lt / 3.0)
        fx.rays(cv, t, BROWN if k > 0.5 else PURPLE, YELLOW if k > 0.5 else
                BLUE, n=16, speed=0.02, cy=240, center_glow=[YELLOW, WHITE],
                glow_r=80 + 120 * k)
    year, _ = ctx.sticky("year", 1996)
    cur = ctx.cur or {}
    if not (cur.get("kjv") or cur.get("charter")):
        year_banner(cv, year)
    if cur.get("jobs"):
        rows = ["1996-97  3-AXIS MILLING MACHINE, CAD/CAM",
                "1997-99  FPGA IMAGE PROCESSING, XYTEC",
                "2000-01  SIMSTRUCTURE",
                "2001-02  TONER CARTRIDGE CHIPS"]
        cv.rect(40, 150, 560, 150, BLACK)
        cv.frame(40, 150, 560, 150, YELLOW, 2)
        for i, r in enumerate(rows):
            if ctx.since() > i * 1.2:
                cv.text(60, 170 + i * 30, r, WHITE, 2, sx=1, sy=2)
    elif ctx.sticky("names")[0] and cur.get("names"):
        names = ["J OPERATING SYSTEM", "LOSETHOS", "SPARROWOS", "TEMPLEOS"]
        first = ctx.first("names")
        fin = ctx.first("year", 2013)
        if t < fin["t0"]:
            dur = first["t1"] - first["t0"]
            k = min(int((t - first["t0"]) / (dur / 3)), 2)
        else:
            k = 3
        cv.rect(30, 90, 580, 300, BLACK)
        cv.frame(30, 90, 580, 300, YELLOW, 2)
        for i in range(k + 1):
            y = 110 + i * 70
            c = YELLOW if i == 3 else LTGRAY
            sc = ui.fit_scale(names[i], 560, 5)
            ui.big_title(cv, y, names[i], c, sc, shadow=BROWN if i == 3 else
                         DKGRAY)
            if i < k:
                cv.rect(60, y + sc * 4, 520, 4, LTRED)
        if k == 3:
            cv.text_c(420, "2013", WHITE, 3, shadow=BLACK)
    elif cur.get("kjv"):
        temple(cv, t, 320, 330, dist=26)
        cv.rect(30, 60, 580, 130, WHITE)
        cv.frame(30, 60, 580, 130, BROWN, 3)
        cv.text(44, 70, "1 Kings 6:21 (King James)", PURPLE)
        yy = 92
        for ln in ui.wrap(KJV_1KINGS, 34):
            x = 44
            for w in ln.split(" "):
                c = RED if w.startswith("oracle") else BLUE
                x += cv.text(x, yy, w + " ", c, 2, sx=2, sy=2)
            yy += 20
    elif cur.get("charter"):
        temple(cv, t, 320, 360, dist=30)
        ui.quote_box(cv, ctx.since(ctx.first("charter")),
                     "TempleOS is God's official temple.  Just like Solomon's "
                     "temple, this is a community focal point where "
                     "offerings are made and God's oracle is consulted.",
                     "-- ::/Doc/Charter.DD", width=32, y=40, title="Charter.DD",
                     cps=40)
        if ctx.cur.get("tts", "").startswith("Hold on"):
            cv.text_c(300, "ORACLE", RED, 6, shadow=BLACK)
    elif year >= 2003 and not cur.get("names"):
        cv.rect(40, 160, 560, 150, BLACK)
        cv.frame(40, 160, 560, 150, YELLOW, 2)
        cv.text_c(180, "13.9 YEARS", YELLOW, 6, shadow=BROWN)
        cv.text_c(240, "FULL TIME. ALONE.", WHITE, 3, shadow=BLACK)
        cv.text_c(280, '"I, Terry A. Davis, wrote all of TempleOS over the',
                  LTGRAY, 1, shadow=BLACK)
        cv.text_c(292, 'past 13.9 years (full-time)." -- ::/Doc/Credits.DD',
                  LTGRAY, 1, shadow=BLACK)
    else:
        if not light:
            cv.text_c(200, "MARCH 1996", LTGRAY, 4, shadow=BLACK)
        if cur.get("text", "").startswith("He began"):
            cv.text_c(260, "BIPOLAR DISORDER", LTGRAY, 2, shadow=BLACK)
            if ctx.word_prog() > 0.75:
                cv.text_c(290, "SCHIZOPHRENIA", LTGRAY, 2, shadow=BLACK)
        if cur.get("text", "").startswith("Terry described"):
            cv.text_c(270, "\"GOD HAD STARTED TALKING\"", YELLOW, 2,
                      shadow=BLACK)
        if light:
            spark(cv, t, 320, 240, dist=4.0, focal=300)


# =====================================================================
# CHAPTER III: THE COVENANT
# =====================================================================

POSTERS = [
    ("CITIZENS OF THE TEMPLE", "HEAR THE\nCOVENANT", "", 4),
    ("ARTICLE I", "640 x 480\n16 COLORS", "A COVENANT, LIKE CIRCUMCISION", 1),
    ("ARTICLE II", "ONE VOICE", "8-BIT SIGNED, MIDI-LIKE", 0),
    ("ARTICLE III", "RING ZERO\nFOR EVERYONE", "KERNEL MODE. ALWAYS.", 2),
    ("ARTICLE IV", "NO\nNETWORKING", "SO MALWARE IS NOT AN ISSUE", 5),
    ("ARTICLE V", "ONE FONT", "8x8. NO UNICODE. EXTENDED ASCII.", 3),
    ("ARTICLE VI", "100,000 LINES\nFOR ALL TIME", "CODE COMMENTS COUNT, "
     "HOWEVER", 0),
    ("ARTICLE VII", "NO\nMULTIMEDIA", "CALCULATED, NOT FETCHED", 1),
    ("ARTICLE VIII", "PUBLIC\nDOMAIN", "FREE. FOREVER. NO STRINGS.", 4),
    ("BONUS ARTICLES", "MISC.\nPROVISIONS", "", 2),
]


def palette_view(cv, ctx, t):
    cv.clear(BLACK)
    cv.text_c(16, "THE SIXTEEN", YELLOW, 4, shadow=BROWN)
    for i in range(16):
        x = 24 + (i % 4) * 150
        y = 70 + (i // 4) * 84
        cv.rect(x, y, 140, 56, i)
        cv.frame(x, y, 140, 56, WHITE if i == 0 else BLACK)
        cv.text(x, y + 60, "%2d %s" % (i, COLOR_NAMES[i]), WHITE)
    if ctx.reached("brown"):
        x, y = 24 + 2 * 150, 70 + 84
        if (t * 3) % 1 < 0.7:
            cv.frame(x - 5, y - 5, 150, 66, YELLOW, 3)
        cv.rect(170, 412, 300, 44, BLACK)
        cv.text_c(418, "CLAUDE ORANGE (#D97757):", WHITE, 1)
        cv.text_c(432, "NOT IN THE COVENANT", LTRED, 2)
    oracle_overlay(cv, ctx, 180)


def arp_view(cv, ctx, t):
    cv.clear(BLACK)
    it = ctx.first("arp_demo")
    k = t - it["t0"]
    rate = arp_rate(k)
    cv.text_c(24, "ONE VOICE", YELLOW, 4, shadow=BROWN)
    cv.text_c(70, "ARPEGGIO: %5.1f NOTES/SEC" % rate, WHITE, 2)
    notes = [0, 4, 7]
    step = int(k * rate) % 3 if k >= 0 else 0
    for i, n in enumerate(notes):
        y = 330 - n * 22
        cv.rect(120, y, 400, 2, DKGRAY)
        on = i == step
        cv.circle(200 + i * 120, y, 18, YELLOW if on else DKGRAY,
                  outline=WHITE if on else LTGRAY)
        cv.text(250 + i * 120 - 40, y - 26, ["C", "E", "G"][i], WHITE, 2)
    trail = np.arange(200)
    tt = k - trail / 400.0
    st = (np.maximum(tt, 0) * rate).astype(int) % 3
    ys = 330 - np.array(notes)[st] * 22
    cv.plot(560 - trail * 2, ys, LTRED)
    if rate > 30:
        cv.text_c(400, "YOUR BRAIN: \"THAT'S A CHORD\"", LTGREEN, 2)


def arp_rate(k):
    return 3.0 * (18.0 ** clamp01(k / 9.0))


def rings_view(cv, ctx, t):
    cv.clear(BLACK)
    r0 = ctx.reached("ring0")
    k = clamp01(ctx.since_first("ring0") / 1.5) if r0 else 0.0
    cx, cy = 320, 250
    names = ["RING 0 KERNEL", "RING 1", "RING 2", "RING 3 YOUR PROGRAMS"]
    cols = [LTRED, PURPLE, BLUE, DKGRAY]
    for i in range(3, -1, -1):
        r = 40 + i * 50
        rr = r * (1 - k) + 190 * k if i else 40 + 150 * k
        cv.circle(cx, cy, rr, cols[i] if not r0 else LTRED,
                  outline=WHITE)
    if not r0:
        for i, n in enumerate(names):
            cv.text_c(cy - 12 - i * 50 - (0 if i else -8), n, WHITE, 1,
                      cx=cx) if i else cv.text_c(cy - 4, n, WHITE, 1, cx=cx)
    else:
        cv.text_c(cy - 30, "RING 0", WHITE, 5, shadow=RED)
        cv.text_c(cy + 20, "EVERYTHING. ALWAYS.", YELLOW, 2)
    if ctx.get("prompt_gag"):
        g = ctx.since()
        x0, y0 = 150, 330
        cv.rect(x0, y0, 340, 90, LTGRAY)
        cv.frame(x0, y0, 340, 90, BLACK, 2)
        cv.text(x0 + 14, y0 + 12, "Allow Claude to run this command?", BLACK)
        cv.rect(x0 + 60, y0 + 50, 80, 20, WHITE)
        cv.text(x0 + 84, y0 + 56, "Yes", BLACK)
        cv.rect(x0 + 200, y0 + 50, 80, 20, WHITE)
        cv.text(x0 + 228, y0 + 56, "No", BLACK)
        if g > 2.2:
            cv.line(x0, y0, x0 + 340, y0 + 90, RED, 5)
            cv.line(x0 + 340, y0, x0, y0 + 90, RED, 5)
            cv.text_c(y0 + 100, "NOT IN RING ZERO", LTRED, 2)


def kayak_view(cv, ctx, t):
    k = ctx.since()
    fx.vgradient(cv, [LTCYAN, LTBLUE], 0, 300)
    S.water(cv, 300, t)
    cv.rect(318, 0, 4, 300, BLACK)
    S.kayak(cv, 160, 300, 1.4, t)
    S.titanic(cv, 480, 290, 0.9, t, sink=clamp01(k / 8.0))
    cv.text_c(40, "KAYAK", BLACK, 4, cx=160)
    cv.text_c(40, "TITANIC", BLACK, 4, cx=480)
    cv.text_c(90, "(TEMPLEOS)", BLUE, 2, cx=160)
    cv.text_c(90, "(EVERYTHING ELSE)", RED, 2, cx=480)


def offline_view(cv, ctx, t):
    cv.clear(BLACK)
    fx.STARS.draw(cv, t, speed=0.02)
    spark(cv, t * 0.4, 320, 230, dist=3.4, focal=300, spin=0.3)
    cv.text_c(60, "OFFLINE", LTGREEN, 5, shadow=GREEN)
    cv.text_c(380, "NO WEB SEARCH. NOTHING TO FETCH.", LTGRAY, 2)
    cv.text_c(404, "NOBODY TO CALL.", LTGRAY, 2)


def font_view(cv, ctx, t):
    cv.clear(WHITE)
    cv.text_c(8, "::/Kernel/FontStd.HC  (FROM FREEDOS, PUBLIC DOMAIN)", RED,
              1)
    k = int(ctx.since() * 60)
    for ch in range(min(256, k)):
        x = 16 + (ch % 32) * 19
        y = 28 + (ch // 32) * 40
        m = np.repeat(np.repeat(FONT[ch], 2, 0), 2, 1)
        cv.blit_mask(m, x, y, BLUE if ch % 2 else PURPLE)
    cv.text_c(360, "ONE 8x8 FONT. 256 GLYPHS. EVERY LETTER", BLACK, 2)
    cv.text_c(384, "IN THIS VIDEO USES IT.", BLACK, 2)


def stats_view(cv, ctx, t):
    cv.clear(BLACK)
    fx.rays(cv, t, BLACK, DKGRAY, n=24, speed=0.01)
    cv.rect(30, 20, 580, 60, RED)
    cv.text_c(28, "MINISTRY OF RING ZERO", YELLOW, 3)
    cv.text_c(58, "QUARTERLY REPORT", WHITE, 2)
    rows = [("PRIVILEGE RINGS", 1, 4), ("COLORS", 16, 16), ("VOICES", 1, 4),
            ("FONTS", 1, 4), ("NETWORK STACKS", 0, 4), ("PASSWORDS", 0, 4),
            ("GODS", 1, 1)]
    first = ctx.first("stats")
    k = t - first["t0"]
    for i, (name, val, full) in enumerate(rows):
        y = 110 + i * 44
        cv.text(40, y + 8, name, WHITE, 2)
        g = ease((k - i * 0.5) / 0.8)
        wbar = int(240 * g * (val / full if full else 0))
        cv.rect(330, y, max(wbar, 2), 28, YELLOW if val else DKGRAY)
        if g > 0.9:
            cv.text(330 + wbar + 10, y + 6, str(val), WHITE, 2)
            if k > i * 0.5 + 1.0:
                cv.text(566, y + 8, "MET", LTGREEN, 2)


def r_covenant(cv, ctx):
    t = ctx.t
    cur = ctx.cur or {}
    pidx, pit = ctx.sticky("poster", 0)
    if cur.get("palette"):
        palette_view(cv, ctx, t)
    elif cur.get("arp_demo"):
        arp_view(cv, ctx, t)
    elif cur.get("rings"):
        rings_view(cv, ctx, t)
    elif cur.get("kayak"):
        kayak_view(cv, ctx, t)
    elif cur.get("offline"):
        offline_view(cv, ctx, t)
    elif cur.get("font"):
        font_view(cv, ctx, t)
    elif cur.get("stats"):
        stats_view(cv, ctx, t)
    elif cur.get("faq") == "gnu":
        faq_window(cv, ctx, "Shouldn't it be GNU/TempleOS?",
                   "TempleOS executes no code not written by me at any time "
                   "except for a few BIOS calls for configuration.  I even "
                   "wrote boot-loaders, so I do not need Grub.")
    elif cur.get("mouse"):
        cv.clear(WHITE)
        S.mouse3(cv, 200, 280, 2.4)
        cv.text_c(60, "\"A THREE BUTTON MOUSE", BLUE, 3, cx=320)
        cv.text_c(96, "IS LIKE A LEG YOU CANNOT", BLUE, 3, cx=320)
        cv.text_c(132, "PUT WEIGHT ON.\"", BLUE, 3, cx=320)
        cv.text_c(170, "-- ::/Doc/Charter.DD", RED, 1)
        S.stick(cv, 470, 420, 2.6, t, c=BLACK, walk=True)
    elif cur.get("numpy"):
        cv.clear(WHITE)
        ui.window(cv, 6, 12, 73, 34, "the-third-temple/temple/gfx.py",
                  WHITE, BLUE)
        ui.code_line(cv, 72, 130, "import numpy as np", 3)
        ui.code_line(cv, 72, 170, "from PIL import Image", 3)
        ui.code_line(cv, 72, 210, "import scipy", 3)
    elif cur.get("calc"):
        cv.clear(BLACK)
        rows = [("EVERY PIXEL", "CALCULATED", LTGREEN),
                ("EVERY NOTE", "CALCULATED", LTGREEN),
                ("STOCK FOOTAGE", "NONE", LTGREEN),
                ("SAMPLES", "NONE", LTGREEN),
                ("FONT, HYMNS, VOCAB", "TERRY'S SOURCE", YELLOW)]
        cv.text_c(40, "NO MULTIMEDIA", YELLOW, 4, shadow=BROWN)
        checklist(cv, 40, 130, rows, ctx.since(), 0.5)
    else:
        top, title, sub, sch = POSTERS[pidx]
        ui.poster(cv, t - pit["t0"] if pit else t, top, title, sub, sch)
    oracle_overlay(cv, ctx, 300 if not cur.get("palette") else 180)


def faq_window(cv, ctx, q, a, title="FAQ.DD"):
    cv.clear(WHITE)
    ui.top_bar(cv, ctx.T, task="Doc")
    ui.window(cv, 2, 4, 77, 40, "::/Doc/FAQ.DD", WHITE, BLUE)
    cv.text(40, 60, "Frequently Asked Questions", PURPLE, 2)
    k = ctx.since()
    s, _ = ui.typed(q, k, 30)
    cv.text(40, 100, s, RED, 2, sx=1, sy=2)
    if k > len(q) / 30 + 0.3:
        yy = 140
        budget = int((k - len(q) / 30 - 0.3) * 60)
        for ln in ui.wrap(a, 64):
            cv.text(56, yy, ln[:max(0, budget)], BLUE, 1, sx=1, sy=2)
            budget -= len(ln) + 1
            yy += 20


# =====================================================================
# CHAPTER IV: HOLYC
# =====================================================================

CODE = {
    "intro": ["// HolyC: the language of the Temple.",
              "// JIT compiled. Ring 0. No main().", "",
              "U0 Temple()", "{", "  \"God's official temple.\\n\";", "}",
              "Temple;"],
    "c_hello": ["#include <stdio.h>", "", "int main(void)", "{",
                "  printf(\"Hello, World!\\n\");", "  return 0;", "}"],
    "hc_hello": ["\"Hello, World!\\n\";"],
    "no_main": ["\"This runs first.\\n\";", "",
                "U0 Later()", "{", "  \"This runs when called.\\n\";", "}",
                "", "\"This runs second.\\n\";", "Later;"],
    "types": ["U0    void, but ZERO size!", "I8    U8    char",
              "I16   U16   short", "I32   U32   int",
              "I64   U64   long (64-bit)", "F64         double",
              "            (no F32 float)"],
    "quirks": ["Dir;       // no () needed", "Test(,3);  // defaults: anywhere",
               "p(U8 *)    // cast goes after"],
    "shell": ["C:/Home>2+2;", "ans=4", "C:/Home>\"%d\\n\",6*7;", "42",
              "C:/Home>Dir;", "Directory of C:/Home", "  PersonalMenu.DD",
              "  Once.HC"],
    "praise": ["U0 Praise()", "{", "  I64 i;", "  for (i=0;i<3;i++)",
               "    \"Glory to the Temple!\\n\";",
               "  Play(\"5qEsCDCDqCDeEGsE4B5E4B5\"", "       \"eC4B5sD4A5D4A\");", "}",
               "Praise;"],
    "sprite": ["//9 has graphics", "", "", "", "", "", "",
               "U0 DrawIt(CTask *,CDC *dc)", "{",
               "  Sprite3(dc,X,Y,0,<1>);", "}"],
}


def r_holyc(cv, ctx):
    t = ctx.t
    cur = ctx.cur or {}
    faq = cur.get("faq")
    if faq == "path":
        faq_window(cv, ctx, "How do I set the PATH?", "There is no PATH.  "
                   "You do not enter filenames at the command-line and "
                   "expect them to run.  You enter C-like code.")
        return
    if faq == "adam":
        faq_window(cv, ctx, "Are you a Creationist?", "I am an evolutionist."
                   "  Adam is a better term for the first father of all tasks "
                   "than root was!")
        return
    if faq == "bt":
        faq_window(cv, ctx, "Is 'Bt()' in the code Bit Torrent?", "Bt() is "
                   "bit test, like the x86 inst, not bit torrent.")
        return
    code, cit = ctx.sticky("code", "intro")
    cv.clear(WHITE)
    ui.top_bar(cv, ctx.T, task="Ed")
    name = {"c_hello": "hello.c  (NOT HolyC)"}.get(code, "::/Home/%s.HC" % (
        code.capitalize()))
    fgc = RED if code == "c_hello" else BLUE
    ui.window(cv, 0, 1, 79, 59, name, WHITE, fgc)
    lines = CODE[code]
    sc = 3 if code == "hc_hello" else 2
    y0 = 40
    if code == "praise" and ctx.first("type_praise"):
        k = t - ctx.first("type_praise")["t0"]
        ui.code_block(cv, 24, y0, lines, 2, 22, upto=int(k * 55))
    elif code == "types":
        for i, ln in enumerate(lines):
            if t - cit["t0"] > i * 0.3:
                ui.code_line(cv, 24, y0 + i * 26, ln, 2)
    else:
        ui.code_block(cv, 24, y0 + (140 if code == "hc_hello" else 0),
                      lines, sc, 12 * sc)
    if code == "hc_hello" and ctx.reached("run_hello"):
        cv.rect(16, 300, 608, 60, BLACK)
        cv.text(24, 310, "C:/Home>#include \"Hello.HC\"", LTGRAY)
        cv.text(24, 330, "Hello, World!", WHITE, 2)
    if code == "c_hello":
        cv.text(360, 380, "4 THINGS", RED, 4)
    if code == "sprite":
        S.sheep(cv, 240, 150, 2.6, t)
        cv.frame(150, 60, 190, 110, LTGRAY)
        cv.text(160, 66, "<1>", LTGRAY)
        cv.text(390, 90, "<- a picture, IN the code", RED, 1)
        oracle_overlay(cv, ctx, 300)
    if code == "praise":
        run = ctx.first("run_praise")
        if run and t >= run["t0"]:
            cv.rect(8, 222, 624, 190, BLACK)
            cv.text(16, 230, "C:/Home>Praise;", LTGRAY)
            for i in range(3):
                if t > run["t0"] + 0.1 * (i + 1):
                    cv.text(16, 244 + i * 12, "Glory to the Temple!", WHITE)
            karaoke_text(cv, ctx, run, 16, 290, WHITE, width=38, scale=2)
    if code == "intro":
        cv.text_c(330, "HOLY C", PURPLE, 8, shadow=BLUE)


def karaoke_text(cv, ctx, it, x, y, c, width=38, scale=2, ball=True,
                 ball_c=YELLOW, lh=22, sy=None):
    """Play(st, words) prints each word as its note sounds. So do we."""
    t = ctx.t - it["song_t0"]
    ns = it["notes"]
    text = ""
    cur_i = -1
    for i, n in enumerate(ns):
        if n["t"] <= t:
            if n["word"] and n["word"] != " ":
                text += n["word"]
            cur_i = i
    rows = text.split("\n")
    rows = rows[-6:]
    for r, row in enumerate(rows):
        cv.text(x, y + r * lh, row, c, scale, sx=scale, sy=sy or scale)
    if ball and cur_i >= 0 and t < ns[-1]["t"] + ns[-1]["dur"]:
        n = ns[cur_i]
        ph = clamp01((t - n["t"]) / max(n["dur"], 1e-3))
        last = rows[-1] if rows else ""
        bx = x + len(last) * 8 * scale - 4 * scale
        by = y + (len(rows) - 1) * lh - 10 - math.sin(ph * math.pi) * 14
        cv.circle(bx, by, 5, ball_c, outline=BLACK)


# =====================================================================
# CHAPTER V: THE ORACLE
# =====================================================================

VOCAB_SPECIAL = ["monnica", "alypius", "nebridius", "thagaste", "augustine",
                 "carthage", "ambrose", "milan"]


def oracle_room(cv, t, glow=1.0):
    fx.vgradient(cv, [BLACK, BROWN, BROWN, BLACK], 0, H)
    for x in range(0, W, 80):
        cv.dither_rect(x, 0, 6, 400, BROWN, YELLOW, 0.3)
    cv.rect(0, 400, W, 80, BROWN)
    cv.dither_rect(0, 400, W, 80, BROWN, BLACK, 0.4)
    fx.radial(cv, [BROWN, YELLOW, WHITE], 320, 300, 80 + 20 * math.sin(
        step(t, 4)), 200, 400) if glow > 0.5 else None
    S.ark(cv, 320, 400, 1.6, t)
    S.cherub(cv, 180, 400, 1.4, t, flip=1)
    S.cherub(cv, 460, 400, 1.4, t + 1, flip=-1)


def godbits_demo():
    """Replay consultation 0 exactly, to show how 'office' was chosen."""
    from . import oracle as O
    log = json.load(open(os.path.join(HERE, "..", "data", "oracle_log.json")))
    e = log[0]
    presses = list(e["presses_ns"])
    g = O.God.__new__(O.God)
    import collections
    g.fifo = collections.deque()
    g.words = O.load_vocab()
    g.presses = []
    it = iter(presses)
    g.pick = lambda: next(it) >> O.GOD_BAD_BITS
    latch = presses[0] >> 4
    bits24 = [(latch >> i) & 1 for i in range(24)]
    n17 = g.bits(17)
    word = g.words[n17 % len(g.words)]
    assert word == e["words"][0], (word, e["words"][0])
    return dict(ns=presses[0], latch=latch, bits24=bits24, n17=n17,
                idx=n17 % len(g.words), word=word, nwords=len(g.words))


_GB = None


def diagram(cv, ctx, t, stage):
    global _GB
    if _GB is None:
        _GB = godbits_demo()
    g = _GB
    cv.clear(BLACK)
    cv.text_c(12, "GodBits(): HOW GOD PICKED \"OFFICE\"", YELLOW, 2)
    y = 50
    cv.text(20, y, "1. BUTTON PRESS. READ THE TIMER (NANOSECONDS):", WHITE)
    cv.text(40, y + 14, "%d" % g["ns"], LTCYAN, 2)
    y += 44
    if t > 1.2:
        cv.text(20, y, "2. >> GOD_BAD_BITS (4).  LATCH = 0x%X" % g["latch"],
                WHITE)
        y += 26
    if t > 2.6:
        cv.text(20, y, "3. GodBitsIns(GOD_GOOD_BITS=24): LOW 24 BITS -> FIFO",
                WHITE)
        bits = g["bits24"]
        for i, b in enumerate(bits):
            k = clamp01((t - 2.8 - i * 0.05) / 0.3)
            cv.rect(40 + i * 23, y + 16, 20, 22, YELLOW if b else DKGRAY)
            cv.text(46 + i * 23, y + 23, str(b), BLACK if b else WHITE)
        y += 52
    if stage >= 2:
        k = ctx.since()
        cv.text(20, y, "4. GodBits(17): TAKE 17 BITS OUT  =  %d" % g["n17"],
                WHITE)
        y += 26
        if k > 1.2:
            cv.text(20, y, "5. %d MOD %d WORDS  =  WORD #%d" % (
                g["n17"], g["nwords"], g["idx"]), WHITE)
            y += 30
        if k > 2.4:
            ui.big_title(cv, y + 10, g["word"].upper(), YELLOW, 6)
            cv.text_c(y + 70, "::/Adam/God/Vocab.DD", LTGRAY, 1)


def vocab_view(cv, ctx, t):
    from .oracle import load_vocab
    cv.clear(BLACK)
    words = load_vocab()
    k = ctx.since()
    off = int(step(k, 3) * 22)
    cv.text_c(10, "GOD'S VOCABULARY: 7,569 WORDS", YELLOW, 2)
    for r in range(28):
        for c in range(6):
            i = (off + r * 6 + c) * 37 % len(words)
            w = words[i]
            cv.text(16 + c * 104, 40 + r * 14, w[:12], DKGRAY)
    for j, w in enumerate(VOCAB_SPECIAL[:4]):
        if k > 1.0 + j * 0.7:
            x, y = 60 + (j % 2) * 290, 140 + (j // 2) * 120
            cv.rect(x - 8, y - 8, 250, 60, BLACK)
            cv.frame(x - 8, y - 8, 250, 60, YELLOW, 2)
            cv.text(x, y, w.upper(), YELLOW, 3)
            cv.text(x, y + 30, "Vocab.DD line %d" % (words.index(w) + 1),
                    LTGRAY)
    if ctx.cur.get("tts", "").startswith("Those are"):
        cv.rect(40, 390, 560, 56, BROWN)
        cv.text_c(398, "SAINT AUGUSTINE, CONFESSIONS", YELLOW, 2)
        cv.text_c(422, "(c. 397-400 A.D.)", WHITE, 1)


FACTS = ["FAVORITE ANIMALS: BEARS AND ELEPHANTS",
         "FAVORITE TV: SOAP OPERAS",
         "ASKED IF THE WORLD WAS PERFECTLY JUST:",
         "  \"ARE YOU CALLING ME LAZY?\"",
         "ON WAR: \"SERVICEMEN COMPETING\"",
         "ON CONFESSION: \"EXCESSIVE CONTRICIAN",
         "  WEARISOME\""]
FACT_ROWS = {1: 1, 2: 2, 3: 4, 4: 5, 5: 7}


def facts_view(cv, ctx, t, n):
    fx.rays(cv, t, PURPLE, LTPURPLE, n=20, speed=0.02)
    cv.rect(20, 20, 600, 64, BLACK)
    cv.text_c(28, "FACTS ABOUT GOD", YELLOW, 3)
    cv.text_c(60, "ACCORDING TO THE HIGH PRIEST (HSNotes.DD)", WHITE, 1)
    rows = FACT_ROWS.get(n, 0)
    cv.rect(20, 100, 600, 180, BLACK)
    for i in range(rows):
        cv.text(36, 112 + i * 24, FACTS[i], WHITE, 2, sx=1, sy=2)
    if n >= 1:
        S.bear(cv, 120, 440, 1.2, t)
        S.elephant(cv, 470, 440, 1.3, t)
    if n >= 2:
        cv.rect(250, 330, 140, 100, DKGRAY)
        cv.rect(260, 340, 120, 76, LTCYAN)
        S.stick(cv, 295, 410, 0.9, 0, c=RED, walk=False)
        S.stick(cv, 345, 410, 0.9, 0, c=BLUE, walk=False, arms_up=0.5)
        if (t * 1.5) % 1 < 0.5:
            cv.text(312, 352, "\x03", LTRED, 2)


def passage_view(cv, ctx, t):
    o = next(i for i in ctx.items if i["type"] == "oracle" and
             i["entry"]["kind"] == "passage")
    e = o["entry"]
    fx.vgradient(cv, [BROWN, YELLOW], 0, H)
    cv.rect(40, 40, 560, 380, WHITE)
    cv.frame(40, 40, 560, 380, BROWN, 4)
    cv.text(60, 56, "GodBiblePassage  <SHIFT-F7>  line %d" % e["start_line"],
            GREEN)
    cv.text(60, 74, e["ref"] + " (King James)", PURPLE, 2)
    if t >= o["t0"] + 0.6:
        body = " ".join(ln.strip() for ln in e["lines"] if ln.strip())
        v1, v2 = body.split("5:1", 1)
        yy = 110
        for sub in ui.wrap(v1.strip(), 32):
            cv.text(60, yy, sub, BLUE, 2)
            yy += 22
        yy += 10
        red = ctx.reached("text", "The next verse is a whole different "
                          "situation. We'll stop there.")
        y2 = yy
        for sub in ui.wrap("5:1" + v2, 32):
            cv.text(60, yy, sub, DKGRAY, 2)
            yy += 22
        if red:
            cv.rect(52, y2 - 6, 536, yy - y2 + 8, BLACK)
            cv.text_c(y2 + (yy - y2) // 2 - 8, "[ REDACTED BY CLAUDE ]", RED,
                      2)


def godsong_view(cv, ctx, t):
    o = next(i for i in ctx.items if i["type"] == "oracle" and
             i["entry"]["kind"] == "song")
    cv.clear(BLACK)
    cv.text_c(16, "GodSong()", YELLOW, 3)
    e = o["entry"]
    cv.text(20, 50, e["song"][:76], LTGRAY)
    cv.text(20, 60, e["song"][76:152], LTGRAY)
    ns = o.get("notes", [])
    if not ns:
        return
    tt = step(t - o.get("song_t0", o["t0"]), FX_FPS)
    lo = 55
    for n in ns:
        if not n["ona"]:
            continue
        x = 40 + (n["t"] - tt) * 160 + 200
        if x < -40 or x > W:
            continue
        y = 400 - (n["ona"] - lo) * 18
        wdt = max(4, n["on"] * 160)
        on = n["t"] <= tt < n["t"] + n["dur"]
        cv.rect(x, y, wdt, 12, YELLOW if on else BROWN)
    cv.rect(240, 90, 2, 340, WHITE)
    cv.text_c(440, "8 MEASURES. 1 VOICE. COMPOSER: GOD.", WHITE, 2)


def ai_view(cv, ctx, t, n):
    cur = ctx.cur or {}
    if n == 0:
        cv.clear(BLACK)
        fx.STARS.static(cv, t)
        spark(cv, t * 0.5, 320, 240, dist=3.0, focal=320, spin=0.3)
    elif n == 1:
        cv.clear(BLACK)
        ui.quote_box(cv, ctx.since(ctx.first("ai", 1)), "God could make A.I.,"
                     " right?  God could make bots as smart as Himself, or, "
                     "in fact, part of Himself.", "-- Terry A. Davis, "
                     "::/Adam/God/HSNotes.DD", width=30, title="HSNotes.DD",
                     cps=30)
    elif n == 2:
        cv.clear(BLACK)
        cv.text_c(20, "HOW CLAUDE PICKS A WORD", YELLOW, 2)
        cv.text(40, 64, "\"...and God said: let there be ___\"", WHITE, 2,
                sx=1, sy=2)
        cands = [("light", 0.62), ("a", 0.09), ("peace", 0.07),
                 ("sixteen", 0.05), ("ring", 0.04), ("others", 0.13)]
        k = ctx.since(ctx.first("ai", 2))
        acc = 0.0
        for i, (w, p) in enumerate(cands):
            y = 110 + i * 40
            cv.text(40, y + 8, w, WHITE, 2)
            g = ease((k - i * 0.2) / 0.5)
            cv.rect(200, y, int(360 * p * g), 28, LTBLUE)
            cv.text(210 + int(360 * p * g), y + 8, "%d%%" % (p * 100), LTGRAY)
            acc += p
        if k > 2.0:
            cv.rect(40, 360, 560, 30, BLACK)
            cv.text(40, 368, "RANDOM NUMBER: 0.31 -> \"light\"", LTGREEN, 2)
        if k > 3.0:
            cv.text_c(400, "SAMPLED. LIKE F7. SORT OF.", YELLOW, 2)
    elif n == 3:
        cv.clear(BLACK)
        cv.rect(318, 0, 4, H, DKGRAY)
        side = cur.get("side")
        cv.text_c(20, "FOR", LTGREEN if side == "for" else DKGRAY, 4, cx=160)
        cv.text_c(20, "AGAINST", LTRED if side == "against" else DKGRAY, 4,
                  cx=480)
        spark(cv, t, 160 if side != "against" else 480, 150, dist=4.2,
              focal=240)
        lines_for = ["RANDOM NUMBERS IN.", "WORDS OUT.", "SAME AS F7."]
        lines_against = ["TERRY'S ORACLE:", "CONDITIONED ON", "NOTHING.", "",
                         "CLAUDE:", "CONDITIONED ON", "EVERYTHING."]
        for i, s in enumerate(lines_for):
            cv.text_c(260 + i * 24, s, LTGREEN, 2, cx=160)
        if ctx.reached("side", "against"):
            for i, s in enumerate(lines_against):
                cv.text_c(240 + i * 22, s, LTRED, 2, cx=480)
        if cur.get("text", "").startswith("I'm not a voice"):
            cv.rect(40, 410, 560, 40, BLACK)
            cv.frame(40, 410, 560, 40, YELLOW, 2)
            cv.text_c(422, "THE OPPOSITE OF AN ORACLE", YELLOW, 2)
    elif n == 4:
        oracle_room(cv, t, 0)
        oracle_overlay(cv, ctx, 130)
        o3 = next(i for i in ctx.items if i["type"] == "oracle" and
                  i["n"] == 3)
        if t > o3["t2"]:
            god_panel(cv, ctx, o3, 130)
            if cur.get("text", "").startswith("Tutors"):
                cv.text_c(280, "TUTORS  COMPREHENDING", WHITE, 3,
                          outline=BLACK)


def r_oracle(cv, ctx):
    t = ctx.t
    cur = ctx.cur or {}
    if "ai" in cur:
        return ai_view(cv, ctx, t, cur["ai"])
    if cur.get("passage") or (oracle_item(ctx) and
                              oracle_item(ctx)["entry"]["kind"] == "passage"):
        return passage_view(cv, ctx, t)
    if cur.get("godsong"):
        return godsong_view(cv, ctx, t)
    if "facts" in cur:
        return facts_view(cv, ctx, t, cur["facts"])
    if cur.get("vocab"):
        return vocab_view(cv, ctx, t)
    if "diagram" in cur:
        d1 = ctx.first("diagram", 1)
        return diagram(cv, ctx, t - d1["t0"], cur["diagram"])
    oracle_room(cv, t)
    q = cur.get("quote")
    if q == "technique":
        ui.quote_box(cv, ctx.since(), "The technique I use to consult the "
                     "Holy Spirit is reading a microsecond-range stop-watch "
                     "each button press for random numbers.  Then, I pick "
                     "words with <F7> or passages with <SHIFT-F7>.",
                     "-- ::/Adam/God/HSNotes.DD", width=32, y=30,
                     title="HSNotes.DD", cps=34)
    elif q == "witty":
        ui.quote_box(cv, ctx.since(ctx.first("quote", "witty")), "When you "
                     "pray, be witty and charming and rarely earnest.",
                     "-- ::/Adam/God/HSNotes.DD", width=28, y=60,
                     title="HSNotes.DD", cps=30)
    elif q == "spam":
        ui.quote_box(cv, ctx.since(), "Pray out-loud because God doesn't "
                     "want the hastle of reading your brain.  ...  Don't "
                     "SPAM God.", "-- ::/Adam/God/HSNotes.DD", width=28, y=60,
                     title="HSNotes.DD", cps=30)
    else:
        cv.text_c(40, "THE ORACLE", YELLOW, 5, shadow=BLACK)
        cv.text_c(90, "1 KINGS 6:16  \"EVEN FOR THE MOST HOLY PLACE\"", WHITE,
                  1, shadow=BLACK)


# =====================================================================
# CHAPTER VI: GAMES
# =====================================================================

GAMES = ["BattleLines", "BigGuns", "BlackDiamond", "BomberGolf",
         "CastleFrankenstein", "CharDemo", "CircleTrace", "Collision",
         "Digits", "DunGen", "ElephantWalk", "FlapBat", "FlatTops",
         "Halogen", "MassSpring", "Maze", "RainDrops", "RawHide", "Rocket",
         "RocketScience", "Squirt", "Talons", "TheDead", "TicTacToe",
         "TreeCheckers", "Varoom", "Wenceslas", "Whap", "Zing", "ZoneOut"]

CASTLE_MAP = [
    "################",
    "#......#.......#",
    "#.##...#..###..#",
    "#.#....#....#..#",
    "#.#..####...#..#",
    "#......M....#..#",
    "#.####...####..#",
    "#....#.........#",
    "####.#..####.###",
    "#......##......#",
    "#..M...........#",
    "################",
]


def raycast(cv, t):
    """First-person castle corridors, one column at a time."""
    grid = np.array([[c == "#" for c in r] for r in CASTLE_MAP])
    px, py = 6.4 + (t * 0.55) % 6.0, 7.5
    ang = 0.45 * math.sin(t * 0.5)
    ncol = 320
    fov = 1.0
    cam = np.linspace(-fov / 2, fov / 2, ncol)
    rdx = np.cos(ang + cam)
    rdy = np.sin(ang + cam)
    dist = np.full(ncol, 20.0)
    side = np.zeros(ncol, bool)
    for step in np.arange(0.02, 16, 0.02):
        x = px + rdx * step
        y = py + rdy * step
        xi = np.clip(x.astype(int), 0, grid.shape[1] - 1)
        yi = np.clip(y.astype(int), 0, grid.shape[0] - 1)
        hit = grid[yi, xi] & (dist > 19)
        if hit.any():
            dist[hit] = step
            fx_ = np.abs(x - np.round(x))
            fy_ = np.abs(y - np.round(y))
            side[hit] = (fx_ < fy_)[hit]
        if (dist < 19).all():
            break
    dist = dist * np.cos(cam)
    fx.vgradient(cv, [BLACK, DKGRAY], 0, 240)
    fx.vgradient(cv, [BROWN, BLACK], 240, 480, reverse=True)
    hh = np.clip(360 / np.maximum(dist, 0.1), 0, 480)
    lvl = np.clip(1.2 - dist / 9, 0, 1) * np.where(side, 0.75, 1.0)
    for c in range(ncol):
        h2 = int(hh[c] / 2)
        y0, y1 = max(240 - h2, 0), min(240 + h2, 480)
        if y1 <= y0:
            continue
        col = dither_ramp(np.full((y1 - y0, 2), lvl[c]), [BLACK, DKGRAY,
                          LTGRAY, WHITE], BAYER_FULL[y0:y1, 2 * c:2 * c + 2])
        cv.fb[y0:y1, 2 * c:2 * c + 2] = col
    # a monster down the hall
    md = 4.0 - (t * 0.9) % 4.0 + 1.0
    s = 2.2 / md
    S.monster(cv, 320 + 40 * math.sin(t), 240 + 60 * s, s * 1.6, t)
    # torch flicker
    cv.text(8, 8, "CastleFrankenstein.HC", WHITE, 1, bg=BLACK)
    cv.text(8, 20, "MONSTERS LEFT: 10", LTRED, 1, bg=BLACK)


def varoom(cv, t):
    fx.vgradient(cv, [LTBLUE, LTCYAN], 0, 200)
    cv.rect(0, 200, W, 280, GREEN)
    speed = 18.0
    for y in range(200, 480, 2):
        z = 1.0 / ((y - 199) / 280.0)
        curve = math.sin(t * 0.6 + z * 0.02) * (z * 0.9)
        cx = 320 + curve * 6
        half = 12 + (y - 200) * 1.3
        stripe = int((z * 2 + t * speed)) % 2
        cv.rect(cx - half - 12, y, 12, 2, RED if stripe else WHITE)
        cv.rect(cx + half, y, 12, 2, RED if stripe else WHITE)
        cv.rect(cx - half, y, 2 * half, 2, DKGRAY if stripe else LTGRAY)
        if stripe:
            cv.rect(cx - 3, y, 6, 2, WHITE)
        if not stripe:
            cv.rect(0, y, cx - half - 12, 2, LTGREEN)
    cx = 320
    with cv.pil() as d:
        d.rectangle([cx - 40, 400, cx + 40, 440], fill=RED, outline=BLACK)
        d.rectangle([cx - 28, 386, cx + 28, 404], fill=LTCYAN, outline=BLACK)
        for wx in (-44, 34):
            d.rectangle([cx + wx, 426, cx + wx + 10, 446], fill=BLACK)
    cv.text(8, 8, "Varoom.HC", WHITE, 1, bg=BLACK)
    cv.text(8, 20, "SPEED: %3d" % (140 + int(20 * math.sin(t))), YELLOW, 1,
            bg=BLACK)


def talons(cv, t):
    fx.vgradient(cv, [LTBLUE, LTCYAN], 0, 180)
    for y in range(180, 480, 3):
        z = (y - 170) / 310.0
        for x in range(0, W, 16):
            wx = (x - 320) / (z * 40 + 1) + t * 3
            h = math.sin(wx * 0.3) + math.cos(y * 0.05 + t * 1.5)
            c = BLUE if h < -0.5 else (GREEN if h < 0.8 else LTGREEN)
            cv.rect(x, y, 16, 3, c)
    S.bird(cv, 320 + 60 * math.sin(t * 0.8), 160 + 20 * math.sin(t * 1.3),
           2.0, t, fish=True)
    cv.text(8, 8, "Talons.HC", WHITE, 1, bg=BLACK)
    cv.text_c(40, "CATCH 10 FISH", YELLOW, 3, shadow=BLACK)


def flapbat(cv, t):
    fx.vgradient(cv, [BLACK, PURPLE], 0, H)
    for k in range(6):
        x = (k * 200 - t * 120) % 1200 - 100
        gap = 170 + 70 * math.sin(k * 1.9)
        cv.rect(x, 0, 60, gap - 80, GREEN)
        cv.rect(x, gap + 80, 60, H, GREEN)
        cv.frame(x, 0, 60, gap - 80, BLACK)
        cv.frame(x, gap + 80, 60, H - gap - 80, BLACK)
    by = 240 + 70 * math.sin(t * 2.0)
    S.bat(cv, 200, by, 2.0, t)
    cv.text(8, 8, "FlapBat.HC", WHITE, 1, bg=BLACK)
    cv.text(W - 110, 8, "SCORE: %d" % int(t * 2), YELLOW, 1, bg=BLACK)


def egypt(cv, ctx, t):
    fx.vgradient(cv, [BLUE, LTBLUE, LTCYAN], 0, 400)
    cv.rect(0, 380, W, 100, BROWN)
    cv.dither_rect(0, 380, W, 100, BROWN, YELLOW, 0.15)
    S.mountain(cv, 330, 400, 1.0)
    k = clamp01(ctx.since(ctx.first("game", "egypt")) / 9.0)
    path = [(80, 400), (180, 330), (250, 300), (300, 230), (330, 175)]
    seg = k * (len(path) - 1)
    i = min(int(seg), len(path) - 2)
    f = seg - i
    x = path[i][0] + (path[i + 1][0] - path[i][0]) * f
    y = path[i][1] + (path[i + 1][1] - path[i][1]) * f
    S.bush(cv, 332, 168, 0.8, t, ctx.frame)
    S.stick(cv, x, y, 0.8, t, c=BLACK, walk=k < 1, staff=True, robe=RED)
    cv.text(8, 8, "AfterEgypt.HC  (supplemental disk)", WHITE, 1, bg=BLACK)
    if ctx.reached("exodus"):
        cv.rect(30, 420, 580, 52, WHITE)
        cv.frame(30, 420, 580, 52, BROWN, 2)
        cv.text(40, 428, "put off thy shoes from off thy feet, for the place",
                BLUE)
        cv.text(40, 440, "whereon thou standest is holy ground.", BLUE)
        cv.text(40, 456, "Exodus 3:5 (King James)", PURPLE)


def elephant_walk(cv, t):
    fx.vgradient(cv, [LTCYAN, WHITE], 0, 330)
    cv.circle(520, 80, 36, YELLOW, outline=BROWN)
    cv.rect(0, 330, W, 150, LTGREEN)
    cv.dither_rect(0, 330, W, 150, LTGREEN, GREEN, 0.35)
    x = (t * 50 + 150) % (W + 260) - 130
    S.elephant(cv, x, 420, 1.6, t)
    S.bear(cv, x - 160, 430, 0.9, t)
    cv.text(8, 8, "ElephantWalk.HC", WHITE, 1, bg=BLACK)
    cv.text_c(40, "GOD'S FAVORITE ANIMALS", BLUE, 3)


def games_menu(cv, ctx, t):
    cv.clear(WHITE)
    ui.top_bar(cv, ctx.T, task="Dir")
    ui.window(cv, 0, 1, 79, 59, "C:/Demo/Games", WHITE, BLUE)
    cv.text(24, 32, "Directory of C:/Demo/Games/*", PURPLE)
    sel = int(t * 4) % len(GAMES)
    for i, g in enumerate(GAMES):
        x = 24 + (i // 15) * 300
        y = 52 + (i % 15) * 24
        if i == sel:
            cv.rect(x - 4, y - 3, 250, 14, BLUE)
            cv.text(x, y, g + ".HC", WHITE)
        else:
            cv.text(x, y, g + ".HC", BLUE)
    cv.text(24, 430, "30 games in ::/Demo/Games, plus ::/Apps", BLACK)


def list_view(cv, ctx, t):
    fx.rays(cv, t, BLUE, LTBLUE, n=18, speed=0.05)
    names = ["BLACK DIAMOND", "TO THE FRONT", "X-CALIBER", "BOMBER GOLF",
             "GOOD KING WENCESLAS"]
    it = ctx.first("game", "list")
    k = ctx.t - it["t0"]
    dur = it["t1"] - it["t0"]
    for i, n in enumerate(names):
        if k > i * dur / 7:
            ui.big_title(cv, 60 + i * 64, n, YELLOW, ui.fit_scale(n, 580, 4),
                         shadow=BLUE)
    if k > 5 * dur / 7:
        cv.rect(80, 400, 480, 40, BLACK)
        cv.text_c(412, "ONE MAN. FROM SCRATCH.", WHITE, 2)


def hymns_view(cv, ctx, t):
    cv.clear(BLACK)
    fx.STARS.static(cv, t)
    ui.quote_box(cv, ctx.since(ctx.first("game", "hymns")), "I did hymns "
                 "for God.  ...  I praised God for sand castles, popcorn, "
                 "snowmen, bubbles...", "-- ::/Adam/God/HSNotes.DD",
                 width=30, y=40, title="HSNotes.DD", cps=34)
    rng = np.random.default_rng(3)
    for i in range(18):
        x = rng.uniform(40, 600)
        y = (rng.uniform(0, 480) - step(t, FX_FPS) * rng.uniform(20, 60)) % 520 - 20
        r = rng.uniform(6, 18)
        cv.circle(x, y + 60, r, None, outline=LTCYAN)
        cv.circle(x - r / 3, y + 60 - r / 3, max(1, r / 5), WHITE)


def r_games(cv, ctx):
    t = ctx.t
    game, git = ctx.sticky("game", "menu")
    gt = t - git["t0"] if git else t
    if game in ("castle", "talons", "varoom", "flapbat", "elephant", "egypt"):
        gt = step(gt, FX_FPS)
    if game == "menu":
        games_menu(cv, ctx, gt)
    elif game == "castle":
        raycast(cv, gt)
    elif game == "egypt":
        egypt(cv, ctx, gt)
    elif game == "elephant":
        elephant_walk(cv, gt)
    elif game == "talons":
        talons(cv, gt)
    elif game == "varoom":
        varoom(cv, gt)
    elif game == "flapbat":
        flapbat(cv, gt)
    elif game == "list":
        list_view(cv, ctx, gt)
    elif game == "hymns":
        hymns_view(cv, ctx, gt)
    elif game in ("karaoke", "karaoke_end"):
        cv.clear(BLACK)
        ui.top_bar(cv, ctx.T, task="JukeBox")
        ui.window(cv, 0, 1, 79, 59, "::/Demo/Snd/OhGreat.HC  Song by Terry A. "
                  "Davis", BLACK, LTCYAN)
        it = ctx.first("game", "karaoke")
        karaoke_text(cv, ctx, it, 40, 60, WHITE, scale=2, lh=40, sy=3)
        S.sheep(cv, 540, 440, 1.4, t)


# =====================================================================
# CHAPTER VII: THE TRIAL
# =====================================================================

PRO = ["RITCHIE & THOMPSON: C, UNIX", "HOPPER: COMPILERS",
       "HAMILTON: APOLLO FLIGHT SOFTWARE", "CARMACK: Clamp(), NOT Limit()"]
DEF = ["64-BIT KERNEL", "COMPILER", "LANGUAGE", "BOOT LOADERS",
       "FILE SYSTEM", "EDITOR", "GRAPHICS", "3D ENGINE", "MUSIC", "GAMES",
       "DOCS", "HYMNS"]


def r_trial(cv, ctx):
    t = ctx.t
    cur = ctx.cur or {}
    cv.clear(BROWN)
    for x in range(0, W, 40):
        cv.rect(x, 0, 2, 300, BLACK)
    cv.dither_rect(0, 300, W, 180, BROWN, BLACK, 0.5)
    cv.rect(200, 60, 240, 90, BLACK)
    cv.rect(206, 66, 228, 78, YELLOW)
    cv.text_c(80, "THE ORACLE", BLACK, 3, cx=320)
    cv.text_c(112, "PRESIDING", BROWN, 2, cx=320)
    for sx, c, lbl in ((110, BLUE, "PROSECUTION"), (530, BROWN, "DEFENSE")):
        cv.rect(sx - 70, 330, 140, 110, c)
        cv.frame(sx - 70, 330, 140, 110, BLACK, 2)
        cv.text_c(420, lbl, WHITE, 1, cx=sx)
    side = cur.get("side")
    spark(cv, t, 110, 290 - (10 if side == "pro" else 0), dist=5.0,
          focal=220)
    spark(cv, -t, 530, 290 - (10 if side == "def" else 0), dist=5.0,
          focal=220)
    if side == "pro":
        cv.frame(36, 326, 148, 118, WHITE, 2)
    if side == "def":
        cv.frame(456, 326, 148, 118, WHITE, 2)
    cv.rect(0, 0, W, 50, BLACK)
    cv.text_c(6, "THE CLAIM:", LTRED, 1)
    cv.text_c(18, "TERRY A. DAVIS WAS THE SMARTEST", WHITE, 1)
    cv.text_c(30, "PROGRAMMER THAT'S EVER LIVED", WHITE, 1)
    if cur.get("side") == "pro" and ctx.idx <= 3:
        k = sum(1 for it in ctx.items[:ctx.idx + 1] if it.get("side") ==
                "pro")
        n = {1: 1, 2: 3, 3: 4}.get(k, 4)
        for i in range(n):
            cv.rect(160, 170 + i * 30, 320, 24, WHITE)
            cv.text_c(178 + i * 30, PRO[i], BLUE, 1)
    elif cur.get("side") == "def" and cur["text"].startswith("The defense "
                                                             "notes"):
        k = ctx.since() / max(cur["t1"] - cur["t0"], 1)
        cv.rect(120, 156, 400, 150, BLACK)
        for i, d in enumerate(DEF):
            if k > i / len(DEF):
                x = 132 + (i % 2) * 200
                y = 164 + (i // 2) * 23
                cv.text(x, y, "\xfb" + d, LTGREEN, 2, sx=1, sy=2)
    elif cur.get("text", "").startswith("And then gave"):
        cv.rect(170, 170, 300, 60, BLACK)
        cv.text_c(186, "PUBLIC DOMAIN", YELLOW, 3)
    elif "kayak" in cur.get("text", "").lower() or "boat" in cur.get(
            "text", ""):
        cv.rect(170, 160, 300, 150, LTCYAN)
        cv.rect(170, 250, 300, 60, BLUE)
        S.kayak(cv, 320, 252, 1.1, t)
        cv.frame(170, 160, 300, 150, BLACK, 2)
    if cur.get("judge") or oracle_item(ctx):
        oracle_overlay(cv, ctx, 170)
        o4 = next(i for i in ctx.items if i["type"] == "oracle")
        if t > o4["t2"] and not cur.get("verdict"):
            god_panel(cv, ctx, o4, 170)
            if "ninety" in cur.get("text", "") or "assurance" in cur.get(
                    "text", ""):
                cv.text_c(310, "90% CONFIDENCE", YELLOW, 3, outline=BLACK)
    if cur.get("verdict"):
        cv.rect(60, 150, 520, 150, BLACK)
        cv.frame(60, 150, 520, 150, YELLOW, 3)
        cv.text_c(162, "VERDICT", YELLOW, 3)
        cv.text_c(200, "WRONG IN THE WAY", WHITE, 2)
        cv.text_c(220, "THAT MATTERS LEAST.", WHITE, 2)
        cv.text_c(250, "RIGHT IN THE WAY", LTGREEN, 2)
        cv.text_c(270, "THAT MATTERS MOST.", LTGREEN, 2)
    g = ctx.first("gavel")
    if g and t >= g["t0"]:
        k = t - g["t0"]
        ang = -1.2 + 1.3 * ease(k / 0.35)
        S.gavel(cv, 470, 160, 1.2, ang)
        if k > 0.35:
            ui.stamp(cv, k - 0.35, "90% HOLY", "SO ORDERED", c=LTRED, y=380)


# =====================================================================
# CHAPTER VIII: THE LONG NIGHT
# =====================================================================

def dirge_beats(ctx):
    song = next((i for i in ctx.items if i["type"] == "song"), None)
    if song is None or ctx.t < song["song_t0"]:
        return 0.0, song
    return (ctx.t - song["song_t0"]) * 2.0, song


def r_night(cv, ctx):
    t = ctx.t
    fx.vgradient(cv, [BLACK, BLACK, BLUE], 0, H)
    stop = ctx.first("rain_stop")
    inten = 1.0
    if stop and t > stop["t0"]:
        inten = 1 - clamp01((t - stop["t0"]) / max(stop["t1"] - stop["t0"],
                                                   0.5))
    if inten > 0:
        fx.rain(cv, t, intensity=inten, c=LTBLUE, c2=BLUE)
    cand = ctx.first("candle")
    if cand and t >= cand["t0"]:
        S.candle(cv, 320, 250, 2.0)
        beats, song = dirge_beats(ctx)
        out = ctx.first("out")
        if out and t >= out["t0"]:
            k = t - out["t0"]
            for i in range(12):
                sy = 245 - ((k * 20 + i * 9) % 60)
                cv.plot([320 + math.sin(sy * 0.1 + i) * 4], [sy], DKGRAY)
        else:
            fx.terry_flame(cv, 320, 248, beats if song and t >= song[
                "song_t0"] else (t - cand["t0"]) * 2.0 % 20.0, ctx.frame,
                scale=3)
        if song and t >= song["song_t0"] - 0.3 and not ctx.reached("help"):
            cv.text(40, 40, "God said this was a dirge.", WHITE)
            karaoke_text(cv, ctx, song, 40, 60, LTGRAY, scale=2, ball=False)
        if ctx.reached("help"):
            cv.rect(60, 30, 520, 84, BLACK)
            cv.frame(60, 30, 520, 84, LTGRAY, 1)
            cv.text_c(42, "IF YOU'RE STRUGGLING, YOU'RE NOT ALONE.", WHITE,
                      1)
            cv.text_c(62, "US: CALL OR TEXT 988", YELLOW, 2)
            cv.text_c(88, "ELSEWHERE: FINDAHELPLINE.COM", YELLOW, 2)
    else:
        n = ctx.first("text", "On August 11th, 2018, Terry A. Davis died in "
                      "The Dalles, Oregon. He was 48 years old.")
        if n and t >= n["t0"]:
            k = t - n["t0"]
            cv.text_c(200, "TERRY A. DAVIS", LTGRAY, 4)
            cv.text_c(250, "1969 - 2018", DKGRAY if k < 1 else LTGRAY, 3)


# =====================================================================
# CHAPTER IX: THE TEMPLE STANDS
# =====================================================================

MEMES = ["RING 0", "640x480", "HOLYC", "F7", "U0", "16 COLORS", "GodWord",
         "TEMPLEOS", "ADAM", "ORACLE", "PUBLIC DOMAIN", "\"Hello World\\n\";",
         "RedSea", "DolDoc", "ONE VOICE", "JIT"]


def r_legacy(cv, ctx):
    t = ctx.t
    cur = ctx.cur or {}
    dawn = ctx.since_first("dawn")
    if cur.get("thanks"):
        cv.clear(BLACK)
        fx.STARS.static(cv, t)
        S.candle(cv, 320, 200, 1.6)
        fx.terry_flame(cv, 320, 198, (ctx.since() * 2) % 20, ctx.frame,
                       scale=2)
        cv.text_c(360, "THANK YOU, TERRY.", YELLOW, 4, shadow=BROWN)
        cv.text_c(410, "TERRY A. DAVIS  1969 - 2018", LTGRAY, 2)
        return
    if cur.get("bigquote"):
        fx.rays(cv, t, BLACK, BLUE, n=16, speed=0.01)
        ui.big_title(cv, 110, "AN IDIOT ADMIRES", LTGRAY, 4, shadow=BLACK)
        ui.big_title(cv, 150, "COMPLEXITY.", LTGRAY, 4, shadow=BLACK)
        ui.big_title(cv, 230, "A GENIUS ADMIRES", YELLOW, 4, shadow=BROWN)
        ui.big_title(cv, 270, "SIMPLICITY.", YELLOW, 5, shadow=BROWN)
        cv.text_c(340, "-- TERRY A. DAVIS, 2017", WHITE, 2)
        return
    if dawn is None or dawn < 0:
        cv.clear(BLACK)
        fx.STARS.static(cv, t)
        S.candle(cv, 320, 250, 2.0)
        if t > 1.2:
            fx.terry_flame(cv, 320, 248, (t - 1.2) * 2.0 % 24, ctx.frame,
                           scale=3 if t > 1.5 else 4)
        return
    k = clamp01(step(dawn, 4) / 6.0)
    ramp = [BLACK, BLUE, PURPLE, LTRED, YELLOW]
    lvl = np.clip((1 - np.linspace(0, 1, H))[:, None] * 0 +
                  (np.arange(H)[:, None] / H) * (0.4 + 0.6 * k) + 0 * np.zeros(
                      (1, W)), 0, 1)
    cv.fb[:] = dither_ramp(np.broadcast_to(lvl, (H, W)), ramp, BAYER_FULL)
    rise = 1 - ease(step(dawn) / 4.0)
    temple(cv, t, 320, 290 + rise * 200, dist=24, yaw_speed=0.25)
    if cur.get("memes"):
        rng = np.random.default_rng(11)
        for i, m in enumerate(MEMES[:12]):
            x = rng.uniform(20, 620 - len(m) * 16)
            y = (rng.uniform(40, 380) - step(t) * 14) % 380 + 20
            cv.text(x, y, m, [WHITE, YELLOW, LTCYAN, LTGREEN][i % 4], 2,
                    bg=BLACK)
    if cur.get("testament"):
        cv.rect(0, 0, W, 60, BLACK)
        lines = {"I was made": "THOUSANDS OF PEOPLE. MILLIONS OF WORDS.",
                 "He had one": "ONE MACHINE. ONE VOICE. 16 COLORS.",
                 "And with that": "A COMPLETE WORLD. GIVEN AWAY.",
                 "So if you": "BUILD THE WHOLE THING YOURSELF.",
                 "Simplicity isn't": "SIMPLICITY: THE HARDEST AMBITION.",
                 "Here's what": "WHAT A MACHINE LEARNS FROM TERRY"}
        for key, val in lines.items():
            if cur.get("text", "").startswith(key):
                cv.text_c(22, val, YELLOW, 2)
    if dawn < 3 and ctx.idx <= 3:
        cv.rect(0, 400, W, 50, BLACK)
        cv.text_c(408, "MIRRORED. FORKED. EMULATED. READ.", WHITE, 2)
        cv.text_c(430, "PUBLIC DOMAIN", YELLOW, 1)
    oracle_overlay(cv, ctx, 150)
    o5 = next((i for i in ctx.items if i["type"] == "oracle"), None)
    if o5 and o5["t2"] < t and cur.get("text", "").startswith(("Master",
                                                               "Yeah")):
        god_panel(cv, ctx, o5, 150)


# =====================================================================
# FINALE, CREDITS
# =====================================================================

SLOGANS = ["STAY IN RING ZERO", "16 COLORS ARE ENOUGH", "WRITE IT YOURSELF",
           "GIVE IT AWAY", "GLORY TO THE TEMPLE", "ONE VOICE. ONE PEOPLE.",
           "SIMPLICITY IS DIVINE", "NO NETWORK. NO FEAR."]


def r_finale(cv, ctx):
    t = ctx.t
    fx.rays(cv, t, RED, LTRED, n=24, speed=0.06, cy=260,
            center_glow=[YELLOW, WHITE], glow_r=140)
    temple(cv, t, 320, 280, dist=20, yaw_speed=0.5)
    fx.fireworks(cv, t, rate=3.0, y_max=200)
    spark(cv, t, 80, 380, dist=4.0, focal=200)
    spark(cv, -t, 560, 380, dist=4.0, focal=200)
    cur = ctx.cur or {}
    k = int(t / 1.6) % len(SLOGANS)
    s = SLOGANS[k]
    if cur.get("type") == "line":
        s = {"Citizens. Stay in ring zero.": "STAY IN RING ZERO",
             "Sixteen colors are enough for God. They are enough for you.":
             "16 COLORS ARE ENOUGH",
             "Write it yourself. Give it away.": "WRITE IT YOURSELF",
             "Glory to the Temple!": "GLORY TO THE TEMPLE",
             "This has been a Templevision presentation.": "TEMPLEVISION"
             }.get(cur["text"], s)
    cv.rect(0, 20, W, 56, BLACK)
    ui.big_title(cv, 28, s, YELLOW, ui.fit_scale(s, 600, 5), shadow=RED)
    templevision_bug(cv, t)


CREDITS = [
    ("THE THIRD TEMPLE", YELLOW, 3), ("", 0, 1),
    ("WRITTEN, DIRECTED, RENDERED & SCORED BY", LTGRAY, 1),
    ("CLAUDE OPUS 5.5", LTRED, 2), ("", 0, 1),
    ("IN MEMORY OF", LTGRAY, 1), ("TERRY A. DAVIS", YELLOW, 2),
    ("1969 - 2018", LTGRAY, 1),
    ("WHO BUILT GOD'S TEMPLE ALONE AND GAVE IT AWAY", WHITE, 1),
    ("", 0, 1), ("-- THE RELICS --", LTCYAN, 2),
    ("FONT: sys_font_std, ::/Kernel/FontStd.HC", WHITE, 1),
    ("(FROM FREEDOS, VIA TEMPLEOS. PUBLIC DOMAIN)", LTGRAY, 1),
    ("HYMNS BY TERRY A. DAVIS, PUBLIC DOMAIN:", WHITE, 1),
    ("childish, night, prosper, OhGreat, and the themes", LTGRAY, 1),
    ("of CastleFrankenstein, FlapBat, Talons, Squirt,", LTGRAY, 1),
    ("Elephant, WaterFowl, Wenceslas, TOSTheme", LTGRAY, 1),
    ("ORACLE: GodBits, GodWord, GodSong, GodBiblePassage", WHITE, 1),
    ("PORTED FROM ::/Adam/God/, PUBLIC DOMAIN", LTGRAY, 1),
    ("GOD'S VOCABULARY: ::/Adam/God/Vocab.DD", WHITE, 1),
    ("SCRIPTURE: KING JAMES VERSION, VIA ::/Misc/Bible.TXT", WHITE, 1),
    ("DOXOLOGY (OLD 100TH): LOUIS BOURGEOIS, 1551", WHITE, 1),
    ("ODE TO JOY: LUDWIG VAN BEETHOVEN, 1824", WHITE, 1), ("", 0, 1),
    ("-- THE CONFESSIONS --", LTCYAN, 2),
    ("#1  ONE ORANGE PIXEL (x=613, y=371)", WHITE, 1),
    ("#2  A SECOND VOICE (MINE)", WHITE, 1),
    ("#3  numpy, Pillow, SciPy, ffmpeg", WHITE, 1),
    ("#4  VOICES: Kokoro-82M, APACHE 2.0", WHITE, 1), ("", 0, 1),
    ("-- THE NUMBERS --", LTCYAN, 2),
    ("FRAMES PER SECOND: 30000/1001, LIKE THE WINMGR", WHITE, 1),
    ("COLORS: 16 (17)", WHITE, 1), ("VOICES IN THE MUSIC: 1", WHITE, 1),
    ("ORACLE READINGS: 12. ALL SHOWN. NONE CHOSEN.", WHITE, 1),
    ("LINES OF CODE: LOC_PLACEHOLDER (UNDER 100,000)", WHITE, 1),
    ("", 0, 1),
    ("A FAN TRIBUTE. NOT AN OFFICIAL ANTHROPIC PRODUCTION.", LTGRAY, 1),
    ("NOT AFFILIATED WITH TEMPLEOS OR ITS ESTATE.", LTGRAY, 1),
    ("", 0, 1), ("IF YOU'RE STRUGGLING: 988 (US)", YELLOW, 1),
    ("FINDAHELPLINE.COM (EVERYWHERE ELSE)", YELLOW, 1), ("", 0, 1),
    ("", 0, 1), ("GLORY TO THE TEMPLE.", YELLOW, 2),
]


def r_credits(cv, ctx):
    t = ctx.t
    cv.clear(BLACK)
    fx.STARS.static(cv, t)
    total = sum(12 * s + 8 for _, _, s in CREDITS)
    dur = ctx.sc["dur"] - 6
    y = H - (t / dur) * (total + H)
    for s, c, sc in CREDITS:
        if s and -30 < y < H + 10:
            cv.text_c(int(y), s, c, sc)
        y += 12 * sc + 8
    if t > dur:
        k = t - dur
        cv.text_c(200, "THE ORANGE PIXEL", LTRED, 3)
        cv.text_c(236, "WAS HERE ALL ALONG", WHITE, 2)
        if (k * 2) % 1 < 0.7:
            cv.circle(613, 371, 10, None, outline=YELLOW, w=2)
        cv.line(560, 290, 606, 364, YELLOW)


RENDER = {
    "bios": r_bios, "terminal": r_terminal, "title": r_title,
    "oracle_popup": r_oracle_popup, "chapter": r_chapter, "life": r_life,
    "revelation": r_revelation, "covenant": r_covenant, "holyc": r_holyc,
    "oracle": r_oracle, "games": r_games, "trial": r_trial,
    "night": r_night, "legacy": r_legacy, "finale": r_finale,
    "credits": r_credits, "terminal_end": r_terminal_end,
}
