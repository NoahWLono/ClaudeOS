// Frame renderer: dispatches to scene modules, then draws global overlays
// (captions, transitions, channel bug).
import { createCanvas, GlobalFonts } from '@napi-rs/canvas';
import fs from 'fs';
import path from 'path';
import { loadTimeline, sceneHelper, FPS, ROOT } from './timeline.mjs';
import { W, H, C, clamp, ease, prog, rr, font, txt, wrap } from './lib.mjs';
import * as CH from './characters.mjs';

const FDIR = path.join(ROOT, 'assets/fonts');
for (const f of fs.readdirSync(FDIR)) GlobalFonts.registerFromPath(path.join(FDIR, f), f.replace(/\.(ttf|woff)$/, ''));

export async function loadAll() {
  const TL = loadTimeline();
  const mods = {};
  const dir = path.join(ROOT, 'render/scenes');
  for (const f of fs.readdirSync(dir)) if (f.endsWith('.mjs')) {
    const m = (await import(path.join(dir, f))).default;
    for (const id of [].concat(m.id)) mods[id] = m;
  }
  const helpers = TL.scenes.map(sc => sceneHelper(TL, sc));
  return { TL, mods, helpers };
}

// ---------- captions ----------
function chunkText(s) {
  const parts = s.split(/(?<=[.?!:;])\s+|\s+\/\s+/);
  const out = [];
  for (const p of parts) {
    const last = out[out.length - 1];
    if (last && (last.length + p.length < 70 || p.length < 14)) out[out.length - 1] = last + ' ' + p; else out.push(p);
  }
  return out;
}
const _cap = new Map();
function capInfo(line) {
  if (_cap.has(line.key)) return _cap.get(line.key);
  const chunks = chunkText(line.text);
  const tot = chunks.reduce((a, c) => a + c.length + 1, 0);
  let acc = 0; const spans = chunks.map(c => { const a = acc / tot; acc += c.length + 1; return { text: c, a, b: acc / tot }; });
  const cum = []; let s = 0;
  for (const e of line.env) { s += e > 0.06 ? 0.4 + e : 0.02; cum.push(s); }
  const info = { spans, cum, total: s };
  _cap.set(line.key, info);
  return info;
}
function drawCaption(ctx, TL, line, t) {
  const info = capInfo(line);
  const f = clamp((t - line.start) * FPS, 0, info.cum.length - 1);
  const p = info.total ? info.cum[Math.floor(f)] / info.total : 0;
  const sp = info.spans.find(s => p < s.b) || info.spans[info.spans.length - 1];
  const local = clamp((p - sp.a) / (sp.b - sp.a));
  const cast = TL.cast[line.who] || {};
  const color = (CH.CHAR_INFO?.[line.who]?.color) || cast.color || C.orange;
  const name = cast.name || line.who;
  const fs = 46, lh = 60, maxW = 1500;
  ctx.save();
  ctx.font = font('Nunito-800', fs);
  const rows = wrap(ctx, sp.text, maxW);
  const w = Math.min(maxW, Math.max(...rows.map(r => ctx.measureText(r).width))) + 70;
  const h = rows.length * lh + 34;
  const x = (W - w) / 2, y = H - 48 - h;
  const fadeIn = clamp((t - line.start) / 0.12);
  ctx.globalAlpha = fadeIn;
  ctx.fillStyle = 'rgba(20,20,19,0.86)'; rr(ctx, x, y, w, h, 20); ctx.fill();
  ctx.strokeStyle = color; ctx.lineWidth = 4; rr(ctx, x, y, w, h, 20); ctx.stroke();
  // name tag
  ctx.font = font('Nunito-900', 28);
  const nw = ctx.measureText(name).width + 36;
  ctx.fillStyle = color; rr(ctx, x + 26, y - 26, nw, 44, 22); ctx.fill();
  ctx.strokeStyle = C.ink; ctx.lineWidth = 3; rr(ctx, x + 26, y - 26, nw, 44, 22); ctx.stroke();
  txt(ctx, name, x + 26 + nw / 2, y - 3, { fam: 'Nunito-900', size: 28, color: C.ink, align: 'center', base: 'middle' });
  // words, karaoke-lit
  ctx.font = font('Nunito-800', fs); ctx.textBaseline = 'alphabetic'; ctx.textAlign = 'left';
  const totalChars = sp.text.length; let seen = 0;
  rows.forEach((r, i) => {
    const rw = ctx.measureText(r).width; let xx = (W - rw) / 2; const yy = y + 17 + fs + i * lh - 4;
    for (const word of r.split(' ')) {
      const lit = (seen + word.length * 0.5) / totalChars <= local + 0.02;
      ctx.fillStyle = lit ? '#FFFFFF' : 'rgba(255,255,255,0.55)';
      ctx.fillText(word, xx, yy);
      xx += ctx.measureText(word + ' ').width; seen += word.length + 1;
    }
  });
  ctx.restore();
}

