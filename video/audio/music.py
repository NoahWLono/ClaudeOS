#!/usr/bin/env python3
"""
Procedural soundtrack for the Arch Linux "propaganda film".

Everything is synthesized from scratch with numpy + scipy: no samples.
Notes are written as MIDI numbers / note names, chords as explicit voicings,
drums on a beat grid.  Oscillators are band-limited (additive or PolyBLEP).

API (imported by the mixer):
    TRACKS: dict[str, dict]            name -> {"bpm": float, ...}
    render_track(name, duration, sr=48000, seed=0) -> float32 (round(duration*sr), 2)

CLI:
    python3 music.py all               40 s previews -> ../assets/music/preview_<name>.wav
    python3 music.py <name> <seconds>  one render    -> ../assets/music/<name>.wav
                                       (optional 3rd arg: output path)
"""
from __future__ import annotations

import functools
import os
import sys
import time
import zlib

import numpy as np
from scipy import signal
from scipy.ndimage import minimum_filter1d, uniform_filter1d

HERE = os.path.dirname(os.path.abspath(__file__))
MUSIC_DIR = os.path.normpath(os.path.join(HERE, "..", "assets", "music"))
TWO_PI = 2.0 * np.pi
DEBUG = bool(os.environ.get("MUSIC_DEBUG"))

# =============================================================================
# basic helpers
# =============================================================================

_PC = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}


def N(name):
    """Note name -> MIDI number ('C4' = 60, 'Bb3' = 58, 'F#5' = 78)."""
    if isinstance(name, (int, np.integer)):
        return int(name)
    s = name.strip()
    pc = _PC[s[0].upper()]
    i = 1
    while i < len(s) and s[i] in "#b":
        pc += 1 if s[i] == "#" else -1
        i += 1
    return 12 * (int(s[i:]) + 1) + pc


def V(s):
    """'A3 D4 F4' -> (57, 62, 65)"""
    return tuple(N(x) for x in s.split())


def mtof(m):
    return 440.0 * 2.0 ** ((np.asarray(m, dtype=float) - 69.0) / 12.0)


def mel(s, expect=None):
    """'A4:1 D5:1.5 r:0.5' -> [(start_beat, dur_beats, midi)] (rests dropped)."""
    ev, t = [], 0.0
    for tok in s.split():
        p, d = tok.split(":")
        d = float(d)
        if p.lower() != "r":
            ev.append((t, d, N(p)))
        t += d
    if expect is not None and abs(t - expect) > 1e-6:
        raise ValueError(f"melody length {t} != {expect}: {s[:40]}...")
    return ev


def in_bar(ev, bar, bpb=4):
    """events of a phrase that start inside phrase-bar `bar`, re-based to that bar."""
    lo, hi = bar * bpb, (bar + 1) * bpb
    return [(s - lo, d, m) for (s, d, m) in ev if lo - 1e-9 <= s < hi - 1e-9]


def _rng(*key):
    return np.random.default_rng(zlib.crc32(repr(key).encode("utf8")))


def _f32(x):
    a = np.ascontiguousarray(x, dtype=np.float32)
    a.flags.writeable = False
    return a


def _frac(x):
    return x - np.floor(x)


@functools.lru_cache(maxsize=None)
def _sos(kind, f, sr, order=2):
    btype = {"low": "lowpass", "high": "highpass", "bp": "bandpass"}[kind]
    return signal.butter(order, f, btype=btype, fs=sr, output="sos")


def filt(x, kind, f, sr, order=2):
    if isinstance(f, (list, tuple)):
        f = tuple(float(v) for v in f)
    else:
        f = float(min(f, 0.45 * sr))
    return signal.sosfilt(_sos(kind, f, int(sr), int(order)), x, axis=-1)


def adsr(n, sr, a, d, s, r, gate):
    """ADSR: linear attack, exponential decay (time constant d) to s, quadratic release."""
    t = np.arange(n) / sr
    a = max(a, 1e-4)
    d = max(d, 1e-4)
    env = np.where(t < a, t / a, s + (1.0 - s) * np.exp(-(t - a) / d))
    lg = gate / a if gate < a else s + (1.0 - s) * np.exp(-(gate - a) / d)
    rel = t >= gate
    tr = (t[rel] - gate) / max(r, 1e-4)
    env[rel] = lg * np.clip(1.0 - tr, 0.0, 1.0) ** 2
    return env


def tail_fade(y, sr, sec=0.01):
    n = min(y.shape[-1], int(sec * sr))
    if n > 1:
        y[..., -n:] *= np.linspace(1.0, 0.0, n)
    return y


# =============================================================================
# oscillators
# =============================================================================

def _polyblep(t, dt):
    y = np.zeros_like(t)
    m = t < dt
    if m.any():
        x = t[m] / dt[m]
        y[m] = x + x - x * x - 1.0
    m = t > 1.0 - dt
    if m.any():
        x = (t[m] - 1.0) / dt[m]
        y[m] = x * x + x + x + 1.0
    return y


def saw_blep(ph, dt):
    return 2.0 * ph - 1.0 - _polyblep(ph, dt)


def pulse_blep(ph, dt, duty):
    """Band-limited pulse, high for a fraction `duty` of the period, zero mean."""
    return saw_blep(ph, dt) - saw_blep(_frac(ph + duty), dt)


