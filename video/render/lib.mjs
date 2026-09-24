// Shared drawing helpers: palette, easing, text, posters, terminal, cards.
import { createCanvas } from '@napi-rs/canvas';

export const W = 1920, H = 1080;
export const C = {
  orange: '#D97757', deep: '#C15F3C', cream: '#F0EEE6', paper: '#FAF9F5', ink: '#141413',
  blue: '#1793D1', blueDeep: '#0E5E8A', blueDark: '#0A3350', pink: '#FF8FC7', pinkSoft: '#F5A9C8',
  lav: '#B39DFF', green: '#39FF14', teal: '#2EC4B6', red: '#E0443E', yellow: '#FFD23F',
  gray: '#8A877E', term: '#0C0F14', termFg: '#D6E2EE',
};

export const clamp = (x, a = 0, b = 1) => Math.max(a, Math.min(b, x));
export const lerp = (a, b, t) => a + (b - a) * t;
export const prog = (t, a, d) => clamp((t - a) / d);
export const ease = {
  out: t => 1 - Math.pow(1 - t, 3),
  in: t => t * t * t,
  inOut: t => (t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2),
  back: t => { const c1 = 1.70158, c3 = c1 + 1; return 1 + c3 * Math.pow(t - 1, 3) + c1 * Math.pow(t - 1, 2); },
  elastic: t => (t === 0 || t === 1 ? t : Math.pow(2, -10 * t) * Math.sin((t * 10 - 0.75) * (2 * Math.PI) / 3) + 1),
};
// pop-in scale: 0 -> overshoot -> 1
export const pop = (t, a, d = 0.35) => ease.back(prog(t, a, d));

export function rng(seed) {
  let a = seed >>> 0;
  return () => { a |= 0; a = (a + 0x6D2B79F5) | 0; let t = Math.imul(a ^ (a >>> 15), 1 | a); t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t; return ((t ^ (t >>> 14)) >>> 0) / 4294967296; };
}
export const hash = (n) => { const r = rng(n * 9301 + 49297); return r(); };

export function rr(ctx, x, y, w, h, r) {
  r = Math.min(r, w / 2, h / 2);
  ctx.beginPath();
  ctx.moveTo(x + r, y);
  ctx.arcTo(x + w, y, x + w, y + h, r);
  ctx.arcTo(x + w, y + h, x, y + h, r);
  ctx.arcTo(x, y + h, x, y, r);
  ctx.arcTo(x, y, x + w, y, r);
  ctx.closePath();
}

export function font(fam, px) { return `${px}px ${fam}, "DejaVu Sans", "Noto Color Emoji"`; }

export function txt(ctx, s, x, y, o = {}) {
  const { fam = 'Nunito-900', size = 48, color = C.ink, align = 'left', base = 'alphabetic', stroke = null, sw = 0, alpha = 1, maxW = 0, shadow = null, track = 0 } = o;
  ctx.save();
  ctx.globalAlpha *= alpha;
  let px = size;
  ctx.font = font(fam, px);
  if (maxW) { const w = ctx.measureText(s).width; if (w > maxW) { px = size * maxW / w; ctx.font = font(fam, px); } }
  ctx.textAlign = align; ctx.textBaseline = base;
  if (track) ctx.letterSpacing = `${track}px`;
  if (shadow) { ctx.fillStyle = shadow.color || 'rgba(0,0,0,.35)'; ctx.fillText(s, x + (shadow.dx ?? 6), y + (shadow.dy ?? 6)); }
  if (stroke) { ctx.lineJoin = 'round'; ctx.lineWidth = sw; ctx.strokeStyle = stroke; ctx.strokeText(s, x, y); }
  ctx.fillStyle = color; ctx.fillText(s, x, y);
  ctx.restore();
  return px;
}

