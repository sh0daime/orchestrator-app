import { invoke } from "@tauri-apps/api/core";
import { getWindow } from "@tauri-apps/api/window";

let config = null;

async function loadConfig() {
    try {
        config = await invoke("load_config");
        
        // Load server config (first server)
        if (config.servers && config.servers.length > 0) {
            const server = config.servers[0];
            document.getElementById("server-name").value = server.name || "";
            document.getElementById("server-host").value = server.host || "";
            document.getElementById("server-port").value = server.port || 22;
            document.getElementById("server-username").value = server.username || "";
            document.getElementById("ssh-key-path").value = server.ssh_key_path || "";
            document.getElementById("portal-port").value = server.portal_port || 8080;
            document.getElementById("portal-path").value = server.portal_path || "";
        }
        
        // Load app config (first app)
        if (config.local_apps && config.local_apps.length > 0) {
            const app = config.local_apps[0];
            document.getElementById("app-name").value = app.name || "";
            document.getElementById("app-path").value = app.executable_path || "";
            document.getElementById("app-working-dir").value = app.working_directory || "";
        }
    } catch (error) {
        console.error("Failed to load config:", error);
        alert("Failed to load configuration: " + error);
    }
}

async function saveConfig() {
    try {
        if (!config) {
            config = await invoke("load_config");
        }
        
        // Update server config
        const serverConfig = {
            id: config.servers && config.servers.length > 0 ? config.servers[0].id : "default",
            name: document.getElementById("server-name").value || "Default Server",
            host: document.getElementById("server-host").value,
            port: parseInt(document.getElementById("server-port").value) || 22,
            username: document.getElementById("server-username").value,
            ssh_key_path: document.getElementById("ssh-key-path").value,
            portal_port: parseInt(document.getElementById("portal-port").value) || 8080,
            portal_path: document.getElementById("portal-path").value,
        };
        
        // Update app config
        const appConfig = {
            id: config.local_apps && config.local_apps.length > 0 ? config.local_apps[0].id : "vctt",
            name: document.getElementById("app-name").value || "VCTT",
            executable_path: document.getElementById("app-path").value,
            working_directory: document.getElementById("app-working-dir").value || null,
        };
        
        // Update config object
        config.servers = [serverConfig];
        config.local_apps = [appConfig];
        
        await invoke("save_config", { config });
        alert("Configuration saved successfully!");
    } catch (error) {
        console.error("Failed to save config:", error);
        alert("Failed to save configuration: " + error);
    }
}

async function testConnection() {
    const resultDiv = document.getElementById("test-result");
    resultDiv.innerHTML = "Testing connection...";
    resultDiv.className = "test-result";
    
    try {
        const serverConfig = {
            id: "test",
            name: document.getElementById("server-name").value || "Test Server",
            host: document.getElementById("server-host").value,
            port: parseInt(document.getElementById("server-port").value) || 22,
            username: document.getElementById("server-username").value,
            ssh_key_path: document.getElementById("ssh-key-path").value,
            portal_port: parseInt(document.getElementById("portal-port").value) || 8080,
            portal_path: document.getElementById("portal-path").value,
        };
        
        const result = await invoke("test_connection", { server: serverConfig });
        resultDiv.innerHTML = "✓ Connection successful!<br>" + result;
        resultDiv.className = "test-result success";
    } catch (error) {
        resultDiv.innerHTML = "✗ Connection failed: " + error;
        resultDiv.className = "test-result error";
    }
}

document.addEventListener("DOMContentLoaded", () => {
    document.getElementById("save-config").addEventListener("click", saveConfig);
    document.getElementById("load-config").addEventListener("click", loadConfig);
    document.getElementById("test-connection").addEventListener("click", testConnection);
    
    // Load config on startup
    loadConfig();
});

