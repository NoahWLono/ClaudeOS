// preview_chars.mjs : contact sheets + timing for characters.mjs
// usage: node preview_chars.mjs [sheet ...]   (sheets: lineup moods talk props extras detail small flip time; default all)
// env CHARS=/path/to/characters.mjs to preview a different copy; OUT=dir for output.
import fs from 'fs';
import path from 'path';
import { pathToFileURL } from 'url';
import { createCanvas, GlobalFonts } from '@napi-rs/canvas';

const F = '/home/user/ClaudeOS/video/assets/fonts/';
for (const f of fs.readdirSync(F)) GlobalFonts.registerFromPath(F + f, f.replace(/\.(ttf|woff)$/, ''));

const OUT = process.env.OUT || new URL('../build/chars/', import.meta.url).pathname;
fs.mkdirSync(OUT, { recursive: true });
const modPath = process.env.CHARS ? pathToFileURL(path.resolve(process.env.CHARS)).href : new URL('./characters.mjs', import.meta.url).href;
const C = await import(modPath + '?v=' + Date.now());
const { CHARACTER_IDS, CHAR_INFO, drawCharacter } = C;

const want = new Set(process.argv.slice(2));
const on = (k) => want.size === 0 || want.has(k);
const T = Number(process.env.T || 0.7);
const MOODS = ['neutral', 'happy', 'excited', 'shock', 'smug', 'angry', 'sad'];

function sheet(name, w, h, bg, fn) {
  const cv = createCanvas(w, h);
  const ctx = cv.getContext('2d');
  ctx.fillStyle = bg; ctx.fillRect(0, 0, w, h);
  fn(ctx);
  fs.writeFileSync(path.join(OUT, name), cv.toBuffer('image/png'));
  console.log('wrote', name);
}
function label(ctx, str, x, y, color = '#141413', size = 22) {
  ctx.font = `${size}px "Nunito-900"`; ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
  ctx.fillStyle = color; ctx.fillText(str, x, y);
}
function baseline(ctx, x0, x1, y) { ctx.strokeStyle = 'rgba(20,20,19,0.12)'; ctx.lineWidth = 2; ctx.beginPath(); ctx.moveTo(x0, y); ctx.lineTo(x1, y); ctx.stroke(); }

if (on('lineup')) {
  const cols = 7, cw = 270, ch = 360;
  sheet('lineup.png', cols * cw, 2 * ch + 20, '#F0EEE6', (ctx) => {
    CHARACTER_IDS.forEach((id, i) => {
      const cx = (i % cols) * cw + cw / 2, by = Math.floor(i / cols) * ch + 290;
      baseline(ctx, cx - cw / 2 + 10, cx + cw / 2 - 10, by);
      drawCharacter(ctx, id, { x: cx, y: by, s: 0.6, t: T + i * 0.37 });
      label(ctx, CHAR_INFO[id].name, cx, by + 34, '#141413', 20);
      ctx.fillStyle = CHAR_INFO[id].color; ctx.fillRect(cx - 30, by + 50, 60, 6);
    });
  });
}

if (on('moods')) {
  for (const id of (process.env.MOOD_IDS || 'claude,gamer,femboy,wiki').split(',')) {
    const cw = 290, s = 0.62;
    sheet(`moods_${id}.png`, MOODS.length * cw, 380, '#F0EEE6', (ctx) => {
      MOODS.forEach((m, i) => {
        const cx = i * cw + cw / 2, by = 310;
        baseline(ctx, cx - cw / 2 + 10, cx + cw / 2 - 10, by);
        drawCharacter(ctx, id, { x: cx, y: by, s, t: T, mood: m, look: m === 'smug' ? 0.6 : 0 });
        label(ctx, m, cx, by + 40);
      });
    });
  }
}

if (on('talk')) {
  const ids = (process.env.TALK_IDS || 'claude,gamer,announcer,tux').split(','), talks = [0, 0.3, 0.6, 1];
  const cw = 300, rh = 330;
  sheet('talk.png', talks.length * cw, ids.length * rh, '#F0EEE6', (ctx) => {
    ids.forEach((id, r) => talks.forEach((k, c) => {
      const cx = c * cw + cw / 2, by = r * rh + 280;
      drawCharacter(ctx, id, { x: cx, y: by, s: 0.6, t: T, talk: k });
      label(ctx, `${id} talk=${k}`, cx, by + 30, '#141413', 18);
    }));
  });
}

