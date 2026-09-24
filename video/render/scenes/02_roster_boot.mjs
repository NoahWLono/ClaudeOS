import { createCanvas } from '@napi-rs/canvas';
import { W, H, C, clamp, lerp, ease, prog, pop, txt, rr, panel, actor, sectionCard, sparkle, rng, banner } from '../lib.mjs';

// ---------------- roster: fighting-game character select ----------------
const CARDS = [
  { id: 'femboy', name: 'socksd', line: 1, stats: [['SOCKS', 1, 'MAX'], ['CUTENESS', 0.99], ['UPTIME', 0.999, '99.9%']] },
  { id: 'wiki', name: 'WIKI ENJOYER', line: 2, stats: [['WIKI READ', 1, 'ALL x2'], ['FOCUS', 1, 'HYPER'], ['SMALL TALK', 0.12]] },
  { id: 'gamer', name: 'PACMANSLAYER', line: 3, stats: [['FPS', 0.95, '240'], ['RGB', 1, 'YES'], ['SLEEP', 0.08]] },
  { id: 'claude', name: 'OPUS 5.5', line: 4, stats: [['CONTEXT', 1, 'HUGE'], ['OPINIONS', 0.92], ['HANDS', 0, '0']] },
];
const LOCKED = ['gentoo', 'lfs', 'nix', 'winupdate'];
const _sil = {};
function silhouette(CH, id) {
  if (_sil[id]) return _sil[id];
  const c = createCanvas(300, 300), x = c.getContext('2d');
  CH.drawCharacter(x, id, { x: 150, y: 290, s: 0.62, t: 0 });
  x.globalCompositeOperation = 'source-atop'; x.fillStyle = '#05060F'; x.fillRect(0, 0, 300, 300);
  return (_sil[id] = c);
}

