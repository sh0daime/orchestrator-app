"""Diagnostic tool to check container name matching"""
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / 'backend'))

from config import AppConfig
from ssh_client import SSHClient

def diagnose_server(server_id):
    """Diagnose container detection for a specific server"""
    print(f"\n{'='*70}")
    print(f"DIAGNOSING SERVER: {server_id}")
    print(f"{'='*70}\n")
    
    config = AppConfig.load()
    server = config.get_server(server_id)
    
    if not server:
        print(f"❌ Server '{server_id}' not found in config")
        print(f"Available servers: {[s.id for s in config.servers]}")
        return
    
    print(f"Server: {server.name}")
    print(f"Host: {server.host}")
    print(f"Services configured: {len(server.services)}\n")
    
    try:
        with SSHClient(
            host=server.host,
            port=server.port,
            username=server.username,
            ssh_key_path=server.ssh_key_path
        ) as ssh:
            print(f"✓ SSH connection successful\n")
            
            for i, service in enumerate(server.services, 1):
                print(f"\n--- Service {i}/{len(server.services)}: {service.name} ---")
                print(f"  Configured container name: '{service.container_name}'")
                print(f"  Path: {service.path}")
                print(f"  Port: {service.port}")
                print(f"  Health check: {service.healthcheck_path}")
                
                try:
                    containers = ssh.check_containers_at_path(service.path)
                    print(f"\n  Containers found: {len(containers)}")
                    
                    if containers:
                        for c in containers:
                            status_icon = "🟢" if c.state == "running" else "🔴"
                            print(f"    {status_icon} {c.name}")
                            print(f"       Status: {c.status}")
                            print(f"       State: {c.state}")
                            
                            # Check matching
                            config_lower = service.container_name.lower()
                            container_lower = c.name.lower()
                            
                            matches = []
                            if config_lower == container_lower:
                                matches.append("exact match")
                            if config_lower in container_lower:
                                matches.append("config in container")
                            if container_lower in config_lower:
                                matches.append("container in config")
                            
                            if matches:
                                print(f"       ✓ Matches: {', '.join(matches)}")
                            else:
                                print(f"       ✗ No match with '{service.container_name}'")
                    else:
                        print(f"    ⚠ No containers found at this path")
                        print(f"    Check if docker-compose.yml exists at: {service.path}")
                    
                    # Check health
                    print(f"\n  Health check:")
                    try:
                        healthy = ssh.check_service_health(service.port, service.healthcheck_path)
                        if healthy:
                            print(f"    ✓ Service is healthy (HTTP 200)")
                        else:
                            print(f"    ✗ Health check failed")
                            print(f"    URL: http://localhost:{service.port}{service.healthcheck_path}")
                            print(f"    (This is normal for non-HTTP services)")
                    except Exception as e:
                        print(f"    ✗ Health check error: {e}")
                    
                except Exception as e:
                    print(f"  ❌ Error checking containers: {e}")
                    import traceback
                    traceback.print_exc()
            
    except Exception as e:
        print(f"❌ SSH connection failed: {e}")
        import traceback
        traceback.print_exc()

def main():
    """Main diagnostic function"""
    print("\n" + "="*70)
    print("CONTAINER NAME DIAGNOSTIC TOOL")
    print("="*70)
    
    config = AppConfig.load()
    
    if not config.servers:
        print("\n❌ No servers configured")
        return
    
    print(f"\nAvailable servers:")
    for i, server in enumerate(config.servers, 1):
        print(f"  {i}. {server.id} ({server.name}) - {server.host}")
    
    if len(sys.argv) > 1:
        # Server ID provided as argument
        server_id = sys.argv[1]
        diagnose_server(server_id)
    else:
        # Diagnose all servers
        for server in config.servers:
            diagnose_server(server.id)
    
    print("\n" + "="*70)
    print("RECOMMENDATIONS")
    print("="*70)
    print("""
1. If containers show up but don't match:
   - Copy the actual container name from the output above
   - Paste it into Settings → Container Name field
   
2. If "No containers found":
   - Verify the Path in Settings points to docker-compose.yml location
   - SSH into server and run: cd <path> && docker compose ps
   
3. If health check fails but container runs:
   - This is normal for non-HTTP services (databases, workers)
   - Service will still be manageable, just won't show "Ready"
   
4. For restart issues:
   - The restart now uses container name directly
   - Make sure the container name matches exactly what docker ps shows
""")

if __name__ == "__main__":
    main()

