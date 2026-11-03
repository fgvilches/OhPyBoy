# OhPyBoy Reborn — plan de trabajo

**Estado:** propuesta ejecutable · **versión:** 0.2 · **fecha:** 2026-11-02

Cambios respecto a 0.1 (tras revisión): walking skeleton Tauri en Fase 1 en vez de Fase 5; BIOS como decisión explícita; ROMs de prueba nombradas con gates duras; Python legado degradado a lectura; presentación de frame y audio con candidatos concretos; un solo crate `core` al inicio; waitstates/prefetch/open bus en la matriz; CI, estimación y alcance de v0.1.

Documentos relacionados: `ARCHITECTURE.md` (contrato y capas), `UI_FLOWS.md` (superficies y estados), `REWRITE_AUDIT.md` (qué se hace con el Python), `../DESIGN.md` (tokens y reglas visuales).

## Objetivo

Reescribir OhPyBoy como un emulador de Game Boy Advance para escritorio, con un núcleo Rust testeable e independiente de la interfaz y una aplicación Tauri liviana, accesible y visualmente cuidada. El código Python actual se conserva como referencia de lectura; no se traduce ni se usa como fuente de tests.

## Alcance de v0.1

**Entra:** ARM/THUMB completos, bus con waitstates, IRQ, timers, DMA, keypad, PPU modos 0–5 con sprites/ventanas/blending, APU (PSG + FIFO), SRAM/Flash/EEPROM, save states, BIOS libre embebida con opción de BIOS propia, shell Tauri con biblioteca, transport e inspector básico, macOS.

**No entra:** SIO/multiplayer, RTC, rumble, tilt/solar, GBA Video, cheats, netplay. Windows/Linux se mantienen compilando pero no se prometen.

## Decisiones base

- **Lenguaje del núcleo:** Rust estable, MSRV fijada en `rust-toolchain.toml`.
- **Shell de escritorio:** Tauri 2, con comandos IPC explícitos y un archivo de capabilities mínimo.
- **UI:** HTML/CSS/TypeScript sin framework en la primera iteración.
- **BIOS:** BIOS libre (Cult-of-GBA / Normmatt, MIT) embebida por defecto; el usuario puede cargar la BIOS original desde disco. Sin HLE de SWI en v0.1: una sola ruta de ejecución es más fácil de depurar. El `bios.S` del repo se conserva como referencia hasta auditarlo.
- **Render:** framebuffer RGBA 240×160 producido por el core. Presentación, dos candidatos: **A**, `invoke` con respuesta binaria (`tauri::ipc::Response`) → `ImageData` → canvas; **B**, custom protocol `ohpyboy://frame`. El spike de Fase 1 decide. **Plan C** si ninguno sostiene 60 fps estables con latencia menor a un frame: superficie nativa `wgpu` dentro del shell. Es un cambio de arquitectura y hay que saberlo en Fase 1, no en Fase 6.
- **Audio:** `cpal`. El core emite estéreo i16 a la tasa interna del mixer (32768 Hz); el adaptador resamplea a la tasa del dispositivo. Ring buffer acotado: en underrun se inserta silencio, en overrun se descartan muestras antiguas; ambos se cuentan y se exponen en el status chip.
- **Persistencia:** saves y save states como archivos versionados en el directorio de datos de la app, escritura atómica por rename. Nada de `localStorage`.
- **Referencia técnica:** GBATEK, mGBA (comportamiento y tests) y gbajs2 (BSD-2, origen real del código Python). El Python no se cita como autoridad.

## Auditoría del legado

Detalle en `REWRITE_AUDIT.md`. Resumen: 18 archivos, 8.216 líneas, compila, nunca funcionó, mezcla APIs de navegador con emulación, stubs silenciosos en todos los subsistemas. Decisión: **leer, no portar.**

## ROMs y fixtures de prueba

Todas libres y redistribuibles; viven en `tests/roms/` con su licencia y un manifest con hashes.

| Fuente | Qué prueba | Gate |
|---|---|---|
| `jsmolka/gba-tests` — `arm.gba`, `thumb.gba` | Instrucciones, flags, modos | Fase 2: 100 % en verde |
| `jsmolka/gba-tests` — `memory.gba`, `bios.gba` | Bus, alineamiento, mirrors, SWI | Fase 3 |
| `jsmolka/gba-tests` — `ppu/*.gba` | Modos, sprites, ventanas | Fase 3: frame idéntico a captura de mGBA |
| `jsmolka/gba-tests` — `save/*.gba` | SRAM, Flash, EEPROM | Fase 4 |
| `mgba-suite` | Timing, DMA, IRQ, waitstates, prefetch | Fase 3/6: fijar el número de pass como baseline en CI y no retroceder |
| Demos TONC | Casos visuales reales | Fase 3, inspección manual |

Las ROMs comerciales son solo del usuario: nunca en el repo ni en CI.

## Fases y criterios de salida

### Fase 0 — Inventario y contrato técnico

1. Etiquetar el estado Python como `legacy-python` y moverlo a `legacy/`.
2. Matriz de subsistemas con decisión por módulo (ya en `REWRITE_AUDIT.md`).
3. Definir invariantes: endianness, alineamiento, ciclos, mapa de memoria, formato de snapshot (header con versión, hash de ROM y CRC).
4. Descargar fixtures y fijar sus hashes en el manifest.

**Salida:** `legacy/` congelado, `tests/roms/` con manifest, contrato de `EmulatorCore` escrito en `ARCHITECTURE.md`.

### Fase 1 — Walking skeleton

Un solo objetivo: **demostrar que la costura Rust → Tauri → canvas sostiene 60 fps antes de escribir una sola instrucción ARM.**