function drawRoster(ctx, t, S, CH) {
  ctx.fillStyle = '#0B1026'; ctx.fillRect(0, 0, W, H);
  // synthwave floor
  ctx.save(); ctx.strokeStyle = 'rgba(255,46,136,0.45)'; ctx.lineWidth = 2;
  const hz = 640;
  for (let i = -20; i <= 20; i++) { ctx.beginPath(); ctx.moveTo(W / 2 + i * 40, hz); ctx.lineTo(W / 2 + i * 260, H); ctx.stroke(); }
  for (let k = 0; k < 12; k++) { const z = ((k + (t * 1.5) % 1) / 12); const y = hz + Math.pow(z, 2.2) * (H - hz); ctx.globalAlpha = z; ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(W, y); ctx.stroke(); }
  ctx.restore();
  const g = ctx.createLinearGradient(0, 0, 0, hz); g.addColorStop(0, '#0B1026'); g.addColorStop(1, '#3A1250');
  ctx.fillStyle = g; ctx.fillRect(0, 0, W, hz);
  txt(ctx, 'CHOOSE YOUR FIGHTER', W / 2, 118, { fam: 'PressStart2P', size: 54, color: C.yellow, align: 'center', shadow: { color: '#FF2E88', dx: 6, dy: 6 } });
  const A = actor(ctx, CH, S, t);
  const cur = S.active(t);
  CARDS.forEach((cd, i) => {
    const x = 110 + i * 400, y = 170, w = 370, h = 590;
    const appear = pop(t, 0.2 + i * 0.12, 0.35);
    if (appear <= 0) return;
    const flipP = clamp((t - (S.L(cd.line) - 0.1)) / 0.4);
    const sx = Math.abs(Math.cos(flipP * Math.PI)) * appear;
    const front = flipP >= 0.5;
    const col = CH.CHAR_INFO?.[cd.id]?.color || C.orange;
    ctx.save(); ctx.translate(x + w / 2, y + h / 2); ctx.scale(Math.max(0.02, sx), appear); ctx.translate(-w / 2, -h / 2);
    panel(ctx, 0, 0, w, h, { fill: front ? '#151A33' : '#2A1F4A', stroke: front ? col : '#6A5ACD', lw: 6, r: 18, shadow: 'rgba(0,0,0,.6)' });
    if (!front) {
      txt(ctx, '?', w / 2, h / 2 + 50, { fam: 'PressStart2P', size: 150, color: '#6A5ACD', align: 'center' });
    } else {
      const talking = cur && cur.who === cd.id;
      ctx.save(); ctx.beginPath(); ctx.rect(6, 6, w - 12, 360); ctx.clip();
      const gg = ctx.createRadialGradient(w / 2, 220, 10, w / 2, 220, 240); gg.addColorStop(0, col + '66'); gg.addColorStop(1, col + '00');
      ctx.fillStyle = gg; ctx.fillRect(0, 0, w, 380);
      CH.drawCharacter(ctx, cd.id, { x: w / 2, y: 365, s: 0.78, t: t + i, talk: S.talk(cd.id, t), mood: talking ? 'excited' : 'happy', prop: cd.id === 'gamer' ? 'can' : cd.id === 'femboy' ? null : null });
      ctx.restore();
      txt(ctx, cd.name, w / 2, 410, { fam: 'PressStart2P', size: 22, color: col, align: 'center', maxW: w - 30 });
      cd.stats.forEach(([lab, v, str], j) => {
        const yy = 450 + j * 44;
        txt(ctx, lab, 22, yy + 18, { fam: 'PressStart2P', size: 13, color: '#C9C6E8' });
        const bx = 170, bw = 170, fill = v * ease.out(prog(t, S.L(cd.line) + 0.3 + j * 0.15, 0.6));
        ctx.fillStyle = '#05060F'; ctx.fillRect(bx, yy + 2, bw, 20);
        ctx.fillStyle = col; ctx.fillRect(bx, yy + 2, bw * fill, 20);
        ctx.strokeStyle = '#C9C6E8'; ctx.lineWidth = 2; ctx.strokeRect(bx, yy + 2, bw, 20);
        if (str) txt(ctx, str, bx + bw - 6, yy + 18, { fam: 'PressStart2P', size: 12, color: '#FFFFFF', align: 'right', stroke: '#05060F', sw: 4 });
      });
    }
    ctx.restore();
    // P1 selector
    if (cur && cur.who === cd.id && front) {
      const b = (Math.sin(t * 10) + 1) * 4;
      ctx.save(); ctx.strokeStyle = C.yellow; ctx.lineWidth = 6; ctx.setLineDash([22, 12]); ctx.lineDashOffset = -t * 60;
      rr(ctx, x - 12 - b, y - 12 - b, w + 24 + 2 * b, h + 24 + 2 * b, 24); ctx.stroke(); ctx.restore();
      banner(ctx, x + w / 2, y - 6, 110, 44, C.yellow, 'P1', { fam: 'PressStart2P', size: 22, color: C.ink });
    }
  });
  // locked hecklers
  LOCKED.forEach((id, i) => {
    const k = pop(t, S.L(4) + 0.3 + i * 0.15, 0.3);
    if (k <= 0) return;
    const x = 1720, y = 170 + i * 150, w = 170, h = 136;
    ctx.save(); ctx.translate(x + w / 2, y + h / 2); ctx.scale(k, k); ctx.translate(-w / 2, -h / 2);
    panel(ctx, 0, 0, w, h, { fill: '#1A1030', stroke: '#FF2E88', lw: 4, r: 14 });
    ctx.save(); ctx.beginPath(); ctx.rect(4, 4, w - 8, h - 8); ctx.clip();
    ctx.drawImage(silhouette(CH, id), -65, -120, 300, 300); ctx.restore();
    txt(ctx, '???', w / 2, h - 14, { fam: 'PressStart2P', size: 18, color: '#FF2E88', align: 'center', stroke: '#05060F', sw: 5 });
    ctx.restore();
  });
  if (t > S.L(4) + 0.3) txt(ctx, 'HECKLERS', 1805, 158, { fam: 'PressStart2P', size: 16, color: '#FF2E88', align: 'center', alpha: clamp((t - S.L(4)) * 2) });
}

