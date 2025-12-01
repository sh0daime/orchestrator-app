use crate::config::ServerConfig;
use anyhow::{Result, Context};
use serde::{Deserialize, Serialize};
use ssh2::Session;
use std::io::prelude::*;
use std::net::TcpStream;
use std::path::Path;
use std::time::Duration;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ContainerStatus {
    pub name: String,
    pub status: String,
    pub state: String, // running, stopped, starting, etc.
}

pub struct SshConnection {
    session: Session,
    host: String,
    portal_path: String,
}

impl SshConnection {
    pub fn connect(config: &ServerConfig) -> Result<Self> {
        let tcp = TcpStream::connect((config.host.as_str(), config.port))
            .with_context(|| format!("Failed to connect to {}:{}", config.host, config.port))?;
        
        tcp.set_read_timeout(Some(Duration::from_secs(10)))?;
        tcp.set_write_timeout(Some(Duration::from_secs(10)))?;
        
        let mut session = Session::new()
            .ok_or_else(|| anyhow::anyhow!("Failed to create SSH session"))?;
        
        session.set_tcp_stream(tcp);
        session.handshake()
            .with_context(|| "SSH handshake failed")?;
        
        // Try to authenticate with SSH key first, then fall back to password
        let key_path = Path::new(&config.ssh_key_path);
        if key_path.exists() {
            session.userauth_pubkey_file(
                &config.username,
                None,
                key_path,
                None,
            ).with_context(|| format!("SSH key authentication failed for key: {:?}", key_path))?;
        } else {
            return Err(anyhow::anyhow!("SSH key not found: {:?}", key_path));
        }
        
        if !session.authenticated() {
            return Err(anyhow::anyhow!("SSH authentication failed"));
        }
        
        Ok(Self {
            session,
            host: config.host.clone(),
            portal_path: config.portal_path.clone(),
        })
    }
    
    pub fn execute_command(&self, cmd: &str) -> Result<String> {
        let mut channel = self.session.channel_session()
            .with_context(|| "Failed to create SSH channel")?;
        
        channel.exec(cmd)
            .with_context(|| format!("Failed to execute command: {}", cmd))?;
        
        let mut output = String::new();
        channel.read_to_string(&mut output)
            .with_context(|| "Failed to read command output")?;
        
        channel.wait_close()?;
        let exit_status = channel.exit_status()?;
        
        if exit_status != 0 {
            return Err(anyhow::anyhow!("Command failed with exit status {}: {}", exit_status, output));
        }
        
        Ok(output)
    }
    
    pub fn check_containers(&self) -> Result<Vec<ContainerStatus>> {
        let cmd = format!(
            "cd {} && docker compose ps --format json",
            self.portal_path
        );
        
        let output = self.execute_command(&cmd)?;
        
        // Parse JSON output from docker compose ps
        let mut containers = Vec::new();
        for line in output.lines() {
            if let Ok(container) = serde_json::from_str::<serde_json::Value>(line) {
                if let (Some(name), Some(status), Some(state)) = (
                    container.get("Name").and_then(|v| v.as_str()),
                    container.get("Status").and_then(|v| v.as_str()),
                    container.get("State").and_then(|v| v.as_str()),
                ) {
                    containers.push(ContainerStatus {
                        name: name.to_string(),
                        status: status.to_string(),
                        state: state.to_string(),
                    });
                }
            }
        }
        
        Ok(containers)
    }
    
    pub fn start_portal(&self) -> Result<()> {
        let cmd = format!(
            "cd {} && docker compose up -d",
            self.portal_path
        );
        
        self.execute_command(&cmd)
            .with_context(|| "Failed to start portal containers")?;
        
        Ok(())
    }
    
    pub fn stop_portal(&self) -> Result<()> {
        let cmd = format!(
            "cd {} && docker compose down",
            self.portal_path
        );
        
        self.execute_command(&cmd)
            .with_context(|| "Failed to stop portal containers")?;
        
        Ok(())
    }
    
    pub fn get_logs(&self, service: Option<&str>, lines: usize) -> Result<String> {
        let cmd = if let Some(service) = service {
            format!(
                "cd {} && docker compose logs --tail {} {}",
                self.portal_path, lines, service
            )
        } else {
            format!(
                "cd {} && docker compose logs --tail {}",
                self.portal_path, lines
            )
        };
        
        self.execute_command(&cmd)
    }
    
    pub fn check_portal_health(&self, port: u16) -> Result<bool> {
        let cmd = format!(
            "curl -s -o /dev/null -w '%{{http_code}}' http://localhost:{} || echo '000'",
            port
        );
        
        let output = self.execute_command(&cmd)?;
        let status_code = output.trim();
        
        Ok(status_code == "200")
    }
}

// Add ssh2 dependency requires this
impl Drop for SshConnection {
    fn drop(&mut self) {
        let _ = self.session.disconnect(None, "Connection closed", None);
    }
}