export function wrap(ctx, s, maxW) {
  const words = s.split(/\s+/); const out = []; let cur = '';
  for (const w of words) {
    const t = cur ? cur + ' ' + w : w;
    if (ctx.measureText(t).width > maxW && cur) { out.push(cur); cur = w; } else cur = t;
  }
  if (cur) out.push(cur);
  return out;
}

// Constructivist sunburst background.
export function sunburst(ctx, cx, cy, n, a, b, rot = 0, R = 2600) {
  ctx.save();
  ctx.fillStyle = a; ctx.fillRect(0, 0, W, H);
  ctx.fillStyle = b;
  for (let i = 0; i < n; i++) {
    const t0 = rot + (i / n) * Math.PI * 2, t1 = t0 + Math.PI / n;
    ctx.beginPath(); ctx.moveTo(cx, cy);
    ctx.lineTo(cx + Math.cos(t0) * R, cy + Math.sin(t0) * R);
    ctx.lineTo(cx + Math.cos(t1) * R, cy + Math.sin(t1) * R);
    ctx.closePath(); ctx.fill();
  }
  ctx.restore();
}

// Cached halftone dot overlay (static texture = compresses well).
const _ht = {};
export function halftone(ctx, color = 'rgba(20,20,19,0.10)', step = 14, alpha = 1) {
  const k = color + step;
  if (!_ht[k]) {
    const c = createCanvas(W, H), x = c.getContext('2d');
    x.fillStyle = color;
    for (let yy = 0; yy < H + step; yy += step) for (let xx = 0; xx < W + step; xx += step) {
      const off = (Math.round(yy / step) % 2) * step / 2;
      const d = Math.hypot(xx - W * 0.5, yy - H * 0.5) / (W * 0.6);
      const r = step * 0.42 * clamp(d * d, 0.05, 1);
      x.beginPath(); x.arc(xx + off, yy, r, 0, 7); x.fill();
    }
    _ht[k] = c;
  }
  ctx.save(); ctx.globalAlpha = alpha; ctx.drawImage(_ht[k], 0, 0); ctx.restore();
}

const _vig = {};
export function vignette(ctx, strength = 0.35) {
  if (!_vig[strength]) {
    const c = createCanvas(W, H), x = c.getContext('2d');
    const g = x.createRadialGradient(W / 2, H / 2, H * 0.35, W / 2, H / 2, H * 1.05);
    g.addColorStop(0, 'rgba(0,0,0,0)'); g.addColorStop(1, `rgba(0,0,0,${strength})`);
    x.fillStyle = g; x.fillRect(0, 0, W, H); _vig[strength] = c;
  }
  ctx.drawImage(_vig[strength], 0, 0);
}

export function paper(ctx, color = C.cream) {
  ctx.fillStyle = color; ctx.fillRect(0, 0, W, H);
}

// Diagonal stripes band, used for banners.
export function banner(ctx, x, y, w, h, color, textStr, o = {}) {
  ctx.save();
  ctx.translate(x, y); ctx.rotate(o.rot ?? 0);
  ctx.fillStyle = C.ink; ctx.fillRect(-w / 2 + 8, -h / 2 + 8, w, h);
  ctx.fillStyle = color; ctx.fillRect(-w / 2, -h / 2, w, h);
  txt(ctx, textStr, 0, 0, { fam: o.fam || 'Anton', size: o.size || h * 0.68, color: o.color || C.cream, align: 'center', base: 'middle', maxW: w - 40, track: o.track ?? 2 });
  ctx.restore();
}

export function stamp(ctx, x, y, s, textStr, t, color = C.red, rot = -0.18) {
  if (t < 0) return;
  const k = t < 0.18 ? lerp(2.2, 1, ease.out(t / 0.18)) : 1;
  ctx.save(); ctx.translate(x, y); ctx.rotate(rot); ctx.scale(k * s, k * s);
  ctx.globalAlpha = clamp(t / 0.1) * 0.92;
  ctx.font = font('Anton', 64); const w = ctx.measureText(textStr).width + 60;
  ctx.strokeStyle = color; ctx.lineWidth = 8; rr(ctx, -w / 2, -52, w, 104, 14); ctx.stroke();
  ctx.lineWidth = 3; rr(ctx, -w / 2 + 10, -42, w - 20, 84, 8); ctx.stroke();
  txt(ctx, textStr, 0, 4, { fam: 'Anton', size: 64, color, align: 'center', base: 'middle' });
  ctx.restore();
}

