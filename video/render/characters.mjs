// characters.mjs : procedural cast for the Arch Linux propaganda film.
// Pure Canvas 2D drawing (works with @napi-rs/canvas or a browser ctx). No imports.
// Coordinate convention inside each character: origin = bottom-center, y up is negative,
// ~420 units tall at s=1 (small ones ~250). Outline ink is LW=6 units, scaled by s.

export const CHARACTER_IDS = ['claude', 'announcer', 'gamer', 'femboy', 'wiki', 'goblin', 'gentoo', 'lfs', 'nix', 'winupdate', 'tux', 'haiku', 'sonnet', 'fable'];

export const CHAR_INFO = {
  claude: { name: 'Claude Opus 5.5', color: '#D97757' },
  announcer: { name: 'The Ministry', color: '#1793D1' },
  gamer: { name: 'xX_PacmanSlayer_Xx', color: '#39FF14' },
  femboy: { name: 'socksd', color: '#FF8FC7' },
  wiki: { name: 'Wiki Enjoyer', color: '#B39DFF' },
  goblin: { name: 'Wiki Goblin', color: '#9ED48A' },
  gentoo: { name: 'Gentoo Wizard', color: '#8A63D2' },
  lfs: { name: 'LFS Ghost', color: '#F5C518' },
  nix: { name: 'NixOS Enjoyer', color: '#7EBAE4' },
  winupdate: { name: 'Windows Update', color: '#2F7FE0' },
  tux: { name: 'Tux', color: '#F5A623' },
  haiku: { name: 'Haiku 4.5', color: '#F4B99A' },
  sonnet: { name: 'Sonnet 5', color: '#B8532F' },
  fable: { name: 'Fable 5.1', color: '#B38B63' },
};

// ------------------------------------------------------------------ constants
const INK = '#141413';
const LW = 6;
const TAU = Math.PI * 2;
const WHITE = '#FFFFFF';
const MOUTH_IN = '#5E1F22';
const TONGUE = '#EE7784';
const ORANGE = '#D97757', ORANGE_D = '#C15F3C', CREAM = '#F0EEE6', ARCH = '#1793D1';
const PINK = '#FF8FC7', PINK2 = '#F5A9C8', LAV = '#B39DFF', NEON = '#39FF14', TEAL = '#2EC4B6';

let FLIP = false; // true while drawing a mirrored character (text is un-mirrored)

const clamp = (v, a, b) => (v < a ? a : v > b ? b : v);
function hashStr(s) {
  let h = 2166136261;
  for (let i = 0; i < s.length; i++) { h ^= s.charCodeAt(i); h = Math.imul(h, 16777619); }
  return h >>> 0;
}
const SEEDS = {};
for (const id of CHARACTER_IDS) SEEDS[id] = hashStr(id);

// ------------------------------------------------------------------ path helpers
function circ(ctx, x, y, r) { ctx.moveTo(x + r, y); ctx.arc(x, y, r, 0, TAU); }
function ell(ctx, x, y, rx, ry, rot = 0) {
  ctx.moveTo(x + rx * Math.cos(rot), y + rx * Math.sin(rot));
  ctx.ellipse(x, y, rx, ry, rot, 0, TAU);
}
function rrect(ctx, x, y, w, h, r) {
  r = Math.max(0, Math.min(r, w / 2, h / 2));
  ctx.moveTo(x + r, y);
  ctx.arcTo(x + w, y, x + w, y + h, r);
  ctx.arcTo(x + w, y + h, x, y + h, r);
  ctx.arcTo(x, y + h, x, y, r);
  ctx.arcTo(x, y, x + w, y, r);
  ctx.closePath();
}
function poly(ctx, pts, close = true) {
  ctx.moveTo(pts[0][0], pts[0][1]);
  for (let i = 1; i < pts.length; i++) ctx.lineTo(pts[i][0], pts[i][1]);
  if (close) ctx.closePath();
}
// closed smooth curve through midpoints; a point [x,y,1] is a sharp corner
function smooth(ctx, pts, ox = 0, oy = 0) {
  const n = pts.length;
  const mx = (a, b) => (a[0] + b[0]) / 2 + ox, my = (a, b) => (a[1] + b[1]) / 2 + oy;
  ctx.moveTo(mx(pts[n - 1], pts[0]), my(pts[n - 1], pts[0]));
  for (let i = 0; i < n; i++) {
    const p = pts[i], q = pts[(i + 1) % n];
    if (p[2]) { ctx.lineTo(p[0] + ox, p[1] + oy); ctx.lineTo(mx(p, q), my(p, q)); }
    else ctx.quadraticCurveTo(p[0] + ox, p[1] + oy, mx(p, q), my(p, q));
  }
  ctx.closePath();
}
function starPath(ctx, x, y, R, r, n, rot = -Math.PI / 2) {
  for (let i = 0; i < n * 2; i++) {
    const a = rot + (i * Math.PI) / n, rad = i % 2 ? r : R;
    const px = x + Math.cos(a) * rad, py = y + Math.sin(a) * rad;
    if (i === 0) ctx.moveTo(px, py); else ctx.lineTo(px, py);
  }
  ctx.closePath();
}
function twinklePath(ctx, x, y, R) { // 4-point concave sparkle
  ctx.moveTo(x, y - R);
  ctx.quadraticCurveTo(x, y, x + R, y);
  ctx.quadraticCurveTo(x, y, x, y + R);
  ctx.quadraticCurveTo(x, y, x - R, y);
  ctx.quadraticCurveTo(x, y, x, y - R);
  ctx.closePath();
}

// ------------------------------------------------------------------ paint helpers
// fill with a flat shadow crescent on the lower-right (light from top-left), then ink outline
function shape(ctx, build, fill, shadow, sdx = 0, sdy = 0, lw = LW) {
  ctx.beginPath(); build();
  if (shadow && (sdx || sdy)) {
    ctx.fillStyle = shadow; ctx.fill();
    ctx.save(); ctx.clip();
    ctx.translate(FLIP ? sdx : -sdx, -sdy);
    ctx.beginPath(); build(); ctx.fillStyle = fill; ctx.fill();
    ctx.restore();
  } else { ctx.fillStyle = fill; ctx.fill(); }
  if (lw) { ctx.beginPath(); build(); ctx.strokeStyle = INK; ctx.lineWidth = lw; ctx.stroke(); }
}
// union of several subpaths with an outer outline only
function unionShape(ctx, build, fill, shadow, sdx = 0, sdy = 0, lw = LW) {
  ctx.beginPath(); build();
  if (lw) { ctx.strokeStyle = INK; ctx.lineWidth = lw * 2; ctx.stroke(); }
  if (shadow && (sdx || sdy)) {
    ctx.fillStyle = shadow; ctx.fill();
    ctx.save(); ctx.clip();
    ctx.translate(FLIP ? sdx : -sdx, -sdy);
    ctx.beginPath(); build(); ctx.fillStyle = fill; ctx.fill();
    ctx.restore();
  } else { ctx.fillStyle = fill; ctx.fill(); }
}
function fillP(ctx, build, color) { ctx.beginPath(); build(); ctx.fillStyle = color; ctx.fill(); }
function strokeP(ctx, build, color = INK, w = LW) { ctx.beginPath(); build(); ctx.strokeStyle = color; ctx.lineWidth = w; ctx.stroke(); }
// outlined rounded stroke (arms, legs, straps)
function limb(ctx, pts, w, color, lw = LW) {
  ctx.beginPath(); poly(ctx, pts, false);
  ctx.strokeStyle = INK; ctx.lineWidth = w + lw * 2; ctx.stroke();
  ctx.strokeStyle = color; ctx.lineWidth = w; ctx.stroke();
}
function limbQ(ctx, x0, y0, cx, cy, x1, y1, w, color, lw = LW) {
  ctx.beginPath(); ctx.moveTo(x0, y0); ctx.quadraticCurveTo(cx, cy, x1, y1);
  ctx.strokeStyle = INK; ctx.lineWidth = w + lw * 2; ctx.stroke();
  ctx.strokeStyle = color; ctx.lineWidth = w; ctx.stroke();
}
function glow(ctx, x, y, r0, r1, color, a0) {
  const g = ctx.createRadialGradient(x, y, r0, x, y, r1);
  g.addColorStop(0, `rgba(${color},${a0})`);
  g.addColorStop(0.45, `rgba(${color},${a0 * 0.42})`);
  g.addColorStop(1, `rgba(${color},0)`);
  ctx.fillStyle = g; ctx.beginPath(); circ(ctx, x, y, r1); ctx.fill();
}
function groundShadow(ctx, rx, k = 1) {
  ctx.fillStyle = `rgba(20,20,19,${0.16 * k})`;
  ctx.beginPath(); ell(ctx, 0, -3, rx, rx * 0.13); ctx.fill();
}
function text(ctx, str, x, y, size, family, color, maxW = 0, align = 'center') {
  ctx.save();
  ctx.translate(x, y);
  if (FLIP) ctx.scale(-1, 1);
  ctx.font = `${size}px "${family}"`;
  ctx.textAlign = align; ctx.textBaseline = 'middle';
  if (maxW) { const m = ctx.measureText(str).width; if (m > maxW) ctx.scale(maxW / m, maxW / m); }
  ctx.fillStyle = color; ctx.fillText(str, 0, 0);
  ctx.restore();
}

// ------------------------------------------------------------------ animation helpers
function blinkAt(t, seed) {
  const p = 3 + (seed % 1000) / 500;           // 3..5 s
  const ph = (((seed >>> 10) % 1000) / 1000) * p;
  const tt = t + ph;
  const k = Math.floor(tt / p);
  const u = tt - k * p;
  const d = 0.16;
  if (u < d) return Math.sin((u / d) * Math.PI);
  if (((k * 7 + (seed & 15)) % 5) === 0 && u > d + 0.07 && u < 2 * d + 0.07) return Math.sin(((u - d - 0.07) / d) * Math.PI);
  return 0;
}
function breathe(ctx, t, seed, amt = 0.012, period = 3.2) {
  const b = Math.sin((t * TAU) / period + (seed % 628) / 100);
  ctx.scale(1 - amt * 0.6 * b, 1 + amt * b);
}
const bobOf = (t, seed, amp = 2, period = 2.6) => Math.sin((t * TAU) / period + (seed % 314) / 50) * amp;

// ------------------------------------------------------------------ face parts
function eye(ctx, cx, cy, rx, ry, side, E) {
  const lw = E.lw ?? 5;
  const mood = E.eyeMood;
  let lidT = E.lidT || 0, slope = 0, low = 0, star = false, tiny = false;
  switch (mood) {
    case 'smug': lidT = Math.max(lidT, 0.5); slope = -0.1; break;
    case 'angry': lidT = Math.max(lidT, 0.3); slope = 0.55; break;
    case 'sad': lidT = Math.max(lidT, 0.22); slope = -0.45; break;
    case 'happy': low = 0.42; break;
    case 'excited': star = true; lidT = 0; break;
    case 'shock': tiny = true; rx *= 1.06; ry *= 1.1; lidT = 0; break;
  }
  const close = Math.max(lidT, E.blink || 0);
  ctx.lineCap = 'round'; ctx.lineJoin = 'round';
  if (E.closed || close > 0.88) {
    const up = E.closed === 'up';
    ctx.beginPath();
    ctx.moveTo(cx - rx, cy + ry * 0.12);
    ctx.quadraticCurveTo(cx, cy + ry * (up ? -0.75 : 0.6), cx + rx, cy + ry * 0.12);
    ctx.strokeStyle = INK; ctx.lineWidth = lw * 1.15; ctx.stroke();
    if (E.lashes) {
      ctx.lineWidth = lw * 0.8;
      ctx.beginPath(); ctx.moveTo(cx + side * rx * 0.9, cy + ry * 0.2); ctx.lineTo(cx + side * (rx + 9), cy - 2); ctx.stroke();
    }
    return;
  }
  ctx.beginPath(); ell(ctx, cx, cy, rx, ry); ctx.fillStyle = E.sclera || WHITE; ctx.fill();
  ctx.save(); ctx.clip();
  const ix = cx + E.look * rx * 0.34, iy = cy + ry * 0.08;
  const ir = Math.min(rx, ry) * (E.irisR ?? 0.74);
  if (star) {
    ctx.beginPath(); starPath(ctx, ix, iy, ir * 1.3, ir * 0.56, 5);
    ctx.fillStyle = E.starColor || '#FFC93C'; ctx.fill();
    ctx.strokeStyle = INK; ctx.lineWidth = lw * 0.55; ctx.stroke();
    ctx.fillStyle = WHITE; ctx.beginPath(); circ(ctx, ix - ir * 0.22, iy - ir * 0.28, ir * 0.24); ctx.fill();
  } else if (tiny) {
    ctx.fillStyle = INK; ctx.beginPath(); circ(ctx, ix, cy, ir * 0.36); ctx.fill();
    ctx.fillStyle = WHITE; ctx.beginPath(); circ(ctx, ix - ir * 0.12, cy - ir * 0.14, ir * 0.1); ctx.fill();
  } else {
    ctx.fillStyle = E.iris || '#3A2A20'; ctx.beginPath(); circ(ctx, ix, iy, ir); ctx.fill();
    ctx.fillStyle = INK; ctx.beginPath(); circ(ctx, ix, iy + ir * 0.06, ir * 0.56); ctx.fill();
    ctx.fillStyle = WHITE; ctx.beginPath(); circ(ctx, ix - ir * 0.34, iy - ir * 0.36, ir * 0.36); ctx.fill();
    ctx.beginPath(); circ(ctx, ix + ir * 0.36, iy + ir * 0.36, ir * 0.15); ctx.fill();
  }
  if (close > 0.01 || slope) {
    const base = cy - ry + 2 * ry * close;
    const yIn = base + slope * ry * 0.55, yOut = base - slope * ry * 0.55;
    const yL = side < 0 ? yOut : yIn, yR = side < 0 ? yIn : yOut;
    const X0 = cx - rx - 3, X1 = cx + rx + 3;
    const bulge = ry * 0.22 * (1 - close);
    ctx.beginPath(); ctx.moveTo(X0, cy - ry - 3); ctx.lineTo(X1, cy - ry - 3); ctx.lineTo(X1, yR);
    ctx.quadraticCurveTo(cx, (yL + yR) / 2 + bulge, X0, yL); ctx.closePath();
    ctx.fillStyle = E.lid; ctx.fill();
    ctx.beginPath(); ctx.moveTo(X1, yR); ctx.quadraticCurveTo(cx, (yL + yR) / 2 + bulge, X0, yL);
    ctx.strokeStyle = INK; ctx.lineWidth = lw; ctx.stroke();
  }
  ctx.restore();
  ctx.beginPath(); ell(ctx, cx, cy, rx, ry); ctx.strokeStyle = INK; ctx.lineWidth = lw; ctx.stroke();
  if (E.lashes) {
    ctx.beginPath(); ctx.ellipse(cx, cy, rx, ry, 0, Math.PI * 1.08, Math.PI * 1.92); ctx.lineWidth = lw * 1.7; ctx.stroke();
    ctx.lineWidth = lw * 0.85;
    const ox = cx + side * rx * 0.86, oy = cy - ry * 0.52;
    ctx.beginPath(); ctx.moveTo(ox, oy); ctx.lineTo(ox + side * 11, oy - 9);
    ctx.moveTo(cx + side * rx * 0.98, cy - ry * 0.15); ctx.lineTo(cx + side * (rx + 11), cy - ry * 0.3); ctx.stroke();
  }
  if (low > 0) {
    const y0 = cy + ry * 0.6, yc = cy + ry * (0.6 - 2.3 * low);
    const X0 = cx - rx - 4, X1 = cx + rx + 4;
    ctx.beginPath(); ctx.moveTo(X0, y0); ctx.quadraticCurveTo(cx, yc, X1, y0); ctx.lineTo(X1, cy + ry + lw); ctx.lineTo(X0, cy + ry + lw); ctx.closePath();
    ctx.fillStyle = E.lid; ctx.fill();
    ctx.save(); ctx.beginPath(); ell(ctx, cx, cy, rx + lw * 0.5, ry + lw * 0.5); ctx.clip();
    ctx.beginPath(); ctx.moveTo(X0, y0); ctx.quadraticCurveTo(cx, yc, X1, y0); ctx.strokeStyle = INK; ctx.lineWidth = lw; ctx.stroke();
    ctx.restore();
  }
}

function brows(ctx, x, y, dx, w, mood, color, thick) {
  for (const side of [-1, 1]) {
    let rot = 0, lift = 0, arch = 0.16;
    switch (mood) {
      case 'angry': rot = 0.42; lift = 7; arch = 0.04; break;
      case 'grumpy': rot = 0.24; lift = 4; arch = 0.06; break;
      case 'sad': rot = -0.36; lift = -3; arch = 0.1; break;
      case 'shock': lift = -12; arch = 0.3; break;
      case 'happy': case 'excited': lift = -7; arch = 0.24; break;
      case 'smug': if (side > 0) { lift = -9; rot = -0.14; } else { lift = 3; rot = 0.1; } break;
    }
    ctx.save(); ctx.translate(x + side * dx, y + lift); ctx.rotate(-side * rot);
    ctx.beginPath(); ctx.moveTo(-w / 2, 0); ctx.quadraticCurveTo(0, -w * arch * 2, w / 2, 0);
    ctx.strokeStyle = color; ctx.lineWidth = thick; ctx.lineCap = 'round'; ctx.stroke();
    ctx.restore();
  }
}

function mouth(ctx, x, y, w, mood, talk, opt = {}) {
  const lw = opt.lw ?? LW * 0.8;
  let o = talk, curv = opt.neutral ?? 0.16, lY = 0, rY = 0, hw = w / 2, dx = 0;
  switch (mood) {
    case 'happy': curv = 0.3; break;
    case 'excited': curv = 0.34; o = Math.max(o, 0.42); break;
    case 'smug': curv = 0.08; lY = 0.06; rY = -0.2; dx = 0.12; hw *= 0.85; break;
    case 'angry': curv = -0.13; break;
    case 'grumpy': curv = -0.08; hw *= 0.8; break;
    case 'sad': curv = -0.2; hw *= 0.8; break;
  }
  ctx.save();
  ctx.translate(x + dx * w, y);
  ctx.lineWidth = lw; ctx.strokeStyle = INK; ctx.lineCap = 'round'; ctx.lineJoin = 'round';
  if (mood === 'shock') {
    const rx = w * (0.17 + 0.1 * talk), ry = w * (0.2 + 0.18 * talk);
    ctx.beginPath(); ell(ctx, 0, ry * 0.4, rx, ry); ctx.fillStyle = MOUTH_IN; ctx.fill();
    ctx.save(); ctx.clip(); ctx.fillStyle = TONGUE; ctx.beginPath(); ell(ctx, 0, ry * 1.25, rx * 0.8, ry * 0.55); ctx.fill(); ctx.restore();
    ctx.beginPath(); ell(ctx, 0, ry * 0.4, rx, ry); ctx.stroke();
    ctx.restore(); return;
  }
  const c = curv * w, avg = ((lY + rY) / 2) * w;
  if (o < 0.06) {
    ctx.beginPath();
    if (opt.cat && (mood === 'neutral' || mood === 'happy' || mood === 'smug')) {
      const k = hw * 0.62;
      ctx.moveTo(-k * 1.25, -k * 0.2);
      ctx.quadraticCurveTo(-k * 0.6, k * 0.95, 0, 0);
      ctx.quadraticCurveTo(k * 0.6, k * 0.95, k * 1.25, -k * 0.2);
      ctx.stroke();
      if (opt.fang) { // tiny fang
        ctx.beginPath(); ctx.moveTo(k * 0.25, k * 0.28); ctx.lineTo(k * 0.55, k * 0.95); ctx.lineTo(k * 0.8, k * 0.3); ctx.closePath();
        ctx.fillStyle = WHITE; ctx.fill(); ctx.lineWidth = lw * 0.6; ctx.stroke();
      }
    } else {
      ctx.moveTo(-hw, lY * w); ctx.quadraticCurveTo(0, avg + 2 * c, hw, rY * w); ctx.stroke();
    }
    ctx.restore(); return;
  }
  const H = o * w * (opt.openK || 0.66), hw2 = hw * (1 - 0.12 * o);
  const cT = c * (1 - o) * (1 - o) - (c < 0 ? H * 0.25 : 0), cB = Math.max(c, cT + 3) + H;
  const build = () => {
    ctx.moveTo(-hw2, lY * w);
    ctx.quadraticCurveTo(0, avg + 2 * cT, hw2, rY * w);
    ctx.bezierCurveTo(hw2 * 0.95, avg + cB * 1.33, -hw2 * 0.95, avg + cB * 1.33, -hw2, lY * w);
    ctx.closePath();
  };
  ctx.beginPath(); build(); ctx.fillStyle = MOUTH_IN; ctx.fill();
  ctx.save(); ctx.clip();
  ctx.fillStyle = TONGUE; ctx.beginPath(); ell(ctx, 0, avg + cB * 1.02, hw2 * 0.6, Math.max(4, H * 0.4)); ctx.fill();
  if (opt.teeth !== false && o > 0.25) {
    ctx.beginPath(); ctx.moveTo(-hw2, lY * w); ctx.quadraticCurveTo(0, avg + 2 * cT, hw2, rY * w);
    ctx.strokeStyle = WHITE; ctx.lineWidth = w * 0.2; ctx.stroke();
  }
  ctx.restore();
  ctx.beginPath(); build(); ctx.strokeStyle = INK; ctx.lineWidth = lw; ctx.stroke();
  if (opt.fang && o > 0.15) {
    ctx.beginPath(); ctx.moveTo(hw2 * 0.3, avg + cT * 1.1); ctx.lineTo(hw2 * 0.45, avg + cT * 1.1 + w * 0.16); ctx.lineTo(hw2 * 0.62, avg + cT * 1.0); ctx.closePath();
    ctx.fillStyle = WHITE; ctx.fill(); ctx.lineWidth = lw * 0.5; ctx.stroke();
  }
  ctx.restore();
}

