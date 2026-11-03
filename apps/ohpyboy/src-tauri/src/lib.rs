use serde::Serialize;
use std::sync::Mutex;
use tauri::Manager;

mod core_bridge;

#[derive(Serialize)]
struct FrameInfo { width: u32, height: u32, frame: u64 }

struct AppState { core: Mutex<ohpyboy_core::Gba> }

#[tauri::command]
fn run_frame(state: tauri::State<AppState>) -> FrameInfo {
    let mut g = state.core.lock().unwrap();
    g.run_frame();
    FrameInfo { width: 240, height: 160, frame: g.frame_counter }
}

#[tauri::command]
fn framebuffer(state: tauri::State<AppState>) -> Vec<u8> {
    let g = state.core.lock().unwrap();
    let fb = g.framebuffer();
    let mut out = Vec::with_capacity(fb.len() * 4);
    for &px in fb {
        out.push((px >> 16) as u8);
        out.push((px >> 8) as u8);
        out.push(px as u8);
        out.push((px >> 24) as u8);
    }
    out
}

#[tauri::command]
fn reset(state: tauri::State<AppState>) {
    state.core.lock().unwrap().reset();
}

#[tauri::command]
fn set_keys(state: tauri::State<AppState>, keys: u16) {
    state.core.lock().unwrap().set_keys(keys);
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .setup(|app| {
            app.manage(AppState { core: Mutex::new(ohpyboy_core::Gba::new()) });
            if let Some(win) = app.get_webview_window("main") {
                #[cfg(target_os = "macos")]
                {
                    use window_vibrancy::{apply_vibrancy, NSVisualEffectMaterial, NSVisualEffectState};
                    let _ = apply_vibrancy(&win, NSVisualEffectMaterial::UnderWindowBackground, Some(NSVisualEffectState::Active), Some(14.0));
                }
            }
            Ok(())
        })
        .invoke_handler(tauri::generate_handler![run_frame, framebuffer, reset, set_keys])
        .run(tauri::generate_context!())
        .expect("error while running OhPyBoy");
}
