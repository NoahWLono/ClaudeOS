import { W, H, C, clamp, lerp, ease, prog, pop, txt, rr, panel, actor, sectionCard, drawTerminal, termRows, banner, sparkle, confetti, shake, rng, scanlines } from '../lib.mjs';

const hsl = (h, s = 90, l = 60) => `hsl(${((h % 360) + 360) % 360},${s}%,${l}%)`;

// ---------------- gaming ----------------
function dealWithIt(ctx, x, y, s) {
  // pixel "deal with it" glasses
  const px = 12 * s; const rows = ['1111111111111111111', '1122211111122211101', '0122210001112221000', '0011100000011100000'];
  ctx.save(); ctx.translate(x - (19 * px) / 2, y);
  rows.forEach((r, j) => [...r].forEach((c, i) => { if (c !== '0') { ctx.fillStyle = c === '2' ? '#FFFFFF' : '#000'; ctx.fillRect(i * px, j * px, px + 0.5, px + 0.5); } }));
  ctx.restore();
}
function drawGaming(ctx, t, S, CH) {
  const L = S.L, E = S.E;
  const btw = S.L(3);
  const punch = t > btw && t < btw + 1.2 ? Math.sin(clamp((t - btw) / 1.2) * Math.PI) : 0;
  ctx.save();
  if (punch > 0) { ctx.translate(W / 2, H / 2); ctx.scale(1 + punch * 0.1, 1 + punch * 0.1); ctx.translate(-W / 2, -H / 2); }
  const hype = t > L(7) ? shake(t, 10) : [0, 0]; ctx.translate(...hype);
  ctx.fillStyle = '#12061F'; ctx.fillRect(-40, -40, W + 80, H + 80);
  // RGB glow strips
  for (let i = 0; i < 6; i++) { const g = ctx.createLinearGradient(0, 0, W, 0); g.addColorStop(0, hsl(t * 80 + i * 60, 90, 45)); g.addColorStop(1, hsl(t * 80 + i * 60 + 120, 90, 45)); ctx.globalAlpha = 0.12; ctx.fillStyle = g; ctx.fillRect(-40, 60 + i * 170, W + 80, 40); }
  ctx.globalAlpha = 1;
  ctx.strokeStyle = 'rgba(57,255,20,0.12)'; ctx.lineWidth = 2;
  for (let x = 0; x < W; x += 80) { ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, H); ctx.stroke(); }
  const A = actor(ctx, CH, S, t);
  // handheld
  const kh = ease.back(prog(t, L(1) + 0.4, 0.5)) * (1 - prog(t, L(4) - 0.2, 0.3));
  if (kh > 0) {
    ctx.save(); ctx.translate(960, 400); ctx.scale(kh, kh);
    if (CH.drawHandheld) CH.drawHandheld(ctx, 0, 0, 720, t);
    ctx.restore();
    const kl = pop(t, L(1) + 2.6, 0.4) * (1 - prog(t, L(4) - 0.2, 0.3));
    if (kl > 0) {
      ctx.save(); ctx.translate(960, 150); ctx.scale(kl, kl);
      panel(ctx, -330, -50, 660, 100, { fill: C.blue, r: 50, lw: 5 });
      txt(ctx, 'SteamOS 3  →  based on ARCH', 0, 16, { fam: 'Anton', size: 50, color: C.cream, align: 'center', track: 2 });
      ctx.restore();
    }
  }
  if (t > L(2) && t < btw) txt(ctx, '?!', 520, 360, { fam: 'Anton', size: 200, color: C.yellow, align: 'center', stroke: C.ink, sw: 12 });
  // proton pipeline
  const kp = ease.out(prog(t, L(4), 0.5)) * (1 - prog(t, L(5), 0.3));
  if (kp > 0) {
    ctx.save(); ctx.globalAlpha = kp;
    const boxes = [['WINDOWS GAME', 'calls DirectX', '#2F7FE0', 330], ['PROTON', 'Wine · DXVK · VKD3D-Proton', C.orange, 960], ['LINUX', 'speaks Vulkan', C.blue, 1590]];
    boxes.forEach(([a, b, col, x], i) => { const k = pop(t, L(4) + i * S.lines[4].dur * 0.28, 0.4); ctx.save(); ctx.translate(x, 330); ctx.scale(k, k); panel(ctx, -250, -95, 500, 190, { fill: col, r: 22 }); txt(ctx, a, 0, -10, { fam: 'Anton', size: 58, color: C.cream, align: 'center', stroke: C.ink, sw: 6, track: 2 }); txt(ctx, b, 0, 55, { fam: 'Nunito-900', size: 28, color: C.ink, align: 'center', maxW: 470 }); ctx.restore(); });
    for (let i = 0; i < 2; i++) {
      const x0 = 590 + i * 630, x1 = x0 + 110;
      ctx.strokeStyle = C.cream; ctx.lineWidth = 8; ctx.beginPath(); ctx.moveTo(x0, 330); ctx.lineTo(x1, 330); ctx.stroke();
      ctx.fillStyle = C.cream; ctx.beginPath(); ctx.moveTo(x1 + 24, 330); ctx.lineTo(x1, 312); ctx.lineTo(x1, 348); ctx.fill();
      for (let j = 0; j < 3; j++) { const q = ((t * 1.2 + j / 3) % 1); ctx.fillStyle = C.green; ctx.fillRect(x0 + q * 110 - 8, 322, 16, 16); }
    }
    ctx.restore();
  }
  // install + mangohud
  if (t > L(5) && t < L(6)) {
    const ev = [{ at: L(5) + 0.3, out: '# /etc/pacman.conf', color: '#6C8BA8' }, { at: L(5) + 0.4, out: '[multilib]', color: C.orange }, { at: L(5) + 0.5, out: 'Include = /etc/pacman.d/mirrorlist', color: C.termFg },
      { at: L(5) + 1.6, cmd: 'sudo pacman -Syu steam gamemode mangohud', cps: 26 }, { at: L(5) + 3.4, out: ':: Proceed with installation? [Y/n] y', color: '#6BE675' }];
    drawTerminal(ctx, 260, 120, 1400, 330, termRows(ev, t, { prompt: '[gamer@archbtw ~]$' }), t, { fs: 30, title: 'kitty — RGB ENABLED', border: hsl(t * 120) });
    if (t > L(5) + 4) {
      ctx.save(); ctx.fillStyle = 'rgba(0,0,0,0.55)'; rr(ctx, 30, 110, 420, 150, 8); ctx.fill();
      txt(ctx, 'GPU  62°C  97%', 50, 150, { fam: 'JBM-800', size: 28, color: '#6BE675' }); txt(ctx, 'CPU  55°C  41%', 50, 190, { fam: 'JBM-800', size: 28, color: '#7FC8F8' });
      txt(ctx, `FPS  ${240 + Math.round(Math.sin(t * 7) * 3)}   4.1 ms`, 50, 234, { fam: 'JBM-800', size: 30, color: C.yellow }); ctx.restore();
    }
  }
  // caveat
  const kc = pop(t, L(6) + 0.2, 0.4) * (1 - prog(t, L(7), 0.3));
  if (kc > 0) {
    ctx.save(); ctx.translate(960, 300); ctx.scale(kc, kc);
    panel(ctx, -560, -130, 1120, 260, { fill: C.yellow, r: 20, lw: 6 });
    txt(ctx, '⚠  HONEST CAVEAT', 0, -50, { fam: 'Anton', size: 64, color: C.ink, align: 'center', track: 2 });
    txt(ctx, 'some multiplayer games with kernel-level anti-cheat', 0, 20, { fam: 'Nunito-900', size: 36, color: C.ink, align: 'center' });
    txt(ctx, 'still refuse Linux. Check before you commit.', 0, 72, { fam: 'Nunito-900', size: 36, color: C.ink, align: 'center' });
    ctx.restore();
  }
  A('gamer', { x: 480, y: 950, s: 1.1, mood: t > L(2) && t < btw + 1 ? 'shock' : t > L(7) ? 'excited' : S.speaking('gamer', t) ? 'excited' : 'happy', prop: t > L(1) && t < L(4) ? 'handheld' : 'controller', look: 0.5 });
  A('claude', { x: 1520, y: 950, s: 1.0, mood: t > btw ? 'smug' : 'happy', look: -0.6 });
  if (t > btw) {
    const q = ease.out(prog(t, btw, 0.6));
    dealWithIt(ctx, 1520, lerp(-200, 740, q), 1.1);
  }
  if (t > btw && t < btw + 1.6) {
    const q = t - btw;
    ctx.fillStyle = `rgba(255,80,20,${0.35 * clamp(1 - q / 1.6)})`; ctx.fillRect(-40, -40, W + 80, H + 80);
    txt(ctx, 'BTW', 960, 520, { fam: 'Anton', size: 420 * (1 + 0.2 * clamp(1 - q * 3)), color: C.cream, align: 'center', base: 'middle', stroke: C.ink, sw: 20, alpha: clamp(2 - q * 1.3) });
  }
  if (t > L(7)) {
    confetti(ctx, t - L(7), 90, 21, [hsl(0), hsl(60), hsl(120), hsl(200), hsl(280)], { spread: 1 });
    txt(ctx, "LET'S GOOOO!", 960, 300, { fam: 'PressStart2P', size: 96 + Math.sin(t * 20) * 6, color: hsl(t * 300), align: 'center', stroke: C.ink, sw: 12 });
  }
  ctx.restore();
  sectionCard(ctx, t, ...S.card);
}