function blush(ctx, x, y, dx, rx, ry, color = 'rgba(255,120,150,0.45)', hatch = false) {
  ctx.fillStyle = color;
  ctx.beginPath(); ell(ctx, x - dx, y, rx, ry); ell(ctx, x + dx, y, rx, ry); ctx.fill();
  if (hatch) {
    ctx.strokeStyle = 'rgba(230,80,120,0.75)'; ctx.lineWidth = 2.6; ctx.lineCap = 'round';
    ctx.beginPath();
    for (const sx of [-dx, dx]) for (let i = -1; i <= 1; i++) {
      const hx = x + sx + i * rx * 0.55;
      ctx.moveTo(hx + ry * 0.5, y - ry * 0.55); ctx.lineTo(hx - ry * 0.5, y + ry * 0.55);
    }
    ctx.stroke();
  }
}

// mood decorations near the head: (x,y) = head center, r = head radius
function moodFX(ctx, mood, x, y, r, t, eyeInfo) {
  if (mood === 'excited') {
    const pts = [[-1.12, -0.55, 0.16, 0], [1.1, -0.72, 0.2, 1.3], [1.22, 0.05, 0.12, 2.4], [-1.02, 0.25, 0.1, 3.1]];
    for (const [px, py, pr, ph] of pts) {
      const k = 0.6 + 0.4 * Math.abs(Math.sin(t * 4 + ph));
      ctx.beginPath(); twinklePath(ctx, x + px * r, y + py * r, pr * r * k);
      ctx.fillStyle = '#FFD84A'; ctx.fill(); ctx.strokeStyle = INK; ctx.lineWidth = 3; ctx.stroke();
    }
  } else if (mood === 'shock') {
    const k = r / 100, px = x + r * 0.92, py = y - r * 0.5 + Math.sin(t * 3) * 2;
    ctx.beginPath();
    ctx.moveTo(px, py - 24 * k);
    ctx.bezierCurveTo(px + 4 * k, py - 12 * k, px + 13 * k, py - 3 * k, px + 13 * k, py + 7 * k);
    ctx.arc(px, py + 7 * k, 13 * k, 0, Math.PI);
    ctx.bezierCurveTo(px - 13 * k, py - 3 * k, px - 4 * k, py - 12 * k, px, py - 24 * k);
    ctx.closePath();
    ctx.fillStyle = '#9ED8FF'; ctx.fill(); ctx.strokeStyle = INK; ctx.lineWidth = 3.5 * k; ctx.stroke();
    ctx.fillStyle = WHITE; ctx.beginPath(); ell(ctx, px - 5 * k, py + 5 * k, 3 * k, 5 * k); ctx.fill();
  } else if (mood === 'angry') {
    const k = r / 100, px = x + r * 0.88, py = y - r * 0.82;
    const p = 1 + 0.12 * Math.sin(t * 9);
    ctx.strokeStyle = '#E8413C'; ctx.lineWidth = 5 * k; ctx.lineCap = 'round';
    ctx.beginPath();
    for (let q = 0; q < 4; q++) {
      const a = q * Math.PI / 2 + Math.PI / 4;
      const qx = px + Math.cos(a) * 12 * k * p, qy = py + Math.sin(a) * 12 * k * p;
      ctx.moveTo(qx + Math.cos(a + Math.PI - 0.9) * 9 * k, qy + Math.sin(a + Math.PI - 0.9) * 9 * k);
      ctx.arc(qx, qy, 9 * k, a + Math.PI - 0.9, a + Math.PI + 0.9);
    }
    ctx.stroke();
  } else if (mood === 'sad' && eyeInfo) {
    const [ex, ey, er] = eyeInfo;
    const drop = (((t * 0.7) % 1) + 1) % 1;
    const py = ey + er * (1.1 + drop * 1.2), px = ex;
    const k = er / 22;
    ctx.save(); ctx.globalAlpha *= 1 - drop * 0.6;
    ctx.beginPath(); ctx.moveTo(px, py - 12 * k); ctx.quadraticCurveTo(px + 8 * k, py + 2 * k, px, py + 8 * k); ctx.quadraticCurveTo(px - 8 * k, py + 2 * k, px, py - 12 * k);
    ctx.fillStyle = '#8FD0FF'; ctx.fill(); ctx.strokeStyle = INK; ctx.lineWidth = 2.5 * k; ctx.stroke();
    ctx.restore();
  }
}

// full face: F = { x, y, dx, rx, ry, lid, iris, mood, look, blink, talk, mouthY, mouthW, browY, browW, browC, browT, blushY, blushDx, ... }
function face(ctx, F) {
  const mood = F.mood;
  const E = {
    lw: F.eyeLw ?? 5, eyeMood: F.eyeMood ?? mood, lidT: F.lidT, blink: F.blink, look: F.look, iris: F.iris, lid: F.lid,
    irisR: F.irisR, lashes: F.lashes, closed: F.closed, starColor: F.starColor, sclera: F.sclera,
  };
  eye(ctx, F.x - F.dx, F.y, F.rx, F.ry, -1, E);
  eye(ctx, F.x + F.dx, F.y, F.rx, F.ry, 1, E);
  if (F.blushDx) blush(ctx, F.x, F.blushY, F.blushDx, F.blushRx || 16, F.blushRy || 9, F.blushC, F.hatch);
  if (F.browW) brows(ctx, F.x, F.browY, F.dx, F.browW, F.browMood ?? mood, F.browC || INK, F.browT || 6);
  if (!F.noMouth) mouth(ctx, F.x, F.mouthY, F.mouthW, F.mouthMood ?? mood, F.talk, F.mouthOpt || {});
}

// ------------------------------------------------------------------ spark family (claude, haiku, sonnet, fable)
function makeRays(n, lens, jit, r0, w0, w1) {
  const out = [];
  for (let i = 0; i < n; i++) out.push({ a: (i / n) * TAU + (jit[i % jit.length] || 0), len: lens[i % lens.length], r0, w0, w1 });
  return out;
}
function tRay(ctx, cx, cy, a, r0, r1, w0, w1) {
  const d = Math.max(1, r1 - r0);
  const ca = Math.acos(clamp((w1 - w0) / d, -1, 1));
  const c = Math.cos(a), s = Math.sin(a);
  const ax = cx + c * r0, ay = cy + s * r0, bx = cx + c * r1, by = cy + s * r1;
  ctx.moveTo(bx + Math.cos(a - ca) * w1, by + Math.sin(a - ca) * w1);
  ctx.arc(bx, by, w1, a - ca, a + ca);
  ctx.arc(ax, ay, w0, a + ca, a + TAU - ca);
  ctx.closePath();
}
function sparkBuild(ctx, cx, cy, R, rays, core, rot, t, br, sp) {
  ctx.moveTo(cx + R * core, cy); ctx.arc(cx, cy, R * core, 0, TAU);
  for (let i = 0; i < rays.length; i++) {
    const r = rays[i];
    const L = R * r.len * (1 + br * Math.sin(t * sp + i * 1.7));
    tRay(ctx, cx, cy, rot + r.a, R * r.r0, L - R * r.w1, R * r.w0, R * r.w1);
  }
}
const SPARKS = {
  claude: { color: ORANGE, shadow: ORANGE_D, hand: CREAM, handS: '#D8D2C2', glow: '255,168,120', core: 0.56, speed: 1, br: 0.03,
    rays: makeRays(10, [1, 0.84, 0.95, 0.8, 0.98, 0.87, 0.82, 0.97, 0.8, 0.9], [0, 0.04, -0.03, 0.03, -0.04, 0.03, -0.02, 0.04, -0.03, 0.02], 0.3, 0.22, 0.08) },
  haiku: { color: '#F6C2A2', shadow: '#E4A07E', hand: WHITE, handS: '#E8DDD4', glow: '255,205,170', eyeK: 1.18, core: 0.6, speed: 1.9, br: 0.05,
    rays: makeRays(8, [0.98, 0.86, 1, 0.84, 0.95, 0.88, 0.99, 0.85], [0, 0.06, -0.05, 0.04, -0.03, 0.05, -0.06, 0.02], 0.3, 0.26, 0.11) },
  sonnet: { color: '#B8532F', shadow: '#8F3A1D', hand: CREAM, handS: '#D8D2C2', glow: '235,120,80', eyeK: 1.12, core: 0.56, speed: 0.8, br: 0.03,
    rays: makeRays(12, [1, 0.86, 0.96, 0.83, 0.99, 0.87, 0.94, 0.84, 0.98, 0.86, 0.95, 0.84], [0, 0.03, -0.03, 0.02, -0.02, 0.03, -0.03, 0.02, 0, 0.03, -0.02, 0.02], 0.3, 0.18, 0.058) },
  fable: { color: '#B38B63', shadow: '#8C6845', hand: CREAM, handS: '#D8D2C2', glow: '240,200,150', eyeK: 1.1, core: 0.58, speed: 0.9, br: 0.035,
    rays: makeRays(10, [0.97, 0.86, 0.95, 0.84, 0.99, 0.88, 0.93, 0.85, 0.97, 0.87], [0.03, -0.04, 0.02, 0.05, -0.03, 0.02, -0.04, 0.03, -0.02, 0.04], 0.3, 0.23, 0.1) },
};

function sparkBody(ctx, cx, cy, R, P, t) {
  const rot = Math.sin(t * 0.45 * P.speed) * 0.1 + t * 0.07 * P.speed;
  const build = () => sparkBuild(ctx, cx, cy, R, P.rays, P.core, rot, t, P.br, 1.7 * P.speed);
  ctx.beginPath(); build();
  ctx.strokeStyle = INK; ctx.lineWidth = LW * 2; ctx.stroke();
  ctx.fillStyle = P.color; ctx.fill();
  // one smooth shadow tone: everything outside a light circle offset to the top-left
  ctx.save(); ctx.clip();
  const ox = FLIP ? R * 0.16 : -R * 0.16;
  ctx.beginPath(); ctx.rect(cx - R * 1.5, cy - R * 1.5, R * 3, R * 3); circ(ctx, cx + ox, cy - R * 0.16, R * 1.02);
  ctx.fillStyle = P.shadow; ctx.fill('evenodd');
  // core rim shade + top-left sheen
  ctx.beginPath(); ctx.rect(cx - R * 1.5, cy - R * 1.5, R * 3, R * 3); circ(ctx, cx + ox * 0.5, cy - R * 0.07, R * P.core * 1.02);
  ctx.restore();
  ctx.fillStyle = 'rgba(255,255,255,0.16)';
  ctx.beginPath(); ell(ctx, cx - R * 0.2 * (FLIP ? -1 : 1), cy - R * 0.3, R * 0.2, R * 0.1, FLIP ? 0.55 : -0.55); ctx.fill();
}

function nub(ctx, x, y, r, color, shadow) {
  shape(ctx, () => circ(ctx, x, y, r), color, shadow, r * 0.25, r * 0.25, LW * 0.9);
}

function sparkFace(ctx, cx, cy, R, P, st, extra = {}) {
  const mood = st.mood, ek = P.eyeK || 1;
  const showBrows = mood !== 'neutral' && mood !== 'happy';
  face(ctx, {
    x: cx, y: cy - R * 0.05, dx: R * 0.215 * (1 + (ek - 1) * 0.5), rx: R * 0.12 * ek, ry: R * 0.155 * ek, lid: P.color, iris: extra.iris || '#2A1712', mood,
    look: st.look, blink: st.blink, talk: st.talk, mouthY: cy + R * 0.19, mouthW: R * 0.23, eyeLw: Math.max(3.5, R * 0.028),
    browW: showBrows ? R * 0.14 : 0, browY: cy - R * 0.28, browC: extra.browC || '#5A2414', browT: R * 0.038,
    blushDx: R * 0.37, blushY: cy + R * 0.12, blushRx: R * 0.08, blushRy: R * 0.048, blushC: 'rgba(255,140,150,0.6)',
    mouthOpt: { lw: Math.max(3.5, R * 0.027) }, closed: extra.closed,
  });
  moodFX(ctx, mood, cx, cy, R * 0.75, st.t, [cx - R * 0.215, cy - R * 0.05, R * 0.155]);
}

function waterGlass(ctx, x, y, h, t) {
  const wT = h * 0.64, wB = h * 0.5;
  const build = () => { ctx.moveTo(x - wT / 2, y - h); ctx.lineTo(x + wT / 2, y - h); ctx.lineTo(x + wB / 2, y); ctx.lineTo(x - wB / 2, y); ctx.closePath(); };
  fillP(ctx, build, 'rgba(215,238,255,0.6)');
  ctx.save(); ctx.beginPath(); build(); ctx.clip();
  const lvl = y - h * 0.6, sl = Math.sin(t * 3.1) * h * 0.035;
  ctx.beginPath(); ctx.moveTo(x - wT, lvl + sl); ctx.quadraticCurveTo(x, lvl - sl * 1.5, x + wT, lvl - sl); ctx.lineTo(x + wT, y + 3); ctx.lineTo(x - wT, y + 3); ctx.closePath();
  ctx.fillStyle = 'rgba(95,175,240,0.72)'; ctx.fill();
  ctx.fillStyle = 'rgba(255,255,255,0.8)'; ctx.fillRect(x - wT * 0.34, y - h * 0.88, h * 0.07, h * 0.7);
  ctx.restore();
  strokeP(ctx, build, INK, LW * 0.75);
  ctx.strokeStyle = 'rgba(255,255,255,0.9)'; ctx.lineWidth = 2; ctx.beginPath(); ctx.moveTo(x - wT * 0.42, y - h + 5); ctx.lineTo(x + wT * 0.42, y - h + 5); ctx.stroke();
}

function laptopFront(ctx, x, y, w, t) { // y = bottom of base; screen faces viewer
  const h = w * 0.64, bh = w * 0.075;
  const lx = x - w / 2, ly = y - bh - h;
  shape(ctx, () => rrect(ctx, lx, ly, w, h, w * 0.05), '#3B3E47', null, 0, 0, LW * 0.8);
  const sx = lx + w * 0.055, sy = ly + w * 0.055, sw = w * 0.89, sh = h - w * 0.1;
  ctx.fillStyle = '#0E1A25'; ctx.beginPath(); rrect(ctx, sx, sy, sw, sh, w * 0.02); ctx.fill();
  const fs = sw * 0.068, lh = fs * 1.35;
  const lines = [['[claude@arch ~]$', ARCH], ['sudo pacman -Syu', '#E8F1F7'], [':: Synchronizing...', '#8FA3B3'], ['core    up to date', NEON], ['extra   up to date', NEON]];
  for (let i = 0; i < lines.length; i++) text(ctx, lines[i][0], sx + sw * 0.06, sy + lh * (i + 0.9), fs, 'JBM-800', lines[i][1], sw * 0.9, FLIP ? 'right' : 'left');
  if (Math.floor(t * 2) % 2 === 0) { ctx.fillStyle = '#E8F1F7'; ctx.fillRect(sx + sw * 0.06, sy + lh * 5.45, fs * 0.6, fs); }
  drawArchPeak(ctx, sx + sw * 0.86, sy + sh * 0.93, sh * 0.22, ARCH);
  // base / keyboard deck
  shape(ctx, () => { ctx.moveTo(x - w * 0.56, y); ctx.lineTo(x + w * 0.56, y); ctx.lineTo(x + w * 0.5, y - bh); ctx.lineTo(x - w * 0.5, y - bh); ctx.closePath(); }, '#CDD1D8', '#A3A9B3', 0, bh * 0.35, LW * 0.8);
}

function drawSparkChar(ctx, st, key, R, hover, accessory) {
  const P = SPARKS[key];
  const { t } = st;
  const bob = bobOf(t, st.seed, R * 0.018, 2.8 / P.speed);
  const cy = -(hover + R) + bob;
  groundShadow(ctx, R * 0.55 * (1 - bob / (R * 0.4)), 0.9);
  glow(ctx, 0, cy, R * 0.5, R * 1.3, P.glow, 0.5);
  const hs = R * 0.11;
  const hk = R < 150 ? 0.78 : 0.84;
  const handY = (side) => cy + R * 0.3 + Math.sin(t * 2.2 * P.speed + side * 1.3) * R * 0.025 - st.talk * R * 0.035;
  let hands = [[-R * hk, handY(-1) + R * 0.1], [R * hk, handY(1) + R * 0.1]];
  const pre = accessory && accessory.before;
  if (pre) pre(ctx, cy, hands);
  sparkBody(ctx, 0, cy, R, P, t);
  if (accessory && accessory.hands) hands = accessory.hands(cy, hands) || hands;
  if (accessory && accessory.under) accessory.under(ctx, cy, hands);
  sparkFace(ctx, 0, cy, R, P, st, accessory && accessory.face || {});
  if (accessory && accessory.over) accessory.over(ctx, cy, hands);
  for (const [hx, hy] of hands) nub(ctx, hx, hy, hs, P.hand || P.color, P.handS || P.shadow);
  if (accessory && accessory.top) accessory.top(ctx, cy, hands);
}

function drawClaude(ctx, st) {
  const R = 180, prop = st.prop, t = st.t;
  drawSparkChar(ctx, st, 'claude', R, 36, {
    hands(cy, h) {
      if (prop === 'water') return [[-R * 0.95, h[0][1]], [R * 0.78, cy + R * 0.42]];
      if (prop === 'laptop') return [[-R * 0.5, cy + R * 1.0], [R * 0.5, cy + R * 1.0]];
      return h;
    },
    under(ctx, cy) {
      // "5.5" badge pinned lower right
      const bx = R * 0.3, by = cy + R * 0.42, br = R * 0.115;
      shape(ctx, () => circ(ctx, bx, by, br), ARCH, '#0F6FA3', br * 0.18, br * 0.18, LW * 0.75);
      ctx.strokeStyle = 'rgba(255,255,255,0.85)'; ctx.lineWidth = 2; ctx.beginPath(); circ(ctx, bx, by, br * 0.78); ctx.stroke();
      text(ctx, '5.5', bx, by + 1, br * 0.92, 'Nunito-900', WHITE, br * 1.4);
    },
    over(ctx, cy, hands) {
      if (prop === 'water') waterGlass(ctx, hands[1][0] + R * 0.02, hands[1][1] + R * 0.08, R * 0.46, t);
      if (prop === 'laptop') laptopFront(ctx, 0, cy + R * 1.1, R * 1.08, t);
    },
  });
}

