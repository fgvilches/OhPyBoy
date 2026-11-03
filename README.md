# OhPyBoy

GBA emulator. Rust core + Tauri shell. Walking skeleton stage.

The original Python implementation (never functional) lives under `legacy/`
(tag `legacy-python`). The rebuild is in `crates/` and `apps/`. See
`docs/PRODUCT_PLAN.md`, `docs/ARCHITECTURE.md`, `docs/REWRITE_AUDIT.md`.

Status: Fase 1 (presentation path). Core is a test pattern generator, not an
emulator. ARM/THUMB, PPU, APU come in Fase 2+.

Build: `cargo build -p ohpyboy` then `tauri build --debug` from `apps/ohpyboy`.
