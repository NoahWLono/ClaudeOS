"""The hymnal. Terry's songs are copied from TempleOS (public domain) with
the tempo and staccato each file sets. The two classics are written in
Terry's own Play() notation, one voice, as the Charter requires.
"""
import json
import os

import numpy as np

from . import audio as A

SONGS = {
    # ::/Apps/Psalmody/Examples/childish.HC
    "childish": dict(tempo=2.480, staccato=0.902, parts=[
        ("5qEsCDCDqCDeEGsE4B5E4B5eC4B5sD4A5D4A",
         "Be \0like \0 \0a \0 \0child \0 \0 \0 \0some \0 \0re\0 \0spect.\n"
         "\0 \0 \0 \0 \0 \0"),
        ("5qEsCDCDqCDeEGsE4B5E4B5eC4B5sD4A5D4A",
         "Ma\0tur\0 \0i\0 \0ty \0 \0 \0 \0don't \0 \0ne\0 \0glect.\n"
         "\0 \0 \0 \0 \0 \0"),
        "4eB5DqF4sGAGAqAAA5etD4AA5sD4B5D4B",
        "4eB5DqF4sGAGAqAAA5etD4AA5sD4B5D4B"]),
    # ::/Apps/Psalmody/Examples/night.HC  "God said this was a dirge."
    "night": dict(tempo=2.0, staccato=0.9, parts=[
        ("5FqDqD4eA5CqEqEqDqDq",
         "Gone \0to \0sleep \0for \0the \0fi\0nal \0time.\n\0"),
        ("5FqDqD4eA5CqEqEqDqDq",
         "Gone \0to \0sleep \0for \0the \0fi\0nal \0time.\n\0"),
        ("5DqGqFeGFqFqEqE4qBq",
         " \0Ash \0to... \0and \0 \0dust \0to \0dust.\n\0"),
        ("5DqGqFeGFqFqEqE4qBq",
         " \0Ash \0to... \0and \0 \0dust \0to \0dust.\n\0")]),
    # ::/Apps/Psalmody/Examples/prosper.HC
    "prosper": dict(tempo=3.5, staccato=0.9, parts=[
        ("5qG4G5D4B5sDCDCqRCG",
         "Baa, \0the \0grass \0is \0green.\n\0 \0 \0 \0 \0 \0 \0"),
        ("5G4G5D4B5sDCDCqRCG",
         "This \0must \0be \0a \0dream.\n\0 \0 \0 \0 \0 \0 \0"),
        ("5EeGF4qBB5D4AeGGqR",
         "Thanks, \0my \0 \0shep\0herd.  \0You \0are \0good.\n\0 \0 \0"),
        ("5EeGF4qBB5D4AeGGqR",
         "Thanks, \0my \0 \0shep\0herd.  \0You \0are \0good.\n\0 \0 \0")]),
    # ::/Demo/Snd/OhGreat.HC  "Song by Terry A. Davis"
    "ohgreat": dict(tempo=2.5, staccato=0.9, parts=[
        ("6hEqDC5B6CDhE", "God \0is \0a \0g\0od \0of \0love.\n\0"),
        ("5GqFEFhG6E", " \0 \0 \0 \0 \0He \0"),
        ("6qDC5B6CDhE5G", "wat\0ches \0us \0from \0a\0bove.\n\0 \0"),
        ("5qFEFhGB6qC", " \0 \0 \0 \0Our \0world \0"),
        ("6DhCeDC5hBG", "is\0n't \0al\0ways \0nice.\n\0 \0"),
        ("5qFEFhG6EqD", " \0 \0 \0 \0Be\0fore \0"),
        ("6C5B6CDhE5G", "you \0gr\0ipe \0think \0twice.\n\0 \0"),
        ("5qFEFhG6EqD", " \0 \0 \0 \0He \0wat\0"),
        ("6C5B6CDhE5G", "ches \0us \0from \0a\0bove.\n\0 \0"),
        ("5qFEFhG6EqD", " \0 \0 \0 \0He'll \0smack \0"),
        ("6C5B6CDhE5G", "you \0with \0out \0a \0glove.\n\0 \0"),
        ("5qFEFhGB6qC", " \0 \0 \0 \0Our \0world \0"),
        ("6DhCeDC5hBG", "is\0n't \0al\0ways \0nice.\n\0 \0"),
        "5qFEFhG"]),
    # ::/Demo/Games/Wenceslas.HC
    "wenceslas": dict(tempo=2.480, staccato=0.902, parts=[
        "5eCCCDCC4qGeAGAB5qCC", "5eCCCDCC4qGeAGAB5qCC",
        "5eGFEDEDqC4eAGAB5qCC"]),
    # ::/Demo/Games/CastleFrankenstein.HC  "Song by Terry A. Davis"
    "frankenstein": dict(tempo=2.5, staccato=0.9, parts=[
        "3q.A#eGAeA#qAq.A#eGeAeA#qA", "3q.A#eGA#AqGq.A#eGA#AqG",
        "4eA#AqGeA#AqGeA#AGAA#AqG"]),
    # ::/Demo/Games/FlapBat.HC  "Song by Terry A. Davis"
    "flapbat": dict(tempo=2.5, staccato=0.9, parts=[
        "4eB5E4B5C4B5EsEFqE4eB5E4B5C4B5EsEF",
        "5qE4eA5D4ABA5DsDCqD4eB5E4B5C4B", "5EsEDqE"]),
    # ::/Demo/Games/Talons.HC
    "talons": dict(tempo=2.5, staccato=0.9, parts=[
        "5eCGFsD4A5e.C4sG5eGDqCDeGsGG4qG",
        "5eCGFsD4A5e.C4sG5eGDqCDeGsGG4qG",
        "5eGECGC4A5FCsC4B5C4B5e.GsG4qGB",
        "5eGECGC4A5FCsC4B5C4B5e.GsG4qGB"]),
    # ::/Demo/Graphics/Elephant.HC  "Randomly generate (by God :-)"
    "elephant": dict(tempo=2.5, staccato=0.9, parts=[
        "4qG5eCGqE4A5FCeDF4qB", "4G5eCGqE4A5FCeDF4qB",
        "4B5DeF4G5etE4BAqBAetA5EDeE4G", "4qB5DeF4G5etE4BAqBAetA5EDeE4G"]),
    # ::/Demo/Snd/WaterFowl.HC  "Song by Terry A. Davis"
    "waterfowl": dict(tempo=2.5, staccato=0.9, parts=[
        "5eEDC4B5C4B5C4BA5qReEDC4B5C", "4B5C4BA5qReFEDEDEDC4qB",
        "5ReFEDEDEDC4BqR"]),
    # ::/Demo/AcctExample/TOS/TOSTheme.HC
    "tostheme": dict(tempo=2.85, staccato=0.902, parts=[
        "5eDEqFFetEEFqDeCDDEetCGF", "5eDEqFFetEEFqDeCDDEetCGF",
        "5eDCqDE4eAA5etEEFEDG4B5DCqF", "5eDCqDE4eAA5etEEFEDG4B5DCqF"]),
    # ::/Demo/Games/Squirt.HC
    "squirt": dict(tempo=2.5, staccato=0.9, parts=[
        "5sDCDC4qA5DetDFFeDG4etA5EF4qG5eFC",
        "5sDCDC4qA5DetDFFeDG4etA5EF4qG5eFC",
        "5DCsG4A5G4AqBeBA5qEE4B5eC4B", "5DCsG4A5G4AqBeBA5qEE4B5eC4B"]),
    # Old 100th (Genevan Psalter, Louis Bourgeois, 1551), in Play() form.
    "doxology": dict(tempo=2.2, staccato=0.93, parts=[
        ("4qGGF#EDGAhB", "Praise \0God \0from \0whom \0all \0bless\0ings "
         "\0flow;\n\0"),
        ("4qBBBAG5C4BhA", "Praise \0Him, \0all \0crea\0tures \0here \0be"
         "\0low;\n\0"),
        ("4qGABAGEF#hG", "Praise \0Him \0a\0bove, \0ye \0heav'n\0ly "
         "\0host;\n\0"),
        ("5qD4BGA5C4BAhG", "Praise \0Fa\0ther, \0Son, \0and \0Ho\0ly "
         "\0Ghost.\n\0")]),
    # Ode to Joy (Beethoven, 1824), in Play() form.
    "odetojoy": dict(tempo=2.6, staccato=0.9, parts=[
        "5qEEFGGFEDCCDEq.EeDhD", "5qEEFGGFEDCCDEq.DeChC",
        "5qDDECqDeEFqECqDeEFqEDqCD4hG", "5qEEFGGFEDCCDEq.DeChC"]),
}