// ---------------- windows update ----------------
function drawWin(ctx, t, S, CH) {
  const L = S.L;
  if (t < 2.2) {
    ctx.fillStyle = '#0B0B0B'; ctx.fillRect(0, 0, W, H);
    txt(ctx, 'Meanwhile, on another operating system...', W / 2, H / 2, { fam: 'Playfair-700i', size: 76, color: C.cream, align: 'center', base: 'middle', alpha: clamp(t * 2) * clamp((2.2 - t) * 4) });
    return;
  }
  const split = ease.inOut(prog(t, L(2) - 0.2, 0.6));
  const g = ctx.createLinearGradient(0, 0, 0, H); g.addColorStop(0, '#0B5CAD'); g.addColorStop(1, '#063A73');
  ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);
  const cx = lerp(W / 2, W * 0.27, split);
  for (let i = 0; i < 6; i++) { const a = t * 4 - i * 0.35; ctx.fillStyle = `rgba(255,255,255,${1 - i * 0.15})`; ctx.beginPath(); ctx.arc(cx + Math.cos(a) * 44, 190 + Math.sin(a) * 44, 8, 0, 7); ctx.fill(); }
  txt(ctx, 'Working on updates  0% complete', cx, 320, { fam: 'Inter-800', size: lerp(52, 34, split), color: '#FFFFFF', align: 'center' });
  txt(ctx, "Don't turn off your computer", cx, 380, { fam: 'Inter-800', size: lerp(40, 28, split), color: 'rgba(255,255,255,.8)', align: 'center' });
  if (t > L(1) + 2.0) {
    const opts = ['4 minutes', '17 minutes', '3 hours', 'Tuesday', 'the rest of your life'];
    const i = Math.min(opts.length - 1, Math.floor((t - L(1) - 2.0) * 1.6));
    txt(ctx, `Time remaining: ${opts[i]}`, cx, 440, { fam: 'Inter-800', size: lerp(36, 26, split), color: C.yellow, align: 'center' });
  }
  const A = actor(ctx, CH, S, t);
  A('winupdate', { x: cx, y: 930, s: lerp(1.1, 0.85, split), mood: split > 0.5 ? 'sad' : 'smug' });
  if (split > 0) {
    ctx.save(); ctx.translate(lerp(W, W * 0.54, split), 0);
    ctx.fillStyle = C.cream; ctx.fillRect(0, 0, W, H);
    ctx.fillStyle = C.ink; ctx.fillRect(0, 0, 12, H);
    const ev = [{ at: L(2) + 0.6, cmd: 'sudo pacman -Syu', cps: 18 }, { at: L(2) + 1.8, out: '# whenever YOU decide.', color: '#6C8BA8' }, { at: L(2) + 4.2, out: '# (and you read the news first.)', color: '#6C8BA8' }];
    drawTerminal(ctx, 60, 130, 800, 280, termRows(ev, t, { prompt: '$' }), t, { fs: 34, title: 'your computer, your rules' });
    ctx.restore();
    A('claude', { x: lerp(W + 300, 1480, split), y: 930, s: 1.0, mood: 'happy', look: -0.5 });
  }
}