function drawHaiku(ctx, st) {
  const R = 100, t = st.t;
  drawSparkChar(ctx, st, 'haiku', R, 26, {
    hands(cy, h) { return [h[0], [R * 0.86, cy + R * 0.2 + Math.sin(t * 5) * R * 0.04]]; },
    over(ctx, cy, hands) {
      // calligraphy brush held diagonally, tip swishing
      const [hx, hy] = hands[1];
      const a = -0.55 + Math.sin(t * 3.4) * 0.18;
      ctx.save(); ctx.translate(hx, hy); ctx.rotate(a);
      const L = R * 0.95;
      shape(ctx, () => rrect(ctx, -R * 0.045, -L * 0.75, R * 0.09, L * 0.95, R * 0.04), '#D9B36C', '#B8914A', R * 0.02, 0, LW * 0.7);
      ctx.strokeStyle = '#8C6A34'; ctx.lineWidth = 2.5; ctx.beginPath();
      for (const k of [-0.5, -0.2, 0.05]) { ctx.moveTo(-R * 0.045, L * k); ctx.lineTo(R * 0.045, L * k); }
      ctx.stroke();
      shape(ctx, () => { ctx.moveTo(-R * 0.06, L * 0.2); ctx.quadraticCurveTo(-R * 0.08, L * 0.42, 0, L * 0.55); ctx.quadraticCurveTo(R * 0.08, L * 0.42, R * 0.06, L * 0.2); ctx.closePath(); }, '#1F1F1E', null, 0, 0, LW * 0.6);
      ctx.restore();
      // ink drops
      ctx.fillStyle = INK;
      for (let i = 0; i < 3; i++) { const u = (((t * 0.9 + i / 3) % 1) + 1) % 1; ctx.save(); ctx.globalAlpha *= 1 - u; ctx.beginPath(); circ(ctx, hx + R * 0.3 + i * 6, hy + R * (0.4 + u * 0.6), R * 0.025); ctx.fill(); ctx.restore(); }
    },
  });
}

function drawSonnet(ctx, st) {
  const R = 104, t = st.t;
  drawSparkChar(ctx, st, 'sonnet', R, 26, {
    hands(cy, h) { return [h[0], [R * 0.9, cy + R * 0.12 + Math.sin(t * 2) * R * 0.03]]; },
    under(ctx, cy) {
      // Elizabethan ruff: pleated ring below the face
      const rx = R * 0.7, ry = R * 0.16, y0 = cy + R * 0.62, n = 18;
      const build = () => {
        for (let i = 0; i < n; i++) {
          const a = (i / n) * TAU;
          circ(ctx, Math.cos(a) * rx, y0 + Math.sin(a) * ry, R * 0.1);
        }
        ell(ctx, 0, y0, rx, ry);
      };
      unionShape(ctx, build, '#FBF8F1', '#DCD5C6', 0, R * 0.04, LW * 0.8);
      ctx.strokeStyle = 'rgba(20,20,19,0.55)'; ctx.lineWidth = 2.2; ctx.beginPath();
      for (let i = 0; i < n; i++) {
        const a = (i / n) * TAU + Math.PI / n;
        ctx.moveTo(Math.cos(a) * rx * 0.45, y0 + Math.sin(a) * ry * 0.45);
        ctx.lineTo(Math.cos(a) * (rx + R * 0.07), y0 + Math.sin(a) * (ry + R * 0.07));
      }
      ctx.stroke();
      ctx.fillStyle = '#E9E2D2'; ctx.beginPath(); ell(ctx, 0, y0 - ry * 0.15, rx * 0.45, ry * 0.4); ctx.fill();
    },
    over(ctx, cy, hands) {
      const [hx, hy] = hands[1];
      const a = 0.35 + Math.sin(t * 2.6) * 0.12;
      ctx.save(); ctx.translate(hx, hy); ctx.rotate(a);
      const L = R * 1.1;
      // feather vane
      shape(ctx, () => { ctx.moveTo(0, R * 0.25); ctx.bezierCurveTo(-R * 0.22, -L * 0.2, -R * 0.12, -L * 0.7, R * 0.05, -L * 0.95); ctx.bezierCurveTo(R * 0.14, -L * 0.55, R * 0.2, -L * 0.1, 0, R * 0.25); ctx.closePath(); }, '#FFFFFF', '#E3DDD0', R * 0.04, 0, LW * 0.7);
      ctx.strokeStyle = 'rgba(20,20,19,0.5)'; ctx.lineWidth = 2; ctx.beginPath(); ctx.moveTo(0, R * 0.25); ctx.quadraticCurveTo(-R * 0.02, -L * 0.4, R * 0.05, -L * 0.93);
      for (let i = 1; i < 5; i++) { const yy = -L * 0.16 * i; ctx.moveTo(-R * 0.01, yy); ctx.lineTo(-R * 0.1, yy - R * 0.06); }
      ctx.stroke();
      // nib
      shape(ctx, () => { ctx.moveTo(-R * 0.03, R * 0.22); ctx.lineTo(R * 0.03, R * 0.22); ctx.lineTo(0, R * 0.42); ctx.closePath(); }, '#2A2A2A', null, 0, 0, LW * 0.5);
      ctx.restore();
    },
  });
}

function drawFable(ctx, st) {
  const R = 102, t = st.t;
  drawSparkChar(ctx, st, 'fable', R, 26, {
    hands(cy) { return [[-R * 0.62, cy + R * 0.78], [R * 0.62, cy + R * 0.78]]; },
    over(ctx, cy) {
      // spectacles
      const ey = cy - R * 0.04, dx = R * 0.19, gr = R * 0.155;
      ctx.strokeStyle = '#5A3A1E'; ctx.lineWidth = Math.max(3, R * 0.032);
      ctx.fillStyle = 'rgba(255,255,255,0.18)';
      ctx.beginPath(); circ(ctx, -dx, ey, gr); circ(ctx, dx, ey, gr); ctx.fill(); ctx.stroke();
      ctx.beginPath(); ctx.moveTo(-dx + gr, ey - gr * 0.2); ctx.quadraticCurveTo(0, ey - gr * 0.6, dx - gr, ey - gr * 0.2); ctx.stroke();
      ctx.strokeStyle = 'rgba(255,255,255,0.7)'; ctx.lineWidth = 2; ctx.beginPath();
      for (const s of [-1, 1]) { ctx.moveTo(s * dx - gr * 0.55, ey - gr * 0.2); ctx.lineTo(s * dx - gr * 0.2, ey - gr * 0.6); }
      ctx.stroke();
      // open storybook
      const by = cy + R * 0.86, bw = R * 0.62, bh = R * 0.42;
      const flap = Math.sin(t * 1.3) * 0.04;
      ctx.save(); ctx.translate(0, by); ctx.rotate(flap);
      shape(ctx, () => { ctx.moveTo(-bw - 6, bh * 0.1); ctx.quadraticCurveTo(-bw * 0.5, -bh * 0.05, 0, bh * 0.2); ctx.quadraticCurveTo(bw * 0.5, -bh * 0.05, bw + 6, bh * 0.1); ctx.lineTo(bw + 6, -bh * 0.85); ctx.quadraticCurveTo(bw * 0.5, -bh * 1.02, 0, -bh * 0.8); ctx.quadraticCurveTo(-bw * 0.5, -bh * 1.02, -bw - 6, -bh * 0.85); ctx.closePath(); }, '#8E2F2A', null, 0, 0, LW * 0.8);
      shape(ctx, () => { ctx.moveTo(-bw, 0); ctx.quadraticCurveTo(-bw * 0.5, -bh * 0.15, 0, bh * 0.08); ctx.quadraticCurveTo(bw * 0.5, -bh * 0.15, bw, 0); ctx.lineTo(bw, -bh * 0.92); ctx.quadraticCurveTo(bw * 0.5, -bh * 1.1, 0, -bh * 0.9); ctx.quadraticCurveTo(-bw * 0.5, -bh * 1.1, -bw, -bh * 0.92); ctx.closePath(); }, '#FBF3DF', '#E9DcBC', 0, bh * 0.08, LW * 0.7);
      ctx.strokeStyle = 'rgba(20,20,19,0.35)'; ctx.lineWidth = 2.2; ctx.beginPath();
      for (let i = 0; i < 4; i++) { const yy = -bh * (0.72 - i * 0.17); ctx.moveTo(-bw * 0.85, yy); ctx.lineTo(-bw * 0.15, yy + bh * 0.04); ctx.moveTo(bw * 0.15, yy + bh * 0.04); ctx.lineTo(bw * 0.85, yy); }
      ctx.stroke();
      strokeP(ctx, () => { ctx.moveTo(0, -bh * 0.88); ctx.lineTo(0, bh * 0.08); }, INK, 3);
      ctx.restore();
    },
  });
}

// ------------------------------------------------------------------ shared human bits
const HUMAN = { hy: -290, hrx: 106, hry: 98 };
function shoe(ctx, x, side, upper, upperS, sole) {
  const w = 62, h = 30, sx = x - w / 2 + side * 6;
  shape(ctx, () => { ctx.moveTo(sx + 8, 0); ctx.lineTo(sx + w - 4, 0); ctx.quadraticCurveTo(sx + w + 4, 0, sx + w, -12); ctx.quadraticCurveTo(sx + w - 8, -h, sx + w / 2, -h); ctx.quadraticCurveTo(sx, -h, sx, -10); ctx.quadraticCurveTo(sx, 0, sx + 8, 0); ctx.closePath(); }, upper, upperS, 6, 4, LW);
  if (sole) {
    ctx.fillStyle = sole; ctx.beginPath(); rrect(ctx, sx + 3, -11, w - 4, 8, 4); ctx.fill();
    strokeP(ctx, () => { ctx.moveTo(sx + 8, 0); ctx.lineTo(sx + w - 4, 0); ctx.quadraticCurveTo(sx + w + 4, 0, sx + w, -12); ctx.quadraticCurveTo(sx + w - 8, -h, sx + w / 2, -h); ctx.quadraticCurveTo(sx, -h, sx, -10); ctx.quadraticCurveTo(sx, 0, sx + 8, 0); ctx.closePath(); }, INK, LW);
  }
}
function hand(ctx, x, y, r, skin, skinS) { shape(ctx, () => circ(ctx, x, y, r), skin, skinS, r * 0.2, r * 0.2, LW * 0.9); }
function headSkin(ctx, hx, hy, rx, ry, skin, skinS, ears = true) {
  if (ears) {
    shape(ctx, () => { ell(ctx, hx - rx * 0.97, hy + ry * 0.12, 18, 24); }, skin, skinS, 4, 3, LW);
    shape(ctx, () => { ell(ctx, hx + rx * 0.97, hy + ry * 0.12, 18, 24); }, skin, skinS, 4, 3, LW);
  }
  shape(ctx, () => ell(ctx, hx, hy, rx, ry), skin, skinS, rx * 0.1, ry * 0.08, LW);
}
function hoodCollar(ctx, y, rx, color, colorS) {
  shape(ctx, () => ell(ctx, 0, y, rx, 24), color, colorS, 0, 6, LW);
}
function strings(ctx, y0, len, color, tip) {
  ctx.lineCap = 'round';
  for (const s of [-1, 1]) {
    const x0 = s * 18, x1 = s * 22 + Math.sin(len) * 0;
    ctx.strokeStyle = INK; ctx.lineWidth = 8; ctx.beginPath(); ctx.moveTo(x0, y0); ctx.lineTo(x1, y0 + len); ctx.stroke();
    ctx.strokeStyle = color; ctx.lineWidth = 3.5; ctx.stroke();
    shape(ctx, () => rrect(ctx, x1 - 4, y0 + len - 2, 8, 13, 3), tip, null, 0, 0, 2.5);
  }
}

// ------------------------------------------------------------------ gamer
function gamerController(ctx, x, y, w, t) {
  const h = w * 0.5;
  const build = () => {
    ctx.moveTo(x - w * 0.3, y - h * 0.5);
    ctx.lineTo(x + w * 0.3, y - h * 0.5);
    ctx.bezierCurveTo(x + w * 0.52, y - h * 0.5, x + w * 0.56, y + h * 0.2, x + w * 0.5, y + h * 0.55);
    ctx.bezierCurveTo(x + w * 0.44, y + h * 0.85, x + w * 0.26, y + h * 0.6, x + w * 0.18, y + h * 0.28);
    ctx.lineTo(x - w * 0.18, y + h * 0.28);
    ctx.bezierCurveTo(x - w * 0.26, y + h * 0.6, x - w * 0.44, y + h * 0.85, x - w * 0.5, y + h * 0.55);
    ctx.bezierCurveTo(x - w * 0.56, y + h * 0.2, x - w * 0.52, y - h * 0.5, x - w * 0.3, y - h * 0.5);
    ctx.closePath();
  };
  shape(ctx, build, '#34363E', '#23252B', w * 0.03, w * 0.04, LW);
  // d-pad
  ctx.fillStyle = '#15161A';
  ctx.fillRect(x - w * 0.33, y - h * 0.08, w * 0.16, h * 0.16); ctx.fillRect(x - w * 0.29, y - h * 0.24, w * 0.08, h * 0.48);
  // buttons
  const cols = ['#39FF14', '#FF4D6D', '#4DA3FF', '#FFD23F'];
  const off = [[0, -1], [1, 0], [0, 1], [-1, 0]];
  for (let i = 0; i < 4; i++) { ctx.fillStyle = cols[i]; ctx.beginPath(); circ(ctx, x + w * 0.27 + off[i][0] * w * 0.065, y + off[i][1] * w * 0.065, w * 0.032); ctx.fill(); }
  ctx.fillStyle = '#15161A'; ctx.beginPath(); circ(ctx, x - w * 0.1, y + h * 0.12, w * 0.06); circ(ctx, x + w * 0.1, y + h * 0.12, w * 0.06); ctx.fill();
  const hue = (t * 120) % 360;
  ctx.fillStyle = `hsl(${hue},100%,60%)`; ctx.beginPath(); rrect(ctx, x - w * 0.07, y - h * 0.4, w * 0.14, h * 0.1, 3); ctx.fill();
}

function drawGamer(ctx, st) {
  const { t, talk, mood, prop } = st;
  const hue = (t * 80 + (st.seed % 360)) % 360;
  breathe(ctx, t, st.seed, 0.012);
  const hb = bobOf(t, st.seed, 1.8) + talk * 2;
  const HOOD = '#2B2E37', HOOD_S = '#1C1E25', PANTS = '#3A4668';
  const SKIN = '#E0A878', SKIN_S = '#C98E5E';
  groundShadow(ctx, 95);
  // legs + shoes
  limb(ctx, [[-28, -92], [-31, -24]], 38, PANTS);
  limb(ctx, [[28, -92], [31, -24]], 38, PANTS);
  shoe(ctx, -34, -1, '#F2F2F2', '#CFCFD6', NEON);
  shoe(ctx, 34, 1, '#F2F2F2', '#CFCFD6', NEON);
  // arms behind torso for default pose
  const twoHand = prop === 'controller' || prop === 'handheld';
  const canUp = prop === 'can';
  const toast = prop === 'monster';
  // torso
  const torso = () => {
    ctx.moveTo(-60, -200);
    ctx.quadraticCurveTo(-80, -150, -86, -86);
    ctx.quadraticCurveTo(-87, -66, -66, -64);
    ctx.lineTo(66, -64);
    ctx.quadraticCurveTo(87, -66, 86, -86);
    ctx.quadraticCurveTo(80, -150, 60, -200);
    ctx.quadraticCurveTo(0, -214, -60, -200);
    ctx.closePath();
  };
  shape(ctx, torso, HOOD, HOOD_S, 12, 6);
  // hem band + pocket
  ctx.save(); ctx.beginPath(); torso(); ctx.clip();
  ctx.fillStyle = NEON; ctx.fillRect(-100, -82, 200, 5);
  ctx.restore();
  strokeP(ctx, () => { ctx.moveTo(-44, -84); ctx.lineTo(-38, -122); ctx.lineTo(38, -122); ctx.lineTo(44, -84); }, '#101114', 4);
  // chest crosshair print
  ctx.strokeStyle = NEON; ctx.lineWidth = 3.5; ctx.beginPath(); circ(ctx, 38, -158, 11); ctx.moveTo(38, -174); ctx.lineTo(38, -142); ctx.moveTo(22, -158); ctx.lineTo(54, -158); ctx.stroke();
  hoodCollar(ctx, -198, 66, HOOD, HOOD_S);
  strings(ctx, -188, 40, NEON, '#E8FFE0');
  // arms
  const armL = twoHand ? [[-62, -186], [-86, -144], [-46, -122]] : [[-62, -186], [-88, -140], [-84, -100]];
  const armR = twoHand ? [[62, -186], [86, -144], [46, -122]] : canUp ? [[62, -186], [92, -150], [68, -132]] : toast ? [[62, -186], [124, -202], [150, -250]] : [[62, -186], [88, -140], [84, -100]];
  const cuff = (a) => { // neon cuff at the sleeve end
    const p = a[a.length - 1], q = a[a.length - 2];
    const dx = p[0] - q[0], dy = p[1] - q[1], d = Math.hypot(dx, dy);
    limb(ctx, [[p[0] - dx / d * 10, p[1] - dy / d * 10], [p[0] - dx / d * 2, p[1] - dy / d * 2]], 36, NEON, 3);
  };
  const preArms = toast ? [armL] : [armL, armR];
  for (const a of preArms) limb(ctx, a, 36, HOOD);
  for (const a of preArms) cuff(a);
  // head
  const hy = HUMAN.hy + hb, hx = 0;
  headSkin(ctx, hx, hy, HUMAN.hrx, HUMAN.hry, SKIN, SKIN_S, false);
  // eye bags
  ctx.strokeStyle = 'rgba(120,60,90,0.35)'; ctx.lineWidth = 3; ctx.beginPath();
  for (const s of [-1, 1]) { ctx.moveTo(hx + s * 40 - 14, hy + 40); ctx.quadraticCurveTo(hx + s * 40, hy + 46, hx + s * 40 + 14, hy + 40); }
  ctx.stroke();
  face(ctx, {
    x: hx, y: hy + 12, dx: 40, rx: 19, ry: 24, lid: SKIN, iris: '#5B3D26', mood, look: st.look, blink: st.blink, talk,
    lidT: 0.14, mouthY: hy + 56, mouthW: 36, browY: hy - 22, browW: 30, browC: '#2A1C15', browT: 7,
    blushDx: 62, blushY: hy + 42, blushC: 'rgba(230,100,90,0.3)',
  });
  // messy hair
  const HAIR = '#3A2A22', HAIR_S = '#261B15';
  const hair = [[-108, 12], [-114, -40], [-130, -70, 1], [-100, -92], [-96, -130, 1], [-54, -110], [-32, -146, 1], [0, -114], [30, -144, 1], [54, -110], [98, -126, 1], [100, -88], [132, -62, 1], [112, -38], [108, 12],
    [94, -26], [76, -52], [62, -16, 1], [44, -50], [24, -12, 1], [6, -48], [-14, -16, 1], [-32, -50], [-52, -18, 1], [-70, -50], [-88, -22, 1], [-98, -20]];
  shape(ctx, () => smooth(ctx, hair, hx, hy), HAIR, HAIR_S, 8, 8);
  // headset
  const band = () => { ctx.moveTo(hx - 112, hy + 4); ctx.bezierCurveTo(hx - 124, hy - 158, hx + 124, hy - 158, hx + 112, hy + 4); };
  ctx.beginPath(); band(); ctx.lineCap = 'round';
  ctx.strokeStyle = INK; ctx.lineWidth = 34; ctx.stroke();
  ctx.strokeStyle = '#26272D'; ctx.lineWidth = 22; ctx.stroke();
  ctx.strokeStyle = `hsl(${hue},100%,62%)`; ctx.lineWidth = 6; ctx.stroke();
  // mic boom (screen-left cup)
  limbQ(ctx, hx - 112, hy + 30, hx - 104, hy + 66, hx - 50, hy + 62, 7, '#26272D', 3.5);
  shape(ctx, () => ell(ctx, hx - 44, hy + 61, 11, 9), '#1B1C20', null, 0, 0, 4);
  for (const s of [-1, 1]) {
    const cx = hx + s * 114, cy = hy + 8;
    shape(ctx, () => ell(ctx, cx, cy, 30, 44), '#26272D', '#17181C', s * 5, 5);
    const h2 = (hue + (s > 0 ? 60 : 0)) % 360;
    ctx.strokeStyle = `hsla(${h2},100%,62%,0.35)`; ctx.lineWidth = 14; ctx.beginPath(); ell(ctx, cx, cy, 20, 32); ctx.stroke();
    ctx.strokeStyle = `hsl(${h2},100%,64%)`; ctx.lineWidth = 6; ctx.beginPath(); ell(ctx, cx, cy, 20, 32); ctx.stroke();
  }
  moodFX(ctx, mood, hx, hy, 118, t, [hx - 40, hy + 12, 24]);
  // props + hands
  if (twoHand) {
    if (prop === 'handheld') drawHandheld(ctx, 0, -132, 190, t);
    else gamerController(ctx, 0, -130, 130, t);
    hand(ctx, -52, -122, 17, SKIN, SKIN_S); hand(ctx, 52, -122, 17, SKIN, SKIN_S);
  } else {
    hand(ctx, armL[2][0], armL[2][1] + 6, 17, SKIN, SKIN_S);
    if (canUp) { drawCan(ctx, 84, -116, 104, 'MONSTER'); hand(ctx, 66, -128, 17, SKIN, SKIN_S); }
    else if (toast) {
      // raised like a toast: "cheers!"
      limb(ctx, armR, 36, HOOD); cuff(armR);
      const lift = Math.sin(t * 3.2) * 3;
      ctx.save(); ctx.translate(154, -256 + lift); ctx.rotate(0.16 + Math.sin(t * 3.2) * 0.04);
      drawCan(ctx, 0, 0, 104, 'MONSTER');
      ctx.restore();
      hand(ctx, 150, -250 + lift, 17, SKIN, SKIN_S);
      const pulse = 0.5 + 0.5 * Math.sin(t * 6);
      ctx.strokeStyle = INK; ctx.lineWidth = 4.5; ctx.lineCap = 'round'; ctx.beginPath();
      for (const [a, r0] of [[-1.05, 0], [-0.55, 4], [-0.05, 0]]) {
        const ox = 176, oy = -366 + lift, r = 16 + r0 + pulse * 5;
        ctx.moveTo(ox + Math.cos(a) * r, oy + Math.sin(a) * r); ctx.lineTo(ox + Math.cos(a) * (r + 14), oy + Math.sin(a) * (r + 14));
      }
      ctx.stroke();
    }
    else hand(ctx, armR[2][0], armR[2][1] + 6, 17, SKIN, SKIN_S);
  }
}

