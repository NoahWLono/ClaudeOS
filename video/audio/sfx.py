#!/usr/bin/env python3
"""
Synthesized sound effects for the Arch Linux propaganda film (no samples).

    python3 sfx.py            -> writes every effect to ../assets/sfx/<name>.wav
    python3 sfx.py boom pop   -> only the named effects

Output: 48 kHz stereo 16-bit PCM, peak -1 dBFS, trailing silence trimmed, micro fades.
Reuses the oscillators / drums / reverb from music.py.
"""
from __future__ import annotations

import importlib.util
import os
import sys

import numpy as np
import soundfile as sf
from scipy import signal

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.normpath(os.path.join(HERE, "..", "assets", "sfx"))
_spec = importlib.util.spec_from_file_location("music", os.path.join(HERE, "music.py"))
M = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(M)

SR = 48000
TWO_PI = 2.0 * np.pi
PEAK = 10 ** (-1.0 / 20.0)


# =============================================================================
# helpers
# =============================================================================
def T(sec):
    return np.arange(int(round(sec * SR))) / SR


def rng(name):
    return M._rng("sfx", name)


def noise(n, r):
    return r.standard_normal(n)


def filt(x, kind, f, order=2):
    return M.filt(x, kind, f, SR, order)


def svf(x, fc, q=0.7, mode="bp"):
    """TPT state-variable filter with a per-sample cutoff (time-varying sweeps)."""
    n = len(x)
    fc = np.clip(np.broadcast_to(np.asarray(fc, float), (n,)), 10.0, 0.45 * SR)
    g = np.tan(np.pi * fc / SR)
    k = 1.0 / q
    a1 = 1.0 / (1.0 + g * (g + k))
    a2 = g * a1
    a3 = g * a2
    xs, A1, A2, A3 = x.tolist(), a1.tolist(), a2.tolist(), a3.tolist()
    y = [0.0] * n
    ic1 = ic2 = 0.0
    for i in range(n):
        v3 = xs[i] - ic2
        v1 = A1[i] * ic1 + A2[i] * v3
        v2 = ic2 + A2[i] * ic1 + A3[i] * v3
        ic1 = 2.0 * v1 - ic1
        ic2 = 2.0 * v2 - ic2
        if mode == "bp":
            y[i] = v1
        elif mode == "lp":
            y[i] = v2
        else:
            y[i] = xs[i] - k * v1 - v2
    return np.array(y)


def pan_st(x, pan=0.0):
    """mono -> stereo (2, n) with constant-power pan (pan may be an array)."""
    th = (np.asarray(pan) + 1.0) * np.pi / 4.0
    return np.stack([x * np.cos(th), x * np.sin(th)]) * np.sqrt(2.0)


def st(x):
    x = np.asarray(x, dtype=np.float64)
    return np.stack([x, x]) if x.ndim == 1 else x


def place(buf, x, t, g=1.0):
    """add stereo/mono x into stereo buf (2, n) at time t."""
    x = st(x)
    i = int(round(t * SR))
    if i < 0:
        x, i = x[:, -i:], 0
    n = min(x.shape[1], buf.shape[1] - i)
    if n > 0:
        buf[:, i:i + n] += g * x[:, :n]
    return buf


def reverb(x, rt60=1.2, mix=0.25, pre=0.015, bright=0.8, hp=200.0):
    x = st(x)
    ir = M._ir(SR, float(rt60), float(pre), float(bright))
    w = filt(x, "high", hp)
    wet = np.stack([signal.fftconvolve(w[c], ir[c]) for c in range(2)])
    out = np.zeros((2, wet.shape[1]))
    out[:, : x.shape[1]] += x
    return out + mix * wet


def env_ar(n, att, rel_start, rel):
    t = np.arange(n) / SR
    e = np.clip(t / max(att, 1e-4), 0, 1)
    m = t >= rel_start
    e[m] *= np.clip(1.0 - (t[m] - rel_start) / rel, 0, 1) ** 2
    return e


def finalize(x, fade_in=0.001, fade_out=0.02, thresh_db=-60.0, min_len=0.0):
    """stereo, trim trailing silence, micro-fades, peak-normalize to -1 dBFS."""
    x = st(x).astype(np.float64)
    a = np.max(np.abs(x), axis=0)
    pk = a.max()
    if pk <= 0:
        raise ValueError("silent effect")
    above = np.nonzero(a > pk * 10 ** (thresh_db / 20.0))[0]
    first, last = above[0], above[-1]
    last = max(last + int(0.005 * SR), int(min_len * SR))
    x = x[:, first: min(x.shape[1], last + 1)]
    n = x.shape[1]
    ni, no = max(1, int(fade_in * SR)), max(1, int(min(fade_out, 0.3 * n / SR) * SR))
    x[:, :ni] *= (0.5 - 0.5 * np.cos(np.pi * np.arange(ni) / ni))
    x[:, n - no:] *= (0.5 + 0.5 * np.cos(np.pi * np.arange(1, no + 1) / no))
    x *= PEAK / np.max(np.abs(x))
    assert np.all(np.isfinite(x))
    return x


