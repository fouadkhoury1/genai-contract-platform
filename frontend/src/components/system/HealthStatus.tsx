'use client';

import { useEffect, useState } from 'react';
import { api, endpoints } from '@/lib/api';
import { CheckCircle, XCircle } from 'lucide-react';

interface HealthStatus {
  status: 'ok' | 'error';
}

export default function HealthStatus() {
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [lastChecked, setLastChecked] = useState<Date>(new Date());

  useEffect(() => {
    const fetchHealth = async () => {
      try {
        const response = await api.get(endpoints.health);
        setHealth(response.data);
        setLastChecked(new Date());
        setError(null);
      } catch (err) {
        setError('Failed to fetch health status');
        console.error('Health check error:', err);
      }
    };

    fetchHealth();
    const interval = setInterval(fetchHealth, 30000); // Refresh every 30 seconds

    return () => clearInterval(interval);
  }, []);

  if (error) {
    return (
      <div className="p-4 bg-red-900/20 text-red-400 rounded-md border border-red-900/50">
        <p>{error}</p>
      </div>
    );
  }

  if (!health) {
    return (
      <div className="flex items-center justify-center h-40">
        <div className="animate-spin rounded-full h-8 w-8 border-2 border-white border-t-transparent"></div>
      </div>
    );
  }

  const isHealthy = health.status === 'ok';

  return (
    <div className="space-y-6">
      <div className={`p-4 rounded-xl ${
        isHealthy 
          ? 'bg-green-900/30 text-green-400' 
          : 'bg-red-900/30 text-red-400'
      }`}>
        <div className="flex items-center gap-2">
          {isHealthy ? (
            <CheckCircle className="w-5 h-5" />
          ) : (
            <XCircle className="w-5 h-5" />
          )}
          <p className="font-semibold">
            Status: {isHealthy ? 'Healthy' : 'Unhealthy'}
          </p>
        </div>
        <p className="text-sm mt-1 text-[#9CABBA]">
          Last Checked: {lastChecked.toLocaleString()}
        </p>
      </div>

      <div className="space-y-3">
        <h3 className="text-[#9CABBA] font-medium">Service Status:</h3>
        <div className="grid gap-3">
          <div className={`flex items-center justify-between p-3 rounded-xl ${
            isHealthy ? 'bg-green-900/30' : 'bg-red-900/30'
          }`}>
            <span className="text-white">API Service</span>
            <div className={`flex items-center gap-2 ${
              isHealthy ? 'text-green-400' : 'text-red-400'
            }`}>
              {isHealthy ? (
                <>
                  <CheckCircle className="w-4 h-4" />
                  <span className="text-sm font-medium">Online</span>
                </>
              ) : (
                <>
                  <XCircle className="w-4 h-4" />
                  <span className="text-sm font-medium">Offline</span>
                </>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
} 