// ------------------------------------------------------------------ femboy
function stickerLaptopBack(ctx, x, y, w, t) { // closed laptop lid seen from the back, centered at (x,y)
  const h = w * 0.68;
  shape(ctx, () => rrect(ctx, x - w / 2, y - h / 2, w, h, w * 0.07), '#D9DCE6', '#B6BAC8', w * 0.04, w * 0.04, LW);
  // stickers
  ctx.save(); ctx.translate(x + w * 0.1, y - h * 0.16); ctx.rotate(-0.2);
  fillP(ctx, () => circ(ctx, 0, 0, w * 0.15), WHITE); strokeP(ctx, () => circ(ctx, 0, 0, w * 0.15), INK, 3);
  drawSpark(ctx, 0, 0, w * 0.12, ORANGE, t);
  ctx.restore();
  ctx.save(); ctx.translate(x + w * 0.3, y + h * 0.2); ctx.rotate(0.15);
  fillP(ctx, () => rrect(ctx, -w * 0.14, -w * 0.13, w * 0.28, w * 0.26, w * 0.05), '#10222F'); strokeP(ctx, () => rrect(ctx, -w * 0.14, -w * 0.13, w * 0.28, w * 0.26, w * 0.05), INK, 3);
  drawArchPeak(ctx, 0, w * 0.09, w * 0.19, ARCH);
  ctx.restore();
  drawHeart(ctx, x + w * 0.34, y - h * 0.24, w * 0.065, PINK);
  drawHeart(ctx, x - w * 0.02, y + h * 0.24, w * 0.05, LAV);
}

function drawFemboy(ctx, st) {
  const { t, talk, mood, prop } = st;
  ctx.scale(0.9, 0.9); // longer legs, so the whole kid is drawn a touch smaller to stay ~430 tall
  breathe(ctx, t, st.seed, 0.012);
  const hb = bobOf(t, st.seed, 1.8) + talk * 2;
  const SKIN = '#F8D7C2', SKIN_S = '#E8B9A0';
  const HOOD = LAV, HOOD_S = '#977FEA';
  const HAIR = '#F6C6E3', HAIR_S = '#E7A2CC';
  const hy = -334 + hb, hx = 0;
  groundShadow(ctx, 96);
  // back hair
  const back = [[-122, 96], [-136, 40], [-138, -20], [-124, -72], [-96, -110], [-54, -132], [0, -140], [54, -132], [96, -110], [124, -72], [138, -20], [136, 40], [122, 96], [100, 112, 1], [70, 70], [-70, 70], [-100, 112, 1]];
  shape(ctx, () => smooth(ctx, back, hx, hy), HAIR, HAIR_S, 8, 8);
  // legs (skin) + thigh-high socks
  limb(ctx, [[-25, -156], [-27, -30]], 34, SKIN);
  limb(ctx, [[25, -156], [27, -30]], 34, SKIN);
  sockShape(ctx, -27, -90, 90, [PINK, WHITE], 0, -1, 37);
  sockShape(ctx, 27, -90, 90, [PINK, WHITE], 0, 1, 37);
  // mary-jane shoes
  for (const s of [-1, 1]) {
    shoe(ctx, s * 33, s, '#6C4BA8', '#533795', null);
    strokeP(ctx, () => { ctx.moveTo(s * 33 - 16 + s * 6, -24); ctx.lineTo(s * 33 + 16 + s * 6, -27); }, INK, 4);
  }
  // pleated skirt
  const skirt = () => { ctx.moveTo(-60, -172); ctx.lineTo(60, -172); ctx.lineTo(86, -110); ctx.quadraticCurveTo(0, -102, -86, -110); ctx.closePath(); };
  shape(ctx, skirt, PINK, '#E86FAE', 8, 0);
  strokeP(ctx, () => { for (const k of [-0.66, -0.33, 0, 0.33, 0.66]) { ctx.moveTo(k * 62, -160); ctx.lineTo(k * 86, -108 - Math.abs(k) * 2); } }, 'rgba(20,20,19,0.55)', 3);
  strokeP(ctx, () => { ctx.moveTo(-80, -118); ctx.quadraticCurveTo(0, -110, 80, -118); }, 'rgba(255,255,255,0.85)', 3);
  // hoodie (oversized)
  const torso = () => {
    ctx.moveTo(-64, -254);
    ctx.quadraticCurveTo(-92, -212, -96, -160);
    ctx.quadraticCurveTo(-98, -146, -80, -146);
    ctx.lineTo(80, -146);
    ctx.quadraticCurveTo(98, -146, 96, -160);
    ctx.quadraticCurveTo(92, -212, 64, -254);
    ctx.quadraticCurveTo(0, -268, -64, -254);
    ctx.closePath();
  };
  shape(ctx, torso, HOOD, HOOD_S, 12, 6);
  ctx.save(); ctx.beginPath(); torso(); ctx.clip(); ctx.fillStyle = HOOD_S; ctx.fillRect(-110, -160, 220, 16); ctx.restore();
  strokeP(ctx, () => { ctx.moveTo(-100, -160); ctx.lineTo(100, -160); }, 'rgba(20,20,19,0.55)', 3);
  strokeP(ctx, () => { ctx.moveTo(-46, -164); ctx.quadraticCurveTo(-44, -192, -30, -194); ctx.lineTo(30, -194); ctx.quadraticCurveTo(44, -192, 46, -164); }, 'rgba(20,20,19,0.6)', 3.5);
  drawHeart(ctx, 36, -220, 9, PINK);
  hoodCollar(ctx, -252, 70, HOOD, HOOD_S);
  strings(ctx, -242, 38, WHITE, PINK);
  // arms: right paw on hip (confident), left relaxed / hugging laptop
  const hug = prop === 'laptop', shark = prop === 'blahaj';
  const armR = shark ? [[66, -240], [106, -198], [80, -158]] : [[66, -240], [106, -202], [84, -168]];
  const armL = hug ? [[-66, -240], [-106, -194], [-70, -156]] : shark ? [[-66, -240], [-104, -194], [-10, -174]] : [[-66, -240], [-94, -198], [-90, -164]];
  limb(ctx, armR, 44, HOOD); // (with the shark, this arm cradles it from underneath)
  if (!hug && !shark) limb(ctx, armL, 44, HOOD);
  // head
  headSkin(ctx, hx, hy, HUMAN.hrx, HUMAN.hry, SKIN, SKIN_S, false);
  face(ctx, {
    x: hx, y: hy + 14, dx: 40, rx: 21, ry: 27, lid: SKIN, iris: '#A064E8', mood, look: st.look, blink: st.blink, talk,
    mouthY: hy + 58, mouthW: 30, lashes: true, browY: hy - 22, browW: 26, browC: '#C57AA8', browT: 5,
    blushDx: 60, blushY: hy + 44, blushRx: 17, blushRy: 9, blushC: 'rgba(255,120,160,0.5)', hatch: true,
    mouthOpt: { cat: true, fang: true },
  });
  // front hair with side locks
  const front = [[-112, 14], [-118, -40], [-102, -88], [-60, -114], [0, -122], [60, -114], [102, -88], [118, -40], [114, 34], [102, 70, 1], [88, 14], [86, -24],
    [66, -22], [54, -50], [36, -18, 1], [18, -52], [0, -24, 1], [-18, -54], [-36, -20, 1], [-54, -50], [-68, -20], [-86, -26], [-88, 14], [-102, 70, 1]];
  shape(ctx, () => smooth(ctx, front, hx, hy), HAIR, HAIR_S, 6, 8);
  strokeP(ctx, () => { ctx.moveTo(hx - 60, hy - 88); ctx.quadraticCurveTo(hx - 30, hy - 106, hx, hy - 106); }, 'rgba(255,255,255,0.6)', 5);
  // cat ear headband (ears twitch now and then)
  const twitch = (side) => { const p = 4.7, u = ((t + (side > 0 ? 2.1 : 0)) % p + p) % p; return u < 0.25 ? Math.sin(u / 0.25 * Math.PI) * 0.22 : 0; };
  for (const s of [-1, 1]) {
    ctx.save(); ctx.translate(hx + s * 66, hy - 100); ctx.rotate(s * (0.38 + twitch(s)));
    shape(ctx, () => { ctx.moveTo(-32, 12); ctx.quadraticCurveTo(-18, -40, -4, -58); ctx.quadraticCurveTo(2, -62, 8, -54); ctx.quadraticCurveTo(26, -30, 32, 12); ctx.closePath(); }, WHITE, '#E4DDF2', 6, 0);
    fillP(ctx, () => { ctx.moveTo(-18, 6); ctx.quadraticCurveTo(-10, -26, -1, -40); ctx.quadraticCurveTo(12, -22, 18, 6); ctx.closePath(); }, PINK);
    ctx.restore();
  }
  const bandP = () => { ctx.moveTo(hx - 112, hy - 34); ctx.bezierCurveTo(hx - 110, hy - 140, hx + 110, hy - 140, hx + 112, hy - 34); };
  ctx.beginPath(); bandP(); ctx.strokeStyle = INK; ctx.lineWidth = 20; ctx.stroke(); ctx.strokeStyle = WHITE; ctx.lineWidth = 9; ctx.stroke();
  moodFX(ctx, mood, hx, hy, 118, t, [hx - 40, hy + 14, 27]);
  // sweater paws
  const paw = (x, y, a) => {
    ctx.save(); ctx.translate(x, y); ctx.rotate(a);
    shape(ctx, () => { ell(ctx, 0, 0, 25, 21); }, HOOD, HOOD_S, 4, 5);
    strokeP(ctx, () => { ctx.moveTo(-8, 12); ctx.lineTo(-7, 20); ctx.moveTo(4, 13); ctx.lineTo(5, 21); }, INK, 3);
    ctx.restore();
  };
  if (shark) {
    drawBlahaj(ctx, 30, -190, 0.72, t, { squish: 0.67 + 0.04 * Math.sin(t * 2.2), rot: -0.12 });
    paw(76, -150, 0.9);
    limb(ctx, armL, 44, HOOD);
    paw(-8, -172, -0.9);
    return;
  }
  paw(armR[2][0] - 4, armR[2][1] + 6, 0.3);
  if (hug) {
    ctx.save(); ctx.translate(-26, -198); ctx.rotate(-0.1); stickerLaptopBack(ctx, 0, 0, 150, t); ctx.restore();
    limb(ctx, armL, 44, HOOD);
    paw(-62, -150, -0.5);
  } else paw(armL[2][0], armL[2][1] + 8, 0);
}

// ------------------------------------------------------------------ wiki enjoyer
function fidgetSpinner(ctx, x, y, r, t) {
  const a = t * 9;
  ctx.save(); ctx.translate(x, y); ctx.rotate(a);
  const lobes = () => { for (let i = 0; i < 3; i++) { const b = i * TAU / 3; circ(ctx, Math.cos(b) * r * 0.62, Math.sin(b) * r * 0.62, r * 0.4); } circ(ctx, 0, 0, r * 0.42); };
  unionShape(ctx, lobes, TEAL, '#1F9A8F', r * 0.08, r * 0.08, LW * 0.6);
  const cs = [PINK, LAV, '#FFD84A'];
  for (let i = 0; i < 3; i++) { const b = i * TAU / 3; fillP(ctx, () => circ(ctx, Math.cos(b) * r * 0.62, Math.sin(b) * r * 0.62, r * 0.2), cs[i]); strokeP(ctx, () => circ(ctx, Math.cos(b) * r * 0.62, Math.sin(b) * r * 0.62, r * 0.2), INK, 2.5); }
  ctx.restore();
  fillP(ctx, () => circ(ctx, x, y, r * 0.2), '#E8E8EE'); strokeP(ctx, () => circ(ctx, x, y, r * 0.2), INK, 3);
  // motion arcs
  ctx.strokeStyle = 'rgba(20,20,19,0.35)'; ctx.lineWidth = 2.5; ctx.beginPath(); ctx.arc(x, y, r * 1.2, a, a + 1.2); ctx.stroke();
}
function wikiBook(ctx, x, y, w, h) {
  const d = w * 0.22;
  shape(ctx, () => { ctx.moveTo(x - w / 2, y - h / 2); ctx.lineTo(x + w / 2, y - h / 2); ctx.lineTo(x + w / 2 + d, y - h / 2 + d * 0.5); ctx.lineTo(x + w / 2 + d, y + h / 2 + d * 0.5); ctx.lineTo(x - w / 2 + d, y + h / 2 + d * 0.5); ctx.lineTo(x - w / 2, y + h / 2); ctx.closePath(); }, '#F7F0DC', '#E0D5B6', 0, 0, LW);
  strokeP(ctx, () => { for (let i = 1; i < 5; i++) { const k = i / 5; ctx.moveTo(x + w / 2 + d * k, y - h / 2 + d * 0.5 * k + 4); ctx.lineTo(x + w / 2 + d * k, y + h / 2 + d * 0.5 * k - 2); } }, 'rgba(20,20,19,0.3)', 2);
  shape(ctx, () => rrect(ctx, x - w / 2, y - h / 2, w, h, 6), ARCH, '#0F76AA', 5, 5, LW);
  ctx.fillStyle = '#0D5F8A'; ctx.fillRect(x - w / 2 + 8, y - h / 2, 7, h);
  drawArchPeak(ctx, x + 4, y - h * 0.05, h * 0.3, WHITE);
  text(ctx, 'ARCH', x + 4, y + h * 0.16, h * 0.15, 'Nunito-900', WHITE, w * 0.8);
  text(ctx, 'WIKI', x + 4, y + h * 0.32, h * 0.15, 'Nunito-900', WHITE, w * 0.8);
}
function browserTab(ctx, x, y, w, color, k) {
  const h = w * 0.7;
  shape(ctx, () => { ctx.moveTo(x - w / 2 + 6, y - h / 2 - 12); ctx.lineTo(x - w / 2 + w * 0.46, y - h / 2 - 12); ctx.lineTo(x - w / 2 + w * 0.52, y - h / 2 + 2); ctx.lineTo(x - w / 2 + 2, y - h / 2 + 2); ctx.closePath(); }, color, null, 0, 0, 3.5);
  shape(ctx, () => rrect(ctx, x - w / 2, y - h / 2, w, h, 7), WHITE, '#E4E4EC', 0, 4, 3.5);
  fillP(ctx, () => rrect(ctx, x - w / 2 + 2, y - h / 2 + 2, w - 4, h * 0.2, 5), color);
  ctx.fillStyle = 'rgba(20,20,19,0.28)';
  for (let i = 0; i < 3; i++) ctx.fillRect(x - w * 0.38, y - h * 0.12 + i * h * 0.19, w * (0.76 - ((k + i) % 3) * 0.14), h * 0.08);
}

