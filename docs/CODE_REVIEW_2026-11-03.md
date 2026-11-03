# Auditoría de código — OhPyBoy (rebuild Rust/Tauri)

**Revisor:** shift (asistido) · **Fecha:** 2026-11-03 · **Commit base de referencia:** docs 0.2 / core walking-skeleton.

> Petición: segunda opinión sobre el rebuild, con foco en el **alto consumo de CPU del runner de Rust** que reportó el otro agente. Veredicto corto arriba, evidencia abajo.

---

## TL;DR

1. **El build no es el problema de diseño.** `cargo build` de un proyecto Tauri es genuinamente pesado (árbol de deps grande, `target/` ya en 2.4 GB). Con varios agentes compitiendo por 6 cores, se siente peor de lo que es. En el momento de esta auditoría **no había ningún proceso `cargo`/`rustc`/`tauri` vivo** y el load average era 1.41 — la máquina está sana. Buena parte del "high CPU" es contención entre agentes, no el proyecto.
2. **Sí hay un quemador de CPU real, pero está en la app corriendo, no en el compilador.** El loop del frontend corre sin pacing (a tope de un core del WebView) y el framebuffer cruza el IPC como `Vec<u8>` por el canal `invoke` estándar → se **serializa a JSON** 60+ veces por segundo. Ese es el costo oculto. Su propia `ARCHITECTURE.md` ya dice cómo evitarlo (candidato A: `tauri::ipc::Response`), pero el código no lo hace todavía.
3. **El diseño documentado es de primer nivel.** Los docs (`REWRITE_AUDIT`, `ARCHITECTURE`, `PRODUCT_PLAN`, `DESIGN`) son honestos y correctos. La decisión "leer, no portar" el Python es la acertada. El esqueleto respeta el contrato. Esto no está "confundido" — está en Fase 0/1 y es coherente.

---

## Lo que está bien (no tocar)

- **Separación de capas correcta.** `crates/core` sin I/O, sin reloj, sin Tauri; adapter en el shell; UI en WebView. Es exactamente la arquitectura que quiere un emulador y la que evita el "grafo mutable y circular" del Python legacy.
- **Core determinista y honesto.** `run_frame` admite en el doc que genera un patrón de prueba ("walking skeleton"). No miente sobre emular. Los tests (`frame_advances`, `framebuffer_size`, `reset_clears`) son los correctos para este estado.
- **`bus.rs` ya hace lo difícil bien:** BIOS modelada como 16 KB reales con open-bus para el resto (no el típico error de rellenar 1 MB), mirrors por región con máscaras correctas, errores tipados. Es el módulo más maduro y está sólido.
- **Docs de referencia.** `REWRITE_AUDIT.md` es modélico: mapa por módulo, problemas concretos del Python (plataforma dentro del core, stubs silenciosos, `load32` sin máscara de 32 bits), política de evidencia ("abrió la ROM" ≠ "emula el juego"). Mantené esa disciplina.

---

## Hallazgos de CPU (ordenados por impacto)

### 🔴 C1 — El framebuffer viaja por IPC como JSON. **Este es el costo real.**
`src-tauri/src/lib.rs`:
```rust
#[tauri::command]
fn framebuffer(state: tauri::State<AppState>) -> Vec<u8> { ... }   // 153.6 KB
```
Un comando `invoke` que devuelve `Vec<u8>` **no** manda bytes crudos: Tauri lo serializa por `serde_json` a un array de 157 000 números, y el WebView lo pasa por `JSON.parse`. A 60 fps son ~9 MB/s de texto JSON generado y parseado en cada lado. Eso es CPU puro, sostenido, tanto en Rust como en el renderer.

**La ironía:** `ARCHITECTURE.md` (candidato A) ya dice la solución textual: `invoke` con **`tauri::ipc::Response(Vec<u8>)`**, que manda el buffer como binario sin JSON. El código quedó a medio camino del propio plan.

**Fix:** envolver el retorno en `tauri::ipc::Response::new(bytes)` (o servir el frame por el custom-protocol, candidato B). En JS, leer el `ArrayBuffer` de la respuesta en vez de un array de números.

### 🔴 C2 — El loop de presentación corre sin pacing (quema un core entero).
`src/app.js`:
```js
let running = true;
async function loop() {
  if (running) { await runFrame(); requestAnimationFrame(loop); }
}
loop();
```
Corre tan rápido como el sistema permita, sin límite a 59.7275 Hz. En una pantalla de 120 Hz, son el doble de frames que los que un GBA produce, cada uno pagando C1. `ARCHITECTURE.md` especifica pacing con `spin_sleep` en el hilo de emulación; el esqueleto aún no lo tiene, y mientras tanto el rAF a tope es el que se ve en el monitor de actividad como "la app de Rust comiéndose la CPU".

**Fix inmediato (barato):** gate temporal en el loop (acumulador a 16.74 ms) o `setTimeout` a 1000/59.7275. **Fix correcto (Fase 1):** mover el ritmo al hilo de emulación del adapter y que la UI solo presente el último frame disponible, como ya dice el doc.