if (on('props')) {
  sheet('props.png', 1920, 1300, '#F0EEE6', (ctx) => {
    const { drawSpark, drawArchPeak, drawRainbowInfinity, drawSock, drawCan, drawHandheld, drawHeart } = C;
    drawSpark(ctx, 120, 120, 80, '#D97757', T); label(ctx, 'drawSpark', 120, 230);
    drawArchPeak(ctx, 330, 190, 150, '#1793D1'); label(ctx, 'drawArchPeak', 330, 230);
    drawRainbowInfinity(ctx, 560, 120, 220, T); label(ctx, 'drawRainbowInfinity', 560, 230);
    drawSock(ctx, 760, 30, 180, ['#FF8FC7', '#FFFFFF'], 0); drawSock(ctx, 840, 30, 180, ['#7EC8F0', '#FF8FC7', '#FFFFFF', '#FF8FC7'], 0.15); label(ctx, 'drawSock', 810, 230);
    drawCan(ctx, 990, 200, 160, 'GAMER FUEL', '#39FF14'); label(ctx, 'drawCan', 990, 230);
    drawHandheld(ctx, 1230, 120, 300, T); label(ctx, 'drawHandheld', 1230, 230);
    drawHeart(ctx, 1480, 110, 50, '#FF8FC7'); drawHeart(ctx, 1580, 120, 30, '#E8413C'); label(ctx, 'drawHeart', 1530, 230);
    drawSpark(ctx, 1760, 120, 60, '#141413', T + 1); label(ctx, 'spark ink', 1760, 230);
    const row = [
      ['claude', 'water'], ['claude', 'laptop'], ['gamer', 'can'], ['gamer', 'controller'], ['gamer', 'handheld'], ['femboy', 'laptop'], ['wiki', 'book'],
    ];
    row.forEach(([id, p], i) => { const cx = 140 + i * 272, by = 700; baseline(ctx, cx - 120, cx + 120, by); drawCharacter(ctx, id, { x: cx, y: by, s: 0.62, t: T, prop: p }); label(ctx, `${id} / ${p}`, cx, by + 34); });
    const row2 = [
      ['wiki', { prop: 'tabs' }], ['goblin', { sign: 'I READ THE WIKI' }], ['goblin', { sign: 'btw' }], ['goblin', { sign: 'have you tried reading the manual page first?' }], ['winupdate', { sign: 'Working on updates 1%' }], ['claude', { prop: 'water', flip: true, mood: 'smug' }],
    ];
    row2.forEach(([id, o], i) => { const cx = 150 + i * 320, by = 1220; baseline(ctx, cx - 140, cx + 140, by); drawCharacter(ctx, id, { x: cx, y: by, s: 0.62, t: T, ...o }); label(ctx, `${id} ${o.sign ? '"' + o.sign.slice(0, 16) + '"' : o.prop || ''}${o.flip ? ' flip' : ''}`, cx, by + 34, '#141413', 18); });
  });
}

if (on('detail')) {
  // each character at s=1 for close inspection, 2 per image
  for (let i = 0; i < CHARACTER_IDS.length; i += 2) {
    const ids = CHARACTER_IDS.slice(i, i + 2);
    sheet(`detail_${ids.join('_')}.png`, 1100, 560, '#F0EEE6', (ctx) => {
      ids.forEach((id, k) => { const cx = 275 + k * 550, by = 500; baseline(ctx, cx - 250, cx + 250, by); drawCharacter(ctx, id, { x: cx, y: by, s: 1, t: T, talk: 0 }); });
    });
  }
}

if (on('small')) {
  // readability at s=0.5 and on a dark background
  sheet('small_dark.png', 14 * 150, 300, '#1B1D24', (ctx) => {
    CHARACTER_IDS.forEach((id, i) => { const cx = 75 + i * 150, by = 250; drawCharacter(ctx, id, { x: cx, y: by, s: 0.5 * (['goblin', 'haiku', 'sonnet', 'fable'].includes(id) ? 1 : 0.62) / 0.62 * 0.62, t: T + i }); label(ctx, id, cx, by + 26, '#F0EEE6', 16); });
  });
}

if (on('flip')) {
  sheet('flip.png', 1600, 380, '#F0EEE6', (ctx) => {
    ['claude', 'gamer', 'femboy', 'winupdate', 'goblin'].forEach((id, i) => {
      const cx = 160 + i * 320, by = 320;
      drawCharacter(ctx, id, { x: cx, y: by, s: 0.6, t: T, flip: true, look: 1, sign: id === 'goblin' ? 'FLIPPED' : null, prop: id === 'gamer' ? 'can' : null });
      label(ctx, `${id} flip look=+1`, cx, by + 30, '#141413', 18);
    });
  });
}

