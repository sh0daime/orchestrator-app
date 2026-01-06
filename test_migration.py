"""Test script for config migration and multi-service functionality"""
import sys
import os
import json
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / 'backend'))

from config import AppConfig, ServerConfig, ServiceConfig

def test_migration():
    """Test v1.0 to v2.0 config migration"""
    print("=" * 60)
    print("Testing Config Migration (v1.0 -> v2.0)")
    print("=" * 60)
    
    # Create a v1.0 config
    old_config = {
        "version": "1.0",
        "servers": [
            {
                "id": "server1",
                "name": "Main Server",
                "host": "192.168.50.101",
                "port": 22,
                "username": "calvin",
                "ssh_key_path": "/path/to/key",
                "portal_port": 8080,
                "portal_path": "/home/calvin/ai-portal"
            }
        ],
        "local_apps": [],
        "preferences": {
            "auto_start_portal": True,
            "minimize_to_tray": True,
            "startup_launch": False
        }
    }
    
    print("\n[OK] Created v1.0 config:")
    print(json.dumps(old_config, indent=2))
    
    # Migrate
    print("\n[MIGRATING] to v2.0...")
    migrated = AppConfig._migrate_v1_to_v2(old_config.copy())
    
    print("\n[OK] Migrated config:")
    print(json.dumps(migrated, indent=2))
    
    # Verify migration
    assert migrated['version'] == '2.0', "Version should be 2.0"
    assert 'services' in migrated['servers'][0], "Server should have services"
    assert len(migrated['servers'][0]['services']) == 1, "Should have 1 service"
    
    service = migrated['servers'][0]['services'][0]
    assert service['id'] == 'ai-portal', "Service ID should be ai-portal"
    assert service['port'] == 8080, "Service port should be 8080"
    assert service['path'] == '/home/calvin/ai-portal', "Service path should match portal_path"
    
    assert 'portal_port' not in migrated['servers'][0], "portal_port should be removed"
    assert 'portal_path' not in migrated['servers'][0], "portal_path should be removed"
    
    print("\n[PASS] Migration verification passed!")
    return True

def test_multi_service():
    """Test multi-service configuration"""
    print("\n" + "=" * 60)
    print("Testing Multi-Service Configuration")
    print("=" * 60)
    
    # Create a multi-service config
    config = AppConfig(version="2.0")
    
    # Add server with multiple services
    server = ServerConfig(
        id="multi-server",
        name="Multi-Service Server",
        host="192.168.50.101",
        port=22,
        username="calvin",
        ssh_key_path="/path/to/key",
        services=[
            ServiceConfig(
                id="ai-portal",
                name="AI Portal",
                container_name="ai-portal",
                port=8080,
                path="/home/calvin/ai-portal",
                healthcheck_path="/"
            ),
            ServiceConfig(
                id="gradio-pipeline",
                name="Gradio Pipeline",
                container_name="gradio-app",
                port=7860,
                path="/home/calvin/gradio-app",
                healthcheck_path="/api/status"
            )
        ]
    )
    
    config.servers.append(server)
    
    print("\n[OK] Created multi-service config:")
    print(f"  Server: {server.name}")
    print(f"  Services: {len(server.services)}")
    for service in server.services:
        print(f"    - {service.name} (port {service.port})")
    
    # Test get_service
    result = config.get_service("multi-server", "ai-portal")
    assert result is not None, "Should find ai-portal service"
    found_server, found_service = result
    assert found_service.name == "AI Portal", "Should find correct service"
    print("\n[PASS] get_service() works correctly")
    
    # Test add_service
    new_service = ServiceConfig(
        id="monitoring",
        name="Monitoring Dashboard",
        container_name="monitoring",
        port=3000,
        path="/home/calvin/monitoring",
        healthcheck_path="/health"
    )
    config.add_service("multi-server", new_service)
    assert len(server.services) == 3, "Should have 3 services after adding"
    print("[PASS] add_service() works correctly")
    
    # Test remove_service
    config.remove_service("multi-server", "monitoring")
    assert len(server.services) == 2, "Should have 2 services after removing"
    print("[PASS] remove_service() works correctly")
    
    return True

def test_save_load():
    """Test saving and loading multi-service config"""
    print("\n" + "=" * 60)
    print("Testing Save/Load with Multi-Service Config")
    print("=" * 60)
    
    # Create config with multiple servers and services
    config = AppConfig(version="2.0")
    
    # Server 1
    server1 = ServerConfig(
        id="server1",
        name="Main Server",
        host="192.168.50.101",
        port=22,
        username="calvin",
        ssh_key_path="/path/to/key1",
        services=[
            ServiceConfig(
                id="portal",
                name="Portal",
                container_name="portal",
                port=8080,
                path="/home/calvin/portal",
                healthcheck_path="/"
            )
        ]
    )
    
    # Server 2
    server2 = ServerConfig(
        id="server2",
        name="Secondary Server",
        host="192.168.50.102",
        port=22,
        username="user",
        ssh_key_path="/path/to/key2",
        services=[
            ServiceConfig(
                id="app1",
                name="App 1",
                container_name="app1",
                port=3000,
                path="/home/user/app1",
                healthcheck_path="/"
            ),
            ServiceConfig(
                id="app2",
                name="App 2",
                container_name="app2",
                port=3001,
                path="/home/user/app2",
                healthcheck_path="/health"
            )
        ]
    )
    
    config.servers = [server1, server2]
    
    print("\n[OK] Created config with:")
    print(f"  - {len(config.servers)} servers")
    print(f"  - Server 1: {len(server1.services)} service(s)")
    print(f"  - Server 2: {len(server2.services)} service(s)")
    
    # Save
    print("\n[SAVING] config...")
    config.save()
    print(f"[OK] Config saved to: {AppConfig.get_config_path()}")
    
    # Load
    print("\n[LOADING] config...")
    loaded_config = AppConfig.load()
    
    print("[OK] Config loaded successfully")
    print(f"  Version: {loaded_config.version}")
    print(f"  Servers: {len(loaded_config.servers)}")
    
    # Verify
    assert loaded_config.version == "2.0", "Version should be 2.0"
    assert len(loaded_config.servers) == 2, "Should have 2 servers"
    assert len(loaded_config.servers[0].services) == 1, "Server 1 should have 1 service"
    assert len(loaded_config.servers[1].services) == 2, "Server 2 should have 2 services"
    
    print("[PASS] Verification passed!")
    
    # Show saved JSON
    with open(AppConfig.get_config_path(), 'r') as f:
        saved_json = json.load(f)
    
    print("\n[OK] Saved JSON structure:")
    print(json.dumps(saved_json, indent=2))
    
    return True

def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("CONFIG MIGRATION & MULTI-SERVICE TESTS")
    print("=" * 60)
    
    try:
        # Test 1: Migration
        if not test_migration():
            print("\n[FAIL] Migration test failed!")
            return False
        
        # Test 2: Multi-service operations
        if not test_multi_service():
            print("\n[FAIL] Multi-service test failed!")
            return False
        
        # Test 3: Save/Load
        if not test_save_load():
            print("\n[FAIL] Save/Load test failed!")
            return False
        
        print("\n" + "=" * 60)
        print("[SUCCESS] ALL TESTS PASSED!")
        print("=" * 60)
        print("\nThe multi-service architecture is working correctly!")
        print("\nNext steps:")
        print("1. Run the app: python backend/main.py")
        print("2. Open Settings to see the new UI")
        print("3. Add multiple servers and services")
        print("4. Check the Status page to see all services")
        
        return True
        
    except Exception as e:
        print(f"\n[ERROR] Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

