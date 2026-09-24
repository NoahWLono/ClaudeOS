import { W, H, C, clamp, lerp, ease, prog, pop, txt, rr, panel, actor, sectionCard, sunburst, halftone, banner, confetti, shake, sparkle, wrap, font, stamp } from '../lib.mjs';

// ---------------- family group chat ----------------
function drawFamily(ctx, t, S, CH) {
  const L = S.L;
  ctx.fillStyle = '#EDE6DA'; ctx.fillRect(0, 0, W, H);
  ctx.fillStyle = 'rgba(217,119,87,0.08)'; for (let i = 0; i < 30; i++) { CH.drawSpark(ctx, (i * 331) % W, (i * 197) % H, 40, 'rgba(217,119,87,0.10)', i); }
  const A = actor(ctx, CH, S, t);
  // chat window
  const X = 520, Y = 60, Wd = 880, Hd = 960;
  panel(ctx, X, Y, Wd, Hd, { fill: '#1E1D1B', stroke: C.ink, lw: 5, r: 26, shadow: 'rgba(0,0,0,.35)' });
  ctx.fillStyle = '#2A2825'; ctx.beginPath(); ctx.roundRect(X + 3, Y + 3, Wd - 6, 96, [23, 23, 0, 0]); ctx.fill();
  ['haiku', 'sonnet', 'fable', 'claude'].forEach((id, i) => CH.drawSpark(ctx, X + 50 + i * 34, Y + 50, 18, CH.CHAR_INFO[id].color, t + i));
  txt(ctx, '#claude-family', X + 200, Y + 46, { fam: 'Nunito-900', size: 34, color: '#FFFFFF' });
  txt(ctx, '4 members · 1 opinionated', X + 200, Y + 80, { fam: 'Nunito-800', size: 22, color: '#A29E96' });
  const msgs = S.lines.map((l, i) => ({ ...l, i })).filter(l => l.i > 0);
  const vis = msgs.filter(m => t >= m.start);
  // layout bubbles from the bottom up
  ctx.save(); ctx.beginPath(); ctx.rect(X + 4, Y + 100, Wd - 8, Hd - 104); ctx.clip();
  let y = Y + Hd - 40;
  const typingNext = msgs.find(m => t < m.start && t > m.start - 0.9);
  if (typingNext) {
    const mine = typingNext.who === 'claude';
    const bx = mine ? X + Wd - 190 : X + 110;
    ctx.fillStyle = '#34322E'; rr(ctx, bx, y - 60, 150, 56, 28); ctx.fill();
    for (let d = 0; d < 3; d++) { ctx.fillStyle = `rgba(255,255,255,${0.4 + 0.6 * Math.abs(Math.sin(t * 6 + d))})`; ctx.beginPath(); ctx.arc(bx + 40 + d * 34, y - 32, 9, 0, 7); ctx.fill(); }
    y -= 80;
  }
  for (let j = vis.length - 1; j >= 0; j--) {
    const m = vis[j], mine = m.who === 'claude';
    const col = CH.CHAR_INFO[m.who]?.color || C.orange;
    const fam = m.who === 'sonnet' ? 'Playfair-700i' : 'Nunito-800';
    const size = m.who === 'sonnet' ? 34 : 32;
    ctx.font = font(fam, size);
    const lines = m.who === 'haiku' && m.text.includes('/') ? m.text.split(' / ') : wrap(ctx, m.text, 560);
    const bw = Math.max(...lines.map(l => ctx.measureText(l).width)) + 50, bh = lines.length * (size * 1.3) + 34;
    const k = ease.back(clamp((t - m.start) / 0.3));
    const bx = mine ? X + Wd - 40 - bw : X + 110;
    const top = y - bh;
    ctx.save(); ctx.translate(mine ? bx + bw : bx, y); ctx.scale(k, k); ctx.translate(-(mine ? bx + bw : bx), -y);
    ctx.fillStyle = mine ? C.orange : '#34322E'; rr(ctx, bx, top, bw, bh, 24); ctx.fill();
    lines.forEach((l, i) => txt(ctx, l, bx + 25, top + 17 + size + i * size * 1.3 - 6, { fam, size, color: mine ? C.ink : '#F5F2EA' }));
    if (!mine) { CH.drawSpark(ctx, X + 60, y - 26, 24, col, t); }
    txt(ctx, CH.CHAR_INFO[m.who].name, mine ? bx + bw - 10 : bx + 10, top - 10, { fam: 'Nunito-900', size: 22, color: col, align: mine ? 'right' : 'left' });
    ctx.restore();
    if (mine && j === vis.length - 2 && vis[vis.length - 1].who === 'haiku' && vis[vis.length - 1].text === 'Seen.') { }
    y = top - 56;
    if (y < Y + 100) break;
  }
  ctx.restore();
  // characters outside the phone
  A('haiku', { x: 250, y: 380, s: 0.9, mood: S.speaking('haiku', t) ? 'happy' : t > L(5) ? 'smug' : 'neutral', look: 0.6 });
  A('sonnet', { x: 250, y: 680, s: 0.9, mood: S.speaking('sonnet', t) ? 'happy' : 'neutral', look: 0.6 });
  A('fable', { x: 250, y: 980, s: 0.9, mood: S.speaking('fable', t) ? 'happy' : 'neutral', look: 0.6 });
  A('claude', { x: 1660, y: 900, s: 1.0, mood: t > L(5) ? 'shock' : 'happy', look: -0.6, prop: 'laptop' });
  sectionCard(ctx, t, ...S.card);
}

