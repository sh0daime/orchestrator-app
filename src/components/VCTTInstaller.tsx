import { useState, useEffect, useRef } from 'react';
import { X, Download, FolderOpen, CheckCircle, AlertCircle, Loader } from 'lucide-react';

interface VCTTInstallerProps {
  onComplete: (installPath: string) => void;
  onCancel: () => void;
}

export default function VCTTInstaller({ onComplete, onCancel }: VCTTInstallerProps) {
  const [installPath, setInstallPath] = useState('');
  const [isInstalling, setIsInstalling] = useState(false);
  const [installStatus, setInstallStatus] = useState<'idle' | 'installing' | 'awaiting_continue' | 'success' | 'error'>('idle');
  const [statusMessage, setStatusMessage] = useState('');
  const [mode, setMode] = useState<'install' | 'browse'>('install'); // 'install' or 'browse'
  const [bootstrapRunning, setBootstrapRunning] = useState(false);
  const pollingIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

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

  const getDefaultPath = () => {
    // Default to user's home directory + VCTT
    return '~/VCTT';
  };

  const startPollingBootstrapStatus = async (installDir: string) => {
    // Poll every 2 seconds to check if terminal window is still open
    pollingIntervalRef.current = setInterval(async () => {
      try {
        await waitForAPI();
        const api = window.pywebview!.api;
        const isRunning = await api.is_vctt_bootstrap_running(installDir);
        
        if (!isRunning) {
          // Terminal window closed - user finished (or cancelled)
          setBootstrapRunning(false);
          setStatusMessage('Terminal window closed. Click "Continue" to verify and configure the installation.');
          setInstallStatus('awaiting_continue'); // Waiting for user to click Continue
          if (pollingIntervalRef.current) {
            clearInterval(pollingIntervalRef.current);
            pollingIntervalRef.current = null;
          }
        }
      } catch (error: any) {
        console.error('Error checking bootstrap status:', error);
        // Continue polling even if there's an error
      }
    }, 2000); // Check every 2 seconds
  };

  // Cleanup polling on unmount
  useEffect(() => {
    return () => {
      if (pollingIntervalRef.current) {
        clearInterval(pollingIntervalRef.current);
      }
    };
  }, []);

  const handleInstall = async () => {
    if (!installPath.trim()) {
      setStatusMessage('Please enter an installation directory');
      setInstallStatus('error');
      return;
    }

    // Prevent multiple installations
    if (bootstrapRunning) {
      setStatusMessage('Installation already in progress. Please wait for it to complete.');
      return;
    }

    setIsInstalling(true);
    setInstallStatus('installing');
    setStatusMessage('Starting installation...');

    try {
      await waitForAPI();
      const api = window.pywebview!.api;

      // Run bootstrap installer (this starts the installer window)
      const result = await api.run_vctt_bootstrap(installPath);

      if (result.success) {
        setStatusMessage('Installation window opened! Please complete the installation in the terminal window. When finished, close the terminal and click "Continue" below.');
        setInstallStatus('installing');
        setBootstrapRunning(true);
        setIsInstalling(false); // Allow UI to update
        
        // Start polling to check if terminal window is closed
        startPollingBootstrapStatus(installPath);
      } else {
        setStatusMessage(`Installation failed: ${result.message}`);
        setInstallStatus('error');
        setIsInstalling(false);
        setBootstrapRunning(false);
      }
    } catch (error: any) {
      setStatusMessage(`Failed to start installation: ${error.message}`);
      setInstallStatus('error');
      setIsInstalling(false);
      setBootstrapRunning(false);
    }
  };

  const handleContinue = async () => {
    // User has confirmed installation is complete, now verify and configure
    setIsInstalling(true);
    setInstallStatus('installing');
    setStatusMessage('Verifying installation...');

    try {
      await waitForAPI();
      const api = window.pywebview!.api;

      // First, verify that VCTT was actually installed at the specified path
      // The configure_vctt_app will validate the path
      setStatusMessage('Configuring VCTT...');
      await api.configure_vctt_app(installPath);
      
      setStatusMessage(`Installation complete! VCTT has been configured.`);
      setInstallStatus('success');
      
      setTimeout(() => {
        onComplete(installPath);
      }, 2000);
    } catch (error: any) {
      // If configuration fails, it means installation didn't complete successfully
      setStatusMessage(`Configuration failed: ${error.message}. Please ensure the installation completed successfully in the terminal window.`);
      setInstallStatus('error');
      setBootstrapRunning(false); // Allow user to try again
    } finally {
      setIsInstalling(false);
    }
  };

  const handleBrowseFolder = async () => {
    try {
      await waitForAPI();
      const api = window.pywebview!.api;
      
      const selectedPath = await api.browse_folder('Select VCTT Installation Directory');
      if (selectedPath) {
        setInstallPath(selectedPath);
      }
    } catch (error: any) {
      setStatusMessage(`Failed to browse folder: ${error.message}`);
      setInstallStatus('error');
    }
  };

  const handleBrowseConfigure = async () => {
    if (!installPath.trim()) {
      setStatusMessage('Please enter a path to your existing VCTT installation');
      setInstallStatus('error');
      return;
    }

    setIsInstalling(true);
    setInstallStatus('installing');
    setStatusMessage('Validating and configuring VCTT...');

    try {
      await waitForAPI();
      const api = window.pywebview!.api;

      // Configure VCTT in orchestrator
      await api.configure_vctt_app(installPath.trim());
      setStatusMessage('VCTT has been configured successfully!');
      setInstallStatus('success');
      
      setTimeout(() => {
        onComplete(installPath.trim());
      }, 2000);
    } catch (error: any) {
      setStatusMessage(`Configuration failed: ${error.message}. Please check the path and try again.`);
      setInstallStatus('error');
    } finally {
      setIsInstalling(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-lg">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <div>
            <h2 className="text-2xl font-bold text-gray-800">Install VCTT App</h2>
            <p className="text-sm text-gray-600 mt-1">
              Install or configure the VCTT application
            </p>
          </div>
          <button
            onClick={onCancel}
            className="text-gray-400 hover:text-gray-600 transition-colors"
            disabled={isInstalling}
          >
            <X className="w-6 h-6" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 space-y-6">
          {/* Mode Selection */}
          <div className="flex gap-3">
            <button
              onClick={() => {
                setMode('install');
                setInstallPath('');
                setStatusMessage('');
                setInstallStatus('idle');
              }}
              className={`flex-1 px-4 py-3 rounded-lg border-2 transition-colors ${
                mode === 'install'
                  ? 'border-blue-500 bg-blue-50 text-blue-700'
                  : 'border-gray-200 bg-white text-gray-700 hover:bg-gray-50'
              }`}
              disabled={isInstalling}
            >
              <Download className="w-5 h-5 mx-auto mb-1" />
              <div className="font-semibold">Install Fresh</div>
              <div className="text-xs mt-1">Install VCTT to a new directory</div>
            </button>
            <button
              onClick={() => {
                setMode('browse');
                setInstallPath('');
                setStatusMessage('');
                setInstallStatus('idle');
              }}
              className={`flex-1 px-4 py-3 rounded-lg border-2 transition-colors ${
                mode === 'browse'
                  ? 'border-blue-500 bg-blue-50 text-blue-700'
                  : 'border-gray-200 bg-white text-gray-700 hover:bg-gray-50'
              }`}
              disabled={isInstalling}
            >
              <FolderOpen className="w-5 h-5 mx-auto mb-1" />
              <div className="font-semibold">Browse Existing</div>
              <div className="text-xs mt-1">Use an existing installation</div>
            </button>
          </div>

          {mode === 'install' && (
            <>
              {/* Installation Directory */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Installation Directory <span className="text-red-500">*</span>
                </label>
                <div className="flex gap-2">
                  <input
                    type="text"
                    value={installPath}
                    onChange={(e) => setInstallPath(e.target.value)}
                    placeholder={getDefaultPath()}
                    className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    disabled={isInstalling || bootstrapRunning}
                  />
                  <button
                    onClick={handleBrowseFolder}
                    className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                    disabled={isInstalling || bootstrapRunning}
                    title="Browse for directory"
                  >
                    <FolderOpen className="w-5 h-5 text-gray-600" />
                  </button>
                </div>
                <p className="text-xs text-gray-500 mt-1">
                  Enter or browse to select where VCTT should be installed (e.g., C:\Users\YourName\VCTT). The directory can be empty or non-existent.
                </p>
              </div>

              {/* Prerequisites Info */}
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <h3 className="font-semibold text-blue-900 mb-2">Prerequisites</h3>
                <ul className="text-sm text-blue-800 space-y-1 list-disc list-inside">
                  <li>Git must be installed and in your PATH</li>
                  <li>Conda (Anaconda or Miniconda) must be installed</li>
                  <li>GitHub authentication (CLI, PAT, or SSH key)</li>
                  <li>Access to the pantheon-lab/data repository</li>
                </ul>
              </div>
            </>
          )}

          {mode === 'browse' && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Existing Installation Path <span className="text-red-500">*</span>
              </label>
              <div className="flex gap-2">
                <input
                  type="text"
                  value={installPath}
                  onChange={(e) => setInstallPath(e.target.value)}
                  placeholder="C:\Users\YourName\VCTT\VCTT_app or /home/user/VCTT/VCTT_app"
                  className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  disabled={isInstalling}
                />
                <button
                  onClick={handleBrowseFolder}
                  className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
                  disabled={isInstalling}
                  title="Browse for directory"
                >
                  <FolderOpen className="w-5 h-5" />
                </button>
              </div>
              <p className="text-xs text-gray-500 mt-1">
                Enter the path to your existing VCTT installation directory (should contain main.py and launch_vctt.bat/sh)
              </p>
            </div>
          )}

          {/* Status Message */}
          {statusMessage && (
            <div
              className={`p-4 rounded-lg flex items-start gap-3 ${
                installStatus === 'success'
                  ? 'bg-green-50 text-green-800 border border-green-200'
                  : installStatus === 'error'
                  ? 'bg-red-50 text-red-800 border border-red-200'
                  : 'bg-blue-50 text-blue-800 border border-blue-200'
              }`}
            >
              {installStatus === 'installing' ? (
                <Loader className="w-5 h-5 animate-spin flex-shrink-0 mt-0.5" />
              ) : installStatus === 'success' ? (
                <CheckCircle className="w-5 h-5 flex-shrink-0 mt-0.5" />
              ) : (
                <AlertCircle className="w-5 h-5 flex-shrink-0 mt-0.5" />
              )}
              <div className="flex-1">
                <p className="text-sm font-medium">{statusMessage}</p>
                {installStatus === 'installing' && mode === 'install' && (
                  <p className="text-xs mt-2 opacity-75">
                    A terminal window will open to guide you through the installation process.
                  </p>
                )}
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="p-6 border-t border-gray-200 bg-gray-50 flex justify-end gap-3">
          <button
            onClick={onCancel}
            disabled={isInstalling || bootstrapRunning}
            className="px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-100 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Cancel
          </button>
          {mode === 'browse' && installPath.trim() && !isInstalling && installStatus !== 'success' ? (
            <button
              onClick={handleBrowseConfigure}
              className="px-6 py-2 bg-green-500 text-white rounded-lg hover:bg-green-600 transition-colors flex items-center gap-2"
            >
              <CheckCircle className="w-4 h-4" />
              Configure VCTT
            </button>
          ) : mode === 'install' && installStatus === 'awaiting_continue' ? (
            <button
              onClick={handleContinue}
              disabled={!installPath.trim() || isInstalling}
              className="px-6 py-2 bg-green-500 text-white rounded-lg hover:bg-green-600 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
            >
              <CheckCircle className="w-4 h-4" />
              Continue
            </button>
          ) : mode === 'install' ? (
            <button
              onClick={handleInstall}
              disabled={isInstalling || bootstrapRunning || !installPath.trim()}
              className="px-6 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
            >
              {isInstalling || bootstrapRunning ? (
                <>
                  <Loader className="w-4 h-4 animate-spin" />
                  {bootstrapRunning ? 'Installing...' : 'Starting...'}
                </>
              ) : (
                <>
                  <Download className="w-4 h-4" />
                  Install VCTT
                </>
              )}
            </button>
          ) : null}
        </div>
      </div>
    </div>
  );
}