if (on('extras')) {
  // Blahaj plush shark, Monster-style can, can pyramid, and the character props that use them
  const { drawBlahaj, drawCan, drawCanStack } = C;
  sheet('extras.png', 1920, 1260, '#F0EEE6', (ctx) => {
    const L = (s, x, y) => label(ctx, s, x, y, '#141413', 18);
    drawBlahaj(ctx, 180, 150, 1, T); L('blahaj', 180, 250);
    drawBlahaj(ctx, 480, 150, 1, T + 1.3, { squish: 0.5 }); L('squish .5', 480, 250);
    drawBlahaj(ctx, 780, 150, 1, T, { squish: 1 }); L('squish 1', 780, 250);
    drawBlahaj(ctx, 1080, 150, 1, T + 0.6, { flip: true, rot: -0.25 }); L('flip + rot', 1080, 250);
    // peek demos: the wall is drawn by the caller at the clip edge
    for (const [i, pk] of [[0, 0.5], [1, 1]]) {
      const cx = 1380 + i * 300, clipX = cx + (-150 + 190 * pk);
      drawBlahaj(ctx, cx, 150, 1, T, { peek: pk });
      ctx.fillStyle = '#B9A58A'; ctx.fillRect(clipX - 90, 40, 90, 200); ctx.strokeStyle = '#141413'; ctx.lineWidth = 5; ctx.strokeRect(clipX - 90, 40, 90, 200);
      L(`peek ${pk}`, cx, 250);
    }
    drawCan(ctx, 110, 640, 200, 'MONSTER'); L('MONSTER h=200', 110, 670);
    drawCan(ctx, 260, 640, 120, 'MONSTER'); drawCan(ctx, 330, 640, 60, 'MONSTER'); L('h=120 / 60', 290, 670);
    drawCan(ctx, 440, 640, 160, 'GAMER FUEL', '#39FF14'); L('GAMER FUEL', 440, 670);
    drawCanStack(ctx, 680, 640, 90, 3, T); L('stack n=3', 680, 670);
    drawCanStack(ctx, 960, 640, 90, 6, T); L('stack n=6', 960, 670);
    drawCanStack(ctx, 1320, 640, 80, 10, T); L('stack n=10', 1320, 670);
    drawCanStack(ctx, 1700, 640, 60, 15, T); L('stack n=15', 1700, 670);
    const row = [['femboy', { prop: 'blahaj' }], ['femboy', { prop: 'blahaj', mood: 'happy', flip: true }], ['gamer', { prop: 'monster', mood: 'excited' }], ['gamer', { prop: 'monster', flip: true }], ['gamer', { prop: 'can' }], ['femboy', { prop: 'blahaj', alpha: 0.5 }]];
    row.forEach(([id, o], i) => { const cx = 170 + i * 316, by = 1170; baseline(ctx, cx - 140, cx + 140, by); drawCharacter(ctx, id, { x: cx, y: by, s: 0.9, t: T, ...o }); L(`${id} ${o.prop}${o.flip ? ' flip' : ''}${o.alpha ? ' a=.5' : ''}`, cx, by + 30); });
  });
}

if (on('time')) {
  // "record" = JS + command recording only; "raster" = includes Skia rasterization (forced flush after each call)
  const cv = createCanvas(1920, 1080), ctx = cv.getContext('2d');
  const flush = () => ctx.getImageData(0, 0, 1, 1);
  const N = Number(process.env.N || 40), S = Number(process.env.S || 1);
  const props = { claude: 'laptop', gamer: 'handheld', femboy: 'laptop', wiki: 'tabs' };
  const opts = (id, i) => ({ x: 400 + (i % 10) * 120, y: 900, s: S, t: i / 30, talk: (i % 7) / 6, mood: MOODS[i % 7], look: Math.sin(i), prop: props[id] || null, sign: id === 'goblin' ? 'I READ THE WIKI' : null });
  const rows = [];
  for (const id of CHARACTER_IDS) {
    for (let i = 0; i < 5; i++) drawCharacter(ctx, id, opts(id, i));
    flush();
    let t0 = process.hrtime.bigint();
    for (let i = 0; i < N; i++) drawCharacter(ctx, id, opts(id, i));
    const rec = Number(process.hrtime.bigint() - t0) / 1e6 / N;
    flush();
    t0 = process.hrtime.bigint();
    for (let i = 0; i < N; i++) { drawCharacter(ctx, id, opts(id, i)); flush(); }
    const ras = Number(process.hrtime.bigint() - t0) / 1e6 / N;
    t0 = process.hrtime.bigint();
    for (let i = 0; i < N; i++) { drawCharacter(ctx, id, { ...opts(id, i), alpha: 0.5 }); flush(); }
    const fad = Number(process.hrtime.bigint() - t0) / 1e6 / N;
    rows.push([id, rec, ras, fad]);
  }
  const mean = (k) => rows.reduce((a, r) => a + r[k], 0) / rows.length;
  console.log(`s=${S}  (ms/call)   record   raster   raster@alpha0.5`);
  for (const [id, a, b, c] of rows) console.log(id.padEnd(12), a.toFixed(3).padStart(8), b.toFixed(3).padStart(8), c.toFixed(3).padStart(10));
  console.log('mean'.padEnd(12), mean(1).toFixed(3).padStart(8), mean(2).toFixed(3).padStart(8), mean(3).toFixed(3).padStart(10));
}
