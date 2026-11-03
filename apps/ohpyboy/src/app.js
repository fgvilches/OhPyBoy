const $ = (s) => document.querySelector(s);
const canvas = $('#screen');
const ctx = canvas.getContext('2d');
const status = $('#status');
let frame = 0;
let last = performance.now();
let fps = 0;

async function runFrame() {
  const info = await window.__TAURI__.core.invoke('run_frame');
  const bytes = await window.__TAURI__.core.invoke('framebuffer');
  const img = new ImageData(new Uint8ClampedArray(bytes), info.width, info.height);
  // draw scaled
  const off = new OffscreenCanvas(info.width, info.height);
  off.getContext('2d').putImageData(img, 0, 0);
  ctx.imageSmoothingEnabled = false;
  ctx.drawImage(off, 0, 0, canvas.width, canvas.height);
  frame = info.frame;
  const now = performance.now();
  fps = 1000 / (now - last);
  last = now;
  status.textContent = `frame ${frame} · ${fps.toFixed(1)} fps`;
}

$('#btn-run').addEventListener('click', runFrame);
$('#btn-reset').addEventListener('click', async () => {
  await window.__TAURI__.core.invoke('reset');
  status.textContent = 'reset';
});

// auto-run to measure presentation path
let running = true;
async function loop() {
  if (running) { await runFrame(); requestAnimationFrame(loop); }
}
loop();
