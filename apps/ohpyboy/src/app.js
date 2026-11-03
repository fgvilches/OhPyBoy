const $ = (s) => document.querySelector(s);
const canvas = $('#screen');
const ctx = canvas.getContext('2d');
const status = $('#status');
const W = 240, H = 160;
const buf = new Uint8ClampedArray(W * H * 4);
const img = new ImageData(buf, W, H);

// Pacing: GBA frame period 16.741 ms. Gate the loop so we never run faster.
const FRAME_MS = 1000 / 59.7275;
let lastFrame = 0;
let running = true;
let paused = false;

const acc = { n: 0, minFps: Infinity, maxFps: 0, fpsSum: 0, run: 0 };
let last = performance.now();

async function runFrame() {
  const t0 = performance.now();
  // Single IPC: returns raw binary framebuffer (no JSON, no second round-trip).
  const res = await window.__TAURI__.core.invoke('run_frame');
  const t1 = performance.now();
  // res is an ArrayBuffer (binary response).
  buf.set(new Uint8Array(res));
  const t2 = performance.now();
  ctx.putImageData(img, 0, 0);
  const t3 = performance.now();

  acc.run += t1 - t0;
  acc.n++;
  const now = performance.now();
  const fps = 1000 / (now - last);
  last = now;
  acc.fpsSum += fps;
  if (fps < acc.minFps) acc.minFps = fps;
  if (fps > acc.maxFps) acc.maxFps = fps;
  const frame = await window.__TAURI__.core.invoke('frame_number');
  status.textContent = `frame ${frame} · ${fps.toFixed(1)} fps${paused ? ' · PAUSED' : ''}`;

  if (acc.n >= 120) {
    const n = acc.n;
    console.log(`[measure] n=${n} fps avg=${(acc.fpsSum/n).toFixed(1)} min=${acc.minFps.toFixed(1)} max=${acc.maxFps.toFixed(1)} | run_frame+fb=${(acc.run/n).toFixed(2)}ms copy=${((t2-t1)/1).toFixed(2)}ms paint=${((t3-t2)/1).toFixed(2)}ms`);
    acc.run = acc.fpsSum = 0; acc.n = 0; acc.minFps = Infinity; acc.maxFps = 0;
  }
}

$('#btn-run').addEventListener('click', () => { paused = !paused; if (!paused) loop(); });
$('#btn-reset').addEventListener('click', async () => {
  await window.__TAURI__.core.invoke('reset');
  status.textContent = 'reset';
});

// Pause when tab hidden (C4).
document.addEventListener('visibilitychange', () => {
  if (document.hidden) { paused = true; status.textContent += ' · hidden'; }
});

async function loop() {
  if (!running || paused) return;
  const now = performance.now();
  const elapsed = now - lastFrame;
  if (elapsed < FRAME_MS) {
    setTimeout(loop, FRAME_MS - elapsed);
    return;
  }
  lastFrame = now - (elapsed % FRAME_MS);
  await runFrame();
  requestAnimationFrame(loop);
}
loop();
