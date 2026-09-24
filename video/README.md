# I Use Arch, By The Way

A ~12 minute first-principles propaganda film about Arch Linux, starring Claude Opus 5.5.
Final render: `out/i-use-arch-btw.mp4` (12:17, 1080p30, H.264 two-pass at ~860 kb/s + AAC, -16 LUFS, 92 MB so it fits
under GitHub's 100 MB file limit). Captions are burned in and also provided as `out/i-use-arch-btw.srt`.
`./build.sh` produces a higher-bitrate (~207 MB) master before any recompression.

Nothing here is stock footage or sampled audio:

| Layer | How it's made |
|---|---|
| Script | `script.json`: scenes, lines, speakers, pronunciation overrides (`say`) |
| Voices | Kokoro TTS (`tts/gen_tts.py`), one voice per character, checked with Whisper (`tts/verify_tts.py`) |
| Visuals | Every frame drawn in code with Skia canvas (`render/`), characters in `render/characters.mjs` |
| Music + SFX | Synthesized in numpy (`audio/music.py`, `audio/sfx.py`) |
| Mix | `audio/mix.py`: narration, per-scene music with voice ducking, timed SFX cues |

Lip flap is driven by each line's real loudness envelope, and captions light up word by word
using the same envelope.

## Build

```sh
pip install kokoro-onnx soundfile numpy scipy   # + faster-whisper for tts/verify_tts.py
# Kokoro model files go in build/kokoro/ (kokoro-v1.0.onnx, voices-v1.0.bin)
./build.sh
```

Useful while editing:

```sh
node render/render.mjs contact <sceneId>      # 4x3 contact sheet of a scene -> build/contact_<id>.png
node render/render.mjs still <sceneId> <sec>  # one frame
node render/render.mjs timeline               # scene start times + cue list
```

## Scenes

cold open, title, character select, the boot chain, the install (with a live speedrun timer),
first boot, the hecklers (Gentoo, LFS, NixOS), the five principles, pacman and partial upgrades,
the AUR, the Wiki, gaming, a Windows Update interlude, the rice, the Claude family group chat,
the finale, credits, and a post-credits scene.
