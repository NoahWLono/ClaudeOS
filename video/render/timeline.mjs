// Builds the master timeline from script.json + synthesized line durations.
// Everything (video frames, SFX cues, music, captions) is placed from this.
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

export const FPS = 30;
export const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');

export function loadTimeline() {
  const script = JSON.parse(fs.readFileSync(path.join(ROOT, 'script.json'), 'utf8'));
  const meta = JSON.parse(fs.readFileSync(path.join(ROOT, 'build/tts/lines.json'), 'utf8'));
  const scenes = [];
  let T = 0;
  for (const sc of script.scenes) {
    let t = sc.lead ?? 0.6;
    const lines = sc.lines.map((ln, i) => {
      const m = meta[`${sc.id}_${i}`];
      if (!m) throw new Error(`missing TTS for ${sc.id}_${i}`);
      if (ln.at != null) t = ln.at;
      const L = { ...ln, i, key: `${sc.id}_${i}`, start: t, end: t + m.dur, dur: m.dur, env: m.env };
      t = L.end + (ln.pause ?? 0.35);
      return L;
    });
    const last = lines[lines.length - 1];
    let dur = last ? last.end + (last.pause ?? 0) + (sc.tail ?? 0.6) : sc.minDur ?? 3;
    dur = Math.max(dur, sc.minDur ?? 0);
    dur = Math.ceil(dur * FPS) / FPS; // keep scene boundaries frame-aligned
    scenes.push({ ...sc, lines, start: T, dur, frames: Math.round(dur * FPS), frame0: Math.round(T * FPS) });
    T += dur;
  }
  const byId = Object.fromEntries(scenes.map(s => [s.id, s]));
  return { script, cast: script.cast, scenes, byId, total: T, frames: Math.round(T * FPS) };
}

// Per-scene helper handed to scene renderers.
export function sceneHelper(TL, sc) {
  const S = {
    ...sc, TL,
    L: i => sc.lines[i].start,           // line start (scene-relative seconds)
    E: i => sc.lines[i].end,             // line end
    tag: name => { const l = sc.lines.find(l => l.tag === name); return l ? l.start : Infinity; },
    active: t => sc.lines.find(l => t >= l.start && t < l.end) || null,
    // mouth openness for a speaker at time t (0..1), from the real audio envelope
    talk(who, t) {
      for (const l of sc.lines) {
        if ((l.who === who || l.who === 'all') && t >= l.start && t < l.end) {
          const f = (t - l.start) * FPS, i = Math.floor(f), a = f - i;
          const e0 = l.env[i] ?? 0, e1 = l.env[i + 1] ?? 0;
          return Math.min(1, (e0 * (1 - a) + e1 * a) * 1.15);
        }
      }
      return 0;
    },
    speaking: (who, t) => sc.lines.some(l => l.who === who && t >= l.start && t < l.end),
    // global time of another scene's start (for effects that span scenes, e.g. the speedrun timer)
    gstart: id => TL.byId[id].start,
  };
  return S;
}
