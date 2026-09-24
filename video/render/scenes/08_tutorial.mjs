import { W, H, C, clamp, lerp, ease, prog, pop, txt, rr, panel, actor, sectionCard, font, sparkle } from '../lib.mjs';

// Line prefixes inside command blocks:
//  '# ' root command   '$ ' user command   '>' continuation   '~' comment   '=' good output
//  '.' plain output    '!' warning         '@' file name      '|' file contents
const R = '#', U = '$';
const P_LIVE = 'root@archiso ~ #', P_CH = '[root@archiso /]#', P_USER = '[you@archbtw ~]$', P_HOST = '[you@old-pc ~]$';
const TOTAL = 23;

const SCENES = {
  tut_intro: [
    { line: 0, step: 0, title: 'THE PLAN', custom: 'roadmap', notes: ['Follows the official Installation guide', 'wiki.archlinux.org/title/Installation_guide'] },
    { line: 2, step: 0, title: 'BEFORE ANYTHING', custom: 'warning', notes: ['Installing wipes the target disk', 'Back up first. Really.'] },
    { line: 3, step: 0, title: 'YOU WILL NEED', custom: 'checklist', notes: ['ISO is ~1.5 GB (2026.09.01)', 'UEFI mode, Secure Boot off (step 3)'] },
  ],
  tut_usb: [
    { line: 0, step: 1, title: 'DOWNLOAD + VERIFY', prompt: P_HOST, cmds: ['~ on your current computer, in the download folder', '$ b2sum -c b2sums.txt --ignore-missing', '= archlinux-2026.09.01-x86_64.iso: OK', '$ gpg --auto-key-locate clear,wkd -v \\', '>    --locate-external-key pierre@archlinux.org', '$ gpg --verify archlinux-2026.09.01-x86_64.iso.sig \\', '>    archlinux-2026.09.01-x86_64.iso', '= gpg: Good signature from "Pierre Schmitz ..."'], notes: ['archlinux.org/download', 'exact commands are on that page'] },
    { line: 1, step: 2, title: 'WRITE THE USB STICK', prompt: P_HOST, cmds: ['$ ls -l /dev/disk/by-id/usb-*', '~ use the WHOLE device, never a -part1 / sdb1', '$ sudo dd bs=4M if=archlinux-2026.09.01-x86_64.iso \\', '>    of=/dev/disk/by-id/usb-My_flash_drive \\', '>    conv=fsync oflag=direct status=progress', '! this erases the USB stick'], notes: ['Windows: Rufus (rufus.ie)', 'everything on the stick is erased'] },
    { line: 2, step: 3, title: 'FIRMWARE SETTINGS', custom: 'bios', notes: ['Secure Boot: Disabled', 'can be re-enabled after install'] },
    { line: 3, step: 4, title: 'BOOT THE USB', custom: 'bootmenu', notes: ['boot menu key: F12 / F11 / F8 / Esc', 'check your motherboard manual'] },
  ],
  tut_live: [
    { line: 0, step: 5, title: 'KEYBOARD (OPTIONAL)', prompt: P_LIVE, cmds: ['~ only if you are not on a US layout', '# localectl list-keymaps', '# loadkeys de-latin1'], notes: ['default layout is US', 'de-latin1 = German example'] },
    { line: 1, step: 6, title: 'CONFIRM UEFI MODE', prompt: P_LIVE, cmds: ['# cat /sys/firmware/efi/fw_platform_size', '= 64', '~ "No such file or directory" = BIOS mode: fix it in firmware'], notes: ['64 = 64-bit UEFI', '32 works, but limits boot loaders'] },
    { line: 2, step: 7, title: 'CONNECT TO THE INTERNET', prompt: P_LIVE, cmds: ['~ Ethernet: just plug it in. Wi-Fi:', '# iwctl', '. [iwd]# device list', '. [iwd]# station wlan0 scan', '. [iwd]# station wlan0 get-networks', '. [iwd]# station wlan0 connect "Your WiFi"', '. [iwd]# exit', '# ping -c 3 ping.archlinux.org', '= 64 bytes from ping.archlinux.org: icmp_seq=1'], notes: ['wlan0 = your device name', 'blocked card? try: rfkill unblock wifi'] },
    { line: 3, step: 8, title: 'CHECK THE CLOCK', prompt: P_LIVE, cmds: ['# timedatectl', '. System clock synchronized: yes', '. NTP service: active'], notes: ['syncs automatically once online', 'wrong time = signature errors'] },
  ],
  tut_disk: [
    { line: 0, step: 9, title: 'FIND YOUR DISK', prompt: P_LIVE, cmds: ['# lsblk', '. NAME          SIZE  TYPE', '= nvme0n1     953.9G  disk     <- install target', '. sda          14.9G  disk     <- the USB stick', '. loop0         1.1G  loop     (ignore)'], notes: ['NVMe: /dev/nvme0n1   SATA: /dev/sda', 'below: replace nvme0n1 with yours'] },
    { line: 1, step: 10, title: 'PARTITION (cfdisk)', custom: 'cfdisk', notes: ['# cfdisk /dev/nvme0n1', 'label type: gpt', 'p1 1G EFI System', 'p2 4G+ Linux swap', 'p3 rest: Linux root (x86-64)'] },
    { line: 3, step: 11, title: 'FORMAT', prompt: P_LIVE, cmds: ['# mkfs.fat -F 32 /dev/nvme0n1p1', '# mkswap /dev/nvme0n1p2', '# mkfs.ext4 /dev/nvme0n1p3'], notes: ['p1 -> FAT32 (EFI)', 'p2 -> swap', 'p3 -> ext4 (root)'] },
    { line: 4, step: 12, title: 'MOUNT', prompt: P_LIVE, cmds: ['# mount /dev/nvme0n1p3 /mnt', '# mount --mkdir /dev/nvme0n1p1 /mnt/boot', '# swapon /dev/nvme0n1p2'], notes: ['root first, then /boot', 'order matters'] },
  ],
  tut_install: [
    { line: 0, step: 13, title: 'INSTALL PACKAGES', prompt: P_LIVE, cmds: ['# pacstrap -K /mnt base linux linux-firmware \\', '>    intel-ucode networkmanager sudo nano \\', '>    man-db man-pages', '~ AMD CPU? use amd-ucode instead of intel-ucode'], notes: ['base + kernel + firmware', 'microcode, network, sudo,', 'an editor, manuals'] },
    { line: 1, step: 13, title: 'INSTALL PACKAGES', prompt: P_LIVE, cmds: ['~ laptop speakers silent later? add:', '# pacstrap -K /mnt sof-firmware'], notes: ['sof-firmware = onboard audio', 'on many laptops'] },
    { line: 2, step: 14, title: 'FSTAB', prompt: P_LIVE, cmds: ['# genfstab -U /mnt >> /mnt/etc/fstab', '# cat /mnt/etc/fstab', '| UUID=4f1c...  /      ext4  rw,relatime  0 1', '| UUID=7A2B...  /boot  vfat  rw,relatime  0 2', '| UUID=91d0...  none   swap  defaults     0 0'], notes: ['expect 3 entries:', '/, /boot and swap'] },
  ],
  tut_config: [
    { line: 0, step: 15, title: 'CHROOT', prompt: P_LIVE, cmds: ['# arch-chroot -S /mnt', '= [root@archiso /]#   <- you are inside the new system'], notes: ['-S = systemd mode', 'needed for bootctl to add', 'its UEFI boot entry'] },
    { line: 1, step: 16, title: 'TIME ZONE', prompt: P_CH, cmds: ['# ln -sf /usr/share/zoneinfo/Europe/Helsinki /etc/localtime', '# hwclock --systohc', '~ list zones: ls /usr/share/zoneinfo'], notes: ['Area/Location, e.g.', 'America/Chicago, Asia/Tokyo'] },
    { line: 2, step: 17, title: 'LOCALE', prompt: P_CH, cmds: ['# nano /etc/locale.gen', '|   en_US.UTF-8 UTF-8        <- remove the leading #', '# locale-gen', '# echo LANG=en_US.UTF-8 > /etc/locale.conf', '~ changed keymap? echo KEYMAP=de-latin1 > /etc/vconsole.conf'], notes: ['uncomment your language', 'nano: Ctrl+O save, Ctrl+X exit'] },
    { line: 3, step: 18, title: 'HOSTNAME + ROOT PASSWORD', prompt: P_CH, cmds: ['# echo archbtw > /etc/hostname', '# passwd', '. New password: ********', '= passwd: password updated successfully'], notes: ['hostname: a-z, 0-9, hyphens', 'pick a strong root password'] },
    { line: 4, step: 19, title: 'YOUR USER + SUDO', prompt: P_CH, cmds: ['# useradd -m -G wheel yourname', '# passwd yourname', '# EDITOR=nano visudo', '|   %wheel ALL=(ALL:ALL) ALL     <- uncomment this line'], notes: ['-m = create home folder', 'wheel = allowed to sudo', 'always edit sudoers with visudo'] },
  ],
  tut_boot: [
    { line: 0, step: 20, title: 'BOOTLOADER', prompt: P_CH, cmds: ['# bootctl install', '= Created EFI boot entry "Linux Boot Manager".'], notes: ['systemd-boot, ships with systemd', 'ESP mounted at /boot'] },
    { line: 1, step: 20, title: 'BOOTLOADER CONFIG', prompt: P_CH, cmds: ['# nano /boot/loader/loader.conf', '@ /boot/loader/loader.conf', '| default  arch.conf', '| timeout  3', '| editor   no', '# nano /boot/loader/entries/arch.conf', '@ /boot/loader/entries/arch.conf', '| title    Arch Linux', '| linux    /vmlinuz-linux', '| initrd   /initramfs-linux.img'], notes: ['loader.conf: which entry, how long', 'arch.conf: kernel + initramfs'] },
    { line: 2, step: 20, title: 'ROOT UUID', prompt: P_CH, cmds: ['# echo "options root=UUID=$(blkid -s UUID -o value /dev/nvme0n1p3) rw" \\', '>    >> /boot/loader/entries/arch.conf', '# cat /boot/loader/entries/arch.conf', '| title    Arch Linux', '| linux    /vmlinuz-linux', '| initrd   /initramfs-linux.img', '| options  root=UUID=4f1c9a2e-...-e9 rw'], notes: ['>> appends; > would overwrite!', 'p3 = your ROOT partition'] },
    { line: 3, step: 20, title: 'MICROCODE', prompt: P_CH, cmds: ['~ nothing to do: mkinitcpio packs microcode', '~ into initramfs-linux.img by default'], notes: ['no separate initrd line', 'for intel-ucode / amd-ucode'] },
    { line: 4, step: 21, title: 'NETWORK AT BOOT', prompt: P_CH, cmds: ['# systemctl enable NetworkManager', '= Created symlink ... NetworkManager.service'], notes: ['the classic mistake,', 'avoided'] },
  ],
  tut_reboot: [
    { line: 0, step: 22, title: 'REBOOT', prompt: P_CH, cmds: ['# exit', '. root@archiso ~ # umount -R /mnt', '. root@archiso ~ # reboot', '~ remove the USB stick when the screen goes dark'], notes: ['exit = leave the chroot', 'then unmount + reboot'] },
    { line: 1, step: 23, title: 'FIRST BOOT', prompt: P_USER, cmds: ['. archbtw login: yourname', '$ nmtui                          ~ Wi-Fi menu', '$ sudo pacman -Syu', '$ sudo pacman -S plasma-meta sddm konsole', '$ sudo systemctl enable --now sddm', '~ or: gnome (uses gdm) · or: hyprland kitty'], notes: ['log in as YOUR user', 'pick any desktop you like'] },
    { line: 2, step: 23, title: 'IF YOU GET STUCK', custom: 'links', notes: ['the wiki is the source of truth', 'this video is not'] },
  ],
};
const ORDER = Object.keys(SCENES);