def additive(f, sr, fc, phase0=0.0, kmax=64, mode="saw"):
    """Band-limited additive oscillator with a (time-varying) 12 dB/oct lowpass.

    f: instantaneous frequency array; fc: cutoff (scalar or array).
    mode: saw (1/k), square (odd 1/k), tri (odd 1/k^2 alternating)."""
    n = f.shape[0]
    ph = TWO_PI * np.cumsum(f) / sr + phase0
    s = np.sin(ph)
    c2 = 2.0 * np.cos(ph)
    fc_arr = np.broadcast_to(np.asarray(fc, dtype=float), (n,))
    K = int(min(kmax, (0.45 * sr) // float(f.max())))
    K = max(1, min(K, int(10.0 * float(fc_arr.max()) / float(f.min())) + 1))
    r2 = (f / fc_arr) ** 2
    out = np.zeros(n)
    sp = np.zeros(n)
    sc = s
    for k in range(1, K + 1):
        if mode == "saw":
            base = 1.0 / k
        elif mode == "square":
            base = 1.0 / k if k % 2 else 0.0
        else:  # tri
            base = ((-1.0) ** ((k - 1) // 2)) / (k * k) if k % 2 else 0.0
        if base:
            out += (base / (1.0 + (k * k) * r2)) * sc
        sp, sc = sc, c2 * sc - sp
    return out


# =============================================================================
# melodic instruments (all cached; return float32 mono (L,) or stereo (2, L))
# =============================================================================

@functools.lru_cache(maxsize=1024)
def brass(midi, dur, sr, bright=1.0, att=0.025, var=0, vib=1.0):
    """Two detuned additive saws through an enveloped lowpass (trumpet/horn/tuba)."""
    rel = 0.16
    q = 2 if sr % 2 == 0 else 1          # synthesize at sr/2 (harmonics to ~10.8 kHz), upsample
    srq = sr // q
    n_full = int((dur + rel) * sr)
    n = -(-n_full // q)
    t = np.arange(n) / srq
    f0 = float(mtof(midi))
    r = _rng("brass", midi, var)
    scoop = -0.3 * np.exp(-t / 0.035)
    vd = vib * 0.13 * np.clip((t - 0.28) / 0.35, 0.0, 1.0)
    amp = adsr(n, srq, att, 0.3, 0.72, rel, dur)
    benv = (1.0 - np.exp(-t / max(att * 0.8, 0.012))) * (0.6 + 0.4 * np.exp(-t / 0.35))
    fc = f0 * 1.3 + bright * (450.0 + 3000.0 * benv) * np.sqrt(np.clip(amp, 0, 1))
    out = np.empty((2, n))
    for v, det in enumerate((-0.07, 0.08)):
        vs = vd * np.sin(TWO_PI * (5.1 + 0.35 * v) * t + r.uniform(0, TWO_PI))
        f = f0 * 2.0 ** ((scoop + vs + det) / 12.0)
        out[v] = additive(f, srq, fc, r.uniform(0, TWO_PI), kmax=60)
    out *= amp * 0.45
    if q > 1:
        out = signal.resample_poly(out, q, 1, axis=1)[:, :n_full]
    L = 0.72 * out[0] + 0.28 * out[1]
    R = 0.28 * out[0] + 0.72 * out[1]
    return _f32(np.stack([L, R]))


@functools.lru_cache(maxsize=1024)
def saw_pad(midi, dur, sr, fc=1500.0, att=0.5, rel=1.0, voices=3, detune=0.12, var=0,
            sus=0.85, dec=0.6):
    """Detuned PolyBLEP saws, static lowpass, stereo (strings / pads / supersaw)."""
    n = int((dur + rel) * sr)
    t = np.arange(n) / sr
    f0 = float(mtof(midi))
    r = _rng("pad", midi, var, voices)
    out = np.zeros((2, n))
    for v in range(voices):
        det = 0.0 if voices == 1 else detune * (2.0 * v / (voices - 1) - 1.0)
        drift = 0.03 * np.sin(TWO_PI * r.uniform(0.15, 0.4) * t + r.uniform(0, TWO_PI))
        f = f0 * 2.0 ** ((det + drift) / 12.0)
        dt = f / sr
        ph = _frac(np.cumsum(dt) + r.uniform())
        x = saw_blep(ph, dt)
        if voices == 1:
            out += x
        elif v == voices // 2 and voices % 2 == 1:
            out += 0.7 * x
        else:
            out[v % 2] += x
    out = filt(out, "low", fc, sr, 2)
    out *= adsr(n, sr, att, dec, sus, rel, dur) * (0.55 / np.sqrt(max(1, voices / 2)))
    return _f32(out)


VOWELS = {
    "a": ((700, 1100, 2600, 3300), (100, 110, 150, 200), (0, -6, -14, -22)),
    "o": ((450, 800, 2600, 3300), (80, 90, 140, 200), (0, -8, -24, -30)),
    "u": ((330, 720, 2500), (70, 90, 150), (0, -14, -30)),
    "e": ((420, 1800, 2600, 3300), (70, 100, 140, 200), (0, -10, -12, -20)),
    "reed": ((480, 1150, 2500), (140, 220, 320), (0, -5, -16)),
}


@functools.lru_cache(maxsize=1024)
def voice(midi, dur, sr, vowel="a", voices=3, att=0.3, rel=0.6, vib=0.15, var=0,
          spread=0.1, dec=0.4, sus=0.9):
    """Formant-filtered additive saws: choir 'aah', vocal chops, bassoon-ish reed."""
    n_full = int((dur + rel) * sr)
    q = 4 if sr % 4 == 0 else 1          # content < 5.4 kHz: synthesize at sr/4, then upsample
    srq = sr // q
    n = -(-n_full // q)
    t = np.arange(n) / srq
    f0 = float(mtof(midi))
    F, BW, G = VOWELS[vowel]
    K = max(1, min(int(0.45 * srq / (f0 * 1.03)), int(5200.0 / f0) + 1))
    k = np.arange(1, K + 1)
    fk = k * f0
    resp = 0.06 + sum(10 ** (g / 20.0) / np.sqrt(1.0 + ((fk - Fi) / (bw / 2.0)) ** 2)
                      for Fi, bw, g in zip(F, BW, G))
    amps = resp / k
    amps /= np.sqrt(np.sum(amps ** 2))
    r = _rng("voice", midi, var, vowel)
    out = np.zeros((2, n))
    for v in range(voices):
        jit = 0.04 * (np.sin(TWO_PI * r.uniform(0.5, 0.9) * t + r.uniform(0, 6))
                      + np.sin(TWO_PI * r.uniform(1.1, 1.7) * t + r.uniform(0, 6)))
        vs = vib * np.sin(TWO_PI * (4.9 + 0.3 * v) * t + r.uniform(0, TWO_PI)) * np.clip(t / 0.5, 0, 1)
        det = 0.0 if voices == 1 else spread * (2.0 * v / (voices - 1) - 1.0)
        f = f0 * 2.0 ** ((vs + det + jit) / 12.0)
        ph = TWO_PI * np.cumsum(f) / srq + r.uniform(0, TWO_PI)
        s = np.sin(ph)
        c2 = 2.0 * np.cos(ph)
        sp = np.zeros(n)
        sc = s
        y = np.zeros(n)
        for kk in range(K):
            y += amps[kk] * sc
            sp, sc = sc, c2 * sc - sp
        if voices == 1:
            out += y
        else:
            p = 2.0 * v / (voices - 1) - 1.0
            out[0] += y * (0.5 - 0.35 * p)
            out[1] += y * (0.5 + 0.35 * p)
    out *= adsr(n, srq, att, dec, sus, rel, dur) * (0.8 / np.sqrt(voices))
    if q > 1:
        out = signal.resample_poly(out, q, 1, axis=1)[:, :n_full]
        out = tail_fade(out, sr, 0.005)
    return _f32(out)


@functools.lru_cache(maxsize=2048)
def pluck(midi, dur, sr, bright=1.0, decay=0.8, pos=0.2, var=0, mute=0.05):
    """Additive plucked string: pluck-position comb, faster decay for upper partials."""
    f0 = float(mtof(midi))
    ring = min(dur, decay * 4.0)
    n = int((ring + mute + 0.005) * sr)
    t = np.arange(n) / sr
    K = max(1, min(int(0.45 * sr / f0), int(bright * 6000.0 / f0) + 1, 48))
    r = _rng("pluck", midi, var)
    ph = TWO_PI * f0 * t + r.uniform(0, TWO_PI)
    s = np.sin(ph)
    c2 = 2.0 * np.cos(ph)
    sp = np.zeros(n)
    sc = s
    y = np.zeros(n)
    for k in range(1, K + 1):
        a = abs(np.sin(np.pi * k * pos)) / k
        rate = (1.0 + (k * f0 / (1200.0 * bright)) ** 1.5) / decay
        y += a * np.exp(-rate * t) * sc
        sp, sc = sc, c2 * sc - sp
    g = np.ones(n)
    m = t >= ring
    g[m] = np.clip(1.0 - (t[m] - ring) / mute, 0, 1) ** 2
    y *= g
    nz = filt(r.standard_normal(n), "bp", (1500.0, min(9000.0, 0.45 * sr)), sr, 1)
    y += 0.15 * bright * nz * np.exp(-t / 0.003)
    y *= 1.0 - np.exp(-t / 0.0006)
    return _f32(y * 0.9)


@functools.lru_cache(maxsize=1024)
def epiano(midi, dur, sr, var=0, bright=1.0, rel=0.3):
    """1:1 FM electric piano with decaying index."""
    f0 = float(mtof(midi))
    tau = float(np.clip(1.8 * (262.0 / f0) ** 0.5, 0.5, 3.5))
    hold = min(dur, tau * 3.0)
    n = int((hold + rel) * sr)
    t = np.arange(n) / sr
    r = _rng("ep", midi, var)
    I = bright * (1.2 * np.exp(-t / 0.12) + 0.4 * np.exp(-t / (tau * 0.6)))
    ph = TWO_PI * f0 * t + r.uniform(0, TWO_PI)
    y = np.sin(ph + I * np.sin(ph)) + 0.12 * np.exp(-t / 0.3) * np.sin(2.0 * ph)
    env = np.exp(-t / tau) * (1.0 - np.exp(-t / 0.0015))
    m = t >= hold
    env[m] *= np.clip(1.0 - (t[m] - hold) / rel, 0, 1) ** 2
    return _f32(y * env * 0.6)


@functools.lru_cache(maxsize=1024)
def fm_bell(midi, dur, sr, ratio=3.5, index=2.2, decay=1.2, var=0):
    """Inharmonic 2-operator FM bell; index capped so sidebands stay below Nyquist."""
    f0 = float(mtof(midi))
    fm = f0 * ratio
    idx = min(index, max(0.0, (0.45 * sr - f0) / fm - 1.5))
    n = int(min(decay * 5.0, dur + decay * 2.5) * sr)
    t = np.arange(n) / sr
    r = _rng("bell", midi, var)
    I = idx * np.exp(-t / (decay * 0.3))
    y = np.sin(TWO_PI * f0 * t + I * np.sin(TWO_PI * fm * t + r.uniform(0, 6))) * np.exp(-t / decay)
    if 2 * f0 < 0.45 * sr:
        y += 0.25 * np.sin(TWO_PI * 2.0 * f0 * t) * np.exp(-t / (decay * 0.4))
    y *= 1.0 - np.exp(-t / 0.0008)
    return _f32(tail_fade(y * 0.6, sr, 0.03))


_MALLETS = {
    "marimba": ([(1.0, 1.0, 1.0), (3.99, 0.28, 0.22), (9.9, 0.08, 0.07)], 0.9),
    "glock": ([(1.0, 1.0, 1.0), (2.76, 0.35, 0.35), (5.40, 0.18, 0.15), (8.93, 0.08, 0.08)], 1.4),
    "vibe": ([(1.0, 1.0, 1.0), (4.0, 0.22, 0.3), (10.0, 0.05, 0.1)], 2.2),
}


@functools.lru_cache(maxsize=1024)
def mallet(midi, sr, kind="marimba", decay=0.0, var=0, bright=1.0):
    """Modal bar percussion (marimba / glockenspiel / vibraphone)."""
    parts, dec0 = _MALLETS[kind]
    f0 = float(mtof(midi))
    dec = decay or (float(np.clip(dec0 * (220.0 / f0) ** 0.5, 0.25, 1.6)) if kind == "marimba" else dec0)
    n = int(dec * 3.6 * sr)
    t = np.arange(n) / sr
    r = _rng("mallet", midi, var, kind)
    y = np.zeros(n)
    for ratio, a, d in parts:
        f = f0 * ratio
        if f < 0.45 * sr:
            aa = a * (bright if ratio > 1 else 1.0)
            y += aa * np.exp(-t / (dec * d)) * np.sin(TWO_PI * f * t + r.uniform(0, 6))
    if kind == "vibe":
        y *= 1.0 - 0.25 * (0.5 - 0.5 * np.cos(TWO_PI * 5.5 * t))
    nz = filt(r.standard_normal(n), "low", 3000.0, sr, 1)
    y += 0.08 * bright * nz * np.exp(-t / 0.0015)
    y *= 1.0 - np.exp(-t / 0.0005)
    return _f32(tail_fade(y * 0.55, sr, 0.25 * dec))


@functools.lru_cache(maxsize=2048)
def chip_pulse(midi, dur, sr, duty=0.25, vib=0.0, att=0.003, dec=0.12, sus=0.65, rel=0.03,
               pwm=0.0, bend=0.0, var=0, vib_delay=0.15):
    """NES-style PolyBLEP pulse with duty cycle, optional PWM, vibrato and pitch bend."""
    f0 = float(mtof(midi))
    n = int((dur + rel) * sr)
    t = np.arange(n) / sr
    semis = bend * np.exp(-t / 0.025)
    if vib:
        semis = semis + vib * np.sin(TWO_PI * 5.8 * t) * np.clip((t - vib_delay) / 0.12, 0, 1)
    f = f0 * 2.0 ** (semis / 12.0)
    dt = f / sr
    ph = _frac(np.cumsum(dt) + _rng("cp", midi, var).uniform())
    if pwm:
        d = duty + pwm * (0.5 - duty) * (0.5 - 0.5 * np.cos(TWO_PI * 1.7 * t))
    else:
        d = np.full(n, duty)
    y = pulse_blep(ph, dt, d) * 0.5
    y *= adsr(n, sr, att, dec, sus, rel, dur)
    return _f32(y)


@functools.lru_cache(maxsize=512)
def chip_arp(notes, dur, sr, rate=50.0, duty=0.125, att=0.002, dec=0.25, sus=0.45, rel=0.03):
    """Frame-rate chord arpeggio (the classic chiptune 'chord')."""
    n = int((dur + rel) * sr)
    t = np.arange(n) / sr
    idx = np.floor(t * rate).astype(int) % len(notes)
    f = mtof(np.array(notes))[idx]
    dt = f / sr
    ph = _frac(np.cumsum(dt))
    y = pulse_blep(ph, dt, np.full(n, duty)) * 0.5
    y *= adsr(n, sr, att, dec, sus, rel, dur)
    return _f32(y)


@functools.lru_cache(maxsize=1024)
def chip_tri(midi, dur, sr, quant=True, rel=0.012, bend=0.0):
    """NES-ish triangle (optionally 4-bit stepped)."""
    f0 = float(mtof(midi))
    n = int((dur + rel) * sr)
    t = np.arange(n) / sr
    f = f0 * 2.0 ** (bend * np.exp(-t / 0.03) / 12.0)
    ph = _frac(np.cumsum(f) / sr + 0.25)
    y = 4.0 * np.abs(ph - 0.5) - 1.0
    if quant:
        y = np.round(y * 7.5) / 7.5
    y = filt(y, "low", 9000.0, sr, 1)
    env = np.clip(t / 0.002, 0, 1)
    m = t >= dur
    env[m] = np.clip(1.0 - (t[m] - dur) / rel, 0, 1)
    return _f32(y * env * 0.7)


@functools.lru_cache(maxsize=2)
def _lfsr(short):
    reg, n = 1, (93 if short else 32767)
    out = np.empty(n, np.float64)
    tap = 6 if short else 1
    for i in range(n):
        fb = (reg ^ (reg >> tap)) & 1
        reg = (reg >> 1) | (fb << 14)
        out[i] = reg & 1
    return out * 2.0 - 1.0


@functools.lru_cache(maxsize=256)
def chip_noise(dur, sr, clock=16000.0, short=False, decay=0.05, var=0, drop=0.0):
    """NES noise channel: 15-bit LFSR clocked at `clock` Hz, exponential decay."""
    seq = _lfsr(short)
    n = int(dur * sr)
    t = np.arange(n) / sr
    clk = clock * (1.0 + drop * np.exp(-t / 0.02))
    idx = (np.floor(np.cumsum(clk) / sr).astype(np.int64) + 977 * var) % len(seq)
    y = seq[idx] * np.exp(-t / decay) * (1.0 - np.exp(-t / 0.0005))
    return _f32(tail_fade(y * 0.5, sr, 0.005))


@functools.lru_cache(maxsize=1024)
def soft_lead(midi, dur, sr, mode="square", fc=2200.0, att=0.02, rel=0.15, vib=0.12, var=0,
              dec=0.5, sus=0.75):
    """Gentle additive square/triangle lead with lowpass and delayed vibrato."""
    f0 = float(mtof(midi))
    n = int((dur + rel) * sr)
    t = np.arange(n) / sr
    r = _rng("lead", midi, var)
    vs = vib * np.sin(TWO_PI * 5.3 * t + r.uniform(0, 6)) * np.clip((t - 0.25) / 0.3, 0, 1)
    f = f0 * 2.0 ** (vs / 12.0)
    y = additive(f, sr, fc, r.uniform(0, 6), kmax=40, mode=mode)
    y *= adsr(n, sr, att, dec, sus, rel, dur)
    return _f32(y * (0.9 if mode == "square" else 1.1))


@functools.lru_cache(maxsize=1024)
def flute(midi, dur, sr, att=0.08, rel=0.25, vib=0.14, var=0, breath=0.05):
    """Soft sine-based flute/ocarina with breath noise."""
    f0 = float(mtof(midi))
    n = int((dur + rel) * sr)
    t = np.arange(n) / sr
    r = _rng("flute", midi, var)
    vs = vib * np.sin(TWO_PI * 5.0 * t + r.uniform(0, 6)) * np.clip((t - 0.3) / 0.4, 0, 1)
    ph = TWO_PI * np.cumsum(f0 * 2.0 ** (vs / 12.0)) / sr
    y = np.sin(ph) + 0.18 * np.sin(2 * ph) + 0.06 * np.sin(3 * ph)
    nz = filt(r.standard_normal(n), "bp", (max(200.0, f0 * 0.8), min(0.45 * sr, f0 * 3.0)), sr, 1)
    y += breath * nz * (0.4 + np.exp(-t / 0.08))
    y *= adsr(n, sr, att, 0.6, 0.8, rel, dur)
    return _f32(y * 0.6)


@functools.lru_cache(maxsize=1024)
def sine_bass(midi, dur, sr, att=0.006, rel=0.08, harm=0.25, dec=0.6, sus=0.7):
    f0 = float(mtof(midi))
    n = int((dur + rel) * sr)
    t = np.arange(n) / sr
    ph = TWO_PI * f0 * t
    y = np.sin(ph) + harm * np.sin(2 * ph) + 0.4 * harm * np.sin(3 * ph)
    y = np.tanh(1.3 * y) / np.tanh(1.3)
    y *= adsr(n, sr, att, dec, sus, rel, dur)
    return _f32(y * 0.8)


@functools.lru_cache(maxsize=1024)
def synth_bass(midi, dur, sr, fc=300.0, env_amt=1400.0, fdec=0.09, var=0, rel=0.05, sus=0.8):
    """Additive saw bass with a filter-envelope 'pluck' (staccato pulsing bass)."""
    f0 = float(mtof(midi))
    n = int((dur + rel) * sr)
    t = np.arange(n) / sr
    fcv = fc + env_amt * np.exp(-t / fdec)
    y = additive(np.full(n, f0), sr, fcv, _rng("sb", midi, var).uniform(0, 6), kmax=48)
    y += 0.5 * np.sin(TWO_PI * f0 * t)
    y *= adsr(n, sr, 0.003, 0.25, sus, rel, dur)
    return _f32(y * 0.7)


# =============================================================================
# drums / percussion (cached by variant index)
# =============================================================================

@functools.lru_cache(maxsize=256)
def kick(sr, f_hi=150.0, f_lo=48.0, p_tau=0.03, a_tau=0.3, click=0.25, var=0, dur=0.8, drive=1.0):
    n = int(dur * sr)
    t = np.arange(n) / sr
    f = f_lo + (f_hi - f_lo) * np.exp(-t / p_tau)
    y = np.sin(TWO_PI * np.cumsum(f) / sr) * np.exp(-t / a_tau)
    if drive > 1.0:
        y = np.tanh(drive * y) / np.tanh(drive)
    nz = filt(_rng("kick", var).standard_normal(n), "low", 4000.0, sr, 2)
    y += click * nz * np.exp(-t / 0.003)
    y *= 1.0 - np.exp(-t / 0.0008)
    return _f32(tail_fade(y * 0.9, sr, 0.02))


@functools.lru_cache(maxsize=256)
def snare(sr, var=0, tone_f=185.0, decay=0.16, tone=0.6, bright=1.0, dur=0.45):
    n = int(dur * sr)
    t = np.arange(n) / sr
    r = _rng("snare", var)
    ph = TWO_PI * tone_f * (t + 0.15 * 0.01 * (1 - np.exp(-t / 0.01)))
    body = (np.sin(ph) * np.exp(-t / 0.06) + 0.5 * np.sin(1.72 * ph) * np.exp(-t / 0.04)) * tone
    nz = filt(r.standard_normal(n), "bp", (1200.0, min(9000.0 * bright, 0.45 * sr)), sr, 2)
    y = 0.7 * body + 1.3 * nz * np.exp(-t / decay)
    y *= 1.0 - np.exp(-t / 0.0005)
    return _f32(tail_fade(y * 0.6, sr, 0.02))


_MET = np.array([205.3, 304.4, 369.6, 522.7, 540.0, 800.0])


def _metal(t, scale, r):
    y = np.zeros_like(t)
    for f in _MET * scale:
        y += np.sign(np.sin(TWO_PI * f * t + r.uniform(0, 6)))
    return y / len(_MET)


@functools.lru_cache(maxsize=256)
def hat(sr, var=0, decay=0.04, open_=False, bright=1.0):
    decay = 0.3 if open_ else decay
    n = int((decay * 6.0 + 0.01) * sr)
    t = np.arange(n) / sr
    r = _rng("hat", var)
    x = 0.6 * r.standard_normal(n) + 0.6 * _metal(t, 1.6 + 0.02 * var, r)
    x = filt(x, "high", 7000.0 * bright, sr, 2)
    y = x * np.exp(-t / decay) * (1.0 - np.exp(-t / 0.0004))
    return _f32(tail_fade(y * 0.5, sr, 0.01))


@functools.lru_cache(maxsize=64)
def crash(sr, dur=2.8, var=0, bright=1.0, decay=0.9):
    n = int(dur * sr)
    t = np.arange(n) / sr
    r = _rng("crash", var)
    out = np.empty((2, n))
    for ch in range(2):
        x = 0.8 * r.standard_normal(n) + 0.4 * _metal(t, 2.3 + 0.05 * ch, r)
        x = filt(x, "high", 3500.0 * bright, sr, 2)
        x = filt(x, "low", 14000.0, sr, 1)
        env = 0.7 * np.exp(-t / decay) + 0.3 * np.exp(-t / 0.1)
        out[ch] = x * env * (1.0 - np.exp(-t / 0.001))
    return _f32(tail_fade(out * 0.45, sr, 0.2))


@functools.lru_cache(maxsize=256)
def timpani(midi, sr, var=0, decay=1.6):
    f0 = float(mtof(midi))
    n = int(decay * 2.6 * sr)
    q = 4 if sr % 4 == 0 else 1           # partials < 1 kHz: synthesize at sr/4
    nq = -(-n // q)
    tq = np.arange(nq) / (sr // q)
    r = _rng("timp", midi, var)
    parts = [(1.0, 1.0, 1.0), (1.504, 0.55, 0.55), (1.742, 0.3, 0.4), (2.0, 0.35, 0.45),
             (2.245, 0.18, 0.3), (2.494, 0.12, 0.25)]
    glide = np.cumsum(1.0 + 0.025 * np.exp(-tq / 0.06)) / (sr // q)
    yq = np.zeros(nq)
    for ratio, a, d in parts:
        yq += a * np.exp(-tq / (decay * d)) * np.sin(TWO_PI * f0 * ratio * glide + r.uniform(0, 6))
    y = signal.resample_poly(yq, q, 1)[:n] if q > 1 else yq
    t = np.arange(n) / sr
    y += 0.6 * filt(r.standard_normal(n), "low", 600.0, sr, 2) * np.exp(-t / 0.02)
    y *= 1.0 - np.exp(-t / 0.001)
    return _f32(tail_fade(y * 0.45, sr, 0.3))


@functools.lru_cache(maxsize=64)
def bass_drum(sr, var=0, f=52.0, decay=0.9, slap=0.3):
    """Orchestral bass drum / taiko-ish boom."""
    n = int(decay * 4.0 * sr)
    t = np.arange(n) / sr
    r = _rng("bd", var)
    ph = TWO_PI * np.cumsum(f * (1.0 + 0.4 * np.exp(-t / 0.03))) / sr
    y = np.sin(ph) * np.exp(-t / decay)
    y += 0.5 * filt(r.standard_normal(n), "low", 250.0, sr, 2) * np.exp(-t / 0.15)
    y += slap * filt(r.standard_normal(n), "low", 2000.0, sr, 2) * np.exp(-t / 0.008)
    y *= 1.0 - np.exp(-t / 0.001)
    return _f32(tail_fade(y * 0.8, sr, 0.05))


@functools.lru_cache(maxsize=64)
def clap(sr, var=0, decay=0.12):
    n = int(0.4 * sr)
    t = np.arange(n) / sr
    r = _rng("clap", var)
    nz = filt(r.standard_normal(n), "bp", (900.0, 4200.0), sr, 2)
    env = np.zeros(n)
    for d in (0.0, 0.011, 0.022, 0.031):
        m = t >= d
        env[m] += np.exp(-(t[m] - d) / 0.004) * (0.8 if d < 0.03 else 0.0)
    m = t >= 0.031
    env[m] += np.exp(-(t[m] - 0.031) / decay)
    return _f32(tail_fade(nz * env * 0.6, sr, 0.02))


@functools.lru_cache(maxsize=64)
def shaker(sr, var=0, decay=0.04):
    n = int(0.2 * sr)
    t = np.arange(n) / sr
    nz = filt(_rng("shk", var).standard_normal(n), "bp", (5000.0, 14000.0), sr, 2)
    env = (1.0 - np.exp(-t / 0.006)) * np.exp(-t / decay)
    return _f32(tail_fade(nz * env * 0.5, sr, 0.02))


@functools.lru_cache(maxsize=64)
def rim(sr, var=0, f=1700.0):
    n = int(0.12 * sr)
    t = np.arange(n) / sr
    r = _rng("rim", var)
    y = np.sin(TWO_PI * f * t) * np.exp(-t / 0.012) + 0.5 * np.sin(TWO_PI * f * 2.3 * t) * np.exp(-t / 0.006)
    y += 0.5 * filt(r.standard_normal(n), "bp", (2000.0, 8000.0), sr, 2) * np.exp(-t / 0.004)
    y *= 1.0 - np.exp(-t / 0.0003)
    return _f32(tail_fade(y * 0.4, sr, 0.01))


@functools.lru_cache(maxsize=64)
def tick(sr, var=0, f=3200.0):
    """Clock-tick style click."""
    n = int(0.06 * sr)
    t = np.arange(n) / sr
    r = _rng("tick", var)
    y = filt(r.standard_normal(n), "bp", (f * 0.8, min(f * 1.6, 0.45 * sr)), sr, 2) * np.exp(-t / 0.003)
    y += 0.4 * np.sin(TWO_PI * f * 1.37 * t) * np.exp(-t / 0.008)
    y *= 1.0 - np.exp(-t / 0.0002)
    return _f32(tail_fade(y * 0.6, sr, 0.005))


@functools.lru_cache(maxsize=64)
def tom(sr, f=110.0, var=0, decay=0.3):
    n = int(decay * 4 * sr)
    t = np.arange(n) / sr
    r = _rng("tom", var, f)
    ph = TWO_PI * np.cumsum(f * (1.0 + 0.5 * np.exp(-t / 0.02))) / sr
    y = np.sin(ph) * np.exp(-t / decay)
    y += 0.3 * filt(r.standard_normal(n), "bp", (200.0, 3000.0), sr, 2) * np.exp(-t / 0.01)
    y *= 1.0 - np.exp(-t / 0.0008)
    return _f32(tail_fade(y * 0.7, sr, 0.03))


# =============================================================================
# effects
# =============================================================================

@functools.lru_cache(maxsize=8)
def _ir(sr, rt60, pre, bright):
    """Synthetic stereo room IR: early reflections + two-band exponentially decaying noise."""
    L = int(sr * (rt60 * 1.15 + pre))
    npre = int(pre * sr)
    m = L - npre
    tt = np.arange(m) / sr
    r = _rng("ir", sr, rt60, pre, bright)
    ir = np.zeros((2, L))
    for ch in range(2):
        nz = r.standard_normal(m)
        lo = filt(nz, "low", 1800.0 * bright + 400.0, sr, 2)
        hi = nz - lo
        tail = (lo * np.exp(-6.9 * tt / rt60) + 0.6 * hi * np.exp(-6.9 * tt / (rt60 * 0.4)))
        tail *= 1.0 - np.exp(-tt / 0.01)
        for j in range(10):
            d = r.uniform(0.004, 0.07)
            tail[int(d * sr)] += 6.0 * r.uniform(0.2, 0.6) * np.exp(-d / 0.05) * (-1) ** j
        ir[ch, npre:] = tail
    ir /= np.sqrt(np.sum(ir ** 2) / 2.0)
    return ir.astype(np.float32)


def reverb(send, sr, rt60, pre, bright):
    ir = _ir(int(sr), float(rt60), float(pre), float(bright))
    x = filt(send, "high", 150.0, sr, 2)
    n = send.shape[1]
    out = np.empty((2, n), np.float32)
    for ch in range(2):
        out[ch] = signal.oaconvolve(x[ch], ir[ch])[:n]
    return out


def pingpong(x, sr, dtime, fb, lp, taps=7):
    n = x.shape[1]
    D = int(round(dtime * sr))
    out = np.zeros((2, n), np.float32)
    cur = 0.5 * (x[0].astype(np.float64) + x[1])
    sos = _sos("low", float(lp), int(sr), 1)
    for k in range(1, taps + 1):
        cur = signal.sosfilt(sos, cur) * fb
        s = k * D
        if s >= n:
            break
        out[(k - 1) % 2, s:] += cur[: n - s]
    return out


def duck_envelope(n, sr, times, depth=0.55, rel=0.16, att=0.004):
    imp = np.zeros(n)
    idx = np.round(np.asarray(times) * sr).astype(np.int64)
    idx = idx[(idx >= 0) & (idx < n)]
    np.add.at(imp, idx, 1.0)
    tk = np.arange(int(rel * 6 * sr)) / sr
    ker = np.exp(-tk / rel) * (1.0 - np.exp(-tk / att))
    ker /= ker.max()
    d = np.clip(signal.oaconvolve(imp, ker)[:n], 0.0, 1.0)
    return (1.0 - depth * d).astype(np.float32)


def limiter(x, sr, thr=0.891, win=0.008):
    """Look-ahead peak limiter: smoothed gain that never exceeds the required gain."""
    a = np.max(np.abs(x), axis=0)
    g = np.minimum(1.0, thr / np.maximum(a, 1e-12))
    if g.min() >= 1.0:
        return x
    R = max(1, int(win * sr))
    g = minimum_filter1d(g, size=2 * R + 1, mode="nearest")
    g = uniform_filter1d(g, size=R, mode="nearest")
    return x * g


def apply_fades(x, sr, fin=0.05, fout=1.2):
    n = x.shape[1]
    fin = min(fin, 0.1 * n / sr)
    fout = min(fout, 0.4 * n / sr)
    ni, no = int(fin * sr), int(fout * sr)
    if ni > 0:
        x[:, :ni] *= 0.5 - 0.5 * np.cos(np.pi * np.arange(ni) / ni)
    if no > 0:
        x[:, n - no:] *= 0.5 + 0.5 * np.cos(np.pi * np.arange(1, no + 1) / no)
    return x


# =============================================================================
# sequencer / mixer
# =============================================================================

class Song:
    def __init__(self, name, duration, sr, seed, bpm, bpb=4, tail=4.0):
        self.name, self.sr = name, int(sr)
        self.bpm, self.bpb = float(bpm), bpb
        self.spb = 60.0 / self.bpm
        self.bar = self.bpb * self.spb
        self.duration = float(duration)
        self.n_out = int(round(duration * sr))
        self.n = self.n_out + int(tail * sr)
        self.n_bars = int(np.ceil(self.duration / self.bar)) + 1
        self.dry = np.zeros((2, self.n), np.float32)
        self.send = np.zeros((2, self.n), np.float32)
        self.bufs = {}
        self.rng = np.random.default_rng([int(seed) & 0xFFFFFFFF, zlib.crc32(name.encode())])
        self.reverb = (1.5, 0.02, 0.7)
        self.wet = 0.8
        self.delay = None           # (seconds, feedback, lowpass Hz)
        self.duck_times = []        # sidechain triggers (seconds)
        self.duck = (0.55, 0.16)
        self.post = None            # callable(song, x) -> x
        self.stats = {} if DEBUG else None

    def t(self, bar, beat=0.0):
        return (bar * self.bpb + beat) * self.spb

    def hz(self, sd=0.005):
        return float(self.rng.normal(0.0, sd))

    def _buf(self, name):
        if name not in self.bufs:
            self.bufs[name] = np.zeros((2, self.n), np.float32)
        return self.bufs[name]

    def add(self, sig, t, g=1.0, pan=0.0, rev=0.0, dly=0.0, duck=False, grp=None):
        if g == 0.0:
            return
        i0 = int(round(t * self.sr))
        if i0 >= self.n:
            return
        if sig.ndim == 1:
            th = (pan + 1.0) * np.pi / 4.0
            gl, gr = np.cos(th) * 1.41421356, np.sin(th) * 1.41421356
            L = R = sig
        else:
            gl, gr = min(1.0, 1.0 - pan), min(1.0, 1.0 + pan)
            L, R = sig[0], sig[1]
        s0 = 0
        if i0 < 0:
            s0, i0 = -i0, 0
        ln = min(L.shape[0] - s0, self.n - i0)
        if ln <= 0:
            return
        a, b = L[s0:s0 + ln], R[s0:s0 + ln]
        tgt = self._buf("duck") if duck else self.dry
        tgt[0, i0:i0 + ln] += (g * gl) * a
        tgt[1, i0:i0 + ln] += (g * gr) * b
        if rev:
            self.send[0, i0:i0 + ln] += (g * gl * rev) * a
            self.send[1, i0:i0 + ln] += (g * gr * rev) * b
        if dly:
            d = self._buf("delay")
            d[0, i0:i0 + ln] += (g * gl * dly) * a
            d[1, i0:i0 + ln] += (g * gr * dly) * b
        if self.stats is not None and grp:
            gb = self.stats.setdefault(grp, np.zeros((2, self.n), np.float32))
            gb[0, i0:i0 + ln] += (g * gl) * a
            gb[1, i0:i0 + ln] += (g * gr) * b

    def render(self, gain):
        sr = self.sr
        out = self.dry
        if "duck" in self.bufs:
            env = duck_envelope(self.n, sr, self.duck_times, *self.duck) if self.duck_times else 1.0
            out += self.bufs["duck"] * env
        if "delay" in self.bufs and self.delay:
            d = pingpong(self.bufs["delay"], sr, *self.delay)
            out += d
            self.send += 0.35 * d
        rt, pre, br = self.reverb
        if self.wet:
            out += self.wet * reverb(self.send, sr, rt, pre, br)
        if self.post is not None:
            out = self.post(self, out)
        out = filt(out, "high", 22.0, sr, 2)[:, : self.n_out] * gain
        out = limiter(out, sr, 0.891)
        out = apply_fades(out, sr)
        np.clip(out, -0.9, 0.9, out=out)
        return np.ascontiguousarray(out.T, dtype=np.float32)


# ---------------------------------------------------------------- shared bits
def snare_roll(S, t0, t1, v0, v1, rate=18.0, g=0.3, pan=0.1, rev=0.3, grp="drums"):
    k = max(1, int((t1 - t0) * rate))
    for i in range(k):
        u = i / max(1, k - 1)
        vel = (v0 + (v1 - v0) * u ** 1.5) * (0.85 + 0.3 * S.rng.random())
        S.add(snare(S.sr, var=int(S.rng.integers(8)), decay=0.09), t0 + i / rate + S.hz(0.002),
              g=g * vel, pan=pan, rev=rev, grp=grp)


def timp_roll(S, midi, t0, t1, v0, v1, rate=14.0, g=0.3, rev=0.4):
    k = max(1, int((t1 - t0) * rate))
    for i in range(k):
        u = i / max(1, k - 1)
        vel = (v0 + (v1 - v0) * u ** 1.3) * (0.85 + 0.3 * S.rng.random())
        S.add(timpani(midi, S.sr, var=int(S.rng.integers(6))), t0 + i / rate + S.hz(0.003),
              g=g * vel, pan=-0.2, rev=rev, grp="timp")


# =============================================================================
# THE ARCH THEME (original).  Head motif spells A-R(e)-C-H: A, D, C, B.
# =============================================================================
ARCH_MINOR = ("A4:1 D5:1.5 C5:0.5 B4:1  Bb4:0.5 C5:0.5 D5:1 F5:1.5 E5:0.5  "
              "D5:1 A4:1 Bb4:0.75 A4:0.25 G4:1  E4:1 A4:1 D4:2")
ARCH_ANSWER = ("C5:1 F5:1.5 E5:0.5 D5:1  D5:0.5 E5:0.5 F5:1 A5:1.5 G5:0.5  "
               "F5:1 C5:1 D5:0.75 C5:0.25 Bb4:1  G4:1 C5:1 F4:2")
ARCH_MAJOR = ("A4:1 D5:1.5 C5:0.5 B4:1  B4:0.5 C#5:0.5 D5:1 F#5:1.5 E5:0.5  "
              "D5:1 A4:1 B4:0.75 A4:0.25 G4:1  E4:1 A4:1 D4:2  "
              "A4:1 D5:1.5 C5:0.5 B4:1  B4:0.5 C#5:0.5 D5:1 G5:1.5 F#5:0.5  "
              "F#5:1 D5:1 E5:0.75 F#5:0.25 G5:1  A5:1 F#5:0.5 E5:0.5 D5:2")


# =============================================================================
# track: hum
# =============================================================================
def comp_hum(S):
    sr, n = S.sr, S.n
    S.reverb, S.wet = (3.2, 0.03, 0.5), 0.9
    t = np.arange(n) / sr
    r = S.rng
    h = np.zeros(n)
    for k, a in ((1, 1.0), (2, 0.55), (3, 0.35), (4, 0.12), (5, 0.1), (6, 0.04), (7, 0.03)):
        h += a * np.sin(TWO_PI * 60.0 * k * t + r.uniform(0, 6))
    wf = 15734.0 + 3.0 * np.sin(TWO_PI * 0.09 * t)
    whine = 0.007 * np.sin(TWO_PI * np.cumsum(wf) / sr)
    for ch in range(2):
        wob = 1.0 + 0.12 * np.sin(TWO_PI * 0.13 * t + 0.4 * ch) \
            + 0.05 * np.sin(TWO_PI * 0.71 * t + 1.3 * ch)
        S.dry[ch] += 0.30 * h * wob + whine
        fan = filt(r.standard_normal(n), "low", 350.0, sr, 2)
        S.dry[ch] += 0.05 * fan * (1.0 + 0.2 * np.sin(TWO_PI * 0.05 * t + ch))
    pads = ["D3 A3 E4 F4", "Bb2 F3 A3 D4", "G2 D3 A3 Bb3", "A2 E3 A3 C#4"]
    roots = ["D2", "Bb1", "G1", "A1"]
    for i, bar in enumerate(range(0, S.n_bars, 2)):
        v = V(pads[i % 4])
        t0 = S.t(bar)
        for j, m in enumerate(v):
            S.add(saw_pad(m, 2 * S.bar, sr, fc=520.0, att=2.8, rel=3.2, voices=3, detune=0.1, var=j),
                  t0, g=0.13, pan=(-0.5, -0.15, 0.15, 0.5)[j], rev=0.6, grp="pad")
        S.add(sine_bass(N(roots[i % 4]), 2 * S.bar, sr, att=2.5, rel=3.0, harm=0.05, dec=4, sus=0.9),
              t0, g=0.10, rev=0.1, grp="pad")


# =============================================================================
# track: anthem  (108 bpm, D minor -> F major)
# =============================================================================
_ANTHEM_CH = {  # name: (bass, alternate bass, horn voicing)
    "Dm": ("D2", "A1", "A3 D4 F4"), "G/B": ("B1", "D2", "G3 B3 D4"), "Bb": ("Bb1", "F2", "F3 Bb3 D4"),
    "F/A": ("A1", "C2", "F3 A3 C4"), "Gm": ("G1", "D2", "G3 Bb3 D4"), "A": ("A1", "E2", "A3 C#4 E4"),
    "F": ("F2", "C2", "F3 A3 C4"), "Bb/D": ("D2", "F2", "F3 Bb3 D4"), "F/C": ("C2", "F2", "F3 A3 C4"),
    "Dm7": ("D2", "A1", "F3 A3 C4"), "C7/E": ("E2", "G1", "G3 Bb3 C4"), "C": ("C2", "G1", "G3 C4 E4"),
    "Eb": ("Eb2", "Bb1", "G3 Bb3 Eb4"),
}
_ANTHEM_A_H = [[(0, 2, "Dm"), (2, 2, "G/B")], [(0, 2, "Bb"), (2, 2, "F/A")],
               [(0, 2, "Dm"), (2, 2, "Gm")], [(0, 2, "A"), (2, 2, "Dm")],
               [(0, 2, "F"), (2, 2, "Bb/D")], [(0, 2, "Bb"), (2, 2, "F/C")],
               [(0, 2, "Dm7"), (2, 2, "C7/E")], [(0, 2, "C"), (2, 2, "F")]]
_ANTHEM_B_H = [[(0, 4, c)] for c in ("Gm", "Dm", "Bb", "F", "Gm", "Dm", "Eb", "A")]
_ANTHEM_BRIDGE = ("G4:1 D5:1.5 C5:0.5 Bb4:1  A4:1 F4:1 D4:2  Bb4:1 F5:1.5 Eb5:0.5 D5:1  C5:1 A4:1 F4:2  "
                  "G4:0.5 A4:0.5 Bb4:0.5 C5:0.5 D5:1 G5:1  F5:1 E5:0.5 D5:0.5 A4:2  "
                  "Bb4:1 Eb5:1 G5:1 Eb5:1  E5:1 C#5:1 A4:2")


def _march_harmony(S, bar, harm, CH, strong, horn_g=0.22, bass_g=0.28, str_g=0.065, key=0, bright=0.55):
    sr, spb = S.sr, S.spb
    t0 = S.t(bar)
    for (b0, blen, nm) in harm:
        bass, alt, vo = CH[nm]
        vo = [m + key for m in V(vo)]
        for i, m in enumerate(vo):
            S.add(saw_pad(m + 12, blen * spb, sr, fc=2400.0, att=0.2, rel=0.6, voices=2, var=i),
                  t0 + b0 * spb, g=str_g, pan=(-0.6, 0.0, 0.6)[i % 3], rev=0.6, grp="strings")
        for j, bb in enumerate(range(int(b0), int(b0 + blen))):
            if strong or bb % 2 == 0:
                m = (N(bass) if j % 2 == 0 else N(alt)) + key
                S.add(brass(m, 0.8 * spb, sr, bright=0.35, var=bb % 3), t0 + bb * spb,
                      g=bass_g, rev=0.15, grp="bass")
                S.add(sine_bass(m, 0.7 * spb, sr, harm=0.0), t0 + bb * spb, g=0.18, grp="bass")
            if bb % 2 == 1:
                for i, m in enumerate(vo):
                    S.add(brass(m, 0.42 * spb, sr, bright=bright, var=i), t0 + bb * spb + S.hz(0.004),
                          g=horn_g, pan=(-0.35, 0.05, 0.35)[i], rev=0.35, grp="horns")


def _march_drums(S, bar, pattern, bd_beats=(0, 2), g=0.2):
    sr, spb = S.sr, S.spb
    t0 = S.t(bar)
    for i, v in enumerate(pattern):
        if v:
            S.add(snare(sr, var=int(S.rng.integers(8)), decay=0.12), t0 + i * spb / 4 + S.hz(0.002),
                  g=g * v * (0.9 + 0.2 * S.rng.random()), pan=0.12, rev=0.25, grp="drums")
    for b in bd_beats:
        S.add(bass_drum(sr, var=b), t0 + b * spb, g=0.4, rev=0.3, grp="drums")


def comp_anthem(S):
    sr, spb = S.sr, S.spb
    S.reverb, S.wet = (2.4, 0.03, 0.75), 0.55
    theme = mel(ARCH_MINOR, 16) + [(s + 16, d, m) for (s, d, m) in mel(ARCH_ANSWER, 16)]
    bridge = mel(_ANTHEM_BRIDGE, 32)
    CH = _ANTHEM_CH
    PA = [0.9, 0, 0, 0.35, 0.6, 0, 0.35, 0, 0.9, 0, 0, 0.35, 0.6, 0.3, 0.4, 0.5]
    PA2 = [1.0, 0.3, 0.35, 0.5, 0.7, 0, 0.45, 0.3, 0.95, 0.3, 0.35, 0.5, 0.7, 0.45, 0.55, 0.7]
    PB = [0.7, 0, 0, 0, 0.4, 0, 0.25, 0.3, 0.6, 0, 0, 0, 0.4, 0, 0.3, 0.35]
    INTRO = 4
    for bar in range(S.n_bars):
        t0 = S.t(bar)
        if bar < INTRO:
            if bar == 0:
                timp_roll(S, N("D2"), t0, t0 + 2 * S.bar, 0.15, 0.8)
                for m in (N("D2"), N("A2"), N("D3")):
                    S.add(brass(m, 2 * S.bar - 0.2, sr, bright=0.45, att=2.5, vib=0.3), t0, g=0.16,
                          rev=0.4, grp="horns")
                S.add(saw_pad(N("D4"), 2 * S.bar, sr, fc=1800.0, att=3.0, rel=1.0, voices=3), t0,
                      g=0.06, rev=0.6, grp="strings")
            if bar == 2:
                S.add(bass_drum(sr, var=1), t0, g=0.7, rev=0.4, grp="drums")
                S.add(crash(sr, var=0), t0, g=0.35, rev=0.4, grp="drums")
                for (s, d, m) in mel("D4:0.75 D4:0.25 A4:1 D5:2", 4):
                    S.add(brass(m, d * spb * 0.9, sr, bright=1.1), t0 + s * spb, g=0.5, rev=0.35, grp="mel")
                    S.add(brass(m - 12, d * spb * 0.9, sr, bright=0.8), t0 + s * spb, g=0.2, rev=0.35, grp="horns")
                _march_harmony(S, bar, [(0, 4, "Dm")], CH, True)
            if bar == 3:
                for (s, d, m) in mel("C#5:0.75 D5:0.25 E5:1", 2):
                    S.add(brass(m, d * spb * 0.9, sr, bright=1.1), t0 + s * spb, g=0.5, rev=0.35, grp="mel")
                for i, m in enumerate(V("A3 C#4 E4")):
                    S.add(brass(m, 1.8 * spb, sr, bright=0.8, var=i), t0, g=0.12, pan=(-0.3, 0, 0.3)[i],
                          rev=0.35, grp="horns")
                S.add(brass(N("A1"), 1.8 * spb, sr, bright=0.4), t0, g=0.3, rev=0.2, grp="bass")
                snare_roll(S, t0 + 2 * spb, t0 + 4 * spb, 0.15, 1.0, rate=20.0, g=0.3)
                timp_roll(S, N("A1"), t0 + 2 * spb, t0 + 4 * spb, 0.2, 0.9)
            continue
        k = (bar - INTRO) % 24
        sec = "A" if k < 8 else ("B" if k < 16 else "A2")
        ib = k % 8
        if ib == 0 or (sec == "A2" and ib == 4):
            S.add(crash(sr, var=ib), t0, g=0.32, rev=0.4, grp="drums")
            S.add(bass_drum(sr, var=3), t0, g=0.6, rev=0.4, grp="drums")
        if sec in ("A", "A2"):
            harm = _ANTHEM_A_H[ib]
            _march_harmony(S, bar, harm, CH, strong=(sec == "A2"),
                           str_g=0.065 if sec == "A" else 0.09)
            for (s, d, m) in in_bar(theme, ib):
                tt = t0 + s * spb
                S.add(brass(m, d * spb * 0.92, sr, bright=1.0), tt, g=0.6, rev=0.3, grp="mel")
                if sec == "A2":
                    S.add(brass(m - 12, d * spb * 0.92, sr, bright=0.7, var=1), tt, g=0.2, pan=-0.2,
                          rev=0.3, grp="mel")
                    S.add(mallet(m + 12, sr, "glock"), tt, g=0.14, pan=0.3, rev=0.4, grp="glock")
            _march_drums(S, bar, PA if sec == "A" else PA2)
            root = N(CH[harm[0][2]][0])
            while root > N("F2"):
                root -= 12
            while root < N("F1"):
                root += 12
            S.add(timpani(root + 12 if root < N("A1") else root, sr, var=bar % 6), t0, g=0.25,
                  pan=-0.2, rev=0.4, grp="timp")
            if ib == 7:
                timp_roll(S, N("A1"), t0 + 3 * spb, t0 + 4 * spb, 0.2, 0.7)
        else:  # B: bridge melody in horns, strings, lighter drums, build at the end
            harm = _ANTHEM_B_H[ib]
            _march_harmony(S, bar, harm, CH, strong=False, horn_g=0.09, str_g=0.1)
            for (s, d, m) in in_bar(bridge, ib):
                tt = t0 + s * spb
                S.add(brass(m, d * spb * 0.95, sr, bright=0.7, var=2), tt, g=0.5, pan=-0.1, rev=0.4, grp="mel")
                S.add(saw_pad(m + 12, d * spb, sr, fc=3000.0, att=0.05, rel=0.3, voices=2), tt, g=0.05,
                      pan=0.3, rev=0.5, grp="strings")
            if ib < 6:
                _march_drums(S, bar, PB, bd_beats=(0,), g=0.16)
            else:
                snare_roll(S, t0, t0 + S.bar, 0.2 + 0.4 * (ib - 6), 0.6 + 0.4 * (ib - 6), rate=18.0, g=0.22)
                S.add(bass_drum(sr, var=2), t0, g=0.5, rev=0.3, grp="drums")
            if ib in (0, 4):
                S.add(timpani(N("G1") + 12, sr), t0, g=0.25, rev=0.4, grp="timp")
            if ib == 7:
                timp_roll(S, N("A1"), t0, t0 + S.bar, 0.3, 1.0)


# =============================================================================
# track: lofi  (88 bpm)
# =============================================================================
_LOFI_CH = {
    "Dm9": ("D2", "F3 A3 C4 E4"), "G13": ("G2", "F3 A3 B3 E4"), "Cmaj9": ("C2", "E3 G3 B3 D4"),
    "Am9": ("A2", "G3 B3 C4 E4"), "A7b13": ("A2", "G3 C#4 F4"), "Fmaj9": ("F2", "A3 C4 E4 G4"),
    "Em7": ("E2", "G3 B3 D4"), "Bbmaj7#11": ("Bb2", "A3 D4 E4"), "Am7": ("A2", "G3 C4 E4"),
    "Em7b5": ("E2", "G3 Bb3 D4"),
}
_LOFI_A = ["Dm9", "G13", "Cmaj9", "Am9", "Dm9", "G13", "Cmaj9", "A7b13"]
_LOFI_B = ["Fmaj9", "Em7", "Dm9", "Cmaj9", "Bbmaj7#11", "Am7", "Em7b5", "A7b13"]
_LOFI_L1 = ("r:1 A4:0.5 C5:0.5 E5:1.5 D5:0.5  r:0.5 B4:0.5 D5:1 E5:2  r:1 G4:0.5 B4:0.5 D5:2  "
            "C5:1 B4:0.5 A4:0.5 E4:2  r:1 F4:0.5 A4:0.5 C5:1 E5:1  F5:1.5 E5:0.5 D5:1 B4:1  "
            "r:0.5 E5:0.5 D5:0.5 C5:0.5 B4:1 G4:1  C#5:1.5 A4:0.5 r:2")
_LOFI_LB = ("A4:2 G4:1 E4:1  G4:2 r:2  r:1 F4:1 A4:1 E5:1  D5:2 B4:2  "
            "r:1 A4:1 D5:1 E5:1  C5:2 r:2  r:1 G4:0.5 Bb4:0.5 D5:2  F5:1 E5:1 C#5:2")
_LOFI_L2 = ("r:2 E5:0.5 D5:0.5 C5:1  D5:3 r:1  r:1 B4:0.5 C5:0.5 E5:1 G5:1  E5:2 r:1 C5:1  "
            "r:2 A4:0.5 C5:0.5 D5:1  F5:1 E5:1 D5:1 B4:1  C5:2 r:1 G4:1  A4:2 C#5:1 E5:1")


def _lofi_post(S, x):
    sr = S.sr
    n = x.shape[1]
    t = np.arange(n) / sr
    r = _rng("lofi-post", S.n)
    dev = 60.0 * np.sin(TWO_PI * 0.33 * t) + 2.0 * np.sin(TWO_PI * 5.5 * t + 1.0)
    pos = np.clip(np.arange(n) + dev - 62.0, 0, n - 1)
    x = filt(x, "low", 5600.0, sr, 2)
    xs = np.empty((2, n), np.float32)
    idx = np.arange(n)
    for ch in range(2):
        xs[ch] = np.interp(pos, idx, x[ch])
    rms = float(np.sqrt(np.mean(xs[:, : S.n_out] ** 2)) + 1e-9)
    imp = np.zeros(n)
    k = r.poisson(3.0 * n / sr)
    pos_c = r.integers(0, n, k)
    imp[pos_c] = r.exponential(1.0, k) * r.choice([-1.0, 1.0], k)
    crack = filt(imp, "bp", (1000.0, 5000.0), sr, 1) * rms * 0.9
    hiss = filt(r.standard_normal((2, n)), "low", 7000.0, sr, 1) * rms * 10 ** (-50 / 20)
    xs += (crack[None, :] * np.array([[1.0], [0.8]]) + hiss).astype(np.float32)
    return xs


def comp_lofi(S):
    sr, spb = S.sr, S.spb
    S.reverb, S.wet = (1.0, 0.015, 0.55), 0.6
    S.delay = (0.75 * spb, 0.38, 2200.0)
    S.post = _lofi_post
    leads = {"L1": mel(_LOFI_L1, 32), "LB": mel(_LOFI_LB, 32), "L2": mel(_LOFI_L2, 32)}
    FORM = [("A", "L1"), ("B", "LB"), ("A", "L2"), ("B", None)]
    e8 = spb / 2.0
    sw = 0.6  # 16th swing

    def st(i):  # 16th step -> beats offset (swung)
        return ((i // 2) + (sw if i % 2 else 0.0)) * 0.5

    for bar in range(S.n_bars):
        t0 = S.t(bar)
        cyc = bar % 32
        sec, lead = FORM[cyc // 8]
        ib = cyc % 8
        name = (_LOFI_A if sec == "A" else _LOFI_B)[ib]
        bass, vo = _LOFI_CH[name]
        vo = V(vo)
        # keys: lazy strummed FM e-piano
        hits = [(0.0, 2.25, 0.8), (2.5, 1.25, 0.55)] if sec == "A" else [(0.0, 3.4, 0.75), (3.5, 0.45, 0.4)]
        for (b, d, vel) in hits:
            for j, m in enumerate(vo):
                S.add(epiano(m, d * spb, sr, var=j), t0 + b * spb + 0.014 * j + S.hz(0.004),
                      g=0.16 * vel * (0.85 + 0.3 * S.rng.random()), pan=-0.3 + 0.2 * j, rev=0.35, grp="keys")
        # bass
        root = N(bass)
        S.add(sine_bass(root, 1.4 * spb, sr), t0, g=0.24, grp="bass")
        S.add(sine_bass(root + (7 if ib % 2 else 12), 0.4 * spb, sr), t0 + 2.5 * spb, g=0.16, grp="bass")
        if ib % 4 == 3:
            nxt = N(_LOFI_CH[(_LOFI_A if sec == "A" else _LOFI_B)[(ib + 1) % 8]][0])
            S.add(sine_bass(nxt + (1 if nxt < root else -1) - (12 if nxt - root > 6 else 0), 0.4 * spb, sr),
                  t0 + 3.5 * spb, g=0.14, grp="bass")
        # chip arpeggio in B sections
        if sec == "B":
            for i in range(8):
                m = vo[[0, 1, 2, 1, 0, 2, 1, 2][i] % len(vo)] + 12
                S.add(chip_pulse(m, 0.35 * spb, sr, duty=0.25, dec=0.1, sus=0.3), t0 + st(2 * i) * spb,
                      g=0.035, pan=0.45, rev=0.3, dly=0.3, grp="arp")
        # drums (enter at bar 1)
        if bar >= 1:
            fill = ib == 7
            kpat = [0, 7, 10] if sec == "A" else [0, 6, 10, 11]
            for i in kpat:
                S.add(kick(sr, f_hi=110.0, f_lo=46.0, a_tau=0.22, click=0.12, var=i), t0 + st(i) * spb,
                      g=0.42 if i == 0 else 0.3, grp="drums")
            for i in (4, 12):
                S.add(snare(sr, var=int(S.rng.integers(8)), decay=0.13, bright=0.6), t0 + st(i) * spb + 0.018,
                      g=0.22, pan=0.05, rev=0.25, grp="drums")
            if fill:
                for i in (13, 14, 15):
                    S.add(snare(sr, var=i, decay=0.07, bright=0.5), t0 + st(i) * spb + 0.012,
                          g=0.07 + 0.02 * (i - 13), rev=0.2, grp="drums")
            for i in range(16):
                if fill and i >= 12:
                    break
                vel = (0.55, 0.22, 0.38, 0.2)[i % 4] * (0.8 + 0.4 * S.rng.random())
                op = (sec == "B" and i == 14)
                S.add(hat(sr, var=i % 5, decay=0.03, open_=op, bright=0.8), t0 + st(i) * spb + S.hz(0.003),
                      g=0.12 * vel * (1.4 if op else 1.0), pan=0.25, grp="drums")
        # lead
        if lead:
            for (s, d, m) in in_bar(leads[lead], ib):
                mode = "square" if lead != "L2" else "tri"
                S.add(soft_lead(m, d * spb * 0.95, sr, mode=mode, fc=1900.0, att=0.03, rel=0.25, vib=0.1),
                      t0 + s * spb + S.hz(0.006), g=0.125 if mode == "square" else 0.17, pan=-0.05,
                      rev=0.3, dly=0.35, grp="lead")
        elif ib % 2 == 0:  # sparse bell answer in the last section
            for (b, off) in ((1.0, 2), (2.5, 3)):
                m = vo[off % len(vo)] + 12
                S.add(fm_bell(m, 1.0, sr, ratio=3.0, index=1.2, decay=0.9), t0 + b * spb,
                      g=0.07, pan=0.35, rev=0.4, dly=0.4, grp="lead")


# =============================================================================
# track: tension  (120 bpm, C minor)
# =============================================================================
_TENS_B = ("C4:0.5 r:0.5 Eb4:0.5 r:0.5 G4:0.5 r:0.5 F#4:0.5 G4:0.5  Ab4:0.5 r:0.5 G4:0.5 r:0.5 Eb4:1 C4:1  "
           "F4:0.5 r:0.5 Ab4:0.5 r:0.5 C5:0.5 r:0.5 B4:0.5 C5:0.5  D5:1 B4:1 G4:1 r:1  "
           "C5:0.5 r:0.5 G4:0.5 r:0.5 Eb4:0.5 r:0.5 D4:0.5 Eb4:0.5  C4:1 Eb4:1 Ab4:1 G4:1  "
           "F4:0.5 Ab4:0.5 Db5:1 C5:0.5 Db5:0.5 F5:1  F5:0.5 r:0.5 D5:0.5 r:0.5 B4:0.5 r:0.5 G4:1")
_OST = {
    "Cm": "C5 G4 Eb5 G4 D5 G4 Eb5 G4", "G": "B4 G4 D5 G4 F5 G4 D5 G4",
    "Ab": "C5 Ab4 Eb5 Ab4 C5 Ab4 Eb5 Ab4", "Fm": "C5 F4 Ab4 F4 C5 F4 Ab4 F4",
    "Db": "Db5 Ab4 F5 Ab4 Db5 Ab4 F5 Ab4",
}
_OST16 = {"Ab": "C5 Eb5 Ab5 Eb5", "Bb": "D5 F5 Bb5 F5", "Bdim": "D5 F5 Ab5 B4", "G": "B4 D5 G5 D5"}


def comp_tension(S):
    sr, spb = S.sr, S.spb
    S.reverb, S.wet = (1.3, 0.02, 0.7), 0.5
    melB = mel(_TENS_B, 32)
    A_bass = ["C2", "B1", "Bb1", "A1", "Ab1", "Ab1", "G1", "G1"]
    A_ost = ["Cm", "Cm", "Cm", "Cm", "Ab", "Ab", "G", "G"]
    B_ch = [("Cm", "C2"), ("Ab", "Ab1"), ("Fm", "F2"), ("G", "G1"), ("Cm", "C2"), ("Ab", "Ab1"),
            ("Db", "Db2"), ("G", "G1")]
    C_ch = [("Ab", "Ab1"), ("Bb", "Bb1"), ("Bdim", "B1"), ("G", "G1")]
    INTRO = 2
    for bar in range(S.n_bars):
        t0 = S.t(bar)
        if bar < INTRO:
            if bar == 0:
                S.add(timpani(N("C2"), sr), t0, g=0.5, rev=0.5, grp="timp")
                S.add(bass_drum(sr, var=0), t0, g=0.5, rev=0.5, grp="drums")
                S.add(saw_pad(N("G4"), 2 * S.bar, sr, fc=2500.0, att=1.5, rel=0.5, voices=3), t0, g=0.05,
                      pan=0.3, rev=0.5, grp="pad")
            for i in range(16):
                S.add(tick(sr, var=i % 3), t0 + i * spb / 4, g=0.28 if i % 4 == 0 else 0.14, pan=0.3, grp="tick")
            S.add(synth_bass(N("C2"), 0.3 * spb, sr), t0 + 3.5 * spb, g=0.3 if bar == 1 else 0.0, grp="bass")
            continue
        k = (bar - INTRO) % 20
        sec = "A" if k < 8 else ("B" if k < 16 else "C")
        ib = k if sec == "A" else (k - 8 if sec == "B" else k - 16)
        if sec == "A":
            bass, ost = N(A_bass[ib]), A_ost[ib]
        elif sec == "B":
            ost, b = B_ch[ib]
            bass = N(b)
        else:
            ost, b = C_ch[ib]
            bass = N(b)
        # pulsing bass: staccato 8ths
        for i in range(8):
            acc = 1.0 if i % 2 == 0 else 0.7
            S.add(synth_bass(bass, 0.32 * spb, sr, var=i % 2), t0 + i * spb / 2, g=0.24 * acc, grp="bass")
        # plucked ostinato
        if sec != "C":
            notes = V(_OST[ost])
            for i, m in enumerate(notes):
                S.add(pluck(m, 0.3 * spb, sr, bright=1.3, decay=0.3, pos=0.13, var=i % 3), t0 + i * spb / 2,
                      g=0.28 if i % 2 == 0 else 0.2, pan=0.35 if i % 2 else -0.2, rev=0.3, grp="ost")
        else:
            notes = V(_OST16[ost])
            for i in range(16):
                m = notes[i % 4] + (0 if i < 8 else 0)
                S.add(pluck(m, 0.2 * spb, sr, bright=1.4, decay=0.25, pos=0.13, var=i % 3),
                      t0 + i * spb / 4, g=0.2 + 0.07 * ib / 3, pan=(-0.3, 0.3)[i % 2], rev=0.3, grp="ost")
        # ticking clock + kick + rim
        for i in range(16):
            S.add(tick(sr, var=i % 3), t0 + i * spb / 4, g=0.28 if i % 4 == 0 else 0.14, pan=0.3, grp="tick")
        for b in (0, 2):
            S.add(kick(sr, f_hi=120.0, f_lo=45.0, a_tau=0.25, click=0.1), t0 + b * spb, g=0.38, grp="drums")
        if sec != "A":
            for b in (1, 3):
                S.add(rim(sr, var=b), t0 + b * spb, g=0.18, pan=-0.15, rev=0.2, grp="drums")
        if ib % 4 == 0 and sec == "A":
            S.add(timpani(bass + 12 if bass < N("F1") + 12 else bass, sr), t0, g=0.24, rev=0.4, grp="timp")
        # string tremolo pad in A
        if sec == "A" and ib % 2 == 0:
            for j, m in enumerate(V("G4 C5") if ost != "G" else V("G4 B4")):
                S.add(saw_pad(m, 2 * S.bar - 0.1, sr, fc=2800.0, att=0.8, rel=0.5, voices=3, var=j),
                      t0, g=0.06, pan=(-0.5, 0.5)[j], rev=0.5, grp="pad")
        # sneaky reed melody + xylophone doubling + brass stabs
        if sec == "B":
            for (s, d, m) in in_bar(melB, ib):
                S.add(voice(m - 12, d * spb * 0.55, sr, vowel="reed", voices=1, att=0.012, rel=0.06, vib=0.0,
                            dec=0.2, sus=0.8), t0 + s * spb, g=0.28, pan=-0.1, rev=0.25, grp="mel")
                if ib >= 4:
                    S.add(mallet(m + 12, sr, "marimba", decay=0.25, bright=1.4), t0 + s * spb, g=0.14,
                          pan=0.25, rev=0.3, grp="mel")
            if ib % 2 == 1:
                ch_notes = {"Ab": "Ab3 C4 Eb4", "G": "G3 B3 D4 F4", "Cm": "G3 C4 Eb4", "Fm": "F3 Ab3 C4",
                            "Db": "F3 Ab3 Db4"}[ost]
                for b in (1.5, 3.5):
                    for j, m in enumerate(V(ch_notes)):
                        S.add(brass(m, 0.22 * spb, sr, bright=0.9, var=j), t0 + b * spb, g=0.09,
                              pan=(-0.3, 0.0, 0.3, 0.15)[j], rev=0.3, grp="stabs")
        if sec == "C":
            if ib == 3:
                for b in (0.0, 1.0, 2.0):
                    for j, m in enumerate(V("G2 G3 B3 F4 Ab4")):
                        S.add(brass(m, (0.3 if b < 2 else 1.6) * spb, sr, bright=1.1, var=j), t0 + b * spb,
                              g=0.12, pan=(-0.3, 0.3, -0.15, 0.15, 0.0)[j], rev=0.4, grp="stabs")
                    S.add(timpani(N("G1") + 12, sr), t0 + b * spb, g=0.45, rev=0.4, grp="timp")
                snare_roll(S, t0 + 2 * spb, t0 + 4 * spb, 0.2, 0.9, rate=16.0, g=0.22)
            elif ib == 0:
                S.add(crash(sr, var=2, bright=0.8), t0, g=0.2, rev=0.4, grp="drums")


# =============================================================================
# track: wiki  (100 bpm, A major pentatonic, phasing)
# =============================================================================
_WIKI_P = ["A4", "E5", "B4", None, "C#5", "F#5", "B4", "E5", "A4", "E5", "C#5", None, "B4", "F#5", "C#5", "E5"]
_WIKI_H = [("A2", "A3 C#4 E4"), ("F#2", "A3 C#4 F#4"), ("D2", "A3 D4 F#4"), ("E2", "B3 E4 G#4")]


def comp_wiki(S):
    sr, spb = S.sr, S.spb
    S.reverb, S.wet = (2.0, 0.02, 0.9), 0.55
    S.delay = (0.75 * spb, 0.3, 3500.0)
    P = [N(x) if x else None for x in _WIKI_P]
    s16 = spb / 4.0
    order = [int(i) for i in _rng("wiki-order").permutation(16)]
    long_tones = V("E5 C#5 B4 F#5 E5 A4 B4 C#5")

    def offset(bar_f):  # L2 phase offset in 16ths: holds 3 bars, drifts during the 4th
        q = max(0.0, (bar_f - 4.0) / 4.0)
        fq = q - np.floor(q)
        u = np.clip((fq - 0.75) / 0.25, 0, 1)
        return np.floor(q) + u * u * (3 - 2 * u)      # no wrap: pattern repeats each bar

    for bar in range(S.n_bars):
        t0 = S.t(bar)
        cyc = bar % 64
        hb, pad = _WIKI_H[(bar // 4) % 4]
        # L1 marimba
        for i, m in enumerate(P):
            if m is not None:
                S.add(mallet(m, sr, "marimba", var=i % 3), t0 + i * s16 + S.hz(0.002), g=0.26 if i % 4 == 0 else 0.2,
                      pan=-0.4, rev=0.3, grp="L1")
        # L2 phasing vibraphone/marimba
        if bar >= 4:
            for i, m in enumerate(P):
                if m is not None:
                    off = offset(bar + i / 16.0)
                    S.add(mallet(m, sr, "vibe", decay=1.2, var=i % 3), t0 + (i + off) * s16, g=0.15,
                          pan=0.45, rev=0.35, grp="L2")
        # L3 bass pulse, 3+3+2 accents
        if bar >= 8:
            b = N(hb)
            for i in range(8):
                acc = 1.0 if i in (0, 3, 6) else 0.55
                S.add(mallet(b + (12 if i in (3, 6) else 0), sr, "marimba", decay=0.5, bright=0.6),
                      t0 + i * spb / 2, g=0.3 * acc, pan=0.0, rev=0.15, grp="L3")
                if i == 0:
                    S.add(sine_bass(b, 1.8 * spb, sr, harm=0.1), t0, g=0.14, grp="L3")
        # L4 pad + additive glock process
        if bar >= 12:
            if bar % 4 == 0:
                for j, m in enumerate(V(pad)):
                    S.add(saw_pad(m, 4 * S.bar, sr, fc=1400.0, att=2.0, rel=2.0, voices=3, var=j), t0, g=0.075,
                          pan=(-0.5, 0.0, 0.5)[j], rev=0.6, grp="pad")
            reveal = min(16, (bar - 12) // 1 + 1) if cyc < 48 else max(4, 16 - (cyc - 48))
            for i in order[:reveal]:
                if P[i] is not None:
                    S.add(mallet(P[i] + 12, sr, "glock", decay=1.0), t0 + i * s16, g=0.085, pan=0.2,
                          rev=0.45, dly=0.25, grp="L4")
        # L5 hyperfocus pulse
        if bar >= 16:
            for b in range(4):
                S.add(kick(sr, f_hi=90.0, f_lo=45.0, a_tau=0.18, click=0.05), t0 + b * spb, g=0.3, grp="L5")
            for i in range(16):
                S.add(shaker(sr, var=i % 4), t0 + i * s16 + S.hz(0.002), g=0.05 if i % 2 else 0.08,
                      pan=0.3, grp="L5")
        # L6 long tones (resulting pattern)
        if bar >= 24:
            for h in range(2):
                m = long_tones[(bar * 2 + h) % len(long_tones)]
                S.add(flute(m, 1.9 * spb, sr, att=0.25, rel=0.5, vib=0.08, breath=0.03), t0 + 2 * h * spb,
                      g=0.12, pan=-0.1, rev=0.5, dly=0.2, grp="L6")


# =============================================================================
# track: gamer  (150 bpm, E minor, 8-bit)
# =============================================================================
_GAMER_A = ("E5:0.5 E5:0.25 G5:0.25 B5:0.5 A5:0.5 G5:0.5 F#5:0.5 G5:1  E5:0.5 G5:0.5 C6:1 B5:0.5 A5:0.5 G5:1  "
            "D5:0.5 G5:0.5 B5:1 A5:0.5 G5:0.5 D6:1  C6:0.5 B5:0.5 A5:0.5 F#5:0.5 D5:2  "
            "E5:0.25 F#5:0.25 G5:0.5 E5:0.5 B5:1 A5:0.5 G5:0.5 A5:0.5  G5:1 E5:0.5 C5:0.5 E5:0.5 G5:0.5 C6:1  "
            "A5:0.5 C6:0.5 E6:1 D6:0.5 C6:0.5 B5:0.5 A5:0.5  B5:0.5 A5:0.25 G5:0.25 F#5:0.5 D#5:0.5 B4:2")
_GAMER_B = ("G5:0.75 G5:0.75 E5:0.5 G5:0.5 A5:0.5 G5:1  F#5:0.75 F#5:0.75 D5:0.5 F#5:0.5 A5:0.5 D6:1  "
            "D6:0.75 B5:0.75 F#5:0.5 B5:0.5 D6:0.5 F#6:1  E6:1.5 D6:0.5 B5:1 G5:1  "
            "E5:0.25 G5:0.25 C6:0.25 E6:0.25 D6:0.5 C6:0.5 G5:1 E5:1  "
            "F#5:0.25 A5:0.25 D6:0.25 F#6:0.25 E6:0.5 D6:0.5 A5:1 F#5:1  D#6:1 B5:1 F#5:1 D#5:1  "
            "B5:0.5 B5:0.5 B5:0.5 r:0.5 B4:0.25 C#5:0.25 D#5:0.25 F#5:0.25 A5:0.25 B5:0.25 D#6:0.5")
_GAMER_CH = {"Em": ("E2", "E4 G4 B4"), "C": ("C2", "E4 G4 C5"), "G": ("G2", "D4 G4 B4"),
             "D": ("D2", "D4 F#4 A4"), "Am": ("A2", "E4 A4 C5"), "B": ("B1", "D#4 F#4 B4"),
             "Bm": ("B1", "D4 F#4 B4")}
_GAMER_SEC = {"intro": ["Em", "Em", "C", "B"], "A": ["Em", "C", "G", "D", "Em", "C", "Am", "B"],
              "B": ["C", "D", "Bm", "Em", "C", "D", "B", "B"], "brk": ["Em", "C", "Am", "B"]}
_EMIN = [4, 6, 7, 9, 11, 0, 2]


def _third_below(m):
    pc = m % 12
    if pc == 3:            # D# (leading tone) -> B
        return m - 4
    idx = min(range(7), key=lambda i: min((pc - _EMIN[i]) % 12, (_EMIN[i] - pc) % 12))
    tgt = _EMIN[(idx - 2) % 7]
    return m - ((pc - tgt) % 12 or 12)


def comp_gamer(S):
    sr, spb = S.sr, S.spb
    S.reverb, S.wet = (0.7, 0.01, 1.0), 0.35
    S.delay = (0.75 * spb, 0.3, 3000.0)
    mA, mB = mel(_GAMER_A, 32), mel(_GAMER_B, 32)
    s16 = spb / 4
    FORM = [("A", 8), ("B", 8), ("brk", 4), ("A2", 8)]

    def drums(t0, kick_steps, snare_steps, hat_steps, open_steps=(), hv=0.1):
        for i in kick_steps:
            S.add(chip_tri(N("A3"), 0.07, sr, quant=False, bend=-24.0), t0 + i * s16, g=0.55, grp="drums")
            S.add(chip_noise(0.05, sr, clock=4000.0, decay=0.012, var=1), t0 + i * s16, g=0.25, grp="drums")
        for i in snare_steps:
            S.add(chip_noise(0.2, sr, clock=11000.0, decay=0.07, var=2), t0 + i * s16, g=0.42, pan=0.05,
                  rev=0.2, grp="drums")
            S.add(chip_tri(N("A3"), 0.05, sr, quant=False, bend=-7.0), t0 + i * s16, g=0.25, grp="drums")
        for i in hat_steps:
            S.add(chip_noise(0.05, sr, clock=36000.0, short=True, decay=0.012, var=i % 3), t0 + i * s16,
                  g=hv * (1.0 if i % 4 == 0 else 0.7), pan=0.3, grp="drums")
        for i in open_steps:
            S.add(chip_noise(0.2, sr, clock=36000.0, short=True, decay=0.07, var=4), t0 + i * s16,
                  g=hv * 0.9, pan=0.3, grp="drums")

    for bar in range(S.n_bars):
        t0 = S.t(bar)
        if bar < 4:
            sec, ib = "intro", bar
        else:
            k = (bar - 4) % 28
            acc = 0
            for sec, ln in FORM:
                if k < acc + ln:
                    ib = k - acc
                    break
                acc += ln
        key = "A" if sec == "A2" else sec
        chname = _GAMER_SEC[key][ib]
        bass, vo = _GAMER_CH[chname]
        vo, b = V(vo), N(bass)
        if ib == 0 and sec != "intro":
            S.add(chip_noise(1.0, sr, clock=9000.0, decay=0.35, var=5), t0, g=0.28, pan=-0.1, rev=0.3, grp="drums")
        # triangle octave bass
        if sec == "brk":
            S.add(chip_tri(b, 2 * spb - 0.02, sr), t0, g=0.4, grp="bass")
            S.add(chip_tri(b, 2 * spb - 0.02, sr), t0 + 2 * spb, g=0.4, grp="bass")
        elif sec == "intro" and ib < 2:
            S.add(chip_tri(b, 4 * spb - 0.02, sr), t0, g=0.3, grp="bass")
        else:
            for i in range(8):
                S.add(chip_tri(b + (12 if i % 2 else 0), 0.45 * spb, sr), t0 + i * spb / 2, g=0.4, grp="bass")
        # arpeggios
        arp_notes = list(vo) + [vo[0] + 12]
        seqi = [0, 1, 2, 3, 2, 1, 0, 1, 2, 3, 2, 1, 0, 1, 2, 3]
        if sec in ("intro", "A", "A2", "brk"):
            duty = 0.125 if sec != "brk" else 0.5
            gg = {"A2": 0.1, "intro": 0.2}.get(sec, 0.12)
            for i in range(16):
                m = arp_notes[seqi[i]] + (12 if sec == "brk" else 0)
                S.add(chip_pulse(m, 0.8 * s16, sr, duty=duty, dec=0.05, sus=0.4, rel=0.01), t0 + i * s16,
                      g=gg, pan=0.35, rev=0.2, dly=0.15 if sec == "brk" else 0.0, grp="arp")
        if sec == "B":
            for i in (0, 3, 6, 10, 12, 14):
                S.add(chip_arp(tuple(m + 12 for m in vo), 0.9 * s16 * 2, sr, rate=60.0, duty=0.25),
                      t0 + i * s16, g=0.1, pan=0.3, rev=0.2, grp="arp")
        # lead
        if sec in ("A", "A2", "B"):
            src = mB if sec == "B" else mA
            duty = {"A": 0.25, "B": 0.125, "A2": 0.5}[sec]
            for (s, d, m) in in_bar(src, ib):
                note = chip_pulse(m, d * spb * 0.9, sr, duty=duty, vib=0.25 if d >= 1 else 0.0,
                                  pwm=0.5 if (sec == "A" and d >= 1) else 0.0, dec=0.15, sus=0.7,
                                  bend=-1.0 if d >= 1 else 0.0)
                S.add(note, t0 + s * spb, g=0.4, pan=-0.12, rev=0.2, dly=0.22, grp="lead")
                if sec == "A2":
                    S.add(chip_pulse(_third_below(m), d * spb * 0.9, sr, duty=0.25, dec=0.15, sus=0.6),
                          t0 + s * spb, g=0.2, pan=0.25, rev=0.2, grp="lead2")
        # drums
        fill = ib == 7 and sec != "intro"
        if sec == "intro":
            drums(t0, [0, 8] if ib >= 2 else [], [], list(range(0, 16, 2)))
            if ib == 3:
                for i in range(8, 16):
                    S.add(chip_noise(0.12, sr, clock=11000.0, decay=0.05, var=i), t0 + i * s16,
                          g=0.15 + 0.03 * (i - 8), rev=0.2, grp="drums")
        elif sec == "brk":
            drums(t0, [0], [8], [0, 4, 8, 12], hv=0.08)
            if ib == 3:
                for i in range(8, 16):
                    S.add(chip_noise(0.12, sr, clock=11000.0, decay=0.05, var=i), t0 + i * s16,
                          g=0.15 + 0.035 * (i - 8), rev=0.2, grp="drums")
        elif sec == "B":
            drums(t0, [0, 4, 8, 12], [4, 12] + ([15] if not fill else []), [1, 3, 5, 7, 9, 11, 13, 15],
                  open_steps=[2, 6, 10, 14] if not fill else [2, 6])
        else:
            drums(t0, [0, 3, 8, 10], [4, 12] if not fill else [4], list(range(0, 16, 2)) if not fill else [0, 2, 4, 6, 8, 10],
                  open_steps=[14] if ib in (3,) else [])
        if fill:
            for i, f in zip(range(12, 16), (N("A3"), N("F3"), N("D3"), N("A2"))):
                S.add(chip_noise(0.1, sr, clock=11000.0, decay=0.05, var=i), t0 + i * s16, g=0.3, grp="drums")
                S.add(chip_tri(f, 0.1, sr, quant=False, bend=-5.0), t0 + i * s16, g=0.35, grp="drums")


# =============================================================================
# track: cute  (128 bpm, C major, kawaii future-bass-lite)
# =============================================================================
_CUTE_A = ("A5:0.5 G5:0.5 E5:0.5 C5:0.5 E5:0.5 G5:0.5 A5:1  B5:0.5 A5:0.5 G5:0.5 E5:0.5 D5:1 G5:1  "
           "G5:0.5 A5:0.5 B5:0.5 D6:0.5 B5:1 G5:1  A5:1.5 G5:0.5 E5:1 C5:1  "
           "D5:0.5 F5:0.5 A5:0.5 C6:0.5 A5:0.5 F5:0.5 A5:1  C6:1 B5:1 D6:1 G5:1  "
           "E6:0.5 D6:0.5 C6:0.5 G5:0.5 E5:0.5 G5:0.5 B5:1  C6:1.5 Bb5:0.5 G5:1 E5:1")
_CUTE_B = ("C6:0.5 C6:0.5 A5:0.5 C6:0.5 D6:1 C6:1  B5:0.5 B5:0.5 G5:0.5 B5:0.5 D6:1 B5:1  "
           "C6:0.5 C6:0.5 A5:0.5 C6:0.5 E6:1 D6:0.5 C6:0.5  G5:2 E5:1 G5:1  "
           "C6:0.5 C6:0.5 A5:0.5 C6:0.5 D6:1 C6:1  B5:0.5 B5:0.5 G5:0.5 B5:0.5 D6:1 B5:1  "
           "B5:0.5 B5:0.5 G5:0.5 B5:0.5 C#6:1 A5:1  A5:0.5 A5:0.5 F5:0.5 A5:0.5 B5:1 D6:1")
_CUTE_CH = {"Fmaj7": ("F2", "F3 C4 E4 A4"), "G6": ("G2", "G3 D4 E4 B4"), "Em7": ("E2", "E3 B3 D4 G4"),
            "Am7": ("A2", "A3 E4 G4 C5"), "Dm7": ("D2", "D3 A3 C4 F4"), "G7sus4": ("G2", "G3 C4 D4 F4"),
            "G7": ("G2", "G3 B3 D4 F4"), "Cmaj7": ("C2", "C4 E4 G4 B4"), "C7": ("C2", "C4 E4 G4 Bb4"),
            "A7": ("A2", "A3 E4 G4 C#5")}
_CUTE_A_H = [[(0, 4, "Fmaj7")], [(0, 4, "G6")], [(0, 4, "Em7")], [(0, 4, "Am7")], [(0, 4, "Dm7")],
             [(0, 1, "G7sus4"), (1, 3, "G7")], [(0, 4, "Cmaj7")], [(0, 4, "C7")]]
_CUTE_B_H = [[(0, 4, "Fmaj7")], [(0, 4, "G6")], [(0, 4, "Am7")], [(0, 4, "Cmaj7")], [(0, 4, "Fmaj7")],
             [(0, 4, "G6")], [(0, 2, "Em7"), (2, 2, "A7")], [(0, 2, "Dm7"), (2, 2, "G7")]]
_PENTA_C = V("C6 D6 E6 G6 A6 C7")


def comp_cute(S):
    sr, spb = S.sr, S.spb
    S.reverb, S.wet = (1.4, 0.02, 1.0), 0.5
    S.delay = (0.75 * spb, 0.35, 5000.0)
    S.duck = (0.6, 0.17)
    mA, mB = mel(_CUTE_A, 32), mel(_CUTE_B, 32)
    s16 = spb / 4
    FORM = ["A", "B", "A2", "B2"]
    for bar in range(S.n_bars):
        t0 = S.t(bar)
        if bar < 4:
            sec, ib = "intro", bar
            harm = _CUTE_A_H[bar]
        else:
            k = (bar - 4) % 32
            sec, ib = FORM[k // 8], k % 8
            harm = (_CUTE_A_H if sec[0] == "A" else _CUTE_B_H)[ib]
        drums_on = sec != "intro"
        # sparkle glissando at section starts
        if ib == 0 or (sec == "intro" and ib == 3):
            base = t0 - (1.0 * spb if sec != "intro" else -2.0 * spb)
            for j, m in enumerate(_PENTA_C * 2):
                if j >= 10:
                    break
                mm = _PENTA_C[j % 6] + (12 if j >= 6 else 0) - 12
                S.add(mallet(mm, sr, "glock", decay=0.6), base + j * spb / 10, g=0.05 + 0.005 * j,
                      pan=-0.6 + 0.12 * j, rev=0.5, dly=0.3, grp="sparkle")
        for (b0, blen, nm) in harm:
            bass, vo = _CUTE_CH[nm]
            vo = V(vo)
            tt = t0 + b0 * spb
            # pad (ducked)
            for j, m in enumerate(vo):
                S.add(saw_pad(m, blen * spb, sr, fc=2600.0, att=0.08 if drums_on else 0.6, rel=0.4, voices=3,
                              detune=0.18, var=j), tt, g=0.085 if sec in ("B", "B2") else 0.065,
                      pan=(-0.5, -0.2, 0.2, 0.5)[j], rev=0.35, duck=True, grp="pad")
            # future-bass chord stabs in B
            if sec in ("B", "B2"):
                for sb in (0.0, 0.75, 1.5):
                    if sb < blen:
                        for j, m in enumerate(vo):
                            S.add(saw_pad(m + 12, 0.35 * spb, sr, fc=4500.0, att=0.004, rel=0.12, voices=5,
                                          detune=0.22, var=j, dec=0.15, sus=0.5), tt + sb * spb,
                                  g=0.12, pan=(-0.6, -0.2, 0.2, 0.6)[j], rev=0.3, grp="stabs")
            # plucky 8th arps in A
            if sec in ("A", "A2", "intro"):
                steps = int(blen * 2)
                for i in range(steps):
                    m = vo[[0, 2, 1, 3, 2, 1, 3, 2][i % 8] % len(vo)] + 12
                    S.add(pluck(m, 0.4 * spb, sr, bright=1.5, decay=0.35, pos=0.3, var=i % 3),
                          tt + i * spb / 2, g=0.1, pan=(0.35, -0.35)[i % 2], rev=0.3, dly=0.2, grp="pluck")
            # bouncy bass (ducked)
            if drums_on:
                r0 = N(bass)
                for (bb, dd, oo) in ((0.0, 0.45, 0), (0.75, 0.2, 12), (1.5, 0.4, 0)):
                    if bb < blen:
                        S.add(sine_bass(r0 + oo, dd * spb, sr, harm=0.35), tt + bb * spb, g=0.27,
                              duck=True, grp="bass")
                if blen > 2:
                    for (bb, dd, oo) in ((2.5, 0.4, 0), (3.0, 0.2, 12), (3.5, 0.4, 7)):
                        S.add(sine_bass(r0 + oo, dd * spb, sr, harm=0.35), tt + bb * spb, g=0.24,
                              duck=True, grp="bass")
        # melody
        if sec in ("A", "A2"):
            for (s, d, m) in in_bar(mA, ib):
                S.add(fm_bell(m, d * spb, sr, ratio=3.5, index=1.6, decay=0.7), t0 + s * spb, g=0.22,
                      pan=-0.05, rev=0.35, dly=0.25, grp="mel")
                S.add(mallet(m, sr, "glock", decay=0.9), t0 + s * spb, g=0.13, pan=0.1, rev=0.35, grp="mel")
        elif sec in ("B", "B2"):
            for (s, d, m) in in_bar(mB, ib):
                S.add(pluck(m, d * spb * 0.9, sr, bright=1.6, decay=0.5, pos=0.25), t0 + s * spb, g=0.26,
                      pan=0.0, rev=0.35, dly=0.2, grp="mel")
                S.add(fm_bell(m, d * spb, sr, ratio=3.5, index=1.2, decay=0.6), t0 + s * spb, g=0.1,
                      rev=0.3, grp="mel")
        elif sec == "intro":
            for (s, d, m) in in_bar(mA, ib):
                S.add(fm_bell(m, d * spb, sr, ratio=3.5, index=1.4, decay=0.8), t0 + s * spb, g=0.12,
                      pan=0.1, rev=0.5, dly=0.35, grp="mel")
        # vocal chops in A2 / B2
        if sec in ("A2", "B2") and ib % 2 == 1:
            vo0 = V(_CUTE_CH[harm[0][2]][1])
            for (b, j, vw) in ((1.5, 3, "a"), (2.25, 2, "o"), (3.0, 3, "a")):
                S.add(voice(vo0[j] + 12, 0.2 * spb, sr, vowel=vw, voices=1, att=0.01, rel=0.08, vib=0.0,
                            dec=0.1, sus=0.7), t0 + b * spb, g=0.16, pan=(-0.3, 0.3)[j % 2], rev=0.4,
                      dly=0.3, grp="chops")
        # sparkles
        if sec != "intro":
            for i in range(16):
                if S.rng.random() < (0.12 if sec in ("A2", "B2") else 0.06):
                    m = _PENTA_C[int(S.rng.integers(len(_PENTA_C)))]
                    S.add(mallet(m, sr, "glock", decay=0.5), t0 + i * s16, g=0.04, pan=float(S.rng.uniform(-0.8, 0.8)),
                          rev=0.5, dly=0.35, grp="sparkle")
        # drums
        if drums_on:
            for i in (0, 8, 11) if ib % 2 == 0 else (0, 6, 8):
                S.add(kick(sr, f_hi=170.0, f_lo=50.0, a_tau=0.2, click=0.3, drive=1.5), t0 + i * s16, g=0.5,
                      grp="drums")
                S.duck_times.append(t0 + i * s16)
            for i in (4, 12):
                S.add(clap(sr, var=i), t0 + i * s16, g=0.3, pan=0.05, rev=0.3, grp="drums")
                S.add(snare(sr, var=i, decay=0.1, bright=1.2), t0 + i * s16, g=0.15, rev=0.2, grp="drums")
            for i in range(2, 16, 4):
                S.add(hat(sr, var=i % 3, open_=(sec in ("B", "B2")), bright=1.0), t0 + i * s16,
                      g=0.07, pan=0.3, grp="drums")
            for i in range(16):
                S.add(shaker(sr, var=i % 4), t0 + i * s16 + S.hz(0.002), g=0.035 if i % 2 else 0.05, pan=-0.3,
                      grp="drums")


# =============================================================================
# track: chat  (110 bpm, G major, sparse plucks)
# =============================================================================
_CHAT_A = ("r:1 D5:0.5 B4:0.5 r:1 G4:0.5 r:0.5  r:1 E5:0.5 D5:0.5 r:1 B4:1  r:1 C5:0.5 E5:0.5 G5:0.5 r:1.5  "
           "F#5:0.5 r:0.5 E5:0.5 r:0.5 D5:1 r:1  r:2 B4:0.5 C5:0.5 D5:1  G5:0.5 r:0.5 E5:0.5 r:0.5 B4:1 r:1  "
           "r:1 A4:0.5 C5:0.5 E5:0.5 G5:0.5 r:1  F#5:0.5 r:0.5 A5:0.5 r:2.5")
_CHAT_B = ("r:2 G5:0.5 E5:0.5 r:1  r:4  r:2 A5:0.5 F#5:0.5 r:1  r:2.5 D5:0.5 E5:0.5 F#5:0.5  "
           "r:2 G5:0.5 E5:0.5 r:1  r:4  r:1 C5:0.5 E5:0.5 A5:1 r:1  B4:0.5 r:0.5 D5:0.5 r:0.5 G4:1 r:1")
_CHAT_CH = {"G": ("G2", "D4 G4 B4 D5"), "Em": ("E2", "E4 G4 B4 E5"), "C": ("C3", "C4 E4 G4 C5"),
            "D": ("D3", "D4 F#4 A4 D5"), "Am7": ("A2", "C4 E4 G4 A4"), "D7": ("D3", "C4 D4 F#4 A4"),
            "G/B": ("B2", "B3 D4 G4 B4")}
_CHAT_A_H = [[(0, 4, c)] for c in ("G", "Em", "C", "D", "G", "Em", "Am7")] + [[(0, 4, "D7")]]
_CHAT_B_H = [[(0, 4, c)] for c in ("C", "G/B", "Am7", "D", "C", "G/B")] + [[(0, 2, "Am7"), (2, 2, "D7")], [(0, 4, "G")]]


def comp_chat(S):
    sr, spb = S.sr, S.spb
    S.reverb, S.wet = (0.8, 0.012, 0.8), 0.45
    mA, mB = mel(_CHAT_A, 32), mel(_CHAT_B, 32)
    for bar in range(S.n_bars):
        t0 = S.t(bar)
        sec = "A" if (bar // 8) % 2 == 0 else "B"
        ib = bar % 8
        harm = (_CHAT_A_H if sec == "A" else _CHAT_B_H)[ib]
        for (b0, blen, nm) in harm:
            bass, vo = _CHAT_CH[nm]
            vo = V(vo)
            strums = [(0.0, 1.0, False), (2.5, 0.6, True)] if sec == "A" else [(0.0, 1.0, False), (1.5, 0.5, True), (3.0, 0.7, False)]
            for (sb, vel, up) in strums:
                if sb >= blen:
                    continue
                order = vo[::-1] if up else vo
                for j, m in enumerate(order[1:] if up else order):
                    S.add(pluck(m, 0.85 * spb, sr, bright=0.9, decay=0.5, pos=0.22, var=j, mute=0.06),
                          t0 + (b0 + sb) * spb + 0.011 * j + S.hz(0.003), g=0.07 * vel, pan=0.3 - 0.1 * j,
                          rev=0.3, grp="uke")
            S.add(pluck(N(bass), 0.5 * spb, sr, bright=0.5, decay=0.35, pos=0.3, mute=0.05), t0 + b0 * spb,
                  g=0.17, pan=-0.05, grp="bass")
            if blen > 2:
                S.add(pluck(N(bass) + 7, 0.4 * spb, sr, bright=0.5, decay=0.3, pos=0.3, mute=0.05),
                      t0 + (b0 + 2) * spb, g=0.12, pan=-0.05, grp="bass")
        src = mA if sec == "A" else mB
        for (s, d, m) in in_bar(src, ib):
            if sec == "A":
                S.add(pluck(m, min(d, 0.9) * spb, sr, bright=0.7, decay=0.3, pos=0.12, mute=0.05), t0 + s * spb + S.hz(0.003),
                      g=0.22, pan=-0.2, rev=0.35, grp="mel")
            else:
                S.add(mallet(m, sr, "marimba", decay=0.35), t0 + s * spb, g=0.2, pan=-0.2, rev=0.35, grp="mel")
        for i in range(4):
            S.add(shaker(sr, var=i, decay=0.03), t0 + (i + 0.5) * spb + S.hz(0.004), g=0.09, pan=0.4, grp="perc")
        if sec == "B":
            for b in (1, 3):
                S.add(rim(sr, var=b, f=1300.0), t0 + b * spb, g=0.16, pan=-0.3, rev=0.3, grp="perc")


# =============================================================================
# track: finale  (116 bpm, D major -> E major, maximal pomp)
# =============================================================================
_FIN_CH = {  # D-relative: bass, alternate, horn voicing, choir voicing
    "D": ("D2", "A1", "F#3 A3 D4", "D3 A3 D4 F#4"), "G/B": ("B1", "D2", "G3 B3 D4", "B2 G3 D4 G4"),
    "G": ("G1", "D2", "G3 B3 D4", "G2 D3 B3 G4"), "D/F#": ("F#2", "A1", "F#3 A3 D4", "F#3 A3 D4 A4"),
    "A": ("A1", "E2", "E3 A3 C#4", "A2 E3 C#4 A4"), "C": ("C2", "G1", "E3 G3 C4", "C3 G3 C4 E4"),
    "Bm": ("B1", "F#2", "F#3 B3 D4", "B2 F#3 D4 F#4"), "Em7": ("E2", "B1", "G3 B3 D4", "E3 B3 D4 G4"),
}
_FIN_H = [[(0, 2, "D"), (2, 2, "G/B")], [(0, 2, "G"), (2, 2, "D/F#")], [(0, 2, "D"), (2, 2, "G")],
          [(0, 2, "A"), (2, 2, "D")], [(0, 2, "D"), (2, 2, "G/B")], [(0, 2, "G"), (2, 2, "C")],
          [(0, 2, "D"), (2, 1, "A"), (3, 1, "G")], [(0, 2, "A"), (2, 2, "D")]]
_FIN_BR_H = [[(0, 4, "Bm")], [(0, 4, "G")], [(0, 4, "Em7")], [(0, 4, "A")]]
_FIN_BR = "B4:1 F#5:1.5 E5:0.5 D5:1  D5:1 B4:1 G4:2  E4:1 B4:1.5 A4:0.5 G4:1  A4:1 C#5:1 E5:2"


def comp_finale(S):
    sr, spb = S.sr, S.spb
    S.reverb, S.wet = (2.8, 0.03, 0.8), 0.55
    theme = mel(ARCH_MAJOR, 32)
    brid = mel(_FIN_BR, 16)
    CH = {k: v[:3] for k, v in _FIN_CH.items()}
    P16 = [1.0, 0.3, 0.4, 0.5, 0.8, 0.3, 0.5, 0.35, 1.0, 0.3, 0.4, 0.5, 0.8, 0.45, 0.6, 0.75]
    # form: intro 2, T1 (D) 8, T2 (E) 8, then loop [bridge (E) 4, T3 (E) 8]
    for bar in range(S.n_bars):
        t0 = S.t(bar)
        if bar < 2:
            if bar == 0:
                timp_roll(S, N("D2"), t0, t0 + 2 * S.bar, 0.1, 0.9, g=0.4)
                for j, m in enumerate(V(_FIN_CH["D"][3])):
                    S.add(voice(m, 2 * S.bar, sr, att=2.5, rel=0.6, var=j), t0, g=0.13, rev=0.5, grp="choir")
                nz = crash(sr, dur=4.2, var=7)[:, ::-1]
                S.add(_f32(nz[:, : int(2 * S.bar * sr)] if nz.shape[1] > int(2 * S.bar * sr) else nz),
                      t0 + max(0.0, 2 * S.bar - nz.shape[1] / sr), g=0.18, rev=0.3, grp="drums")
            else:
                for (s, d, m) in mel("A3:0.333 A3:0.333 A3:0.334 D4:1 F#4:1 A4:1", 4):
                    S.add(brass(m, d * spb * 0.9, sr, bright=1.1), t0 + s * spb, g=0.48, rev=0.35, grp="mel")
                    S.add(brass(m + 12, d * spb * 0.9, sr, bright=1.0, var=1), t0 + s * spb, g=0.2, rev=0.35,
                          grp="mel")
                snare_roll(S, t0, t0 + S.bar, 0.2, 1.0, rate=20.0, g=0.3)
            continue
        k = bar - 2
        if k < 16:
            sec, ib, key = ("T1" if k < 8 else "T2"), k % 8, (0 if k < 8 else 2)
        else:
            kk = (k - 16) % 12
            sec, ib, key = ("BR", kk, 2) if kk < 4 else ("T3", kk - 4, 2)
        harm = _FIN_BR_H[ib] if sec == "BR" else _FIN_H[ib]
        if ib in (0, 4) and sec != "BR" or (sec == "BR" and ib == 0):
            S.add(crash(sr, var=ib + key), t0, g=0.36, rev=0.4, grp="drums")
            S.add(crash(sr, var=ib + key + 1), t0 + 0.01, g=0.2, pan=0.4, rev=0.4, grp="drums")
        _march_harmony(S, bar, harm, CH, strong=True, horn_g=0.22, bass_g=0.28, str_g=0.09, key=key, bright=0.7)
        # choir aah
        for (b0, blen, nm) in harm:
            for j, m in enumerate(V(_FIN_CH[nm][3])):
                S.add(voice(m + key, blen * spb, sr, att=0.18, rel=0.5, var=j), t0 + b0 * spb, g=0.16,
                      pan=(-0.5, -0.15, 0.15, 0.5)[j], rev=0.5, grp="choir")
        # melody
        if sec == "BR":
            for (s, d, m) in in_bar(brid, ib):
                S.add(brass(m + key, d * spb * 0.95, sr, bright=0.9), t0 + s * spb, g=0.6, rev=0.4, grp="mel")
                S.add(brass(m + key - 12, d * spb * 0.95, sr, bright=0.6, var=1), t0 + s * spb, g=0.24,
                      pan=-0.2, rev=0.4, grp="mel")
            for i in range(4):
                S.add(tom(sr, f=(110.0, 98.0, 87.0, 73.0)[i]), t0 + i * spb, g=0.35 * (0.7 + 0.1 * ib), pan=-0.2 + 0.13 * i,
                      rev=0.4, grp="drums")
                S.add(bass_drum(sr, var=i, slap=0.5), t0 + i * spb, g=0.35, rev=0.4, grp="drums")
            if ib == 3:
                snare_roll(S, t0, t0 + S.bar, 0.3, 1.0, rate=20.0, g=0.32)
                timp_roll(S, N("A1") + key, t0, t0 + S.bar, 0.3, 1.0)
        else:
            for (s, d, m) in in_bar(theme, ib):
                tt = t0 + s * spb
                S.add(brass(m + key, d * spb * 0.92, sr, bright=1.1), tt, g=0.62, rev=0.35, grp="mel")
                S.add(brass(m + key - 12, d * spb * 0.92, sr, bright=0.8, var=1), tt, g=0.22, pan=-0.25,
                      rev=0.35, grp="mel")
                if sec != "T1":
                    S.add(mallet(m + key + 12, sr, "glock"), tt, g=0.09, pan=0.3, rev=0.4, grp="glock")
            _march_drums(S, bar, P16, bd_beats=(0, 1, 2, 3) if sec == "T3" else (0, 2), g=0.22)
            S.add(timpani(N("D2") + key if harm[0][2] != "A" else N("A1") + key, sr, var=bar % 6), t0, g=0.28,
                  pan=-0.2, rev=0.4, grp="timp")
            if sec == "T1" and ib == 7:
                snare_roll(S, t0 + 2 * spb, t0 + 4 * spb, 0.3, 1.0, rate=22.0, g=0.3)
                timp_roll(S, N("A1"), t0 + 2 * spb, t0 + 4 * spb, 0.3, 1.0)


# =============================================================================
# track: credits  (84 bpm, D major, warm)
# =============================================================================
_CRED_CH = {
    "Dmaj9": ("D2", "F#3 A3 C#4 E4"), "Gmaj7/B": ("B1", "F#3 G3 B3 D4"), "Gmaj9": ("G1", "F#3 A3 B3 D4"),
    "F#m7": ("F#2", "E3 A3 C#4"), "Dmaj7": ("D2", "F#3 A3 C#4"), "Em7": ("E2", "G3 B3 D4 E4"),
    "A9": ("A1", "G3 B3 C#4 E4"), "Bm9": ("B1", "A3 C#4 D4 F#4"), "Gmaj7": ("G1", "F#3 B3 D4"),
    "Cmaj7#11": ("C2", "E3 F#3 B3"), "A7": ("A1", "G3 C#4 E4"), "A7sus4": ("A1", "G3 D4 E4"),
    "B7": ("B1", "A3 D#4 F#4"), "Em9": ("E2", "G3 B3 D4 F#4"),
}
_CRED_T = [[(0, 2, "Dmaj9"), (2, 2, "Gmaj7/B")], [(0, 2, "Gmaj9"), (2, 2, "F#m7")],
           [(0, 2, "Dmaj7"), (2, 2, "Em7")], [(0, 2, "A9"), (2, 2, "Dmaj9")],
           [(0, 2, "Bm9"), (2, 2, "Gmaj7")], [(0, 2, "Gmaj9"), (2, 2, "Cmaj7#11")],
           [(0, 2, "Dmaj7"), (2, 1, "A7"), (3, 1, "Gmaj7")], [(0, 2, "A7sus4"), (2, 2, "Dmaj9")]]
_CRED_I = [[(0, 4, "Gmaj7")], [(0, 4, "F#m7")], [(0, 4, "Em7")], [(0, 2, "A7sus4"), (2, 2, "A7")],
           [(0, 4, "Gmaj7")], [(0, 2, "F#m7"), (2, 2, "B7")], [(0, 4, "Em9")], [(0, 4, "A7sus4")]]


def comp_credits(S):
    sr, spb = S.sr, S.spb
    S.reverb, S.wet = (2.2, 0.025, 0.6), 0.6
    S.delay = (1.5 * spb, 0.3, 2500.0)
    theme = mel(ARCH_MAJOR, 32)
    FORM = ["T", "I", "T2", "I2"]
    for bar in range(S.n_bars):
        t0 = S.t(bar)
        if bar < 2:
            sec, ib = "intro", bar
            harm = [(0, 4, "Dmaj9")] if bar == 0 else [(0, 4, "A7sus4")]
        else:
            k = (bar - 2) % 32
            sec, ib = FORM[k // 8], k % 8
            harm = (_CRED_T if sec[0] == "T" else _CRED_I)[ib]
        for (b0, blen, nm) in harm:
            bass, vo = _CRED_CH[nm]
            vo = V(vo)
            tt = t0 + b0 * spb
            for j, m in enumerate(vo):
                S.add(saw_pad(m, blen * spb, sr, fc=900.0, att=0.8, rel=1.2, voices=3, detune=0.08, var=j), tt,
                      g=0.08, pan=(-0.5, -0.15, 0.15, 0.5)[j], rev=0.5, grp="pad")
            if sec[0] == "I":
                seqi = [0, 1, 2, 3, 2, 1, 2, 3] if sec == "I" else [0, 2, 1, 3, 0, 2, 1, 3]
                for i in range(int(blen * 2)):
                    m = vo[seqi[i % 8] % len(vo)] + 12
                    S.add(epiano(m, 0.9 * spb, sr, var=i % 3, bright=0.7), tt + i * spb / 2 + S.hz(0.006),
                          g=0.15 * (1.0 if i % 2 == 0 else 0.75), pan=(-0.3, 0.3)[i % 2], rev=0.4, dly=0.2,
                          grp="keys")
            else:
                hits = [(0.0, min(blen, 2.0) - 0.1, 0.8)]
                if blen >= 4:
                    hits.append((2.5, 1.4, 0.5))
                for (b, d, vel) in hits:
                    if b >= blen:
                        continue
                    for j, m in enumerate(vo):
                        S.add(epiano(m, d * spb, sr, var=j, bright=0.8), tt + b * spb + 0.02 * j + S.hz(0.005),
                              g=0.15 * vel, pan=-0.25 + 0.15 * j, rev=0.4, grp="keys")
            r0 = N(bass)
            if r0 < N("C2"):
                r0 += 12
            S.add(sine_bass(r0, blen * spb * 0.97, sr, att=0.03, rel=0.35, harm=0.12, dec=1.5, sus=0.6), tt,
                  g=0.16, grp="bass")
        if sec == "T":
            for (s, d, m) in in_bar(theme, ib):
                S.add(flute(m, d * spb * 0.95, sr, var=int(s)), t0 + s * spb + S.hz(0.008), g=0.22, pan=0.0,
                      rev=0.45, dly=0.2, grp="mel")
        elif sec == "T2":
            for (s, d, m) in in_bar(theme, ib):
                S.add(fm_bell(m + 12, d * spb, sr, ratio=3.0, index=1.0, decay=1.3), t0 + s * spb, g=0.11,
                      pan=0.1, rev=0.5, dly=0.25, grp="mel")
                S.add(epiano(m, d * spb, sr, bright=1.0), t0 + s * spb, g=0.12, pan=-0.1, rev=0.4, grp="mel")
        elif sec[0] == "I" and ib % 2 == 0:
            vo0 = V(_CRED_CH[harm[0][2]][1])
            S.add(mallet(vo0[-1] + 24, sr, "vibe", decay=2.0), t0 + 1.0 * spb, g=0.05, pan=0.4, rev=0.6, dly=0.3,
                  grp="mel")
        if sec in ("T2", "I2"):
            for b in (1, 3):
                S.add(shaker(sr, var=b, decay=0.07), t0 + b * spb, g=0.05, pan=0.3, rev=0.3, grp="perc")
                S.add(snare(sr, var=b, decay=0.2, tone=0.1, bright=0.35), t0 + b * spb, g=0.05, rev=0.3, grp="perc")
            S.add(kick(sr, f_hi=90.0, f_lo=45.0, a_tau=0.25, click=0.02), t0, g=0.25, grp="perc")


# =============================================================================
# registry
# =============================================================================
TRACKS: dict[str, dict] = {
    "hum": {"bpm": 60.0, "key": "D minor", "beats_per_bar": 4,
            "desc": "cold-open CRT hum: 60 Hz mains buzz, faint 15.7 kHz flyback whine, dark slow pad"},
    "anthem": {"bpm": 108.0, "key": "D minor -> F major", "beats_per_bar": 4,
               "desc": "over-the-top propaganda march introducing the Arch theme (A-D-C-B head motif)"},
    "lofi": {"bpm": 88.0, "key": "C major / D dorian", "beats_per_bar": 4,
             "desc": "chill terminal lo-fi chiptune: swung hats, FM keys, soft square lead, tape wow"},
    "tension": {"bpm": 120.0, "key": "C minor", "beats_per_bar": 4,
                "desc": "OBJECTION! courtroom tension: plucked ostinato, line-cliche bass, sneaky reed"},
    "wiki": {"bpm": 100.0, "key": "A major pentatonic", "beats_per_bar": 4,
             "desc": "hypnotic phasing marimbas, layers add in every 4 bars (hyperfocus)"},
    "gamer": {"bpm": 150.0, "key": "E minor", "beats_per_bar": 4,
              "desc": "hype 8-bit: pulse leads with duty changes, frame arps, triangle octave bass, noise drums"},
    "cute": {"bpm": 128.0, "key": "C major", "beats_per_bar": 4,
             "desc": "kawaii bubblegum future-bass-lite: bells, plucks, sidechained supersaws, sparkles"},
    "chat": {"bpm": 110.0, "key": "G major", "beats_per_bar": 4,
             "desc": "sparse playful ukulele/pizzicato loop for the family group chat"},
    "finale": {"bpm": 116.0, "key": "D major -> E major", "beats_per_bar": 4,
               "desc": "triumphant Arch theme with choir, big drums, crashes and a key change"},
    "credits": {"bpm": 84.0, "key": "D major", "beats_per_bar": 4,
                "desc": "warm relaxed Arch theme on flute/e-piano with soft pad"},
}

_COMPOSERS = {"hum": comp_hum, "anthem": comp_anthem, "lofi": comp_lofi, "tension": comp_tension,
              "wiki": comp_wiki, "gamer": comp_gamer, "cute": comp_cute, "chat": comp_chat,
              "finale": comp_finale, "credits": comp_credits}

# master gains calibrated so a 60 s render sits at the TRACKS[...]["rms_db"] target
_GAIN = {"hum": 0.293, "anthem": 0.462, "lofi": 0.765, "tension": 0.682, "wiki": 0.608, "gamer": 0.485,
         "cute": 0.489, "chat": 2.347, "finale": 0.352, "credits": 0.831}
_TARGET_DB = {"hum": -22.0}
for _k, _v in TRACKS.items():
    _v["rms_db"] = _TARGET_DB.get(_k, -19.0)
    _v["bar_sec"] = 60.0 / _v["bpm"] * _v["beats_per_bar"]
    _v["gain"] = _GAIN[_k]

_CACHED = [brass, saw_pad, voice, pluck, epiano, fm_bell, mallet, chip_pulse, chip_arp, chip_tri, chip_noise,
           soft_lead, flute, sine_bass, synth_bass, kick, snare, hat, crash, timpani, bass_drum, clap, shaker,
           rim, tick, tom]


def clear_caches():
    for f in _CACHED:
        f.cache_clear()


def render_track(name: str, duration: float, sr: int = 48000, seed: int = 0) -> np.ndarray:
    """Render track `name` for `duration` seconds.

    Returns float32 array of shape (round(duration*sr), 2), peak <= 0.9, with a ~50 ms
    fade-in and ~1.2 s fade-out.  Deterministic for a given (name, duration, sr, seed)."""
    if name not in TRACKS:
        raise KeyError(f"unknown track {name!r}; choose from {sorted(TRACKS)}")
    duration = float(duration)
    n_out = int(round(duration * sr))
    if n_out <= 0:
        return np.zeros((0, 2), np.float32)
    info = TRACKS[name]
    S = Song(name, duration, sr, seed, info["bpm"], info["beats_per_bar"])
    try:
        _COMPOSERS[name](S)
        out = S.render(_GAIN[name])
    finally:
        clear_caches()
    if DEBUG and S.stats:
        import pyloudnorm as pyln
        meter = pyln.Meter(sr)
        ref = meter.integrated_loudness(out.astype(np.float64) / _GAIN[name])
        res = []
        for k, v in S.stats.items():
            x = v[:, : n_out].T.astype(np.float64)
            res.append((k, meter.integrated_loudness(x) - ref))
        print("  stems (LU rel. mix):", ", ".join(f"{k} {v:+.1f}" for k, v in sorted(res, key=lambda kv: -kv[1])))
    assert out.shape == (n_out, 2)
    return out


def _write(path, x, sr):
    import soundfile as sf
    os.makedirs(os.path.dirname(path), exist_ok=True)
    sf.write(path, x, sr, subtype="PCM_16")


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 1
    sr = 48000
    if argv[1] == "all":
        for name in TRACKS:
            t = time.time()
            x = render_track(name, 40.0, sr)
            p = os.path.join(MUSIC_DIR, f"preview_{name}.wav")
            _write(p, x, sr)
            rms = 20 * np.log10(np.sqrt(np.mean(x.astype(np.float64) ** 2)) + 1e-12)
            print(f"{name:8s} {time.time() - t:5.1f}s  rms {rms:6.1f} dBFS  peak {np.abs(x).max():.3f}  -> {p}")
        return 0
    name = argv[1]
    dur = float(argv[2]) if len(argv) > 2 else 40.0
    p = argv[3] if len(argv) > 3 else os.path.join(MUSIC_DIR, f"{name}.wav")
    t = time.time()
    x = render_track(name, dur, sr)
    _write(p, x, sr)
    rms = 20 * np.log10(np.sqrt(np.mean(x.astype(np.float64) ** 2)) + 1e-12)
    print(f"{name}: {dur}s in {time.time() - t:.1f}s  rms {rms:.1f} dBFS  peak {np.abs(x).max():.3f} -> {p}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
