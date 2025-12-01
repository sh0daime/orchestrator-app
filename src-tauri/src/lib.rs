mod config;
mod ssh;
mod process;
mod commands;

use tauri::{Manager, SystemTray, SystemTrayEvent, SystemTrayMenu, SystemTrayMenuItem, CustomMenuItem};

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    // Create system tray menu
    let launch_portal = CustomMenuItem::new("launch_portal".to_string(), "Launch Portal");
    let launch_vctt = CustomMenuItem::new("launch_vctt".to_string(), "Launch VCTT");
    let settings = CustomMenuItem::new("settings".to_string(), "Settings");
    let status = CustomMenuItem::new("status".to_string(), "Status");
    let quit = CustomMenuItem::new("quit".to_string(), "Quit");
    
    let tray_menu = SystemTrayMenu::new()
        .add_item(launch_portal)
        .add_item(launch_vctt)
        .add_native_item(SystemTrayMenuItem::Separator)
        .add_item(settings)
        .add_item(status)
        .add_native_item(SystemTrayMenuItem::Separator)
        .add_item(quit);
    
    let system_tray = SystemTray::new().with_menu(tray_menu);
    
    tauri::Builder::default()
        .plugin(tauri_plugin_opener::init())
        .plugin(tauri_plugin_shell::init())
        .plugin(tauri_plugin_store::Builder::default().build())
        .system_tray(system_tray)
        .on_system_tray_event(|app, event| {
            match event {
                SystemTrayEvent::LeftClick {
                    position: _,
                    size: _,
                    ..
                } => {
                    // Left click - could open status window
                }
                SystemTrayEvent::MenuItemClick { id, .. } => {
                    match id.as_str() {
                        "launch_portal" => {
                            let app_handle = app.clone();
                            tauri::async_runtime::spawn(async move {
                                // Get first server from config
                                if let Ok(config) = commands::load_config().await {
                                    if let Some(server) = config.servers.first() {
                                        match commands::launch_portal(server.id.clone()).await {
                                            Ok(url) => {
                                                // Use opener plugin to open URL
                                                if let Err(e) = tauri_plugin_opener::open(&url, None) {
                                                    eprintln!("Failed to open URL: {:?}", e);
                                                }
                                            }
                                            Err(e) => {
                                                eprintln!("Failed to launch portal: {}", e);
                                            }
                                        }
                                    }
                                }
                            });
                        }
                        "launch_vctt" => {
                            let app_handle = app.clone();
                            tauri::async_runtime::spawn(async move {
                                if let Ok(config) = commands::load_config().await {
                                    if let Some(app) = config.local_apps.first() {
                                        if let Err(e) = commands::launch_local_app(app.id.clone()).await {
                                            eprintln!("Failed to launch VCTT: {}", e);
                                        }
                                    }
                                }
                            });
                        }
                        "settings" => {
                            if let Some(window) = app.get_window("settings") {
                                let _ = window.show();
                                let _ = window.set_focus();
                            } else {
                                // Window should be created from tauri.conf.json
                                // If it doesn't exist, create it manually
                                if let Err(e) = tauri::WindowBuilder::new(
                                    app,
                                    "settings",
                                    tauri::WindowUrl::App("settings.html".into())
                                )
                                .title("Orchestrator Settings")
                                .inner_size(600.0, 700.0)
                                .resizable(true)
                                .visible(true)
                                .build() {
                                    eprintln!("Failed to create settings window: {:?}", e);
                                }
                            }
                        }
                        "status" => {
                            if let Some(window) = app.get_window("status") {
                                let _ = window.show();
                                let _ = window.set_focus();
                            } else {
                                if let Err(e) = tauri::WindowBuilder::new(
                                    app,
                                    "status",
                                    tauri::WindowUrl::App("status.html".into())
                                )
                                .title("Orchestrator Status")
                                .inner_size(800.0, 600.0)
                                .resizable(true)
                                .visible(true)
                                .build() {
                                    eprintln!("Failed to create status window: {:?}", e);
                                }
                            }
                        }
                        "quit" => {
                            process::cleanup_all();
                            std::process::exit(0);
                        }
                        _ => {}
                    }
                }
                _ => {}
            }
        })
        .invoke_handler(tauri::generate_handler![
            commands::launch_portal,
            commands::launch_local_app,
            commands::get_status,
            commands::save_config,
            commands::load_config,
            commands::test_connection,
            commands::is_app_running,
            commands::terminate_app,
        ])
        .setup(|app| {
            // Cleanup on exit
            let app_handle = app.handle().clone();
            app.handle().listen("tauri://close-requested", move |_| {
                process::cleanup_all();
                std::process::exit(0);
            });
            
            Ok(())
        })
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
