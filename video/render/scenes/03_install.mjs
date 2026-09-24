import { W, H, C, clamp, lerp, ease, prog, pop, txt, rr, panel, actor, sectionCard, termRows, typingCues, drawTerminal, sparkle, stamp, confetti, scanlines } from '../lib.mjs';

const P0 = 'root@archiso ~ #', P1 = '[root@archiso /]#';
// typed command with a deadline: speeds up typing so it finishes by `by`
const cmd = (at, text, by) => ({ at, cmd: text, cps: by ? Math.max(24, text.length / Math.max(0.3, by - at)) : 30 });
const out = (at, text, color) => ({ at, out: text, color });
const OK = '#6BE675', DIM = '#7C8A99', YEL = '#FFD23F';

const EVENTS = {
  install_net: (L, E) => [
    out(0.2, 'Arch Linux 6.18.9-arch1-1 (tty1)', DIM), out(0.25, 'archiso login: root (automatic login)', DIM), out(0.3, ''),
    cmd(L(1) + 1.6, 'cat /sys/firmware/efi/fw_platform_size', E(1) + 0.2), out(L(2) - 0.1, '64', OK),
    cmd(L(3) + 1.8, 'iwctl station wlan0 connect "Pretty Fly for a WiFi"', L(3) + 3.6), out(L(3) + 3.7, 'Passphrase: ****************', DIM),
    cmd(L(3) + 4.0, 'ping -c 2 archlinux.org', E(3) + 0.1),
    out(E(3) + 0.3, '64 bytes from archlinux.org: icmp_seq=1 ttl=52 time=11.8 ms', OK), out(E(3) + 0.9, '64 bytes from archlinux.org: icmp_seq=2 ttl=52 time=12.1 ms', OK),
  ],
  install_disk: (L, E) => [
    cmd(L(0) + 1.2, 'fdisk /dev/nvme0n1', L(0) + 2.2),
    out(L(0) + 2.4, 'Command (m for help): g    # new GPT partition table', DIM),
    out(L(1) + 0.6, 'Command (m for help): n    # +1G   -> EFI system', YEL),
    out(L(1) + 3.6, 'Command (m for help): n    # rest  -> Linux root', '#7FC8F8'),
    out(E(1) - 0.3, 'Command (m for help): w    # the partition table has been altered', OK),
    cmd(L(2) + 0.4, 'mkfs.fat -F 32 /dev/nvme0n1p1', L(2) + 2.0), out(L(2) + 2.1, 'mkfs.fat 4.2 (2021-01-31)', DIM),
    cmd(L(2) + 5.6, 'mkfs.ext4 /dev/nvme0n1p2', L(2) + 7.0), out(L(2) + 7.1, 'Writing superblocks and filesystem accounting information: done', DIM),
    cmd(L(2) + 8.0, 'mount /dev/nvme0n1p2 /mnt', E(2)), cmd(E(2) + 0.3, 'mount --mkdir /dev/nvme0n1p1 /mnt/boot', E(3)),
  ],
  install_pacstrap: (L, E) => [
    cmd(L(0) + 1.3, 'pacstrap -K /mnt base linux linux-firmware', E(0) + 0.3),
    out(E(0) + 0.5, ':: Synchronizing package databases...', DIM), out(E(0) + 0.8, ' core  ·  extra  ·  multilib ............ up to date', DIM),
    out(E(0) + 1.1, 'resolving dependencies...', DIM), out(E(0) + 1.4, 'Packages (132)  Total Installed Size: 1.6 GiB', '#FFFFFF'),
    out(L(1) + 3.0, '(  1/132) installing filesystem ............. [######] 100%', DIM),
    out(L(1) + 4.2, '( 61/132) installing systemd ................ [######] 100%', DIM),
    out(L(1) + 6.2, '(129/132) installing linux ................... [######] 100%', DIM),
    out(L(1) + 8.4, '(132/132) installing linux-firmware .......... [######] 100%', DIM),
    out(E(1), ':: Running post-transaction hooks... done', OK),
    cmd(L(3) + 0.2, 'pacstrap -K /mnt neovim', E(3) + 0.1), out(E(3) + 0.3, '(1/1) installing neovim ...................... [######] 100%', OK),
  ],
  install_chroot: (L, E) => [
    cmd(L(0) + 0.8, 'genfstab -U /mnt >> /mnt/etc/fstab', L(0) + 2.4), cmd(L(0) + 2.6, 'arch-chroot /mnt', E(0) + 0.2),
    { at: E(0) + 0.3, prompt: P1 },
    cmd(L(2) + 0.2, 'ln -sf /usr/share/zoneinfo/Europe/Helsinki /etc/localtime', L(2) + 1.6), out(L(2) + 1.7, '# (Linus says hi)', DIM),
    cmd(L(2) + 1.9, 'locale-gen', L(2) + 2.4), out(L(2) + 2.5, 'Generating locales...  en_US.UTF-8... done', DIM),
    cmd(L(2) + 2.8, 'echo archbtw > /etc/hostname', L(2) + 3.6), cmd(L(2) + 3.8, 'passwd', E(2)), out(E(2) + 0.1, 'passwd: password updated successfully', OK),
    cmd(L(3) + 1.5, 'bootctl install', L(3) + 2.4), out(L(3) + 2.5, 'Created "/boot/loader/"... Installed systemd-boot.', OK),
    cmd(L(3) + 5.4, 'cat /boot/loader/entries/arch.conf', L(3) + 6.4),
    out(L(3) + 6.6, 'title    Arch Linux\nlinux    /vmlinuz-linux\ninitrd   /initramfs-linux.img\noptions  root=UUID=4f1c...e9 rw', '#F5E6C8'),
    cmd(L(6) + 3.2, 'pacman -S networkmanager', L(6) + 4.4), out(L(6) + 4.6, '(1/1) installing networkmanager ...... [######] 100%', OK),
    cmd(L(6) + 4.9, 'systemctl enable NetworkManager', E(6) + 0.1), out(E(6) + 0.2, 'Created symlink ... NetworkManager.service', DIM),
    cmd(L(7) + 0.3, 'exit', L(7) + 0.6), { at: L(7) + 0.7, prompt: P0 }, cmd(L(7) + 0.8, 'reboot', E(7)),
  ],
};
const ORDER = ['install_net', 'install_disk', 'install_pacstrap', 'install_chroot'];
function sceneEvents(TL, id) {
  const sc = TL.byId[id]; const L = i => sc.lines[i].start, E = i => sc.lines[i].end;
  return EVENTS[id](L, E);
}
// History: earlier scenes' events are shown as already finished.
function allEvents(TL, id) {
  const ev = [];
  for (const k of ORDER) {
    if (k === id) { ev.push(...sceneEvents(TL, k)); break; }
    for (const e of sceneEvents(TL, k)) ev.push({ ...e, at: -100 + (e.at || 0) * 0.001 });
  }
  return ev;
}

