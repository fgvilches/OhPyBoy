//! Memory bus: regions, mirrors, bounds.
//!
//! This is the first piece of the core. It owns the address map and answers
//! reads/writes without any CPU involvement, so it can be unit-tested in
//! isolation. Waitstates, prefetch and open-bus behaviour arrive in Fase 3.

use crate::types::{Address, Region};
use thiserror::Error;

#[derive(Debug, Error, PartialEq, Eq)]
pub enum BusError {
    #[error("address 0x{addr:08X} is outside any mapped region", addr = .0)]
    Unmapped(Address),
    #[error("address 0x{addr:08X} is not {align}-byte aligned", addr = .addr, align = .align)]
    Unaligned { addr: u32, align: u8 },
    #[error("address 0x{addr:08X} is read-only", addr = .0)]
    ReadOnly(Address),
}

/// GBA address map (see GBATEK "Memory Map"). Only boundaries are modelled
/// here; the actual backing stores (BIOS, EWRAM, ...) are owned by `Gba`.
pub fn region_of(addr: Address) -> Option<Region> {
    let a = addr.0;
    // BIOS is 16 KB (0x0000_0000..0x0000_3FFF); the rest of the 0x00xxxxxx
    // range is open bus. Model that honestly instead of pretending the BIOS
    // fills the whole 1 MB region.
    Some(match a >> 24 {
        0x00 => {
            if a < 0x0000_4000 {
                Region::Bios
            } else {
                return None;
            }
        }
        0x02 => Region::Ewram,
        0x03 => Region::Iwram,
        0x04 => Region::Io,
        0x05 => Region::Palette,
        0x06 => Region::Vram,
        0x07 => Region::Oam,
        0x08..=0x09 => Region::Rom0,
        0x0A..=0x0B => Region::Rom1,
        0x0C..=0x0D => Region::Rom2,
        0x0E..=0x0F => Region::Sram,
        _ => return None,
    })
}

/// Mirror an address into its base region range.
pub fn mirror(addr: Address) -> Address {
    let a = addr.0;
    let base = match region_of(addr) {
        Some(Region::Bios) => a & 0x0000_3FFF,
        Some(Region::Ewram) => a & 0x0003_FFFF,
        Some(Region::Iwram) => a & 0x0000_7FFF,
        Some(Region::Io) => a & 0x0000_03FF,
        Some(Region::Palette) => a & 0x0000_03FF,
        Some(Region::Vram) => a & 0x0001_FFFF,
        Some(Region::Oam) => a & 0x0000_03FF,
        Some(Region::Rom0) | Some(Region::Rom1) | Some(Region::Rom2) => a & 0x01FF_FFFF,
        Some(Region::Sram) => a & 0x0000_FFFF,
        Some(Region::OpenBus) | None => a,
    };
    Address(base)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn region_boundaries() {
        assert_eq!(region_of(Address(0x0000_0000)), Some(Region::Bios));
        assert_eq!(region_of(Address(0x0000_3FFF)), Some(Region::Bios));
        assert_eq!(region_of(Address(0x0000_4000)), None);
        assert_eq!(region_of(Address(0x0200_0000)), Some(Region::Ewram));
        assert_eq!(region_of(Address(0x0300_0000)), Some(Region::Iwram));
        assert_eq!(region_of(Address(0x0400_0000)), Some(Region::Io));
        assert_eq!(region_of(Address(0x0500_0000)), Some(Region::Palette));
        assert_eq!(region_of(Address(0x0600_0000)), Some(Region::Vram));
        assert_eq!(region_of(Address(0x0700_0000)), Some(Region::Oam));
        assert_eq!(region_of(Address(0x0800_0000)), Some(Region::Rom0));
        assert_eq!(region_of(Address(0x0A00_0000)), Some(Region::Rom1));
        assert_eq!(region_of(Address(0x0C00_0000)), Some(Region::Rom2));
        assert_eq!(region_of(Address(0x0E00_0000)), Some(Region::Sram));
        assert_eq!(region_of(Address(0x1000_0000)), None);
    }

    #[test]
    fn mirrors_stay_inside_region() {
        // EWRAM mirror: 0x0204_0000 -> 0x0200_0000
        assert_eq!(mirror(Address(0x0204_0000)), Address(0x0000_0000));
        // IWRAM mirror
        assert_eq!(mirror(Address(0x0300_8000)), Address(0x0000_0000));
    }
}
