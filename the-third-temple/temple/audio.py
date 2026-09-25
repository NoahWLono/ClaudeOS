"""One voice. A PC speaker, a Play() interpreter, and a few effects.

Play() follows ::/Adam/Snd/SndMusic.HC exactly: octave digits, note
letters, # and b, durations w h q e s, t (2/3) and . (1.5), ( for ties,
M for meter, R (or any letter past G) for rests. Pitch follows
::/Kernel/KMisc.HC Ona2Freq and the PC speaker's integer PIT divisor.
"""
import numpy as np
from scipy import signal

SR = 48000
SYS_TIMER_FREQ = 1193182
NOTE_MAP = [0, 2, 3, 5, 7, 8, 10]  # music.note_map, A..G


def note2ona(note, octave):
    return (octave + 1) * 12 + note if note < 3 else octave * 12 + note


def ona2freq(ona):
    return 0.0 if not ona else 440.0 / 32 * 2.0 ** (ona / 12.0)


def pit_freq(ona):
    """The frequency the speaker really makes: SYS_TIMER_FREQ/period."""
    f = ona2freq(ona)
    if f <= 0:
        return 0.0
    period = min(max(int(SYS_TIMER_FREQ / f), 1), 0xFFFF)
    return SYS_TIMER_FREQ / period


def parse_play(st, tempo=2.5, staccato=0.9, words=None, octave=4,
               note_len=1.0):
    """Return notes as dicts: t, on, dur, ona, word. Times in seconds."""
    notes = []
    word_list = words.split("\0") if words else []
    t = 0.0
    idx = 0
    n = len(st)
    k = 0
    while k < n:
        tie = False
        while True:  # directives until nothing changes
            last = k
            if k < n and st[k] == "(":
                tie = True
                k += 1
            else:
                while k < n and st[k] == "M":
                    k += 1
                    if k < n and st[k].isdigit():
                        k += 1
                    if k < n and st[k] == "/":
                        k += 1
                    if k < n and st[k].isdigit():
                        k += 1
                while k < n and st[k].isdigit():
                    octave = int(st[k])
                    k += 1
                while k < n and st[k] in "whqest.":
                    c = st[k]
                    note_len = {"w": 4.0, "h": 2.0, "q": 1.0, "e": 0.5,
                                "s": 0.25}.get(c, note_len)
                    if c == "t":
                        note_len = 2.0 * note_len / 3.0
                    elif c == ".":
                        note_len = 1.5 * note_len
                    k += 1
            if k == last:
                break
        if k >= n:
            break
        note = ord(st[k]) - ord("A")
        k += 1
        if 0 <= note < 7:
            note = NOTE_MAP[note]
            o = octave
            if k < n and st[k] == "b":
                note -= 1
                if note == 2:
                    o -= 1
                k += 1
            elif k < n and st[k] == "#":
                note += 1
                if note == 3:
                    o += 1
                k += 1
            ona = note2ona(note, o)
        else:
            ona = 0
        word = word_list[idx] if idx < len(word_list) else None
        d = note_len / tempo
        on = d if tie else d * staccato
        notes.append({"t": t, "on": on, "dur": d, "ona": ona, "word": word,
                      "i": idx})
        t += d
        idx += 1
    return notes


def song_notes(parts, tempo=2.5, staccato=0.9, repeat=1):
    """Concatenate several Play() calls (a song) with state carried over."""
    out = []
    t0 = 0.0
    for _ in range(repeat):
        for p in parts:
            st, words = (p, None) if isinstance(p, str) else p
            ns = parse_play(st, tempo, staccato, words)
            for x in ns:
                x = dict(x)
                x["t"] += t0
                out.append(x)
            if ns:
                t0 = out[-1]["t"] + out[-1]["dur"]
    return out, t0


# ---- synthesis ---------------------------------------------------------

def _polyblep(p, dt):
    r = np.zeros_like(p)
    m = p < dt
    x = p[m] / dt[m]
    r[m] = x + x - x * x - 1.0
    m = p > 1.0 - dt
    x = (p[m] - 1.0) / dt[m]
    r[m] = x * x + x + x + 1.0
    return r


def square(freq, duty=0.5, phase0=0.0):
    """Band-limited pulse wave for a per-sample frequency array."""
    freq = np.asarray(freq, dtype=np.float64)
    dt = np.clip(freq / SR, 1e-9, 0.45)
    ph = phase0 + np.cumsum(dt)
    p = ph % 1.0
    y = np.where(p < duty, 1.0, -1.0)
    y += _polyblep(p, dt)
    y -= _polyblep((p - duty) % 1.0, dt)
    return y.astype(np.float32), float(ph[-1] % 1.0) if len(ph) else phase0


