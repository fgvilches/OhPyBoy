//! GBA emulator core.
//!
//! Deterministic and UI-free: no files, no clock, no async. The host (Tauri
//! adapter) decides when to call `run_frame` and how to present the result.
//!
//! Nothing here is functional yet; this is the walking-skeleton skeleton.

pub mod bus;
pub mod gba;
pub mod types;

pub use gba::Gba;
pub use types::{Address, Cycles};

/// Framebuffer dimensions (GBA native).
pub const FB_WIDTH: usize = 240;
pub const FB_HEIGHT: usize = 160;
pub const FB_PIXELS: usize = FB_WIDTH * FB_HEIGHT;