// ---------- Terminal ----------
// events: [{at, cmd}|{at, out}|{at, clear:true}|{at, prompt}] ; cmds type at cps chars/sec
export function termRows(events, t, o = {}) {
  const cps = o.cps ?? 28; let prompt = o.prompt ?? 'root@archiso ~ #';
  const rows = []; let cursorRow = -1; let typing = false;
  for (const e of events) {
    if (e.at > t) break;
    if (e.clear) { rows.length = 0; continue; }
    if (e.prompt) { prompt = e.prompt; continue; }
    if (e.cmd != null) {
      const n = Math.floor((t - e.at) * (e.cps ?? cps));
      const shown = e.cmd.slice(0, Math.max(0, n));
      rows.push({ kind: 'cmd', prompt, text: shown, full: e.cmd, color: e.color });
      typing = n < e.cmd.length; cursorRow = rows.length - 1;
    } else if (e.out != null) {
      for (const l of String(e.out).split('\n')) rows.push({ kind: 'out', text: l, color: e.color });
      cursorRow = -1;
    }
  }
  return { rows, typing, cursorRow, prompt };
}

// Times at which each typed character lands (for keyboard SFX cues).
export function typingCues(events, sceneStart, o = {}) {
  const cps = o.cps ?? 28; const out = [];
  for (const e of events) if (e.cmd != null) {
    const c = e.cps ?? cps;
    for (let i = 0; i < e.cmd.length; i++) if (e.cmd[i] !== ' ' || i % 3 === 0) out.push({ t: sceneStart + e.at + i / c, name: ['key1', 'key2', 'key3'][i % 3], gain: 0.22 });
    out.push({ t: sceneStart + e.at + e.cmd.length / c + 0.12, name: 'enter', gain: 0.3 });
  }
  return out;
}

export function drawTerminal(ctx, x, y, w, h, state, t, o = {}) {
  const fs = o.fs ?? 30, lh = fs * 1.38, pad = 28, bar = 46;
  ctx.save();
  ctx.fillStyle = 'rgba(0,0,0,.35)'; rr(ctx, x + 12, y + 14, w, h, 18); ctx.fill();
  ctx.fillStyle = o.bg ?? C.term; rr(ctx, x, y, w, h, 18); ctx.fill();
  ctx.strokeStyle = o.border ?? C.ink; ctx.lineWidth = 5; rr(ctx, x, y, w, h, 18); ctx.stroke();
  ctx.fillStyle = o.barColor ?? '#1D2430'; ctx.beginPath(); ctx.roundRect(x + 2.5, y + 2.5, w - 5, bar, [16, 16, 0, 0]); ctx.fill();
  ['#FF5F57', '#FEBC2E', '#28C840'].forEach((c, i) => { ctx.fillStyle = c; ctx.beginPath(); ctx.arc(x + 30 + i * 30, y + bar / 2 + 2, 9, 0, 7); ctx.fill(); });
  txt(ctx, o.title ?? 'tty1 : archiso', x + w / 2, y + bar / 2 + 3, { fam: 'JBM-800', size: 20, color: '#8FA3B8', align: 'center', base: 'middle' });
  ctx.beginPath(); ctx.rect(x + 4, y + bar + 4, w - 8, h - bar - 8); ctx.clip();
  const maxRows = Math.floor((h - bar - pad * 1.2) / lh);
  const rows = state.rows.slice(-maxRows);
  const offset = state.rows.length - rows.length;
  ctx.font = font('JBM-400', fs);
  rows.forEach((r, i) => {
    const yy = y + bar + pad + fs + i * lh;
    let xx = x + pad;
    if (r.kind === 'cmd') {
      ctx.font = font('JBM-800', fs); ctx.fillStyle = o.promptColor ?? C.blue; ctx.fillText(r.prompt, xx, yy);
      xx += ctx.measureText(r.prompt + ' ').width;
      ctx.fillStyle = r.color ?? '#FFFFFF'; ctx.fillText(r.text, xx, yy);
      if (i + offset === state.cursorRow && (state.typing || Math.floor(t * 2) % 2 === 0)) {
        const cw = ctx.measureText(r.text).width; ctx.fillStyle = C.orange; ctx.fillRect(xx + cw + 3, yy - fs * 0.82, fs * 0.55, fs * 1.0);
      }
      ctx.font = font('JBM-400', fs);
    } else {
      ctx.fillStyle = r.color ?? C.termFg; ctx.fillText(r.text, xx, yy);
    }
  });
  if (state.cursorRow === -1 && o.idleCursor !== false && rows.length < maxRows) {
    const yy = y + bar + pad + fs + rows.length * lh; ctx.font = font('JBM-800', fs);
    ctx.fillStyle = o.promptColor ?? C.blue; ctx.fillText(state.prompt, x + pad, yy);
    const px = x + pad + ctx.measureText(state.prompt + ' ').width;
    if (Math.floor(t * 2) % 2 === 0) { ctx.fillStyle = C.orange; ctx.fillRect(px, yy - fs * 0.82, fs * 0.55, fs); }
  }
  ctx.restore();
}