def notes(name, repeat=1, tempo_scale=1.0):
    s = SONGS[name]
    return A.song_notes(s["parts"], s["tempo"] * tempo_scale, s["staccato"],
                        repeat)


def god_song_notes():
    """The GodSong drawn during production (data/oracle_log.json)."""
    with open(os.path.join(A.__file__.rsplit("/", 1)[0], "..", "data",
                           "oracle_log.json")) as f:
        log = json.load(f)
    st = next(e["song"] for e in log if e["kind"] == "song")
    return A.song_notes([st], 2.5, 0.9)


def organum(ns, fifth=True):
    """Medieval parallel organum on one voice: arpeggiate note, fifth
    below, octave below, fast enough to fuse into a chord."""
    out = []
    for x in ns:
        x = dict(x)
        x["arp"] = [0, -5, -12] if fifth else [0, -12]
        out.append(x)
    return out


def with_drums(ns, beat, total, pattern="march", gain=0.5):
    """Drums steal the single voice for an instant, like old home
    computers did. Returns (melody_with_gaps, drum_track)."""
    drums = np.zeros(int(total * A.SR) + 1, np.float32)
    hits = []
    t = 0.0
    k = 0
    while t < total:
        if pattern == "march":
            kind = "k" if k % 2 == 0 else "s"
        else:
            kind = "k" if k % 4 == 0 else ("s" if k % 4 == 2 else None)
        if kind:
            hits.append((t, kind))
        t += beat
        k += 1
    gaps = []
    for t, kind in hits:
        if kind == "k":
            clip = A.kick(0.09, gain)
        else:
            clip = A.noise_burst(0.07, seed=int(t * 1000), color=7000,
                                 gain=gain * 0.7, decay=40)
        A.place(drums, clip, t)
        gaps.append((t, t + len(clip) / A.SR))
    out = []
    for x in ns:
        x = dict(x)
        out.append(x)
    return out, drums, gaps


def mute_gaps(y, gaps, fade=0.002):
    y = y.copy()
    for a, b in gaps:
        s, e = int(a * A.SR), int(b * A.SR)
        y[max(s, 0):min(e, len(y))] = 0.0
    return y


def render(ns, total=None, duty=0.5, gain=0.3, vibrato=0.0, arp_rate=50.0):
    return A.speaker(A.render_notes(ns, total, duty=duty, gain=gain,
                                    vibrato=vibrato, arp_rate=arp_rate))