### 🟠 C3 — Dos round-trips de IPC por frame.
`runFrame()` hace `invoke('run_frame')` **y** `invoke('framebuffer')` por cada frame. Son dos cruces de puente + dos locks del `Mutex`. `run_frame` puede devolver el `FrameInfo` y el buffer binario en una sola llamada, o usar el custom-protocol para el frame y dejar `invoke` solo para control.

### 🟠 C4 — Sin botón de pausa real; el trabajo nunca cesa.
`running` arranca en `true` y nada lo pone en `false`. No hay forma de parar el loop desde la UI (el botón Reset solo invoca `reset`, no pausa). Si dejás la ventana abierta en segundo plano, sigue quemando. `DESIGN.md` pide Play/Pause como transporte primario — todavía no existe. Añadir pausa y, de paso, parar el loop cuando `document.hidden` (ventana oculta/minimizada).

### 🟡 C5 — Copia byte-a-byte en el serializador del framebuffer.
```rust
for &px in fb { out.push((px>>16) as u8); out.push((px>>8) as u8); ... }
```
Cuatro `push` por píxel × 38 400 píxeles. Menor frente a C1, pero cuando arregles C1 conviene reempaquetar con `to_le_bytes`/`chunks` o exponer el buffer ya en RGBA para copiar de un slice. Secundario.

---

## Otros hallazgos (no-CPU, pero reales)

### 🟠 D1 — `tauri.conf.json` tiene metadata copiada de hShop Glass.
```json
"longDescription": "Browse and download 3DS titles from hShop with a native Liquid Glass interface."
```
Esto es de otro proyecto. OhPyBoy es un emulador GBA, no un descargador de 3DS. Además:
- `"version": "1.0.0"` contradice el workspace (`0.1.0`). Un emulador en walking-skeleton no es 1.0.0.
- `"category": "DeveloperTool"` — debería ser `"public.app-category.games"` o Entertainment.

### 🟡 D2 — `core_bridge.rs` es módulo muerto.
`mod core_bridge;` importa un archivo de una sola línea-comentario. Genera warning y ruido. O lo poblás ya con la lógica del adapter (sesión, hilo, pacing — que es justo lo que falta) o lo quitás hasta que haga falta.

### 🟡 D3 — README desactualizado.
Sigue diciendo *"A Python based gba emulator · Currently not working"*. El rebuild es Rust/Tauri. El README debería reflejar el estado real y la decisión de arquitectura, aunque sea un párrafo.

### 🟡 D4 — `csp: null` y toolchain mono-target.
- `security.csp: null` es aceptable en dev, pero anotarlo como deuda para release (define CSP antes de publicar).
- `rust-toolchain.toml` fija solo `aarch64-apple-darwin` pese a que el plan es cross-platform. Fácil de ampliar cuando toque; solo dejarlo anotado para que no sorprenda en Windows/Linux.

---

## Sobre "el otro agente está confundido"

No lo veo confundido en el **diseño** — los docs son coherentes y el esqueleto respeta el contrato. Donde sí hay un hueco es que **la Fase 1 (ruta de presentación de frame + pacing) aún no se decidió ni implementó**, y el adapter (`core_bridge.rs`) está vacío. El resultado es un esqueleto que "funciona" pero por el camino caro (C1+C2), y eso es justo lo que dispara el CPU y confunde la lectura del monitor de actividad: parece que "Rust consume mucho" cuando en realidad es el puente JSON + rAF sin ritmo.

**Recomendación de orden de trabajo:**
1. Cerrar **Fase 1** del propio `ARCHITECTURE.md`: elegir candidato A (con `ipc::Response`, no `Vec<u8>` crudo) o B, y medir. Esto mata C1.
2. Meter pacing + pausa + corte en `document.hidden` (C2, C4). Barato, alto impacto.
3. Unificar a un IPC por frame (C3) o mover el ritmo al adapter y que la UI solo presente.
4. Limpieza: metadata de `tauri.conf.json` (D1), módulo muerto (D2), README (D3).
5. Recién entonces empezar el core de verdad (`arm7tdmi`, `ppu`), con los ROM-tests de jsmolka que ya menciona el audit.

## Sobre el build pesado (lo que reportaste)
No es un bug. Tauri + wry arrastran un árbol grande; `target/` en 2.4 GB es normal. Para que deje de doler con varios agentes:
- Usá `cargo build` normal, no `--release`, mientras iterás.
- Considerá `sccache` para cachear artefactos entre rebuilds.
- Si el otro agente dejó `cargo tauri dev` con watcher, cada guardado recompila: cerralo cuando no lo uses.
- Mientras un `cargo build` está vivo, va a usar los cores que haya — eso es correcto, no un leak. El problema sería si **sigue** alto después de terminar el build: ahí el culpable es la app corriendo (C1/C2), no el compilador.

---

*Veredicto: el proyecto está bien encaminado y honestamente documentado. El "alto CPU" es, en partes, (a) contención con otros agentes, (b) `cargo build` legítimamente pesado, y (c) un esqueleto que presenta frames por el camino caro. Lo (c) se arregla cerrando la Fase 1 que su propio diseño ya especifica.*
