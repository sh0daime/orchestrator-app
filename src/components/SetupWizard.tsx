import { useState } from 'react';
import { X, ChevronLeft, ChevronRight, CheckCircle, AlertCircle } from 'lucide-react';

interface SetupWizardProps {
  onComplete: () => void;
  onSkip: () => void;
}

interface ServerData {
  name: string;
  host: string;
  port: number;
  username: string;
  ssh_key_path: string;
}

interface ServiceData {
  id: string;
  name: string;
  container_name: string;
  port: number;
  path: string;
  healthcheck_path: string;
  enabled: boolean;
}

export default function SetupWizard({ onComplete, onSkip }: SetupWizardProps) {
  const [currentStep, setCurrentStep] = useState(1);
  const [serverData, setServerData] = useState<ServerData>({
    name: 'Main Server',
    host: '',
    port: 22,
    username: '',
    ssh_key_path: '',
  });
  const [services, setServices] = useState<ServiceData[]>([
    {
      id: 'gradio',
      name: 'AI Gradio Apps Portal',
      container_name: 'portal',
      port: 8080,
      path: '/home/calvin/gradio-app',
      healthcheck_path: '/',
      enabled: true,
    },
    {
      id: 'pipeline',
      name: 'Pipeline Management Tool',
      container_name: 'pipeline-tool',
      port: 7860,
      path: '/home/calvin/pipeline-tool',
      healthcheck_path: '/',
      enabled: true,
    },
  ]);
  const [connectionStatus, setConnectionStatus] = useState<'idle' | 'testing' | 'success' | 'error'>('idle');
  const [connectionMessage, setConnectionMessage] = useState('');
  const [isSaving, setIsSaving] = useState(false);

  // Helper function to wait for PyWebView API
  const waitForAPI = (): Promise<void> => {
    return new Promise((resolve) => {
      if (window.pywebview?.api) {
        resolve();
      } else {
        window.addEventListener('pywebviewready', () => resolve());
      }
    });
  };

  const generateId = () => {
    return 'id-' + Date.now() + '-' + Math.random().toString(36).substr(2, 9);
  };

  const handleTestConnection = async () => {
    setConnectionStatus('testing');
    setConnectionMessage('Testing connection...');

    try {
      await waitForAPI();
      const api = window.pywebview!.api;

      const result = await api.test_connection({
        name: serverData.name,
        host: serverData.host,
        port: serverData.port,
        username: serverData.username,
        ssh_key_path: serverData.ssh_key_path,
      });

      if (result.includes('Successfully connected')) {
        setConnectionStatus('success');
        setConnectionMessage('Connection successful!');
      } else {
        setConnectionStatus('error');
        setConnectionMessage(result);
      }
    } catch (error: any) {
      setConnectionStatus('error');
      setConnectionMessage(error.message || 'Connection test failed');
    }
  };

  const handleFinish = async () => {
    setIsSaving(true);

    try {
      await waitForAPI();
      const api = window.pywebview!.api;

      // Load current config
      const config = await api.load_config();

      // Create server with services
      const serverId = generateId();
      const serverServices = services
        .filter(s => s.enabled)
        .map(s => ({
          id: generateId(),
          name: s.name,
          container_name: s.container_name,
          port: s.port,
          path: s.path,
          healthcheck_path: s.healthcheck_path,
        }));

      // Add server to config
      if (!config.servers) config.servers = [];
      config.servers.push({
        id: serverId,
        name: serverData.name,
        host: serverData.host,
        port: serverData.port,
        username: serverData.username,
        ssh_key_path: serverData.ssh_key_path,
        services: serverServices,
      });

      // Save config
      await api.save_config(config);

      // Mark setup as completed
      await api.mark_setup_completed();

      onComplete();
    } catch (error: any) {
      alert(`Failed to save configuration: ${error.message}`);
    } finally {
      setIsSaving(false);
    }
  };

  const handleSkip = async () => {
    try {
      await waitForAPI();
      const api = window.pywebview!.api;
      await api.mark_setup_completed();
      onSkip();
    } catch (error: any) {
      console.error('Failed to skip setup:', error);
      onSkip();
    }
  };

  const updateService = (index: number, field: keyof ServiceData, value: any) => {
    const updated = [...services];
    updated[index] = { ...updated[index], [field]: value };
    setServices(updated);
  };

  const canProceedToNext = () => {
    switch (currentStep) {
      case 1:
        return true; // Welcome screen, can always proceed
      case 2:
        return serverData.host.trim() !== '' && 
               serverData.username.trim() !== '' && 
               serverData.ssh_key_path.trim() !== '';
      case 3:
        return services.some(s => s.enabled);
      case 4:
        return true; // Review screen
      default:
        return false;
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-2xl max-h-[90vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <div>
            <h2 className="text-2xl font-bold text-gray-800">Welcome to PLATONIC</h2>
            <p className="text-sm text-gray-600 mt-1">Setup Wizard - Step {currentStep} of 4</p>
          </div>
          <button
            onClick={handleSkip}
            className="text-gray-400 hover:text-gray-600 transition-colors"
          >
            <X className="w-6 h-6" />
          </button>
        </div>

        {/* Progress Bar */}
        <div className="px-6 py-4 bg-gray-50 border-b border-gray-200">
          <div className="flex items-center gap-2">
            {[1, 2, 3, 4].map((step) => (
              <div key={step} className="flex-1 flex items-center">
                <div
                  className={`w-full h-2 rounded-full ${
                    step <= currentStep ? 'bg-blue-500' : 'bg-gray-300'
                  }`}
                />
                {step < 4 && (
                  <div
                    className={`w-2 h-2 rounded-full mx-1 ${
                      step < currentStep ? 'bg-blue-500' : 'bg-gray-300'
                    }`}
                  />
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6">
          {/* Step 1: Welcome */}
          {currentStep === 1 && (
            <div className="text-center py-8">
              <div className="mb-6">
                <div className="inline-flex p-4 rounded-full bg-gradient-to-br from-blue-500 to-purple-500 mb-4">
                  <CheckCircle className="w-12 h-12 text-white" />
                </div>
              </div>
              <h3 className="text-2xl font-bold text-gray-800 mb-4">
                Welcome to PLATONIC!
              </h3>
              <p className="text-gray-600 mb-8 max-w-md mx-auto">
                PLATONIC (Pantheon Lab Tools Orchestration for Integration and Control) helps you
                manage and launch your AI services and applications from a single dashboard.
              </p>
              <p className="text-gray-600 mb-8 max-w-md mx-auto">
                Let's set up your first server and services. This will only take a few minutes.
              </p>
            </div>
          )}

          {/* Step 2: Server Configuration */}
          {currentStep === 2 && (
            <div className="space-y-6">
              <div>
                <h3 className="text-xl font-bold text-gray-800 mb-2">Server Configuration</h3>
                <p className="text-gray-600 text-sm">
                  Enter your server details to connect via SSH
                </p>
              </div>

              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Server Name
                  </label>
                  <input
                    type="text"
                    value={serverData.name}
                    onChange={(e) => setServerData({ ...serverData, name: e.target.value })}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="Main Server"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Host <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="text"
                    value={serverData.host}
                    onChange={(e) => setServerData({ ...serverData, host: e.target.value })}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="192.168.50.101"
                    required
                  />
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Port <span className="text-red-500">*</span>
                    </label>
                    <input
                      type="number"
                      value={serverData.port}
                      onChange={(e) => setServerData({ ...serverData, port: parseInt(e.target.value) || 22 })}
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      placeholder="22"
                      required
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Username <span className="text-red-500">*</span>
                    </label>
                    <input
                      type="text"
                      value={serverData.username}
                      onChange={(e) => setServerData({ ...serverData, username: e.target.value })}
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      placeholder="calvin"
                      required
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    SSH Key Path <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="text"
                    value={serverData.ssh_key_path}
                    onChange={(e) => setServerData({ ...serverData, ssh_key_path: e.target.value })}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="C:\Users\plab\calvin@desktop"
                    required
                  />
                  <p className="text-xs text-gray-500 mt-1">
                    Path to your private SSH key file
                  </p>
                </div>

                <div className="pt-4">
                  <button
                    onClick={handleTestConnection}
                    disabled={connectionStatus === 'testing' || !serverData.host || !serverData.username || !serverData.ssh_key_path}
                    className="w-full px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
                  >
                    {connectionStatus === 'testing' ? 'Testing...' : 'Test Connection'}
                  </button>

                  {connectionStatus !== 'idle' && (
                    <div className={`mt-3 p-3 rounded-lg flex items-center gap-2 ${
                      connectionStatus === 'success' ? 'bg-green-50 text-green-800' : 'bg-red-50 text-red-800'
                    }`}>
                      {connectionStatus === 'success' ? (
                        <CheckCircle className="w-5 h-5" />
                      ) : (
                        <AlertCircle className="w-5 h-5" />
                      )}
                      <span className="text-sm">{connectionMessage}</span>
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}

          {/* Step 3: Service Selection */}
          {currentStep === 3 && (
            <div className="space-y-6">
              <div>
                <h3 className="text-xl font-bold text-gray-800 mb-2">Service Selection</h3>
                <p className="text-gray-600 text-sm">
                  Select which services you want to configure (you can add more later)
                </p>
              </div>

              <div className="space-y-4">
                {services.map((service, index) => (
                  <div
                    key={service.id}
                    className={`border-2 rounded-lg p-4 ${
                      service.enabled ? 'border-blue-500 bg-blue-50' : 'border-gray-200 bg-gray-50'
                    }`}
                  >
                    <div className="flex items-start gap-3">
                      <input
                        type="checkbox"
                        checked={service.enabled}
                        onChange={(e) => updateService(index, 'enabled', e.target.checked)}
                        className="mt-1 w-5 h-5 text-blue-500 rounded focus:ring-blue-500"
                      />
                      <div className="flex-1 space-y-3">
                        <div>
                          <h4 className="font-semibold text-gray-800">{service.name}</h4>
                        </div>

                        {service.enabled && (
                          <div className="grid grid-cols-2 gap-3">
                            <div>
                              <label className="block text-xs font-medium text-gray-700 mb-1">
                                Container Name
                              </label>
                              <input
                                type="text"
                                value={service.container_name}
                                onChange={(e) => updateService(index, 'container_name', e.target.value)}
                                className="w-full px-3 py-1.5 text-sm border border-gray-300 rounded focus:ring-2 focus:ring-blue-500"
                              />
                            </div>
                            <div>
                              <label className="block text-xs font-medium text-gray-700 mb-1">
                                Port
                              </label>
                              <input
                                type="number"
                                value={service.port}
                                onChange={(e) => updateService(index, 'port', parseInt(e.target.value) || 8080)}
                                className="w-full px-3 py-1.5 text-sm border border-gray-300 rounded focus:ring-2 focus:ring-blue-500"
                              />
                            </div>
                            <div className="col-span-2">
                              <label className="block text-xs font-medium text-gray-700 mb-1">
                                Path
                              </label>
                              <input
                                type="text"
                                value={service.path}
                                onChange={(e) => updateService(index, 'path', e.target.value)}
                                className="w-full px-3 py-1.5 text-sm border border-gray-300 rounded focus:ring-2 focus:ring-blue-500"
                                placeholder="/home/calvin/service"
                              />
                            </div>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Step 4: Review & Finish */}
          {currentStep === 4 && (
            <div className="space-y-6">
              <div>
                <h3 className="text-xl font-bold text-gray-800 mb-2">Review Configuration</h3>
                <p className="text-gray-600 text-sm">
                  Review your settings before completing setup
                </p>
              </div>

              <div className="space-y-4">
                <div className="bg-gray-50 rounded-lg p-4">
                  <h4 className="font-semibold text-gray-800 mb-3">Server</h4>
                  <div className="space-y-1 text-sm">
                    <div className="flex justify-between">
                      <span className="text-gray-600">Name:</span>
                      <span className="font-medium">{serverData.name}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Host:</span>
                      <span className="font-medium">{serverData.host}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Port:</span>
                      <span className="font-medium">{serverData.port}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Username:</span>
                      <span className="font-medium">{serverData.username}</span>
                    </div>
                  </div>
                </div>

                <div className="bg-gray-50 rounded-lg p-4">
                  <h4 className="font-semibold text-gray-800 mb-3">
                    Services ({services.filter(s => s.enabled).length})
                  </h4>
                  <div className="space-y-2">
                    {services.filter(s => s.enabled).map((service) => (
                      <div key={service.id} className="text-sm border-l-2 border-blue-500 pl-3">
                        <div className="font-medium text-gray-800">{service.name}</div>
                        <div className="text-gray-600 text-xs mt-1">
                          Container: {service.container_name} • Port: {service.port} • Path: {service.path}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between p-6 border-t border-gray-200 bg-gray-50">
          <div>
            {currentStep === 1 && (
              <button
                onClick={handleSkip}
                className="px-4 py-2 text-gray-600 hover:text-gray-800 transition-colors"
              >
                Skip Setup
              </button>
            )}
          </div>

          <div className="flex items-center gap-3">
            {currentStep > 1 && (
              <button
                onClick={() => setCurrentStep(currentStep - 1)}
                className="px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-100 transition-colors flex items-center gap-2"
              >
                <ChevronLeft className="w-4 h-4" />
                Back
              </button>
            )}

            {currentStep < 4 ? (
              <button
                onClick={() => setCurrentStep(currentStep + 1)}
                disabled={!canProceedToNext()}
                className="px-6 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
              >
                Next
                <ChevronRight className="w-4 h-4" />
              </button>
            ) : (
              <button
                onClick={handleFinish}
                disabled={isSaving}
                className="px-6 py-2 bg-green-500 text-white rounded-lg hover:bg-green-600 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
              >
                {isSaving ? 'Saving...' : 'Finish Setup'}
                <CheckCircle className="w-4 h-4" />
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

