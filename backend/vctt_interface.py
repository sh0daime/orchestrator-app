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
from typing import Optional, Tuple, Dict, Any, List


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
                # Windows: run batch file in a new console window
                # Use 'start' command to ensure a new visible terminal window
                bootstrap_path = str(self.bootstrap_script)
                if wait:
                    # For wait=True, use CREATE_NEW_CONSOLE
                    result = subprocess.run(
                        bootstrap_path,
                        shell=True,
                        cwd=str(install_path.parent),
                        creationflags=subprocess.CREATE_NEW_CONSOLE
                    )
                    output = result.stdout if hasattr(result, 'stdout') and result.stdout else ""
                    return result.returncode, output
                else:
                    # For wait=False, use 'start' command to open in new window
                    # This ensures the terminal window is visible and interactive
                    # Use absolute paths and proper quoting
                    bootstrap_abs = str(self.bootstrap_script.resolve())
                    work_dir_abs = str(install_path.parent.resolve())
                    # start "title" /D "working_dir" cmd /c "command"
                    cmd = f'start "VCTT Bootstrap Installer" /D "{work_dir_abs}" cmd /c "{bootstrap_abs}"'
                    print(f"[VCTT] Spawning terminal with command: {cmd}")
                    subprocess.Popen(
                        cmd,
                        shell=True
                    )
                    return 0, "Bootstrap installer started in new terminal window"
            else:
                # Mac/Linux: run shell script
                cmd = ['bash', str(self.bootstrap_script), install_dir]
                if wait:
                    result = subprocess.run(
                        cmd,
                        cwd=str(install_path.parent),
                        text=True
                    )
                    output = result.stdout if result.stdout else ""
                    return result.returncode, output
                else:
                    # Don't wait - spawn in new terminal
                    subprocess.Popen(
                        cmd,
                        cwd=str(install_path.parent)
                    )
                    return 0, "Bootstrap installer started in new terminal window"
                
        except Exception as e:
            return 1, f"Failed to run bootstrap: {e}"
    
    def is_valid_vctt_path(self) -> bool:
        """
        Check if the current vctt_path is a valid VCTT installation.
        
        Returns:
            True if path contains VCTT_app with main.py and launch scripts
        """
        # Check for VCTT_app subdirectory
        vctt_app_dir = self.vctt_path / "VCTT_app"
        if vctt_app_dir.exists() and vctt_app_dir.is_dir():
            # Check for main.py
            main_py = vctt_app_dir / "main.py"
            if main_py.exists():
                # Check for launch script
                if self.launch_script.exists() or (vctt_app_dir / self.launch_script.name).exists():
                    return True
        
        # Also check if vctt_path itself is VCTT_app
        main_py = self.vctt_path / "main.py"
        if main_py.exists() and self.launch_script.exists():
            return True
        
        return False
    
    @staticmethod
    def find_vctt_installations() -> List[Path]:
        """
        Search for VCTT installations on the system.
        
        Returns:
            List of paths to VCTT_app directories
        """
        import os
        found_paths = []
        
        # Common installation locations
        search_paths = []
        
        # Get home directory
        home = Path.home()
        
        # Windows common locations
        if platform.system() == 'Windows':
            search_paths = [
                home / "VCTT",
                home / "Documents" / "VCTT",
                Path("C:/VCTT"),
                Path("D:/VCTT"),
            ]
        else:
            # Mac/Linux common locations
            search_paths = [
                home / "VCTT",
                home / "Documents" / "VCTT",
                Path("/opt/VCTT"),
                Path("/usr/local/VCTT"),
            ]
        
        # Search in each location
        for base_path in search_paths:
            if not base_path.exists():
                continue
            
            # Check for VCTT_app subdirectory
            vctt_app = base_path / "VCTT_app"
            if vctt_app.exists() and (vctt_app / "main.py").exists():
                found_paths.append(vctt_app)
            
            # Also check if base_path itself is VCTT_app
            if (base_path / "main.py").exists() and (
                (base_path / "launch_vctt.bat").exists() or 
                (base_path / "launch_vctt.sh").exists()
            ):
                found_paths.append(base_path)
        
        # Also search recursively in home directory (limited depth)
        try:
            for path in [home / "VCTT", home]:
                if path.exists():
                    for item in path.rglob("VCTT_app"):
                        if item.is_dir() and (item / "main.py").exists():
                            if item not in found_paths:
                                found_paths.append(item)
                            # Limit search depth
                            if len(found_paths) >= 5:
                                break
                    if len(found_paths) >= 5:
                        break
        except Exception:
            pass  # Ignore permission errors
        
        return found_paths
    
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
                if 'VCTT' in app.name or 'vctt' in app.name.lower():
                    # Verify the path exists and is valid
                    app_path = Path(app.executable_path)
                    if app_path.exists():
                        # Check if it's a valid VCTT path
                        vctt_check = VCTTInterface(str(app_path.parent))
                        if vctt_check.is_valid_vctt_path():
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
        try:
            installed = self.is_installed()
            configured, app_id = self.is_configured_in_orchestrator()
            valid_path = self.is_valid_vctt_path()
            
            # If current path is not valid, try to find VCTT installations
            found_installations = []
            if not valid_path:
                try:
                    found_installations = self.find_vctt_installations()
                    if found_installations:
                        # Use the first found installation
                        best_path = found_installations[0]
                        self.vctt_path = best_path
                        # Update script paths
                        if self.is_windows:
                            self.launch_script = self.vctt_path / "launch_vctt.bat"
                        else:
                            self.launch_script = self.vctt_path / "launch_vctt.sh"
                        valid_path = True
                        print(f"Found VCTT installation at: {best_path}")
                except Exception as e:
                    print(f"Error searching for VCTT installations: {e}")
            
            return {
                "installed": installed,
                "configured": configured,
                "app_id": app_id,
                "version": self.get_version() if installed and valid_path else None,
                "path": str(self.vctt_path),
                "valid_path": valid_path,
                "found_installations": [str(p) for p in found_installations],
                "launch_script": str(self.launch_script),
                "bootstrap_script": str(self.bootstrap_script),
                "bootstrap_exists": self.bootstrap_script.exists(),
                "scripts_exist": {
                    "launch": self.launch_script.exists(),
                    "install": self.install_script.exists(),
                    "update": self.update_script.exists(),
                }
            }
        except Exception as e:
            print(f"Error in get_status: {e}")
            import traceback
            traceback.print_exc()
            return {
                "installed": False,
                "configured": False,
                "valid_path": False,
                "found_installations": [],
                "error": str(e)
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
