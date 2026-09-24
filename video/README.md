# I Use Arch, By The Way

A 17 minute first-principles propaganda film about Arch Linux, starring Claude Opus 5.5, ending in a
real step-by-step install tutorial (23 steps, starts at 11:37). There are hidden Blåhaj sightings; Monster is not hidden.
Final render: `out/i-use-arch-btw.mp4` (17:15, 1080p30, H.264 two-pass sized to stay under GitHub's 100 MB file
limit, AAC, -16 LUFS, with chapter markers). Captions are burned in and also in `out/i-use-arch-btw.srt`.
`./build.sh` also leaves a higher-bitrate master at `build/master.mp4`.

The tutorial's commands were checked against the live Arch Wiki (Installation guide, systemd-boot,
Microcode, USB flash installation medium, Sudo) and archlinux.org/download for the 2026.09.01 ISO.
The wiki remains the source of truth; if this video and the wiki disagree, the wiki wins.

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

## Chapters

```
00:00 Cold open
00:18 Title
00:45 Choose your fighter
01:06 Part 1: What even is a computer
01:50 Part 2: The install (any%)
03:43 First boot
04:06 Objection! (Gentoo, LFS, NixOS)
04:52 Part 3: The five principles
05:55 Part 4: pacman and partial upgrades
06:59 Part 5: The AUR
07:34 Part 6: The Wiki (a special interest)
08:43 Part 7: But can it game?
09:31 Meanwhile, on Windows
09:51 Part 8: The rice
10:31 Intermission: the family group chat
11:02 Finale
11:37 TUTORIAL: before you start
12:13 Tutorial 1-4: USB + boot
12:58 Tutorial 5-8: live system
13:34 Tutorial 9-12: partition, format, mount
14:18 Tutorial 13-14: pacstrap + fstab
14:40 Tutorial 15-19: configure
15:18 Tutorial 20-21: bootloader + network
15:51 Tutorial 22-23: reboot + first steps
16:33 Credits
17:07 Post-credits
```
