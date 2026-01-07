"""Process manager for launching and managing local applications"""
import subprocess
import os
import sys
from typing import Dict, Optional
from config import LocalAppConfig


class ProcessManager:
    """Manages local application processes"""
    
    def __init__(self):
        self.processes: Dict[str, subprocess.Popen] = {}
    
    def launch_app(self, config: LocalAppConfig) -> None:
        """Launch a local application"""
        # Check if already running
        if config.id in self.processes:
            process = self.processes[config.id]
            if process.poll() is None:  # Still running
                print(f"App '{config.name}' is already running (PID: {process.pid})")
                raise Exception(f"App '{config.name}' is already running")
            else:
                # Process has exited, remove it
                print(f"Previous process for '{config.name}' has exited, cleaning up...")
                del self.processes[config.id]
        
        try:
            if config.use_shell:
                # Build shell command
                if config.shell_command:
                    # Use custom shell command
                    shell_cmd = config.shell_command
                elif config.conda_env:
                    # Build conda activation command
                    conda_base = "conda" if sys.platform == 'win32' else "source $(conda info --base)/etc/profile.d/conda.sh && conda"
                    
                    # Build command parts
                    cmd_parts = []
                    
                    if sys.platform == 'win32':
                        cmd_parts.append(f"conda activate {config.conda_env}")
                    else:
                        cmd_parts.append(f"source $(conda info --base)/etc/profile.d/conda.sh")
                        cmd_parts.append(f"conda activate {config.conda_env}")
                    
                    # Install dependencies if requested
                    if config.install_dependencies and config.requirements_file:
                        req_path = config.requirements_file
                        if config.working_directory and not os.path.isabs(req_path):
                            req_path = os.path.join(config.working_directory, req_path)
                        # Use absolute path for requirements file
                        req_path = os.path.abspath(req_path)
                        cmd_parts.append(f"pip install -r \"{req_path}\"")
                    
                    # Run the Python script
                    exec_path = config.executable_path
                    if config.working_directory and not os.path.isabs(exec_path):
                        exec_path = os.path.join(config.working_directory, exec_path)
                    cmd_parts.append(f"python {exec_path}")
                    
                    shell_cmd = " && ".join(cmd_parts)
                else:
                    # Just run the executable path as a command
                    shell_cmd = config.executable_path
                
                # Execute via shell
                if sys.platform == 'win32':
                    # Windows: use cmd.exe
                    process = subprocess.Popen(
                        shell_cmd,
                        shell=True,
                        cwd=config.working_directory,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        creationflags=subprocess.CREATE_NEW_CONSOLE if sys.platform == 'win32' else 0
                    )
                else:
                    # Mac/Linux: use sh
                    process = subprocess.Popen(
                        ['sh', '-c', shell_cmd],
                        cwd=config.working_directory,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE
                    )
            else:
                # Direct execution
                process = subprocess.Popen(
                    [config.executable_path],
                    cwd=config.working_directory,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
            
            self.processes[config.id] = process
            print(f"Launched app: {config.name} (PID: {process.pid})")
            
        except Exception as e:
            raise Exception(f"Failed to launch app '{config.name}': {e}")
    
    def is_running(self, app_id: str) -> bool:
        """Check if an app is currently running"""
        if app_id not in self.processes:
            return False
        
        process = self.processes[app_id]
        if process.poll() is None:
            return True
        else:
            # Process has exited
            del self.processes[app_id]
            return False
    
    def terminate(self, app_id: str) -> None:
        """Terminate a running app"""
        if app_id not in self.processes:
            return
        
        process = self.processes[app_id]
        try:
            process.terminate()
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
        finally:
            del self.processes[app_id]
    
    def cleanup_all(self) -> None:
        """Terminate all running processes"""
        for app_id in list(self.processes.keys()):
            try:
                self.terminate(app_id)
            except:
                pass


# Global process manager instance
_process_manager = ProcessManager()


def get_process_manager() -> ProcessManager:
    """Get the global process manager instance"""
    return _process_manager

