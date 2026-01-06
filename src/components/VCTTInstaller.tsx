import { useState } from 'react';
import { X, Download, FolderOpen, CheckCircle, AlertCircle, Loader } from 'lucide-react';

interface VCTTInstallerProps {
  onComplete: (installPath: string) => void;
  onCancel: () => void;
}

export default function VCTTInstaller({ onComplete, onCancel }: VCTTInstallerProps) {
  const [installPath, setInstallPath] = useState('');
  const [isInstalling, setIsInstalling] = useState(false);
  const [installStatus, setInstallStatus] = useState<'idle' | 'installing' | 'success' | 'error'>('idle');
  const [statusMessage, setStatusMessage] = useState('');

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
    if (window.pywebview?.api) {
      // Try to get platform-specific default
      return '~/VCTT';
    }
    return '~/VCTT';
  };

  const handleInstall = async () => {
    if (!installPath.trim()) {
      setStatusMessage('Please enter an installation directory');
      setInstallStatus('error');
      return;
    }

    setIsInstalling(true);
    setInstallStatus('installing');
    setStatusMessage('Starting installation...');

    try {
      await waitForAPI();
      const api = window.pywebview!.api;

      // Run bootstrap installer
      const result = await api.run_vctt_bootstrap(installPath);

      if (result.success) {
        setStatusMessage('Installation started successfully! The installer window will guide you through the process.');
        setInstallStatus('success');
        
        // Wait a bit, then configure the app
        setTimeout(async () => {
          try {
            // Configure VCTT in orchestrator
            await api.configure_vctt_app(installPath);
            setStatusMessage(`Installation complete! VCTT has been configured.`);
            setTimeout(() => {
              onComplete(installPath);
            }, 2000);
          } catch (error: any) {
            setStatusMessage(`Installation started, but configuration failed: ${error.message}. You can configure it manually in Settings.`);
            setInstallStatus('error');
          }
        }, 1000);
      } else {
        setStatusMessage(`Installation failed: ${result.message}`);
        setInstallStatus('error');
      }
    } catch (error: any) {
      setStatusMessage(`Failed to start installation: ${error.message}`);
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
              Install the VCTT application on your system
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
                disabled={isInstalling}
              />
              <button
                onClick={() => {
                  // Note: File picker would require additional API support
                  // For now, user can type the path
                }}
                className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
                disabled={isInstalling}
                title="Enter path manually"
              >
                <FolderOpen className="w-5 h-5" />
              </button>
            </div>
            <p className="text-xs text-gray-500 mt-1">
              Enter the directory where VCTT should be installed (e.g., ~/VCTT or C:\Users\YourName\VCTT)
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
                {installStatus === 'installing' && (
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
            disabled={isInstalling}
            className="px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-100 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Cancel
          </button>
          <button
            onClick={handleInstall}
            disabled={isInstalling || !installPath.trim()}
            className="px-6 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
          >
            {isInstalling ? (
              <>
                <Loader className="w-4 h-4 animate-spin" />
                Installing...
              </>
            ) : (
              <>
                <Download className="w-4 h-4" />
                Install VCTT
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}

