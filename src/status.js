// PyWebView API bridge
let refreshInterval = null;
let activeServerTab = 0;
let allStatus = [];

// Logs modal management
let activeModals = [];
let modalIdCounter = 0;

// Wait for pywebview to be ready
function waitForAPI() {
    return new Promise((resolve) => {
        if (window.pywebview && window.pywebview.api) {
            resolve();
        } else {
            window.addEventListener('pywebviewready', resolve);
        }
    });
}

// Refresh status for all servers
async function refreshAllStatus() {
    try {
        await waitForAPI();
        allStatus = await window.pywebview.api.get_all_status();
        console.log("All status:", allStatus);
        
        if (!allStatus || allStatus.length === 0) {
            document.getElementById('server-tabs').innerHTML = '<p class="no-services">No servers configured</p>';
            document.getElementById('server-tab-contents').innerHTML = '';
            return;
        }
        
        renderServerTabs();
        
    } catch (error) {
        console.error("Failed to refresh status:", error);
        document.getElementById('server-tabs').innerHTML = '<p class="no-services">Error loading status</p>';
    }
}

// Render server tabs
function renderServerTabs() {
    const tabsContainer = document.getElementById('server-tabs');
    const contentsContainer = document.getElementById('server-tab-contents');
    
    tabsContainer.innerHTML = '';
    contentsContainer.innerHTML = '';
    
    allStatus.forEach((serverStatus, index) => {
        // Create tab
        const tab = document.createElement('div');
        tab.className = 'tab' + (index === activeServerTab ? ' active' : '');
        
        const statusIcon = serverStatus.connected ? '🟢' : '🔴';
        tab.innerHTML = `${statusIcon} ${serverStatus.server_name || `Server ${index + 1}`}`;
        tab.onclick = () => switchTab(index);
        tabsContainer.appendChild(tab);
        
        // Create tab content
        const content = document.createElement('div');
        content.className = 'tab-content' + (index === activeServerTab ? ' active' : '');
        content.innerHTML = renderServerContent(serverStatus);
        contentsContainer.appendChild(content);
    });
}

// Render server content
function renderServerContent(serverStatus) {
    if (!serverStatus.connected) {
        return `
            <div class="status-card">
                <div class="status-header">
                    <h2>${serverStatus.server_name}</h2>
                    <span class="status-badge disconnected">Disconnected</span>
                </div>
                <p style="color: #666;">Unable to connect to server. Check your SSH credentials in Settings.</p>
            </div>
        `;
    }
    
    if (!serverStatus.services || serverStatus.services.length === 0) {
        return `
            <div class="status-card">
                <div class="status-header">
                    <h2>${serverStatus.server_name}</h2>
                    <span class="status-badge connected">Connected</span>
                </div>
                <p class="no-services">No services configured for this server.</p>
            </div>
        `;
    }
    
    return `
        <div class="status-card">
            <div class="status-header">
                <h2>${serverStatus.server_name}</h2>
                <span class="status-badge connected">Connected</span>
            </div>
        </div>
        
        ${serverStatus.services.map(service => renderServiceCard(serverStatus.server_id, service)).join('')}
    `;
        }
        
