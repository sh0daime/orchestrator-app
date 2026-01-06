import { Server, Cloud } from 'lucide-react';

interface ServiceInstance {
  serverId: string;
  serverName: string;
  serviceId: string;
  serviceName: string;
  port: number;
  host: string;
}

interface ServiceSelectorProps {
  serviceName: string;
  instances: ServiceInstance[];
  onSelect: (serverId: string, serviceId: string) => void;
  onCancel: () => void;
}

export default function ServiceSelector({
  serviceName,
  instances,
  onSelect,
  onCancel,
}: ServiceSelectorProps) {
  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-lg">
        {/* Header */}
        <div className="p-6 border-b border-gray-200">
          <h2 className="text-2xl font-bold text-gray-800">Select {serviceName}</h2>
          <p className="text-sm text-gray-600 mt-1">
            Multiple instances found. Choose which server to launch from:
          </p>
        </div>

        {/* Service List */}
        <div className="p-6">
          <div className="space-y-3">
            {instances.map((instance) => (
              <button
                key={`${instance.serverId}-${instance.serviceId}`}
                onClick={() => onSelect(instance.serverId, instance.serviceId)}
                className="w-full text-left p-4 border-2 border-gray-200 rounded-lg hover:border-blue-500 hover:bg-blue-50 transition-all group"
              >
                <div className="flex items-start gap-3">
                  <div className="p-2 bg-blue-100 rounded-lg group-hover:bg-blue-200 transition-colors">
                    <Server className="w-5 h-5 text-blue-600" />
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <h3 className="font-semibold text-gray-800">{instance.serviceName}</h3>
                      <span className="text-xs text-gray-500 bg-gray-100 px-2 py-0.5 rounded">
                        Port {instance.port}
                      </span>
                    </div>
                    <div className="flex items-center gap-2 text-sm text-gray-600">
                      <Cloud className="w-4 h-4" />
                      <span>{instance.serverName}</span>
                      <span className="text-gray-400">•</span>
                      <span className="font-mono text-xs">{instance.host}</span>
                    </div>
                  </div>
                </div>
              </button>
            ))}
          </div>
        </div>

        {/* Footer */}
        <div className="p-6 border-t border-gray-200 bg-gray-50 flex justify-end">
          <button
            onClick={onCancel}
            className="px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-100 transition-colors"
          >
            Cancel
          </button>
        </div>
      </div>
    </div>
  );
}

