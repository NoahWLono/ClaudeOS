"""Build THE THIRD TEMPLE.

  python3 build.py timeline          synthesize speech, print scene times
  python3 build.py frames T1 T2 ...  render single frames (PNG) at times
  python3 build.py audio             mix the soundtrack
  python3 build.py video [--jobs N]  render the whole film and mux it
"""
import glob
import math
import multiprocessing as mp
import os
import pickle
import subprocess
import sys
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import script  # noqa: E402
from temple import audio as A  # noqa: E402
from temple import fx, gfx, music as M, scenes as SC, timeline, ui  # noqa
from temple.gfx import H, W, Canvas  # noqa: E402

BUILD = os.path.join(HERE, "build")
FINAL = os.path.join(HERE, "THE_THIRD_TEMPLE.mp4")
TL_PICKLE = os.path.join(BUILD, "timeline.pkl")
ORANGE_XY = (613, 371)
DISSOLVE = 0.35
CRF = os.environ.get("CRF", "28")
PRESET = os.environ.get("PRESET", "slow")
SONG_GAIN = 0.42  # square waves sound louder than their RMS says
NO_DISSOLVE = {"hello", "title", "ch1_card"}


def ffmpeg():
    import imageio_ffmpeg
    return imageio_ffmpeg.get_ffmpeg_exe()


def loc():
    n = 0
    for p in glob.glob(os.path.join(HERE, "*.py")) + glob.glob(
            os.path.join(HERE, "temple", "*.py")):
        with open(p) as f:
            n += sum(1 for _ in f)
    return n


# ---------------------------------------------------------------- timeline
def get_timeline(rebuild=False):
    if os.path.exists(TL_PICKLE) and not rebuild:
        with open(TL_PICKLE, "rb") as f:
            return pickle.load(f)
    scenes, clips, T = timeline.build(script.SCENES)
    os.makedirs(BUILD, exist_ok=True)
    with open(TL_PICKLE, "wb") as f:
        pickle.dump((scenes, clips, T), f)
    return scenes, clips, T


# ------------------------------------------------------------------- audio
def bed_track(name, dur):
    """Background music for a scene, looped to dur seconds."""
    sr = A.SR
    if name == "rain":
        n = int(dur * sr)
        rng = np.random.default_rng(2)
        y = rng.standard_normal(n).astype(np.float32)
        y = A.lowpass(A.highpass(y, 300), 2500) * 0.5
        return y
    if name == "drone":
        ns = [{"t": 0.0, "on": dur, "dur": dur, "ona": 42, "word": None,
               "arp": [0, 7, 12, 7], "gain": 1.0}]
        y = A.render_notes(ns, dur, gain=0.22, arp_rate=38.0)
        swell = 0.6 + 0.4 * np.sin(np.arange(len(y)) / sr * 0.5)
        return A.speaker(y * swell.astype(np.float32))
    drums = None
    if name.endswith("_fanfare") or name.endswith("_march"):
        base = name.rsplit("_", 1)[0]
        ns, L = M.notes(base)
        ns = M.organum(ns)
        beat = 1.0 / M.SONGS[base]["tempo"]
        _, drums, gaps = M.with_drums(ns, beat, L, "march", 0.55)
        y = A.render_notes(ns, L, gain=0.26, arp_rate=55.0)
        y = M.mute_gaps(y, gaps) + drums[:len(y)]
        y = A.speaker(y)
    else:
        scale = 1.0
        base = name
        if name.endswith("_slow"):
            base, scale = name[:-5], 0.78
        if name == "prosper_credits":
            parts = []
            for nm in ("prosper", "childish", "prosper", "doxology"):
                ns, L = M.notes(nm)
                parts.append(M.render(ns, L, gain=0.28))
            y = np.concatenate(parts)
        else:
            ns, L = M.notes(base, tempo_scale=scale)
            y = M.render(ns, L, gain=0.28)
    reps = int(math.ceil(dur * sr / max(len(y), 1))) + 1
    return np.tile(y, reps)[:int(dur * sr)]


def fade(y, a=0.6, b=1.2):
    y = y.copy()
    na, nb = min(int(a * A.SR), len(y)), min(int(b * A.SR), len(y))
    if na:
        y[:na] *= np.linspace(0, 1, na)
    if nb:
        y[-nb:] *= np.linspace(1, 0, nb)
    return y


