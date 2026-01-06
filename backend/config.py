"""Configuration management for Orchestrator App"""
import json
import os
from dataclasses import dataclass, field, asdict
from typing import Optional, List, Dict, Any, Tuple
from pathlib import Path


@dataclass
class ServiceConfig:
    """Service configuration for a Docker service on a server"""
    id: str
    name: str
    container_name: str
    port: int
    path: str
    healthcheck_path: str = "/"
    pre_launch_command: Optional[str] = None  # Optional command to run before starting service


@dataclass
class ServerConfig:
    """Server configuration for SSH and Docker operations"""
    id: str
    name: str
    host: str
    port: int
    username: str
    ssh_key_path: str
    services: List[ServiceConfig] = field(default_factory=list)


@dataclass
class LocalAppConfig:
    """Local application configuration"""
    id: str
    name: str
    executable_path: str
    working_directory: Optional[str] = None
    use_shell: bool = False
    conda_env: Optional[str] = None
    shell_command: Optional[str] = None
    install_dependencies: bool = False  # Install dependencies before launch
    requirements_file: Optional[str] = None  # Path to requirements.txt


@dataclass
class Preferences:
    """User preferences"""
    auto_start_portal: bool = True
    minimize_to_tray: bool = True
    startup_launch: bool = False
    setup_completed: bool = False  # Flag to track if first-run setup wizard has been completed


@dataclass
class AppConfig:
    """Main application configuration"""
    version: str = "1.0"
    servers: List[ServerConfig] = field(default_factory=list)
    local_apps: List[LocalAppConfig] = field(default_factory=list)
    preferences: Preferences = field(default_factory=Preferences)

    @staticmethod
    def get_config_path() -> Path:
        """Get the config file path"""
        if os.name == 'nt':  # Windows
            config_dir = Path(os.getenv('APPDATA')) / 'orchestrator-app'
        else:  # Mac/Linux
            config_dir = Path.home() / '.config' / 'orchestrator-app'
        
        config_dir.mkdir(parents=True, exist_ok=True)
        return config_dir / 'config.json'

    @classmethod
    def load(cls) -> 'AppConfig':
        """Load configuration from file with automatic migration"""
        config_path = cls.get_config_path()
        
        if not config_path.exists():
            return cls(version="2.0")
        
        try:
            with open(config_path, 'r') as f:
                data = json.load(f)
            
            version = data.get('version', '1.0')
            
            # Migrate from v1.0 to v2.0
            if version == '1.0':
                print("Migrating config from v1.0 to v2.0...")
                data = cls._migrate_v1_to_v2(data)
                version = '2.0'
            
            # Convert dictionaries to dataclass instances
            servers = []
            for server_data in data.get('servers', []):
                services_data = server_data.get('services', [])
                services = [ServiceConfig(**s) for s in services_data]
                
                # Create ServerConfig without 'services' key first
                server_dict = {k: v for k, v in server_data.items() if k != 'services'}
                server = ServerConfig(**server_dict, services=services)
                servers.append(server)
            
            local_apps = [LocalAppConfig(**app) for app in data.get('local_apps', [])]
            preferences = Preferences(**data.get('preferences', {}))
            
            config = cls(
                version=version,
                servers=servers,
                local_apps=local_apps,
                preferences=preferences
            )
            
            # Auto-save migrated config
            if data.get('_migrated', False):
                print("Saving migrated config...")
                config.save()
            
            return config
            
        except Exception as e:
            print(f"Error loading config: {e}")
            import traceback
            traceback.print_exc()
            return cls(version="2.0")
    
    @staticmethod
    def _migrate_v1_to_v2(data: Dict[str, Any]) -> Dict[str, Any]:
        """Migrate config from v1.0 to v2.0 format"""
        migrated_servers = []
        
        for server in data.get('servers', []):
            # Check if old format (has portal_port and portal_path)
            if 'portal_port' in server and 'portal_path' in server:
                # Create a service from the old portal_port and portal_path
                service = {
                    'id': 'ai-portal',
                    'name': 'AI Portal',
                    'container_name': 'ai-portal',
                    'port': server['portal_port'],
                    'path': server['portal_path'],
                    'healthcheck_path': '/'
                }
                
                # Create new server without portal_port and portal_path
                new_server = {
                    'id': server['id'],
                    'name': server['name'],
                    'host': server['host'],
                    'port': server['port'],
                    'username': server['username'],
                    'ssh_key_path': server['ssh_key_path'],
                    'services': [service]
                }
                migrated_servers.append(new_server)
            else:
                # Already in new format
                migrated_servers.append(server)
        
        data['servers'] = migrated_servers
        data['version'] = '2.0'
        data['_migrated'] = True
        
        return data

    def save(self) -> None:
        """Save configuration to file"""
        config_path = self.get_config_path()
        
        try:
            # Convert dataclasses to dictionaries
            data = {
                'version': self.version,
                'servers': [asdict(s) for s in self.servers],
                'local_apps': [asdict(app) for app in self.local_apps],
                'preferences': asdict(self.preferences)
            }
            
            with open(config_path, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            raise Exception(f"Failed to save config: {e}")

    def get_server(self, server_id: str) -> Optional[ServerConfig]:
        """Get server by ID"""
        for server in self.servers:
            if server.id == server_id:
                return server
        return None
    
    def get_service(self, server_id: str, service_id: str) -> Optional[Tuple[ServerConfig, ServiceConfig]]:
        """Get service by server ID and service ID"""
        server = self.get_server(server_id)
        if not server:
            return None
        
        for service in server.services:
            if service.id == service_id:
                return (server, service)
        return None
    
    def add_service(self, server_id: str, service: ServiceConfig) -> bool:
        """Add a service to a server"""
        server = self.get_server(server_id)
        if not server:
            return False
        
        server.services.append(service)
        return True
    
    def remove_service(self, server_id: str, service_id: str) -> bool:
        """Remove a service from a server"""
        server = self.get_server(server_id)
        if not server:
            return False
        
        server.services = [s for s in server.services if s.id != service_id]
        return True

    def get_local_app(self, app_id: str) -> Optional[LocalAppConfig]:
        """Get local app by ID"""
        for app in self.local_apps:
            if app.id == app_id:
                return app
        return None
    
    def is_first_run(self) -> bool:
        """Check if this is a first-run (setup wizard not completed)"""
        return not self.preferences.setup_completed and len(self.servers) == 0