// Render service card
function renderServiceCard(serverId, service) {
    const statusBadge = service.ready ? 
        '<span class="status-badge ready">Ready</span>' : 
        service.running ?
            '<span class="status-badge not-ready">Starting...</span>' :
            '<span class="status-badge disconnected">Stopped</span>';
    
    const containersHtml = service.containers && service.containers.length > 0 ? `
        <ul class="container-list">
            ${service.containers.map(container => `
                    <li class="container-item">
                        <div>
                            <strong>${container.name}</strong>
                        <div style="font-size: 11px; color: #666;">${container.status}</div>
                    </div>
                    <div style="display: flex; gap: 5px; align-items: center;">
                        <span class="container-state ${container.state}">${container.state}</span>
                        <button class="secondary" style="padding: 4px 8px; font-size: 11px;" 
                                onclick="viewContainerLogs('${serverId}', '${service.id}', '${container.name}')">
                            📜 Logs
                        </button>
                        ${container.state === 'running' ? `
                            <button class="secondary" style="padding: 4px 8px; font-size: 11px;" 
                                    onclick="restartContainer('${serverId}', '${service.id}', '${container.name}')">
                                🔄 Restart
                            </button>
                        ` : ''}
                        </div>
                    </li>
            `).join('')}
        </ul>
    ` : '<p style="color: #666; font-size: 13px;">No containers found</p>';
    
    const containerCountBadge = service.container_count > 0 ? 
        `<span style="background: #e9ecef; padding: 3px 8px; border-radius: 3px; font-size: 11px; margin-left: 10px;">${service.container_count} container${service.container_count > 1 ? 's' : ''}</span>` : '';
    
    return `
        <div class="service-card">
            <div class="service-header">
                <span class="service-name">${service.name}${containerCountBadge}</span>
                ${statusBadge}
            </div>
            
            ${service.ready ? `
                <div class="service-url">
                    <code>${service.url}</code>
                    <div>
                        <button class="secondary" onclick="copyServiceUrl('${service.url}')">📋 Copy</button>
                        <button class="success" onclick="openServiceUrl('${service.url}')">🌐 Open</button>
                    </div>
                </div>
            ` : ''}
            
            <div class="service-actions">
                ${!service.running ? `
                    <button class="success" onclick="launchService('${serverId}', '${service.id}')">
                        ▶ Start Service
                    </button>
                ` : `
                    <button class="danger" onclick="stopService('${serverId}', '${service.id}')">
                        ⏹ Stop Service
                    </button>
                `}
                <button class="secondary" onclick="refreshServiceStatus('${serverId}')">
                    🔄 Refresh
                </button>
            </div>
            
            <details style="margin-top: 10px;">
                <summary style="cursor: pointer; font-size: 13px; font-weight: bold;">Container Details</summary>
                ${containersHtml}
            </details>
        </div>
    `;
    }

// Switch tabs
function switchTab(index) {
    activeServerTab = index;
    
    // Update tabs
    document.querySelectorAll('.tab').forEach((tab, i) => {
        tab.classList.toggle('active', i === index);
    });
    
    // Update tab contents
    document.querySelectorAll('.tab-content').forEach((content, i) => {
        content.classList.toggle('active', i === index);
    });
}

// Launch service
async function launchService(serverId, serviceId) {
    try {
        await waitForAPI();
        console.log(`Launching service: ${serviceId} on server: ${serverId}`);
        
        // Disable button
        event.target.disabled = true;
        event.target.textContent = 'Starting...';
        
        const url = await window.pywebview.api.launch_service(serverId, serviceId);
        console.log(`Service launched: ${url}`);
        
        // Refresh status
        await refreshAllStatus();
        
        alert(`Service launched successfully!\nURL: ${url}`);
        
    } catch (error) {
        console.error("Failed to launch service:", error);
        alert("Failed to launch service: " + error);
        await refreshAllStatus();
    }
}

// Stop service
async function stopService(serverId, serviceId) {
    if (!confirm("Are you sure you want to stop this service?")) {
        return;
    }
    
    try {
        await waitForAPI();
        console.log(`Stopping service: ${serviceId} on server: ${serverId}`);
        
        // Disable button
        event.target.disabled = true;
        event.target.textContent = 'Stopping...';
        
        await window.pywebview.api.stop_service(serverId, serviceId);
        console.log(`Service stopped`);
        
        // Refresh status
        await refreshAllStatus();
        
    } catch (error) {
        console.error("Failed to stop service:", error);
        alert("Failed to stop service: " + error);
        await refreshAllStatus();
        }
}

// Refresh specific server status
async function refreshServiceStatus(serverId) {
    try {
        await waitForAPI();
        const status = await window.pywebview.api.get_status(serverId);
        
        // Update the specific server in allStatus
        const index = allStatus.findIndex(s => s.server_id === serverId);
        if (index !== -1) {
            allStatus[index] = status;
            renderServerTabs();
        }
        
    } catch (error) {
        console.error("Failed to refresh service status:", error);
    }
}

// Copy service URL
async function copyServiceUrl(url) {
    try {
        await navigator.clipboard.writeText(url);
        alert("URL copied to clipboard!");
    } catch (error) {
        console.error("Failed to copy URL:", error);
        // Fallback for older browsers
        const textArea = document.createElement("textarea");
        textArea.value = url;
        document.body.appendChild(textArea);
        textArea.select();
        document.execCommand('copy');
        document.body.removeChild(textArea);
        alert("URL copied to clipboard!");
    }
}