function hdr(ctx, t, S, blk) {
  ctx.fillStyle = '#0A1119'; ctx.fillRect(0, 0, W, 96);
  txt(ctx, 'ARCH INSTALL TUTORIAL', 150, 60, { fam: 'Anton', size: 40, color: C.cream, track: 2 });
  if (blk.step) txt(ctx, `STEP ${blk.step} / ${TOTAL}`, 620, 60, { fam: 'JBM-800', size: 34, color: C.blue });
  txt(ctx, blk.title, 1880, 60, { fam: 'Anton', size: 40, color: C.orange, align: 'right', track: 2, maxW: 900 });
  const p = blk.step / TOTAL;
  ctx.fillStyle = '#1C2A38'; ctx.fillRect(0, 90, W, 8);
  ctx.fillStyle = C.blue; ctx.fillRect(0, 90, W * p, 8);
  txt(ctx, '⏸ pause anytime', 1880, 128, { fam: 'Nunito-800', size: 22, color: '#6C8BA8', align: 'right' });
}

function termBlock(ctx, t, S, blk, x, y, w, h) {
  const t0 = S.L(blk.line) + 0.25;
  panel(ctx, x, y, w, h, { fill: '#0C0F14', stroke: '#2A3A4C', lw: 4, r: 18, shadow: 'rgba(0,0,0,.45)' });
  const fs = 33, lh = 50; let yy = y + 68;
  const cps = 70; let budget = Math.max(0, (t - t0) * cps);
  for (const raw of blk.cmds) {
    const k = raw[0], body = raw.slice(raw[1] === ' ' ? 2 : 1);
    const isCmd = k === R || k === U || k === '>';
    let shown = body;
    if (isCmd) { const n = Math.min(body.length, Math.floor(budget)); shown = body.slice(0, n); budget -= body.length; if (n <= 0 && budget < 0 && shown === '') break; }
    else { if (budget < 0) break; budget -= 6; }
    let xx = x + 34;
    if (k === R || k === U) { const pr = blk.prompt; txt(ctx, pr, xx, yy, { fam: 'JBM-800', size: fs, color: C.blue }); ctx.font = font('JBM-800', fs); xx += ctx.measureText(pr + ' ').width; }
    if (k === '>') xx += 0;
    const col = { '#': '#FFFFFF', '$': '#FFFFFF', '>': '#FFFFFF', '~': '#6C8BA8', '=': '#6BE675', '.': '#C8D3DE', '!': C.yellow, '@': C.orange, '|': '#F5E6C8' }[k] || '#FFFFFF';
    const fam = k === '~' || k === '.' ? 'JBM-400' : 'JBM-800';
    txt(ctx, (k === '~' ? '# ' : '') + shown, xx, yy, { fam, size: k === '@' ? 24 : fs, color: col, maxW: x + w - xx - 24 });
    if (isCmd && shown.length < body.length) { ctx.font = font(fam, fs); ctx.fillStyle = C.orange; ctx.fillRect(xx + ctx.measureText(shown).width + 3, yy - fs * 0.8, fs * 0.55, fs); break; }
    yy += k === '@' ? lh * 0.8 : lh;
    if (yy > y + h - 20) break;
  }
}

