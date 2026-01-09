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
    
    def start_local_server(self, directory: Path, port: int = 8765):
        """Start a local HTTP server to serve static files"""
        class Handler(http.server.SimpleHTTPRequestHandler):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, directory=str(directory), **kwargs)
            
            def log_message(self, format, *args):
                # Suppress HTTP server logs unless debugging
                pass
        
        try:
            # Don't use 'with' statement - we want the server to persist
            httpd = socketserver.TCPServer(("", port), Handler)
            # Allow address reuse to avoid "Address already in use" errors
            httpd.allow_reuse_address = True
            self.http_server = httpd
            server_thread = threading.Thread(target=httpd.serve_forever, daemon=True)
            server_thread.start()
            print(f"Started local HTTP server on port {port}")
            return True
        except OSError as e:
            print(f"Could not start HTTP server on port {port}: {e}")
            return False
    
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
                # Window exists, restore and show it on top
                try:
                    self.windows['home'].restore()
                    self.windows['home'].show()
                except:
                    # If showing fails, create a new window
                    self.create_window('home')
            else:
                # Create new dashboard window
                self.create_window('home')
        
        # Run in separate thread to avoid blocking the tray
        threading.Thread(target=show_dashboard, daemon=True).start()
    

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
        use_http_server = False
        if window_type == 'home':
            # For home dashboard, try to load built version first
            html_file = self.project_root / 'dist' / 'home.html'
            if not html_file.exists():
                # Fallback to src/ for development
                html_file = self.src_dir / 'home.html'
            else:
                use_http_server = True
            title = 'PLATONIC - Pantheon Lab Tools Orchestration for Integration and Control'
            width, height = 1280, 740
        elif window_type == 'settings':
            # Try built version first
            html_file = self.project_root / 'dist' / 'src' / 'settings.html'
            if not html_file.exists():
                html_file = self.src_dir / 'settings.html'
            else:
                use_http_server = True
            title = 'PLATONIC - Settings'
            width, height = 600, 700
        elif window_type == 'status':
            # Try built version first
            html_file = self.project_root / 'dist' / 'src' / 'status.html'
            if not html_file.exists():
                html_file = self.src_dir / 'status.html'
            else:
                use_http_server = True
            title = 'PLATONIC - Status'
            width, height = 800, 600
        else:
            html_file = self.src_dir / 'index.html'
            title = 'Orchestrator'
            width, height = 400, 300
        
        if not html_file.exists():
            print(f"HTML file not found: {html_file}")
            return None
        
        # If using HTTP server (for built versions), convert file path to URL
        if use_http_server and self.http_server:
            # Convert absolute path to relative path from dist directory
            try:
                relative_path = html_file.relative_to(self.project_root / 'dist')
                url = f"http://localhost:{self.http_port}/{relative_path}"
                print(f"Loading {window_type} from HTTP server: {url}")
                html_source = url
            except ValueError:
                # Fallback to file path if not in dist
                html_source = str(html_file)
        else:
            html_source = str(html_file)
        
        # Create window with API exposed
        # Note: js_api exposes the API object as window.pywebview.api
        window = webview.create_window(
            title,
            html_source,
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
        import platform
        
        # Create system tray icon (non-blocking, continue even if it fails)
        # NOTE: On macOS, pystray can conflict with pywebview's event loop
        # Skip tray icon on macOS for now
        if platform.system() != 'Darwin':
            try:
                self.create_tray_icon()
            except Exception as e:
                print(f"Warning: Could not create tray icon: {e}")
                print("Application will continue without tray icon.")
        else:
            print("Note: Tray icon disabled on macOS (conflicts with pywebview event loop)")
        
        # Find the home HTML file - check multiple options in order:
        # 1. Built version (dist/home.html) - preferred
        # 2. Vite dev server (http://localhost:1420/home.html) - for development
        # 3. Error if neither available
        
        home_html = self.project_root / 'dist' / 'home.html'
        using_built = home_html.exists()
        using_vite_dev = False
        html_path = None
        
        if using_built:
            print("Found built version in dist/home.html")
            # Start local HTTP server for built assets
            if self.start_local_server(self.project_root / 'dist', self.http_port):
                html_path = f"http://localhost:{self.http_port}/home.html"
                print(f"Using HTTP server: {html_path}")
            else:
                html_path = str(home_html.resolve())
        else:
            # Check if Vite dev server is running
            import urllib.request
            try:
                response = urllib.request.urlopen('http://localhost:1420/home.html', timeout=1)
                response.close()
                html_path = 'http://localhost:1420/home.html'
                using_vite_dev = True
                print("Found Vite dev server running on port 1420")
                print(f"Using Vite dev server: {html_path}")
            except:
                # Vite dev server not running
                pass
        
        # If neither built version nor Vite dev server available, show error
        if not html_path:
            error_msg = f"""ERROR: Cannot load frontend!

The built version (dist/home.html) was not found, and Vite dev server is not running.

To fix this, please run ONE of the following:

1. Build the frontend (recommended for production):
   cd {self.project_root}
   npm run build

2. Start Vite dev server (for development):
   cd {self.project_root}
   npm run dev

Then restart this application.

Searched locations:
  - {self.project_root / 'dist' / 'home.html'}
  - Vite dev server: http://localhost:1420/home.html"""
            print(error_msg)
            # On Mac, show a simple error window if possible
            try:
                error_window = webview.create_window(
                    'PLATONIC - Setup Required',
                    html=f'''<html>
                        <head>
                            <style>
                                body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif; padding: 40px; line-height: 1.6; }}
                                h1 {{ color: #d32f2f; }}
                                code {{ background: #f5f5f5; padding: 2px 6px; border-radius: 3px; font-family: 'Monaco', 'Courier New', monospace; }}
                                .command {{ background: #263238; color: #aed581; padding: 15px; border-radius: 5px; margin: 10px 0; font-family: 'Monaco', 'Courier New', monospace; }}
                            </style>
                        </head>
                        <body>
                            <h1>⚠️ Frontend Not Built</h1>
                            <p>The frontend needs to be built before running the application.</p>
                            <h2>To fix this, run ONE of the following:</h2>
                            <h3>Option 1: Build for production (recommended)</h3>
                            <div class="command">cd {self.project_root}<br>npm install<br>npm run build</div>
                            <h3>Option 2: Start dev server (for development)</h3>
                            <div class="command">cd {self.project_root}<br>npm install<br>npm run dev</div>
                            <p><strong>Then restart this application.</strong></p>
                            <p style="color: #666; font-size: 0.9em;">Note: On Mac, the build script may need to be adjusted (remove PowerShell step).</p>
                        </body>
                    </html>''',
                    width=700,
                    height=500,
                    resizable=True
                )
                webview.start(debug=False)
            except:
                # If even error window fails, print and exit
                print("Could not create error window. Exiting.")
                sys.exit(1)
            return
        
        print(f"Loading: {html_path}")
        
        # On macOS, PyWebView works better when window is created before start()
        # but we need to ensure it's properly shown
        try:
            # Create window - use URL string directly (PyWebView handles http:// and file://)
            main_window = webview.create_window(
                'PLATONIC - Pantheon Lab Tools Orchestration for Integration and Control',
                html_path,  # Can be http:// URL or file:// path
                width=1280,
                height=740,
                resizable=True,
                hidden=False,  # Show the home dashboard window
                js_api=self.api,  # Expose API to JavaScript as window.pywebview.api
                text_select=False,  # Prevent text selection issues
                shadow=True  # Enable window shadow on Mac
            )
            self.windows['home'] = main_window
            
            # Set up error handler to prevent window from closing on JS errors
            def on_loaded():
                """Called when window finishes loading"""
                print("Window loaded successfully")
                try:
                    # Inject error handler to catch JS errors and prevent window closure
                    main_window.evaluate_js("""
                        window.addEventListener('error', function(e) {
                            console.error('JavaScript error:', e.error);
                            // Don't let errors close the window
                            e.preventDefault();
                        });
                        window.addEventListener('unhandledrejection', function(e) {
                            console.error('Unhandled promise rejection:', e.reason);
                            e.preventDefault();
                        });
                    """)
                except Exception as e:
                    print(f"Could not inject error handler: {e}")
            
            main_window.events.loaded += on_loaded
            
            print(f"Window created successfully. Platform: {platform.system()}")
            print(f"Loading: {html_path}")
            print("Starting webview...")
            # Start webview (this blocks)
            # Enable debug mode on Mac to see console errors
            webview.start(debug=platform.system() == 'Darwin')
        except Exception as e:
            error_msg = f"Failed to start application: {e}"
            print(error_msg)
            import traceback
            traceback.print_exc()
            
            # Try to show error in a window
            try:
                error_window = webview.create_window(
                    'PLATONIC - Error',
                    html=f'<html><body style="font-family: Arial; padding: 20px;"><h1>Startup Error</h1><p>{error_msg}</p><pre>{traceback.format_exc()}</pre></body></html>',
                    width=800,
                    height=600,
                    resizable=True
                )
                webview.start(debug=False)
            except:
                print("Could not create error window. Exiting.")
                sys.exit(1)


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

