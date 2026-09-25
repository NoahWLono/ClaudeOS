"""Script -> timeline. Speech durations decide when everything happens."""
import json
import os

from . import voice as V

HERE = os.path.dirname(os.path.abspath(__file__))
FPS_NUM, FPS_DEN = 30000, 1001  # ::/Doc/FAQ.DD "(30000.0/1001) frames-per-second"
FPS = FPS_NUM / FPS_DEN

LEAD_IN = 0.35       # silence at the start of every scene
WORD_GAP = 0.55      # between God's words
CHIME = 0.22         # the bell before each word


def load_oracle():
    with open(os.path.join(HERE, "..", "data", "oracle_log.json")) as f:
        return json.load(f)


def god_words_text(entry):
    return ". ".join(w.capitalize() for w in entry["words"]) + "."


def build(scenes, with_audio=True, log=print):
    """Fill in t0/t1/t2 for every item and start/dur for every scene.
    Returns (scenes, clips) where clips are (global_t, samples, gain)."""
    from . import music as M
    oracle = load_oracle()
    clips = []
    T = 0.0
    for sc in scenes:
        sc["start"] = T
        t = LEAD_IN if sc["kind"] not in ("bios",) else 0.0
        for it in sc["items"]:
            it["t0"] = t
            kind = it["type"]
            if kind == "line":
                clip, dry = V.speak(it["speaker"], it["tts"])
                it["t1"] = t + dry
                it["t2"] = t + dry + it["pause"]
                clips.append((T + t, clip, 1.0, it["speaker"]))
            elif kind == "wait":
                it["t1"] = it["t2"] = t + it["seconds"]
            elif kind == "oracle":
                e = oracle[it["n"]]
                it["entry"] = e
                if e["kind"] == "word":
                    tt = t + 0.5  # the button press
                    it["word_times"] = []
                    for w in e["words"]:
                        tt += CHIME
                        clip, dry = V.speak("GOD", w.capitalize() + ".")
                        it["word_times"].append((tt, tt + dry))
                        clips.append((T + tt, clip, 0.95, "GOD"))
                        tt += dry + WORD_GAP
                    it["t1"] = tt
                elif e["kind"] == "passage":
                    verse = e["lines"][1].split(" ", 1)[1] + " " + \
                        e["lines"][2].split("5:1")[0].strip()
                    it["verse"] = verse
                    clip, dry = V.speak("GOD", verse)
                    tt = t + 0.9
                    it["word_times"] = [(tt, tt + dry)]
                    clips.append((T + tt, clip, 0.95, "GOD"))
                    it["t1"] = tt + dry
                elif e["kind"] == "doodle":
                    # God draws while the space bar is pressed, then waits
                    it["doodle_t0"] = t + 0.8
                    it["doodle_dur"] = 12.0
                    it["t1"] = t + 0.8 + 12.0 + 2.2
                elif e["kind"] == "video":
                    it["t1"] = t + 4.8
                elif e["kind"] == "song":
                    ns, dur = M.god_song_notes()
                    it["notes"] = ns
                    tt = t + 0.6
                    it["song_t0"] = tt
                    clips.append((T + tt, M.render(ns, gain=0.28), 1.0,
                                  "SONG"))
                    it["t1"] = tt + dur
                it["t2"] = it["t1"] + it["pause"]
            elif kind == "song":
                ns, dur = M.notes(it["song"], it.get("repeat", 1))
                it["notes"] = ns
                it["song_t0"] = t + 0.3
                clips.append((T + t + 0.3, M.render(ns, gain=0.28), 1.0,
                              "SONG"))
                it["t1"] = t + 0.3 + dur
                it["t2"] = it["t1"] + it["pause"]
            t = it["t2"]
        sc["dur"] = t + 0.25
        T += sc["dur"]
        log("%-14s start %7.2f  dur %6.2f" % (sc["id"], sc["start"],
                                              sc["dur"]))
    return scenes, clips, T