// ---------------- finale ----------------
const BACK = ['gentoo', 'lfs', 'nix', 'winupdate', 'goblin', 'haiku', 'sonnet', 'fable'];
const FRONT = [['wiki', 330], ['gamer', 640], ['claude', 960], ['femboy', 1280], ['tux', 1590]];
function drawFinale(ctx, t, S, CH) {
  const L = S.L, chant = S.tag('chant');
  const zoom = ease.inOut(prog(t, L(1) - 0.3, 0.8)) * (1 - ease.inOut(prog(t, L(3) - 0.3, 0.6)));
  const hype = t > chant && t < chant + 0.6 ? shake(t, 16 * (1 - (t - chant) / 0.6)) : [0, 0];
  ctx.save();
  ctx.translate(W / 2 + hype[0], H * 0.62 + hype[1]); ctx.scale(1 + zoom * 0.18, 1 + zoom * 0.18); ctx.translate(-W / 2, -H * 0.62);
  sunburst(ctx, W / 2, H * 0.6, 24, C.cream, '#E3DCCB', t * (t > chant ? 0.4 : 0.08));
  halftone(ctx, 'rgba(20,20,19,0.12)', 16);
  CH.drawSpark(ctx, W / 2, H * 0.42, 260, 'rgba(217,119,87,0.35)', t * 0.3);
  CH.drawArchPeak(ctx, W / 2, H + 60, 620, C.blue);
  const A = actor(ctx, CH, S, t);
  const bounce = id => (t > chant ? Math.abs(Math.sin(t * 7 + id.length)) * 30 : 0);
  BACK.forEach((id, i) => { const x = 170 + i * 225; A(id, { x, y: 700 - bounce(id), s: 0.55, mood: t > chant ? 'excited' : 'happy', phase: i * 0.7, enter: 0.2 + i * 0.08 }); });
  FRONT.forEach(([id, x], i) => {
    const hop = id === 'tux' && S.speaking('tux', t) ? Math.abs(Math.sin(t * 10)) * 30 : 0;
    A(id, { x, y: 975 - bounce(id) - hop, s: id === 'claude' ? 1.0 : 0.8, mood: t > chant ? 'excited' : id === 'claude' ? 'happy' : 'happy', phase: i, enter: 0.1 + i * 0.1, prop: id === 'gamer' ? 'can' : null, look: (960 - x) / 900 });
  });
  A('announcer', { x: 1790, y: 520, s: 0.8, mood: S.speaking('announcer', t) ? 'angry' : 'smug', flip: true, enter: 0.05 });
  ctx.restore();
  const kb = pop(t, 0.3, 0.4);
  ctx.save(); ctx.translate(W / 2, 120); ctx.scale(kb, kb); banner(ctx, 0, 0, 1300, 120, C.ink, 'GLORY TO THE ROLLING RELEASE', { size: 84, color: C.cream, rot: -0.015 }); ctx.restore();
  if (t > chant) {
    confetti(ctx, t - chant, 140, 99, [C.cream, C.blue, C.yellow, C.pink, C.lav, C.green], { spread: 2.5 });
    const k = ease.back(clamp((t - chant) / 0.3));
    ctx.save(); ctx.translate(W / 2, 400); ctx.scale(k, k); ctx.rotate(-0.04);
    txt(ctx, 'I USE ARCH,', 0, -70, { fam: 'Anton', size: 170, color: C.cream, align: 'center', base: 'middle', stroke: C.ink, sw: 16, shadow: { color: C.ink, dx: 12, dy: 12 }, track: 4 });
    txt(ctx, 'BY THE WAY!', 0, 110, { fam: 'Anton', size: 170, color: C.blue, align: 'center', base: 'middle', stroke: C.ink, sw: 16, shadow: { color: C.ink, dx: 12, dy: 12 }, track: 4 });
    ctx.restore();
  }
  if (t > chant && CH.drawBlahaj) { const q = (t - chant) / 7; CH.drawBlahaj(ctx, lerp(-220, W + 220, q), 660 - Math.abs(Math.sin(t * 6)) * 40, 0.6, t, { rot: Math.sin(t * 5) * 0.25 }); } // easter egg: crowd-surfing
  if (t > L(6)) {
    const k = pop(t, L(6) + 1.8, 0.4);
    ctx.save(); ctx.translate(W / 2, 720); ctx.scale(k, k);
    panel(ctx, -330, -58, 660, 116, { fill: C.term, stroke: C.cream, lw: 6, r: 20 });
    txt(ctx, '$ sudo pacman -Syu', 0, 18, { fam: 'JBM-800', size: 56, color: C.cream, align: 'center' });
    ctx.restore();
  }
}