def key_click(seed):
    return A.noise_burst(0.012, seed=seed, color=5000, gain=0.12, decay=300)


def chime(freq=1568.0):
    n = int(0.35 * A.SR)
    y, _ = A.square(np.full(n, freq))
    e = np.exp(-np.arange(n) / A.SR * 11).astype(np.float32)
    y2, _ = A.square(np.full(n, freq * 1.5))
    return A.speaker(0.12 * y * e + 0.05 * y2 * e)


def sting():
    ns, _ = A.song_notes(["5sCEG6hC"], 2.5, 0.95)
    return A.speaker(A.render_notes(M.organum(ns), gain=0.25, arp_rate=55))


def thud():
    a = A.kick(0.2, 0.6)
    b = A.noise_burst(0.12, 5, 1800, 0.35, 25)
    a[:len(b)] += b
    return a


def moving_avg(x, k):
    c = np.cumsum(np.concatenate([[0.0], x.astype(np.float64)]))
    h = k // 2
    i0 = np.clip(np.arange(len(x)) - h, 0, len(x))
    i1 = np.clip(np.arange(len(x)) + (k - h), 0, len(x))
    return ((c[i1] - c[i0]) / k).astype(np.float32)


def scene_sfx(sc):
    """(local_t, clip, gain) for one scene."""
    out = []
    kind = sc["kind"]
    items = sc["items"]
    if kind == "bios":
        out.append((0.15, A.beep(1000, 0.16, 0.22), 1.0))
        for t0 in SC.BIOS_TYPE_TIMES:
            for j in range(0, 6):
                out.append((t0 + j * 0.05, key_click(int(t0 * 100) + j), 1))
        for j in range(16):
            out.append((1.4 + j * 0.1, A.beep(2000 + j * 40, 0.01, 0.06), 1))
        ns, _ = A.song_notes(["5sCEG6C"], 3.0, 0.9)
        out.append((14.6, A.speaker(A.render_notes(ns, gain=0.25)), 1.0))
    if kind in ("terminal", "terminal_end", "oracle_popup"):
        for it in items:
            for key in ("type_cmd", "type_cmd2"):
                if key in it:
                    for j in range(len(it[key])):
                        out.append((it["t0"] + 0.3 + j / 11.0,
                                    key_click(j + int(it["t0"] * 10)), 1.0))
            if "out" in it:
                out.append((it["t0"], A.beep(1320, 0.05, 0.12), 1.0))
            if it.get("type_cmd2") == "Reboot;":
                out.append((it["t0"] + 1.4, A.sweep(1400, 60, 0.9, 0.2), 1))
            if it.get("black"):
                out.append((it["t0"] + 0.8, A.beep(880, 0.2, 0.18), 1.0))
    if kind == "oracle_popup":
        q = next(i for i in items if i.get("question") == 0)
        s = "GodWord; GodWord; GodWord; GodWord; GodWord; //God, are you there?"
        for j in range(0, len(s), 2):
            out.append((q["t0"] + j / 30.0, key_click(j), 0.8))
    if kind == "title":
        out.append((0.0, A.noise_burst(0.5, 3, 6000, 0.25, 3), 1.0))
    if kind == "chapter":
        out.append((0.3, sting(), 1.0))
    if kind == "terminal":
        sp = next(i for i in items if i.get("text", "").startswith("But "
                  "first"))
        out.append((sp["t1"] - 0.2, A.noise_burst(0.4, 8, 7000, 0.2, 4), 1))
    for it in items:
        if it["type"] == "oracle":
            out.append((it["t0"] + 0.5, A.beep(660, 0.06, 0.15), 1.0))
            for a, b in it.get("word_times", []):
                out.append((a - 0.2, chime(), 1.0))
        if "stamp" in it:
            out.append((it["t0"], thud(), 1.0))
        if it.get("gavel"):
            for d in (0.35, 0.62):
                out.append((it["t0"] + d, thud(), 0.9))
        if "poster" in it and kind == "covenant":
            prev = items[items.index(it) - 1] if items.index(it) else {}
            if prev.get("poster") != it["poster"]:
                out.append((it["t0"], A.kick(0.15, 0.5), 1.0))
    if kind == "covenant":
        it = next(i for i in items if i.get("arp_demo"))
        end = max(i["t2"] for i in items if i.get("arp_demo"))
        dur = end - it["t0"]
        n = int(dur * A.SR)
        tt = np.arange(n) / A.SR
        rate = np.array([SC.arp_rate(x) for x in tt[::480]])
        rate = np.repeat(rate, 480)[:n]
        ph = np.cumsum(rate / A.SR)
        step = np.array([0, 4, 7])[(ph.astype(np.int64)) % 3]
        f = 523.25 * 2.0 ** (step / 12.0)
        y, _ = A.square(f)
        out.append((it["t0"], A.speaker(fade(0.11 * y, 0.05, 0.6)), 1.0))
    if kind == "finale":
        rng = np.random.default_rng(1)
        t = 0.5
        while t < sc["dur"] - 2:
            out.append((t, A.noise_burst(0.3, int(t * 10), 3000, 0.18, 9), 1))
            t += rng.uniform(0.3, 0.9)
    return out


