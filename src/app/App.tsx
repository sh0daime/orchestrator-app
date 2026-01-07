import { useState, useEffect } from 'react';
import { Sparkles, Workflow, Monitor, Settings, Activity } from 'lucide-react';
import logo from "../../icons/icon.png";
import ServiceSelector from '../components/ServiceSelector';
import VCTTInstaller from '../components/VCTTInstaller';
import SetupWizard from '../components/SetupWizard';

// Helper function to wait for PyWebView API to be ready
function waitForAPI(): Promise<void> {
  return new Promise((resolve) => {
    if (window.pywebview?.api) {
      resolve();
    } else {
      window.addEventListener('pywebviewready', () => resolve());
    }
  });
}

interface ServiceInstance {
  serverId: string;
  serverName: string;
  serviceId: string;
  serviceName: string;
  port: number;
  host: string;
}

export default function App() {
  const [showWizard, setShowWizard] = useState(false);
  const [isCheckingFirstRun, setIsCheckingFirstRun] = useState(true);
  const [serviceSelector, setServiceSelector] = useState<{
    serviceName: string;
    instances: ServiceInstance[];
  } | null>(null);
  const [showVCTTInstaller, setShowVCTTInstaller] = useState(false);
  const [launchingVCTT, setLaunchingVCTT] = useState(false); // Prevent double launch

  // Check if this is a first-run on mount
  useEffect(() => {
    checkFirstRun();
  }, []);

  async function checkFirstRun() {
    try {
      await waitForAPI();
      const api = window.pywebview!.api;
      const config = await api.load_config();
      
      // Check if setup is incomplete
      // Show wizard if:
      // 1. setup_completed is false/undefined AND
      // 2. No servers configured
      const setupCompleted = config.preferences?.setup_completed ?? false;
      const hasServers = config.servers && config.servers.length > 0;
      const isFirstRun = !setupCompleted && !hasServers;
      
      console.log('First-run check:', {
        setup_completed: setupCompleted,
        servers_count: config.servers?.length || 0,
        hasServers,
        isFirstRun,
        config: config
      });
      
      if (isFirstRun) {
        console.log('Showing setup wizard - first run detected');
        setShowWizard(true);
      } else {
        console.log('Skipping setup wizard - already configured');
      }
    } catch (error) {
      console.error('Failed to check first-run status:', error);
      // On error, don't show wizard (safer)
    } finally {
      setIsCheckingFirstRun(false);
    }
  }

  const handleWizardComplete = () => {
    setShowWizard(false);
    // Optionally refresh the page or show success message
    window.location.reload();
  };

  const handleWizardSkip = () => {
    setShowWizard(false);
  };

  // Find services by name across all servers
  const findServicesByName = (config: any, serviceNames: string[]): ServiceInstance[] => {
    const instances: ServiceInstance[] = [];
    
    if (!config.servers || config.servers.length === 0) {
      return instances;
    }

    for (const server of config.servers) {
      if (!server.services || server.services.length === 0) {
        continue;
      }

      for (const service of server.services) {
        // Check if service name matches any of the target names (case-insensitive, partial match)
        const serviceNameLower = (service.name || '').toLowerCase();
        const matches = serviceNames.some(targetName => 
          serviceNameLower.includes(targetName.toLowerCase()) ||
          targetName.toLowerCase().includes(serviceNameLower)
        );

        if (matches) {
          instances.push({
            serverId: server.id,
            serverName: server.name || server.host,
            serviceId: service.id,
            serviceName: service.name,
            port: service.port || 8080,
            host: server.host,
          });
        }
      }
    }

    return instances;
  };

  const handleServiceSelect = async (serverId: string, serviceId: string) => {
    try {
      await waitForAPI();
      const api = window.pywebview!.api;
      const url = await api.launch_service(serverId, serviceId);
      window.open(url, '_blank');
      setServiceSelector(null);
    } catch (error: any) {
      alert(`Failed to launch service: ${error.message}`);
    }
  };

  const handleVCTTInstallComplete = async (_installPath: string) => {
    setShowVCTTInstaller(false);
    // Optionally refresh or show success message
    alert('VCTT installation complete! You can now launch it from the dashboard.');
  };

  const tools = [
    {
      id: 'gradio',
      name: 'AI Gradio Apps',
      description: 'Launch AI-powered Gradio applications',
      icon: Sparkles,
      color: 'from-purple-500 to-pink-500',
    },
    {
      id: 'pipeline',
      name: 'Pipeline Management Tool',
      description: 'Launch our digital human preprocessor',
      icon: Workflow,
      color: 'from-blue-500 to-cyan-500',
    },
    {
      id: 'vctt',
      name: 'VCTT App',
      description: 'Launch the local VCTT application',
      icon: Monitor,
      color: 'from-green-500 to-emerald-500',
    },
    {
      id: 'settings',
      name: 'Settings',
      description: 'Configure servers and services',
      icon: Settings,
      color: 'from-orange-500 to-amber-500',
    },
    {
      id: 'status',
      name: 'Status',
      description: 'View system status and logs',
      icon: Activity,
      color: 'from-indigo-500 to-purple-500',
    },
  ];

  const handleLaunch = async (toolId: string) => {
    try {
      console.log(`Launching ${toolId}...`);
      
      // Wait for PyWebView API to be ready
      await waitForAPI();
      const api = window.pywebview!.api;
      
      switch (toolId) {
        case 'gradio': {
          // Find AI Portal/Gradio services across all servers
          const config = await api.load_config();
          const serviceNames = ['AI Portal', 'AI Gradio Apps', 'Gradio', 'Portal'];
          const instances = findServicesByName(config, serviceNames);
          
          if (instances.length === 0) {
            // No instances found, show setup wizard
            setShowWizard(true);
          } else if (instances.length === 1) {
            // Single instance, launch directly
            const instance = instances[0];
            const url = await api.launch_service(instance.serverId, instance.serviceId);
            window.open(url, '_blank');
          } else {
            // Multiple instances, show selector
            setServiceSelector({
              serviceName: 'AI Gradio Apps',
              instances,
            });
          }
          break;
        }
        
        case 'pipeline': {
          // Find Pipeline Management Tool services across all servers
          const config = await api.load_config();
          const serviceNames = ['Pipeline Management Tool', 'Pipeline Tool', 'Pipeline'];
          const instances = findServicesByName(config, serviceNames);
          
          if (instances.length === 0) {
            // No instances found, show setup wizard
            setShowWizard(true);
          } else if (instances.length === 1) {
            // Single instance, launch directly
            const instance = instances[0];
            const url = await api.launch_service(instance.serverId, instance.serviceId);
            window.open(url, '_blank');
          } else {
            // Multiple instances, show selector
            setServiceSelector({
              serviceName: 'Pipeline Management Tool',
              instances,
            });
          }
          break;
        }
        
        case 'vctt': {
          // Prevent double launch - check if already launching
          if (launchingVCTT) {
            console.log('[VCTT] Launch already in progress, ignoring duplicate request');
            break;
          }
          
          try {
            setLaunchingVCTT(true);
            // Check VCTT status
            console.log('[VCTT] Checking VCTT status...');
            const vcttStatus = await api.get_vctt_status();
            console.log('[VCTT] Status result:', vcttStatus);
            
            if (vcttStatus.error) {
              console.error('[VCTT] Status error:', vcttStatus.error);
              alert(`Error checking VCTT status: ${vcttStatus.error}`);
              break;
            }
            
            if (vcttStatus.configured && vcttStatus.valid_path && vcttStatus.app_id) {
              // VCTT is configured and path is valid, launch it
              console.log('[VCTT] Configured and valid, checking if already running...');
              try {
                // Check if already running via API before launching
                const isRunning = await api.is_app_running(vcttStatus.app_id);
                if (isRunning) {
                  console.log('[VCTT] Already running, skipping launch');
                  alert('VCTT App is already running.');
                  break;
                }
                
                console.log('[VCTT] Not running, launching...');
                await api.launch_local_app(vcttStatus.app_id);
                console.log('[VCTT] Launch command sent successfully');
                // Don't show alert - launch happens in background
              } catch (error: any) {
                console.error('[VCTT] Launch error:', error);
                // Check if error is "already running"
                if (error.message && error.message.includes('already running')) {
                  alert('VCTT App is already running.');
                } else {
                  alert(`Failed to launch VCTT: ${error.message}`);
                }
              }
            } else if (vcttStatus.configured && !vcttStatus.valid_path) {
              // VCTT is configured but path is invalid
              console.log('[VCTT] Configured but path invalid, showing installer to reconfigure...');
              alert(`VCTT is configured but the installation path is invalid: ${vcttStatus.path || 'unknown'}\n\nPlease reconfigure VCTT.`);
              setShowVCTTInstaller(true);
            } else {
              // VCTT is not configured, show installer
              console.log('[VCTT] Not configured, showing installer...');
              setShowVCTTInstaller(true);
            }
          } catch (error: any) {
            console.error('[VCTT] Handler error:', error);
            alert(`Error: ${error.message}`);
          } finally {
            setLaunchingVCTT(false);
          }
          break;
        }
        
        case 'settings': {
          // Open Settings window
          console.log('Opening Settings window...');
          await api.open_settings_window();
          break;
        }
        
        case 'status': {
          // Open Status window
          console.log('Opening Status window...');
          await api.open_status_window();
          break;
        }
      }
    } catch (error) {
      console.error(`Failed to launch ${toolId}:`, error);
      alert(`Failed to launch ${toolId}: ${error}`);
    }
  };

  // Don't render dashboard while checking first-run status
  if (isCheckingFirstRun) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-50 via-gray-100 to-gray-200 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 via-gray-100 to-gray-200 flex flex-col relative overflow-hidden">
      {/* Setup Wizard Modal */}
      {showWizard && (
        <SetupWizard
          onComplete={handleWizardComplete}
          onSkip={handleWizardSkip}
        />
      )}

      {/* Service Selector Modal */}
      {serviceSelector && (
        <ServiceSelector
          serviceName={serviceSelector.serviceName}
          instances={serviceSelector.instances}
          onSelect={handleServiceSelect}
          onCancel={() => setServiceSelector(null)}
        />
      )}

      {/* VCTT Installer Modal */}
      {showVCTTInstaller && (
        <VCTTInstaller
          onComplete={handleVCTTInstallComplete}
          onCancel={() => setShowVCTTInstaller(false)}
        />
      )}

      {/* Background Logo */}
      <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
        <img
          src={logo}
          alt=""
          className="w-[600px] h-[600px] opacity-[0.03] object-contain"
        />
      </div>
      
      {/* Header */}
      <header className="pt-12 pb-8 px-8 text-center relative z-10">
        <h1 className="text-gray-800 mb-2">Pantheon Lab Digital Human Tool Orchestrator</h1>
        <p className="text-gray-600">Select a tool to launch</p>
      </header>

      {/* Main Content */}
      <main className="flex-1 px-8 pb-12 relative z-10">
        <div className="max-w-5xl mx-auto grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {tools.map((tool) => {
            const Icon = tool.icon;
            return (
              <button
                key={tool.id}
                onClick={() => handleLaunch(tool.id)}
                className="group relative bg-white/80 backdrop-blur-sm border border-gray-200 rounded-2xl p-8 transition-all duration-300 hover:scale-105 hover:border-gray-600 hover:shadow-2xl overflow-hidden"
              >
                {/* Gradient Background Effect */}
                <div
                  className={`absolute inset-0 bg-gradient-to-br ${tool.color} opacity-0 group-hover:opacity-10 transition-opacity duration-300`}
                />

                {/* Icon with Gradient */}
                <div className="relative mb-4">
                  <div
                    className={`inline-flex p-4 rounded-xl bg-gradient-to-br ${tool.color} opacity-90 group-hover:opacity-100 transition-opacity`}
                  >
                    <Icon className="size-8 text-white" />
                  </div>
                </div>

                {/* Content */}
                <div className="relative text-left">
                  <h3 className="text-gray-800 mb-2">{tool.name}</h3>
                  <p className="text-gray-600 text-sm">{tool.description}</p>
                </div>

                {/* Launch Indicator */}
                <div className="absolute bottom-6 right-6 opacity-0 group-hover:opacity-100 transition-opacity">
                  <div className="size-2 rounded-full bg-green-400 animate-pulse" />
                </div>
              </button>
            );
          })}
        </div>
      </main>

      {/* Footer */}
      <footer className="py-6 px-8 text-center relative z-10">
        <p className="text-gray-500 text-sm">
        Pantheon Lab Digital Human Tool Orchestrator • Ready to launch
        </p>
      </footer>
    </div>
  );
}
