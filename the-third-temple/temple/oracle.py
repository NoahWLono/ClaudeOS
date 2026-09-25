"""Terry A. Davis's oracle, ported from TempleOS (public domain).

Sources, TempleOS V5.03:
  ::/Adam/God/HolySpirit.HC   GodBitsIns, GodBits, GodWordStr, GodBiblePassage
  ::/Adam/God/GodSong.HC      GodSongStr
  ::/Adam/God/GodExt.HC       GOD_BAD_BITS=4, GOD_GOOD_BITS=24
  ::/Adam/God/Vocab.DD        God's vocabulary (7,569 words)

Terry: "The technique I use to consult the Holy Spirit is reading a
microsecond-range stop-watch each button press for random numbers.
Then, I pick words with <F7> or passages with <SHIFT-F7>."

Here a "button press" is the moment this program reads the nanosecond
clock. Run `python3 -m temple.oracle word 6` to consult; every press is
appended to data/oracle_log.json so the video uses exactly what God said.
"""
import collections
import json
import os
import sys
import time

GOD_BAD_BITS = 4
GOD_GOOD_BITS = 24

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "..", "data")
LOG_PATH = os.path.join(DATA, "oracle_log.json")

# ::/Adam/God/GodBible.HC ST_BIBLE_BOOKS / ST_BIBLE_BOOK_LINES
BIBLE_BOOKS = ["Genesis", "Exodus", "Leviticus", "Numbers", "Deuteronomy",
    "Joshua", "Judges", "Ruth", "1 Samuel", "2 Samuel", "1 Kings", "2 Kings",
    "1 Chronicles", "2 Chronicles", "Ezra", "Nehemiah", "Esther", "Job",
    "Psalms", "Proverbs", "Ecclesiastes", "Song of Songs", "Isaiah",
    "Jeremiah", "Lamentations", "Ezekiel", "Daniel", "Hosea", "Joel", "Amos",
    "Obadiah", "Jonah", "Micah", "Nahum", "Habakkuk", "Zephaniah", "Haggai",
    "Zechariah", "Malachi", "Matthew", "Mark", "Luke", "John", "Acts",
    "Romans", "1 Corinthians", "2 Corinthians", "Galatians", "Ephesians",
    "Philippians", "Colossians", "1 Thessalonians", "2 Thessalonians",
    "1 Timothy", "2 Timothy", "Titus", "Philemon", "Hebrews", "James",
    "1 Peter", "2 Peter", "1 John", "2 John", "3 John", "Jude", "Revelation"]
BIBLE_BOOK_LINES = [297, 5068, 9123, 12005, 15977, 19168, 21329, 23598,
    23902, 26892, 29345, 32241, 34961, 37633, 40756, 41671, 42963, 43605,
    46190, 53793, 56267, 56966, 57332, 61806, 66736, 67217, 71804, 73189,
    73876, 74130, 74615, 74697, 74860, 75241, 75416, 75604, 75806, 75932,
    76684, 76908, 79970, 81941, 85266, 87803, 90914, 92110, 93323, 94088,
    94514, 94869, 95153, 95402, 95647, 95772, 96090, 96320, 96440, 96500,
    97370, 97687, 97976, 98163, 98506, 98552, 98597, 98684, 100111]
ST_BIBLE_LINES = BIBLE_BOOK_LINES[-1] - 1


def load_vocab():
    """GodInit: every run of word characters in Vocab.DD is one word."""
    with open(os.path.join(DATA, "Vocab.DD"), encoding="latin-1") as f:
        words = []
        cur = []
        for ch in f.read():
            if ch.isalnum() or ch == "_":
                cur.append(ch)
            elif cur:
                words.append("".join(cur))
                cur = []
        if cur:
            words.append("".join(cur))
    return words


