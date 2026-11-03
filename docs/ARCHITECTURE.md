# Arquitectura

**Versión:** 0.2 · acompaña a `PRODUCT_PLAN.md` 0.2.

## Capas

```text
UI renderer (WebView: HTML/CSS/TS)
├── game surface (canvas 2D; WebGL solo si el spike lo exige)
├── biblioteca y recientes
├── transport, overlay de pausa, toasts
└── inspector (CPU · memoria · PPU · APU · logs)
        │  invoke / eventos de baja frecuencia / frame binario
        ▼
Tauri shell (apps/ohpyboy/src-tauri)
├── comandos IPC y capabilities
├── diálogos de archivo, rutas de datos, configuración
└── eventos de estado (métricas 1–4 Hz, errores)
        │
        ▼
Application adapter (Rust, dentro del shell)
├── session: posee el hilo de emulación
├── input mapping (teclado → máscara KEYINPUT)
├── presentación: último frame disponible → WebView
├── audio: resampler + ring buffer → cpal
└── orquestación de saves y snapshots (I/O fuera del hilo de emulación)
        │
        ▼
Emulator core (crates/core, sin I/O, sin reloj, sin Tauri)
├── gba        — reset, scheduler, run_until_frame
├── arm7tdmi   — ARM/THUMB, PSR, excepciones, modos
├── bus        — mapa, mirrors, waitstates, prefetch, open bus
├── irq · timers · dma · keypad
├── ppu        — modos 0–5, OAM, ventanas, blending, framebuffer
├── apu        — PSG ×4, FIFO ×2, mixer, SOUNDBIAS
├── cartridge  — header, detección de save, SRAM/Flash/EEPROM
└── snapshot   — serialización versionada
```

Un solo crate `core` con módulos internos. Se parte en crates cuando el tiempo de compilación o un consumidor externo (por ejemplo, un harness de tests headless) lo justifique, no antes.

## Contrato del núcleo

```rust
pub struct Gba { /* estado completo */ }

impl Gba {
    pub fn new(bios: Bios) -> Self;
    pub fn load_rom(&mut self, rom: &[u8]) -> Result<CartridgeInfo, RomError>;
    pub fn reset(&mut self);

    pub fn run_frame(&mut self);               // hasta el próximo VBlank
    pub fn step(&mut self) -> StepInfo;        // una instrucción (debug)

    pub fn set_keys(&mut self, keys: KeyMask);
    pub fn framebuffer(&self) -> &[u32; 240 * 160];   // RGBA8, listo para ImageData
    pub fn drain_audio(&mut self, out: &mut Vec<[i16; 2]>);

    pub fn save_state(&self) -> Snapshot;
    pub fn load_state(&mut self, s: &Snapshot) -> Result<(), SnapshotError>;
    pub fn save_ram(&self) -> Option<&[u8]>;
    pub fn load_save_ram(&mut self, data: &[u8]) -> Result<(), SaveError>;

    #[cfg(feature = "debug")]
    pub fn debug(&self) -> DebugView<'_>;
}
```

Reglas:

- El core no abre archivos, no conoce Tauri, no publica eventos y no lee el reloj del sistema.
- `run_frame` es determinista: misma ROM, misma BIOS, misma secuencia de `set_keys` → mismos frames y muestras.
- `load_rom` y `load_state` validan antes de mutar; si fallan, el estado anterior sigue intacto.
- `framebuffer()` solo cambia entre llamadas a `run_frame`; el adaptador puede copiarlo sin bloquear al core más de una copia de 153 KB.

## Hilos

| Hilo | Posee | Hace | Comunica con |
|---|---|---|---|
| Emulación | `Gba` | `run_frame` en bucle, pacing a 59.7275 Hz | Frame slot (triple buffer), audio ring, canal de comandos |
| Audio (cpal) | callback | Lee del ring buffer; silencio en underrun | Contadores de underrun/overrun |
| Tauri main / WebView | ventana | Presenta el último frame, envía input y comandos | Canal de comandos, eventos |
| I/O | — | Lee/escribe ROM, saves, snapshots; entrega bytes validados | Canal de comandos |

Primera versión con `std::thread` y `crossbeam`/`std::sync::mpsc`. Lock-free o GPU solo tras perfilar.

Pacing: el hilo de emulación duerme hasta el siguiente frame con `spin_sleep` o equivalente; si va retrasado más de 3 frames, descarta pacing y marca `behind` en métricas en vez de acumular deuda.

## Presentación del frame

