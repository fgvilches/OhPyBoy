# Flujos y superficies de UI

**Versión:** 0.2 · tokens y reglas visuales en `../DESIGN.md`.

Superficie primaria: **Operate** (abrir, jugar, pausar, guardar). Secundaria: **Inspect** (debug bajo demanda). Toda pantalla se diseña para la primaria; la secundaria nunca roba foco ni ciclos.

## 1. Primer arranque

1. Ventana con biblioteca vacía: un botón **Abrir ROM** y una línea de texto sobre dónde encontrar la BIOS si quiere usar la original.
2. Sin BIOS propia, la app usa la BIOS libre embebida y lo indica en el status chip (`BIOS: libre`). No hay bloqueo ni asistente.
3. Arrastrar un `.gba` sobre la ventana equivale a Abrir ROM.

## 2. Abrir y jugar

1. El usuario elige un `.gba` (diálogo nativo o drag & drop).
2. Validación: tamaño ≤ 32 MB, header con checksum válido, game code legible. Se muestra nombre, código, tamaño y tipo de save detectado.
3. Mientras carga: estado `Cargando ROM` sin congelar la ventana.
4. Éxito: canvas a escala entera (3× por defecto o la última elegida); el foco queda en el juego; la ROM entra en recientes.
5. Error: mensaje concreto (`Header inválido`, `Tamaño fuera de rango`, `No se pudo leer el archivo`) y acción para abrir otra ROM. No hay pantalla de pánico.

Atajos por defecto: `Space` pausa/reanuda, `Cmd/Ctrl+R` reset, `F5` guarda estado en el slot activo, `F9` carga, `Cmd/Ctrl+O` abre ROM, `Cmd/Ctrl+I` inspector, `Esc` cierra overlay.

## 3. Pausa e inspector

- Pausar muestra un overlay ligero sobre el canvas: estado, FPS, slot activo, Reset, Guardar y Cargar estado.
- El inspector se abre por botón o atajo; nunca por un warning.
- Pestañas: CPU (registros, CPSR, modo, PC con desensamblado corto), Memoria (región + offset, hex + ASCII, diff resaltado desde la última pausa), PPU (DISPCNT, BG, paleta, tiles), APU (canales, FIFO, contadores de underrun/overrun), Logs.
- Los paneles se refrescan al pausar o al pulsar Actualizar; nunca por frame.
- Logs: nivel, timestamp relativo, origen. Copiar y exportar son acciones separadas.

## 4. Saves y snapshots

- **Save del cartucho:** se escribe en disco cuando el core marca el save como estable (sin escrituras durante N frames). Escritura atómica por rename. Export/import desde el menú.
- **Save state:** cinco slots por ROM. Cada slot muestra hora, miniatura del frame y versión de formato.
- Guardar sobre un slot ocupado no pide confirmación; existe Deshacer durante 10 segundos.
- Cargar un estado incompatible (otra ROM, otra versión, CRC roto) se rechaza con razón y no toca el estado actual.

## 5. Ajustes

Secciones: Controles, Vídeo, Audio, BIOS y rutas, Diagnóstico. Opciones avanzadas bajo disclosure. La pantalla principal no se convierte en BIOS de una nave.

- Controles: remapeo por botón, restaurar defaults, gamepad detectado automáticamente.
- Vídeo: factor de escala entera, filtro (ninguno/pixelado), mostrar FPS.
- Audio: volumen, dispositivo, latencia objetivo.
- BIOS y rutas: BIOS propia, directorio de saves y estados.
- Diagnóstico: exportar logs, limpiar recientes, versión del core.

## Estados obligatorios

| Superficie | Vacío | Cargando | Error | Éxito |
|---|---|---|---|---|
| Biblioteca | Sin ROMs recientes + Abrir ROM | Leyendo archivo | Razón concreta + reintentar | ROM en lista con metadatos |
| Juego | No hay ROM cargada | Inicializando core | ROM rechazada (razón) | Frame visible, foco en canvas |
| Save state | Slots vacíos | Guardando | Snapshot inválido (razón) | Slot con hora y miniatura |
| Inspector | Pausa para inspeccionar | Actualizando | Vista no disponible | Valores legibles |
| Audio | — | Abriendo dispositivo | Sin dispositivo (juego sigue mudo) | Chip verde |

## Accesibilidad

- Todas las acciones existen en menú o botón además del atajo.
- Foco visible en todos los controles; navegación completa por teclado.
- Los atajos no capturan texto dentro de campos de configuración.
- `prefers-reduced-motion` desactiva transiciones largas y animaciones decorativas.
- Estado nunca se comunica solo por color: siempre texto o icono.
- Hit targets ≥ 44 px.

## Controles por defecto

| GBA | Teclado |
|---|---|
| D-pad | Flechas |
| A / B | `X` / `Z` |
| L / R | `A` / `S` |
| Start / Select | `Enter` / `Backspace` |

Gamepad: mapeo estándar del navegador (Gamepad API) con A/B invertidos a la convención Nintendo.

## Layout y plataformas

- Escritorio ancho: biblioteca colapsable a la izquierda, canvas al centro, inspector como panel derecho opcional.
- Ventana pequeña: biblioteca y ajustes como paneles deslizantes; inspector ocupa una pestaña completa.
- macOS: respeta traffic lights y usa material nativo. Windows y Linux reciben la misma jerarquía con la aurora como fondo.
