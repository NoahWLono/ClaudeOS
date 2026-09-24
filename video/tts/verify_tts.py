"""Transcribe each TTS line with Whisper and report word error rate vs the script."""
import json, os, re, sys
from faster_whisper import WhisperModel
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
script = json.load(open(os.path.join(ROOT, "script.json")))
m = WhisperModel("small.en", device="cpu", compute_type="int8")
norm = lambda s: re.sub(r"[^a-z0-9 ]", " ", s.lower().replace("-", " ")).split()
def wer(a, b):
    d = list(range(len(b) + 1))
    for i in range(1, len(a) + 1):
        p, d[0] = d[0], i
        for j in range(1, len(b) + 1):
            p, d[j] = d[j], min(d[j] + 1, d[j - 1] + 1, p + (a[i - 1] != b[j - 1]))
    return d[len(b)] / max(1, len(a))
rows = []
for sc in script["scenes"]:
    for i, ln in enumerate(sc["lines"]):
        key = f"{sc['id']}_{i}"
        segs, _ = m.transcribe(os.path.join(ROOT, "build/tts", key + ".wav"), beam_size=3, language="en")
        hyp = " ".join(s.text for s in segs).strip()
        ref = ln.get("say", ln["text"])
        w = wer(norm(ref), norm(hyp))
        rows.append((w, key, ref, hyp))
        print(f"{w:4.2f} {key:20s} | {hyp}", flush=True)
json.dump(rows, open(os.path.join(ROOT, "build/tts_verify.json"), "w"), indent=1)
print("worst:")
for r in sorted(rows, reverse=True)[:15]: print(f"{r[0]:.2f} {r[1]}\n   ref: {r[2]}\n   hyp: {r[3]}")
