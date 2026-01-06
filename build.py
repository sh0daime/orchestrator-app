"""Build script for creating standalone executable with PyInstaller"""
import PyInstaller.__main__
import sys
import os
from pathlib import Path

def build():
    """Build the orchestrator app executable"""
    
    project_root = Path(__file__).parent
    src_dir = project_root / 'src'
    icons_dir = project_root / 'src-tauri' / 'icons'
    
    # Prepare PyInstaller arguments
    args = [
        str(project_root / 'backend' / 'main.py'),
        '--name=Orchestrator',
        '--onefile',
        '--windowed',  # No console window
        f'--add-data={src_dir}{os.pathsep}src',
        f'--add-data={icons_dir}{os.pathsep}icons',
        '--hidden-import=backend.config',
        '--hidden-import=backend.ssh_client',
        '--hidden-import=backend.process_manager',
        '--hidden-import=backend.api',
        '--clean',
    ]
    
    # Add icon if on Windows
    if sys.platform == 'win32':
        icon_path = icons_dir / 'icon.ico'
        if icon_path.exists():
            args.append(f'--icon={icon_path}')
    
    print("Building Orchestrator App...")
    print(f"Arguments: {' '.join(args)}")
    
    try:
        PyInstaller.__main__.run(args)
        print("\n✓ Build completed successfully!")
        print(f"Executable location: {project_root / 'dist' / 'Orchestrator.exe' if sys.platform == 'win32' else project_root / 'dist' / 'Orchestrator'}")
    except Exception as e:
        print(f"\n✗ Build failed: {e}")
        sys.exit(1)

if __name__ == '__main__':
    build()

