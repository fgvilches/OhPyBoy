use std::sync::Mutex;
use tauri::Manager;
use tauri::ipc::Response;


// FrameInfo removed: run_frame returns raw binary Response directly.

struct AppState {
    core: Mutex<ohpyboy_core::Gba>,
}

/// Single IPC per frame: runs one frame AND returns the framebuffer as raw
/// binary (no JSON). This closes C1+C3 from the code review.
#[tauri::command]
fn run_frame(state: tauri::State<AppState>) -> Response {
    let mut g = state.core.lock().unwrap();
    g.run_frame();
    // Re-pack u32 RGBA -> bytes in one pass using to_le_bytes (C5).
    let fb = g.framebuffer();
    let mut out = Vec::with_capacity(fb.len() * 4);
    for &px in fb {
        out.extend_from_slice(&px.to_le_bytes());
    }
    Response::new(out)
}

#[tauri::command]
fn reset(state: tauri::State<AppState>) {
    state.core.lock().unwrap().reset();
}

#[tauri::command]
fn set_keys(state: tauri::State<AppState>, keys: u16) {
    state.core.lock().unwrap().set_keys(keys);
}

#[tauri::command]
fn frame_number(state: tauri::State<AppState>) -> u64 {
    state.core.lock().unwrap().frame_counter
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .setup(|app| {
            app.manage(AppState {
                core: Mutex::new(ohpyboy_core::Gba::new()),
            });
            if let Some(win) = app.get_webview_window("main") {
                #[cfg(target_os = "macos")]
                {
                    use window_vibrancy::{apply_vibrancy, NSVisualEffectMaterial, NSVisualEffectState};
                    let _ = apply_vibrancy(
                        &win,
                        NSVisualEffectMaterial::UnderWindowBackground,
                        Some(NSVisualEffectState::Active),
                        Some(14.0),
                    );
                }
            }
            Ok(())
        })
        .invoke_handler(tauri::generate_handler![
            run_frame,
            reset,
            set_keys,
            frame_number,
        ])
        .run(tauri::generate_context!())
        .expect("error while running OhPyBoy");
}