function sidebar(ctx, t, S, blk, CH) {
  const x = 1350, y = 150, w = 530;
  const k = ease.out(prog(t, S.L(blk.line), 0.35));
  ctx.save(); ctx.globalAlpha = k;
  panel(ctx, x, y, w, 90 + blk.notes.length * 50, { fill: '#15202C', stroke: C.orange, lw: 4, r: 18 });
  txt(ctx, blk.step ? `STEP ${blk.step}` : 'READ ME', x + 28, y + 52, { fam: 'Anton', size: 38, color: C.orange, track: 2 });
  blk.notes.forEach((n, i) => txt(ctx, (n.startsWith('#') ? '' : '• ') + n, x + 28, y + 104 + i * 50, { fam: n.startsWith('#') ? 'JBM-800' : 'Nunito-800', size: 29, color: C.cream, maxW: w - 50 }));
  ctx.restore();
}

// ---- custom panels ----
function roadmap(ctx, t, S, x, y, w, h) {
  panel(ctx, x, y, w, h, { fill: C.cream, r: 20 });
  txt(ctx, 'THE ROAD TO  archbtw login:', x + 40, y + 70, { fam: 'Anton', size: 50, color: C.ink, track: 2 });
  const steps = [['1-4', 'Make the USB, boot it'], ['5-8', 'Keyboard, UEFI check, internet, clock'], ['9-12', 'Partition, format, mount'], ['13-14', 'Install packages, fstab'], ['15-19', 'Time, locale, hostname, users'], ['20-23', 'Bootloader, network, reboot']];
  steps.forEach(([n, s], i) => {
    const k = pop(t, S.L(0) + 1.0 + i * 0.5, 0.35); if (k <= 0) return;
    const yy = y + 140 + i * 88;
    ctx.save(); ctx.translate(x + 40, yy); ctx.scale(k, k);
    ctx.fillStyle = [C.blue, C.teal, C.orange, C.lav, C.pink, C.yellow][i]; rr(ctx, 0, -40, 150, 64, 32); ctx.fill();
    txt(ctx, n, 75, 2, { fam: 'JBM-800', size: 30, color: C.ink, align: 'center' });
    txt(ctx, s, 180, 4, { fam: 'Nunito-900', size: 36, color: C.ink });
    ctx.restore();
  });
}
function warning(ctx, t, S, x, y, w, h) {
  const pulse = 0.85 + 0.15 * Math.sin(t * 5);
  panel(ctx, x, y, w, h, { fill: '#3A0F12', stroke: C.red, lw: 8, r: 20 });
  txt(ctx, '⚠', x + w / 2, y + 230, { fam: 'DejaVu Sans', size: 200 * pulse, color: C.yellow, align: 'center' });
  txt(ctx, 'THIS ERASES THE ENTIRE DISK', x + w / 2, y + 380, { fam: 'Anton', size: 76, color: C.cream, align: 'center', track: 2, maxW: w - 60 });
  txt(ctx, 'everything on it: other OSes, photos, homework', x + w / 2, y + 450, { fam: 'Nunito-900', size: 36, color: '#F5B7B1', align: 'center' });
  txt(ctx, 'back up first', x + w / 2, y + 530, { fam: 'Playfair-700i', size: 48, color: C.yellow, align: 'center' });
}
function checklist(ctx, t, S, CH, x, y, w, h) {
  panel(ctx, x, y, w, h, { fill: C.cream, r: 20 });
  txt(ctx, 'CHECKLIST', x + 40, y + 70, { fam: 'Anton', size: 54, color: C.ink, track: 3 });
  const items = [['USB stick, 2 GB or more', true], ['a 64-bit UEFI computer', true], ['internet (Ethernet is easiest)', true], ['a disk you are OK erasing (32 GB+)', true], ['one (1) Monster', 'opt'], ['water', 'must']];
  const d = S.lines[3].dur;
  items.forEach(([s, kind], i) => {
    const at = S.L(3) + (i / items.length) * d * 0.9;
    const k = pop(t, at, 0.3); if (k <= 0) return;
    const yy = y + 150 + i * 82;
    ctx.save(); ctx.translate(x + 50, yy); ctx.scale(k, k);
    ctx.strokeStyle = C.ink; ctx.lineWidth = 5; rr(ctx, 0, -38, 48, 48, 8); ctx.stroke();
    txt(ctx, '✓', 6, 2, { fam: 'DejaVu Sans', size: 44, color: kind === 'opt' ? '#2E7D32' : C.deep });
    txt(ctx, s, 76, 0, { fam: 'Nunito-900', size: 38, color: C.ink });
    if (kind === 'opt') txt(ctx, '(optional)', 470, 0, { fam: 'Nunito-800', size: 30, color: C.gray });
    if (kind === 'must') txt(ctx, '(mandatory)', 200, 0, { fam: 'Nunito-900', size: 30, color: C.blue });
    ctx.restore();
  });
  if (t > S.L(3) + d * 0.6) {
    if (CH.drawCan) CH.drawCan(ctx, x + w - 170, y + h - 60, 190, 'MONSTER', '#111');
    // water glass
    const gx = x + w - 330, gy = y + h - 60;
    ctx.fillStyle = 'rgba(127,200,248,0.55)'; ctx.beginPath(); ctx.moveTo(gx - 42, gy - 120); ctx.lineTo(gx + 42, gy - 120); ctx.lineTo(gx + 34, gy); ctx.lineTo(gx - 34, gy); ctx.fill();
    ctx.strokeStyle = C.ink; ctx.lineWidth = 5; ctx.beginPath(); ctx.moveTo(gx - 50, gy - 170); ctx.lineTo(gx - 34, gy); ctx.lineTo(gx + 34, gy); ctx.lineTo(gx + 50, gy - 170); ctx.stroke();
  }
}
function bios(ctx, t, S, x, y, w, h) {
  ctx.fillStyle = '#1B2A6B'; rr(ctx, x, y, w, h, 12); ctx.fill();
  ctx.fillStyle = '#C8C8C8'; ctx.fillRect(x, y + 10, w, 56);
  txt(ctx, 'FIRMWARE SETUP UTILITY', x + w / 2, y + 50, { fam: 'JBM-800', size: 30, color: '#1B2A6B', align: 'center' });
  const rows = [['Boot Mode', 'UEFI'], ['Secure Boot', t > S.L(2) + 2.2 ? 'Disabled' : 'Enabled'], ['Fast Boot', 'Disabled'], ['Boot Option #1', 'USB: My flash drive']];
  rows.forEach(([a, b], i) => {
    const yy = y + 150 + i * 80, hot = i === 1;
    if (hot) { ctx.fillStyle = 'rgba(255,255,255,0.12)'; ctx.fillRect(x + 30, yy - 44, w - 60, 64); }
    txt(ctx, a, x + 60, yy, { fam: 'JBM-800', size: 34, color: '#FFFFFF' });
    txt(ctx, `[${b}]`, x + w - 60, yy, { fam: 'JBM-800', size: 34, color: hot ? (b === 'Disabled' ? '#6BE675' : C.yellow) : '#A9C1FF', align: 'right' });
  });
  txt(ctx, 'F10: Save & Exit    Esc: Back', x + w / 2, y + h - 40, { fam: 'JBM-400', size: 26, color: '#A9C1FF', align: 'center' });
}
function bootmenu(ctx, t, S, x, y, w, h) {
  ctx.fillStyle = '#000'; rr(ctx, x, y, w, h, 12); ctx.fill();
  const items = ['Arch Linux install medium (x86_64, UEFI)', 'Arch Linux install medium (x86_64, UEFI) with speech', 'EFI Shell', 'Reboot Into Firmware Interface'];
  items.forEach((s, i) => {
    const yy = y + 160 + i * 64;
    if (i === 0) { ctx.fillStyle = '#C8C8C8'; ctx.fillRect(x + 60, yy - 42, w - 120, 58); }
    txt(ctx, s, x + 80, yy, { fam: 'JBM-400', size: 30, color: i === 0 ? '#000' : '#C8C8C8', maxW: w - 160 });
  });
  const k = prog(t, S.L(3) + S.lines[3].dur * 0.8, 0.5);
  if (k > 0) txt(ctx, 'root@archiso ~ #', x + 80, y + h - 70, { fam: 'JBM-800', size: 36, color: C.blue, alpha: k });
}
function cfdisk(ctx, t, S, x, y, w, h) {
  ctx.fillStyle = '#0C0F14'; rr(ctx, x, y, w, h, 12); ctx.fill();
  ctx.strokeStyle = '#2A3A4C'; ctx.lineWidth = 4; rr(ctx, x, y, w, h, 12); ctx.stroke();
  txt(ctx, 'Disk: /dev/nvme0n1', x + w / 2, y + 60, { fam: 'JBM-800', size: 30, color: '#FFFFFF', align: 'center' });
  txt(ctx, 'Size: 953.87 GiB   Label: gpt', x + w / 2, y + 100, { fam: 'JBM-400', size: 26, color: '#C8D3DE', align: 'center' });
  txt(ctx, 'Device              Size   Type', x + 50, y + 180, { fam: 'JBM-800', size: 28, color: '#6C8BA8' });
  const rows = [['/dev/nvme0n1p1', '1G', 'EFI System', C.yellow], ['/dev/nvme0n1p2', '4G', 'Linux swap', C.pink], ['/dev/nvme0n1p3', '948.9G', 'Linux root (x86-64)', '#7FC8F8']];
  const d = S.lines[1].dur;
  rows.forEach(([dev, sz, ty, col], i) => {
    const at = S.L(1) + d * (0.35 + i * 0.2);
    if (t < at) return;
    const yy = y + 240 + i * 60;
    if (i === rows.length - 1 || t < at + 1.2) { ctx.fillStyle = 'rgba(23,147,209,0.25)'; ctx.fillRect(x + 30, yy - 40, w - 60, 54); }
    txt(ctx, dev, x + 50, yy, { fam: 'JBM-800', size: 28, color: '#FFFFFF' });
    txt(ctx, sz.padStart(7), x + 330, yy, { fam: 'JBM-800', size: 28, color: '#FFFFFF' });
    txt(ctx, ty, x + 520, yy, { fam: 'JBM-800', size: 28, color: col });
  });
  const btns = ['Delete', 'Resize', 'Quit', 'Type', 'Help', 'Write', 'Dump'];
  const write = t > S.L(2) - 0.2;
  btns.forEach((b, i) => { const bx = x + 50 + i * 152, by = y + h - 150; const hot = write && b === 'Write'; if (hot) { ctx.fillStyle = C.orange; ctx.fillRect(bx - 8, by - 34, 140, 46); } txt(ctx, `[ ${b} ]`, bx, by, { fam: 'JBM-800', size: 24, color: hot ? C.ink : '#C8D3DE' }); });
  if (write) txt(ctx, 'Are you sure you want to write the partition table to disk? yes', x + 50, y + h - 70, { fam: 'JBM-400', size: 24, color: C.yellow, maxW: w - 100 });
}
function links(ctx, t, S, x, y, w, h) {
  panel(ctx, x, y, w, h, { fill: C.cream, r: 20 });
  txt(ctx, 'WHEN IN DOUBT', x + 40, y + 76, { fam: 'Anton', size: 54, color: C.ink, track: 3 });
  const L = [['Installation guide', 'wiki.archlinux.org/title/Installation_guide'], ['After installing', 'wiki.archlinux.org/title/General_recommendations'], ['Just get it done', 'run  archinstall  on the live USB'], ['Humans', 'bbs.archlinux.org  ·  #archlinux on Libera Chat']];
  L.forEach(([a, b], i) => { const yy = y + 170 + i * 110; txt(ctx, a, x + 50, yy, { fam: 'Nunito-900', size: 38, color: C.deep }); txt(ctx, b, x + 50, yy + 46, { fam: 'JBM-800', size: 28, color: C.ink, maxW: w - 100 }); });
}

