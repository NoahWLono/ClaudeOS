import { W, H, C, clamp, lerp, ease, prog, pop, txt, termRows, typingCues, scanlines, vignette, sunburst, halftone, banner, stamp, actor, rr, rng } from '../lib.mjs';

const BOOT = [
  '[    0.000000] Linux version 7.2.2-arch1-1 (linux@archlinux)',
  '[    0.000000] Command line: initrd=\\initramfs-linux.img root=UUID=4f1c rw',
  '[    0.112233] ACPI: Core revision 20250404',
  '[    0.448151] smpboot: Allowing 16 CPUs, 0 hotplug CPUs',
  '[    1.337000] systemd[1]: systemd 261 running in system mode',
  '[    1.420420] systemd[1]: Detected architecture x86-64.',
  '[  OK  ] Reached target Opinions.',
  '[  OK  ] Started Claude Opus 5.5 Narration Daemon.',
];

function coldEvents(S) {
  const ev = [];
  BOOT.forEach((l, i) => ev.push({ at: 0.15 + i * 0.12, out: l, color: l.includes('OK') ? '#6BE675' : '#8FA3B8' }));
  ev.push({ at: 1.5, out: '' });
  ev.push({ at: 1.7, cmd: 'whoami', cps: 18 });
  ev.push({ at: 2.2, out: 'claude-opus-5-5', color: C.orange });
  ev.push({ at: 2.5, cmd: 'cat /etc/os-release | head -1', cps: 30 });
  ev.push({ at: 3.5, out: 'NAME="Arch Linux"', color: C.blue });
  ev.push({ at: S.L(1) + 0.4, cmd: 'grep -rc "by the way" /internet', cps: 26 });
  ev.push({ at: S.L(2) + 0.2, out: '/internet: 8,675,309 matches', color: C.yellow });
  return ev;
}

function drawCold(ctx, t, S, CH) {
  ctx.fillStyle = '#07090C'; ctx.fillRect(0, 0, W, H);
  const st = termRows(coldEvents(S), t, { prompt: '[claude@archbtw ~]$' });
  const fs = 34, lh = 48;
  ctx.font = `${fs}px JBM-400`;
  const x0 = 90, y0 = 120;
  st.rows.slice(-14).forEach((r, i) => {
    const y = y0 + i * lh;
    if (r.kind === 'cmd') {
      txt(ctx, r.prompt, x0, y, { fam: 'JBM-800', size: fs, color: C.blue });
      ctx.font = `${fs}px JBM-800`; const pw = ctx.measureText(r.prompt + ' ').width;
      txt(ctx, r.text, x0 + pw, y, { fam: 'JBM-800', size: fs, color: '#FFFFFF' });
      if (i === st.rows.slice(-14).length - 1 && (st.typing || Math.floor(t * 2) % 2 === 0)) {
        ctx.font = `${fs}px JBM-800`; const cw = ctx.measureText(r.text).width;
        ctx.fillStyle = C.orange; ctx.fillRect(x0 + pw + cw + 4, y - fs * 0.8, fs * 0.55, fs);
      }
    } else txt(ctx, r.text, x0, y, { fam: 'JBM-400', size: fs * 0.82, color: r.color || '#C8D3DE' });
  });
  // Claude floats in beside the terminal when it starts talking
  const A = actor(ctx, CH, S, t);
  const k = ease.out(prog(t, S.L(0) - 0.6, 0.8));
  if (k > 0) {
    ctx.save(); ctx.globalAlpha = k;
    const g = ctx.createRadialGradient(1540, 560, 20, 1540, 560, 420);
    g.addColorStop(0, 'rgba(217,119,87,0.35)'); g.addColorStop(1, 'rgba(217,119,87,0)');
    ctx.fillStyle = g; ctx.fillRect(1100, 100, 840, 900);
    ctx.restore();
    A('claude', { x: 1540, y: 820 + (1 - k) * 80, s: 1.05, alpha: k, mood: t > S.L(2) ? 'smug' : 'happy', look: -0.4 });
  }
  // The punchline: glitch slam
  const tb = S.L(3);
  if (t >= tb) {
    const q = t - tb;
    const flash = clamp(1 - q / 0.25);
    ctx.fillStyle = `rgba(217,119,87,${0.25 + flash * 0.6})`; ctx.fillRect(0, 0, W, H);
    const k2 = lerp(1.6, 1, ease.out(clamp(q / 0.2)));
    ctx.save(); ctx.translate(W / 2 + Math.sin(q * 80) * 10 * clamp(1 - q), H / 2 - 40); ctx.scale(k2, k2);
    for (const [dx, col] of [[-8, '#00E5FF'], [8, '#FF2E88'], [0, C.cream]])
      txt(ctx, 'I USE ARCH,', dx, -70, { fam: 'Anton', size: 190, color: col, align: 'center', base: 'middle', track: 4 });
    for (const [dx, col] of [[-8, '#00E5FF'], [8, '#FF2E88'], [0, C.cream]])
      txt(ctx, 'BY THE WAY.', dx, 120, { fam: 'Anton', size: 190, color: col, align: 'center', base: 'middle', track: 4 });
    ctx.restore();
  }
  scanlines(ctx, 0.22, 4);
  vignette(ctx, 0.55);
}