// ---------------- rice ----------------
const FETCH = [
  ['socksd@archbtw', C.pink], ['--------------', '#B9A5D6'], ['OS', 'Arch Linux x86_64'], ['Kernel', '6.18.9-arch1-1'], ['Uptime', '47 days (never reboots)'], ['Packages', '1337 (pacman)'],
  ['Shell', 'zsh 5.9'], ['WM', 'Hyprland'], ['Terminal', 'kitty'], ['Theme', 'pastel, obviously'], ['CPU', 'yes'], ['Socks', '2 (striped)'],
];
const ASCII = ['        /\\', '       /  \\', '      /    \\', '     /  /\\  \\', '    /  /  \\  \\', '   /__/    \\__\\'];
function win(ctx, x, y, w, h, title, t) {
  ctx.save();
  ctx.shadowColor = 'rgba(80,40,120,0.35)'; ctx.shadowBlur = 30;
  ctx.fillStyle = 'rgba(30,24,48,0.88)'; rr(ctx, x, y, w, h, 16); ctx.fill(); ctx.restore();
  const g = ctx.createLinearGradient(x, y, x + w, y + h); g.addColorStop(0, C.pink); g.addColorStop(1, '#A7D8FF');
  ctx.strokeStyle = g; ctx.lineWidth = 4; rr(ctx, x, y, w, h, 16); ctx.stroke();
  txt(ctx, title, x + 24, y + 38, { fam: 'JBM-800', size: 20, color: '#E8D8FF' });
}
function desktop(ctx, t, S, CH) {
  const g = ctx.createLinearGradient(0, 0, W, H); g.addColorStop(0, '#FFC2E2'); g.addColorStop(0.5, '#D4C2FF'); g.addColorStop(1, '#AEE0FF');
  ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);
  ctx.save(); ctx.globalAlpha = 0.5; CH.drawArchPeak(ctx, 1450, 1000, 700, '#FFFFFF'); CH.drawSpark(ctx, 1450, 420, 170, '#FFFFFF', t * 0.2); ctx.restore();
  // top bar
  ctx.fillStyle = 'rgba(255,255,255,0.55)'; rr(ctx, 16, 12, W - 32, 50, 25); ctx.fill();
  [0, 1, 2, 3, 4].forEach(i => { ctx.fillStyle = i === 0 ? '#E0559A' : 'rgba(120,80,160,0.45)'; ctx.beginPath(); ctx.arc(60 + i * 40, 37, i === 0 ? 12 : 9, 0, 7); ctx.fill(); });
  txt(ctx, 'socksd@archbtw', W / 2, 46, { fam: 'Nunito-900', size: 26, color: '#5A3D7A', align: 'center' });
  txt(ctx, '🧦  🔋 100%   13:37', W - 50, 46, { fam: 'Nunito-900', size: 26, color: '#5A3D7A', align: 'right' });
  // fastfetch window
  win(ctx, 30, 80, 1000, 740, 'kitty — fastfetch', t);
  ASCII.forEach((l, i) => txt(ctx, l, 60, 190 + i * 44, { fam: 'JBM-800', size: 36, color: i < 3 ? C.pink : '#A7D8FF' }));
  const shown = Math.floor(clamp((t - S.tag('morph') - 1.6) * 8, 0, FETCH.length));
  FETCH.slice(0, shown).forEach(([k, v], i) => {
    const y = 160 + i * 46;
    if (i < 2) { txt(ctx, k, 470, y, { fam: 'JBM-800', size: 30, color: v }); return; }
    const socks = k === 'Socks' && t > S.L(4);
    if (socks) { ctx.fillStyle = `rgba(255,143,199,${0.3 + 0.15 * Math.sin(t * 8)})`; ctx.fillRect(460, y - 34, 550, 46); }
    txt(ctx, k + ':', 470, y, { fam: 'JBM-800', size: 30, color: C.pink });
    txt(ctx, v, 650, y, { fam: 'JBM-800', size: 30, color: '#F3EEFF' });
  });
  [C.red, C.orange, C.yellow, C.green, C.teal, C.blue, C.lav, C.pink].forEach((c, i) => { ctx.fillStyle = c; ctx.fillRect(470 + i * 60, 740, 56, 36); });
  // nvim window
  win(ctx, 1050, 80, 840, 440, 'nvim ~/.config/hypr/hyprland.conf', t);
  const code = [['general {', '#D19CF5'], ['  gaps_in = 8', '#F3EEFF'], ['  gaps_out = 16', '#F3EEFF'], ['  col.active_border = rgb(ff8fc7)', '#F5C28A'], ['}', '#D19CF5'], ['# do not question the socks', '#8C7FA8']];
  code.forEach(([l, c], i) => txt(ctx, l, 1080, 150 + i * 50, { fam: 'JBM-800', size: 28, color: c }));
  // cava window
  win(ctx, 1050, 540, 840, 280, 'cava', t);
  for (let i = 0; i < 32; i++) { const h = 30 + Math.abs(Math.sin(t * 5 + i * 0.7) * Math.cos(t * 3.1 + i * 0.3)) * 170; const gg = ctx.createLinearGradient(0, 800 - h, 0, 800); gg.addColorStop(0, C.pink); gg.addColorStop(1, '#A7D8FF'); ctx.fillStyle = gg; rr(ctx, 1080 + i * 25, 800 - h, 18, h, 6); ctx.fill(); }
}
function drawRice(ctx, t, S, CH) {
  const L = S.L, m = S.tag('morph');
  ctx.fillStyle = '#050608'; ctx.fillRect(0, 0, W, H);
  txt(ctx, 'Arch Linux 6.18.9-arch1-1 (tty1)', 120, 330, { fam: 'JBM-400', size: 44, color: '#C8D3DE' });
  txt(ctx, 'archbtw login: socksd', 120, 440, { fam: 'JBM-800', size: 64, color: '#FFFFFF' });
  txt(ctx, '[socksd@archbtw ~]$ Hyprland', 120, 540, { fam: 'JBM-800', size: 44, color: C.pink, alpha: prog(t, m - 0.8, 0.2) });
  scanlines(ctx, 0.2, 4);
  const r = ease.inOut(prog(t, m, 1.2));
  if (r > 0) {
    ctx.save(); ctx.beginPath(); ctx.arc(W / 2, H / 2, r * 1200, 0, 7); ctx.clip();
    desktop(ctx, t, S, CH);
    ctx.restore();
    if (r < 1) { ctx.save(); ctx.strokeStyle = '#FFFFFF'; ctx.lineWidth = 16; ctx.beginPath(); ctx.arc(W / 2, H / 2, r * 1200, 0, 7); ctx.stroke(); ctx.restore(); for (let i = 0; i < 12; i++) sparkle(ctx, W / 2 + Math.cos(i * 0.52) * r * 1200, H / 2 + Math.sin(i * 0.52) * r * 1200, 26, '#FFFFFF', t * 5); }
  }
  const A = actor(ctx, CH, S, t);
  A('femboy', { x: 1650, y: 1010, s: 0.95, mood: S.speaking('femboy', t) ? 'happy' : 'smug', look: -0.4 });
  A('claude', { x: 240, y: 1000, s: 0.75, enter: L(1) - 0.3, mood: 'happy', look: 0.6 });
  A('gamer', { x: 1340, y: 1030, s: 0.75, enter: L(6) - 0.3, mood: t > L(7) ? 'excited' : 'happy', look: 0.6 });
  if (t > L(4) && t < L(6)) {
    const k = pop(t, L(4) + 0.3, 0.4);
    ctx.save(); ctx.translate(560, 420); ctx.scale(k, k); ctx.rotate(-0.05);
    if (CH.drawSock) { CH.drawSock(ctx, -80, -180, 380, ['#FF8FC7', '#FFFFFF'], -0.2); CH.drawSock(ctx, 80, -180, 380, ['#A7D8FF', '#FFFFFF'], 0.2); }
    ctx.restore();
  }
  if (t > L(7)) {
    const rr2 = rng(77);
    for (let i = 0; i < 40; i++) {
      const x = rr2() * W, v = 250 + rr2() * 250, t0 = rr2() * 1.2, tt = t - L(7) - t0; if (tt < 0) continue;
      const y = -120 + v * tt; if (y > H + 100) continue;
      if (CH.drawSock) CH.drawSock(ctx, x, y, 110, i % 2 ? ['#FF8FC7', '#FFFFFF'] : ['#A7D8FF', '#FFFFFF'], tt * 3 + i);
    }
  }
  sectionCard(ctx, t, ...S.card);
}

