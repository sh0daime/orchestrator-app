"""SSH client for remote Docker operations using paramiko"""
import json
import paramiko
import logging
from typing import List, Dict, Optional
from dataclasses import dataclass

logging.getLogger('paramiko').setLevel(logging.WARNING)

@dataclass
class ContainerStatus:
    """Docker container status"""
    name: str
    status: str
    state: str


class SSHClient:
    """SSH client for connecting to remote servers and executing commands"""
    
    def __init__(self, host: str, port: int, username: str, ssh_key_path: str, portal_path: str = ""):
        self.host = host
        self.port = port
        self.username = username
        self.ssh_key_path = ssh_key_path
        self.portal_path = portal_path  # Kept for backward compatibility
        self.client = None
    
    def connect(self) -> None:
        """Establish SSH connection"""
        try:
            self.client = paramiko.SSHClient()
            self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            # Check if key file exists
            import os
            if not os.path.exists(self.ssh_key_path):
                raise Exception(f"SSH key not found at path: {self.ssh_key_path}\nPlease check the file exists and the path is correct.")
            
            # Read key file to check format
            with open(self.ssh_key_path, 'r') as f:
                key_content = f.read()
            
            # Log key format (paramiko handles OpenSSH format natively!)
            if "BEGIN OPENSSH PRIVATE KEY" in key_content:
                print("Note: Detected OpenSSH format key (ED25519 supported by paramiko)")
            elif "BEGIN RSA PRIVATE KEY" in key_content or "BEGIN EC PRIVATE KEY" in key_content:
                print("Note: Detected PEM format key")
            
            # Connect using private key (paramiko supports OpenSSH format including ED25519)
            self.client.connect(
                hostname=self.host,
                port=self.port,
                username=self.username,
                key_filename=self.ssh_key_path,
                timeout=10,
                look_for_keys=False,  # Only use the specified key
                allow_agent=False
            )
            print(f"Successfully connected to {self.username}@{self.host}:{self.port}")
            
        except paramiko.AuthenticationException as e:
            raise Exception(f"SSH authentication failed: {e}\nUsername: {self.username}\nKey: {self.ssh_key_path}")
        except paramiko.SSHException as e:
            raise Exception(f"SSH connection failed: {e}")
        except Exception as e:
            raise Exception(f"Failed to connect to {self.host}:{self.port}: {e}")
    
    def execute_command(self, cmd: str) -> str:
        """Execute a command on the remote server"""
        if not self.client:
            raise Exception("Not connected to SSH server")
        
        try:
            stdin, stdout, stderr = self.client.exec_command(cmd, timeout=30)
            exit_status = stdout.channel.recv_exit_status()
            
            output = stdout.read().decode('utf-8')
            error = stderr.read().decode('utf-8')
            
            if exit_status != 0:
                raise Exception(f"Command failed with exit status {exit_status}: {error or output}")
            
            return output
        except Exception as e:
            raise Exception(f"Failed to execute command '{cmd}': {e}")
    
    def check_containers(self) -> List[ContainerStatus]:
        """Check Docker containers status (uses portal_path for backward compatibility)"""
        return self.check_containers_at_path(self.portal_path)
    
    def check_containers_at_path(self, path: str) -> List[ContainerStatus]:
        """Check Docker containers status at a specific path"""
        # First check if path exists
        try:
            check_dir_cmd = f"test -d {path} && echo 'dir_exists' || echo 'dir_not_found'"
            dir_check = self.execute_command(check_dir_cmd).strip()
            if dir_check != 'dir_exists':
                print(f"Error: Path does not exist: {path}")
                print(f"Please verify the path is correct in Settings.")
                return []
            
            # Check if docker-compose.yml exists
            check_compose_cmd = f"test -f {path}/docker-compose.yml && echo 'compose_yml' || (test -f {path}/docker-compose.yaml && echo 'compose_yaml' || echo 'no_compose')"
            compose_check = self.execute_command(check_compose_cmd).strip()
            if compose_check == 'no_compose':
                print(f"Warning: No docker-compose.yml or docker-compose.yaml found at {path}")
                print(f"Path exists but docker-compose file is missing. Listing directory contents:")
                try:
                    ls_cmd = f"ls -la {path} | head -20"
                    ls_output = self.execute_command(ls_cmd)
                    print(ls_output)
                except:
                    pass
                # Return empty list - service will show as not configured
                return []
        except Exception as e:
            print(f"Warning: Could not verify path {path}: {e}")
            # Continue anyway - docker compose will fail with a clearer error
        
        # Try to get containers
        try:
            cmd = f"cd {path} && docker compose ps --format json 2>&1"
            output = self.execute_command(cmd)
            
            containers = []
            for line in output.strip().split('\n'):
                if not line or line.strip() == '':
                    continue
                try:
                    container = json.loads(line)
                    containers.append(ContainerStatus(
                        name=container.get('Name', ''),
                        status=container.get('Status', ''),
                        state=container.get('State', '')
                    ))
                except json.JSONDecodeError:
                    # Skip non-JSON lines (like error messages)
                    continue
            
            return containers
        except Exception as e:
            error_msg = str(e)
            # Check if it's a "no configuration file" error
            if 'no configuration file' in error_msg.lower() or 'not found' in error_msg.lower():
                print(f"Error: No docker-compose.yml found at {path}")
                print(f"This usually means:")
                print(f"  1. The path '{path}' is incorrect")
                print(f"  2. The docker-compose.yml file doesn't exist at that location")
                print(f"  3. The file might be named differently (docker-compose.yaml)")
                print(f"Please check the path in Settings and ensure docker-compose.yml exists.")
                # Return empty list instead of failing - allows graceful handling
                return []
            # For other errors, re-raise
            raise
    
    def start_portal(self) -> None:
        """Start the portal Docker containers (deprecated, use start_service)"""
        self.start_service(self.portal_path, None)
    
    def stop_portal(self) -> None:
        """Stop the portal Docker containers (deprecated, use stop_service)"""
        self.stop_service(self.portal_path, None)
    
    def start_service(self, path: str, service_name: Optional[str] = None, pre_launch_command: Optional[str] = None) -> None:
        """Start a Docker service at a specific path"""
        # Run pre-launch command if specified (e.g., for setup, env file creation)
        if pre_launch_command:
            print(f"Running pre-launch command: {pre_launch_command}")
            pre_cmd = f"cd {path} && {pre_launch_command}"
            self.execute_command(pre_cmd)
        
        # Start the service
        if service_name:
            cmd = f"cd {path} && docker compose up -d {service_name}"
        else:
            cmd = f"cd {path} && docker compose up -d"
        self.execute_command(cmd)
    
    def stop_service(self, path: str, service_name: Optional[str] = None) -> None:
        """Stop a Docker service at a specific path"""
        if service_name:
            cmd = f"cd {path} && docker compose stop {service_name}"
        else:
            cmd = f"cd {path} && docker compose down"
        self.execute_command(cmd)
    
    def restart_container(self, path: str, container_name: str) -> None:
        """Restart a specific Docker container using docker restart (not docker compose)"""
        # Use 'docker restart' which takes container names, not 'docker compose restart' which takes service names
        cmd = f"docker restart {container_name}"
        self.execute_command(cmd)
    
    def get_logs(self, service: Optional[str] = None, lines: int = 100) -> str:
        """Get Docker container logs"""
        if service:
            cmd = f"cd {self.portal_path} && docker compose logs --tail {lines} {service}"
        else:
            cmd = f"cd {self.portal_path} && docker compose logs --tail {lines}"
        return self.execute_command(cmd)
    
    def check_portal_health(self, port: int) -> bool:
        """Check if the portal is responding (deprecated, use check_service_health)"""
        return self.check_service_health(port, "/")
    
    def check_service_health(self, port: int, path: str = "/") -> bool:
        """Check if a service is responding at a specific port and path"""
        cmd = f"curl -s -o /dev/null -w '%{{http_code}}' http://localhost:{port}{path} || echo '000'"
        try:
            output = self.execute_command(cmd)
            status_code = output.strip()
            return status_code == "200"
        except:
            return False
    
    def disconnect(self) -> None:
        """Close SSH connection"""
        if self.client:
            self.client.close()
            self.client = None
    
    def __enter__(self):
        """Context manager entry"""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.disconnect()

