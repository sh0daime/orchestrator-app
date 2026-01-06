"""
VCTT Orchestrator Integration Module

This module provides a simple interface for the orchestrator to interact with VCTT.
It can be imported directly or called via command line.

Usage from orchestrator:
    import subprocess
    result = subprocess.run(['python', 'vctt_interface.py', '--check'], capture_output=True, text=True)
    
Or import directly:
    from vctt_interface import VCTTInterface
    interface = VCTTInterface()
    if interface.is_installed():
        interface.launch()
"""

import subprocess
import sys
import os
import json
import platform
from pathlib import Path
from typing import Optional, Tuple, Dict, Any


class VCTTInterface:
    """Interface for orchestrator to manage VCTT application."""
    
    def __init__(self, vctt_path: Optional[str] = None):
        """
        Initialize the VCTT interface.
        
        Args:
            vctt_path: Path to VCTT_app directory. If None, uses script location.
        """
        if vctt_path:
            self.vctt_path = Path(vctt_path)
        else:
            self.vctt_path = Path(__file__).parent
        
        self.env_name = "vtcc_test"
        self.is_windows = platform.system() == 'Windows'
        
        # Cross-platform script detection
        if self.is_windows:
            self.launch_script = self.vctt_path / "launch_vctt.bat"
            self.install_script = self.vctt_path / "install_vctt.bat"
            self.update_script = self.vctt_path / "update_vctt.bat"
            self.bootstrap_script = Path(__file__).parent / "bootstrap_vctt.bat"
        else:
            self.launch_script = self.vctt_path / "launch_vctt.sh"
            self.install_script = self.vctt_path / "install_vctt.sh"
            self.update_script = self.vctt_path / "update_vctt.sh"
            self.bootstrap_script = Path(__file__).parent / "bootstrap_vctt.sh"
    
    def is_installed(self) -> bool:
        """Check if VCTT environment is installed."""
        try:
            result = subprocess.run(
                ["conda", "info", "--envs"],
                capture_output=True, text=True, shell=True
            )
            return self.env_name in result.stdout
        except Exception:
            return False
    
    def get_version(self) -> Optional[str]:
        """Get the current VCTT version."""
        if not self.is_installed():
            return None
        
        try:
            result = subprocess.run(
                [str(self.launch_script), "--version"],
                capture_output=True, text=True, shell=True,
                cwd=str(self.vctt_path)
            )
            return result.stdout.strip() if result.returncode == 0 else None
        except Exception:
            return None
    
    def check_for_updates(self) -> Tuple[bool, Optional[str]]:
        """
        Check if updates are available.
        
        Returns:
            Tuple of (update_available, latest_version)
        """
        try:
            result = subprocess.run(
                [str(self.launch_script), "--check-update"],
                capture_output=True, text=True, shell=True,
                cwd=str(self.vctt_path)
            )
            update_available = "UPDATE_AVAILABLE" in result.stdout
            return update_available, None
        except Exception as e:
            return False, None
    
    def install(self, wait: bool = True) -> int:
        """
        Run the VCTT installer.
        
        Args:
            wait: If True, wait for installation to complete.
            
        Returns:
            Exit code (0 = success)
        """
        if wait:
            result = subprocess.run(
                [str(self.install_script)],
                shell=True, cwd=str(self.vctt_path)
            )
            return result.returncode
        else:
            subprocess.Popen(
                [str(self.install_script)],
                shell=True, cwd=str(self.vctt_path)
            )
            return 0
    
    def update(self, wait: bool = True) -> int:
        """
        Run the VCTT updater.
        
        Args:
            wait: If True, wait for update to complete.
            
        Returns:
            Exit code (0 = success)
        """
        if wait:
            result = subprocess.run(
                [str(self.update_script)],
                shell=True, cwd=str(self.vctt_path)
            )
            return result.returncode
        else:
            subprocess.Popen(
                [str(self.update_script)],
                shell=True, cwd=str(self.vctt_path)
            )
            return 0
    
    def launch(self, wait: bool = False, *args) -> int:
        """
        Launch the VCTT application.
        
        Args:
            wait: If True, wait for application to close.
            args: Additional arguments to pass to VCTT.
            
        Returns:
            Exit code if wait=True, else 0
        """
        cmd = [str(self.launch_script)] + list(args)
        
        if wait:
            result = subprocess.run(
                cmd, shell=True, cwd=str(self.vctt_path)
            )
            return result.returncode
        else:
            subprocess.Popen(
                cmd, shell=True, cwd=str(self.vctt_path)
            )
            return 0
    
    def run_bootstrap(self, install_dir: str, wait: bool = True) -> Tuple[int, str]:
        """
        Run the VCTT bootstrap installer.
        
        Args:
            install_dir: Directory where VCTT should be installed
            wait: If True, wait for installation to complete.
            
        Returns:
            Tuple of (exit_code, output_message)
        """
        if not self.bootstrap_script.exists():
            return 1, f"Bootstrap script not found: {self.bootstrap_script}"
        
        try:
            install_path = Path(install_dir)
            install_path.mkdir(parents=True, exist_ok=True)
            
            if self.is_windows:
                # Windows: run batch file
                cmd = [str(self.bootstrap_script)]
                # Note: bootstrap_vctt.bat is interactive, so we can't easily pass install_dir
                # For now, it will prompt the user
                result = subprocess.run(
                    cmd,
                    shell=True,
                    cwd=str(install_path.parent),
                    capture_output=not wait,
                    text=True
                )
            else:
                # Mac/Linux: run shell script
                cmd = ['bash', str(self.bootstrap_script), install_dir]
                result = subprocess.run(
                    cmd,
                    cwd=str(install_path.parent),
                    capture_output=not wait,
                    text=True
                )
            
            if wait:
                output = result.stdout if result.stdout else ""
                return result.returncode, output
            else:
                return 0, "Bootstrap installer started"
                
        except Exception as e:
            return 1, f"Failed to run bootstrap: {e}"
    
    def is_configured_in_orchestrator(self) -> Tuple[bool, Optional[str]]:
        """
        Check if VCTT is configured in orchestrator local_apps.
        
        Returns:
            Tuple of (is_configured, app_id_if_found)
        """
        try:
            from config import AppConfig
            config = AppConfig.load()
            
            for app in config.local_apps:
                # Check if this app points to VCTT
                app_path = Path(app.executable_path)
                if 'VCTT' in app.name or 'vctt' in app.name.lower():
                    # Verify the path exists
                    if app_path.exists() or (app.working_directory and Path(app.working_directory).exists()):
                        return True, app.id
            
            return False, None
        except Exception:
            return False, None
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get comprehensive status of VCTT.
        
        Returns:
            Dictionary with installation status, version, etc.
        """
        installed = self.is_installed()
        configured, app_id = self.is_configured_in_orchestrator()
        
        return {
            "installed": installed,
            "configured": configured,
            "app_id": app_id,
            "version": self.get_version() if installed else None,
            "path": str(self.vctt_path),
            "launch_script": str(self.launch_script),
            "bootstrap_script": str(self.bootstrap_script),
            "bootstrap_exists": self.bootstrap_script.exists(),
            "scripts_exist": {
                "launch": self.launch_script.exists(),
                "install": self.install_script.exists(),
                "update": self.update_script.exists(),
            }
        }


def main():
    """Command line interface for orchestrator integration."""
    import argparse
    
    parser = argparse.ArgumentParser(description="VCTT Orchestrator Interface")
    parser.add_argument("--check", action="store_true", help="Check if VCTT is installed")
    parser.add_argument("--version", action="store_true", help="Get VCTT version")
    parser.add_argument("--status", action="store_true", help="Get full status as JSON")
    parser.add_argument("--install", action="store_true", help="Run installer")
    parser.add_argument("--update", action="store_true", help="Run updater")
    parser.add_argument("--launch", action="store_true", help="Launch VCTT")
    parser.add_argument("--check-updates", action="store_true", help="Check for updates")
    parser.add_argument("--path", type=str, help="Path to VCTT_app directory")
    
    args = parser.parse_args()
    
    interface = VCTTInterface(args.path)
    
    if args.check:
        print("INSTALLED" if interface.is_installed() else "NOT_INSTALLED")
        sys.exit(0 if interface.is_installed() else 1)
    
    elif args.version:
        version = interface.get_version()
        if version:
            print(version)
            sys.exit(0)
        else:
            print("UNKNOWN")
            sys.exit(1)
    
    elif args.status:
        status = interface.get_status()
        print(json.dumps(status, indent=2))
        sys.exit(0)
    
    elif args.install:
        sys.exit(interface.install(wait=True))
    
    elif args.update:
        sys.exit(interface.update(wait=True))
    
    elif args.launch:
        sys.exit(interface.launch(wait=True))
    
    elif args.check_updates:
        available, _ = interface.check_for_updates()
        print("UPDATE_AVAILABLE" if available else "UP_TO_DATE")
        sys.exit(0)
    
    else:
        # Default: show status
        status = interface.get_status()
        print(json.dumps(status, indent=2))


if __name__ == "__main__":
    main()