1. Workspace con dos miembros: `crates/core` (módulos internos, un solo crate por ahora) y `apps/ohpyboy` (Tauri 2).
2. Tipos base (`Cycles`, `Address`) y bus con regiones, mirrors y límites explícitos; sin `unsafe`.
3. Core de prueba que genera un patrón animado de 240×160 a 59.7275 Hz.
4. Hilo de emulación y presentación en WebView por candidatos A y B; medir fps, latencia y CPU de ambos.
5. CI: `cargo fmt --check`, `clippy -D warnings`, `cargo test`, build Tauri en macOS.

**Salida:** ventana que muestra el patrón a 60 fps estables durante 10 minutos con uso de CPU documentado; decisión escrita A/B/C en `ARCHITECTURE.md`.

### Fase 2 — CPU

1. ARM7TDMI ARM: decode, condiciones, barrel shifter, ALU, multiplicación, branches, load/store, PSR, excepciones y cambio de modo.
2. THUMB: decode separado.
3. Scheduler por eventos/ciclos; sin reloj de pared en el core.
4. Unit tests para shifter, ALU y flags; tests de ROM con jsmolka.
5. Trazas exportables (PC, opcode, registros) para diff contra mGBA cuando algo falle.

**Salida:** `arm.gba` y `thumb.gba` 100 % en verde; `bios.gba` arranca la BIOS libre hasta el salto a ROM.

### Fase 3 — Sistema y vídeo

1. IO, IRQ, timers, DMA (incluido timing de HBlank/VBlank DMA), keypad.
2. **Waitstates por región (WAITCNT), prefetch buffer de ROM y open bus**, cada uno con su test de `mgba-suite`.
3. PPU modos 0–5, sprites afines, ventanas, mosaico, blending, timing de HBlank/VBlank/VCount.
4. Framebuffer puro; comparación contra capturas de mGBA con tolerancia 0 en modos tile y documentada en modos afines.

**Salida:** `memory.gba` y `ppu/*` en verde; baseline de `mgba-suite` fijada en CI; demos TONC visualmente correctas.

### Fase 4 — Audio, saves y snapshots

1. APU: cuatro canales PSG, dos FIFO de DirectSound, mixer, SOUNDBIAS.
2. Detección de save: firmas (`SRAM_V`, `FLASH_V`, `FLASH512_V`, `FLASH1M_V`, `EEPROM_V`) más tabla de overrides por game code. Tamaño de EEPROM (512 B u 8 KB) inferido por la longitud de la primera DMA de lectura; heurística documentada y con test.
3. Save states: header versionado, hash de ROM, CRC; rechazo limpio sin mutar el core.
4. Tests: corrupción deliberada, versión incompatible, cierre a mitad de escritura.

**Salida:** `save/*` en verde; audio sin bloquear emulación con contadores de underrun/overrun visibles; persistencia verificada en disco.

### Fase 5 — Shell completa

1. Material nativo de ventana donde exista; aurora como fallback.
2. Comandos: abrir ROM, pausar, reanudar, reset, save/load state, configuración, importar/exportar save, cargar BIOS.
3. Métricas a baja frecuencia (1–4 Hz); nunca por instrucción.
4. Biblioteca/recientes, transport, overlay de pausa, inspector (CPU, memoria, PPU, APU, logs) bajo demanda y pausado por defecto.
5. Teclado completo, foco visible, `prefers-reduced-motion`, remapeo de controles.

**Salida:** flujo abrir → jugar → pausar → guardar estado → cerrar → restaurar, cubierto por smoke test automatizado; estados de `UI_FLOWS.md` implementados.

### Fase 6 — Conformidad, rendimiento y release

- Matriz de resultados con ROMs del usuario, por subsistema: build, arranque, vídeo, input, audio, saves, 30 min de sesión.
- Perfilado CPU, PPU, audio, IPC y memoria; optimizar solo con mediciones. Objetivo: menos del 25 % de un core en Apple Silicon a velocidad real.
- Firma y notarización macOS; Windows/Linux como builds no soportadas.
- Documentación de instalación, BIOS, atajos y limitaciones conocidas.

**Salida:** release candidate con limitaciones listadas, logs exportables y ninguna compatibilidad afirmada sin matriz.

## Orden de riesgos

1. Timing ARM/PPU/IRQ/waitstates: puede invalidar todo lo demás.
2. Presentación del frame vía Tauri: si falla, cambia la arquitectura. Por eso va en Fase 1.
3. APU y sincronización: glitches difíciles de reproducir.
4. Detección de saves: daño de datos del usuario.
5. Glass y branding: importante, nunca bloqueante.

## Definition of Done por feature

- Especificación breve con referencia a GBATEK o mGBA.
- Unit tests donde la lógica es pura (ALU, shifter, bus, detección de save) y test de ROM donde no lo es.
- Sin APIs de UI dentro de `crates/core`.
- Error observable y recuperable en el shell.
- Perfilada si toca el camino por frame.
- La UI tiene estado vacío, cargando, error y éxito cuando corresponda.
- La documentación distingue **build correcto** de **comportamiento emulado verificado**.
- CI en verde.

## Estimación honesta

Una persona a tiempo parcial: Fase 1, una o dos semanas; Fase 2, tres a cinco; Fase 3, cuatro a ocho (la PPU y el timing son el grueso); Fase 4, dos a cuatro; Fase 5, dos a tres; Fase 6 abierta. Entre cuatro y seis meses hasta una v0.1 que corra juegos comerciales comunes. Una cifra menor es optimismo, no plan.

## Primera iteración

Fase 1 completa. Si el patrón de prueba no llega a 60 fps estables por A ni por B, se decide C antes de tocar la CPU. El vidrio espera.