function drawTut(ctx, t, S, CH) {
  const blocks = SCENES[S.id];
  let blk = blocks[0];
  for (const b of blocks) if (t >= S.L(b.line) - 0.05) blk = b;
  const g = ctx.createLinearGradient(0, 0, 0, H); g.addColorStop(0, '#101B26'); g.addColorStop(1, '#0B121A');
  ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);
  ctx.strokeStyle = 'rgba(240,238,230,0.04)'; ctx.lineWidth = 1;
  for (let xx = 0; xx < W; xx += 60) { ctx.beginPath(); ctx.moveTo(xx, 0); ctx.lineTo(xx, H); ctx.stroke(); }
  hdr(ctx, t, S, blk);
  const X = 50, Y = 150, Wd = 1270, Hd = 690;
  const k = ease.out(prog(t, S.L(blk.line) - 0.05, 0.3));
  ctx.save(); ctx.globalAlpha = k; ctx.translate((1 - k) * -40, 0);
  if (blk.custom === 'roadmap') roadmap(ctx, t, S, X, Y, Wd, Hd);
  else if (blk.custom === 'warning') warning(ctx, t, S, X, Y, Wd, Hd);
  else if (blk.custom === 'checklist') checklist(ctx, t, S, CH, X, Y, Wd, Hd);
  else if (blk.custom === 'bios') bios(ctx, t, S, X, Y, Wd, Hd);
  else if (blk.custom === 'bootmenu') bootmenu(ctx, t, S, X, Y, Wd, Hd);
  else if (blk.custom === 'cfdisk') cfdisk(ctx, t, S, X, Y, Wd, Hd);
  else if (blk.custom === 'links') links(ctx, t, S, X, Y, Wd, Hd);
  else termBlock(ctx, t, S, blk, X, Y, Wd, Hd);
  ctx.restore();
  sidebar(ctx, t, S, blk, CH);
  const A = actor(ctx, CH, S, t);
  const femboyHere = S.id === 'tut_intro' || S.id === 'tut_reboot';
  if (femboyHere) {
    A('femboy', { x: 1760, y: 930, s: 0.72, mood: S.speaking('femboy', t) ? 'happy' : 'smug', prop: 'blahaj', look: -0.5 });
    A('claude', { x: 1480, y: 900, s: 0.6, mood: 'happy', look: -0.6 });
  } else {
    A('claude', { x: 1650, y: 900, s: 0.65, mood: 'happy', look: -0.8 });
    // easter egg: a shark peeking in from the right edge
    if (CH.drawBlahaj && (S.id === 'tut_disk' || S.id === 'tut_boot')) CH.drawBlahaj(ctx, 1905, 760, 0.7, t, { flip: true, peek: 0.5 });
  }
  if (S.id === 'tut_reboot') {
    A('gamer', { x: 1250, y: 960, s: 0.7, enter: S.L(3) - 0.3, exit: S.E(4) + 0.2, mood: t > S.L(4) ? 'sad' : 'excited', prop: 'monster', look: 0.6 });
    if (CH.drawCanStack && t > S.L(3) - 0.3 && t < S.E(4) + 0.4) CH.drawCanStack(ctx, 1080, 1000, 70, 6, t);
  }
  if (S.card) sectionCard(ctx, t, ...S.card);
}

export default {
  id: ORDER,
  render: drawTut,
  cues(S) {
    const c = [];
    for (const b of SCENES[S.id]) {
      c.push({ t: S.L(b.line) - 0.05, name: b.custom ? 'pop' : 'tick', gain: 0.3 });
      if (b.cmds) { let n = 0; for (const l of b.cmds) if ('#$>'.includes(l[0])) n += l.length; for (let i = 0; i < Math.min(40, n); i += 2) c.push({ t: S.L(b.line) + 0.25 + i / 70, name: ['key1', 'key2', 'key3'][i % 3], gain: 0.12 }); }
    }
    if (S.id === 'tut_intro') c.push({ t: S.tag('warn'), name: 'error', gain: 0.3 });
    return c;
  },
};
