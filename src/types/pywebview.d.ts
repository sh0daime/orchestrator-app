// TypeScript declarations for PyWebView API bridge

interface ServerConfig {
  id: string;
  name: string;
  host: string;
  port: number;
  username: string;
  ssh_key_path: string;
  services: ServiceConfig[];
}

interface ServiceConfig {
  id: string;
  name: string;
  container_name?: string;
  port: number;
  path: string;
  healthcheck_path: string;
  pre_launch_command?: string;
}

interface LocalAppConfig {
  id: string;
  name: string;
  executable_path: string;
  working_directory: string;
  use_shell?: boolean;
  conda_env?: string;
  shell_command?: string;
  install_dependencies?: boolean;
  requirements_file?: string;
}

interface Preferences {
  auto_start_portal?: boolean;
  minimize_to_tray?: boolean;
  startup_launch?: boolean;
  setup_completed?: boolean;
}

interface AppConfig {
  version: string;
  servers: ServerConfig[];
  local_apps: LocalAppConfig[];
  preferences: Preferences;
}

interface ContainerStatus {
  name: string;
  state: string;
  status: string;
}

interface ServiceStatus {
  id: string;
  name: string;
  url: string;
  ready: boolean;
  running: boolean;
  has_containers: boolean;
  containers: ContainerStatus[];
  container_count: number;
  matched_container?: string;
}

interface ServerStatus {
  server_id: string;
  server_name: string;
  connected: boolean;
  services: ServiceStatus[];
}

interface PyWebViewAPI {
  // Configuration
  load_config: () => Promise<AppConfig>;
  save_config: (config: Record<string, any>) => Promise<void>;
  
  // Remote service management
  launch_service: (serverId: string, serviceId: string) => Promise<string>;
  stop_service: (serverId: string, serviceId: string) => Promise<void>;
  launch_portal: (serverId: string) => Promise<string>;
  restart_container: (serverId: string, serviceId: string, containerName: string) => Promise<void>;
  
  // Local app management
  launch_local_app: (appId: string) => Promise<void>;
  is_app_running: (appId: string) => Promise<boolean>;
  terminate_app: (appId: string) => Promise<void>;
  
  // Status
  get_status: (serverId: string) => Promise<ServerStatus>;
  get_all_status: () => Promise<ServerStatus[]>;
  
  // Connection testing
  test_connection: (server: Record<string, any>) => Promise<string>;
  
  // Window management
  open_settings_window: () => Promise<void>;
  open_status_window: () => Promise<void>;
  
  // Setup wizard
  mark_setup_completed: () => Promise<void>;
  
  // VCTT installation
  get_vctt_status: () => Promise<{
    installed: boolean;
    configured: boolean;
    app_id?: string;
    version?: string;
    path?: string;
    bootstrap_exists?: boolean;
    error?: string;
  }>;
  run_vctt_bootstrap: (installDir: string) => Promise<{
    success: boolean;
    exit_code: number;
    message: string;
  }>;
  configure_vctt_app: (vcttPath: string, condaEnv?: string) => Promise<string>;
}

interface Window {
  pywebview?: {
    api: PyWebViewAPI;
  };
}