Ancho de banda: 240×160×4 = 153.6 KB por frame, 9.2 MB/s a 60 fps. No es el problema; lo es la latencia y el número de copias.

| Candidato | Mecanismo | Copias estimadas | Decide |
|---|---|---|---|
| A | `invoke` con `tauri::ipc::Response(Vec<u8>)` → `Uint8ClampedArray` → `ImageData` → `putImageData` | 2–3 | Fase 1 |
| B | Custom protocol `ohpyboy://frame` servido desde el adaptador; `fetch` + `ImageData` | 2–3 | Fase 1 |
| C | Superficie nativa `wgpu` como child window; WebView solo para chrome | 1 | Solo si A y B fallan |

Criterio: 60 fps estables durante 10 minutos, latencia de presentación menor a un frame, CPU del WebView medida. Resultado y cifras se registran aquí al cerrar Fase 1.

### Resultado de Fase 1 (2026-11-03): candidato A adoptado

Medición con el patrón de prueba a 59.7275 Hz, ventana 960×640, Apple Silicon:

| Variante | CPU del proceso | Notas |
|---|---|---|
| `Vec<u8>` crudo por `invoke` (serde_json) | **81.7 %** | 153.6 KB serializados a JSON por frame (~9 MB/s de texto) |
| `ipc::Response` binario, 1 round-trip, `to_le_bytes`, pacing | **33.2 %** | misma imagen, sin JSON, loop con gate temporal |
| Ventana oculta (`document.hidden`) | 0 % | trabajo detenido |

**Decisión: candidato A con `tauri::ipc::Response`.** B y C no se implementan: A cumple el criterio con margen. El presupuesto de presentación queda en ~33 % de un core, y ~67 % libre para CPU/PPU/APU reales. Si el perfilado de Fase 3 muestra que el margen no alcanza, C sigue disponible y documentado.

Reglas derivadas, ya aplicadas en el código:

- Un solo IPC por frame: `run_frame` ejecuta y devuelve el framebuffer.
- El framebuffer nunca viaja como JSON ni como array de números.
- El pacing vive en el presentador (`16.741 ms`); el core no duerme.
- Ventana oculta = emulación detenida.

## IPC

Comandos pequeños y explícitos: `open_rom`, `open_bios`, `pause`, `resume`, `reset`, `save_state(slot)`, `load_state(slot)`, `set_keys(mask)`, `export_save`, `import_save`, `get_debug(view)`, `get_metrics`.

- El framebuffer nunca viaja como JSON.
- Las métricas se emiten a 1–4 Hz, nunca por frame.
- El inspector pide datos bajo demanda; no hay streaming de estado de CPU.
- Capabilities de Tauri: solo `dialog`, `fs` en el directorio de datos de la app y el protocolo custom si se elige B.

## Invariantes

- Registros y PC son `u32`; los flags del CPSR se modelan explícitamente.
- Lecturas y escrituras respetan little-endian, alineamiento, rotación de lecturas desalineadas y mirrors del GBA.
- Un frame solo se publica al completar VBlank.
- Un snapshot incluye versión de formato, hash de ROM, hash de BIOS y CRC del payload.
- Un error de ROM o snapshot nunca deja la sesión a medias.
- Ningún `unsafe` en `crates/core` sin un comentario que justifique y un benchmark que lo respalde.

## Estructura de repositorio

```text
Cargo.toml                 # workspace
rust-toolchain.toml        # MSRV
crates/core/
  src/{lib,gba,arm7tdmi,bus,irq,timers,dma,keypad,ppu,apu,cartridge,snapshot}.rs
  tests/                   # tests de ROM (jsmolka, mgba-suite)
apps/ohpyboy/
  src-tauri/               # shell + adapter
  src/                     # UI
tests/roms/                # fixtures libres + manifest de hashes
legacy/                    # Python original, solo lectura
docs/
DESIGN.md
```

## Qué se descarta del diseño Python

- Grafo de dependencias mutable y circular (`cpu.mmu`, `mmu.core`, `irq.video`).
- Tkinter como debugger y frontend.
- APIs de navegador dentro del emulador.
- `pass` como sustituto de comportamiento.
- Persistencia implícita en `localStorage`.

## Qué se conserva como referencia

- Nombres de módulos y registros, para leer gbajs2 con el mismo vocabulario.
- Constantes de timing (1232 ciclos por línea, 280896 por frame) contrastadas con GBATEK antes de usarlas.
- La idea de freeze/defrost, convertida a snapshots binarios versionados.
