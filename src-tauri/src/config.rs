use serde::{Deserialize, Serialize};
use std::path::PathBuf;
use anyhow::{Result, Context};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ServerConfig {
    pub id: String,
    pub name: String,
    pub host: String,
    pub port: u16,
    pub username: String,
    pub ssh_key_path: String,
    pub portal_port: u16,
    pub portal_path: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct LocalAppConfig {
    pub id: String,
    pub name: String,
    pub executable_path: String,
    pub working_directory: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Preferences {
    #[serde(default = "default_true")]
    pub auto_start_portal: bool,
    #[serde(default = "default_true")]
    pub minimize_to_tray: bool,
    #[serde(default)]
    pub startup_launch: bool,
}

fn default_true() -> bool {
    true
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AppConfig {
    pub version: String,
    pub servers: Vec<ServerConfig>,
    pub local_apps: Vec<LocalAppConfig>,
    #[serde(default)]
    pub preferences: Preferences,
}

impl Default for AppConfig {
    fn default() -> Self {
        Self {
            version: "1.0".to_string(),
            servers: Vec::new(),
            local_apps: Vec::new(),
            preferences: Preferences::default(),
        }
    }
}

impl Default for Preferences {
    fn default() -> Self {
        Self {
            auto_start_portal: true,
            minimize_to_tray: true,
            startup_launch: false,
        }
    }
}

impl AppConfig {
    pub fn load() -> Result<Self> {
        let config_path = Self::config_path()?;
        
        if !config_path.exists() {
            return Ok(Self::default());
        }
        
        let content = std::fs::read_to_string(&config_path)
            .with_context(|| format!("Failed to read config file: {:?}", config_path))?;
        
        let config: AppConfig = serde_json::from_str(&content)
            .with_context(|| "Failed to parse config file")?;
        
        Ok(config)
    }
    
    pub fn save(&self) -> Result<()> {
        let config_path = Self::config_path()?;
        
        // Create parent directory if it doesn't exist
        if let Some(parent) = config_path.parent() {
            std::fs::create_dir_all(parent)
                .with_context(|| format!("Failed to create config directory: {:?}", parent))?;
        }
        
        let content = serde_json::to_string_pretty(self)
            .with_context(|| "Failed to serialize config")?;
        
        std::fs::write(&config_path, content)
            .with_context(|| format!("Failed to write config file: {:?}", config_path))?;
        
        Ok(())
    }
    
    fn config_path() -> Result<PathBuf> {
        let mut path = dirs::config_dir()
            .ok_or_else(|| anyhow::anyhow!("Failed to get config directory"))?;
        path.push("orchestrator-app");
        path.push("config.json");
        Ok(path)
    }
    
    pub fn get_server(&self, id: &str) -> Option<&ServerConfig> {
        self.servers.iter().find(|s| s.id == id)
    }
    
    pub fn get_local_app(&self, id: &str) -> Option<&LocalAppConfig> {
        self.local_apps.iter().find(|a| a.id == id)
    }
}