// ---------- Section title card (first ~2.8 s of a scene) ----------
export function sectionCard(ctx, t, part, title, dur = 2.8) {
  if (t > dur) return;
  const out = prog(t, dur - 0.4, 0.4);
  ctx.save();
  ctx.translate(0, -ease.in(out) * H * 1.05);
  sunburst(ctx, W / 2, H * 0.55, 18, C.blue, '#1A86BE', t * 0.08);
  halftone(ctx, 'rgba(10,51,80,0.18)', 16);
  const k = pop(t, 0.05, 0.4);
  ctx.save(); ctx.translate(W / 2, H * 0.5); ctx.scale(k, k);
  banner(ctx, 0, -150, 520, 110, C.orange, part, { rot: -0.03, size: 78 });
  txt(ctx, title, 0, 60, { fam: 'Anton', size: 150, color: C.cream, align: 'center', base: 'middle', stroke: C.ink, sw: 14, maxW: 1700, shadow: { color: C.blueDark, dx: 10, dy: 10 }, track: 3 });
  ctx.restore();
  stamp(ctx, W - 330, H - 190, 0.9, 'APPROVED BY THE MINISTRY', t - 0.55, C.cream, -0.12);
  ctx.fillStyle = C.ink; ctx.fillRect(0, H - 22, W, 22); ctx.fillRect(0, 0, W, 22);
  ctx.restore();
}

// Floating seeded particles (confetti / sparkles).
export function confetti(ctx, t, n, seed, colors, o = {}) {
  const r = rng(seed); const g = o.g ?? 260;
  for (let i = 0; i < n; i++) {
    const x0 = r() * W, vy = 120 + r() * 220, ph = r() * 10, sz = 8 + r() * 14, c = colors[i % colors.length], t0 = r() * (o.spread ?? 3);
    const tt = t - t0; if (tt < 0) continue;
    const y = -40 + vy * tt + 0.5 * g * 0.2 * tt * tt;
    if (y > H + 40) continue;
    const x = x0 + Math.sin(tt * 2 + ph) * 60;
    ctx.save(); ctx.translate(x, y); ctx.rotate(tt * 4 + ph); ctx.scale(1, Math.sin(tt * 6 + ph));
    ctx.fillStyle = c; ctx.fillRect(-sz / 2, -sz / 4, sz, sz / 2); ctx.restore();
  }
}

