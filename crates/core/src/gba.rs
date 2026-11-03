//! GBA lifecycle and frame scheduler.
//!
//! `Gba` owns the whole machine state. In this first version it does not
//! emulate anything; it exists to prove the costura (Rust -> Tauri -> canvas)
//! with a generated test pattern, and to freeze the public API.

use crate::bus;
use crate::types::{Address, Cycles};
use crate::FB_PIXELS;

pub struct Gba {
    pub cycles: Cycles,
    pub framebuffer: [u32; FB_PIXELS],
    pub frame_counter: u64,
    keys: u16,
}

impl Gba {
    pub fn new() -> Self {
        Self {
            cycles: Cycles::ZERO,
            framebuffer: [0; FB_PIXELS],
            frame_counter: 0,
            keys: 0,
        }
    }

    pub fn reset(&mut self) {
        self.cycles = Cycles::ZERO;
        self.framebuffer = [0; FB_PIXELS];
        self.frame_counter = 0;
        self.keys = 0;
    }

    pub fn set_keys(&mut self, keys: u16) {
        self.keys = keys;
    }

    /// Run until the next VBlank. For now this generates a moving test pattern
    /// so the presentation path can be measured end to end.
    pub fn run_frame(&mut self) {
        let t = self.frame_counter as f32;
        for (i, px) in self.framebuffer.iter_mut().enumerate() {
            let x = (i % 240) as f32;
            let y = (i / 240) as f32;
            let v = ((x + t).sin() * 0.5 + 0.5) * 255.0;
            let r = v as u32 & 0xFF;
            let g = (((y + t * 0.7).cos() * 0.5 + 0.5) * 255.0) as u32 & 0xFF;
            let b = (((x * y * 0.001 + t).sin() * 0.5 + 0.5) * 255.0) as u32 & 0xFF;
            *px = 0xFF00_0000 | (r << 16) | (g << 8) | b;
        }
        self.frame_counter = self.frame_counter.wrapping_add(1);
        // GBA: 280896 cycles per frame @ 16.78 MHz.
        self.cycles = Cycles(self.cycles.0.wrapping_add(280_896));
    }

    pub fn framebuffer(&self) -> &[u32; FB_PIXELS] {
        &self.framebuffer
    }

    /// Placeholder for the future audio drain. Returns the number of samples
    /// produced (0 until the APU exists).
    pub fn drain_audio(&mut self, _out: &mut Vec<[i16; 2]>) -> usize {
        0
    }

    #[allow(dead_code)]
    fn _touch_bus(addr: Address) {
        let _ = bus::region_of(addr);
    }
}

impl Default for Gba {
    fn default() -> Self { Self::new() }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn frame_advances() {
        let mut g = Gba::new();
        let before = g.frame_counter;
        g.run_frame();
        assert_eq!(g.frame_counter, before + 1);
        assert!(g.cycles.as_u32() > 0);
    }

    #[test]
    fn framebuffer_size() {
        let g = Gba::new();
        assert_eq!(g.framebuffer().len(), FB_PIXELS);
    }

    #[test]
    fn reset_clears() {
        let mut g = Gba::new();
        g.run_frame();
        g.reset();
        assert_eq!(g.frame_counter, 0);
        assert_eq!(g.cycles, Cycles::ZERO);
        assert!(g.framebuffer().iter().all(|&p| p == 0));
    }
}