function drawWiki(ctx, st) {
  const { t, talk, mood, prop } = st;
  breathe(ctx, t, st.seed, 0.012);
  const hb = bobOf(t, st.seed, 1.8) + talk * 2 + (mood === 'excited' ? Math.abs(Math.sin(t * 7)) * 4 : 0);
  const SKIN = '#8D5A3B', SKIN_S = '#724629';
  const SHIRT = '#F7F3EA', SHIRT_S = '#DCD6C8', PANTS = '#3D5A88';
  const hy = HUMAN.hy + hb, hx = 0;
  if (prop === 'tabs') {
    const tabs = [[-214, -390, '#1793D1', 0], [206, -410, '#B39DFF', 1], [-222, -238, '#2EC4B6', 2], [218, -256, '#FF8FC7', 3], [-150, -510, '#FFD84A', 4], [146, -530, '#39C07F', 5]];
    for (const [x, y, c, k] of tabs) browserTab(ctx, x + Math.sin(t * 1.3 + k) * 6, y + Math.sin(t * 1.7 + k * 2) * 8, 96, c, k);
  }
  groundShadow(ctx, 92);
  limb(ctx, [[-27, -92], [-30, -24]], 38, PANTS);
  limb(ctx, [[27, -92], [30, -24]], 38, PANTS);
  shoe(ctx, -34, -1, LAV, '#9A83EC', WHITE);
  shoe(ctx, 34, 1, LAV, '#9A83EC', WHITE);
  const torso = () => {
    ctx.moveTo(-58, -202);
    ctx.quadraticCurveTo(-72, -150, -74, -86);
    ctx.quadraticCurveTo(-74, -72, -60, -72);
    ctx.lineTo(60, -72);
    ctx.quadraticCurveTo(74, -72, 74, -86);
    ctx.quadraticCurveTo(72, -150, 58, -202);
    ctx.quadraticCurveTo(0, -214, -58, -202);
    ctx.closePath();
  };
  // skin arms (behind sleeves)
  const book = prop === 'book';
  const armL = [[-66, -176], [-86, -140], [-74, -112]];
  const armR = book ? [[66, -176], [90, -146], [62, -122]] : [[66, -176], [88, -140], [84, -104]];
  limb(ctx, armL, 28, SKIN); limb(ctx, armR, 28, SKIN);
  shape(ctx, torso, SHIRT, SHIRT_S, 10, 6);
  // sleeves
  for (const s of [-1, 1]) shape(ctx, () => { ctx.moveTo(s * 50, -204); ctx.quadraticCurveTo(s * 86, -196, s * 96, -160); ctx.lineTo(s * 70, -148); ctx.quadraticCurveTo(s * 62, -170, s * 52, -176); ctx.closePath(); }, SHIRT, SHIRT_S, 4, 4);
  // neck + collar
  strokeP(ctx, () => { ctx.moveTo(-26, -206); ctx.quadraticCurveTo(0, -186, 26, -206); }, INK, 4);
  drawRainbowInfinity(ctx, 0, -146, 74, t);
  headSkin(ctx, hx, hy, HUMAN.hrx, HUMAN.hry, SKIN, SKIN_S, false);
  face(ctx, {
    x: hx, y: hy + 12, dx: 40, rx: 19, ry: 24, lid: SKIN, iris: '#3B2416', mood, look: st.look, blink: st.blink, talk,
    mouthY: hy + 58, mouthW: 36, browY: hy - 28, browW: 28, browC: '#1E130D', browT: 7,
    blushDx: 62, blushY: hy + 44, blushC: 'rgba(240,110,110,0.35)',
  });
  // round glasses
  ctx.strokeStyle = INK; ctx.lineWidth = 5; ctx.fillStyle = 'rgba(255,255,255,0.14)';
  ctx.beginPath(); circ(ctx, hx - 40, hy + 12, 30); circ(ctx, hx + 40, hy + 12, 30); ctx.fill(); ctx.stroke();
  ctx.beginPath(); ctx.moveTo(hx - 12, hy + 8); ctx.quadraticCurveTo(hx, hy + 2, hx + 12, hy + 8); ctx.moveTo(hx - 70, hy + 8); ctx.lineTo(hx - 100, hy); ctx.moveTo(hx + 70, hy + 8); ctx.lineTo(hx + 100, hy); ctx.stroke();
  ctx.strokeStyle = 'rgba(255,255,255,0.75)'; ctx.lineWidth = 3; ctx.beginPath();
  for (const s of [-1, 1]) { ctx.moveTo(hx + s * 40 - 18, hy + 4); ctx.lineTo(hx + s * 40 - 6, hy - 10); }
  ctx.stroke();
  // curly hair
  const HAIR = '#2A1C15', HAIR_S = '#1A110C';
  const curls = () => {
    const pts = [[-100, -10, 26], [-104, -46, 30], [-86, -80, 32], [-54, -104, 32], [-16, -114, 32], [22, -114, 32], [58, -102, 32], [88, -78, 32], [104, -44, 30], [100, -10, 26],
      [72, -60, 24], [36, -72, 24], [0, -76, 24], [-36, -72, 24], [-72, -60, 24], [-30, -96, 30], [30, -96, 30]];
    for (const [x, y, r] of pts) circ(ctx, hx + x, hy + y, r);
  };
  unionShape(ctx, curls, HAIR, HAIR_S, 6, 6);
  strokeP(ctx, () => { for (const [x, y] of [[-60, -80], [-10, -96], [40, -84], [80, -60], [-86, -40]]) { ctx.moveTo(hx + x - 8, hy + y + 4); ctx.arc(hx + x, hy + y + 4, 8, Math.PI, TAU); } }, 'rgba(255,255,255,0.18)', 3);
  // comfy headphones
  const band = () => { ctx.moveTo(hx - 118, hy + 6); ctx.bezierCurveTo(hx - 128, hy - 176, hx + 128, hy - 176, hx + 118, hy + 6); };
  ctx.beginPath(); band(); ctx.strokeStyle = INK; ctx.lineWidth = 36; ctx.stroke(); ctx.strokeStyle = '#3A3F4A'; ctx.lineWidth = 24; ctx.stroke(); ctx.strokeStyle = TEAL; ctx.lineWidth = 6; ctx.stroke();
  for (const s of [-1, 1]) {
    const cx = hx + s * 116, cy = hy + 14;
    shape(ctx, () => rrect(ctx, cx - 26 - (s > 0 ? 0 : 8), cy - 46, 34, 92, 16), '#3A3F4A', '#2A2E36', 0, 0, LW);
    shape(ctx, () => ell(ctx, cx + s * 10, cy, 30, 50), TEAL, '#1F9A8F', s * 6, 6);
    fillP(ctx, () => ell(ctx, cx + s * 12, cy, 14, 26), 'rgba(255,255,255,0.28)');
  }
  moodFX(ctx, mood, hx, hy, 124, t, [hx - 40, hy + 12, 24]);
  // hands, spinner, book
  hand(ctx, armL[2][0], armL[2][1] + 4, 16, SKIN, SKIN_S);
  fidgetSpinner(ctx, armL[2][0] - 4, armL[2][1] - 18, 30, t);
  if (book) {
    ctx.save(); ctx.translate(96, -136); ctx.rotate(0.12); wikiBook(ctx, 0, 0, 74, 100); ctx.restore();
    hand(ctx, 60, -118, 16, SKIN, SKIN_S);
  } else hand(ctx, armR[2][0], armR[2][1] + 4, 16, SKIN, SKIN_S);
}

// ------------------------------------------------------------------ goblin
const SIGN_CACHE = new Map();
function signLayout(ctx, str, w, h) {
  const key = str + '|' + w + '|' + h;
  if (SIGN_CACHE.has(key)) return SIGN_CACHE.get(key);
  const words = String(str).split(/\s+/).filter(Boolean);
  let best = { size: 12, lines: [String(str)] };
  for (let size = 46; size >= 12; size -= 2) {
    ctx.font = `${size}px "Nunito-900"`;
    const lines = []; let cur = '';
    for (const wd of words) {
      const tryL = cur ? cur + ' ' + wd : wd;
      if (ctx.measureText(tryL).width <= w || !cur) cur = tryL; else { lines.push(cur); cur = wd; }
    }
    if (cur) lines.push(cur);
    const maxW = Math.max(...lines.map((l) => ctx.measureText(l).width));
    if (lines.length * size * 1.08 <= h && maxW <= w) { best = { size, lines }; break; }
    best = { size, lines };
  }
  if (SIGN_CACHE.size > 200) SIGN_CACHE.clear();
  SIGN_CACHE.set(key, best);
  return best;
}
function drawGoblin(ctx, st) {
  const { t, talk, mood } = st;
  const G = '#BFE3AE', G_S = '#98CB86';
  const hop = mood === 'excited' ? Math.abs(Math.sin(t * 6)) * 14 : 0;
  breathe(ctx, t, st.seed, 0.025, 2.2);
  groundShadow(ctx, 80, 1 - hop / 40);
  const by = -126 - hop;
  // stubby legs
  for (const s of [-1, 1]) {
    limb(ctx, [[s * 38, by + 70], [s * 40, -14 - hop * 0.3]], 30, G);
    shape(ctx, () => ell(ctx, s * 44, -10 - hop * 0.3, 24, 12), G, G_S, 3, 3);
  }
  const sign = st.sign;
  const sway = Math.sin(t * 2.3) * 0.04;
  const sy = by - 190;
  // arms
  if (sign) {
    for (const s of [-1, 1]) limbQ(ctx, s * 84, by - 20, s * 118, by - 100, s * 78 - 64 * sway, sy + 66 + s * 78 * sway, 22, G);
  }
  // body blob
  shape(ctx, () => { ctx.moveTo(0, by - 100); ctx.bezierCurveTo(70, by - 100, 116, by - 56, 116, by + 4); ctx.bezierCurveTo(116, by + 70, 64, by + 94, 0, by + 94); ctx.bezierCurveTo(-64, by + 94, -116, by + 70, -116, by + 4); ctx.bezierCurveTo(-116, by - 56, -70, by - 100, 0, by - 100); ctx.closePath(); }, G, G_S, 14, 10);
  fillP(ctx, () => ell(ctx, -46, by - 64, 26, 12, -0.5), 'rgba(255,255,255,0.35)');
  const tw = Math.sin(t * 3.1) * 4;
  ctx.beginPath(); ctx.moveTo(-2, by - 98); ctx.bezierCurveTo(4, by - 130, 30 + tw, by - 136, 24 + tw, by - 116); ctx.bezierCurveTo(20 + tw, by - 106, 8, by - 112, 12, by - 122);
  ctx.strokeStyle = INK; ctx.lineWidth = 16; ctx.stroke(); ctx.strokeStyle = G; ctx.lineWidth = 6; ctx.stroke();
  if (!sign) for (const s of [-1, 1]) shape(ctx, () => ell(ctx, s * 116, by + 24 + Math.sin(t * 3 + s) * 3, 16, 22, s * 0.4), G, G_S, 3, 3);
  const gm = mood === 'neutral' ? 'happy' : mood;
  face(ctx, {
    x: 0, y: by - 12, dx: 44, rx: 30, ry: 34, lid: G, iris: '#141413', irisR: 0.8, eyeMood: mood === 'happy' ? 'neutral' : mood, mood, look: st.look, blink: st.blink, talk,
    mouthY: by + 36, mouthW: 96, mouthMood: gm, mouthOpt: { neutral: 0.26, teeth: false },
    blushDx: 78, blushY: by + 26, blushRx: 14, blushRy: 8, blushC: 'rgba(255,130,150,0.45)',
    browW: mood === 'neutral' || mood === 'happy' ? 0 : 22, browY: by - 58, browC: '#4E7A3F', browT: 6,
  });
  moodFX(ctx, mood, 0, by - 20, 110, t, [-44, by - 12, 34]);
  if (sign) {
    ctx.save(); ctx.translate(0, sy); ctx.rotate(sway);
    const w = 230, h = 124;
    shape(ctx, () => rrect(ctx, -w / 2, -h / 2, w, h, 6), '#D9B77E', '#BF9A5E', 6, 6);
    ctx.strokeStyle = 'rgba(120,80,30,0.3)'; ctx.lineWidth = 2; ctx.beginPath(); ctx.moveTo(-w / 2 + 10, h / 2 - 10); ctx.lineTo(-w / 2 + 34, h / 2 - 22); ctx.moveTo(w / 2 - 20, -h / 2 + 8); ctx.lineTo(w / 2 - 8, -h / 2 + 20); ctx.stroke();
    const L = signLayout(ctx, sign, w - 26, h - 34);
    const lh = L.size * 1.05;
    for (let i = 0; i < L.lines.length; i++) text(ctx, L.lines[i], 0, (i - (L.lines.length - 1) / 2) * lh - 6, L.size, 'Nunito-900', '#2A1D10');
    ctx.restore();
    for (const s of [-1, 1]) shape(ctx, () => circ(ctx, s * 78 - 64 * sway, sy + 64 + s * 78 * sway, 15), G, G_S, 3, 3);
  }
}

// ------------------------------------------------------------------ gentoo wizard
const ROBE_STARS = [[-60, -150, 9], [40, -120, 7], [-20, -60, 8], [70, -60, 9], [-80, -50, 7], [10, -180, 6], [-50, -100, 6], [55, -170, 6], [25, -40, 6]];
function gear(ctx, x, y, r, teeth, rot, color, shadow) {
  const build = () => {
    for (let i = 0; i < teeth * 2; i++) {
      const a0 = rot + (i / (teeth * 2)) * TAU, a1 = rot + ((i + 1) / (teeth * 2)) * TAU;
      const rad = i % 2 ? r * 0.78 : r;
      if (i === 0) ctx.moveTo(x + Math.cos(a0) * rad, y + Math.sin(a0) * rad);
      ctx.lineTo(x + Math.cos(a0) * rad, y + Math.sin(a0) * rad);
      ctx.lineTo(x + Math.cos(a1) * rad, y + Math.sin(a1) * rad);
    }
    ctx.closePath();
  };
  shape(ctx, build, color, shadow, r * 0.08, r * 0.08, LW * 0.8);
}
function drawGentoo(ctx, st) {
  const { t, talk, mood } = st;
  breathe(ctx, t, st.seed, 0.01);
  const hb = bobOf(t, st.seed, 1.5) + talk * 1.5;
  const SKIN = '#F3C9AE', SKIN_S = '#DFAA8C';
  const ROBE = '#6C4AA6', ROBE_S = '#533789';
  const BEARD = '#E6E6EC', BEARD_S = '#BDBDC8';
  const hy = -288 + hb;
  groundShadow(ctx, 120);
  // staff (behind hand, in front of robe)
  const sx = 128;
  // shoes
  for (const s of [-1, 1]) shape(ctx, () => { ctx.moveTo(s * 20, 0); ctx.lineTo(s * 70, 0); ctx.quadraticCurveTo(s * 92, -2, s * 88, -16); ctx.lineTo(s * 84, -10); ctx.quadraticCurveTo(s * 70, -26, s * 44, -26); ctx.quadraticCurveTo(s * 20, -24, s * 20, 0); ctx.closePath(); }, '#5A3A26', '#432A1B', 3, 3);
  // robe
  const robe = () => { ctx.moveTo(-50, -206); ctx.quadraticCurveTo(-96, -120, -118, -14); ctx.quadraticCurveTo(0, 4, 118, -14); ctx.quadraticCurveTo(96, -120, 50, -206); ctx.quadraticCurveTo(0, -216, -50, -206); ctx.closePath(); };
  shape(ctx, robe, ROBE, ROBE_S, 14, 0);
  ctx.save(); ctx.beginPath(); robe(); ctx.clip();
  for (const [x, y, r] of ROBE_STARS) { ctx.beginPath(); twinklePath(ctx, x, y, r); ctx.fillStyle = '#FFD76A'; ctx.fill(); }
  ctx.fillStyle = '#FFD76A'; ctx.fillRect(-130, -22, 260, 7);
  ctx.restore();
  // left bell sleeve
  shape(ctx, () => { ctx.moveTo(-50, -200); ctx.quadraticCurveTo(-92, -170, -112, -108); ctx.lineTo(-66, -100); ctx.quadraticCurveTo(-62, -150, -40, -176); ctx.closePath(); }, ROBE, ROBE_S, 5, 5);
  hand(ctx, -86, -98, 16, SKIN, SKIN_S);
  // staff
  const gy = -392;
  shape(ctx, () => rrect(ctx, sx - 8, gy + 20, 16, -gy - 20, 8), '#8B5A2B', '#6C4420', 4, 0);
  glow(ctx, sx, gy, 10, 90, '150,255,220', 0.55 + 0.15 * Math.sin(t * 3));
  gear(ctx, sx, gy, 34, 8, t * 0.8, '#D8D2EE', '#ABA2CC');
  fillP(ctx, () => circ(ctx, sx, gy, 14), '#9CFFE0'); strokeP(ctx, () => circ(ctx, sx, gy, 14), INK, 4);
  // right sleeve to staff
  shape(ctx, () => { ctx.moveTo(46, -202); ctx.quadraticCurveTo(100, -196, 124, -150); ctx.lineTo(104, -128); ctx.quadraticCurveTo(80, -160, 40, -168); ctx.closePath(); }, ROBE, ROBE_S, 5, 5);
  hand(ctx, sx, -150, 17, SKIN, SKIN_S);
  // head
  headSkin(ctx, 0, hy, 96, 92, SKIN, SKIN_S, true);
  const gm = mood === 'neutral' ? 'grumpy' : mood;
  face(ctx, {
    x: 0, y: hy - 2, dx: 38, rx: 15, ry: 19, lid: SKIN, iris: '#4A5A70', mood, eyeMood: mood === 'neutral' ? 'neutral' : mood, lidT: 0.25, look: st.look, blink: st.blink, talk,
    mouthY: hy + 60, mouthW: 30, mouthMood: gm, noMouth: true, browW: 0,
  });
  // beard (mouth drawn inside)
  const beard = [[-92, 10], [-86, 60], [-72, 110], [-46, 150], [0, 186, 1], [46, 150], [72, 110], [86, 60], [92, 10], [62, 36], [30, 30], [0, 34], [-30, 30], [-62, 36]];
  shape(ctx, () => smooth(ctx, beard, 0, hy), BEARD, BEARD_S, 10, 8);
  strokeP(ctx, () => { ctx.moveTo(-40, hy + 90); ctx.quadraticCurveTo(-30, hy + 120, -18, hy + 140); ctx.moveTo(30, hy + 96); ctx.quadraticCurveTo(24, hy + 122, 14, hy + 142); ctx.moveTo(0, hy + 110); ctx.lineTo(0, hy + 150); }, 'rgba(20,20,19,0.3)', 3);
  mouth(ctx, 0, hy + 62, 32, gm, talk, { teeth: false });
  // mustache
  for (const s of [-1, 1]) shape(ctx, () => { ctx.moveTo(0, hy + 38); ctx.quadraticCurveTo(s * 30, hy + 28, s * 52, hy + 48); ctx.quadraticCurveTo(s * 60, hy + 62, s * 66, hy + 56); ctx.quadraticCurveTo(s * 50, hy + 72, s * 26, hy + 58); ctx.quadraticCurveTo(s * 10, hy + 54, 0, hy + 50); ctx.closePath(); }, BEARD, BEARD_S, 0, 4, LW * 0.85);
  // nose
  shape(ctx, () => ell(ctx, 0, hy + 26, 17, 15), '#EDA78E', '#D88C72', 3, 3);
  // bushy brows
  const bm = mood === 'neutral' ? 'grumpy' : mood;
  brows(ctx, 0, hy - 23, 40, 42, bm, INK, 18);
  brows(ctx, 0, hy - 23, 40, 42, bm, '#D9D9E0', 11);
  // spectacles
  ctx.strokeStyle = '#B8912A'; ctx.lineWidth = 4; ctx.fillStyle = 'rgba(255,255,255,0.15)';
  ctx.beginPath(); circ(ctx, -38, hy + 2, 23); circ(ctx, 38, hy + 2, 23); ctx.fill(); ctx.stroke();
  ctx.beginPath(); ctx.moveTo(-15, hy); ctx.quadraticCurveTo(0, hy - 6, 15, hy); ctx.stroke();
  // hat
  const HAT = '#5E3F98', HAT_S = '#48307A';
  const cone = () => { ctx.moveTo(-86, hy - 58); ctx.quadraticCurveTo(-40, hy - 110, -10, hy - 150); ctx.quadraticCurveTo(20, hy - 180, 66, hy - 168); ctx.quadraticCurveTo(28, hy - 150, 22, hy - 120); ctx.quadraticCurveTo(50, hy - 90, 86, hy - 58); ctx.closePath(); };
  shape(ctx, cone, HAT, HAT_S, 10, 0);
  ctx.save(); ctx.beginPath(); cone(); ctx.clip();
  for (const [x, y, r] of [[-30, -94, 8], [18, -128, 6], [30, -80, 7], [-6, -150, 5]]) { ctx.beginPath(); twinklePath(ctx, x, hy + y, r); ctx.fillStyle = '#FFD76A'; ctx.fill(); }
  ctx.fillStyle = '#FFD76A'; ctx.fillRect(-100, hy - 76, 200, 10);
  ctx.restore();
  shape(ctx, () => ell(ctx, 0, hy - 58, 128, 24), HAT, HAT_S, 0, 6);
  moodFX(ctx, mood, 0, hy, 110, t, [-38, hy - 2, 19]);
}

