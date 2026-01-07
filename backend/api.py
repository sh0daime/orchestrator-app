"""API functions exposed to the frontend (equivalent to Tauri commands)"""
import time
import threading
from typing import Dict, List, Any, Tuple, Callable, Optional
from dataclasses import asdict
from config import AppConfig, ServerConfig, LocalAppConfig, ServiceConfig
from ssh_client import SSHClient, ContainerStatus
from process_manager import get_process_manager
from vctt_interface import VCTTInterface


class API:
    """API class containing all command functions"""
    
    def __init__(self):
        self.process_manager = get_process_manager()
        self._window_creator = None  # Callback to create windows
    
    def set_window_creator(self, creator_func: Callable[[str], None]):
        """Set a callback function to create windows (called from OrchestratorApp)"""
        self._window_creator = creator_func
    
    def launch_portal(self, server_id: str) -> str:
        """Launch the portal on the remote server (backward compatible - launches first service)"""
        try:
            config = AppConfig.load()
            server = config.get_server(server_id)
            
            if not server:
                raise Exception(f"Server not found: {server_id}")
            
            # For backward compatibility, launch the first service
            if not server.services:
                raise Exception(f"No services configured for server: {server_id}")
            
            first_service = server.services[0]
            return self.launch_service(server_id, first_service.id)
                
        except Exception as e:
            raise Exception(f"Failed to launch portal: {e}")
    
    def launch_service(self, server_id: str, service_id: str) -> str:
        """Launch a specific service on a remote server"""
        try:
            print(f"Loading config for server_id: {server_id}, service_id: {service_id}")
            config = AppConfig.load()
            result = config.get_service(server_id, service_id)
            
            if not result:
                raise Exception(f"Service not found: {service_id} on server: {server_id}")
            
            server, service = result
            
            print(f"Connecting to SSH server: {server.host}:{server.port}")
            # Connect to SSH
            with SSHClient(
                host=server.host,
                port=server.port,
                username=server.username,
                ssh_key_path=server.ssh_key_path
            ) as ssh:
                print(f"Checking containers at: {service.path}")
                # Check current status
                containers = ssh.check_containers_at_path(service.path)
                print(f"Found {len(containers)} containers")
                service_running = any(
                    c.name == service.container_name and c.state == "running" 
                    for c in containers
                )
                print(f"Service {service.name} running: {service_running}")
                
                # Start if not running
                if not service_running:
                    print(f"Starting service {service.name}...")
                    # Pass pre-launch command if specified
                    ssh.start_service(service.path, None, service.pre_launch_command)
                    print("Service start command sent")
                    
                    # Wait for service to be ready (with timeout)
                    max_wait = 120  # 2 minutes
                    waited = 0
                    ready = False
                    
                    while waited < max_wait:
                        time.sleep(2)
                        waited += 2
                        
                        if ssh.check_service_health(service.port, service.healthcheck_path):
                            ready = True
                            break
                    
                    if not ready:
                        # Service started but health check didn't pass
                        # This might be OK if the service doesn't have an HTTP endpoint
                        print(f"Warning: Service started but health check didn't return 200 within {max_wait}s")
                        print(f"Health check URL: http://localhost:{service.port}{service.healthcheck_path}")
                        print("This is normal if the service doesn't have an HTTP endpoint or uses a different health check path")
                
                service_url = f"http://{server.host}:{service.port}"
                return service_url
                
        except Exception as e:
            raise Exception(f"Failed to launch service: {e}")
    
    def stop_service(self, server_id: str, service_id: str) -> None:
        """Stop a specific service on a remote server"""
        try:
            print(f"Stopping service: {service_id} on server: {server_id}")
            config = AppConfig.load()
            result = config.get_service(server_id, service_id)
            
            if not result:
                raise Exception(f"Service not found: {service_id} on server: {server_id}")
            
            server, service = result
            
            with SSHClient(
                host=server.host,
                port=server.port,
                username=server.username,
                ssh_key_path=server.ssh_key_path
            ) as ssh:
                print(f"Stopping service at: {service.path}")
                ssh.stop_service(service.path, None)
                print(f"Service {service.name} stopped")
                
        except Exception as e:
            raise Exception(f"Failed to stop service: {e}")
    
    def launch_local_app(self, app_id: str) -> None:
        """Launch a local application"""
        try:
            config = AppConfig.load()
            app = config.get_local_app(app_id)
            
            if not app:
                raise Exception(f"App not found: {app_id}")
            
            self.process_manager.launch_app(app)
            
        except Exception as e:
            raise Exception(f"Failed to launch app: {e}")
    
    def get_status(self, server_id: str) -> Dict[str, Any]:
        """Get status of the remote server and all its services"""
        try:
            config = AppConfig.load()
            server = config.get_server(server_id)
            
            if not server:
                raise Exception(f"Server not found: {server_id}")
            
            try:
                with SSHClient(
                    host=server.host,
                    port=server.port,
                    username=server.username,
                    ssh_key_path=server.ssh_key_path
                ) as ssh:
                    # Get status for each service
                    services_status = []
                    for service in server.services:
                        try:
                            containers = ssh.check_containers_at_path(service.path)
                        except Exception as e:
                            print(f"Error checking containers at {service.path}: {e}")
                            # Continue with empty containers list
                            containers = []
                        service_ready = ssh.check_service_health(service.port, service.healthcheck_path)
                        
                        # Debug logging
                        print(f"\n=== Service: {service.name} ===")
                        print(f"Configured container name: '{service.container_name}'")
                        print(f"Containers found: {[c.name for c in containers]}")
                        
                        # Check if ANY container from this compose file is running
                        service_running = any(c.state == "running" for c in containers)
                        
                        # Flexible container name matching:
                        # 1. Exact match: "pipeline-management-tool" == "pipeline-management-tool"
                        # 2. Partial match (both directions):
                        #    - "pipeline-tool" in "data-pipeline-tool-1"
                        #    - "data-pipeline-tool-1" contains "pipeline-tool"
                        # 3. Normalized match: remove hyphens and compare
                        main_container_running = False
                        matched_container = None
                        
                        for c in containers:
                            if c.state != "running":
                                continue
                            
                            # Try multiple matching strategies
                            config_name_lower = service.container_name.lower()
                            container_name_lower = c.name.lower()
                            
                            # Strategy 1: Exact match
                            if config_name_lower == container_name_lower:
                                main_container_running = True
                                matched_container = c.name
                                print(f"✓ Matched (exact): {c.name}")
                                break
                            
                            # Strategy 2: Partial match (bidirectional)
                            if config_name_lower in container_name_lower or container_name_lower in config_name_lower:
                                main_container_running = True
                                matched_container = c.name
                                print(f"✓ Matched (partial): {c.name}")
                                break
                            
                            # Strategy 3: Normalized match (remove special chars)
                            import re
                            config_normalized = re.sub(r'[^a-z0-9]', '', config_name_lower)
                            container_normalized = re.sub(r'[^a-z0-9]', '', container_name_lower)
                            
                            if config_normalized in container_normalized or container_normalized in config_normalized:
                                main_container_running = True
                                matched_container = c.name
                                print(f"✓ Matched (normalized): {c.name}")
                                break
                        
                        if not main_container_running and service_running:
                            print(f"⚠ No container matched '{service.container_name}', but containers are running")
                            print(f"  Tip: Set container name to match one of: {[c.name for c in containers if c.state == 'running']}")
                        
                        # If ANY container is running from this compose file, consider it running
                        # This handles cases where the name doesn't match but service is actually up
                        if not main_container_running and service_running:
                            main_container_running = True
                            print(f"✓ Using fallback: Any container running = service running")
                        
                        services_status.append({
                            'id': service.id,
                            'name': service.name,
                            'url': f"http://{server.host}:{service.port}",
                            'ready': service_ready,
                            'running': main_container_running,
                            'has_containers': service_running,
                            'containers': [asdict(c) for c in containers],
                            'container_count': len(containers),
                            'matched_container': matched_container  # For debugging
                        })
                    
                    return {
                        'server_id': server_id,
                        'server_name': server.name,
                        'connected': True,
                        'services': services_status
                    }
            except Exception as e:
                print(f"Error getting status for {server_id}: {e}")
                return {
                    'server_id': server_id,
                    'server_name': server.name,
                    'connected': False,
                    'services': []
                }
                
        except Exception as e:
            raise Exception(f"Failed to get status: {e}")
    
    def get_all_status(self) -> List[Dict[str, Any]]:
        """Get status for all servers and their services"""
        try:
            config = AppConfig.load()
            all_status = []
            
            for server in config.servers:
                status = self.get_status(server.id)
                all_status.append(status)
            
            return all_status
            
        except Exception as e:
            raise Exception(f"Failed to get all status: {e}")
    
    def validate_server_config(self, servers: List[Dict[str, Any]]) -> Tuple[bool, str]:
        """
        Validate server configuration for duplicates and other issues.
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not servers:
            return True, ""  # Empty is OK
        
        # Check for duplicate server names
        server_names = {}
        for idx, server in enumerate(servers):
            name = server.get('name', '').strip()
            if not name:
                return False, f"Server {idx + 1} has an empty name. Server names are required."
            
            if name in server_names:
                return False, f"Duplicate server name '{name}'. Server names must be unique."
            server_names[name] = idx
        
        # Check for duplicate server IPs (host:port combination)
        server_hosts = {}
        for idx, server in enumerate(servers):
            host = server.get('host', '').strip()
            port = server.get('port', 22)
            
            if not host:
                return False, f"Server '{server.get('name', f'Server {idx + 1}')}' has an empty host/IP address."
            
            # Validate IP/hostname format (basic check)
            if not self._is_valid_host(host):
                return False, f"Server '{server.get('name', f'Server {idx + 1}')}' has an invalid host/IP address: '{host}'"
            
            # Validate port range
            if not (1 <= port <= 65535):
                return False, f"Server '{server.get('name', f'Server {idx + 1}')}' has an invalid port: {port}. Port must be between 1 and 65535."
            
            host_key = f"{host}:{port}"
            if host_key in server_hosts:
                other_name = servers[server_hosts[host_key]].get('name', f'Server {server_hosts[host_key] + 1}')
                return False, f"Duplicate server IP/Port '{host_key}'. Server '{server.get('name', f'Server {idx + 1}')}' conflicts with '{other_name}'."
            server_hosts[host_key] = idx
            
            # Validate required fields
            if not server.get('username', '').strip():
                return False, f"Server '{server.get('name', f'Server {idx + 1}')}' is missing a username."
            
            if not server.get('ssh_key_path', '').strip():
                return False, f"Server '{server.get('name', f'Server {idx + 1}')}' is missing an SSH key path."
        
        return True, ""
    
    def _is_valid_host(self, host: str) -> bool:
        """Validate host/IP address format"""
        import re
        host = host.strip()
        
        # IPv4 pattern
        ipv4_pattern = r'^(\d{1,3}\.){3}\d{1,3}$'
        if re.match(ipv4_pattern, host):
            parts = host.split('.')
            return all(0 <= int(part) <= 255 for part in parts)
        
        # IPv6 pattern (basic check)
        if ':' in host:
            # Basic IPv6 validation
            return len(host) <= 45  # Max IPv6 length
        
        # Hostname pattern (letters, numbers, dots, hyphens)
        hostname_pattern = r'^[a-zA-Z0-9]([a-zA-Z0-9\-\.]*[a-zA-Z0-9])?$'
        if re.match(hostname_pattern, host):
            return len(host) <= 253  # Max hostname length
        
        return False
    
    def save_config(self, config_dict: Dict[str, Any]) -> None:
        """Save configuration with validation"""
        try:
            servers_data = config_dict.get('servers', [])
            
            # Validate servers before saving
            is_valid, error_msg = self.validate_server_config(servers_data)
            if not is_valid:
                raise Exception(f"Configuration validation failed: {error_msg}")
            
            # Convert dictionary to AppConfig
            servers = [ServerConfig(**s) for s in servers_data]
            local_apps = [LocalAppConfig(**app) for app in config_dict.get('local_apps', [])]
            
            config = AppConfig(
                version=config_dict.get('version', '1.0'),
                servers=servers,
                local_apps=local_apps
            )
            
            config.save()
            
        except Exception as e:
            raise Exception(f"Failed to save config: {e}")
    
    def load_config(self) -> Dict[str, Any]:
        """Load configuration"""
        try:
            config = AppConfig.load()
            
            return {
                'version': config.version,
                'servers': [asdict(s) for s in config.servers],
                'local_apps': [asdict(app) for app in config.local_apps],
                'preferences': asdict(config.preferences)
            }
            
        except Exception as e:
            raise Exception(f"Failed to load config: {e}")
    
    def test_connection(self, server_dict: Dict[str, Any]) -> str:
        """Test SSH connection to a server"""
        try:
            print(f"Starting SSH connection test to {server_dict['username']}@{server_dict['host']}:{server_dict['port']}")
            print(f"Using SSH key: {server_dict['ssh_key_path']}")
            
            with SSHClient(
                host=server_dict['host'],
                port=server_dict['port'],
                username=server_dict['username'],
                ssh_key_path=server_dict['ssh_key_path']
            ) as ssh:
                print("SSH connection established successfully!")
                
                # Test by running a simple command
                output = ssh.execute_command("echo 'Connection successful'")
                print(f"Command executed successfully: {output}")
                
                return output
                
        except Exception as e:
            print(f"Connection error: {e}")
            raise Exception(f"Connection failed: {e}")
    
    def is_app_running(self, app_id: str) -> bool:
        """Check if an app is currently running"""
        is_running = self.process_manager.is_running(app_id)
        print(f"[API] Checking if app {app_id} is running: {is_running}")
        return is_running
    
    def terminate_app(self, app_id: str) -> None:
        """Terminate a running app"""
        try:
            self.process_manager.terminate(app_id)
        except Exception as e:
            raise Exception(f"Failed to terminate app: {e}")
    
    def restart_container(self, server_id: str, service_id: str, container_name: str) -> None:
        """Restart a specific container within a service"""
        try:
            print(f"Restarting container: {container_name} in service: {service_id} on server: {server_id}")
            config = AppConfig.load()
            result = config.get_service(server_id, service_id)
            
            if not result:
                raise Exception(f"Service not found: {service_id} on server: {server_id}")
            
            server, service = result
            
            with SSHClient(
                host=server.host,
                port=server.port,
                username=server.username,
                ssh_key_path=server.ssh_key_path
            ) as ssh:
                print(f"Restarting container at: {service.path}")
                ssh.restart_container(service.path, container_name)
                print(f"Container {container_name} restarted")
                
        except Exception as e:
            raise Exception(f"Failed to restart container: {e}")
    
    def get_container_logs(self, server_id: str, service_id: str, container_name: str, lines: int = 200) -> str:
        """Get logs for a specific container"""
        try:
            print(f"Fetching logs for container: {container_name} in service: {service_id} on server: {server_id}")
            config = AppConfig.load()
            result = config.get_service(server_id, service_id)
            
            if not result:
                return f"Error: Service not found: {service_id} on server: {server_id}"
            
            server, service = result
            
            # Limit lines to reasonable range
            lines = max(1, min(1000, int(lines)))
            
            try:
                with SSHClient(
                    host=server.host,
                    port=server.port,
                    username=server.username,
                    ssh_key_path=server.ssh_key_path
                ) as ssh:
                    # Use 2>&1 to capture both stdout and stderr (many apps log to stderr)
                    cmd = f"docker logs --tail {lines} --timestamps {container_name} 2>&1"
                    output = ssh.execute_command(cmd)
                    return output if output else "(no logs)"
            except Exception as ssh_error:
                return f"Error connecting to server: {ssh_error}"
                
        except Exception as e:
            return f"Error fetching logs: {e}"
    
    def get_container_logs_since(self, server_id: str, service_id: str, container_name: str, since_timestamp: str) -> str:
        """Get logs for a container since a specific timestamp"""
        try:
            print(f"Fetching incremental logs for container: {container_name} since: {since_timestamp}")
            config = AppConfig.load()
            result = config.get_service(server_id, service_id)
            
            if not result:
                return f"Error: Service not found: {service_id} on server: {server_id}"
            
            server, service = result
            
            try:
                with SSHClient(
                    host=server.host,
                    port=server.port,
                    username=server.username,
                    ssh_key_path=server.ssh_key_path
                ) as ssh:
                    # Docker accepts ISO 8601 timestamps or relative time (e.g., "2s")
                    # Use 2>&1 to capture both stdout and stderr (many apps log to stderr)
                    cmd = f"docker logs --since {since_timestamp} --timestamps {container_name} 2>&1"
                    output = ssh.execute_command(cmd)
                    return output if output else ""
            except Exception as ssh_error:
                return f"Error connecting to server: {ssh_error}"
                
        except Exception as e:
            return f"Error fetching logs: {e}"
    
    def open_settings_window(self) -> None:
        """Open the Settings window"""
        if self._window_creator:
            # Create window in a separate thread to avoid blocking
            threading.Thread(target=lambda: self._window_creator('settings'), daemon=True).start()
        else:
            raise Exception("Window creator not initialized")
    
    def open_status_window(self) -> None:
        """Open the Status window"""
        if self._window_creator:
            # Create window in a separate thread to avoid blocking
            threading.Thread(target=lambda: self._window_creator('status'), daemon=True).start()
        else:
            raise Exception("Window creator not initialized")
    
    def mark_setup_completed(self) -> None:
        """Mark the setup wizard as completed"""
        try:
            config = AppConfig.load()
            config.preferences.setup_completed = True
            config.save()
            print("Setup wizard marked as completed")
        except Exception as e:
            raise Exception(f"Failed to mark setup as completed: {e}")
    
    def get_vctt_status(self) -> Dict[str, Any]:
        """
        Get VCTT installation and configuration status.
        Only checks local_apps config - no file system scanning.
        """
        try:
            print("[VCTT] Checking status from config...")
            config = AppConfig.load()
            
            # Look for VCTT in local_apps
            vctt_app = None
            for app in config.local_apps:
                if 'VCTT' in app.name or 'vctt' in app.name.lower() or app.id.startswith('vctt'):
                    vctt_app = app
                    break
            
            if vctt_app:
                # Validate the path exists
                from pathlib import Path
                work_dir = Path(vctt_app.working_directory)
                main_py = work_dir / "main.py"
                
                if work_dir.exists() and main_py.exists():
                    return {
                        "installed": True,
                        "configured": True,
                        "app_id": vctt_app.id,
                        "path": str(work_dir),
                        "valid_path": True,
                        "error": None
                    }
                else:
                    return {
                        "installed": False,
                        "configured": True,  # Configured but path invalid
                        "app_id": vctt_app.id,
                        "path": str(work_dir),
                        "valid_path": False,
                        "error": f"VCTT path does not exist or is invalid: {work_dir}"
                    }
            else:
                # Not configured
                return {
                    "installed": False,
                    "configured": False,
                    "valid_path": False,
                    "error": None
                }
        except Exception as e:
            print(f"[VCTT] Error getting status: {e}")
            import traceback
            traceback.print_exc()
            return {
                "installed": False,
                "configured": False,
                "valid_path": False,
                "error": str(e)
            }
    
    def run_vctt_bootstrap(self, install_dir: str) -> Dict[str, Any]:
        """
        Run VCTT bootstrap installer.
        
        Args:
            install_dir: Directory where VCTT should be installed
            
        Returns:
            Dictionary with success status and message
        """
        try:
            interface = VCTTInterface()
            # Note: bootstrap is interactive, so wait=False starts it but doesn't wait for completion
            # The installer window will guide the user through the process
            exit_code, message = interface.run_bootstrap(install_dir, wait=False)
            
            return {
                "success": True,  # Success means installer started, not that installation completed
                "exit_code": exit_code,
                "message": message or "Bootstrap installer started. Please follow the prompts in the installer window."
            }
        except Exception as e:
            return {
                "success": False,
                "exit_code": 1,
                "message": f"Failed to run bootstrap: {e}"
            }
    
    def is_vctt_bootstrap_running(self, install_dir: str) -> bool:
        """
        Check if VCTT bootstrap installation is still running.
        
        Args:
            install_dir: Installation directory used to identify the process
            
        Returns:
            True if bootstrap is still running, False otherwise
        """
        return VCTTInterface.is_bootstrap_running(install_dir)
    
    def configure_vctt_app(self, vctt_path: str, conda_env: str = "vtcc_test") -> str:
        """
        Automatically configure VCTT in local_apps after installation.
        
        Args:
            vctt_path: Path to VCTT installation directory (can be parent or VCTT_app)
            conda_env: Conda environment name (default: vtcc_test)
            
        Returns:
            App ID of the configured app
        """
        try:
            import time
            from pathlib import Path
            
            config = AppConfig.load()
            base_path = Path(vctt_path)
            
            # Determine the actual VCTT_app directory
            # Check if vctt_path is VCTT_app itself
            if (base_path / "main.py").exists():
                vctt_app_dir = base_path
            # Check if vctt_path/VCTT_app exists
            elif (base_path / "VCTT_app" / "main.py").exists():
                vctt_app_dir = base_path / "VCTT_app"
            else:
                # Try to find VCTT installations
                found = VCTTInterface.find_vctt_installations()
                if found:
                    vctt_app_dir = found[0]
                    print(f"Found VCTT installation at: {vctt_app_dir}")
                else:
                    raise Exception(f"VCTT installation not found at {vctt_path}. Please ensure VCTT is installed.")
            
            # Validate it's a real VCTT installation
            main_py = vctt_app_dir / "main.py"
            if not main_py.exists():
                raise Exception(f"main.py not found in {vctt_app_dir}. This doesn't appear to be a valid VCTT installation.")
            
            # Check for launch script - prefer using launch script over python main.py
            launch_bat = vctt_app_dir / "launch_vctt.bat"
            launch_sh = vctt_app_dir / "launch_vctt.sh"
            
            # Determine which launch method to use
            use_launch_script = False
            if launch_bat.exists():
                executable = str(launch_bat)
                use_launch_script = True
            elif launch_sh.exists():
                executable = str(launch_sh)
                use_launch_script = True
            else:
                # Fallback to python main.py if launch script doesn't exist
                executable = str(main_py)
                print(f"Warning: Launch script not found, using python main.py directly")
            
            # Check if VCTT is already configured
            for app in config.local_apps:
                if 'VCTT' in app.name or 'vctt' in app.name.lower():
                    # Update existing config with validated path
                    app.executable_path = executable
                    app.working_directory = str(vctt_app_dir)
                    if use_launch_script:
                        # Use launch script directly (it handles conda internally)
                        app.use_shell = True
                        app.conda_env = None  # Launch script handles conda
                        app.shell_command = None
                    else:
                        # Fallback: use shell with conda
                        app.use_shell = True
                        app.conda_env = conda_env
                        app.shell_command = None
                    config.save()
                    print(f"Updated VCTT configuration: {app.id} (using {'launch script' if use_launch_script else 'python main.py'})")
                    return app.id
            
            # Create new VCTT app config
            app_id = f"vctt-{int(time.time())}"
            if use_launch_script:
                # Use launch script directly (it handles conda internally)
                vctt_app = LocalAppConfig(
                    id=app_id,
                    name="VCTT App",
                    executable_path=executable,
                    working_directory=str(vctt_app_dir),
                    use_shell=True,
                    conda_env=None,  # Launch script handles conda
                    shell_command=None,
                    install_dependencies=False,
                    requirements_file=None
                )
            else:
                # Fallback: use shell with conda
                vctt_app = LocalAppConfig(
                    id=app_id,
                    name="VCTT App",
                    executable_path=executable,
                    working_directory=str(vctt_app_dir),
                    use_shell=True,
                    conda_env=conda_env,
                    shell_command=None,
                    install_dependencies=False,
                    requirements_file=None
                )
            
            config.local_apps.append(vctt_app)
            config.save()
            
            print(f"VCTT configured as local app: {app_id} at {vctt_app_dir}")
            return app_id
            
        except Exception as e:
            raise Exception(f"Failed to configure VCTT app: {e}")


    def browse_folder(self, title: str = "Select Folder") -> Optional[str]:
        """
        Open a folder picker dialog.
        
        Args:
            title: Dialog title
            
        Returns:
            Selected folder path or None if cancelled
        """
        try:
            import tkinter as tk
            from tkinter import filedialog
            
            # Create a hidden root window
            root = tk.Tk()
            root.withdraw()  # Hide the main window
            root.attributes('-topmost', True)  # Bring to front
            
            # Open folder dialog
            folder_path = filedialog.askdirectory(
                title=title,
                initialdir='~'
            )
            
            root.destroy()
            
            if folder_path:
                return folder_path
            return None
        except Exception as e:
            print(f"Error opening folder dialog: {e}")
            import traceback
            traceback.print_exc()
            return None


# Global API instance
_api = API()


def get_api() -> API:
    """Get the global API instance"""
    return _api

