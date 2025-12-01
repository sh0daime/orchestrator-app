use crate::config::LocalAppConfig;
use anyhow::{Result, Context};
use std::collections::HashMap;
use std::process::{Child, Command};
use std::sync::Mutex;

static PROCESSES: Mutex<HashMap<String, Child>> = Mutex::new(HashMap::new());

pub fn launch_app(config: &LocalAppConfig) -> Result<()> {
    let mut processes = PROCESSES.lock()
        .map_err(|e| anyhow::anyhow!("Failed to lock processes: {}", e))?;
    
    // Check if already running
    if processes.contains_key(&config.id) {
        if let Some(process) = processes.get_mut(&config.id) {
            // Check if process is still alive
            match process.try_wait() {
                Ok(Some(_)) => {
                    // Process has exited, remove it
                    processes.remove(&config.id);
                }
                Ok(None) => {
                    // Process is still running
                    return Err(anyhow::anyhow!("App '{}' is already running", config.name));
                }
                Err(e) => {
                    return Err(anyhow::anyhow!("Failed to check process status: {}", e));
                }
            }
        }
    }
    
    // Launch the process
    let mut cmd = Command::new(&config.executable_path);
    
    if let Some(working_dir) = &config.working_directory {
        cmd.current_dir(working_dir);
    }
    
    let child = cmd.spawn()
        .with_context(|| format!("Failed to launch app: {}", config.executable_path))?;
    
    processes.insert(config.id.clone(), child);
    
    Ok(())
}

pub fn is_running(app_id: &str) -> bool {
    let processes = match PROCESSES.lock() {
        Ok(p) => p,
        Err(_) => return false,
    };
    
    if let Some(process) = processes.get(app_id) {
        match process.try_wait() {
            Ok(Some(_)) => false, // Process has exited
            Ok(None) => true,     // Process is still running
            Err(_) => false,
        }
    } else {
        false
    }
}

pub fn terminate(app_id: &str) -> Result<()> {
    let mut processes = PROCESSES.lock()
        .map_err(|e| anyhow::anyhow!("Failed to lock processes: {}", e))?;
    
    if let Some(mut process) = processes.remove(app_id) {
        process.kill()
            .with_context(|| format!("Failed to terminate app: {}", app_id))?;
        process.wait()?;
    }
    
    Ok(())
}

pub fn cleanup_all() {
    let mut processes = match PROCESSES.lock() {
        Ok(p) => p,
        Err(_) => return,
    };
    
    for (_, mut process) in processes.drain() {
        let _ = process.kill();
        let _ = process.wait();
    }
}