class God:
    def __init__(self):
        self.fifo = collections.deque()
        self.words = load_vocab()
        self.presses = []

    def pick(self):
        """GodPick: KbdMsEvtTime>>GOD_BAD_BITS, taken at the button press."""
        time.sleep(0.2)  # a human needs a moment between presses
        t = time.perf_counter_ns()
        self.presses.append(t)
        return t >> GOD_BAD_BITS

    def bits_ins(self, num_bits, n):
        for _ in range(num_bits):
            self.fifo.append(n & 1)
            n >>= 1

    def bits(self, num_bits):
        res = 0
        while num_bits:
            if self.fifo:
                res = (res << 1) + self.fifo.popleft()
                num_bits -= 1
            else:
                self.bits_ins(GOD_GOOD_BITS, self.pick())
        return res

    def word(self, bits=17):
        return self.words[self.bits(bits) % len(self.words)]

    def song_str(self, complexity=1, octave=4):
        """GodSongStr with the default form: Normal rhythm, no rests, 4/4."""
        simple = [0, 0, 0, 0, 1]
        normal = [0, 0, 1, 2, 3]
        complex_ = [0, 0, 1, 1, 4, 2, 5, 6, 3]
        buf = []
        state = {"oct": octave + 1}

        def ins_note(k):
            k //= 2
            if k < 3:
                if state["oct"] != octave:
                    state["oct"] = octave
                    buf.append(str(octave))
                buf.append("G" if not k else chr(k - 1 + ord("A")))
            else:
                if state["oct"] != octave + 1:
                    state["oct"] = octave + 1
                    buf.append(str(octave + 1))
                buf.append(chr(k - 1 + ord("A")))

        buf.append(str(state["oct"]))
        self.fifo.clear()  # FifoU8Flush(god.fifo)
        last = -1
        for _ in range(8):
            n = self.bits(8)
            dur = (complex_[n % 9] if complexity == 2 else
                   normal[n % 5] if complexity == 1 else simple[n % 5])
            if dur == 1:  # DUR_8_8
                if last != 1:
                    buf.append("e")
                ins_note(self.bits(4)); ins_note(self.bits(4))
            elif dur == 4:  # DUR_8DOT_16
                buf.append("e."); ins_note(self.bits(4))
                buf.append("s"); ins_note(self.bits(4))
                dur = 3
            elif dur == 2:  # DUR_3_3_3
                if last != 2:
                    buf.append("et")
                for _ in range(3):
                    ins_note(self.bits(4))
            elif dur == 5:  # DUR_8_16_16
                if last != 1:
                    buf.append("e")
                ins_note(self.bits(4)); buf.append("s")
                ins_note(self.bits(4)); ins_note(self.bits(4))
                dur = 3
            elif dur == 6:  # DUR_16_16_8
                if last != 3:
                    buf.append("s")
                ins_note(self.bits(4)); ins_note(self.bits(4))
                buf.append("e"); ins_note(self.bits(4))
                dur = 1
            elif dur == 3:  # DUR_16_16_16_16
                if last != 3:
                    buf.append("s")
                k, k2 = self.bits(4), self.bits(4)
                for x in (k, k2, k, k2):
                    ins_note(x)
            else:  # DUR_4
                if last != 0:
                    buf.append("q")
                ins_note(self.bits(4))
            last = dur
        return "".join(buf)

    def song(self):
        """GodSong: st1 st1 st2 st2."""
        a, b = self.song_str(), self.song_str()
        return a + a + b + b

    def bible_passage(self, bible_path, num_lines=6):
        start = self.bits(21) % (ST_BIBLE_LINES - (num_lines - 1)) + 1
        with open(bible_path, encoding="latin-1") as f:
            lines = f.read().split("\n")
        book = BIBLE_BOOKS[0]
        for name, first in zip(BIBLE_BOOKS, BIBLE_BOOK_LINES):
            if start >= first:
                book = name
        # BibleLine2Verse: first verse number at or after the start line.
        ref = ""
        for ln in lines[start - 1:start + 40]:
            tok = ln.strip().split(" ", 1)[0]
            if tok and tok[0].isdigit() and ":" in tok:
                ref = tok
                break
        body = [ln.rstrip() for ln in lines[start - 1:start - 1 + num_lines]]
        return start, "%s %s" % (book, ref), body