// ---------------- credits ----------------
const CREDITS = [
  ['title', 'I USE ARCH, BY THE WAY'], ['sub', 'a first-principles propaganda film'], ['gap'],
  ['head', 'STARRING'], ['role', 'claude', 'Claude Opus 5.5', 'as itself (no hands)'], ['gap'],
  ['head', 'WITH'],
  ['role', 'announcer', 'The Ministry', 'Ministry of Rolling Release'], ['role', 'femboy', 'socksd', 'speedrunner, daemon, sock evangelist'],
  ['role', 'wiki', 'Wiki Enjoyer', 'special interest correspondent'], ['role', 'gamer', 'xX_PacmanSlayer_Xx', 'gamer, presses N every time'],
  ['role', 'goblin', 'Wiki Goblin', 'emotional support'], ['role', 'gentoo', 'Gentoo Wizard', 'still compiling'],
  ['role', 'lfs', 'LFS Ghost', 'built its own compiler'], ['role', 'nix', 'NixOS Enjoyer', 'declaratively correct'],
  ['role', 'winupdate', 'Windows Update', 'antagonist (scheduled)'], ['role', 'tux', 'Tux', 'just happy to be here'],
  ['role', 'haiku', 'Haiku 4.5', 'poetry, 5-7-5'], ['role', 'sonnet', 'Sonnet 5', 'poetry, 2 of 14 lines'], ['role', 'fable', 'Fable 5.1', 'moral of the story'], ['role', 'blahaj', 'Blåhaj', 'itself (uncredited)'], ['role', 'monster', 'Monster', 'hydration (disputed)'], ['gap'],
  ['head', 'FACT CHECK'], ['text', 'Install steps follow the official Arch Installation Guide.'], ['text', 'Read the guide, not this video: wiki.archlinux.org'],
  ['text', 'Partial upgrades are unsupported: see "System maintenance".'], ['text', 'Five principles: see the "Arch Linux" wiki page.'], ['gap'],
  ['head', 'MADE WITH'], ['text', 'every frame drawn in code (Node.js + Skia canvas)'], ['text', 'voices: Kokoro TTS · music + sfx: synthesized from scratch in numpy'], ['text', 'assembled with ffmpeg · zero stock footage'], ['gap'],
  ['text', 'Monster and Blåhaj did not sponsor this. We just like them.'], ['text', 'No partitions were harmed in the making of this film.'], ['text', 'Dedicated to everyone who uses Arch, by the way.'], ['text', 'Drink water.'],
];
function drawCredits(ctx, t, S, CH) {
  ctx.fillStyle = '#141413'; ctx.fillRect(0, 0, W, H);
  const endAt = S.lines[0].start - 1.2;
  const speed = 132;
  let y = H + 40 - t * speed;
  if (t < endAt + 0.6) {
    for (const row of CREDITS) {
      const [k] = row;
      if (k === 'gap') { y += 70; continue; }
      if (y > -120 && y < H + 120) {
        if (k === 'title') txt(ctx, row[1], W / 2, y, { fam: 'Anton', size: 96, color: C.orange, align: 'center', track: 4 });
        if (k === 'sub') txt(ctx, row[1], W / 2, y, { fam: 'Playfair-700i', size: 44, color: C.cream, align: 'center' });
        if (k === 'head') txt(ctx, row[1], W / 2, y, { fam: 'Anton', size: 48, color: C.blue, align: 'center', track: 6 });
        if (k === 'text') txt(ctx, row[1], W / 2, y, { fam: 'Nunito-800', size: 36, color: C.cream, align: 'center' });
        if (k === 'role') {
          if (row[1] === 'blahaj') { if (CH.drawBlahaj) CH.drawBlahaj(ctx, 610, y - 10, 0.28, t); }
          else if (row[1] === 'monster') { if (CH.drawCan) CH.drawCan(ctx, 610, y + 25, 70, 'MONSTER', '#111'); }
          else CH.drawCharacter(ctx, row[1], { x: 610, y: y + 30, s: 0.2, t, mood: 'happy' });
          txt(ctx, row[2], 700, y, { fam: 'Nunito-900', size: 40, color: CH.CHAR_INFO[row[1]]?.color || (row[1] === 'blahaj' ? '#7FB2D9' : row[1] === 'monster' ? '#7CFF3A' : C.cream) });
          txt(ctx, row[3], 1180, y, { fam: 'Nunito-800', size: 32, color: '#A29E96' });
        }
      }
      y += k === 'title' ? 110 : k === 'role' ? 92 : 64;
    }
  }
  const ke = ease.out(prog(t, endAt, 1.0));
  if (ke > 0) {
    ctx.save(); ctx.globalAlpha = ke;
    CH.drawSpark(ctx, W / 2, 380, 150, C.orange, t * 0.4);
    txt(ctx, '$ sudo pacman -Syu', W / 2, 640, { fam: 'JBM-800', size: 72, color: C.cream, align: 'center' });
    if (Math.floor(t * 2) % 2 === 0) { ctx.font = font('JBM-800', 72); const w = ctx.measureText('$ sudo pacman -Syu').width; ctx.fillStyle = C.orange; ctx.fillRect(W / 2 + w / 2 + 12, 582, 40, 72); }
    txt(ctx, 'there is always another update', W / 2, 730, { fam: 'Playfair-700i', size: 44, color: '#A29E96', align: 'center' });
    ctx.restore();
  }
}