# =============================================================================
# effects
# =============================================================================
def fx_boom():
    r = rng("boom")
    t = T(1.7)
    n = len(t)
    f = 34.0 + (125.0 - 34.0) * np.exp(-t / 0.12)
    sub = np.sin(TWO_PI * np.cumsum(f) / SR) * np.exp(-t / 0.55)
    punch = filt(noise(n, r), "low", 1800.0) * np.exp(-t / 0.018) * 0.7
    thump = np.sin(TWO_PI * 78.0 * t) * np.exp(-t / 0.09) * 0.5
    x = sub + punch + thump
    x = np.tanh(2.2 * x) / np.tanh(2.2)
    x *= 1.0 - np.exp(-t / 0.0005)
    y = reverb(x, rt60=1.1, mix=0.22, bright=0.6, hp=120.0)
    return finalize(y, fade_out=0.25)


def _sweep_noise(dur, f_path, q, amp, pan_path, name):
    r = rng(name)
    n = int(dur * SR)
    u = np.linspace(0, 1, n)
    fc = np.interp(u, *zip(*f_path))
    outs = []
    for ch in range(2):
        y = svf(noise(n, r), fc * (1.0 + 0.04 * ch), q=q, mode="bp")
        outs.append(y)
    e = np.interp(u, *zip(*amp))
    p = np.interp(u, *zip(*pan_path))
    th = (p + 1.0) * np.pi / 4.0
    return np.stack([outs[0] * e * np.cos(th), outs[1] * e * np.sin(th)]) * np.sqrt(2.0)


def fx_whoosh():
    x = _sweep_noise(0.55, [(0, 300), (0.42, 2600), (1, 500)], 1.3,
                     [(0, 0), (0.42, 1.0), (0.8, 0.25), (1, 0)], [(0, -0.7), (1, 0.7)], "whoosh")
    return finalize(reverb(x, rt60=0.6, mix=0.12), fade_out=0.05)


def fx_swoosh_up():
    x = _sweep_noise(0.65, [(0, 250), (0.6, 2500), (1, 8000)], 1.6,
                     [(0, 0), (0.7, 0.6), (0.93, 1.0), (1, 0)], [(0, -0.3), (1, 0.3)], "swoosh")
    t = T(0.65)
    f = 300.0 * (5.0 ** (t / 0.65))
    riser = 0.12 * np.sin(TWO_PI * np.cumsum(f) / SR) * (t / 0.65) ** 2
    x += st(riser)
    return finalize(reverb(x, rt60=0.5, mix=0.1), fade_out=0.03)


def _key(name, body_f, thock_f, lvl=1.0, rel_gap=0.075, heavy=False, r=None):
    r = r or rng(name)
    dur = 0.26 if heavy else 0.16
    t = T(dur)
    n = len(t)
    nz = noise(n, r)
    click = filt(nz, "high", 2500.0) * np.exp(-t / 0.0012)
    body = filt(nz, "bp", (body_f * 0.85, body_f * 1.15)) * np.exp(-t / 0.010) * 2.5
    th_tau = 0.045 if heavy else 0.022
    thock = (np.sin(TWO_PI * thock_f * t) * np.exp(-t / th_tau) * 0.6
             + filt(nz, "bp", (thock_f * 0.7, thock_f * 1.6)) * np.exp(-t / th_tau) * 1.2)
    y = click + body + thock
    if heavy:  # stabilizer rattle
        for d, a in ((0.008, 0.35), (0.016, 0.25)):
            m = t >= d
            y[m] += a * filt(nz, "bp", (3000.0, 7000.0))[: m.sum()] * np.exp(-(t[m] - d) / 0.003)
    m = t >= rel_gap                           # key release (up-stroke), quieter
    y[m] += 0.28 * (filt(nz, "bp", (body_f * 1.1, body_f * 1.5))[: m.sum()] * np.exp(-(t[m] - rel_gap) / 0.006))
    y *= 1.0 - np.exp(-t / 0.0002)
    return y * lvl


def fx_key1():
    return finalize(reverb(pan_st(_key("key1", 3200.0, 380.0), -0.1), rt60=0.3, mix=0.05), fade_out=0.01)


