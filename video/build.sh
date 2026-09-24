#!/usr/bin/env bash
# Full pipeline: TTS -> timeline -> frames -> audio mix -> final MP4.
# Needs: python3 (kokoro-onnx, numpy, scipy, soundfile), node 18+, ffmpeg.
set -euo pipefail
cd "$(dirname "$0")"
mkdir -p build out
[ -f assets/fonts/Anton.ttf ] || assets/fetch_fonts.sh
python3 tts/gen_tts.py                       # cached per line
(cd render && [ -d node_modules ] || npm install --silent)
node render/render.mjs timeline              # build/timeline.json
python3 audio/sfx.py                         # assets/sfx/*.wav
python3 audio/mix.py                         # build/audio.wav
node render/render.mjs all "${JOBS:-$(nproc)}"   # build/video.mp4
python3 audio/chapters.py > /dev/null           # build/chapters.txt
ffmpeg -y -loglevel error -i build/video.mp4 -i build/audio.wav -i build/chapters.txt \
  -map 0:v -map 1:a -map_metadata 2 -map_chapters 2 -c:v copy \
  -af "loudnorm=I=-16:TP=-1.5:LRA=11" -ar 48000 -c:a aac -b:a 192k -movflags +faststart -shortest build/master.mp4
# repo copy: two-pass to stay under GitHub's 100 MB file limit (target from duration)
DUR=$(ffprobe -v error -show_entries format=duration -of csv=p=0 build/master.mp4)
VBR=$(python3 -c "print(int((93e6*8/$DUR - 128e3)/1e3))")k
ffmpeg -y -loglevel error -i build/master.mp4 -map 0:v -c:v libx264 -preset slow -tune animation -b:v $VBR -pass 1 -passlogfile build/x264pass -an -f mp4 /dev/null
ffmpeg -y -loglevel error -i build/master.mp4 -map 0 -map_chapters 0 -c:v libx264 -preset slow -tune animation -b:v $VBR -pass 2 -passlogfile build/x264pass \
  -c:a aac -b:a 128k -movflags +faststart out/i-use-arch-btw.mp4
python3 - <<'PY'
import json
tl = json.load(open("build/timeline.json")); sc = json.load(open("script.json"))
text = {f"{s['id']}_{i}": l["text"] for s in sc["scenes"] for i, l in enumerate(s["lines"])}
name = {k: v["name"] for k, v in sc["cast"].items()}
ts = lambda t: "%02d:%02d:%02d,%03d" % (t // 3600, t % 3600 // 60, t % 60, round(t % 1 * 1000) % 1000)
with open("out/i-use-arch-btw.srt", "w") as f:
    for n, l in enumerate(tl["lines"], 1):
        f.write(f"{n}\n{ts(l['start'])} --> {ts(l['start'] + l['dur'])}\n{name[l['who']]}: {text[l['key']]}\n\n")
PY
ls -la out/
