import { W, H, C, clamp, lerp, ease, prog, pop, txt, rr, panel, actor, sectionCard, sunburst, halftone, banner, burst, stamp, sparkle, shake } from '../lib.mjs';

// ---------------- objection: the hecklers ----------------
function bar(ctx, x, y, w, p, label, sub, col = C.lav) {
  panel(ctx, x, y, w, 130, { fill: '#15101F', stroke: col, lw: 4, r: 14 });
  txt(ctx, label, x + 22, y + 40, { fam: 'JBM-800', size: 24, color: '#E8E2F8', maxW: w - 40 });
  ctx.fillStyle = '#05030A'; rr(ctx, x + 22, y + 58, w - 44, 30, 8); ctx.fill();
  ctx.fillStyle = col; rr(ctx, x + 22, y + 58, (w - 44) * p, 30, 8); ctx.fill();
  txt(ctx, sub, x + 22, y + 116, { fam: 'JBM-400', size: 21, color: '#A99FC4', maxW: w - 40 });
}
function drawObjection(ctx, t, S, CH) {
  const L = S.L, E = S.E;
  // speed-line background
  ctx.fillStyle = '#240A12'; ctx.fillRect(0, 0, W, H);
  ctx.save(); ctx.translate(W / 2, H / 2);
  for (let i = 0; i < 48; i++) { const a = i / 48 * Math.PI * 2 + t * 0.05; ctx.fillStyle = i % 2 ? '#2E0D17' : '#3A111D'; ctx.beginPath(); ctx.moveTo(0, 0); ctx.lineTo(Math.cos(a) * 2000, Math.sin(a) * 2000); ctx.lineTo(Math.cos(a + 0.07) * 2000, Math.sin(a + 0.07) * 2000); ctx.fill(); }
  ctx.restore();
  const hits = [L(0), L(1), L(2)];
  const lastHit = hits.filter(h => t >= h).pop();
  const [sx, sy] = lastHit != null && t - lastHit < 0.35 ? shake(t, 14 * (1 - (t - lastHit) / 0.35)) : [0, 0];
  ctx.save(); ctx.translate(sx, sy);
  const A = actor(ctx, CH, S, t);
  const claudeTime = t > L(3) - 0.3;
  const dim = claudeTime && t < L(6) ? 0.45 : 1;
  ctx.save(); ctx.globalAlpha = dim;
  A('gentoo', { x: 300, y: 900, s: 0.95, enter: L(0) - 0.15, mood: t > L(6) ? 'sad' : S.speaking('gentoo', t) ? 'angry' : 'smug', look: 0.5 });
  A('lfs', { x: 960, y: 820, s: 0.8, enter: L(1) - 0.15, mood: S.speaking('lfs', t) ? 'smug' : 'neutral' });
  A('nix', { x: 1620, y: 900, s: 0.95, enter: L(2) - 0.15, mood: 'smug', look: -0.5, flip: true });
  ctx.restore();
  // shout bursts
  if (t > L(0) && t < L(0) + 1.6) burst(ctx, 560, 240, 820, 300, C.red, 'OBJECTION!', { rot: -0.08, seed: 3 });
  if (t > L(1) && t < L(1) + 1.3) burst(ctx, 1000, 250, 700, 260, C.yellow, 'AMATEURS.', { rot: 0.05, seed: 9, color: C.ink });
  if (t > L(2) && t < L(2) + 1.3) burst(ctx, 1380, 250, 820, 280, '#7EBAE4', 'DECLARATIVE.', { rot: -0.04, seed: 5, color: C.ink });
  // gentoo compile bar
  if (t > L(0) + 1.6 && t < L(1)) bar(ctx, 470, 220, 760, 0.31 + (t - L(0)) * 0.002, 'emerge --ask www-client/chromium', '[31%]  ETA: 3 days, 4 hours  (USE="-* lto pgo")');
  // lfs recursion
  if (t > L(1) + 1.3 && t < L(2)) {
    const n = Math.min(5, Math.floor((t - L(1) - 1.3) * 3) + 1);
    for (let i = 0; i < n; i++) {
      const w = 340 - i * 50, x = 1000 - w / 2 + i * 0, y = 160 + i * 34;
      panel(ctx, 1000 - w / 2 + (i - 2) * 120 + 240, 150 + i * 30, w * 0.8, 70, { fill: '#F5C518', r: 12, lw: 4 });
      txt(ctx, i < 4 ? 'gcc' : '…', 1000 + (i - 2) * 120 + 240, 198 + i * 30, { fam: 'JBM-800', size: 34, color: C.ink, align: 'center' });
      if (i) txt(ctx, 'built by ←', 1000 + (i - 2) * 120 + 90, 175 + i * 30, { fam: 'Nunito-800', size: 18, color: '#F5C518', align: 'center' });
    }
  }
  // nix config
  if (t > L(2) + 1.3 && t < L(3)) {
    panel(ctx, 1010, 120, 860, 330, { fill: '#0F1B2B', stroke: '#7EBAE4', lw: 4, r: 16 });
    const code = ['# configuration.nix', '{ pkgs, ... }: {', '  environment.systemPackages = [ pkgs.neovim ];', '  services.openssh.enable = true;', '  programs.steam.enable = true;', '}'];
    code.forEach((l, i) => txt(ctx, l, 1040, 170 + i * 46, { fam: 'JBM-800', size: 26, color: i === 0 ? '#6C8BA8' : '#CFE6FA', maxW: 800 }));
    txt(ctx, '$ nixos-rebuild switch  ✓ identical, anywhere', 1040, 432, { fam: 'JBM-800', size: 22, color: '#8CE99A' });
  }
  // Claude's honest scoreboard
  if (claudeTime) {
    A('claude', { x: 960, y: 930, s: 1.0, enter: L(3) - 0.3, mood: t > L(5) ? 'smug' : 'neutral' });
    const rows = [
      ['BUILD EVERY BYTE YOURSELF', 'Linux From Scratch', '#F5C518', L(4) + 0.3],
      ['REPRODUCIBILITY', 'NixOS', '#7EBAE4', L(4) + S.lines[4].dur * 0.55],
      ['SEE EVERY LAYER, DONE BY LUNCH', 'Arch', C.blue, L(5) + 0.4],
    ];
    const k0 = pop(t, L(3) + 0.8, 0.4);
    if (k0 > 0) {
      ctx.save(); ctx.translate(W / 2, 110); ctx.scale(k0, k0);
      txt(ctx, 'FAIR POINTS. SCOREBOARD:', 0, 0, { fam: 'Anton', size: 56, color: C.cream, align: 'center', stroke: C.ink, sw: 8, track: 2 });
      ctx.restore();
    }
    rows.forEach(([q, who, col, at], i) => {
      const k = ease.out(prog(t, at, 0.4)); if (k <= 0) return;
      const y = 150 + i * 105;
      ctx.save(); ctx.globalAlpha = k; ctx.translate((1 - k) * -80, 0);
      panel(ctx, 360, y, 1200, 88, { fill: C.cream, r: 16 });
      txt(ctx, q, 390, y + 57, { fam: 'Anton', size: 40, color: C.ink, track: 1, maxW: 700 });
      ctx.fillStyle = col; rr(ctx, 1110, y + 12, 430, 64, 32); ctx.fill();
      txt(ctx, '🏆 ' + who, 1325, y + 56, { fam: 'Nunito-900', size: 34, color: C.ink, align: 'center', maxW: 400 });
      ctx.restore();
    });
  }
  if (t > L(6)) bar(ctx, 470, 480, 980, clamp(0.02 + (t - L(6)) * 0.002), 'emerge --ask food/lunch', '[2%]  started: Tuesday  ·  ETA: Tuesday (a later one)', C.lav);
  ctx.restore();
}