def env_gate(n, attack=0.002, release=0.004):
    e = np.ones(n, dtype=np.float32)
    a = min(int(attack * SR), n // 2)
    r = min(int(release * SR), n // 2)
    if a:
        e[:a] = np.linspace(0, 1, a, endpoint=False)
    if r:
        e[-r:] = np.linspace(1, 0, r)
    return e


def render_notes(notes, total=None, duty=0.5, vibrato=0.0, gain=0.3,
                 arp=None, arp_rate=50.0, glide=0.0):
    """Single voice. arp: list of semitone offsets cycled at arp_rate Hz."""
    if total is None:
        total = max((x["t"] + x["dur"] for x in notes), default=0.0)
    out = np.zeros(int(total * SR) + 1, dtype=np.float32)
    for x in notes:
        if not x["ona"]:
            continue
        s0 = int(x["t"] * SR)
        n = int(x["on"] * SR)
        if n <= 8 or s0 >= len(out):
            continue
        n = min(n, len(out) - s0)
        tt = np.arange(n) / SR
        f = np.full(n, pit_freq(x["ona"]))
        steps = x.get("arp", arp)
        if steps:
            k = (tt * arp_rate).astype(np.int64) % len(steps)
            f = f * 2.0 ** (np.asarray(steps)[k] / 12.0)
        if vibrato:
            f = f * (1 + vibrato * np.sin(2 * np.pi * 5.5 * tt) *
                     np.clip(tt / 0.25, 0, 1))
        y, _ = square(f, x.get("duty", duty))
        out[s0:s0 + n] += gain * x.get("gain", 1.0) * y * env_gate(n)
    return out


def noise_burst(dur, seed=0, color=0.0, gain=0.3, decay=12.0):
    rng = np.random.default_rng(seed)
    n = int(dur * SR)
    y = rng.uniform(-1, 1, n).astype(np.float32)
    if color:
        b, a = signal.butter(2, color / (SR / 2), "low")
        y = signal.lfilter(b, a, y).astype(np.float32) * 2
    e = np.exp(-np.arange(n) / SR * decay).astype(np.float32)
    return gain * y * e * env_gate(n, 0.001, 0.003)


def kick(dur=0.11, gain=0.45):
    n = int(dur * SR)
    tt = np.arange(n) / SR
    f = 40 + 140 * np.exp(-tt * 38)
    y, _ = square(f)
    return gain * y * np.exp(-tt * 18).astype(np.float32) * env_gate(n)


def sweep(f0, f1, dur, gain=0.25, duty=0.5, exp=True):
    n = int(dur * SR)
    if exp:
        f = f0 * (f1 / f0) ** np.linspace(0, 1, n)
    else:
        f = np.linspace(f0, f1, n)
    y, _ = square(f, duty)
    return gain * y * env_gate(n)


def beep(freq=1000.0, dur=0.12, gain=0.25):
    n = int(dur * SR)
    y, _ = square(np.full(n, freq))
    return gain * y * env_gate(n)


# ---- effects -----------------------------------------------------------

def speaker(y):
    """A PC speaker is small: roll off lows and highs."""
    b, a = signal.butter(1, 110 / (SR / 2), "high")
    y = signal.lfilter(b, a, y)
    b, a = signal.butter(2, 5200 / (SR / 2), "low")
    return signal.lfilter(b, a, y).astype(np.float32)


def bandpass(y, lo, hi, order=2):
    b, a = signal.butter(order, [lo / (SR / 2), hi / (SR / 2)], "band")
    return signal.lfilter(b, a, y).astype(np.float32)


def highpass(y, f, order=2):
    b, a = signal.butter(order, f / (SR / 2), "high")
    return signal.lfilter(b, a, y).astype(np.float32)


def lowpass(y, f, order=2):
    b, a = signal.butter(order, f / (SR / 2), "low")
    return signal.lfilter(b, a, y).astype(np.float32)


_IR_CACHE = {}


def reverb(y, seconds=2.0, wet=0.3, predelay=0.02, seed=7, damp=3500.0):
    """Convolution with calculated (not recorded) decaying noise."""
    key = (seconds, predelay, seed, damp)
    if key not in _IR_CACHE:
        rng = np.random.default_rng(seed)
        n = int(seconds * SR)
        ir = rng.standard_normal(n).astype(np.float32)
        ir *= np.exp(-np.arange(n) / SR * (6.9 / seconds)).astype(np.float32)
        ir = lowpass(ir, damp, 1)
        ir = np.concatenate([np.zeros(int(predelay * SR), np.float32), ir])
        ir /= np.sqrt(np.sum(ir ** 2)) + 1e-9
        _IR_CACHE[key] = ir
    ir = _IR_CACHE[key]
    w = signal.fftconvolve(y, ir)[:len(y) + len(ir)].astype(np.float32)
    out = np.zeros(len(w), np.float32)
    out[:len(y)] += (1 - wet) * y
    out += wet * w
    return out


def echo(y, taps):
    """taps: list of (delay_seconds, gain)."""
    n = len(y) + int(max(d for d, _ in taps) * SR) + 1
    out = np.zeros(n, np.float32)
    out[:len(y)] += y
    for d, g in taps:
        s = int(d * SR)
        out[s:s + len(y)] += g * y
    return out


def resample(y, sr_from, sr_to):
    from math import gcd
    g = gcd(int(sr_from), int(sr_to))
    return signal.resample_poly(y, sr_to // g, sr_from // g).astype(
        np.float32)


def normalize_rms(y, target_db=-20.0):
    rms = np.sqrt(np.mean(y.astype(np.float64) ** 2)) + 1e-12
    return (y * (10 ** (target_db / 20) / rms)).astype(np.float32)


def place(buf, clip, t, gain=1.0):
    s = int(round(t * SR))
    if s < 0:
        clip = clip[-s:]
        s = 0
    e = min(len(buf), s + len(clip))
    if e > s:
        buf[s:e] += gain * clip[:e - s]