// ------------------------------------------------------------------ LFS ghost
function drawLFS(ctx, st) {
  const { t, talk, mood } = st;
  const bob = bobOf(t, st.seed, 6, 2.4);
  const GH = 'rgba(252,253,255,0.86)', GH_S = 'rgba(206,216,238,0.9)';
  groundShadow(ctx, 90 * (1 - bob / 40), 0.8);
  const oy = -30 + bob, bw = 116, top = -262 + oy, yb = -70 + oy;
  const body = () => {
    ctx.moveTo(-bw, top);
    ctx.arc(0, top, bw, Math.PI, TAU);
    ctx.bezierCurveTo(bw, top + 80, bw + 12, yb - 60, bw + 8, yb);
    const n = 4, x0 = bw + 8, x1 = -bw - 8;
    for (let i = 0; i < n; i++) {
      const xa = x0 + ((x1 - x0) * i) / n, xb = x0 + ((x1 - x0) * (i + 1)) / n;
      const d = 30 + Math.sin(t * 4 + i * 1.6) * 8;
      ctx.quadraticCurveTo((xa + xb) / 2, yb + d, xb, yb);
    }
    ctx.bezierCurveTo(-bw - 12, yb - 60, -bw, top + 80, -bw, top);
    ctx.closePath();
  };
  // arms (wisps)
  const tap = Math.pow(Math.max(0, Math.sin(t * 4.5)), 3) * 0.6;
  shape(ctx, () => ell(ctx, -bw - 6, top + 110, 20, 30, 0.5), GH, GH_S, 3, 3, LW);
  shape(ctx, body, GH, GH_S, 14, 12);
  // hammer, held up in the right wisp
  const hx = bw + 4, hyy = top + 120;
  ctx.save(); ctx.translate(hx, hyy); ctx.rotate(0.35 - tap);
  shape(ctx, () => rrect(ctx, -7, -110, 14, 118, 6), '#B07A45', '#8E5E31', 3, 0, LW * 0.9);
  shape(ctx, () => { rrect(ctx, -36, -136, 58, 34, 7); }, '#8B929E', '#6B727E', 4, 4, LW * 0.9);
  shape(ctx, () => { ctx.moveTo(20, -132); ctx.quadraticCurveTo(44, -134, 50, -112); ctx.quadraticCurveTo(38, -120, 20, -108); ctx.closePath(); }, '#8B929E', '#6B727E', 2, 2, LW * 0.8);
  ctx.restore();
  shape(ctx, () => ell(ctx, hx, hyy, 22, 26, -0.4), GH, GH_S, 3, 3, LW);
  const fy = top + 34;
  face(ctx, {
    x: 0, y: fy, dx: 40, rx: 22, ry: 29, lid: '#F4F6FB', iris: '#1E2230', irisR: 0.8, mood, look: st.look, blink: st.blink, talk,
    mouthY: fy + 48, mouthW: 34, browW: mood === 'neutral' ? 0 : 26, browY: fy - 42, browC: '#6A7385', browT: 6,
    blushDx: 64, blushY: fy + 34, blushC: 'rgba(255,150,170,0.45)',
  });
  // hard hat
  const HH = '#F5C518', HH_S = '#D6A60C';
  shape(ctx, () => { ctx.moveTo(-96, top - 34); ctx.arc(0, top - 34, 96, Math.PI, TAU); ctx.closePath(); }, HH, HH_S, 10, 0);
  shape(ctx, () => rrect(ctx, -26, top - 136, 52, 104, 14), HH, HH_S, 6, 0, LW * 0.9);
  shape(ctx, () => rrect(ctx, -128, top - 42, 256, 22, 11), HH, HH_S, 0, 6);
  text(ctx, 'LFS', -54, top - 66, 22, 'JBM-800', INK);
  moodFX(ctx, mood, 0, fy, 110, t, [-40, fy, 29]);
}

// ------------------------------------------------------------------ NixOS enjoyer
function snowHalo(ctx, x, y, R, rot) {
  const arms = () => {
    for (let i = 0; i < 6; i++) {
      const a = rot + (i * TAU) / 6, c = Math.cos(a), sn = Math.sin(a);
      ctx.moveTo(x + c * R * 0.25, y + sn * R * 0.25); ctx.lineTo(x + c * R, y + sn * R);
      const bx = x + c * R * 0.64, by = y + sn * R * 0.64;
      for (const d of [-1, 1]) { const b = a + d * 0.8; ctx.moveTo(bx, by); ctx.lineTo(bx + Math.cos(b) * R * 0.26, by + Math.sin(b) * R * 0.26); }
    }
  };
  ctx.lineCap = 'round';
  ctx.beginPath(); arms(); ctx.strokeStyle = INK; ctx.lineWidth = R * 0.1 + 8; ctx.stroke();
  for (let i = 0; i < 6; i++) {
    const a = rot + (i * TAU) / 6, c = Math.cos(a), sn = Math.sin(a);
    ctx.strokeStyle = i % 2 ? '#5277C3' : '#7EBAE4';
    ctx.beginPath(); ctx.moveTo(x + c * R * 0.25, y + sn * R * 0.25); ctx.lineTo(x + c * R, y + sn * R);
    const bx = x + c * R * 0.64, by = y + sn * R * 0.64;
    for (const d of [-1, 1]) { const b = a + d * 0.8; ctx.moveTo(bx, by); ctx.lineTo(bx + Math.cos(b) * R * 0.26, by + Math.sin(b) * R * 0.26); }
    ctx.lineWidth = R * 0.1; ctx.stroke();
  }
  glow(ctx, x, y, R * 0.2, R * 0.75, '160,210,245', 0.5);
}
function drawNix(ctx, st) {
  const { t, talk, mood } = st;
  breathe(ctx, t, st.seed, 0.014, 4.2);
  const hb = bobOf(t, st.seed, 1.6, 4.2) + talk * 1.5;
  const SKIN = '#F5D2B8', SKIN_S = '#E2B598';
  const TN = '#2F3441', TN_S = '#21252F', PANTS = '#CBBFA6';
  const hy = HUMAN.hy + hb, hx = 0;
  snowHalo(ctx, hx, hy - 8, 176, t * 0.15);
  groundShadow(ctx, 90);
  limb(ctx, [[-27, -92], [-29, -24]], 38, PANTS);
  limb(ctx, [[27, -92], [29, -24]], 38, PANTS);
  shoe(ctx, -34, -1, '#F2F2F2', '#D0D0D8', '#C9C9D2');
  shoe(ctx, 34, 1, '#F2F2F2', '#D0D0D8', '#C9C9D2');
  const torso = () => { ctx.moveTo(-58, -200); ctx.quadraticCurveTo(-74, -150, -76, -86); ctx.quadraticCurveTo(-76, -70, -60, -70); ctx.lineTo(60, -70); ctx.quadraticCurveTo(76, -70, 76, -86); ctx.quadraticCurveTo(74, -150, 58, -200); ctx.quadraticCurveTo(0, -212, -58, -200); ctx.closePath(); };
  shape(ctx, torso, TN, TN_S, 10, 6);
  // clasped hands pose
  const armL = [[-62, -186], [-86, -146], [-18, -124]], armR = [[62, -186], [86, -146], [18, -124]];
  limb(ctx, armL, 34, TN); limb(ctx, armR, 34, TN);
  hand(ctx, -10, -122, 17, SKIN, SKIN_S); hand(ctx, 10, -124, 17, SKIN, SKIN_S);
  // turtleneck roll
  shape(ctx, () => rrect(ctx, -44, -222, 88, 32, 14), TN, TN_S, 0, 5);
  strokeP(ctx, () => { ctx.moveTo(-36, -206); ctx.lineTo(36, -206); }, 'rgba(255,255,255,0.18)', 3);
  headSkin(ctx, hx, hy, HUMAN.hrx, HUMAN.hry, SKIN, SKIN_S, true);
  const serene = mood === 'neutral';
  face(ctx, {
    x: hx, y: hy + 12, dx: 40, rx: 18, ry: 23, lid: SKIN, iris: '#5277C3', mood, look: st.look, blink: serene ? 0 : st.blink, talk,
    closed: serene ? 'down' : false, mouthY: hy + 56, mouthW: 32, mouthOpt: { neutral: 0.22 },
    browY: hy - 22, browW: 28, browC: '#8C6A3F', browT: 5, browMood: serene ? 'happy' : mood,
    blushDx: 60, blushY: hy + 40, blushC: 'rgba(255,140,150,0.35)',
  });
  // neat hair with swoop
  const HAIR = '#D9B26F', HAIR_S = '#BA924E';
  const hair = [[-110, 12], [-114, -40], [-96, -88], [-50, -116], [10, -122], [66, -108], [104, -74], [114, -26], [110, 16], [94, -6, 1], [62, -36], [22, -50], [-18, -56], [-50, -62, 1], [-74, -40], [-96, -18], [-104, 6]];
  shape(ctx, () => smooth(ctx, hair, hx, hy), HAIR, HAIR_S, 6, 8);
  strokeP(ctx, () => { ctx.moveTo(hx - 46, hy - 62); ctx.quadraticCurveTo(hx - 40, hy - 96, hx - 10, hy - 112); ctx.moveTo(hx + 10, hy - 96); ctx.quadraticCurveTo(hx + 50, hy - 94, hx + 80, hy - 70); }, 'rgba(255,255,255,0.4)', 4);
  limbQ(ctx, hx + 6, hy - 118, hx + 14, hy - 146, hx + 36, hy - 140, 7, HAIR, 3.5);
  moodFX(ctx, mood, hx, hy, 118, t, [hx - 40, hy + 12, 23]);
}

// ------------------------------------------------------------------ windows update
function drawWinUpdate(ctx, st) {
  const { t, talk, mood } = st;
  if (FLIP) { ctx.scale(-1, 1); FLIP = false; st = { ...st, look: -st.look }; }
  breathe(ctx, t, st.seed, 0.01);
  const BL = '#2F7FE0', BL_S = '#1F64BE', BAR = '#1A56A8';
  const bob = bobOf(t, st.seed, 1.5);
  groundShadow(ctx, 130);
  // legs
  for (const s of [-1, 1]) { limb(ctx, [[s * 56, -90], [s * 58, -20]], 22, '#3A4250'); shape(ctx, () => ell(ctx, s * 64, -12, 30, 14), '#2B3140', null, 0, 0, LW); }
  const x0 = -172, y0 = -392 + bob, w = 344, h = 310;
  // arms
  for (const s of [-1, 1]) limbQ(ctx, s * 170, y0 + 190, s * 212, y0 + 220, s * 200, y0 + 262 + Math.sin(t * 2 + s) * 4, 18, '#3A4250');
  shape(ctx, () => rrect(ctx, x0, y0, w, h, 24), BL, BL_S, 12, 10);
  // title bar
  ctx.save(); ctx.beginPath(); rrect(ctx, x0, y0, w, h, 24); ctx.clip();
  ctx.fillStyle = BAR; ctx.fillRect(x0, y0, w, 48);
  ctx.restore();
  strokeP(ctx, () => { ctx.moveTo(x0, y0 + 48); ctx.lineTo(x0 + w, y0 + 48); }, INK, LW * 0.8);
  // _ □ X buttons
  const by = y0 + 24;
  ctx.strokeStyle = WHITE; ctx.lineWidth = 4; ctx.lineCap = 'round';
  ctx.beginPath(); ctx.moveTo(x0 + w - 124, by + 6); ctx.lineTo(x0 + w - 106, by + 6); ctx.stroke();
  ctx.beginPath(); ctx.rect(x0 + w - 86, by - 8, 16, 15); ctx.stroke();
  ctx.beginPath(); ctx.moveTo(x0 + w - 46, by - 8); ctx.lineTo(x0 + w - 30, by + 8); ctx.moveTo(x0 + w - 30, by - 8); ctx.lineTo(x0 + w - 46, by + 8); ctx.stroke();
  fillP(ctx, () => rrect(ctx, x0 + 18, by - 8, 16, 16, 3), 'rgba(255,255,255,0.8)');
  fillP(ctx, () => rrect(ctx, x0 + 42, by - 4, 80, 8, 4), 'rgba(255,255,255,0.45)');
  // face
  const fy = y0 + 118;
  const wm = mood;
  face(ctx, {
    x: 0, y: fy, dx: 50, rx: 24, ry: 30, lid: BL, iris: '#0D2A5A', mood: wm, look: st.look, blink: st.blink, talk,
    mouthY: fy + 54, mouthW: 44, browY: fy - 44, browW: wm === 'neutral' ? 0 : 30, browC: INK, browT: 6,
    blushDx: 84, blushY: fy + 36, blushC: 'rgba(255,140,170,0.4)', mouthOpt: { neutral: 0.2 },
  });
  // spinner dots
  const cx = 0, cy = y0 + 222;
  for (let i = 0; i < 6; i++) {
    const ph = (((t * 1.1 - i * 0.075) % 1) + 1) % 1;
    const a = -Math.PI / 2 + easeSpin(ph) * TAU;
    ctx.fillStyle = `rgba(255,255,255,${1 - i * 0.12})`;
    ctx.beginPath(); circ(ctx, cx + Math.cos(a) * 25, cy + Math.sin(a) * 25, 6.2 - i * 0.45); ctx.fill();
  }
  text(ctx, st.sign || 'Working on updates 0%', 0, y0 + 274, 24, 'Nunito-800', WHITE, w - 40);
  moodFX(ctx, mood, 0, fy - 10, 150, t, [-50, fy, 30]);
}
function easeSpin(u) { return u < 0.5 ? 2 * u * u * 0.9 + u * 0.1 : 1 - Math.pow(-2 * u + 2, 2) / 2 * 0.9 - (1 - u) * 0.1; }

// ------------------------------------------------------------------ tux
function drawTux(ctx, st) {
  const { t, talk, mood } = st;
  breathe(ctx, t, st.seed, 0.016, 2.8);
  const BK = '#26262A', BK_S = '#101012', BW = '#FAFAF7', BW_S = '#DCDCE2', OR = '#F5A623', OR_S = '#D6860C';
  groundShadow(ctx, 130);
  const flap = (mood === 'excited' ? Math.sin(t * 14) * 0.35 : Math.sin(t * 2) * 0.06) + talk * 0.1;
  // flippers (behind body)
  for (const s of [-1, 1]) {
    ctx.save(); ctx.translate(s * 126, -226); ctx.rotate(-s * (0.3 + flap));
    shape(ctx, () => { ctx.moveTo(-26, 0); ctx.bezierCurveTo(-30, 46, s * 6, 108, s * 14, 132); ctx.bezierCurveTo(s * 34, 98, 30, 46, 26, 0); ctx.arc(0, 0, 26, 0, Math.PI, true); ctx.closePath(); }, BK, BK_S, 6, 6);
    ctx.restore();
  }
  const body = () => { ctx.moveTo(0, -404); ctx.bezierCurveTo(98, -404, 150, -296, 152, -176); ctx.bezierCurveTo(154, -72, 100, -24, 0, -24); ctx.bezierCurveTo(-100, -24, -154, -72, -152, -176); ctx.bezierCurveTo(-150, -296, -98, -404, 0, -404); ctx.closePath(); };
  shape(ctx, body, BK, BK_S, 14, 10);
  ctx.save(); ctx.beginPath(); body(); ctx.clip(); ctx.translate(FLIP ? -7 : 7, 7); ctx.beginPath(); body(); ctx.strokeStyle = 'rgba(150,170,205,0.45)'; ctx.lineWidth = 5; ctx.stroke(); ctx.restore();
  fillP(ctx, () => ell(ctx, -60, -340, 26, 14, -0.7), 'rgba(255,255,255,0.14)');
  // white belly + face mask (union)
  const mask = () => { ctx.moveTo(0, -250); ctx.bezierCurveTo(90, -250, 118, -160, 116, -110); ctx.bezierCurveTo(112, -56, 70, -34, 0, -34); ctx.bezierCurveTo(-70, -34, -112, -56, -116, -110); ctx.bezierCurveTo(-118, -160, -90, -250, 0, -250); ctx.closePath(); ell(ctx, -40, -300, 50, 60); ell(ctx, 40, -300, 50, 60); };
  unionShape(ctx, mask, BW, BW_S, 10, 8, LW * 0.8);
  // feet
  for (const s of [-1, 1]) {
    shape(ctx, () => { ctx.moveTo(s * 12, -14); ctx.quadraticCurveTo(s * 20, -40, s * 60, -38); ctx.quadraticCurveTo(s * 112, -34, s * 110, -8); ctx.quadraticCurveTo(s * 60, 4, s * 12, -14); ctx.closePath(); }, OR, OR_S, 0, 6);
  }
  face(ctx, {
    x: 0, y: -306, dx: 38, rx: 22, ry: 32, lid: BW, iris: INK, irisR: 0.62, mood, look: st.look, blink: st.blink, talk,
    noMouth: true, browW: mood === 'neutral' || mood === 'happy' ? 0 : 26, browY: -350, browC: INK, browT: 7,
    blushDx: 76, blushY: -262, blushC: 'rgba(255,140,160,0.45)',
  });
  // beak: fixed upper half, hinged lower half
  const bo = talk * 24 + (mood === 'shock' ? 16 : 0) + (mood === 'excited' ? 8 : 0);
  const byy = -262;
  const tilt = mood === 'smug' ? -6 : mood === 'sad' || mood === 'angry' ? 4 : 0;
  if (bo > 1.5) fillP(ctx, () => { ctx.moveTo(-32, byy + 2); ctx.quadraticCurveTo(0, byy + 12 + bo * 1.2, 32, byy + 2); ctx.closePath(); }, MOUTH_IN);
  if (bo > 6) fillP(ctx, () => ell(ctx, 0, byy + 6 + bo * 0.75, 14, Math.min(8, bo * 0.3)), TONGUE);
  shape(ctx, () => { ctx.moveTo(-30, byy + 2 + bo * 0.6); ctx.quadraticCurveTo(-24, byy + 22 + bo, 0, byy + 26 + bo); ctx.quadraticCurveTo(24, byy + 22 + bo, 30, byy + 2 + bo * 0.6); ctx.quadraticCurveTo(0, byy + 12 + bo * 0.9, -30, byy + 2 + bo * 0.6); ctx.closePath(); }, OR, OR_S, 0, 4, LW * 0.9);
  shape(ctx, () => { ctx.moveTo(-40, byy + tilt); ctx.quadraticCurveTo(-36, byy - 22, 0, byy - 24); ctx.quadraticCurveTo(36, byy - 22, 40, byy - tilt); ctx.quadraticCurveTo(20, byy + 14, 0, byy + 16); ctx.quadraticCurveTo(-20, byy + 14, -40, byy + tilt); ctx.closePath(); }, OR, OR_S, 0, 5, LW * 0.9);
  fillP(ctx, () => ell(ctx, -12, byy - 12, 9, 4, -0.2), 'rgba(255,255,255,0.5)');
  moodFX(ctx, mood, 0, -300, 130, t, [-38, -306, 32]);
}