// Open service URL
function openServiceUrl(url) {
    window.open(url, '_blank');
}

// Initialize on page load
document.addEventListener("DOMContentLoaded", () => {
    document.getElementById("refresh-all").addEventListener("click", refreshAllStatus);
    
    // Refresh status immediately and then every 5 seconds
    refreshAllStatus();
    refreshInterval = setInterval(refreshAllStatus, 5000);
});

// Cleanup on page unload
window.addEventListener("beforeunload", () => {
    if (refreshInterval) {
        clearInterval(refreshInterval);
    }
});

// Restart container
async function restartContainer(serverId, serviceId, containerName) {
    if (!confirm(`Restart container "${containerName}"?`)) {
        return;
    }
    
    try {
        await waitForAPI();
        console.log(`Restarting container: ${containerName} in service: ${serviceId} on server: ${serverId}`);
        
        await window.pywebview.api.restart_container(serverId, serviceId, containerName);
        console.log(`Container restarted`);
        
        // Refresh status after a short delay
        setTimeout(() => refreshServiceStatus(serverId), 2000);
        
    } catch (error) {
        console.error("Failed to restart container:", error);
        alert("Failed to restart container: " + error);
    }
}

// View container logs
async function viewContainerLogs(serverId, serviceId, containerName) {
    const modalId = `logs-modal-${modalIdCounter++}`;
    
    // Create modal HTML
    const modal = document.createElement('div');
    modal.id = modalId;
    modal.className = 'logs-modal-backdrop';
    modal.innerHTML = `
        <div class="logs-modal-content">
            <div class="logs-modal-header">
                <strong class="logs-modal-title">Logs — ${containerName}</strong>
                <div class="logs-modal-controls">
                    <label style="display: flex; align-items: center; gap: 5px; font-size: 12px; margin-right: 10px;">
                        <input type="checkbox" class="logs-auto-refresh" />
                        Auto-refresh (2s)
                    </label>
                    <button class="logs-copy-btn secondary" style="padding: 4px 8px; font-size: 12px;">📋 Copy</button>
                    <button class="logs-close-btn secondary" style="padding: 4px 8px; font-size: 12px;">✖ Close</button>
                </div>
            </div>
            <div class="logs-content-wrapper">
                <div class="logs-content">Loading logs...</div>
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
    
    const logsContent = modal.querySelector('.logs-content');
    const autoRefreshCheckbox = modal.querySelector('.logs-auto-refresh');
    const copyBtn = modal.querySelector('.logs-copy-btn');
    const closeBtn = modal.querySelector('.logs-close-btn');
    
    // Modal state
    const modalState = {
        id: modalId,
        element: modal,
        serverId,
        serviceId,
        containerName,
        lastTimestamp: null,
        pollInterval: null,
        totalLines: 0,
        logsText: ''
    };
    
    activeModals.push(modalState);
    
    // Load initial logs
    await loadInitialLogs(modalState, logsContent);
    
    // Auto-refresh toggle
    autoRefreshCheckbox.addEventListener('change', (e) => {
        if (e.target.checked) {
            startLogPolling(modalState, logsContent);
        } else {
            stopLogPolling(modalState);
        }
    });
    
    // Copy logs
    copyBtn.addEventListener('click', async () => {
        try {
            await navigator.clipboard.writeText(modalState.logsText);
            const originalText = copyBtn.textContent;
            copyBtn.textContent = '✓ Copied';
            setTimeout(() => copyBtn.textContent = originalText, 2000);
        } catch (error) {
            console.error('Failed to copy logs:', error);
        }
    });
    
    // Close modal
    closeBtn.addEventListener('click', () => closeLogsModal(modalState));
    modal.addEventListener('click', (e) => {
        if (e.target === modal) {
            closeLogsModal(modalState);
        }
    });
}

// Load initial logs
async function loadInitialLogs(modalState, logsContent) {
    try {
        await waitForAPI();
        const logs = await window.pywebview.api.get_container_logs(
            modalState.serverId,
            modalState.serviceId,
            modalState.containerName,
            200
        );
        
        if (logs.startsWith('Error:')) {
            logsContent.innerHTML = `<span style="color: #d32f2f;">${logs}</span>`;
            modalState.logsText = logs;
        } else {
            modalState.logsText = logs;
            modalState.totalLines = logs.split('\n').length;
            modalState.lastTimestamp = new Date().toISOString();
            displayLogs(logsContent, logs);
        }
    } catch (error) {
        logsContent.innerHTML = `<span style="color: #d32f2f;">Error loading logs: ${error}</span>`;
        modalState.logsText = `Error: ${error}`;
    }
}

// Start log polling
function startLogPolling(modalState, logsContent) {
    stopLogPolling(modalState); // Clear any existing interval
    
    modalState.pollInterval = setInterval(async () => {
        try {
            await waitForAPI();
            const newLogs = await window.pywebview.api.get_container_logs_since(
                modalState.serverId,
                modalState.serviceId,
                modalState.containerName,
                modalState.lastTimestamp
            );
            
            if (newLogs && !newLogs.startsWith('Error:') && newLogs.trim()) {
                // Append new logs
                modalState.logsText += '\n' + newLogs;
                
                // Truncate to last 500 lines
                const lines = modalState.logsText.split('\n');
                if (lines.length > 500) {
                    modalState.logsText = lines.slice(-500).join('\n');
                }
                
                modalState.totalLines = modalState.logsText.split('\n').length;
                modalState.lastTimestamp = new Date().toISOString();
                displayLogs(logsContent, modalState.logsText, true);
            } else if (newLogs && newLogs.startsWith('Error:')) {
                // Show error but keep polling
                logsContent.innerHTML = `<span style="color: #d32f2f;">${newLogs}</span>`;
            }
        } catch (error) {
            console.error('Error polling logs:', error);
        }
    }, 2000);
}

// Stop log polling
function stopLogPolling(modalState) {
    if (modalState.pollInterval) {
        clearInterval(modalState.pollInterval);
        modalState.pollInterval = null;
    }
}

// Display logs with ANSI color conversion
function displayLogs(logsContent, logs, autoScroll = false) {
    const shouldScroll = autoScroll || isScrolledToBottom(logsContent);
    
    // Convert ANSI codes to HTML
    const htmlLogs = convertAnsiToHtml(logs);
    logsContent.innerHTML = htmlLogs;
    
    if (shouldScroll) {
        logsContent.scrollTop = logsContent.scrollHeight;
    }
}

// Check if scrolled to bottom
function isScrolledToBottom(element) {
    return element.scrollHeight - element.scrollTop <= element.clientHeight + 100;
}

// Simple ANSI to HTML converter (lightweight)
function convertAnsiToHtml(text) {
    const colors = {
        '30': '#000000', '31': '#e74856', '32': '#16c60c', '33': '#f9f1a5',
        '34': '#3b78ff', '35': '#b4009e', '36': '#61d6d6', '37': '#cccccc',
        '90': '#767676', '91': '#ff6b6b', '92': '#4cd97b', '93': '#fff899',
        '94': '#5ca7ff', '95': '#ff6fff', '96': '#9ae9e9', '97': '#ffffff'
    };
    
    // Escape HTML
    text = text.replace(/&/g, '&amp;')
               .replace(/</g, '&lt;')
               .replace(/>/g, '&gt;');
    
    // Convert ANSI color codes
    text = text.replace(/\x1b\[([0-9;]+)m/g, (match, codes) => {
        if (codes === '0' || codes === '00') {
            return '</span>';
        }
        const codeList = codes.split(';');
        const colorCode = codeList[codeList.length - 1];
        if (colors[colorCode]) {
            return `<span style="color:${colors[colorCode]}">`;
        }
        return '';
    });
    
    // Close any unclosed spans
    const openSpans = (text.match(/<span/g) || []).length;
    const closeSpans = (text.match(/<\/span>/g) || []).length;
    for (let i = 0; i < openSpans - closeSpans; i++) {
        text += '</span>';
    }
    
    return text;
}

// Close logs modal
function closeLogsModal(modalState) {
    stopLogPolling(modalState);
    modalState.element.remove();
    activeModals = activeModals.filter(m => m.id !== modalState.id);
}

// Make functions globally accessible for onclick handlers
window.launchService = launchService;
window.stopService = stopService;
window.refreshServiceStatus = refreshServiceStatus;
window.copyServiceUrl = copyServiceUrl;
window.openServiceUrl = openServiceUrl;
window.restartContainer = restartContainer;
window.viewContainerLogs = viewContainerLogs;

