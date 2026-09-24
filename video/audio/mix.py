"""Mix narration + music + SFX into build/audio.wav using build/timeline.json."""
import json, os, sys
import numpy as np
import soundfile as sf
from scipy.signal import resample_poly

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "audio"))
SR = 48000
MUSIC = float(os.environ.get("MUSIC_GAIN", 0.8))
SFX = float(os.environ.get("SFX_GAIN", 0.7))


def load(path):
    x, sr = sf.read(path, dtype="float32", always_2d=True)
    if sr != SR:
        from math import gcd
        g = gcd(SR, sr)
        x = resample_poly(x, SR // g, sr // g, axis=0).astype(np.float32)
    if x.shape[1] == 1:
        x = np.repeat(x, 2, axis=1)
    return x


def place(buf, x, t, gain=1.0):
    i = int(round(t * SR))
    if i < 0:
        x, i = x[-i:], 0
    n = min(len(x), len(buf) - i)
    if n > 0:
        buf[i:i + n] += x[:n] * gain


def smooth_env(mono, attack=0.02, release=0.35):
    # peak follower with separate attack/release, computed on 10 ms hops
    hop = SR // 100
    n = len(mono) // hop + 1
    pk = np.array([np.abs(mono[i * hop:(i + 1) * hop]).max() if i * hop < len(mono) else 0 for i in range(n)])
    a, r = np.exp(-0.01 / attack), np.exp(-0.01 / release)
    out = np.zeros(n); y = 0.0
    for i, v in enumerate(pk):
        c = a if v > y else r
        y = c * y + (1 - c) * v
        out[i] = y
    return np.repeat(out, hop)[:len(mono)]


def loudness_norm(x, target_db=-17.0):
    # SFX ship peak-normalized; level them by their loudest 250 ms window instead
    m = x.mean(axis=1); w = max(1, int(0.25 * SR))
    if len(m) <= w:
        rms = np.sqrt(np.mean(m ** 2))
    else:
        c = np.cumsum(np.concatenate([[0], m ** 2]))
        rms = np.sqrt(((c[w:] - c[:-w]) / w).max())
    g = 10 ** (target_db / 20) / max(rms, 1e-6)
    g = min(g, 0.99 / max(np.abs(x).max(), 1e-6))
    return x * g


def main():
    tl = json.load(open(os.path.join(ROOT, "build", "timeline.json")))
    N = int(np.ceil(tl["total"] * SR)) + SR
    voice = np.zeros((N, 2), np.float32)
    music = np.zeros((N, 2), np.float32)
    sfx = np.zeros((N, 2), np.float32)

    for ln in tl["lines"]:
        x = load(os.path.join(ROOT, "build", "tts", ln["key"] + ".wav"))
        place(voice, x * 0.85, ln["start"])

    # music: merge consecutive scenes that share a track so it plays continuously
    groups = []
    for seg in tl["music"]:
        if groups and groups[-1]["track"] == seg["track"] and abs(groups[-1]["end"] - seg["start"]) < 1e-3:
            groups[-1]["end"] = seg["start"] + seg["dur"]
        else:
            groups.append({"track": seg["track"], "start": seg["start"], "end": seg["start"] + seg["dur"]})
    try:
        import music as M
    except Exception as e:  # music module not ready yet
        print("music module unavailable:", e); M = None
    for g in groups:
        if not g["track"] or M is None:
            continue
        dur = g["end"] - g["start"] + 0.4  # small tail overlap into the next scene
        try:
            x = M.render_track(g["track"], dur, sr=SR).astype(np.float32)
        except Exception as e:
            print("track failed", g["track"], e); continue
        place(music, x, g["start"])
        print(f"music {g['track']:8s} {g['start']:7.1f} +{dur:.1f}")

    sdir = os.path.join(ROOT, "assets", "sfx")
    cache, missing = {}, set()
    for c in tl["cues"]:
        p = os.path.join(sdir, c["name"] + ".wav")
        if not os.path.exists(p):
            missing.add(c["name"]); continue
        if p not in cache:
            cache[p] = loudness_norm(load(p))
        place(sfx, cache[p], c["t"], c.get("gain", 0.6))
    if missing:
        print("missing sfx:", sorted(missing))

    # music bed sits ~6 dB down, ducking another ~10 dB while someone is talking
    env = smooth_env(voice.mean(axis=1), attack=0.03, release=0.45)
    duck = 1.0 - 0.7 * np.clip(env / 0.1, 0, 1)
    music *= duck[:, None]
    mix = voice + music * MUSIC + sfx * SFX
    peak = np.abs(mix).max()
    # gentle soft-clip then normalize
    mix = np.tanh(mix * 1.1) / np.tanh(1.1)
    mix = mix / max(1e-9, np.abs(mix).max()) * 0.95
    n = int(round(tl["total"] * SR))
    if os.environ.get("STEMS"):
        for nm, st in (("voice", voice), ("music", music * MUSIC), ("sfx", sfx * SFX)):
            sf.write(os.path.join(ROOT, "build", f"stem_{nm}.wav"), st[:int(round(tl["total"] * SR))], SR, subtype="FLOAT")
    out = os.path.join(ROOT, "build", "audio.wav")
    sf.write(out, mix[:n], SR, subtype="PCM_16")
    print(f"wrote {out}: {n / SR:.1f}s, pre-limit peak {peak:.2f}")


if __name__ == "__main__":
    main()