function drawTitle(ctx, t, S, CH) {
  const rot = t * 0.05;
  sunburst(ctx, W / 2, H * 0.62, 20, C.orange, C.deep, rot);
  halftone(ctx, 'rgba(20,20,19,0.12)', 16);
  const A = actor(ctx, CH, S, t);
  // rising spark sun + peak
  const sunK = ease.out(prog(t, 0.0, 1.4));
  CH.drawSpark(ctx, W / 2, lerp(H + 200, H * 0.56, sunK), 330, C.cream, t * 0.2);
  CH.drawArchPeak(ctx, W / 2, H + 30, 560 * ease.back(prog(t, 0.3, 0.7)), C.blue);
  // title shrinks up once dialogue starts
  const up = ease.inOut(prog(t, S.L(0) - 0.4, 0.8));
  ctx.save();
  ctx.translate(W / 2, lerp(H * 0.36, 210, up)); const sc = lerp(1, 0.62, up); ctx.scale(sc, sc);
  const k1 = pop(t, 0.2, 0.3), k2 = pop(t, 0.8, 0.3);
  ctx.save(); ctx.scale(k1, k1);
  txt(ctx, 'I USE ARCH,', 0, -110, { fam: 'Anton', size: 210, color: C.cream, align: 'center', base: 'middle', stroke: C.ink, sw: 18, shadow: { color: C.ink, dx: 14, dy: 14 }, track: 6 });
  ctx.restore();
  ctx.save(); ctx.scale(k2, k2);
  txt(ctx, 'BY THE WAY', 0, 110, { fam: 'Anton', size: 210, color: C.blue, align: 'center', base: 'middle', stroke: C.ink, sw: 18, shadow: { color: C.ink, dx: 14, dy: 14 }, track: 6 });
  ctx.restore();
  const k3 = ease.out(prog(t, 1.5, 0.4));
  if (k3 > 0) { ctx.save(); ctx.translate(lerp(-1400, 0, k3), 0); banner(ctx, 0, 270, 1150, 90, C.ink, 'A FIRST-PRINCIPLES PROPAGANDA FILM', { size: 58, color: C.cream, rot: -0.02 }); ctx.restore(); }
  ctx.restore();
  stamp(ctx, 1530, lerp(820, 470, up), lerp(1.1, 0.8, up), 'STARRING CLAUDE OPUS 5.5', t - 2.2, C.cream, -0.1);
  // announcer + claude
  A('announcer', { x: 330, y: 930, s: 1.05, enter: S.L(0) - 0.3, mood: t > S.L(1) + 4 ? 'smug' : 'neutral' });
  { const k = pop(t, S.L(1) + 3.5, 0.4); if (k > 0) { const g = ctx.createRadialGradient(1560, 690, 20, 1560, 690, 300); g.addColorStop(0, 'rgba(240,238,230,0.95)'); g.addColorStop(0.6, 'rgba(240,238,230,0.6)'); g.addColorStop(1, 'rgba(240,238,230,0)'); ctx.save(); ctx.globalAlpha = k; ctx.fillStyle = g; ctx.fillRect(1200, 330, 720, 720); ctx.restore(); } }
  A('claude', { x: 1560, y: 900, s: 1.0, enter: S.L(1) + 3.5, mood: t > S.L(2) ? 'happy' : 'neutral', look: -0.5 });
  if (t > S.L(1)) {
    // "strong opinions about partition tables" gag: a pie-chart partition table
    const q = pop(t, S.L(1) + 3.0, 0.4) * (1 - prog(t, S.L(2), 0.3));
    if (q > 0) {
      ctx.save(); ctx.translate(960, 700); ctx.scale(q, q);
      const parts = [[0.08, C.yellow, 'EFI'], [0.72, C.blue, 'ROOT'], [0.2, C.pink, 'OPINIONS']];
      let a = -Math.PI / 2;
      for (const [f, c, l] of parts) { ctx.beginPath(); ctx.moveTo(0, 0); ctx.arc(0, 0, 150, a, a + f * Math.PI * 2); ctx.closePath(); ctx.fillStyle = c; ctx.fill(); ctx.lineWidth = 6; ctx.strokeStyle = C.ink; ctx.stroke();
        const m = a + f * Math.PI; txt(ctx, l, Math.cos(m) * 95, Math.sin(m) * 95, { fam: 'Anton', size: 30, color: C.ink, align: 'center', base: 'middle' }); a += f * Math.PI * 2; }
      ctx.restore();
    }
  }
  if (t > S.L(3)) {
    // friends teaser silhouettes marching in at bottom
    const q = ease.out(prog(t, S.L(3), 0.8));
    ['gamer', 'femboy', 'wiki', 'goblin', 'tux'].forEach((id, i) => A(id, { x: lerp(-300, 520 + i * 190, q), y: 1010, s: 0.5, mood: 'happy', phase: i }));
  }
}

export default {
  id: ['cold_open', 'title'],
  render(ctx, t, S, CH) { (S.id === 'cold_open' ? drawCold : drawTitle)(ctx, t, S, CH); },
  cues(S) {
    if (S.id === 'cold_open') return [...typingCues(coldEvents(S), 0)];
    return [{ t: 0.2, name: 'stamp', gain: 0.8 }, { t: 0.8, name: 'stamp', gain: 0.8 }, { t: 1.5, name: 'whoosh', gain: 0.5 }, { t: 2.2, name: 'stamp', gain: 0.7 }, { t: S.L(1) + 3.0, name: 'pop', gain: 0.5 }];
  },
};