export function sparkle(ctx, x, y, r, color = '#FFFFFF', rot = 0) {
  ctx.save(); ctx.translate(x, y); ctx.rotate(rot); ctx.fillStyle = color; ctx.beginPath();
  for (let i = 0; i < 4; i++) { const a = i * Math.PI / 2; ctx.lineTo(Math.cos(a) * r, Math.sin(a) * r); ctx.lineTo(Math.cos(a + Math.PI / 4) * r * 0.28, Math.sin(a + Math.PI / 4) * r * 0.28); }
  ctx.closePath(); ctx.fill(); ctx.restore();
}

// Speech-bubble / panel
export function panel(ctx, x, y, w, h, o = {}) {
  ctx.save();
  ctx.fillStyle = o.shadow ?? 'rgba(20,20,19,.9)'; rr(ctx, x + 10, y + 10, w, h, o.r ?? 22); ctx.fill();
  ctx.fillStyle = o.fill ?? C.paper; rr(ctx, x, y, w, h, o.r ?? 22); ctx.fill();
  ctx.lineWidth = o.lw ?? 5; ctx.strokeStyle = o.stroke ?? C.ink; rr(ctx, x, y, w, h, o.r ?? 22); ctx.stroke();
  ctx.restore();
}

export function shake(t, amt, seed = 1) {
  return [Math.sin(t * 91 + seed) * amt, Math.cos(t * 77 + seed * 3) * amt];
}

const _scan = {};
export function scanlines(ctx, alpha = 0.18, gap = 4) {
  const k = alpha + ':' + gap;
  if (!_scan[k]) {
    const c = createCanvas(W, H), x = c.getContext('2d');
    x.fillStyle = `rgba(0,0,0,${alpha})`;
    for (let y = 0; y < H; y += gap) x.fillRect(0, y, W, gap / 2);
    _scan[k] = c;
  }
  ctx.drawImage(_scan[k], 0, 0);
}

// Character draw helper bound to a scene: auto talk + entrance pop.
export function actor(ctx, CH, S, t) {
  return (id, o = {}) => {
    const enter = o.enter != null ? pop(t, o.enter, o.enterDur ?? 0.4) : 1;
    const exit = o.exit != null ? 1 - ease.in(prog(t, o.exit, 0.3)) : 1;
    const k = enter * exit;
    if (k <= 0.001) return;
    CH.drawCharacter(ctx, id, { t: t + (o.phase ?? 0), talk: S.talk(id, t), ...o, s: (o.s ?? 1) * k });
  };
}

// Big jagged "shout" bubble.
export function burst(ctx, x, y, w, h, color, textStr, o = {}) {
  ctx.save(); ctx.translate(x, y); ctx.rotate(o.rot ?? -0.05);
  const n = 22, r = rng(o.seed ?? 7);
  const pts = [];
  for (let i = 0; i < n; i++) { const a = (i / n) * Math.PI * 2, k = i % 2 ? 1 : 0.78 + r() * 0.1; pts.push([Math.cos(a) * w / 2 * k, Math.sin(a) * h / 2 * k]); }
  const path = () => { ctx.beginPath(); pts.forEach(([px, py], i) => i ? ctx.lineTo(px, py) : ctx.moveTo(px, py)); ctx.closePath(); };
  ctx.translate(10, 12); path(); ctx.fillStyle = C.ink; ctx.fill(); ctx.translate(-10, -12);
  path(); ctx.fillStyle = color; ctx.fill(); ctx.lineWidth = 7; ctx.strokeStyle = C.ink; ctx.stroke();
  txt(ctx, textStr, 0, 4, { fam: o.fam || 'Anton', size: o.size || h * 0.32, color: o.color || C.cream, align: 'center', base: 'middle', stroke: C.ink, sw: 10, maxW: w * 0.7, track: 2 });
  ctx.restore();
}
