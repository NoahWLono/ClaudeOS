"""Synthesize every script line with Kokoro TTS.

Writes build/tts/<scene>_<n>.wav (24 kHz mono) and build/tts/lines.json with
duration + a 30 fps loudness envelope per line (drives lip flap).
Cached by content hash, so re-running only redoes changed lines.
"""
import hashlib, json, os, sys
import numpy as np
import soundfile as sf

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "build", "tts")
MODEL_DIR = os.environ.get("KOKORO_DIR", os.path.join(ROOT, "build", "kokoro"))
FPS = 30
SR = 24000


def trim(x, thresh=0.006, pad=0.09):
    idx = np.where(np.abs(x) > thresh)[0]
    if len(idx) == 0:
        return x
    a = max(0, idx[0] - int(pad * SR))
    b = min(len(x), idx[-1] + int(pad * SR))
    return x[a:b]


def envelope(x):
    hop = SR // FPS
    n = int(np.ceil(len(x) / hop))
    env = np.array([np.sqrt(np.mean(x[i * hop:(i + 1) * hop] ** 2) + 1e-12) for i in range(n)])
    if env.max() > 0:
        env = env / np.percentile(env, 95)
    return np.clip(env, 0, 1).round(3).tolist()


def main():
    from kokoro_onnx import Kokoro
    script = json.load(open(os.path.join(ROOT, "script.json")))
    cast = script["cast"]
    os.makedirs(OUT, exist_ok=True)
    kok = Kokoro(os.path.join(MODEL_DIR, "kokoro-v1.0.onnx"), os.path.join(MODEL_DIR, "voices-v1.0.bin"))
    meta_path = os.path.join(OUT, "lines.json")
    meta = json.load(open(meta_path)) if os.path.exists(meta_path) else {}

    for sc in script["scenes"]:
        for i, ln in enumerate(sc["lines"]):
            key = f"{sc['id']}_{i}"
            who = cast[ln["who"]]
            say = ln.get("say", ln["text"])
            h = hashlib.sha1(json.dumps([say, who], sort_keys=True).encode()).hexdigest()[:12]
            wav = os.path.join(OUT, key + ".wav")
            if key in meta and meta[key]["hash"] == h and os.path.exists(wav):
                continue
            if "voices" in who:  # group chant: every voice, time-matched to the lead voice
                lang = lambda v: "en-gb" if v[0] == "b" else "en-us"
                vs = who["voices"]
                lead, _ = kok.create(say, voice=vs[0], speed=who["speed"], lang=lang(vs[0]))
                lead = trim(np.asarray(lead, dtype=np.float64))
                parts = [lead]
                for v in vs[1:]:
                    s1, _ = kok.create(say, voice=v, speed=1.0, lang=lang(v))
                    sp = float(np.clip(len(trim(np.asarray(s1))) / len(lead), 0.7, 1.6))
                    s2, _ = kok.create(say, voice=v, speed=sp, lang=lang(v))
                    parts.append(trim(np.asarray(s2, dtype=np.float64)))
                L = max(len(p) for p in parts) + int(0.03 * SR)
                mix = np.zeros(L)
                for j, p in enumerate(parts):
                    off = int((j * 7 % 4) * 0.006 * SR)
                    g = 1.0 if j == 0 else 0.42
                    mix[off:off + len(p)] += g * p / (np.abs(p).max() + 1e-9)
                x = mix / np.abs(mix).max() * 0.9
            else:
                v = who["voice"]
                s, _ = kok.create(say, voice=v, speed=who["speed"], lang="en-gb" if v[0] == "b" else "en-us")
                x = trim(np.asarray(s, dtype=np.float64))
                x = x / (np.abs(x).max() + 1e-9) * 0.9
            sf.write(wav, x.astype(np.float32), SR)
            meta[key] = {"hash": h, "dur": round(len(x) / SR, 3), "env": envelope(x)}
            print(f"{key:24s} {meta[key]['dur']:6.2f}s  {say[:60]}", flush=True)
            json.dump(meta, open(meta_path, "w"))
    json.dump(meta, open(meta_path, "w"))
    total = sum(m["dur"] for m in meta.values())
    print(f"done: {len(meta)} lines, {total:.1f}s of speech")


if __name__ == "__main__":
    main()
