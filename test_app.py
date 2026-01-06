"""Test script for the Orchestrator App Python implementation"""
import sys
import asyncio
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from backend.config import AppConfig, ServerConfig, LocalAppConfig
from backend.ssh_client import SSHClient
from backend.process_manager import get_process_manager
from backend.api import get_api


def test_config():
    """Test configuration management"""
    print("Testing configuration...")
    
    # Create test config
    config = AppConfig(
        version="1.0",
        servers=[
            ServerConfig(
                id="test-server",
                name="Test Server",
                host="192.168.50.101",
                port=22,
                username="calvin",
                ssh_key_path=r"C:\Users\plab\calvin@desktop",
                portal_port=8080,
                portal_path="/home/calvin/calvinsidharta/unified-gradio-portal"
            )
        ],
        local_apps=[
            LocalAppConfig(
                id="vctt",
                name="VCTT",
                executable_path="main.py",
                working_directory=r"C:\Users\plab\calvinsidharta\data\VCTT_app",
                use_shell=True,
                conda_env="vctt_env"
            )
        ]
    )
    
    # Save and load
    config.save()
    print("✓ Config saved")
    
    loaded_config = AppConfig.load()
    assert len(loaded_config.servers) == 1
    assert loaded_config.servers[0].host == "192.168.50.101"
    print("✓ Config loaded successfully")
    
    return True


async def test_ssh_connection():
    """Test SSH connection"""
    print("\nTesting SSH connection...")
    
    config = AppConfig.load()
    if not config.servers:
        print("⚠ No servers configured, skipping SSH test")
        return False
    
    server = config.servers[0]
    
    try:
        with SSHClient(
            host=server.host,
            port=server.port,
            username=server.username,
            ssh_key_path=server.ssh_key_path,
            portal_path=server.portal_path
        ) as ssh:
            # Test simple command
            output = ssh.execute_command("echo 'Connection successful'")
            assert "Connection successful" in output
            print("✓ SSH connection successful")
            print(f"  Output: {output.strip()}")
            
            return True
    except Exception as e:
        print(f"✗ SSH connection failed: {e}")
        return False


async def test_api():
    """Test API functions"""
    print("\nTesting API...")
    
    api = get_api()
    
    # Test load config
    config_dict = await api.load_config()
    assert 'servers' in config_dict
    print("✓ API load_config works")
    
    # Test save config
    await api.save_config(config_dict)
    print("✓ API save_config works")
    
    return True


async def main():
    """Run all tests"""
    print("=" * 50)
    print("Orchestrator App - Python Implementation Tests")
    print("=" * 50)
    
    results = []
    
    # Test 1: Configuration
    try:
        results.append(("Configuration", test_config()))
    except Exception as e:
        print(f"✗ Configuration test failed: {e}")
        results.append(("Configuration", False))
    
    # Test 2: API
    try:
        result = await test_api()
        results.append(("API", result))
    except Exception as e:
        print(f"✗ API test failed: {e}")
        results.append(("API", False))
    
    # Test 3: SSH Connection
    try:
        result = await test_ssh_connection()
        results.append(("SSH Connection", result))
    except Exception as e:
        print(f"✗ SSH test failed: {e}")
        results.append(("SSH Connection", False))
    
    # Summary
    print("\n" + "=" * 50)
    print("Test Summary:")
    print("=" * 50)
    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{name:.<30} {status}")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n✓ All tests passed!")
        return 0
    else:
        print(f"\n⚠ {total - passed} test(s) failed")
        return 1


if __name__ == '__main__':
    sys.exit(asyncio.run(main()))