def fg_windows(sc):
    """Times when a song is in the foreground or the bed must be silent."""
    w = []
    for it in sc["items"]:
        if it["type"] == "song" or (it["type"] == "oracle" and
                                    it["entry"]["kind"] == "song"):
            w.append((it["t0"], it["t2"]))
        if it.get("arp_demo"):
            w.append((it["t0"] - 0.2, it["t2"]))
        if it.get("silence"):
            w.append((it["t0"], it["t2"]))
    return w


def mix(scenes, clips, T):
    n = int((T + 1.0) * A.SR)
    voice = np.zeros(n, np.float32)
    songs = np.zeros(n, np.float32)
    beds = np.zeros(n, np.float32)
    sfx = np.zeros(n, np.float32)
    for t, clip, g, spk in clips:
        if spk == "SONG":
            A.place(songs, clip, t, g * SONG_GAIN)
        else:
            A.place(voice, clip, t, g)
    # voice activity -> ducking envelope
    a = np.abs(voice)
    k = int(0.05 * A.SR)
    env = moving_avg(a, k)
    act = (env > 0.004).astype(np.float32)
    rel = int(0.4 * A.SR)
    act = moving_avg(act, rel)
    duck = 1.0 - 0.62 * np.clip(act * 1.5, 0, 1)
    for sc in scenes:
        s0 = sc["start"]
        for t, clip, g in scene_sfx(sc):
            A.place(sfx, clip, s0 + t, g)
        if sc["kind"] == "games":
            items = sc["items"]
            segs = []
            for it in items:
                m = it.get("music")
                if m and (not segs or segs[-1][0] != m):
                    segs.append([m, it["t0"], None])
                elif not m and it["type"] == "song" and segs:
                    pass
                if segs and it["type"] == "song":
                    segs[-1][2] = it["t0"]
            for i, sg in enumerate(segs):
                end = sg[2] if sg[2] is not None else (
                    segs[i + 1][1] if i + 1 < len(segs) else sc["dur"])
                if i + 1 < len(segs):
                    end = min(end, segs[i + 1][1])
                y = fade(bed_track(sg[0], end - sg[1] + 0.3), 0.15, 0.3)
                A.place(beds, 0.2 * y, s0 + sg[1])
            continue
        if not sc["bed"]:
            continue
        name, gain = sc["bed"]
        y = fade(bed_track(name, sc["dur"]), 0.5, 1.0) * gain
        for a0, b0 in fg_windows(sc):
            i0 = int(a0 * A.SR)
            i1 = int(b0 * A.SR)
            y[max(i0, 0):min(i1, len(y))] = 0.0
            r = int(0.3 * A.SR)
            if i0 - r > 0:
                y[i0 - r:i0] *= np.linspace(1, 0, r)
            if i1 + r < len(y):
                y[i1:i1 + r] *= np.linspace(0, 1, r)
        if name == "rain":
            st = next((i for i in sc["items"] if i.get("rain_stop")), None)
            if st:
                i0 = int(st["t0"] * A.SR)
                i1 = int(st["t2"] * A.SR)
                y[i0:i1] *= np.linspace(1, 0, i1 - i0)
                y[i1:] = 0
        A.place(beds, y, s0)
    m = voice + songs + beds * duck + sfx
    m = np.tanh(m * 1.1) / 1.1
    m *= 0.93 / max(np.abs(m).max(), 1e-6)
    return m.astype(np.float32)