export default {
  id: ['gaming', 'winupdate', 'rice'],
  render(ctx, t, S, CH) { ({ gaming: drawGaming, winupdate: drawWin, rice: drawRice })[S.id](ctx, t, S, CH); },
  cues(S) {
    const L = S.L;
    if (S.id === 'gaming') return [{ t: L(1) + 0.4, name: 'swoosh_up', gain: 0.4 }, { t: L(1) + 2.6, name: 'pop', gain: 0.4 }, { t: L(3) + 0.5, name: 'glitch', gain: 0.3 },
      ...[0, 1, 2].map(i => ({ t: L(4) + i * S.lines[4].dur * 0.28, name: 'pop', gain: 0.35 })), { t: L(6) + 0.2, name: 'error', gain: 0.3 }, { t: L(7) + 0.8, name: 'cheer', gain: 0.4 }];
    if (S.id === 'winupdate') return [{ t: 2.2, name: 'bios_beep', gain: 0.2 }, { t: L(2) - 0.2, name: 'whoosh', gain: 0.5 }];
    return [{ t: S.tag('morph') - 0.8, name: 'enter', gain: 0.4 }, { t: S.tag('morph'), name: 'sparkle', gain: 0.6 }, { t: S.tag('morph') + 0.3, name: 'swoosh_up', gain: 0.4 }, { t: L(4) + 0.3, name: 'pop', gain: 0.5 }];
  },
};