// ---- speedrun timer ----
const SPLITS = [
  ['BOOT MODE', 'install_net', 2], ['NETWORK', 'install_net', 4], ['PARTITION', 'install_disk', 2], ['FORMAT + MOUNT', 'install_disk', 3],
  ['PACSTRAP', 'install_pacstrap', 2], ['FSTAB + CHROOT', 'install_chroot', 1], ['CONFIG', 'install_chroot', 3], ['BOOTLOADER', 'install_chroot', 4],
  ['NETWORK (AGAIN)', 'install_chroot', 7], ['REBOOT', 'first_boot', 0],
];
const FINAL = 11 * 60 + 47.83;
function timerSpan(TL) {
  const a = TL.byId.install_net.start + TL.byId.install_net.lines[0].start + 2.4;
  const b = TL.byId.first_boot.start + TL.byId.first_boot.lines[0].start;
  return [a, b];
}
const fmt = s => { s = Math.max(0, s); const m = Math.floor(s / 60), r = s - m * 60; return `${m}:${r.toFixed(2).padStart(5, '0')}`; };
export function drawTimer(ctx, TL, G, x, y, w) {
  const [a, b] = timerSpan(TL);
  const fake = g => clamp((g - a) / (b - a)) * FINAL;
  const now = fake(G), done = G >= b;
  panel(ctx, x, y, w, 420, { fill: '#10131A', stroke: done ? YEL : '#3A4556', lw: 4, r: 16, shadow: 'rgba(0,0,0,.5)' });
  txt(ctx, 'ARCH INSTALL · any% glitchless', x + w / 2, y + 36, { fam: 'Nunito-900', size: 24, color: '#C9D4E0', align: 'center' });
  SPLITS.forEach(([name, sid, li], i) => {
    const sc = TL.byId[sid]; const g = sc.start + sc.lines[li].start;
    const yy = y + 72 + i * 28.5, hit = G >= g;
    const cur = !hit && (i === 0 || G >= (() => { const [_, s2, l2] = SPLITS[i - 1]; const q = TL.byId[s2]; return q.start + q.lines[l2].start; })());
    if (cur) { ctx.fillStyle = 'rgba(23,147,209,0.25)'; ctx.fillRect(x + 8, yy - 20, w - 16, 27); }
    txt(ctx, name, x + 20, yy, { fam: 'JBM-800', size: 19, color: hit ? '#FFFFFF' : '#6C7A8C' });
    txt(ctx, hit ? fmt(fake(g)) : '-', x + w - 20, yy, { fam: 'JBM-800', size: 19, color: hit ? OK : '#6C7A8C', align: 'right' });
  });
  const col = done ? (Math.floor(G * 4) % 2 ? YEL : '#FFFFFF') : G < a ? '#8FA3B8' : OK;
  txt(ctx, fmt(now), x + w - 22, y + 400, { fam: 'JBM-800', size: 58, color: col, align: 'right' });
  if (done) txt(ctx, 'PB!', x + 26, y + 395, { fam: 'Anton', size: 48, color: YEL, stroke: C.ink, sw: 6 });
}