def write_audio(scenes, clips, T):
    import soundfile as sf
    m = mix(scenes, clips, T)
    path = os.path.join(BUILD, "audio.wav")
    sf.write(path, np.stack([m, m], 1), A.SR, subtype="PCM_16")
    print("audio: %.1f s -> %s" % (len(m) / A.SR, path))
    return path


# ------------------------------------------------------------------- video
_G = {}


def _setup(scenes, T):
    _G["scenes"] = scenes
    _G["T"] = T
    _G["starts"] = [sc["start"] for sc in scenes]
    orange = None
    for sc in scenes:
        for it in sc["items"]:
            if it.get("orange_on"):
                orange = sc["start"] + it["t0"]
    _G["orange"] = orange
    n = loc()
    for i, (s, c, sz) in enumerate(SC.CREDITS):
        if "LOC_PLACEHOLDER" in s:
            SC.CREDITS[i] = (s.replace("LOC_PLACEHOLDER", "{:,}".format(n)),
                             c, sz)


def scene_at(T):
    import bisect
    i = bisect.bisect_right(_G["starts"], T) - 1
    return max(0, min(i, len(_G["scenes"]) - 1))


def draw_scene(i, T, frame):
    sc = _G["scenes"][i]
    cv = Canvas()
    ctx = SC.Ctx(sc, T - sc["start"], T, frame)
    SC.RENDER[sc["kind"]](cv, ctx)
    return cv, ctx


def overlays(cv, ctx):
    it = ctx.cur
    sc = ctx.sc
    # stamps with shake
    for x in sc["items"]:
        if "stamp" in x and x["t0"] <= ctx.t < x["t2"] + 0.1:
            dt = ctx.t - x["t0"]
            dx, dy = ui.stamp_shake(dt)
            fx.shake(cv, dx, dy)
            ui.stamp(cv, dt, x["stamp"], x.get("stamp2", ""), sc1=3,
                     sc2=2)
    # subtitles
    if it is not None and it["type"] == "line" and ctx.t <= it["t1"] + 0.3:
        prog = gfx.clamp01((ctx.t - it["t0"]) / max(it["t1"] - it["t0"],
                                                     0.1))
        ui.subtitles(cv, it["text"], it["speaker"], prog)
    elif ctx.idx > 0:
        prev = ctx.items[ctx.idx - 1]
        if prev["type"] == "line" and ctx.t <= prev["t1"] + 0.3 and \
                it["type"] != "line":
            ui.subtitles(cv, prev["text"], prev["speaker"], 1.0)


def render_frame(frame):
    T = frame * timeline.FPS_DEN / timeline.FPS_NUM
    i = scene_at(T)
    cv, ctx = draw_scene(i, T, frame)
    sc = _G["scenes"][i]
    lt = T - sc["start"]
    if i > 0 and lt < DISSOLVE and sc["id"] not in NO_DISSOLVE:
        prev = _G["scenes"][i - 1]
        pcv, pctx = draw_scene(i - 1, prev["start"] + prev["dur"] - 0.02,
                               frame)
        cv.fb[:] = fx.dissolve(pcv.fb, cv.fb, lt / DISSOLVE)
    overlays(cv, ctx)
    if _G["orange"] is not None and T >= _G["orange"]:
        cv.orange_pixel = ORANGE_XY
    return cv.rgb()


def encode_chunk(args):
    k0, k1, path = args[:3]
    crf = args[3] if len(args) > 3 else CRF
    cmd = [ffmpeg(), "-y", "-loglevel", "error", "-f", "rawvideo",
           "-pix_fmt", "rgb24", "-s", "%dx%d" % (W, H), "-r", "30000/1001",
           "-i", "-", "-vf", "scale=1280:960:flags=neighbor", "-c:v",
           "libx264", "-preset", PRESET, "-tune", "animation", "-crf", str(crf),
           "-pix_fmt", "yuv420p", "-threads", "1", path]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    t0 = time.time()
    for k in range(k0, k1):
        p.stdin.write(render_frame(k).tobytes())
        if (k - k0) % 600 == 0:
            print("  chunk %s: %d/%d (%.0fs)" % (os.path.basename(path),
                  k - k0, k1 - k0, time.time() - t0), flush=True)
    p.stdin.close()
    p.wait()
    return path