def fx_key2():
    return finalize(reverb(pan_st(_key("key2", 2500.0, 300.0), 0.05), rt60=0.3, mix=0.05), fade_out=0.01)


def fx_key3():
    return finalize(reverb(pan_st(_key("key3", 4200.0, 470.0, rel_gap=0.06), 0.15), rt60=0.3, mix=0.05),
                    fade_out=0.01)


def fx_enter():
    y = _key("enter", 2000.0, 170.0, heavy=True, rel_gap=0.11)
    return finalize(reverb(pan_st(y, 0.2), rt60=0.35, mix=0.07), fade_out=0.015)


def fx_typing():
    r = rng("typing")
    buf = np.zeros((2, int(1.62 * SR)))
    t, i = 0.01, 0
    while t < 1.46:
        space = i % 6 == 5
        if space:
            k = _key("sp", 1700.0, 210.0, heavy=True, rel_gap=0.09, r=np.random.default_rng(1000 + i))
            pan = 0.0
        else:
            body = float(r.choice([2500.0, 3200.0, 4200.0])) * r.uniform(0.9, 1.1)
            k = _key("k", body, r.uniform(280.0, 480.0), lvl=r.uniform(0.6, 1.0),
                     rel_gap=r.uniform(0.05, 0.09), r=np.random.default_rng(2000 + i))
            pan = r.uniform(-0.35, 0.35)
        place(buf, pan_st(k, pan), t)
        gap = r.lognormal(np.log(0.075), 0.35)
        if r.random() < 0.08:
            gap += 0.12
        t += gap
        i += 1
    return finalize(reverb(buf, rt60=0.3, mix=0.05), fade_out=0.03)


def _horn_blast(dur, r, vib=0.0):
    t = T(dur + 0.08)
    n = len(t)
    bend = -1.2 * np.exp(-t / 0.035)
    wob = vib * np.sin(TWO_PI * 5.5 * t) * np.clip((t - 0.2) / 0.3, 0, 1)
    y = np.zeros(n)
    for f0, a in ((466.2, 1.0), (469.0, 0.8), (587.3, 0.7), (698.5, 0.45)):
        f = f0 * 2.0 ** ((bend + wob) / 12.0)
        dt = f / SR
        ph = M._frac(np.cumsum(dt) + r.uniform())
        y += a * M.saw_blep(ph, dt)
    y = np.tanh(2.8 * y / 2.0)
    y = filt(y, "bp", (380.0, 5200.0), 2) + 0.6 * filt(y, "bp", (1300.0, 2100.0), 2)
    y *= env_ar(n, 0.012, dur, 0.06)
    return y


def fx_airhorn():
    r = rng("airhorn")
    buf = np.zeros((2, int(2.3 * SR)))
    for t0, d, v in ((0.0, 0.17, 0.0), (0.27, 0.17, 0.0), (0.54, 1.25, 0.25)):
        place(buf, pan_st(_horn_blast(d, r, v), 0.0), t0)
    return finalize(reverb(buf, rt60=0.9, mix=0.18), fade_out=0.08)


def fx_record_scratch():
    r = rng("scratch")
    src_t = T(3.0)
    src = np.zeros(len(src_t))
    for m in (48, 55, 64, 70):
        f = M.mtof(m)
        dt = np.full(len(src_t), f / SR)
        src += 0.25 * M.saw_blep(M._frac(np.cumsum(dt) + r.uniform()), dt)
    beat = (src_t % 0.25) / 0.25
    src += 0.8 * np.sin(TWO_PI * 60 * src_t) * np.exp(-beat * 0.25 / 0.08)
    src += 0.3 * filt(noise(len(src_t), r), "high", 6000.0) * np.exp(-((src_t + 0.125) % 0.25) / 0.02)
    src = filt(src, "low", 6000.0)
    keys = [(0.0, 1.0), (0.05, 1.0), (0.11, -2.8), (0.2, 2.6), (0.3, -2.2), (0.42, 0.7), (0.56, 0.0), (0.7, 0.0)]
    t = T(0.7)
    rate = np.interp(t, *zip(*keys))
    rate = np.convolve(rate, np.ones(480) / 480, mode="same")
    pos = 1.0 * SR + np.cumsum(rate)
    y = np.interp(pos, np.arange(len(src)), src)
    y *= np.clip(np.abs(rate), 0, 1) ** 0.5
    zip_nz = filt(noise(len(t), r), "bp", (1500.0, 7000.0)) * np.clip(np.abs(np.gradient(rate)) * 400, 0, 1) * 0.25
    y += zip_nz
    y += 0.02 * filt(noise(len(t), r), "high", 3000.0)
    y = filt(y, "high", 60.0)
    return finalize(reverb(pan_st(y, 0.0), rt60=0.4, mix=0.08), fade_out=0.06)