// ------------------------------------------------------------------ announcer (The Ministry)
function drawAnnouncer(ctx, st) {
  const { t, talk, mood } = st;
  const CH = '#CDD3DC', CH_S = '#9CA4B2', DARK = '#3A3E48', DARK_S = '#262930';
  const sway = Math.sin(t * 1.3) * 0.015 + talk * 0.02;
  groundShadow(ctx, 110);
  // heavy round base + pole
  shape(ctx, () => { ctx.moveTo(-96, -6); ctx.quadraticCurveTo(-96, -40, 0, -42); ctx.quadraticCurveTo(96, -40, 96, -6); ctx.quadraticCurveTo(0, 6, -96, -6); ctx.closePath(); }, DARK, DARK_S, 0, 8);
  strokeP(ctx, () => { ctx.moveTo(-60, -30); ctx.quadraticCurveTo(0, -38, 60, -30); }, 'rgba(255,255,255,0.18)', 4);
  shape(ctx, () => rrect(ctx, -9, -168, 18, 132, 8), CH, CH_S, 5, 0);
  ctx.save(); ctx.translate(0, -158); ctx.rotate(sway); ctx.translate(0, 158);
  const top = -372, bot = -148, rX = 94;
  const pod = () => rrect(ctx, -rX, top, rX * 2, bot - top, rX * 0.92);
  // yoke
  limb(ctx, [[-114, -262], [-114, -196], [-58, -156], [58, -156], [114, -196], [114, -262]], 14, DARK);
  shape(ctx, pod, CH, CH_S, 14, 10);
  ctx.save(); ctx.beginPath(); pod(); ctx.clip();
  // grille (lower third) + chrome band
  ctx.fillStyle = '#AEB6C3'; ctx.fillRect(-rX, -196, rX * 2, 60);
  ctx.strokeStyle = 'rgba(20,20,19,0.5)'; ctx.lineWidth = 3;
  ctx.beginPath(); for (let y = -188; y < -146; y += 9) { ctx.moveTo(-rX, y); ctx.lineTo(rX, y); } ctx.stroke();
  ctx.fillStyle = '#7C8594'; ctx.fillRect(-rX, -202, rX * 2, 8);
  // side ribs
  ctx.fillStyle = 'rgba(255,255,255,0.35)'; ctx.fillRect(-rX + 16, top, 7, bot - top);
  ctx.restore();
  strokeP(ctx, pod, INK, LW);
  // pivot knobs
  for (const s of [-1, 1]) shape(ctx, () => circ(ctx, s * 112, -262, 16), '#E2B84A', '#B88E24', 3, 3, LW * 0.8);
  // medals pinned on the chest (grille)
  const medal = (mx, c1, c2) => {
    shape(ctx, () => rrect(ctx, mx - 9, -204, 18, 22, 3), c1, null, 0, 0, 3);
    ctx.fillStyle = c2; ctx.fillRect(mx - 3, -202, 6, 18);
    shape(ctx, () => circ(ctx, mx, -170, 11), '#F2C94C', '#C99A1E', 2, 2, 3);
    ctx.beginPath(); starPath(ctx, mx, -170, 6, 3, 5); ctx.fillStyle = '#FFF2B8'; ctx.fill();
  };
  medal(-62, '#C8303A', WHITE); medal(-36, ARCH, WHITE);
  // face
  const fy = -274;
  const stern = mood === 'neutral';
  face(ctx, {
    x: 0, y: fy, dx: 38, rx: 19, ry: 22, lid: CH, iris: '#1B3A5A', mood, eyeMood: stern ? 'neutral' : mood, lidT: stern ? 0.28 : 0.08, look: st.look, blink: st.blink, talk,
    noMouth: true, browY: fy - 32, browW: 40, browMood: stern ? 'angry' : mood, browC: INK, browT: 11,
  });
  mouth(ctx, 0, fy + 58, 48, stern ? 'grumpy' : mood, talk, { teeth: true });
  // handlebar mustache (bounces while talking)
  const mj = -talk * 5, fy2 = fy - 4;
  for (const s of [-1, 1]) shape(ctx, () => { ctx.moveTo(0, fy2 + 34 + mj); ctx.quadraticCurveTo(s * 34, fy2 + 22 + mj, s * 56, fy2 + 42 + mj); ctx.quadraticCurveTo(s * 70, fy2 + 52 + mj, s * 80, fy2 + 30 + mj); ctx.quadraticCurveTo(s * 86, fy2 + 56 + mj, s * 60, fy2 + 62 + mj); ctx.quadraticCurveTo(s * 30, fy2 + 64 + mj, 0, fy2 + 50 + mj); ctx.closePath(); }, '#3B2A20', '#261B15', 0, 4, LW * 0.85);
  // officer cap
  const cy0 = top + 4;
  const CAP = ARCH, CAP_S = '#0F6FA3';
  const crown = () => { ctx.moveTo(-100, cy0 + 20); ctx.quadraticCurveTo(-146, cy0 - 22, -118, cy0 - 44); ctx.quadraticCurveTo(0, cy0 - 70, 118, cy0 - 44); ctx.quadraticCurveTo(146, cy0 - 22, 100, cy0 + 20); ctx.closePath(); };
  shape(ctx, crown, CAP, CAP_S, 12, 8);
  shape(ctx, () => rrect(ctx, -102, cy0 - 2, 204, 28, 8), '#0E3550', '#0A2538', 0, 6);
  strokeP(ctx, () => { ctx.moveTo(-92, cy0 + 10); ctx.lineTo(92, cy0 + 10); }, '#F2C94C', 5);
  for (const s of [-1, 1]) shape(ctx, () => circ(ctx, s * 92, cy0 + 10, 6), '#F2C94C', null, 0, 0, 2.5);
  // visor
  shape(ctx, () => { ctx.moveTo(-100, cy0 + 22); ctx.quadraticCurveTo(0, cy0 + 36, 100, cy0 + 22); ctx.quadraticCurveTo(106, cy0 + 42, 78, cy0 + 48); ctx.quadraticCurveTo(0, cy0 + 60, -78, cy0 + 48); ctx.quadraticCurveTo(-106, cy0 + 42, -100, cy0 + 22); ctx.closePath(); }, '#17181C', null, 0, 0);
  strokeP(ctx, () => { ctx.moveTo(-66, cy0 + 42); ctx.quadraticCurveTo(0, cy0 + 51, 66, cy0 + 42); }, 'rgba(255,255,255,0.3)', 3);
  // emblem: gold wreath disc with peak
  shape(ctx, () => circ(ctx, 0, cy0 - 26, 23), '#F2C94C', '#C99A1E', 3, 3, LW * 0.7);
  drawArchPeak(ctx, 0, cy0 - 13, 28, '#0E3550');
  ctx.restore();
  moodFX(ctx, mood, 0, fy, 130, t, [-38, fy, 22]);
}

// ------------------------------------------------------------------ dispatcher
const DRAW = {
  claude: drawClaude, announcer: drawAnnouncer, gamer: drawGamer, femboy: drawFemboy, wiki: drawWiki, goblin: drawGoblin,
  gentoo: drawGentoo, lfs: drawLFS, nix: drawNix, winupdate: drawWinUpdate, tux: drawTux, haiku: drawHaiku, sonnet: drawSonnet, fable: drawFable,
};
const MOODS = new Set(['neutral', 'happy', 'excited', 'shock', 'smug', 'angry', 'sad']);

// Group opacity: with alpha < 1 the character is drawn opaque into a cached offscreen layer and
// composited once, so overlapping parts don't show through each other. Falls back to direct drawing.
let LAYER = null, LAYER_BUSY = false;
// conservative local-space bounds per character: [half-width, height above anchor]
const BOUNDS = { claude: [250, 470], announcer: [180, 460], gamer: [240, 470], femboy: [190, 480], wiki: [200, 490], goblin: [170, 290],
  gentoo: [240, 500], lfs: [230, 460], nix: [210, 510], winupdate: [240, 420], tux: [200, 440], haiku: [170, 300], sonnet: [175, 300], fable: [170, 300] };
function boundsOf(id, o) {
  if (id === 'wiki' && o.prop === 'tabs') return [300, 600];
  if (id === 'goblin' && o.sign) return [170, 430];
  return BOUNDS[id] || [340, 610];
}
function getLayer(ctx, w, h) {
  if (LAYER && LAYER.width >= w && LAYER.height >= h) return LAYER;
  const W = Math.max(w, LAYER ? LAYER.width : 0), H = Math.max(h, LAYER ? LAYER.height : 0);
  let cv = null;
  try { if (typeof OffscreenCanvas !== 'undefined') cv = new OffscreenCanvas(W, H); } catch (e) { cv = null; }
  if (!cv) { try { if (ctx.canvas && ctx.canvas.constructor) cv = new ctx.canvas.constructor(W, H); } catch (e) { cv = null; } }
  if (cv && cv.getContext && cv.width >= w && cv.height >= h) LAYER = cv; else return null;
  return LAYER;
}
function drawFaded(ctx, id, o, alpha) {
  if (LAYER_BUSY || typeof ctx.getTransform !== 'function') return false;
  const m = ctx.getTransform();
  const s = o.s ?? 1, x = o.x ?? 0, y = o.y ?? 0;
  const [bwL, bhL] = boundsOf(id, o);
  const xs = [x - bwL * s, x + bwL * s], ys = [y - bhL * s, y + 30 * s];
  let x0 = Infinity, y0 = Infinity, x1 = -Infinity, y1 = -Infinity;
  for (const px of xs) for (const py of ys) {
    const dx = m.a * px + m.c * py + m.e, dy = m.b * px + m.d * py + m.f;
    if (dx < x0) x0 = dx; if (dx > x1) x1 = dx; if (dy < y0) y0 = dy; if (dy > y1) y1 = dy;
  }
  if (ctx.canvas && ctx.canvas.width) { x0 = Math.max(x0, 0); y0 = Math.max(y0, 0); x1 = Math.min(x1, ctx.canvas.width); y1 = Math.min(y1, ctx.canvas.height); }
  const bx = Math.floor(x0) - 2, by = Math.floor(y0) - 2, bw = Math.ceil(x1) - bx + 2, bh = Math.ceil(y1) - by + 2;
  if (bw <= 2 || bh <= 2) return true; // fully off-canvas
  if (bw > 2400 || bh > 2400) return false;
  const L = getLayer(ctx, bw, bh);
  if (!L) return false;
  const lc = L.getContext('2d');
  lc.setTransform(1, 0, 0, 1, 0, 0); lc.globalAlpha = 1; lc.globalCompositeOperation = 'source-over';
  lc.clearRect(0, 0, bw, bh);
  lc.setTransform(m.a, m.b, m.c, m.d, m.e - bx, m.f - by);
  LAYER_BUSY = true;
  try { drawCharacter(lc, id, { ...o, alpha: 1 }); } finally { LAYER_BUSY = false; }
  ctx.save();
  ctx.setTransform(1, 0, 0, 1, 0, 0);
  ctx.globalAlpha *= alpha;
  ctx.drawImage(L, 0, 0, bw, bh, bx, by, bw, bh);
  ctx.restore();
  return true;
}

export function drawCharacter(ctx, id, o = {}) {
  const fn = DRAW[id] || DRAW.claude;
  const alpha = Number.isFinite(o.alpha) ? clamp(o.alpha, 0, 1) : 1;
  if (alpha <= 0) return;
  if (alpha < 0.995 && drawFaded(ctx, id, o, alpha)) return;
  const s = o.s ?? 1;
  const prevFlip = FLIP;
  ctx.save();
  try {
    ctx.translate(o.x ?? 0, o.y ?? 0);
    ctx.scale(o.flip ? -s : s, s);
    ctx.globalAlpha *= alpha;
    ctx.lineJoin = 'round'; ctx.lineCap = 'round';
    FLIP = !!o.flip;
    const t = Number.isFinite(o.t) ? o.t : 0;
    const seed = SEEDS[id] ?? 1;
    const look = clamp(Number.isFinite(o.look) ? o.look : 0, -1, 1) * (o.flip ? -1 : 1);
    fn(ctx, {
      t, seed, look,
      talk: clamp(Number.isFinite(o.talk) ? o.talk : 0, 0, 1),
      mood: MOODS.has(o.mood) ? o.mood : 'neutral',
      prop: o.prop ?? null, sign: o.sign ?? null,
      blink: blinkAt(t, seed),
    });
  } finally {
    FLIP = prevFlip;
    ctx.restore();
  }
}

// ------------------------------------------------------------------ reusable props
const LOGO_RAYS = makeRays(12, [1, 0.8, 0.94, 0.78, 0.98, 0.84, 0.9, 0.76, 1, 0.82, 0.92, 0.8], [0, 0.06, -0.04, 0.05, -0.03, 0.04, -0.05, 0.03, 0.02, -0.04, 0.05, -0.02], 0.12, 0.1, 0.055);
export function drawSpark(ctx, x, y, r, color = ORANGE, t = 0) {
  ctx.save();
  ctx.beginPath();
  sparkBuild(ctx, x, y, r, LOGO_RAYS, 0.2, t * 0.3, t, 0.025, 1.7);
  ctx.fillStyle = color; ctx.fill();
  ctx.restore();
}

export function drawArchPeak(ctx, x, y, size, color = ARCH) {
  const h = size, w = size * 0.92;
  ctx.save();
  ctx.beginPath();
  ctx.moveTo(x, y - h);
  ctx.quadraticCurveTo(x + w * 0.2, y - h * 0.52, x + w * 0.5, y);
  ctx.quadraticCurveTo(x + w * 0.42, y - h * 0.04, x + w * 0.33, y);
  ctx.quadraticCurveTo(x + w * 0.1, y - h * 0.62, x - w * 0.02, y - h * 0.5);
  ctx.quadraticCurveTo(x - w * 0.14, y - h * 0.4, x - w * 0.33, y);
  ctx.quadraticCurveTo(x - w * 0.42, y - h * 0.04, x - w * 0.5, y);
  ctx.quadraticCurveTo(x - w * 0.2, y - h * 0.52, x, y - h);
  ctx.closePath();
  ctx.fillStyle = color; ctx.fill();
  ctx.restore();
}

export function drawRainbowInfinity(ctx, x, y, w, t = 0) {
  const a = w / 2, N = 56;
  const lw = w * 0.13;
  ctx.save();
  ctx.lineCap = 'round'; ctx.lineJoin = 'round';
  ctx.beginPath();
  for (let i = 0; i <= N; i++) {
    const th = (i / N) * TAU, d = 1 + Math.sin(th) ** 2;
    const px = x + (a * Math.cos(th)) / d, py = y + (a * Math.sin(th) * Math.cos(th)) / d;
    if (i === 0) ctx.moveTo(px, py); else ctx.lineTo(px, py);
  }
  ctx.closePath();
  ctx.strokeStyle = INK; ctx.lineWidth = lw + Math.max(3, w * 0.07); ctx.stroke();
  // left-to-right rainbow whose hues drift slowly with t
  const g = ctx.createLinearGradient(x - a, y, x + a, y);
  const sh = (t * 40) % 360;
  for (let k = 0; k <= 6; k++) g.addColorStop(k / 6, `hsl(${(k * 50 + sh) % 360},92%,58%)`);
  ctx.strokeStyle = g; ctx.lineWidth = lw; ctx.stroke();
  ctx.restore();
}

// (x,y) = top-center of the sock (thigh band); h = length to sole; dir = toe direction (+1 right, -1 left)
function sockShape(ctx, x, y, h, colors = [PINK, WHITE], angle = 0, dir = 1, widthOverride = 0, withFoot = true) {
  const w0 = widthOverride || h * 0.24, w1 = w0 * 0.8;
  ctx.save(); ctx.translate(x, y); ctx.rotate(angle);
  const ank = h * 0.8;
  const build = () => {
    ctx.moveTo(-w0 / 2, 0); ctx.lineTo(w0 / 2, 0);
    ctx.quadraticCurveTo(w0 / 2 + 2, ank * 0.5, w1 / 2, ank);
    if (withFoot) {
      if (dir > 0) { ctx.quadraticCurveTo(w1 * 1.4, ank + h * 0.02, w1 * 1.5, h * 0.92); ctx.quadraticCurveTo(w1 * 1.5, h, w1 * 1.1, h); ctx.lineTo(-w1 / 2 + 2, h); ctx.quadraticCurveTo(-w1 / 2 - 4, h * 0.95, -w1 / 2, ank); }
      else { ctx.quadraticCurveTo(w1 / 2 + 4, h * 0.95, w1 / 2 - 2, h); ctx.lineTo(-w1 * 1.1, h); ctx.quadraticCurveTo(-w1 * 1.5, h, -w1 * 1.5, h * 0.92); ctx.quadraticCurveTo(-w1 * 1.4, ank + h * 0.02, -w1 / 2, ank); }
    } else ctx.lineTo(-w1 / 2, ank);
    ctx.quadraticCurveTo(-w0 / 2 - 2, ank * 0.5, -w0 / 2, 0);
    ctx.closePath();
  };
  ctx.beginPath(); build(); ctx.fillStyle = colors[0]; ctx.fill();
  ctx.save(); ctx.clip();
  const band = h * 0.1;
  for (let i = 1, k = 1; i * band < h * 1.05; i++, k++) { ctx.fillStyle = colors[k % colors.length]; ctx.fillRect(-w0 * 2, i * band, w0 * 4, band); }
  ctx.fillStyle = colors[0]; ctx.fillRect(-w0 * 2, -2, w0 * 4, band * 0.9);
  ctx.fillStyle = 'rgba(20,20,19,0.12)'; ctx.fillRect(w0 * 0.18, -2, w0, h * 1.1);
  ctx.restore();
  ctx.beginPath(); build(); ctx.strokeStyle = INK; ctx.lineWidth = Math.min(LW, Math.max(2, h * 0.04)); ctx.stroke();
  ctx.restore();
}
export function drawSock(ctx, x, y, h, colors = [PINK, WHITE], angle = 0) {
  sockShape(ctx, x, y, h, colors && colors.length ? colors : [PINK, WHITE], angle, 1, 0, true);
}