# Busy chunks (3D, fireworks, dithered motion) get a higher CRF: motion
# hides the difference, and the file has to fit under GitHub's 100 MB.
HEAVY_BYTES = 6_000_000
HEAVY_CRF = "30"


def plan_chunks(T, jobs):
    nframes = int(round(T * timeline.FPS))
    per = int(math.ceil(nframes / (jobs * 3)))
    return [(c, min(c + per, nframes), os.path.join(BUILD,
             "chunk_%05d.mp4" % c)) for c in range(0, nframes, per)]


def render_video(scenes, T, jobs=4, audio_path=None, only_heavy=False):
    _setup(scenes, T)
    chunks = plan_chunks(T, jobs)
    todo = chunks
    if only_heavy:
        todo = [c + (HEAVY_CRF,) for c in chunks
                if os.path.getsize(c[2]) > HEAVY_BYTES]
    print("%d chunks to encode, %d jobs" % (len(todo), jobs))
    ctx = mp.get_context("fork")
    with ctx.Pool(jobs) as pool:
        pool.map(encode_chunk, todo, chunksize=1)
    paths = [c[2] for c in chunks]
    lst = os.path.join(BUILD, "chunks.txt")
    with open(lst, "w") as f:
        for p in paths:
            f.write("file '%s'\n" % p)
    cmd = [ffmpeg(), "-y", "-loglevel", "error", "-f", "concat", "-safe",
           "0", "-i", lst, "-i", audio_path, "-map", "0:v", "-map", "1:a",
           "-c:v", "copy", "-c:a", "aac", "-ac", "1", "-b:a", "80k",
           "-shortest", "-movflags", "+faststart", FINAL]
    subprocess.check_call(cmd)
    print("wrote", FINAL, os.path.getsize(FINAL) // (1 << 20), "MB")


def frames(times, scenes, T, outdir):
    from PIL import Image
    _setup(scenes, T)
    os.makedirs(outdir, exist_ok=True)
    paths = []
    for tt in times:
        k = int(round(float(tt) * timeline.FPS))
        img = Image.fromarray(render_frame(k))
        p = os.path.join(outdir, "f_%07.2f.png" % float(tt))
        img.save(p)
        paths.append(p)
    return paths


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "video"
    if cmd == "timeline":
        get_timeline(rebuild=True)
    elif cmd == "frames":
        sc, cl, T = get_timeline()
        out = os.environ.get("FRAMES_DIR", os.path.join(BUILD, "frames"))
        for p in frames(sys.argv[2:], sc, T, out):
            print(p)
    elif cmd == "audio":
        write_audio(*get_timeline())
    elif cmd == "heavy":
        sc, cl, T = get_timeline()
        render_video(sc, T, 4, os.path.join(BUILD, "audio.wav"),
                     only_heavy=True)
    elif cmd == "preview":
        a, b = float(sys.argv[2]), float(sys.argv[3])
        sc, cl, T = get_timeline()
        _setup(sc, T)
        k0, k1 = int(a * timeline.FPS), int(b * timeline.FPS)
        tmp = os.path.join(BUILD, "preview_v.mp4")
        encode_chunk((k0, k1, tmp))
        out = os.path.join(BUILD, "preview.mp4")
        subprocess.check_call([ffmpeg(), "-y", "-loglevel", "error", "-i",
                               tmp, "-ss", str(k0 / timeline.FPS), "-t",
                               str((k1 - k0) / timeline.FPS), "-i",
                               os.path.join(BUILD, "audio.wav"), "-map",
                               "0:v", "-map", "1:a", "-c:v", "copy", "-c:a",
                               "aac", "-b:a", "160k", "-shortest", out])
        print(out)
    elif cmd == "video":
        jobs = int(sys.argv[sys.argv.index("--jobs") + 1]) if \
            "--jobs" in sys.argv else 4
        sc, cl, T = get_timeline("--rebuild" in sys.argv)
        ap = write_audio(sc, cl, T)
        render_video(sc, T, jobs, ap)
        render_video(sc, T, jobs, ap, only_heavy=True)
