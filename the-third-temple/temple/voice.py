"""Voices. The one place this production fetched something from storage:
Kokoro-82M (Apache 2.0), an open-weight text-to-speech model. Charter
violation #4, confessed on screen. Everything after the model is
calculated here: pitch, echo, the loudspeaker, the cathedral.
"""
import hashlib
import os

import numpy as np
import soundfile as sf

from . import audio as A

MODEL_DIR = os.environ.get("KOKORO_DIR", "/home/user/models")
CACHE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..",
                     "build", "tts")

CAST = {
    # speaker: (kokoro voice, speed)
    "CLAUDE": ("af_heart", 1.0),
    "ANNOUNCER": ("am_michael", 0.92),
    "GOD": ("am_fenrir", 0.80),
}

_kokoro = None


def _engine():
    global _kokoro
    if _kokoro is None:
        from kokoro_onnx import Kokoro
        _kokoro = Kokoro(os.path.join(MODEL_DIR, "kokoro-v1.0.onnx"),
                         os.path.join(MODEL_DIR, "voices-v1.0.bin"))
    return _kokoro


def raw_tts(text, voice, speed):
    """Kokoro at 24 kHz, cached on disk, returned at 48 kHz."""
    os.makedirs(CACHE, exist_ok=True)
    key = hashlib.sha1(("%s|%s|%.3f" % (text, voice, speed)).encode()
                       ).hexdigest()[:16]
    path = os.path.join(CACHE, key + ".wav")
    if not os.path.exists(path):
        y, sr = _engine().create(text, voice=voice, speed=speed,
                                 lang="en-us" if voice[0] == "a" else "en-gb")
        sf.write(path, y, sr)
    y, sr = sf.read(path, dtype="float32")
    return A.resample(y, sr, A.SR)


def trim(y, thresh=0.008, pad=0.03):
    idx = np.where(np.abs(y) > thresh)[0]
    if len(idx) == 0:
        return y[:1]
    s = max(idx[0] - int(pad * A.SR), 0)
    e = min(idx[-1] + int(pad * A.SR), len(y))
    return y[s:e]


def fx_claude(y):
    y = A.highpass(y, 70)
    y = A.normalize_rms(y, -19.0)
    return A.reverb(y, 0.6, wet=0.07, predelay=0.01, seed=3)


def fx_announcer(y):
    """A stadium loudspeaker: narrow band, pushed hard, bouncing around."""
    y = A.bandpass(y, 220, 3800)
    y = A.normalize_rms(y, -17.0)
    y = np.tanh(2.2 * y) / np.tanh(2.2)
    y = A.echo(y, [(0.11, 0.28), (0.23, 0.13), (0.37, 0.06)])
    y = A.reverb(y, 1.6, wet=0.22, predelay=0.03, seed=11)
    return A.normalize_rms(y, -19.5)


def fx_god(y, shift=0.92):
    """Slower and lower (plain resampling), in a stone room. Light enough
    that the words survive: tested by transcribing them back."""
    n = int(len(y) / shift)
    idx = np.arange(n) * shift
    y = np.interp(idx, np.arange(len(y)), y).astype(np.float32)
    y = A.lowpass(A.highpass(y, 60), 7000)
    y = A.normalize_rms(y, -18.0)
    return A.reverb(y, 2.4, wet=0.22, predelay=0.04, seed=19, damp=3500)


FX = {"CLAUDE": fx_claude, "ANNOUNCER": fx_announcer, "GOD": fx_god}


def speak(speaker, text):
    voice, speed = CAST[speaker]
    dry = trim(raw_tts(text, voice, speed))
    return FX[speaker](dry), len(dry) / A.SR
