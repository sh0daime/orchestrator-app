// PyWebView API bridge (replaces Tauri invoke)
let config = null;
let activeServerTab = 0;

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

// Generate unique ID
function generateId() {
    return 'id-' + Date.now() + '-' + Math.random().toString(36).substr(2, 9);
}

// Load configuration
async function loadConfig() {
    try {
        await waitForAPI();
        config = await window.pywebview.api.load_config();
        console.log("Loaded config:", config);
        
        // Ensure config has the right structure
        if (!config.servers) config.servers = [];
        if (!config.local_apps) config.local_apps = [];
        
        // If no servers, add a default one
        if (config.servers.length === 0) {
            config.servers.push({
                id: generateId(),
                name: "New Server",
                host: "",
                port: 22,
                username: "",
                ssh_key_path: "",
                services: []
            });
        }
        
        renderServers();
        renderLocalApps();
        
    } catch (error) {
        console.error("Failed to load config:", error);
        alert("Failed to load configuration: " + error);
    }
}

// Save configuration
async function saveConfig() {
    try {
        await waitForAPI();
        
        // Collect data from UI
        collectServerData();
        collectLocalAppData();
        
        console.log("Saving config:", config);
        await window.pywebview.api.save_config(config);
        alert("Configuration saved successfully!");
        
    } catch (error) {
        console.error("Failed to save config:", error);
        alert("Failed to save configuration: " + error);
    }
}

// Collect server data from UI
function collectServerData() {
    config.servers.forEach((server, serverIndex) => {
        const prefix = `server-${serverIndex}`;
        server.name = document.getElementById(`${prefix}-name`)?.value || "";
        server.host = document.getElementById(`${prefix}-host`)?.value || "";
        server.port = parseInt(document.getElementById(`${prefix}-port`)?.value) || 22;
        server.username = document.getElementById(`${prefix}-username`)?.value || "";
        server.ssh_key_path = document.getElementById(`${prefix}-ssh-key`)?.value || "";
        
        // Collect service data
        server.services.forEach((service, serviceIndex) => {
            const sPrefix = `${prefix}-service-${serviceIndex}`;
            service.name = document.getElementById(`${sPrefix}-name`)?.value || "";
            service.container_name = document.getElementById(`${sPrefix}-container`)?.value || "";
            service.port = parseInt(document.getElementById(`${sPrefix}-port`)?.value) || 8080;
            service.path = document.getElementById(`${sPrefix}-path`)?.value || "";
            service.healthcheck_path = document.getElementById(`${sPrefix}-health`)?.value || "/";
            service.pre_launch_command = document.getElementById(`${sPrefix}-prelaunch`)?.value || null;
        });
    });
}

// Collect local app data from UI
function collectLocalAppData() {
    config.local_apps.forEach((app, appIndex) => {
        const prefix = `app-${appIndex}`;
        app.name = document.getElementById(`${prefix}-name`)?.value || "";
        app.executable_path = document.getElementById(`${prefix}-path`)?.value || "";
        app.working_directory = document.getElementById(`${prefix}-workdir`)?.value || null;
        app.use_shell = document.getElementById(`${prefix}-use-shell`)?.checked || false;
        app.conda_env = app.use_shell ? (document.getElementById(`${prefix}-conda`)?.value || null) : null;
        app.shell_command = app.use_shell ? (document.getElementById(`${prefix}-shell-cmd`)?.value || null) : null;
        app.install_dependencies = document.getElementById(`${prefix}-install-deps`)?.checked || false;
        app.requirements_file = app.install_dependencies ? (document.getElementById(`${prefix}-requirements`)?.value || null) : null;
    });
}

// Render servers (tabs and content)
function renderServers() {
    const tabsContainer = document.getElementById('server-tabs');
    const contentsContainer = document.getElementById('server-tab-contents');
    
    tabsContainer.innerHTML = '';
    contentsContainer.innerHTML = '';
    
    config.servers.forEach((server, index) => {
        // Create tab
        const tab = document.createElement('div');
        tab.className = 'tab' + (index === activeServerTab ? ' active' : '');
        tab.innerHTML = `
            <span>${server.name || `Server ${index + 1}`}</span>
            ${config.servers.length > 1 ? `<span class="tab-close" data-index="${index}">×</span>` : ''}
        `;
        tab.onclick = (e) => {
            if (!e.target.classList.contains('tab-close')) {
                switchTab(index);
            }
        };
        tabsContainer.appendChild(tab);
        
        // Create tab content
        const content = document.createElement('div');
        content.className = 'tab-content' + (index === activeServerTab ? ' active' : '');
        content.id = `server-tab-${index}`;
        content.innerHTML = renderServerContent(server, index);
        contentsContainer.appendChild(content);
    });
    
    // Add "Add Server" button
    const addBtn = document.createElement('button');
    addBtn.className = 'add-tab-btn';
    addBtn.textContent = '+ Add Server';
    addBtn.onclick = addServer;
    tabsContainer.appendChild(addBtn);
    
    // Attach event listeners
    attachServerEventListeners();
}

