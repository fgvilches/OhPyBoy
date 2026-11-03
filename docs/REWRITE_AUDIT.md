# Auditoría de reescritura

**Versión:** 0.2 · fecha de inspección: 2026-11-02.

## Estado observado

- Repositorio Git limpio en `main`, remoto `fgvilches/OhPyBoy`, último commit `2f5e1b6`.
- 18 módulos Python en `src/`, 8.216 líneas. `python3 -m compileall -q src` pasa.
- README declara *Currently not working*. No hay suite de tests, fixtures de ROM ni CI.
- Origen del código: traducción de gbajs2 (JavaScript, BSD-2). Las APIs de navegador quedaron dentro de la traducción.

## Veredicto

**Leer, no portar.** El valor del Python es el vocabulario (nombres de módulos, registros, constantes) y servir de mapa para leer gbajs2. Como fuente de comportamiento no es confiable: nunca ejecutó una ROM. Para comportamiento se usan GBATEK y mGBA.

Destino: mover `src/` a `legacy/` con tag `legacy-python`. No se borra; no se mantiene.

## Mapa por módulo

| Legado | Líneas | Destino en `crates/core` | Decisión |
|---|---|---|---|
| `arm.py`, `thumb.py` | 1233, 772 | `arm7tdmi` | Reescribir desde GBATEK; tests por instrucción con jsmolka |
| `core.py` | 1144 | `arm7tdmi` + `gba` | Separar estado de CPU, excepciones y scheduler |
| `mmu.py` | 680 | `bus` | Rehacer: mirrors, rotación de lecturas desalineadas, waitstates, prefetch, open bus |
| `irq.py` | 642 | `irq` + scheduler | Prioridades y timing verificables; hoy mezcla IRQ con timers |
| `dma.py` | 161 | `dma` | Integrar con timing de HBlank/VBlank/FIFO |
| `gbio.py` | 554 | `io` dividido por periférico | Un archivo por registro-grupo |
| `video.py`, `software.py` | 163, 1036 | `ppu` | Framebuffer puro; el FIXME de VCounter se convierte en test |
| `audio.py` | 591 | `apu` | Mixer y ring buffer; sin callback de UI |
| `keypad.py` | 184 | `keypad` | Máscara KEYINPUT + KEYCNT IRQ |
| `savedata.py` | 248 | `cartridge` | Detección por firma + overrides + inferencia de EEPROM |
| `sio.py` | 97 | — | Fuera de v0.1; stub que devuelve valores por defecto |
| `console.py` | 285 | inspector Tauri | No portar Tkinter; conservar la lista de vistas |
| `gba.py` | 348 | `gba` + adapter | Eliminar `window`, `document`, `FileReader`, `Date`, `localStorage` |
| `audio_module_test.py`, `audio_test simple.py` | 26, 52 | — | Descartar |
| `bios.S` | — | `tests/` o referencia | Auditar origen y licencia antes de usarlo; por defecto, BIOS libre embebida |

## Problemas concretos encontrados

1. **Plataforma dentro del core.** `gba.py` usa `window.setTimeout`, `document.createElement`, `FileReader`, `ArrayBuffer`, `Date.now`, `localStorage`. `video.py` pinta en un contexto Canvas.
2. **Grafo mutable y circular.** El ensamblaje depende de asignaciones cruzadas tras construir (`cpu.mmu`, `mmu.core`, `irq.video`...). Un objeto parcialmente conectado falla en runtime, no al construir.
3. **Stubs silenciosos.** `pass` como implementación en `audio.py`, `core.py` (3), `gbio.py` (2), `mmu.py` (12), `sio.py` (2), `software.py` (3). Algunos son legítimos (escrituras a ROM ignoradas); otros tapan comportamiento.
4. **Efectos laterales al importar.** `console.py` instancia `GameBoyAdvance()` y `Console()` al final del módulo.
5. **Timing de vídeo.** `video.py:153` tiene un FIXME sobre VCounter IRQ en mitad de HBlank. `irq.py` mezcla interrupciones y timers en un solo módulo.
6. **Persistencia.** Saves en `localStorage` codificados en base64, sin versión ni checksum.
7. **Bus.** `MemoryView.load32` no rota correctamente lecturas desalineadas en Python (shift sin máscara de 32 bits). `BIOSView` devuelve `-1` fuera de rango en vez de open bus.

## Qué cierra esta auditoría

- Set de ROMs de prueba: jsmolka/gba-tests, mgba-suite, demos TONC (ver `PRODUCT_PLAN.md`).
- BIOS: libre embebida por defecto, original opcional.
- Periféricos fuera de v0.1: SIO, RTC, rumble, tilt/solar, GBA Video.

## Qué queda abierto para la implementación

- Ruta de presentación de frame en Tauri (candidatos A/B/C, se decide en Fase 1).
- Formato exacto de snapshot y política de migración entre versiones.
- Tabla inicial de overrides de save por game code (se construye a medida que aparezcan casos).

## Política de evidencia

Cada afirmación de compatibilidad apunta a una prueba reproducible. "Abrió la ROM" no es "emula el juego". Se reportan por separado: build, arranque, vídeo, input, audio, saves, rendimiento y duración de sesión.
