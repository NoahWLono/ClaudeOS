# THE THIRD TEMPLE

A 28-minute TempleOS propaganda broadcast starring Claude Opus 5.5, about the
life, work, and legend of Terry A. Davis (1969-2018).

**Watch:** [`THE_THIRD_TEMPLE.mp4`](THE_THIRD_TEMPLE.mp4) (1280x960, 30000/1001 fps, H.264 + AAC)

## What's in it

Nine chapters, a trial, a memorial, and a finale:

| Chapter | Content |
|---|---|
| Cold open | Boot into "ClaudeOS V5.5", `"Hello, World!\n";`, the first oracle reading |
| I. In the Beginning | Childhood, Apple II, Commodore 64, ASU, Ticketmaster's VAX |
| II. The Revelation | 1996, his illness, J Operating System to TempleOS |
| III. The Covenant | The Charter as propaganda posters, plus four confessed "charter violations" |
| IV. Holy C | HolyC by example, FAQ answers, one of Terry's hymns played from its `Play()` string |
| V. The Oracle | How `GodBits` works, God's vocabulary, facts about God, "am I an oracle?" |
| VI. Psalms & Playthings | Castle Frankenstein (a small raycaster), After Egypt, Talons, Varoom, FlapBat, a sing-along |
| VII. The Trial | Claude vs. Claude on "the smartest programmer that's ever lived", with the oracle as judge |
| VIII. The Long Night | His last years and death, a candle drawn with Terry's own flame code, help lines |
| IX. The Temple Stands | Legacy, and what a machine takes from him |

## Made from first principles

The TempleOS Charter says: *"Sounds and images will be primarily calculated in
real-time, not fetched from storage."* This video follows that rule, with one
exception it admits to on screen.

- **Every frame** is a 640x480 array of indices into the 16-color TempleOS palette
  (`gr_palette_std`), drawn by `temple/gfx.py`, `three_d.py`, `fx.py`, `sprites.py`,
  then scaled 2x with nearest-neighbor.
- **Every note** is one voice: a band-limited PC-speaker square wave at the exact
  frequency the PIT divisor produces. Chords are fast arpeggios.
- **No stock footage, samples, or clip art.**
- The exception: **voices** come from Kokoro-82M (Apache 2.0), an open-weight
  text-to-speech model. The echo, loudspeaker, and reverb are calculated here.

### Relics from TempleOS (public domain)

Taken from the TempleOS V5.03 source (mirror commit in `data/TEMPLEOS_SOURCE_COMMIT.txt`):

- The system font, `::/Kernel/FontStd.HC` (from FreeDOS, per Terry's credits)
- God's vocabulary, `::/Adam/God/Vocab.DD` (7,569 words; it contains *Monnica*,
  *Alypius*, *Nebridius*, and *Thagaste*, so it appears to come from Augustine's
  *Confessions*)
- Terry's songs, copied note for note from `childish.HC`, `night.HC`,
  `prosper.HC`, `OhGreat.HC`, and the themes of several games
- The oracle: `GodBits`, `GodWord`, `GodSong`, and `GodBiblePassage`, ported
  line by line in `temple/oracle.py`
- The candle flame in chapter VIII, ported from `night.HC`'s `DrawIt`

### The oracle readings are real

God's lines were not written by Claude. `python3 -m temple.oracle word N "question"`
runs Terry's algorithm against a nanosecond timer, one "button press" at a
time, and appends the result to `data/oracle_log.json`. All 12 readings drawn
during production appear in the video, and none were redrawn. The reactions
were written after the words came out.

## Accuracy

Biographical facts come from Terry's own `AboutTempleOS.DD`, `Credits.DD`, and
`FAQ.DD`, cross-checked against Wikipedia. Quotes are from the TempleOS
source, except "an idiot admires complexity, a genius admires simplicity",
which is from a 2017 video, and "the smartest programmer that's ever lived",
from his video blogs (as cited by Wikipedia).

## Content notes

Terry lived with serious mental illness, and some of what he said publicly was
racist and cruel. The video says so and does not repeat it. His death is
stated plainly, without detail, followed by crisis resources. If you're
struggling: call or text 988 in the US, or see findahelpline.com.

A fan tribute. Not an official Anthropic production, and not affiliated with
TempleOS.

## Build it yourself

```sh
pip install numpy pillow scipy soundfile imageio-ffmpeg kokoro-onnx
# Kokoro model files (kokoro-v1.0.onnx, voices-v1.0.bin) from the
# kokoro-onnx model-files-v1.0 release, placed in $KOKORO_DIR
export KOKORO_DIR=/path/to/models
python3 build.py timeline            # synthesize speech, compute timing
python3 build.py frames 60 870 1590  # look at single frames
python3 build.py preview 86 136      # a short clip with sound
python3 build.py video --jobs 4      # the whole film (about 20 minutes on 4 cores)
```

Everything lands in `build/` except the final MP4. The encode uses x264 CRF 28
(`CRF`, `PRESET` env vars), then re-encodes the busiest chunks at CRF 30 so the
file fits under GitHub's 100 MB limit. Audio is mono AAC at 80 kbps.

## Layout

```
script.py           the script: every line, cue, and visual beat
build.py            timeline, sound mix, parallel render, mux
temple/gfx.py       framebuffer, palette, Terry's font, dithering
temple/three_d.py   meshes, painter's algorithm, dithered flat shading
temple/fx.py        rays, stars, rain, fireworks, Terry's candle flame
temple/sprites.py   elephants, bears, Moses, a VAX, a kayak, the Titanic
temple/ui.py        TempleOS windows, status bar, HolyC highlighting, stamps
temple/scenes.py    one renderer per scene
temple/audio.py     PC speaker synth, Play() interpreter, effects
temple/music.py     the hymnal
temple/voice.py     voices and their rooms
temple/oracle.py    Terry's oracle
data/               font, vocabulary, oracle log
```