def _tri_sweep(f0, f1, dur):
    t = T(dur)
    f = f0 * (f1 / f0) ** (t / dur)
    ph = M._frac(np.cumsum(f) / SR)
    y = 4.0 * np.abs(ph - 0.5) - 1.0
    y = np.round(y * 7.5) / 7.5
    return filt(y, "low", 9000.0, 1) * env_ar(len(t), 0.003, dur - 0.012, 0.012)


def fx_waka():
    y = np.concatenate([_tri_sweep(240.0, 520.0, 0.135), np.zeros(int(0.012 * SR)), _tri_sweep(520.0, 240.0, 0.135)])
    return finalize(pan_st(y, 0.0), fade_out=0.01)


def fx_error():
    t = T(0.62)
    n = len(t)
    y = np.zeros(n)
    for f in (110.0, 116.5, 220.7):
        dt = np.full(n, f / SR)
        y += M.pulse_blep(M._frac(np.cumsum(dt)), dt, np.full(n, 0.5)) * (0.5 if f > 200 else 1.0)
    y = np.tanh(1.5 * y)
    y = filt(y, "low", 2800.0, 2)
    y *= env_ar(n, 0.008, 0.56, 0.05)
    return finalize(reverb(pan_st(y, 0.0), rt60=0.4, mix=0.08), fade_out=0.02)


def fx_ding():
    t = T(1.8)
    f0 = 1318.5
    y = np.zeros(len(t))
    for ratio, a, d in ((1.0, 1.0, 0.9), (2.0, 0.35, 0.5), (2.76, 0.3, 0.3), (5.4, 0.12, 0.12), (8.93, 0.05, 0.06)):
        if f0 * ratio < 0.45 * SR:
            y += a * np.sin(TWO_PI * f0 * ratio * t) * np.exp(-t / d)
    y *= 1.0 - np.exp(-t / 0.0006)
    y *= 1.0 + 0.04 * np.sin(TWO_PI * 5.0 * t)
    return finalize(reverb(pan_st(y, 0.0), rt60=1.2, mix=0.2), fade_out=0.2)


def fx_pop():
    r = rng("pop")
    t = T(0.14)
    f = 280.0 + (1150.0 - 280.0) * (1.0 - np.exp(-t / 0.012))
    y = np.sin(TWO_PI * np.cumsum(f) / SR) * np.exp(-t / 0.028)
    y += 0.3 * filt(noise(len(t), r), "bp", (800.0, 5000.0)) * np.exp(-t / 0.002)
    y *= 1.0 - np.exp(-t / 0.0004)
    return finalize(reverb(pan_st(y, 0.0), rt60=0.3, mix=0.06), fade_out=0.02)


