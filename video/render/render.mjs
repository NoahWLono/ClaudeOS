// CLI:
//   node render.mjs still <sceneId> <t> [out.png]
//   node render.mjs contact <sceneId> [cols] [rows] [out.png]   grid of frames across a scene
//   node render.mjs range <f0> <f1> <out.mp4>                   raw frames -> ffmpeg
//   node render.mjs all [jobs]                                  parallel full render -> build/video.mp4
//   node render.mjs timeline                                    write build/timeline.json (lines, music, sfx cues)
import { spawn } from 'child_process';
import fs from 'fs';
import path from 'path';
import os from 'os';
import { createCanvas } from '@napi-rs/canvas';
import { loadAll, renderFrame, newCanvas, FPS } from './engine.mjs';
import { ROOT } from './timeline.mjs';
import { W, H } from './lib.mjs';

const [cmd, ...args] = process.argv.slice(2);
const BUILD = path.join(ROOT, 'build');
fs.mkdirSync(BUILD, { recursive: true });

async function still() {
  const world = await loadAll();
  const [id, t, out] = args;
  const sc = world.TL.byId[id];
  const f = sc.frame0 + Math.min(sc.frames - 1, Math.round(parseFloat(t) * FPS));
  const [c, ctx] = newCanvas();
  renderFrame(ctx, world, f);
  fs.writeFileSync(out || path.join(BUILD, `still_${id}.png`), await c.encode('png'));
}

async function contact() {
  const world = await loadAll();
  const [id, cols = 4, rows = 3, out] = args;
  const sc = world.TL.byId[id];
  const n = cols * rows;
  const sheet = createCanvas(W, H), sx = sheet.getContext('2d');
  sx.fillStyle = '#000'; sx.fillRect(0, 0, W, H);
  const [c, ctx] = newCanvas();
  const cw = W / cols, chh = H / rows;
  for (let i = 0; i < n; i++) {
    const t = (sc.dur * (i + 0.5)) / n;
    renderFrame(ctx, world, sc.frame0 + Math.round(t * FPS));
    sx.drawImage(c, (i % cols) * cw + 2, Math.floor(i / cols) * chh + 2, cw - 4, chh - 4);
    sx.fillStyle = '#ff0'; sx.font = '22px JBM-800'; sx.fillText(t.toFixed(1) + 's', (i % cols) * cw + 8, Math.floor(i / cols) * chh + 26);
  }
  fs.writeFileSync(out || path.join(BUILD, `contact_${id}.png`), await sheet.encode('png'));
  console.log(`${id}: ${sc.dur.toFixed(2)}s`);
}

async function range() {
  const world = await loadAll();
  const [f0, f1, out] = [parseInt(args[0]), parseInt(args[1]), args[2]];
  const ff = spawn('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgba', '-s', `${W}x${H}`, '-r', `${FPS}`, '-i', '-',
    '-c:v', 'libx264', '-preset', 'medium', '-crf', '19', '-tune', 'animation', '-pix_fmt', 'yuv420p', '-g', '60', out], { stdio: ['pipe', 'inherit', 'inherit'] });
  const [c, ctx] = newCanvas();
  const t0 = Date.now();
  for (let f = f0; f < f1; f++) {
    renderFrame(ctx, world, f);
    const buf = c.data();
    if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
    if ((f - f0) % 300 === 0) console.log(`[${path.basename(out)}] ${f - f0}/${f1 - f0} ${((Date.now() - t0) / (f - f0 + 1)).toFixed(0)}ms/f`);
  }
  ff.stdin.end();
  await new Promise(r => ff.on('close', r));
}

async function all() {
  const world = await loadAll();
  const jobs = parseInt(args[0] || os.cpus().length);
  const total = world.TL.frames;
  const chunks = jobs * 3; const per = Math.ceil(total / chunks);
  const parts = [];
  for (let i = 0; i < chunks; i++) parts.push([i * per, Math.min(total, (i + 1) * per), path.join(BUILD, `part_${String(i).padStart(3, '0')}.mp4`)]);
  console.log(`total ${total} frames (${(total / FPS).toFixed(1)}s) in ${chunks} parts, ${jobs} jobs`);
  let next = 0;
  const run = () => new Promise(res => {
    const go = () => {
      if (next >= parts.length) return res();
      const [a, b, o] = parts[next++];
      const p = spawn(process.execPath, [path.join(ROOT, 'render/render.mjs'), 'range', a, b, o], { stdio: 'inherit' });
      p.on('close', code => { if (code) console.error('part failed', o); go(); });
    };
    go();
  });
  await Promise.all(Array.from({ length: jobs }, run));
  fs.writeFileSync(path.join(BUILD, 'parts.txt'), parts.map(p => `file '${p[2]}'`).join('\n'));
  await new Promise(r => spawn('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', path.join(BUILD, 'parts.txt'), '-c', 'copy', path.join(BUILD, 'video.mp4')], { stdio: 'inherit' }).on('close', r));
  console.log('wrote build/video.mp4');
}

async function timeline() {
  const world = await loadAll();
  const { TL, mods, helpers } = world;
  const cues = [], lines = [], music = [];
  TL.scenes.forEach((sc, si) => {
    const S = helpers[si];
    music.push({ id: sc.id, track: sc.music, start: sc.start, dur: sc.dur });
    for (const l of sc.lines) {
      lines.push({ key: l.key, who: l.who, start: sc.start + l.start, dur: l.dur });
      if (l.sfx) cues.push({ t: sc.start + l.start - (l.sfx === 'boom' ? 0.02 : 0), name: l.sfx, gain: 0.8 });
    }
    const next = TL.scenes[si + 1];
    if (next && (next.transIn ?? 'wipe') === 'wipe') cues.push({ t: next.start - 0.28, name: 'whoosh', gain: 0.45 });
    if (sc.card) cues.push({ t: sc.start + 0.08, name: 'stamp', gain: 0.6 }, { t: sc.start + 2.45, name: 'swoosh_up', gain: 0.35 });
    const m = mods[sc.id];
    if (m && m.cues) for (const c of m.cues(S)) cues.push({ ...c, t: sc.start + c.t });
  });
  cues.sort((a, b) => a.t - b.t);
  fs.writeFileSync(path.join(BUILD, 'timeline.json'), JSON.stringify({ total: TL.total, fps: FPS, music, lines, cues }, null, 1));
  console.log(`timeline: ${TL.total.toFixed(1)}s, ${lines.length} lines, ${cues.length} cues`);
  for (const sc of TL.scenes) console.log(`  ${sc.id.padEnd(18)} ${sc.start.toFixed(1).padStart(6)}  +${sc.dur.toFixed(1)}`);
}

({ still, contact, range, all, timeline })[cmd]().catch(e => { console.error(e); process.exit(1); });