// Render server content
function renderServerContent(server, serverIndex) {
    const prefix = `server-${serverIndex}`;
    
    return `
        <div class="server-info-section">
            <h2>Server Information</h2>
            <div class="form-group">
                <label for="${prefix}-name">Server Name</label>
                <input type="text" id="${prefix}-name" value="${server.name || ''}" placeholder="Production Server">
            </div>
            <div class="form-group">
                <label for="${prefix}-host">Host / IP Address</label>
                <input type="text" id="${prefix}-host" value="${server.host || ''}" placeholder="192.168.1.100">
            </div>
            <div class="form-group">
                <label for="${prefix}-port">SSH Port</label>
                <input type="number" id="${prefix}-port" value="${server.port || 22}">
            </div>
            <div class="form-group">
                <label for="${prefix}-username">Username</label>
                <input type="text" id="${prefix}-username" value="${server.username || ''}" placeholder="calvin">
            </div>
            <div class="form-group">
                <label for="${prefix}-ssh-key">SSH Key Path</label>
                <input type="text" id="${prefix}-ssh-key" value="${server.ssh_key_path || ''}" placeholder="~/.ssh/id_rsa">
            </div>
            <button class="test-connection-btn" data-server-index="${serverIndex}">Test Connection</button>
            <div id="${prefix}-test-result" class="test-result" style="display: none;"></div>
        </div>
        
        <div class="services-section">
            <h2>Services</h2>
            <div class="accordion" id="${prefix}-services">
                ${renderServices(server.services, serverIndex)}
            </div>
            <button class="success add-service-btn" data-server-index="${serverIndex}">+ Add Service</button>
        </div>
    `;
}

// Render services accordion
function renderServices(services, serverIndex) {
    if (!services || services.length === 0) {
        return '<p style="color: #666;">No services configured. Click "Add Service" to add one.</p>';
    }
    
    return services.map((service, serviceIndex) => {
        const prefix = `server-${serverIndex}-service-${serviceIndex}`;
        return `
            <div class="accordion-item">
                <div class="accordion-header" data-server="${serverIndex}" data-service="${serviceIndex}">
                    <span>
                        <span class="accordion-toggle">▶</span>
                        ${service.name || `Service ${serviceIndex + 1}`}
                    </span>
                    <div class="accordion-actions">
                        <button class="danger remove-service-btn" data-server="${serverIndex}" data-service="${serviceIndex}">Remove</button>
                    </div>
                </div>
                <div class="accordion-content">
                    <div class="form-group">
                        <label for="${prefix}-name">Service Name</label>
                        <input type="text" id="${prefix}-name" value="${service.name || ''}" placeholder="AI Portal">
                    </div>
                    <div class="form-group">
                        <label for="${prefix}-container">Container Name</label>
                        <input type="text" id="${prefix}-container" value="${service.container_name || ''}" placeholder="ai-portal">
                        <small>Name of the Docker container to manage</small>
                    </div>
                    <div class="form-group">
                        <label for="${prefix}-port">Port</label>
                        <input type="number" id="${prefix}-port" value="${service.port || 8080}">
                    </div>
                    <div class="form-group">
                        <label for="${prefix}-path">Path on Server</label>
                        <input type="text" id="${prefix}-path" value="${service.path || ''}" placeholder="/home/user/app">
                        <small>Directory containing docker-compose.yml</small>
                    </div>
                    <div class="form-group">
                        <label for="${prefix}-health">Health Check Path</label>
                        <input type="text" id="${prefix}-health" value="${service.healthcheck_path || '/'}" placeholder="/">
                        <small>URL path to check service health (e.g., /, /health, /api/status)</small>
                    </div>
                    <div class="form-group">
                        <label for="${prefix}-prelaunch">Pre-Launch Command (optional)</label>
                        <input type="text" id="${prefix}-prelaunch" value="${service.pre_launch_command || ''}" placeholder="python launcher.py">
                        <small>Command to run before starting (e.g., for env setup, permission fixes)</small>
                    </div>
                </div>
            </div>
        `;
    }).join('');
}

