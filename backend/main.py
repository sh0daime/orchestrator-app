"""Main application entry point with PyWebView and system tray"""
import webview
import sys
import os
from pathlib import Path
from PIL import Image
import pystray
from pystray import MenuItem as Item, Menu
import threading
from api import get_api
from process_manager import get_process_manager


class OrchestratorApp:
    """Main orchestrator application"""
    
    def __init__(self):
        self.api = get_api()
        self.process_manager = get_process_manager()
        self.windows = {}
        self.tray_icon = None
        self.running = True
        
        # Get project root (parent of backend directory)
        self.project_root = Path(__file__).parent.parent
        self.src_dir = self.project_root / 'src'
        # Icons are still in src-tauri/icons (or can be moved to icons/)
        icons_path = self.project_root / 'icons'
        if not icons_path.exists():
            icons_path = self.project_root / 'src-tauri' / 'icons'
        self.icons_dir = icons_path
        
        # Register window creator callback with API so it can open windows
        self.api.set_window_creator(self.create_window)
    
    def get_icon_path(self):
        """Get the tray icon path"""
        icon_path = self.icons_dir / 'icon.png'
        if not icon_path.exists():
            # Fallback to 32x32
            icon_path = self.icons_dir / '32.png'
        return str(icon_path)
    
    def create_tray_icon(self):
        """Create the system tray icon"""
        try:
            icon_path = self.get_icon_path()
            image = Image.open(icon_path)
            
            menu = Menu(
                Item('Open Dashboard', self.on_open_dashboard),
                Menu.SEPARATOR,
                Item('Launch Portal', self.on_launch_portal),
                Item('Launch VCTT', self.on_launch_vctt),
                Menu.SEPARATOR,
                Item('Settings', self.on_settings),
                Item('Status', self.on_status),
                Menu.SEPARATOR,
                Item('Quit', self.on_quit)
            )
            
            self.tray_icon = pystray.Icon(
                "orchestrator",
                image,
                "Platonic",
                menu
            )
            
            # Run tray icon in separate thread
            threading.Thread(target=self.tray_icon.run, daemon=True).start()
            
        except Exception as e:
            print(f"Failed to create tray icon: {e}")
    
    def on_open_dashboard(self, icon=None, item=None):
        """Open/show the dashboard window"""
        def show_dashboard():
            if 'home' in self.windows and self.windows['home']:
                # Window exists, just show it
                try:
                    self.windows['home'].show()
                except:
                    # If showing fails, create a new window
                    self.create_window('home')
            else:
                # Create new dashboard window
                self.create_window('home')
        
        # Run in separate thread to avoid blocking the tray
        threading.Thread(target=show_dashboard, daemon=True).start()
    
    def on_launch_portal(self, icon=None, item=None):
        """Launch Portal action"""
        def launch():
            try:
                print("Launch Portal clicked - loading config...")
                config_dict = self.api.load_config()
                print(f"Config loaded: {len(config_dict.get('servers', []))} server(s)")
                
                if config_dict['servers']:
                    server_id = config_dict['servers'][0]['id']
                    print(f"Launching portal on server: {server_id}")
                    url = self.api.launch_portal(server_id)
                    print(f"Portal launched successfully at: {url}")
                    # Open URL in browser
                    import webbrowser
                    webbrowser.open(url)
                else:
                    print("No servers configured!")
            except Exception as e:
                print(f"Failed to launch portal: {e}")
                import traceback
                traceback.print_exc()
        
        threading.Thread(target=launch, daemon=True).start()
    
    def on_launch_vctt(self, icon=None, item=None):
        """Launch VCTT action"""
        def launch():
            try:
                config_dict = self.api.load_config()
                if config_dict['local_apps']:
                    app_id = config_dict['local_apps'][0]['id']
                    self.api.launch_local_app(app_id)
            except Exception as e:
                print(f"Failed to launch VCTT: {e}")
        
        threading.Thread(target=launch, daemon=True).start()
    
    def on_settings(self, icon=None, item=None):
        """Open Settings window"""
        def create_settings():
            self.create_window('settings')
        
        # Run in separate thread to avoid blocking the tray
        threading.Thread(target=create_settings, daemon=True).start()
    
    def on_status(self, icon=None, item=None):
        """Open Status window"""
        def create_status():
            self.create_window('status')
        
        # Run in separate thread to avoid blocking the tray
        threading.Thread(target=create_status, daemon=True).start()
    
    def on_quit(self, icon=None, item=None):
        """Quit application"""
        self.running = False
        self.process_manager.cleanup_all()
        
        if self.tray_icon:
            self.tray_icon.stop()
        
        # Close all windows
        for window in self.windows.values():
            if window:
                try:
                    window.destroy()
                except:
                    pass
        
        sys.exit(0)
    
    def create_window(self, window_type):
        """Create a webview window or focus existing one"""
        # Check if window already exists and hasn't been closed
        if window_type in self.windows and self.windows[window_type]:
            existing_window = self.windows[window_type]
            # Check if window still exists (hasn't been destroyed)
            # PyWebView windows lose their internal state when closed
            try:
                # Try to access window properties to check if it's still valid
                _ = existing_window.width
                # Window is still valid, restore and focus it
                # Use restore() to bring back minimized windows, then show() to focus
                existing_window.restore()
                existing_window.show()
                print(f"Restored and focused existing {window_type} window")
                return existing_window
            except:
                # Window was closed or is invalid, remove from dict
                print(f"Existing {window_type} window was closed, creating new one")
                self.windows[window_type] = None
        
        # Determine window properties based on type
        if window_type == 'home':
            # For home dashboard, try to load built version first
            html_file = self.project_root / 'dist' / 'home.html'
            if not html_file.exists():
                # Fallback to src/ for development
                html_file = self.src_dir / 'home.html'
            title = 'PLATONIC - Pantheon Lab Tools Orchestration for Integration and Control'
            width, height = 1280, 740
        elif window_type == 'settings':
            html_file = self.src_dir / 'settings.html'
            title = 'PLATONIC - Settings'
            width, height = 600, 700
        elif window_type == 'status':
            html_file = self.src_dir / 'status.html'
            title = 'PLATONIC - Status'
            width, height = 800, 600
        else:
            html_file = self.src_dir / 'index.html'
            title = 'Orchestrator'
            width, height = 400, 300
        
        if not html_file.exists():
            print(f"HTML file not found: {html_file}")
            return None
        
        # Create window with API exposed
        # Note: js_api exposes the API object as window.pywebview.api
        window = webview.create_window(
            title,
            str(html_file),
            width=width,
            height=height,
            resizable=True,
            hidden=False,
            js_api=self.api  # Expose API to this window as window.pywebview.api
        )
        
        # Set up event handler to clear window from dict when closed
        def on_closing():
            print(f"{window_type} window closing, removing from registry")
            self.windows[window_type] = None
        
        window.events.closing += on_closing
        
        self.windows[window_type] = window
        print(f"Created {window_type} window")
        return window
    
    def run(self):
        """Run the application"""
        # Create system tray icon
        self.create_tray_icon()
        
        # PyWebView requires at least one window to be created before start()
        # Create the home dashboard as the main window
        home_html = self.project_root / 'dist' / 'home.html'
        if not home_html.exists():
            # Fallback to src/ for development
            home_html = self.src_dir / 'home.html'
        
        main_window = webview.create_window(
            'PLATONIC - Pantheon Lab Tools Orchestration for Integration and Control',
            str(home_html),
            width=1280,
            height=740,
            resizable=True,
            hidden=False,  # Show the home dashboard window
            js_api=self.api  # Expose API to JavaScript as window.pywebview.api
        )
        self.windows['home'] = main_window
        
        # Start webview (this blocks)
        webview.start(debug=False)


def main():
    """Main entry point"""
    # Set up logging
    import logging
    logging.basicConfig(level=logging.INFO)
    
    # Create and run app
    app = OrchestratorApp()
    app.run()


if __name__ == '__main__':
    main()