DOODLE_W, DOODLE_H = 640, 472   # WinMax, no border, below the menu row


def doodle(god, w=DOODLE_W, h=DOODLE_H):
    """::/Adam/God/GodDoodle.HC GodDoodleSprite: three passes of 29 red
    shapes, 6 gray flood fills, and a 7x7 majority-color smooth. Returns
    the drawing ops; render_doodle() replays them."""
    ops = []
    B = god.bits
    for _ in range(3):
        for _ in range(29):
            k = B(3)
            if k == 0:
                x = (w - 1) * B(5) / 15.5 - w / 2
                y = (h - 1) * B(5) / 15.5 - h / 2
                rx = (w - 1) * B(5) / 15.5
                ry = (h - 1) * B(5) / 15.5
                ops.append(("ellipse", x, y, rx, ry))
            elif k == 1:
                x = (w - 1) * B(5) / 15.5 - w / 2
                y = (h - 1) * B(5) / 15.5 - h / 2
                r = (w - 1) * B(5) / 15.5
                ops.append(("circle", x, y, r))
            elif k == 2:
                x1 = (w - 1) * B(5) / 15.5 - w / 2
                y1 = (h - 1) * B(5) / 15.5 - h / 2
                x2 = (w - 1) * B(5) / 15.5
                y2 = (h - 1) * B(5) / 15.5
                ops.append(("border", x1, y1, x2, y2))
            else:
                x1 = (w - 1) * B(4) / 15
                y1 = (h - 1) * B(4) / 15
                x2 = (w - 1) * B(4) / 15
                y2 = (h - 1) * B(4) / 15
                ops.append(("line", x1, y1, x2, y2))
        for _ in range(6):
            x = (w - 1) * B(5) / 31 + w / 64
            y = (h - 1) * B(5) / 31 + h / 64
            c = (0, 8, 7, 15)[B(2)]  # BLACK DKGRAY LTGRAY WHITE
            ops.append(("fill", x, y, c))
        ops.append(("smooth", 3))
    return ops


def video_pick(god, path=None):
    """Pick a video from Terry's list (Sup1Blog/YouTube.DD: title and
    serial number, one line each). ::/Demo/AcctExample/TOS/TOSExt.HC
    declares GodVideoU32(U32 rand_u32,U8 *filename), but its body is not
    on the V5.03 disks, so this uses the plainest rule: 32 bits from the
    oracle, modulo the number of videos."""
    path = path or os.path.join(DATA, "relics", "Sup1Blog", "YouTube.DD")
    with open(path, encoding="latin-1") as f:
        lines = [ln.rstrip("\r\n") for ln in f.read().split("\n")]
    while lines and lines[-1] == "":
        lines.pop()
    num = len(lines) // 2
    r = god.bits(32)
    i = r % num
    return dict(rand_u32=r, index=i, num=num, title=lines[2 * i],
                serial=lines[2 * i + 1])


def consult(kind, arg, question):
    god = God()
    entry = {"question": question, "kind": kind,
             "when": time.strftime("%Y-%m-%d %H:%M:%S")}
    if kind == "word":
        entry["words"] = [god.word() for _ in range(int(arg))]
    elif kind == "song":
        entry["song"] = god.song()
    elif kind == "passage":
        start, ref, body = god.bible_passage(arg)
        entry.update(start_line=start, ref=ref, lines=body)
    elif kind == "doodle":
        entry["ops"] = doodle(god)
    elif kind == "video":
        entry.update(video_pick(god))
    entry["presses_ns"] = god.presses
    log = []
    if os.path.exists(LOG_PATH):
        with open(LOG_PATH) as f:
            log = json.load(f)
    log.append(entry)
    with open(LOG_PATH, "w") as f:
        json.dump(log, f, indent=1)
    return entry


if __name__ == "__main__":
    kind, arg, question = sys.argv[1], sys.argv[2], " ".join(sys.argv[3:])
    e = consult(kind, arg, question)
    print(json.dumps({k: v for k, v in e.items() if k != "presses_ns"}))