function diskDiagram(ctx, t, L, E) {
  const k = ease.out(prog(t, L(0) + 0.6, 0.4)) * (1 - prog(t, E(2), 0.3));
  if (k <= 0) return;
  ctx.save(); ctx.globalAlpha = k; ctx.translate(0, (1 - k) * 60);
  panel(ctx, 90, 540, 1110, 240, { fill: C.cream, r: 18 });
  txt(ctx, '/dev/nvme0n1   (1 TB NVMe)', 130, 590, { fam: 'JBM-800', size: 28, color: C.ink });
  const bx = 130, by = 615, bw = 1030, bh = 110;
  const split = ease.out(prog(t, L(1) + 0.4, 0.6));
  const p1w = lerp(0, 150, split);
  ctx.fillStyle = '#BDB9AE'; rr(ctx, bx, by, bw, bh, 14); ctx.fill();
  if (split > 0) {
    ctx.fillStyle = C.yellow; rr(ctx, bx, by, p1w, bh, 14); ctx.fill();
    ctx.fillStyle = C.blue; rr(ctx, bx + p1w + 8, by, bw - p1w - 8, bh, 14); ctx.fill();
    txt(ctx, 'p1 · EFI', bx + p1w / 2, by + 48, { fam: 'Nunito-900', size: 26, color: C.ink, align: 'center', alpha: split });
    txt(ctx, '1 GiB', bx + p1w / 2, by + 82, { fam: 'Nunito-800', size: 22, color: C.ink, align: 'center', alpha: split });
    txt(ctx, 'p2 · ROOT ( / )', bx + p1w + (bw - p1w) / 2, by + 50, { fam: 'Nunito-900', size: 34, color: C.cream, align: 'center', alpha: prog(t, L(1) + 3.3, 0.3) });
    txt(ctx, 'everything else', bx + p1w + (bw - p1w) / 2, by + 86, { fam: 'Nunito-800', size: 24, color: C.cream, align: 'center', alpha: prog(t, L(1) + 3.3, 0.3) });
  }
  ctx.strokeStyle = C.ink; ctx.lineWidth = 5; rr(ctx, bx, by, bw, bh, 14); ctx.stroke();
  stamp(ctx, bx + 80, by - 10, 0.55, 'FAT32', t - (L(2) + 1.0), C.deep, -0.15);
  stamp(ctx, bx + 820, by - 10, 0.55, 'EXT4 (BORING = GOOD)', t - (L(2) + 5.0), C.deep, 0.06);
  ctx.restore();
}

function pkgCards(ctx, t, L, E, dur) {
  const cards = [['base', 'shell · coreutils · systemd', C.orange, L(1) + 0.5], ['linux', 'the kernel', C.blue, L(1) + dur * 0.47], ['linux-firmware', 'blobs so hardware wakes up', C.lav, L(1) + dur * 0.62]];
  const gone = prog(t, E(2) + 0.2, 0.3);
  cards.forEach(([n, d, col, at], i) => {
    const k = pop(t, at, 0.4) * (1 - gone);
    if (k <= 0) return;
    ctx.save(); ctx.translate(250 + i * 380, 640); ctx.scale(k, k); ctx.rotate((i - 1) * 0.03);
    panel(ctx, -170, -95, 340, 190, { fill: col, r: 18 });
    txt(ctx, n, 0, -18, { fam: 'JBM-800', size: 40, color: C.ink, align: 'center', maxW: 310 });
    txt(ctx, d, 0, 40, { fam: 'Nunito-900', size: 25, color: C.ink, align: 'center', maxW: 310 });
    ctx.restore();
  });
  const k = pop(t, L(2) + 0.2, 0.4) * (1 - gone);
  if (k > 0) { ctx.save(); ctx.translate(630, 790); ctx.scale(k, k); txt(ctx, '= AN ENTIRE OPERATING SYSTEM', 0, 0, { fam: 'Anton', size: 54, color: C.yellow, align: 'center', stroke: C.ink, sw: 10, track: 2 }); ctx.restore(); }
}