// ---------------- boot chain: the five layers ----------------
const LAYERS = [
  { name: 'FIRMWARE', sub: 'UEFI', icon: '⚡', col: '#2B4C7E', job: 'JOB: find something bootable' },
  { name: 'BOOTLOADER', sub: 'systemd-boot / GRUB', icon: '🥾', col: '#1F6FA8', job: 'JOB: load the kernel' },
  { name: 'KERNEL', sub: 'linux', icon: '🧠', col: '#1793D1', job: 'JOB: talk to the hardware' },
  { name: 'INIT · PID 1', sub: 'systemd', icon: '🌳', col: '#C15F3C', job: 'JOB: start everything else' },
  { name: 'USERSPACE', sub: 'shells, tools, desktops, games', icon: '🪟', col: '#D97757', job: 'JOB: be useful' },
  { name: 'YOU', sub: 'the point of all this', icon: '🫵', col: '#E8A33D', job: 'YOU ARE HERE' },
];
function blueprint(ctx) {
  ctx.fillStyle = '#0E2A47'; ctx.fillRect(0, 0, W, H);
  ctx.strokeStyle = 'rgba(240,238,230,0.07)'; ctx.lineWidth = 1;
  for (let x = 0; x < W; x += 40) { ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, H); ctx.stroke(); }
  for (let y = 0; y < H; y += 40) { ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(W, y); ctx.stroke(); }
  ctx.strokeStyle = 'rgba(240,238,230,0.14)';
  for (let x = 0; x < W; x += 200) { ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, H); ctx.stroke(); }
  for (let y = 0; y < H; y += 200) { ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(W, y); ctx.stroke(); }
}
function drawBoot(ctx, t, S, CH) {
  blueprint(ctx);
  const A = actor(ctx, CH, S, t);
  const layerAt = [S.L(1) + 1.2, S.L(2) + 0.3, S.L(3) + 0.3, S.L(4) + 0.5, S.L(5) + 0.3, S.L(5) + 3.0];
  // power button (line 0)
  const pb = prog(t, S.L(0), 0.4), press = t > S.L(0) + 3.0 ? 0.9 : 1;
  const pbOut = ease.inOut(prog(t, S.L(1), 0.8));
  if (pb > 0) {
    const px = lerp(960, 110, pbOut), py = lerp(470, 860, pbOut), r = lerp(170, 50, pbOut) * ease.back(pb) * press;
    ctx.save(); ctx.translate(px, py);
    if (t > S.L(0) + 3.0) { ctx.shadowColor = C.green; ctx.shadowBlur = 40; }
    ctx.fillStyle = C.ink; ctx.beginPath(); ctx.arc(8, 10, r, 0, 7); ctx.fill();
    ctx.fillStyle = t > S.L(0) + 3.0 ? '#2E7D32' : '#37474F'; ctx.beginPath(); ctx.arc(0, 0, r, 0, 7); ctx.fill();
    ctx.shadowBlur = 0; ctx.strokeStyle = C.cream; ctx.lineWidth = r * 0.14; ctx.lineCap = 'round';
    ctx.beginPath(); ctx.arc(0, 0, r * 0.5, -Math.PI / 2 + 0.6, -Math.PI / 2 - 0.6 + Math.PI * 2); ctx.stroke();
    ctx.beginPath(); ctx.moveTo(0, -r * 0.62); ctx.lineTo(0, -r * 0.12); ctx.stroke();
    ctx.restore();
    if (t > S.L(0) + 3.0 && t < S.L(1) + 0.5) for (let i = 0; i < 8; i++) sparkle(ctx, px + Math.cos(i * 0.8 + t * 3) * r * 1.4, py + Math.sin(i * 0.8 + t * 3) * r * 1.4, 18, C.yellow, t * 4);
  }
  // tower
  const X = 200, LW = 800, LH = 100, GAP = 12, BASE = 820;
  const skill = t > S.L(6);
  LAYERS.forEach((L, i) => {
    const a = layerAt[i];
    if (t < a) return;
    const q = ease.out(clamp((t - a) / 0.45));
    const y = BASE - (i + 1) * LH - i * GAP;
    const yy = lerp(-150, y, q) + (q >= 1 ? 0 : 0);
    const squash = t - a < 0.6 ? 1 + Math.sin(clamp((t - a - 0.45) / 0.15) * Math.PI) * 0.06 : 1;
    ctx.save(); ctx.translate(X + LW / 2, yy + LH); ctx.scale(1 / squash, squash); ctx.translate(-(X + LW / 2), -(yy + LH));
    const w = LW - i * 40, x = X + i * 20;
    panel(ctx, x, yy, w, LH, { fill: L.col, stroke: C.cream, lw: 4, r: 16, shadow: 'rgba(0,0,0,.45)' });
    txt(ctx, L.icon, x + 30, yy + 68, { size: 50, fam: 'Noto Color Emoji' });
    txt(ctx, L.name, x + 110, yy + 52, { fam: 'Anton', size: 46, color: C.cream, track: 2 });
    txt(ctx, L.sub, x + 110, yy + 84, { fam: 'Nunito-800', size: 24, color: 'rgba(240,238,230,.85)' });
    txt(ctx, `L${i + 1}`, x + w - 24, yy + 64, { fam: 'Anton', size: 44, color: 'rgba(240,238,230,.35)', align: 'right' });
    if (skill && i < 5) {
      const unlocked = t > S.L(7) + 1.2 + i * 0.25;
      txt(ctx, unlocked ? '🔓' : '🔒', x + w - 100, yy + 68, { size: 44, fam: 'Noto Color Emoji' });
    }
    ctx.restore();
  });
  // job label for the newest layer
  const idx = layerAt.filter(a => t >= a).length - 1;
  if (idx >= 0 && t < S.L(6)) {
    const L = LAYERS[idx], y = BASE - (idx + 1) * LH - idx * GAP;
    const k = pop(t, layerAt[idx] + 0.35, 0.3);
    ctx.save(); ctx.translate(X + LW - idx * 20 + 40, y + LH / 2); ctx.scale(k, k);
    panel(ctx, 0, -34, 440, 68, { fill: C.cream, r: 34, lw: 4 });
    txt(ctx, L.job, 220, 11, { fam: 'Nunito-900', size: 30, color: C.ink, align: 'center', maxW: 400 });
    ctx.fillStyle = C.cream; ctx.beginPath(); ctx.moveTo(0, -12); ctx.lineTo(-30, 0); ctx.lineTo(0, 12); ctx.fill();
    ctx.restore();
  }
  // process tree (PID 1 line)
  const pt = prog(t, S.L(4) + 2.5, 0.5) * (1 - prog(t, S.L(5) + 0.2, 0.3));
  if (pt > 0) {
    ctx.save(); ctx.globalAlpha = pt;
    const nodes = [['systemd (1)', 1400, 150], ['journald', 1150, 250], ['NetworkManager', 1420, 250], ['login', 1720, 250], ['bash', 1720, 340], ['nvim', 1600, 430], ['steam', 1830, 430]];
    const edges = [[0, 1], [0, 2], [0, 3], [3, 4], [4, 5], [4, 6]];
    ctx.strokeStyle = C.cream; ctx.lineWidth = 3;
    for (const [a, b] of edges) { ctx.beginPath(); ctx.moveTo(nodes[a][1], nodes[a][2] + 24); ctx.lineTo(nodes[b][1], nodes[b][2] - 24); ctx.stroke(); }
    nodes.forEach(([n, x, y], i) => { ctx.font = '26px JBM-800'; const w = ctx.measureText(n).width + 30; panel(ctx, x - w / 2, y - 24, w, 48, { fill: i ? '#1F6FA8' : C.deep, stroke: C.cream, lw: 3, r: 12, shadow: 'rgba(0,0,0,.4)' }); txt(ctx, n, x, y + 9, { fam: 'JBM-800', size: 26, color: C.cream, align: 'center' }); });
    ctx.restore();
  }
  // tech tree overlay
  if (skill) {
    const k = pop(t, S.L(6) + 0.1, 0.4);
    ctx.save(); ctx.translate(600, 70); ctx.scale(k, k); banner(ctx, 0, 0, 520, 70, C.yellow, 'TECH TREE', { fam: 'PressStart2P', size: 34, color: C.ink, rot: -0.02 }); ctx.restore();
    const k2 = pop(t, S.L(7) + 0.8, 0.4);
    if (k2 > 0) { ctx.save(); ctx.translate(1420, 250); ctx.scale(k2, k2); ctx.rotate(0.05); txt(ctx, '+5 SKILL POINTS', 0, 0, { fam: 'PressStart2P', size: 44, color: C.green, align: 'center', stroke: C.ink, sw: 10 }); ctx.restore(); }
  }
  A('claude', { x: lerp(1690, 1500, ease.inOut(prog(t, S.L(6) - 0.4, 0.5))), y: 900, s: 1.0, enter: S.L(0) - 0.2, look: -0.6, mood: t > S.L(7) ? 'smug' : 'happy', prop: null });
  A('gamer', { x: 1790, y: 900, s: 0.85, enter: S.L(6) - 0.2, flip: true, mood: 'excited', look: -0.5 });
  sectionCard(ctx, t, ...S.card);
}

export default {
  id: ['roster', 'boot_chain'],
  render(ctx, t, S, CH) { (S.id === 'roster' ? drawRoster : drawBoot)(ctx, t, S, CH); },
  cues(S) {
    if (S.id === 'roster') return [
      ...CARDS.map((cd) => ({ t: S.L(cd.line) - 0.1, name: 'swoosh_up', gain: 0.4 })),
      ...CARDS.map((cd, i) => ({ t: 0.2 + i * 0.12, name: 'pop', gain: 0.35 })),
      ...LOCKED.map((_, i) => ({ t: S.L(4) + 0.3 + i * 0.15, name: 'glitch', gain: 0.2 })),
    ];
    const a = [S.L(1) + 1.2, S.L(2) + 0.3, S.L(3) + 0.3, S.L(4) + 0.5, S.L(5) + 0.3, S.L(5) + 3.0];
    return [{ t: S.L(0) + 3.0, name: 'boot_chime', gain: 0.6 }, ...a.map(x => ({ t: x + 0.4, name: 'stamp', gain: 0.45 })), { t: S.L(7) + 0.8, name: 'levelup', gain: 0.6 }];
  },
};