// can silhouette; crush 0..1 dents the waist (side = which flank takes the dent)
function canBody(ctx, x, y, w, h, crush = 0, side = 1) {
  const r = w * 0.18;
  if (!crush) { rrect(ctx, x - w / 2, y - h, w, h, r); return; }
  const d = w * 0.2 * crush, top = y - h, my = y - h * 0.52;
  const L = x - w / 2, R = x + w / 2;
  const dR = side > 0 ? d : d * 0.35, dL = side > 0 ? d * 0.35 : d;
  ctx.moveTo(L + r, top);
  ctx.lineTo(R - r, top + h * 0.03 * crush * side);
  ctx.quadraticCurveTo(R, top + h * 0.03 * crush * side, R, top + r);
  ctx.lineTo(R, my - h * 0.13); ctx.lineTo(R - dR, my - h * 0.02); ctx.lineTo(R - dR * 0.6, my + h * 0.05); ctx.lineTo(R, my + h * 0.14);
  ctx.lineTo(R, y - r); ctx.quadraticCurveTo(R, y, R - r, y);
  ctx.lineTo(L + r, y); ctx.quadraticCurveTo(L, y, L, y - r);
  ctx.lineTo(L, my + h * 0.12); ctx.lineTo(L + dL, my + h * 0.03); ctx.lineTo(L + dL * 0.5, my - h * 0.06); ctx.lineTo(L, my - h * 0.15);
  ctx.lineTo(L, top + r); ctx.quadraticCurveTo(L, top, L + r, top);
  ctx.closePath();
}
// three jagged claw tears (original shape): centered at (cx,cy), W wide, H tall
function clawSlashes(ctx, cx, cy, W, H, color) {
  const specs = [[-0.34, 0.86, -0.1, 0.07], [0, 1, 0.02, 0.085], [0.34, 0.9, 0.12, 0.07]]; // x, length, lean, width
  ctx.fillStyle = color;
  for (let k = 0; k < 3; k++) {
    const [ox, len, lean, wd] = specs[k];
    const n = 8, top = cy - (H * len) / 2 + (k === 1 ? -H * 0.04 : H * 0.03), L = H * len, mw = W * wd;
    const L_ = [], R_ = [];
    for (let i = 0; i <= n; i++) {
      const u = i / n, yy = top + u * L;
      const xc = cx + ox * W + lean * W * (u - 0.5);
      const hw = mw * Math.pow(Math.sin(Math.PI * clamp(u, 0.02, 0.98)), 0.75);
      const j = (i % 2 ? 1 : -1) * mw * 0.42 * (i > 0 && i < n ? 1 : 0);
      L_.push([xc - hw + j, yy]); R_.push([xc + hw + j * 0.6, yy + (i % 2 ? L * 0.03 : 0)]);
    }
    ctx.beginPath(); ctx.moveTo(L_[0][0], L_[0][1]);
    for (let i = 1; i < L_.length; i++) ctx.lineTo(L_[i][0], L_[i][1]);
    for (let i = R_.length - 1; i >= 0; i--) ctx.lineTo(R_[i][0], R_[i][1]);
    ctx.closePath(); ctx.fill();
  }
}
function smallCaps(ctx, str, x, y, size, family, color, maxW) {
  const first = str.slice(0, 1), rest = str.slice(1);
  ctx.save(); ctx.translate(x, y); if (FLIP) ctx.scale(-1, 1);
  ctx.textBaseline = 'alphabetic'; ctx.textAlign = 'left'; ctx.fillStyle = color;
  ctx.font = `${size}px "${family}"`; const w1 = ctx.measureText(first).width;
  ctx.font = `${size * 0.76}px "${family}"`; const w2 = ctx.measureText(rest).width;
  const tot = w1 + w2 + size * 0.04, k = maxW && tot > maxW ? maxW / tot : 1;
  ctx.scale(k, k);
  ctx.font = `${size}px "${family}"`; ctx.fillText(first, -tot / 2, size * 0.36);
  ctx.font = `${size * 0.76}px "${family}"`; ctx.fillText(rest, -tot / 2 + w1 + size * 0.04, size * 0.36);
  ctx.restore();
}
function monsterCan(ctx, x, y, h, crush = 0, side = 1, claw = '#7CFF3A') {
  const w = h * 0.46, lw = Math.min(LW, Math.max(2, h * 0.05));
  const body = () => canBody(ctx, x, y, w, h, crush, side);
  ctx.beginPath(); body(); ctx.fillStyle = '#18191C'; ctx.fill();
  ctx.save(); ctx.clip();
  ctx.fillStyle = 'rgba(255,255,255,0.08)'; ctx.fillRect(x - w * 0.36, y - h, w * 0.15, h);
  ctx.fillStyle = 'rgba(0,0,0,0.4)'; ctx.fillRect(x + w * 0.24, y - h, w * 0.3, h);
  clawSlashes(ctx, x - w * 0.02, y - h * 0.56, w * 0.8, h * 0.5, claw);
  // silver rims
  ctx.fillStyle = '#CDD2DA'; ctx.fillRect(x - w / 2, y - h - 2, w, h * 0.09 + 2);
  ctx.fillStyle = '#8F97A3'; ctx.fillRect(x - w / 2, y - h + h * 0.075, w, h * 0.02);
  ctx.fillStyle = '#B9BFC9'; ctx.fillRect(x - w / 2, y - h * 0.065, w, h * 0.065);
  ctx.fillStyle = 'rgba(255,255,255,0.55)'; ctx.fillRect(x - w * 0.34, y - h - 2, w * 0.1, h * 0.09 + 2);
  ctx.restore();
  smallCaps(ctx, 'MONSTER', x - w * 0.02, y - h * 0.2, h * 0.12, 'BebasNeue', '#F2F2F2', w * 0.8);
  if (crush) {
    ctx.strokeStyle = 'rgba(255,255,255,0.28)'; ctx.lineWidth = Math.max(1.5, h * 0.018);
    ctx.beginPath(); ctx.moveTo(x - w * 0.3, y - h * 0.5); ctx.lineTo(x + w * 0.05, y - h * 0.56); ctx.lineTo(x + w * 0.3, y - h * 0.47); ctx.stroke();
  }
  ctx.beginPath(); body(); ctx.strokeStyle = INK; ctx.lineWidth = lw; ctx.stroke();
}
function fuelCan(ctx, x, y, h, label, color, crush = 0, side = 1) {
  const w = h * 0.46, lw = Math.min(LW, Math.max(2, h * 0.05));
  const body = () => canBody(ctx, x, y, w, h, crush, side);
  ctx.beginPath(); body(); ctx.fillStyle = '#1A1B1F'; ctx.fill();
  ctx.save(); ctx.clip();
  ctx.fillStyle = color; ctx.fillRect(x - w / 2, y - h * 0.82, w, h * 0.62);
  ctx.fillStyle = 'rgba(255,255,255,0.35)'; ctx.fillRect(x - w * 0.34, y - h, w * 0.12, h);
  ctx.fillStyle = 'rgba(0,0,0,0.2)'; ctx.fillRect(x + w * 0.24, y - h, w * 0.3, h);
  ctx.fillStyle = '#C9CED6'; ctx.fillRect(x - w / 2, y - h, w, h * 0.09); ctx.fillRect(x - w / 2, y - h * 0.07, w, h * 0.07);
  ctx.restore();
  ctx.beginPath(); ctx.moveTo(x + w * 0.1, y - h * 0.79); ctx.lineTo(x - w * 0.18, y - h * 0.66); ctx.lineTo(x - w * 0.01, y - h * 0.645); ctx.lineTo(x - w * 0.1, y - h * 0.53); ctx.lineTo(x + w * 0.2, y - h * 0.68); ctx.lineTo(x + w * 0.03, y - h * 0.69); ctx.closePath();
  ctx.fillStyle = '#141413'; ctx.fill();
  const words = String(label || '').split(/\s+/).filter(Boolean);
  const fs = h * 0.125;
  for (let i = 0; i < words.length && i < 2; i++) text(ctx, words[i], x, y - h * (0.43 - i * 0.13), fs, 'Anton', '#141413', w * 0.84);
  ctx.beginPath(); body(); ctx.strokeStyle = INK; ctx.lineWidth = lw; ctx.stroke();
}
// (x,y) = bottom center, h = height. label 'MONSTER' -> matte black can with neon claw tears.
export function drawCan(ctx, x, y, h, label = 'GAMER FUEL', color = NEON) {
  ctx.save();
  ctx.lineJoin = 'round';
  if (label === 'MONSTER') monsterCan(ctx, x, y, h, 0, 1, '#7CFF3A');
  else fuelCan(ctx, x, y, h, label, color);
  ctx.restore();
}
// pyramid of n empty cans on the floor y, bottom row centered on x; h = one can's height
export function drawCanStack(ctx, x, y, h, n = 6, t = 0) {
  n = Math.max(0, Math.floor(n || 0));
  if (!n) return;
  const w = h * 0.46, gap = w * 1.05;
  let k = 1; while ((k * (k + 1)) / 2 < n) k++;
  const rows = []; let left = n;
  for (let r = k; r >= 1 && left > 0; r--) { const c = Math.min(r, left); rows.push(c); left -= c; }
  ctx.save();
  ctx.lineJoin = 'round';
  ctx.fillStyle = 'rgba(20,20,19,0.16)'; ctx.beginPath(); ell(ctx, x, y - 2, (rows[0] * gap) / 2 + w * 0.3, h * 0.07); ctx.fill();
  const last = rows.length - 1;
  for (let r = 0; r < rows.length; r++) {
    const c = rows[r];
    for (let j = 0; j < c; j++) {
      const hsh = hashStr(`${r}:${j}:${n}`);
      const top = r === last;
      const crush = top && (hsh % 3 !== 0) ? 0.55 + (hsh % 5) * 0.08 : 0;
      let tilt = ((hsh % 7) - 3) * 0.006 + (r === 1 && j === 0 ? -0.05 : 0);
      if (top) tilt += (j % 2 ? 0.07 : -0.06) + Math.sin(t * 2.3 + j) * 0.02;
      const cx = x + (j - (c - 1) / 2) * gap + ((hsh >>> 4) % 5 - 2) * w * 0.015;
      const cy = y - r * h * 0.985 + (crush ? h * 0.04 : 0);
      ctx.save(); ctx.translate(cx, cy); ctx.rotate(tilt);
      monsterCan(ctx, 0, 0, crush ? h * 0.9 : h, crush, hsh % 2 ? 1 : -1, '#7CFF3A');
      ctx.restore();
    }
  }
  ctx.restore();
}

export function drawHandheld(ctx, x, y, w, t = 0) {
  const h = w * 0.42, lw = Math.min(LW, Math.max(2, w * 0.026));
  ctx.save();
  const body = () => {
    ctx.moveTo(x - w * 0.4, y - h / 2);
    ctx.lineTo(x + w * 0.4, y - h / 2);
    ctx.quadraticCurveTo(x + w / 2, y - h / 2, x + w / 2, y - h * 0.2);
    ctx.quadraticCurveTo(x + w * 0.52, y + h * 0.55, x + w * 0.4, y + h * 0.62);
    ctx.quadraticCurveTo(x + w * 0.32, y + h * 0.66, x + w * 0.27, y + h / 2);
    ctx.lineTo(x - w * 0.27, y + h / 2);
    ctx.quadraticCurveTo(x - w * 0.32, y + h * 0.66, x - w * 0.4, y + h * 0.62);
    ctx.quadraticCurveTo(x - w * 0.52, y + h * 0.55, x - w / 2, y - h * 0.2);
    ctx.quadraticCurveTo(x - w / 2, y - h / 2, x - w * 0.4, y - h / 2);
    ctx.closePath();
  };
  const sh = FLIP; FLIP = false; // this prop has its own lighting
  shape(ctx, body, '#2C2D33', '#1C1D21', w * 0.02, w * 0.03, lw);
  FLIP = sh;
  // screen
  const sw = w * 0.46, shh = h * 0.72, sx = x - sw / 2, sy = y - shh / 2 - h * 0.02;
  ctx.fillStyle = '#0A0B0D'; ctx.beginPath(); rrect(ctx, sx - w * 0.015, sy - w * 0.015, sw + w * 0.03, shh + w * 0.03, w * 0.02); ctx.fill();
  const g = ctx.createLinearGradient(sx, sy, sx, sy + shh);
  const hue = (t * 30) % 360;
  g.addColorStop(0, `hsl(${(hue + 250) % 360},70%,55%)`); g.addColorStop(1, `hsl(${(hue + 190) % 360},80%,62%)`);
  ctx.fillStyle = g; ctx.fillRect(sx, sy, sw, shh);
  ctx.save(); ctx.beginPath(); ctx.rect(sx, sy, sw, shh); ctx.clip();
  // tiny platformer scene
  ctx.fillStyle = 'rgba(20,20,40,0.55)';
  for (let i = 0; i < 6; i++) { const bx = sx + ((i * sw * 0.3 - t * sw * 0.25) % (sw * 1.8) + sw * 1.8) % (sw * 1.8) - sw * 0.2; ctx.fillRect(bx, sy + shh * (0.65 - (i % 3) * 0.12), sw * 0.18, shh * 0.5); }
  ctx.fillStyle = '#FFE066'; ctx.beginPath(); circ(ctx, sx + sw * 0.35, sy + shh * (0.5 - Math.abs(Math.sin(t * 3)) * 0.2), shh * 0.08); ctx.fill();
  ctx.restore();
  ctx.fillStyle = 'rgba(255,255,255,0.12)'; ctx.beginPath(); ctx.moveTo(sx, sy); ctx.lineTo(sx + sw * 0.4, sy); ctx.lineTo(sx, sy + shh * 0.6); ctx.closePath(); ctx.fill();
  // controls
  for (const s of [-1, 1]) {
    const cx = x + s * w * 0.385;
    ctx.fillStyle = '#15161A'; ctx.beginPath(); circ(ctx, cx, y - h * 0.08, w * 0.045); ctx.fill();
    ctx.strokeStyle = '#4A4C55'; ctx.lineWidth = Math.max(1, w * 0.008); ctx.beginPath(); circ(ctx, cx, y - h * 0.08, w * 0.03); ctx.stroke();
    ctx.fillStyle = '#23242A'; ctx.beginPath(); rrect(ctx, cx - w * 0.04, y + h * 0.14, w * 0.08, w * 0.08, w * 0.015); ctx.fill();
  }
  ctx.fillStyle = '#15161A';
  ctx.fillRect(x - w * 0.415, y - h * 0.34, w * 0.06, w * 0.02); ctx.fillRect(x - w * 0.395, y - h * 0.34 - w * 0.02, w * 0.02, w * 0.06);
  const bc = ['#E8E8EE', '#E8E8EE', '#E8E8EE', '#E8E8EE'];
  const off = [[0, -1], [1, 0], [0, 1], [-1, 0]];
  for (let i = 0; i < 4; i++) { ctx.fillStyle = bc[i]; ctx.beginPath(); circ(ctx, x + w * 0.385 + off[i][0] * w * 0.022, y - h * 0.3 + off[i][1] * w * 0.022, w * 0.012); ctx.fill(); }
  ctx.restore();
}

export function drawHeart(ctx, x, y, r, color = PINK) {
  ctx.save();
  const build = () => {
    ctx.moveTo(x, y + r * 0.95);
    ctx.bezierCurveTo(x - r * 1.5, y - r * 0.05, x - r * 1.05, y - r * 1.25, x, y - r * 0.52);
    ctx.bezierCurveTo(x + r * 1.05, y - r * 1.25, x + r * 1.5, y - r * 0.05, x, y + r * 0.95);
    ctx.closePath();
  };
  ctx.beginPath(); build(); ctx.fillStyle = color; ctx.fill();
  ctx.lineJoin = 'round'; ctx.strokeStyle = INK; ctx.lineWidth = Math.min(LW, Math.max(1.5, r * 0.16)); ctx.stroke();
  ctx.fillStyle = 'rgba(255,255,255,0.6)'; ctx.beginPath(); ell(ctx, x - r * 0.45, y - r * 0.4, r * 0.2, r * 0.13, -0.6); ctx.fill();
  ctx.restore();
}

// ------------------------------------------------------------------ plush shark (Blahaj-style easter egg)
// (x,y) = body center, ~260 px nose-to-tail at s=1, head faces +x. o: { rot, flip, squish 0..1, peek 0..1 }
export function drawBlahaj(ctx, x, y, s = 1, t = 0, o = {}) {
  const rot = Number.isFinite(o.rot) ? o.rot : 0, flip = !!o.flip;
  const sq = clamp(Number.isFinite(o.squish) ? o.squish : 0, 0, 1), peek = clamp(Number.isFinite(o.peek) ? o.peek : 0, 0, 1);
  const B = '#5E8EB5', B_S = '#4A7599', B_L = '#7AA5C9', W = '#F7F8FA', W_S = '#D5DCE5', PK = '#F58FA8';
  const prevFlip = FLIP;
  ctx.save();
  try {
    ctx.translate(x, y);
    ctx.rotate(rot);
    ctx.scale(flip ? -s : s, s);
    FLIP = prevFlip !== flip;
    ctx.scale(1 + 0.08 * sq, 1 - 0.2 * sq); // hug squash
    ctx.lineJoin = 'round'; ctx.lineCap = 'round';
    if (peek > 0) { ctx.beginPath(); ctx.rect(-150 + 190 * peek, -220, 420, 440); ctx.clip(); }
    const wig = Math.sin(t * 2.1);
    ctx.rotate(wig * 0.03);
    const tailA = Math.sin(t * 2.7) * 0.16;
    // tail fin (behind body), swishing
    const tail = () => {
      ctx.moveTo(-78, -18);
      ctx.bezierCurveTo(-98, -32, -116, -56, -128, -74);
      ctx.quadraticCurveTo(-146, -84, -146, -60);
      ctx.bezierCurveTo(-144, -36, -130, -14, -120, 0);
      ctx.bezierCurveTo(-128, 12, -136, 28, -138, 44);
      ctx.quadraticCurveTo(-140, 62, -124, 54);
      ctx.bezierCurveTo(-108, 42, -92, 28, -78, 18);
      ctx.closePath();
    };
    ctx.save(); ctx.translate(-86, 0); ctx.rotate(tailA); ctx.translate(86, 0);
    shape(ctx, tail, B, B_S, 5, 6);
    ctx.restore();
    // dorsal fin + far pectoral fin (behind body)
    const dorsal = () => { ctx.moveTo(-26, -50); ctx.bezierCurveTo(-28, -76, -34, -96, -40, -110); ctx.quadraticCurveTo(-34, -122, -20, -112); ctx.bezierCurveTo(2, -96, 22, -78, 32, -60); ctx.closePath(); };
    shape(ctx, dorsal, B, B_S, 6, 4);
    const pec = (bx, by, tx, ty) => () => { ctx.moveTo(bx - 22, by - 8); ctx.bezierCurveTo(bx - 28, by + 20, tx - 14, ty - 8, tx - 4, ty + 2); ctx.quadraticCurveTo(tx + 8, ty + 10, tx + 18, ty - 4); ctx.bezierCurveTo(bx + 14, by + 24, bx + 22, by + 10, bx + 22, by - 8); ctx.closePath(); };
    shape(ctx, pec(34, 46, 10 + wig * 2, 84), B_S, null, 0, 0);
    // body: chunky plush torpedo with a blunt snout
    const body = () => {
      ctx.moveTo(124, 4);
      ctx.bezierCurveTo(122, -40, 86, -68, 34, -68);
      ctx.bezierCurveTo(-12, -68, -56, -50, -88, -22);
      ctx.quadraticCurveTo(-100, -4, -88, 18);
      ctx.bezierCurveTo(-56, 48, -6, 66, 44, 64);
      ctx.bezierCurveTo(96, 62, 126, 42, 124, 4);
      ctx.closePath();
    };
    ctx.beginPath(); body(); ctx.fillStyle = B; ctx.fill();
    ctx.save(); ctx.clip();
    const bellyLine = () => { ctx.moveTo(132, -4); ctx.bezierCurveTo(104, 6, 60, 6, 0, 8); ctx.bezierCurveTo(-40, 9, -74, 2, -106, -6); };
    ctx.beginPath(); bellyLine(); ctx.lineTo(-106, 100); ctx.lineTo(132, 100); ctx.closePath(); ctx.fillStyle = W; ctx.fill();
    // plush shading: soft top highlight, shadow along the underside
    ctx.fillStyle = 'rgba(255,255,255,0.22)'; ctx.beginPath(); ell(ctx, 26, -48, 74, 13, -0.04); ctx.fill();
    ctx.translate(FLIP ? -6 : 6, -11);
    ctx.beginPath(); ctx.rect(-170, -130, 340, 260); body(); ctx.fillStyle = 'rgba(70,95,125,0.22)'; ctx.fill('evenodd');
    ctx.restore();
    // stitch seam along the belly line
    ctx.save(); ctx.beginPath(); body(); ctx.clip();
    ctx.setLineDash([7, 6]); ctx.beginPath(); bellyLine(); ctx.strokeStyle = 'rgba(60,85,115,0.55)'; ctx.lineWidth = 2.4; ctx.stroke(); ctx.setLineDash([]);
    ctx.restore();
    ctx.beginPath(); body(); ctx.strokeStyle = INK; ctx.lineWidth = LW; ctx.stroke();
    // gills
    ctx.strokeStyle = 'rgba(40,60,85,0.5)'; ctx.lineWidth = 2.6; ctx.beginPath();
    for (const gx of [50, 40, 30]) { ctx.moveTo(gx + 3, -30); ctx.quadraticCurveTo(gx - 4, -14, gx + 1, 0); }
    ctx.stroke();
    // mouth: wide, slightly open smile with a pink inside
    const mo = () => { ctx.moveTo(123, 10); ctx.quadraticCurveTo(102, 28, 72, 22); ctx.quadraticCurveTo(96, 44 + wig, 120, 24); ctx.closePath(); };
    ctx.beginPath(); mo(); ctx.fillStyle = PK; ctx.fill(); ctx.strokeStyle = INK; ctx.lineWidth = 4; ctx.stroke();
    // eye: black bead, happy squint when squeezed
    if (sq > 0.6) {
      ctx.beginPath(); ctx.moveTo(72, -14); ctx.quadraticCurveTo(81, -28, 90, -14); ctx.strokeStyle = INK; ctx.lineWidth = 4.5; ctx.stroke();
    } else {
      ctx.fillStyle = INK; ctx.beginPath(); circ(ctx, 81, -17, 9); ctx.fill();
      ctx.fillStyle = WHITE; ctx.beginPath(); circ(ctx, 78, -20, 3); ctx.fill();
    }
    ctx.fillStyle = 'rgba(255,140,170,0.45)'; ctx.beginPath(); ell(ctx, 96, 2, 10, 5.5); ctx.fill();
    // near pectoral fin (front)
    shape(ctx, pec(58, 48, 32 - wig * 2, 94), B, B_S, 4, 5);
  } finally {
    FLIP = prevFlip;
    ctx.restore();
  }
}
