import { invoke } from "@tauri-apps/api/core";
import { open } from "@tauri-apps/plugin-opener";
import { getWindow } from "@tauri-apps/api/window";

let refreshInterval = null;

async function refreshStatus() {
    try {
        // Get first server from config
        const config = await invoke("load_config");
        if (!config.servers || config.servers.length === 0) {
            document.getElementById("connection-status").textContent = "No Server Configured";
            document.getElementById("connection-status").className = "status-badge disconnected";
            return;
        }
        
        const serverId = config.servers[0].id;
        const status = await invoke("get_status", { serverId });
        
        // Update connection status
        const connectionBadge = document.getElementById("connection-status");
        if (status.connected) {
            connectionBadge.textContent = "Connected";
            connectionBadge.className = "status-badge connected";
        } else {
            connectionBadge.textContent = "Disconnected";
            connectionBadge.className = "status-badge disconnected";
        }
        
        // Update portal status
        const portalBadge = document.getElementById("portal-status");
        if (status.portal_ready) {
            portalBadge.textContent = "Ready";
            portalBadge.className = "status-badge ready";
        } else {
            portalBadge.textContent = "Not Ready";
            portalBadge.className = "status-badge disconnected";
        }
        
        // Update portal URL
        if (status.portal_url) {
            document.getElementById("portal-url-text").textContent = status.portal_url;
            document.getElementById("portal-url-container").style.display = "block";
        } else {
            document.getElementById("portal-url-container").style.display = "none";
        }
        
        // Update containers list
        const containerList = document.getElementById("container-list");
        if (status.containers && status.containers.length > 0) {
            containerList.innerHTML = status.containers.map(container => {
                const stateClass = container.state === "running" ? "running" : 
                                  container.state === "starting" ? "starting" : "stopped";
                return `
                    <li class="container-item">
                        <div>
                            <strong>${container.name}</strong>
                            <div style="font-size: 12px; color: #666; margin-top: 4px;">${container.status}</div>
                        </div>
                        <span class="container-state ${stateClass}">${container.state}</span>
                    </li>
                `;
            }).join("");
        } else {
            containerList.innerHTML = "<li>No containers found</li>";
        }
        
    } catch (error) {
        console.error("Failed to refresh status:", error);
        document.getElementById("connection-status").textContent = "Error";
        document.getElementById("connection-status").className = "status-badge disconnected";
    }
}

async function copyUrl() {
    const url = document.getElementById("portal-url-text").textContent;
    await navigator.clipboard.writeText(url);
    alert("URL copied to clipboard!");
}

async function openPortal() {
    const url = document.getElementById("portal-url-text").textContent;
    try {
        await open(url);
    } catch (error) {
        console.error("Failed to open portal:", error);
        // Fallback: try using window.open
        window.open(url, '_blank');
    }
}

async function restartPortal() {
    if (!confirm("Are you sure you want to restart the portal? This will stop and start all containers.")) {
        return;
    }
    
    try {
        const config = await invoke("load_config");
        if (!config.servers || config.servers.length === 0) {
            alert("No server configured");
            return;
        }
        
        const serverId = config.servers[0].id;
        // Note: We'd need to add a restart_portal command for this
        alert("Restart functionality will be implemented in the next phase");
    } catch (error) {
        alert("Failed to restart portal: " + error);
    }
}

document.addEventListener("DOMContentLoaded", () => {
    document.getElementById("refresh-status").addEventListener("click", refreshStatus);
    document.getElementById("copy-url").addEventListener("click", copyUrl);
    document.getElementById("open-portal").addEventListener("click", openPortal);
    document.getElementById("restart-portal").addEventListener("click", restartPortal);
    
    // Refresh status immediately and then every 5 seconds
    refreshStatus();
    refreshInterval = setInterval(refreshStatus, 5000);
});

// Cleanup on page unload
window.addEventListener("beforeunload", () => {
    if (refreshInterval) {
        clearInterval(refreshInterval);
    }
});