function drawInstall(ctx, t, S, CH) {
  const TL = S.TL, G = S.start + t, L = S.L, E = S.E;
  // desk background
  const g = ctx.createLinearGradient(0, 0, 0, H); g.addColorStop(0, '#2B2440'); g.addColorStop(1, '#171325');
  ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);
  ctx.fillStyle = 'rgba(255,143,199,0.06)'; for (let i = 0; i < 9; i++) ctx.fillRect(0, 120 * i + 40, W, 40);
  const events = allEvents(TL, S.id);
  const st = termRows(events, t, { prompt: P0 });
  const panic = S.id === 'install_chroot' && t > L(4) && t < L(6) + 0.3;
  drawTerminal(ctx, 40, 110, 1250, 710, st, t, { fs: 25, title: S.id === 'install_chroot' && t > E(0) + 0.3 && t < L(7) + 0.7 ? 'arch-chroot /mnt' : 'tty1 : archiso', bg: panic ? '#2A0C10' : C.term });
  if (S.id === 'install_disk') diskDiagram(ctx, t, L, E);
  if (S.id === 'install_pacstrap') {
    // highlight the big command
    const k = prog(t, L(0) + 1.3, 0.3) * (1 - prog(t, L(1) + 0.3, 0.4));
    if (k > 0) { ctx.save(); ctx.globalAlpha = k * (0.6 + 0.4 * Math.sin(t * 8)); ctx.strokeStyle = C.orange; ctx.lineWidth = 6; rr(ctx, 50, 160, 1230, 50, 10); ctx.stroke(); ctx.restore(); }
    pkgCards(ctx, t, L, E, S.lines[1].dur);
  }
  if (S.id === 'install_chroot') {
    const k = pop(t, L(1) + 0.5, 0.4) * (1 - prog(t, E(1), 0.3));
    if (k > 0) {
      ctx.save(); ctx.translate(660, 640); ctx.scale(k, k);
      panel(ctx, -470, -110, 940, 220, { fill: C.cream, r: 20 });
      txt(ctx, '/mnt', -300, 20, { fam: 'JBM-800', size: 80, color: C.gray, align: 'center' });
      txt(ctx, '→', 0, 20, { fam: 'Nunito-900', size: 90, color: C.ink, align: 'center' });
      txt(ctx, '/', 300, 30, { fam: 'JBM-800', size: 110, color: C.deep, align: 'center' });
      txt(ctx, 'chroot: "this directory is the whole world now"', 0, 90, { fam: 'Nunito-900', size: 28, color: C.ink, align: 'center' });
      ctx.restore();
    }
    if (panic) {
      const q = t - L(4);
      txt(ctx, '!', 1200, 300, { fam: 'Anton', size: 260, color: C.red, align: 'center', stroke: C.ink, sw: 12, alpha: clamp(q * 4) });
    }
  }
  drawTimer(ctx, TL, G, 1320, 110, 560);
  const A = actor(ctx, CH, S, t);
  const fMood = panic ? 'shock' : S.speaking('femboy', t) ? 'happy' : 'smug';
  A('claude', { x: 1450, y: 850, s: 0.62, mood: 'happy', look: -0.8, phase: 1.3 });
  A('femboy', { x: 1730, y: 870, s: 0.72, mood: fMood, look: -0.6, prop: 'laptop' });
  if (S.id === 'install_chroot') A('gamer', { x: 1850, y: 860, s: 0.7, flip: true, enter: L(4) - 0.25, exit: L(6) + 0.5, mood: 'shock', look: -1 });
  if (S.card) sectionCard(ctx, t, ...S.card);
}

