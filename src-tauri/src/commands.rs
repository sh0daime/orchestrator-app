use crate::config::{AppConfig, ServerConfig, LocalAppConfig};
use crate::ssh::{SshConnection, ContainerStatus};
use crate::process;
use anyhow::{Result, Context};
use serde::{Deserialize, Serialize};
use std::time::Duration;
use tokio::time::sleep;

#[derive(Debug, Serialize, Deserialize)]
pub struct StatusInfo {
    pub connected: bool,
    pub containers: Vec<ContainerStatus>,
    pub portal_url: Option<String>,
    pub portal_ready: bool,
}

#[tauri::command]
pub async fn launch_portal(server_id: String) -> Result<String, String> {
    let config = AppConfig::load()
        .map_err(|e| format!("Failed to load config: {}", e))?;
    
    let server = config.get_server(&server_id)
        .ok_or_else(|| format!("Server not found: {}", server_id))?;
    
    let connection = SshConnection::connect(server)
        .map_err(|e| format!("Failed to connect to server: {}", e))?;
    
    // Check current status
    let containers = connection.check_containers()
        .map_err(|e| format!("Failed to check containers: {}", e))?;
    
    let portal_running = containers.iter()
        .any(|c| c.name == "ai-portal" && c.state == "running");
    
    // Start if not running
    if !portal_running {
        connection.start_portal()
            .map_err(|e| format!("Failed to start portal: {}", e))?;
        
        // Wait for portal to be ready (with timeout)
        let max_wait = 120; // 2 minutes
        let mut waited = 0;
        let mut ready = false;
        
        while waited < max_wait {
            sleep(Duration::from_secs(2)).await;
            waited += 2;
            
            match connection.check_portal_health(server.portal_port) {
                Ok(true) => {
                    ready = true;
                    break;
                }
                Ok(false) => continue,
                Err(_) => continue,
            }
        }
        
        if !ready {
            return Err(format!("Portal did not become ready within {} seconds", max_wait));
        }
    }
    
    let portal_url = format!("http://{}:{}", server.host, server.portal_port);
    Ok(portal_url)
}

#[tauri::command]
pub async fn launch_local_app(app_id: String) -> Result<(), String> {
    let config = AppConfig::load()
        .map_err(|e| format!("Failed to load config: {}", e))?;
    
    let app = config.get_local_app(&app_id)
        .ok_or_else(|| format!("App not found: {}", app_id))?;
    
    process::launch_app(app)
        .map_err(|e| format!("Failed to launch app: {}", e))?;
    
    Ok(())
}

#[tauri::command]
pub async fn get_status(server_id: String) -> Result<StatusInfo, String> {
    let config = AppConfig::load()
        .map_err(|e| format!("Failed to load config: {}", e))?;
    
    let server = config.get_server(&server_id)
        .ok_or_else(|| format!("Server not found: {}", server_id))?;
    
    let connection = match SshConnection::connect(server) {
        Ok(conn) => conn,
        Err(e) => {
            return Ok(StatusInfo {
                connected: false,
                containers: Vec::new(),
                portal_url: None,
                portal_ready: false,
            });
        }
    };
    
    let containers = connection.check_containers()
        .unwrap_or_default();
    
    let portal_ready = connection.check_portal_health(server.portal_port)
        .unwrap_or(false);
    
    let portal_url = Some(format!("http://{}:{}", server.host, server.portal_port));
    
    Ok(StatusInfo {
        connected: true,
        containers,
        portal_url,
        portal_ready,
    })
}

#[tauri::command]
pub async fn save_config(config: AppConfig) -> Result<(), String> {
    config.save()
        .map_err(|e| format!("Failed to save config: {}", e))?;
    Ok(())
}

#[tauri::command]
pub async fn load_config() -> Result<AppConfig, String> {
    AppConfig::load()
        .map_err(|e| format!("Failed to load config: {}", e))
}

#[tauri::command]
pub async fn test_connection(server: ServerConfig) -> Result<String, String> {
    let connection = SshConnection::connect(&server)
        .map_err(|e| format!("Connection failed: {}", e))?;
    
    // Test by running a simple command
    let output = connection.execute_command("echo 'Connection successful'")
        .map_err(|e| format!("Command execution failed: {}", e))?;
    
    Ok(output)
}

#[tauri::command]
pub fn is_app_running(app_id: String) -> bool {
    process::is_running(&app_id)
}

#[tauri::command]
pub fn terminate_app(app_id: String) -> Result<(), String> {
    process::terminate(&app_id)
        .map_err(|e| format!("Failed to terminate app: {}", e))?;
    Ok(())
}