// ---------------- principles: five propaganda posters ----------------
const POSTERS = [
  { n: 1, title: 'SIMPLICITY', slogan: 'UPSTREAM, UNMODIFIED.', bg: C.blue, fg: C.cream },
  { n: 2, title: 'MODERNITY', slogan: 'NO VERSIONS. ONLY THE UPDATE.', bg: C.orange, fg: C.cream },
  { n: 3, title: 'PRAGMATISM', slogan: 'TECHNICAL MERIT OVER IDEOLOGY.', bg: '#2A2A28', fg: C.yellow },
  { n: 4, title: 'USER CENTRALITY', slogan: 'USER-CENTRIC, NOT USER-FRIENDLY.', bg: '#B8406E', fg: C.cream },
  { n: 5, title: 'VERSATILITY', slogan: 'BUILD IT INTO ANYTHING.', bg: '#1D8A7E', fg: C.cream },
];
function box(ctx, x, y, w, h, fill, label, size = 36, fg = C.ink) { panel(ctx, x - w / 2, y - h / 2, w, h, { fill, r: 14, lw: 5 }); txt(ctx, label, x, y + size * 0.36, { fam: 'Anton', size, color: fg, align: 'center', maxW: w - 20, track: 1 }); }
function art(ctx, n, t, CH) {
  // drawn inside a 820x420 area centered at (0,0)
  if (n === 1) {
    box(ctx, -270, -80, 240, 110, C.cream, 'UPSTREAM'); box(ctx, 270, -80, 200, 110, C.yellow, 'YOU');
    ctx.strokeStyle = C.cream; ctx.lineWidth = 14; ctx.beginPath(); ctx.moveTo(-140, -80); ctx.lineTo(150, -80); ctx.stroke();
    ctx.fillStyle = C.cream; ctx.beginPath(); ctx.moveTo(170, -80); ctx.lineTo(130, -110); ctx.lineTo(130, -50); ctx.fill();
    ctx.strokeStyle = 'rgba(240,238,230,.5)'; ctx.lineWidth = 8; ctx.beginPath(); ctx.moveTo(-270, -20);
    for (let i = 0; i < 12; i++) ctx.bezierCurveTo(-240 + i * 45, 120, -200 + i * 45, -30, -180 + i * 45, 90);
    ctx.stroke();
    txt(ctx, 'distro patches', 0, 170, { fam: 'Nunito-900', size: 32, color: 'rgba(240,238,230,.8)', align: 'center' });
    txt(ctx, '✗', 0, 90, { fam: 'Nunito-900', size: 150, color: C.red, align: 'center', stroke: C.ink, sw: 8 });
  } else if (n === 2) {
    ['v12', 'v13', 'v14'].forEach((v, i) => { ctx.save(); ctx.translate(-300 + i * 110, -60 + i * 16); ctx.rotate(-0.2 + i * 0.12); box(ctx, 0, 0, 120, 140, C.cream, v, 44); ctx.restore(); });
    txt(ctx, '✗', -190, 0, { fam: 'Nunito-900', size: 210, color: C.red, align: 'center', stroke: C.ink, sw: 8 });
    ctx.save(); ctx.translate(210, -10); ctx.rotate(t * 2.2);
    ctx.lineWidth = 22; ctx.strokeStyle = C.cream; ctx.beginPath(); ctx.arc(0, 0, 130, 0.3, Math.PI * 1.75); ctx.stroke();
    ctx.fillStyle = C.cream; ctx.beginPath(); const a = Math.PI * 1.75; ctx.moveTo(Math.cos(a) * 170, Math.sin(a) * 170); ctx.lineTo(Math.cos(a) * 90, Math.sin(a) * 90); ctx.lineTo(Math.cos(a + 0.45) * 130, Math.sin(a + 0.45) * 130); ctx.fill();
    ctx.restore();
    txt(ctx, 'pacman -Syu', 210, 20, { fam: 'JBM-800', size: 34, color: C.ink, align: 'center' });
  } else if (n === 3) {
    const tilt = 0.22 + Math.sin(t * 2) * 0.03;
    ctx.fillStyle = C.yellow; ctx.fillRect(-12, -120, 24, 280); ctx.fillRect(-120, 150, 240, 24);
    ctx.save(); ctx.translate(0, -120); ctx.rotate(tilt);
    ctx.fillRect(-320, -10, 640, 20);
    for (const [sx, lab, heavy] of [[-300, 'TECHNICAL MERIT', 1], [300, 'IDEOLOGY', 0]]) {
      ctx.save(); ctx.translate(sx, 0); ctx.rotate(-tilt);
      ctx.strokeStyle = C.yellow; ctx.lineWidth = 5; ctx.beginPath(); ctx.moveTo(0, 0); ctx.lineTo(-90, 110); ctx.moveTo(0, 0); ctx.lineTo(90, 110); ctx.stroke();
      ctx.fillStyle = C.yellow; ctx.beginPath(); ctx.ellipse(0, 115, 120, 22, 0, 0, 7); ctx.fill();
      if (heavy) { box(ctx, 0, 65, 190, 80, C.cream, 'MERIT', 40); } else { txt(ctx, 'ideology', 0, 95, { fam: 'Playfair-700i', size: 30, color: C.cream, align: 'center' }); }
      ctx.restore();
    }
    ctx.restore();
    txt(ctx, 'proprietary GPU drivers? in the repos ✓', 0, 215, { fam: 'Nunito-900', size: 30, color: C.cream, align: 'center' });
  } else if (n === 4) {
    ctx.save(); for (let i = 0; i < 16; i++) { ctx.rotate(Math.PI / 8); ctx.fillStyle = 'rgba(255,255,255,0.14)'; ctx.beginPath(); ctx.moveTo(0, 0); ctx.lineTo(600, -60); ctx.lineTo(600, 60); ctx.fill(); } ctx.restore();
    ctx.fillStyle = C.ink; ctx.beginPath(); ctx.arc(0, -110, 62, 0, 7); ctx.fill();
    ctx.beginPath(); ctx.moveTo(-130, 170); ctx.lineTo(-90, -30); ctx.quadraticCurveTo(0, -60, 90, -30); ctx.lineTo(130, 170); ctx.fill();
    ctx.fillStyle = C.yellow; ctx.fillRect(-60, 40, 120, 70); txt(ctx, 'root', 0, 88, { fam: 'JBM-800', size: 38, color: C.ink, align: 'center' });
    txt(ctx, 'YOU (THE ADMIN)', 0, 215, { fam: 'Anton', size: 40, color: C.cream, align: 'center', track: 2 });
    ctx.save(); ctx.translate(300, -60); ctx.rotate(0.15); txt(ctx, '"friendly"', 0, 0, { fam: 'Playfair-700i', size: 42, color: 'rgba(240,238,230,.75)', align: 'center' }); ctx.fillStyle = C.red; ctx.fillRect(-110, -14, 220, 8); ctx.restore();
  } else if (n === 5) {
    // server
    ctx.save(); ctx.translate(-270, 0);
    for (let i = 0; i < 4; i++) { panel(ctx, -90, -150 + i * 72, 180, 60, { fill: '#2A2A28', stroke: C.cream, lw: 4, r: 8, shadow: 'rgba(0,0,0,.3)' }); ctx.fillStyle = Math.floor(t * 4 + i) % 3 ? C.green : '#115511'; ctx.beginPath(); ctx.arc(60, -120 + i * 72, 8, 0, 7); ctx.fill(); }
    txt(ctx, 'SERVER', 0, 190, { fam: 'Anton', size: 38, color: C.cream, align: 'center' }); ctx.restore();
    // handheld
    if (CH.drawHandheld) CH.drawHandheld(ctx, 0, -10, 260, t);
    txt(ctx, 'GAMING RIG', 0, 190, { fam: 'Anton', size: 38, color: C.cream, align: 'center' });
    // laptop with tabs
    ctx.save(); ctx.translate(280, 0);
    panel(ctx, -120, -140, 240, 160, { fill: C.cream, r: 10, lw: 5 });
    for (let i = 0; i < 12; i++) { ctx.fillStyle = i % 2 ? '#C7C2B5' : '#DDD8CB'; ctx.fillRect(-112 + i * 19, -132, 17, 16); }
    ctx.fillStyle = '#2A2A28'; ctx.beginPath(); ctx.moveTo(-150, 30); ctx.lineTo(150, 30); ctx.lineTo(125, 10); ctx.lineTo(-125, 10); ctx.fill();
    ctx.fillStyle = C.red; ctx.beginPath(); ctx.arc(110, -140, 34, 0, 7); ctx.fill(); txt(ctx, '47', 110, -128, { fam: 'Anton', size: 36, color: C.cream, align: 'center' });
    txt(ctx, 'LAPTOP', 0, 190, { fam: 'Anton', size: 38, color: C.cream, align: 'center' }); ctx.restore();
  }
}
function poster(ctx, P, t, CH) {
  const w = 900, h = 700;
  ctx.fillStyle = C.ink; ctx.fillRect(-w / 2 + 16, -h / 2 + 16, w, h);
  ctx.fillStyle = P.bg; ctx.fillRect(-w / 2, -h / 2, w, h);
  ctx.save(); ctx.beginPath(); ctx.rect(-w / 2, -h / 2, w, h); ctx.clip();
  ctx.globalAlpha = 0.12; ctx.fillStyle = '#000'; for (let i = -10; i < 20; i++) { ctx.beginPath(); ctx.moveTo(-w / 2 + i * 90, -h / 2); ctx.lineTo(-w / 2 + i * 90 + 45, -h / 2); ctx.lineTo(-w / 2 + i * 90 - 300, h / 2); ctx.lineTo(-w / 2 + i * 90 - 345, h / 2); ctx.fill(); }
  ctx.restore();
  ctx.strokeStyle = P.fg; ctx.lineWidth = 6; ctx.strokeRect(-w / 2 + 22, -h / 2 + 22, w - 44, h - 44);
  txt(ctx, String(P.n), -w / 2 + 60, -h / 2 + 170, { fam: 'Anton', size: 170, color: P.fg, stroke: C.ink, sw: 10 });
  txt(ctx, P.title, 60, -h / 2 + 130, { fam: 'Anton', size: 104, color: P.fg, align: 'center', stroke: C.ink, sw: 10, maxW: 660, track: 3 });
  ctx.save(); ctx.translate(0, 30); art(ctx, P.n, t, CH); ctx.restore();
  ctx.fillStyle = C.ink; ctx.fillRect(-w / 2, h / 2 - 96, w, 96);
  txt(ctx, P.slogan, 0, h / 2 - 32, { fam: 'BebasNeue', size: 60, color: P.fg, align: 'center', maxW: w - 60, track: 2 });
}
function drawPrinciples(ctx, t, S, CH) {
  const L = S.L;
  sunburst(ctx, 1010, 480, 24, C.cream, '#E6E1D3', t * 0.03);
  halftone(ctx, 'rgba(20,20,19,0.08)', 16);
  const A = actor(ctx, CH, S, t);
  const tags = [1, 2, 3, 4, 5].map(i => S.tag('p' + i));
  const cur = tags.filter(x => t >= x - 0.1).length - 1;
  // intro shields
  if (cur < 0) {
    [1, 2, 3, 4, 5].forEach((n, i) => {
      const k = pop(t, L(0) + 0.8 + i * 0.35, 0.4); if (k <= 0) return;
      ctx.save(); ctx.translate(560 + i * 225, 440); ctx.scale(k, k);
      ctx.fillStyle = C.ink; ctx.beginPath(); ctx.moveTo(-90 + 8, -110 + 8); ctx.lineTo(90 + 8, -110 + 8); ctx.lineTo(90 + 8, 20 + 8); ctx.lineTo(8, 130 + 8); ctx.lineTo(-90 + 8, 20 + 8); ctx.fill();
      ctx.fillStyle = POSTERS[i].bg; ctx.beginPath(); ctx.moveTo(-90, -110); ctx.lineTo(90, -110); ctx.lineTo(90, 20); ctx.lineTo(0, 130); ctx.lineTo(-90, 20); ctx.fill(); ctx.lineWidth = 6; ctx.strokeStyle = C.ink; ctx.stroke();
      txt(ctx, String(n), 0, 40, { fam: 'Anton', size: 130, color: C.cream, align: 'center', stroke: C.ink, sw: 8 });
      ctx.restore();
    });
    const k = pop(t, L(0) + 0.3, 0.4);
    ctx.save(); ctx.translate(1010, 190); ctx.scale(k, k); banner(ctx, 0, 0, 900, 100, C.deep, 'COMMIT THEM TO MEMORY, CITIZEN', { size: 62, rot: -0.02 }); ctx.restore();
  } else {
    for (let i = Math.max(0, cur - 1); i <= cur; i++) {
      const a = tags[i];
      const inK = ease.out(prog(t, a - 0.1, 0.45));
      const outK = i < cur ? ease.in(prog(t, tags[i + 1] - 0.1, 0.45)) : 0;
      if (outK >= 1) continue;
      ctx.save();
      ctx.translate(lerp(W + 600, 1010, inK) + lerp(0, -1500, outK), 450);
      ctx.rotate(lerp(0.3, (i % 2 ? 0.015 : -0.02), inK) - outK * 0.3);
      ctx.scale(0.92, 0.92);
      poster(ctx, POSTERS[i], t, CH);
      ctx.restore();
      stamp(ctx, 1420, 150, 0.6, 'OFFICIAL', t - (a + 0.3), C.red, 0.18);
    }
  }
  A('announcer', { x: 250, y: 930, s: 1.0, mood: S.speaking('announcer', t) ? 'angry' : 'neutral', look: 0.6 });
  A('claude', { x: 1720, y: 950, s: 0.75, mood: 'happy', look: -0.6, enter: S.L(2) - 0.3 });
  A('wiki', { x: 1580, y: 960, s: 0.72, enter: S.L(11) - 0.3, mood: 'smug', prop: 'tabs', look: -0.3 });
  sectionCard(ctx, t, ...S.card);
}

export default {
  id: ['objection', 'principles'],
  render(ctx, t, S, CH) { (S.id === 'objection' ? drawObjection : drawPrinciples)(ctx, t, S, CH); },
  cues(S) {
    if (S.id === 'objection') return [
      { t: S.L(3) + 0.8, name: 'pop', gain: 0.5 },
      { t: S.L(4) + 0.3, name: 'ding', gain: 0.4 }, { t: S.L(4) + S.lines[4].dur * 0.55, name: 'ding', gain: 0.4 }, { t: S.L(5) + 0.4, name: 'fanfare', gain: 0.5 },
    ];
    const c = [0, 1, 2, 3, 4].map(i => ({ t: S.L(0) + 0.8 + i * 0.35, name: 'pop', gain: 0.4 }));
    for (let i = 1; i <= 5; i++) c.push({ t: S.tag('p' + i) - 0.1, name: 'whoosh', gain: 0.4 });
    return c;
  },
};
