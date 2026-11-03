---
version: alpha
name: OhPyBoy Glass
description: Un emulador GBA de escritorio con precisión técnica, calma visual y una capa de cristal nativo.
colors:
  primary: "#E8F4FF"
  secondary: "#99A8BC"
  tertiary: "#00E5FF"
  neutral: "#0B1220"
  success: "#30E58C"
  warning: "#FFC24B"
  danger: "#FF5C7A"
  ink: "#04141A"
typography:
  display:
    fontFamily: "-apple-system, SF Pro Display, Segoe UI Variable Display, Inter, sans-serif"
    fontSize: 28px
    fontWeight: 600
    lineHeight: 1.15
    letterSpacing: "-0.02em"
  body:
    fontFamily: "-apple-system, SF Pro Text, Segoe UI Variable Text, Segoe UI, Inter, sans-serif"
    fontSize: 14px
    fontWeight: 400
    lineHeight: 1.45
  label:
    fontFamily: "-apple-system, SF Pro Text, Segoe UI Variable Text, Segoe UI, Inter, sans-serif"
    fontSize: 11px
    fontWeight: 600
    lineHeight: 1.2
    letterSpacing: "0.08em"
  mono:
    fontFamily: "SF Mono, ui-monospace, Cascadia Code, JetBrains Mono, Menlo, monospace"
    fontSize: 12px
    fontWeight: 500
    lineHeight: 1.4
rounded:
  xs: 6px
  sm: 10px
  md: 14px
  lg: 20px
  xl: 28px
  pill: 999px
spacing:
  xs: 4px
  sm: 8px
  md: 16px
  lg: 24px
  xl: 40px
components:
  button-primary:
    backgroundColor: "{colors.tertiary}"
    textColor: "{colors.ink}"
    rounded: "{rounded.sm}"
    padding: 10px
  button-secondary:
    backgroundColor: "{colors.neutral}"
    textColor: "{colors.primary}"
    rounded: "{rounded.sm}"
    padding: 10px
  status-success:
    backgroundColor: "{colors.success}"
    textColor: "{colors.ink}"
    rounded: "{rounded.pill}"
    padding: 4px
  status-warning:
    backgroundColor: "{colors.warning}"
    textColor: "{colors.ink}"
    rounded: "{rounded.pill}"
    padding: 4px
  status-danger:
    backgroundColor: "{colors.danger}"
    textColor: "{colors.ink}"
    rounded: "{rounded.pill}"
    padding: 4px
---

## Overview

**Primary surface: Operate. Secondary surface: Inspect.** OhPyBoy debe hacer que abrir una ROM, jugar, pausar y guardar sea inmediato. La depuración existe, pero se revela bajo demanda; no compite con el juego. Flujos y estados concretos en `docs/UI_FLOWS.md`.

La dirección visual toma la disciplina de interfaces técnicas oscuras y la convierte en una identidad propia: aurora fría, cristal translúcido, tipografía de sistema y un acento cian con función real. Comparte el lenguaje material de HShop Glass (mismos tokens de cristal) sin clonar su interfaz.

El canvas del juego es el protagonista: todo lo demás se diseña para no competir con 240×160 píxeles escalados.

## Colors

- `primary` es texto principal y no debe depender del blur para ser legible.
- `secondary` es texto auxiliar; nunca se usa como único indicador de estado.
- `tertiary` es la acción primaria y el foco; no se reparte como decoración.
- `neutral` es la base oscura. El fondo del shell queda transparente cuando el material nativo de Tauri esté disponible.
- `ink` es el texto sobre fondos saturados (cian, verde, ámbar, coral): blanco sobre esos tonos no pasa AA.
- Estados: `success` para confirmado (save escrito, audio activo), `warning` para atención (underrun de audio, pacing retrasado), `danger` para error o acción destructiva. Siempre con texto o icono, nunca solo color.
- El cristal usa blanco con alfa, borde especular y highlight interior; el contraste se valida sobre el fondo compuesto, no sobre el alfa aislado.

## Typography

SF Pro / Segoe UI / Inter son una pila pragmática para escritorio. La mono se reserva para registros, direcciones, registros ARM y diagnósticos. No usar mayúsculas técnicas como sustituto de jerarquía.

## Layout

- Barra superior mínima con título de ROM, estado y acciones inmediatas.
- Canvas GBA dominante, centrado ópticamente pero no dentro de una tarjeta genérica.
- Panel lateral opcional para biblioteca/controles; se oculta cuando el juego necesita foco.
- Inspector como panel secundario, con tabs CPU / memoria / vídeo / audio / logs.
- Escalado entero por defecto; mostrar el factor actual y permitir ventana libre como opción explícita.
- 44px mínimo para controles táctiles; foco visible para teclado.

## Elevation & Depth

La receta glass es: `rgba(255,255,255,.08)` + blur 28px + saturación 1.4 + borde blanco 18% + highlight superior + sombra suave. El material nativo de la ventana aporta profundidad real en macOS/Windows; el CSS no debe pintar un fondo opaco encima.

## Shapes

El canvas de juego usa una forma sobria y ligeramente redondeada; los controles usan `sm`; paneles de inspector `lg`; badges `pill`. No convertir cada elemento en una cápsula.

## Components

- **Game surface:** lienzo pixel-art con `image-rendering: pixelated`, escala entera, marco mínimo (`rounded.sm`) y overlay de pausa translúcido sobreimpreso. Sin sombra de tarjeta: el canvas no es una card.
- **Transport controls:** Play/Pause (`button-primary`), Reset, Save State y Load State (`button-secondary`). Una sola acción primaria visible a la vez.
- **ROM picker:** lista de recientes con nombre, game code y tipo de save, más botón Abrir ROM. Vacío honesto, sin métricas inventadas.
- **Status chip:** FPS, BIOS (libre/propia), audio, save y versión del core. Usa `status-*`; texto siempre presente.
- **Inspector:** tablas en `mono`, diffs de memoria resaltados, refresco manual o al pausar. Panel `rounded.lg` con fondo glass.
- **Toast:** feedback breve para operaciones de archivo; los errores incluyen la acción de recuperación.
- **Slot de save state:** miniatura del frame, hora, versión; `danger` solo en el botón de borrar.

## Do's and Don'ts

- **Sí:** profundidad medida, controles de teclado, estados explícitos, contraste real, blur reducido cuando el sistema lo pide.
- **Sí:** una animación corta que explique una transición.
- **No:** neon por todas partes, gradientes tecnológicos, números decorativos, tres tarjetas idénticas, blur sin material detrás.
- **No:** llamar “compatible” a una ROM solo porque abrió.
- **No:** bloquear el hilo de emulación con una operación de UI.

## Accesibilidad y movimiento

- `prefers-reduced-motion`: desactivar respiración del logo, transiciones largas y parallax.
- `forced-colors`: bordes y estados deben seguir siendo distinguibles.
- Contraste AA en texto y botones sólidos; el cristal requiere comprobación por captura en los fondos soportados.
- Teclas documentadas y remapeables. Todas las acciones también deben existir en menú o botones.