def fx_sparkle():
    r = rng("sparkle")
    buf = np.zeros((2, int(2.0 * SR)))
    penta = [0, 2, 4, 7, 9]
    notes = [84 + 12 * (i // 5) + penta[i % 5] for i in range(16)]    # C6 .. A8 (capped below)
    notes = [m for m in notes if M.mtof(m) < 4000]
    k = len(notes)
    for i, m in enumerate(notes):
        u = i / (k - 1)
        tt = 0.62 * u ** 1.3
        y = M.mallet(m, SR, "glock", decay=0.5, var=i % 3).astype(np.float64)
        place(buf, pan_st(y, float(r.uniform(-0.8, 0.8))), tt, 0.5 + 0.5 * u)
    t = np.arange(buf.shape[1]) / SR
    shimmer = filt(noise(buf.shape[1], r), "high", 7000.0) * np.exp(-np.abs(t - 0.45) / 0.18) * 0.08
    buf += pan_st(shimmer * (1 + 0.5 * np.sin(TWO_PI * 23 * t)), 0.0)
    return finalize(reverb(buf, rt60=1.4, mix=0.35, bright=1.2), fade_out=0.25)


def fx_levelup():
    buf = np.zeros((2, int(1.2 * SR)))
    seq = [72, 76, 79, 84, 88, 91]
    step = 0.055
    for i, m in enumerate(seq):
        y = M.chip_pulse(m, step * 0.9, SR, duty=0.25, dec=0.05, sus=0.7, rel=0.01).astype(np.float64)
        place(buf, pan_st(y, -0.1), i * step)
        place(buf, pan_st(M.chip_tri(m - 24, step * 0.9, SR).astype(np.float64), 0.1), i * step, 0.8)
    tl = len(seq) * step
    y = M.chip_pulse(96, 0.4, SR, duty=0.5, vib=0.3, vib_delay=0.05, dec=0.3, sus=0.5, rel=0.12).astype(np.float64)
    place(buf, pan_st(y, 0.0), tl)
    place(buf, pan_st(M.chip_pulse(91, 0.4, SR, duty=0.125, dec=0.3, sus=0.4, rel=0.12).astype(np.float64), 0.25), tl, 0.5)
    return finalize(reverb(buf, rt60=0.5, mix=0.12), fade_out=0.05)


def fx_objection_hit():
    buf = np.zeros((2, int(1.6 * SR)))
    for j, m in enumerate((48, 55, 60, 63, 67, 72, 75)):
        y = M.saw_pad(m, 0.3, SR, fc=5200.0, att=0.003, rel=0.25, voices=3, detune=0.16, var=j,
                      dec=0.12, sus=0.3).astype(np.float64)
        place(buf, y, 0.0, 0.5)
    r = rng("objection")
    n = buf.shape[1]
    t = np.arange(n) / SR
    buf += pan_st(filt(noise(n, r), "bp", (500.0, 6000.0)) * np.exp(-t / 0.05) * 0.5, 0.0)
    place(buf, pan_st(M.kick(SR, f_hi=130.0, f_lo=40.0, p_tau=0.04, a_tau=0.3, click=0.2, dur=1.2).astype(np.float64), 0.0), 0.0, 1.2)
    buf = np.tanh(1.2 * buf) / np.tanh(1.2)
    return finalize(reverb(buf, rt60=1.6, mix=0.3, bright=0.9), fade_out=0.25)


def fx_drumroll():
    r = rng("drumroll")
    buf = np.zeros((2, int(2.9 * SR)))
    t = 0.0
    while t < 2.38:
        u = t / 2.38
        rate = 16.0 + 7.0 * u
        vel = (0.12 + 0.88 * u ** 1.6) * (0.85 + 0.3 * r.random())
        y = M.snare(SR, var=int(r.integers(8)), decay=0.09).astype(np.float64)
        place(buf, pan_st(y, 0.05 * np.sin(t * 9)), t + r.normal(0, 0.002), vel)
        t += 1.0 / rate
    place(buf, pan_st(M.snare(SR, var=3, decay=0.2, tone=0.8).astype(np.float64), 0.0), 2.42, 1.3)
    return finalize(reverb(buf, rt60=1.0, mix=0.2), fade_out=0.1)


def fx_crash():
    y = M.crash(SR, dur=3.2, var=11, bright=1.05, decay=1.0).astype(np.float64)
    return finalize(reverb(y, rt60=1.2, mix=0.15, bright=1.2), fade_out=0.4)


def _yell(r, dur):
    t = T(dur)
    n = len(t)
    f0 = r.uniform(170.0, 420.0)
    up = r.uniform(2.0, 6.0)
    shape = np.sin(np.pi * np.clip(t / dur, 0, 1)) ** 0.7
    f = f0 * 2.0 ** ((up * shape + 0.3 * np.sin(TWO_PI * r.uniform(4, 7) * t)) / 12.0)
    dt = f / SR
    src = M.saw_blep(M._frac(np.cumsum(dt) + r.uniform()), dt)
    F = [(730.0, 1090.0, 2440.0), (450.0, 800.0, 2600.0), (400.0, 1900.0, 2600.0)][int(r.integers(3))]
    y = sum(g * filt(src, "bp", (Fi * 0.85, Fi * 1.15)) for Fi, g in zip(F, (1.0, 0.6, 0.25)))
    return y * env_ar(n, 0.06, dur * 0.7, dur * 0.3)


def fx_cheer():
    r = rng("cheer")
    D = 3.3
    n = int(D * SR)
    t = np.arange(n) / SR
    buf = np.zeros((2, n))
    env = np.clip(t / 0.35, 0, 1) ** 1.5 * np.clip(1.0 - (t - 1.9) / 1.3, 0, 1) ** 1.2
    for ch in range(2):
        mod = filt(noise(n, r), "low", 4.0, 1)
        mod = 1.0 + 1.8 * mod / (np.abs(mod).max() + 1e-9)
        roar = filt(noise(n, r), "bp", (350.0, 3500.0)) * mod * env
        buf[ch] += 0.5 * roar
    for _ in range(28):
        d = r.uniform(0.35, 1.2)
        t0 = r.uniform(0.05, 2.1)
        place(buf, pan_st(_yell(r, d), r.uniform(-0.8, 0.8)), t0, r.uniform(0.15, 0.35))
    for _ in range(220):
        t0 = r.uniform(0.1, 2.9)
        gain = r.uniform(0.2, 0.6) * float(np.interp(t0, t, env) + 0.1)
        place(buf, pan_st(M.clap(SR, var=int(r.integers(12)), decay=0.03).astype(np.float64), r.uniform(-0.9, 0.9)),
              t0, gain)
    for (t0, dur, f0) in ((0.5, 0.9, 2100.0), (1.3, 0.7, 2500.0)):
        tw = T(dur)
        f = f0 * 2.0 ** ((3.0 * np.sin(np.pi * tw / dur) + 0.5 * np.sin(TWO_PI * 6 * tw)) / 12.0)
        w = np.sin(TWO_PI * np.cumsum(f) / SR) * env_ar(len(tw), 0.05, dur * 0.7, dur * 0.3)
        place(buf, pan_st(w, r.uniform(-0.5, 0.5)), t0, 0.05)
    buf = filt(buf, "low", 8000.0, 2)
    buf *= np.clip(1.0 - (t - 2.9) / 0.4, 0, 1)
    return finalize(reverb(buf, rt60=1.3, mix=0.2), fade_in=0.02, fade_out=0.3)


def fx_bios_beep():
    y = M.chip_pulse(83, 0.2, SR, duty=0.5, att=0.001, dec=1.0, sus=1.0, rel=0.004).astype(np.float64)
    y = filt(y, "low", 6000.0, 2)
    return finalize(pan_st(y, 0.0), fade_in=0.001, fade_out=0.004)


def fx_notify():
    buf = np.zeros((2, int(0.9 * SR)))
    for t0, m, g in ((0.0, 81, 0.8), (0.075, 88, 1.0)):
        tt = T(0.6)
        f = M.mtof(m)
        y = (np.sin(TWO_PI * f * tt) + 0.25 * np.sin(TWO_PI * 2 * f * tt) * np.exp(-tt / 0.05)) * np.exp(-tt / 0.14)
        y *= 1.0 - np.exp(-tt / 0.0008)
        place(buf, pan_st(y, 0.0), t0, g)
    return finalize(reverb(buf, rt60=0.6, mix=0.12, bright=1.1), fade_out=0.06)


def fx_glitch():
    r = rng("glitch")
    src_t = T(1.0)
    src = np.zeros(len(src_t))
    for m in r.integers(55, 90, 6):
        f = M.mtof(int(m))
        dt = np.full(len(src_t), f / SR)
        src += 0.3 * M.pulse_blep(M._frac(np.cumsum(dt) + r.uniform()), dt, np.full(len(src_t), r.uniform(0.1, 0.5)))
    src += 0.4 * noise(len(src_t), r) * (r.random(len(src_t)) < 0.3)
    out = []
    total = int(0.5 * SR)
    while sum(len(o) for o in out) < total:
        slice_len = int(r.uniform(0.02, 0.06) * SR)
        chunk_len = int(r.uniform(0.006, 0.03) * SR)
        a = int(r.integers(0, len(src) - chunk_len))
        chunk = src[a: a + chunk_len].copy()
        fl = min(24, chunk_len // 4)
        chunk[:fl] *= np.linspace(0, 1, fl)
        chunk[-fl:] *= np.linspace(1, 0, fl)
        seg = np.tile(chunk, slice_len // chunk_len + 1)[:slice_len]
        hold = int(r.choice([1, 2, 4, 8, 16]))
        seg = np.repeat(seg[::hold], hold)[:slice_len]
        bits = int(r.integers(3, 7))
        seg = np.round(seg * (2 ** bits)) / (2 ** bits)
        if r.random() < 0.15:
            seg *= 0.0
        seg = filt(seg, "low", 12000.0, 1)
        fl2 = min(48, slice_len // 4)
        seg[:fl2] *= np.linspace(0, 1, fl2)
        seg[-fl2:] *= np.linspace(1, 0, fl2)
        out.append(seg * r.uniform(0.5, 1.0))
    y = np.concatenate(out)[:total]
    pans = np.repeat(r.uniform(-0.6, 0.6, len(out)), [len(o) for o in out])[:total]
    return finalize(pan_st(y, pans), fade_out=0.01)


def fx_stamp():
    r = rng("stamp")
    t = T(0.9)
    n = len(t)
    f = 45.0 + 50.0 * np.exp(-t / 0.03)
    thump = np.sin(TWO_PI * np.cumsum(f) / SR) * np.exp(-t / 0.16)
    nz = noise(n, r)
    slap = filt(nz, "bp", (150.0, 2500.0)) * np.exp(-t / 0.022) * 1.2
    wood = filt(nz, "bp", (600.0, 820.0)) * np.exp(-t / 0.04) * 1.5
    y = thump + slap + wood
    y = np.tanh(1.8 * y) / np.tanh(1.8)
    y *= 1.0 - np.exp(-t / 0.0004)
    return finalize(reverb(pan_st(y, 0.0), rt60=0.5, mix=0.15, bright=0.6), fade_out=0.08)


def fx_tick():
    r = rng("tick")
    t = T(0.07)
    nz = noise(len(t), r)
    y = filt(nz, "bp", (3500.0, 6500.0)) * np.exp(-t / 0.0025) * 1.5
    y += 0.5 * np.sin(TWO_PI * 4400.0 * t) * np.exp(-t / 0.006)
    y += 0.4 * np.sin(TWO_PI * 1250.0 * t) * np.exp(-t / 0.01)
    y *= 1.0 - np.exp(-t / 0.0002)
    return finalize(reverb(pan_st(y, 0.0), rt60=0.25, mix=0.05), fade_out=0.008)


def fx_fanfare():
    buf = np.zeros((2, int(1.9 * SR)))
    lead = [(0.0, 0.1, 67), (0.125, 0.1, 72), (0.25, 0.1, 76), (0.375, 0.22, 79), (0.625, 0.1, 76),
            (0.75, 0.1, 79), (0.875, 0.62, 84)]
    harm = [(0.0, 0.1, 64), (0.125, 0.1, 67), (0.25, 0.1, 72), (0.375, 0.22, 76), (0.625, 0.1, 72),
            (0.75, 0.1, 76), (0.875, 0.62, 79)]
    bass = [(0.0, 0.34, 48), (0.375, 0.47, 43), (0.875, 0.62, 48)]
    for (t0, d, m) in lead:
        place(buf, pan_st(M.chip_pulse(m, d, SR, duty=0.25, vib=0.25 if d > 0.5 else 0.0, vib_delay=0.1,
                                       dec=0.2, sus=0.7, rel=0.05).astype(np.float64), -0.15), t0, 0.9)
    for (t0, d, m) in harm:
        place(buf, pan_st(M.chip_pulse(m, d, SR, duty=0.125, dec=0.2, sus=0.6, rel=0.05).astype(np.float64), 0.2),
              t0, 0.45)
    for (t0, d, m) in bass:
        place(buf, pan_st(M.chip_tri(m, d, SR).astype(np.float64), 0.0), t0, 1.0)
    for t0 in (0.0, 0.375, 0.875):
        place(buf, pan_st(M.chip_noise(0.3 if t0 > 0.8 else 0.1, SR, clock=9000.0, decay=0.12 if t0 > 0.8 else 0.04,
                                       var=int(t0 * 8)).astype(np.float64), 0.0), t0, 0.35)
    return finalize(reverb(buf, rt60=0.6, mix=0.12), fade_out=0.08)


def fx_sad_trombone():
    buf = np.zeros((2, int(2.9 * SR)))
    notes = [(0.0, 0.36, 55), (0.42, 0.36, 54), (0.84, 0.36, 53), (1.26, 1.25, 52)]
    for i, (t0, d, m) in enumerate(notes):
        last = i == 3
        t = T(d + 0.12)
        n = len(t)
        f0 = float(M.mtof(m))
        vib = (0.45 * np.sin(TWO_PI * 5.5 * t) * np.clip((t - 0.15) / 0.2, 0, 1)) if last else 0.0
        droop = -1.2 * np.clip((t - (d - 0.3)) / 0.35, 0, 1) ** 2 if last else 0.0
        f = f0 * 2.0 ** ((-0.35 * np.exp(-t / 0.04) + vib + droop) / 12.0)
        u = np.clip(t / d, 0, 1)
        if last:
            wah = 0.55 + 0.45 * np.sin(TWO_PI * 5.5 * t - 1.2) * np.clip((t - 0.15) / 0.2, 0, 1)
            wah *= np.sin(np.pi * np.clip(t / 0.25, 0, 0.5)) * np.clip(1.0 - (t - d + 0.3) / 0.4, 0.2, 1)
        else:
            wah = np.sin(np.pi * u) ** 1.2
        fc = f0 * 1.2 + 1700.0 * wah
        y = M.additive(f, SR, fc, 0.3 * i, kmax=50)
        y *= env_ar(n, 0.03, d, 0.1)
        place(buf, pan_st(y, 0.0), t0)
    return finalize(reverb(buf, rt60=0.8, mix=0.15), fade_out=0.1)


def fx_timer_start():
    buf = np.zeros((2, int(1.75 * SR)))
    for t0, d, m in ((0.0, 0.14, 74), (0.5, 0.14, 74), (1.0, 0.5, 86)):
        y = M.soft_lead(m, d, SR, mode="square", fc=4000.0, att=0.003, rel=0.03, vib=0.0, dec=0.4, sus=0.8)
        place(buf, pan_st(y.astype(np.float64), 0.0), t0)
    return finalize(reverb(buf, rt60=0.4, mix=0.08), fade_out=0.03)


def fx_boot_chime():
    buf = np.zeros((2, int(3.4 * SR)))
    for t0, m in ((0.0, 74), (0.09, 81), (0.18, 88)):
        y = M.fm_bell(m, 1.2, SR, ratio=3.0, index=1.0, decay=1.0).astype(np.float64)
        place(buf, pan_st(y, (m - 81) / 14.0), t0, 0.5)
    for j, m in enumerate((50, 57, 66, 73, 76)):
        y = M.saw_pad(m, 1.1, SR, fc=2400.0, att=0.12, rel=1.0, voices=3, detune=0.1, var=j, dec=0.6,
                      sus=0.7).astype(np.float64)
        place(buf, y, 0.22, 0.35)
    tt = T(2.3)
    sub = np.sin(TWO_PI * M.mtof(38) * tt) * env_ar(len(tt), 0.3, 1.2, 1.0) * 0.4
    place(buf, pan_st(sub, 0.0), 0.2)
    return finalize(reverb(buf, rt60=2.0, mix=0.3, bright=0.9), fade_out=0.35)


EFFECTS = {
    "boom": fx_boom, "whoosh": fx_whoosh, "swoosh_up": fx_swoosh_up, "key1": fx_key1, "key2": fx_key2,
    "key3": fx_key3, "enter": fx_enter, "typing": fx_typing, "airhorn": fx_airhorn,
    "record_scratch": fx_record_scratch, "waka": fx_waka, "error": fx_error, "ding": fx_ding, "pop": fx_pop,
    "sparkle": fx_sparkle, "levelup": fx_levelup, "objection_hit": fx_objection_hit, "drumroll": fx_drumroll,
    "crash": fx_crash, "cheer": fx_cheer, "bios_beep": fx_bios_beep, "notify": fx_notify, "glitch": fx_glitch,
    "stamp": fx_stamp, "tick": fx_tick, "fanfare": fx_fanfare, "sad_trombone": fx_sad_trombone,
    "timer_start": fx_timer_start, "boot_chime": fx_boot_chime,
}


# target maximum lengths (s): long reverb tails are faded out smoothly at this point
MAXLEN = {"boom": 1.6, "whoosh": 0.6, "swoosh_up": 0.75, "key1": 0.2, "key2": 0.2, "key3": 0.2, "enter": 0.3,
          "typing": 1.6, "airhorn": 2.2, "record_scratch": 0.8, "waka": 0.3, "error": 0.75, "ding": 1.6,
          "pop": 0.25, "sparkle": 1.2, "levelup": 1.0, "objection_hit": 1.3, "drumroll": 2.7, "crash": 3.0,
          "cheer": 3.2, "bios_beep": 0.2, "notify": 0.5, "glitch": 0.5, "stamp": 0.7, "tick": 0.07,
          "fanfare": 1.7, "sad_trombone": 2.7, "timer_start": 1.7, "boot_chime": 2.6}


def render(name):
    x = EFFECTS[name]()
    M.clear_caches()
    L = MAXLEN.get(name)
    if L and x.shape[1] > int(L * SR):
        n = int(L * SR)
        x = x[:, :n].copy()
        no = int(min(0.3, 0.2 * L) * SR)
        x[:, n - no:] *= (0.5 + 0.5 * np.cos(np.pi * np.arange(1, no + 1) / no))
        x *= PEAK / np.max(np.abs(x))
    return np.ascontiguousarray(x.T, dtype=np.float32)


def main(argv):
    names = argv[1:] or list(EFFECTS)
    os.makedirs(OUT_DIR, exist_ok=True)
    for nm in names:
        x = render(nm)
        p = os.path.join(OUT_DIR, f"{nm}.wav")
        sf.write(p, x, SR, subtype="PCM_16")
        rms = 20 * np.log10(np.sqrt(np.mean(x.astype(np.float64) ** 2)) + 1e-12)
        print(f"{nm:15s} {len(x) / SR:5.2f}s  peak {20 * np.log10(np.abs(x).max()):5.1f} dBFS  rms {rms:6.1f} dBFS")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