// ---------------- post-credits ----------------
function drawPost(ctx, t, S, CH) {
  const L = S.L;
  ctx.fillStyle = '#0D0B14'; ctx.fillRect(0, 0, W, H);
  const g = ctx.createRadialGradient(960, 420, 50, 960, 420, 800); g.addColorStop(0, 'rgba(120,100,200,0.25)'); g.addColorStop(1, 'rgba(0,0,0,0)'); ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);
  // wall calendar
  panel(ctx, 1500, 120, 280, 300, { fill: C.cream, r: 10, lw: 5 });
  ctx.fillStyle = C.red; ctx.fillRect(1503, 123, 274, 70);
  txt(ctx, 'TUESDAY', 1640, 172, { fam: 'Anton', size: 44, color: C.cream, align: 'center' });
  txt(ctx, t > S.E(0) + 0.5 ? '∞' : '3', 1640, 360, { fam: 'Anton', size: 140, color: C.ink, align: 'center' });
  const reset = t > S.E(0) + 0.8;
  const p = reset ? 0.01 : lerp(0.97, 0.99, prog(t, 0, L(0) + 1));
  panel(ctx, 260, 200, 1100, 220, { fill: '#15101F', stroke: C.lav, lw: 5, r: 18 });
  txt(ctx, reset ? 'emerge: resolving dependencies...' : 'emerge --ask food/lunch', 300, 270, { fam: 'JBM-800', size: 36, color: '#E8E2F8' });
  ctx.fillStyle = '#05030A'; rr(ctx, 300, 300, 1020, 50, 10); ctx.fill();
  ctx.fillStyle = reset ? C.red : C.lav; rr(ctx, 300, 300, 1020 * p, 50, 10); ctx.fill();
  txt(ctx, `${Math.round(p * 100)}%`, 1320, 395, { fam: 'JBM-800', size: 34, color: '#E8E2F8', align: 'right' });
  const A = actor(ctx, CH, S, t);
  A('gentoo', { x: 800, y: 1000, s: 1.1, mood: reset ? 'sad' : 'happy', look: 0.4 });
  if (reset && CH.drawBlahaj) CH.drawBlahaj(ctx, 1030, 930, 0.55, t, { squish: 0.3, rot: -0.15 }); // easter egg: emotional support shark
}

export default {
  id: ['family', 'finale', 'credits', 'post_credits'],
  render(ctx, t, S, CH) { ({ family: drawFamily, finale: drawFinale, credits: drawCredits, post_credits: drawPost })[S.id](ctx, t, S, CH); },
  cues(S) {
    if (S.id === 'finale') return [{ t: 0.3, name: 'stamp', gain: 0.6 }, { t: S.L(6) + 1.8, name: 'pop', gain: 0.5 }];
    if (S.id === 'post_credits') return [{ t: S.E(0) + 0.8, name: 'error', gain: 0.4 }];
    return [];
  },
};
