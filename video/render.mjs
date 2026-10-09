// Renders video/index.html frame by frame with Playwright, then encodes with ffmpeg.
// Usage: node render.mjs [out.mp4] [--fps 30] [--workers 4] [--from 0 --to 132] [--stills 5,20,40]
import { chromium } from 'playwright';
import { spawn } from 'node:child_process';
import { mkdirSync, rmSync, existsSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const dir = path.dirname(fileURLToPath(import.meta.url));
const args = process.argv.slice(2);
const opt = (k, d) => { const i = args.indexOf('--' + k); return i >= 0 ? args[i + 1] : d; };
const out = args[0] && !args[0].startsWith('--') ? args[0] : path.join(dir, 'video_sin_audio.mp4');
const fps = +opt('fps', 30), workers = +opt('workers', 4);
const exe = process.env.CHROMIUM || '/opt/pw-browsers/chromium-1194/chrome-linux/chrome';
const url = 'file://' + path.join(dir, 'index.html') + '?render';

async function openPage(browser) {
  const page = await browser.newPage({ viewport: { width: 1920, height: 1080 } });
  await page.goto(url);
  await page.evaluate(() => window.ready);
  return page;
}

const browser = await chromium.launch(existsSync(exe) ? { executablePath: exe } : {});

const stills = opt('stills');
if (stills) {
  const page = await openPage(browser);
  mkdirSync(path.join(dir, 'stills'), { recursive: true });
  for (const s of stills.split(',')) {
    await page.evaluate(t => window.render(t), +s);
    await page.screenshot({ path: path.join(dir, 'stills', `t${String(s).padStart(6, '0')}.jpg`), type: 'jpeg', quality: 85 });
  }
  await browser.close();
  process.exit(0);
}

const duration = await (await openPage(browser)).evaluate(() => window.DURATION);
const from = +opt('from', 0), to = +opt('to', duration);
const total = Math.round((to - from) * fps);
const tmp = path.join(dir, '.parts'); rmSync(tmp, { recursive: true, force: true }); mkdirSync(tmp);
const chunk = Math.ceil(total / workers);
let done = 0;

async function work(w) {
  const a = w * chunk, b = Math.min(total, a + chunk);
  if (a >= b) return null;
  const page = await openPage(browser);
  const file = path.join(tmp, `part${w}.mp4`);
  const ff = spawn('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', String(fps), '-c:v', 'mjpeg', '-i', '-',
    '-c:v', 'libx264', '-preset', 'medium', '-crf', '18', '-pix_fmt', 'yuv420p', file], { stdio: ['pipe', 'inherit', 'inherit'] });
  for (let f = a; f < b; f++) {
    await page.evaluate(t => window.render(t), from + f / fps);
    const buf = await page.screenshot({ type: 'jpeg', quality: 92 });
    if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
    if (++done % 150 === 0) console.log(`${done}/${total} frames`);
  }
  ff.stdin.end();
  await new Promise(r => ff.on('close', r));
  return file;
}

const parts = (await Promise.all([...Array(workers)].map((_, w) => work(w)))).filter(Boolean);
await browser.close();
const list = path.join(tmp, 'list.txt');
const { writeFileSync } = await import('node:fs');
writeFileSync(list, parts.map(p => `file '${p}'`).join('\n'));
await new Promise(r => spawn('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', list, '-c', 'copy', out], { stdio: 'inherit' }).on('close', r));
rmSync(tmp, { recursive: true, force: true });
console.log('wrote', out);