// ---------- transitions ----------
function wipe(ctx, k, dir) {
  // k: 0..1 coverage progress. dir 'in' reveals scene (panel leaves), 'out' covers.
  const off = dir === 'out' ? lerpW(-1.25, 0, ease.inOut(k)) : lerpW(0, 1.25, ease.inOut(k));
  ctx.save(); ctx.translate(off, 0);
  ctx.fillStyle = C.orange; ctx.beginPath(); ctx.moveTo(-200, 0); ctx.lineTo(W + 100, 0); ctx.lineTo(W - 100, H); ctx.lineTo(-400, H); ctx.closePath(); ctx.fill();
  ctx.fillStyle = C.ink; ctx.beginPath(); ctx.moveTo(W + 100, 0); ctx.lineTo(W + 160, 0); ctx.lineTo(W - 40, H); ctx.lineTo(W - 100, H); ctx.closePath(); ctx.fill();
  if (CH.drawSpark) CH.drawSpark(ctx, W / 2 - 120, H / 2, 110, C.cream, k * 3);
  ctx.restore();
}
const lerpW = (a, b, k) => (a + (b - a) * k) * W;

function bug(ctx, t) {
  ctx.save(); ctx.globalAlpha = 0.75;
  if (CH.drawSpark) CH.drawSpark(ctx, 62, 58, 20, C.orange, t * 0.5);
  txt(ctx, 'OPUS 5.5', 92, 52, { fam: 'Anton', size: 30, color: '#FFFFFF', stroke: C.ink, sw: 6, track: 2 });
  txt(ctx, 'MINISTRY OF ROLLING RELEASE', 94, 80, { fam: 'Nunito-900', size: 16, color: '#FFFFFF', stroke: C.ink, sw: 4, track: 1 });
  ctx.restore();
}

function placeholder(ctx, sc, t) {
  ctx.fillStyle = '#333'; ctx.fillRect(0, 0, W, H);
  txt(ctx, `[${sc.id}] t=${t.toFixed(2)}`, W / 2, H / 2, { size: 80, color: '#fff', align: 'center' });
}

export function renderFrame(ctx, world, frame) {
  const { TL, mods, helpers } = world;
  const T = frame / FPS;
  let si = TL.scenes.findIndex(s => T >= s.start && T < s.start + s.dur);
  if (si < 0) si = TL.scenes.length - 1;
  const sc = TL.scenes[si], S = helpers[si], mod = mods[sc.id];
  const t = (frame - sc.frame0) / FPS;
  ctx.save();
  if (mod) mod.render(ctx, t, S, CH); else placeholder(ctx, sc, t);
  ctx.restore();
  if (!sc.noBug && !(sc.card && t < 2.6)) bug(ctx, T);
  const line = sc.nocaps ? null : S.active(t);
  if (line && !line.nocap) drawCaption(ctx, TL, line, t);
  const next = TL.scenes[si + 1];
  const tin = sc.transIn ?? 'wipe', tout = next ? (next.transIn ?? 'wipe') : 'cut';
  if (tin === 'wipe' && si > 0 && t < 0.3) wipe(ctx, t / 0.3, 'in');
  if (tout === 'wipe' && t > sc.dur - 0.3) wipe(ctx, (t - (sc.dur - 0.3)) / 0.3, 'out');
  if (tin === 'flash' && t < 0.5) { ctx.fillStyle = `rgba(255,255,255,${1 - t / 0.5})`; ctx.fillRect(0, 0, W, H); }
}

export function newCanvas() { const c = createCanvas(W, H); return [c, c.getContext('2d')]; }
export { FPS };