function drawFirstBoot(ctx, t, S, CH) {
  const TL = S.TL, G = S.start + t, L = S.L;
  ctx.fillStyle = '#050608'; ctx.fillRect(0, 0, W, H);
  const lines = ['[  OK  ] Started Journal Service.', '[  OK  ] Reached target Local File Systems.', '[  OK  ] Started Network Manager.', '[  OK  ] Reached target Network.', '[  OK  ] Started User Login Management.', '[  OK  ] Reached target Multi-User System.', '[  OK  ] Reached target Socks.'];
  if (t < 2.4) {
    const n = Math.floor(clamp((t - 0.4) / 1.6) * lines.length);
    lines.slice(0, n).forEach((l, i) => { const y = 140 + i * 50; txt(ctx, '[', 80, y, { fam: 'JBM-400', size: 32, color: '#C8D3DE' }); txt(ctx, 'OK', 138, y, { fam: 'JBM-800', size: 32, color: OK }); txt(ctx, ']' + l.slice(8), 234, y, { fam: 'JBM-400', size: 32, color: '#C8D3DE' }); });
  } else {
    txt(ctx, 'Arch Linux 6.18.9-arch1-1 (tty1)', 120, 330, { fam: 'JBM-400', size: 44, color: '#C8D3DE' });
    txt(ctx, 'archbtw login: ', 120, 440, { fam: 'JBM-800', size: 64, color: '#FFFFFF' });
    if (Math.floor(t * 2) % 2 === 0) { ctx.fillStyle = C.orange; ctx.fillRect(700, 388, 36, 64); }
  }
  scanlines(ctx, 0.2, 4);
  if (t > 2.4) {
    drawTimer(ctx, TL, G, 1320, 110, 560);
    if (t > L(0)) confetti(ctx, t - L(0), 60, 5, [C.pink, C.lav, C.yellow, '#FFFFFF', C.blue], { spread: 1.5 });
    const A = actor(ctx, CH, S, t);
    A('femboy', { x: 1700, y: 900, s: 0.85, enter: L(0) - 0.3, mood: t < L(1) ? 'excited' : 'happy', prop: 'laptop' });
    A('claude', { x: 1420, y: 880, s: 0.8, enter: L(1) - 0.3, mood: 'happy', look: -0.3 });
    A('gamer', { x: 1150, y: 910, s: 0.8, enter: L(3) - 0.3, mood: t > L(4) ? 'sad' : 'neutral', look: 0.6, prop: 'controller' });
    // "no desktop, no browser, no wallpaper" checklist
    const items = ['desktop', 'browser', 'wallpaper'];
    items.forEach((it, i) => { const k = pop(t, L(1) + 2.3 + i * 0.7, 0.3); if (k > 0) { ctx.save(); ctx.translate(230 + i * 280, 620); ctx.scale(k, k); txt(ctx, `✗ ${it}`, 0, 0, { fam: 'Nunito-900', size: 46, color: C.red, align: 'center', stroke: C.ink, sw: 6 }); ctx.restore(); } });
    const k = pop(t, L(2) + 2.8, 0.4);
    if (k > 0) { ctx.save(); ctx.translate(510, 730); ctx.scale(k, k); ctx.rotate(-0.03); txt(ctx, '✓ understanding of every layer', 0, 0, { fam: 'Nunito-900', size: 50, color: OK, align: 'center', stroke: C.ink, sw: 6 }); ctx.restore(); }
  }
}

export default {
  id: [...ORDER, 'first_boot'],
  render(ctx, t, S, CH) { (S.id === 'first_boot' ? drawFirstBoot : drawInstall)(ctx, t, S, CH); },
  cues(S) {
    if (S.id === 'first_boot') return [{ t: 0.4, name: 'bios_beep', gain: 0.4 }, { t: 2.4, name: 'boot_chime', gain: 0.5 }, ...[0, 1, 2].map(i => ({ t: S.L(1) + 2.3 + i * 0.7, name: 'error', gain: 0.18 })), { t: S.L(2) + 2.8, name: 'ding', gain: 0.5 }];
    const c = typingCues(sceneEvents(S.TL, S.id), 0);
    for (const [name, sid, li] of SPLITS) if (sid === S.id) c.push({ t: S.L(li), name: 'tick', gain: 0.35 });
    if (S.id === 'install_disk') c.push({ t: S.L(1) + 0.4, name: 'pop', gain: 0.4 }, { t: S.L(2) + 1.0, name: 'stamp', gain: 0.4 }, { t: S.L(2) + 5.0, name: 'stamp', gain: 0.4 });
    if (S.id === 'install_pacstrap') [S.L(1) + 0.5, S.L(1) + S.lines[1].dur * 0.47, S.L(1) + S.lines[1].dur * 0.62, S.L(2) + 0.2].forEach(x => c.push({ t: x, name: 'pop', gain: 0.45 }));
    if (S.id === 'install_chroot') c.push({ t: S.L(1) + 0.5, name: 'pop', gain: 0.4 });
    return c;
  },
};