// Render local apps
function renderLocalApps() {
    const container = document.getElementById('local-apps-container');
    
    if (!config.local_apps || config.local_apps.length === 0) {
        container.innerHTML = '<p style="color: #666;">No local applications configured.</p>';
        return;
    }
    
    container.innerHTML = config.local_apps.map((app, index) => {
        const prefix = `app-${index}`;
        return `
            <div class="accordion-item">
                <div class="accordion-header" data-app="${index}">
                    <span>
                        <span class="accordion-toggle">▶</span>
                        ${app.name || `App ${index + 1}`}
                    </span>
                    <button class="danger remove-app-btn" data-app="${index}">Remove</button>
                </div>
                <div class="accordion-content">
                    <div class="form-group">
                        <label for="${prefix}-name">App Name</label>
                        <input type="text" id="${prefix}-name" value="${app.name || ''}" placeholder="VCTT">
                    </div>
                    <div class="form-group">
                        <label for="${prefix}-path">Executable Path</label>
                        <input type="text" id="${prefix}-path" value="${app.executable_path || ''}" placeholder="main.py">
                        <small>Python script name or full path</small>
                    </div>
                    <div class="form-group">
                        <label for="${prefix}-workdir">Working Directory</label>
                        <input type="text" id="${prefix}-workdir" value="${app.working_directory || ''}" placeholder="C:\\Users\\user\\app">
                    </div>
                    <div class="form-group">
                        <label>
                            <input type="checkbox" id="${prefix}-use-shell" ${app.use_shell ? 'checked' : ''}>
                            Use Shell Command (for Python/Conda apps)
                        </label>
                    </div>
                    <div class="form-group" id="${prefix}-conda-group" style="display: ${app.use_shell ? 'block' : 'none'};">
                        <label for="${prefix}-conda">Conda Environment Name</label>
                        <input type="text" id="${prefix}-conda" value="${app.conda_env || ''}" placeholder="myenv">
                    </div>
                    <div class="form-group" id="${prefix}-shell-cmd-group" style="display: ${app.use_shell ? 'block' : 'none'};">
                        <label for="${prefix}-shell-cmd">Custom Shell Command (optional)</label>
                        <input type="text" id="${prefix}-shell-cmd" value="${app.shell_command || ''}" placeholder="conda activate env && python main.py">
                    </div>
                    <div class="form-group" id="${prefix}-install-deps-group" style="display: ${app.use_shell ? 'block' : 'none'};">
                        <label>
                            <input type="checkbox" id="${prefix}-install-deps" ${app.install_dependencies ? 'checked' : ''}>
                            Install dependencies before launch
                        </label>
                    </div>
                    <div class="form-group" id="${prefix}-requirements-group" style="display: ${app.install_dependencies && app.use_shell ? 'block' : 'none'};">
                        <label for="${prefix}-requirements">Requirements File Path</label>
                        <input type="text" id="${prefix}-requirements" value="${app.requirements_file || ''}" placeholder="requirements.txt">
                    </div>
                </div>
            </div>
        `;
    }).join('');
    
    attachLocalAppEventListeners();
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

// Add server
function addServer() {
    config.servers.push({
        id: generateId(),
        name: "New Server",
        host: "",
        port: 22,
        username: "",
        ssh_key_path: "",
        services: []
    });
    activeServerTab = config.servers.length - 1;
    renderServers();
}

// Remove server
function removeServer(index) {
    if (config.servers.length <= 1) {
        alert("Cannot remove the last server.");
        return;
    }
    
    if (confirm(`Remove server "${config.servers[index].name || 'Server ' + (index + 1)}"?`)) {
        config.servers.splice(index, 1);
        if (activeServerTab >= config.servers.length) {
            activeServerTab = config.servers.length - 1;
        }
        renderServers();
    }
}

// Add service
function addService(serverIndex) {
    config.servers[serverIndex].services.push({
        id: generateId(),
        name: "New Service",
        container_name: "",
        port: 8080,
        path: "",
        healthcheck_path: "/",
        pre_launch_command: null
    });
    renderServers();
    switchTab(serverIndex);
}

// Remove service
function removeService(serverIndex, serviceIndex) {
    if (confirm(`Remove service "${config.servers[serverIndex].services[serviceIndex].name || 'Service ' + (serviceIndex + 1)}"?`)) {
        config.servers[serverIndex].services.splice(serviceIndex, 1);
        renderServers();
        switchTab(serverIndex);
    }
}

// Add local app
function addLocalApp() {
    config.local_apps.push({
        id: generateId(),
        name: "New App",
        executable_path: "",
        working_directory: null,
        use_shell: false,
        conda_env: null,
        shell_command: null,
        install_dependencies: false,
        requirements_file: null
    });
    renderLocalApps();
}

// Remove local app
function removeLocalApp(index) {
    if (confirm(`Remove app "${config.local_apps[index].name || 'App ' + (index + 1)}"?`)) {
        config.local_apps.splice(index, 1);
        renderLocalApps();
    }
}

// Test connection
async function testConnection(serverIndex) {
    const prefix = `server-${serverIndex}`;
    const resultDiv = document.getElementById(`${prefix}-test-result`);
    resultDiv.style.display = 'block';
    resultDiv.innerHTML = "Testing connection...";
    resultDiv.className = "test-result";
    
    try {
        await waitForAPI();
        
        const serverConfig = {
            host: document.getElementById(`${prefix}-host`).value,
            port: parseInt(document.getElementById(`${prefix}-port`).value) || 22,
            username: document.getElementById(`${prefix}-username`).value,
            ssh_key_path: document.getElementById(`${prefix}-ssh-key`).value
        };
        
        const result = await window.pywebview.api.test_connection(serverConfig);
        resultDiv.innerHTML = "✓ Connection successful!<br>" + result;
        resultDiv.className = "test-result success";
    } catch (error) {
        resultDiv.innerHTML = "✗ Connection failed: " + error;
        resultDiv.className = "test-result error";
    }
}

// Attach server event listeners
function attachServerEventListeners() {
    // Tab close buttons
    document.querySelectorAll('.tab-close').forEach(btn => {
        btn.onclick = (e) => {
            e.stopPropagation();
            removeServer(parseInt(e.target.dataset.index));
        };
    });
    
    // Test connection buttons
    document.querySelectorAll('.test-connection-btn').forEach(btn => {
        btn.onclick = () => testConnection(parseInt(btn.dataset.serverIndex));
    });
    
    // Add service buttons
    document.querySelectorAll('.add-service-btn').forEach(btn => {
        btn.onclick = () => addService(parseInt(btn.dataset.serverIndex));
    });
    
    // Remove service buttons
    document.querySelectorAll('.remove-service-btn').forEach(btn => {
        btn.onclick = (e) => {
            e.stopPropagation();
            removeService(parseInt(btn.dataset.server), parseInt(btn.dataset.service));
        };
    });
    
    // Accordion toggles
    document.querySelectorAll('.accordion-header').forEach(header => {
        header.onclick = (e) => {
            if (e.target.tagName === 'BUTTON') return;
            
            const content = header.nextElementSibling;
            const toggle = header.querySelector('.accordion-toggle');
            const isOpen = content.classList.contains('active');
            
            content.classList.toggle('active');
            toggle.textContent = isOpen ? '▶' : '▼';
        };
    });
}

// Attach local app event listeners
function attachLocalAppEventListeners() {
    // Remove app buttons
    document.querySelectorAll('.remove-app-btn').forEach(btn => {
        btn.onclick = (e) => {
            e.stopPropagation();
            removeLocalApp(parseInt(btn.dataset.app));
        };
    });
    
    // Use shell checkboxes
    config.local_apps.forEach((app, index) => {
        const prefix = `app-${index}`;
        const useShellCheckbox = document.getElementById(`${prefix}-use-shell`);
        const installDepsCheckbox = document.getElementById(`${prefix}-install-deps`);
        
        if (useShellCheckbox) {
            useShellCheckbox.onchange = () => {
                const checked = useShellCheckbox.checked;
                document.getElementById(`${prefix}-conda-group`).style.display = checked ? 'block' : 'none';
                document.getElementById(`${prefix}-shell-cmd-group`).style.display = checked ? 'block' : 'none';
                document.getElementById(`${prefix}-install-deps-group`).style.display = checked ? 'block' : 'none';
                if (!checked) {
                    document.getElementById(`${prefix}-requirements-group`).style.display = 'none';
                }
            };
        }
        
        if (installDepsCheckbox) {
            installDepsCheckbox.onchange = () => {
                const useShell = useShellCheckbox?.checked;
                const installDeps = installDepsCheckbox.checked;
                document.getElementById(`${prefix}-requirements-group`).style.display = 
                    (useShell && installDeps) ? 'block' : 'none';
            };
        }
    });
    
    // Accordion toggles
    document.querySelectorAll('#local-apps-container .accordion-header').forEach(header => {
        header.onclick = (e) => {
            if (e.target.tagName === 'BUTTON') return;
            
            const content = header.nextElementSibling;
            const toggle = header.querySelector('.accordion-toggle');
            const isOpen = content.classList.contains('active');
            
            content.classList.toggle('active');
            toggle.textContent = isOpen ? '▶' : '▼';
        };
    });
}

// Initialize on page load
document.addEventListener("DOMContentLoaded", () => {
    document.getElementById("save-config").addEventListener("click", saveConfig);
    document.getElementById("load-config").addEventListener("click", loadConfig);
    document.getElementById("add-local-app").addEventListener("click", addLocalApp);
    
    // Load config on startup
    loadConfig();
});
